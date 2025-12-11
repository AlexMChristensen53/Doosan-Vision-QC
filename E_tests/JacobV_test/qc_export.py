"""
qc_export.py
Håndterer genereringen af JSON-filen som Doosan-robotten læser.
Filen indeholder en liste af kommando-strenge der sendes til robotten,
typisk i formatet:

"add movel X Y Z Angle OK/NOK"

Dette modul har ansvaret for:
- Konvertering af QC-resultater til robotkommandoer
- Skrive en fuld JSON-struktur til disk
- Håndtere fast Z-højde (pick height)
"""
import json
from pathlib import Path

class QCExport:
    """
    Klasse der genererer robot-kommando JSON-filen.

    Parametre:
        z_height_mm (float): Fast Z-værdi som robotten skal bruge ved pick.

    Metoder:
        - payload_to_json(payload): skriver listen af kommandoer til disk.

    Anvendelse:
        payload forventes at være en liste med dicts:
            {
                "id": int,
                "ok": bool,
                "x_mm": float,
                "y_mm": float,
                "angle_deg": float
            }
    """
    def __init__(self, z_height_mm=55):
        """
        Export QC results to JSON robot command format.
        """
        self.z_height = z_height_mm

        # ROOT = project root (Doosan-Vision-QC folder)
        self.ROOT = Path(__file__).resolve().parents[2]

        # C_data ALWAYS exists in project root
        self.CDATA = self.ROOT / "C_data"

    def payload_to_json(self, robot_payload, filename="robot_commands.json"):
        """
    Konverterer en liste af QC-payloads til robot-kommandoer
    og gemmer dem i 'C_data/robot_commands.json'.

    Parametre:
        payload (list[dict]): Liste af objekter med robotposition, vinkel
                              og OK/NOK vurdering.

    Returnerer:
        None - skriver JSON til filsystemet.

    JSON-format:
        {
            "objects": [
                "add movel X Y Z Angle OK",
                "add movel X Y Z Angle NOK",
                ...
            ]
        }
    """

        commands = []

        for item in robot_payload:
            X = round(item["x_mm"], 2)
            Y = round(item["y_mm"], 2)
            A = round(item["angle_deg"], 2)
            status = "OK" if item["ok"] else "NOK"

            cmd = f"add movel {X} {Y} {self.z_height} {A} {status}"
            commands.append(cmd)

        data = {"objects": commands}

        # Save inside project-level C_data
        out_path = self.CDATA / filename

        with open(out_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"[EXPORT] Saved robot commands → {out_path}")

        return out_path
