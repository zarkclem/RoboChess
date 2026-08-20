"""HTTP endpoints for board calibration — see contracts/calibration-api.md."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from robochess_vision.calibration_state import CalibrationIncompleteError, CalibrationState
from robochess_vision.grid_mapping import DegenerateQuadrilateralError

router = APIRouter()

_backend: Optional[CalibrationState] = None


def set_backend(backend: CalibrationState) -> None:
    global _backend
    _backend = backend


def get_backend() -> Optional[CalibrationState]:
    return _backend


def _require_backend() -> CalibrationState:
    if _backend is None:
        # FR-011: never silently proceed without a working calibration backend.
        raise HTTPException(
            status_code=503,
            detail={"error": "camera_unavailable", "message": "Backend de calibration non initialisé."},
        )
    return _backend


class PointRequest(BaseModel):
    x: float
    y: float


@router.get("/status")
def get_status():
    return _require_backend().status()


@router.post("/start")
def start_calibration():
    return _require_backend().start_draft()


@router.post("/point")
def submit_point(point: PointRequest):
    try:
        return _require_backend().add_point(point.x, point.y)
    except DegenerateQuadrilateralError as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "degenerate_quadrilateral", "message": str(exc)},
        ) from exc
    except CalibrationIncompleteError as exc:
        raise HTTPException(status_code=409, detail={"error": "incomplete", "message": str(exc)}) from exc


@router.post("/confirm")
def confirm_calibration():
    try:
        return _require_backend().confirm()
    except CalibrationIncompleteError as exc:
        raise HTTPException(status_code=409, detail={"error": "incomplete", "message": str(exc)}) from exc


@router.post("/discard")
def discard_calibration():
    return _require_backend().discard()
