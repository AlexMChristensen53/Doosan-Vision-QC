# qc_size.py
import numpy as np


class QCSize:
    """
    QC Size
    -------
    Modulet modtager form-features fra QCForm (width/height i pixels),
    omregner dem til millimeter via mm_per_pixel,
    og validerer om objektets fysiske størrelse er korrekt.
    """

    def __init__(self,
                 mm_per_pixel: float = 0.383,
                 expected_width_mm: float = 96.7,
                 expected_height_mm: float = 25.7,
                 tolerance_width_mm: float = 3.0,
                 tolerance_height_mm: float = 2.0):
        """
        Kalibreringsparametre:

        mm_per_pixel:
            Fast kalibreringsfaktor (mm pr. pixel).

        expected_width_mm / expected_height_mm:
            Objektets FAKTISKE mål i millimeter baseret på billeddata.
            (Efter normalisering fra QC Form)

        tolerance_width_mm / tolerance_height_mm:
            Tilladt afvigelse i mm.
        """
        self.mm_per_pixel = mm_per_pixel
        self.expected_width_mm = expected_width_mm
        self.expected_height_mm = expected_height_mm
        self.tol_w = tolerance_width_mm
        self.tol_h = tolerance_height_mm

    # ------------------------------------------------------------------
    # 1) Evaluér størrelse for alle objekter
    # ------------------------------------------------------------------
    def evaluate_all(self, form_results: list) -> list:
        """
        form_results:
            Liste af dicts returneret fra QC Form.

        Returnerer:
            Liste af dicts med width_mm, height_mm, valid_size, reason
        """
        size_results = []

        for r in form_results:

            # Pixelmål fra QC Form
            w_px = r["width"]
            h_px = r["height"]

            # Konverter pixels → mm
            w_mm = w_px * self.mm_per_pixel
            h_mm = h_px * self.mm_per_pixel

            # Tolerancetjek
            valid_width = abs(w_mm - self.expected_width_mm) <= self.tol_w
            valid_height = abs(h_mm - self.expected_height_mm) <= self.tol_h

            valid_size = valid_width and valid_height

            if not valid_size:
                if not valid_width:
                    reason = f"Width out of tolerance (measured {w_mm:.2f} mm)"
                elif not valid_height:
                    reason = f"Height out of tolerance (measured {h_mm:.2f} mm)"
                else:
                    reason = "Out of tolerance"
            else:
                reason = "OK"

            size_results.append({
                "width_mm": w_mm,
                "height_mm": h_mm,
                "valid_size": valid_size,
                "reason": reason
            })

        return size_results

    # ------------------------------------------------------------------
    # 2) Visualisering: separat SIZES overlay
    # ------------------------------------------------------------------
    def draw_overlay(self, frame, form_results, size_results):
        """
        Tegner boks baseret på størrelse:

            Grøn = størrelse OK
            Rød  = størrelse NOT OK

        form_results: liste fra QCForm (pixels)
        size_results: liste fra QCSize (mm + valid_size)
        """
        import cv2 as cv

        vis = frame.copy()

        for fr, sr in zip(form_results, size_results):

            # Vælg farve
            color = (0, 255, 0) if sr["valid_size"] else (0, 0, 255)

            # Roteret boks
            box = fr["bbox_points"]
            cv.polylines(vis, [box], True, color, 2)

            # Center punkt
            cx, cy = map(int, fr["center"])
            cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)

        return vis
