# Angle_utils.py

def normalize_angle(angle: float) -> float:
    """Normalize angle to 0–180° (OpenCV compatible range)."""
    return float(angle % 180)


def compute_robot_angle(w: float, h: float, raw_angle: float) -> float:
    """
    Convert raw OpenCV angle into the FINAL robot tool angle.

    NOTE:
    - QCForm already normalizes width/height:
        width  = long side
        height = short side
    - So we must NOT swap w/h again here.
    - We only apply your calibrated offset to the raw angle.

    Right now this uses a single global offset that you can tune.
    """

    angle = normalize_angle(raw_angle)

    # --- SIMPLE CALIBRATION MODEL ---
    # Robot angle ≈ image angle + offset
    #
    # If, for example:
    #  - Image shows ~48°
    #  - Robot must be at 118°
    #  then offset ≈ +70°
    #
    # For now we keep offset = 0 and let you tune it.
    OFFSET = 0.0  # <-- adjust this after measuring on the robot

    robot_angle = angle + OFFSET

    return normalize_angle(robot_angle)
