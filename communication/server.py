import os
import json
import socket

socket_path = 'server.sock'

class CommandServer(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def __enter__(self):
        self.setup()

    def __exit__(self, *args, **kwargs):
        self.cleanup()

    def setup(self):
        self.sock.bind(socket_path)
        self.sockfile = self.sock.makefile()

    def cleanup(self):
        self.sock.shutdown(socket.SHUT_RDWR)
        self.sock.close()
        os.remove(socket_path)

    def send_command(self, name, data):
        data['__cmd__'] = name
        self.sockfile.write(json.dumps(data) + '\n')
        self.sockfile.flush()

server_socket = CommandServer()
