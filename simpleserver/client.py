import socket
import sys

HOST = '127.0.0.1'
PORT = 10000
MAX_LENGTH = 4096
s = socket.socket()
s.connect((HOST, PORT))

msg = sys.argv[1:]
s.send(' '.join(msg))
message = s.recv(MAX_LENGTH)
print(message)
