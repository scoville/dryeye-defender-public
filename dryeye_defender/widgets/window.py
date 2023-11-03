# pylint: disable=attribute-defined-outside-init
"""Class for the main window widget"""
import logging
import os
import sys
import time
from functools import partial
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QGridLayout, QGroupBox, QLabel,
                               QMenu, QMessageBox, QPushButton, QSlider,
                               QSpinBox, QSystemTrayIcon, QWidget)

from blinkdetector.utils.database import EventTypes
from dryeye_defender.utils.database import BlinkHistory
from dryeye_defender.utils.utils import find_data_file, get_cap_indexes
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.widgets.animated_blink_reminder import AnimatedBlinkReminder
from dryeye_defender.widgets.blink_model_thread import BlinkModelThread
from dryeye_defender.widgets.blink_window.main import BlinkStatsWindow
from dryeye_defender.widgets.components.notification_dropdown import NotificationDropdown
from dryeye_defender.widgets.debug_window.main import DebugWindow

DEBUG = True
MINIMUM_DURATION_LACK_OF_BLINK_MS = 10  # minimum duration for considering lack of blink
DEFAULT_INFERENCE_INTERVAL_MS = 10
DEFAULT_INFERENCE_TICK_INTERVAL_MS = 50
MIN_INFERENCE_INTERVAL_MS = 10
MAX_INFERENCE_INTERVAL_MS = 1000
LOGGER = logging.getLogger(__name__)

# if user dismisses a popup, allow this many seconds before permitting another popup
ALERT_SECONDS_COOLDOWN = 10


class Window(QWidget):
    """Widget of the main window"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """Initialize all variable and create the layout of the window
        :param parent: parent of the widget, defaults to None
        """
        super().__init__(parent)
        window_layout = QGridLayout(self)

        self.eye_th = BlinkModelThread(self, DEBUG)  # also creates the DB if it does not exist
        self.blink_history = BlinkHistory(get_saved_data_path())
        self.blink_history.store_event(time.time(),
                                       EventTypes.SOFTWARE_STARTUP)
        self.eye_th.finished.connect(self._thread_finished)
        self.eye_th.update_label_output.connect(self._blink_value_updated_slot)
        self.eye_th.model_api.lack_of_blink_threshold = MINIMUM_DURATION_LACK_OF_BLINK_MS
        self.icon = QIcon(find_data_file("assets/blink.png"))

        if DEBUG:
            self.compute_button = QPushButton("Compute one frame")
            self.compute_button.clicked.connect(self._start_thread)
            self.label_output = QLabel("0")
            self.debug_window_button = QPushButton("Open debug window")
            self.debug_window_button.clicked.connect(self._open_debug_window)
            window_layout.addWidget(self.compute_button, 0, 0, 1, 1)
            window_layout.addWidget(self.label_output, 0, 1, 1, 1)
            window_layout.addWidget(self.debug_window_button, 0, 2, 1, 1)

            self.time_last_finished_th = 0.0
            self.label_fps = QLabel("fps: 0")
            window_layout.addWidget(self.label_fps, 0, 3, 1, 1)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._start_thread)
        self.timer.setInterval(DEFAULT_INFERENCE_INTERVAL_MS)

        self.tray_available = (QSystemTrayIcon.isSystemTrayAvailable() and
                               QSystemTrayIcon.supportsMessages())
        if self.tray_available:
            self.tray = self._create_tray()
        self.blink_reminder = self._create_blink_reminder()

        # Blink Graph window
        self.open_blink_stats_button = QPushButton(("Blink Statistics"))
        self.open_blink_stats_button.clicked.connect(self._open_blink_stats)
        window_layout.addWidget(self.open_blink_stats_button, 3, 0, 1, 6)

        # Create Settings
        window_layout.addWidget(self._create_settings(), 1, 0, 2, 6)

    def _create_blink_reminder(self) -> AnimatedBlinkReminder:
        """Initialize blink reminder for later usage

        :return: return the AnimatedBlinkReminder object
        """
        self.blink_reminder_gifs = {
            "default": find_data_file("assets/blink_animated.gif"),
            "anime": find_data_file("assets/blink_animated_anime.gif")
        }
        event_type = "POPUP_NOTIFICATION"
        reset_alert_time_partial = partial(self._reset_last_end_of_alert_time, event_type)
        blink_reminder = AnimatedBlinkReminder(
            movie_path=self.blink_reminder_gifs["default"],
            dismiss_callback=reset_alert_time_partial,
            duration_lack=self.eye_th.model_api.lack_of_blink_threshold,
            alert_seconds_cooldown=ALERT_SECONDS_COOLDOWN
        )
        self.last_end_of_alert_time = time.time() - ALERT_SECONDS_COOLDOWN
        return blink_reminder

    def _reset_last_end_of_alert_time(self, event_type: str) -> None:
        """Reset the last time the alert (POPUP or SYSTEM NOTIFICATION) ended

        In case of the POPUP, it's a callback, in case of SYSTEM NOTIFICATION, it's called
        directly after invocation.

        :param event_type: either POPUP_NOTIFICATION OR SYSTEM_TRAY_NOTIFCATION
        """
        time_since_last_alert = time.time() - self.last_end_of_alert_time
        self.blink_history.store_event(time.time(),
                                       event_type,
                                       time_since_last_alert)
        self.last_end_of_alert_time = time.time()

    def _create_tray(self) -> QSystemTrayIcon:
        """Initialize system tray

        :return: Return the system tray initialized
        """
        LOGGER.info("using system tray")
        menu = QMenu()
        self.toggle_tray = menu.addAction("Enable")
        quit_tray = menu.addAction("Quit")
        quit_tray.triggered.connect(sys.exit)
        # self.toggle_tray.triggered.connect(self._set_timer)

        tray = QSystemTrayIcon(self.icon)
        tray.setContextMenu(menu)
        # system_tray.setContextMenu()
        tray.setVisible(True)
        tray.showMessage("DryEye Defender initialized", "", self.icon, 5000)
        return tray

    def _create_frequency_slider(self) -> None:
        """Create frequency slider for settings"""
        self.frequency_spin_box = QSpinBox()
        self.frequency_label = QLabel("Interval of the blinking detection (ms):")
        self.frequency_slider = QSlider(Qt.Orientation.Horizontal)
        self.frequency_slider.setSingleStep(MIN_INFERENCE_INTERVAL_MS)
        # self.frequency_spin_box.singleStep(MIN_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setTickInterval(DEFAULT_INFERENCE_TICK_INTERVAL_MS)
        self.frequency_slider.setRange(MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS)
        self.frequency_spin_box.setRange(MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.frequency_slider.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_spin_box.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_slider.valueChanged.connect(self._set_timer_interval)
        self.frequency_spin_box.valueChanged.connect(self._sync_slider)

    def _create_toggle_settings(self) -> None:
        """Create toggle widget for toggle settings"""
        self.toggle_label = QLabel("Enable blinking detection:")
        # self.toggle_label.adjustSize()
        self.toggle_button = QPushButton()
        self.toggle_button.setText("Enable")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        # toggleButton.setEnabled(True)
        self.toggle_button.clicked.connect(self._set_timer)
        if self.tray_available:
            self.toggle_tray.triggered.connect(self.toggle_button.nextCheckState)
            self.toggle_tray.triggered.connect(self._set_timer)

    def _sound_notification_toggle(self) -> None:
        """Create toggle widget for sound notification"""
        self.sound_toggle_label = QLabel("Enable sound notifications")
        # self.toggle_label.adjustSize()
        self.sound_toggle_button = QPushButton()
        self.sound_toggle_button.setText("Enable")
        self.sound_toggle_button.setCheckable(True)
        self.sound_toggle_button.setChecked(True)
        # toggleButton.setEnabled(True)
        self.sound_toggle_button.clicked.connect(self._toggle_sound_slot)

    def _create_notification_dropdown_row(self) -> None:
        """Create the notification settings dropdown and associated text labek"""
        self.alert_mode_label = QLabel("Notification Type")
        self.notification_dropdown = NotificationDropdown(self.tray_available)

    def _create_duration_settings(self) -> None:
        """Create duration for settings button and label"""
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(1, 60)
        self.duration_lack_spin_box.setValue(self.eye_th.model_api.lack_of_blink_threshold)
        self.duration_lack_spin_box.valueChanged.connect(self._update_duration_lack)
        self.duration_lack_label = QLabel("Minimum duration for considering lack of blink (s):")

    def _create_select_cam_settings(self) -> None:
        """Create select cam and label cam"""
        self.select_cam_label = QLabel("Choose which camera device to use")
        self.select_cam = QComboBox()
        cap_indexes = get_cap_indexes()
        if not cap_indexes:
            LOGGER.error("No cameras could be found")
            self.toggle_button.setEnabled(False)
            cap_indexes = self._alert_no_cam()

        # rebut to true because the alert cam is finished and camera is detected
        self.toggle_button.setEnabled(True)
        self.select_cam.addItems(cap_indexes)
        selected_cap_index = int(cap_indexes[int(os.environ.get("DEFAULT_CAMERA_INDEX", 0))])
        self.eye_th.init_cap(selected_cap_index)
        # default to first camera index detected if DEFAULT_CAMERA_INDEX env var not specified
        self.select_cam.activated.connect(
            lambda: self.eye_th.init_cap(int(self.select_cam.currentText())))

    def _create_select_blink_reminder_gif(self) -> None:
        """Create select blink reminder gif and label blink reminder gif"""
        self.select_blink_reminder_gif_label = QLabel("Choose blink reminder gif (popup mode only)")
        self.select_blink_reminder_gif = QComboBox()
        self.select_blink_reminder_gif.addItems(list(self.blink_reminder_gifs.keys()))
        self.select_blink_reminder_gif.activated.connect(
            lambda: self.blink_reminder.setup_movie(
                self.blink_reminder_gifs[self.select_blink_reminder_gif.currentText()]
            )
        )

    def _create_settings(self) -> QGroupBox:
        """Initialize all variable/object for the settings part of the program"""
        group_box = QGroupBox("&Settings")
        self._create_toggle_settings()
        self._sound_notification_toggle()
        self._create_notification_dropdown_row()
        self._create_frequency_slider()
        self._create_duration_settings()
        self._create_select_cam_settings()
        self._create_select_blink_reminder_gif()

        grid = QGridLayout()
        grid.addWidget(self.toggle_label, 0, 0, 1, 1)
        grid.addWidget(self.toggle_button, 0, 1, 1, 1)

        grid.addWidget(self.frequency_label, 1, 0, 1, 1)
        grid.addWidget(self.frequency_spin_box, 1, 1, 1, 1)
        grid.addWidget(self.frequency_slider, 1, 2, 1, 4)

        grid.addWidget(self.duration_lack_label, 2, 0, 1, 1)
        grid.addWidget(self.duration_lack_spin_box, 2, 1, 1, 1)

        grid.addWidget(self.alert_mode_label, 3, 0, 1, 1)
        grid.addWidget(self.notification_dropdown.dropdown, 3, 1, 1, 1)

        grid.addWidget(self.select_blink_reminder_gif_label, 4, 0, 1, 1)
        grid.addWidget(self.select_blink_reminder_gif, 4, 1, 1, 1)

        grid.addWidget(self.select_cam_label, 5, 0, 1, 1)
        grid.addWidget(self.select_cam, 5, 1, 1, 1)

        grid.addWidget(self.sound_toggle_label, 6, 0, 1, 1)
        grid.addWidget(self.sound_toggle_button, 6, 1, 1, 1)

        # vbox.addStretch(1)
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

    @Slot()
    def _start_thread(self) -> None:
        """Slot that call the thread for inference"""
        # The following line ensures we only have one thread processing a frame at a time
        if not self.eye_th.isRunning():
            LOGGER.debug("starting thread for computing one frame")
            self.eye_th.start()
        else:
            LOGGER.debug("inference thread already running so skipping computing this frame")

    @Slot()
    def _thread_finished(self) -> None:
        """Slot called at the end of the thread, and manage the lack of blink detection"""
        LOGGER.debug("Thread is finished")
        if DEBUG:
            diff_time = time.time() - self.time_last_finished_th
            self.time_last_finished_th = time.time()
            self.label_fps.setText(f"fps:{str(int(1 / diff_time))}")

        if self.eye_th.model_api.lack_of_blink:
            # Only display popup if it's been > ALERT_SECONDS_COOLDOWN since last popup
            # dismissal
            time_since_last_alert = time.time() - self.last_end_of_alert_time
            if time_since_last_alert > ALERT_SECONDS_COOLDOWN:
                LOGGER.info("Lack of blink detected")
                if self.notification_dropdown.is_current_setting("Popup"):
                    self.blink_reminder.update_duration_lack(
                        self.eye_th.model_api.lack_of_blink_threshold)
                    self.blink_reminder.show_reminder()
                elif self.notification_dropdown.is_current_setting("Tray Notification"):
                    self.tray.showMessage(
                        f"You didn't blink in the last "
                        f"{self.eye_th.model_api.lack_of_blink_threshold:.0f} seconds",
                        "Blink now !", self.icon, 5000)
                    self._reset_last_end_of_alert_time(EventTypes["SYSTEM_TRAY_NOTIFICATION"])
                elif self.notification_dropdown.is_current_setting("None"):
                    LOGGER.info("No GUI notifications enabled, but lack of blink has been "
                                "detected.")
                else:
                    raise NotImplementedError("Only the above notification types have been defined")

    @Slot()
    def _blink_value_updated_slot(self, output: int) -> None:
        """Slot called each frame by the inference thread when the current frame's blink value
         is emited as `output`

        :param output: output for the frame processed 1 for blink detected, -1 for no blink
        """
        if output == 1:
            if DEBUG:
                self.label_output.setText("Blink detected")
            if self.notification_dropdown.is_current_setting("Popup"):
                if self.blink_reminder.isVisible():
                    self.blink_reminder.close()
                    self._reset_last_end_of_alert_time(EventTypes["POPUP_NOTIFICATION"])
        elif DEBUG:
            self.label_output.setText("No blink detected")

    @Slot()
    def _set_timer_interval(self, slider_value: int) -> None:
        """Slot called when slider is modified, update the timer value(frequency of the inference)

        :param slider_value: current value of the slider
        """
        self.timer.setInterval(slider_value)
        self.frequency_spin_box.setValue(slider_value)
        LOGGER.info("slider_value=%s", slider_value)

    @Slot()
    def _sync_slider(self, spinbox_value: int) -> None:
        """Sync the slider with the spinbox

        :param spinbox_value: current value of the spin box
        """
        self.frequency_slider.setValue(spinbox_value)

    @Slot()
    def _update_duration_lack(self, spinbox_value: int) -> None:
        """Update the value of duration_lack

        :param spinbox_value: current value of the spin box
        """
        self.eye_th.model_api.lack_of_blink_threshold = spinbox_value

    @Slot()
    def _toggle_sound_slot() -> None:
        """Slot called when the sound toggle button is pressed"""
        button_state = self.sound_toggle_button.isChecked()
        if button_state:
            self.toggle_button.setText("Disable")
        else:
            self.toggle_button.setText("Enable")

    @Slot()
    def _set_timer(self) -> None:
        """Slot called when automatic inference is enabled, manage button and timer state"""
        LOGGER.info("timer check")
        button_state = self.toggle_button.isChecked()
        if button_state:
            self.toggle_button.setText("Disable")
            if self.tray_available:
                self.toggle_tray.setText("Disable")
            self.timer.start()
            LOGGER.info("timer started")
            self.blink_history.store_event(time.time(),
                                           EventTypes.DETECTION_ENABLED)
        else:
            self.toggle_button.setText("Enable")
            if self.tray_available:
                self.toggle_tray.setText("Enable")
            LOGGER.info("timer stop")
            self.timer.stop()
            self.blink_history.store_event(time.time(),
                                           EventTypes.DETECTION_DISABLED)

    @Slot()
    def _open_debug_window(self) -> None:
        """Create debug window and launch it"""
        self.debug_window = DebugWindow(self.eye_th)
        self.debug_window.show()
        LOGGER.info("open debug")

    @Slot()
    def _open_blink_stats(self) -> None:
        """Create blink stats window and launch it"""
        self.blink_stats_window = BlinkStatsWindow(self.blink_history)
        # Set default graph
        self.blink_stats_window.show_default_plot()
        self.blink_stats_window.show()
        LOGGER.info("open blink stats windows")
