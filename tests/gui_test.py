"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import pytest
from unittest.mock import patch

from pytestqt import qtbot
import pytest_xvfb
import cv2
import PySide6.QtCore as QtCore

from eyeblink_gui.__main__ import MainWindow


@pytest.fixture(autouse=True, scope='session')
def ensure_xvfb():
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")


def test_application(qtbot):
    # TODO: ensure that DEBUG is set to True
    with patch("eyeblink_gui.widgets.window.EyeblinkModelThread.init_cap", new=mock_init_cap), \
         patch("eyeblink_gui.widgets.window.get_cap_indexes", new=lambda *args, **kwargs: [0]):
        main_window = MainWindow()
        main_window.show()
        qtbot.addWidget(main_window)
        window = main_window.centralWidget()
        for i in range(1):
            with qtbot.waitSignal(window.eye_th.finished, timeout=3000):
                qtbot.mouseClick(window.compute_button, QtCore.Qt.LeftButton)
                assert window.eye_th.isRunning()

def mock_init_cap(*args, **kwargs):
    args[0].cap = cv2.VideoCapture("tests/dummy.jpg")