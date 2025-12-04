import numpy as np
import cv2 as cv
from Vision_tools import load_image
import json

# ------------------------------------------------------
# 0. Settings
# ------------------------------------------------------
SETTINGS_FILE = (
    "C:/Users/Alexc/OneDrive/Skrivebord/Doosan-Vision-QC/"
    "Doosan-Vision-QC/A_Vision/calibration_settings.json"
)

IMAGE_NAME = "frame_1764241656914.png"

# Fixed ROI (same as before)
x1, x2 = 120, 528
y1, y2 = 60, 472

OUTPUT_H_FILE = "calibration_h.npz"

# ------------------------------------------------------
# 1. Load image and HSV settings
# ------------------------------------------------------
img = load_image(IMAGE_NAME)        # BGR
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
hsv_full = cv.cvtColor(img, cv.COLOR_BGR2HSV)

with open(SETTINGS_FILE, "r") as f:
    cfg = json.load(f)

lower = np.array(
    [cfg["H_low"], cfg["S_low"], cfg["V_low"]],
    dtype=np.uint8
)
upper = np.array(
    [cfg["H_high"], cfg["S_high"], cfg["V_high"]],
    dtype=np.uint8
)

min_area = cfg["min_area"]
blur_k = cfg["blur_k"]

# ------------------------------------------------------
# 2. Create mask in ROI and find contours
# ------------------------------------------------------
hsv = hsv_full[y1:y2, x1:x2]

blurred = cv.GaussianBlur(hsv, (blur_k, blur_k), 0)
mask = cv.inRange(blurred, lower, upper)

contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

# First pass: raw centroids in GLOBAL image coordinates
raw_points = []

for cnt in contours:
    area = cv.contourArea(cnt)
    if area < min_area:
        continue

    M = cv.moments(cnt)
    if M["m00"] == 0:
        continue

    cx_local = M["m10"] / M["m00"]
    cy_local = M["m01"] / M["m00"]

    # ROI → global coordinates
    cx = cx_local + x1
    cy = cy_local + y1

    raw_points.append([cx, cy])

print(f"Detected {len(raw_points)} points (before check).")

if len(raw_points) != 20:
    raise ValueError(f"Expected 20 calibration dots, got {len(raw_points)}")

# ------------------------------------------------------
# 3. Sub-pixel refinement of dot centers
# ------------------------------------------------------
points = np.array(raw_points, dtype=np.float32).reshape(-1, 1, 2)

criteria = (
    cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER,
    40,
    0.001,
)

cv.cornerSubPix(
    gray,
    points,
    winSize=(5, 5),
    zeroZone=(-1, -1),
    criteria=criteria,
)

# points now refined in-place
points = points.reshape(-1, 2)  # shape (20, 2)
img_points = points.copy()      # float32 array

# ------------------------------------------------------
# 4. Sort into 4 rows × 5 columns (row-major)
#    - Sort by Y (top→bottom)
#    - Split into 4 rows of 5
#    - Sort each row by X (left→right)
# ------------------------------------------------------
# Sort all points by Y first (top to bottom)
sorted_idx_by_y = np.argsort(img_points[:, 1])
pts_sorted_y = img_points[sorted_idx_by_y]

rows = []
num_rows = 4
num_cols = 5

for r in range(num_rows):
    row_slice = pts_sorted_y[r * num_cols:(r + 1) * num_cols]
    # sort this row by X (left→right)
    row_sorted_x = row_slice[np.argsort(row_slice[:, 0])]
    rows.append(row_sorted_x)

ordered_points = np.vstack(rows).astype(np.float32)  # shape (20,2)

# ------------------------------------------------------
# Debug draw: show numbering of points
# ------------------------------------------------------
debug_img = img.copy()
for i, (x, y) in enumerate(ordered_points):
    cv.circle(debug_img, (int(x), int(y)), 5, (0, 255, 0), -1)
    cv.putText(
        debug_img,
        str(i + 1),
        (int(x) + 5, int(y) - 5),
        cv.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 0, 255),
        1,
        cv.LINE_AA,
    )

cv.imshow("Calibration points (numbered)", debug_img)
cv.waitKey(0)
cv.destroyAllWindows()

# ------------------------------------------------------
# 5. Robot coordinates (flipped Y, 4 rows × 5 cols, row-major)
#    Camera sees top row first, so that must correspond
#    to Y = 420, then 280, 140, 0 in robot space.
# ------------------------------------------------------
robot_points = np.array([
    [0.0,    420.0], [112.5, 420.0], [225.0, 420.0], [337.5, 420.0], [450.0, 420.0],
    [0.0,    280.0], [112.5, 280.0], [225.0, 280.0], [337.5, 280.0], [450.0, 280.0],
    [0.0,    140.0], [112.5, 140.0], [225.0, 140.0], [337.5, 140.0], [450.0, 140.0],
    [0.0,      0.0], [112.5,   0.0], [225.0,   0.0], [337.5,   0.0], [450.0,   0.0]
], dtype=np.float32)

# Sanity check
assert ordered_points.shape == robot_points.shape == (20, 2), \
    f"Shape mismatch: img {ordered_points.shape}, robot {robot_points.shape}"

# ------------------------------------------------------
# 6. Compute Homography with RANSAC
# ------------------------------------------------------
H, inliers = cv.findHomography(
    ordered_points,
    robot_points,
    method=cv.RANSAC,
    ransacReprojThreshold=3.0
)

if H is None:
    raise RuntimeError("Homography computation failed!")

np.savez(OUTPUT_H_FILE, H=H)
print(f"\nSaved calibration matrix to {OUTPUT_H_FILE}")
print("Homography matrix H:\n", H)

# ------------------------------------------------------
# 7. Diagnostics: pixel → robot error for all 20 points
# ------------------------------------------------------
print("\nPixel → Robot coordinates for all 20 points:")
errors = []

pts_for_transform = ordered_points.reshape(-1, 1, 2)
mapped = cv.perspectiveTransform(pts_for_transform, H).reshape(-1, 2)

for i in range(20):
    px, py = ordered_points[i]
    X_est, Y_est = mapped[i]
    X_true, Y_true = robot_points[i]

    dx = X_est - X_true
    dy = Y_est - Y_true
    err = np.sqrt(dx * dx + dy * dy)
    errors.append(err)

    print(
        f"{i+1:02d}: Pixel({px:7.2f}, {py:7.2f}) "
        f"→ Robot_est({X_est:8.3f}, {Y_est:8.3f}) "
        f"true({X_true:8.3f}, {Y_true:8.3f})  "
        f"err = {err:6.3f} mm"
    )

errors = np.array(errors)
print("\nMax error:  {:.3f} mm".format(errors.max()))
print("Mean error: {:.3f} mm".format(errors.mean()))
print("RMS error:  {:.3f} mm".format(np.sqrt(np.mean(errors**2))))
