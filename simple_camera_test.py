#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import time
import signal

class SimpleCameraTest:
    def __init__(self):
        GObject.threads_init()
        Gst.init(None)
        self.pipeline = None
        self.loop = None
        
    def create_pipeline(self):
        print("Creating simple camera test pipeline...")
        
        # Create pipeline
        self.pipeline = Gst.Pipeline.new("camera-test")
        
        # Create elements
        source = Gst.ElementFactory.make("v4l2src", "camera-source")
        caps_filter = Gst.ElementFactory.make("capsfilter", "caps")
        videoconvert = Gst.ElementFactory.make("videoconvert", "convert")
        videoscale = Gst.ElementFactory.make("videoscale", "scale")
        sink = Gst.ElementFactory.make("fakesink", "sink")
        
        if not all([source, caps_filter, videoconvert, videoscale, sink]):
            print("Failed to create pipeline elements")
            return False
            
        # Set properties
        source.set_property("device", "/dev/video0")
        caps_filter.set_property("caps", 
            Gst.Caps.from_string("video/x-raw, width=640, height=480, framerate=30/1"))
        sink.set_property("sync", False)
        sink.set_property("dump", True)  # Print buffer info
        
        # Add elements to pipeline
        self.pipeline.add(source)
        self.pipeline.add(caps_filter)
        self.pipeline.add(videoconvert)
        self.pipeline.add(videoscale)
        self.pipeline.add(sink)
        
        # Link elements
        if not source.link(caps_filter):
            print("Failed to link source -> caps")
            return False
        if not caps_filter.link(videoconvert):
            print("Failed to link caps -> convert")
            return False
        if not videoconvert.link(videoscale):
            print("Failed to link convert -> scale")
            return False
        if not videoscale.link(sink):
            print("Failed to link scale -> sink")
            return False
            
        print("Pipeline created successfully")
        return True
        
    def run(self):
        if not self.create_pipeline():
            return False
            
        # Set up bus monitoring
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
        
        print("Starting pipeline...")
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            print("Failed to start pipeline")
            return False
            
        # Run main loop
        self.loop = GObject.MainLoop()
        
        def signal_handler(sig, frame):
            print("\nStopping pipeline...")
            self.loop.quit()
            
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            print("Pipeline running. Press Ctrl+C to stop.")
            self.loop.run()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received")
        
        # Cleanup
        self.pipeline.set_state(Gst.State.NULL)
        print("Pipeline stopped")
        return True
        
    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.EOS:
            print("End-of-stream")
            self.loop.quit()
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"Error: {err}, {debug}")
            self.loop.quit()
        elif t == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                print(f"Pipeline state changed from {old_state.value_nick} to {new_state.value_nick}")

def main():
    test = SimpleCameraTest()
    return 0 if test.run() else 1

if __name__ == '__main__':
    sys.exit(main())