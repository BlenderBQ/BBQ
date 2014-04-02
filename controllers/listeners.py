import math
import Leap
from communication import send_command, send_long_command
from leaputils import rescale_position

# first real hack
is_grabbing = False
is_scaling = False

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when the fingers all converge to the center of the hand.
    FIXME this class is *extremely* bugged (notably the can_grab method).
    """
    def __init__(self, min_nb_fingers=3, max_nb_fingers=5, threshold=3,
            history_size=30, rotation_enabled=False):
        Leap.Listener.__init__(self)

        self.min_nb_fingers = min_nb_fingers
        self.max_nb_fingers = max_nb_fingers
        self.threshold = threshold
        self.history_size = history_size
        self.rotation_enabled = rotation_enabled

        self.fingers_history = []
        self.hand_origin = None

    def on_init(self, controller):
        global is_grabbing
        is_grabbing = False

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Getting only one hand
        if len(frame.hands) is not 1:
            if self.fingers_history is not None:
                self.fingers_history = []
            return

        hand = frame.hands[0]
        fingers = hand.fingers

        # Grab: analysis of movement to find mode
        if not is_grabbing and self.can_grab(hand):
            self.begin_grab(hand)

        # Grabbing logic
        if is_grabbing:
            # Move
            if self.hand_origin is not None:
                pfh = hand.stabilized_palm_position - self.hand_origin
                send_long_command('object_move', {'tx': pfh.z, 'ty': pfh.x, 'tz': pfh.y},
                        filters={'tx': 'coordinate', 'ty': 'coordinate', 'tz': 'coordinate'})

            # Rotate
            x, y, z = hand.palm_normal.x, hand.palm_normal.y, hand.palm_normal.z
            yaw = math.atan2(x, y)
            pitch = math.atan2(z, math.sqrt(x ** 2 + y ** 2))
            roll = 0 # osef du roll
            rotation = (yaw, pitch, roll)
            if self.rotation_enabled:
                send_long_command('object_rotate', {'yaw': rotation[0], 'pitch': rotation[1], 'roll': rotation[2]},
                        filters={'yaw': 'coordinate', 'pitch': 'coordinate', 'roll': 'coordinate'})

        # Ungrab
        if is_grabbing and len(fingers) >= self.min_nb_fingers:
            self.end_grab()

    def can_grab(self, hand):
        if self.fingers_history is None:
            return True

        fingers = hand.fingers

        distances = []
        if fingers.is_empty and not self.fingers_history:
            return False

        self.fingers_history.append(len(hand.fingers))

        less_fingers = False
        if len(self.fingers_history) == self.history_size:

            less_fingers = self.fingers_history[-1] == 0
            less_fingers = less_fingers and self.fingers_history[-1] < self.fingers_history[0]

            for i in xrange(1, len(self.fingers_history)):
                if self.fingers_history[i - 1] < self.fingers_history[i]:
                    less_fingers = False

            self.fingers_history = []

            if less_fingers:
                self.fingers_history = None

        return less_fingers

    def begin_grab(self, hand):
        self.hand_origin = hand.stabilized_palm_position

        global is_grabbing
        is_grabbing = True

        # Move origin
        send_command('object_move_origin', {'x': self.hand_origin.z, 'y': self.hand_origin.x, 'z': self.hand_origin.y})

        # Rotate origin
        x, y, z = hand.palm_normal.x, hand.palm_normal.y, hand.palm_normal.z
        yaw = math.atan2(x, y)
        r = math.sqrt(x * x + y * y)
        pitch = math.atan2(z, r)
        roll = 0
        send_command('object_rotate_origin', {'yaw': yaw, 'pitch': pitch, 'roll': roll})

    def end_grab(self):
        send_command('object_move_end', {})
        global is_grabbing
        is_grabbing = False
        self.fingers_history = []
        self.hand_origin = None

class ScaleListener(Leap.Listener):
    """
    The scale gesture is detected when two hands are initially closed (no
    fingers visible). The amount of scaling sent is proportionnal to the
    variation of distance between the two hands during the gesture. Detecting
    at least a finger cancels the movement.
    """
    def __init__(self, threshold=5):
        Leap.Listener.__init__(self)
        self.threshold = threshold

    def on_frame(self, controller):
        frame = controller.frame()

        # Need at least two hands for this gesture
        # and can't scale when grabbing
        if len(frame.hands) < 2 or self.grabbing:
            self.scaling = False
            return

        # Get first two hands
        hand1, hand2 = frame.hands[:2]

        # No (or few) fingers must be visible
        if len(hand1.fingers) + len(hand2.fingers) > 1:
            self.scaling = False
            return

        # Distance between the two hands
        dis = hand1.stabilized_palm_position - hand2.stabilized_palm_position
        mag = dis.magnitude

        # Scale when scaling (duh)
        if self.scaling:
            send_long_command('object_scale', { 'sx': mag, 'sy': mag, 'sz': mag },
                filters={'sx': 'coordinate', 'sy': 'coordinate', 'sz': 'coordinate'})
            return

        # Start scaling only if hands move apart enough
        if abs(mag - self.last_mag) >= self.threshold:
            self.scaling = True
            send_command('object_scale_origin')

    # The following properties are used to hide globals these should disappear
    # in the future, and therefore will be changed in the properties

    @property
    def grabbing(self):
        global is_grabbing
        return is_grabbing

    @property
    def scaling(self):
        global is_scaling
        return is_scaling

    @scaling.setter
    def set_scaling(self, scaling):
        global is_scaling
        is_scaling = scaling

class StopListener(Leap.Listener):
    """
    The "calm down" gesture is activated when a fully opened hand is lowered.
    """
    def __init__(self, threshold = 35, history_size = 10):
        Leap.Listener.__init__(self)

        self.hand_origin = Leap.Vector()
        self.history = []

        self.history_size = history_size
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need exactly one hand for this gesture
        if len(frame.hands) is not 1:
            self.history = []
            return

        hand = frame.hands[0]

        # About five fingers must be visible
        if len(hand.fingers) < 4:
            self.history = []
            return
        altitude = hand.stabilized_palm_position.y
        self.history.append(altitude)

        # Limit history size
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]

        # Hand must not be going up
        elif len(self.history) >= 2:
            if self.history[-2] < self.history[-1]:
                return

        # Activate the gesture if there's enough vertical change
        variation = 0
        for i in xrange(1, len(self.history)):
            variation += self.history[i] - self.history[i-1]
        if -variation >= self.threshold:
            self.stop()

    def stop(self):
        self.history = []
        send_command('stop_rotation')

class PointersListener(Leap.Listener):
    """
    This gesture is intended for sculpt mode.
    Each finger could potentially send "pressure" commands.
    """
    def __init__(self, threshold=1, length_threshold=10, history_size=30):
        Leap.Listener.__init__(self)
        self.threshold = threshold
        self.length_threshold = length_threshold
        self.history_size = history_size

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need at least one hand
        if not frame.hands:
            return
        # And three fingers at most
        nb_fingers = sum(len(hand.fingers) for hand in frame.hands)
        if nb_fingers > 2 or nb_fingers < 1:
            return

        # TODO itertools.chain <3
        for hand in frame.hands:
            for finger in hand.fingers:

                # Each finger must be present for some time before being able to paint
                # and have a minimum length
                if finger.time_visible > self.threshold \
                        and finger.length > self.length_threshold:
                    self.point_finger(finger.stabilized_tip_position,
                                      finger.direction)

    def point_finger(self, tip, direction):
        # TODO send as long command ?
        tip = rescale_position(tip)
        send_command('finger_touch', { 'x': tip.z, 'y': tip.x, 'z': tip.y,
            'vx': direction.z, 'vy': direction.x, 'vz': direction.y })
