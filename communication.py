import json
import socket
import threading
import logging
import time

# debugging
from pprint import pformat
debug = False

# connection sockets for clients
clients = []

# TODO remove this, used for debugging
from pprint import pformat
dont_use_network = False

_lock = threading.Lock()
def send_command(name, data={}):
    """
    Send a command: name is the target function's name, data is the target
    function's kwargs.
    """
    global clients
    with _lock:
        data['__cmd__'] = name
        if debug:
            print 'Sending:', pformat(data)
        jdata = json.dumps(data) + '\n'
        for c in clients:
            try:
                c.send(jdata)
            except socket.timeout as e:
                logging.exception(e)
                continue
            except IOError as e:
                logging.exception(e)
                clients.remove(c)
        time.sleep(0.02)
