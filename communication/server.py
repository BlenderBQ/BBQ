import os
import socket

socket_path = 'server.sock'

class SocketServer(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def __enter__(self):
        self.sock.bind(socket_path)

    def __exit__(self, *args, **kwargs):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        os.remove(socket_path)

server_socket = SocketServer()
