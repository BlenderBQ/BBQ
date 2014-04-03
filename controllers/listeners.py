import Leap
from communication import send_command

class StopListener(Leap.Listener):
    """
    The "calm down" gesture is activated when a fully opened hand is lowered.
    """
    def __init__(self, threshold = 35, history_size = 10):
        Leap.Listener.__init__(self)

        self.hand_origin = Leap.Vector()
        self.history = []

        self.history_size = history_size
        self.threshold = threshold

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need exactly one hand for this gesture
        if len(frame.hands) is not 1:
            self.history = []
            return

        hand = frame.hands[0]

        # About five fingers must be visible
        if len(hand.fingers) < 4:
            self.history = []
            return
        altitude = hand.stabilized_palm_position.y
        self.history.append(altitude)

        # Limit history size
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]

        # Hand must not be going up
        elif len(self.history) >= 2:
            if self.history[-2] < self.history[-1]:
                return

        # Activate the gesture if there's enough vertical change
        variation = 0
        for i in xrange(1, len(self.history)):
            variation += self.history[i] - self.history[i-1]
        if -variation >= self.threshold:
            self.stop()

    def stop(self):
        self.history = []
        send_command('stop_rotation')

class PointersListener(Leap.Listener):
    """
    This gesture is intended for sculpt mode.
    Each finger could potentially send "pressure" commands.
    """
    def __init__(self, threshold=1, length_threshold=10, history_size=30):
        Leap.Listener.__init__(self)
        self.threshold = threshold
        self.length_threshold = length_threshold
        self.history_size = history_size

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need at least one hand
        if not frame.hands:
            return
        # And three fingers at most
        nb_fingers = sum(len(hand.fingers) for hand in frame.hands)
        if nb_fingers > 2 or nb_fingers < 1:
            return

        # TODO itertools.chain <3
        for hand in frame.hands:
            for finger in hand.fingers:

                # Each finger must be present for some time before being able to paint
                # and have a minimum length
                if finger.time_visible > self.threshold \
                        and finger.length > self.length_threshold:
                    self.point_finger(finger.stabilized_tip_position,
                                      finger.direction)

    def point_finger(self, tip, direction):
        # TODO send as long command ?
        tip = rescale_position(tip)
        send_command('finger_touch', { 'x': tip.z, 'y': tip.x, 'z': tip.y,
            'vx': direction.z, 'vy': direction.x, 'vz': direction.y })
