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



