"""
qc_main.py
Hovedstyringsmodul for Vision QC-systemet.

Dette modul håndterer:
- Start og stop af OAK-D kameraet
- Start og nedlukning af robotlytter-processen
- Hovedmenuen og QC-loop'et
- Keybindings til debug af QC-resultater
- Rendering af overlay-vinduer til form/size/color/special

Modulet fungerer som 'entry point' til hele QC-systemet og binder alle
delmoduler sammen (QCForm, QCSize, QCColor, QCSpecial, QCEvaluate,
HomographyMapper og OakCamera).
"""

import cv2 as cv
import numpy as np
import subprocess
import sys
import time
from pathlib import Path

# -------------------------------------------
# PATH SETUP
# -------------------------------------------
ROOT = Path(__file__).resolve().parents[0]
sys.path.append(str(ROOT))
# QC modules
from qc_preprocess import QCPreprocess
from qc_form import QCForm
from qc_size import QCSize
from qc_color import QCColor
from qc_special import QCSpecial
from qc_evaluate import QCEvaluate
from qc_export import QCExport

# Pose utilities
from Angle_utility import pca_angle
from mapping import HomographyMapper

# Camera
from qc_vision_camera import OakCamera


# ======================================================
# QC MODULE INSTANCES
# ======================================================
qc_form = QCForm(
    min_area=1500,
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.88,
    min_extent=0.90,
)

qc_size = QCSize(
    mm_per_pixel=0.5098,
    expected_width_mm=100.0,
    expected_height_mm=25.0,
    tolerance_width_mm=5.0,
    tolerance_height_mm=3.0,
)

qc_color = QCColor(
    reference_lab=np.array([107.30, 187.07, 160.88]),
    tolerance_dE=25.0,
)

qc_special = QCSpecial(expected_hole_count=2, min_hole_area=50)

qc_eval = QCEvaluate()
qc_export = QCExport(z_height_mm=55)


# ======================================================
# ROBOT LISTENER
# ======================================================
def start_robot_listener():
    """
    Starter robotlytter-processen som et separat subprocess, der overvåger
    'robot_commands.json' og kommunikerer kommandoer til Doosan-robotten.

    Returnerer:
        subprocess.Popen objekt, eller None hvis robotfilen ikke findes.
    """
    robot_script = ROOT.parents[1] / "B_Robot" / "main_robot.py"

    if not robot_script.exists():
        print("[ROBOT ERROR] Could not find:", robot_script)
        return None

    print(f"[ROBOT] Starting robot listener: {robot_script}")
    return subprocess.Popen(
        [sys.executable, str(robot_script)]
    )


# ======================================================
# DRAW HELPERS
# ======================================================

def draw_form_with_id(img, form_results):
    vis = img.copy()
    for idx, fr in enumerate(form_results, start=1):
        color = (0, 255, 0) if fr["valid"] else (0, 0, 255)
        box = fr["bbox_points"]
        cx, cy = map(int, fr["center"])
        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)
        cv.putText(vis, f"ID {idx}", (cx - 20, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_size_with_id(img, form_results, size_results):
    vis = img.copy()
    for idx, (fr, sr) in enumerate(zip(form_results, size_results), start=1):
        color = (0, 255, 0) if sr["valid_size"] else (0, 0, 255)
        box = fr["bbox_points"]
        cx, cy = map(int, fr["center"])
        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)
        cv.putText(vis, f"ID {idx}", (cx - 20, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_color_with_id(img, form_results, color_results):
    vis = img.copy()
    for idx, (fr, cr) in enumerate(zip(form_results, color_results), start=1):
        color = (0, 255, 0) if cr["valid_color"] else (0, 0, 255)
        box = fr["bbox_points"]
        cx, cy = map(int, fr["center"])
        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)
        cv.putText(vis, f"ID {idx}", (cx - 20, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_special_with_id(img, form_results, special_results):
    vis = img.copy()
    for idx, (fr, sr) in enumerate(zip(form_results, special_results), start=1):
        color = (0, 255, 0) if sr["valid_special"] else (0, 0, 255)
        box = fr["bbox_points"]
        cx, cy = map(int, fr["center"])
        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)
        cv.putText(vis, f"ID {idx}", (cx - 20, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_overall_with_id(img, form_results, final_results):
    vis = img.copy()
    for idx, (fr, frf) in enumerate(zip(form_results, final_results), start=1):
        color = (0, 255, 0) if frf["overall"] else (0, 0, 255)
        box = fr["bbox_points"]
        cx, cy = map(int, fr["center"])
        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx, cy), 5, (0, 255, 255), -1)
        cv.putText(vis, f"ID {idx}: {'OK' if frf['overall'] else 'NOK'}",
                   (cx - 50, cy - 20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis



# ======================================================
# CAMERA INSTANCE (device is NOT started yet)
# ======================================================
cam = OakCamera((1920, 1080)) 
robot_process = None

DISPLAY_W = 640
DISPLAY_H = 400


# ======================================================
# HELP MENU
# ======================================================
def print_qc_help():
    """
    Udskriver alle tilgængelige debug- og styringstaster, som kan bruges
    inde i QC-loopet. Dette inkluderer:
    - u/i/o/p : debug af form/size/color/special
    - r       : print robot payload
    - s       : print pose-resultater
    - g       : print frame shapes
    - e       : eksportér JSON
    - m       : tilbage til main menu
    - q       : afslut program
    """
    print("\n========== QC COMMANDS ==========")
    print("u → Debug FORM")
    print("i → Debug SIZE")
    print("o → Debug COLOR")
    print("p → Debug SPECIAL")
    print("r → Print robot payload")
    print("s → Print pose results")
    print("g → Print frame shapes")
    print("e → Export JSON")
    print("m → Return to MAIN MENU")
    print("q → Quit program")
    print("h → Show this help menu")
    print("=================================\n")


# ======================================================
# QC LOOP
# ======================================================
def run_qc_loop():
    """
    Starter hele QC-loopet, som kører så længe brugeren ikke trykker 'm' eller 'q'.

    Funktionens ansvar:
    - Initialisere kameraet, hvis det ikke allerede kører
    - Starte robot-lytter processen (subprocess)
    - Læse frames fra OAK-kameraet
    - Køre preprocess og alle QC-moduler (form, size, color, special)
    - Beregne pose (center + vinkel) og robotpositioner via homografi
    - Tegne alle debug-vinduer og overlays
    - Håndtere brugerinput (u, i, o, p, r, s, g, e, m, q)
    - Stoppe robot-lytter, lukke vinduer og returnere til main-menuen

    Returnerer:
        None - funktionen afslutter kun når brugeren går tilbage til menuen.
    """
    global cam, robot_process

    print("\n[QC] Starting QC pipeline...")

    # 1) Start OAK camera ONLY if not already running
    if not cam.initialized:
        print("[QC] Initializing camera...")
        if not cam.start():
            print("[QC ERROR] Camera failed to initialize. Returning to menu.")
            time.sleep(1)
            return
        time.sleep(0.20)

    # 2) Start robot listener
    robot_process = start_robot_listener()
    print_qc_help()

    # Pre-create windows
    cv.namedWindow("QC-overlay", cv.WINDOW_NORMAL)
    cv.resizeWindow("QC-overlay", DISPLAY_W, DISPLAY_H)

    # MAIN QC LOOP
    while True:
        frame = cam.get_frame()
        if frame is None:
            continue

        # 1) PREPROCESS
        mask, gray, thresh, edges, debug = QCPreprocess(frame)

        # 2) MODULES
        form_results = qc_form.evaluate_all(mask)
        size_results = qc_size.evaluate_all(form_results)
        color_results = qc_color.evaluate_all(frame, form_results)
        special_results = qc_special.evaluate_all(mask, form_results)

        final_results = qc_eval.combine(
            form_results, size_results, color_results, special_results
        )

        # 3) POSE
        poses = []
        if pose_mapper is not None:
            for idx, fr in enumerate(form_results, start=1):
                cx, cy = fr["center"]
                cnt = fr["contour"]

                raw_angle = pca_angle(cnt)
                corrected = (raw_angle + 151.55) % 180

                Xr, Yr = pose_mapper.pixel_to_robot(cx, cy)

                poses.append({
                    "id": idx,
                    "center_px": (cx, cy),
                    "angle_deg": corrected,
                    "robot_xy": (Xr, Yr),
                    "area": fr["area"],
                })

        # 4) ROBOT PAYLOAD
        robot_payload = []
        if pose_mapper is not None:
            for pose, fr_final in zip(poses, final_results):
                robot_payload.append({
                    "id": pose["id"],
                    "ok": bool(fr_final["overall"]),
                    "x_mm": pose["robot_xy"][0],
                    "y_mm": pose["robot_xy"][1],
                    "angle_deg": pose["angle_deg"],
                })

        # 5) DRAW WINDOWS
        overlay = draw_overall_with_id(frame, form_results, final_results)
        cv.imshow("QC-overlay", cv.resize(overlay, (DISPLAY_W, DISPLAY_H)))

        form_bgr = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
        cv.imshow("QC-FORM", cv.resize(draw_form_with_id(form_bgr, form_results),
                                       (DISPLAY_W, DISPLAY_H)))

        cv.imshow("QC-Size", cv.resize(draw_size_with_id(form_bgr, form_results, size_results),
                                       (DISPLAY_W, DISPLAY_H)))

        cv.imshow("QC-color", cv.resize(draw_color_with_id(frame.copy(), form_results, color_results),
                                        (DISPLAY_W, DISPLAY_H)))

        cv.imshow("QC-special", cv.resize(draw_special_with_id(form_bgr, form_results, special_results),
                                          (DISPLAY_W, DISPLAY_H)))

        # 6) KEY HANDLING
        key = cv.waitKey(1) & 0xFF

        if key == ord('m'):
            print("[QC] Returning to main menu...")
            cv.destroyAllWindows()

            if robot_process is not None:
                robot_process.kill()
                robot_process = None

            return

        elif key == ord('q'):
            print("[QC] Quit system.")
            cv.destroyAllWindows()

            if robot_process is not None:
                robot_process.kill()

            cam.stop()
            sys.exit(0)

        elif key == ord('h'):
            print_qc_help()

        elif key == ord('e'):
            qc_export.payload_to_json(robot_payload)
            print("[EXPORT] JSON saved.")

        elif key == ord('u'):
            print("\n--- FORM DEBUG ---")
            for i, r in enumerate(form_results, start=1):
                print(i, r)

        elif key == ord('i'):
            print("\n--- SIZE DEBUG ---")
            for i, r in enumerate(size_results, start=1):
                print(i, r)

        elif key == ord('o'):
            print("\n--- COLOR DEBUG ---")
            for i, r in enumerate(color_results, start=1):
                print(i, r)

        elif key == ord('p'):
            print("\n--- SPECIAL DEBUG ---")
            for i, r in enumerate(special_results, start=1):
                print(i, r)

        elif key == ord('r'):
            print("\n--- ROBOT PAYLOAD ---")
            for it in robot_payload:
                print(it)

        elif key == ord('s'):
            print("\n--- POSE RESULTS ---")
            for p in poses:
                print(p)

        elif key == ord('g'):
            print("Frame:", frame.shape, "Mask:", mask.shape)

        time.sleep(0.001)


# ======================================================
# HOMOGRAPHY LOAD
# ======================================================
try:
    pose_mapper = HomographyMapper.from_file()
    print("[QC] Loaded homography.")
except FileNotFoundError:
    pose_mapper = None
    print("[QC] No homography found.")


# ======================================================
# MAIN MENU
# ======================================================
while True:
    print("\n==============================")
    print(" DOOSAN VISION QC SYSTEM")
    print("==============================")
    print("1. Commands info")
    print("2. Start QC pipeline")
    print("3. Quit")
    print("==============================")

    choice = input("Select: ").strip()

    if choice == "1":
        print_qc_help()
        input("Enter to return...")

    elif choice == "2":
        run_qc_loop()

    elif choice == "3":
        print("Exiting...")
        if robot_process is not None:
            robot_process.kill()
        cam.stop()
        sys.exit(0)

    else:
        print("Invalid.")
