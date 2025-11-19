from pathlib import Path
import numpy as np
import cv2 as cv

# Variables to locate "Sample_images" folder
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
PICTURE_FOLDER = PROJECT_ROOT / "data" / "Sample_images"


def load_image(filename):
    """Always loads images from path in variable "PICTURE_FOLDER"
    """
    path = PICTURE_FOLDER / filename
    img = cv.imread(path)
    assert img is not None, f"Could not read image: {path}"
    return img

def rescalePicture(frame, scale=0.4):
    """Rescales the picture

    Args:
        frame (_type_): jpg, png
        scale (float, optional): Change this value depending on rescale needs. Defaults to 0.4.

    Returns:
        _type_: jpg, png
    """
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
           f"Image Size: {Picture_size_text}px",
           (10,30), 
           font, 1,(255,255,255),2,cv.LINE_AA)
cv.imshow("Sample2", resized_image)

drawing = False # true if mouse is pressed
mode = True # if True, draw rectangle.
ix, iy = -1, -1

original = resized_image.copy()
overlay = resized_image.copy()

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, mode, original, overlay
    
    if not mode:
        return
    
    if event == cv.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y
        
    elif event == cv.EVENT_MOUSEMOVE and drawing:
        overlay = original.copy()
        cv.rectangle(overlay, (ix, iy), (x, y), (255, 0, 0), 3)
                
    elif event == cv.EVENT_LBUTTONUP and drawing:
        drawing = False
        cv.rectangle(original, (ix, iy), (x, y),(255,0,0), 3)
        overlay = original.copy()
                
cv.namedWindow("Sample2")
cv.setMouseCallback("Sample2", draw_rectangle)

while True:
    cv.imshow("Sample2", overlay)
    k = cv.waitKey(1) & 0xFF
    if k == ord("m"):
        mode = not mode
    elif k == 27:
        break
    
cv.destroyAllWindows()

print(img.shape)
if len(img.shape) == 3:
    print("Color image (BGR)")
else:
    print("Grayscale image")