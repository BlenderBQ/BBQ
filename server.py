"""
Usage:
    python2.7 server.py [options]

Options:
    -h, --help      show this screen
    --debug         run in debug mode (display network commands)
    --interactive   run in interactive mode, allowing voice commands to be entered via stdin
    --no-vr         run without voice recognition (automatic if not available)
"""

import os, sys
import socket
import threading
import logging

# leap python binding
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap

from controllers import set_current_controller, disable_current_controller
import communication as com
from commands import interpret_command

# Mac not-imports
try:
    from voice import VoiceRecognition
    vr_available = True
except ImportError:
    vr_available = False

def run_server():
    print 'Server started: Ctrl-C to kill'
    try:
        while True:
            pipe, _ = sock.accept()
            pipe.settimeout(0.05)
            com.clients.append(pipe)
    except KeyboardInterrupt:
        print 'interrupted'

def cleanup_server():
    disable_current_controller()
    sock.close()
    for pipe in com.clients:
        pipe.close()

if __name__ == '__main__':
    if '-h' in sys.argv or '--help' in sys.argv:
        print __doc__
        sys.exit(0)

    # debugging
    if '--debug' in sys.argv:
        com.debug = True
        # TODO set log level to logging.DEBUG

    # setup server
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', 1337))
    sock.listen(0)

    if vr_available and '--no-vr' not in sys.argv:
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
                exit_cmd = 'exit'
                print 'Kill server and exit with "%s"' % exit_cmd
                while True:
                    cmd = raw_input('(speak) ').strip().lower()
                    if not cmd:
                        pass
                    elif cmd == exit_cmd:
                        break
                    else:
                        interpret_command(cmd)
            except EOFError:
                pass
        except Exception as e:
            logging.exception(e)
        finally:
            cleanup_server()
    else:
        run_server()
        cleanup_server()
