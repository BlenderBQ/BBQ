from functools import partial
from communication import send_command
from controllers import set_current_controller

def view_from(direction):
    print 'viewing from:', direction
    send_command('view_%s' % direction)

_mode_mapping = {
        'sculpt': 'sculpt',
        'pottery': 'pottery',
        'texture_paint': 'paint',
        'object': 'object',
        }
def enter_mode(mode):
    print 'entering mode:', mode
    if mode not in _mode_mapping:
        print 'COMMENT T\'ES TROP NUL', mode
    if mode == 'pottery':
        send_command('mode_sculpt')
    else:
        send_command('mode_%s' % mode)
    set_current_controller(_mode_mapping[mode])

_cmd_mapping = {
            'reset': partial(send_command, 'object_reset_everything'),
            'center': partial(send_command, 'object_center'),
            'render': partial(send_command, 'render'),
            'above': partial(view_from, 'top'), 'over': partial(view_from, 'top'),
            'below': partial(view_from, 'bottom'), 'under': partial(view_from, 'bottom'),
            'camera': partial(view_from, 'camera'),
            'front': partial(view_from, 'front'),
            'back': partial(view_from, 'back'),
            'left': partial(view_from, 'left'),
            'right': partial(view_from, 'right'),
            'sculpt': partial(enter_mode, 'sculpt'),
            'paint': partial(enter_mode, 'texture_paint'),
            'pottery': partial(enter_mode, 'pottery'),
            'object': partial(enter_mode, 'object'),
            'add': partial(send_command, 'sculpt_add'),
            'substract': partial(send_command, 'sculpt_subtract'),
            'exit': None,
            }

def interpret_command(cmd):
    if cmd not in _cmd_mapping:
        print "T'es trop nul, ta commande elle est naze", cmd
        return

    if _cmd_mapping[cmd] is not None:
        return _cmd_mapping[cmd]()
    return cmd
