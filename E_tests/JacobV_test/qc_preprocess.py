# =======================================================
# qc_preprocess.py
# =======================================================

import cv2 as cv
import numpy as np
import json
from pathlib import Path

# -----------------------------
# SETTINGS PATH (GLOBAL)
# -----------------------------
ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[0]                     # <-- vigtigt!
SETTINGS_FILE = PROJECT_ROOT / "qc_calibration_settings.json"


# -----------------------------
# LOAD SETTINGS
# -----------------------------
def load_settings():
    if not SETTINGS_FILE.exists():
        raise FileNotFoundError(f"Settings fil mangler: {SETTINGS_FILE}")

    with open(SETTINGS_FILE, "r") as f:
        cfg = json.load(f)

    return cfg


# -----------------------------
# MAIN PREPROCESS FUNCTION
# -----------------------------
def QCPreprocess(frame):
    """
    Input: RAW frame (BGR)
    Output:
        mask           (HSV mask)
        gray           (Grayscale of masked frame)
        thresh         (Adaptive or global threshold)
        edges          (Canny edges)
        debug_overlay  (Contour overlay for debugging)
    """

    cfg = load_settings()

    # HSV ranges
    lower = np.array([cfg["H_low"],  cfg["S_low"],  cfg["V_low"]], dtype=np.uint8)
    upper = np.array([cfg["H_high"], cfg["S_high"], cfg["V_high"]], dtype=np.uint8)

    blur_k      = int(cfg["blur_k"])
    global_thr  = int(cfg["global_thresh"])
    thresh_mode = int(cfg["thresh_mode"])
    block_size  = int(cfg["block_size"])
    C_val       = int(cfg["C"])
    canny_low   = int(cfg["canny_low"])
    canny_high  = int(cfg["canny_high"])
    min_area    = int(cfg["min_area"])

    # Ensure valid kernel sizes
    if blur_k < 1: blur_k = 1
    if blur_k % 2 == 0: blur_k += 1
    if block_size < 3: block_size = 3
    if block_size % 2 == 0: block_size += 1
    if canny_high <= canny_low:
        canny_high = canny_low + 1

    # -----------------------------
    # 1. HSV Mask
    # -----------------------------
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, lower, upper)
    masked = cv.bitwise_and(frame, frame, mask=mask)

    # -----------------------------
    # 2. Blur + Gray
    # -----------------------------
    gray = cv.cvtColor(masked, cv.COLOR_BGR2GRAY)
    blur = cv.GaussianBlur(gray, (blur_k, blur_k), 0)

    # -----------------------------
    # 3. Threshold modes
    # -----------------------------
    if thresh_mode == 0:
        _, thresh = cv.threshold(blur, global_thr, 255, cv.THRESH_BINARY_INV)

    elif thresh_mode == 1:
        thresh = cv.adaptiveThreshold(
            blur, 255,
            cv.ADAPTIVE_THRESH_MEAN_C,
            cv.THRESH_BINARY_INV,
            block_size, C_val)

    else:
        thresh = cv.adaptiveThreshold(
            blur, 255,
            cv.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv.THRESH_BINARY_INV,
            block_size, C_val)

    # -----------------------------
    # 4. Edges
    # -----------------------------
    edges = cv.Canny(blur, canny_low, canny_high)

    # -----------------------------
    # 5. Contour Overlay (debug)
    # -----------------------------
    contours, _ = cv.findContours(edges, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
    big_contours = [c for c in contours if cv.contourArea(c) >= min_area]

    debug_overlay = frame.copy()
    cv.drawContours(debug_overlay, big_contours, -1, (0, 0, 255), 2)

    return mask, gray, thresh, edges, debug_overlay


# -----------------------------
# END OF FILE
# -----------------------------
