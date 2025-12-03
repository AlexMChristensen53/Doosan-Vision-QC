import json
from pathlib import Path

class QCExport:
    def __init__(self, z_height_mm=55):
        """
        Export QC results to JSON robot command format.
        z_height_mm = constant tool Z during robot moves
        """
        self.z_height = z_height_mm

    def payload_to_json(self, robot_payload, filename="robot_commands.json"):
        """
        Convert QC robot payload to JSON command file.

        Format of each command:
            "add movel X Y Z ANGLE OK/NOK"
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

        out_path = Path(filename)
        with open(out_path, "w") as f:
            json.dump(data, f, indent=4)

        print(f"[EXPORT] Saved robot commands → {out_path.resolve()}")

        return out_path
