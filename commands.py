import logging
from functools import partial
from communication import send_command
from controllers import set_current_controller

def view_from(direction):
    logging.debug('viewing from %s' % direction)
    send_command('view_%s' % direction)

# mapping of mode to mode changing command (falsy: keep current)
_mode_mapping = {
        'sculpt': 'sculpt',
        'pottery': 'sculpt',
        'paint': 'texture_paint',
        'object': 'object',
        }
def enter_mode(mode):
    logging.debug('entering mode: %s' % mode)
    if mode not in _mode_mapping:
        logging.error('unrecognized mode %s' % mode)
    mode_command = _mode_mapping[mode]
    if mode_command:
        send_command('mode_%s' % mode_command)
    set_current_controller(mode)

# mapping of command word to callable
_cmd_mapping = {
            'above':      partial(view_from,     'top'),
            'add':        partial(send_command,  'sculpt_add'),
            'back':       partial(view_from,     'back'),
            'below':      partial(view_from,     'bottom'),
            'camera':     partial(view_from,     'camera'),
            'center':     partial(send_command,  'object_center'),
            'front':      partial(view_from,     'front'),
            'left':       partial(view_from,     'left'),
            'noob':       partial(send_command,  'toggle_noob'),
            'object':     partial(enter_mode,    'object'),
            'over':       partial(view_from,     'top'),
            'paint':      partial(enter_mode,    'paint'),
            'pottery':    partial(enter_mode,    'pottery'),
            'render':     partial(send_command,  'render'),
            'reset':      partial(send_command,  'object_reset_everything'),
            'right':      partial(view_from,     'right'),
            'sculpt':     partial(enter_mode,    'sculpt'),
            'substract':  partial(send_command,  'sculpt_subtract'),
            'under':      partial(view_from,     'bottom'),
            }

def interpret_command(cmd):
    if cmd not in _cmd_mapping:
        logging.debug('unrecognized command %s' % cmd)
        return
    _cmd_mapping[cmd]()
