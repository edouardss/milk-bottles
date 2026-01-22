#!/bin/bash

# Fix OpenCV installation for Raspberry Pi
# This script reinstalls OpenCV with the correct architecture

set -e

echo "======================================================"
echo "Fixing OpenCV Installation on Raspberry Pi"
echo "======================================================"
echo ""

# Detect architecture
ARCH=$(uname -m)
echo "Detected architecture: $ARCH"

if [ "$ARCH" = "armv7l" ]; then
    echo "32-bit Raspberry Pi OS detected"
    INSTALL_METHOD="apt"
elif [ "$ARCH" = "aarch64" ]; then
    echo "64-bit Raspberry Pi OS detected"
    INSTALL_METHOD="pip"
else
    echo "Unknown architecture: $ARCH"
    INSTALL_METHOD="pip"
fi

echo ""
echo "Step 1: Activating virtual environment..."
source venv/bin/activate

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "✗ ERROR: Virtual environment not activated"
    exit 1
fi
echo "✓ Virtual environment activated"

echo ""
echo "Step 2: Uninstalling existing OpenCV..."
pip uninstall -y opencv-python opencv-contrib-python opencv-python-headless 2>/dev/null || true

echo ""
if [ "$INSTALL_METHOD" = "apt" ]; then
    echo "Step 3: Installing OpenCV from apt (32-bit)..."
    echo "This uses the system OpenCV which is pre-compiled for 32-bit ARM"

    # Install system OpenCV
    sudo apt install -y python3-opencv

    # Create symlink in venv to use system OpenCV
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    SITE_PACKAGES="venv/lib/python${PYTHON_VERSION}/site-packages"

    mkdir -p "$SITE_PACKAGES"

    # Find system cv2.so
    SYSTEM_CV2=$(find /usr/lib -name "cv2*.so" 2>/dev/null | head -1)

    if [ -n "$SYSTEM_CV2" ]; then
        ln -sf "$SYSTEM_CV2" "$SITE_PACKAGES/"
        echo "✓ Linked system OpenCV to venv"
    else
        echo "⚠ Could not find system cv2.so, trying pip install..."
        pip install opencv-python==4.5.3.56
    fi
else
    echo "Step 3: Installing OpenCV from pip (64-bit)..."

    # First try installing numpy with specific build flags for ARM
    echo "Installing numpy optimized for ARM..."
    pip install --no-cache-dir numpy

    # Install opencv-python-headless (lighter, no GUI dependencies)
    # This version tends to work better on ARM systems
    echo "Installing opencv-python-headless (recommended for headless servers)..."
    pip install --no-cache-dir opencv-python-headless

    echo "✓ OpenCV headless installed"
fi

echo ""
echo "Step 4: Testing OpenCV installation..."
python << EOF
import sys
try:
    import cv2
    print(f"✓ OpenCV {cv2.__version__} imported successfully")
    print(f"  Location: {cv2.__file__}")

    # Test basic functionality
    import numpy as np
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    print("✓ NumPy arrays working")

    # Try to create a VideoCapture object (don't open camera yet)
    cap = cv2.VideoCapture()
    print("✓ VideoCapture object created")

    print("")
    print("OpenCV is working correctly!")
    sys.exit(0)
except Exception as e:
    print(f"✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "OpenCV Fix Complete! ✓"
    echo "======================================================"
    echo ""
    echo "You can now run the application:"
    echo "  python app_pi.py"
    echo ""
else
    echo ""
    echo "======================================================"
    echo "OpenCV Fix Failed"
    echo "======================================================"
    echo ""
    echo "Please try manually:"
    echo "  1. Deactivate venv: deactivate"
    echo "  2. Remove venv: rm -rf venv"
    echo "  3. Recreate venv: python3 -m venv venv"
    echo "  4. Run setup again: ./setup_pi.sh"
    echo ""
    exit 1
fi

deactivate 2>/dev/null || true
