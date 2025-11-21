import socket
import threading
import sys
import time
import queue

HOST = "192.168.137.51"  # Server (Doosan Robot) IP
PORT = 20002  # Server Port

def input_reader(cmd_queue, stop_event):
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


def send_worker(cmd_queue, s_getter, disconnect_event, stop_event):
    """Worker: tager kommandoer fra køen og sender dem over den aktuelle socket.
    s_getter er en callable der returnerer den aktuelle socket-objekt (eller None).
    stop_event bruges ved program-afslutning.
    """
    try:
        while not (disconnect_event.is_set() or stop_event.is_set()):
            try:
                command = cmd_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if not command:
                continue
            command_up = command.upper().strip()

            parts = command_up.split()
            # POPUP håndtering
            if parts and parts[0].startswith("POPUP"):
                popup_type = parts[0][5:]
                popup_message = " ".join(parts[1:])
                if popup_type and popup_message:
                    full_popup_command = f"POPUP{popup_type} {popup_message}\r\n"
                    try:
                        sock = s_getter()
                        if sock:
                            sock.sendall(full_popup_command.encode())
                            print(f"✓ Sendt: {full_popup_command.strip()}")
                        else:
                            # Ingen forbindelse: sæt tilbage i kø og vent
                            cmd_queue.put(command)
                            time.sleep(0.2)
                    except Exception as e:
                        print(f"Fejl ved sending af kommando: {e}")
                        disconnect_event.set()
                        cmd_queue.put(command)
                        return
                    continue

            # MOVEL udvidelse
            if parts and parts[0] == "MOVEL" and len(parts) == 4:
                command_up = f"{command_up} -25 0 0"

            if not command_up.endswith('\r\n'):
                command_up += '\r\n'

            try:
                sock = s_getter()
                if sock:
                    sock.sendall(command_up.encode())
                    print(f"✓ Sendt: {command_up.strip()}")
                else:
                    cmd_queue.put(command)
                    time.sleep(0.2)
            except Exception as e:
                print(f"Fejl ved sending af kommando: {e}")
                disconnect_event.set()
                cmd_queue.put(command)
                return
    except Exception as e:
        print(f"Send worker stoppet: {e}")

def receive_data(s, disconnect_event):
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

def main():
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
            receive_thread = threading.Thread(target=receive_data, args=(s, disconnect_event), daemon=True)
            receive_thread.start()

            # Start input reader (kører persist over reconnects) og send_worker hvis ikke allerede startet
            try:
                # cmd_queue og input thread oprettes én gang
                if 'cmd_queue' not in globals():
                    globals()['cmd_queue'] = queue.Queue()
                if 'input_stop' not in globals():
                    globals()['input_stop'] = threading.Event()
                    input_thread = threading.Thread(target=input_reader, args=(globals()['cmd_queue'], globals()['input_stop']), daemon=True)
                    globals()['input_thread'] = input_thread
                    input_thread.start()

                # send_worker bruger en callable til at få aktuel socket
                def s_getter():
                    return s

                send_stop = threading.Event()
                send_thread = threading.Thread(target=send_worker, args=(globals()['cmd_queue'], s_getter, disconnect_event, send_stop), daemon=True)
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
    main()