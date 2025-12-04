# Mapping.py

import numpy as np


def pixel_to_robot(
    cx: float,
    cy: float,
    H: np.ndarray,
    frame_w: int,
    frame_h: int,
    roi_origin: tuple[int, int] = (0, 0)
) -> tuple[float, float]:
    """
    Convert pixel coordinates (cx, cy) → robot coordinates (X, Y)
    using a homography matrix H.

    Steps:
        1) Convert local ROI coordinates into full-frame coordinates.
        2) Flip X and Y axes (your camera orientation requirement).
        3) Apply homography H to map into robot coordinate system.
        4) Normalize homogeneous coordinates.

    Args:
        cx, cy:      Pixel center (global coordinates, NOT scaled)
        H:           3x3 homography matrix
        frame_w:     Width of the camera image
        frame_h:     Height of the camera image
        roi_origin:  (x1, y1) offset of ROI in the full frame

    Returns:
        (X, Y) robot coordinates
    """

    x1, y1 = roi_origin

    # ---------------------------------------
    # Step 1 — Convert ROI-local → global pixel coords
    # ---------------------------------------
    cx_global = float(cx)
    cy_global = float(cy)

    # ---------------------------------------
    # Step 2 — Apply your rotation compensation:
    #   (cx_r, cy_r) = (FRAME_W - cx, FRAME_H - cy)
    #
    # This matches EXACTLY what you used during calibration.
    # ---------------------------------------
    cx_r = float(frame_w) - cx_global
    cy_r = float(frame_h) - cy_global

    # ---------------------------------------
    # Step 3 — Apply homography transform
    # ---------------------------------------
    p = np.array([cx_r, cy_r, 1.0])
    mapped = H @ p

    # Normalize homogeneous coordinates
    X = mapped[0] / mapped[2]
    Y = mapped[1] / mapped[2]

    return float(X), float(Y)


def sort_by_distance(objects: list[tuple[float, float, float]], center=(0.0, 0.0)):
    """
    Sort detected objects by distance from robot origin.
    Input format: list of (X, Y, angle)

    Returns: sorted list using Euclidean distance.
    """
    cx, cy = center

    return sorted(
        objects,
        key=lambda obj: np.sqrt((obj[0] - cx)**2 + (obj[1] - cy)**2)
    )
