# ======================================================
# main.py — FULL QC PIPELINE (LIVE OAK-D)
# Debug-visning + print identisk med alle QC testmoduler
# Med objekt-ID på ALLE overlays (FORM, SIZE, COLOR, SPECIAL, OVERALL)
# Og stabil POSE ESTIMATION (center + angle + robot XY)
# ======================================================

import cv2 as cv
import numpy as np
from pathlib import Path
import sys

# -------------------------------------------
# PATH SETUP
# -------------------------------------------
ROOT = Path(__file__).resolve().parent
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
from Angle_utility import pca_angle, draw_orientation
from mapping import HomographyMapper

# Camera
from qc_vision_camera import OakCamera


# ------------------------------------------------------
# QC MODULE INSTANCES
# ------------------------------------------------------
qc_form = QCForm(
    min_area=1500,
    min_aspect=2.0,
    max_aspect=7.0,
    min_solidity=0.88,
    min_extent=0.90
)

qc_size = QCSize(
    mm_per_pixel=0.5098,
    expected_width_mm=100.0,
    expected_height_mm=25.0,
    tolerance_width_mm=5.0,
    tolerance_height_mm=3.0
)

qc_color = QCColor(
    reference_lab=np.array([107.30, 187.07, 160.88]),
    tolerance_dE=25.0
)

qc_special = QCSpecial(
    expected_hole_count=2,
    min_hole_area=50
)

qc_eval = QCEvaluate()


# ------------------------------------------------------
# CAMERA INIT
# ------------------------------------------------------
cam = OakCamera((1920, 1080))

DISPLAY_W = 640
DISPLAY_H = 400


# ------------------------------------------------------
# LOAD HOMOGRAPHY (pixel -> robot)
# ------------------------------------------------------
try:
    pose_mapper = HomographyMapper.from_file()
    print("[QC] Loaded homography from C_data/calibration_h.npz")
except FileNotFoundError:
    pose_mapper = None
    print("[QC] No calibration_h.npz found – mapping disabled.")



# ------------------------------------------------------
# DRAW HELPERS (unchanged)
# ------------------------------------------------------

def draw_form_with_id(img, form_results):
    vis = img.copy()
    for idx, fr in enumerate(form_results, start=1):
        color = (0,255,0) if fr["valid"] else (0,0,255)
        box   = fr["bbox_points"]
        cx,cy = map(int, fr["center"])

        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx,cy), 5, (0,255,255), -1)
        cv.putText(vis, f"ID {idx}", (cx-20, cy-20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_size_with_id(img, form_results, size_results):
    vis = img.copy()
    for idx, (fr, sr) in enumerate(zip(form_results, size_results), start=1):
        color = (0,255,0) if sr["valid_size"] else (0,0,255)
        box   = fr["bbox_points"]
        cx,cy = map(int, fr["center"])

        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx,cy), 5, (0,255,255), -1)
        cv.putText(vis, f"ID {idx}", (cx-20, cy-20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_color_with_id(img, form_results, color_results):
    vis = img.copy()
    for idx, (fr, cr) in enumerate(zip(form_results, color_results), start=1):
        color = (0,255,0) if cr["valid_color"] else (0,0,255)
        box   = fr["bbox_points"]
        cx,cy = map(int, fr["center"])

        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx,cy), 5, (0,255,255), -1)
        cv.putText(vis, f"ID {idx}", (cx-20, cy-20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_special_with_id(img, form_results, special_results):
    vis = img.copy()
    for idx, (fr, sr) in enumerate(zip(form_results, special_results), start=1):
        color = (0,255,0) if sr["valid_special"] else (0,0,255)
        box   = fr["bbox_points"]
        cx,cy = map(int, fr["center"])

        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx,cy), 5, (0,255,255), -1)
        cv.putText(vis, f"ID {idx}", (cx-20, cy-20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis


def draw_overall_with_id(img, form_results, final_results):
    vis = img.copy()
    for idx, (fr, frf) in enumerate(zip(form_results, final_results), start=1):
        color = (0,255,0) if frf["overall"] else (0,0,255)
        box   = fr["bbox_points"]
        cx,cy = map(int, fr["center"])

        cv.polylines(vis, [box], True, color, 2)
        cv.circle(vis, (cx,cy), 5, (0,255,255), -1)

        cv.putText(vis, f"ID {idx}: {'OK' if frf['overall'] else 'NOK'}",
                   (cx-50, cy-20),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    return vis



# ------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------
while True:

    frame = cam.get_frame()
    if frame is None:
        continue

    # --------------------------------------------------
    # 1) PREPROCESS
    # --------------------------------------------------
    mask, gray, thresh, edges, debug = QCPreprocess(frame)

    # --------------------------------------------------
    # 2) EVALUATE MODULES (FORM → SIZE → COLOR → SPECIAL)
    # --------------------------------------------------
    form_results    = qc_form.evaluate_all(mask)
    size_results    = qc_size.evaluate_all(form_results)
    color_results   = qc_color.evaluate_all(frame, form_results)
    special_results = qc_special.evaluate_all(mask, form_results)

    final_results = qc_eval.combine(
        form_results,
        size_results,
        color_results,
        special_results
    )


    # --------------------------------------------------
    # 2B) POSE ESTIMATION (center + PCA angle + robot XY)
    #     Uses RAW pixel coords (same as in calibration)
    # --------------------------------------------------
    poses = []
    if pose_mapper is not None:
        for idx, fr in enumerate(form_results, start=1):
            cx, cy = fr["center"]
            cnt    = fr["contour"]

            angle_raw = pca_angle(cnt)

            # Camera-to-robot angle correction (solve camera tilt)
            CAMERA_ROTATION_OFFSET = 151.55    # fine-tune if needed
            angle_deg = (angle_raw + CAMERA_ROTATION_OFFSET) % 180


            # Pixel -> robot (NO flipping, homography already correct)
            Xr, Yr = pose_mapper.pixel_to_robot(cx, cy)

            poses.append({
                "id": idx,
                "center_px": (cx, cy),
                "angle_deg": angle_deg,
                "robot_xy": (Xr, Yr),
                "area": fr["area"],
            })




    # --------------------------------------------------
    # 3) ROBOT PAYLOAD (clean + real values)
    # --------------------------------------------------
    robot_payload = []

    if pose_mapper is not None:
        for pose, fr_final in zip(poses, final_results):
            Xr, Yr = pose["robot_xy"]
            ang    = pose["angle_deg"]
            ok     = bool(fr_final["overall"])

            robot_payload.append({
                "id": pose["id"],
                "ok": ok,
                "x_mm": float(Xr),
                "y_mm": float(Yr),
                "angle_deg": float(ang)
            })


    # --------------------------------------------------
    # 4) DRAW MASTER OVERLAY
    # --------------------------------------------------
    overlay = draw_overall_with_id(frame, form_results, final_results)
    preview5 = cv.resize(overlay, (DISPLAY_W, DISPLAY_H))
    cv.imshow("QC-overlay", preview5)
    qc_export = QCExport(z_height_mm=55)



    # --------------------------------------------------
    # 5) DEBUG WINDOWS
    # --------------------------------------------------
    form_bgr = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)

    cv.imshow("QC-FORM",   cv.resize(draw_form_with_id(form_bgr, form_results), (DISPLAY_W, DISPLAY_H)))
    cv.imshow("QC-Size",   cv.resize(draw_size_with_id(form_bgr, form_results, size_results), (DISPLAY_W, DISPLAY_H)))
    cv.imshow("QC-color",  cv.resize(draw_color_with_id(frame.copy(), form_results, color_results), (DISPLAY_W, DISPLAY_H)))
    cv.imshow("QC-special",cv.resize(draw_special_with_id(form_bgr, form_results, special_results), (DISPLAY_W, DISPLAY_H)))


    # --------------------------------------------------
    # 6) KEYBOARD INPUT
    # --------------------------------------------------
    key = cv.waitKey(1) & 0xFF

    if key == ord('q'):
        break

    elif key == ord('u'):
        print("\n--- QC FORM (px) ---")
        for i, r in enumerate(form_results, start=1):
            print(f"Objekt {i}:")
            print("  area        :", r["area"])
            print("  aspect_ratio:", r["aspect_ratio"])
            print("  solidity    :", r["solidity"])
            print("  extent      :", r["extent"])
            print("  valid       :", r["valid"])
            print("  reason      :", r["reason"])

    elif key == ord('i'):
        print("\n--- QC SIZE (mm) ---")
        for i, r in enumerate(size_results, start=1):
            print(f"Objekt {i}: width={r['width_mm']:.2f}mm, "
                  f"height={r['height_mm']:.2f}mm, valid_size={r['valid_size']}, "
                  f"reason={r['reason']}")

    elif key == ord('o'):
        print("\n--- QC COLOR (LAB + ΔE) ---")
        for i, r in enumerate(color_results, start=1):
            print(f"Objekt {i}: valid_color={r['valid_color']}, "
                  f"ΔE={r['deltaE']:.2f}, reason={r['reason']}")

    elif key == ord('p'):
        print("\n--- QC SPECIAL (huller) ---")
        for i, r in enumerate(special_results, start=1):
            print(f"Objekt {i}: holes={r['hole_count']} → valid={r['valid_special']}, "
                  f"reason={r['reason']}")

    elif key == ord('r'):
        print("\n--- ROBOT PAYLOAD ---")
        for item in robot_payload:
            print(item)

    elif key == ord('s'):
        print("\n--- POSE RESULTS (ID, ROBOT XY, ANGLE) ---")
        print(angle_raw)
        for p in poses:
            pid = p["id"]
            (cx, cy) = p["center_px"]
            (Xr, Yr) = p["robot_xy"]
            ang = p["angle_deg"]
            
        
            print(
                f"ID {pid}:  "
                f"RobotX={Xr:.2f} mm   "
                f"RobotY={Yr:.2f} mm   "
                f"Angle={ang:.2f}°"
            )
            
    elif key == ord('g'):
        print("RAW FRAME SHAPE:", frame.shape)
        print("MASK SHAPE:", mask.shape)
        
    elif key == ord('e'):
        qc_export.payload_to_json(robot_payload)




cv.destroyAllWindows()
