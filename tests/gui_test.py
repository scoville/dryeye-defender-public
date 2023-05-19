"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
from unittest.mock import patch
import pytest

from pytestqt.qtbot import QtBot    # type: ignore[import]
import pytest_xvfb    # type: ignore[import]
import cv2
from PySide6.QtCore import Qt

from eyeblink_gui.__main__ import MainWindow
from eyeblink_gui.widgets.window import Window
from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread

DUMMY_IMAGE_PATH = "tests/assets/dummy.jpg"
EYEBLINK_MODEL_THREAD_TIMEOUT = 3000


@pytest.fixture(autouse=True, scope="session")
def ensure_xvfb() -> None:
    """Ensure that Xvfb is available."""
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")


def mock_init_cap(self: EyeblinkModelThread, input_device: int) -> None:
    # pylint: disable = unused-argument
    """Mock the init_cap function to use a dummy image instead of a camera"""
    self.cap = cv2.VideoCapture(DUMMY_IMAGE_PATH)  # pylint: disable=no-member


@patch("eyeblink_gui.widgets.window.DEBUG", True)
def test_main_window(qtbot: QtBot) -> None:
    """Test the main window, and the running the detector for a few frames on a dummy image"""
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=lambda *args, **kwargs: [0]):
        main_window = MainWindow()
        main_window.show()
        qtbot.addWidget(main_window)
        window = Window(main_window.centralWidget())
        for _ in range(5):
            with qtbot.waitSignal(window.eye_th.finished, timeout=EYEBLINK_MODEL_THREAD_TIMEOUT):
                qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
                assert window.eye_th.isRunning()
            window.eye_th.cap = cv2.VideoCapture(DUMMY_IMAGE_PATH)  # pylint: disable=no-member
