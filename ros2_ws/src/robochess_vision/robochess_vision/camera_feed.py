"""Pure image handling for the live camera feed exposed at /camera/live.

Kept free of any ROS2/rclpy dependency (mirrors grid_mapping.py — research.md
§5): frame decoding/encoding is unit-testable without a real ZED camera.
CalibrationNode stays the only place that touches rclpy/sensor_msgs directly,
per Principe III (un seul point d'accès au périphérique caméra).
"""

from __future__ import annotations

import threading
from typing import Optional

import cv2
import numpy as np

_CHANNELS_BY_ENCODING = {
    "bgra8": 4,
    "rgba8": 4,
    "bgr8": 3,
    "rgb8": 3,
    "mono8": 1,
}


class UnsupportedEncodingError(ValueError):
    """Raised when the camera publishes a pixel encoding we don't decode."""


def image_to_jpeg(width: int, height: int, step: int, encoding: str, data: bytes, quality: int = 85) -> bytes:
    channels = _CHANNELS_BY_ENCODING.get(encoding)
    if channels is None:
        raise UnsupportedEncodingError(f"Encodage image non supporté : {encoding}")

    # step may include row padding beyond width*channels bytes — slice it off before reshaping.
    frame = np.frombuffer(data, dtype=np.uint8).reshape(height, step)
    frame = frame[:, : width * channels].reshape(height, width, channels)

    if encoding == "rgba8":
        frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)
    elif encoding == "bgra8":
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    elif encoding == "rgb8":
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
    if not ok:
        raise RuntimeError("Échec de l'encodage JPEG.")
    return buffer.tobytes()


class LiveFrameBuffer:
    """Thread-safe latest-frame cache.

    Written from the ROS spin thread's image callback, read from FastAPI's
    MJPEG generator — same in-process-thread handoff as CalibrationState
    (research.md §4).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._latest_jpeg: Optional[bytes] = None

    def on_image_message(self, width: int, height: int, step: int, encoding: str, data: bytes) -> None:
        try:
            jpeg = image_to_jpeg(width, height, step, encoding, data)
        except (UnsupportedEncodingError, RuntimeError):
            return
        with self._lock:
            self._latest_jpeg = jpeg

    def latest_jpeg(self) -> Optional[bytes]:
        with self._lock:
            return self._latest_jpeg
