import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap

import socket
from controllers import (set_current_controller, disable_current_controller,
        SculptListener, GrabListener, ScaleListener, CalmGestureListener)
from controllers.pottery import PotteryListener
from communication import clients
from communication import send_command

# Risquy imports
import platform
if not platform.mac_ver():
    from voice import VoiceRecognition

if __name__ == '__main__':
    socket_path = 'server.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(socket_path)
    sock.listen(0)

    if not platform.mac_ver():
        vr = VoiceRecognition()
        vr.start()

    set_current_controller([
        GrabListener,
        ScaleListener,
        PotteryListener,
        CalmGestureListener
    ])

    # default mode
    set_current_controller('sculpt')

    print 'Started: Ctrl-C to kill'
    try:
        while True:
            pipe, _ = sock.accept()
            clients.append(pipe)
            # send_command('mode_sculpt', {})
            # TODO: instantiate all the controllers
            # They will use communication.send_command to send (automatically filtered) data

    except (KeyboardInterrupt, EOFError):
        print 'Done'
    finally:
        disable_current_controller()
        sock.close()
        for pipe in clients:
            pipe.close()
        os.remove(socket_path)
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
