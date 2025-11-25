from __future__ import annotations
import cv2 as cv
import numpy as np

from Vision_tools import load_image, downscale


try:
    from Vision_camera import OakCamera
    OAK_AVAILABLE = True
except ImportError:
    OakCamera = None
    OAK_AVAILABLE = False


def nothing(_):
    """Dummy for trackbars."""
    pass


def create_trackbars(window_name: str) -> None:
    """Creates all trackbars in a single 'control' window."""

    cv.namedWindow(window_name, cv.WINDOW_NORMAL)

    # Display scale
    cv.createTrackbar("scale %", window_name, 40, 100, nothing) 

    # Blur kernel size
    cv.createTrackbar("blur k", window_name, 5, 31, nothing) 

    # Threshold value
    cv.createTrackbar("thresh", window_name, 120, 255, nothing)

    # Canny edges
    cv.createTrackbar("canny low", window_name, 50, 255, nothing)
    cv.createTrackbar("canny high", window_name, 150, 255, nothing)

    # Min contour area
    cv.createTrackbar("min area", window_name, 200, 10000, nothing)

    # HSV range
    cv.createTrackbar("H low", window_name, 0, 179, nothing)
    cv.createTrackbar("H high", window_name, 179, 179, nothing)
    cv.createTrackbar("S low", window_name, 0, 255, nothing)
    cv.createTrackbar("S high", window_name, 255, 255, nothing)
    cv.createTrackbar("V low", window_name, 0, 255, nothing)
    cv.createTrackbar("V high", window_name, 255, 255, nothing)


def get_frame(source: str, filename: str | None, camera: "OakCamera | None"):
    """gets frame."""
    if source == "image":
        return load_image(filename)

    if source == "camera":
        if not OAK_AVAILABLE or camera is None:
            raise RuntimeError("Camera mode selected but OakCamera is not available.")
        return camera.get_frame()

    raise ValueError(f"Invalid source: {source}")


def vision_settings(source: str = "image",
                 filename: str | None = None) -> None:
    """
    trackbar window used to adjust settings for:
      - scale, blur, threshold, canny, hsv mask, min area.
    Press 'q' or ESC to quit.
    """

    camera = OakCamera() if (source == "camera" and OAK_AVAILABLE) else None

    control_window = "controls"
    create_trackbars(control_window)

    # For image mode we load once and reuse
    base_frame = None
    if source == "image":
        if not filename:
            raise ValueError("filename is required when source='image'")
        base_frame = load_image(filename)

    while True:
        # Get frame 
        if source == "camera":
            frame = get_frame(source, filename, camera)
        else:
            frame = base_frame.copy()

        # Read current trackbar values
        scale_percent = max(10, cv.getTrackbarPos("scale %", control_window))
        scale = scale_percent / 100.0

        blur_kernel = cv.getTrackbarPos("blur k", control_window)
        if blur_kernel < 1:
            blur_kernel = 1
        if blur_kernel % 2 == 0:
            blur_kernel += 1

        thresh_val = cv.getTrackbarPos("thresh", control_window)
        canny_low = cv.getTrackbarPos("canny low", control_window)
        canny_high = cv.getTrackbarPos("canny high", control_window)
        if canny_high <= canny_low:
            canny_high = canny_low + 1

        min_area = cv.getTrackbarPos("min area", control_window)

        h_low = cv.getTrackbarPos("H low", control_window)
        h_high = cv.getTrackbarPos("H high", control_window)
        s_low = cv.getTrackbarPos("S low", control_window)
        s_high = cv.getTrackbarPos("S high", control_window)
        v_low = cv.getTrackbarPos("V low", control_window)
        v_high = cv.getTrackbarPos("V high", control_window)

        # Sets ROI and scale frame for display & processing
        x1, x2 = 380, 1478
        y1, y2 = 143, 872
        frame = frame[y1:y2, x1:x2]

        h, w = frame.shape[:2]
        frame_small = cv.resize(frame, (int(w * scale), int(h * scale)))

        # HSV mask
        hsv = cv.cvtColor(frame_small, cv.COLOR_BGR2HSV)
        lower = np.array([h_low, s_low, v_low], dtype=np.uint8)
        upper = np.array([h_high, s_high, v_high], dtype=np.uint8)
        mask = cv.inRange(hsv, lower, upper)
        masked = cv.bitwise_and(frame_small, frame_small, mask=mask)

        # Grayscale + blur
        gray = cv.cvtColor(masked, cv.COLOR_BGR2GRAY)
        blur = cv.GaussianBlur(gray, (blur_kernel, blur_kernel), 0)

        # Threshold + edges 
        _, thres = cv.threshold(blur, thresh_val, 255, cv.THRESH_BINARY)
        edge = cv.Canny(blur, canny_low, canny_high)

        # Contours with area filter (maybe we change approach)
        contours, _ = cv.findContours(edge, cv.RETR_LIST,
                                      cv.CHAIN_APPROX_SIMPLE)
        big_contours = [c for c in contours if cv.contourArea(c) >= min_area]

        overlay = frame_small.copy()
        cv.drawContours(overlay, big_contours, -1, (0, 0, 255), 2)

        # Debug print
        print(f"\rContours: {len(big_contours)} | "
              f"scale={scale:.2f}, blur={blur_kernel}, "
              f"thr={thresh_val}, canny=({canny_low},{canny_high}), "
              f"min_area={min_area}", end="")

        # Show windows
        cv.imshow("Frame", frame_small)
        cv.imshow("Mask", mask)
        cv.imshow("Gray", gray)
        cv.imshow("Thresh", thres)
        cv.imshow("Edges", edge)
        cv.imshow("Overlay", overlay)

        key = cv.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    print() 
    cv.destroyAllWindows()


if __name__ == "__main__":
    # Start in image mode using your frame
    vision_settings(source="image", filename="frame_1764083636036.png")
    # Later you can test camera mode with:
    # vision_tuner(source="camera")
