import cv2 as cv
import numpy as np
import json
from pathlib import Path
import sys

# ---------------------------------------------
# PATH SETUP
# ---------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from A_Vision.Vision_camera import OakCamera

CONFIG_PATH = ROOT / "C_data" / "object_settings.json"
H_PATH      = ROOT / "C_data" / "calibration_h.npz"

# ---------------------------------------------
# LOAD HSV + OBJECT SETTINGS
# ---------------------------------------------
with open(CONFIG_PATH, "r") as f:
    cfg = json.load(f)

lower    = np.array([cfg["H_low"],  cfg["S_low"],  cfg["V_low"]], dtype=np.uint8)
upper    = np.array([cfg["H_high"], cfg["S_high"], cfg["V_high"]], dtype=np.uint8)
min_area = cfg["min_area"]
blur_k   = cfg["blur_k"]

# ---------------------------------------------
# LOAD HOMOGRAPHY MATRIX (H)
# ---------------------------------------------
H = np.load(H_PATH)["H"]

# ---------------------------------------------
# ROI used during CALIBRATION (IMPORTANT)
# ---------------------------------------------
x1, x2 = 120, 528
y1, y2 = 60, 472

# ---------------------------------------------
# CAMERA INIT (do NOT rotate frame anymore)
# ---------------------------------------------
cam = OakCamera(resolution=(640, 400))

latest_detections = []   # (cx, cy, angle)

# Dimensions for rotation compensation
FRAME_W = 640
FRAME_H = 400

# ---------------------------------------------
# MAIN LOOP
# ---------------------------------------------
while True:
    frame = cam.get_frame()
    if frame is None:
        continue

    # --- Extract ROI JUST LIKE DURING CALIBRATION ---
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    roi = hsv[y1:y2, x1:x2]

    # Blur + mask
    roi_blur = cv.GaussianBlur(roi, (blur_k, blur_k), 0)
    mask = cv.inRange(roi_blur, lower, upper)

    # FIND CONTOURS
    cnts, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    latest_detections = []

    # -----------------------------------------
    # DETECT OBJECTS IN THIS FRAME
    # -----------------------------------------
    for cnt in cnts:
        if cv.contourArea(cnt) < min_area:
            continue

        rot_rect = cv.minAreaRect(cnt)
        (center_local, (w, h), angle) = rot_rect

        # Angle normalization
        object_angle = angle if w < h else angle + 153

        # UNROTATED PIXEL COORDINATES INSIDE FULL FRAME
        cx = int(center_local[0]) + x1
        cy = int(center_local[1]) + y1

        latest_detections.append((cx, cy, object_angle))

        # ----- VISUALIZE ON FRAME -----
        cv.circle(frame, (cx, cy), 5, (0,255,0), -1)

        box = cv.boxPoints(rot_rect)
        box = np.intp(box)
        box[:,0] += x1
        box[:,1] += y1
        cv.drawContours(frame, [box], 0, (0,255,0), 2)

    cv.imshow("frame", frame)
    key = cv.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    # -----------------------------------------
    # SNAPSHOT (PRESS S)
    # -----------------------------------------
    if key == ord('s'):
        print("\n▶ Snapshot: Sorted robot coordinates:\n")

        processed = []  # (dist, X, Y, angle, cx, cy)

        for (cx, cy, angle) in latest_detections:

            # ------------------------------------------------
            # ROTATION COMPENSATION (Instead of rotating image)
            # ------------------------------------------------
            cx_r = FRAME_W - cx
            cy_r = FRAME_H - cy

            # Convert using homography
            p = np.array([cx_r, cy_r, 1.0])
            mapped = H @ p
            X = mapped[0] / mapped[2]
            Y = mapped[1] / mapped[2]

            dist = np.sqrt(X**2 + Y**2)
            processed.append((dist, X, Y, angle, cx, cy))

        # SORT OBJECTS CLOSEST TO ROBOT ORIGIN
        processed.sort(key=lambda x: x[0])

        # PRINT + VISUALIZE
        for idx, (_, X, Y, angle, cx, cy) in enumerate(processed):
            print(f"[Obj {idx}] Robot=({X:.2f}, {Y:.2f}), Angle={angle:.2f}°, Pixel=({cx},{cy})")

            cv.circle(frame, (cx, cy), 8, (0,0,255), -1)
            cv.putText(frame, f"{idx}", (cx + 10, cy - 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv.imshow("frame", frame)

cv.destroyAllWindows()
