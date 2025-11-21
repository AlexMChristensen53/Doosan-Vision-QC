import cv2 as cv
from rescale_size_drawing import load_image
from rescale_size_drawing import rescalePicture


sample2 = load_image("Sample2.jpg")
resized_picture = rescalePicture(sample2, scale=0.2)

cv.imshow("Sample2", resized_picture)

# Converting to grayscale
gray = cv.cvtColor(resized_picture, cv.COLOR_BGR2GRAY)
cv.imshow("gray", gray)

# Blur
blur = cv.GaussianBlur(resized_picture, (7,7), cv.BORDER_DEFAULT)
cv.imshow("blur", blur)

# Edge Cascade
canny = cv.Canny(blur, 125, 175)
cv.imshow("canny", canny)

# Dilating images
dilated = cv.dilate(canny, (7,7), iterations=2)
cv.imshow("dilated", dilated)

# Eroding
eroded = cv.erode(dilated, (7,7), iterations=2)
cv.imshow("eroded", eroded)

# Resize
resized = cv.resize(resized_picture,(1024, 1080), interpolation=cv.INTER_AREA)
cv.imshow("resized", resized)

# Cropping
cropped = canny[150:450, 250:500]
cv.imshow("cropped", cropped)

cv.waitKey(0)