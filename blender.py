import bpy
import socket
import json
import logging

def mode_set(mode):
    if bpy.context.area.type == 'VIEW_3D':
        bpy.ops.object.mode_set(mode=mode)

def mode_sculpt():
    mode_set('SCULPT')

def mode_object():
    mode_set('OBJECT')

def mode_texture_paint():
    mode_set('TEXTURE_PAINT')

def mode_edit():
    mode_set('EDIT')

def view_numpad(view):
    if bpy.context.area.type == 'VIEW_3D':
        bpy.ops.view3d.viewnumpad(type=view)

def view_top():
    view_numpad('TOP')

def view_bottom():
    view_numpad('BOTTOM')

def view_left():
    view_numpad('LEFT')

def view_right():
    view_numpad('RIGHT')

def view_camera():
    view_numpad('CAMERA')

def object_move(tx, ty, tz):
    for o in bpy.context.selected_objects:
        o.location = (tx, ty, tz)

def object_rotate(ax, ay, az):
    for o in bpy.context.selected_objects:
        o.rotation_euler = (ax, ay, az)

def object_scale(sx, sy, sz):
    for o in bpy.context.selected_objects:
        o.scale = (sx, sy, sz)

def object_center():
    object_move(0, 0, 0)

def read_command(transport):
    try:
        data = json.loads(transport.readline())
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
        print("Start")
        self.transport = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.transport.setblocking(False)
        self.sockfile = None

    def __del__(self):
        self.transport.shutdown(socket.SHUT_RDWR)
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
        try:
            cmd, args = read_command(self.transport)
        except IOError as e:
            logging.exception(e)
        else:
            # Do something
            print(cmd, args)
        # object_move(event.mouse_x / 100, event.mouse_y / 100, 0)
        # object_rotate(event.mouse_x / 100, event.mouse_y / 100, 0)
        # object_scale(event.mouse_x / 1000, event.mouse_y / 1000, 0)
        # if event.type == 'LEFTMOUSE':
        #     view_top()
        # if event.type == 'RIGHTMOUSE':
        #     view_left()
        if event.type == 'ESC':
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        try:
            self.transport.connect(self.sock_path)
            self.sockfile = self.transport.makefile()
        except IOError as e:
            logging.exception(e)
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_class(BBQOperator)
