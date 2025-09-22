#!/usr/bin/env python3
import os
import sys

print("Testing camera device access...")
for i in range(3):
    device = f"/dev/video{i}"
    exists = os.path.exists(device)
    print(f"{device}: {'✓' if exists else '✗'}")
    
    if exists:
        try:
            with open(device, 'rb') as f:
                print(f"  - Can open {device}")
        except PermissionError:
            print(f"  - Permission denied for {device}")
        except Exception as e:
            print(f"  - Error opening {device}: {e}")

print("\nTesting GStreamer availability...")
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst
    Gst.init(None)
    print("✓ GStreamer available")
    
    # Test v4l2src element
    source = Gst.ElementFactory.make("v4l2src", "test-source")
    if source:
        print("✓ v4l2src element available")
    else:
        print("✗ v4l2src element not available")
        
except Exception as e:
    print(f"✗ GStreamer error: {e}")

print("\nTesting PyDS availability...")
try:
    import pyds
    print("✓ PyDS available")
except Exception as e:
    print(f"✗ PyDS error: {e}")