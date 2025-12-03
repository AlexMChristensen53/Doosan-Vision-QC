import numpy as np
import cv2 as cv
import json
from pathlib import Path
import sys

# -------------------------------------------------
# PATH / IMPORTS
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]  # Doosan-Vision-QC/
sys.path.append(str(ROOT))

from A_Vision.Vision_tools import load_image  # adjust if needed

SETTINGS_FILE = "calibration_settings_dots.json"
IMG_NAME = "frame_1764685940878.png"   # your saved calibration frame

# -------------------------------------------------
# LOAD IMAGE + SETTINGS
# -------------------------------------------------
img = load_image(IMG_NAME)
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

with open(SETTINGS_FILE, "r") as f:
    cfg = json.load(f)

lower = np.array([cfg["H_low"],  cfg["S_low"],  cfg["V_low"] ], dtype=np.uint8)
upper = np.array([cfg["H_high"], cfg["S_high"], cfg["V_high"]], dtype=np.uint8)

min_area = max(23, int(cfg.get("min_area", 20)))
blur_k   = max(3, int(cfg.get("blur_k", 3)))
if blur_k % 2 == 0:
    blur_k += 1

print(f"[CONFIG] HSV lower={lower}, upper={upper}, blur_k={blur_k}, min_area={min_area}")

# -------------------------------------------------
# DETECT DOTS (FULL FRAME)
# -------------------------------------------------
blurred = cv.GaussianBlur(hsv, (blur_k, blur_k), 0)
mask = cv.inRange(blurred, lower, upper)

contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

img_points = []
for cnt in contours:
    if cv.contourArea(cnt) < min_area:
        continue

    M = cv.moments(cnt)
    if M["m00"] == 0:
        continue

    cx = M["m10"] / M["m00"]
    cy = M["m01"] / M["m00"]
    img_points.append([cx, cy])

print(f"[DETECTED] {len(img_points)} points")

if len(img_points) != 20:
    raise ValueError(f"Expected 20 calibration dots, got {len(img_points)}.")

# -------------------------------------------------
# SORT INTO 4 ROWS × 5 COLS (ROW-MAJOR)
# -------------------------------------------------
# sort by Y (top→bottom), then X (left→right)
img_points = sorted(img_points, key=lambda p: (p[1], p[0]))

rows = []
row = [img_points[0]]
for p in img_points[1:]:
    if abs(p[1] - row[-1][1]) < 25:   # row tolerance in pixels
        row.append(p)
    else:
        rows.append(row)
        row = [p]
rows.append(row)

if len(rows) != 4:
    raise ValueError(f"Expected 4 rows, got {len(rows)}")

for i in range(4):
    if len(rows[i]) != 5:
        raise ValueError(f"Row {i} has {len(rows[i])} points (expected 5)")
    rows[i] = sorted(rows[i], key=lambda p: p[0])

ordered_points = [p for row in rows for p in row]
pixels = np.array(ordered_points, dtype=np.float32)
debug = img.copy()
for i, (x, y) in enumerate(ordered_points, start=1):
    cv.circle(debug, (int(x), int(y)), 12, (0, 0, 255), -1)
    cv.putText(debug, str(i), (int(x)+10, int(y)-10),
               cv.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

cv.imshow("DOT ORDER CHECK", debug)
cv.waitKey(0)


# preview
preview = img.copy()
for (x, y) in ordered_points:
    cv.circle(preview, (int(x), int(y)), 7, (0, 255, 0), -1)
cv.imshow("Detected Dots (sorted 4x5)", preview)
cv.waitKey(500)

# -------------------------------------------------
# ROBOT COORDINATES (4 rows × 5 cols)
# -------------------------------------------------
robot_points = np.array([
    [0.0,    420.0], [112.5, 420.0], [225.0, 420.0], [337.5, 420.0], [450.0, 420.0],
    [0.0,    280.0], [112.5, 280.0], [225.0, 280.0], [337.5, 280.0], [450.0, 280.0],
    [0.0,    140.0], [112.5, 140.0], [225.0, 140.0], [337.5, 140.0], [450.0, 140.0],
    [0.0,      0.0], [112.5,   0.0], [225.0,   0.0], [337.5,   0.0], [450.0,   0.0],
], dtype=np.float32)



# -------------------------------------------------
# COMPUTE HOMOGRAPHY
# -------------------------------------------------
H, _ = cv.findHomography(pixels, robot_points)
out_path = ROOT / "C_data" / "calibration_h.npz"
np.savez(out_path, H=H)

print(f"[SAVED] Homography matrix → {out_path}")
print("H =\n", H)

# -------------------------------------------------
# TEST: PRINT PIXEL → ROBOT FOR ALL 20 DOTS
# -------------------------------------------------
print("\n[Test] Pixel → Robot mapping:")
for i, (px, py) in enumerate(ordered_points):
    p = np.array([px, py, 1.0])
    mapped = H @ p
    Xr, Yr = mapped[0] / mapped[2], mapped[1] / mapped[2]
    print(f"{i+1:02d}: Pixel({px:.1f}, {py:.1f}) → Robot({Xr:.2f}, {Yr:.2f})")

cv.waitKey(0)
cv.destroyAllWindows()
