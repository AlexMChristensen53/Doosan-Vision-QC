# qc_evaluate.py
from pathlib import Path
import sys
import numpy as np
import cv2 as cv

# ---------------------------------------------
# PATH SETUP
# ---------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from qc_form import QCForm
from qc_size import QCSize
from qc_color import QCColor
from qc_special import QCSpecial

class QCEvaluator:
    """
    Unified QC pipeline.

    Runs all modules:
        - QCForm    (geometry & contour shape)
        - QCSize    (dimension tolerances)
        - QCColor   (color checks)
        - QCSpecial (custom rules)
    """

    def __init__(self,
                 cfg_form=None,
                 cfg_size=None,
                 cfg_color=None,
                 cfg_special=None):

        self.qc_form = QCForm(**(cfg_form or {}))
        self.qc_size = QCSize(**(cfg_size or {}))
        self.qc_color = QCColor(**(cfg_color or {}))
        self.qc_special = QCSpecial(**(cfg_special or {}))

    # ------------------------------------------------------------
    # MAIN QC FUNCTION
    # ------------------------------------------------------------
    def evaluate(self, mask, roi_color):
        """
        Runs all QC checks and combines the results.
        
        mask       = grayscale or binary mask (uint8)
        roi_color  = BGR image of ROI

        Returns a list of objects with:
            {
                "overall": True/False,
                "reasons": [...],
                "center": (cx,cy),
                "angle": angle,
                "bbox_points": [...],
                "width_mm": ...,
                "height_mm": ...,
                ...
            }
        """

        # 1) SHAPE (QCForm)
        form_results = self.qc_form.evaluate_all(mask)

        final_results = []

        # Run the other QC modules one object at a time
        for form in form_results:

            # ----------------------------------
            # SIZE
            # ----------------------------------
            size_ok, size_reason, size_data = self.qc_size.check(form)

            # ----------------------------------
            # COLOR
            # ----------------------------------
            color_ok, color_reason, color_data = self.qc_color.check(form, roi_color)

            # ----------------------------------
            # SPECIAL
            # ----------------------------------
            spec_ok, spec_reason, spec_data = self.qc_special.check(form)

            # ----------------------------------
            # COMBINE RESULTS
            # ----------------------------------
            reasons = []
            if not form["valid"]:
                reasons.append(form["reason"])
            if not size_ok:
                reasons.append(size_reason)
            if not color_ok:
                reasons.append(color_reason)
            if not spec_ok:
                reasons.append(spec_reason)

            overall_ok = form["valid"] and size_ok and color_ok and spec_ok

            result = {
                "overall": overall_ok,
                "reasons": reasons,

                # Geometry
                "center": form["center"],
                "angle": form["angle"],
                "bbox_points": form["bbox_points"],
                "width": form["width"],
                "height": form["height"],

                # Size QC
                "width_mm": size_data.get("width_mm"),
                "height_mm": size_data.get("height_mm"),

                # Color QC
                "mean_lab": color_data.get("mean_lab"),
                "deltaE": color_data.get("deltaE"),

                # Special QC
                "hole_count": spec_data.get("hole_count"),
                "hole_areas": spec_data.get("hole_areas"),
            }

            final_results.append(result)

        return final_results

    # ------------------------------------------------------------
    # OVERLAY DRAWING
    # ------------------------------------------------------------
    def draw_overlay(self, frame, results):
        vis = frame.copy()

        for res in results:
            box = res["bbox_points"].astype(int)

            color = (0, 255, 0) if res["overall"] else (0, 0, 255)

            cv.polylines(vis, [box], True, color, 2)

            cx, cy = map(int, res["center"])
            cv.circle(vis, (cx, cy), 4, (0, 255, 255), -1)

            status = "OK" if res["overall"] else "NOK"
            cv.putText(vis, status,
                       (cx - 20, cy - 10),
                       cv.FONT_HERSHEY_SIMPLEX,
                       0.6, color, 2)

        return vis
