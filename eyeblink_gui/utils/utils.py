"""Utils functions"""

from typing import List

import cv2


def get_cap_indexes() -> List[str]:
    """Test the ports and returns a tuple with the available ports and the ones that are working."""
    # non_working_ports = []
    dev_port = 0
    working_ports: List[str] = []
    # available_ports = []
    for dev_port in range(6):  # if there are more than 5 non working ports stop the testing.
        camera = cv2.VideoCapture(dev_port)
        if not camera.isOpened():
            # non_working_ports.append(dev_port)
            print(f"Port {dev_port} is not working.")
        else:
            is_reading, _ = camera.read()
            w = camera.get(3)
            h = camera.get(4)
            if is_reading:
                print(f"Port {dev_port} is working and reads images ({h} x {w})")
                working_ports.append(str(dev_port))
            else:
                print(f"Port {dev_port} for camera ( {h} x {w}) is present but does not reads.")
                # available_ports.append(dev_port)
    return working_ports
