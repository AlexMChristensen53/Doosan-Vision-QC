class Queue:
    def __init__(self):
        self.queue =[]

    def enqueue(self, elemet): 
        self.queue.append(elemet)

    def dequeue(self):
        if self.isEmpty():
            return "Køen er tom"
        return self.queue.pop(0) 
    
    def peek(self):
        if self.isEmpty():
            return "Queue is empty"
        return self.queue[0]
    
    def isEmpty(self):
        return len(self.queue) == 0
    
    def size (self):
        return len(self.queue)
