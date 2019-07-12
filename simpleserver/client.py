import socket
import sys
from threading import Thread
HOST = '127.0.0.1'
PORT = 10000
MAX_LENGTH = 4096
s = socket.socket()
s.connect((HOST, PORT))

def _send(socket):
    msg = raw_input("Command To Send: ")
    if msg == "close":
        socket.shutdown(socket.SHUT_RDWR)
        socket.close()
        sys.exit(0)
    socket.send(msg)

def _recv(socket):
    message = socket.recv(MAX_LENGTH)
    print(message)

while 1:
    send = Thread(target=_send, args=(s,))
    send.start()
    receive = Thread(target=_recv, args=(s,))
    receive.start()

# while 1:
#     msg = raw_input("Command To Send: ")
#     if msg == "close":
#         s.shutdown(socket.SHUT_RDWR)
#         s.close()
#         sys.exit(0)
#     s.send(msg)

