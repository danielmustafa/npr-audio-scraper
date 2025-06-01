# Start from a CUDA + Python base image
FROM nvidia/cuda:12.9.0-cudnn-runtime-ubuntu24.04

# System dependencies
RUN apt-get update && apt-get install -y \
    python3 python3-pip ffmpeg git cmake pkg-config python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set Python as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 1
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Upgrade pip
RUN pip install --upgrade pip

# Install PyTorch with CUDA 12.1 support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install your Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install Playwright + browsers
RUN pip install playwright && playwright install --with-deps

WORKDIR /workspace
