# Test.py
import threading
import time
from queue import Queue
import json
import os

from socket_com import socketCom
from send_worker import SendWorker
from receive_data import Data

HOST = "192.168.137.51"
PORT = 20002

# filen fra vision-kameraet (som du allerede havde)
VISION_JSON_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "C_data",
    "robot_commands.json"
)


def load_vision_commands(cmd_queue: Queue) -> int:
    """
    Læser JSON-filen fra vision-kameraet og fylder cmd_queue med kommandoer.
    Forventer format:
    {
        "objects": [
            "add movel 97.55 233.55 55 26.49 NOK",
            "add movel 203.69 349.56 55 138.39 NOK"
        ]
    }
    """
    # tøm eksisterende queue først
    while not cmd_queue.empty():
        try:
            cmd_queue.get_nowait()
        except Exception:
            break

    with open(VISION_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    objects = data.get("objects", [])
    count = 0

    for raw in objects:
        if not isinstance(raw, str):
            continue

        line = raw.strip()
        # fjern evt. "add " foran
        if line.lower().startswith("add "):
            line = line[4:]

        # læg kommandoen i køen (du kan vælge at upper-case hvis du vil)
        cmd_queue.put(line)
        count += 1

    print(f"[MAIN] Indlæste {count} kommandoer fra JSON.")
    return count


def main():
    cmd_queue = Queue()

    com = socketCom()
    disconnect_event = threading.Event()
    stop_event = threading.Event()

    robot_ready = threading.Event()   # robot klar/busy
    batch_active = threading.Event()  # om vi er midt i en batch

    # 1) Start socket-forbindelse
    t_conn = threading.Thread(
        target=com.connected,
        args=(HOST, PORT, disconnect_event),
        daemon=True,
    )
    t_conn.start()

    # 2) Start data-modtager
    data_receiver = Data()
    t_recv = threading.Thread(
        target=data_receiver.receive_data,
        args=(lambda: com.s, disconnect_event, robot_ready, batch_active, cmd_queue),
        daemon=True,
    )
    t_recv.start()

    # 3) Start send-worker
    t_send = threading.Thread(
        target=SendWorker.send_worker,
        args=(cmd_queue, lambda: com.s, disconnect_event, stop_event, robot_ready, batch_active),
        daemon=True,
    )
    t_send.start()

    print("=== Automatisk JSON-mode ===")
    print(f"Overvåger fil: {VISION_JSON_PATH}")
    print("Når filen ændres, indlæses kommandoer og en batch køres automatisk.")

    last_processed_mtime = None   # sidste mtime vi HAR kørt
    pending_mtime = None          # mtime som venter på at nuværende batch bliver færdig

    try:
        while not disconnect_event.is_set():
            # tjek om filen findes / har ændret sig
            try:
                mtime = os.path.getmtime(VISION_JSON_PATH)
            except FileNotFoundError:
                mtime = None

            # der er en ny ændring i JSON-filen
            if mtime is not None and mtime != last_processed_mtime:
                if not batch_active.is_set():
                    # vi er idle → vi kan starte en ny batch med det samme
                    print(f"[MAIN] Ændring registreret i JSON (mtime={mtime}) → loader og starter batch")
                    try:
                        count = load_vision_commands(cmd_queue)
                        if count > 0:
                            batch_active.set()
                            robot_ready.set()
                            last_processed_mtime = mtime
                        else:
                            print("[MAIN] JSON indeholdt ingen kommandoer – ingen batch startet.")
                            last_processed_mtime = mtime
                    except Exception as e:
                        print(f"[MAIN] Fejl ved læsning af JSON: {e}")
                else:
                    # der kører allerede en batch → vi venter med at køre denne ændring
                    print("[MAIN] JSON ændret mens batch kører – gemmer til næste batch.")
                    pending_mtime = mtime

            # hvis vi IKKE er midt i en batch, men vi har en pending ændring
            if (not batch_active.is_set()
                    and pending_mtime is not None
                    and pending_mtime != last_processed_mtime):
                print("[MAIN] Batch afsluttet – starter ny batch fra seneste JSON.")
                try:
                    count = load_vision_commands(cmd_queue)
                    if count > 0:
                        batch_active.set()
                        robot_ready.set()
                        last_processed_mtime = pending_mtime
                    else:
                        print("[MAIN] JSON indeholdt ingen kommandoer – ingen batch startet.")
                        last_processed_mtime = pending_mtime
                except Exception as e:
                    print(f"[MAIN] Fejl ved læsning af JSON (pending): {e}")
                finally:
                    pending_mtime = None

            time.sleep(0.1)  # undgå at spinne CPU'en

    except KeyboardInterrupt:
        print("\n[MAIN] Ctrl+C – stopper…")
        stop_event.set()
        disconnect_event.set()
        robot_ready.set()
        batch_active.clear()

    time.sleep(0.5)


if __name__ == "__main__":
    main()
