from __future__ import annotations

import socket
import threading
import time
from typing import Callable

from .config import APP_VERSION, SERVER_NAME
from .models import (
    AUDIO_QUALITY_PRESETS,
    AUDIO_TRANSPORT_PRESETS,
    FRAME_RATE_PRESETS,
    RESOLUTION_PRESETS,
    AppSettings,
    ClientSession,
)
from .protocol import (
    HANDSHAKE_TOKEN,
    PROTOCOL_VERSION,
    ProtocolError,
    decode_packet,
    encode_message,
    perform_server_handshake,
    recv_message,
)
from .services import AudioService, ControlService, VideoService
from .system import ensure_firewall_rules, is_running_as_admin, resolve_preferred_local_ip

EventCallback = Callable[[str, dict], None]


class PeriflowServer:
    def __init__(
        self,
        settings: AppSettings,
        event_callback: EventCallback,
        *,
        video_service: VideoService | None = None,
        audio_service: AudioService | None = None,
        control_service: ControlService | None = None,
    ) -> None:
        self._settings = settings
        self._event_callback = event_callback
        self._stop_event = threading.Event()
        self._server_socket: socket.socket | None = None
        self._udp_audio_socket: socket.socket | None = None
        self._accept_thread: threading.Thread | None = None
        self._udp_audio_thread: threading.Thread | None = None
        self._client_thread: threading.Thread | None = None
        self._client_socket: socket.socket | None = None
        self._client_lock = threading.Lock()
        self._client_session: ClientSession | None = None
        self._ignored_udp_addresses: set[str] = set()

        self._video_service = video_service or VideoService(self._log)
        self._audio_service = audio_service or AudioService(self._log)
        self._control_service = control_service or ControlService(self._log)
        self.update_settings(settings)

    @property
    def is_running(self) -> bool:
        return self._accept_thread is not None and self._accept_thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            self._log("Server is already running.")
            return

        self._stop_event.clear()
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self._settings.server_host, self._settings.server_port))
        listener.listen(5)
        listener.settimeout(1.0)

        try:
            udp_socket = self._create_udp_audio_socket() if self._settings.audio_transport == "udp" else None
        except OSError:
            listener.close()
            raise

        self._server_socket = listener
        self._udp_audio_socket = udp_socket
        self._accept_thread = threading.Thread(target=self._accept_loop, name="PeriflowAccept", daemon=True)
        self._accept_thread.start()
        if udp_socket is not None:
            self._udp_audio_thread = threading.Thread(target=self._udp_audio_loop, name="PeriflowUdpAudio", daemon=True)
            self._udp_audio_thread.start()

        display_host = resolve_preferred_local_ip()
        self._emit(
            "server_started",
            {
                "bind_host": self._settings.server_host,
                "display_host": display_host,
                "port": self._settings.server_port,
                "audio_port": self._settings.audio_port,
                "audio_transport": self._settings.audio_transport,
                "is_admin": is_running_as_admin(),
            },
        )
        self._log(
            f"Listening on {self._settings.server_host}:{self._settings.server_port} "
            f"(share {display_host}:{self._settings.server_port} with the phone). "
            f"Expected handshake token: {HANDSHAKE_TOKEN}"
        )
        if udp_socket is not None:
            self._log(f"UDP audio listener is active on {display_host}:{self._settings.audio_port}.")

        if self._settings.auto_firewall_rule:
            self.configure_firewall(auto=True)

    def stop(self) -> None:
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.close()
            except OSError:
                pass
            finally:
                self._server_socket = None

        if self._udp_audio_socket is not None:
            try:
                self._udp_audio_socket.close()
            except OSError:
                pass
            finally:
                self._udp_audio_socket = None

        with self._client_lock:
            if self._client_socket is not None:
                try:
                    self._client_socket.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self._client_socket.close()
                except OSError:
                    pass
                finally:
                    self._client_socket = None

        if self._accept_thread is not None:
            self._accept_thread.join(timeout=1.5)
            self._accept_thread = None
        if self._udp_audio_thread is not None:
            self._udp_audio_thread.join(timeout=1.5)
            self._udp_audio_thread = None
        if self._client_thread is not None:
            self._client_thread.join(timeout=1.5)
            self._client_thread = None

        self._client_session = None
        self._ignored_udp_addresses.clear()
        self._video_service.cleanup()
        self._audio_service.cleanup()
        self._control_service.cleanup()
        self._emit("server_stopped", {})
        self._log("Server stopped.")

    def update_settings(self, settings: AppSettings) -> None:
        self._settings = settings
        self._video_service.update_settings(settings)
        self._audio_service.update_settings(settings)
        self._control_service.update_settings(settings)

    def configure_firewall(self, *, auto: bool = False) -> None:
        result = ensure_firewall_rules(self._settings.server_port, self._settings.audio_port)
        self._emit(
            "firewall_status",
            {"success": result.success, "changed": result.changed, "message": result.message},
        )
        if result.success:
            prefix = "Windows Firewall auto-configured." if auto else "Windows Firewall configured."
            self._log(f"{prefix} {result.message}")
        else:
            prefix = "Automatic firewall setup skipped." if auto else "Firewall setup failed."
            self._log(f"{prefix} {result.message}")

    def _create_udp_audio_socket(self) -> socket.socket:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind((self._settings.server_host, self._settings.audio_port))
        udp_socket.settimeout(1.0)
        return udp_socket

    def _accept_loop(self) -> None:
        assert self._server_socket is not None
        while not self._stop_event.is_set():
            try:
                client_socket, address = self._server_socket.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            with self._client_lock:
                if self._client_socket is not None:
                    self._log(f"Rejected extra client from {address[0]}:{address[1]}.")
                    try:
                        client_socket.sendall(
                            encode_message(
                                {
                                    "type": "server_busy",
                                    "message": "Only one client is supported in this build.",
                                }
                            )
                        )
                    except OSError:
                        pass
                    client_socket.close()
                    continue
                self._client_socket = client_socket

            self._client_thread = threading.Thread(
                target=self._handle_client,
                args=(client_socket, address),
                name="PeriflowClient",
                daemon=True,
            )
            self._client_thread.start()

    def _handle_client(self, client_socket: socket.socket, address: tuple[str, int]) -> None:
        client_socket.settimeout(0.5)
        try:
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        except OSError:
            pass
        try:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        except OSError:
            pass

        session: ClientSession | None = None
        last_message_at = time.monotonic()
        try:
            handshake = perform_server_handshake(client_socket)
            session = ClientSession(
                address=address[0],
                port=address[1],
                name=str(handshake.get("client_name", "Android Client")),
            )
            self._client_session = session
            self._ignored_udp_addresses.clear()
            self._emit(
                "client_connected",
                {
                    "address": session.address,
                    "port": session.port,
                    "name": session.name,
                },
            )
            self._log(f"Client connected from {session.label}.")
            client_socket.sendall(
                encode_message(
                    {
                        "type": "handshake_ack",
                        "accepted": True,
                        "server_name": SERVER_NAME,
                        "server_version": APP_VERSION,
                        "protocol_version": PROTOCOL_VERSION,
                        "video_enabled": self._settings.video_enabled,
                        "audio_enabled": self._settings.audio_enabled,
                        "control_enabled": self._settings.control_enabled,
                        "audio_transport": self._settings.audio_transport,
                        "audio_port": self._settings.audio_port,
                        "resolution": self._settings.resolution,
                        "fps": self._settings.fps,
                        "supported_resolutions": list(RESOLUTION_PRESETS.keys()),
                        "supported_fps": list(FRAME_RATE_PRESETS),
                        "supported_audio_transports": list(AUDIO_TRANSPORT_PRESETS.values()),
                        "supported_audio_sample_rates": sorted(
                            {profile["sample_rate"] for profile in AUDIO_QUALITY_PRESETS.values()}
                        ),
                    }
                )
            )

            while not self._stop_event.is_set():
                try:
                    metadata, body = recv_message(client_socket, timeout_seconds=1.5)
                except TimeoutError:
                    if time.monotonic() - last_message_at > self._settings.client_timeout_seconds:
                        raise TimeoutError("No TCP traffic from the client for too long.")
                    continue
                except ConnectionError:
                    break
                last_message_at = time.monotonic()
                self._dispatch_tcp_message(client_socket, metadata, body)
        except (ProtocolError, OSError, TimeoutError, ValueError) as exc:
            self._log(f"Client error from {address[0]}:{address[1]}: {exc}")
        finally:
            self._cleanup_client(client_socket, session)

    def _dispatch_tcp_message(self, client_socket: socket.socket, metadata: dict, body: bytes) -> None:
        message_type = metadata.get("type")
        if message_type == "video_frame":
            self._video_service.submit_frame(metadata, body)
        elif message_type == "audio_frame":
            self._audio_service.submit_frame(metadata, body)
        elif message_type in {
            "mouse_move",
            "mouse_click",
            "mouse_scroll",
            "key_press",
            "key_release",
            "text_input",
        }:
            self._control_service.submit_message(metadata)
        elif message_type in {"text", "log"}:
            self._log(f"Client says: {metadata.get('message', '')}")
        elif message_type == "ping":
            try:
                client_socket.sendall(encode_message({"type": "pong"}))
            except OSError as exc:
                self._log(f"Failed to reply to ping: {exc}")
        else:
            self._log(f"Unhandled message type '{message_type}'.")

    def _udp_audio_loop(self) -> None:
        assert self._udp_audio_socket is not None
        while not self._stop_event.is_set():
            try:
                packet, address = self._udp_audio_socket.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            session = self._client_session
            if session is None:
                continue
            if address[0] != session.address:
                if address[0] not in self._ignored_udp_addresses:
                    self._ignored_udp_addresses.add(address[0])
                    self._log(f"Ignored UDP audio packet from {address[0]}:{address[1]} because it is not the active client.")
                continue

            try:
                metadata, body = self._parse_udp_audio_packet(packet)
            except ProtocolError as exc:
                self._log(f"Invalid UDP audio packet from {address[0]}:{address[1]}: {exc}")
                continue
            self._audio_service.submit_frame(metadata, body)

    def _parse_udp_audio_packet(self, packet: bytes) -> tuple[dict, bytes]:
        try:
            metadata, body = decode_packet(packet)
        except ProtocolError:
            metadata = {
                "type": "audio_frame",
                "format": "pcm_s16le",
                "channels": self._settings.audio_profile["channels"],
                "sample_rate": self._settings.audio_profile["sample_rate"],
                "size": len(packet),
            }
            return metadata, packet

        if metadata.get("type") != "audio_frame":
            raise ProtocolError(f"Unexpected UDP payload type '{metadata.get('type')}'.")
        return metadata, body

    def _cleanup_client(self, client_socket: socket.socket, session: ClientSession | None) -> None:
        with self._client_lock:
            if self._client_socket is client_socket:
                self._client_socket = None
        try:
            client_socket.close()
        except OSError:
            pass

        if session is not None:
            self._emit(
                "client_disconnected",
                {
                    "address": session.address,
                    "port": session.port,
                    "name": session.name,
                },
            )
            self._log(f"Client disconnected: {session.label}.")
        self._client_session = None
        self._ignored_udp_addresses.clear()

    def _emit(self, event_type: str, payload: dict) -> None:
        self._event_callback(event_type, payload)

    def _log(self, message: str) -> None:
        self._emit("log", {"message": message})
