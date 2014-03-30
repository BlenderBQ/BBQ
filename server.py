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
from voice.commands import interpret_command

# Mac not-imports
# import platform
# if not platform.mac_ver()[0]:
#     from voice import VoiceRecognition

def run_server():
    print 'Started: Ctrl-C to kill'
    try:
        while True:
            pipe, _ = sock.accept()
            clients.append(pipe)
    except KeyboardInterrupt:
        pass

def cleanup_server():
    disable_current_controller()
    sock.close()
    for pipe in clients:
        pipe.close()
    os.remove(socket_path)

if __name__ == '__main__':
    socket_path = 'server.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(socket_path)
    sock.listen(0)

    # debugging
    com.debug = '--debug' in sys.argv # or True

    # if not platform.mac_ver()[0]:
    #     vr = VoiceRecognition()
    #     vr.start()

    set_current_controller([
        GrabListener,
        ScaleListener,
        PotteryListener,
        CalmGestureListener
    ])

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
