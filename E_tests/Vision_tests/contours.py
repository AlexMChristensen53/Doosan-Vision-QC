import cv2 as cv
import numpy as np
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

img = load_image("Sample2.jpg")
img_resized = rescalePicture(img, scale=0.2)

blank = np.zeros(img_resized.shape, dtype='uint8')
cv.imshow('Blank', blank)

gray = cv.cvtColor(img_resized, cv.COLOR_BGR2GRAY)
blur = cv.GaussianBlur(gray, (1,1), cv.BORDER_DEFAULT)
canny = cv.Canny(blur, 125, 175)

ret, thresh = cv.threshold(gray, 125, 255, cv.THRESH_BINARY)

contours, hierarchies = cv.findContours(canny, cv.RETR_LIST, cv.CHAIN_APPROX_SIMPLE)
print(f"{len(contours)} contour(s) found!")

cv.drawContours(blank, contours, -1, (0,0,255), 1)
cv.imshow('Contours Drawn', blank)
cv.imshow('Canny', canny)

cv.imshow("Sample2", thresh)



cv.waitKey(0)