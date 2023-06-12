# pylint: disable = redefined-outer-name, unused-argument
"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
from typing import List, Generator, Any
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
NO_BLINKING_IMAGE_PATH = "tests/assets/no_blink.jpg"
BLINKING_IMAGE_PATH = "tests/assets/blink.jpg"
EYEBLINK_MODEL_THREAD_TIMEOUT_MS = 3000


class MockVideoCapture():
    """Mock the VideoCapture class to use instead of cv2.VideoCapture. Reads from a dummy image"""
    def __init__(self, image_path=DUMMY_IMAGE_PATH) -> None:
        """Initialize VideoCapture with the dummy image"""
        self.image_path = image_path
        self._cap = cv2.VideoCapture(image_path)  # pylint: disable=no-member

    def read(self) -> Any:
        # pylint: disable=no-self-use
        """Read from the dummy image"""
        return cv2.VideoCapture(self.image_path).read()  # pylint: disable=no-member

    def release(self) -> None:
        """Release the dummy image"""
        self._cap.release()


@pytest.fixture(autouse=True, scope="module")
def ensure_xvfb() -> None:
    """Ensure that Xvfb is available"""
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")


@pytest.fixture(scope="module")
def qapp() -> Generator[Application, None, None]:
    """Override creating a QApplication for the tests with our custom application. The init_cap
    and get_cap_indexes functions are mocked to use a dummy image instead of a camera
    """
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        print("setup")
        application = Application([])
        yield application
        print("teardown")
        del application

'''
@pytest.fixture(scope="module")
def qapp_no_blink() -> Generator[Application, None, None]:
    """Override creating a QApplication for the tests with our custom application. The init_cap
    and get_cap_indexes functions are mocked to use an image of a face  that isn't blinking instead
    of a camera
    """
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap_no_blink), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        print("setup")
        application = Application([])
        yield application
        print("teardown")
        del application


@pytest.fixture(scope="module")
def qapp_blink() -> Generator[Application, None, None]:
    """Override creating a QApplication for the tests with our custom application. The init_cap
    and get_cap_indexes functions are mocked to use an image of a face that is blinking instead of
    a camera
    """
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap_blink), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        print("setup")
        application = Application([])
        yield application
        print("teardown")
        del application
'''

def mock_init_cap(self: EyeblinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use a dummy image instead of a camera"""
    self.cap = MockVideoCapture()  # type: ignore[assignment]


def mock_init_cap_no_blink(self: EyeblinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use an image of a face that isn't blinking instead of a
    camera
    """
    self.cap = MockVideoCapture(NO_BLINKING_IMAGE_PATH)  # type: ignore[assignment]


def mock_init_cap_blink(self: EyeblinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use an image of a face that is blinking instead of a
    camera
    """
    self.cap = MockVideoCapture(BLINKING_IMAGE_PATH)  # type: ignore[assignment]


def mock_get_cap_indexes() -> List[str]:
    """Mock the get_cap_indexes function to return a list of two indexes"""
    return ["0", "1"]


def test_application(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector for a few frames on a dummy image"""
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        window = Window(qapp.main_window.centralWidget())
        for _ in range(5):
            with qtbot.waitSignal(window.eye_th.finished, timeout=EYEBLINK_MODEL_THREAD_TIMEOUT_MS):
                qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
                assert window.eye_th.isRunning()


def test_application_no_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector for a frame on an image of a face that
    isn't blinking"""
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap_no_blink), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        window = Window(qapp.main_window.centralWidget())
        window.cap = MockVideoCapture(NO_BLINKING_IMAGE_PATH)
        with qtbot.waitSignal(window.eye_th.finished, timeout=EYEBLINK_MODEL_THREAD_TIMEOUT_MS):
            qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
            # TODO: Ensure debug to true
            assert window.eye_th.isRunning()
        assert window.label_output.text() == "No blink detected"


def test_application_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector for a frame on an image of a face that
    is blinking"""
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap_blink), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=mock_get_cap_indexes):
        window = Window(qapp.main_window.centralWidget())
        with qtbot.waitSignal(window.eye_th.finished, timeout=EYEBLINK_MODEL_THREAD_TIMEOUT_MS):
            qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
            # TODO: Ensure debug to true
            assert window.eye_th.isRunning()
        assert window.label_output.text() == "Blink detected"
