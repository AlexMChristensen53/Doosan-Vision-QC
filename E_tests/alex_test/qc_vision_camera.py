import depthai as dai
import cv2 as cv
import numpy as np
from qc_vision_tools import rotation
from pathlib import Path
import time

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[0]
PICTURE_FOLDER = PROJECT_ROOT / "C_data" / "Sample_images"

class OakCamera:
    def __init__(self, resolution=(1080, 1080)):
        self.resolution = resolution
        self.pipeline = dai.Pipeline()

        cam = self.pipeline.createColorCamera()
        xout = self.pipeline.createXLinkOut()
        xout.setStreamName("video")

        cam.setPreviewSize(*resolution)
        cam.setInterleaved(False)
        cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        cam.preview.link(xout.input)

        print("[OAK] Starting camera...")
        self.device = dai.Device(self.pipeline)
        self.q_video = self.device.getOutputQueue("video", maxSize=1, blocking=False)

    def get_frame(self):
        frame = self.q_video.tryGet()
        if frame is None:
            return None
        return frame.getCvFrame()


if __name__ == "__main__":
    cam = OakCamera((640, 400))

    while True:
        frame = cam.get_frame()
        if frame is None:
            continue

        frame = rotation(frame, 180)
        cv.imshow("OAK-D Live", frame)

        key = cv.waitKey(1) & 0xFF

        if key == ord('s'):
            filename = PICTURE_FOLDER / f"frame_{int(time.time()*1000)}.png"
            cv.imwrite(str(filename), frame)
            print("Saved:", filename)

        elif key == ord('q'):
            break

    cv.destroyAllWindows()
