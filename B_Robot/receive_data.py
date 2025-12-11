"""
receive_data.py
Håndterer indkommende TCP-data fra Doosan-robotten.

Funktionalitet:
- Lytter på robot-socket'en for statusbeskeder
- Opdaterer event-flags (robot_ready, batch_active)
- Afgør hvornår en batch af robotkommandoer er færdig
- Sikrer korrekt sekventiel afvikling af kommandoer i cmd_queue
"""
import time
from queue import Queue


class Data:
    """
    Klasse der indeholder metode til at modtage og behandle
    data fra robotten over en TCP socket.

    Metoder:
        receive_data(): Kører i en separat tråd og lytter på robotten.
    """
    def receive_data(self, s_getter, disconnect_event, robot_ready, batch_active, cmd_queue: Queue):
        """
    Lytter kontinuerligt på robotforbindelsen og håndterer robotstatus.

    Parametre:
        s_getter (callable): Funktion der returnerer aktiv socket.
        disconnect_event (Event): Sættes når forbindelsen afbrydes.
        robot_ready (Event): Signal til send_worker om robotten er klar
                             til næste kommando.
        batch_active (Event): Angiver om en batch af kommandoer er aktiv.
        cmd_queue (Queue): Kommandoer der mangler at blive sendt til robotten.

    Funktion:
        - Robotten sender "DONE" når den er klar.
        - Hvis batch_active er sat og cmd_queue er tom → batch afsluttes.
        - Hvis batch_active er sat og cmd_queue IKKE er tom → næste kommando sendes.
        - Hvis batch ikke er aktiv → markér robot som klar uden batchstyring.

    Returnerer:
        None - funktionen afsluttes når disconnect_event sættes.
    """
        print("[Data] start")

        try:
            while not disconnect_event.is_set():
                s = s_getter()
                if not s:
                    time.sleep(0.1)
                    continue

                try:
                    data = s.recv(1024)
                except Exception as e:
                    print(f"[Data] recv-fejl: {e}")
                    time.sleep(0.2)
                    continue

                if not data:
                    print("[Data] Robot lukkede forbindelsen")
                    disconnect_event.set()
                    return

                text = data.decode("utf-8", errors="replace").strip()
                if not text:
                    continue

                print(f"[Data] Robot: {repr(text)}")

                msg = text.upper()

                # --- FIX: React ONLY to DONE ---
                if "DONE" in msg:

                    # If no batch is active, ignore stray DONE messages
                    if not batch_active.is_set():
                        continue

                    # More commands waiting → next command
                    if not cmd_queue.empty():
                        print("[Data] DONE → robot_ready.set() (next command)")
                        robot_ready.set()
                        continue

                    # Queue empty → batch finished
                    print("[Data] Batch færdig → batch_active.clear(), robot_ready.clear()")
                    batch_active.clear()
                    robot_ready.clear()
                    continue

                # Ignore IDLE (robot is just reporting general state)
                if "IDLE" in msg:
                    continue

                    
        except Exception as e:
            print(f"[Data] stoppet: {e}")
            disconnect_event.set()
            robot_ready.set()
