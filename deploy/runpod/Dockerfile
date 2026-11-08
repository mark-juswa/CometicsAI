FROM python:3.12.13-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    NVIDIA_VISIBLE_DEVICES=all NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    RUNPOD_WORKSPACE=/workspace/beautycore MPLBACKEND=Agg
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates libgomp1 libportaudio2 libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/ /opt/requirements/
RUN python -m pip install pip==25.3 \
    && python -m pip install torch==2.10.0+cu128 --index-url https://download.pytorch.org/whl/cu128 \
    && python -m pip install -r /opt/requirements/gpu.txt \
    && python -m pip check
RUN python -m venv /opt/api \
    && /opt/api/bin/python -m pip install pip==25.3 \
    && /opt/api/bin/python -m pip install -r /opt/requirements/requirements-nails.txt -c /opt/requirements/requirements-demo-constraints.txt \
    && /opt/api/bin/python -m pip check
RUN python -m venv /opt/segment \
    && /opt/segment/bin/python -m pip install pip==25.3 \
    && /opt/segment/bin/python -m pip install torch==2.10.0 torchvision==0.25.0 --index-url https://download.pytorch.org/whl/cpu \
    && /opt/segment/bin/python -m pip install -r /opt/requirements/requirements-nails-segmenter.txt \
    && /opt/segment/bin/python -m pip check
RUN python -m venv /opt/notebook \
    && /opt/notebook/bin/python -m pip install pip==25.3 jupyterlab==4.6.6
# MediaPipe imports lazily; its native task library also needs EGL and GLES.
RUN apt-get update && apt-get install -y --no-install-recommends libegl1 libgles2 \
    && rm -rf /var/lib/apt/lists/*
COPY . /opt/server/
RUN python -c "import platform, torch; assert platform.python_version() == '3.12.13'; assert torch.__version__ == '2.10.0+cu128'; from diffusers import Flux2KleinPipeline" \
    && /opt/api/bin/python -c "import mediapipe; import ctypes.util; assert ctypes.util.find_library('portaudio'); from mediapipe.tasks.python.core.mediapipe_c_bindings import load_raw_library; load_raw_library()" \
    && /opt/segment/bin/python -c "import torch, torchvision; from ultralytics import YOLO; assert '+cpu' in torch.__version__; assert torchvision.extension._has_ops()"
WORKDIR /workspace
EXPOSE 8888
ENTRYPOINT ["python", "/opt/server/runtime.py"]
CMD ["notebook"]
