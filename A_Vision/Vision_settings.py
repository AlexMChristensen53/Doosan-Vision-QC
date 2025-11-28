from __future__ import annotations
import cv2 as cv
import numpy as np
import json
from Vision_tools import load_image
from Vision_camera import OakCamera

SETTINGS_FILE = "calibration_settings.json"

def nothing(_): 
    pass


def create_trackbars(window_name: str):
    """Creates trackbars with correct and consistent names."""
    
    cv.namedWindow(window_name, cv.WINDOW_NORMAL)

    cv.createTrackbar("scale %", window_name, 40, 100, nothing)

    cv.createTrackbar("blur k", window_name, 5, 31, nothing)

    cv.createTrackbar("thresh", window_name, 120, 255, nothing)
    cv.createTrackbar("canny low", window_name, 50, 255, nothing)
    cv.createTrackbar("canny high", window_name, 150, 255, nothing)

    cv.createTrackbar("min area", window_name, 40, 1000, nothing)

    cv.createTrackbar("H low", window_name, 18, 179, nothing)
    cv.createTrackbar("H high", window_name, 32, 179, nothing)
    cv.createTrackbar("S low", window_name, 120, 255, nothing)
    cv.createTrackbar("S high", window_name, 255, 255, nothing)
    cv.createTrackbar("V low", window_name, 120, 255, nothing)
    cv.createTrackbar("V high", window_name, 255, 255, nothing)


def get_frame(source: str, filename: str, camera: OakCamera | None):
    """Returns frame from image or camera."""
    
    if source == "image":
        return load_image(filename)

    if source == "camera":
        if camera is None:
            raise RuntimeError("Camera mode selected but no camera found.")
        return camera.get_frame()

    raise ValueError("Invalid source type.")


def vision_settings(source: str = "image",
                    filename: str | None = None):
    """
    GUI tool with trackbars for adjusting HSV/color settings.
    Press 'S' to save settings → calibration_settings.json
    Press 'Q' or ESC to exit
    """
    camera = OakCamera() if source == "camera" else None

    if source == "image":
        if filename is None:
            raise ValueError("filename is required in image mode.")

        base_frame = load_image(filename)

    control_window = "controls"
    create_trackbars(control_window)

    # Fixed ROI used earlier
    x1, x2 = 120, 528
    y1, y2 = 60, 472

    while True:

        frame = get_frame(source, filename, camera) if source == "camera" else base_frame.copy()
        frame = frame[y1:y2, x1:x2]   # crop ROI

        # Read trackbar values
        scale = max(10, cv.getTrackbarPos("scale %", control_window)) / 100.0

        blur_k = cv.getTrackbarPos("blur k", control_window)
        blur_k = blur_k if blur_k % 2 == 1 else blur_k + 1
        blur_k = max(1, blur_k)

        thresh_val = cv.getTrackbarPos("thresh", control_window)
        canny_low = cv.getTrackbarPos("canny low", control_window)
        canny_high = cv.getTrackbarPos("canny high", control_window)
        if canny_high <= canny_low:
            canny_high = canny_low + 1

        min_area = cv.getTrackbarPos("min area", control_window)

        H_low  = cv.getTrackbarPos("H low", control_window)
        H_high = cv.getTrackbarPos("H high", control_window)
        S_low  = cv.getTrackbarPos("S low", control_window)
        S_high = cv.getTrackbarPos("S high", control_window)
        V_low  = cv.getTrackbarPos("V low", control_window)
        V_high = cv.getTrackbarPos("V high", control_window)

        # HSV mask
        hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)
        lower = np.array([H_low, S_low, V_low])
        upper = np.array([H_high, S_high, V_high])
        mask = cv.inRange(hsv, lower, upper)
        masked = cv.bitwise_and(frame, frame, mask=mask)

        # Gray + blur
        gray = cv.cvtColor(masked, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (blur_k, blur_k), 0)

        # Threshold + edges
        _, thres = cv.threshold(blur, thresh_val, 255, cv.THRESH_BINARY_INV)
        edges = cv.Canny(blur, canny_low, canny_high)

        # Contours
        cnts, _ = cv.findContours(edges, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        big_cnts = [c for c in cnts if cv.contourArea(c) >= min_area]

        overlay = frame.copy()
        cv.drawContours(overlay, big_cnts, -1, (0,0,255), 2)

        # Draw centers
        for c in big_cnts:
            M = cv.moments(c)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                cv.circle(overlay, (cx,cy), 4, (0,255,255), -1)

        # Show windows
        cv.imshow("Frame", frame)
        cv.imshow("Mask", mask)
        cv.imshow("Thresh", thres)
        cv.imshow("Edges", edges)
        cv.imshow("Overlay", overlay)

        key = cv.waitKey(1) & 0xFF

        # SAVE SETTINGS
        if key == ord('s'):
            settings = {
                "H_low": H_low,
                "H_high": H_high,
                "S_low": S_low,
                "S_high": S_high,
                "V_low": V_low,
                "V_high": V_high,
                "blur_k": blur_k,
                "min_area": min_area,
                "scale": scale
            }

            with open(SETTINGS_FILE, "w") as f:
                json.dump(settings, f, indent=4)

            print("\n[SAVED] calibration_settings.json")

        # EXIT
        if key in (27, ord('q')):
            break

    cv.destroyAllWindows()


if __name__ == "__main__":
    # Edit this to your test image
    vision_settings(source="image", filename="frame_1764252953417.png")
