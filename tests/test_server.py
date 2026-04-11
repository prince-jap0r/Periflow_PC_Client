import socket
import time
import unittest

from periflow.models import AppSettings
from periflow.protocol import HANDSHAKE_TOKEN, PROTOCOL_VERSION, encode_message, recv_message
from periflow.server import PeriflowServer


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class DummyMediaService:
    def __init__(self) -> None:
        self.items = []

    def update_settings(self, settings) -> None:
        self.settings = settings

    def cleanup(self) -> None:
        return

    def submit_frame(self, metadata, body) -> None:
        self.items.append((metadata, body))


class DummyControlService:
    def __init__(self) -> None:
        self.items = []

    def update_settings(self, settings) -> None:
        self.settings = settings

    def cleanup(self) -> None:
        return

    def submit_message(self, metadata) -> None:
        self.items.append(metadata)


class ServerTests(unittest.TestCase):
    def test_tcp_handshake_ack_and_video_dispatch(self) -> None:
        tcp_port = get_free_port()
        udp_port = get_free_port()
        events = []
        video = DummyMediaService()
        audio = DummyMediaService()
        control = DummyControlService()
        server = PeriflowServer(
            AppSettings(server_port=tcp_port, audio_port=udp_port, auto_firewall_rule=False),
            lambda event_type, payload: events.append((event_type, payload)),
            video_service=video,
            audio_service=audio,
            control_service=control,
        )
        server.start()
        try:
            client = socket.create_connection(("127.0.0.1", tcp_port), timeout=2)
            client.sendall(HANDSHAKE_TOKEN.encode("utf-8"))
            metadata, _ = recv_message(client)
            self.assertEqual(metadata["type"], "handshake_ack")
            self.assertEqual(metadata["protocol_version"], PROTOCOL_VERSION)
            self.assertIn("1080p", metadata["supported_resolutions"])
            self.assertIn(24, metadata["supported_fps"])

            client.sendall(encode_message({"type": "video_frame", "format": "jpeg"}, b"fake"))
            client.sendall(encode_message({"type": "mouse_move", "x": 10, "y": 20}, b""))
            time.sleep(0.2)

            self.assertEqual(video.items[0][0]["type"], "video_frame")
            self.assertEqual(control.items[0]["type"], "mouse_move")
            client.close()
        finally:
            server.stop()

    def test_udp_audio_datagram_is_accepted_for_active_client(self) -> None:
        tcp_port = get_free_port()
        udp_port = get_free_port()
        audio = DummyMediaService()
        server = PeriflowServer(
            AppSettings(
                server_port=tcp_port,
                audio_port=udp_port,
                audio_transport="udp",
                auto_firewall_rule=False,
            ),
            lambda *_args: None,
            video_service=DummyMediaService(),
            audio_service=audio,
            control_service=DummyControlService(),
        )
        server.start()
        try:
            client = socket.create_connection(("127.0.0.1", tcp_port), timeout=2)
            client.sendall(HANDSHAKE_TOKEN.encode("utf-8"))
            recv_message(client)

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_client:
                udp_client.sendto(
                    encode_message(
                        {
                            "type": "audio_frame",
                            "format": "pcm_s16le",
                            "channels": 1,
                            "sample_rate": 44100,
                        },
                        b"\x00\x01",
                    ),
                    ("127.0.0.1", udp_port),
                )
            time.sleep(0.2)
            self.assertEqual(audio.items[0][0]["type"], "audio_frame")
            self.assertEqual(audio.items[0][1], b"\x00\x01")
            client.close()
        finally:
            server.stop()
