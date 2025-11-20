from pathlib import Path
import numpy as np
import cv2 as cv

# Variables to locate "Sample_images" folder
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PICTURE_FOLDER = PROJECT_ROOT / "data" / "Sample_images"


def load_image(filename: str) -> np.ndarray:
    """Loads an image from the PICTURE_FOLDER directory.

    Args:
        filename (str): Name of the image file to load ("Sample1.jpg").

    Returns:
        NumPy: The loaded image in BGR format.
        
    Raises:
        AssertionError: if the image file cannot be found or loaded.
    """
    path = PICTURE_FOLDER / filename
    img = cv.imread(str(path))
    assert img is not None, f"Could not read image: {path}"
    return img


def rescalePicture(frame: np.ndarray, scale: float = 0.4) -> np.ndarray:
    """Rescales the image based on the scale factor.

    Args:
        frame (np.ndarray): Input image loaded by OpenCV.
        scale (float, optional): 
            Values <1 shrink the image, values >1 enlarge it.
            Defaults to 0.4.

    Returns:
        NumPy: The resized image.
    """
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    return cv.resize(frame, (width, height), interpolation=cv.INTER_AREA)


# -------------------------------
# DRAWING FUNCTION
# -------------------------------
drawing = False
mode = True
ix, iy = -1, -1
original = None
overlay = None


def draw_rectangle(event, x, y, flags, param):
    """Mouse callback used to draw rectangles interactively on an image."""
    global ix, iy, drawing, mode, original, overlay

    if not mode:
        return

    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv.EVENT_MOUSEMOVE and drawing:
        if original is None:
            return
        overlay = original.copy()
        cv.rectangle(overlay, (ix, iy), (x, y), (255, 0, 0), 3)

    elif event == cv.EVENT_LBUTTONUP and drawing:
        drawing = False
        if original is None:
            return
        cv.rectangle(original, (ix, iy), (x, y), (255, 0, 0), 3)
        overlay = original.copy()


# -------------------------------
# DEMO CODE
# -------------------------------
def main():
    """Demo code to test the tools in this module."""

    global original, overlay, img, resized_image, h, w

    img = load_image("Sample2.jpg")
    resized_image = rescalePicture(img)
    h, w = img.shape[:2]

    
    text = f"Image Size: {h} x {w}px"
    cv.putText(resized_image, text, (10, 30), cv.FONT_ITALIC,
               1, (255, 255, 255), 2, cv.LINE_AA)

    original = resized_image.copy()
    overlay = resized_image.copy()

    cv.namedWindow("Sample2")
    cv.setMouseCallback("Sample2", draw_rectangle)

    # Main loop
    while True:
        cv.imshow("Sample2", overlay)
        k = cv.waitKey(1) & 0xFF
        if k == ord("m"):
            mode = not mode
        elif k == 27:
            break

    cv.destroyAllWindows()

    print(img.shape)
    print("Color image (BGR)" if len(img.shape) == 3 else "Grayscale image")

if __name__ == "__main__":
    main()
