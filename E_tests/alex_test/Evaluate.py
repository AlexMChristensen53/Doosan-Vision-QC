# qc_evaluate.py

from qc_form import QCForm
from qc_size import QCSize
from qc_color import QColor
from qc_special import QCSpecial




class QCEvaluator:
    """
    Unified quality control pipeline that runs:
        - QCForm   (geometry / shape)
        - QCSize   (dimension tolerances)
        - QCColor  (HSV color checks)
        - QCSpecial (custom project rules)

    Returns a list of objects with:
        {
            "center": (cx, cy),
            "angle": ...,
            "width": ...,
            "height": ...,
            "bbox_points": ...,
            "ok": True/False,
            "reasons": ["shape_bad", "size_fail", ...]
        }
    """

    def __init__(self, cfg_form=None, cfg_size=None, cfg_color=None, cfg_special=None):
        self.qc_form = QCForm(**(cfg_form or {}))
        self.qc_size = QCSize(**(cfg_size or {}))
        self.qc_color = QColor(**(cfg_color or {}))
        self.qc_special = QCSpecial(**(cfg_special or {}))

    def evaluate(self, mask, roi_color):
        """
        mask: binary mask from Vision_processing
        roi_color: BGR image of ROI, for color checks

        Output: list of objects with QC results
        """

        objects = self.qc_form.evaluate_all(mask)
        results = []

        for obj in objects:
            ok = True
            reasons = []

            # ------------------------------
            # SHAPE (QCForm)
            # ------------------------------
            if not obj["valid"]:
                ok = False
                reasons.append("shape_fail")

            # ------------------------------
            # SIZE (QCSize)
            # ------------------------------
            size_ok, size_reason = self.qc_size.check(obj)
            if not size_ok:
                ok = False
                reasons.append(size_reason)

            # ------------------------------
            # COLOR (QColor)
            # ------------------------------
            color_ok, color_reason = self.qc_color.check(obj, roi_color)
            if not color_ok:
                ok = False
                reasons.append(color_reason)

            # ------------------------------
            # SPECIAL (custom)
            # ------------------------------
            special_ok, special_reason = self.qc_special.check(obj)
            if not special_ok:
                ok = False
                reasons.append(special_reason)

            # ------------------------------
            # Build final record
            # ------------------------------
            obj_out = obj.copy()
            obj_out["ok"] = ok
            obj_out["reasons"] = reasons
            results.append(obj_out)

        return results
