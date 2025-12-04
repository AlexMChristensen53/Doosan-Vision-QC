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
