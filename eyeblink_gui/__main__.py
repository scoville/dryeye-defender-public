"""Main qt file, containing code for the qt window etc"""
import logging
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow

from eyeblink_gui.widgets.window import Window
from eyeblink_gui.utils.utils import find_data_file

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class MainWindow(QMainWindow):  # pylint: disable=too-few-public-methods
    """Main window that contain the main widget"""

    def __init__(self) -> None:
        """Initialize main window with custom config"""
        QMainWindow.__init__(self)
        self.setWindowTitle("Eyeblink detection")
        self.resize(800, 700)
        widget = Window()
        self.setCentralWidget(widget)
        icon_path = find_data_file("blink.png")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)


if __name__ == "__main__":
    app = QApplication()
    # app.setQuitOnLastWindowClosed(False)# usefull if we use system tray icon

    # if QSystemTrayIcon.isSystemTrayAvailable() and QSystemTrayIcon.supportsMessages():
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
