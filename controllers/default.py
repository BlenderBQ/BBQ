from communication import send_command
from controllers import Controller
from controllers.gestures import GrabGesture
from filters import (MixedFilter, NoiseFilter, LowpassFilter)

class ObjectController(Controller):
    def __init__(self):
        super(ObjectController, self).__init__([GrabGesture])

        # hand location
        self.loc_x_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.loc_y_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.loc_z_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.loc_x_origin = 0
        self.loc_y_origin = 0
        self.loc_z_origin = 0

        # hand rotation
        self.rot_x_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.rot_y_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.rot_z_hand = MixedFilter([ NoiseFilter(1000, 100, 20), LowpassFilter(0.05) ])
        self.rot_x_origin = 0
        self.rot_y_origin = 0
        self.rot_z_origin = 0

        # observe grab for activate/deactivate
        self.gestures[GrabGesture.__name__].observers.append(self.observe_grab)

    def observe_grab(self, grabbed):
        if not grabbed:
            return
        hand = self.current_frame.hands[0]

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

    def update(self):
        hand = self.current_frame.hands[0]
        fingers = hand.fingers

        pos = hand.stabilized_palm_position
        self.loc_x_hand.add_value(pos.x)
        self.loc_y_hand.add_value(pos.y)
        self.loc_z_hand.add_value(pos.z)

        self.rot_x_hand.add_value(hand.direction.pitch)
        self.rot_y_hand.add_value(hand.direction.yaw)
        self.rot_z_hand.add_value(hand.direction.roll)

        # grab grabbing :P
        is_grabbing = self.gesture_is_activated(GrabGesture.__name__)

        if is_grabbing:
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

    def leave(self):
        if self.gesture_is_activated(GrabGesture.__name__):
            send_command('object_move_end', {})
