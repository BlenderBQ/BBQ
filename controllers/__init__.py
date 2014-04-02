from threading import Lock
import Leap

class Controller(object):
    """
    Base controller, override in order to implement gesture handling.
    """
    def __init__(self, gestures_clss=None):
        """
        Build controller, passing in optional gesture *class* list.
        """
        # add all passed gestures
        if gestures_clss is None:
            gestures_clss = []
        gestures = [g_cls() for g_cls in gestures_clss]
        for gesture in gestures:
            gesture.controller = self

        # setup leap listener
        lstn = Leap.Listener()
        lstn.on_init = lambda _: map(lambda g: g.setup(), self.gestures)
        lstn.on_exit = lambda _: map(lambda g: g.cleanup(), self.gestures)
        lstn.on_init = lambda c: self.frame(c.frame())

        # members
        self.lock = Lock()
        self.listener = lstn
        self.gestures = dict(zip(map(lambda cls: cls.__name__, gestures_clss), gestures))
        self.gesture_activated = {}

    def add_gesture(self, gesture_cls):
        """
        Add a handled gesture to the controller, taking in a gesture class.
        """
        with self.lock:
            gesture_name = gesture_cls.__name__
            if gesture_name in self.gestures:
                raise ValueError('Gesture already added')
            self.gestures[gesture_name] = gesture_cls()

    def remove_gesture(self, gesture_cls):
        """
        Remove a handled gesture to the controller, taking in a gesture class.
        """
        gesture_name = gesture_cls.__name__
        with self.lock:
            if gesture_name not in self.gestures:
                raise ValueError('Gesture not added')
            del self.gestures[gesture_name]

    def frame(self, frame):
        """
        Called on a frame, taking care of gestures and calling update().
        """
        with self.lock:
            # gesture detection
            for gesture_name, gesture in self.gestures.iteritems():
                self.gesture_activated[gesture_name] = gesture.detect(frame)

            # actual update
            self.current_frame = frame
            self.update(frame)

    def gesture_is_active(self, gesture_name):
        """
        Return if the passed gesture is currently active.
        """
        return gesture_name in self.gesture_activated

    def enter(self):
        """
        Implement initializing operations here.
        """
        pass

    def leave(self):
        """
        Implement exiting operations here.
        """
        pass

    def update(self, frame):
        """
        Implement updating logic here.
        """
        raise NotImplementedError

class Gesture(object):
    """
    Base gesture class, override any of the callback methods to setup detection
    of this gesture.
    """
    def init(self):
        """
        Do any setup operations here.
        """
        pass

    def cleanup(self):
        """
        Do any cleanup operations here.
        """
        pass

    def detect(self, frame):
        """
        Detect the gesture, returning a truthy/falsy indicating wether the
        gesture should be detected or not.
        """
        return False

_leap_controller = Leap.Controller()
_current_controller = None

def disable_current_controller():
    global _current_controller
    if _current_controller is None:
        return
    _current_controller.leave()
    _leap_controller.remove_listener(_current_controller.listener)
    _current_controller = None

defined_controllers = {}

def set_current_controller(ctrl):
    if isinstance(ctrl, (str, unicode)):
        if ctrl not in defined_controllers:
            raise ValueError('Undefined controller %s' % ctrl)
        ctrl = defined_controllers[ctrl]
    disable_current_controller()

    # add listener to leap controller
    global _current_controller
    _current_controller = ctrl()
    _current_controller.enter()
    _leap_controller.add_listener(_current_controller.listener)

class ControllerBinding(object):
    def __init__(self, update, gestures=None, ctrl_cls=Controller):
        if gestures is None:
            gestures = []

        # controller class binding
        self.ctrl_cls = ctrl_cls
        self.ctrl_cls.enter = lambda ctrl: self.do_enter(ctrl)
        self.ctrl_cls.leave = lambda ctrl: self.do_leave(ctrl)
        self.ctrl_cls.update = lambda ctrl: self.update(ctrl)
        self.gestures = gestures

        # bound callbacks
        self.update = update
        self._enter = None
        self._leave = None

    def build_controller(self):
        return self.ctrl_cls(self.gestures)

    def do_enter(self, ctrl):
        if self._enter is not None:
            self._enter(ctrl)

    def do_leave(self, ctrl):
        if self._leave is not None:
            self._leave(ctrl)

    def on_enter(self, f):
        self._enter = f

    def on_leave(self, f):
        self._leave = f

def make_controller(*gestures):
    """
    Make a basic controller, retuning a decoratable object (similar to property)
    """
    def decorator(f):
        binding = ControllerBinding(f, gestures)
        defined_controllers[f.__name__] = lambda: binding.build_controller()
        return binding
    return decorator
