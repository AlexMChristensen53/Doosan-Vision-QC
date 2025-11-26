import cv2 as cv  
import numpy as np  

from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

sample2 = load_image("Sample2.jpg")
resized_picture = rescalePicture(sample2, scale=0.2)

# Averaging blur
average = cv.blur(resized_picture, (3,3))
cv.imshow('Average', average)

# Gaussian blur
gaussian = cv.GaussianBlur(resized_picture, (3,3), 0)
cv.imshow('Gaussian', gaussian)

# Median blur
median = cv.medianBlur(resized_picture, 3)
cv.imshow('Median', median)

# Bilateral blur
bilateral = cv.bilateralFilter(resized_picture, 10, 35, 25)
cv.imshow('Bilateral', bilateral)

cv.waitKey(0)