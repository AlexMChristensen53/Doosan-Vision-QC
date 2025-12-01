# ======================================================
# main.py — FULL QC PIPELINE WITH LIVE OAK-D + OVERLAY
# ======================================================

import cv2 as cv
import numpy as np
from pathlib import Path
import sys

# -------------------------------------------
# PATH SETUP
# -------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

# Import QC modules
from qc_preprocess import QCPreprocess
from qc_form import QCForm
from qc_size import QCSize
from qc_color import QCColor
from qc_special import QCSpecial
from qc_evaluate import QCEvaluate

# Camera
from A_Vision.Vision_camera import OakCamera


# -------------------------------------------
# Draw overlay (with reason text)
# -------------------------------------------
def draw_qc_overlay(frame, form, size, color, special, evaluated):
    vis = frame.copy()

    for f, s, c, sp, ev in zip(form, size, color, special, evaluated):

        overall_ok = ev["overall_ok"]
        color_box = (0,255,0) if overall_ok else (0,0,255)

        box = f["bbox_points"]
        cx, cy = map(int, f["center"])

        cv.polylines(vis, [box], True, color_box, 2)
        cv.circle(vis, (cx, cy), 5, (0,255,255), -1)

        # Status text
        status = "OK" if overall_ok else "NOT OK"
        cv.putText(vis, status, (cx - 40, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color_box, 2)

        # Reason lines
        y = cy + 10
        for r in ev["reasons"]:
            cv.putText(vis, r, (cx - 60, y),
                       cv.FONT_HERSHEY_SIMPLEX, 0.45, (255,255,255), 1)
            y += 18

    return vis



# -------------------------------------------
# Instantiate QC modules
# -------------------------------------------
qc_form    = QCForm()
qc_size    = QCSize()
qc_color   = QCColor(reference_lab=[107.30, 187.07, 160.88], tolerance_dE=25)
qc_special = QCSpecial(min_holes=2, hole_min_area=30)
qc_eval    = QCEvaluate()


# -------------------------------------------
# Camera init
# -------------------------------------------
cam = OakCamera((640, 400))


# -------------------------------------------
# MAIN LOOP
# -------------------------------------------
while True:

    frame = cam.get_frame()
    if frame is None:
        continue

    # 1) PREPROCESS
    mask, gray, thresh, edges, debug = QCPreprocess(frame)

    # 2) QC MODULES
    form_results    = qc_form.evaluate_all(mask)
    size_results    = qc_size.evaluate_all(form_results)
    color_results   = qc_color.evaluate_all(frame, form_results)
    special_results = qc_special.evaluate_all(mask, form_results)

    # 3) QC EVALUATE
    eval_results = qc_eval.evaluate(form_results,
                                    size_results,
                                    color_results,
                                    special_results)

    # 4) Draw overlay
    overlay = draw_qc_overlay(frame,
                              form_results,
                              size_results,
                              color_results,
                              special_results,
                              eval_results)

    # 5) Show
    cv.imshow("QC OVERLAY", overlay)

    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv.destroyAllWindows()
