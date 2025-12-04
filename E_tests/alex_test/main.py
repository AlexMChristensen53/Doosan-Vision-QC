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

from qc_vision_camera import OakCamera
from qc_form import QCForm
from Vision_processing import generate_mask_from_settings
from Angle_utility import compute_robot_angle
from mapping import pixel_to_robot

# ---------------------------------------------
# PATHS / CONFIG
# ---------------------------------------------
# Adjust this if your calibration_settings.json is elsewhere
SETTINGS_PATH = "calibration_settings.json"
H_PATH        = "calibration_h.npz"

with open(SETTINGS_PATH, "r") as f:
    cfg = json.load(f)

# Homography matrix
H = np.load(H_PATH)["H"]

# ---------------------------------------------
# ROI USED DURING CALIBRATION (PIXELS)
# ---------------------------------------------
# Make sure these match the ROI you used when you did homography calibration.
x1, x2 = 120, 528
y1, y2 = 60, 472

# Camera reads at full resolution
FRAME_W = 1920
FRAME_H = 1080

# What you display (not used for robot)
DISPLAY_W = 640
DISPLAY_H = 400

# ---------------------------------------------
# CAMERA + QC INIT
# ---------------------------------------------
cam = OakCamera(resolution=(FRAME_W, FRAME_H))

qc = QCForm(
    min_area=1000,
    min_aspect=1.2,
    max_aspect=10.0,
    min_solidity=0.88,
    min_extent=0.80
)

# For snapshot output
latest_detections = []   # list of dicts: {"cx":..., "cy":..., "angle":..., "X":..., "Y":...}


# ---------------------------------------------
# MAIN LOOP
# ---------------------------------------------
while True:
    frame = cam.get_frame()
    if frame is None:
        continue

    # -----------------------------------------
    # 1) EXTRACT ROI LIKE IN CALIBRATION
    # -----------------------------------------
    roi_color = frame[y1:y2, x1:x2]

    # -----------------------------------------
    # 2) BUILD MASK FROM CALIBRATION SETTINGS
    # -----------------------------------------
    mask = generate_mask_from_settings(roi_color, cfg)

    # -----------------------------------------
    # 3) QCForm DETECTION ON MASK
    # -----------------------------------------
    results = qc.evaluate_all(mask)
    latest_detections = []

    # -----------------------------------------
    # 4) PROCESS EACH DETECTED OBJECT
    # -----------------------------------------
    for r in results:
        # QCForm center is in ROI coordinates
        cx_local, cy_local = r["center"]
        w = r["width"]
        h = r["height"]
        raw_angle = r["angle"]

        # Final robot tool angle
        object_angle = compute_robot_angle(w, h, raw_angle)

        # Convert ROI center → global pixel coordinates
        cx = int(cx_local) + x1
        cy = int(cy_local) + y1

        # Pixel → robot using homography + your flip logic
        X, Y = pixel_to_robot(
            cx=cx,
            cy=cy,
            H=H,
            frame_w=FRAME_W,
            frame_h=FRAME_H,
            roi_origin=(x1, y1)
        )

        latest_detections.append({
            "cx": cx,
            "cy": cy,
            "angle": object_angle,
            "X": X,
            "Y": Y
        })

    # -----------------------------------------
    # 5) DRAW QCForm BOXES ON COLOR FRAME
    # -----------------------------------------
    overlay = frame.copy()

    for r in results:
        box = r["bbox_points"].astype(int)
        # shift ROI coords → global coords
        box[:, 0] += x1
        box[:, 1] += y1
        cv.polylines(overlay, [box], True, (0, 255, 0), 2)

    frame = overlay

    # -----------------------------------------
    # 6) SHOW LIVE FEED
    # -----------------------------------------
    preview = cv.resize(frame, (DISPLAY_W, DISPLAY_H))
    cv.imshow("frame", preview)
    cv.imshow("mask", mask)

    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        break

    # -----------------------------------------
    # 7) SNAPSHOT (PRESS 's') → PRINT ROBOT COORDS
    # -----------------------------------------
    if key == ord('s'):
        print("\n▶ Snapshot: Sorted robot coordinates:\n")

        # Build list with distance
        processed = []
        for det in latest_detections:
            X = det["X"]
            Y = det["Y"]
            angle = det["angle"]
            cx = det["cx"]
            cy = det["cy"]

            dist = np.sqrt(X**2 + Y**2)
            processed.append((dist, X, Y, angle, cx, cy))

        # Sort by distance from robot origin (0,0)
        processed.sort(key=lambda x: x[0])

        # Print and label on frame
        for idx, (_, X, Y, angle, cx, cy) in enumerate(processed):
            print(f"[Obj {idx}] Robot=({X:.2f}, {Y:.2f}), "
                  f"Angle={angle:.2f}°, Pixel=({cx},{cy})")

            cv.circle(frame, (cx, cy), 8, (0, 0, 255), -1)
            cv.putText(frame, f"Obj {idx}",
                       (cx + 10, cy - 10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        preview = cv.resize(frame, (DISPLAY_W, DISPLAY_H))
        cv.imshow("frame", preview)

cv.destroyAllWindows()
