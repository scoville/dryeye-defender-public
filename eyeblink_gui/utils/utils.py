"""Utils functions"""

import logging
import os
import sys
from typing import List

import cv2

LOGGER = logging.getLogger(__name__)


def find_data_file(filename: str) -> str:
    """Search where the file is, depending if the app is compiled(frozen) or not

    :param filename: name of the file to find
    :return: path to the file
    """
    if getattr(sys, "frozen", False):
        # The application is frozen(binary file)
        # datadir = os.path.dirname("/usr/share/eyeblinkgui/")
        datadir = os.path.join(os.path.dirname(sys.executable), "assets/")
    else:
        # The application is not frozen (python mode)
        # where we store your data files:
        datadir = os.path.dirname("submodules/eyeblink-detection/assets/")
    return os.path.join(datadir, filename)


def get_cap_indexes() -> List[str]:
    """Test the ports and returns a tuple with the available ports and the ones that are working.

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
