from setuptools import find_packages, setup

package_name = "robochess_vision"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/launch", ["launch/calibration.launch.py"]),
        (f"share/{package_name}/config", ["config/zed_params_override.yaml"]),
    ],
    install_requires=["setuptools", "opencv-python", "pyyaml"],
    zip_safe=True,
    maintainer="zarkclem",
    maintainer_email="clement.jaguenaud@edu.ece.fr",
    description="Calibration du plateau et accès caméra/profondeur pour RoboChess.",
    license="TODO",
    tests_require=["pytest"],
    entry_points={
        "console_scripts": [
            "calibration_node = robochess_vision.calibration_node:main",
        ],
    },
)
