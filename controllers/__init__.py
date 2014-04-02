import Leap
from listeners import (GrabListener, ScaleListener, StopListener, PointersListener)
from pottery import SlideRotateListener
from paint import ColorListener

# global leap controller
leap_controller = Leap.Controller()

_current_controller = []

def disable_current_controller():
    for lstn in _current_controller:
        leap_controller.remove_listener(lstn)

def set_current_controller(listener_clss):
    """
    Set the current controller (mode), taking a list of listener classes, or
    the controller's id.
    """
    if isinstance(listener_clss, (str, unicode)):
        assert listener_clss in basic_controllers
        listener_clss = basic_controllers[listener_clss]
    global _current_controller
    disable_current_controller()
    _current_controller = []
    for lstn_cls in listener_clss:
        lstn = lstn_cls()
        _current_controller.append(lstn)
        leap_controller.add_listener(lstn)

basic_controllers = {
        'object': [ScaleListener, GrabListener],
        'sculpt': [PointersListener],
        'pottery': [SlideRotateListener, StopListener, PointersListener],
        'paint': [PointersListener, ColorListener],
        }
