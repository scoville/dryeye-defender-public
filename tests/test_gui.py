# pylint: disable = redefined-outer-name, unused-argument, protected-access
"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import time
from typing import Generator, Any
from unittest.mock import patch

import cv2
import pytest
import pytest_xvfb  # type: ignore[import]
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot  # type: ignore[import]

from dryeye_defender.__main__ import Application
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.widgets.blink_model_thread import BlinkModelThread
from dryeye_defender.widgets.window import Window

DUMMY_IMAGE_PATH = "tests/assets/dummy.jpg"
NO_BLINKING_IMAGE_PATH = "tests/assets/no_blink.jpg"
BLINKING_IMAGE_PATH = "tests/assets/blink.jpg"
BLINK_MODEL_THREAD_TIMEOUT_MS = 3000


class MockVideoCapture():
    """Mock the VideoCapture class to use instead of cv2.VideoCapture. Reads from a dummy image"""

    def __init__(self, image_path: str = DUMMY_IMAGE_PATH) -> None:
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
    """Override creating a QApplication for the tests with our custom application. The
    get_cap_indexes function is mocked to return a list of two available ports
    """
    with patch("dryeye_defender.widgets.window.get_cap_indexes",
               new=lambda *args, **kwargs: [0, 1]), \
            patch("dryeye_defender.widgets.window.DEBUG", new=True):
        application = Application([])
        yield application
    application.quit()
    time.sleep(0.5)
    try:
        db_path = get_saved_data_path()
        print("The fixture teardown is deleting the database at ", db_path)
        db_path.unlink(missing_ok=False)
    except FileNotFoundError:
        print("The fixture teardown did not not need to delete a database as it was not present")


def mock_init_cap(self: BlinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use a dummy image instead of a camera"""
    self.cap = MockVideoCapture()  # type: ignore[assignment]


def mock_init_cap_no_blink(self: BlinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use an image of a face that isn't blinking instead of a
    camera
    """
    self.cap = MockVideoCapture(NO_BLINKING_IMAGE_PATH)  # type: ignore[assignment]


def mock_init_cap_blink(self: BlinkModelThread, input_device: int) -> None:
    """Mock the init_cap function to use an image of a face that is blinking instead of a
    camera
    """
    self.cap = MockVideoCapture(BLINKING_IMAGE_PATH)  # type: ignore[assignment]


def test_application(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector using the debug compute button for a few
    frames on a dummy image
    """
    with patch("dryeye_defender.widgets.window.BlinkModelThread.init_cap", new=mock_init_cap):
        window = Window(qapp.main_window.centralWidget())
        for _ in range(5):
            with qtbot.waitSignal(window.eye_th.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS):
                qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
                assert window.eye_th.isRunning()


def test_application_no_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector using the debug compute button for a frame
    on an image of a face that isn't blinking
    """
    with patch("dryeye_defender.widgets.window.BlinkModelThread.init_cap",
               new=mock_init_cap_no_blink):
        window = Window(qapp.main_window.centralWidget())
        with qtbot.waitSignal(window.eye_th.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS):
            qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
            assert window.eye_th.isRunning()
        assert window.label_output.text() == "No blink detected"


def test_application_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector using the debug compute button for a frame
    on an image of a face that is blinking
    """
    with patch("dryeye_defender.widgets.window.BlinkModelThread.init_cap", new=mock_init_cap_blink):
        window = Window(qapp.main_window.centralWidget())
        with qtbot.waitSignal(window.eye_th.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS):
            qtbot.mouseClick(window.compute_button, Qt.MouseButton.LeftButton)
            assert window.eye_th.isRunning()
        assert window.label_output.text() == "Blink detected"


def test_application_popup(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application with the popup alert mode, running the detector and checking
    that the popup window appears
    """
    with patch("dryeye_defender.widgets.window.BlinkModelThread.init_cap",
               new=mock_init_cap_no_blink):
        window = Window(qapp.main_window.centralWidget())

        # Set variables so that the popup window will appear
        window.alert_mode = "popup"
        window.duration_lack_spin_box.setValue(1)  # seconds

        qtbot.mouseClick(window.toggle_button, Qt.MouseButton.LeftButton)
        assert window.toggle_button.isChecked()
        assert not window.blink_reminder.isVisible()

        # Initialise the last blink time, otherwise lack of blinking will not be detected
        # Must be done after the thread is started (which happens when the toggle button is clicked)
        window.eye_th.model_api._last_blink_time = time.time()

        # Wait for the popup window to appear
        qtbot.wait(1500)
        assert window.blink_reminder.isVisible()

        qtbot.mouseClick(window.toggle_button, Qt.MouseButton.LeftButton)
        assert not window.toggle_button.isChecked()
