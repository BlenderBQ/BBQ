import time
import Leap
from Leap import SwipeGesture
from communication import send_command

class SlideRotateListener(Leap.Listener):
    def __init__(self):
        Leap.Listener.__init__(self)

        # swipe ttl
        self.last_swipe_time = 0
        self.swipe_min_delay = 1

    def on_init(self, controller):
        controller.enable_gesture(Leap.Gesture.TYPE_SWIPE)

    def on_exit(self, controller):
        send_command('stop_rotation')

    def on_frame(self, controller):
        frame = controller.frame()

        # handle leap native gestures
        for gesture in frame.gestures():
            if gesture.type == Leap.Gesture.TYPE_SWIPE:
                self.swipe(gesture)

    def swipe(self, gesture):
        swipe_time = time.time()
        if abs(swipe_time - self.last_swipe_time) < self.swipe_min_delay:
            return

        self.last_swipe_time = swipe_time
        swipe_gesture = SwipeGesture(gesture)

        # don't handle vertical swipes
        if abs(swipe_gesture.direction[0]) < abs(swipe_gesture.direction[1]):
            return

        if swipe_gesture.direction[0] > 0:
            #print 'Rotating left'
            send_command('do_rotation_left')
        else:
            #print 'Rotating right'
            send_command('do_rotation_right')
