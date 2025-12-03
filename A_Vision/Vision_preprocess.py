import cv2 as cv
from Vision_tools import (
    load_image, to_gray, blurred, threshold_binary,
    edges, get_contours, downscale
)


from A_Vision.Vision_camera import OakCamera
oak = OakCamera()

def get_frame(source="image", filename=None):
    if source == "image":
        return load_image(filename)
    elif source == "camera":
        return oak.get_frame()
    else:
        raise ValueError("Invalid source")

def run(source="image", filename=None):
    frame = get_frame(source, filename)
    down_scale = downscale(frame)

    gray = to_gray(down_scale)
    blur = blurred(gray)
    thres = threshold_binary(blur)
    edge = edges(blur)
    contours = get_contours(edge)

    print(f"Found {len(contours)} contours")

    cv.imshow("Frame", down_scale)
    cv.imshow("Gray", gray)
    cv.imshow("Edges", edge)
    cv.imshow("Thresh", thres)
    cv.waitKey(0)

if __name__ == "__main__":
  run(source="image", filename="frame_1764083636036.png")
