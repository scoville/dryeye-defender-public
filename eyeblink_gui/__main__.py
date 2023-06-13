"""Main qt file, containing code for the qt window etc"""
import logging
import os
import signal
import sys
from typing import Any, Tuple, Sequence

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMainWindow

from eyeblink_gui.utils.utils import find_data_file
from eyeblink_gui.widgets.window import Window

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

LOGGER = logging.getLogger(__name__)


class Application(QApplication):
    """The entire application encapsulated in this class"""

    def __init__(self, argv: Sequence[str]) -> None:
        """Initialise the application
        :param argv: sys.argv
        """
        super().__init__(argv)
        # Connect the SIGINT signal to a slot
        signal.signal(signal.SIGINT, self.handle_sigint)  # type: ignore
        # Create and show the main window
        self.main_window = MainWindow()
        self.main_window.show()

    def handle_sigint(self, *_: Tuple[Any, ...]) -> None:
        """Perform any cleanup or save operations here
        before exiting the application due to a SIGINT/keyboard interrupt
        """
        LOGGER.info("SIGINT received. Shutting down gracefully.")
        self.quit()
        # app.setQuitOnLastWindowClosed(False)# usefull if we use system tray icon
        # if QSystemTrayIcon.isSystemTrayAvailable() and QSystemTrayIcon.supportsMessages():


class MainWindow(QMainWindow):  # pylint: disable=too-few-public-methods
    """Main window that contain the main widget"""

    def __init__(self) -> None:
        """Initialize main window with custom config"""
        QMainWindow.__init__(self)
        self.setWindowTitle("Eye health")
        self.resize(800, 700)
        widget = Window()
        self.setCentralWidget(widget)
        icon_path = find_data_file("images/blink.png")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)


if __name__ == "__main__":
    app = Application(sys.argv)
    # Start the application event loop
    sys.exit(app.exec())
