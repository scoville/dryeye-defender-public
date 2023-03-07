"""Utils function"""
import time
from typing import Any, List, Tuple

import torch
from blinkdetector.models.heatmapmodel import HeatMapLandmarker
from blinkdetector.services.blinkdetect import compute_ear
from retinaface import RetinaFace


def compute_single_frame(face_detector: RetinaFace, keypoint_model: HeatMapLandmarker,
                         cap: Any, device: torch.device) -> int:
    """Wrapper for calling function from blinkdetector library, compute ear threshold

    :param face_detector: model object of the face detector
    :param keypoint_model: model object to detect keypoint
    :param cap: capture device cv2 object
    :param device: cuda device
    :return: blink value from inference, 1 if detected blink else -1
    """
    ret, img = cap.read()
    if not ret:
        return 0  # raise error ?

    ear_threshold = 0.2
    left_ear, right_ear = compute_ear(img, keypoint_model, face_detector, device)

    # other possible formula
    # if (left_ear is not None and right_ear is not None and
    # left_ear < ear_threshold and right_ear < ear_threshold):
    if (left_ear is not None and right_ear is not None and
            ((left_ear+right_ear)/2 < ear_threshold)):
        return 1
    return -1


def lack_of_blink_detection(blink_history: List[Tuple[float, int]], duration_lack: int) -> bool:
    """Check if there is a lack of blink from the history

    :param blink_history: List of blink value(1 if detected blink, else -1) associated with time
    :param duration_lack: minimum duration for considering lack of blink

    :return: true if no blink for the last ?? second (=> lack of blink)
    """
    current_time = time.time()

    for time_code, blink_value in reversed(blink_history):
        # search for the last detected blink
        if blink_value == 1:  # blink detected
            since_last_blink_duration = current_time - time_code  # how long ago was the last blink

            if since_last_blink_duration > duration_lack:  # is it was more than 10s ago
                print(f"{time_code=}{blink_value=}{since_last_blink_duration=}")
                return True
            # meaning that the last blink was more than 6 second ago
            # meaning there is less than 10 blink per minutes, healthy average is 15-20
            return False
    return False
