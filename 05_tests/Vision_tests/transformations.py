import cv2 as cv 
import numpy as np
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

img = load_image("Sample2.jpg")
resized_img = rescalePicture(img, scale=0.2)

cv.imshow("Sample2", resized_img)

# Translation
def translate(img, x, y):
    TranslateMatrix = np.float32([[1,0,x],[0,1,y]])
    dimensions = (img.shape[1], img.shape[0])
    return cv.warpAffine(img, TranslateMatrix, dimensions)

# -x --> Left
# -y --> Up
# x --> Right
# y --> Down

translated_image = translate(resized_img, -100, 50)
cv.imshow("translated", translated_image)

# Rotation 
def rotation(img, angle, rotPoint=None):
    (height,width) = img.shape[:2]

    if rotPoint is None:
        rotPoint = (width//2,height//2)
        
    RotationMatrix = cv.getRotationMatrix2D(rotPoint, angle, 1.0 )
    dimensions = (width, height)
    
    return cv.warpAffine(img, RotationMatrix, dimensions)

rotated = rotation(resized_img, 45)
cv.imshow("rotated", rotated)




