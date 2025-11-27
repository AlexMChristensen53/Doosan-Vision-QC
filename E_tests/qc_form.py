# qc_form.py
import cv2 as cv
import numpy as np


class QCForm:
    """
    QCForm analyserer formen på alle objekter i et binært mask-billede.
    QCForm måler hvor rektangulært hvert objekt er ud fra areal, bounding box og hull 
    og markerer store formfejl, men ignorerer små features såsom skruehuller.

    Simple QC Form (v2.2):
        - min_area
        - aspect_ratio i interval
        - solidity >= min_solidity
        - extent >= min_extent
    """

    def __init__(self,
                 min_area: int = 1000,
                 min_aspect: float = 2.0,
                 max_aspect: float = 7.0,
                 min_solidity: float = 0.90,
                 min_extent: float = 0.88):   # <-- ny parameter
        self.min_area = min_area
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect
        self.min_solidity = min_solidity
        self.min_extent = min_extent

    # ------------------------------------------------------------
    # Evaluer ALLE objekter i masken
    # ------------------------------------------------------------
    def evaluate_all(self, mask: np.ndarray) -> list:

        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        results = []

        for cnt in contours:
            area = cv.contourArea(cnt)
            if area < self.min_area:
                continue

            # --- bounding box ---
            rect = cv.minAreaRect(cnt)
            (cx, cy), (w, h), angle = rect

            if min(w, h) == 0:
                continue

            aspect_ratio = max(w, h) / min(w, h)

            # --- solidity ---
            hull = cv.convexHull(cnt)
            hull_area = cv.contourArea(hull)
            if hull_area == 0:
                continue

            solidity = float(area) / hull_area

            # --- extent ---
            bbox_area = w * h
            if bbox_area == 0:
                continue

            extent = area / bbox_area

            # --- form-validering ---
            valid_form = (
                (self.min_aspect <= aspect_ratio <= self.max_aspect) and
                (solidity >= self.min_solidity) and
                (extent >= self.min_extent)   # <-- afgørende filtrering
            )

            box = cv.boxPoints(rect)
            box = np.int32(box)

            results.append({
                "valid": valid_form,
                "area": area,
                "center": (cx, cy),
                "width": w,
                "height": h,
                "angle": angle,
                "aspect_ratio": aspect_ratio,
                "solidity": solidity,
                "extent": extent,
                "bbox_points": box,
            })

        return results

    # ------------------------------------------------------------
    # Overlay: tegn ALLE objekter
    # ------------------------------------------------------------
    def draw_overlay(self, frame: np.ndarray, results: list) -> np.ndarray:
        vis = frame.copy()

        for r in results:
            color = (0, 255, 0) if r["valid"] else (0, 0, 255)  # Grøn = OK, Rød = NOT OK
            box = r["bbox_points"]

            cv.polylines(vis, [box], True, color, 2)

            cx, cy = map(int, r["center"])
            cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)

        return vis
