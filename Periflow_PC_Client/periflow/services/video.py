from __future__ import annotations

import importlib
import io
from typing import Callable

from ..models import AppSettings
from ._worker import DroppingWorker


class VideoService:
    def __init__(self, log: Callable[[str], None]) -> None:
        self._log = log
        self._settings = AppSettings()
        self._camera = None
        self._camera_config: tuple[int, int, int] | None = None
        self._runtime_ready = False
        self._runtime_error: str | None = None
        self._pixel_format = None
        self._worker: DroppingWorker[tuple[dict, bytes]] | None = None

    def update_settings(self, settings: AppSettings) -> None:
        camera_changed = self._camera is not None and self._settings.video_size != settings.video_size
        self._settings = settings
        if camera_changed:
            self._close_camera()

    def cleanup(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        self._close_camera()

    def submit_frame(self, metadata: dict, body: bytes) -> None:
        if not self._settings.video_enabled:
            return
        if not body:
            return
        self._ensure_worker()
        self._worker.submit((metadata.copy(), body))

    def _ensure_worker(self) -> None:
        if self._worker is None:
            self._worker = DroppingWorker("PeriflowVideo", self._process_frame, self._log, maxsize=2)

    def _process_frame(self, item: tuple[dict, bytes]) -> None:
        metadata, body = item
        frame_format = str(metadata.get("format", "jpeg")).lower()
        if frame_format in {"h264", "avc"}:
            self._log("H.264 decoding is not enabled in this build yet; send JPEG frames for now.")
            return

        if not self._ensure_runtime():
            return

        frame = self._decode_frame(frame_format, metadata, body)
        if frame is None:
            self._log(f"Unable to decode video frame with format '{frame_format}'.")
            return

        cv2 = self._cv2
        target_width, target_height = self._settings.video_size
        if frame.shape[1] != target_width or frame.shape[0] != target_height:
            frame = cv2.resize(frame, (target_width, target_height))
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        fps = int(metadata.get("fps", self._settings.fps))
        if not self._ensure_camera(target_width, target_height, fps):
            return

        try:
            self._camera.send(rgb_frame)
            self._camera.sleep_until_next_frame()
        except Exception as exc:  # pragma: no cover - depends on host camera driver
            self._log(f"Virtual camera send failed: {exc}")
            self._close_camera()

    def _ensure_runtime(self) -> bool:
        if self._runtime_ready:
            return True
        if self._runtime_error is not None:
            return False
        try:
            self._np = importlib.import_module("numpy")
            self._cv2 = importlib.import_module("cv2")
            pyvirtualcam = importlib.import_module("pyvirtualcam")
            self._virtualcam_cls = pyvirtualcam.Camera
            self._pixel_format = getattr(getattr(pyvirtualcam, "PixelFormat", None), "RGB", None)
            self._runtime_ready = True
            return True
        except Exception as exc:
            self._runtime_error = str(exc)
            self._log(f"Video pipeline unavailable: {exc}")
            return False

    def _decode_frame(self, frame_format: str, metadata: dict, body: bytes):
        cv2 = self._cv2
        if frame_format in {"jpeg", "jpg", "png"}:
            data = self._np.frombuffer(body, dtype=self._np.uint8)
            return cv2.imdecode(data, cv2.IMREAD_COLOR)

        width = int(metadata.get("width", self._settings.video_size[0]))
        height = int(metadata.get("height", self._settings.video_size[1]))
        if frame_format in {"rgb", "raw"}:
            expected = width * height * 3
            if len(body) != expected:
                return None
            frame = self._np.frombuffer(body, dtype=self._np.uint8).reshape((height, width, 3))
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if frame_format == "bgr":
            expected = width * height * 3
            if len(body) != expected:
                return None
            return self._np.frombuffer(body, dtype=self._np.uint8).reshape((height, width, 3))

        if frame_format == "pil_jpeg":
            try:
                pillow = importlib.import_module("PIL.Image")
                image = pillow.open(io.BytesIO(body)).convert("RGB")
                frame = self._np.array(image)
                return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            except Exception:
                return None

        return None

    def _ensure_camera(self, width: int, height: int, fps: int) -> bool:
        config = (width, height, fps)
        if self._camera is not None and self._camera_config == config:
            return True
        if self._camera is not None:
            self._close_camera()

        launch_attempts = [
            {"width": width, "height": height, "fps": fps, "backend": "obs"},
            {"width": width, "height": height, "fps": fps},
        ]

        for kwargs in launch_attempts:
            if self._pixel_format is not None:
                kwargs["fmt"] = self._pixel_format
            try:
                self._camera = self._virtualcam_cls(**kwargs)
                self._camera_config = config
                backend_label = kwargs.get("backend", "default")
                self._log(f"Virtual camera ready at {width}x{height} @{fps}fps using {backend_label} backend.")
                return True
            except Exception:
                self._camera = None

        self._camera_config = None
        self._log("Virtual camera could not start. Install OBS Virtual Camera first, then restart Periflow.")
        return False

    def _close_camera(self) -> None:
        if self._camera is None:
            return
        try:
            self._camera.close()
        except Exception:
            pass
        finally:
            self._camera = None
            self._camera_config = None
