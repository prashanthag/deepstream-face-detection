# DeepStream Face Detection with USB Camera

This setup uses NVIDIA DeepStream to perform face detection on video from a Logitech USB camera.

## System Requirements
- NVIDIA GPU with CUDA support
- Docker with NVIDIA Container Runtime
- USB camera (tested with Logitech C920 PRO)

## Quick Start

1. **Build and run the container:**
   ```bash
   docker-compose up --build
   ```

2. **Run with X11 forwarding (for display):**
   ```bash
   xhost +local:docker
   docker-compose up --build
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

## Files Description

- `Dockerfile`: Custom DeepStream container with USB camera support
- `docker-compose.yaml`: Container orchestration with device access
- `face_detection_pipeline.py`: Main DeepStream pipeline for face detection
- `deepstream_face_detection.py`: Alternative simplified pipeline
- `output/`: Directory for output files
- `config/`: Directory for custom configurations

## Camera Access

The container is configured to access:
- `/dev/video0` and `/dev/video1` (USB camera devices)
- Video4Linux utilities for camera control
- Privileged mode for hardware access

## Troubleshooting

1. **Camera not detected:**
   ```bash
   lsusb | grep -i logitech
   ls -la /dev/video*
   ```

2. **Permission issues:**
   ```bash
   sudo usermod -a -G video $USER
   sudo usermod -a -G docker $USER
   ```

3. **GPU not accessible:**
   ```bash
   nvidia-smi
   docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
   ```

## Configuration

The pipeline uses the default DeepStream primary inference configuration. You can customize by:
1. Modifying the config file path in the Python scripts
2. Adding custom model configurations in the `config/` directory