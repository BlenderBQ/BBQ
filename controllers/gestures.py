# from controllers import Gesture
from communication import send_command
from filters import *

# FIXME wtf ?
NOTHING = 0x00
GRABBING = 0x01

class ClosingHand(object):
    def __init__(self):
        self.nb_fingers = MixedFilter([
            NoiseFilter(100, 0.3, 10),
            LowpassFilter(0.9)])

    def frame(self, hand):
        fingers = hand.fingers
        self.nb_fingers.add_value(len(fingers))

    def reset(self):
        self.nb_fingers.empty()

    def is_done(self):
        if self.nb_fingers.around(3.0, 0.5) \
                and self.nb_fingers.derivative < -0.012:
            return True
        return False

class OpeningHand(object):
    def __init__(self):
        self.nb_fingers = MixedFilter([
            NoiseFilter(100, 0.3, 10),
            LowpassFilter(0.9)])

    def frame(self, hand):
        fingers = hand.fingers
        self.nb_fingers.add_value(len(fingers))

    def reset(self):
        self.nb_fingers.empty()

    def is_done(self):
        if self.nb_fingers.derivative > 0.015 \
                or self.nb_fingers.around(5, 1.5):
            return True
        return False

# class GrabGesture(Gesture):
#     """
#     The grab gesture is detected when the fingers all converge to the center of
#     the hand.
#     """
#     def __init__(self):
#         super(GrabGesture, self).__init__()
#         self.nb_hands = MixedFilter([NoiseFilter(10, 0.3, 10), LowpassFilter(0.5)])
#         self.nb_fingers = MixedFilter([NoiseFilter(100, 0.3, 10), LowpassFilter(0.9)])
#
#     def setup(self):
#         self.nb_hands.empty()
#         self.nb_fingers.empty()
#
#     def detect(self, controller):
#         frame = controller.frame()
#         self.nb_hands.add_value(len(frame.hands))
#
#         # gesture needs about 1 hand
#         if not self.nb_hands.around(1, 0.1):
#             # print 'HAND'
#             return False
#
#         # grab hands and fingers
#         hand = frame.hands[0]
#         fingers = hand.fingers
#         self.nb_fingers.add_value(len(fingers))
#
#         if self.is_activated:
#             #print 'UPDATE'
#             if self.nb_fingers.derivative > 0.015 \
#                     or self.nb_fingers.around(5, 1.5):
#                 print 'UNGRAB', self.nb_fingers.value, self.nb_fingers.derivative
#                 return False
#         else:
#             if self.nb_fingers.around(3.0, 0.5) \
#                     and self.nb_fingers.derivative < -0.012:
#                 print 'GRAB', self.nb_fingers.derivative
#                 return True
#
#     def on_change(self):
#         if not self.is_activated:
#             self.nb_fingers.empty()
