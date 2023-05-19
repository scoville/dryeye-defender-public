# pylint: disable = redefined-outer-name, unused-argument
"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
from typing import Generator
from unittest.mock import patch
import pytest

from pytestqt.qtbot import QtBot    # type: ignore[import]
import pytest_xvfb    # type: ignore[import]
import cv2
from PySide6.QtCore import Qt

from eyeblink_gui.__main__ import Application
from eyeblink_gui.widgets.window import Window
from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

DUMMY_IMAGE_PATH = "tests/assets/dummy.jpg"
EYEBLINK_MODEL_THREAD_TIMEOUT = 3000


@pytest.fixture(autouse=True, scope="module")
def ensure_xvfb() -> None:
    """Ensure that Xvfb is available."""
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")


@pytest.fixture(scope="module")
def qapp() -> Generator[Application, None, None]:
    """Override creating a QApplication for the tests with our custom application. The init_cap
    and get_cap_indexes functions are mocked to use a dummy image instead of a camera
    """
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=lambda *args, **kwargs: [0]):
        yield Application([])


def mock_init_cap(self: EyeblinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use a dummy image instead of a camera"""
    self.cap = cv2.VideoCapture(DUMMY_IMAGE_PATH)  # pylint: disable=no-member


def test_application(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector for a few frames on a dummy image"""
    window = Window(qapp.main_window.centralWidget())
    for _ in range(5):
        with qtbot.waitSignal(window.eye_th.finished, timeout=EYEBLINK_MODEL_THREAD_TIMEOUT):
            qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
            assert window.eye_th.isRunning()
        window.eye_th.cap = cv2.VideoCapture(DUMMY_IMAGE_PATH)  # pylint: disable=no-member
