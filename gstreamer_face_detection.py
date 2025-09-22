#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import signal

class DeepStreamFaceDetection:
    def __init__(self):
        GObject.threads_init()
        Gst.init(None)
        self.pipeline = None
        self.loop = None
        self.frame_count = 0
        
    def create_pipeline(self):
        print("Creating DeepStream face detection pipeline...")
        
        # Create pipeline
        self.pipeline = Gst.Pipeline.new("deepstream-face-detection")
        
        # Create elements
        source = Gst.ElementFactory.make("v4l2src", "camera-source")
        caps_v4l2src = Gst.ElementFactory.make("capsfilter", "v4l2src_caps")
        vidconvsrc = Gst.ElementFactory.make("videoconvert", "convertor_src1")
        nvvidconvsrc = Gst.ElementFactory.make("nvvideoconvert", "convertor_src2")
        caps_vidconvsrc = Gst.ElementFactory.make("capsfilter", "nvmm_caps")
        streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
        pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
        nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
        nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
        nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
        caps_filter = Gst.ElementFactory.make("capsfilter", "filter")
        videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
        sink = Gst.ElementFactory.make("xvimagesink", "videosink")
        
        if not all([source, caps_v4l2src, vidconvsrc, nvvidconvsrc, caps_vidconvsrc, 
                   streammux, pgie, nvvidconv, nvosd, nvvidconv_postosd, caps_filter, videoconvert, sink]):
            print("Failed to create pipeline elements")
            return False
            
        # Set properties
        source.set_property("device", "/dev/video0")
        caps_v4l2src.set_property("caps", 
            Gst.Caps.from_string("video/x-raw, framerate=30/1"))
        caps_vidconvsrc.set_property("caps", 
            Gst.Caps.from_string("video/x-raw(memory:NVMM)"))
        
        streammux.set_property("width", 1920)
        streammux.set_property("height", 1080)
        streammux.set_property("batch-size", 1)
        streammux.set_property("batched-push-timeout", 4000000)
        
        # Use primary inference config for face detection
        config_path = "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt"
        pgie.set_property("config-file-path", config_path)
        
        caps_filter.set_property("caps", Gst.Caps.from_string("video/x-raw, format=RGBA"))
        
        sink.set_property("sync", False)
        sink.set_property("async", False)
        
        # Add elements to pipeline
        elements = [source, caps_v4l2src, vidconvsrc, nvvidconvsrc, caps_vidconvsrc,
                   streammux, pgie, nvvidconv, nvosd, nvvidconv_postosd, caps_filter, videoconvert, sink]
        for element in elements:
            self.pipeline.add(element)
        
        # Link elements
        source.link(caps_v4l2src)
        caps_v4l2src.link(vidconvsrc)
        vidconvsrc.link(nvvidconvsrc)
        nvvidconvsrc.link(caps_vidconvsrc)
        
        # Link to streammux
        sinkpad = streammux.get_request_pad("sink_0")
        srcpad = caps_vidconvsrc.get_static_pad("src")
        srcpad.link(sinkpad)
        
        # Link rest of pipeline
        streammux.link(pgie)
        pgie.link(nvvidconv)
        nvvidconv.link(nvosd)
        nvosd.link(nvvidconv_postosd)
        nvvidconv_postosd.link(caps_filter)
        caps_filter.link(videoconvert)
        videoconvert.link(sink)
        
        # Add probe to see detection results
        osdsinkpad = nvosd.get_static_pad("sink")
        osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, self.osd_sink_pad_buffer_probe, 0)
        
        print("Pipeline created successfully")
        return True
        
    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        # This is a simplified probe without PyDS
        self.frame_count += 1
        if self.frame_count % 30 == 0:  # Print every 30 frames (1 second at 30fps)
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
    detection = DeepStreamFaceDetection()
    return 0 if detection.run() else 1

if __name__ == '__main__':
    sys.exit(main())