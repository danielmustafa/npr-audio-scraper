FROM mcr.microsoft.com/devcontainers/python:3.11

# Install system dependencies
RUN pip install --upgrade pip

RUN sudo apt-get install pkg-config cmake ffmpeg

# Install Python dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

WORKDIR /workspace


# python 3.11
# sudo apt-get install pkg-config cmake