"""Main qt file, containing code for the qt window etc"""
import sys
import time
from typing import List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (QApplication, QComboBox, QGridLayout, QGroupBox,
                               QLabel, QMainWindow, QMenu, QMessageBox,
                               QPushButton, QSlider, QSpinBox, QSystemTrayIcon,
                               QWidget)

from eyeblink_gui.utils.eyeblink_verification import lack_of_blink_detection
from eyeblink_gui.utils.utils import get_cap_indexes
from eyeblink_gui.widgets.blink_graph import BlinkGraph
from eyeblink_gui.widgets.eyeblink_thread import EyeblinkModelThread


class Window(QWidget):
    """Widget of the main window"""

    # pylint: disable=too-many-instance-attributes
    def __init__(self,  parent: Optional[QWidget] = None) -> None:
        """Initialize all variable and create the layout of the window
        :param parent: parent of the widget, defaults to None
        """
        super().__init__(parent)

        self.duration_lack = 10  # minimum duration for considering lack of blink
        window_layout = QGridLayout(self)

        self.compute_button = QPushButton(("Compute one frame"))
        self.compute_button.clicked.connect(self.start_thread)  # type: ignore[attr-defined]
        self.label_output = QLabel("0")
        window_layout.addWidget(self.compute_button, 0, 0, 1, 1)
        window_layout.addWidget(self.label_output, 0, 1, 1, 1)

        self.eye_th = EyeblinkModelThread(self)
        self.eye_th.finished.connect(self.thread_finished)  # type: ignore[attr-defined]
        self.eye_th.update_label_output.connect(self.output_slot)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start_thread)  # type: ignore[attr-defined]
        self.timer.setInterval(100)

        self.blink_history: List[Tuple[float, int]] = []

        self.time_last_finished_th = 0.0
        self.label_fps = QLabel("fps: 0")
        window_layout.addWidget(self.label_fps, 0, 2, 1, 1)

        self.tray_available = QSystemTrayIcon.isSystemTrayAvailable() and \
            QSystemTrayIcon.supportsMessages()
        if self.tray_available:
            self.alert_mode = "notification"
            self.tray = self.create_tray()
        else:
            self.alert_mode = "popup"
        self.blink_messagebox = self.create_messagebox()

        self.blink_graph = BlinkGraph()
        self.get_stats = QPushButton(("Update statistics"))
        self.get_stats.clicked.connect(  # type: ignore[attr-defined]
            lambda: self.blink_graph.update_graph(self.blink_history))
        window_layout.addWidget(self.create_settings(), 1, 0, 2, 6)
        window_layout.addWidget(self.get_stats, 3, 0, 1, 6)
        window_layout.addWidget(self.blink_graph, 4, 0, 3, 6)

    def create_messagebox(self) -> QMessageBox:
        """Initialize messagebox for later usage

        :return: return the messagebox object
        """
        blink_messagebox = QMessageBox()
        blink_messagebox.setIcon(QMessageBox.Icon.Information)
        blink_messagebox.setText(f"You didn't blink in the last {self.duration_lack} secondes")
        blink_messagebox.setInformativeText("Blink now to close the window!")
        return blink_messagebox

    def create_tray(self) -> QSystemTrayIcon:
        """Initialize system tray

        :return: Return the system tray initialized
        """
        print("using system tray")
        menu = QMenu()
        self.toggle_tray = menu.addAction("Disabled")
        quit_tray = menu.addAction("Quit")
        quit_tray.triggered.connect(sys.exit)  # type: ignore[attr-defined]
        # self.toggle_tray.triggered.connect(self.set_timer)

        tray = QSystemTrayIcon(icon)
        tray.setContextMenu(menu)
        # system_tray.setContextMenu()
        tray.setVisible(True)
        tray.showMessage("Test", "Tray initialized", icon, 5000)
        return tray

    def create_frequency_slider(self) -> None:
        """Create frequency slider for settings"""
        self.frequency_spin_box = QSpinBox()
        self.frequency_label = QLabel("Interval of the blinking detection (ms):")
        self.frequency_slider = QSlider(Qt.Orientation.Horizontal)
        self.frequency_slider.setSingleStep(50)
        # self.frequency_spin_box.singleStep(50)
        self.frequency_slider.setTickInterval(50)
        self.frequency_slider.setRange(50, 1000)
        self.frequency_spin_box.setRange(50, 1000)
        self.frequency_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.frequency_slider.setValue(100)
        self.frequency_spin_box.setValue(100)
        self.frequency_slider.valueChanged.connect(  # type: ignore[attr-defined]
            self.set_timer_interval)
        self.frequency_spin_box.valueChanged.connect(  # type: ignore[attr-defined]
            self.sync_slider)

    def create_toggle_settings(self) -> None:
        """Create toggle widget for toggle settings"""
        self.toggle_label = QLabel(("Enable blinking detection:"))
        # self.toggle_label.adjustSize()
        self.toggle_button = QPushButton()
        self.toggle_button.setText("Disabled")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        # toggleButton.setEnabled(True)
        self.toggle_button.clicked.connect(self.set_timer)  # type: ignore[attr-defined]
        self.toggle_tray.triggered.connect(  # type: ignore[attr-defined]
            self.toggle_button.nextCheckState)
        self.toggle_tray.triggered.connect(self.set_timer)  # type: ignore[attr-defined]

    def create_alert_settings(self) -> None:
        self.alert_mode_label = QLabel(("Lack of blink alert (Window popup|OS notification)"))
        self.alert_mode_button = QPushButton()
        self.alert_mode_button.setText(self.alert_mode)
        # togalert_mode_buttonEnabled(True)
        self.alert_mode_button.clicked.connect(self.switch_mode)  # type: ignore[attr-defined]
        if not self.tray_available:
            self.alert_mode_button.setEnabled(False)

    def create_duration_settings(self) -> None:
        """Create duration for settings button and label"""
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(5, 60)
        self.duration_lack_spin_box.setValue(self.duration_lack)
        self.duration_lack_spin_box.valueChanged.connect(  # type: ignore[attr-defined]
            self.update_duration_lack)
        self.duration_lack_label = QLabel("Minimum duration for considering lack of blink (s):")

    def create_select_cam_settings(self) -> None:
        """Create select cam and label cam """
        self.select_cam_label = QLabel(("Choose which camera device to use"))
        self.select_cam = QComboBox()
        try:
            cap_indexes = get_cap_indexes()
            self.select_cam.addItems(cap_indexes)
            self.eye_th.init_cap(int(cap_indexes[0]))
        except ValueError as err:
            print(err)
            self.toggle_button.setEnabled(False)
            self.alert_no_cam()
        self.select_cam.activated.connect(lambda: self.eye_th.init_cap(int(self.select_cam.currentText())))

    def create_settings(self) -> QGroupBox:
        """Initialize all variable/object for the settings part of the program"""
        group_box = QGroupBox(("&Settings"))
        self.create_toggle_settings()
        self.create_alert_settings()
        self.create_frequency_slider()
        self.create_duration_settings()
        self.create_select_cam_settings()

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
        grid.addWidget(self.select_cam_label, 4, 0, 1, 1)
        grid.addWidget(self.select_cam, 4, 1, 1, 1)
        # vbox.addStretch(1)
        group_box.setLayout(grid)
        return group_box

    def alert_no_cam(self) -> None:
        """Alert the user with a window popup that there is no webcam connected"""

        no_cam_messagebox = QMessageBox()
        no_cam_messagebox.setIcon(QMessageBox.Icon.Warning)
        no_cam_messagebox.setText(f"No webcam has been detected")
        no_cam_messagebox.setInformativeText("Connect a webcam for blinking detection")
        no_cam_messagebox.exec()

    @Slot()
    def start_thread(self) -> None:
        """Slot that call the thread for inference"""
        if not self.eye_th.isRunning():
            print("starting thread for computing one frame")
            self.eye_th.start()

    @Slot()
    def thread_finished(self) -> None:
        """Slot called at the end of the thread, and manage the lack of blink detection"""
        print("Thread is finished")
        diff_time = time.time() - self.time_last_finished_th
        self.time_last_finished_th = time.time()
        self.label_fps.setText(f"fps:{str(int(1/diff_time))}")
        lack_blink = lack_of_blink_detection(self.blink_history, self.duration_lack)
        if lack_blink:
            print("Lack of blink detected")
            if self.alert_mode == "popup":
                self.blink_messagebox.exec()
            else:
                self.tray.showMessage(f"You didn't blink in the last {self.duration_lack} secondes",
                                      "Blink now to close the window!", icon, 5000)

    @Slot()
    def output_slot(self, output: int) -> None:
        """Slot called when the output from the thread is ready

        :param output: output for the frame processed 1 for blink detected, -1 for no blink
        """
        self.blink_history.append((time.time(), output))
        if output == 1:
            self.label_output.setText("Blink detected")
            if self.alert_mode == "popup":
                self.blink_messagebox.close()
        else:
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
        print(f"{slider_value=}")

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

    @Slot()
    def set_timer(self) -> None:
        """Slot called when automatic inference is enable, manage button and timer state"""
        print("timer check")
        button_state = self.toggle_button.isChecked()
        if button_state:
            self.toggle_button.setText("Enabled")
            self.toggle_tray.setText("Enabled")
            self.blink_history = [(time.time(), 1)]
            # initialize with a blink, maybe need to change
            self.timer.start()
            print("timer started")
        else:
            self.toggle_button.setText("Disabled")
            self.toggle_tray.setText("Disabled")
            print("timer stop")
            self.timer.stop()


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
