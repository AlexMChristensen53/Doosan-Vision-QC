import cv2 as cv
import numpy as np

def generate_mask_from_settings(frame, cfg):
    """
    Recreates the EXACT same mask pipeline as the calibration tool.
    Uses:
      - scale
      - HSV threshold
      - Gaussian blur
      - thresh_mode (global / adaptive mean / adaptive gaussian)
      - block_size
      - C
    Returns:
        Binary mask (uint8, 0/255)
    """

    scale = cfg.get("scale", 1.0)
    h, w = frame.shape[:2]
    frame_small = cv.resize(frame, (int(w * scale), int(h * scale)))

    # HSV mask
    hsv = cv.cvtColor(frame_small, cv.COLOR_BGR2HSV)
    lower = np.array([cfg["H_low"], cfg["S_low"], cfg["V_low"]], dtype=np.uint8)
    upper = np.array([cfg["H_high"], cfg["S_high"], cfg["V_high"]], dtype=np.uint8)
    mask_hsv = cv.inRange(hsv, lower, upper)

    masked = cv.bitwise_and(frame_small, frame_small, mask=mask_hsv)

    # Gray + Blur
    gray = cv.cvtColor(masked, cv.COLOR_BGR2GRAY)

    blur_k = cfg["blur_k"]
    if blur_k < 1: blur_k = 1
    if blur_k % 2 == 0: blur_k += 1
    blur = cv.GaussianBlur(gray, (blur_k, blur_k), 0)

    mode = cfg["thresh_mode"]

    if mode == 0:
        # global threshold (INVERTED because calibration uses INV)
        _, thres = cv.threshold(blur, cfg["global_thresh"], 255, cv.THRESH_BINARY_INV)

    elif mode == 1:
        # adaptive mean
        thres = cv.adaptiveThreshold(
            blur, 255,
            cv.ADAPTIVE_THRESH_MEAN_C,
            cv.THRESH_BINARY_INV,
            cfg["block_size"],
            cfg["C"]
        )

    else:
        # adaptive gaussian
        thres = cv.adaptiveThreshold(
            blur, 255,
            cv.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv.THRESH_BINARY_INV,
            cfg["block_size"],
            cfg["C"]
        )

    return thres
