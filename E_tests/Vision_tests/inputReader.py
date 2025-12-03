# inputReader.py
import threading
from queue import Queue


class Reader:
    """Reader der fylder cmd_queue fra brugerens input."""

    def __init__(self,
                 disconnect_event: threading.Event | None = None,
                 cmd_queue: Queue | None = None):
        self.disconnect_event = disconnect_event
        self.cmd_queue: Queue = cmd_queue if cmd_queue is not None else Queue()

    def add_line(self, line: str):
        line = line.strip()
        if line:
            self.cmd_queue.put(line)

    def print_queue(self):
        if self.cmd_queue.empty():
            print("  (queue er tom)")
        else:
            print("  Indhold i cmd_queue:")
            for i, elem in enumerate(list(self.cmd_queue.queue)):
                print(f"    [{i}]: {elem}")

    def build_queue(self):
        print("Byg kø (fase 1)")
        print("Skriv:")
        print("  add <tekst>   (fx: add MOVEL 225.5 -250 55 90 OK)")
        print("  print         (vis queue)")
        print("  run           (start robotten)")
        print("  finish        (afslut uden at køre)")

        while True:
            cmd = input("> ").strip()

            if cmd.startswith("add "):
                text = cmd[4:]
                self.add_line(text)
                print(f"Tilføjet: {text}")

            elif cmd == "print":
                self.print_queue()

            elif cmd == "run":
                print("Starter fase 2 (robot kører køen)…")
                return "run"

            elif cmd == "finish":
                print("Afslutter uden at køre.")
                return "finish"

            else:
                print("Ukendt kommando.")
