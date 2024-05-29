# Use base image
FROM ubuntu:22.04

# Set maintainer information
LABEL maintainer="your-email@example.com"

# Avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive


# Install Python 3.11
RUN apt-get update && \
    apt-get install -y python3.11 python3.11-venv python3.11-dev --quiet && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 && \
    apt-get install -y python3-pip


# Install git
RUN apt-get install -y git


# Set working directory
WORKDIR /workspace

# Default command (can be modified as needed)
CMD ["bash"]