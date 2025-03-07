"""Utils functions"""
from pathlib import Path
import logging
import os
import sys
from typing import List, Any

import cv2

LOGGER = logging.getLogger(__name__)


def find_data_file(filename: str, submodule: bool = False) -> str:
    """Search where the file is, depending if the app is compiled(frozen) or not

    :param filename: name of the file to find
    :param submodule: if True and not frozen binary,
      the assets are searched for in the submodule folder
    :return: path to the file
    """
    if getattr(sys, "frozen", False):
        # The application is frozen(binary file)
        if sys.platform == "darwin":
            datadir = os.path.join(os.path.dirname(sys.executable), "../Resources/assets/")
        else:
            datadir = os.path.join(os.path.dirname(sys.executable), "assets/")
    else:
        # The application is not frozen (python mode)
        # where we store your data files:
        if submodule:
            datadir = os.path.join(os.path.dirname(__file__),
                                   "../../submodules/blink-detection/assets/")
        else:
            datadir = os.path.join(os.path.dirname(__file__),
                                   "../../assets/")
    path = os.path.join(datadir, filename)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File {filename} not found in {datadir}")
    return path


def get_saved_data_path() -> Path:
    """Get the path where the data is saved.
    If running os.environ["CI_TESTS"] then simply return "/tmp/saved_blink.db"

    :return: path to where to save the database
    """
    if os.environ.get("CI_TESTS", False):
        LOGGER.info("Database path: %s", "/tmp/saved_blink.db")
        return Path("/tmp/saved_blink.db")

    if getattr(sys, "frozen", False):
        # The application is frozen(binary file)

        app_name = "dryeye_defender"

        if os.name == "nt":  # Windows
            # appdata_path = Path(os.getenv("LOCALAPPDATA"))
            appdata_path = os.getenv("APPDATA")
            assert appdata_path is not None
            saved_data_dir = Path(appdata_path) / app_name
        elif os.name == "posix":  # Linux or macOS
            if "darwin" in sys.platform:  # macOS
                saved_data_dir = Path.home() / "Library" / "Application Support" / app_name
            else:  # Assume Linux
                saved_data_dir = Path.home() / ".local" / "share" / app_name

    else:
        # The application is not frozen (python mode)
        # where we store your data files:
        saved_data_dir = Path(__file__).parent.parent.parent / "saved_data"

    saved_data_dir.mkdir(parents=True, exist_ok=True)
    database_path = saved_data_dir / "saved_blink.db"
    LOGGER.info("Database path: %s", database_path)
    return database_path


def get_cap_indexes() -> List[str]:
    """Test the ports and returns a tuple with the available ports and the ones that are working.

    TODO: Use device names:
    https://abhitronix.github.io/deffcode/v0.2.5-stable/recipes/basic/decode-camera-devices/

    :return: List of indexes that are available for reading, in str format
    """
    # non_working_ports = []
    dev_port = 0
    working_ports: List[str] = []
    # available_ports = []
    for dev_port in range(6):  # if there are more than 5 non working ports stop the testing.
        camera = cv2.VideoCapture(dev_port)  # pylint: disable=no-member
        if not camera.isOpened():
            # non_working_ports.append(dev_port)
            LOGGER.info("Port %s is not working.", dev_port)
        else:
            is_reading, _ = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                LOGGER.info("Port %s is working and reads images (%s x %s)", dev_port, h, w)
                working_ports.append(str(dev_port))
            else:
                LOGGER.info("Port %s for camera ( %s x %s) is present but does not reads.")
                # available_ports.append(dev_port)
    return working_ports


def update_font(instance_self: Any,
                font_family: str = "AvenirNext LT Pro Bold",
                font_size: int = 15) -> None:
    """
    Update the font of the instance_self to the font_family and font_size.

    :param instance_self: instance of a class that has a self.font() method
    :param font_family: name of the font family, e.g. Avenir Next LT Pro
    :param font_size: size of the font
    """
    font = instance_self.font()
    font.setPixelSize(font_size)
    LOGGER.info("Setting default MainWindow font: %s", font_family)
    font.setFamily(font_family)
    instance_self.setFont(font)
