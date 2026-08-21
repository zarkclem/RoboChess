"""FastAPI application entrypoint for the calibration UI/backend."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Optional

import rclpy
from ament_index_python.packages import get_package_share_directory
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from robochess_vision.calibration_node import CalibrationNode

from .routers import calibration, camera

STATIC_DIR = Path(get_package_share_directory("robochess_web")) / "static"

app = FastAPI(title="RoboChess - Calibration")
app.include_router(calibration.router, prefix="/api/calibration", tags=["calibration"])
app.include_router(camera.router, tags=["camera"])
app.mount(
    "/calibration",
    StaticFiles(directory=STATIC_DIR / "calibration", html=True),
    name="calibration-ui",
)

_ros_thread: Optional[threading.Thread] = None
_node: Optional[CalibrationNode] = None


@app.on_event("startup")
def start_calibration_node() -> None:
    global _ros_thread, _node
    rclpy.init()
    _node = CalibrationNode()
    calibration.set_backend(_node.state)
    camera.set_backend(_node.camera_feed)
    _ros_thread = threading.Thread(target=rclpy.spin, args=(_node,), daemon=True)
    _ros_thread.start()


@app.on_event("shutdown")
def stop_calibration_node() -> None:
    # Principe III : libérer proprement les ressources ROS2 à l'arrêt.
    if _node is not None:
        _node.destroy_node()
    rclpy.shutdown()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
