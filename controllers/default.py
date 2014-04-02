from communication import send_command
from controllers import make_controller
from gestures import GrabGesture
from filters import *

@make_controller(GrabGesture)
def default(ctrl):
    hand = ctrl.current_frame.hands[0]
    fingers = hand.fingers

    pos = hand.stabilized_palm_position
    ctrl.loc_x_hand.add_value(pos.x)
    ctrl.loc_y_hand.add_value(pos.y)
    ctrl.loc_z_hand.add_value(pos.z)

    ctrl.rot_x_hand.add_value(hand.direction.pitch)
    ctrl.rot_y_hand.add_value(hand.direction.yaw)
    ctrl.rot_z_hand.add_value(hand.direction.roll)

    # grab grabbing :P
    is_grabbing = ctrl.gesture_is_activated(GrabGesture)

    if is_grabbing:
        # send motion
        dx = ctrl.loc_x_hand.value - ctrl.loc_x_origin
        dy = ctrl.loc_y_hand.value - ctrl.loc_y_origin
        dz = ctrl.loc_z_hand.value - ctrl.loc_z_origin
        send_command('object_move', { 'loc_x': dx, 'loc_y': dy, 'loc_z': dz})

        # send rotation
        rx = ctrl.rot_x_hand.value - ctrl.rot_x_origin
        ry = ctrl.rot_y_hand.value - ctrl.rot_y_origin
        rz = ctrl.rot_z_hand.value - ctrl.rot_z_origin
        send_command('object_rotate', { 'rot_x': rx, 'rot_y': ry, 'rot_z': rz})

@default.on_enter
def default_enter(ctrl):
    # hand location
    ctrl.loc_x_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.loc_y_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.loc_z_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.loc_x_origin = 0
    ctrl.loc_y_origin = 0
    ctrl.loc_z_origin = 0

    # hand rotation
    ctrl.rot_x_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.rot_y_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.rot_z_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
    ctrl.rot_x_origin = 0
    ctrl.rot_y_origin = 0
    ctrl.rot_z_origin = 0

    def begin_grab(self, grabbed):
        if not grabbed:
            return
        hand = ctrl.current_frame.hands[0]

        # move origin
        pos = hand.stabilized_palm_position
        self.loc_x_origin = pos.x
        self.loc_y_origin = pos.y
        self.loc_z_origin = pos.z
        send_command('object_move_origin', {'loc_x': self.loc_x_origin,
            'loc_y': self.loc_y_origin, 'loc_z': self.loc_z_origin})

        # rotate origin
        self.rot_x_origin = hand.direction.pitch
        self.rot_y_origin = hand.direction.yaw
        self.rot_z_origin = hand.direction.roll
        #send_command('object_rotate_origin', {'rot_x': self.rot_x_origin,
            #'rot_y': self.rot_y_origin, 'rot_z': self.rot_z_origin})
    ctrl.gestures['GrabGesture'].observers.append(begin_grab)

@default.on_leave
def default_leave(ctrl):
    if ctrl.gesture_is_activated(GrabGesture):
        send_command('object_move_end', {})
