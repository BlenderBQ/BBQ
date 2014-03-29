import Leap

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when nbFingersMax disappear at once
    """
    def __init__(self, nbFingersMax = 5):
        Leap.Listener.__init__(self)

        self._isGrabbing = False
        self._readyToGrab = False
        self._handOrigin = Leap.Vector()

        self.nbFingersMax = nbFingersMax

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        if frame.hands.is_empty:
            return

        # Getting only the first hand
        hand = frame.hands[0]
        nbFingers = len(hand.fingers)

        if self._isGrabbing:
            self.sendNewPosition(hand.palm_position - self._handOrigin)

        # Grab
        if not self._isGrabbing and self._isGrab(nbFingers):
            self._isGrabbing = True
            self._handOrigin = hand.palm_position
            # TODO send coordinates origin

        # Ungrab
        if self._isGrabbing and nbFingers == self.nbFingersMax:
            self._isGrabbing = False
            self.finishObjectMovement()

    def _isGrab(self, nbFingers):
        if self.nbFingersMax == nbFingers:
            self._readyToGrab = True

        return self._readyToGrab and nbFingers == 0

    def sendNewPosition(self, positionFromHand):
        print('Moving object to {}'.format(positionFromHand))
        # TODO send move object command

    def finishObjectMovement(self):
        print('Object moved.')
