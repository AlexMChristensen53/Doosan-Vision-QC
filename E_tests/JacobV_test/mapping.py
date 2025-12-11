"""
mapping.py
Indeholder HomographyMapper-klassen, som konverterer pixelkoordinater fra
kameraet til robotkoordinater (mm) ved hjælp af et 3×3 homografi-matrix.

Homografi-matricen genereres ved kalibrering i et separat script og gemmes
i 'C_data/calibration_h.npz'.

Funktionalitet:
- Indlæsning af homografi-matrix fra fil
- Konvertering fra (x, y) pixel → (X, Y) robotkoordinater
- Intern normalisering og sikkerhedstjek på input
"""

import numpy as np
import cv2 as cv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple, List

ROOT = Path(__file__).resolve().parent
CALIB_PATH = ROOT / "calibration_h.npz"


@dataclass
class HomographyMapper:
    """
    Klasse til at udføre mapping mellem pixelkoordinater og robotkoordinater
    via et 3x3 homografi-matrix.

    Parametre:
        H (ndarray 3x3): Homografi-matrix genereret under kamerakalibrering.

    Metoder:
        - pixel_to_robot(x, y): konverterer pixelposition til mm-position
        - from_file(): indlæser 'calibration_h.npz' og returnerer instans
    """
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
    def from_file(cls, path: Path = CALIB_PATH):
        """
    Indlæser homografi-matrixen fra en .npz-fil.

    Parametre:
        path (str | Path): Valgfri sti. Hvis None bruges standardstien:
            C_data/calibration_h.npz

    Returnerer:
        HomographyMapper-instans med indlæst matrix.

    Kaster:
        FileNotFoundError hvis filen ikke findes.
    """
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
        """
    Konverterer et punkt fra pixel-koordinater (x, y)
    til robotkoordiner (X, Y) i millimeter.

    Parametre:
        x (float): Pixel X-position.
        y (float): Pixel Y-position.

    Returnerer:
        tuple(float, float): (Xr, Yr) - robotkoordinater i mm.
    """
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
