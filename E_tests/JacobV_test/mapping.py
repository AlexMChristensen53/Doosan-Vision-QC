# qc_mapping.py
import numpy as np
import cv2 as cv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, List

ROOT = Path(__file__).resolve().parent
CALIB_PATH = ROOT / "calibration_h.npz"


@dataclass
class HomographyMapper:
    H: np.ndarray

    # ------------------------------
    # Constructors
    # ------------------------------

    @classmethod
    def from_correspondences(
        cls,
        pixel_points: Iterable[Tuple[float, float]],
        robot_points: Iterable[Tuple[float, float]],
    ) -> "HomographyMapper":
        """
        pixel_points : centroids fundet af vision (x_pix, y_pix)
        robot_points : kendte robot-punkter (X_mm, Y_mm)
        """
        pix = np.asarray(list(pixel_points), dtype=np.float32)
        rob = np.asarray(list(robot_points), dtype=np.float32)

        if pix.shape != rob.shape or len(pix) < 4:
            raise ValueError("We need >= 4 matching pixel <-> robot points.")

        H, _ = cv.findHomography(pix, rob, method=0)
        if H is None:
            raise RuntimeError("Homography calculation failed")

        return cls(H=H)

    @classmethod
    def from_file(cls, path: Path = CALIB_PATH) -> "HomographyMapper":
        data = np.load(str(path))
        return cls(H=data["H"])

    # ------------------------------
    # Save
    # ------------------------------

    def save(self, path: Path = CALIB_PATH):
        path.parent.mkdir(parents=True, exist_ok=True)
        np.savez(str(path), H=self.H)

    # ------------------------------
    # Mapping functions
    # ------------------------------

    def pixel_to_robot(self, x: float, y: float) -> Tuple[float, float]:
        pt = np.array([x, y, 1.0], dtype=float)
        dst = self.H @ pt
        X = dst[0] / dst[2]
        Y = dst[1] / dst[2]
        return float(X), float(Y)

    def pixels_to_robot(
        self, points: Iterable[Tuple[float, float]]
    ) -> np.ndarray:
        pts = np.asarray(list(points), dtype=float)
        if len(pts) == 0:
            return np.empty((0, 2))
        homog = np.hstack([pts, np.ones((len(pts), 1))])
        dst = (self.H @ homog.T).T
        XY = dst[:, :2] / dst[:, 2:3]
        return XY
