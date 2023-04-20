"""Class for the thread computing the model"""
import logging
import time
from typing import Optional

import cv2
from blinkdetector.api.model_e2e_openvino_api import E2EOpenVinoModelAPI
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QPixmap
from eyeblink_gui.utils.utils import find_data_file

LOGGER = logging.getLogger(__name__)


class EyeblinkModelThread(QThread):
    """Thread doing the inference of the model and outputting if blink is detected
    callable maximum one at a time
    """
    update_label_output = Signal(int)
    update_debug_img = Signal(QPixmap)
    update_ear_values = Signal(float, float)

    def __init__(self,  parent: Optional[QObject] = None, debug: bool = False) -> None:
        """Initialized the model and class variables,
        these variables are saved between inference and even on different thread

        :param parent: parent of the thread, defaults to None
        """
        QThread.__init__(self, parent)

        LOGGER.info("init thread")

        self.model_api = E2EOpenVinoModelAPI(
            find_data_file("face-detection-adas-0001/FP16-INT8/face-detection-adas-0001.xml"),
            find_data_file("vino_preprocess/lmks.xml"))

        self.cap = None
        self.debug = debug
        # self.init_cap()

    def init_cap(self, input_device: int = 0) -> None:
        """Initialise the capture device with the selected cam

        :param input_device: camera to choose, defaults to 0
        """
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(input_device)  # pylint: disable=no-member

    def run(self) -> None:
        """Run the thread, compute model and signal the image and output"""
        ret, img = self.cap.read()  # type: ignore[attr-defined]
        if not ret:
            raise IOError("No output from camera")

        time_start = time.time()
        blink_value, annotated_img, left_ear, rigth_ear = self.model_api.update(
                                                            img, debug=self.debug)
        LOGGER.info("time to compute frame: %s", str(time.time()-time_start))
        self.update_label_output.emit(blink_value)
        if self.debug:
            # assert annotated_img, f"The image was invalid {annotated_img }"
            annotated_img = cv2.cvtColor(  # pylint: disable=no-member
                annotated_img, cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
            annotated_img = Image.fromarray(annotated_img).convert("RGB")
            self.update_debug_img.emit(QPixmap.fromImage(ImageQt(annotated_img)))
            self.update_ear_values.emit(left_ear, rigth_ear)
