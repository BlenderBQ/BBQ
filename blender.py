import bpy

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

# class TranslationOperator:
#     @classmethod
#     def poll(cls, context):
#         return context.selected_objects != []
#
#     def modal(self, context, event):
#         if event.type == 'ESC':
#             return {'CANCELLED'}
#         return {'RUNNING_MODAL'}
#
#     def invoke(self, context, event):
#         self.x_init = event.mouse_x
#         self.y_init = event.mouse_y
#         return {'RUNNING_MODAL'}

class BBQOperator(bpy.types.Operator):
    bl_idname = "object.bbq"
    bl_label = "BBQ Operator"

    def __init__(self):
        print("Start")

    def __del__(self):
        print("End")

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D' # Only enable in 3d view

    def execute(self, context):
        pass

    def modal(self, context, event):
        # object_move(event.mouse_x / 100, event.mouse_y / 100, 0)
        # object_rotate(event.mouse_x / 100, event.mouse_y / 100, 0)
        object_scale(event.mouse_x / 1000, event.mouse_y / 1000, 0)
        if event.type == 'LEFTMOUSE':
            view_top()
        elif event.type == 'RIGHTMOUSE':
            view_left()
        elif event.type == 'ESC':
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        print(context.window_manager.modal_handler_add(self))
        return {'RUNNING_MODAL'}

bpy.utils.register_class(BBQOperator)
