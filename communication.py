import os
import json
import socket
import threading

_lock = threading.Lock()

clients = []

def send_command(name, data):
    """
    Send a command: name is the target function's name, data is the target
    function's kwargs.
    """
    with _lock:
        data['__cmd__'] = name
        jdata = json.dumps(data) + '\n'
        for c in clients:
            try:
                c.send(jdata)
            except IOError as e:
                logging.exception(e)
                clients.remove(c)

def send_long_command(self, name, data, filters=None):
    if filters is None:
        filters = {}
    # TODO
    return send_command(name, data)
