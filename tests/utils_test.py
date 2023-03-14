"""Test utils function"""
from typing import List
import time
import pytest

from eyeblink_gui.utils.eyeblink_verification import lack_of_blink_detection


@pytest.fixture(name="blink_history")
def get_blink_history() -> List:
    """Create a false prediction array containing a few blinks

    :return: return the array
    """
    current_time = time.time()
    prediction_array = [
        [current_time - 0, -1],
        [current_time - 1, -1],
        [current_time - 2, -1],
        [current_time - 3, -1],
        [current_time - 4, -1],
        [current_time - 5, -1],
        [current_time - 6, 1],
        [current_time - 7, -1],
        [current_time - 8, -1],
        [current_time - 9, -1],
        [current_time - 10, -1],
        [current_time - 11, -1],
        [current_time - 12, -1],
        [current_time - 13, -1],
        [current_time - 14, -1],
    ]
    return prediction_array


def test_lack_of_blink_detection(blink_history: List) -> None:
    """Test the lack of blink detection(not really useful, placeholder test)"""
    assert lack_of_blink_detection(blink_history, 5) is True
    assert lack_of_blink_detection(blink_history, 16) is False
