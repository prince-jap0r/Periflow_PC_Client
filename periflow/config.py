from __future__ import annotations

import json
import os
from pathlib import Path

from .models import AppSettings
from .system import resolve_preferred_local_ip

APP_NAME = "Periflow"
DESKTOP_APP_NAME = "Periflow PC Client"
APP_VERSION = "1.0.0"
SERVER_NAME = DESKTOP_APP_NAME
SETTINGS_FILE = "settings.json"


def get_appdata_dir() -> Path:
    roaming = os.getenv("APPDATA")
    if roaming:
        return Path(roaming) / APP_NAME
    return Path.home() / "AppData" / "Roaming" / APP_NAME


def resolve_local_ip() -> str:
    try:
        return resolve_preferred_local_ip()
    except OSError:
        return "127.0.0.1"


class SettingsStore:
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or get_appdata_dir()
        self.path = self.base_dir / SETTINGS_FILE

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return AppSettings()
        return AppSettings.from_dict(data)

    def save(self, settings: AppSettings) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(settings.to_dict(), handle, indent=2)
