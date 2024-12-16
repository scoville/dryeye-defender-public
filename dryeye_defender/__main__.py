"""Main qt file, containing code for the qt window etc"""

import logging
from logging.handlers import RotatingFileHandler
import os
import signal
import sys
import time
from typing import Any, Tuple, Sequence
import warnings


from PySide6.QtGui import QIcon, QFontDatabase, QCloseEvent, QPalette, QColor
from PySide6.QtWidgets import QApplication, QMainWindow

from blinkdetector.utils.database import EventTypes
from dryeye_defender.utils.utils import find_data_file, update_font
from dryeye_defender.widgets.settings_window import Window

warnings.filterwarnings("ignore",
                        category=UserWarning,
                        message="SymbolDatabase\\.GetPrototype\\(\\) is deprecated")
LEVEL = os.environ.get("LOGLEVEL", "INFO")


# Configure the root logger
logging.basicConfig(level=LEVEL, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Create a rotating file handler
file_handler = RotatingFileHandler('dryeye-defender.log', maxBytes=5*1024*1024, backupCount=5)
file_handler.setLevel(LEVEL)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Add the file handler to the root logger
logging.getLogger().addHandler(file_handler)

# This line is not redundant on my machine, not sure why it's needed to set twice.
logging.getLogger().setLevel(LEVEL)

# Create a logger for this module
LOGGER = logging.getLogger(__name__)


class Application(QApplication):
    """The entire application encapsulated in this class"""

    def __init__(self, argv: Sequence[str]) -> None:
        """Initialise the application
        :param argv: sys.argv
        """
        super().__init__(argv)
        LOGGER.info("Starting application")
        # Connect the SIGINT signal to a slot
        signal.signal(signal.SIGINT, self._handle_sigint)  # type: ignore
        # Create and show the main window
        self.main_window = MainWindow()
        self.main_window.show()

    def _handle_sigint(self, *_: Tuple[Any, ...]) -> None:
        """Perform any cleanup or save operations here
        before exiting the application due to a SIGINT/keyboard interrupt
        """
        LOGGER.info("SIGINT received. Shutting down gracefully.")
        self.quit()
        # app.setQuitOnLastWindowClosed(False) # useful if we use system tray icon
        # if QSystemTrayIcon.isSystemTrayAvailable() and QSystemTrayIcon.supportsMessages():


class MainWindow(QMainWindow):  # pylint: disable=too-few-public-methods
    """Main window that contain the main widget"""

    def __init__(self) -> None:
        """Initialize main window with custom config"""
        QMainWindow.__init__(self)
        self.setWindowTitle("DryEye Defender")
        self.resize(800, 700)

        # Set main window's background to grey
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(243, 243, 243))
        self.setPalette(palette)

        self.window_widget = Window()
        self.setCentralWidget(self.window_widget)
        icon_path = find_data_file("blink.png")
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        self.load_fonts()
        update_font(self)

    def closeEvent(self, _: QCloseEvent) -> None:  # pylint: disable=invalid-name
        """This event handler is called with the given event when Qt receives a window close
        request for a top-level widget from the window system.
        """
        LOGGER.info("The user closed the main window")
        self.window_widget.db_api.store_event(
            time.time(), EventTypes.SOFTWARE_SHUTDOWN
        )

    @staticmethod
    def load_fonts() -> None:
        """Load fonts from disk into global database"""
        # Set the default fonts
        # Load a font from a font file on disk
        font_paths = [
            "AvenirNextLTPro-Regular.otf",
            "AvenirNextLTPro-Bold.otf",
            "AvenirNextLTPro-It.otf",
        ]
        for font_name in font_paths:
            font_id = QFontDatabase.addApplicationFont(find_data_file(font_name))
            LOGGER.info(
                "Font id: %s, Font name: %s",
                font_id,
                QFontDatabase.applicationFontFamilies(font_id),
            )
            if font_id == -1:
                LOGGER.error("Issue loading font %s", font_name)


if __name__ == "__main__":
    LOGGER.info("Starting application in timezone (TZ): %s", os.environ.get("TZ"))
    APP = Application(sys.argv)

    # Start the application event loop
    sys.exit(APP.exec())
