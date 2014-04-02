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

        self.loc_x_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.loc_y_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.loc_z_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])

        self.rot_x_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.rot_y_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])
        self.rot_z_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)
            ])

        self.current_state = NOTHING

        self.loc_x_origin = 0
        self.loc_y_origin = 0
        self.loc_z_origin = 0
        self.rot_x_origin = 0
        self.rot_y_origin = 0
        self.rot_z_origin = 0

    def is_grabbing(self):
        return self.current_state & GRABBING == GRABBING

    def on_init(self, controller):
        self.current_state = NOTHING
        self.nb_hands.empty()
        self.nb_fingers.empty()
        self.loc_x_hand.empty()
        self.loc_y_hand.empty()
        self.loc_z_hand.empty()
        self.rot_x_hand.empty()
        self.rot_y_hand.empty()
        self.rot_z_hand.empty()

    def on_frame(self, controller):
        frame = controller.frame()

        self.nb_hands.add_value(len(frame.hands))
        if not self.nb_hands.around(1, 0.1):
            # print 'HAND'
            self.end_grab()
            return

        hand = frame.hands[0]
        fingers = hand.fingers

        pos = hand.stabilized_palm_position
        self.loc_x_hand.add_value(pos.x)
        self.loc_y_hand.add_value(pos.y)
        self.loc_z_hand.add_value(pos.z)

        rot_x = hand.direction.pitch
        rot_y = hand.direction.yaw
        rot_z = hand.direction.roll
        self.rot_x_hand.add_value(rot_x)
        self.rot_y_hand.add_value(rot_y)
        self.rot_z_hand.add_value(rot_z)

        # print 'INFO', self.nb_fingers.value, self.nb_fingers.derivative, self.x_hand.value, self.y_hand.value, self.z_hand.value

        self.nb_fingers.add_value(len(fingers))
        # print 'Nb finger :', self.nb_fingers.value, self.nb_fingers.derivative
        if self.is_grabbing():
            dx = self.loc_x_hand.value - self.loc_x_origin
            dy = self.loc_y_hand.value - self.loc_y_origin
            dz = self.loc_z_hand.value - self.loc_z_origin
            send_command('object_move', {
                'loc_x': dx,
                'loc_y': dy,
                'loc_z': dz})

            rx = self.rot_x_hand.value - self.rot_x_origin
            ry = self.rot_y_hand.value - self.rot_y_origin
            rz = self.rot_z_hand.value - self.rot_z_origin
            # send_command('object_rotate', {
            #     'rot_x': rx,
            #     'rot_y': ry,
            #     'rot_z': rz})

        if self.is_grabbing():
            print 'FRAME'
            if self.nb_fingers.derivative > 0.015 \
                    or self.nb_fingers.around(5, 1.5):
                print 'UNGRAB', self.nb_fingers.value, self.nb_fingers.derivative
                self.end_grab()

        if not self.is_grabbing():
            if self.nb_fingers.around(3.0, 0.5) \
                    and self.nb_fingers.derivative < -0.012:
                print 'GRAB', self.nb_fingers.derivative
                self.begin_grab(hand)

    def begin_grab(self, hand):
        self.current_state = GRABBING

        # Move origin
        pos = hand.stabilized_palm_position
        self.loc_x_origin = pos.x
        self.loc_y_origin = pos.y
        self.loc_z_origin = pos.z
        send_command('object_move_origin', {
            'loc_x': self.loc_x_origin,
            'loc_y': self.loc_y_origin,
            'loc_z': self.loc_z_origin})

        # Rotate origin
        self.rot_x_origin = hand.direction.pitch
        self.rot_y_origin = hand.direction.yaw
        self.rot_z_origin = hand.direction.roll
        # send_command('object_rotate_origin', {
        #     'rot_x': self.rot_x_origin,
        #     'rot_y': self.rot_y_origin,
        #     'rot_z': self.rot_z_origin})

    def end_grab(self):
        self.loc_x_hand.empty()
        self.loc_y_hand.empty()
        self.loc_z_hand.empty()
        self.rot_x_hand.empty()
        self.rot_y_hand.empty()
        self.rot_z_hand.empty()
        self.nb_fingers.empty()
        if self.is_grabbing():
            send_command('object_move_end', {})
            # send_command('object_rotate_end', {})
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
