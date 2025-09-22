#!/usr/bin/env python3

import subprocess
import sys
import os

def create_usb_config():
    """Create a simple config file for USB camera detection"""
    
    config_content = """
[application]
enable-perf-measurement=1
perf-measurement-interval-sec=5

[tiled-display]
enable=1
rows=1
columns=1
width=1280
height=720

[source0]
enable=1
type=1
camera-v4l2-dev-node=0
width=640
height=480
framerate=30

[streammux]
gpu-id=0
batch-size=1
batched-push-timeout=40000
width=1920
height=1080

[primary-gie]
enable=1
gpu-id=0
batch-size=1
bbox-border-color0=1;0;0;1
bbox-border-color1=0;1;1;1
bbox-border-color2=0;0;1;1
bbox-border-color3=0;1;0;1
interval=0
gie-unique-id=1
model-engine-file=/opt/nvidia/deepstream/deepstream/samples/models/Primary_Detector/resnet18_trafficcamnet_pruned.onnx_b30_gpu0_fp16.engine
config-file-path=/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/config_infer_primary.txt

[sink0]
enable=1
type=2
sync=0
source-id=0
gpu-id=0
nvbuf-memory-type=0
"""
    
    config_path = "/tmp/usb_camera_detection.txt"
    with open(config_path, 'w') as f:
        f.write(config_content)
    
    return config_path

def run_usb_detection():
    """Run DeepStream with USB camera for detection"""
    
    print("🚀 Setting up DeepStream USB Camera Detection")
    
    # Create config file
    config_file = create_usb_config()
    print(f"📄 Created config file: {config_file}")
    
    # Run deepstream-app
    cmd = ["deepstream-app", "-c", config_file]
    
    print(f"🔧 Running: {' '.join(cmd)}")
    print("\n📹 This will:")
    print("✅ Capture from USB camera (/dev/video0)")
    print("✅ Run object detection")
    print("✅ Show detected objects with bounding boxes")
    print("✅ Display confidence scores")
    print("\n👤 Position yourself in front of the camera!")
    print("⏱️  Press Ctrl+C to stop...\n")
    
    try:
        os.chdir("/opt/nvidia/deepstream/deepstream")
        process = subprocess.run(cmd)
        return process.returncode
    except KeyboardInterrupt:
        print("\n🛑 Detection stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_usb_detection())