from socket_com import socketCom

connected = None 

socket = socketCom.connected(HOST="192.168.137.51", PORT=20002, disconnect_event= connected)

