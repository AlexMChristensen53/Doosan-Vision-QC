import matplotlib.pyplot as plt
import cv2 as cv
from rescale_size_drawing import load_image

img = load_image("frame_1764079701216.png")
img = cv.cvtColor(img, cv.COLOR_BGR2RGB)

plt.figure(figsize=(8, 6))   # keep aspect ratio
plt.imshow(img)
plt.axis('on')
pts = plt.ginput(2)          # click 2 exact points
plt.close()

print(pts)  # This gives the TRUE pixel coordinates
