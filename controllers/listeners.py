from communication import send_command, send_long_command
import Leap
import time
import math
from leaputils import *

# first real hack
is_grabbing = False

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when the fingers all converge to the center of the hand.
    """
    def __init__(self, min_nb_fingers=3, max_nb_fingers=5, threshold=3, history_size=30):
        Leap.Listener.__init__(self)

        is_grabbing = False
        self.hand_origin = None
        self.fingers_history = []

        self.min_nb_fingers = min_nb_fingers
        self.max_nb_fingers = max_nb_fingers
        self.history_size = history_size
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Getting only one hand
        if len(frame.hands) is not 1:
            if self.fingers_history is not None:
                del self.fingers_history[:]
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
            r = math.sqrt(x * x + y * y)
            pitch = math.atan2(z, r)
            roll = 0
            rotation = (yaw, pitch, roll)
            # FIXME disable/enable ?
            #send_long_command('object_rotate', {'yaw': rotation[0], 'pitch': rotation[1], 'roll': rotation[2]},
                    #filters={'yaw': 'coordinate', 'pitch': 'coordinate', 'roll': 'coordinate'})


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

            for i in range(1, len(self.fingers_history)):
                if self.fingers_history[i - 1] < self.fingers_history[i]:
                    less_fingers = False

            del self.fingers_history[:]

            if less_fingers:
                self.fingers_history = None

        return less_fingers

    def begin_grab(self, hand):
        #print('Grab')
        self.hand_origin = hand.stabilized_palm_position
        #print(hand.stabilized_palm_position)

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
        #print('Ungrab')
        send_command('object_move_end', {})
        global is_grabbing
        is_grabbing = False
        self.fingers_history = []
        self.hand_origin = None

class ScaleListener(Leap.Listener):
    """
    The scale gesture is detected when two hands are initially closed (no fingers visible).
    The amount of scaling sent is proportionnal to the variation of distance between the two hands
    during the gesture.
    Detecting at least a finger cancels the movement.
    """
    def __init__(self, threshold = 5, history_size = 10):
        Leap.Listener.__init__(self)

        self.history = []
        self._isScaling = False
        self._initialFactor = 0

        self.history_size = history_size
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need at least two hands for this gesture
        # and can't scale when grabbing
        if len(frame.hands) < 2 or is_grabbing:
            del self.history[:]
            return

        hand1 = frame.hands[0]
        hand2 = frame.hands[1]

        # No (or few) fingers must be visible
        if len(hand1.fingers) + len(hand2.fingers) > 1:
            self._isScaling = False
            del self.history[:]
            return

        # Distance between the two hands
        displacement = hand1.stabilized_palm_position - hand2.stabilized_palm_position
        mag = displacement.magnitude

        # Should we activate the gesture?
        if not self._isScaling:
            self.history.append(displacement)

            # Limit history length to history_size
            if len(self.history) > self.history_size:
                self.history = self.history[:-len(self.history)]

            # Start scaling if hands move apart enough
            # (must happen between history_size frames)
            variation = 0
            for i in range(1, len(self.history)):
                variation = self.history[i].magnitude - self.history[i-1].magnitude

            if abs(variation) >= self.threshold:
                self.startScaling(mag)

            # Limit history length to history_size
            n = len(self.history)
            if n > self.history_size:
                n -= self.history_size
                self.history = self.history[n:]

        # Send the scaling command
        else:
            # Scale back the magnitude between 0 and 1 (make smaller) or > 1 (make bigger)
            self.sendNewScalingFactor(mag / self._initialFactor)

    def startScaling(self, currentMagnitude):
        self._initialFactor = currentMagnitude
        self._isScaling = True
        # Clear history (it is not needed when movement is activated)
        del self.history[:]

        send_command('object_scale_origin', {})
        #print('Starting to scale object')

    def sendNewScalingFactor(self, factor):
        send_long_command('object_scale', {
            'sx': factor,
            'sy': factor,
            'sz': factor
            },
            filters={'sx': 'coordinate', 'sy': 'coordinate', 'sz': 'coordinate'}
        )
        #print('Scaling object of factor {}'.format(factor))

class CalmGestureListener(Leap.Listener):
    """
    The "calm down" gesture is activated when a fully opened hand is lowered.
    """
    def __init__(self, threshold = 5, history_size = 50):
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
            del self.history[:]
            return

        hand = frame.hands[0]

        # About five fingers must be visible
        if len(hand.fingers) < 4:
            del self.history[:]
            return
        altitude = hand.stabilized_palm_position.y

        self.history.append(altitude)
        # Limit history size
        if len(self.history) > self.history_size:
            self.history[:-self.history_size]
        # Hand must not be going up
        elif len(self.history) >= 2:
            if self.history[-2] < self.history[-1]:
                return

        # Activate the gesture if there's enough vertical change
        variation = 0
        for i in range(1, len(self.history)):
            variation = self.history[i] - self.history[i-1]
        if -variation >= self.threshold:
            self.activateGesture()

    def activateGesture(self):
        del self.history[:]
        send_command('stop_rotation')
        #print('Setting rotation speed to 0')

class FingersListener(Leap.Listener):
    """
    This gesture is intended for sculpt mode.
    Each finger could potentially send "pressure" commands.
    """
    def __init__(self, threshold = 1, lengthThreshold = 10, history_size = 30):
        Leap.Listener.__init__(self)
        self.threshold = threshold
        self.lengthThreshold = lengthThreshold
        self.history_size = history_size

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need at least one hand
        if not frame.hands:
            return
        # And three fingers at most
        nFingers = 0
        for hand in frame.hands:
            nFingers += len(hand.fingers)
        if nFingers > 2 or nFingers < 1:
            return

        for hand in frame.hands:
            for finger in hand.fingers:
                # Each finger must be present for some time before being able to paint
                # and have a minimum length
                if finger.time_visible > self.threshold and finger.length > self.lengthThreshold:
                    self.activateGesture(finger.stabilized_tip_position, finger.direction)

    def activateGesture(self, tip, direction):
        # TODO: rescale coordinates, center them at user-confortable origin
        tip = rescale_position(tip)

        #print 'sculpt_touch', tip, direction
        send_command('sculpt_touch', {
            'x': tip.x, 'y': tip.y, 'z': tip.z,
            'vx': direction.x, 'vy': direction.y, 'vz': direction.z
        })
#        print('Sending sculpt command pointing at ({}, {}, {})'.format(tip.x, tip.y, tip.z))

