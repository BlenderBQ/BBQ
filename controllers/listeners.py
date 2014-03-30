from communication import send_command, send_long_command
import Leap
import time
import math
from leaputils import *

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when the fingers all converge to the center of the hand.
    """
    def __init__(self, nbFingersMax=5, threshold=0, nbFramesAnalyzed=0):
        Leap.Listener.__init__(self)

        self._isGrabbing = False
        self._handOrigin = None
        self._posHistory = []
        self._fingersHistory = []

        self.nbFingersMax = nbFingersMax
        self.nbFramesAnalyzed = nbFramesAnalyzed
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        if len(frame.hands) is not 1:
            del self._fingersHistory[:]
            del self._posHistory[:]
            return

        # Getting only the first hand
        hand = frame.hands[0]
        fingers = hand.fingers

        # Grab: analysis of movement to find mode
        if not self._isGrabbing and self._isGrab(hand):
            print('Grab.')

            if self._handOrigin is None:
                self._handOrigin = hand.stabilized_palm_position
            else:
                self._posHistory.append(hand.stabilized_palm_position - self._handOrigin)

            # When we have nbFramesAnalyzed positions in the list
            if True or len(self._posHistory) >= self.nbFramesAnalyzed:
                sumDistances = 0

                for i in xrange(len(self._posHistory)):
                    sumDistances += self._posHistory[i].distance_to(self._posHistory[i - 1])

                # We want to MOVE!!!
                if True or sumDistances > self.threshold:
                    self._isGrabbing = True
                    send_command('object_move_origin', {'x': self._handOrigin.z, 'y': self._handOrigin.x, 'z': self._handOrigin.y})
                    x, y, z = hand.palm_normal
                    yaw = math.atan2(x, y)
                    r = math.sqrt(x * x + y * y)
                    pitch = math.atan2(z, r)
                    roll = 0
                    # send_command('object_rotate_origin', {'yaw': yaw, 'pitch': pitch, 'roll': roll})

                del self._posHistory[:]

        # Grabbing
        if self._isGrabbing:
            self.sendNewPosition(hand.stabilized_palm_position - self._handOrigin)
            pass #TODO rotate

            x, y, z = hand.palm_normal.x, hand.palm_normal.y, hand.palm_normal.z
            yaw = math.atan2(x, y)
            r = math.sqrt(x * x + y * y)
            pitch = math.atan2(z, r)
            roll = 0
            # self.sendNewRotation((yaw, pitch, roll))

        # Ungrab
        if self._isGrabbing and len(fingers) == self.nbFingersMax:
            print('Ungrab')
            self._isGrabbing = False

    def _isGrab(self, hand, nbFramesAnalyzed=45):
        fingers = hand.fingers

        distances = []
        if fingers.is_empty and not self._fingersHistory:
            return False

        self._fingersHistory.append(len(hand.fingers))

        lessFingers = False
        if len(self._fingersHistory) == nbFramesAnalyzed:

            lessFingers = self._fingersHistory[-1] == 0
            lessFingers = lessFingers and self._fingersHistory[-1] < self._fingersHistory[0]

            for i in range(1, len(self._fingersHistory)):
                if self._fingersHistory[i - 1] < self._fingersHistory[i]:
                    lessFingers = False

            del self._fingersHistory[:]

        return lessFingers

    def sendNewPosition(self, positionFromHand):
        print 'sendNewPosition', positionFromHand
        send_long_command('object_move', {'tx': positionFromHand.z, 'ty': positionFromHand.x, 'tz': positionFromHand.y},
                filters={'tx': 'coordinate', 'ty': 'coordinate', 'tz': 'coordinate'})
        time.sleep(0.02)
        # print 'Moving object to ({positionFromHand.x}, {positionFromHand.y}, {positionFromHand.z})'.format()

    def sendNewRotation(self, rotation):
        print 'sendNewRotation', rotation
        send_long_command('object_rotation', {'yaw': rotation[0], 'pitch': rotation[1], 'roll': rotation[2]},
                filters={'yaw': 'coordinate', 'pitch': 'coordinate', 'roll': 'coordinate'})
        time.sleep(0.02)
        # print 'Moving object to ({positionFromHand.x}, {positionFromHand.y}, {positionFromHand.z})'.format()

class ScaleListener(Leap.Listener):
    """
    The scale gesture is detected when two hands are initially closed (no fingers visible).
    The amount of scaling sent is proportionnal to the variation of distance between the two hands
    during the gesture.
    Detecting at least a finger cancels the movement.
    """
    def __init__(self, threshold = 5, nbFramesAnalyzed = 10):
        Leap.Listener.__init__(self)

        self._history = []
        self._isScaling = False
        self._initialFactor = 0

        self.nbFramesAnalyzed = nbFramesAnalyzed
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need at least two hands for this gesture
        if len(frame.hands) < 2:
            del self._history[:]
            return

        hand1 = frame.hands[0]
        hand2 = frame.hands[1]

        # No (or few) fingers must be visible
        if (len(hand1.fingers) + len(hand2.fingers) > 1):
            self._isScaling = False
            del self._history[:]
            return

        # Distance between the two hands
        displacement = hand1.stabilized_palm_position - hand2.stabilized_palm_position
        mag = displacement.magnitude

        # Should we activate the gesture?
        if not self._isScaling:
            self._history.append(displacement)

            # Limit history length to nbFramesAnalyzed
            if len(self._history) > self.nbFramesAnalyzed:
                self._history = self._history[:-len(self._history)]

            # Start scaling if hands move apart enough
            # (must happen between nbFramesAnalyzed frames)
            variation = 0
            for i in range(1, len(self._history)):
                variation = self._history[i].magnitude - self._history[i-1].magnitude

            if abs(variation) >= self.threshold:
                self.startScaling(mag)

            # Limit history length to nbFramesAnalyzed
            n = len(self._history)
            if n > self.nbFramesAnalyzed:
                n -= self.nbFramesAnalyzed
                self._history = self._history[n:]

        # Send the scaling command
        else:
            # Scale back the magnitude between 0 and 1 (make smaller) or > 1 (make bigger)
            self.sendNewScalingFactor(mag / self._initialFactor)

    def startScaling(self, currentMagnitude):
        self._initialFactor = currentMagnitude
        self._isScaling = True
        # Clear history (it is not needed when movement is activated)
        del self._history[:]

        send_command('object_scale_origin', {})
        print('Starting to scale object')

    def sendNewScalingFactor(self, factor):
        send_long_command('object_scale', {
            'sx': factor,
            'sy': factor,
            'sz': factor
            },
            filters={'sx': 'coordinate', 'sy': 'coordinate', 'sz': 'coordinate'}
        )
        time.sleep(0.02)
        print('Scaling object of factor {}'.format(factor))

class CalmGestureListener(Leap.Listener):
    """
    The "calm down" gesture is activated when a fully opened hand is lowered.
    """
    def __init__(self, threshold = 7, nbFramesAnalyzed = 50):
        Leap.Listener.__init__(self)

        self._handOrigin = Leap.Vector()
        self._history = []

        self.nbFramesAnalyzed = nbFramesAnalyzed
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need exactly one hand for this gesture
        if len(frame.hands) is not 1:
            del self._history[:]
            return

        hand = frame.hands[0]

        # About five fingers must be visible
        if len(hand.fingers) < 4:
            del self._history[:]
            return
        altitude = hand.stabilized_palm_position.y

        self._history.append(altitude)
        # Limit history size
        if len(self._history) > self.nbFramesAnalyzed:
            self._history[:-self.nbFramesAnalyzed]
        # Hand must not be going up
        elif len(self._history) >= 2:
            if self._history[-2] < self._history[-1]:
                return

        # Activate the gesture if there's enough vertical change
        variation = 0
        for i in range(1, len(self._history)):
            variation = self._history[i] - self._history[i-1]
        if -variation >= self.threshold:
            self.activateGesture()

    def activateGesture(self):
        del self._history[:]
        send_command('set_continuous_rotation', { 'speed': 0 })
        print('Setting rotation speed to 0')

class FingersListener(Leap.Listener):
    """
    This gesture is intended for sculpt mode.
    Each finger could potentially send "pressure" commands.
    """
    def __init__(self, threshold = 1, lengthThreshold = 25, nbFramesAnalyzed = 30):
        Leap.Listener.__init__(self)
        self.threshold = threshold
        self.lengthThreshold = lengthThreshold
        self.nbFramesAnalyzed = nbFramesAnalyzed

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

        send_command('sculp_touch', {
            'x': tip.x, 'y': tip.y, 'z': tip.z,
            'vx': direction.x, 'vy': direction.y, 'vz': direction.z
        })
        print('Sending sculpt command pointing at ({}, {}, {})'.format(tip.x, tip.y, tip.z))

