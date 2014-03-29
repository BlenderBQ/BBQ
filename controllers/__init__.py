import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))
import Leap
from sculpt import SculptListener
from pottery import PotteryListener
from listeners import GrabListener

# global leap controller
leap_controller = Leap.Controller()

_current_controller = []

def disable_current_controller():
    global _current_controller
    for lstn in _current_controller:
        leap_controller.remove_listener(lstn)

def set_current_controller(listener_clss):
    """
    Set the current controller (mode), taking a list of listener classes.
    """
    global _current_controller
    disable_current_controller()
    _current_controller = []
    for lstn_cls in listener_clss:
        lstn = lstn_cls()
        _current_controller.append(lstn)
        leap_controller.add_listener(lstn)
