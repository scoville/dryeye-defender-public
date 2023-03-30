"""Utils function"""
import logging
import time
from typing import List, Tuple

LOGGER = logging.getLogger(__name__)


def lack_of_blink_detection(blink_history: List[Tuple[float, int]], duration_lack: int) -> bool:
    """Check if there is a lack of blink from the history

    :param blink_history: List of blink value(1 if detected blink, else -1) associated with time
    :param duration_lack: minimum duration for considering lack of blink

    :return: true if no blink for the last ?? second (=> lack of blink)
    """
    current_time = time.time()

    for time_code, blink_value in reversed(blink_history):
        # search for the last detected blink
        if blink_value == 1:  # blink detected
            since_last_blink_duration = current_time - time_code  # how long ago was the last blink

            if since_last_blink_duration > duration_lack:  # is it was more than 10s ago
                LOGGER.info(f"{time_code=}{blink_value=}{since_last_blink_duration=}")
                return True
            # meaning that the last blink was more than 6 second ago
            # meaning there is less than 10 blink per minutes, healthy average is 15-20
            return False
    return False
