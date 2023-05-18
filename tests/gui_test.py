"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import pytest
from time import sleep

from pytestqt import qtbot
import pytest_xvfb

from eyeblink_gui.widgets.window import Window


def test_application(qtbot):
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")
    #widget = Window()
    #qtbot.addWidget(widget)
