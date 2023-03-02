import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import cv2
import torch
from retinaface import RetinaFace

from blinkdetector.models.heatmapmodel import load_keypoint_model
from eyeblink_gui.utils.eyeblink_verification import compute_single_frame, lack_of_blink_detection

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def compute_test_camera():
    time_start = time.time()
    id_after = root.after(slider_value, compute_test_camera)
    print(slider_value)
    global last_alert
    blink_value = compute_single_frame(face_detector, keypoint_model, cap, DEVICE)
    print(len(blink_history), blink_value)
    blink_history.append((time.time(), blink_value))
    if (time.time() - last_alert > 20) and lack_of_blink_detection(blink_history):
        last_alert = time.time()
        root.after_cancel(id_after)
        messagebox.showwarning(title="Lack of blink", message="You need to blink")
        id_after = root.after(10000, compute_test_camera)  # stop computing for 10s

    output_model.set(str(blink_value))
    print("time to process"+str(time.time()-time_start))


def set_slider(val):
    global slider_value
    slider_value = val


face_detector = RetinaFace(quality="speed")  # speed for better performance
keypoint_model = load_keypoint_model("./assets/ckpt/epoch_80.pth.tar", DEVICE)

blink_history = []
last_alert = time.time()
slider_value = 300
cap = cv2.VideoCapture(0)

root = tk.Tk()
root.after(2000, compute_test_camera)
frm = ttk.Frame(root, padding=10)
frm.grid()
output_model = tk.StringVar(root, "0")
ttk.Label(frm, text="Activate").grid(column=0, row=0)
ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
ttk.Button(frm, text="Compute camera frame", command=compute_test_camera).grid(column=0, row=1)
ttk.Label(frm, textvariable=output_model).grid(column=1, row=1)
ms_slider = ttk.Scale(root, from_=50, to=300, orient="horizontal",
                      command="set_slider", value=300).grid(column=0, row=3)
root.mainloop()
