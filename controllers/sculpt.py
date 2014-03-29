import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, '..', 'lib'))
import Leap
from Leap import ScreenTapGesture

class GrabListener(Leap.Listener):
    """
    The grab gesture is detected when nbFingersMax disappear at once
    """
    def __init__(self, nbFingersMax = 5):
        Leap.Listener.__init__(self)

        self._isGrabbing = False
        self._readyToGrab = False
        self._position = Leap.Vector()

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
            self.moveObject(self._position - hand.palm_position)

        # Grab
        if not self._isGrabbing and self._isGrab(nbFingers):
            self._isGrabbing = True
            self._position = hand.palm_position

        # Ungrab
        if self._isGrabbing and nbFingers == self.nbFingersMax:
            self._isGrabbing = False
            self.finishObjectMovement()

    def _isGrab(self, nbFingers):
        if self.nbFingersMax == nbFingers:
            self._readyToGrab = True

        return self._readyToGrab and nbFingers == 0

    def moveObject(self, translateVector):
        print('Moving object of {}'.format(translateVector))
        # TODO move object

    def finishObjectMovement(self):
        print('Object moved.')
        # TODO finish movement

class SculptListener(Leap.Listener):
    def on_init(self, controller):
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);

    def on_exit(self, controller):
        pass#controller.disable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);

    def on_frame(self, controller):
        frame = controller.frame()
        if frame.hands.is_empty:
            return

        # handle only one hand
        hand = frame.hands[0]

        # handle cursor positioning
        fingers = hand.fingers
        if not fingers.is_empty:
            avg_pos = Leap.Vector()
            for finger in fingers:
                avg_pos += finger.tip_position
            avg_pos /= len(fingers)
            self.set_cursor_position(avg_pos)

        # handle command gestures
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
                self.screen_tap(gesture)

    def set_cursor_position(self, position):
        pass#print 'Position changed:', position # TODO finir

    def screen_tap(self, gesture):
        print('Screen tapped') # TODO finir
