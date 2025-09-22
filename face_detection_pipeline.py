#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst
import pyds
import platform
import math
import time
from ctypes import *
import threading

def osd_sink_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    num_rects = 0
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

        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break

            if obj_meta.class_id == 0:  # Face detection class
                print(f"Frame {frame_number}: Face detected at "
                      f"({obj_meta.rect_params.left:.0f}, {obj_meta.rect_params.top:.0f}) "
                      f"width={obj_meta.rect_params.width:.0f} "
                      f"height={obj_meta.rect_params.height:.0f} "
                      f"confidence={obj_meta.confidence:.2f}")

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        print(f"Frame {frame_number}: Objects detected: {num_rects}")
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def main(args):
    GObject.threads_init()
    Gst.init(None)

    print("Creating Pipeline")
    pipeline = Gst.Pipeline()

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")

    print("Creating Source")
    source = Gst.ElementFactory.make("v4l2src", "usb-cam-source")
    if not source:
        sys.stderr.write(" Unable to create Source \n")

    caps_v4l2src = Gst.ElementFactory.make("capsfilter", "v4l2src_caps")
    if not caps_v4l2src:
        sys.stderr.write(" Unable to create v4l2src caps \n")

    print("Creating Video Converter")
    vidconvsrc = Gst.ElementFactory.make("videoconvert", "convertor_src1")
    if not vidconvsrc:
        sys.stderr.write(" Unable to create videoconvert \n")

    nvvidconvsrc = Gst.ElementFactory.make("nvvideoconvert", "convertor_src2")
    if not nvvidconvsrc:
        sys.stderr.write(" Unable to create nvvideoconvert \n")

    caps_vidconvsrc = Gst.ElementFactory.make("capsfilter", "nvmm_caps")
    if not caps_vidconvsrc:
        sys.stderr.write(" Unable to create capsfilter \n")

    print("Creating Streamux")
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    print("Creating Pgie")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")

    print("Creating nvvidconv")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")

    print("Creating nvosd")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")

    nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    if not nvvidconv_postosd:
        sys.stderr.write(" Unable to create nvvidconv_postosd \n")

    caps = Gst.ElementFactory.make("capsfilter", "filter")
    caps.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

    encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    if not encoder:
        sys.stderr.write(" Unable to create encoder")

    rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
    if not rtppay:
        sys.stderr.write(" Unable to create rtppay")

    print("Creating Sink")
    sink = Gst.ElementFactory.make("udpsink", "udpsink")
    if not sink:
        sys.stderr.write(" Unable to create udpsink")

    print("Playing USB camera")
    source.set_property('device', '/dev/video0')
    caps_v4l2src.set_property('caps', Gst.Caps.from_string("video/x-raw, framerate=30/1"))
    caps_vidconvsrc.set_property('caps', Gst.Caps.from_string("video/x-raw(memory:NVMM)"))

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', 1)
    streammux.set_property('batched-push-timeout', 4000000)

    pgie.set_property('config-file-path', "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt")

    sink.set_property('host', '224.224.255.255')
    sink.set_property('port', 5000)
    sink.set_property('async', False)
    sink.set_property('sync', 1)

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
    if not sinkpad:
        sys.stderr.write(" Unable to get the sink pad of streammux \n")
    srcpad = caps_vidconvsrc.get_static_pad("src")
    if not srcpad:
        sys.stderr.write(" Unable to get source pad of caps_vidconvsrc \n")
    srcpad.link(sinkpad)

    streammux.link(pgie)
    pgie.link(nvvidconv)
    nvvidconv.link(nvosd)
    nvosd.link(sink)

    osdsinkpad = nvosd.get_static_pad("sink")
    if not osdsinkpad:
        sys.stderr.write(" Unable to get sink pad of nvosd \n")

    osdsinkpad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    print("Starting pipeline")
    pipeline.set_state(Gst.State.PLAYING)

    try:
        loop = GObject.MainLoop()
        loop.run()
    except:
        pass

    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    sys.exit(main(sys.argv))