# pylint: disable=attribute-defined-outside-init
"""Class for the main window widget"""
import logging
import os
import time
from functools import partial
from typing import List, Optional
from playsound import playsound

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QSystemTrayIcon,
    QWidget,
)


from blinkdetector.utils.database import EventTypes
from dryeye_defender.utils.database import BlinkHistory
from dryeye_defender.utils.utils import find_data_file, get_cap_indexes
from dryeye_defender.utils.utils import get_saved_data_path
from dryeye_defender.widgets.animated_blink_popup_window.animated_blink_reminder import (
    AnimatedBlinkReminder,
)
from dryeye_defender.widgets.components.blink_model_thread import BlinkModelThread
from dryeye_defender.widgets.blink_window.main import BlinkStatsWindow
from dryeye_defender.widgets.components.notification_dropdown import (
    NotificationDropdown,
)
from dryeye_defender.widgets.debug_window.main import DebugWindow
from dryeye_defender.widgets.components.tray_icon import TrayIcon

# This beep sound effect is based on https://link.springer.com/article/10.1007/s00347-004-1072-7
# An acoustic animation signal was generated as a beep (800 Hz, 190 ms)
# via Assembler with direct hardware support
# Median of 3.45 blinks/min --> median 8.9 blinks/min
# (Confidence interval 0.32–0.45). https://app.clickup.com/t/7508642/POC-2537
BEEP_SOUND_EFFECT_PATH = find_data_file("audiocheck.net_sin_800Hz_-3dBFS_0.19s.wav")
BLINK_ICON_PATH = find_data_file("blink.png")
BLINK_GIF_PATH = find_data_file("blink_animated.gif")
BLINK_ANIME_GIF_PATH = find_data_file("blink_animated_anime.gif")
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

        # BlinkModelThread also creates the DB if it does not exist
        self.blink_thread = BlinkModelThread(self.blink_value_updated_slot,
                                             self.thread_finished_slot,
                                             MINIMUM_DURATION_LACK_OF_BLINK_MS,
                                             self,
                                             DEBUG)
        self.blink_history = BlinkHistory(get_saved_data_path())
        self.blink_history.store_event(time.time(), EventTypes.SOFTWARE_STARTUP)

        if DEBUG:
            self.compute_button = QPushButton("Compute one frame")
            self.compute_button.clicked.connect(self.blink_thread.start_thread)
            self.label_output = QLabel("0")
            self.debug_window_button = QPushButton("Open debug window")
            self.debug_window_button.clicked.connect(self._open_debug_window)
            window_layout.addWidget(self.compute_button, 0, 0, 1, 1)
            window_layout.addWidget(self.label_output, 0, 1, 1, 1)
            window_layout.addWidget(self.debug_window_button, 0, 2, 1, 1)

            self.label_fps = QLabel("fps: 0")
            window_layout.addWidget(self.label_fps, 0, 3, 1, 1)

            self.time_last_finished_th = 0.0

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
            "default": BLINK_GIF_PATH,
            "anime": BLINK_ANIME_GIF_PATH,
        }
        event_type = "POPUP_NOTIFICATION"
        reset_alert_time_partial = partial(
            self._reset_last_end_of_alert_time, event_type
        )
        blink_reminder = AnimatedBlinkReminder(
            movie_path=self.blink_reminder_gifs["default"],
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
        self.blink_history.store_event(time.time(), event_type, time_since_last_alert)
        self.last_end_of_alert_time = time.time()

    def _create_frequency_slider(self) -> None:
        """Create frequency slider for settings"""
        self.frequency_spin_box = QSpinBox()
        self.frequency_label = QLabel("Interval of the blinking detection (ms):")
        self.frequency_slider = QSlider(Qt.Orientation.Horizontal)
        self.frequency_slider.setSingleStep(MIN_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setTickInterval(DEFAULT_INFERENCE_TICK_INTERVAL_MS)
        self.frequency_slider.setRange(
            MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS
        )
        self.frequency_spin_box.setRange(
            MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS
        )
        self.frequency_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.frequency_slider.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_spin_box.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_slider.valueChanged.connect(self._set_timer_interval)
        self.frequency_spin_box.valueChanged.connect(self._sync_slider)

    def _create_toggle_settings(self) -> None:
        """Create toggle widget for toggle settings"""
        self.toggle_label = QLabel("Enable blinking detection:")
        self.toggle_button = QPushButton()
        self.toggle_button.setText("Enable")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        self.toggle_button.clicked.connect(self._toggle_inference)
        if self.tray_available:
            self.tray.toggle_tray.triggered.connect(self.toggle_button.nextCheckState)
            self.tray.toggle_tray.triggered.connect(self._toggle_inference)

    def _create_toggle_sound_notification(self) -> None:
        """Create toggle widget for sound notification"""
        self.sound_toggle_label = QLabel("Enable sound notifications")
        self.sound_toggle_button = QPushButton()
        self.sound_toggle_button.setText("Disable")
        self.sound_toggle_button.setCheckable(True)
        self.sound_toggle_button.setChecked(True)
        self.sound_toggle_button.clicked.connect(self._toggle_sound_slot)

    def _create_notification_dropdown(self) -> None:
        """Create the notification settings dropdown and associated text label"""
        self.alert_mode_label = QLabel("Notification Type")
        self.notification_dropdown = NotificationDropdown(self.tray_available)

    def _create_duration_settings(self) -> None:
        """Create duration for settings button and label"""
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(1, 60)
        self.duration_lack_spin_box.setValue(
            self.blink_thread.model_api.lack_of_blink_threshold
        )
        self.duration_lack_spin_box.valueChanged.connect(self._update_duration_lack)
        self.duration_lack_label = QLabel(
            "Minimum duration for considering lack of blink (s):"
        )

    def _create_select_cam_settings(self) -> None:
        """Create select cam and label cam"""
        self.select_cam_label = QLabel("Choose which camera device to use")
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

    def _create_select_blink_reminder_gif(self) -> None:
        """Create select blink reminder gif and label blink reminder gif"""
        self.select_blink_reminder_gif_label = QLabel(
            "Choose blink reminder gif (popup mode only)"
        )
        self.select_blink_reminder_gif = QComboBox()
        self.select_blink_reminder_gif.addItems(list(self.blink_reminder_gifs.keys()))
        self.select_blink_reminder_gif.activated.connect(
            lambda: self.blink_reminder.setup_movie(
                self.blink_reminder_gifs[self.select_blink_reminder_gif.currentText()]
            )
        )

    @staticmethod
    def _add_widget_to_grid(grid: QGridLayout, widget: QWidget,
                            label: QWidget, row: int, col: int,
                            span: int = 1) -> None:
        """Helper function to add widget and its label to the grid."""
        # pylint: disable = too-many-arguments
        grid.addWidget(label, row, col, span, span)
        grid.addWidget(widget, row, col + 1, span, span)

    def _create_toggle_settings_row(self, grid: QGridLayout) -> None:
        self._create_toggle_settings()
        self._add_widget_to_grid(grid, self.toggle_button, self.toggle_label, 0, 0)

    def _create_frequency_slider_row(self, grid: QGridLayout) -> None:
        self._create_frequency_slider()
        self._add_widget_to_grid(grid, self.frequency_spin_box, self.frequency_label, 1, 0)
        grid.addWidget(self.frequency_slider, 1, 2, 1, 4)

    def _create_duration_settings_row(self, grid: QGridLayout) -> None:
        self._create_duration_settings()
        self._add_widget_to_grid(grid, self.duration_lack_spin_box, self.duration_lack_label, 2, 0)

    def _create_notification_dropdown_row(self, grid: QGridLayout) -> None:
        self._create_notification_dropdown()
        self._add_widget_to_grid(grid, self.notification_dropdown.dropdown,
                                 self.alert_mode_label, 3, 0)

    def _create_select_blink_reminder_gif_row(self, grid: QGridLayout) -> None:
        self._create_select_blink_reminder_gif()
        self._add_widget_to_grid(grid, self.select_blink_reminder_gif,
                                 self.select_blink_reminder_gif_label, 4, 0)

    def _create_select_cam_settings_row(self, grid: QGridLayout) -> None:
        self._create_select_cam_settings()
        self._add_widget_to_grid(grid, self.select_cam, self.select_cam_label, 5, 0)

    def _create_toggle_sound_notification_row(self, grid: QGridLayout) -> None:
        self._create_toggle_sound_notification()
        self._add_widget_to_grid(grid, self.sound_toggle_button, self.sound_toggle_label, 6, 0)

    def _create_settings(self) -> QGroupBox:
        """Initialize all variable/object for the settings part of the program"""
        group_box = QGroupBox("&Settings")
        grid = QGridLayout()

        self._create_toggle_settings_row(grid)
        self._create_frequency_slider_row(grid)
        self._create_duration_settings_row(grid)
        self._create_notification_dropdown_row(grid)
        self._create_select_blink_reminder_gif_row(grid)
        self._create_select_cam_settings_row(grid)
        self._create_toggle_sound_notification_row(grid)

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
        if DEBUG:
            diff_time = time.time() - self.time_last_finished_th
            self.time_last_finished_th = time.time()
            self.label_fps.setText(f"fps:{str(int(1 / diff_time))}")

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
                    self.tray.showTrayBlinkReminder(
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
                self.tray.setTrayToggleText("Disable")
            self.timer.start()
            LOGGER.info("timer started")
            self.blink_history.store_event(time.time(), EventTypes.DETECTION_ENABLED)
        else:
            self.toggle_button.setText("Enable")
            if self.tray_available:
                self.tray.setTrayToggleText("Enable")
            LOGGER.info("timer stop")
            # By stopping the timer, it means we do not schedule the inference thread periodically.
            self.timer.stop()
            self.blink_history.store_event(time.time(), EventTypes.DETECTION_DISABLED)

    @Slot()
    def _open_debug_window(self) -> None:
        """Create debug window and launch it"""
        self.debug_window = DebugWindow(self.blink_thread)
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
