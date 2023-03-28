"""Main qt file, containing code for the qt window etc"""
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow

from eyeblink_gui.widgets.window import Window


class MainWindow(QMainWindow):  # pylint: disable=too-few-public-methods
    """Main window that contain the main widget"""

    def __init__(self) -> None:
        """Initialize main window with custom config"""
        QMainWindow.__init__(self)
        self.setWindowTitle("Eyeblink detection")
        self.resize(800, 700)
        widget = Window()
        self.setCentralWidget(widget)
        self.setWindowIcon(icon)


if __name__ == "__main__":
    app = QApplication()
    # app.setQuitOnLastWindowClosed(False)# usefull if we use system tray icon

    icon = QIcon("images/blink.png")
    # if QSystemTrayIcon.isSystemTrayAvailable() and QSystemTrayIcon.supportsMessages():
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())
