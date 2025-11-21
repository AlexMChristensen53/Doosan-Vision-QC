# Doosan Vision QC – Project 3B

This repository contains a Python-based quality control system using an OAK-D PoE camera and a Doosan M0617 robot arm. 

The objective is to detect objects placed randomly on a tray, classify them as OK or NOK, 
and provide coordinates and classifications to the robot for automated sorting.

---

## Quick Start

### Python Version
This project requires **Python 3.11**.  
Python 3.12+ is not supported due to DepthAI compatibility issues.

### 1. Create a virtual environment

**Windows**
1. python -m venv venv
2. Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
3. .\venv\Scripts\activate

### 2. Install dependencies
pip install -r requirements.txt

---

## Project Structure

```text
Doosan-Vision-QC/
├─ vision/
│  ├─ main.py               # Main program (idle loop, detection, robot output)
│  ├─ camera.py             # OAK-D camera interface
│  ├─ processing.py         # Object detection and QC logic
│  └─ robot_comms.py        # TCP/IP communication to Doosan robot
│  
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


### 1. Install dependencies
bash
pip install -r requirements.txt


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

## [Git Workflow](https://docs.google.com/document/d/1TSOkabhG66mFjT1kPjO0tYmKt7WV0dke9f8nmHOzbDQ/edit?usp=drive_link)
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
