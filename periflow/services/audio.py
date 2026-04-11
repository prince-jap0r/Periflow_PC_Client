from __future__ import annotations

import importlib
from typing import Callable

from ..models import AppSettings
from ._worker import DroppingWorker

VB_CABLE_KEYWORDS = (
    "cable input",
    "vb-audio virtual cable",
    "cable-a input",
    "cable-b input",
    "voiceemeeter input",
)


class AudioService:
    def __init__(self, log: Callable[[str], None]) -> None:
        self._log = log
        self._settings = AppSettings()
        self._audio = None
        self._stream = None
        self._stream_device_name = "unknown"
        self._runtime_ready = False
        self._runtime_error: str | None = None
        self._active_profile: tuple[int, int] | None = None
        self._worker: DroppingWorker[tuple[dict, bytes]] | None = None

    def update_settings(self, settings: AppSettings) -> None:
        old_profile = self._active_profile
        self._settings = settings
        new_profile = (
            self._settings.audio_profile["channels"],
            self._settings.audio_profile["sample_rate"],
        )
        if old_profile is not None and old_profile != new_profile:
            self._close_stream()

    def cleanup(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        self._close_stream()
        if self._audio is not None:
            try:
                self._audio.terminate()
            except Exception:
                pass
            finally:
                self._audio = None
        self._runtime_ready = False
        self._runtime_error = None

    def submit_frame(self, metadata: dict, body: bytes) -> None:
        if not self._settings.audio_enabled:
            return
        if not body:
            return
        self._ensure_worker()
        self._worker.submit((metadata.copy(), body))

    def _ensure_worker(self) -> None:
        if self._worker is None:
            self._worker = DroppingWorker("PeriflowAudio", self._process_frame, self._log, maxsize=32)

    def _process_frame(self, item: tuple[dict, bytes]) -> None:
        metadata, body = item
        audio_format = str(metadata.get("format", "pcm_s16le")).lower()
        if audio_format == "opus":
            self._log("Opus audio is not enabled in this build yet; send PCM frames for now.")
            return
        if audio_format not in {"pcm", "raw_pcm", "pcm_s16le"}:
            self._log(f"Unsupported audio format '{audio_format}'.")
            return

        if not self._ensure_runtime():
            return

        channels = int(metadata.get("channels", self._settings.audio_profile["channels"]))
        sample_rate = int(metadata.get("sample_rate", self._settings.audio_profile["sample_rate"]))
        if not self._ensure_stream(channels, sample_rate):
            return

        try:
            self._stream.write(body, exception_on_underflow=False)
        except TypeError:
            self._stream.write(body)
        except Exception as exc:  # pragma: no cover - depends on host audio stack
            self._log(f"Audio playback failed: {exc}")
            self._close_stream()

    def _ensure_runtime(self) -> bool:
        if self._runtime_ready:
            return True
        if self._runtime_error is not None:
            return False
        try:
            module = importlib.import_module("pyaudio")
            self._pyaudio = module
            self._audio = module.PyAudio()
            self._runtime_ready = True
            return True
        except Exception as exc:
            self._runtime_error = str(exc)
            self._log(f"Audio pipeline unavailable: {exc}")
            return False

    def _ensure_stream(self, channels: int, sample_rate: int) -> bool:
        profile = (channels, sample_rate)
        if self._stream is not None and self._active_profile == profile:
            return True
        if self._stream is not None:
            self._close_stream()

        device_index, device_name, opened_rate = self._choose_output_device(channels, sample_rate)
        try:
            self._stream = self._audio.open(
                format=self._pyaudio.paInt16,
                channels=channels,
                rate=opened_rate,
                output=True,
                output_device_index=device_index,
                frames_per_buffer=1024,
            )
            self._active_profile = (channels, opened_rate)
            self._stream_device_name = device_name
            self._log(f"Audio output ready on {device_name} ({channels} ch, {opened_rate} Hz).")
            return True
        except Exception as exc:  # pragma: no cover - depends on host audio stack
            self._log(
                f"Virtual audio output could not start on {device_name}. "
                f"Install VB-CABLE and check that the device supports {sample_rate} Hz. Details: {exc}"
            )
            self._stream = None
            self._active_profile = None
            return False

    def _choose_output_device(self, channels: int, sample_rate: int) -> tuple[int | None, str, int]:
        cable_candidate = self._find_virtual_audio_device(channels, sample_rate)
        if cable_candidate is not None:
            return cable_candidate

        default_index = None
        default_name = "default output device"
        try:
            default_info = self._audio.get_default_output_device_info()
            default_index = int(default_info["index"])
            default_name = str(default_info.get("name", default_name))
            default_rate = int(default_info.get("defaultSampleRate", sample_rate))
        except Exception:
            default_rate = sample_rate

        selected_rate = self._select_supported_rate(default_index, channels, sample_rate, default_rate)
        self._log("VB-CABLE device was not detected; falling back to the default output device.")
        return default_index, default_name, selected_rate

    def _find_virtual_audio_device(self, channels: int, sample_rate: int) -> tuple[int | None, str, int] | None:
        try:
            count = self._audio.get_device_count()
        except Exception:
            return None

        best_match: tuple[int | None, str, int] | None = None
        for index in range(count):
            try:
                info = self._audio.get_device_info_by_index(index)
            except Exception:
                continue

            if int(info.get("maxOutputChannels", 0)) < channels:
                continue

            name = str(info.get("name", ""))
            lowered = name.lower()
            if not any(keyword in lowered for keyword in VB_CABLE_KEYWORDS) and "cable" not in lowered and "vb-audio" not in lowered:
                continue

            default_rate = int(info.get("defaultSampleRate", sample_rate))
            selected_rate = self._select_supported_rate(index, channels, sample_rate, default_rate)
            best_match = (index, name, selected_rate)
            if any(keyword in lowered for keyword in VB_CABLE_KEYWORDS):
                break
        return best_match

    def _select_supported_rate(self, device_index: int | None, channels: int, preferred_rate: int, fallback_rate: int) -> int:
        if device_index is None:
            return preferred_rate

        for candidate in (preferred_rate, fallback_rate):
            try:
                self._audio.is_format_supported(
                    candidate,
                    output_device=device_index,
                    output_channels=channels,
                    output_format=self._pyaudio.paInt16,
                )
                return candidate
            except Exception:
                continue

        self._log(
            f"The selected audio device rejected {preferred_rate} Hz. Falling back to {fallback_rate} Hz for stability."
        )
        return fallback_rate

    def _close_stream(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.stop_stream()
            self._stream.close()
        except Exception:
            pass
        finally:
            self._stream = None
            self._active_profile = None
