import sys
from PySide6.QtWidgets import QMenu, QSystemTrayIcon, QWidget
from PySide6.QtGui import QIcon

from dryeye_defender.utils.utils import find_data_file
import logging


LOGGER = logging.getLogger(__name__)


class TrayIcon(QWidget):
    """Tray icon for the system tray and right-click context menu for it."""

    def __init__(self, BLINK_ICON_PATH: str) -> None:
        """Initialise the tray icon"""
        self.icon = QIcon(find_data_file(BLINK_ICON_PATH))
        LOGGER.info("using system tray")
        menu = QMenu()
        self.toggle_tray = menu.addAction("Enable")
        # Toggling the Enable/Disable via tray will have an effect defined by
        #  `self.tray.toggle_tray.triggered.connect()` elsewhere in code.
        quit_tray = menu.addAction("Quit")
        # TODO: add proper software tear down here, for safe DB closing.
        quit_tray.triggered.connect(sys.exit)

        self.tray = QSystemTrayIcon(self.icon)
        self.tray.setContextMenu(menu)
        # system_tray.setContextMenu()
        self.tray.setVisible(True)
        self.tray.showMessage("DryEye Defender initialized", "", self.icon, 5000)

    def showTrayBlinkReminder(self, time_since_last_reminder_seconds: float) -> None:
        """Display a blink reminder as a system tray message

        :param time_since_last_reminder_seconds: time since last blink reminder
        """
        self.tray.showMessage(
            f"You didn't blink in the last "
            f"{time_since_last_reminder_seconds:.0f} seconds",
            "Blink now !",
            self.icon,
            5000,
        )

    def setTrayToggleText(self, text: str) -> None:
        """Set the tray toggle's text to enabled or disable"""
        self.toggle_tray.setText(text)
