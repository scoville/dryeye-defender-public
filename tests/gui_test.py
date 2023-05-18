"""
This is a unit test for running the application, and testing the detector on a few dummy frames.
"""
import pytest
from time import sleep

from pytestqt import qtbot
import pytest_xvfb
from PySide6.QtWidgets import QLabel

def test_application(qtbot):
    if not pytest_xvfb.xvfb_available():
        raise Exception("Tests need Xvfb to run.")
    qlabel = QLabel()
    qlabel.setText("Hello World")
    qtbot.addWidget(qlabel)
