from pathlib import Path
import cv2 as cv
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[0]
IMAGE_DIR = PROJECT_ROOT / "03_data" / "Sample_images"

# Loads capture or stored frame
def load_image(filename):
    path = IMAGE_DIR / filename
    img = cv.imread(str(path))
    if img is None:
        raise FileNotFoundError(f"Image not found: {path}")
    return img

# Downscales image to make it easierer to work with
def downscale(img, scale=0.5):
    h, w = img.shape[:2]
    return cv.resize(img, (int(w*scale), int(h*scale)))

# converts to gray
def to_gray(img): return cv.cvtColor(img, cv.COLOR_BGR2GRAY)

# Applies blur
def blurred(img): return cv.GaussianBlur(img, (5,5), 0)

# Applies binary threshold (maybe we change to different kind of thresholding)
def threshold_binary(img): _, t = cv.threshold(img, 125, 255, cv.THRESH_BINARY); return t

# Detects Edges
def edges(img): return cv.Canny(img, 50, 150)

# returns amount of contours
def get_contours(binary):
    contours, _ = cv.findContours(binary, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    return contours

# Rotation 
def rotation(img, angle, rotPoint=None):
    (height,width) = img.shape[:2]

    if rotPoint is None:
        rotPoint = (width//2,height//2)
        
    RotationMatrix = cv.getRotationMatrix2D(rotPoint, angle, 1.0 )
    dimensions = (width, height)
    
    return cv.warpAffine(img, RotationMatrix, dimensions)
