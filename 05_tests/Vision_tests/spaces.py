import cv2 as cv 
import matplotlib.pyplot as plt
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

img = load_image("Sample2.jpg")
img = rescalePicture(img, scale=0.2)

# BGR to Grayscale
gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow('GRAY', gray)

# BGR to HSV
hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
cv.imshow('BGR', hsv)

# BGR to LAB
lab = cv.cvtColor(img, cv.COLOR_BGR2LAB)
cv.imshow('LAB', lab)

# BGR to RGB
rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
cv.imshow('RGB', rgb)

# HSV to BGR
hsv_bgr = cv.cvtColor(hsv, cv.COLOR_HSV2BGR)
cv.imshow('HSV_BGR', hsv_bgr)

# LAB to BGR
lab_bgr = cv.cvtColor(hsv, cv.COLOR_LAB2BGR)
cv.imshow('LAB_BGR', lab_bgr)

plt.imshow(rgb)
plt.show()

cv.waitKey(0)