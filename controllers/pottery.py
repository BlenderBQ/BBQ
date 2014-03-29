import os, sys
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, '..', 'lib'))
import Leap
from Leap import SwipeGesture

class PotteryListener(Leap.Listener):
    def on_init(self, controller):
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_exit(self, controller):
        pass#controller.disable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);

    def on_frame(self, controller):
        frame = controller.frame()
        print 'frame', frame
        #if frame.hands.is_empty:
            #return

        # handle only one hand
        hand = frame.hands[0]

        # handle command gestures
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                self.swipe(gesture)

    def swipe(self, gesture):
        swipe_gesture = SwipeGesture(gesture)
        print swipe_gesture.speed
