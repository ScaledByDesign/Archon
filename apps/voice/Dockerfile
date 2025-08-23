# syntax=docker/dockerfile:1.7
# Stage 1: Builder Stage - Install dependencies including build tools and CUDA toolkit components
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04 AS builder

# Avoid prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.10, pip, build essentials, git, and other system dependencies
# Use cache mounts for apt to avoid re-downloading packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /var/lib/apt/lists/lock && \
    rm -f /var/cache/apt/archives/lock && \
    rm -f /var/lib/dpkg/lock* && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3.10-dev \
    python3.10-venv \
    build-essential \
    git \
    libsndfile1 \
    libportaudio2 \
    ffmpeg \
    portaudio19-dev \
    python3-setuptools \
    python3.10-distutils \
    ninja-build \
    libpython3.10-dev

# Make python3.10 the default python/pip
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Set working directory
WORKDIR /app

# Upgrade pip with cache mount
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip

# Install PyTorch 2.7+ with CUDA 12.8 support for Blackwell architecture (RTX 5070 Ti sm_120)
# Use cache mount to avoid re-downloading the large PyTorch wheels
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
    torch==2.7.0 \
    torchaudio \
    torchvision \
    --index-url https://download.pytorch.org/whl/cu128

# Install DeepSpeed from PyPI (let pip handle platform-specific compilation)
# Note: Pre-compiled Windows wheel not compatible with Linux container
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install deepspeed==0.16.1 || \
    (echo "DeepSpeed installation failed, continuing without it..." && true)

# Copy and install base requirements first (these change less frequently)
COPY --chown=1001:1001 requirements-base.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r requirements-base.txt

# Copy and install ML requirements (these change more frequently)
COPY --chown=1001:1001 requirements-ml.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --prefer-binary -r requirements-ml.txt "ctranslate2<4.5.0" \
    || (echo "pip install ML requirements FAILED." && exit 1)

# Keep original requirements.txt for compatibility
COPY --chown=1001:1001 requirements.txt .

# Copy the application code
COPY --chown=1001:1001 code/ ./code/

# --- Stage 2: Runtime Stage ---
# Base image still needs CUDA toolkit for PyTorch/DeepSpeed/etc in the app
FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

# Avoid prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install ONLY runtime dependencies (no build tools in runtime stage)
# Use cache mounts for apt to avoid re-downloading packages
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    rm -f /var/lib/apt/lists/lock && \
    rm -f /var/cache/apt/archives/lock && \
    rm -f /var/lib/dpkg/lock* && \
    apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    libportaudio2 \
    python3-setuptools \
    curl \
    gosu \
    ninja-build \
    libpython3.10-dev \
    python3.10-dev \
    build-essential

# Make python3.10 the default python
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# Set working directory for the application
WORKDIR /app/code

# Copy installed Python packages from the builder stage
RUN mkdir -p /usr/local/lib/python3.10/dist-packages
COPY --chown=1001:1001 --from=builder /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages

# Copy the application code from the builder stage
COPY --chown=1001:1001 --from=builder /app/code /app/code

# Models will be downloaded on first run via model_initializer.py
# This significantly reduces build time and image size
ARG WHISPER_MODEL=base.en
ENV WHISPER_MODEL=${WHISPER_MODEL}

# Set up model directory structure (will be mounted from host)
RUN mkdir -p /models/huggingface /models/torch /models/whisper /models/coqui-tts


# Create a non-root user and group - DO NOT switch to it here
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --create-home appuser

# Ensure directories are owned by appuser - This prepares the image layers correctly
# The entrypoint will handle runtime permissions for volumes/cache
RUN mkdir -p /home/appuser/.cache && \
    chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /home/appuser && \
    chown -R appuser:appgroup /models && \
    # Also chown the caches potentially populated by root during build
    if [ -d /root/.cache ]; then chown -R appuser:appgroup /root/.cache; fi

# Copy and set permissions for entrypoint script
COPY --chown=1001:1001 entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# --- REMOVED USER appuser --- The container will start as root.

# --- Keep ENV vars ---
ENV HOME=/home/appuser
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="${CUDA_HOME}/bin:${PATH}"
ENV LD_LIBRARY_PATH="${CUDA_HOME}/lib64:${LD_LIBRARY_PATH}"
ENV PYTHONUNBUFFERED=1
ENV MAX_AUDIO_QUEUE_SIZE=50
ENV LOG_LEVEL=INFO
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
ENV RUNNING_IN_DOCKER=true
ENV DS_BUILD_OPS=1
ENV DS_BUILD_CPU_ADAM=0
ENV DS_BUILD_FUSED_ADAM=0
ENV DS_BUILD_UTILS=0
ENV DS_BUILD_TRANSFORMER=1
# Centralized model storage paths
ENV HF_HOME=/models/huggingface
ENV TORCH_HOME=/models/torch
ENV TRANSFORMERS_CACHE=/models/huggingface/transformers
ENV WHISPER_CACHE_DIR=/models/whisper
ENV COQUI_TTS_CACHE_DIR=/models/coqui-tts

# Expose the port the FastAPI application runs on
EXPOSE 8000

# Set the entrypoint script - This runs as root
ENTRYPOINT ["/entrypoint.sh"]
# Define the default command - This is passed as "$@" to the entrypoint script
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
