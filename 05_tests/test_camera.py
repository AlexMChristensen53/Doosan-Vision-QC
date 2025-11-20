import cv2 as cv
import depthai as dai
import numpy as np
from transformations import rotation

pipeline = dai.Pipeline()

cam = pipeline.createColorCamera()
cam.setPreviewSize(640, 400)
cam.setInterleaved(False)

xout = pipeline.createXLinkOut()
xout.setStreamName("video")
cam.preview.link(xout.input)

with dai.Device(pipeline) as device:
    q = device.getOutputQueue("video", 4, False)

    while True:
        frame = q.get().getCvFrame()
        rotated = rotation(frame, 180)
        blur = cv.GaussianBlur(rotated, (7, 7), 5)
        edges = cv.Canny(blur, 100, 200)

        cv.imshow("Livefeed, rotated", edges)
        if cv.waitKey(1) == ord('q'):
            break


