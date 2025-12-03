# angle_utils.py
import cv2 as cv
import numpy as np
from typing import Tuple


def normalize_angle(angle: float) -> float:
    """
    Normaliserer en vinkel til [0, 180) grader.

    Vi arbejder kun med linjens retning (ikke pilens retning),
    så +v og -v repræsenterer samme akse → 0–180° er nok.
    """
    return float(angle % 180.0)


def pca_angle(contour: np.ndarray) -> float:
    """
    Stabil vinkelberegning vha. PCA.

    Input:
        contour: Nx1x2 eller Nx2 array af punkter fra cv.findContours

    Output:
        vinkel i grader i intervallet [0, 180)
        0°  = linjen peger vandret mod højre (x-akse)
        90° = linjen peger lodret nedad (y-akse, billedkoordinat)

    Fordele:
        - Ingen 81° → 182° flip
        - Uafhængig af bounding box / minAreaRect
        - Følger objektets længste retning
    """
    if contour.ndim == 3:
        pts = contour.reshape(-1, 2)
    else:
        pts = contour

    pts = pts.astype(np.float32)

    # Brug OpenCV PCA (hurtig og nem)
    mean, eigenvectors = cv.PCACompute(pts, mean=None)
    # Første egenvektor svarer til største egenværdi (længste retning)
    vx, vy = eigenvectors[0]

    angle_rad = np.arctan2(vy, vx)
    angle_deg = np.degrees(angle_rad)

    return normalize_angle(angle_deg)


def enforce_long_side(w: float,
                      h: float,
                      angle: float,
                      long_side_min: float = 40.0) -> Tuple[float, float, float]:
    """
    Hvis du stadig bruger width/height fra minAreaRect, kan du sikre at 'h'
    altid er den lange side og rotere vinklen 90° hvis nødvendigt.

    Bruges fx til SIZE-QC der forventer at højden ~ længste side.

    Returnerer:
        (w_fix, h_fix, angle_fix) med angle_fix i [0, 180)
    """
    angle = normalize_angle(angle)

    if w > long_side_min and w > h:
        w, h = h, w
        angle = normalize_angle(angle + 90.0)

    return float(w), float(h), float(angle)


def draw_orientation(
    img: np.ndarray,
    center: Tuple[float, float],
    angle_deg: float,
    length: float = 60.0,
    color: Tuple[int, int, int] = (0, 255, 255),
    thickness: int = 2
) -> np.ndarray:
    """
    Tegner en pil fra center i retning af vinklen (debug).

    img    : BGR billede
    center : (cx, cy) i pixels
    angle_deg : vinkel i grader (0–180)
    """
    cx, cy = center
    theta = np.deg2rad(angle_deg)

    x2 = int(cx + length * np.cos(theta))
    y2 = int(cy + length * np.sin(theta))

    cv.arrowedLine(
        img,
        (int(cx), int(cy)),
        (x2, y2),
        color,
        thickness,
        tipLength=0.2,
    )
    return img
