import cv2 as cv  
import numpy as np  
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

img = load_image("Sample2.jpg")
img = rescalePicture(img, scale=0.2)

blank = np.zeros(img.shape[:2], dtype='uint8')
cv.imshow('Blank image', blank)

rectangle = cv.rectangle(blank.copy(), (50,50), (300,300), 255, -1)
circle = cv.circle(blank.copy(), (200,200), 200, 255, -1)

mask = cv.circle(blank, (img.shape[1]//2 + -50,img.shape[0]//2 + 45), 100, 255, -1)
#cv.imshow('Mask', mask)

weird_shape = cv.bitwise_and(circle, rectangle)
cv.imshow('Weird Shape', weird_shape)


masked = cv.bitwise_or(img,img,mask=weird_shape)
cv.imshow('Masked Image', masked)

cv.waitKey(0)
