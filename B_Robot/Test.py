from socket_com import socketCom
from inputReader import *
from myqueue import Queue


#Socket
connected = None 
#socket = socketCom.connected(HOST="192.168.137.51", PORT=20002, disconnect_event= connected)


#Input reader med kø
cmd_queue = Queue()
reader = Reader(disconnect_event=connected, input=None, queue_finish=None, cmd_queue = cmd_queue)

reader.test()

