import cv2 as cv  
import numpy as np
import matplotlib.pyplot as plt
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture

img = load_image("Sample2.jpg")
img = rescalePicture(img, scale=0.2)
cv.imshow('IMG', img)

blank = np.zeros(img.shape[:2], dtype='uint8')

gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
cv.imshow('Gray', gray)

mask = cv.circle(blank, (img.shape[1]//2, img.shape[0]//2), 100, 255, -1)

masked = cv.bitwise_and(img,img,mask=mask)
cv.imshow('Mask', masked)

 #Grayscaling histogram
gray_hist = cv.calcHist([gray], [0], mask, [256], [0,256])

plt.figure()
plt.title('Grayscale Histogram')
plt.xlabel('Bins')
plt.ylabel('# of pixels')
plt.plot(gray_hist)
plt.xlim([0,256])

# Color Histogram

plt.figure()
plt.title('Color Histogram')
plt.xlabel('Bins')
plt.ylabel('# of pixels')
colors = ('b', 'g', 'r')
for i, col in enumerate(colors):
    hist = cv.calcHist([img], [i], mask, [256], [0,256])
    plt.plot(hist, color=col)
    plt.xlim([0,256])
    
plt.show()

cv.waitKey(0)