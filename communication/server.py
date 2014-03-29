import os
import json
import socket
import threading

socket_path = 'server.sock'

class CommandServer(object):
    def __init__(self):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._lock = threading.Lock()

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
        with self._lock:
            data['__cmd__'] = name
            json.dump(data, self.sockfile)
            self.sockfile.write(json.dumps(data) + '\n')
            self.sockfile.flush()

server_socket = CommandServer()
