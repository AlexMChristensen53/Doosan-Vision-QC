import numpy as np  
import cv2 as cv 
import sys
from Vision_tools import load_image

img = load_image("frame_1764151184544.png")
img_points = []
H = None
robot_points = []

def click_events(event, x, y, events, flags):
    global img_points, H
    
    if H is None and event == cv.EVENT_LBUTTONDOWN:
        img_points.append([x,y])
        print(f"[Pixel] Selected Point: {len(img_points)}: {[x, y]}" )
        
        # Draw dot on screen
        cv.circle(img, (x,y), 2, (0, 255, 0), -1)
        cv.imshow("image", img)
        
        if len(img_points) == 4:
            print(" 4 points have been selected")
            print("Enter corresponding robot coordinates:")
            
            for i in range(4):
                x = float(input(f"Robot x for point{i+1} :"))
                y = float(input(f"Robot y for point{i+1} :"))
                robot_points.append([x,y])
                
            calculate_homography()
            print("Homography calculated! click anywhere to convert pixel to coordinates.\n")
        
    elif H is not None and event == cv.EVENT_LBUTTONDOWN:
        p = np.array([x, y, 1.0])
        mapped = H @ p
        X = mapped[0] / mapped[2]
        Y = mapped[1] / mapped[2]

        print(f"[TEST] Pixel ({x},{y}) → Robot ({X:.2f}, {Y:.2f})")

        cv.circle(img, (x, y), 3, (0, 255, 0), -1)
        cv.imshow("image", img)


def calculate_homography():
    global H
    pixels = np.array(img_points, dtype=np.float32)
    robot = np.array(robot_points, dtype=np.float32)
    H, _ = cv.findHomography(pixels, robot)
    print("Homography matrix H:\n", H)        
        
cv.imshow("image", img)
cv.setMouseCallback("image", click_events)
cv.waitKey(0)
cv.destroyAllWindows()
        
        