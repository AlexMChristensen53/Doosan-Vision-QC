"""
qc_vision_tools.py
Indeholder generelle hjælpefunktioner anvendt under vision-debugging.

Kun få funktioner bruges i det endelige QC-system, primært:
- load_image(): loader billeder til debug eller testscenarier
- rotation(): roterer et billede omkring et centrum

Resten af funktionerne er generelle debug-værktøjer.
"""

from pathlib import Path
import cv2 as cv
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[0]
IMAGE_DIR = PROJECT_ROOT / "C_data" / "Sample_images"

# Loads capture or stored frame
def load_image(filename):
    """
    Loader et billede fra projektets standard-billedmappe.
    
    Parametre:
        filename (str): Filnavn (fx "sample_01.png")

    Returnerer:
        ndarray: Billedet i BGR-format.

    Kaster:
        AssertionError hvis billedet ikke kan indlæses.
    """
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
    """
    Roterer et billede med en given vinkel, brugt ved
    debug og for at kompensere for kameraorientering.

    Parametre:
        img (ndarray): Inputbillede.
        angle (float): Rotationsvinkel i grader.
        rotPoint (tuple | None): Rotationscenter. Hvis None bruges billedets midte.

    Returnerer:
        ndarray: Det roterede billede.
    """
    (height,width) = img.shape[:2]

    if rotPoint is None:
        rotPoint = (width//2,height//2)
        
    RotationMatrix = cv.getRotationMatrix2D(rotPoint, angle, 1.0 )
    dimensions = (width, height)
    
    return cv.warpAffine(img, RotationMatrix, dimensions)
