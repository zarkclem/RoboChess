"""ROS2 node wrapper around CalibrationState.

Spun in-process inside robochess_web's FastAPI server (background thread —
see app.py) rather than reached as a separate node over ROS2 services:
research.md §4 leaves both options open ("un client ROS 2 minimal ... ou
dans un thread dédié"), and a same-process thread avoids inventing custom
.srv interfaces that were never specified in this feature's contracts. It
stays a real rclpy Node so it joins the project's dedicated ROS_DOMAIN_ID
and can be extended with camera/depth topics later without restructuring.
"""

from __future__ import annotations

from typing import Optional

from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image

from .calibration_state import CalibrationState
from .camera_feed import LiveFrameBuffer

# Topic par défaut de zed-ros2-wrapper pour camera_name='zed', node_name='zed_node'
# (zed_camera.launch.py) — voir calibration.launch.py qui lance le node avec ces valeurs.
RGB_IMAGE_TOPIC = "/zed/zed_node/rgb/color/rect/image"


class CalibrationNode(Node):
    def __init__(self, state: Optional[CalibrationState] = None) -> None:
        super().__init__("robochess_calibration_node")
        self.state = state or CalibrationState()
        self.camera_feed = LiveFrameBuffer()
        self._image_sub = self.create_subscription(
            Image, RGB_IMAGE_TOPIC, self._on_image, qos_profile_sensor_data
        )

    def _on_image(self, msg: Image) -> None:
        self.camera_feed.on_image_message(msg.width, msg.height, msg.step, msg.encoding, bytes(msg.data))


def main(args: Optional[list] = None) -> None:
    import rclpy

    rclpy.init(args=args)
    node = CalibrationNode()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
