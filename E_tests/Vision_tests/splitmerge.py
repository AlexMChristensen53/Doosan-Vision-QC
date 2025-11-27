import cv2 as cv 
import numpy as np  

from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture


sample2 = load_image("Sample2.jpg")
resized_picture = rescalePicture(sample2, scale=0.2)

blank = np.zeros(resized_picture.shape[:2], dtype='uint8')

b,g,r = cv.split(resized_picture)

blue = cv.merge([b, blank,blank])
green = cv.merge([blank, g, blank])
red = cv.merge([blank, blank, r])

cv.imshow('Blue', blue)
cv.imshow('Green', green)
cv.imshow('Red', red)

print (resized_picture.shape)
print(b.shape)
print(g.shape)
print(r.shape)

merged = cv.merge([b,g,r])
cv.imshow('Merged', merged)

cv.waitKey(0)