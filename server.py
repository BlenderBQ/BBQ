import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap

import socket
import threading

from controllers import (set_current_controller, disable_current_controller,
        SculptListener, GrabListener, ScaleListener, CalmGestureListener,
        PotteryListener)
from communication import clients, send_command
import communication as com
from commands import interpret_command
from config import server_address

# Mac not-imports
import platform
if not platform.mac_ver()[0]:
    from voice import VoiceRecognition

def run_server():
    print 'Started: Ctrl-C to kill'
    try:
        while True:
            pipe, _ = sock.accept()
            pipe.settimeout(0.1)
            clients.append(pipe)
    except KeyboardInterrupt:
        pass

def cleanup_server():
    disable_current_controller()
    sock.close()
    for pipe in clients:
        pipe.close()
    if isinstance(server_address, (str, unicode)):
        os.remove(server_address)

if __name__ == '__main__':
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen(0)

    # debugging
    com.debug = '--debug' in sys.argv

    if not platform.mac_ver()[0]:
        vr = VoiceRecognition()
        vr.start()

    # default mode
    set_current_controller('object')

    if '--interactive' in sys.argv:
        t = threading.Thread(target=run_server)
        t.daemon = True
        try:
            t.start()
            try:
                cmd = ''
                while cmd is not 'exit':
                    cmd = raw_input('Command ?').strip()
                    if not cmd:
                        pass
                    interpret_command(cmd)
            except EOFError:
                pass
        except Exception as e:
            print 'exception:', str(e)
            cleanup_server()
    else:
        run_server()
        cleanup_server()
