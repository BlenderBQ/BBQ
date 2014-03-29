import os, sys
import time
this_dir = os.path.dirname(os.path.realpath(__name__))
sys.path.insert(0, os.path.join(this_dir, '..', 'lib'))
import Leap
from Leap import SwipeGesture
from communication import send_long_command, send_command

class PotteryListener(Leap.Listener):
    def __init__(self):
        super(PotteryListener, self).__init__()

        # rotation level (scale)
        self.rotation_level = 0
        self.max_rotation_level = 5.

        # max rotation speed
        rotation_inc = 360.
        self.max_rotation_speed = self.max_rotation_level * rotation_inc

        # swipe ttl
        self.last_swipe_time = 0
        self.swipe_min_delay = 1

    def on_init(self, controller):
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_exit(self, controller):
        pass#controller.disable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);

    def on_frame(self, controller):
        frame = controller.frame()
        #if frame.hands.is_empty:
            #return

        # handle only one hand
        hand = frame.hands[0]

        # handle command gestures
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                self.swipe(gesture)

    def swipe(self, gesture):
        swipe_time = time.time()
        if abs(swipe_time - self.last_swipe_time) < self.swipe_min_delay:
            return
        self.last_swipe_time = swipe_time
        swipe_gesture = SwipeGesture(gesture)
        self.do_swipe(swipe_gesture)

    def do_swipe(self, swipe_gesture):
        direction = -1 if swipe_gesture.direction[0] < 0 else 1
        self.rotation_level = min(max(self.rotation_level + direction,
            -self.max_rotation_speed), self.max_rotation_speed)
        send_long_command('set_continuous_rotation', { 'speed': float(self.rotation_level) * self.max_rotation_speed / self.max_rotation_level }, filters={ 'speed': 'float' })
