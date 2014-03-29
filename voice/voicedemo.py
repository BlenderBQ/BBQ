# TODO: need to export some paths to GST_PLUGIN_PATH, etc?

import pygst
pygst.require('0.10')
#gobject.threads_init() # This is very important!
import gst

class VoiceDemo(object):
    """GStreamer/PocketSphinx Demo Application"""
    def __init__(self):
        """Initialize a DemoApp object"""
        self.init_app()
        self.init_gstreamer()
        self.is_active = False

    def init_app(self):
        """Initialize the GUI components"""
        #print("----- VoiceDemo: voice recognition -----")
        # TODO: improve voice recognition by configuring the pocketsphinx object
        # TODO: build a custom Language Model (http://www.speech.cs.cmu.edu/tools/lmtool-new.html)
        pass

    def init_gstreamer(self):
        """Initialize the speech components"""
        self.pipeline = gst.parse_launch('gconfaudiosrc ! audioconvert ! audioresample '
                                        + '! vader name=vad auto_threshold=true '
                                        + '! pocketsphinx name=asr ! fakesink')
        asr = self.pipeline.get_by_name('asr')
        asr.connect('partial_result', self.forward_partial_result)
        asr.connect('result', self.forward_result)
        asr.set_property('configured', True)
        asr.set_property('lm', 'BlenderBQ.lm')
        asr.set_property('dict', 'BlenderBQ.dic')

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect('message::application', self.receive_result)

    def start(self):
        print 'Starting voice recognition...'
        self.pipeline.set_state(gst.STATE_PLAYING)

    def pause(self):
        vader = self.pipeline.get_by_name('vad')
        vader.set_property('silent', True)
        print 'Voice recognition stopped.'

    def toggle_activity(self):
        """Toggle activation state."""
        if self.is_active:
            self.pause()
        else:
            self.start()
        self.is_active = (not self.is_active)

    def receive_result(self, bus, message):
        """Receive a partial or complete message from the gstreamer application bus"""
        message_type = message.structure.get_name()
        if message_type == 'partial_result':
            self.partial_result(message.structure['hyp'], message.structure['uttid'])
        elif message_type == 'result':
            self.final_result(message.structure['hyp'], message.structure['uttid'])
            self.pause()

    def partial_result(self, text, utterance_id):
        """Display / act on a partial result"""
        print 'Partial result [', utterance_id, ']: ', text

    def forward_partial_result(self, asr, text, utterance_id):
        """
        Receive a partially interpreted result from Automatic Voice Recognition.
        Forward the received text to the main thread through the gstreamer pipeline bus.
        """
        print 'partial...'
        struct = gst.Structure('partial_result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', utterance_id)
        asr.post_message(gst.message_new_application(asr, struct))

    def forward_result(self, asr, text, utterance_id):
        """
        Receive an entirely interpreted result from Automatic Voice Recognition
        Forward the received text to the main thread through the gstreamer pipeline bus."""
        print 'Complete'
        print 'Message:', text
        struct = gst.Structure('result')
        struct.set_value('hyp', text)
        struct.set_value('uttid', utterance_id)
        asr.post_message(gst.message_new_application(asr, struct))

    def final_result(self, text, utterance_id):
        """Display / act on a complete result"""
        print 'Complete result [', utterance_id, ']: ', text

app = VoiceDemo()
app.start()
while True: pass
# TODO: input & main loop until keyboard interrupt
