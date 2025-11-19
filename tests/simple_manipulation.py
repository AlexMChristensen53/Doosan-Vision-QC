from pathlib import Path
import numpy as np
import cv2 as cv

# Variables to locate "Sample_images" folder
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PICTURE_FOLDER = PROJECT_ROOT / "data" / "Sample_images"


def load_image(filename):
    """Always loads images from the 'Sample_images' folder."""
    path = PICTURE_FOLDER / filename
    img = cv.imread(path)
    assert img is not None, f"Could not read image: {path}"
    return img

img = load_image("Sample2.jpg")

cv.imshow("Sample2", img)
cv.waitKey(0)