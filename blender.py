import bpy
import socket
import json
import logging
import mathutils

def blendPos(dim):
    return dim / 50.0

def read_command(transport):
    try:
        line = transport.readline()
        if not line:
            return
        data = json.loads(line)
    except ValueError as e:
        logging.exception(e)
        raise IOError()

    try:
        cmd = data['__cmd__']
        del data['__cmd__']
    except KeyError as e:
        logging.exception(e)
        raise IOError()

    return cmd, data

class BBQOperator(bpy.types.Operator):
    bl_idname = "object.bbq"
    bl_label = "BBQ Operator"

    # TODO use Blender's Properties
    # sock_addr = bpy.props.StringProperty(name="Server address")
    sock_path = 'server.sock'

    def __init__(self):
        print("Starting")
        self.transport = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.transport.setblocking(False)
        self.sockfile = None
        self.move_origin = 0, 0, 0
        self.scale_origin = 1, 1, 1
        self.continuous_speed = 0
        _commands = [
            self.mode_sculpt,
            self.mode_object,
            self.mode_texture_paint,
            self.mode_edit,
            self.view_top,
            self.view_bottom,
            self.view_left,
            self.view_right,
            self.object_move_origin,
            self.object_move,
            self.object_rotate,
            self.object_scale_origin,
            self.object_scale,
            self.object_center,
            self.set_continuous_rotation,
            self.my_little_swinging_vase,
            self.sculpt_touch
        ]
        self.commands = {f.__name__: f for f in _commands}
        self._timer = None

    def __del__(self):
        print("Ending")
        self.transport.close()
        if self.sockfile:
            self.sockfile.close()
        print("End")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' # Only enable in 3d view

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == 'ESC':
            context.window_manager.event_timer_remove(self._timer)
            return {'FINISHED'}

        if event.type == 'TIMER':
            self.my_little_swinging_vase()
            try:
                cmd = read_command(self.sockfile)
            except IOError as e:
                logging.exception(e)
            else:
                if cmd:
                    func, kwargs = cmd
                    print(func, kwargs)
                    if func in self.commands:
                        self.commands[func](**kwargs)

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        try:
            self.transport.connect(self.sock_path)
            self.sockfile = self.transport.makefile()
        except IOError as e:
            logging.exception(e)
            return {'CANCELLED'}

        print("Started")
        self._timer = context.window_manager.event_timer_add(0.01, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return context.window_manager.invoke_props_dialog(self)

    def my_little_swinging_vase(self, **kwargs):
        for o in bpy.context.selected_objects:
            angle = o.rotation_euler.copy()
            angle.z += self.continuous_speed
            o.rotation_euler = angle

    def set_continuous_rotation(self, **kwargs):
        self.continuous_speed = kwargs['speed']

    def sculpt_touch(self, **kwargs):
        x, y, z = kwargs['x'], kwargs['y'], kwargs['z']
        vx, vy, vz = kwargs['vx'], kwargs['vy'], kwargs['vz']

        dist = 0.42 # magic number
        x2, y2, z2 = x + vx * dist, y + vy * dist, z + vz * dist

        p1 = bpy.types.OperatorStrokeElement()
        p1.is_start = True
        p1.location = x, y, z
        p1.pressure = 1.0
        p1.time = 1.0

        p2 = bpy.types.OperatorStrokeElement()
        p2.is_start = False
        p2.pressure = 1.0
        p2.time = 1.0

        bpy.ops.sculpt.brush_stroke(stroke=[p1, p2])

    def mode_set(self, mode):
        if bpy.context.area.type == 'VIEW_3D':
            bpy.ops.object.mode_set(mode=mode)

    def mode_sculpt(self):
        self.mode_set('SCULPT')

    def mode_object(self):
        self.mode_set('OBJECT')

    def mode_texture_paint(self):
        self.mode_set('TEXTURE_PAINT')

    def mode_edit(self):
        self.mode_set('EDIT')

    def view_numpad(self, view):
        if bpy.context.area.type == 'VIEW_3D':
            bpy.ops.view3d.viewnumpad(type=view)

    def view_top(self):
        self.view_numpad('TOP')

    def view_bottom(self):
        self.view_numpad('BOTTOM')

    def view_left(self):
        self.view_numpad('LEFT')

    def view_right(self):
        self.view_numpad('RIGHT')

    def view_camera(self):
        self.view_numpad('CAMERA')

    def object_move_origin(self, **kwargs):
        x, y, z = kwargs['x'], kwargs['y'], kwargs['z']
        self.move_origin = x, y, z
        self.move_matrix_origin = bpy.context.area.spaces[0].region_3d.view_matrix

    def object_move(self, **kwargs):
        tx, ty, tz = kwargs['tx'], kwargs['ty'], kwargs['tz']
        x, y, z = self.move_origin
        dx, dy, dz = tx - x, ty - y, tz - z
        dx, dy, dz = map(blendPos, [dx, dy, dz])
        # mat_trans = mathutils.Matrix.Translation((dx, dy, dz))
        # loc = (self.move_matrix_origin * mat_trans).decompose()[0]
        for o in bpy.context.selected_objects:
            # o.location = loc
            o.location = dx, dy, dz

    def object_rotate(self, **kwargs):
        ax, ay, az = kwargs['ax'], kwargs['ay'], kwargs['az']
        for o in bpy.context.selected_objects:
            o.rotation_euler = (ax, ay, az)

    def object_scale_origin(self):
        s = bpy.context.selected_objects[0].scale
        self.scale_origin = s.x, s.y, s.z

    def object_scale(self, **kwargs):
        sx, sy, sz = kwargs['sx'], kwargs['sy'], kwargs['sz']
        x, y, z = self.scale_origin
        dx, dy, dz = sx * x, sy * y, sz * z
        for o in bpy.context.selected_objects:
            o.scale = (dx, dy, dz)

    def object_center(self):
        object_move(0, 0, 0)

bpy.utils.register_class(BBQOperator)
