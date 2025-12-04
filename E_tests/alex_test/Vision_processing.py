# Vision_processing.py

import cv2 as cv
import numpy as np
from typing import Dict


def _ensure_odd(value: int, minimum: int = 1) -> int:
    """Make sure a kernel size is odd and >= minimum."""
    if value < minimum:
        value = minimum
    if value % 2 == 0:
        value += 1
    return value


def generate_mask_from_settings(frame_bgr: np.ndarray, cfg: Dict) -> np.ndarray:
    """
    Generate a binary mask from a BGR frame using the SAME pipeline as the
    calibration tool (Vision_settings.py).

    - Uses:
        - scale
        - HSV threshold (H_low/high, S_low/high, V_low/high)
        - blur_k
        - thresh_mode (0=global, 1=adaptive mean, 2=adaptive gaussian)
        - global_thresh
        - block_size
        - C

    - Returns:
        mask_full (uint8, 0/255) with SAME size as the input frame.

    This mask is what you should pass into QCForm, or use for contour finding.
    """

    # -----------------------------
    # 1) SCALE FRAME (like calibration)
    # -----------------------------
    h, w = frame_bgr.shape[:2]
    scale = float(cfg.get("scale", 1.0))
    scale = max(0.1, min(scale, 1.0))  # clamp 0.1–1.0 just in case

    new_w = int(w * scale)
    new_h = int(h * scale)

    if new_w <= 0 or new_h <= 0:
        new_w, new_h = w, h
        scale = 1.0

    frame_small = cv.resize(frame_bgr, (new_w, new_h))

    # -----------------------------
    # 2) HSV MASK (same as Vision_settings)
    # -----------------------------
    hsv = cv.cvtColor(frame_small, cv.COLOR_BGR2HSV)

    H_low  = int(cfg["H_low"])
    H_high = int(cfg["H_high"])
    S_low  = int(cfg["S_low"])
    S_high = int(cfg["S_high"])
    V_low  = int(cfg["V_low"])
    V_high = int(cfg["V_high"])

    lower = np.array([H_low, S_low, V_low], dtype=np.uint8)
    upper = np.array([H_high, S_high, V_high], dtype=np.uint8)

    mask_hsv = cv.inRange(hsv, lower, upper)
    masked = cv.bitwise_and(frame_small, frame_small, mask=mask_hsv)

    # -----------------------------
    # 3) GRAY + BLUR (same as calibration)
    # -----------------------------
    gray = cv.cvtColor(masked, cv.COLOR_BGR2GRAY)

    blur_k = _ensure_odd(int(cfg["blur_k"]), minimum=1)
    blur = cv.GaussianBlur(gray, (blur_k, blur_k), 0)

    # -----------------------------
    # 4) THRESHOLDING (thresh_mode 0 / 1 / 2)
    # -----------------------------
    mode = int(cfg["thresh_mode"])
    block_size = _ensure_odd(int(cfg["block_size"]), minimum=3)
    C_val = int(cfg["C"])
    global_thresh = int(cfg["global_thresh"])

    if mode == 0:
        # Global threshold (INVERTED, like calibration)
        _, thres = cv.threshold(
            blur,
            global_thresh,
            255,
            cv.THRESH_BINARY_INV
        )
    elif mode == 1:
        # Adaptive Mean
        thres = cv.adaptiveThreshold(
            blur,
            255,
            cv.ADAPTIVE_THRESH_MEAN_C,
            cv.THRESH_BINARY_INV,
            block_size,
            C_val
        )
    else:
        # Adaptive Gaussian (mode == 2)
        thres = cv.adaptiveThreshold(
            blur,
            255,
            cv.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv.THRESH_BINARY_INV,
            block_size,
            C_val
        )

    # -----------------------------
    # 5) UPSCALE MASK BACK TO FRAME SIZE
    # -----------------------------
    # QCForm & robot logic expect coordinates in the original ROI size.
    # So we resize the threshold mask back to the original frame size.
    mask_full = cv.resize(
        thres,
        (w, h),
        interpolation=cv.INTER_NEAREST  # keep it binary
    )

    return mask_full
