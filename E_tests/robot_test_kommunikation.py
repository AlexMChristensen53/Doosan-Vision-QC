import socket
import threading
import sys
import time
import queue
import os

# Add parent directory to path to import B_Robot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from B_Robot.send_worker import SendWorker

HOST = "192.168.137.51"  # Server (Doosan Robot) IP
PORT = 20002  # Server Port

class Doosan_robot():
    def input_reader(self, cmd_queue, stop_event):
        """Baggrundstråd: læser brugerinput og putter i køen."""
        try:
            while not stop_event.is_set():
                try:
                    line = input("Indtast kommando (MOVEL eller POPUPn,w,a): ").strip()
                except EOFError:
                    break
                if line:
                    cmd_queue.put(line)
        except Exception:
            pass




    def receive_data(self ,s, disconnect_event):
        """Funktion til at modtage data fra serveren.
        Sætter disconnect_event hvis forbindelsen lukkes eller fejl opstår.
        """
        try:
            while not disconnect_event.is_set():
                data = s.recv(1024)
                if not data:
                    print("\nForbindelsen blev lukket af serveren.")
                    disconnect_event.set()
                    return
                try:
                    text = data.decode('utf-8')
                except Exception:
                    text = repr(data)
                # Vis modtaget tekst og genskriv prompt
                sys.stdout.write(f"\rModtaget: {text}\n")
                sys.stdout.write("Indtast kommando (MOVEL eller POPUPn,w,a): ")
                sys.stdout.flush()
        except Exception as e:
            print(f"Fejl ved modtagelse: {e}")
            disconnect_event.set()

    def main(self):
        s = None
        backoff = 1.0
        try:
            # Prøv at forbinde indtil det lykkes; når forbindelsen tabes, genstart loopet
            while True:
                # Forbindelsesloop
                while True:
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(5.0)
                        s.connect((HOST, PORT))
                        s.settimeout(None)
                        print(f"✓ Succesfuldt forbundet til Doosan socket server på {HOST}:{PORT}")
                        try:
                            # Brug CRLF handshake for kompatibilitet
                            s.sendall(b"Connected to SUSAN\r\n")
                        except Exception:
                            pass
                        time.sleep(0.2)
                        # Genskab input-prompten efter genforbindelse
                        try:
                            sys.stdout.write("Indtast kommando (MOVEL eller POPUPn,w,a): ")
                            sys.stdout.flush()
                        except Exception:
                            pass
                        break
                    except KeyboardInterrupt:
                        print("\nAnnulleret af bruger før forbindelse blev etableret.")
                        if s:
                            s.close()
                        return
                    except Exception as e:
                        print(f"Kunne ikke forbinde til {HOST}:{PORT} ({e}). Prøver igen om {backoff:.1f}s...")
                        try:
                            s.close()
                        except Exception:
                            pass
                        time.sleep(backoff)
                        backoff = min(backoff * 2, 30.0)

                # Når forbundet: lav disconnect event og start receiver i en tråd
                disconnect_event = threading.Event()
                receive_thread = threading.Thread(target=self.receive_data, args=(s, disconnect_event), daemon=True)
                receive_thread.start()

                # Start input reader (kører persist over reconnects) og send_worker hvis ikke allerede startet
                try:
                    # cmd_queue og input thread oprettes én gang
                    if 'cmd_queue' not in globals():
                        globals()['cmd_queue'] = queue.Queue()
                    if 'input_stop' not in globals():
                        globals()['input_stop'] = threading.Event()
                        input_thread = threading.Thread(target=self.input_reader, args=(globals()['cmd_queue'], globals()['input_stop']), daemon=True)
                        globals()['input_thread'] = input_thread
                        input_thread.start()

                    # send_worker bruger en callable til at få aktuel socket
                    def s_getter():
                        return s

                    send_stop = threading.Event()
                    send_thread = threading.Thread(target=SendWorker.send_worker, args=(globals()['cmd_queue'], s_getter, disconnect_event, send_stop), daemon=True)
                    send_thread.start()

                    # Vent indtil vi mister forbindelsen
                    while not disconnect_event.is_set():
                        time.sleep(0.2)

                    # Når disconnect_event er sat: stop send_worker
                    send_stop.set()
                    send_thread.join(timeout=1.0)
                except KeyboardInterrupt:
                    print("\nAfslutter programmet (KeyboardInterrupt)")
                    try:
                        s.shutdown(socket.SHUT_RDWR)
                    except Exception:
                        pass
                    try:
                        s.close()
                    except Exception:
                        pass
                    # stop input thread
                    if 'input_stop' in globals():
                        globals()['input_stop'].set()
                    return

                # Hvis vi når hertil, blev disconnect_event sat -> luk og genforbind
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    s.close()
                except Exception:
                    pass
                print("Forbindelsen er afbrudt — forsøger genforbindelse...")
                # retry loop fortsætter
        finally:
            try:
                if s:
                    s.close()
            except Exception:
                pass

if __name__ == "__main__":
    robot = Doosan_robot()
    robot.main()