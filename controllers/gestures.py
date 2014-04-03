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

class GrabbingHand(object):
    def __init__(self):
        self.opening_hand = OpeningHand()
        self.closing_hand = ClosingHand()

    def frame(self, hand):
        self.opening_hand.frame(hand)
        self.closing_hand.frame(hand)

    def reset(self):
        self.opening_hand.reset()
        self.closing_hand.reset()

    def just_closed(self):
        return self.closing_hand.is_done()

    def just_opened(self):
        return self.opening_hand.is_done()
