# qc_size_test.py
import cv2 as cv
from qc_form import QCForm
from qc_size import QCSize

# 1. Indlæs masken
mask = cv.imread("C_data/Sample_images/Mask_sample_1.png", cv.IMREAD_GRAYSCALE)

# 2. QC FORM
qc_form = QCForm(
    min_area=1500,
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.90,
    min_extent=0.88
)

form_results = qc_form.evaluate_all(mask)

# 3. QC SIZE
qc_size = QCSize(
    mm_per_pixel=0.383,
    expected_width_mm=96.7,
    expected_height_mm=25.7,
    tolerance_width_mm=3.0,
    tolerance_height_mm=2.0
)

size_results = qc_size.evaluate_all(form_results)

# Print form-resultater
print("\n--- QC FORM (px) ---")
for i, r in enumerate(form_results):
    print(f"Objekt {i+1}: width={r['width']:.1f}px, height={r['height']:.1f}px, valid_form={r['valid']}")

# Print size-resultater
print("\n--- QC SIZE (mm) ---")
for i, r in enumerate(size_results):
    print(f"Objekt {i+1}: width={r['width_mm']:.2f}mm, height={r['height_mm']:.2f}mm, "
          f"valid_size={r['valid_size']}, reason={r['reason']}")

# 4. Form overlay
color = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
overlay_form = qc_form.draw_overlay(color, form_results)

# 5. Size overlay (separat vindue)
overlay_size = qc_size.draw_overlay(color, form_results, size_results)

cv.imshow("QC Form Overlay", overlay_form)
cv.imshow("QC Size Overlay", overlay_size)
cv.waitKey(0)
