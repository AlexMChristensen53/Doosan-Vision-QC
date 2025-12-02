# qc_color.py
import numpy as np
import cv2 as cv


class QCColor:
    """
    QC Color (LAB + ΔE)
    -------------------
    Simpel og stabil produktions-version:
        - Brug fast reference LAB
        - Brug fast tolerance
        - Ingen autotune / ingen automatiske ændringer
    """

    def __init__(self,
                 reference_lab=np.array([107.30393, 187.07338, 160.88551]),
                 tolerance_dE=25.0):
        """
        reference_lab:
            Den forventede LAB-farve for et korrekt, rødt emne.
            Denne værdi er fundet via autotune i udviklingsfasen.

        tolerance_dE:
            Max tilladt ΔE for at emnet godkendes.
        """
        self.reference_lab = np.array(reference_lab, dtype=np.float32)
        self.tolerance_dE = tolerance_dE

    # ------------------------------------------------------------
    # ΔE funktion (CIE76)
    # ------------------------------------------------------------
    @staticmethod
    def deltaE(lab1, lab2):
        return np.linalg.norm(lab1 - lab2)

    # ------------------------------------------------------------
    # Evaluer farve for alle objekter
    # ------------------------------------------------------------
    def evaluate_all(self, frame_bgr, form_results):

        lab_frame = cv.cvtColor(frame_bgr, cv.COLOR_BGR2LAB)
        color_results = []

        for fr in form_results:

            box = fr["bbox_points"]
            mask = np.zeros(frame_bgr.shape[:2], dtype=np.uint8)
            cv.drawContours(mask, [box], -1, 255, -1)

            # LAB ROI
            lab_pixels = lab_frame[mask == 255]
            mean_lab = np.mean(lab_pixels, axis=0)

            # ΔE
            dE = self.deltaE(mean_lab, self.reference_lab)
            valid_color = dE <= self.tolerance_dE
            reason = "OK" if valid_color else f"ΔE={dE:.1f} > {self.tolerance_dE}"

            color_results.append({
                "mean_lab": mean_lab,
                "deltaE": dE,
                "valid_color": valid_color,
                "reason": reason
            })

        return color_results

    # ------------------------------------------------------------
    # Overlay
    # ------------------------------------------------------------
    def draw_overlay(self, frame, form_results, color_results):
        vis = frame.copy()

        for fr, cr in zip(form_results, color_results):
            color = (0, 255, 0) if cr["valid_color"] else (0, 0, 255)
            box = fr["bbox_points"]

            cv.polylines(vis, [box], True, color, 2)

            cx, cy = map(int, fr["center"])
            cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)

            cv.putText(vis, f"dE={cr['deltaE']:.1f}",
                       (cx - 30, cy - 10),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        return vis
