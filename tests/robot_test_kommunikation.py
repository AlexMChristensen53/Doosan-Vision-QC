import socket
import threading
import sys
import time 

HOST = "192.168.137.51"  # Server (Doosan Robot) IP
PORT = 20002  # Server Port

def send_commands(s):
    """Funktion til at sende kommandoer til serveren"""
    try:
        while True:
            command = input("Indtast kommando (MOVEL eller POPUPn,w,a): ").upper().strip()
            if command:
                # Tilføjer automatisk de sidste 3 cifre til MOVEL commands
                parts = command.split()
                if parts and parts[0] == "MOVEL":
                    if len(parts) == 4:
                        command = f"{command} -25 0 0"
                elif parts and parts[0].startswith("POPUP"):
                    # Kombiner POPUP kommandoen og teksten i én besked
                    popup_type = parts[0][5:]  # Ekstraher 'n', 'w', eller 'a'
                    popup_message = " ".join(parts[1:])
                    if popup_type and popup_message:
                        full_popup_command = f"POPUP{popup_type} {popup_message}\r\n"
                        s.sendall(full_popup_command.encode())
                # Tilføj \r\n (carriage return + line feed) så formatet matcher Hercules
                if not command.endswith('\r\n'):
                    command += '\r\n'
                command_bytes = command.encode()
                s.sendall(command_bytes)
                print(f"✓ Sendt: {command.strip()}")
    except Exception as e:
        print(f"Fejl ved sending af kommando: {e}")

def receive_data(s):
    """Funktion til at modtage data fra serveren"""
    try:
        while True:
            data = s.recv(1024)
            if not data:
                print("Forbindelsen blev lukket af serveren.")
                break
    except Exception as e:
        print(f"Fejl ved modtagelse: {e}")

def main():
    s = None
    backoff = 1.0
    try:
        # Prøv at forbinde indtil det lykkes
        while True:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(5.0)
                s.connect((HOST, PORT))
                s.settimeout(None)
                print(f"✓ Succesfuldt forbundet til Doosan socket server på {HOST}:{PORT}")
                # Send initial besked (kan bruge \n her)
                try:
                    s.sendall(b"Connected to SUSAN\n")
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

    except Exception as e:
        print(f"Uventet fejl under forbindelse: {e}")
        if s:
            s.close()
        return

    # Når forbundet: start receiver og sender
    try:
        receive_thread = threading.Thread(target=receive_data, args=(s,), daemon=True)
        receive_thread.start()
        send_commands(s)
    except KeyboardInterrupt:
        print("\nAfslutter programmet (KeyboardInterrupt)")
    finally:
        try:
            s.close()
        except Exception:
            pass

if __name__ == "__main__":
    main()