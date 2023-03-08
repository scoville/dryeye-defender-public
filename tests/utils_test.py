"""Test utils function"""
from typing import List
import pytest

from eyeblink_gui.utils.eyeblink_verification import lack_of_blink_detection


@pytest.fixture(name="blink_history")
def get_blink_history() -> List:
    """Create a false prediction array containing a few blinks

    :return: return the array
    """
    prediction_array = [
        [1, -1],
        [2, -1],
        [3, -1],
        [4, -1],
        [5, -1],
        [6, -1],
        [7, -1],
        [8, 1],
        [9, 1],
        [10, -1],
        [10, 1],
    ]
    return prediction_array


def test_lack_of_blink_detection(blink_history: List) -> None:
    """Test the lack of blink detection(not really useful, placeholder test)"""
    assert True == lack_of_blink_detection(blink_history)
