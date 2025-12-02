# qc_evaluate.py
import numpy as np


class QCEvaluate:
    """
    QCEvaluate
    ----------
    Samler resultater fra:
        - QC Form
        - QC Size
        - QC Color
        - QC Special

    Et objekt er kun "overall = True" hvis ALLE fire QC-moduler er OK.

    Returnerer ét samlet resultat pr. objekt.
    """

    def combine(self, form_results, size_results, color_results, special_results):
        """
        Kombinerer resultaterne fra alle QC-moduler.

        Input:
            form_results:    liste fra QCForm
            size_results:    liste fra QCSize
            color_results:   liste fra QCColor
            special_results: liste fra QCSpecial

        Output:
            liste af dicts med samlet QC-status
        """

        final_results = []

        for i in range(len(form_results)):
            form   = form_results[i]
            size   = size_results[i]
            color  = color_results[i]
            spec   = special_results[i]

            # Individuelle OK/NOTOK værdier
            form_ok   = form["valid"]
            size_ok   = size["valid_size"]
            color_ok  = color["valid_color"]
            spec_ok   = spec["valid_special"]

            # Samlet OK
            overall_ok = form_ok and size_ok and color_ok and spec_ok

            # Samlede fejlforklaringer
            reasons = []
            if not form_ok:
                reasons.append(f"FORM: {form['reason']}")
            if not size_ok:
                reasons.append(f"SIZE: {size['reason']}")
            if not color_ok:
                reasons.append(f"COLOR: {color['reason']}")
            if not spec_ok:
                reasons.append(f"SPECIAL: {spec['reason']}")

            # Udvidet info til logging/robotik
            result = {
                "overall": overall_ok,

                # Individuelle del-resultater
                "form": form_ok,
                "size": size_ok,
                "color": color_ok,
                "special": spec_ok,

                # Tekster
                "reasons": reasons,

                # Geometri
                "center": form["center"],
                "angle": form["angle"],
                "bbox": form["bbox_points"],
                "width_mm": size["width_mm"],
                "height_mm": size["height_mm"],

                # Avancerede QC-datapunkter
                "deltaE": color["deltaE"],
                "mean_lab": color["mean_lab"],
                "hole_count": spec["hole_count"],
                "hole_areas": spec["hole_areas"],
            }

            final_results.append(result)

        return final_results

    # ------------------------------------------------------------
    # Overlay til samlet QC (grøn = OK, rød = NOT OK)
    # ------------------------------------------------------------
    def draw_overlay(self, frame, form_results, final_results):
        import cv2 as cv

        vis = frame.copy()

        for fr, fr_final in zip(form_results, final_results):

            color = (0, 255, 0) if fr_final["overall"] else (0, 0, 255)
            box   = fr["bbox_points"]

            # tegn boks
            cv.polylines(vis, [box], True, color, 2)

            # center
            cx, cy = map(int, fr["center"])
            cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)

            # tekst: samlet OK/NOTOK
            status_text = "OK" if fr_final["overall"] else "NOT OK"
            cv.putText(vis, status_text,
                       (cx - 20, cy - 10),
                       cv.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 2)

        return vis
