#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import pyds
import configparser

PGIE_CLASS_ID_FACE = 0

def osd_sink_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        face_count = 0

        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            if obj_meta.class_id == PGIE_CLASS_ID_FACE:
                face_count += 1
                print(f"Frame {frame_number}: Face {face_count} - "
                      f"bbox=({obj_meta.rect_params.left:.0f},{obj_meta.rect_params.top:.0f},"
                      f"{obj_meta.rect_params.width:.0f},{obj_meta.rect_params.height:.0f}) "
                      f"confidence={obj_meta.confidence:.2f}")

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        if face_count > 0:
            print(f"Frame {frame_number}: Total faces detected: {face_count}")
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def main():
    GObject.threads_init()
    Gst.init(None)

    print("Creating DeepStream Face Detection Pipeline")
    pipeline = Gst.Pipeline()

    source = Gst.ElementFactory.make("v4l2src", "usb-cam-source")
    caps_v4l2src = Gst.ElementFactory.make("capsfilter", "v4l2src_caps")
    vidconvsrc = Gst.ElementFactory.make("videoconvert", "convertor_src1")
    nvvidconvsrc = Gst.ElementFactory.make("nvvideoconvert", "convertor_src2")
    caps_vidconvsrc = Gst.ElementFactory.make("capsfilter", "nvmm_caps")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    caps = Gst.ElementFactory.make("capsfilter", "filter")
    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
    sink = Gst.ElementFactory.make("fakesink", "fakesink")

    if not (pipeline and source and caps_v4l2src and vidconvsrc and nvvidconvsrc and
            caps_vidconvsrc and streammux and pgie and nvvidconv and nvosd and sink):
        print("Unable to create pipeline elements")
        return -1

    source.set_property('device', '/dev/video0')
    caps_v4l2src.set_property('caps', Gst.Caps.from_string("video/x-raw, framerate=30/1"))
    caps_vidconvsrc.set_property('caps', Gst.Caps.from_string("video/x-raw(memory:NVMM)"))

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    pgie.set_property('config-file-path', "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt")

    print("Adding elements to Pipeline")
    pipeline.add(source)
    pipeline.add(caps_v4l2src)
    pipeline.add(vidconvsrc)
    pipeline.add(nvvidconvsrc)
    pipeline.add(caps_vidconvsrc)
    pipeline.add(streammux)
    pipeline.add(pgie)
    pipeline.add(nvvidconv)
    pipeline.add(nvosd)
    pipeline.add(sink)

    print("Linking elements in the Pipeline")
    source.link(caps_v4l2src)
    caps_v4l2src.link(vidconvsrc)
    vidconvsrc.link(nvvidconvsrc)
    nvvidconvsrc.link(caps_vidconvsrc)

    sinkpad = streammux.get_request_pad("sink_0")
    srcpad = caps_vidconvsrc.get_static_pad("src")
    srcpad.link(sinkpad)

    streammux.link(pgie)
    pgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(sink)

    osdsinkpad = nvosd.get_static_pad("sink")
    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    print("Starting pipeline")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop = GObject.MainLoop()
        loop.run()
    except KeyboardInterrupt:
        print("\nStopping pipeline...")
    except Exception as e:
        print(f"Error: {e}")

    pipeline.set_state(Gst.State.NULL)
    print("Pipeline stopped")

if __name__ == '__main__':
    sys.exit(main())