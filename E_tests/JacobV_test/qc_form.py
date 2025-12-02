# qc_form.py
import cv2 as cv
import numpy as np

class QCForm:
    """
    QCForm analyserer formen på objekter i et binært mask-billede.
    Returnerer både OK og NOT OK objekter (store objekter),
    men ignorerer små konturer (fx skruehuller og støj).
    """

    def __init__(self, min_area=1000, min_aspect=2.0, max_aspect=7.0,
                 min_solidity=0.88, min_extent=0.90):
        """
        min_area:
            Minimumsareal for et objekt. Alt under dette ignoreres totalt.
            (bruges til at fjerne skruehuller og støj)
        """
        self.min_area = min_area
        self.min_aspect = min_aspect
        self.max_aspect = max_aspect
        self.min_solidity = min_solidity
        self.min_extent = min_extent

    # ------------------------------------------------------------
    # Evaluer ALLE store objekter (små ignoreres)
    # ------------------------------------------------------------
    def evaluate_all(self, mask):
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        results = []

        for cnt in contours:
            area = cv.contourArea(cnt)

            # IGNORÉR ALLE SMÅ KONTURER (skruehuller, støj, knæk)
            if area < self.min_area:
                continue

            r = self.evaluate_single(cnt)
            results.append(r)

        return results

    # ------------------------------------------------------------
    # Evaluér én kontur
    # ------------------------------------------------------------
    def evaluate_single(self, cnt):

        area = cv.contourArea(cnt)

        # bounding rect
        rect = cv.minAreaRect(cnt)
        (cx, cy), (w, h), angle = rect

        # NORMALISER width/height uanset rotation
        w_norm = max(w, h)
        h_norm = min(w, h)

        # form descriptors
        aspect_ratio = w_norm / max(1, h_norm)

        hull = cv.convexHull(cnt)
        hull_area = cv.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0

        extent = area / (w_norm * h_norm) if w_norm * h_norm > 0 else 0

        # form-validation
        valid = True
        reason = "OK"

        if not (self.min_aspect <= aspect_ratio <= self.max_aspect):
            valid = False
            reason = "Aspect ratio out of range"

        if solidity < self.min_solidity:
            valid = False
            reason = "Solidity too low"

        if extent < self.min_extent:
            valid = False
            reason = "Extent too low"

        # boks til overlay
        box = cv.boxPoints(rect)
        box = np.int32(box)

        return {
            "valid": valid,
            "area": area,
            "center": (cx, cy),
            "width": w_norm,
            "height": h_norm,
            "angle": angle,
            "aspect_ratio": aspect_ratio,
            "solidity": solidity,
            "extent": extent,
            "bbox_points": box,
            "reason": reason,
            "contour": cnt,
        }

    # ------------------------------------------------------------
    # Overlay
    # ------------------------------------------------------------
    def draw_overlay(self, frame, results):
        vis = frame.copy()

        for r in results:
            color = (0, 255, 0) if r["valid"] else (0, 0, 255)  # grøn = OK, rød = NOT OK
            box = r["bbox_points"]

            cv.polylines(vis, [box], True, color, 2)

            cx, cy = map(int, r["center"])
            cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)

        return vis
