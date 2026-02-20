# Use a slim Ubuntu or a dedicated Zephyr image
FROM mcr.microsoft.com/devcontainers/base:ubuntu-22.04

# Install Zephyr/NCS dependencies
RUN apt-get update && apt-get install -y \
    cmake \
    ninja-build \
    gperf \
    ccache \
    dfu-util \
    device-tree-compiler \
    wget \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-tk \
    python3-wheel \
    xz-utils \
    file \
    make \
    gcc \
    libsdl2-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install West (Zephyr's meta-tool)
RUN pip3 install west
