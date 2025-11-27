# test_qc_form.py
import cv2 as cv
import numpy as np
from qc_form import QCForm

mask = cv.imread("C_data/Sample_images/Mask_sample_1.png", cv.IMREAD_GRAYSCALE)

qc = QCForm(min_area=1500)
results = qc.evaluate_all(mask)
for i, r in enumerate(results):
    print(f"Objekt {i+1}:")
    print("  area:", r["area"])
    print("  aspect_ratio:", r["aspect_ratio"])
    print("  solidity:", r["solidity"])
    print("  valid:", r["valid"])
    print()


print(results)

color = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
overlay = qc.draw_overlay(color, results)

cv.imshow("QC Form", overlay)
cv.waitKey(0)
