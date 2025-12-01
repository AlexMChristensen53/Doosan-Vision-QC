import queue
import time


class SendWorker:
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


if __name__ == "__main__":
    worker = SendWorker()
