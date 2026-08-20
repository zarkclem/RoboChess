"""Lance le serveur de calibration RoboChess.

robochess_web_server exécute en interne le node ROS2 de calibration
(calibration_node.py) dans un thread dédié — un seul point d'entrée pour
respecter le Principe III (lancement manuel, arrêt propre) : Ctrl+C arrête
ce launch file et libère la caméra.
"""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    return LaunchDescription(
        [
            Node(
                package="robochess_web",
                executable="robochess_web_server",
                name="robochess_web_server",
                output="screen",
            ),
        ]
    )
