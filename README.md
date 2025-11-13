# Doosan Vision QC – Project 3B

This repository contains a Python-based quality control system using an OAK-D PoE camera and a Doosan M0617 robot arm. 

The objective is to detect objects placed randomly on a tray, classify them as OK or NOK, 
and provide coordinates and classifications to the robot for automated sorting.

---

## Project Structure

```text
Doosan-Vision-QC/
├─ vision/
│  ├─ main.py               # Main program (idle loop, detection, robot output)
│  ├─ camera.py             # OAK-D camera interface
│  ├─ processing.py         # Object detection and QC logic
│  ├─ robot_comms.py        # TCP/IP communication to Doosan robot
│  └─ __init__.py
│
├─ robot/
│  ├─ doosan-programs/      # Robot-side programs/scripts
│  └─ docs/                 # Robot setup notes, IP configuration, ports, etc.
│
├─ data/
│  └─ Sample_images/        # Small test images (no large files)
│
├─ docs/
│  ├─ Flowcharts/           # System flowcharts (PNG/PDF)
│  └─ notes.md              # Technical notes and documentation
│
├─ tests/
│  ├─ test_camera.py        # Basic camera test
│  └─ test_communication.py # TCP/IP communication test
│
├─ .gitignore               # Python gitignore
├─ requirements.txt         # Python dependencies
└─ README.md
```

---

## Quick Start

### 1. Create a virtual environment (recommended)
Windows:
bash
py -3 -m venv venv
venv\Scripts\activate


Linux / Mac:
bash
python3 -m venv venv
source venv/bin/activate


### 2. Install dependencies
bash
pip install -r requirements.txt


### 3. Run the project
bash
python vision/main.py


---

## System Overview
1. The OAK-D PoE camera runs in an idle loop and captures frames.
2. The software checks whether the tray is empty.
3. When objects appear, the system waits 5 seconds for stability.
4. Image processing is performed using OpenCV.
5. Objects are detected and classified as OK or NOK based on:
   - shape deviations  
   - missing features  
   - holes or geometric irregularities  
   - (optional) color differences  
6. Coordinates and classification results are sent to the Doosan robot via TCP/IP.
7. The robot sorts the objects accordingly.
8. The system returns to idle mode.

---

## Git Workflow [(refer to GitHub Workflow.docs on google drive)](https://docs.google.com/document/d/1TSOkabhG66mFjT1kPjO0tYmKt7WV0dke9f8nmHOzbDQ/edit?usp=drive_link)
- Always pull before making changes.
- Use feature branches for new functionality.
- Commit small, clear changes.
- Push only when the code is stable.
- Avoid large files in the repository.

---

## Notes
- `vision/` contains all Python logic.
- `robot/` contains Doosan-related scripts and documentation.
- `data/` contains small test images only.
- `docs/` contains diagrams and supporting documentation.
- `tests/` contains simple debugging scripts.
