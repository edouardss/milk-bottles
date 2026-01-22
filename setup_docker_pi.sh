#!/bin/bash

# Install Docker and Roboflow Inference Server on Raspberry Pi
# Based on official Roboflow documentation for ARM devices

set -e

echo "======================================================"
echo "Installing Docker and Roboflow Inference on Pi"
echo "======================================================"
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo && ! grep -q "BCM" /proc/cpuinfo; then
    echo "⚠ WARNING: This doesn't appear to be a Raspberry Pi"
    echo "Architecture: $(uname -m)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for 64-bit OS (required by Roboflow)
if [ "$(uname -m)" != "aarch64" ]; then
    echo "✗ ERROR: Roboflow Inference requires 64-bit Raspberry Pi OS"
    echo "  Current architecture: $(uname -m)"
    echo ""
    echo "Please install 64-bit Raspberry Pi OS:"
    echo "  https://www.raspberrypi.com/software/operating-systems/"
    exit 1
fi

echo "✓ Running on 64-bit ARM (aarch64)"
echo ""

echo "Step 1: Checking if Docker is installed..."
if command -v docker &> /dev/null; then
    echo "✓ Docker is already installed"
    docker --version
else
    echo "Docker not found. Installing Docker..."
    echo ""

    # Use Docker's official convenience script for Raspberry Pi
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh

    # Add current user to docker group (to run without sudo)
    sudo usermod -aG docker $USER

    # Clean up
    rm get-docker.sh

    echo ""
    echo "✓ Docker installed successfully"
    echo ""
    echo "⚠ IMPORTANT: You need to log out and back in for Docker"
    echo "  group permissions to take effect, OR run:"
    echo "  newgrp docker"
    echo ""
fi

echo ""
echo "Step 2: Pulling Roboflow Inference ARM CPU container..."
echo "This may take several minutes on first run..."
echo ""

# Pull the ARM-optimized inference server container
sudo docker pull roboflow/roboflow-inference-server-arm-cpu:latest

echo ""
echo "✓ Docker image pulled successfully"
echo ""

echo "Step 3: Testing Docker container..."
echo "Starting inference server on port 9001..."
echo ""

# Test if container starts (run for 10 seconds then stop)
CONTAINER_ID=$(sudo docker run -d -p 9001:9001 roboflow/roboflow-inference-server-arm-cpu:latest)

echo "Container started: $CONTAINER_ID"
echo "Waiting 10 seconds for server to initialize..."
sleep 10

# Check if container is running
if sudo docker ps | grep -q $CONTAINER_ID; then
    echo "✓ Inference server is running"

    # Test HTTP endpoint
    echo "Testing API endpoint..."
    if curl -s http://localhost:9001/ > /dev/null; then
        echo "✓ API endpoint is accessible"
    else
        echo "⚠ API endpoint test failed, but container is running"
    fi
else
    echo "✗ Container failed to start"
    echo "Checking logs:"
    sudo docker logs $CONTAINER_ID
    exit 1
fi

# Stop the test container
echo ""
echo "Stopping test container..."
sudo docker stop $CONTAINER_ID > /dev/null
sudo docker rm $CONTAINER_ID > /dev/null

echo ""
echo "======================================================"
echo "Docker and Roboflow Inference Setup Complete! ✓"
echo "======================================================"
echo ""
echo "The inference server container is ready."
echo ""
echo "To start the server manually:"
echo "  sudo docker run -d -p 9001:9001 \\"
echo "    --name roboflow-inference \\"
echo "    roboflow/roboflow-inference-server-arm-cpu:latest"
echo ""
echo "To stop the server:"
echo "  sudo docker stop roboflow-inference"
echo ""
echo "To view logs:"
echo "  sudo docker logs -f roboflow-inference"
echo ""
echo "The server will be available at: http://localhost:9001"
echo ""
echo "Next step: Modify app_pi.py to use InferenceHTTPClient"
echo "instead of InferencePipeline to connect to the Docker server."
echo ""
