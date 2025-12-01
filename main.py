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
# ROI USED DURING CALIBRATION
# ---------------------------------------------
x1, x2 = 120, 528
y1, y2 = 60, 472

# ---------------------------------------------
# CAMERA INIT
# ---------------------------------------------
cam = OakCamera(resolution=(640, 400))

# Frame dimensions for rotation compensation
FRAME_W = 640
FRAME_H = 400

latest_detections = []   # (cx, cy, angle)


# ---------------------------------------------
# MAIN LOOP
# ---------------------------------------------
while True:
    frame = cam.get_frame()
    if frame is None:
        continue

    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    # Extract ROI exactly like in calibration
    roi = hsv[y1:y2, x1:x2]
    roi_blur = cv.GaussianBlur(roi, (blur_k, blur_k), 0)

    # HSV mask
    mask = cv.inRange(roi_blur, lower, upper)

    # -----------------------------------------
    # ⭐ MORPHOLOGY PIPELINE FOR STABLE CONTOURS
    # -----------------------------------------
    kernel = np.ones((5,5), np.uint8)

    # Remove tiny noise
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=2)

    # Fill internal gaps
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=2)

    # Smooth edges
    mask = cv.GaussianBlur(mask, (5,5), 0)

    # Sharpen shape
    mask_edges = cv.Canny(mask, 40, 120)
    mask_edges = cv.dilate(mask_edges, kernel, iterations=1)

    # -----------------------------------------
    # FIND CONTOURS
    # -----------------------------------------
    cnts, _ = cv.findContours(mask_edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    latest_detections = []

    # -----------------------------------------
    # DETECT OBJECTS (STABLE VERSION)
    # -----------------------------------------
    for cnt in cnts:
        if cv.contourArea(cnt) < min_area:
            continue

        # Smooth contour to remove jitter
        epsilon = 0.01 * cv.arcLength(cnt, True)
        cnt_smooth = cv.approxPolyDP(cnt, epsilon, True)

        # force longest side to be height
        rot_rect = cv.minAreaRect(cnt_smooth)
        (center_local, (w, h), angle) = rot_rect

        if w > h:
            # swap so h is always the long side
            w, h = h, w
            angle = angle + 27  # rotate angle to follow the long side

        # Normalize to 0–180°
        object_angle = angle % 180


        # Convert ROI → global pixel coords
        cx = int(center_local[0]) + x1
        cy = int(center_local[1]) + y1

        latest_detections.append((cx, cy, object_angle))

        # ----- VISUALIZE -----
        cv.circle(frame, (cx, cy), 5, (0,255,0), -1)

        box = cv.boxPoints(rot_rect)
        box = np.intp(box)
        box[:,0] += x1
        box[:,1] += y1
        cv.drawContours(frame, [box], 0, (0,255,0), 2)

    cv.imshow("frame", frame)

    # single waitKey per loop
    key = cv.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    # -----------------------------------------
    # SNAPSHOT (PRESS S): Sort + Print + Overlay
    # -----------------------------------------
    if key == ord('s'):
        print("\n▶ Snapshot: Sorted robot coordinates:\n")

        processed = []  # (distance, X, Y, angle, cx, cy)

        for (cx, cy, angle) in latest_detections:

            # Rotation compensation (instead of rotating image)
            cx_r = FRAME_W - cx
            cy_r = FRAME_H - cy

            # Pixel → robot using homography
            p = np.array([cx_r, cy_r, 1.0])
            mapped = H @ p
            X = mapped[0] / mapped[2]
            Y = mapped[1] / mapped[2]

            dist = np.sqrt(X**2 + Y**2)
            processed.append((dist, X, Y, angle, cx, cy))

        # Sort closest to robot origin
        processed.sort(key=lambda x: x[0])

        # Print & draw labels
        for idx, (_, X, Y, angle, cx, cy) in enumerate(processed):
            print(f"[Obj {idx}] Robot=({X:.2f}, {Y:.2f}), Angle={angle:.2f}°, Pixel=({cx},{cy})")

            cv.circle(frame, (cx, cy), 8, (0,0,255), -1)
            cv.putText(frame, f"{idx}", (cx + 10, cy - 15),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

        cv.imshow("frame", frame)

cv.destroyAllWindows()
