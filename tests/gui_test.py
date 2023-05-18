"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import sys
import threading

from pytestqt import qtbot

from eyeblink_gui.widgets.window import Window


def test_application(qtbot):
    widget = Window()
    qtbot.addWidget(widget)
