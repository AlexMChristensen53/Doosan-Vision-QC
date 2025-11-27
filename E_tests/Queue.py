class Queue:    #Her starter jeg med af definere klassen, under er funtioner

    def __init__(self): #Laver selve quenen som et array
        self.queue =[]  

    def enqueue(self, elemet): #Laver en kommand som smides i quenen
        self.queue.append(elemet)

    def dequeue(self):  #Fjerne den første i køen via .pop(0) som er -1 i et array
        if self.isEmpty():
            return "Køen er tom"
        return self.queue.pop(0) 
    
    def peek(self): #Peek kigger på den første i queuen
        if self.isEmpty():
            return "Queue is empty"
        return self.queue[0]
    
    def isEmpty(self):  #Kigger om arrayet er tomt, alså at den er længden af 0
        return len(self.queue) == 0
    
    def size (self):    #Kigger på størrelsen af queuen
        return len(self.queue)

myQueue = Queue() #

def inputs():
    while True:
        try:
            user_input = input("Indtast et element til køen (eller skriv 'stop' for at afslutte): ")
            if user_input.lower() == 'stop':
                input("Tryk Enter for at bekræfte afslutning...")
                dequeue()
                break
            myQueue.enqueue(user_input)

            print("Queue: ", myQueue.queue)
            print("isEmpty: ", myQueue.isEmpty())
            print("Size: ", myQueue.size())
        except KeyboardInterrupt:
            print("\nProgrammet blev afbrudt.")
            break

def dequeue(): 
    while True:
        if myQueue.isEmpty():
            print("Køen er tom. Afslutter programmet.")
            break
    for _ in range(myQueue.size()):
        user_input = input("Tryk 'o' for at dequeue det næste element, eller 'q' for at afslutte: ").lower()
        if user_input == 'o':
            command = myQueue.dequeue()
            # Simulate sending the command to a robot
            print(f"Sender kommando til robot: {command}")
            # Simulate receiving an "OK" response from the robot
            print("Robot svarer: OK")
            print("Queue after Dequeue: ", myQueue.queue)
        elif user_input == 'q':
            print("Afslutter programmet.")
        else:
            print("Ugyldigt input. Prøv igen.")

inputs = inputs()