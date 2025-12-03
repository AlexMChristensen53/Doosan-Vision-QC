# =======================================================
# calibrate_live.py — LIVE KALIBRERING MED OAK-D
# -------------------------------------------------------
# Formål:
#   - Find 20 mørkegrønne prikker på hvid baggrund (1080x1080)
#   - Sortér dem stabilt (4 rækker x 5 kolonner)
#   - Match til kendte robot-koordinater
#   - Beregn homografi H (image -> robot)
#   - Justér HSV live med trackbars
#   - Gem H + HSV med 's'
#   - Test transform med 't'
#
#  NOTE:
#   - Dette er en foreslået, speciallavet løsning til jeres setup.
#   - HSV-grænser SKAL tunes til jeres faktiske lys/baggrund.
# =======================================================

import cv2 as cv
import numpy as np
import json
import time
from pathlib import Path
import sys

# -------------------------------------------
# PATH + CAMERA
# -------------------------------------------
ROOT = Path(__file__).resolve().parent
sys.path.append(str(ROOT))

from qc_vision_camera import OakCamera  # bruger jeres eksisterende kamera-wrapper


# -------------------------------------------
# ROBOT GRID (20 PUNKTER, 4x5)
# -------------------------------------------
def get_robot_points_sorted():
    """
    Returnerer robot-koordinaterne for de 20 prikker,
    i layout (4 rækker x 5 kolonner):

        X: 0, 112.5, 225, 337.5, 450
        Y: 420, 280, 140, 0

    Sorteret til samme rækkefølge som billede-punkterne:
        sorteret efter (y stigende, x stigende)
    """

    robot_points = np.array([
        [0.0,   420.0], [112.5, 420.0], [225.0, 420.0], [337.5, 420.0], [450.0, 420.0],
        [0.0,   280.0], [112.5, 280.0], [225.0, 280.0], [337.5, 280.0], [450.0, 280.0],
        [0.0,   140.0], [112.5, 140.0], [225.0, 140.0], [337.5, 140.0], [450.0, 140.0],
        [0.0,     0.0], [112.5,   0.0], [225.0,   0.0], [337.5,   0.0], [450.0,   0.0]
    ], dtype=np.float32)

    # Billedet sorteres (y ASC, x ASC).
    # Robot har y=420 øverst, y=0 nederst → vend y-signatur med -y.
    robot_points_sorted = sorted(robot_points, key=lambda p: (-p[1], p[0]))
    return np.array(robot_points_sorted, dtype=np.float32)


ROBOT_POINTS_SORTED = get_robot_points_sorted()
EXPECTED_DOTS = 20


# -------------------------------------------
# TRACKBARS TIL HSV
# -------------------------------------------
def nothing(_):
    pass


def create_hsv_trackbars(window_name: str):
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)

    # H: 0-179, S: 0-255, V: 0-255
    cv.createTrackbar("H_low",  window_name, 40, 179, nothing)
    cv.createTrackbar("H_high", window_name, 85, 179, nothing)

    cv.createTrackbar("S_low",  window_name, 40, 255, nothing)
    cv.createTrackbar("S_high", window_name, 255, 255, nothing)

    cv.createTrackbar("V_low",  window_name, 30, 255, nothing)
    cv.createTrackbar("V_high", window_name, 255, 255, nothing)


def get_hsv_from_trackbars(window_name: str):
    H_low  = cv.getTrackbarPos("H_low",  window_name)
    H_high = cv.getTrackbarPos("H_high", window_name)
    S_low  = cv.getTrackbarPos("S_low",  window_name)
    S_high = cv.getTrackbarPos("S_high", window_name)
    V_low  = cv.getTrackbarPos("V_low",  window_name)
    V_high = cv.getTrackbarPos("V_high", window_name)

    lower = np.array([H_low,  S_low,  V_low],  dtype=np.uint8)
    upper = np.array([H_high, S_high, V_high], dtype=np.uint8)

    return lower, upper


# -------------------------------------------
# DETEKTION AF GRØNNE PRIKKER
# -------------------------------------------
def detect_green_dots(
    frame_bgr: np.ndarray,
    lower_hsv: np.ndarray,
    upper_hsv: np.ndarray,
    min_area: float = 5.0,
    max_area: float = 10000.0,
    min_circularity: float = 0.15,
    max_aspect_ratio: float = 4.0
):
    blur = cv.GaussianBlur(frame_bgr, (5, 5), 0)
    hsv = cv.cvtColor(blur, cv.COLOR_BGR2HSV)

    mask = cv.inRange(hsv, lower_hsv, upper_hsv)

    kernel = np.ones((3, 3), np.uint8)
    mask_clean = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=1)
    mask_clean = cv.morphologyEx(mask_clean, cv.MORPHCLOSE, kernel, iterations=1)

    contours,  = cv.findContours(mask_clean, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)

    centers = []
    debug_img = frame_bgr.copy()

    for cnt in contours:
        area = cv.contourArea(cnt)
        if not (min_area <= area <= max_area):
            continue

        x, y, w, h = cv.boundingRect(cnt)
        if h == 0:
            continue
        aspect = max(w, h) / float(min(w, h))
        if aspect > max_aspect_ratio:
            continue

        perimeter = cv.arcLength(cnt, True)
        if perimeter == 0:
            continue
        circularity = 4.0 * np.pi * area / (perimeter * perimeter)
        if circularity < min_circularity:
            continue

        (cx, cy), radius = cv.minEnclosingCircle(cnt)
        centers.append((cx, cy))

        cv.circle(debug_img, (int(cx), int(cy)), 5, (0, 255, 255), -1)

    centers = sorted(centers, key=lambda p: (p[1], p[0]))
    return np.array(centers, dtype=np.float32), mask_clean, debug_img


# -------------------------------------------
# BEREGN HOMOGRAFI + FEJL
# -------------------------------------------
def compute_homography_and_error(points_img: np.ndarray, robot_points: np.ndarray):
    """
    points_img   : (N,2) pixel
    robot_points : (N,2) robot (mm)

    Returnerer:
        H         : 3x3 homografi
        mask      : inlier mask (RANSAC)
        avg_error : gennemsnitlig fejl (mm)
        max_error : max fejl (mm)
        errors    : fejl pr. punkt (mm)
    """
    if points_img.shape != robot_points.shape:
        raise ValueError("points_img og robot_points skal have samme shape.")

    N = points_img.shape[0]
    if N < 4:
        raise ValueError("Mindst 4 punkter kræves for homografi.")

    H, mask = cv.findHomography(points_img, robot_points, cv.RANSAC, 3.0)
    if H is None:
        return None, None, None, None, None

    pts = points_img.reshape(-1, 1, 2)
    robot_est = cv.perspectiveTransform(pts, H).reshape(-1, 2)

    errors = np.linalg.norm(robot_est - robot_points, axis=1)
    avg_error = float(np.mean(errors))
    max_error = float(np.max(errors))

    return H, mask, avg_error, max_error, errors


# -------------------------------------------
# MAIN: LIVE KALIBRERING
# -------------------------------------------
def main():
    cam = OakCamera((1080, 1080))

    controls_win = "Calib Controls"
    create_hsv_trackbars(controls_win)

    H = None
    last_avg_error = None
    last_max_error = None
    last_points_img = None

    while True:
        frame = cam.get_frame()
        if frame is None:
            continue

        lower_hsv, upper_hsv = get_hsv_from_trackbars(controls_win)

        points_img, mask_clean, dbg = detect_green_dots(frame, lower_hsv, upper_hsv)

        N = points_img.shape[0]

        # Tegn indexnumre på debug-billede
        for i, (x, y) in enumerate(points_img):
            cv.putText(dbg, str(i), (int(x) + 5, int(y) - 5),
                       cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)

        text_line = f"Detected dots: {N}"

        if N == EXPECTED_DOTS:
            try:
                H, mask, avg_err, max_err, errors = compute_homography_and_error(
                    points_img, ROBOT_POINTS_SORTED
                )
                last_avg_error = avg_err
                last_max_error = max_err
                last_points_img = points_img.copy()

                text_line += f" | avg_err={avg_err:.2f} mm, max_err={max_err:.2f} mm"

                # Farvekod punkter efter fejl
                for i, (x, y) in enumerate(points_img):
                    e = errors[i]
                    if e < 1.0:
                        col = (0, 255, 0)   # grøn = meget god
                    elif e < 3.0:
                        col = (0, 255, 255) # gul = ok
                    else:
                        col = (0, 0, 255)   # rød = dårlig
                    cv.circle(dbg, (int(x), int(y)), 6, col, 2)

            except Exception as ex:
                text_line += f" | homography error: {ex}"

        else:
            H = None
            last_avg_error = None
            last_max_error = None
            last_points_img = None
            text_line += f" | venter på præcis {EXPECTED_DOTS} prikker..."

        # Skriv tekst på debug-billede
        cv.putText(dbg, text_line, (10, 25),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # Vis vinduer
        cv.imshow("Calib Live", frame)
        cv.imshow("Calib Mask", mask_clean)
        cv.imshow("Calib Debug", dbg)

        key = cv.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        # Gem H + HSV + meta
        if key == ord('s'):
            if H is None or last_points_img is None:
                print("[WARN] Kan ikke gemme: ingen gyldig homografi endnu.")
            else:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                H_path = ROOT / "homography_H.npy"
                meta_path = ROOT / "homography_meta.json"

                np.save(str(H_path), H)

                meta = {
                    "timestamp": timestamp,
                    "num_points": int(last_points_img.shape[0]),
                    "avg_error_mm": last_avg_error,
                    "max_error_mm": last_max_error,
                    "hsv": {
                        "H_low":  int(lower_hsv[0]),
                        "S_low":  int(lower_hsv[1]),
                        "V_low":  int(lower_hsv[2]),
                        "H_high": int(upper_hsv[0]),
                        "S_high": int(upper_hsv[1]),
                        "V_high": int(upper_hsv[2]),
                    }
                }

                with open(meta_path, "w", encoding="utf-8") as f:
                    json.dump(meta, f, indent=2)

                print(f"[INFO] Homografi gemt til: {H_path}")
                print(f"[INFO] Meta + HSV gemt til: {meta_path}")
                print(f"       avg_error={last_avg_error:.3f} mm, max_error={last_max_error:.3f} mm")

        # Test-transform (T): eksempelpunkt
        if key == ord('t'):
            if H is None:
                print("[WARN] Ingen homografi til test endnu.")
            else:
                h, w = frame.shape[:2]
                cx, cy = w / 2.0, h / 2.0
                pt = np.array([[[cx, cy]]], dtype=np.float32)
                world = cv.perspectiveTransform(pt, H)[0, 0]
                print(f"[TEST] Pixel({cx:.1f}, {cy:.1f}) -> Robot({world[0]:.2f}, {world[1]:.2f})")

    cv.destroyAllWindows()


if __name__ == "__main__":
    main()