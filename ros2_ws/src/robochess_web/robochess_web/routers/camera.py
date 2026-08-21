"""HTTP endpoint serving the live camera feed as MJPEG for the calibration UI.

/camera/live is what index.html's <img> tag points to — browsers render a
multipart/x-mixed-replace stream natively in an <img>, so no extra JS/WebRTC
plumbing is needed on the frontend.
"""

from __future__ import annotations

import time
from typing import Iterator, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from robochess_vision.camera_feed import LiveFrameBuffer

router = APIRouter()

_backend: Optional[LiveFrameBuffer] = None

_BOUNDARY = b"frame"
_POLL_INTERVAL_S = 1 / 15


def set_backend(backend: LiveFrameBuffer) -> None:
    global _backend
    _backend = backend


def _require_backend() -> LiveFrameBuffer:
    if _backend is None:
        # FR-011 : ne jamais laisser un <img> cassé sans explication.
        raise HTTPException(
            status_code=503,
            detail={"error": "camera_unavailable", "message": "Backend caméra non initialisé."},
        )
    return _backend


def _mjpeg_frames(backend: LiveFrameBuffer) -> Iterator[bytes]:
    last_sent: Optional[bytes] = None
    while True:
        jpeg = backend.latest_jpeg()
        if jpeg is not None and jpeg is not last_sent:
            last_sent = jpeg
            yield (
                b"--" + _BOUNDARY + b"\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n"
            )
        time.sleep(_POLL_INTERVAL_S)


@router.get("/camera/live")
def live_feed():
    backend = _require_backend()
    if backend.latest_jpeg() is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "camera_unavailable",
                "message": "Aucune image reçue de la caméra pour le moment.",
            },
        )
    return StreamingResponse(
        _mjpeg_frames(backend),
        media_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY.decode()}",
    )
