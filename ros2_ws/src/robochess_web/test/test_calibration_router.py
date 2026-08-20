"""Contract tests for the calibration HTTP API (contracts/calibration-api.md)."""

import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from robochess_vision.calibration_state import CalibrationState
from robochess_web.routers import calibration

VALID_CLICKS = {
    "a1": (100.0, 500.0),
    "h1": (500.0, 500.0),
    "a8": (100.0, 100.0),
    "h8": (500.0, 100.0),
}


def make_client() -> TestClient:
    config_path = Path(tempfile.mkdtemp()) / "calibration.yaml"
    calibration.set_backend(CalibrationState(config_path=config_path))
    app = FastAPI()
    app.include_router(calibration.router, prefix="/api/calibration")
    return TestClient(app)


def test_status_is_none_before_any_calibration():
    client = make_client()
    response = client.get("/api/calibration/status")
    assert response.status_code == 200
    assert response.json() == {"status": "none"}


def test_full_calibration_flow_confirms_successfully():
    client = make_client()
    assert client.post("/api/calibration/start").json()["next_corner"] == "a1"

    last_response = None
    for x, y in VALID_CLICKS.values():
        last_response = client.post("/api/calibration/point", json={"x": x, "y": y})
        assert last_response.status_code == 200
    assert last_response.json()["preview_grid"] is not None

    confirm_response = client.post("/api/calibration/confirm")
    assert confirm_response.status_code == 200
    assert confirm_response.json()["status"] == "confirmed"

    status_response = client.get("/api/calibration/status")
    assert status_response.json()["status"] == "confirmed"


def test_confirm_without_four_points_returns_409():
    client = make_client()
    client.post("/api/calibration/start")
    client.post("/api/calibration/point", json={"x": 100.0, "y": 500.0})

    response = client.post("/api/calibration/confirm")
    assert response.status_code == 409
    assert response.json()["detail"]["error"] == "incomplete"


def test_degenerate_points_are_rejected_with_422():
    client = make_client()
    client.post("/api/calibration/start")
    degenerate = {"a1": (100.0, 100.0), "h1": (101.0, 100.0), "a8": (100.0, 101.0), "h8": (101.0, 101.0)}
    response = None
    for x, y in degenerate.values():
        response = client.post("/api/calibration/point", json={"x": x, "y": y})

    assert response.status_code == 422
    assert response.json()["detail"]["error"] == "degenerate_quadrilateral"


def test_recalibration_keeps_previous_confirmed_until_new_confirm():
    client = make_client()
    client.post("/api/calibration/start")
    for x, y in VALID_CLICKS.values():
        client.post("/api/calibration/point", json={"x": x, "y": y})
    first = client.post("/api/calibration/confirm").json()

    client.post("/api/calibration/start")
    still_active = client.get("/api/calibration/status").json()
    assert still_active == first  # US2 / FR-010: unaffected until the new draft confirms

    for x, y in VALID_CLICKS.values():
        client.post("/api/calibration/point", json={"x": x + 10, "y": y + 10})
    second = client.post("/api/calibration/confirm").json()
    assert second["created_at"] != first["created_at"]


def test_status_without_backend_returns_503():
    calibration.set_backend(None)
    app = FastAPI()
    app.include_router(calibration.router, prefix="/api/calibration")
    client = TestClient(app)

    response = client.get("/api/calibration/status")
    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "camera_unavailable"
