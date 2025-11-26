import sys
import cv2
import depthai as dai

print("===================================")
print("  Versionsoversigt på systemet")
print("===================================")
print(f"Python  : {sys.version.split()[0]}")
print(f"OpenCV  : {cv2.__version__}")
print(f"DepthAI : {dai.__version__}")
print("===================================")