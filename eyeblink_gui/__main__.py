from eyeblink_gui.utils.eyeblink_verification import compute_single_frame, lack_of_blink_detection
from blinkdetector.models.heatmapmodel import load_keypoint_model
from retinaface import RetinaFace
import torch
import os
import sys
import time
import numpy as np


import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot, QTimer
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap, QPainter
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QGridLayout,
                               QMessageBox, QSlider)
from PySide6.QtCharts import QBarSeries, QLineSeries, QChart, QBarSet, QValueAxis, QChartView


class BlinkGraph(QWidget):
    def __init__(self):
        super().__init__()

        self.series = QBarSeries()
        self.blink_bar = QBarSet("blink")
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle("How many blink per minutes")
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.chart.createDefaultAxes()

        axis_y = self.chart.axes(Qt.Vertical)[0]
        # axis_x = self.chart.axes(Qt.Horizontal)[0]
        axis_y.setTitleText("Number of blink")
        # axis_x.setTitleText("Minutes")

        self.chart.legend().setVisible(True)
        self.chart.legend().setAlignment(Qt.AlignBottom)

        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)

        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.chart_view, 0, 0, 5, 6)
        self.setLayout(self.main_layout)

    @Slot(list)
    def update_graph(self, blink_history):
        print("updating graph")
        current_time = time.time()
        if blink_history:
            start_of_detection = blink_history[0][0]
            n_minutes = ((int(current_time) - int(start_of_detection))//60)
            blink_per_minutes = [0]+[0]*n_minutes
            for time_code, blink_value in reversed(blink_history):
                current_minute = (int(current_time) - int(time_code))//60
                if blink_value == 1:
                    blink_per_minutes[current_minute] += 1
            blink_per_minutes.reverse()
            print(f"{blink_per_minutes=}")
            self.blink_bar.append(blink_per_minutes)
            self.series.append(self.blink_bar)

        self.chart.createDefaultAxes()

        axis_y = self.chart.axes(Qt.Vertical)[0]
        axis_y.setTitleText("Number of blink")
        axis_y.setRange(0, max(blink_per_minutes))


class EyeblinkModelThread(QThread):
    update_label_output = Signal(int)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        print("init thread")
        self.DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.face_detector = RetinaFace(quality="speed")  # speed for better performance
        self.keypoint_model = load_keypoint_model("./assets/ckpt/epoch_80.pth.tar", self.DEVICE)

        self.blink_history = []
        # last_alert = time.time()
        self.cap = cv2.VideoCapture(0)

    def run(self):
        time_start = time.time()
        blink_value = compute_single_frame(self.face_detector,
                                           self.keypoint_model, self.cap, self.DEVICE)

        self.update_label_output.emit(blink_value)


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        # Title and dimensions
        self.setWindowTitle("Eyeblink detection")
        self.setGeometry(0, 0, 800, 700)
        window_layout = QGridLayout(self)
        window_layout.addWidget(self.create_settings(), 1, 0, 2, 6)
        self.compute_button = QPushButton(("Compute one frame"))
        self.compute_button.clicked.connect(self.start)
        self.label_output = QLabel("0")
        window_layout.addWidget(self.compute_button, 0, 0, 1, 1)
        window_layout.addWidget(self.label_output, 0, 1, 1, 1)

        self.th = EyeblinkModelThread(self)
        self.th.finished.connect(self.finished)
        self.th.update_label_output.connect(self.output_slot)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.start)
        self.timer.setInterval(100)

        self.blink_history = []
        self.blink_messagebox = QMessageBox()
        # self.blink_messagebox.setIcon(QMessageBox.Information)
        self.blink_messagebox.setText("You didn't blink in the last 10 secondes")
        self.blink_messagebox.setInformativeText("Blink now to close the window!")

        self.blink_graph = BlinkGraph()
        self.get_stats = QPushButton(("Update statistics"))
        self.get_stats.clicked.connect(lambda: self.blink_graph.update_graph(self.blink_history))
        window_layout.addWidget(self.get_stats, 3, 0, 1, 6)
        window_layout.addWidget(self.blink_graph, 4, 0, 3, 6)

    def create_settings(self):
        group_box = QGroupBox(("&Settings"))
        self.toggle_label = QLabel(("Enable blinking detection"))
        # self.toggle_label.adjustSize()
        self.toggle_button = QPushButton()
        self.toggle_button.setText("Disabled")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(False)
        # toggleButton.setEnabled(True)
        self.toggle_button.clicked.connect(self.set_timer)

        self.frequency_spin_box = QSpinBox()
        self.frequency_label = QLabel("Interval of the blinking detection:")
        self.frequency_slider = QSlider(Qt.Orientation.Horizontal)
        self.frequency_slider.setSingleStep(50)
        # self.frequency_spin_box.singleStep(50)
        self.frequency_slider.setTickInterval(50)
        self.frequency_slider.setRange(50, 1000)
        self.frequency_spin_box.setRange(50, 1000)
        self.frequency_slider.setTickPosition(QSlider.TickPosition.TicksBothSides)
        self.frequency_slider.setValue(100)
        self.frequency_spin_box.setValue(100)
        self.frequency_slider.valueChanged.connect(self.set_timer_interval)
        self.frequency_spin_box.valueChanged.connect(self.synch_slider)

        self.duration_lack = 10  # minimum duration for considering lack of blink
        self.duration_lack_spin_box = QSpinBox()
        self.duration_lack_spin_box.setRange(5, 60)
        self.duration_lack_spin_box.setValue(self.duration_lack)
        self.duration_lack_spin_box.valueChanged.connect(self.update_duration_lack)
        self.duration_lack_label = QLabel("Minimum duration for considering lack of blink:")
        grid = QGridLayout()
        grid.addWidget(self.toggle_label, 0, 0, 1, 1)
        grid.addWidget(self.toggle_button, 0, 1, 1, 1)
        grid.addWidget(self.frequency_label, 1, 0, 1, 1)
        grid.addWidget(self.frequency_spin_box, 1, 1, 1, 1)
        grid.addWidget(self.frequency_slider, 1, 2, 1, 4)
        grid.addWidget(self.duration_lack_label, 2, 0, 1, 1)
        grid.addWidget(self.duration_lack_spin_box, 2, 1, 1, 1)
        # vbox.addStretch(1)
        group_box.setLayout(grid)
        return group_box

    @ Slot()
    def start(self):
        print("starting thread for computing one frame")
        self.th.start()

    @ Slot()
    def finished(self):
        print("Thread is finished")
        lack_blink = lack_of_blink_detection(self.blink_history, self.duration_lack)
        if lack_blink:
            self.blink_messagebox.exec()

    @ Slot(int)
    def output_slot(self, output):
        self.blink_history.append((time.time(), output))
        if output == 1:
            self.label_output.setText("Blink detected")
            self.blink_messagebox.close()
        else:
            self.label_output.setText("No blink detected")

    @ Slot()
    def set_timer_interval(self, slider_value: int) -> None:
        """Slot called when slider is modified, update the timer value(frequency of the inference)

        :param slider_value: current value of the slider
        """
        self.timer.setInterval(slider_value)
        self.frequency_spin_box.setValue(slider_value)
        print(f"{slider_value=}")

    @Slot()
    def synch_slider(self, spinbox_value: int) -> None:
        """Synch the slider with the spinbox

        :param spinbox_value: current value of the spin box
        """
        self.frequency_slider.setValue(spinbox_value)

    @Slot()
    def update_duration_lack(self, spinbox_value: int) -> None:
        """Update the value of duration_lack

        :param spinbox_value: current value of the spin box
        """
        self.duration_lack = spinbox_value

    @ Slot()
    def set_timer(self):
        print("timer check")
        button_state = self.toggle_button.isChecked()
        if button_state:
            self.toggle_button.setText("Enabled")
            self.timer.start()
            print("timer started")
        else:
            self.toggle_button.setText("Disabled")
            print("timer stop")
            self.timer.stop()


if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())
