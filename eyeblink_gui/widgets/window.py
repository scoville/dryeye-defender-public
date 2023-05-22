# pylint: disable=attribute-defined-outside-init
"""Class for the main window widget"""
import logging
import os
import sys
import time
from typing import Optional, List

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QComboBox, QGridLayout, QGroupBox, QLabel,
                               QMenu, QMessageBox, QPushButton, QSlider,
                               QSpinBox, QSystemTrayIcon, QWidget)

from eyeblink_gui.utils.utils import get_cap_indexes
from eyeblink_gui.widgets.blink_graph import BlinkGraph
from eyeblink_gui.widgets.debug_window.main import DebugWindow
from eyeblink_gui.widgets.eyeblink_model_thread import EyeblinkModelThread
from eyeblink_gui.widgets.animated_blink_reminder import AnimatedBlinkReminder

DEBUG = True
MINIMUM_DURATION_LACK_OF_BLINK_MS = 10  # minimum duration for considering lack of blink
DEFAULT_INFERENCE_INTERVAL_MS = 50
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

        self.duration_lack = MINIMUM_DURATION_LACK_OF_BLINK_MS
        window_layout = QGridLayout(self)

        self.icon = QIcon("images/blink.png")
        if DEBUG:
            self.compute_button = QPushButton("Compute one frame")
            self.compute_button.clicked.connect(self.start_thread)
            self.label_output = QLabel("0")
            self.debug_window_button = QPushButton("Open debug window")
            self.debug_window_button.clicked.connect(self.open_debug_window)
            window_layout.addWidget(self.compute_button, 0, 0, 1, 1)
            window_layout.addWidget(self.label_output, 0, 1, 1, 1)
            window_layout.addWidget(self.debug_window_button, 0, 2, 1, 1)

        self.eye_th = EyeblinkModelThread(self, DEBUG)
        self.eye_th.finished.connect(self.thread_finished)
        self.eye_th.update_label_output.connect(self.output_slot)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_thread)
        self.timer.setInterval(DEFAULT_INFERENCE_INTERVAL_MS)

        if DEBUG:
            self.time_last_finished_th = 0.0
            self.label_fps = QLabel("fps: 0")
            window_layout.addWidget(self.label_fps, 0, 3, 1, 1)

        self.tray_available = (QSystemTrayIcon.isSystemTrayAvailable() and
                               QSystemTrayIcon.supportsMessages())
        if self.tray_available:
            self.alert_mode = "notification"
            self.tray = self.create_tray()
        else:
            self.alert_mode = "popup"
        self.blink_reminder = self.create_blink_reminder()

        self.blink_graph = BlinkGraph()
        self.get_stats = QPushButton(("Update statistics"))
        self.get_stats.clicked.connect(
            lambda: self.blink_graph.update_graph(self.eye_th.model_api.blink_history))
        window_layout.addWidget(self.create_settings(), 1, 0, 2, 6)
        window_layout.addWidget(self.get_stats, 3, 0, 1, 6)
        window_layout.addWidget(self.blink_graph, 4, 0, 3, 6)

    def create_blink_reminder(self) -> AnimatedBlinkReminder:
        """Initialize blink reminder for later usage

        :return: return the AnimatedBlinkReminder object
        """
        self.blink_reminder_gifs = {
            "default": "images/blink_animated.gif",
            "anime": "images/blink_animated_anime.gif"
        }
        blink_reminder = AnimatedBlinkReminder(
            movie_path=self.blink_reminder_gifs["default"],
            dismiss_callback=self.reset_last_end_of_alert_time,
            duration_lack=self.duration_lack,
            alert_seconds_cooldown=ALERT_SECONDS_COOLDOWN
        )
        self.last_end_of_alert_time = time.time() - ALERT_SECONDS_COOLDOWN
        return blink_reminder

    def reset_last_end_of_alert_time(self) -> None:
        """Reset the last time the alert ended"""
        self.last_end_of_alert_time = time.time()

    def create_tray(self) -> QSystemTrayIcon:
        """Initialize system tray

        :return: Return the system tray initialized
        """
        LOGGER.info("using system tray")
        menu = QMenu()
        self.toggle_tray = menu.addAction("Enable")
        quit_tray = menu.addAction("Quit")
        quit_tray.triggered.connect(sys.exit)
        # self.toggle_tray.triggered.connect(self.set_timer)

        tray = QSystemTrayIcon(self.icon)
        tray.setContextMenu(menu)
        # system_tray.setContextMenu()
        tray.setVisible(True)
        tray.showMessage("Test", "Tray initialized", self.icon, 5000)
        return tray

    def create_frequency_slider(self) -> None:
        """Create frequency slider for settings"""
        self.frequency_spin_box = QSpinBox()
        self.frequency_label = QLabel("Interval of the blinking detection (ms):")
        self.frequency_slider = QSlider(Qt.Orientation.Horizontal)
        self.frequency_slider.setSingleStep(MIN_INFERENCE_INTERVAL_MS)
        # self.frequency_spin_box.singleStep(MIN_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setTickInterval(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setRange(MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS)
        self.frequency_spin_box.setRange(MIN_INFERENCE_INTERVAL_MS, MAX_INFERENCE_INTERVAL_MS)
        self.frequency_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.frequency_slider.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_spin_box.setValue(DEFAULT_INFERENCE_INTERVAL_MS)
        self.frequency_slider.valueChanged.connect(self.set_timer_interval)
        self.frequency_spin_box.valueChanged.connect(self.sync_slider)

    def create_toggle_settings(self) -> None:
        """Create toggle widget for toggle settings"""
        self.toggle_label = QLabel("Enable blinking detection:")
        # self.toggle_label.adjustSize()
        self.toggle_button = QPushButton()
        self.toggle_button.setText("Enable")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        # toggleButton.setEnabled(True)
        self.toggle_button.clicked.connect(self.set_timer)
        self.toggle_tray.triggered.connect(self.toggle_button.nextCheckState)
        self.toggle_tray.triggered.connect(self.set_timer)

    def create_alert_settings(self) -> None:
        """Create the alert button and label"""
        self.alert_mode_label = QLabel("Lack of blink alert (Window popup|OS notification)")
        self.alert_mode_button = QPushButton()
        self.alert_mode_button.setText(self.alert_mode)
        # togalert_mode_buttonEnabled(True)
        self.alert_mode_button.clicked.connect(self.switch_mode)
        if not self.tray_available:
            self.alert_mode_button.setEnabled(False)

    def create_duration_settings(self) -> None:
        """Create duration for settings button and label"""
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(1, 60)
        self.duration_lack_spin_box.setValue(self.duration_lack)
        self.duration_lack_spin_box.valueChanged.connect(self.update_duration_lack)
        self.duration_lack_label = QLabel("Minimum duration for considering lack of blink (s):")

    def create_select_cam_settings(self) -> None:
        """Create select cam and label cam"""
        self.select_cam_label = QLabel("Choose which camera device to use")
        self.select_cam = QComboBox()
        cap_indexes = get_cap_indexes()
        if not cap_indexes:
            LOGGER.error("No cameras could be found")
            self.toggle_button.setEnabled(False)
            cap_indexes = self.alert_no_cam()
        self.select_cam.addItems(cap_indexes)
        selected_cap_index = int(cap_indexes[int(os.environ.get("DEFAULT_CAMERA_INDEX", 0))])
        self.eye_th.init_cap(selected_cap_index)
        # default to first camera index detected if DEFAULT_CAMERA_INDEX env var not specified
        self.select_cam.activated.connect(
            lambda: self.eye_th.init_cap(int(self.select_cam.currentText())))

    def create_select_blink_reminder_gif(self) -> None:
        """Create select blink reminder gif and label blink reminder gif"""
        self.select_blink_reminder_gif_label = QLabel("Choose blink reminder gif (popup mode only)")
        self.select_blink_reminder_gif = QComboBox()
        self.select_blink_reminder_gif.addItems(list(self.blink_reminder_gifs.keys()))
        self.select_blink_reminder_gif.activated.connect(
            lambda: self.blink_reminder.setup_movie(
                self.blink_reminder_gifs[self.select_blink_reminder_gif.currentText()]
            )
        )

    def create_settings(self) -> QGroupBox:
        """Initialize all variable/object for the settings part of the program"""
        group_box = QGroupBox("&Settings")
        self.create_toggle_settings()
        self.create_alert_settings()
        self.create_frequency_slider()
        self.create_duration_settings()
        self.create_select_cam_settings()
        self.create_select_blink_reminder_gif()

        grid = QGridLayout()
        grid.addWidget(self.toggle_label, 0, 0, 1, 1)
        grid.addWidget(self.toggle_button, 0, 1, 1, 1)
        grid.addWidget(self.frequency_label, 1, 0, 1, 1)
        grid.addWidget(self.frequency_spin_box, 1, 1, 1, 1)
        grid.addWidget(self.frequency_slider, 1, 2, 1, 4)
        grid.addWidget(self.duration_lack_label, 2, 0, 1, 1)
        grid.addWidget(self.duration_lack_spin_box, 2, 1, 1, 1)
        grid.addWidget(self.alert_mode_label, 3, 0, 1, 1)
        grid.addWidget(self.alert_mode_button, 3, 1, 1, 1)
        grid.addWidget(self.select_blink_reminder_gif_label, 4, 0, 1, 1)
        grid.addWidget(self.select_blink_reminder_gif, 4, 1, 1, 1)
        grid.addWidget(self.select_cam_label, 5, 0, 1, 1)
        grid.addWidget(self.select_cam, 5, 1, 1, 1)
        # vbox.addStretch(1)
        group_box.setLayout(grid)
        return group_box

    def alert_no_cam(self) -> List[str]:  # pylint: disable=no-self-use
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
            self.alert_no_cam()
        return get_cap_indexes()

    @Slot()
    def start_thread(self) -> None:
        """Slot that call the thread for inference"""
        # The following line ensures we only have one thread processing a frame at a time
        if not self.eye_th.isRunning():
            LOGGER.info("starting thread for computing one frame")
            self.eye_th.start()
        else:
            LOGGER.info("inference thread already running so skipping computing this frame")

    @Slot()
    def thread_finished(self) -> None:
        """Slot called at the end of the thread, and manage the lack of blink detection"""
        LOGGER.info("Thread is finished")
        if DEBUG:
            diff_time = time.time() - self.time_last_finished_th
            self.time_last_finished_th = time.time()
            self.label_fps.setText(f"fps:{str(int(1 / diff_time))}")

        # lack_blink = self.eye_th.model_api.lack_of_blink_detection(duration_lack=self.duration_lack)
        if self.eye_th.model_api.lack_of_blink:
            # Only display popup if it's been > POPUP_DISMISS_SECONDS_COOLDOWN_S since last popup
            # dismissal
            if (time.time() - self.last_end_of_alert_time) > ALERT_SECONDS_COOLDOWN:
                LOGGER.info("Lack of blink detected")
                if self.alert_mode == "popup":
                    self.blink_reminder.update_duration_lack(self.duration_lack)
                    self.blink_reminder.show_reminder()
                else:
                    self.tray.showMessage(
                        f"You didn't blink in the last {self.duration_lack} seconds",
                        "Blink now !", self.icon, 5000)
                    self.last_end_of_alert_time = time.time()

    @Slot()
    def output_slot(self, output: int) -> None:
        """Slot called when the output from the thread is ready

        :param output: output for the frame processed 1 for blink detected, -1 for no blink
        """
        # self.eye_th.model_api.add_blink(time.time(), output)
        if output == 1:
            if DEBUG:
                self.label_output.setText("Blink detected")
            if self.alert_mode == "popup":
                if self.blink_reminder.isVisible():
                    self.blink_reminder.close()
                    self.reset_last_end_of_alert_time()
        elif DEBUG:
            self.label_output.setText("No blink detected")

    @Slot()
    def switch_mode(self) -> None:
        """Update the button to switch alert mode and also change the alert mode"""
        if self.alert_mode == "popup":
            self.alert_mode = "notification"
        else:
            self.alert_mode = "popup"
        self.alert_mode_button.setText(self.alert_mode)

    @Slot()
    def set_timer_interval(self, slider_value: int) -> None:
        """Slot called when slider is modified, update the timer value(frequency of the inference)

        :param slider_value: current value of the slider
        """
        self.timer.setInterval(slider_value)
        self.frequency_spin_box.setValue(slider_value)
        LOGGER.info("slider_value=%s", slider_value)

    @Slot()
    def sync_slider(self, spinbox_value: int) -> None:
        """Sync the slider with the spinbox

        :param spinbox_value: current value of the spin box
        """
        self.frequency_slider.setValue(spinbox_value)

    @Slot()
    def update_duration_lack(self, spinbox_value: int) -> None:
        """Update the value of duration_lack

        :param spinbox_value: current value of the spin box
        """
        self.duration_lack = spinbox_value
        # TODO remove duration lack for internal api variable

    @Slot()
    def set_timer(self) -> None:
        """Slot called when automatic inference is enabled, manage button and timer state"""
        LOGGER.info("timer check")
        button_state = self.toggle_button.isChecked()
        if button_state:
            self.toggle_button.setText("Disable")
            self.toggle_tray.setText("Disable")
            # initialize with a blink, https://app.clickup.com/t/7508642/POC-2256
            self.eye_th.model_api.init_blink()  # pylint:disable=no-member
            self.timer.start()
            LOGGER.info("timer started")
        else:
            self.toggle_button.setText("Enable")
            self.toggle_tray.setText("Enable")
            LOGGER.info("timer stop")
            self.timer.stop()

    @Slot()
    def open_debug_window(self) -> None:
        """Create debug window and launch it"""
        self.debug_window = DebugWindow(self.eye_th)
        self.debug_window.show()
        LOGGER.info("open debug")
