from functools import partial
from communication import send_command
from controllers import set_current_controller

def center_object():
    print 'centering object'
    send_command('object_center')

def view_from(direction):
    print 'viewing from:', direction
    if direction == 'over': direction = 'top'
    elif direction == 'under': direction = 'bottom'
    view_command = 'view_%s' % direction
    print view_command
    send_command(view_command)

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
    set_current_controller(_mode_mapping[mode])

_cmd_mapping = {
            'center': center_object,
            'over': partial(view_from, 'over'),
            'under': partial(view_from, 'under'),
            'left': partial(view_from, 'left'),
            'right': partial(view_from, 'right'),
            'sculpt': partial(enter_mode, 'sculpt'),
            'pottery': partial(enter_mode, 'pottery'),
            'object': partial(enter_mode, 'object'),
            'drop': partial(enter_mode, 'default'),
            'exit': None
            }

def interpret_command(cmd):
    if cmd not in _cmd_mapping:
        print "T'es trop nul, ta commande elle est naze", cmd
        return
    # Whenever leaving pottery mode, stop rotation
    send_command('stop_rotation')

    if _cmd_mapping[cmd]:
        _cmd_mapping[cmd]()
    else:
        return cmd
