import bpy
import bgl
import socket
import json
import math
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
        self.moving = False
        self.move_lock = None
        self.scale_origin = 1, 1, 1

        # rotation (pottery mode)
        self.continuous_speed = 0
        self.rotation_level = 0
        self.max_rotation_level = 5.
        self.rotation_inc = 0.02

        _commands = [
            self.mode_sculpt,
            self.mode_object,
            self.mode_texture_paint,
            self.mode_edit,
            self.view_top,
            self.view_bottom,
            self.view_left,
            self.view_right,
            self.view_front,
            self.view_back,
            self.view_camera,
            self.render,
            self.object_move_origin,
            self.object_move,
            self.object_move_end,
            self.object_rotate,
            self.object_scale_origin,
            self.object_scale,
            self.object_center,
            self.set_continuous_rotation,
            self.do_rotation_left,
            self.do_rotation_right,
            self.stop_rotation,
            self.my_little_swinging_vase,
            self.sculpt_touch,
            self.object_reset_everything,
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
            context.space_data.draw_handler_remove(self._handle, 'WINDOW')
            return {'FINISHED'}

        if self.moving:
            if event.type == 'X':
                self.move_lock = 'X'
            if event.type == 'Y':
                self.move_lock = 'Y'
            if event.type == 'Z':
                self.move_lock = 'Z'

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
            self.x, self.y, self.z = 0, 0, 0
            self.transport.connect(self.sock_path)
            self.sockfile = self.transport.makefile()
            self._handle = context.space_data.draw_handler_add(self.draw_gl,
                    (self, context), 'WINDOW', 'POST_PIXEL')
        except IOError as e:
            logging.exception(e)
            return {'CANCELLED'}

        print("Started")
        self._timer = context.window_manager.event_timer_add(0.01, context.window)
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return context.window_manager.invoke_props_dialog(self)

    def draw_gl(self, op, context):
        bgl.glColor3f(0, 0.5, 0.5)

        # position, radius
        radius = 15. # FIXME magic number
        nb_iters = 360

        bgl.glPushMatrix()
        bgl.glTranslatef(self.x, self.y, self.z)
        bgl.glBegin(bgl.GL_LINE_LOOP)
        for i in range(nb_iters):
            angle = math.radians(i)
            bgl.glVertex2f(math.cos(angle)*radius, math.sin(angle)*radius);
        bgl.glPopMatrix()
        bgl.glEnd()

    def my_little_swinging_vase(self, **kwargs):
        for o in bpy.context.selected_objects:
            angle = o.rotation_euler.copy()
            angle.z += self.continuous_speed
            o.rotation_euler = angle

    def set_continuous_rotation(self, direction):
        self.rotation_level = max(-self.max_rotation_level, min(self.rotation_level + direction, self.max_rotation_level))
        print('Rotation level', self.rotation_level)
        self.continuous_speed = float(self.rotation_level) * self.rotation_inc

    def do_rotation_left(self):
        self.set_continuous_rotation(1)
    def do_rotation_right(self):
        self.set_continuous_rotation(-1)
    def stop_rotation(self):
        self.continuous_speed = 0
        self.rotation_level = 0

    def sculpt_touch(self, **kwargs):
        x, y, z = kwargs['x'], kwargs['y'], kwargs['z']
        vx, vy, vz = kwargs['vx'], kwargs['vy'], kwargs['vz']

        dist = 0.42 # magic number
        x2, y2, z2 = x + vx * dist, y + vy * dist, z + vz * dist
        x, y, z = self.foo(x, y, z)
        x2, y2, z2 = self.foo(x2, y2, z2)
        self.x, self.y, self.z = x, y, z

        print('#####', x, y, z)

        p1 = { 'name': 'dummy_foo',
                'is_start': True,
                'location': (x, y, z),
                'mouse': (0, 0),
                'pressure': 1.0,
                'pen_flip': False,
                'time': 1.0}

        p2 = { 'name': 'dummy_bar',
                'is_start': False,
                'location': (x2, y2, z2),
                'mouse': (0, 0),
                'pressure': 1.0,
                'pen_flip': False,
                'time': 1.0}

        bpy.ops.sculpt.brush_stroke(stroke=[p1, p2])

    def foo(self, x, y, z):
        bbox = bpy.context.selected_objects[0].bound_box
        xmin = min(pos[0] for pos in bbox)
        ymin = min(pos[1] for pos in bbox)
        zmin = min(pos[2] for pos in bbox)
        xmax = max(pos[0] for pos in bbox)
        ymax = max(pos[1] for pos in bbox)
        zmax = max(pos[2] for pos in bbox)

        dx = xmax - xmin
        dy = ymax - ymin
        dz = zmax - zmin

        def bar(p, d, t, m):
            print('@@@@', p, d, t, m)
            return (p + 1) / 2.0 * d * (1 + t * 2) + m - d * t

        # TODO x est toujours constant après transfo. Jeune homme allez i
        t = 0.1
        x_ = bar(x, dx, t, xmin)
        y_ = bar(y, dy, t, ymin)
        z_ = bar(z, dz, t, zmin)

        return x_, y_, z_

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

    def view_front(self):
        self.view_numpad('FRONT')

    def view_back(self):
        self.view_numpad('BACK')

    def view_camera(self):
        self.view_numpad('CAMERA')

    def object_move_origin(self, **kwargs):
        x, y, z = kwargs['x'], kwargs['y'], kwargs['z']
        self.move_origin = x, y, z
        self.moving = True
        self.move_matrix_origin = bpy.context.area.spaces[0].region_3d.view_matrix
        print('save', x, y, z)

    def object_move_end(self):
        self.moving = False
        self.move_lock = None

    def object_move(self, **kwargs):
        tx, ty, tz = kwargs['tx'], kwargs['ty'], kwargs['tz']
        x, y, z = self.move_origin
        dx, dy, dz = tx + x, ty + y, tz + z
        if self.move_lock == 'X':
            dy, dz = y, z
        if self.move_lock == 'Y':
            dx, dz = x, z
        if self.move_lock == 'Z':
            dx, dy = x, y
        print('tr', tx, ty, tz)
        print('pos', dx, dy, dz)
        dx, dy, dz = map(blendPos, [dx, dy, dz])
        # mat_trans = mathutils.Matrix.Translation((dx, dy, dz))
        # loc = (self.move_matrix_origin * mat_trans).decompose()[0]
        for o in bpy.context.selected_objects:
            # o.location = loc
            o.location = dx, dy, dz

    def object_rotate(self, **kwargs):
        ax, ay, az = -kwargs['yaw'], -kwargs['pitch'], kwargs['roll']
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
        for o in bpy.context.selected_objects:
            o.location = 0, 0, 0

    def object_reset_everything(self):
        for o in bpy.context.selected_objects:
            o.location = 0, 0, 0
            o.rotation_euler = 0, 0, 0

    def render(self):
        bpy.ops.render.render()

bpy.utils.register_class(BBQOperator)
