import os
import json
import socket
import threading
import logging

from filters import Filter, CompositeFilter

# connection sockets for clients
clients = []

# TODO remove this, used for debugging
from pprint import pformat
dont_use_network = False

_lock = threading.Lock()
def send_command(name, data):
    """
    Send a command: name is the target function's name, data is the target
    function's kwargs.
    """
    global clients
    with _lock:
        data['__cmd__'] = name
        if dont_use_network:
            print 'Sending:', pformat(data)
            return
        jdata = json.dumps(data) + '\n'
        for c in clients:
            try:
                c.send(jdata)
            except IOError as e:
                logging.exception(e)
                clients.remove(c)

_filters = {}
_filter_mapping = {
        'angle': Filter,#lambda: Filter(threshold=0.005),
        'coordinate': Filter,
        'position': lambda: CompositeFilter(n=3)
        }

def send_long_command(name, data, filters=None):
    """
    Send a command which can be sent many times per frame, in which case
    filters can be specified for certain arguments.
    The "filters" dictionary maps arguments to filter functions.
    """
    if filters is None:
        filters = {}
    changed = False
    for arg, filter_key in filters.iteritems():
        assert arg in data, "Comment t'es trop nul ! (t'as mis un filtre sur un truc qui existe pas)"
        _filters.setdefault(name, {})
        if filter_key not in _filters[name]:
            assert filter_key in _filter_mapping, "Comment t'es trop nul ! (t'as mis un filtre qui existe pas)"
            _filters[name][arg] = _filter_mapping[filter_key]()
        new_value, interesting = _filters[name][arg].apply(data[arg])
        if not interesting:
            continue
        data[arg] = new_value
        changed = True
    if changed:
        return send_command(name, data)
