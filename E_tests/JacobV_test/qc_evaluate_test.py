# qc_evaluate_test.py
import cv2 as cv

from qc_form import QCForm
from qc_size import QCSize
from qc_color import QCColor
from qc_special import QCSpecial
from qc_evaluate import QCEvaluate

# ---------------------------------------------------------
# 1. Indlæs billeder
# ---------------------------------------------------------
frame = cv.imread("C_data/Sample_images/frame_1764333461.png")
mask  = cv.imread("C_data/Sample_images/mask_1764333461.png", cv.IMREAD_GRAYSCALE)

if frame is None:
    raise FileNotFoundError("Kunne ikke indlæse frame_1764333461.png")
if mask is None:
    raise FileNotFoundError("Kunne ikke indlæse mask_1764333461.png")

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

print("\n--- QC FORM ---")
for i, r in enumerate(form_results):
    print(f"Objekt {i+1}: valid={r['valid']}, reason={r['reason']}, "
          f"area={r['area']:.1f}, aspect={r['aspect_ratio']:.2f}, "
          f"solidity={r['solidity']:.3f}, extent={r['extent']:.3f}")
print()

# ---------------------------------------------------------
# 3. QC SIZE
# ---------------------------------------------------------
qc_size = QCSize(
    mm_per_pixel=0.5098,
    expected_width_mm=100.0,
    expected_height_mm=25.0,
    tolerance_width_mm=5.0,
    tolerance_height_mm=3.0
)


size_results = qc_size.evaluate_all(form_results)

print("\n--- QC SIZE ---")
for i, r in enumerate(size_results):
    print(f"Objekt {i+1}: valid_size={r['valid_size']}, reason={r['reason']}, "
          f"width={r['width_mm']:.2f}mm, height={r['height_mm']:.2f}mm")
print()

# ---------------------------------------------------------
# 4. QC COLOR
# ---------------------------------------------------------
reference_lab = [107.30, 187.07, 160.88]  # fra autotune

qc_color = QCColor(
    reference_lab=reference_lab,
    tolerance_dE=25.0
)

color_results = qc_color.evaluate_all(frame, form_results)

print("\n--- QC COLOR (LAB + ΔE) ---")
for i, r in enumerate(color_results):
    print(f"Objekt {i+1}: valid_color={r['valid_color']}, reason={r['reason']}, "
          f"ΔE={r['deltaE']:.2f}")
print()

# ---------------------------------------------------------
# 5. QC SPECIAL (skruehuller)
# ---------------------------------------------------------
qc_special = QCSpecial(
    expected_hole_count=2,
    min_hole_area=50
)

special_results = qc_special.evaluate_all(mask, form_results)

print("\n--- QC SPECIAL (skruehuller) ---")
for i, r in enumerate(special_results):
    print(f"Objekt {i+1}: valid_special={r['valid_special']}, reason={r['reason']}, "
          f"hole_count={r['hole_count']}, hole_areas={r['hole_areas']}")
print()

# ---------------------------------------------------------
# 6. Samlet QC EVALUATE
# ---------------------------------------------------------
qc_eval = QCEvaluate()
final_results = qc_eval.combine(
    form_results,
    size_results,
    color_results,
    special_results
)

print("\n=== SAMLET QC RESULTAT ===")
for i, r in enumerate(final_results):
    print(f"\nObjekt {i+1}:")
    print(f"  OVERALL: {'OK' if r['overall'] else 'NOT OK'}")
    print(f"  FORM    : {r['form']}")
    print(f"  SIZE    : {r['size']}")
    print(f"  COLOR   : {r['color']}")
    print(f"  SPECIAL : {r['special']}")
    print(f"  center  : {r['center']}")
    print(f"  dims_mm : {r['width_mm']:.2f} x {r['height_mm']:.2f} mm")
    print(f"  ΔE      : {r['deltaE']:.2f}")
    print(f"  holes   : {r['hole_count']}")
    if r['reasons']:
        print("  reasons :")
        for reason in r['reasons']:
            print(f"    - {reason}")
    else:
        print("  reasons : (ingen, objektet er OK)")

# ---------------------------------------------------------
# 7. Samlet overlay
# ---------------------------------------------------------
overlay = qc_eval.draw_overlay(frame, form_results, final_results)

cv.imshow("QC – Samlet OVERALL overlay", overlay)
cv.waitKey(0)
cv.destroyAllWindows()
