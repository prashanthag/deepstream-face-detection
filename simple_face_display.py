#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import signal

class SimpleFaceDisplay:
    def __init__(self):
        GObject.threads_init()
        Gst.init(None)
        self.pipeline = None
        self.loop = None
        self.frame_count = 0
        
    def create_pipeline(self):
        print("Creating simple face detection pipeline with display...")
        
        # Create pipeline
        self.pipeline = Gst.Pipeline.new("simple-face-display")
        
        # Create elements - simpler pipeline like test_camera_simple.py
        source = Gst.ElementFactory.make("v4l2src", "camera-source")
        caps_filter = Gst.ElementFactory.make("capsfilter", "caps")
        videoconvert1 = Gst.ElementFactory.make("videoconvert", "convert1")
        nvvideoconvert = Gst.ElementFactory.make("nvvideoconvert", "nvconvert")
        caps_nvmm = Gst.ElementFactory.make("capsfilter", "caps_nvmm")
        streammux = Gst.ElementFactory.make("nvstreammux", "mux")
        pgie = Gst.ElementFactory.make("nvinfer", "inference")
        nvvideoconvert2 = Gst.ElementFactory.make("nvvideoconvert", "nvconvert2")
        nvosd = Gst.ElementFactory.make("nvdsosd", "osd")
        nvvideoconvert3 = Gst.ElementFactory.make("nvvideoconvert", "nvconvert3")
        caps_display = Gst.ElementFactory.make("capsfilter", "caps_display")
        videoconvert2 = Gst.ElementFactory.make("videoconvert", "convert2")
        sink = Gst.ElementFactory.make("xvimagesink", "display")
        
        if not all([source, caps_filter, videoconvert1, nvvideoconvert, caps_nvmm,
                   streammux, pgie, nvvideoconvert2, nvosd, nvvideoconvert3, 
                   caps_display, videoconvert2, sink]):
            print("Failed to create pipeline elements")
            return False
            
        # Set properties
        source.set_property("device", "/dev/video0")
        caps_filter.set_property("caps", 
            Gst.Caps.from_string("video/x-raw, width=640, height=480, framerate=30/1"))
        caps_nvmm.set_property("caps", 
            Gst.Caps.from_string("video/x-raw(memory:NVMM)"))
        caps_display.set_property("caps", 
            Gst.Caps.from_string("video/x-raw, format=RGBA"))
            
        streammux.set_property("width", 640)
        streammux.set_property("height", 480)
        streammux.set_property("batch-size", 1)
        streammux.set_property("batched-push-timeout", 4000000)
        
        pgie.set_property("config-file-path", 
            "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt")
        
        sink.set_property("sync", False)
        
        # Add elements to pipeline
        elements = [source, caps_filter, videoconvert1, nvvideoconvert, caps_nvmm,
                   streammux, pgie, nvvideoconvert2, nvosd, nvvideoconvert3, 
                   caps_display, videoconvert2, sink]
        for element in elements:
            self.pipeline.add(element)
        
        # Link elements
        source.link(caps_filter)
        caps_filter.link(videoconvert1)
        videoconvert1.link(nvvideoconvert)
        nvvideoconvert.link(caps_nvmm)
        
        # Link to streammux
        sinkpad = streammux.get_request_pad("sink_0")
        srcpad = caps_nvmm.get_static_pad("src")
        srcpad.link(sinkpad)
        
        # Link rest of pipeline
        streammux.link(pgie)
        pgie.link(nvvideoconvert2)
        nvvideoconvert2.link(nvosd)
        nvosd.link(nvvideoconvert3)
        nvvideoconvert3.link(caps_display)
        caps_display.link(videoconvert2)
        videoconvert2.link(sink)
        
        # Add probe for detection info
        osdsinkpad = nvosd.get_static_pad("sink")
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self.osd_sink_pad_buffer_probe, 0)
        
        print("Pipeline created successfully")
        return True
        
    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        self.frame_count += 1
        if self.frame_count % 30 == 0:  # Print every 30 frames
            print(f"Processing frame {self.frame_count}")
        return Gst.PadProbeReturn.OK
        
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
            print(f"\nStopping pipeline... Processed {self.frame_count} frames")
            self.loop.quit()
            
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            print("Pipeline running. Press Ctrl+C to stop.")
            print("You should see a window with your camera feed and detection boxes.")
            self.loop.run()
        except KeyboardInterrupt:
            print(f"\nKeyboard interrupt received. Processed {self.frame_count} frames")
        
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
            print(f"Error: {err}")
            if debug:
                print(f"Debug: {debug}")
            self.loop.quit()
        elif t == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                print(f"Pipeline state: {old_state.value_nick} -> {new_state.value_nick}")

def main():
    detection = SimpleFaceDisplay()
    return 0 if detection.run() else 1

if __name__ == '__main__':
    sys.exit(main())