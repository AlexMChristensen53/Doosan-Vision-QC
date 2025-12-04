# qc_special.py
import cv2 as cv
import numpy as np


class QCSpecial:
    """
    QCSpecial (skruehuller)
    ------------------------
    Modulet analyserer interne konturer inde i objektet for at sikre:

    • At objektet har præcis det forventede antal skruehuller
    • At hullerne har en minimumsstørrelse (fjerner støj)
    • At der ikke er ekstra indre defekter

    Input kommer fra QCForm → contouren + bbox.
    """

    def __init__(self,
                 expected_hole_count=2,
                 min_hole_area=50,
                 max_hole_area=150):
        """
        expected_hole_count:
            Hvor mange huller et OK objekt skal have.

        min_hole_area:
            Mindste areal for at en intern kontur tæller som et hul.
        """
        self.expected_hole_count = expected_hole_count
        self.min_hole_area = min_hole_area
        self.max_hole_area = max_hole_area

    # ------------------------------------------------------------
    # Evaluér alle objekter (loop over QCForm resultater)
    # ------------------------------------------------------------
    def evaluate_all(self, mask, form_results):
        """
        mask:
            Det komplette binære mask-billede (0/255)

        form_results:
            Liste fra QCForm med bounding boxes og contourinfo

        Returnerer:
            Liste af dicts med:
                - hole_count
                - hole_areas
                - valid_special
                - reason
        """

        results = []

        for fr in form_results:
            box = fr["bbox_points"]

            # 1) Ekstraher ROI baseret på objektets boks
            x, y, w, h = cv.boundingRect(box)
            roi_mask = mask[y:y+h, x:x+w]

            # 2) Find konturer inde i ROI (brug RETR_TREE for hierarki)
            contours, hierarchy = cv.findContours(
                roi_mask, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE
            )

            hole_areas = []
            hole_count = 0

            # 3) Tjek hierarki → interne konturer har parent != -1
            if hierarchy is not None:
                hierarchy = hierarchy[0]  # OpenCV-format

                for cnt, hier in zip(contours, hierarchy):
                    parent = hier[3]

                    if parent != -1:  # intern kontur
                        area = cv.contourArea(cnt)

                        if self.min_hole_area <= area <= self.max_hole_area:
                            hole_areas.append(area)
                            hole_count += 1

            # 4) Validitet
            valid_special = (hole_count == self.expected_hole_count)

            if not valid_special:
                reason = f"Wrong number of holes ({hole_count} found)"
            else:
                reason = "OK"

            results.append({
                "hole_count": hole_count,
                "hole_areas": hole_areas,
                "valid_special": valid_special,
                "reason": reason
            })

        return results

    # ------------------------------------------------------------
    # Overlay til visualisering
    # ------------------------------------------------------------
    def draw_overlay(self, frame, form_results, special_results):
        """
        Tegner:
            - Grøn boks hvis hullerne er OK
            - Rød boks hvis hullerne er NOT OK
            - Markering af hvert hul i cyan
        """
        vis = frame.copy()

        for fr, sr in zip(form_results, special_results):

            color = (0, 255, 0) if sr["valid_special"] else (0, 0, 255)
            box = fr["bbox_points"]

            # tegn objektboks
            cv.polylines(vis, [box], True, color, 2)

            # tegn hullerne (cyan)
            if "hole_centers" in sr:
                for cx, cy in sr["hole_centers"]:
                    cv.circle(vis, (cx, cy), 4, (255, 255, 0), -1)

        return vis
