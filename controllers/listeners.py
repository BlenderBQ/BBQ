import math
import Leap
from communication import send_command, send_long_command
from leaputils import rescale_position
from filters import *
import time

# first real hack
is_grabbing = False
is_scaling = False

# state
NOTHING = 0x00
GRABBING = 0x01

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when the fingers all converge to the center of the hand.
    FIXME this class is *extremely* bugged (notably the can_grab method).
    """
    def __init__(self):
        Leap.Listener.__init__(self)

        self.nb_hands = MixedFilter([
            NoiseFilter(10, 0.3, 10),
            LowpassFilter(0.5)
            ])

        self.nb_fingers = MixedFilter([
            NoiseFilter(100, 0.3, 10),
            LowpassFilter(0.9)
            ])

        self.x_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.y_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.z_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])

        self.current_state = NOTHING
        self.hand_origin = None

    def is_grabbing(self):
        return self.current_state & GRABBING == GRABBING

    def on_init(self, controller):
        self.current_state = NOTHING
        self.nb_hands.empty()
        self.nb_fingers.empty()
        self.x_hand.empty()
        self.y_hand.empty()
        self.z_hand.empty()

    def on_frame(self, controller):
        frame = controller.frame()

        self.nb_hands.add_value(len(frame.hands))
        if not self.nb_hands.around(1, 0.1):
            # print 'HAND'
            self.end_grab()
            return

        hand = frame.hands[0]
        fingers = hand.fingers

        self.nb_fingers.add_value(len(fingers))
        # print 'Nb finger :', self.nb_fingers.value, self.nb_fingers.derivative
        if self.is_grabbing():
            pos = hand.stabilized_palm_position
            self.x_hand.add_value(pos.x)
            self.y_hand.add_value(pos.y)
            self.z_hand.add_value(pos.z)

            origin = self.hand_origin
            dx = self.x_hand.value - origin.x
            dy = self.y_hand.value - origin.y
            dz = self.z_hand.value - origin.z

            send_command('object_move', {'tx': dz, 'ty': dx, 'tz': dy})

        if self.is_grabbing():
            if self.nb_fingers.derivative > 0.015 \
                    or self.nb_fingers.around(5, 1.5):
                print 'UNGRAB', self.nb_fingers.value, time.time()
                self.end_grab()

        if not self.is_grabbing():
            if self.nb_fingers.around(3.0, 0.2) \
                    and self.nb_fingers.derivative < -0.015:
                print 'GRAB', self.nb_fingers.derivative
                self.begin_grab(hand)

    def begin_grab(self, hand):
        self.hand_origin = hand.stabilized_palm_position
        self.current_state = GRABBING

        # Move origin
        send_command('object_move_origin', {'x': self.hand_origin.z, 'y': self.hand_origin.x, 'z': self.hand_origin.y})

        # Rotate origin
        # x, y, z = hand.palm_normal.x, hand.palm_normal.y, hand.palm_normal.z
        # yaw = math.atan2(x, y)
        # r = math.sqrt(x * x + y * y)
        # pitch = math.atan2(z, r)
        # roll = 0
        # send_command('object_rotate_origin', {'yaw': yaw, 'pitch': pitch, 'roll': roll})

    def end_grab(self):
        self.x_hand.empty()
        self.y_hand.empty()
        self.z_hand.empty()
        self.nb_fingers.empty()
        self.hand_origin = None
        if self.is_grabbing():
            send_command('object_move_end', {})
            self.current_state = NOTHING

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
        self.last_mag = 0

    def on_frame(self, controller):
        frame = controller.frame()
        global is_scaling

        # Need at least two hands for this gesture
        # and can't scale when grabbing
        if len(frame.hands) < 2 or is_grabbing:
            is_scaling = False
            return

        # Get first two hands
        hand1, hand2 = frame.hands[0], frame.hands[2]

        # No (or few) fingers must be visible
        if len(hand1.fingers) + len(hand2.fingers) > 1:
            is_scaling = False
            return

        # Distance between the two hands
        dis = hand1.stabilized_palm_position - hand2.stabilized_palm_position
        mag = dis.magnitude

        # Scale when scaling (duh)
        if is_scaling:
            send_long_command('object_scale', { 'sx': mag, 'sy': mag, 'sz': mag },
                filters={'sx': 'coordinate', 'sy': 'coordinate', 'sz': 'coordinate'})

        # Start scaling only if hands move apart enough
        if abs(mag - self.last_mag) >= self.threshold:
            is_scaling = True
            send_command('object_scale_origin')
        self.last_mag = mag

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
