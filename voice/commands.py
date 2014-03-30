from functools import partial
from communication import send_command
from controllers import set_current_controller

def reset_object():
    print 'resetting object'
    send_command('object_reset_everything')

def center_object():
    print 'centering object'
    send_command('object_center')

def view_from(direction):
    print 'viewing from:', direction
    send_command('view_%s' % direction)

_mode_mapping = {
        'sculpt': 'sculpt',
        'pottery': 'pottery',
        'object': 'object',
        'default': 'object',
        }
def enter_mode(mode):
    print 'entering mode:', mode
    if mode not in _mode_mapping:
        print 'COMMENT T\'ES TROP NUL', mode
    if mode == 'sculpt' or mode == 'pottery':
        send_command('mode_sculpt')
    else:
        send_command('mode_object')
    set_current_controller(_mode_mapping[mode])

_cmd_mapping = {
            'center': center_object, 'reset': reset_object,
            'above': partial(view_from, 'top'), 'over': partial(view_from, 'top'),
            'below': partial(view_from, 'bottom'), 'under': partial(view_from, 'bottom'),
            'left': partial(view_from, 'left'),
            'right': partial(view_from, 'right'),
            'sculpt': partial(enter_mode, 'sculpt'),
            'pottery': partial(enter_mode, 'pottery'),
            'object': partial(enter_mode, 'object'),
            'default': partial(enter_mode, 'default'), 'drop': partial(enter_mode, 'default'),
            'exit': None,
            }

def interpret_command(cmd):
    if cmd not in _cmd_mapping:
        if 'above' == cmd:
            print 'AbOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOOVE!!!!!!!!'
        print "T'es trop nul, ta commande elle est naze", cmd
        return

    if _cmd_mapping[cmd] is not None:
        return _cmd_mapping[cmd]()
    return cmd
