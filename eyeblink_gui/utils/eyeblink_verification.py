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


def lack_of_blink_detection(blink_history) -> bool:
    current_time = time.time()

    blink_history.reverse()  # newer first
    # finding the index of element
    for blink_tuple in blink_history:
        if blink_tuple[1] == 1:  # blink detected
            since_last_blink_duration = current_time - blink_tuple[0]
            if since_last_blink_duration > 6:
                return True
            # meaning that the last blink was more than 6 second ago
            # meaning there is less than 10 blink per minutes, healthy average is 15-20
            return False
    return False
