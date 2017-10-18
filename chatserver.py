# server.py
import socket
import time

# create a socket object
serversocket = socket.socket(
	        socket.AF_INET, socket.SOCK_STREAM)

# get local machine name
host = socket.gethostname()

port = 9999
print("Host server started at "+host+" at port "+str(port))
message = "Hello there, client. "

# bind to the port
serversocket.bind((host, port))

# queue up to 5 requests
serversocket.listen(5)

while True:
    # establish a connection
    clientsocket,addr = serversocket.accept()

    print("Got a connection from %s" % str(addr))
    currentTime = time.ctime(time.time()) + "\r\n"
    clientsocket.send(message.encode('ascii')+"You joined the chat at ".encode('ascii')+currentTime.encode('ascii'))
    clientsocket.close()
