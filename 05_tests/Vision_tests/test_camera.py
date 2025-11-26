import cv2 as cv
import depthai as dai
import numpy as np
#from transformations import rotation
from pathlib import Path
import matplotlib.pyplot as plt
import time

# Variables to locate "Sample_images" folder
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]
PICTURE_FOLDER = PROJECT_ROOT / "03_data" / "Sample_images"

focus_value = 150

pipeline = dai.Pipeline()

x1, x2 = 380, 1478
y1, y2 = 143, 872

cam = pipeline.createColorCamera()
cam.setIspScale(1, 1)
cam.setInterleaved(False)

control = pipeline.createXLinkIn()
control.setStreamName("Control")
control.out.link(cam.inputControl)

xout = pipeline.createXLinkOut()
xout.setStreamName("video")
cam.isp.link(xout.input)

with dai.Device(pipeline) as device:
    q = device.getOutputQueue("video", 4, False)
    
    ControlQueue = device.getInputQueue(name="Control")
    
    ctrl = dai.CameraControl()
    ctrl.setManualFocus(130)
    ControlQueue.send(ctrl)

    print(f"Initial Focus Value: ", focus_value)

    while True:
        frame = q.get().getCvFrame()
        raw_frame = frame.copy()
        work_frame = frame.copy()
        
        cv.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        
        ROI = frame[y1:y2, x1:x2]
        
        focus_value = max(0, min(focus_value, 255))
        
        cv.imshow("Livefeed, rotated", frame)

        key = cv.waitKey(1) & 0xFF

        if key == ord('s'):
            filename = PICTURE_FOLDER / f"frame_{int(time.time()*1000)}.png"
            cv.imwrite(str(filename), raw_frame)
            print("Saved:", filename)

        
        if key == ord("."):
            focus_value += 5
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(130)
            ControlQueue.send(ctrl)
            print(f"New Focus Value: ", focus_value)
            
        elif key == ord(","):
            focus_value -= 5
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(130)
            ControlQueue.send(ctrl)
            print(f"New Focus Value: ", focus_value)
        
            
        elif key == ord('q'):
            break
        
        #rotated = rotation(frame, 180)
        #blur = cv.GaussianBlur(rotated, (7, 7), 5)
        #edges = cv.Canny(blur, 100, 200)

        


