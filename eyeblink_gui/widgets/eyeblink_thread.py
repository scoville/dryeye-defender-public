import time
from typing import Optional

import cv2
import torch
from blinkdetector.models.heatmapmodel import load_keypoint_model_vino
from PySide6.QtCore import QObject, QThread, Signal
from retinaface import RetinaFace

from eyeblink_gui.utils.eyeblink_verification import (compute_single_frame)


class EyeblinkModelThread(QThread):
    """Thread doing the inference of the model and outputting if blink is detected
    callable maximum one at a time
    """
    update_label_output = Signal(int)

    def __init__(self, parent: Optional[QObject] = None) -> None:
        """Initialized the model and class variables,
        these variables are saved between inference and even on different thread

        :param parent: parent of the thread, defaults to None
        """
        QThread.__init__(self, parent)

        print("init thread")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.face_detector = RetinaFace(quality="speed")  # speed for better performance
        self.keypoint_model = load_keypoint_model_vino(
            "submodules/eyeblink-detection/assets/vino/lmks_opti.xml")

        # last_alert = time.time()
        self.cap = None
        # self.init_cap()

    def init_cap(self, input_device: int = 0) -> None:
        """Initialise the capture device with the selected cam

        :param input_device: camera to choose, defaults to 0
        """
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(input_device)

    def run(self) -> None:
        """Run the inference and emit to a slot the blink value"""
        time_start = time.time()
        blink_value = compute_single_frame(self.face_detector,
                                           self.keypoint_model, self.cap, self.device)
        print("time to compute frame:"+str(time.time()-time_start))
        self.update_label_output.emit(blink_value)
