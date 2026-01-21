#!/bin/bash

# Raspberry Pi 4 Setup Script for Milk Bottle Monitoring System
# This script installs all dependencies and prepares the system

set -e  # Exit on error

echo "======================================================"
echo "Raspberry Pi 4 - Milk Bottle Monitoring Setup"
echo "======================================================"
echo ""

# Configuration
VENV_NAME="venv"
PYTHON_CMD="python3"

# Check if running on Raspberry Pi
if [ -f /proc/device-tree/model ]; then
    PI_MODEL=$(cat /proc/device-tree/model)
    echo "Detected: $PI_MODEL"
else
    echo "WARNING: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    python3-opencv \
    libatlas-base-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk-3-dev \
    libcanberra-gtk3-module \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    libjasper-dev \
    libqt5gui5 \
    libqt5webkit5 \
    libqt5test5 \
    git

echo ""
echo "Step 3: Creating Python virtual environment..."
if [ -d "${VENV_NAME}" ]; then
    echo "Virtual environment already exists at ${VENV_NAME}"
    read -p "Recreate it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf ${VENV_NAME}
        ${PYTHON_CMD} -m venv ${VENV_NAME}
        echo "✓ Virtual environment recreated"
    else
        echo "Using existing virtual environment"
    fi
else
    ${PYTHON_CMD} -m venv ${VENV_NAME}
    echo "✓ Virtual environment created at ${VENV_NAME}"
fi

echo ""
echo "Step 4: Activating virtual environment and upgrading pip..."
source ${VENV_NAME}/bin/activate

# Verify we're in the virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ Virtual environment activated: $VIRTUAL_ENV"
else
    echo "✗ ERROR: Failed to activate virtual environment"
    exit 1
fi

pip install --upgrade pip

echo ""
echo "Step 5: Installing Python packages into venv..."
echo "Installing to: $(which python)"
pip install -r requirements_pi.txt

echo ""
echo "Step 6: Checking webcam availability..."
if ls /dev/video* 1> /dev/null 2>&1; then
    echo "✓ Webcam detected:"
    ls -l /dev/video*
else
    echo "⚠ WARNING: No webcam detected at /dev/video*"
    echo "  Please connect a USB webcam and run 'ls /dev/video*' to verify"
fi

echo ""
echo "Step 7: Checking config.env file..."
if [ ! -f config.env ]; then
    echo "⚠ config.env not found"
    if [ -f config.env.example ]; then
        echo "Creating config.env from config.env.example..."
        cp config.env.example config.env
        echo "✓ Created config.env - PLEASE EDIT IT WITH YOUR ROBOFLOW_API_KEY"
        echo ""
        echo "Edit now? (y/n)"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            nano config.env
        fi
    else
        echo "Creating new config.env..."
        cat > config.env << EOF
# Roboflow API Configuration
ROBOFLOW_API_KEY=YOUR_API_KEY_HERE

# Optional: Twilio SMS (not used in Pi version)
TWILIO_AUTH_TOKEN=
TWILIO_ACCOUNT_SID=
TWILIO_API_KEY_SID=
TWILIO_FROM_NUMBER=
TWILIO_TO_NUMBER=
EOF
        echo "✓ Created config.env - PLEASE EDIT IT WITH YOUR ROBOFLOW_API_KEY"
    fi
else
    echo "✓ config.env already exists"

    # Check if API key is set
    if grep -q "YOUR_API_KEY_HERE" config.env; then
        echo "⚠ WARNING: ROBOFLOW_API_KEY not set in config.env"
        echo "  Please edit config.env and add your API key"
    else
        echo "✓ ROBOFLOW_API_KEY appears to be configured"
    fi
fi

echo ""
echo "Step 8: Testing camera access with venv Python..."
${VENV_NAME}/bin/python << EOF
import cv2
import sys
print("Attempting to open camera...")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera opened successfully")
    ret, frame = cap.read()
    if ret:
        print(f"✓ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("⚠ WARNING: Could not read frame from camera")
        sys.exit(1)
    cap.release()
else:
    print("✗ ERROR: Could not open camera")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo "✓ Camera test passed"
else
    echo "⚠ Camera test failed (non-critical, may work when app runs)"
fi

echo ""
echo "======================================================"
echo "Setup Complete!"
echo "======================================================"
echo ""
echo "Virtual environment created at: ${VENV_NAME}"
echo ""
echo "To activate the virtual environment:"
echo "  source ${VENV_NAME}/bin/activate"
echo ""
echo "To run the application:"
echo "  source ${VENV_NAME}/bin/activate"
echo "  python app_pi.py"
echo ""
echo "Or run directly:"
echo "  ${VENV_NAME}/bin/python app_pi.py"
echo ""
echo "Access the dashboard at:"
echo "  http://$(hostname -I | awk '{print $1}'):5050"
echo "  http://$(hostname).local:5050"
echo ""
echo "For auto-start on boot, run:"
echo "  sudo ./install_service.sh"
echo ""
echo "======================================================"

deactivate 2>/dev/null || true
