from myqueue import Queue


class Reader:
    """Reader der læser linjer og putter dem i en Queue."""

    def __init__(self, disconnect_event=None, input=None, queue_finish=False, cmd_queue=None, queue_peek=None):
        self.disconnect_event = disconnect_event
        self.queue_finish = queue_finish
        self.input = input
        self.queue_peek = queue_peek
        # brug caller's queue eller lav en ny instans af din Queue
        self.cmd_queue = cmd_queue if cmd_queue is not None else Queue()

    def reader(self):
        """Behandler ÉN 'cyklus' med den nuværende self.input og self.queue_finish."""
        if self.disconnect_event:
            return  # hvis vi er 'disconnected', gør ingenting

        line = self.input

        # hvis vi har en linje og ikke er i dequeue-mode → enqueue
        if line and not self.queue_finish:
            self.cmd_queue.enqueue(line)

        # hvis bit er sat → dequeue én gang
        if self.queue_finish:
            self.cmd_queue.dequeue()
            self.queue_finish = False  # nulstil bit
        
        if line is not None:
            self.queue_peek = self.cmd_queue.peek()

    def print_queue(self):
        """Hjælpefunktion til at printe hele køen pænt."""
        if self.cmd_queue.isEmpty():
            print("  (queue er tom)")
        else:
            print("  Indhold i queue:")
            for i, elem in enumerate(self.cmd_queue.queue):
                print(f"    [{i}]: {elem}")

    def test(self):
        """Interaktiv test af Reader og køen."""
        print("Test af Queue")
        print("Skriv kommandoer:")
        print(" - add <tekst>")
        print(" - dequeue")
        print(" - print")
        print(" - finish")

        while True:
            cmd = input("> ").strip()

            if not cmd:
                continue

            # enqueue via Reader
            if cmd.startswith("add "):
                text = cmd[len("add "):]
                self.input = text          # giv Reader en linje
                self.queue_finish = False  # vi vil enqueue
                self.reader()              # kør ÉN cyklus
                print(text)

            # dequeue via queue_finish-bit
            elif cmd == "dequeue":
                self.input = None          # ingen ny linje
                self.queue_finish = True   # bit aktiv
                self.reader()              # kør ÉN cyklus (dequeue)

            elif cmd == "print":
                self.print_queue()
                print (self.queue_peek)

            elif cmd == "finish":
                print("Afslutter test…")
                break

            else:
                print("Ukendt kommando.")


if __name__ == "__main__":
    reader = Reader(disconnect_event=False)
    reader.test()
