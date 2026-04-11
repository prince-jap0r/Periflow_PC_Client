from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

RESOLUTION_PRESETS = {
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
}

FRAME_RATE_PRESETS = (15, 24, 30)

AUDIO_QUALITY_PRESETS = {
    "Mono 22.05 kHz": {"channels": 1, "sample_rate": 22050},
    "Mono 44.1 kHz": {"channels": 1, "sample_rate": 44100},
    "Stereo 44.1 kHz": {"channels": 2, "sample_rate": 44100},
}

AUDIO_TRANSPORT_PRESETS = {
    "UDP (Recommended)": "udp",
    "TCP Fallback": "tcp",
}


@dataclass(slots=True)
class AppSettings:
    server_host: str = "0.0.0.0"
    server_port: int = 5000
    audio_port: int = 5001
    audio_transport: str = "udp"
    video_enabled: bool = True
    audio_enabled: bool = True
    control_enabled: bool = True
    resolution: str = "720p"
    audio_quality: str = "Mono 44.1 kHz"
    fps: int = 24
    client_timeout_seconds: int = 120
    auto_firewall_rule: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "AppSettings":
        payload = payload or {}
        instance = cls()
        for field_name in cls.__dataclass_fields__:
            if field_name in payload:
                setattr(instance, field_name, payload[field_name])
        instance.server_port = int(instance.server_port)
        instance.audio_port = int(instance.audio_port)
        instance.fps = int(instance.fps)
        instance.client_timeout_seconds = int(instance.client_timeout_seconds)
        instance.audio_transport = str(instance.audio_transport).lower()
        instance.auto_firewall_rule = bool(instance.auto_firewall_rule)
        if instance.resolution not in RESOLUTION_PRESETS:
            instance.resolution = "720p"
        if instance.audio_quality not in AUDIO_QUALITY_PRESETS:
            instance.audio_quality = "Mono 44.1 kHz"
        if instance.audio_transport not in set(AUDIO_TRANSPORT_PRESETS.values()):
            instance.audio_transport = "udp"
        if instance.fps not in FRAME_RATE_PRESETS:
            instance.fps = 24
        return instance

    def to_dict(self) -> dict[str, Any]:
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "audio_port": self.audio_port,
            "audio_transport": self.audio_transport,
            "video_enabled": self.video_enabled,
            "audio_enabled": self.audio_enabled,
            "control_enabled": self.control_enabled,
            "resolution": self.resolution,
            "audio_quality": self.audio_quality,
            "fps": self.fps,
            "client_timeout_seconds": self.client_timeout_seconds,
            "auto_firewall_rule": self.auto_firewall_rule,
        }

    @property
    def video_size(self) -> tuple[int, int]:
        return RESOLUTION_PRESETS[self.resolution]

    @property
    def audio_profile(self) -> dict[str, int]:
        return AUDIO_QUALITY_PRESETS[self.audio_quality].copy()


@dataclass(slots=True)
class ClientSession:
    address: str
    port: int
    name: str = "Android Client"
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def label(self) -> str:
        return f"{self.name} ({self.address}:{self.port})"
