# ======================================================
# qc_vision_camera.py — FIXED OAK CAMERA CLASS
# Proper device lifecycle, safe initialization, no lockups
# ======================================================

import depthai as dai
import cv2 as cv
from pathlib import Path
import time


class OakCamera:
    def __init__(self, resolution=(1080, 1080)):
        self.resolution = resolution

        self.pipeline = None
        self.device = None
        self.q_video = None
        self.initialized = False

    # --------------------------------------------------
    # Build DepthAI Pipeline
    # --------------------------------------------------
    def build_pipeline(self):
        print("[OAK] Building pipeline...")
        self.pipeline = dai.Pipeline()

        cam = self.pipeline.createColorCamera()
        cam.setPreviewSize(*self.resolution)
        cam.setInterleaved(False)
        cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)

        xout = self.pipeline.createXLinkOut()
        xout.setStreamName("video")
        cam.preview.link(xout.input)

    # --------------------------------------------------
    # Start OAK device + queues
    # --------------------------------------------------
    def start(self):
        if self.initialized:
            print("[OAK] Already initialized.")
            return True

        if self.pipeline is None:
            self.build_pipeline()

        print("[OAK] Starting device...")

        try:
            self.device = dai.Device(self.pipeline)
            self.q_video = self.device.getOutputQueue(
                "video", maxSize=1, blocking=False
            )
            self.initialized = True
            print("[OAK] Camera READY.")
            return True

        except Exception as e:
            print("[OAK ERROR] Device init failed:", e)
            self.initialized = False
            return False

    # --------------------------------------------------
    # Stop the device (only on program exit)
    # --------------------------------------------------
    def stop(self):
        if self.device is not None:
            print("[OAK] Closing device...")
            del self.device
        self.initialized = False

    # --------------------------------------------------
    # Get frame with safe handling
    # --------------------------------------------------
    def get_frame(self):
        if not self.initialized:
            return None

        msg = self.q_video.tryGet()
        if msg is None:
            return None

        frame = msg.getCvFrame()

        # Single 180° rotate (no double-rotation)
        frame = cv.rotate(frame, cv.ROTATE_180)
        return frame
