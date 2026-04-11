from __future__ import annotations

import importlib
from typing import Callable

from ..models import AppSettings
from ..system import is_running_as_admin
from ._worker import DroppingWorker

NAMED_KEYS = {
    "alt": "alt",
    "backspace": "backspace",
    "caps_lock": "caps_lock",
    "cmd": "cmd",
    "ctrl": "ctrl",
    "delete": "delete",
    "down": "down",
    "end": "end",
    "enter": "enter",
    "esc": "esc",
    "f1": "f1",
    "f2": "f2",
    "f3": "f3",
    "f4": "f4",
    "f5": "f5",
    "f6": "f6",
    "f7": "f7",
    "f8": "f8",
    "f9": "f9",
    "f10": "f10",
    "f11": "f11",
    "f12": "f12",
    "home": "home",
    "left": "left",
    "page_down": "page_down",
    "page_up": "page_up",
    "right": "right",
    "shift": "shift",
    "space": "space",
    "tab": "tab",
    "up": "up",
    "win": "cmd",
    "windows": "cmd",
}


class ControlService:
    def __init__(self, log: Callable[[str], None]) -> None:
        self._log = log
        self._settings = AppSettings()
        self._runtime_ready = False
        self._runtime_error: str | None = None
        self._admin_hint_logged = False
        self._worker: DroppingWorker[dict] | None = None

    def update_settings(self, settings: AppSettings) -> None:
        self._settings = settings

    def cleanup(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None

    def submit_message(self, metadata: dict) -> None:
        if not self._settings.control_enabled:
            return
        self._ensure_worker()
        self._worker.submit(metadata.copy())

    def _ensure_worker(self) -> None:
        if self._worker is None:
            self._worker = DroppingWorker("PeriflowControl", self._process_message, self._log, maxsize=128)

    def _process_message(self, metadata: dict) -> None:
        if not self._ensure_runtime():
            return

        message_type = metadata.get("type")
        try:
            if message_type == "mouse_move":
                if "x" in metadata and "y" in metadata:
                    self._mouse.position = (int(metadata["x"]), int(metadata["y"]))
                else:
                    current_x, current_y = self._mouse.position
                    dx = int(float(metadata.get("dx", 0)))
                    dy = int(float(metadata.get("dy", 0)))
                    self._mouse.position = (current_x + dx, current_y + dy)
            elif message_type == "mouse_click":
                self._handle_mouse_click(metadata)
            elif message_type == "mouse_scroll":
                self._mouse.scroll(int(metadata.get("dx", 0)), int(metadata.get("dy", 0)))
            elif message_type == "key_press":
                self._handle_key_press(metadata)
            elif message_type == "key_release":
                self._handle_key_release(metadata)
            elif message_type == "text_input":
                self._keyboard.type(str(metadata.get("text", "")))
            else:
                self._log(f"Unsupported control event '{message_type}'.")
        except Exception as exc:  # pragma: no cover - depends on host input permissions
            self._log(f"Control event failed: {exc}")

    def _ensure_runtime(self) -> bool:
        if self._runtime_ready:
            return True
        if self._runtime_error is not None:
            return False
        try:
            mouse_module = importlib.import_module("pynput.mouse")
            keyboard_module = importlib.import_module("pynput.keyboard")
            self._mouse_module = mouse_module
            self._keyboard_module = keyboard_module
            self._mouse = mouse_module.Controller()
            self._keyboard = keyboard_module.Controller()
            self._runtime_ready = True
            if not is_running_as_admin() and not self._admin_hint_logged:
                self._admin_hint_logged = True
                self._log("Periflow is not running as Administrator. Mouse and keyboard control will not work inside elevated Windows apps.")
            return True
        except Exception as exc:
            self._runtime_error = str(exc)
            self._log(f"Control pipeline unavailable: {exc}")
            return False

    def _handle_mouse_click(self, metadata: dict) -> None:
        button_name = str(metadata.get("button", "left")).lower()
        button_map = {
            "left": self._mouse_module.Button.left,
            "right": self._mouse_module.Button.right,
            "middle": self._mouse_module.Button.middle,
        }
        button = button_map.get(button_name)
        if button is None:
            self._log(f"Unsupported mouse button '{button_name}'.")
            return

        action = str(metadata.get("action", "tap")).lower()
        if action == "down":
            self._mouse.press(button)
        elif action == "up":
            self._mouse.release(button)
        elif action == "double":
            self._mouse.click(button, 2)
        else:
            self._mouse.click(button)

    def _handle_key_press(self, metadata: dict) -> None:
        key = self._resolve_key(str(metadata["key"]))
        modifiers = [self._resolve_key(str(item)) for item in metadata.get("modifiers", [])]
        action = str(metadata.get("action", "tap")).lower()

        for modifier in modifiers:
            self._keyboard.press(modifier)
        if action == "down":
            self._keyboard.press(key)
            return
        if action == "up":
            self._keyboard.release(key)
            for modifier in reversed(modifiers):
                self._keyboard.release(modifier)
            return

        try:
            self._keyboard.press(key)
            self._keyboard.release(key)
        finally:
            for modifier in reversed(modifiers):
                self._keyboard.release(modifier)

    def _handle_key_release(self, metadata: dict) -> None:
        key = self._resolve_key(str(metadata["key"]))
        self._keyboard.release(key)
        for modifier in reversed(metadata.get("modifiers", [])):
            try:
                self._keyboard.release(self._resolve_key(str(modifier)))
            except Exception:
                pass

    def _resolve_key(self, value: str):
        value = value.lower()
        if len(value) == 1:
            return value
        key_name = NAMED_KEYS.get(value)
        if key_name is None:
            raise ValueError(f"Unknown key '{value}'")
        return getattr(self._keyboard_module.Key, key_name)
