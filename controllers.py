import os
import sys

this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, 'lib'))

import Leap
from Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture

class SculptListener(Leap.Listener):
    def on_init(self, controller):
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);

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

_leap_controller = Leap.Controller()
_current_controller = []

def disable_current_controller():
    global _current_controller
    for lstn in _current_controller:
        _leap_controller.remove_listener(lstn)

def set_current_controller(listener_clss):
    """
    Set the current controller (mode), taking a list of listener classes.
    """
    global _current_controller
    disable_current_controller()
    _current_controller = []
    for lstn_cls in listener_clss:
        lstn = lstn_cls()
        _current_controller.append(lstn)
        _leap_controller.add_listener(lstn)

def main():
    set_current_controller([SculptListener])

    # Keep this process running until Enter is pressed
    print "Press Enter to quit..."
    sys.stdin.readline()

    # Remove the sample listener when done
    disable_current_controller()

if __name__ == "__main__":
    main()
