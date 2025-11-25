import cv2 as cv
import depthai as dai
import numpy as np
#from transformations import rotation
import time

focus_value = 150

pipeline = dai.Pipeline()

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
    ctrl.setManualFocus(50)
    ControlQueue.send(ctrl)

    print(f"Initial Focus Value: ", focus_value)

    while True:
        frame = q.get().getCvFrame()
        cv.imshow("Livefeed, rotated", frame)
        
        focus_value = max(0, min(focus_value, 255))

        
        key = cv.waitKey(1)
        
        if key == ord("."):
            focus_value += 5
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(50)
            ControlQueue.send(ctrl)
            print(f"New Focus Value: ", focus_value)
            
        elif key == ord(","):
            focus_value -= 5
            ctrl = dai.CameraControl()
            ctrl.setManualFocus(50)
            ControlQueue.send(ctrl)
            print(f"New Focus Value: ", focus_value)
        
            
        elif key == ord('q'):
            break
        
        #rotated = rotation(frame, 180)
        #blur = cv.GaussianBlur(rotated, (7, 7), 5)
        #edges = cv.Canny(blur, 100, 200)

        


