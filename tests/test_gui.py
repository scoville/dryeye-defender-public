# pylint: disable = redefined-outer-name, unused-argument, protected-access
"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import time
from typing import Generator, Any
from unittest.mock import patch

import cv2
import pytest
import pytest_xvfb  # type: ignore[import-untyped]
from PySide6.QtCore import Qt
from pytestqt.qtbot import QtBot  # type: ignore[import-untyped]

from dryeye_defender.__main__ import Application
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.widgets.components.blink_model_thread import BlinkModelThread
from dryeye_defender.widgets.settings_window import Window

DUMMY_IMAGE_PATH = "tests/assets/dummy.jpg"
NO_BLINKING_IMAGE_PATH = "tests/assets/no_blink.jpg"
BLINKING_IMAGE_PATH = "tests/assets/blink.jpg"
BLINK_MODEL_THREAD_TIMEOUT_MS = 3000


class MockVideoCapture:
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


@pytest.fixture()
def qapp() -> Generator[Application, None, None]:
    """Override creating a QApplication for the tests with our custom application. The
    get_cap_indexes function is mocked to return a list of two available ports
    """
    db_path = get_saved_data_path()
    try:
        db_path.unlink(missing_ok=False)
        print("The fixture SETUP deleted the database at ", db_path)
    except FileNotFoundError:
        print(
            "The fixture SETUP did not not need to delete a database as it was not present"
        )

    with patch(
        "dryeye_defender.widgets.settings_window.get_cap_indexes",
        new=lambda *args, **kwargs: [0, 1],
    ):
        # https://forum.qt.io/topic/110418/how-to-destroy-a-singleton-and-then-create-a-new-one/11
        application: Any = Application.instance()
        if application is None:
            application = Application([])
        yield application

    print("Force child thread to exit")
    application.main_window.window_widget.blink_thread.terminate()
    application.main_window.window_widget.blink_thread.wait()
    application.quit()
    del application
    time.sleep(0.5)
    try:
        db_path.unlink(missing_ok=False)
        print("The fixture TEARDOWN is deleted the database at ", db_path)
    except FileNotFoundError:
        print(
            "The fixture TEARDOWN did not not need to delete a database as it was not present"
        )
    time.sleep(0.5)


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
    with patch(
        "dryeye_defender.widgets.settings_window.BlinkModelThread.init_cap", new=mock_init_cap
    ):
        window = Window(qapp.main_window.centralWidget())
        for _ in range(5):
            with qtbot.waitSignal(
                window.blink_thread.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS
            ):
                window.blink_thread.start_thread()
                assert window.blink_thread.isRunning()


def test_application_no_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector using the debug compute button for a frame
    on an image of a face that isn't blinking
    """
    with patch(
        "dryeye_defender.widgets.settings_window.BlinkModelThread.init_cap",
        new=mock_init_cap_no_blink,
    ):
        window = Window(qapp.main_window.centralWidget())
        with qtbot.waitSignal(
            window.blink_thread.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS
        ):
            window.blink_thread.start_thread()  # run one frame
            assert window.blink_thread.isRunning()

        for row in window.db_api._display_all_rows():
            blink_value = row[1]
            assert blink_value == -1
        assert len(window.db_api._display_all_rows()) == 1, "1 row of data recorded"


def test_application_blink(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application, running the detector using the debug compute button for a frame
    on an image of a face that is blinking
    """
    with patch(
        "dryeye_defender.widgets.settings_window.BlinkModelThread.init_cap",
        new=mock_init_cap_blink,
    ):
        window = Window(qapp.main_window.centralWidget())
        with qtbot.waitSignal(
            window.blink_thread.finished, timeout=BLINK_MODEL_THREAD_TIMEOUT_MS
        ):
            window.blink_thread.start_thread()  # run one frame
            assert window.blink_thread.isRunning()

        for row in window.db_api._display_all_rows():
            blink_value = row[1]
            assert blink_value == 1
        assert len(window.db_api._display_all_rows()) == 1, "1 row of data recorded"


def test_application_popup(qtbot: QtBot, qapp: Application) -> None:
    """Test the main application with the popup alert mode, running the detector and checking
    that the popup window appears
    """
    with patch(
        "dryeye_defender.widgets.settings_window.BlinkModelThread.init_cap",
        new=mock_init_cap_no_blink,
    ):
        window = Window(qapp.main_window.centralWidget())

        # Set variables so that the popup window will appear
        window.notification_dropdown.set_current_notification_settings(
            window.notification_dropdown.dropdown_options.Popup.value - 1
        )
        window.duration_lack_spin_box.setValue(1)  # seconds
        qtbot.mouseClick(window.toggle_button, Qt.MouseButton.LeftButton)
        assert window.toggle_button.isChecked()
        assert not window.blink_reminder.isVisible()

        # Initialise the last blink time, otherwise lack of blinking will not be detected
        # Must be done after the thread is started (which happens when the toggle button is clicked)
        window.blink_thread.model_api._last_blink_time = time.time()

        # Wait for the popup window to appear
        qtbot.wait(1500)
        assert window.blink_reminder.isVisible()

        qtbot.mouseClick(window.toggle_button, Qt.MouseButton.LeftButton)
        assert not window.toggle_button.isChecked()
