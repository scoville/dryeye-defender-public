"""Class for the thread computing the model"""
import logging
import time
from typing import Optional

import cv2
from blinkdetector.api.filtered_mediapipe_api import FilteredMediaPipeAPI
from PIL import Image
from PIL.ImageQt import ImageQt
from PySide6.QtCore import QObject, QThread, Signal, Slot
from PySide6.QtGui import QPixmap

from dryeye_defender.utils.utils import find_data_file, get_saved_data_path

LOGGER = logging.getLogger(__name__)


class BlinkModelThread(QThread):
    """Thread doing the inference of the model and outputting if blink is detected
    callable maximum one at a time
    """
    update_label_output = Signal(int)
    update_debug_img = Signal(QPixmap)
    update_ear_values = Signal(float, float)

    def __init__(self,
                 blink_value_updated_slot: Slot,
                 thread_finished_slot: Slot,
                 minimum_duration_lack_of_blink_ms: int,
                 parent: Optional[QObject] = None,
                 debug: bool = False) -> None:
        """Initialized the model and class variables,
        these variables are saved between inference and even on different thread

        :param parent: parent of the thread, defaults to None
        :param minimum_duration_lack_of_blink_ms: minimum duration of lack of blink to be considered
        """
        QThread.__init__(self, parent)

        LOGGER.info("init thread")

        self.model_api = FilteredMediaPipeAPI(model_path=find_data_file(
            "mediapipe/face_landmarker_v2_with_blendshapes.task", submodule=True),
            db_path=get_saved_data_path(),
            debug=True)

        self.cap: Optional[cv2.VideoCapture] = None  # pylint: disable=no-member
        self.debug = debug
        self.finished.connect(thread_finished_slot)
        self.update_label_output.connect(blink_value_updated_slot)
        self.model_api.lack_of_blink_threshold = (
            minimum_duration_lack_of_blink_ms
        )

    def init_cap(self, input_device: int = 0) -> None:
        """Initialise the capture device with the selected cam

        :param input_device: camera to choose, defaults to 0
        """
        LOGGER.info("Selecting camera index: %s", input_device)
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(input_device)  # pylint: disable=no-member

    def run(self) -> None:
        """Run the thread, compute model and signal the image and output"""
        time_pre_read = time.time()
        ret, img = self.cap.read()  # type: ignore[union-attr]
        if not ret:
            raise IOError("No output from camera")

        time_start = time.time()
        update_dict = self.model_api.update(img, blink_timestamp_s=time_start)
        time_grab_frame = time_start - time_pre_read
        time_compute_frame = time.time() - time_start
        # A signal used to notify other services of this frame's blink value
        self.update_label_output.emit(update_dict["blink_value"])
        if self.debug:
            annotated_img = cv2.cvtColor(  # pylint: disable=no-member
                update_dict["img"], cv2.COLOR_BGR2RGB)  # pylint: disable=no-member
            annotated_img = Image.fromarray(annotated_img).convert("RGB")
            self.update_debug_img.emit(QPixmap.fromImage(ImageQt(annotated_img)))
            self.update_ear_values.emit(update_dict["left_ear"], update_dict["right_ear"])
        time_taken = time.time() - time_pre_read
        LOGGER.info("inference took: %.6f s, FPS: %.1f. frame_grab took: %.6f s, FPS: %.1f. "
                    "overall took: %.6f s, FPS: %.1f",
                    time_compute_frame,
                    1 / time_compute_frame,
                    time_grab_frame,
                    1 / time_grab_frame,
                    time_taken,
                    1 / time_taken)

    @Slot()
    def start_thread(self) -> None:
        """Slot that call the thread for inference"""
        # The following line ensures we only have one thread processing a frame at a time
        if not self.isRunning():
            LOGGER.debug("starting thread for computing one frame")
            self.start()
        else:
            LOGGER.debug(
                "inference thread already running so skipping computing this frame"
            )
