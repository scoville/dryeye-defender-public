"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
from pytestqt import qtbot
from pyvirtualdisplay import Display

from eyeblink_gui.widgets.window import Window


def test_application(qtbot):
    with Display() as disp:
        print(disp.is_alive()) # True
        widget = Window()
        qtbot.addWidget(widget)
