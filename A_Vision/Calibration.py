import numpy as np  
import cv2 as cv 
from Vision_tools import load_image
import json
from pathlib import Path
import sys

img = load_image("frame_1764682982871.png")
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))
SETTINGS_FILE = "calibration_settings_dots.json"

with open(SETTINGS_FILE, "r") as f: 
    cfg = json.load(f)

# Green calibration dots range
lower = np.array([cfg["H_low"],  cfg["S_low"],  cfg["V_low"] ], dtype=np.uint8)
upper = np.array([cfg["H_high"], cfg["S_high"], cfg["V_high"]], dtype=np.uint8)
min_area = cfg["min_area"]
blur_k   = cfg["blur_k"]

 # Fixed ROI used earlier
x1, x2 = 120, 528
y1, y2 = 60, 472

hsv = hsv[y1:y2, x1:x2]
# --------------------------------------
# 2. Find contours and centers
# --------------------------------------
blurred_image = cv.GaussianBlur(hsv, (blur_k, blur_k), 0)
mask = cv.inRange(blurred_image, lower, upper)

contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

img_points = []

for cnt in contours:
    if cv.contourArea(cnt) < min_area:
        continue

    M = cv.moments(cnt)
    if M["m00"] != 0:
        cx_local = int(M["m10"] / M["m00"])
        cy_local = int(M["m01"] / M["m00"])

        # Convert from ROI coords → global coords
        cx = cx_local + x1
        cy = cy_local + y1

        img_points.append([cx, cy])

print(f"Detected {len(img_points)} points")

#if len(img_points) != 20:
    #raise ValueError("Did not detect exactly 20 calibration dots!")

# --------------------------------------
# 3. Sort points into grid order (4 rows x 5 columns)
# --------------------------------------

# Sort by Y first (top to bottom)
img_points = sorted(img_points, key=lambda p: (p[1], p[0]))

# Group into 4 rows
rows = []
row = [img_points[0]]

for p in img_points[1:]:
    if abs(p[1] - row[-1][1]) < 20:    # same row tolerance
        row.append(p)
    else:
        rows.append(row)
        row = [p]
rows.append(row)

# Sort each row by X coordinate
for i in range(len(rows)):
    rows[i] = sorted(rows[i], key=lambda p: p[0])

# Flatten into final ordered list (row-major)
ordered_points = [p for row in rows for p in row]

for (x,y) in img_points:
    cv.circle(img, (x,y), 6, (0,255,0), -1)

cv.imshow("Detected Dots", img)
cv.waitKey(0)
cv.destroyAllWindows()
# --------------------------------------
# 4. Robot coordinates (20 points, row-major)
# --------------------------------------
robot_points = np.array([
    [0.0,    420.0], [112.5, 420.0], [225.0, 420.0], [337.5, 420.0], [450.0, 420.0],
    [0.0,    280.0], [112.5, 280.0], [225.0, 280.0], [337.5, 280.0], [450.0, 280.0],
    [0.0,    140.0], [112.5, 140.0], [225.0, 140.0], [337.5, 140.0], [450.0, 140.0],
    [0.0,      0.0], [112.5,   0.0], [225.0,   0.0], [337.5,   0.0], [450.0,   0.0]
], dtype=np.float32)


# --------------------------------------
# 5. Compute Homography
# --------------------------------------
pixels = np.array(ordered_points, dtype=np.float32)
H, _ = cv.findHomography(pixels, robot_points)
np.savez("calibration_h.npz", H=H)
print("Saved calibration matrix to calibration_h.npz")
print("Homography matrix H:\n", H)

# --------------------------------------
# 6. Click test: pixel → robot conversion
# --------------------------------------
print("\nPixel → Robot coordinates for all 20 detected points:")
for i, (px, py) in enumerate(ordered_points):
    p = np.array([px, py, 1.0])
    mapped = H @ p
    X = mapped[0] / mapped[2]
    Y = mapped[1] / mapped[2]

    print(f"{i+1:02d}: Pixel({px:.1f}, {py:.1f}) → Robot({X:.2f}, {Y:.2f})")

cv.imshow("image", img)
cv.waitKey(0)
cv.destroyAllWindows()
