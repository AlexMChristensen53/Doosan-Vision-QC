# =======================================================
# qc_preprocess_test.py (FINAL)
# Tester qc_preprocess pipeline
# =======================================================

import cv2 as cv
from pathlib import Path
import sys

# Ensure project root is on PATH
ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[1]
sys.path.append(str(PROJECT))

from qc_preprocess import QCPreprocess

# Testimage
TEST_IMAGE = PROJECT / "C_data" / "Sample_images" / "frame_actual.png"

print("[INFO] Loading test image:")
print(TEST_IMAGE)

frame = cv.imread(str(TEST_IMAGE))
if frame is None:
    raise FileNotFoundError(f"Kunne ikke åbne testbilledet: {TEST_IMAGE}")

# Run preprocess
mask, gray, thresh, edges, debug = QCPreprocess(frame)

# Show windows
cv.imshow("RAW Frame", frame)
cv.imshow("Mask", mask)
cv.imshow("Gray", gray)
cv.imshow("Threshold", thresh)
cv.imshow("Edges", edges)
cv.imshow("Debug Overlay", debug)

print("\n[INFO] qc_preprocess test kører OK. Luk vinduer for at afslutte.")
cv.waitKey(0)
cv.destroyAllWindows()
