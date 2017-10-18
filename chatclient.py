# client.py
import socket

# create a socket object
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# get local machine name
host = socket.gethostname()


port = 9999

# connection to hostname on the port.
s.connect((host, port))
print("Found Host server at "+host+" at "+str(port))

# Receive no more than 1024 bytes
ms = s.recv(1024)


s.close()

print("Server says %s" % ms.decode('ascii'))
