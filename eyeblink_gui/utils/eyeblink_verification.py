import time

from blinkdetector.services.blinkdetect import compute_ear


def compute_single_frame(face_detector, keypoint_model, cap, DEVICE) -> int:
    ret, img = cap.read()
    if not ret:
        return 0  # raise error ?

    ear_threshold = 0.2
    left_ear, right_ear = compute_ear(
        img, keypoint_model, face_detector, DEVICE)

    # other possible formula
    # if (left_ear is not None and right_ear is not None and
    # left_ear < ear_threshold and right_ear < ear_threshold):
    if (left_ear is not None and right_ear is not None and
            ((left_ear+right_ear)/2 < ear_threshold)):
        return 1

    return -1
def lack_of_blink_detection(blink_history: List[Tuple[float, int]], duration_lack: int) -> bool:


def lack_of_blink_detection(blink_history) -> bool:
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
