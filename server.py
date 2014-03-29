import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap

import socket
import threading
from controllers import set_current_controller, disable_current_controller
from controllers import SculptListener
from communication.server import server_socket

clients = []
_lock = threading.Lock()

def send_command(name, data):
    with _lock:
        data['__cmd__'] = name
        jdata = json.dumps(data) + '\n'
        for c in clients:
            try:
                c.send(jdata)
            except IOError as e:
                logging.exception(e)
                clients.remove(c)

if __name__ == '__main__':
    socket_path = 'server.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(socket_path)
    sock.listen()

    print 'Started: Ctrl-C to kill'
    try:
        while True:
            pipe, _ = sock.accept()
            clients.append(pipe)
    except (KeyboardInterrupt, EOFError):
        print 'Done'
    finally:
        disable_current_controller()
        sock.close()
        for pipe in clients:
            pipe.close()
        os.remove(sock_path)
#
#     with server_socket:
#         try:
#             print 'Started: Ctrl-C to kill'
#             while True:
#                 line = raw_input().rstrip('\n').lower()
#                 if line == 'sculpt':
#                     set_current_controller([SculptListener])
#                 elif line == 'none':
#                     disable_current_controller()
#         except (KeyboardInterrupt, EOFError):
#             print 'Done'
#         finally:
#             disable_current_controller()
