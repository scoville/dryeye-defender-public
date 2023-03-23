"""Utils functions"""


from typing import List, Any
import cv2


def get_cap_indexes() -> List[Any]:
    """Find all camera available

    :return: List of all cap device available
    """
    available_cap = []
    for index in range(10):
        cap = cv2.VideoCapture(index)
        if cap.read()[0]:
            available_cap.append(str(index))
        cap.release()
    print(available_cap)
    return available_cap
