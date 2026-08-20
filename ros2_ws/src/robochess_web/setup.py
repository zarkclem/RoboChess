from pathlib import Path

from setuptools import find_packages, setup

package_name = "robochess_web"
static_dir = Path("robochess_web/static/calibration")
static_files = [str(p) for p in static_dir.glob("*") if p.is_file()]

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
        (f"share/{package_name}", ["package.xml"]),
        (f"share/{package_name}/static/calibration", static_files),
    ],
    install_requires=["setuptools", "fastapi", "uvicorn", "pyyaml"],
    zip_safe=True,
    maintainer="zarkclem",
    maintainer_email="clement.jaguenaud@edu.ece.fr",
    description="Backend FastAPI et UI web (calibration, puis suivi de partie) pour RoboChess.",
    license="TODO",
    tests_require=["pytest", "httpx"],
    entry_points={
        "console_scripts": [
            "robochess_web_server = robochess_web.app:main",
        ],
    },
)
