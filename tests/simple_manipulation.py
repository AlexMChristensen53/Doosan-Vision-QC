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

def rescalePicture(frame, scale=0.4):
    width = int(frame.shape[1] * scale)
    height = int(frame.shape[0] * scale)
    
    dimensions = (width,height)
    
    return cv.resize(frame, dimensions, interpolation=cv.INTER_AREA)

img = load_image("Sample2.jpg")
resized_image = (rescalePicture(img))
h, w = img.shape[:2]
Picture_size_text = f"{h} x {w}"
font = cv.FONT_ITALIC

cv.putText(resized_image,
           f"Image Size: {Picture_size_text}",
           (10,30), 
           font, 1,(255,255,255),2,cv.LINE_AA)
cv.imshow("Sample2", resized_image)

print(img.shape)
cv.waitKey(0)