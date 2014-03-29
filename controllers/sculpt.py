import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, '..', 'lib'))
import Leap
from Leap import ScreenTapGesture

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
        print 'Position changed:', position # TODO finir

    def screen_tap(self, gesture):
        print 'Screen tapped' # TODO finir
