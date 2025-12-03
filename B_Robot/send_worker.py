# send_worker.py
import queue
import time
import threading


class SendWorker:
    @staticmethod
    def send_worker(
        cmd_queue: queue.Queue,
        s_getter,
        disconnect_event: threading.Event,
        stop_event: threading.Event,
        robot_ready: threading.Event,
        batch_active: threading.Event,
    ):
        """
        Sender én kommando ad gangen til robotten.

        - Sender KUN når:
            * batch_active er sat (vi er i gang med en batch)
            * robot_ready er sat (robotten har sagt DONE/IDLE)
        - Når der er sendt én kommando, sættes robot_ready til "busy" (clear).
        - Når robotten sender DONE/IDLE, sætter receive_data robot_ready igen.
        """

        print("[SendWorker] start")

        try:
            while not (disconnect_event.is_set() or stop_event.is_set()):

                # Batch er ikke aktiv → vi skal ikke sende noget
                if not batch_active.is_set():
                    time.sleep(0.05)
                    continue

                # Robotten er ikke klar → vent
                if not robot_ready.is_set():
                    time.sleep(0.05)
                    continue

                # Robot klar + batch aktiv → prøv at få én kommando
                try:
                    command = cmd_queue.get(timeout=0.1)
                except queue.Empty:
                    # ingen kommandoer lige nu
                    time.sleep(0.05)
                    continue

                command = command.strip()
                if not command:
                    print("[SendWorker] Tom kommando, ignorerer")
                    continue

                # nu er robotten "busy" indtil vi får DONE
                robot_ready.clear()

                print(f"[SendWorker] Dequeued: {repr(command)}")

                sock = s_getter()
                if not sock:
                    print("[SendWorker] Ingen socket → lægger kommando tilbage i kø")
                    cmd_queue.put(command)
                    # robotten har ikke fået noget, så stadig klar
                    robot_ready.set()
                    time.sleep(0.2)
                    continue

                msg = command + "\n"
                print(f"[SendWorker] Sender: {repr(msg)}")

                try:
                    sock.sendall(msg.encode("utf-8"))
                    print("[SendWorker] ✓ Sendt")
                except Exception as e:
                    print(f"[SendWorker] FEJL ved send: {e}")
                    disconnect_event.set()
                    cmd_queue.put(command)
                    # vi ved ikke hvor vi er → lad robot_ready være klar
                    robot_ready.set()
                    return

                # NU gør vi ikke mere.
                # Når robotten er færdig, sender den DONE/IDLE,
                # og Data.receive_data håndterer robot_ready / batch_active.

        except Exception as e:
            print(f"[SendWorker] Send worker stoppet: {e}")
