from __future__ import annotations
import cv2 as cv
import numpy as np
import json
import os
import time

from Vision_tools import load_image, downscale

try:
    from Vision_camera import OakCamera
    OAK_AVAILABLE = True
except ImportError:
    OakCamera = None
    OAK_AVAILABLE = False


SETTINGS_FILE = "calibration_settings_dots.json"


def nothing(_):
    pass


def create_trackbars(window_name: str) -> None:

    cv.namedWindow(window_name, cv.WINDOW_NORMAL)

    cv.createTrackbar("scale %", window_name, 40, 100, nothing)
    cv.createTrackbar("blur k", window_name, 5, 31, nothing)

    cv.createTrackbar("global thresh", window_name, 120, 255, nothing)
    cv.createTrackbar("thresh mode", window_name, 0, 2, nothing)

    cv.createTrackbar("block size", window_name, 21, 51, nothing)
    cv.createTrackbar("C", window_name, 2, 20, nothing)

    cv.createTrackbar("canny low", window_name, 50, 255, nothing)
    cv.createTrackbar("canny high", window_name, 150, 255, nothing)

    cv.createTrackbar("min area", window_name, 200, 10000, nothing)

    # HSV trackbars
    cv.createTrackbar("H low", window_name, 0, 179, nothing)
    cv.createTrackbar("H high", window_name, 179, 179, nothing)
    cv.createTrackbar("S low", window_name, 0, 255, nothing)
    cv.createTrackbar("S high", window_name, 255, 255, nothing)
    cv.createTrackbar("V low", window_name, 0, 255, nothing)
    cv.createTrackbar("V high", window_name, 255, 255, nothing)


def load_settings_into_trackbars(window: str):
    """Load calibration_settings.json and apply to trackbars."""

    if not os.path.exists(SETTINGS_FILE):
        print("[INFO] No settings file found — using default trackbars.")
        return

    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
    except:
        print("[WARN] Could not read settings file.")
        return

    # JSON KEY → TRACKBAR NAME
    mapping = {
        "H_low": "H low",
        "H_high": "H high",
        "S_low": "S low",
        "S_high": "S high",
        "V_low": "V low",
        "V_high": "V high",

        "blur_k": "blur k",
        "min_area": "min area",
        "global_thresh": "global thresh",
        "thresh_mode": "thresh mode",
        "block_size": "block size",
        "C": "C",
        "canny_low": "canny low",
        "canny_high": "canny high",
    }

    for key, trackbar in mapping.items():
        if key in data:
            try:
                cv.setTrackbarPos(trackbar, window, int(data[key]))
            except:
                print(f"[WARN] Could not set trackbar {trackbar}")

    # scale is special
    if "scale" in data:
        cv.setTrackbarPos("scale %", window, int(data["scale"] * 100))

    print("[LOADED] Settings applied.")


def get_frame(source: str, filename: str | None, camera: "OakCamera | None"):
    if source == "image":
        return load_image(filename)

    if source == "camera":
        if not OAK_AVAILABLE or camera is None:
            raise RuntimeError("Camera mode selected but OakCamera is not available.")
        return camera.get_frame()

    raise ValueError(f"Invalid source: {source}")


def vision_settings(source: str = "image",
                    filename: str | None = None) -> None:

    camera = OakCamera() if (source == "camera" and OAK_AVAILABLE) else None

    control_window = "controls"
    create_trackbars(control_window)
    load_settings_into_trackbars(control_window)

    if source == "image":
        if not filename:
            raise ValueError("filename required when using source=image")
        base_frame = load_image(filename)
    else:
        base_frame = None

    while True:

        if source == "camera":
            frame = get_frame(source, filename, camera)
        else:
            frame = base_frame.copy()

        scale_percent = max(10, cv.getTrackbarPos("scale %", control_window))
        scale = scale_percent / 100.0

        blur_k = cv.getTrackbarPos("blur k", control_window)
        if blur_k < 1:
            blur_k = 1
        if blur_k % 2 == 0:
            blur_k += 1

        global_thresh_val = cv.getTrackbarPos("global thresh", control_window)
        thresh_mode = cv.getTrackbarPos("thresh mode", control_window)

        block_size = cv.getTrackbarPos("block size", control_window)
        if block_size % 2 == 0:
            block_size += 1
        if block_size < 3:
            block_size = 3

        C_val = cv.getTrackbarPos("C", control_window)

        canny_low = cv.getTrackbarPos("canny low", control_window)
        canny_high = cv.getTrackbarPos("canny high", control_window)
        if canny_high <= canny_low:
            canny_high = canny_low + 1

        min_area = cv.getTrackbarPos("min area", control_window)

        H_low = cv.getTrackbarPos("H low", control_window)
        H_high = cv.getTrackbarPos("H high", control_window)
        S_low = cv.getTrackbarPos("S low", control_window)
        S_high = cv.getTrackbarPos("S high", control_window)
        V_low = cv.getTrackbarPos("V low", control_window)
        V_high = cv.getTrackbarPos("V high", control_window)

        # -----------------------------
        # ROI
        # -----------------------------
       #

        h, w = frame.shape[:2]
        frame_small = cv.resize(frame, (int(w * scale), int(h * scale)))

        # HSV mask
        hsv = cv.cvtColor(frame_small, cv.COLOR_BGR2HSV)
        lower = np.array([H_low, S_low, V_low], dtype=np.uint8)
        upper = np.array([H_high, S_high, V_high], dtype=np.uint8)
        mask = cv.inRange(hsv, lower, upper)
        masked = cv.bitwise_and(frame_small, frame_small, mask=mask)

        # --- DOT DETECTION FOR CALIBRATION (MATCHES Calibration.py) ---
        # Work directly on the HSV mask – no canny, no adaptive thresh.
        blur_mask = cv.GaussianBlur(mask, (blur_k, blur_k), 0)

        contours, _ = cv.findContours(blur_mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        big_contours = [c for c in contours if cv.contourArea(c) >= min_area]


        overlay = frame_small.copy()
        cv.drawContours(overlay, big_contours, -1, (0, 0, 255), 2)

        print(f"\rContours: {len(big_contours)}", end="")

        # SHOW
        cv.imshow("Frame", frame_small)
        cv.imshow("Mask", mask)
        #cv.imshow("Gray", gray)
        #cv.imshow("Thresh", thres)
        #cv.imshow("Edges", edge)
        cv.imshow("Overlay", overlay)

        key = cv.waitKey(1) & 0xFF

        # SAVE SETTINGS
        if key == ord('s'):
            settings = {
                "H_low": H_low, "H_high": H_high,
                "S_low": S_low, "S_high": S_high,
                "V_low": V_low, "V_high": V_high,

                "blur_k": blur_k,
                "min_area": min_area,
                "scale": scale,

                "thresh_mode": thresh_mode,
                "global_thresh": global_thresh_val,
                "block_size": block_size,
                "C": C_val,

                "canny_low": canny_low,
                "canny_high": canny_high
            }

            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=4)

            print("\n[SAVED] calibration_settings.json")

        # PNG SAVE
        if key == ord('p'):
            outdir = os.path.join("C_data", "Sample_images")
            os.makedirs(outdir, exist_ok=True)
            ts = int(time.time())

            cv.imwrite(f"{outdir}/mask_{ts}.png", mask)
            cv.imwrite(f"{outdir}/gray_{ts}.png", gray)
            cv.imwrite(f"{outdir}/thresh_{ts}.png", thres)
            cv.imwrite(f"{outdir}/edges_{ts}.png", edge)
            cv.imwrite(f"{outdir}/overlay_{ts}.png", overlay)

            print(f"\n[SAVED PNG SERIES] → {outdir}/frame_{ts}.png")


        # EXIT
        if key in (27, ord("q")):
            break

    cv.destroyAllWindows()


if __name__ == "__main__":
    vision_settings(source="image", filename="frame_1764685940878.png")
