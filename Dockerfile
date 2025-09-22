FROM nvcr.io/nvidia/deepstream:8.0-gc-triton-devel

WORKDIR /opt/nvidia/deepstream/deepstream

ENV DISPLAY=:0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility,video

RUN apt-get update && apt-get install -y \
    v4l-utils \
    udev \
    python3-pip \
    python3-dev \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    && rm -rf /var/lib/apt/lists/*

# Try to build PyDS from source or use alternative approach
RUN python3 -c "import sys; print('Python version:', sys.version)" && \
    find /opt -name "*.so" | grep -i pyds || echo "PyDS not found in shared libraries"

COPY face_detection_pipeline.py /opt/nvidia/deepstream/deepstream/
COPY deepstream_face_detection.py /opt/nvidia/deepstream/deepstream/
COPY test_camera.py /opt/nvidia/deepstream/deepstream/
COPY simple_face_display.py /opt/nvidia/deepstream/deepstream/
COPY simple_camera_test.py /opt/nvidia/deepstream/deepstream/
COPY gstreamer_face_detection.py /opt/nvidia/deepstream/deepstream/
COPY test_with_sample.py /opt/nvidia/deepstream/deepstream/
COPY run_deepstream_app.py /opt/nvidia/deepstream/deepstream/
COPY simple_usb_detection.py /opt/nvidia/deepstream/deepstream/
COPY console_detection.py /opt/nvidia/deepstream/deepstream/
COPY test_camera_simple.py /opt/nvidia/deepstream/deepstream/
COPY simple_face_config.txt /opt/nvidia/deepstream/deepstream/

CMD ["python3", "face_detection_pipeline.py"]