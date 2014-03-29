import os
import pygst
pygst.require('0.10')
import gobject
gobject.threads_init()
import gst

class VoiceRecognition(object):
    def __init__(self):
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                        + '! vader name=vad auto_threshold=true '
                                        + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('result', self.asr_result)
        asr.set_property('configured', True)

        # Language model: http://www.speech.cs.cmu.edu/tools/lmtool-new.html
        #print os.path.dirname(os.path.realpath(__name__))
        asr.set_property('lm', 'words.lm')
        asr.set_property('dict', 'words.dic')
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.application_message)
        self.is_active = False

    def start(self):
        self.pipeline.set_state(gst.STATE_PLAYING)

    def pause(self):
        vader = self.pipeline.get_by_name('vad')
        vader.set_property('silent', True)

    def toggle_activity(self):
        if self.is_active:
            self.pause()
        else:
            self.start()
        self.is_active = not self.is_active

    def asr_result(self, asr, text, utterance_id):
        print 'asr_result:', text
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', utterance_id)
        asr.post_message(gst.message_new_application(asr, struct))

    def application_message(self, bus, msg):
        msgtype = msg.structure.get_name()
        print 'application_message'
        if msgtype == 'result':
            self.on_result(msg.structure['hyp'])
            #self.pipeline.set_state(gst.STATE_PAUSED)

    def on_result(self, text):
        """
        Receive an entirely interpreted result from Automatic Voice
        Recognition from a different thread.
        """
        print 'on_result:', text

if __name__ == '__main__':
    app = VoiceRecognition()
    app.start()
    while True: pass
    # TODO: input & main loop until keyboard interrupt
