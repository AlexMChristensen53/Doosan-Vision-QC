import depthai as dai
import cv2 as cv
import numpy as np


class OakCamera:
    def __init__(self, resolution=(1080, 1080)):
        """
        Initialize the OAK-D camera.
        Creates a DepthAI pipeline with a color camera and XLinkOut.
        """
        self.resolution = resolution
        self.pipeline = dai.Pipeline()

        # Create nodes here
        cam = self.pipeline.createColorCamera()
        xout = self.pipeline.createXLinkOut()

        xout.setStreamName("video")

        # Camera settings
        cam.setPreviewSize(*resolution)
        cam.setInterleaved(False)
        cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

        cam.preview.link(xout.input)

        # Start camera
        print("[OAK] Starting camera...")
        self.device = dai.Device(self.pipeline)
        self.q_video = self.device.getOutputQueue("video", maxSize=1, blocking=False)

    def get_frame(self):
        """
        Returns the latest frame from the OAK camera as a numpy BGR image.
        """
        frame = self.q_video.tryGet()
        if frame is None:
            return None
        return frame.getcvFrame()


if __name__ == "__main__":
    cam = OakCamera((640, 400))

    while True:
        frame = cam.get_frame()
        if frame is not None:
            cv.imshow("OAK-D Live", frame)

        if cv.waitKey(1) & 0xFF == ord('q'):
            break

    cv.destroyAllWindows()
