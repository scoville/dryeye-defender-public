# pylint: disable=attribute-defined-outside-init
"""Class for the main window widget"""
from collections import OrderedDict
import logging
import os
import time
from functools import partial
from typing import List, Optional, Any, TypedDict, Union
from playsound import playsound

from PySide6.QtCore import QTimer, Slot, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QWidget,
    QFrame,
    QVBoxLayout,
)

from PySide6.QtGui import QPainter, QColor, QPen, QFont, QPalette, QPixmap

from blinkdetector.utils.database import EventTypes
from dryeye_defender.utils.database import BlinkHistoryDryEyeDefender
from dryeye_defender.utils.config import GREY
from dryeye_defender.utils.utils import find_data_file, get_cap_indexes
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.widgets.animated_blink_popup_window.animated_blink_reminder import (
    AnimatedBlinkReminder,
)
from dryeye_defender.widgets.components.blink_model_thread import BlinkModelThread
from dryeye_defender.widgets.stats_window.main import BlinkStatsWindow
from dryeye_defender.widgets.components.notification_dropdown import (
    NotificationDropdown,
)
from dryeye_defender.widgets.debug_window.main import DebugWindow
from dryeye_defender.widgets.components.tray_icon import TrayIcon
from dryeye_defender.widgets.components.animated_toggle import AnimatedToggle

# This beep sound effect is based on https://link.springer.com/article/10.1007/s00347-004-1072-7
# An acoustic animation signal was generated as a beep (800 Hz, 190 ms)
# via Assembler with direct hardware support
# Median of 3.45 blinks/min --> median 8.9 blinks/min
# (Confidence interval 0.32–0.45). https://app.clickup.com/t/7508642/POC-2537
BEEP_SOUND_EFFECT_PATH = find_data_file("audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav")
BLINK_ICON_PATH = find_data_file("blink.png")
BLINK_GIF_PATH = find_data_file("blink_animated.gif")
BLINK_ANIME_GIF_PATH = find_data_file("blink_animated_anime.gif")
LOGO_PNG_PATH = find_data_file("Logo.png")
MINIMUM_DURATION_LACK_OF_BLINK_MS = 10  # minimum duration for considering lack of blink
DEFAULT_INFERENCE_INTERVAL_MS = 10
LOGGER = logging.getLogger(__name__)

# if user dismisses a popup, allow this many seconds before permitting another popup
ALERT_SECONDS_COOLDOWN = 10
MARGIN_PX = 70


class SettingType(TypedDict):
    """Type to describe the label, subtitle and
    clickable widget for a row on the settings page"""

    layout: Optional[QVBoxLayout]
    title_label: QLabel
    subtitle_label: QLabel
    interactive_element: Optional[Union[QWidget, AnimatedToggle]]


class RoundedFrame(QFrame):
    """A class for drawing curved box around a setting row"""

    def __init__(self) -> None:
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        # self.setStyleSheet("background-color: lightblue;")
        # border.setFrameShape(QFrame.Box)
        # border.setFrameStyle(QFrame.Panel)
        self.setLineWidth(3)  # Adjust the border width
        # border.setContentsMargins(30, 30, 30, 30)

    def paintEvent(self, _: Any) -> None:
        """Configures the appearance of the QFrame

        :param _: event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rounded_rect = self.rect().adjusted(1, 1, -1, -1)
        painter.setBrush(QColor(255, 255, 255, 200))
        # painter.setPen(Qt.NoPen)
        pen = QPen(GREY)
        pen.setWidth(0)
        painter.setPen(pen)
        xyradius = 5
        painter.drawRoundedRect(rounded_rect, xyradius, xyradius)


def make_vboxlayout(title: str, subtitle: str) -> SettingType:
    """Makes a VBoxLayout object, which is a title with a subtitle below it"""
    layout = QVBoxLayout()
    layout.addStretch()
    title_label = QLabel(title)
    title_label.setIndent(10)  # indent from left
    layout.addWidget(title_label)
    subtitle_label = QLabel(subtitle)
    subtitle_label.setIndent(10)
    subtitle_font = QFont("Avenir Next LT Pro")
    subtitle_font.setPointSize(10)  # Adjust the font size as needed
    subtitle_label.setFont(subtitle_font)
    palette = QPalette()
    palette.setColor(subtitle_label.foregroundRole(), GREY)
    subtitle_label.setPalette(palette)
    layout.addStretch()
    layout.addWidget(subtitle_label)
    layout.addStretch()
    settings: SettingType = {
        "layout": layout,
        "title_label": title_label,
        "subtitle_label": subtitle_label,
        "interactive_element": None,  # populated later
    }
    return settings


class Window(QWidget):  # pylint: disable=too-many-instance-attributes
    # pylint: disable=too-many-instance-attributes
    """Widget of the main window"""
    PERFORMANCE_DROPDOWNS = OrderedDict(
        [
            ("Normal", DEFAULT_INFERENCE_INTERVAL_MS),
            ("Power Saving", DEFAULT_INFERENCE_INTERVAL_MS * 5),
            ("Ultra Power Saving", DEFAULT_INFERENCE_INTERVAL_MS * 10),
        ]
    )

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize all variable and create the layout of the window
        :param parent: parent of the widget, defaults to None
        """
        super().__init__(parent)
        LOGGER.info("Starting Window")
        window_layout = QVBoxLayout(self)
        # window_layout.setContentsMargins(MARGIN_PX, MARGIN_PX, MARGIN_PX, MARGIN_PX)

        self.db_api = BlinkHistoryDryEyeDefender(get_saved_data_path())

        # BlinkModelThread also creates the DB if it does not exist
        self.blink_thread = BlinkModelThread(
            self.db_api,
            self.blink_value_updated_slot,
            self.thread_finished_slot,
            MINIMUM_DURATION_LACK_OF_BLINK_MS,
            self,
            True,
        )
        self.db_api.store_event(time.time(), EventTypes.SOFTWARE_STARTUP)

        self.timer = QTimer(self)
        self.timer.setInterval(DEFAULT_INFERENCE_INTERVAL_MS)
        # QTimer produced timeout signal at constant intervals
        self.timer.timeout.connect(self.blink_thread.start_thread)

        self.tray_available = (
            QSystemTrayIcon.isSystemTrayAvailable()
            and QSystemTrayIcon.supportsMessages()
        )
        if self.tray_available:
            self.tray = TrayIcon(BLINK_ICON_PATH)
        self.blink_reminder = self._create_blink_reminder()

        image_label = QLabel()
        pixmap = QPixmap(LOGO_PNG_PATH)
        scaled_pixmap = pixmap.scaled(200, 200,
                                      Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation)
        image_label.setPixmap(scaled_pixmap)
        window_layout.addWidget(image_label)

        # Create Settings
        settings_layout = QGridLayout()
        offset_label = QLabel("                ")
        settings_layout.addWidget(offset_label, 0, 0)
        settings_layout.addWidget(self._create_settings_grid())
        window_layout.addLayout(settings_layout)

    def _create_blink_reminder(self) -> AnimatedBlinkReminder:
        """Initialize blink reminder for later usage

        :return: return the AnimatedBlinkReminder object
        """
        self.blink_reminder_gifs = {
            "Default": BLINK_GIF_PATH,
            "Anime": BLINK_ANIME_GIF_PATH,
        }
        event_type = "POPUP_NOTIFICATION"
        reset_alert_time_partial = partial(
            self._reset_last_end_of_alert_time, event_type
        )
        blink_reminder = AnimatedBlinkReminder(
            movie_path=self.blink_reminder_gifs["Default"],
            dismiss_callback=reset_alert_time_partial,
            duration_lack=self.blink_thread.model_api.lack_of_blink_threshold,
            alert_seconds_cooldown=ALERT_SECONDS_COOLDOWN,
        )
        self.last_end_of_alert_time = time.time() - ALERT_SECONDS_COOLDOWN
        return blink_reminder

    def _reset_last_end_of_alert_time(self, event_type: EventTypes) -> None:
        """Reset the last time the alert (POPUP or SYSTEM NOTIFICATION) ended

        In case of the POPUP, it's a callback, in case of SYSTEM NOTIFICATION, it's called
        directly after invocation.

        :param event_type: either POPUP_NOTIFICATION OR SYSTEM_TRAY_NOTIFICATION
        """
        time_since_last_alert = time.time() - self.last_end_of_alert_time
        self.db_api.store_event(time.time(), event_type, time_since_last_alert)
        self.last_end_of_alert_time = time.time()

    def _create_toggle_settings(self) -> SettingType:
        """Create toggle widget for toggle settings to toggle starting blink monitoring"""
        settings = make_vboxlayout(
            "Enable Blinking Detection", "Start monitoring your blink rate using webcam"
        )
        self.toggle_button = AnimatedToggle()
        self.toggle_button.setFixedSize(self.toggle_button.sizeHint())
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self._toggle_inference)
        if self.tray_available:
            self.tray.toggle_tray.triggered.connect(self.toggle_button.nextCheckState)
            self.tray.toggle_tray.triggered.connect(self._toggle_inference)

        settings["interactive_element"] = self.toggle_button
        return settings

    def _create_see_face_mapping_setting(self) -> SettingType:
        """Toggle to display view of the face mapping/blink detection"""
        settings = make_vboxlayout(
            "Tracking", "Visualize how the blink and face detection is working"
        )
        self.view_face_button = QPushButton("View")
        self.view_face_button.clicked.connect(self._open_facial_window)
        settings["interactive_element"] = self.view_face_button
        return settings

    def _create_duration_settings(self) -> SettingType:
        """Create duration for settings button and label"""
        settings = make_vboxlayout(
            "Notification Frequency (s)",
            "Number of seconds after no blinks to trigger a reminder",
        )
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(1, 60)
        self.duration_lack_spin_box.setValue(
            self.blink_thread.model_api.lack_of_blink_threshold
        )
        self.duration_lack_spin_box.valueChanged.connect(self._update_duration_lack)
        settings["interactive_element"] = self.duration_lack_spin_box
        return settings

    def _create_notification_dropdown(self) -> SettingType:
        """Create the notification settings dropdown and associated text label"""
        settings = make_vboxlayout(
            "Notification Type",
            "Select type of notification from the list",
        )
        self.notification_dropdown = NotificationDropdown(self.tray_available)
        settings["interactive_element"] = self.notification_dropdown.dropdown
        return settings

    def _create_select_blink_reminder_gif(self) -> SettingType:
        """Create select blink reminder gif and label blink reminder gif"""
        settings = make_vboxlayout(
            "Blink reminder animation",
            "Select choice of animation for 'Popup' Notification Type",
        )
        self.select_blink_reminder_gif = QComboBox()
        self.select_blink_reminder_gif.addItems(list(self.blink_reminder_gifs.keys()))
        self.select_blink_reminder_gif.activated.connect(
            lambda: self.blink_reminder.setup_movie(
                self.blink_reminder_gifs[self.select_blink_reminder_gif.currentText()]
            )
        )
        settings["interactive_element"] = self.select_blink_reminder_gif
        return settings

    def _create_select_cam_settings(self) -> SettingType:
        """Create select cam and label cam"""
        settings = make_vboxlayout("Camera", "Select which camera device to use")

        self.select_cam = QComboBox()
        cap_indexes = get_cap_indexes()
        if not cap_indexes:
            LOGGER.error("No cameras could be found")
            self.toggle_button.setEnabled(False)
            cap_indexes = self._alert_no_cam()
        # reset blink detection enabled button to enabled because the camera is detected
        self.toggle_button.setEnabled(True)
        self.select_cam.addItems(cap_indexes)
        selected_cap_index = int(
            cap_indexes[int(os.environ.get("DEFAULT_CAMERA_INDEX", 0))]
        )
        self.blink_thread.init_cap(selected_cap_index)
        # default to first camera index detected if DEFAULT_CAMERA_INDEX env var not specified
        self.select_cam.activated.connect(
            lambda: self.blink_thread.init_cap(int(self.select_cam.currentText()))
        )
        settings["interactive_element"] = self.select_cam
        return settings

    def _create_toggle_sound_notification(self) -> SettingType:
        """Create toggle widget for enable/disable sound notification"""
        settings = make_vboxlayout(
            "Sound Notification",
            "Enable or disable sound notification when lack of blink is detected",
        )
        self.sound_toggle_button = QPushButton()
        self.sound_toggle_button.setText("Disable")
        self.sound_toggle_button.setCheckable(True)
        self.sound_toggle_button.setChecked(True)
        self.sound_toggle_button.clicked.connect(self._toggle_sound_slot)
        settings["interactive_element"] = self.sound_toggle_button
        return settings

    def _create_see_blink_statistics_setting(self) -> SettingType:
        """Create a button to display the blink statistics window"""
        settings = make_vboxlayout(
            "Statistics",
            "View your blinking trends over time",
        )

        # Blink Graph window
        self.open_blink_stats_button = QPushButton(("View"))
        self.open_blink_stats_button.clicked.connect(self._open_blink_stats)
        settings["interactive_element"] = self.open_blink_stats_button
        return settings

    @Slot()
    def _set_inference_frequency(self, index: int) -> None:
        """Set how often we trigger the inference (face/blink detection) thread to start

        :param index: index of the dropdown option selected by the user, 0-indexed
        """
        if list(Window.PERFORMANCE_DROPDOWNS.keys())[index] == "Normal":
            self._set_timer_interval(list(Window.PERFORMANCE_DROPDOWNS.values())[index])
        if list(Window.PERFORMANCE_DROPDOWNS.keys())[index] == "Power Saving":
            self._set_timer_interval(list(Window.PERFORMANCE_DROPDOWNS.values())[index])
        if list(Window.PERFORMANCE_DROPDOWNS.keys())[index] == "Ultra Power Saving":
            self._set_timer_interval(list(Window.PERFORMANCE_DROPDOWNS.values())[index])

    def _create_performance_setting(self) -> SettingType:
        """Choose how performance the software should run (how often we run inference)"""
        settings = make_vboxlayout(
            "Performance Mode", "Select how much CPU to use for blinking detection"
        )
        self.combo_box = QComboBox()
        self.combo_box.addItems(list(Window.PERFORMANCE_DROPDOWNS.keys()))
        self.combo_box.activated.connect(self._set_inference_frequency)
        settings["interactive_element"] = self.combo_box
        return settings

    @staticmethod
    def _add_widget_to_grid(
        grid: QGridLayout,
        settings: SettingType,
        row: int,
        col: int = 0,
        span: int = 1,  # rowSpan, columnsSpan
        _: Optional[QVBoxLayout] = None,
    ) -> None:
        """Helper function to add widget and its label to the grid."""
        # pylint: disable = too-many-arguments
        grid.addWidget(RoundedFrame(), row, 0, 1, 6)
        if settings["layout"]:
            grid.addLayout(settings["layout"], row, col, span, span)
        grid.addWidget(settings["title_label"], row, col, span, span)
        if settings["interactive_element"]:
            # Place in column 5 of 6 to right align the buttons
            grid.addWidget(settings["interactive_element"], row, col + 4, span, span)

    def _create_toggle_settings_row(self, grid: QGridLayout) -> None:
        settings = self._create_toggle_settings()
        self._add_widget_to_grid(grid, settings, 0)

    def _create_see_facial_mapping_row(self, grid: QGridLayout) -> None:
        settings = self._create_see_face_mapping_setting()
        self._add_widget_to_grid(grid, settings, 1)

    def _create_duration_settings_row(self, grid: QGridLayout) -> None:
        settings = self._create_duration_settings()
        self._add_widget_to_grid(grid, settings, 2)

    def _create_notification_dropdown_row(self, grid: QGridLayout) -> None:
        settings = self._create_notification_dropdown()
        self._add_widget_to_grid(grid, settings, 3)

    def _create_select_blink_reminder_gif_row(self, grid: QGridLayout) -> None:
        settings = self._create_select_blink_reminder_gif()
        self._add_widget_to_grid(grid, settings, 4)

    def _create_select_cam_settings_row(self, grid: QGridLayout) -> None:
        settings = self._create_select_cam_settings()
        self._add_widget_to_grid(grid, settings, 5)

    def _create_toggle_sound_notification_row(self, grid: QGridLayout) -> None:
        settings = self._create_toggle_sound_notification()
        self._add_widget_to_grid(grid, settings, 6)

    def _create_see_blink_statistics_row(self, grid: QGridLayout) -> None:
        settings = self._create_see_blink_statistics_setting()
        self._add_widget_to_grid(grid, settings, 7)

    def _create_set_performance_level_row(self, grid: QGridLayout) -> None:
        settings = self._create_performance_setting()
        self._add_widget_to_grid(grid, settings, 8)

    def _create_settings_grid(self) -> QGroupBox:
        """Initialize all variable/object for the settings part of the program"""
        group_box = QGroupBox("Settings")
        grid = QGridLayout()
        vertical_spacing_px = 10
        grid.setVerticalSpacing(vertical_spacing_px)
        grid.setRowMinimumHeight(0, 60)

        self._create_toggle_settings_row(grid)
        self._create_see_facial_mapping_row(grid)
        self._create_duration_settings_row(grid)
        self._create_notification_dropdown_row(grid)
        self._create_select_blink_reminder_gif_row(grid)
        self._create_select_cam_settings_row(grid)
        self._create_toggle_sound_notification_row(grid)
        self._create_see_blink_statistics_row(grid)
        self._create_set_performance_level_row(grid)

        group_box.setLayout(grid)
        return group_box

    def _alert_no_cam(self) -> List[str]:  # pylint: disable=no-self-use
        """Alert the user with a window popup that there is no webcam connected

        :return: return available video capture ports after alerting the user
        """
        no_cam_messagebox = QMessageBox()
        no_cam_messagebox.setIcon(QMessageBox.Icon.Warning)
        no_cam_messagebox.setText("No webcam has been detected")
        no_cam_messagebox.setInformativeText("Connect a webcam for blinking detection")
        no_cam_messagebox.exec()
        cap_indexes = get_cap_indexes()
        if not cap_indexes:
            LOGGER.error("No cameras could be found")
            self.toggle_button.setEnabled(False)
            self._alert_no_cam()
        return get_cap_indexes()

    @staticmethod
    def _play_sound_notification() -> None:
        """Play the sound notification"""
        LOGGER.info("Sound notification triggered")
        playsound(BEEP_SOUND_EFFECT_PATH, block=False)

    @Slot()
    def thread_finished_slot(self) -> None:
        """Slot called at the end of the inference thread (after processing each single frame),
        and manages the lack of blink detection for the software"""
        LOGGER.debug("Thread is finished")

        if self.blink_thread.model_api.lack_of_blink:
            # Only display popup if it's been > ALERT_SECONDS_COOLDOWN since last popup
            # dismissal
            time_since_last_alert = time.time() - self.last_end_of_alert_time
            if time_since_last_alert > ALERT_SECONDS_COOLDOWN:
                LOGGER.info("Lack of blink detected")
                if self.notification_dropdown.is_current_setting("Popup"):
                    self.blink_reminder.update_duration_lack(
                        self.blink_thread.model_api.lack_of_blink_threshold
                    )
                    self.blink_reminder.show_reminder()
                    if self.sound_toggle_button.isChecked():
                        self._play_sound_notification()
                elif self.notification_dropdown.is_current_setting("Tray Notification"):
                    self.tray.show_tray_blink_reminder(
                        self.blink_thread.model_api.lack_of_blink_threshold
                    )
                    self._reset_last_end_of_alert_time(
                        EventTypes["SYSTEM_TRAY_NOTIFICATION"]
                    )
                    if self.sound_toggle_button.isChecked():
                        self._play_sound_notification()
                elif self.notification_dropdown.is_current_setting("None"):
                    LOGGER.info(
                        "No GUI notifications enabled, but lack of blink has been "
                        "detected."
                    )
                else:
                    raise NotImplementedError(
                        "Only the above notification types have been defined"
                    )

    @Slot()
    def blink_value_updated_slot(self, output: int) -> None:
        """Slot called each frame by the inference thread when the current frame's blink value
         is emitted as `output`

        :param output: output for the frame processed 1 for blink detected, -1 for no blink
        """
        if output == 1:
            if self.notification_dropdown.is_current_setting("Popup"):
                if self.blink_reminder.isVisible():
                    self.blink_reminder.close()
                    self._reset_last_end_of_alert_time(EventTypes["POPUP_NOTIFICATION"])

    @Slot()
    def _set_timer_interval(self, slider_value: int) -> None:
        """Slot called when slider is modified, update the timer value(frequency of the inference)

        :param slider_value: current value of the slider
        """
        self.timer.setInterval(slider_value)
        LOGGER.info("slider_value=%s", slider_value)

    @Slot()
    def _update_duration_lack(self, spinbox_value: int) -> None:
        """Update the value of duration_lack

        :param spinbox_value: current value of the spin box
        """
        self.blink_thread.model_api.lack_of_blink_threshold = spinbox_value

    @Slot()
    def _toggle_sound_slot(self) -> None:
        """Slot called when the sound toggle button is pressed"""
        button_state = self.sound_toggle_button.isChecked()
        if button_state:
            self.sound_toggle_button.setText("Disable")
        else:
            self.sound_toggle_button.setText("Enable")
            self._play_sound_notification()

    @Slot()
    def _toggle_inference(self) -> None:
        """Slot called when automatic inference is enabled, manage button and timer state"""
        LOGGER.info("timer check")
        button_state = self.toggle_button.isChecked()
        if button_state:
            # If inference button state is enabled,
            # toggle it to enabled and show button text 'Disable'
            self.toggle_button.setText("Disable")
            if self.tray_available:
                self.tray.set_tray_toggle_text("Disable")
            self.timer.start()
            LOGGER.info("timer started")
            self.db_api.store_event(time.time(), EventTypes.DETECTION_ENABLED)
        else:
            self.toggle_button.setText("Enable")
            if self.tray_available:
                self.tray.set_tray_toggle_text("Enable")
            LOGGER.info("timer stop")
            # By stopping the timer, it means we do not schedule the inference thread periodically.
            self.timer.stop()
            self.db_api.store_event(time.time(), EventTypes.DETECTION_DISABLED)

    @Slot()
    def _open_facial_window(self) -> None:
        """Create debug window showing facial mapping and launch it"""
        self.debug_window = DebugWindow(self.blink_thread)
        self.debug_window.show()
        LOGGER.info("open debug")

    @Slot()
    def _open_blink_stats(self) -> None:
        """Create blink stats window and launch it"""
        self.blink_stats_window = BlinkStatsWindow(self.db_api)
        # Set default graph
        self.blink_stats_window.show_default_plot()
        self.blink_stats_window.show()
        LOGGER.info("open blink stats windows")
