import cv2 as cv
import depthai as dai
import numpy as np
from pathlib import Path
import time

# Variables to locate "Sample_images" folder
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
PICTURE_FOLDER = PROJECT_ROOT / "03_data" / "Sample_images"

focus_value = 150  # start focus

pipeline = dai.Pipeline()

# ROI boundaries
x1, x2 = 380, 1478
y1, y2 = 143, 872

# -----------------------
# CREATE CAMERA NODE
# -----------------------
cam = pipeline.createColorCamera()
cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
cam.setInterleaved(False)
cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
cam.setIspScale(1, 1)  # no scaling

# -----------------------
# CONTROL INPUT
# -----------------------
control = pipeline.createXLinkIn()
control.setStreamName("Control")
control.out.link(cam.inputControl)

# -----------------------
# VIDEO OUTPUT
# -----------------------
xout = pipeline.createXLinkOut()
xout.setStreamName("video")
cam.isp.link(xout.input)

# -----------------------
# START DEVICE
# -----------------------
with dai.Device(pipeline) as device:

    q = device.getOutputQueue("video", 4, False)
    ControlQueue = device.getInputQueue("Control")

    # INITIAL CAMERA SETTINGS
    ctrl = dai.CameraControl()
    ctrl.setAutoFocusMode(dai.CameraControl.AutoFocusMode.OFF)
    ctrl.setAutoWhiteBalanceMode(dai.CameraControl.AutoWhiteBalanceMode.AUTO)
    ctrl.setManualExposure(12000, 200)
    ctrl.setManualFocus(focus_value)
    ControlQueue.send(ctrl)


    # Manual exposure: (exposure microseconds, iso)
    ctrl.setManualExposure(12000, 200)

    # Manual focus
    ctrl.setManualFocus(focus_value)
    ControlQueue.send(ctrl)

    print("Initial Focus Value:", focus_value)

    # -----------------------
    # MAIN LOOP
    # -----------------------
    while True:
        frame = q.get().getCvFrame()
        raw_frame = frame.copy()

        # Draw ROI on live view
        cv.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv.imshow("Livefeed", frame)

        key = cv.waitKey(1) & 0xFF

        # SAVE FRAME
        if key == ord('s'):
            filename = PICTURE_FOLDER / f"frame_{int(time.time()*1000)}.png"
            cv.imwrite(str(filename), raw_frame)
            print("Saved:", filename)

        # INCREASE FOCUS
        if key == ord('.'):
            focus_value = min(focus_value + 5, 255)
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(focus_value)
            ControlQueue.send(ctrl)
            print("Focus:", focus_value)

        # DECREASE FOCUS
        elif key == ord(','):
            focus_value = max(focus_value - 5, 0)
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(focus_value)
            ControlQueue.send(ctrl)
            print("Focus:", focus_value)

        # QUIT
        elif key == ord('q'):
            break
