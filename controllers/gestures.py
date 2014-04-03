from communication import send_command
from filters import (MixedFilter, NoiseFilter, LowpassFilter)

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
