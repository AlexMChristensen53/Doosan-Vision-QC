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

# QC modules (uændret)
from qc_preprocess import QCPreprocess
from qc_form import QCForm
from qc_size import QCSize
from qc_color import QCColor
from qc_special import QCSpecial
from qc_evaluate import QCEvaluate

# Camera
from qc_vision_camera import OakCamera


# -------------------------------------------
# Instantiate QC modules (samme settings som i test)
# -------------------------------------------
qc_form = QCForm(
    min_area=1500,
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.88,
    min_extent=0.90
)

qc_size = QCSize(
    mm_per_pixel=0.5098,
    expected_width_mm=100.0,
    expected_height_mm=25.0,
    tolerance_width_mm=5.0,
    tolerance_height_mm=3.0
)

qc_color = QCColor(
    reference_lab=[107.30, 187.07, 160.88],
    tolerance_dE=25.0
)

qc_special = QCSpecial(
    expected_hole_count=2,
    min_hole_area=50
)

qc_eval = QCEvaluate()


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

    # -----------------------------
    # 1) PREPROCESS → mask
    # -----------------------------
    mask, gray, thresh, edges, debug = QCPreprocess(frame)

    # -----------------------------
    # 2) QC MODULES
    # -----------------------------
    form_results    = qc_form.evaluate_all(mask)
    size_results    = qc_size.evaluate_all(form_results)
    color_results   = qc_color.evaluate_all(frame, form_results)
    special_results = qc_special.evaluate_all(mask, form_results)

    # -----------------------------
    # 3) COMBINE / FINAL QC
    # -----------------------------
    final_results = qc_eval.combine(
        form_results,
        size_results,
        color_results,
        special_results
    )

    # -----------------------------
    # 4) IDENTISK overlay som test
    # -----------------------------
    overlay = qc_eval.draw_overlay(frame, form_results, final_results)

    # -----------------------------
    # 5) VISUALIZE
    # -----------------------------
    cv.imshow("QC – LIVE OVERLAY", overlay)

    key = cv.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv.destroyAllWindows()
