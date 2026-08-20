"""Pure geometry: derive the 64-square grid from the 4 clicked board corners.

No ROS2/hardware dependency on purpose (research.md §5) so this stays
unit-testable in any Python environment, including outside the Jetson.
"""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

BOARD_FILES = "abcdefgh"
BOARD_SIZE = 8
DEPTH_REGION_SHRINK = 0.5
MIN_QUAD_AREA_PX = 400.0


class DegenerateQuadrilateralError(ValueError):
    """Raised when the 4 clicked corners do not form a usable quadrilateral (FR-006)."""


@dataclass(frozen=True)
class Square:
    id: str
    image_region: list[tuple[float, float]]
    depth_region: list[tuple[float, float]]


def compute_grid(corners: dict[str, tuple[float, float]]) -> list[Square]:
    """Derive the 64 squares of a chessboard from its 4 internal grid corners.

    `corners` must map "a1", "h1", "a8", "h8" to pixel coordinates in the
    source image. No assumption is made about board size, color or border
    width (Constitution Principle I) — the mapping is purely geometric,
    via a perspective transform so an oblique camera angle is supported.
    """
    required = {"a1", "h1", "a8", "h8"}
    missing = required - corners.keys()
    if missing:
        raise ValueError(f"Missing corner(s): {sorted(missing)}")

    _validate_quadrilateral(corners)

    src = np.float32([[0, 0], [BOARD_SIZE, 0], [0, BOARD_SIZE], [BOARD_SIZE, BOARD_SIZE]])
    dst = np.float32([corners["a1"], corners["h1"], corners["a8"], corners["h8"]])
    grid_to_image = cv2.getPerspectiveTransform(src, dst)

    squares: list[Square] = []
    for rank in range(BOARD_SIZE):
        for file_idx in range(BOARD_SIZE):
            square_id = f"{BOARD_FILES[file_idx]}{rank + 1}"
            grid_quad = np.float32(
                [
                    [file_idx, rank],
                    [file_idx + 1, rank],
                    [file_idx + 1, rank + 1],
                    [file_idx, rank + 1],
                ]
            )
            image_quad = _project(grid_quad, grid_to_image)
            squares.append(
                Square(
                    id=square_id,
                    image_region=_to_point_list(image_quad),
                    depth_region=_to_point_list(_shrink_quad(image_quad, DEPTH_REGION_SHRINK)),
                )
            )
    return squares


def _to_point_list(quad: np.ndarray) -> list[tuple[float, float]]:
    # cv2/numpy keep coordinates as numpy.float32 scalars, which FastAPI's
    # JSON encoder cannot serialize — cast down to plain Python floats.
    return [(float(x), float(y)) for x, y in quad]


def _project(points: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    projected = cv2.perspectiveTransform(points.reshape(-1, 1, 2), matrix)
    return projected.reshape(-1, 2)


def _shrink_quad(quad: np.ndarray, factor: float) -> np.ndarray:
    centroid = quad.mean(axis=0)
    return centroid + (quad - centroid) * factor


def _validate_quadrilateral(corners: dict[str, tuple[float, float]]) -> None:
    # Perimeter order (a1 -> h1 -> h8 -> a8) so contourArea sees a simple polygon.
    ordered = np.float32([corners["a1"], corners["h1"], corners["h8"], corners["a8"]])
    area = abs(cv2.contourArea(ordered))
    if area < MIN_QUAD_AREA_PX:
        raise DegenerateQuadrilateralError(
            "Les 4 points sont trop proches ou quasi alignés pour former un quadrilatère exploitable."
        )
