import bpy
import socket
import json

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
    data = json.loads(transport.readline())
    return None, None

class BBQOperator(bpy.types.Operator):
    bl_idname = "object.bbq"
    bl_label = "BBQ Operator"

    # TODO use Blender's Properties
    # sock_addr = bpy.props.StringProperty(name="Server address")
    sock_addr = '/tmp/bbq'

    def __init__(self):
        print("Start")
        self.transport = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.transport.setblocking(False)

    def __del__(self):
        self.transport.close()
        print("End")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' # Only enable in 3d view

    def execute(self, context):
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        try:
            cmd, args = read_command(self.transport)
        except IOError:
            pass
        else:
            # Do something
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
            self.transport.connect(self.sock_addr)
            self.transport = self.transport.makefile()
        except IOError:
            return {'CANCELLED'}

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}
        # return context.window_manager.invoke_props_dialog(self)

bpy.utils.register_class(BBQOperator)
