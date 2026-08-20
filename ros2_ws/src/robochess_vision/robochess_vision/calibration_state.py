"""In-memory + persisted state machine for the active board calibration.

Kept free of any ROS2/rclpy dependency (unlike calibration_node.py, which
just wraps this in a Node) so it can be unit-tested and driven directly by
robochess_web's router without spinning a real ROS2 node — research.md §5.
Implements the operations described in contracts/calibration-api.md.
"""

from __future__ import annotations

import datetime
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import yaml

from .grid_mapping import Square, compute_grid

CORNER_ORDER = ("a1", "h1", "a8", "h8")
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "calibration.yaml"


class CalibrationIncompleteError(ValueError):
    """Raised by `confirm()` when fewer than 4 points have been collected."""


@dataclass
class ConfirmedCalibration:
    created_at: str
    corner_points: dict[str, tuple[float, float]]
    squares: list[Square]

    def to_status(self) -> dict:
        return {"status": "confirmed", "created_at": self.created_at}


class CalibrationState:
    def __init__(self, config_path: Path = DEFAULT_CONFIG_PATH) -> None:
        self._config_path = config_path
        self._draft_points: dict[str, tuple[float, float]] = {}
        self._confirmed: Optional[ConfirmedCalibration] = None
        self._load_persisted()

    def status(self) -> dict:
        if self._confirmed is None:
            return {"status": "none"}
        return self._confirmed.to_status()

    def start_draft(self) -> dict:
        # Never touches self._confirmed: the previous calibration stays active
        # until a new one is confirmed (FR-010, US2).
        self._draft_points = {}
        return {"status": "draft", "next_corner": CORNER_ORDER[0]}

    def add_point(self, x: float, y: float) -> dict:
        next_corner = self._next_corner()
        if next_corner is None:
            raise CalibrationIncompleteError("Aucun coin en attente ; démarrez une nouvelle calibration.")

        candidate_points = {**self._draft_points, next_corner: (x, y)}

        if len(candidate_points) == len(CORNER_ORDER):
            # Validate before committing the 4th point: a rejected click can
            # simply be retried (recliquer le même coin) instead of forcing a
            # full /start reset.
            preview_squares = compute_grid(candidate_points)
            self._draft_points = candidate_points
            return {
                "status": "draft",
                "next_corner": None,
                "points_collected": list(self._draft_points.keys()),
                "preview_grid": [asdict(sq) for sq in preview_squares],
            }

        self._draft_points = candidate_points
        return {
            "status": "draft",
            "next_corner": self._next_corner(),
            "points_collected": list(self._draft_points.keys()),
        }

    def confirm(self) -> dict:
        if len(self._draft_points) != len(CORNER_ORDER):
            raise CalibrationIncompleteError("4 points requis avant confirmation.")

        squares = compute_grid(self._draft_points)
        self._confirmed = ConfirmedCalibration(
            created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            corner_points=dict(self._draft_points),
            squares=squares,
        )
        self._draft_points = {}
        self._persist()
        return self._confirmed.to_status()

    def discard(self) -> dict:
        self._draft_points = {}
        return self.status()

    def _next_corner(self) -> Optional[str]:
        for corner in CORNER_ORDER:
            if corner not in self._draft_points:
                return corner
        return None

    def _persist(self) -> None:
        if self._confirmed is None:
            return
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": self._confirmed.created_at,
            "corner_points": {k: list(v) for k, v in self._confirmed.corner_points.items()},
            "squares": [
                {
                    "id": sq.id,
                    "image_region": [list(p) for p in sq.image_region],
                    "depth_region": [list(p) for p in sq.depth_region],
                }
                for sq in self._confirmed.squares
            ],
        }
        self._config_path.write_text(yaml.safe_dump(payload, sort_keys=False))

    def _load_persisted(self) -> None:
        if not self._config_path.exists():
            return
        payload = yaml.safe_load(self._config_path.read_text())
        if not payload:
            return
        squares = [
            Square(
                id=sq["id"],
                image_region=[tuple(p) for p in sq["image_region"]],
                depth_region=[tuple(p) for p in sq["depth_region"]],
            )
            for sq in payload["squares"]
        ]
        self._confirmed = ConfirmedCalibration(
            created_at=payload["created_at"],
            corner_points={k: tuple(v) for k, v in payload["corner_points"].items()},
            squares=squares,
        )
