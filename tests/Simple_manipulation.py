import os
import numpy as np
import cv2 as cv

BILLED_MAPPE = os.path.join(os.path.dirname(__file__), "billeder")

def load_image(filename):
    """Always loads images from the 'billeder' folder."""
    path = os.path.join(BILLED_MAPPE, filename)
    img = cv.imread(path)
    assert img is not None, f"Could not read image: {path}"
    return img

img = load_image("Square_test.jpg")
