"""A widget which provides a dropdown selection for what notification type to use"""
from enum import Enum
import logging
from typing import Optional
from PySide6.QtWidgets import (QComboBox, QWidget)

from PySide6.QtCore import Slot

LOGGER = logging.getLogger(__name__)

class NotificationDropdown(QWidget):
    """A widget which provides a dropdown selection for what notification type to use"""

    def __init__(self, tray_available: bool) -> None:
        """Create the widget

        :param tray_available: whether the system tray is available on this platform
        """
        super().__init__()

        self.DropdownOptions = Enum("DropdownOptions", ["Tray Notification", "Popup", "None"])
        if not tray_available:
            LOGGER.info("Tray not available, removing tray notification option")
            self.DropdownOptions = Enum("DropdownOptions", ["Popup", "None"])
        self.dropdown = QComboBox()
        default_alert_setting_index = 0
        # Remember Enums are 1-indexed whereas dropdowns are 0-indexed
        self.dropdown.addItems([i.name for i in self.DropdownOptions])
        self.dropdown.setCurrentIndex(default_alert_setting_index)
        self.dropdown.currentIndexChanged.connect(
            self.set_current_notification_settings)

    def get_current_notification_setting(self) -> str:
        """Return the currently selected notification setting mode as a string"""
        return self.DropdownOptions(self.dropdown.currentIndex()+1).name

    @Slot()
    def set_current_notification_settings(self, selected_index: Optional[int] = None) -> None:
        """Slot for setting the current notification settings via dropdown box selection

        :param selected_index: index of the selected type of notification if called via
        currentIndexChanged() signal.
        """
        if selected_index is False:
            raise NotImplementedError("This should not occur as this is not a button, %s",
                                      selected_index)
        if selected_index == -1:
            raise RuntimeError("This should not occur as there is no unselected option")
        if selected_index == 0:
            LOGGER.info("Setting notification type to %s", self.DropdownOptions(1).name)
        elif selected_index == 1:
            LOGGER.info("Setting notification type to %s", self.DropdownOptions(2).name)
        elif selected_index == 2:
            LOGGER.info("Setting notification type to %s", self.DropdownOptions(3).name)
        else:
            raise NotImplementedError(f"This should not occur as"
                                      f" this option does not exist: {selected_index}")
