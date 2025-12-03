# receive_data.py
import time
from queue import Queue


class Data:
    def receive_data(self, s_getter, disconnect_event, robot_ready, batch_active, cmd_queue: Queue):
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

                up = text.upper()
                if "DONE" in up or "IDLE" in up:
                    # Robotten siger: jeg er færdig med en kommando
                    if batch_active.is_set():
                        if cmd_queue.empty():
                            # Ingen flere kommandoer → batch færdig
                            print("[Data] Batch færdig → batch_active.clear(), robot_ready.clear()")
                            batch_active.clear()
                            robot_ready.clear()
                        else:
                            # Der er flere kommandoer i køen → kør næste
                            print("[Data] DONE/IDLE → robot_ready.set() (næste kommando)")
                            robot_ready.set()
                    else:
                        # batch er ikke aktiv, men vi får DONE/IDLE → bare markér robotten som klar
                        robot_ready.set()

        except Exception as e:
            print(f"[Data] stoppet: {e}")
            disconnect_event.set()
            robot_ready.set()
