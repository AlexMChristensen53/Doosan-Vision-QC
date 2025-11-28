import socket
import time
import threading


class socketCom:
    def connected(HOST, PORT, disconnect_event=None):
        """
        Opretter og vedligeholder en TCP-forbindelse til en server.
        Når forbindelsen ryger, forsøger den at genoprette forbindelsen.
        """
        if disconnect_event is None:
            disconnect_event = threading.Event()

        s = None
        backoff = 1.0

        try:
            while not disconnect_event.is_set():

                # 1) FORSØG AT CONNECTE
                while not disconnect_event.is_set():
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(5.0)
                        s.connect((HOST, PORT))
                        s.settimeout(None)

                        print(f"✓ Connected to Doosan server at {HOST}:{PORT}")

                        try:
                            s.sendall(b"Connected to SUSAN\r\n")
                        except Exception:
                            print("Failed to send initial message.")
                            break

                        time.sleep(0.2)
                        backoff = 1.0
                        break

                    except KeyboardInterrupt:
                        print("\nCancelled by user during connection attempt.")
                        disconnect_event.set()
                        return

                    except Exception as e:
                        print(f"Could not connect to {HOST}:{PORT} ({e}). Retrying in {backoff:.1f}s...")
                        if s:
                            try:
                                s.close()
                            except Exception:
                                pass

                        time.sleep(backoff)
                        backoff = min(backoff * 2, 30.0)

                # 2) PING / KEEP-ALIVE LOOP
                while not disconnect_event.is_set():
                    try:
                        s.sendall(b"PING\r\n")
                        time.sleep(5.0)  # Adjust keep-alive interval as needed
                    except Exception:
                        print("Connection lost. Attempting to reconnect...")
                        break

                # 3) RYD OP OG RECONNECT
                if s:
                    try:
                        s.shutdown(socket.SHUT_RDWR)
                    except Exception:
                        pass
                    try:
                        s.close()
                    except Exception:
                        pass

                # Hvis disconnect_event ikke er sat, prøv at genoprette forbindelsen
                if not disconnect_event.is_set():
                    print("Reconnecting...")
                    continue

                print("Disconnect requested — stopping.")
                break

        finally:
            if s:
                try:
                    s.close()
                except Exception:
                    pass


if __name__ == "__main__":
    com = socketCom()
