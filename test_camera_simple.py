#!/usr/bin/env python3

import subprocess
import sys
import time

def test_camera_with_gstreamer():
    """Test camera with simple GStreamer pipeline"""
    
    print("🔍 Testing camera with simple GStreamer pipeline...")
    
    # Simple test pipeline
    cmd = [
        "gst-launch-1.0", 
        "v4l2src", "device=/dev/video0", "!",
        "video/x-raw,width=640,height=480,framerate=30/1", "!",
        "videoconvert", "!",
        "xvimagesink"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print("This should open a window showing your camera feed")
    print("Press Ctrl+C to stop...")
    
    try:
        process = subprocess.run(cmd, timeout=30)
        return process.returncode == 0
    except subprocess.TimeoutExpired:
        print("✅ Camera test completed (timeout reached)")
        return True
    except KeyboardInterrupt:
        print("✅ Camera test stopped by user")
        return True
    except Exception as e:
        print(f"❌ Camera test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_camera_with_gstreamer()
    sys.exit(0 if success else 1)