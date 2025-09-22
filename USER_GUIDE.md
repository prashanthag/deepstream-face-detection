# NVIDIA DeepStream Face Detection - User Guide

## Quick Setup & Run

### Prerequisites
- Linux system with NVIDIA GPU
- Docker with NVIDIA Container Runtime
- USB camera connected
- X11 display available

### 1. Clone & Build
```bash
git clone https://github.com/prashanthag/deepstream-face-detection.git
cd deepstream-face-detection
docker compose build
```

### 2. Setup Display
```bash
# Allow Docker to access X11 display
xhost +local:docker
export DISPLAY=:1  # or :0 depending on your setup
```

### 3. Test Camera
```bash
# Verify camera works
DISPLAY=:1 docker compose run --rm -e DISPLAY=:1 -v /tmp/.X11-unix:/tmp/.X11-unix deepstream-face-detection python3 test_camera_simple.py
```

### 4. Run Face Detection
```bash
# IMPORTANT: Always stop old containers first
docker ps | grep deepstream
docker stop <container-id>  # if any running

# Run face detection with bounding boxes
DISPLAY=:1 docker compose run --rm -e DISPLAY=:1 -v /tmp/.X11-unix:/tmp/.X11-unix deepstream-face-detection python3 simple_face_display.py
```

## Key Files
- `simple_face_display.py` - Main face detection with visual output
- `test_camera_simple.py` - Camera test script
- `docker-compose.yaml` - Container configuration
- `Dockerfile` - Image build instructions

## Troubleshooting
- **Black video**: Stop all containers before running new ones
- **No display**: Check DISPLAY variable and xhost permissions
- **Camera busy**: Use `docker ps | grep deepstream` and stop running containers
- **Permission denied**: Ensure user is in docker group

## Performance Notes
- First run builds TensorRT engine (takes ~40 seconds)
- Uses ResNet18 TrafficCamNet model (optimized for vehicles/people)
- Detection accuracy varies - model sometimes misses faces
- Processes 30 fps in real-time on RTX 5070 Ti

Press `Ctrl+C` to stop the detection pipeline.