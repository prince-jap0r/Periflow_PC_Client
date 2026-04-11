from __future__ import annotations

import json
import socket
import struct
import time
from typing import Any

HANDSHAKE_TOKEN = "PERIFLOW_CONNECT"
PROTOCOL_VERSION = 1
MAX_HEADER_LENGTH = 64 * 1024
MAX_BODY_LENGTH = 10 * 1024 * 1024
DEFAULT_MESSAGE_TIMEOUT_SECONDS = 15.0
DEFAULT_HANDSHAKE_TIMEOUT_SECONDS = 5.0
RAW_HANDSHAKE_PEEK_LIMIT = 4 * 1024


class ProtocolError(RuntimeError):
    pass


def recv_exact(sock: socket.socket, size: int, timeout_seconds: float = DEFAULT_MESSAGE_TIMEOUT_SECONDS) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    chunks = bytearray()
    while len(chunks) < size:
        if time.monotonic() >= deadline:
            raise TimeoutError(f"Timed out while waiting for {size} bytes.")
        try:
            chunk = sock.recv(size - len(chunks))
        except socket.timeout:
            continue
        if not chunk:
            raise ConnectionError("Socket closed while receiving data")
        chunks.extend(chunk)
    return bytes(chunks)


def _peek_bytes(sock: socket.socket, size: int, timeout_seconds: float) -> bytes:
    deadline = time.monotonic() + timeout_seconds
    while True:
        if time.monotonic() >= deadline:
            raise TimeoutError("Timed out while waiting for handshake bytes.")
        try:
            data = sock.recv(size, socket.MSG_PEEK)
        except socket.timeout:
            continue
        if data:
            return data
        raise ConnectionError("Socket closed while peeking at data")


def _skip_handshake_prefix(data: bytes) -> int:
    offset = 3 if data.startswith(b"\xef\xbb\xbf") else 0
    while offset < len(data) and data[offset] in b" \t\r\n":
        offset += 1
    return offset


def _consume_handshake_suffix(data: bytes, start: int) -> int:
    end = start
    while end < len(data) and data[end] in b" \t\r\n\x00":
        end += 1
    return end


def _extract_handshake_token(metadata: dict[str, Any]) -> str | None:
    for key in ("token", "message", "handshake", "auth_token"):
        value = metadata.get(key)
        if isinstance(value, str) and value:
            return value.strip()
    return None


def _normalize_handshake_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    message_type = metadata.get("type")
    if message_type is not None and message_type != "handshake":
        raise ProtocolError("Expected handshake message")

    token = _extract_handshake_token(metadata)
    if token != HANDSHAKE_TOKEN:
        raise ProtocolError("Handshake token mismatch")

    normalized = metadata.copy()
    normalized["type"] = "handshake"
    normalized["token"] = HANDSHAKE_TOKEN
    return normalized


def _handshake_preview(data: bytes, limit: int = 32) -> str:
    preview = data[:limit]
    ascii_preview = "".join(chr(byte) if 32 <= byte <= 126 else "." for byte in preview)
    suffix = "..." if len(data) > limit else ""
    return f"'{ascii_preview}{suffix}'"


def _parse_text_handshake_bytes(data: bytes) -> tuple[str, dict[str, Any] | None, int | None]:
    offset = _skip_handshake_prefix(data)
    payload = data[offset:]
    if not payload:
        return "incomplete", None, None

    raw_token = HANDSHAKE_TOKEN.encode("utf-8")
    if payload.startswith(raw_token):
        consume = _consume_handshake_suffix(data, offset + len(raw_token))
        return "matched", {"type": "handshake", "token": HANDSHAKE_TOKEN}, consume
    if raw_token.startswith(payload):
        return "incomplete", None, None

    if payload[:1] not in {b"{", b'"'}:
        return "mismatch", None, None

    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError:
        return "mismatch", None, None

    try:
        decoded, end = json.JSONDecoder().raw_decode(text)
    except json.JSONDecodeError:
        return "incomplete", None, None

    if isinstance(decoded, str):
        metadata = {"type": "handshake", "token": decoded.strip()}
    elif isinstance(decoded, dict):
        metadata = decoded
    else:
        return "mismatch", None, None

    try:
        normalized = _normalize_handshake_metadata(metadata)
    except ProtocolError:
        return "mismatch", None, None

    consume = offset + len(text[:end].encode("utf-8"))
    consume = _consume_handshake_suffix(data, consume)
    return "matched", normalized, consume


def _parse_utf_handshake_bytes(data: bytes) -> tuple[str, dict[str, Any] | None, int | None]:
    offset = _skip_handshake_prefix(data)
    payload = data[offset:]
    if len(payload) < 2:
        return "incomplete", None, None

    text_length = struct.unpack(">H", payload[:2])[0]
    if text_length <= 0:
        return "mismatch", None, None
    if len(payload) < 2 + text_length:
        return "incomplete", None, None

    status, metadata, consumed = _parse_text_handshake_bytes(payload[2 : 2 + text_length])
    if status != "matched" or consumed != text_length:
        return "mismatch", None, None
    return "matched", metadata, offset + 2 + text_length


def encode_message(metadata: dict[str, Any], body: bytes = b"") -> bytes:
    metadata = metadata.copy()
    metadata.setdefault("size", len(body))
    header = json.dumps(metadata, separators=(",", ":")).encode("utf-8")
    if len(header) > MAX_HEADER_LENGTH:
        raise ProtocolError("Header exceeds allowed length")
    if len(body) > MAX_BODY_LENGTH:
        raise ProtocolError("Body exceeds allowed length")
    return struct.pack(">I", len(header)) + header + body


def decode_packet(packet: bytes) -> tuple[dict[str, Any], bytes]:
    if len(packet) < 4:
        raise ProtocolError("Packet is too short to contain a header length.")
    header_length = struct.unpack(">I", packet[:4])[0]
    if header_length <= 0 or header_length > MAX_HEADER_LENGTH:
        raise ProtocolError(f"Invalid header length: {header_length}")
    if len(packet) < 4 + header_length:
        raise ProtocolError("Packet ended before JSON metadata completed.")

    header_bytes = packet[4 : 4 + header_length]
    try:
        metadata = json.loads(header_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError("Invalid JSON metadata") from exc

    try:
        body_length = int(metadata.get("size", len(packet) - (4 + header_length)))
    except (TypeError, ValueError) as exc:
        raise ProtocolError("Message size is invalid.") from exc

    if body_length < 0 or body_length > MAX_BODY_LENGTH:
        raise ProtocolError(f"Invalid body size: {body_length}")

    body_start = 4 + header_length
    body_end = body_start + body_length
    if len(packet) < body_end:
        raise ProtocolError("Packet ended before body completed.")
    if len(packet) != body_end:
        raise ProtocolError("Packet contains trailing bytes beyond the declared body.")
    return metadata, packet[body_start:body_end]


def recv_message(sock: socket.socket, timeout_seconds: float = DEFAULT_MESSAGE_TIMEOUT_SECONDS) -> tuple[dict[str, Any], bytes]:
    header_length = struct.unpack(">I", recv_exact(sock, 4, timeout_seconds=timeout_seconds))[0]
    if header_length <= 0 or header_length > MAX_HEADER_LENGTH:
        raise ProtocolError(f"Invalid header length: {header_length}")

    header_bytes = recv_exact(sock, header_length, timeout_seconds=timeout_seconds)
    try:
        metadata = json.loads(header_bytes.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ProtocolError("Invalid JSON metadata") from exc

    try:
        body_length = int(metadata.get("size", 0))
    except (TypeError, ValueError) as exc:
        raise ProtocolError("Message size is invalid.") from exc

    if body_length < 0 or body_length > MAX_BODY_LENGTH:
        raise ProtocolError(f"Invalid body size: {body_length}")
    body = recv_exact(sock, body_length, timeout_seconds=timeout_seconds) if body_length else b""
    return metadata, body


def perform_server_handshake(sock: socket.socket, timeout_seconds: float = DEFAULT_HANDSHAKE_TIMEOUT_SECONDS) -> dict[str, Any]:
    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Timed out while waiting for handshake bytes.")

        peek = _peek_bytes(sock, RAW_HANDSHAKE_PEEK_LIMIT, timeout_seconds=remaining)
        if len(peek) >= 4:
            framed_header_length = struct.unpack(">I", peek[:4])[0]
            if 0 < framed_header_length <= MAX_HEADER_LENGTH:
                metadata, _ = recv_message(sock, timeout_seconds=remaining)
                return _normalize_handshake_metadata(metadata)

        for parser in (_parse_text_handshake_bytes, _parse_utf_handshake_bytes):
            status, metadata, consume = parser(peek)
            if status == "matched":
                assert metadata is not None
                assert consume is not None
                recv_exact(sock, consume, timeout_seconds=remaining)
                return metadata
            if status == "incomplete":
                time.sleep(0.01)
                break
        else:
            raise ProtocolError(f"Raw handshake token mismatch; received {_handshake_preview(peek)}")
