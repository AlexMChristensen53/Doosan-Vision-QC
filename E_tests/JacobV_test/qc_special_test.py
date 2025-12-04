# qc_special_test.py
import cv2 as cv
from qc_form import QCForm
from qc_special import QCSpecial

# ---------------------------------------------------------
# 1. Indlæs maskebillede
# ---------------------------------------------------------
# Brug samme maskefil som QC Form og QC Color
mask = cv.imread("C_data/Sample_images/mask_1764853751.png", cv.IMREAD_GRAYSCALE)

if mask is None:
    raise FileNotFoundError("Maskebillede ikke fundet. Tjek filstien.")

# Lav et farvebillede for overlayvisning
color = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)

# ---------------------------------------------------------
# 2. QC FORM – find objekterne
# ---------------------------------------------------------
qc_form = QCForm(
    min_area=1500,       # ignorer små ting/støj
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.88,
    min_extent=0.90
)

form_results = qc_form.evaluate_all(mask)

print("\n--- QC FORM (objekter fundet) ---")
for i, r in enumerate(form_results):
    print(f"Objekt {i+1}: area={r['area']:.1f}, valid_form={r['valid']}, reason={r['reason']}")
print()

# ---------------------------------------------------------
# 3. QC SPECIAL – evaluér huller
# ---------------------------------------------------------
qc_special = QCSpecial(
    expected_hole_count=2,
    min_hole_area=50
)

special_results = qc_special.evaluate_all(mask, form_results)

print("\n--- QC SPECIAL (skruehuller) ---")
for i, r in enumerate(special_results):
    print(f"Objekt {i+1}: holes={r['hole_count']} → valid={r['valid_special']}, reason={r['reason']}")
print()

# ---------------------------------------------------------
# 4. Tegn overlay
# ---------------------------------------------------------
overlay_special = qc_special.draw_overlay(color, form_results, special_results)

cv.imshow("QC Special – Hulleresultater", overlay_special)
cv.waitKey(0)
cv.destroyAllWindows()
