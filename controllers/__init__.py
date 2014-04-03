import Leap
from controllers import gestures
from filters import (MixedFilter, NoiseFilter, LowpassFilter)
from communication import send_command

class ObjectController(Leap.Listener):
    def __init__(self):
        super(ObjectController, self).__init__()
        self.nb_hands = MixedFilter([
            NoiseFilter(10, 0.3, 10),
            LowpassFilter(0.5)])
        self.grab = GrabLogic()
        self.scale = ScaleLogic()

    def on_init(self, controller):
        pass

    def on_exit(self, controller):
        pass

    def on_frame(self, controller):
        frame = controller.frame()
        self.nb_hands.add_value(len(frame.hands))

        # 1 hand for grab, 2 for scale
        if self.nb_hands.around(1, 0.1):
            self.grab.frame(frame)
        elif self.nb_hands.around(2, 0.1):
            self.scale.frame(frame)
        else:
            self.grab.reset()
            self.scale.reset()

class GrabLogic(object):
    def __init__(self):
        self.grabbing_hand = gestures.GrabbingHand()
        self.is_activated = False

        # hand location
        self.loc_x_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)])
        self.loc_y_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)])
        self.loc_z_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)])

        self.loc_x_origin = 0
        self.loc_y_origin = 0
        self.loc_z_origin = 0

        # hand rotation
        self.rot_x_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05) ])
        self.rot_y_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05) ])
        self.rot_z_hand = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05) ])

        self.rot_x_origin = 0
        self.rot_y_origin = 0
        self.rot_z_origin = 0

    def frame(self, frame):
        hand = frame.hands[0]
        self.grabbing_hand.frame(hand)

        if not self.is_activated and self.grabbing_hand.just_closed():
            self.start(hand)
        if self.is_activated and self.grabbing_hand.just_opened():
            self.stop()
        if self.is_activated:
            self.run(hand)

    def reset(self):
        self.grabbing_hand.reset()
        if self.is_activated:
            self.stop()

    def start(self, hand):
        print 'GRAB'
        self.is_activated = True

        # move origin
        pos = hand.stabilized_palm_position
        self.loc_x_origin = pos.x
        self.loc_y_origin = pos.y
        self.loc_z_origin = pos.z
        send_command('object_move_origin', {})

        # rotate origin
        self.rot_x_origin = hand.direction.pitch
        self.rot_y_origin = hand.direction.yaw
        self.rot_z_origin = hand.direction.roll
        send_command('object_rotate_origin', {})

    def stop(self):
        print 'UNGRAB'
        self.is_activated = False
        self.loc_x_hand.empty()
        self.loc_y_hand.empty()
        self.loc_z_hand.empty()
        self.rot_x_hand.empty()
        self.rot_y_hand.empty()
        self.rot_z_hand.empty()

        send_command('object_move_end', {})
        send_command('object_rotate_end', {})

    def run(self, hand):
        pos = hand.stabilized_palm_position
        self.loc_x_hand.add_value(pos.x)
        self.loc_y_hand.add_value(pos.y)
        self.loc_z_hand.add_value(pos.z)

        self.rot_x_hand.add_value(hand.direction.pitch)
        self.rot_y_hand.add_value(hand.direction.yaw)
        self.rot_z_hand.add_value(hand.direction.roll)

        # send motion
        dx = self.loc_x_hand.value - self.loc_x_origin
        dy = self.loc_y_hand.value - self.loc_y_origin
        dz = self.loc_z_hand.value - self.loc_z_origin
        send_command('object_move', { 'loc_x': dx, 'loc_y': dy, 'loc_z': dz})

        # send rotation
        rx = self.rot_x_hand.value - self.rot_x_origin
        ry = self.rot_y_hand.value - self.rot_y_origin
        rz = self.rot_z_hand.value - self.rot_z_origin
        send_command('object_rotate', { 'rot_x': rx, 'rot_y': ry, 'rot_z': rz})

class ScaleLogic(object):
    def __init__(self):
        self.grabbing_hands = {}
        self.magnitude = MixedFilter([
            NoiseFilter(1000, 100, 20),
            LowpassFilter(0.05)])
        self.magnitude_origin = 0
        self.is_scaling = False

    def frame(self, frame):
        first_hand, second_hand = frame.hands[0], frame.hands[1]

        # make sure hands are setup
        if not self.grabbing_hands:
            self.grabbing_hands = { hand.id: gestures.GrabbingHand() for hand in (first_hand, second_hand) }

        # do frames
        self.grabbing_hands[first_hand.id].frame(first_hand)
        self.grabbing_hands[second_hand.id].frame(second_hand)

        # start scaling
        if not self.is_scaling:
            if all(gh.just_closed() for gh in self.grabbing_hands.itervalues()):
                self.start(first_hand, second_hand)
        else:
            if any(gh.just_opened() for gh in self.grabbing_hands.itervalues()):
                self.stop()
            else:
                self.run(first_hand, second_hand)

    def start(self, first_hand, second_hand):
        self.is_scaling = True
        send_command('object_scale_origin')
        dis = first_hand.stabilized_palm_position - second_hand.stabilized_palm_position
        self.magnitude_origin = dis.magnitude

    def stop(self):
        self.is_scaling = False

    def run(self, first_hand, second_hand):
        dis = first_hand.stabilized_palm_position - second_hand.stabilized_palm_position
        self.magnitude.add_value(dis.magnitude)
        mag = self.magnitude.value / self.magnitude_origin
        send_command('object_scale', { 'sx': mag, 'sy': mag, 'sz': mag })

    def reset(self):
        for hand_filter in self.grabbing_hands.itervalues():
            hand_filter.reset()
        if self.is_scaling:
            self.stop()
        self.magnitude.empty()
        self.grabbing_hands = {}

# leap and its listener/controller
_leap_controller = Leap.Controller()
_current_controller = None

def disable_current_controller():
    global _current_controller
    if _current_controller is None:
        return
    _leap_controller.remove_listener(_current_controller)
    _current_controller = None

defined_controllers = {}

def set_current_controller(ctrl):
    if isinstance(ctrl, (str, unicode)):
        if ctrl not in defined_controllers:
            raise ValueError('Undefined controller %s' % ctrl)
        ctrl = defined_controllers[ctrl]
    disable_current_controller()

    # add listener to leap controller
    global _current_controller
    _current_controller = ctrl()
    _leap_controller.add_listener(_current_controller)
