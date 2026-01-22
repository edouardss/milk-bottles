#!/bin/bash

# Setup Raspberry Pi as simple camera server
# This runs on the Pi and streams video to your Mac

set -e

echo "======================================================"
echo "Setting up Pi Camera Server"
echo "======================================================"
echo ""

echo "Step 1: Creating virtual environment..."
if [ ! -d "venv_camera" ]; then
    python3 -m venv venv_camera
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

echo ""
echo "Step 2: Activating virtual environment..."
source venv_camera/bin/activate

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "✗ ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"

echo ""
echo "Step 3: Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_pi_camera.txt

echo ""
echo "Step 4: Testing camera..."
python << 'EOF'
import cv2
import sys

cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✓ Camera detected and accessible")
    ret, frame = cap.read()
    if ret:
        print(f"✓ Camera resolution: {frame.shape[1]}x{frame.shape[0]}")
    cap.release()
else:
    print("✗ ERROR: Cannot access camera")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "Camera test failed. Check:"
    echo "  1. Is camera connected?"
    echo "  2. Run: ls /dev/video*"
    echo "  3. Try: vcgencmd get_camera"
    exit 1
fi

echo ""
echo "======================================================"
echo "Pi Camera Server Setup Complete! ✓"
echo "======================================================"
echo ""
echo "To start the camera server:"
echo "  source venv_camera/bin/activate"
echo "  python camera_server_pi.py"
echo ""
echo "The server will run on port 8888"
echo "Your Mac will connect to: http://edsspi3.local:8888/video_feed"
echo ""

deactivate 2>/dev/null || true
