import bpy
import socket
import json
import logging

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
        _commands = [
            self.mode_sculpt,
            self.mode_object,
            self.mode_texture_paint,
            self.mode_edit,
            self.view_top,
            self.view_bottom,
            self.view_left,
            self.view_right,
            self.object_move,
            self.object_rotate,
            self.object_scale,
            self.object_center
        ]
        self.commands = {f.__name__: f for f in _commands}

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
            return {'FINISHED'}

        try:
            cmd = read_command(self.sockfile)
        except IOError as e:
            logging.exception(e)
        else:
            if cmd:
                func, kwargs = cmd
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
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return context.window_manager.invoke_props_dialog(self)

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

    def object_move(self, **kwargs):
        tx, ty, tz = kwargs['tx'], kwargs['ty'], kwargs['tz']
        for o in bpy.context.selected_objects:
            o.location = (tx, ty, tz)

    def object_rotate(self, **kwargs):
        ax, ay, az = kwargs['ax'], kwargs['ay'], kwargs['az']
        for o in bpy.context.selected_objects:
            o.rotation_euler = (ax, ay, az)

    def object_scale(self, **kwargs):
        sx, sy, sz = kwsrgs['sx'], kwsrgs['sy'], kwsrgs['sz']
        for o in bpy.context.selected_objects:
            o.scale = (sx, sy, sz)

    def object_center(self):
        object_move(0, 0, 0)

bpy.utils.register_class(BBQOperator)
