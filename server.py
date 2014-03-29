import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap

import socket
from controllers import set_current_controller, disable_current_controller
from controllers import SculptListener
from communication.server import server_socket

if __name__ == '__main__':
    with server_socket:
        try:
            print 'Started: Ctrl-C to kill'
            while True:
                line = raw_input().rstrip('\n').lower()
                if line == 'sculpt':
                    set_current_controller([SculptListener])
                elif line == 'none':
                    disable_current_controller()
        except (KeyboardInterrupt, EOFError):
            print 'Done'
        finally:
            disable_current_controller()
