import json
import socket
import struct
import threading
import time
import unittest

from periflow.protocol import (
    HANDSHAKE_TOKEN,
    PROTOCOL_VERSION,
    decode_packet,
    encode_message,
    perform_server_handshake,
    recv_message,
)


class ProtocolTests(unittest.TestCase):
    def _perform_handshake(self, *payload_parts: bytes) -> dict:
        left, right = socket.socketpair()
        result = {}
        error = {}

        def worker() -> None:
            try:
                result["metadata"] = perform_server_handshake(right)
            except Exception as exc:  # pragma: no cover - test helper plumbing
                error["exception"] = exc

        thread = threading.Thread(target=worker)
        thread.start()
        try:
            for index, payload in enumerate(payload_parts):
                left.sendall(payload)
                if index < len(payload_parts) - 1:
                    time.sleep(0.05)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive(), "Handshake worker thread did not finish.")
            if "exception" in error:
                raise error["exception"]
            return result["metadata"]
        finally:
            left.close()
            right.close()

    def test_framed_message_round_trip(self) -> None:
        left, right = socket.socketpair()
        try:
            payload = encode_message({"type": "text", "message": "hello"}, b"")
            left.sendall(payload)
            metadata, body = recv_message(right)
            self.assertEqual(metadata["type"], "text")
            self.assertEqual(metadata["message"], "hello")
            self.assertEqual(body, b"")
        finally:
            left.close()
            right.close()

    def test_framed_handshake_is_accepted(self) -> None:
        metadata = self._perform_handshake(encode_message({"type": "handshake", "token": HANDSHAKE_TOKEN}))
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)

    def test_raw_handshake_is_accepted(self) -> None:
        metadata = self._perform_handshake(HANDSHAKE_TOKEN.encode("utf-8"))
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)

    def test_split_raw_handshake_is_accepted(self) -> None:
        metadata = self._perform_handshake(b"PERI", b"FLOW_CONNECT")
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)

    def test_raw_json_handshake_is_accepted(self) -> None:
        payload = json.dumps(
            {
                "type": "handshake",
                "token": HANDSHAKE_TOKEN,
                "client_name": "Periflow Android",
                "protocol_version": PROTOCOL_VERSION,
            }
        ).encode("utf-8")
        metadata = self._perform_handshake(payload)
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)
        self.assertEqual(metadata["client_name"], "Periflow Android")
        self.assertEqual(metadata["protocol_version"], PROTOCOL_VERSION)

    def test_utf_handshake_token_is_accepted(self) -> None:
        payload = HANDSHAKE_TOKEN.encode("utf-8")
        metadata = self._perform_handshake(struct.pack(">H", len(payload)) + payload)
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)

    def test_utf_json_handshake_is_accepted(self) -> None:
        payload = json.dumps({"token": HANDSHAKE_TOKEN, "client_name": "Periflow Android"}).encode("utf-8")
        metadata = self._perform_handshake(struct.pack(">H", len(payload)) + payload)
        self.assertEqual(metadata["token"], HANDSHAKE_TOKEN)
        self.assertEqual(metadata["client_name"], "Periflow Android")

    def test_decode_packet_round_trip(self) -> None:
        packet = encode_message({"type": "audio_frame", "format": "pcm_s16le"}, b"\x00\x01")
        metadata, body = decode_packet(packet)
        self.assertEqual(metadata["type"], "audio_frame")
        self.assertEqual(body, b"\x00\x01")


if __name__ == "__main__":
    unittest.main()
