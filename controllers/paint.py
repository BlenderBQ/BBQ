import Leap
from communication import send_long_command
from leaputils import MAX_X, MAX_Y, MAX_Z

class ColorListener(Leap.Listener):
    """
    This listener is intended for painting mode.
    It can change the color according to position of the hand with all five fingers opened
    """
    def __init__(self, threshold = 1, length_threshold = 10, history_size = 30):
        Leap.Listener.__init__(self)
        self.threshold = threshold
        self.length_threshold = length_threshold
        self.history_size = history_size
        self.history = []

    def on_frame(self, controller):
        # Get the most recent frame
        frame = controller.frame()

        # Need exactly one hand for this gesture
        if len(frame.hands) is not 1:
            del self.history[:]
            return

        hand = frame.hands[0]

        # About five fingers must be visible
        if len(hand.fingers) < 4:
            del self.history[:]
            return

        self.history.append(hand.stabilized_palm_position)

        # Limit history size
        if len(self.history) > self.history_size:
            self.history = self.history[:-self.history_size]

        # Activate the gesture if there's enough change
        variation = Leap.Vector()
        for i in range(1, len(self.history)):
            variation += self.history[i] - self.history[i-1]
        if variation.magnitude >= self.threshold:
            self.change_color(hand.stabilized_palm_position)

    def change_color(self, position):
        r, g, b = self.to_color(position)
        r, g, b = min(1, r), min(1, g), min(1, b)
        send_long_command('paint_color', {'r': r, 'g': g, 'b': b},
            filters={'r': 'coordinate', 'g': 'coordinate', 'b': 'coordinate'})

    def to_color(self, position):
        """
        Convert a position in Leap space to a color in the RGB cube.
        We use the subspace (0..250, 0..350, -50..0).
        The RGB components are scaled to [0..1]
        """
        # Translate
        x = position.x
        y = position.y
        z = -position.z
        # Scale
        r = max(0, x / MAX_X)
        g = max(0, y / MAX_Y)
        b = max(0, z / MAX_Z)
        return r, g, b
