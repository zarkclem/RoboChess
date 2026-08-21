"""Lance le serveur de calibration RoboChess.

robochess_web_server exécute en interne le node ROS2 de calibration
(calibration_node.py) dans un thread dédié — un seul point d'entrée pour
respecter le Principe III (lancement manuel, arrêt propre) : Ctrl+C arrête
ce launch file et libère la caméra.

Inclut aussi zed_wrapper (camera_model=zedx) : c'est lui qui publie le topic
image que calibration_node.py consomme (RGB_IMAGE_TOPIC). publish_urdf/
publish_tf sont désactivés — la calibration n'a besoin que de l'image, pas de
robot_state_publisher/TF, ce qui évite une dépendance supplémentaire. Pour la
même raison, depth.depth_mode='NONE' est appliqué via zed_params_override.yaml :
la profondeur (et le positional tracking qu'elle force sinon) n'est pas
nécessaire ici, et le pos tracking par défaut bloquerait le démarrage du node
en attendant un TF qu'on ne publie jamais.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    params_override_path = os.path.join(
        get_package_share_directory("robochess_vision"), "config", "zed_params_override.yaml"
    )
    zed_wrapper_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory("zed_wrapper"), "launch", "zed_camera.launch.py"
            )
        ),
        launch_arguments={
            "camera_model": "zedx",
            "publish_urdf": "false",
            "publish_tf": "false",
            "ros_params_override_path": params_override_path,
        }.items(),
    )

    return LaunchDescription(
        [
            zed_wrapper_launch,
            Node(
                package="robochess_web",
                executable="robochess_web_server",
                name="robochess_web_server",
                output="screen",
            ),
        ]
    )
