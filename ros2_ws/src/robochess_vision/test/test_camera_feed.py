import numpy as np
import pytest

from robochess_vision.camera_feed import LiveFrameBuffer, UnsupportedEncodingError, image_to_jpeg


def _solid_frame(width: int, height: int, channels: int, value: int = 128) -> bytes:
    return np.full((height, width, channels), value, dtype=np.uint8).tobytes()


def test_image_to_jpeg_decodes_bgra8_without_padding():
    width, height = 8, 4
    data = _solid_frame(width, height, 4)
    jpeg = image_to_jpeg(width, height, step=width * 4, encoding="bgra8", data=data)
    assert jpeg[:2] == b"\xff\xd8"  # JPEG magic bytes


def test_image_to_jpeg_strips_row_padding_from_step():
    width, height, channels = 4, 3, 3
    padded_step = width * channels + 8  # simulate alignment padding beyond the pixel row
    rows = [bytes([value] * padded_step) for value in range(height)]
    data = b"".join(rows)
    jpeg = image_to_jpeg(width, height, step=padded_step, encoding="bgr8", data=data)
    assert jpeg[:2] == b"\xff\xd8"


def test_image_to_jpeg_rejects_unsupported_encoding():
    with pytest.raises(UnsupportedEncodingError):
        image_to_jpeg(4, 4, step=16, encoding="yuv422", data=b"\x00" * 64)


def test_live_frame_buffer_starts_empty():
    buffer = LiveFrameBuffer()
    assert buffer.latest_jpeg() is None


def test_live_frame_buffer_stores_decoded_frame():
    buffer = LiveFrameBuffer()
    width, height = 4, 4
    buffer.on_image_message(width, height, width * 3, "bgr8", _solid_frame(width, height, 3))
    jpeg = buffer.latest_jpeg()
    assert jpeg is not None
    assert jpeg[:2] == b"\xff\xd8"


def test_live_frame_buffer_ignores_unsupported_encoding_and_keeps_previous_frame():
    buffer = LiveFrameBuffer()
    width, height = 4, 4
    buffer.on_image_message(width, height, width * 3, "bgr8", _solid_frame(width, height, 3))
    first = buffer.latest_jpeg()
    buffer.on_image_message(width, height, width * 2, "yuv422", b"\x00" * (width * height * 2))
    assert buffer.latest_jpeg() == first
