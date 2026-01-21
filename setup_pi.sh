#!/bin/bash

# Raspberry Pi 4 Setup Script for Milk Bottle Monitoring System
# This script installs all dependencies and prepares the system

echo "======================================================"
echo "Raspberry Pi 4 - Milk Bottle Monitoring Setup"
echo "======================================================"
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "WARNING: This script is designed for Raspberry Pi"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "Step 1: Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo ""
echo "Step 2: Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
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
    libqt5test5

echo ""
echo "Step 3: Upgrading pip..."
python3 -m pip install --upgrade pip

echo ""
echo "Step 4: Installing Python packages from requirements_pi.txt..."
python3 -m pip install -r requirements_pi.txt

echo ""
echo "Step 5: Checking webcam availability..."
if ls /dev/video* 1> /dev/null 2>&1; then
    echo "✓ Webcam detected:"
    ls -l /dev/video*
else
    echo "⚠ WARNING: No webcam detected at /dev/video*"
    echo "  Please connect a USB webcam and run 'ls /dev/video*' to verify"
fi

echo ""
echo "Step 6: Creating config.env file (if not exists)..."
if [ ! -f config.env ]; then
    echo "Creating config.env from template..."
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
else
    echo "✓ config.env already exists"
fi

echo ""
echo "Step 7: Testing camera access..."
python3 << EOF
import cv2
print("Attempting to open camera...")
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera opened successfully")
    ret, frame = cap.read()
    if ret:
        print(f"✓ Frame captured: {frame.shape[1]}x{frame.shape[0]}")
    else:
        print("⚠ WARNING: Could not read frame from camera")
    cap.release()
else:
    print("✗ ERROR: Could not open camera")
EOF

echo ""
echo "======================================================"
echo "Setup Complete!"
echo "======================================================"
echo ""
echo "Next Steps:"
echo "1. Edit config.env and add your ROBOFLOW_API_KEY"
echo "2. Run the application:"
echo "   python3 app_pi.py"
echo ""
echo "3. Access the dashboard from any device on your network:"
echo "   http://$(hostname -I | awk '{print $1}'):5050"
echo ""
echo "Optional: Set up auto-start on boot"
echo "  sudo nano /etc/systemd/system/milk-monitor.service"
echo ""
echo "For troubleshooting, check:"
echo "  - Camera: ls /dev/video*"
echo "  - Network: ifconfig"
echo "  - Logs: Check terminal output when running app_pi.py"
echo "======================================================"
