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
