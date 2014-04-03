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

class TwoHandsGrabbing(object):
    def __init__(self):
        self.grabbing_hands = {}
        self.first_hand_closed = MixedFilter([
            #NoiseFilter(2, 100, 20),
            LowpassFilter(0.1)])
        self.second_hand_closed = MixedFilter([
            #NoiseFilter(2, 100, 20),
            LowpassFilter(0.1)])

    def frame(self, hands):
        first_hand, second_hand = hands

        # make sure hands are setup
        if any(hand.id not in self.grabbing_hands for hand in hands):
            self.grabbing_hands = { hand.id: GrabbingHand() for hand in hands }

        # do frames
        self.grabbing_hands[first_hand.id].frame(first_hand)
        self.grabbing_hands[second_hand.id].frame(second_hand)

        # start scaling
        self.first_hand_closed.add_value(int(self.grabbing_hands[first_hand.id].just_closed()))
        self.second_hand_closed.add_value(int(self.grabbing_hands[second_hand.id].just_closed()))

    def reset(self):
        self.first_hand_closed.empty()
        self.second_hand_closed.empty()
        #for hand_filter in self.grabbing_hands.itervalues():
            #hand_filter.reset()
        self.grabbing_hands = {}

    def just_grabbed(self):
        both_closed = self.first_hand_closed.value + self.second_hand_closed.value
        return abs(both_closed - 1.7) < .3

    def just_lost(self):
        return any(gh.just_opened() for gh in self.grabbing_hands.itervalues())
