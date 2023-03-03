import os
import sys
import time

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QGridLayout)

import cv2
import torch
from retinaface import RetinaFace

from blinkdetector.models.heatmapmodel import load_keypoint_model
from eyeblink_gui.utils.eyeblink_verification import compute_single_frame, lack_of_blink_detection


class EyeblinkModelThread(QThread):
    update_label_output = Signal(int)

    def __init__(self, parent=None):
        QThread.__init__(self, parent)

        self.DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.face_detector = RetinaFace(quality="speed")  # speed for better performance
        self.keypoint_model = load_keypoint_model("./assets/ckpt/epoch_80.pth.tar", self.DEVICE)

        self.blink_history = []
        # last_alert = time.time()
        self.cap = cv2.VideoCapture(0)

    def run(self):
        time_start = time.time()
        # id_after = root.after(slider_value, compute_test_camera)
        # print(slider_value)
        # global last_alert
        blink_value = compute_single_frame(self.face_detector,
                                           self.keypoint_model, self.cap, self.DEVICE)

        self.update_label_output.emit(blink_value)
        print("finished")
        # sys.exit(-1)
        # print(len(blink_history), blink_value)
        # blink_history.append((time.time(), blink_value))
        # if (time.time() - last_alert > 20) and lack_of_blink_detection(blink_history):
        #     last_alert = time.time()
        #     root.after_cancel(id_after)
        #     messagebox.showwarning(title="Lack of blink", message="You need to blink")
        #     id_after = root.after(10000, compute_test_camera)  # stop computing for 10s

        # output_model.set(str(blink_value))
        # print("time to process"+str(time.time()-time_start))


class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        # Title and dimensions
        self.setWindowTitle("Eyeblink detection")
        self.setGeometry(0, 0, 800, 500)
        self.window_layout = QGridLayout(self)
        self.window_layout.addWidget(self.create_settings())
        self.pushButton = QPushButton(("Compute one frame"))
        self.pushButton.clicked.connect(self.start)
        self.label_output = QLabel("0")
        self.window_layout.addWidget(self.pushButton)
        self.window_layout.addWidget(self.label_output)

        self.th = EyeblinkModelThread(self)
        self.th.finished.connect(self.finished)
        self.th.update_label_output.connect(self.set_label_output)

    def create_settings(self):
        group_box = QGroupBox(("&Settings"))
        toggleButton = QPushButton(("&Toggle Button"))
        toggleButton.setCheckable(True)
        toggleButton.setChecked(True)
        flatButton = QPushButton(("&Flat Button"))
        flatButton.setFlat(True)
        vbox = QVBoxLayout()
        vbox.addWidget(toggleButton)
        vbox.addWidget(flatButton)
        vbox.addStretch(1)
        group_box.setLayout(vbox)
        return group_box

    @Slot()
    def start(self):
        print("starting thread for computing one frame")
        self.th.start()

    @Slot()
    def finished(self):
        print("Thread is finished")

    @Slot(int)
    def set_label_output(self, output):
        self.label_output.setText(str(output))


if __name__ == "__main__":
    app = QApplication()
    w = Window()
    w.show()
    sys.exit(app.exec())
