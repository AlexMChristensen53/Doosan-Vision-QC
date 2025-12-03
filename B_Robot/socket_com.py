# socket_com.py
import socket
import time
import threading


class socketCom:
    def __init__(self):
        self.s: socket.socket | None = None

    def connected(self, HOST, PORT, disconnect_event: threading.Event):
        """
        Holder en TCP-forbindelse til robotten kørende.
        Sender INGEN data – det klarer send_worker.
        """
        backoff = 1.0

        while not disconnect_event.is_set():
            s = None
            try:
                print(f"[socketCom] Forsøger at connecte til {HOST}:{PORT}...")
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((HOST, PORT))
                s.settimeout(None)

                self.s = s
                print(f"[socketCom] ✓ Connected til {HOST}:{PORT}")

                # hold forbindelsen åben
                while not disconnect_event.is_set():
                    time.sleep(0.5)

            except Exception as e:
                print(f"[socketCom] Forbindelsesfejl: {e}")
                self.s = None
                if s:
                    try:
                        s.close()
                    except Exception:
                        pass

                if disconnect_event.is_set():
                    break

                print(f"[socketCom] Prøver igen om {backoff:.1f} sek...")
                time.sleep(backoff)
                backoff = min(backoff * 2, 30.0)

            finally:
                if s:
                    try:
                        s.close()
                    except Exception:
                        pass
                self.s = None

        print("[socketCom] Disconnect requested – stopper.")
