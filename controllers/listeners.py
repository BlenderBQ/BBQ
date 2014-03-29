from communication import send_command, send_long_command
import Leap
import time

class GrabMode:
    """
    When someone grabs, two actions are possible: MOVE or ROTATE. SEARCHING is used to find out which movement the user wants to do.
    """
    SEARCHING = 0
    MOVE = 1
    ROTATE = 2

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when nbFingersMax disappear at once.
    Must have only one hand.
    """
    def __init__(self, nbFingersMax=5, threshold=15, nbFramesAnalyzed=10):
        Leap.Listener.__init__(self)

        self._readyToGrab = False
        self._handOrigin = Leap.Vector()
        self._historicPositions = []
        self._grabModes = [GrabMode.SEARCHING]

        self.nbFingersMax = nbFingersMax
        self.nbFramesAnalyzed = nbFramesAnalyzed
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        if len(frame.hands) is not 1:
            return

        # Getting only the first hand
        hand = frame.hands[0]
        nbFingers = len(hand.fingers)

        # Grab: analysis of movement to find mode
        if GrabMode.SEARCHING in self._grabModes and self._isGrab(nbFingers):
            self._historicPositions.append(hand.palm_position - self._handOrigin)

            # When we have nbFramesAnalyzed positions in the list
            if len(self._historicPositions) == self.nbFramesAnalyzed:
                sumDistances = 0

                for i in xrange(len(self._historicPositions)):
                    sumDistances += self._historicPositions[i].distance_to(self._historicPositions[i - 1])

                # We want to MOVE!!!
                if sumDistances > self.threshold:
                    self._grabModes.remove(GrabMode.SEARCHING)
                    self._grabModes.append(GrabMode.MOVE)
                    self._handOrigin = hand.palm_position
                    send_command('object_move_origin', {'x': self._handOrigin.z, 'y': self._handOrigin.x, 'z': self._handOrigin.y})

                del self._historicPositions[:]

        # Grabbing
        elif GrabMode.MOVE in self._grabModes:
            self.sendNewPosition(hand.palm_position - self._handOrigin)

        if GrabMode.ROTATE in self._grabModes:
            pass#TODO rotate

        # Ungrab
        if GrabMode.SEARCHING not in self._grabModes and nbFingers == self.nbFingersMax:
            self._grabModes = [GrabMode.SEARCHING]

    def _isGrab(self, nbFingers):
        if self.nbFingersMax == nbFingers:
            self._readyToGrab = True

        return self._readyToGrab and nbFingers == 0

    def sendNewPosition(self, positionFromHand):
        send_long_command('object_move', {'tx': positionFromHand.z, 'ty': positionFromHand.x, 'tz': positionFromHand.y},
                filters={'tx': 'coordinate', 'ty': 'coordinate', 'tz': 'coordinate'})
        time.sleep(0.02)
        print('Moving object to {}'.format(positionFromHand))
        # TODO send move object command

class ScaleListener(Leap.Listener):
    """
    The scale gesture is detected when two hands are initially closed (no fingers visible).
    The amount of scaling sent is proportionnal to the variation of distance between the two hands
    during the gesture.
    Detecting at least a finger cancels the movement.
    """
    def __init__(self, threshold = 5, nbFramesAnalyzed = 10):
        Leap.Listener.__init__(self)

        self._handOrigin = Leap.Vector()
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
            return

        hand1 = frame.hands[0]
        hand2 = frame.hands[1]

        # No (or few) fingers must be visible
        if (len(hand1.fingers) + len(hand2.fingers) > 1):
            self._isScaling = False
            return

        # Distance between the two hands
        displacement = hand1.stabilized_palm_position - hand2.stabilized_palm_position
        mag = displacement.magnitude

        # Should we activate the gesture?
        if not self._isScaling:
            self._history.append(displacement)

            # Start scaling if hands move apart enough
            # (must happen between nbFramesAnalyzed frames)
            variation = 0
            for i in range(1, len(self._history)):
                variation = self._history[i].magnitude - self._history[i-1].magnitude

            if abs(variation) >= self.threshold:
                startScaling(mag)

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

        send_command('object_scale_origin')
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
