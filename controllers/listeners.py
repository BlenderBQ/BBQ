import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, '..', 'lib'))
from communication import send_command, send_long_command
import Leap

class GrabMode:
    """
    When someone grabs, two actions are possible: MOVE or ROTATE. SEARCHING is used to find out which movement the user wants to do.
    """
    SEARCHING = 0
    MOVE = 1
    ROTATE = 2

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when nbFingersMax disappear at once
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

        if frame.hands.is_empty:
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
                    send_command('object_move_origin', {'x': self._handOrigin.x, 'y': self._handOrigin.y, 'z': self._handOrigin.z})

                    for j in range(len(self._historicPositions) - 1):
                        self.sendNewPosition(self._historicPositions[j] - self._handOrigin)

                del self._historicPositions[:]

        # Grabbing
        if GrabMode.MOVE in self._grabModes:
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
        send_long_command('object_move_origin', {'tx': positionFromHand.x, 'ty': positionFromHand.y, 'tz': positionFromHand.z}, filters={'tx': 'float', 'ty': 'float', 'tz': 'float'})
        print('Moving object to {}'.format(positionFromHand))
        # TODO send move object command
