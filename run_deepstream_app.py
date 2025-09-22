#!/usr/bin/env python3

import subprocess
import sys
import os

def run_deepstream_app():
    """Run DeepStream sample application with USB camera for face detection"""
    
    print("🚀 Starting DeepStream App with USB Camera for Face Detection")
    print("📹 This will show real-time detection results!")
    
    # Use the built-in deepstream-app with primary detection
    cmd = [
        "deepstream-app",
        "-c", "/opt/nvidia/deepstream/deepstream/samples/configs/deepstream-app/source1_usb_dec_infer_resnet_int8.txt"
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    print("This will:")
    print("✅ Use your USB camera as input")
    print("✅ Run ResNet-based object detection")
    print("✅ Display detected objects with bounding boxes")
    print("✅ Show confidence scores")
    print("\nPress Ctrl+C to stop...")
    
    try:
        # Run the deepstream app
        process = subprocess.run(cmd, cwd="/opt/nvidia/deepstream/deepstream")
        return process.returncode
    except KeyboardInterrupt:
        print("\n🛑 DeepStream app stopped by user")
        return 0
    except Exception as e:
        print(f"❌ Error running DeepStream app: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(run_deepstream_app())