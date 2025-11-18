import socket
import threading

HOST = "192.168.137.51"  # Server (Doosan Robot) IP
PORT = 20002  # Server Port

def send_commands(s):
    """Funktion til at sende kommandoer til serveren"""
    try:
        while True:
            command = input("Indtast kommando (f.eks. MOVEL): ").strip()
            print(f"  [INPUT DEBUG] Modtaget: '{command}'")
            if command:
                # Tilføjer automatisk de sidste 3 cifre til MOVEL commands
                parts = command.split()
                if parts and parts[0] == "MOVEL":
                    if len(parts) == 4:
                        command = f"{command} -25 0 0"
                        print(f"  ✓ Kommando udvidet til: {command}")
                    else:
                        print(f"  Kommando IKKE udvidet - der er {len(parts)-1} talværdier (forventet 3)")
                
                # Tilføj \r\n (carriage return + line feed) så formatet matcher Hercules
                if not command.endswith('\r\n'):
                    command += '\r\n'
                command_bytes = command.encode()
                s.sendall(command_bytes)
                print(f"✓ Sendt: {command.strip()}")
    except EOFError:
        pass
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
            print(f"Modtaget: {data!r}")
    except Exception as e:
        print(f"Fejl ved modtagelse: {e}")

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    print(f"✓ Succesfuldt forbundet til Doosan socket server på {HOST}:{PORT}")
    s.sendall(b"Connected to SUSAN\n")
    
    # Start tråd til at modtage data
    receive_thread = threading.Thread(target=receive_data, args=(s,), daemon=True)
    receive_thread.start()
    
    # Start tråd til at sende kommandoer
    send_commands(s)