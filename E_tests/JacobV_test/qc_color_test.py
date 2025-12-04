# qc_color_test.py
import cv2 as cv
import numpy as np

from qc_form import QCForm
from qc_color import QCColor

# ---------------------------------------------------------
# 1. Indlæs inputbilleder
# ---------------------------------------------------------
frame = cv.imread("C_data/Sample_images/frame_actual.png")
mask = cv.imread("C_data/Sample_images/mask_1764853751.png", cv.IMREAD_GRAYSCALE)

# ---------------------------------------------------------
# 2. QC FORM
# ---------------------------------------------------------
qc_form = QCForm(
    min_area=1500,
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.88,
    min_extent=0.90
)

form_results = qc_form.evaluate_all(mask)

# ---------------------------------------------------------
# 3. QC COLOR (produktionsmode)
# ---------------------------------------------------------
qc_color = QCColor(
    reference_lab=np.array([107.30393, 187.07338, 160.88551]),
    tolerance_dE=25.0
)

color_results = qc_color.evaluate_all(frame, form_results)

# ---------------------------------------------------------
# 4. VISUALISERING
# ---------------------------------------------------------
overlay = qc_color.draw_overlay(frame, form_results, color_results)

cv.imshow("QC Color Overlay", overlay)
cv.waitKey(0)
cv.destroyAllWindows()
