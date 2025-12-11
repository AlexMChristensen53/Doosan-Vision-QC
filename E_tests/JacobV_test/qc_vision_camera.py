"""
qc_vision_camera.py
Wrapper-klasse til DepthAI/OAK-D kameraet.

Denne klasse håndterer:
- Opsætning af DepthAI-pipelinen
- Start af device og outputqueue
- Indhentning af frames fra kameraet
- Valgfri rotation eller billedbehandling

Klassen abstraherer DepthAI API’et, så resten af systemet kun skal
kalde start(), stop() og get_frame().
"""

import depthai as dai
import cv2 as cv
from pathlib import Path
import time


class OakCamera:
    """
    Wrapper for en OAK-D enhed med DepthAI pipeline.

    Parametre:
        resolution (tuple): (width, height) i pixels for camera preview.

    Attributter:
        pipeline   : DepthAI Pipeline-objekt
        device     : dai.Device instans (initialiseres ved start())
        q_video    : OutputQueue fra kameraet
        initialized: Boolean, om kameraet er startet

    Funktionalitet:
        - start(): opbygger pipeline og åbner connection til kameraet
        - get_frame(): returnerer seneste frame som OpenCV BGR-image
        - stop(): lukker kameraet ned og frigør ressourcer
    """
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
        """
    Initialiserer DepthAI device og opretter output-queue fra kameraet.

    Returnerer:
        True  - hvis kameraet blev initialiseret korrekt.
        False - hvis pipeline/device ikke kunne startes.
    """
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
        """
    Stopper kameraet og frigør DepthAI device-resurser.

    Efter stop() skal kameraet kaldes med start() igen før get_frame() virker.
    """
        if self.device is not None:
            print("[OAK] Closing device...")
            del self.device
        self.initialized = False

    # --------------------------------------------------
    # Get frame with safe handling
    # --------------------------------------------------
    def get_frame(self):
        """
    Returnerer seneste frame fra OAK-kameraet.

    Returnerer:
        ndarray (BGR image) hvis der findes et frame,
        None hvis der ikke modtages data.

    Bemærkning:
        Frame roteres 180° da systemet er kalibreret sådan.
    """
        if not self.initialized:
            return None

        msg = self.q_video.tryGet()
        if msg is None:
            return None

        frame = msg.getCvFrame()

        # 180° rotate
        frame = cv.rotate(frame, cv.ROTATE_180)
        return frame
