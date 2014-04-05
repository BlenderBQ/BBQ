import os
import pygst; pygst.require('0.10')
import gobject; gobject.threads_init()
import gst
from commands import interpret_command

class VoiceRecognition(object):
    def __init__(self):
        self.is_interpreting = True
        self.pipeline = gst.parse_launch(('gconfaudiosrc ! audioconvert ! audioresample '
            '! vader name=vad auto_threshold=true '
            '! pocketsphinx name=asr ! fakesink'))

        # setup asr
        asr = self.pipeline.get_by_name('asr')
        asr.connect('result', self.asr_result)

        # Language model: http://www.speech.cs.cmu.edu/tools/lmtool-new.html
        this_dir = os.path.dirname(os.path.realpath(__file__))
        asr.set_property('lm', os.path.join(this_dir, 'words.lm'))
        asr.set_property('dict', os.path.join(this_dir, 'words.dic'))
        asr.set_property('configured', True)

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def asr_result(self, asr, text, utterance_id):
        self.on_result(text)

    def on_result(self, text):
        if not text.strip() or len(text.split()) > 1:
            #print 'empty text'
            return
        cmd = text.lower()
        if cmd in ('sleep', 'quiet',):
            #print 'going to sleep'
            self.is_interpreting = False
        elif cmd == 'wake':
            #print 'waking up'
            self.is_interpreting = True
        elif self.is_interpreting:
            interpret_command(cmd)

if __name__ == '__main__':
    vr = VoiceRecognition()
    vr.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass
