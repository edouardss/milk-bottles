#!/bin/bash

# Fix numpy on Raspberry Pi by installing ARM-compatible version
# The "Illegal instruction" error happens when numpy is compiled with
# CPU instructions that your ARM processor doesn't support

set -e

echo "======================================================"
echo "Fixing NumPy on Raspberry Pi"
echo "======================================================"
echo ""

echo "Activating virtual environment..."
source venv/bin/activate

if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "✗ ERROR: Virtual environment not activated"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

echo "Step 1: Uninstalling existing numpy and dependencies..."
pip uninstall -y numpy scipy pandas opencv-python-headless inference inference-sdk 2>/dev/null || true

echo ""
echo "Step 2: Installing system BLAS/LAPACK libraries..."
echo "These provide optimized math operations for ARM"
sudo apt update
sudo apt install -y libopenblas-dev libatlas-base-dev gfortran

echo ""
echo "Step 3: Installing numpy from piwheels (ARM-optimized)..."
# piwheels.org provides pre-compiled packages specifically for Raspberry Pi
# These are built without advanced CPU instructions that cause "Illegal instruction"
pip install --no-cache-dir --index-url https://www.piwheels.org/simple numpy

echo ""
echo "Step 4: Testing numpy..."
python << 'EOF'
import sys
try:
    print("Testing numpy import...")
    import numpy as np
    print(f"✓ NumPy {np.__version__} imported successfully")
    print(f"  Location: {np.__file__}")

    # Test basic operations
    a = np.array([1, 2, 3])
    b = np.dot(a, a)
    print(f"✓ Basic operations work: {b}")

    # Test matrix operations (often causes issues)
    x = np.random.rand(10, 10)
    y = np.random.rand(10, 10)
    z = np.dot(x, y)
    print("✓ Matrix operations work")

    sys.exit(0)
except Exception as e:
    print(f"✗ NumPy test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo ""
    echo "NumPy test failed. Trying alternative approach..."
    echo ""

    # Try installing older, more compatible version
    echo "Installing older numpy version known to work on ARM..."
    pip uninstall -y numpy
    pip install --no-cache-dir numpy==1.21.6

    python << 'EOF'
import sys
try:
    import numpy as np
    print(f"✓ NumPy {np.__version__} working")
    sys.exit(0)
except Exception as e:
    print(f"✗ Still failing: {e}")
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        echo ""
        echo "======================================================"
        echo "NumPy Fix Failed"
        echo "======================================================"
        echo ""
        echo "Your Raspberry Pi's CPU may not be compatible with"
        echo "any available numpy build. This can happen on older"
        echo "ARM processors."
        echo ""
        echo "Check your CPU:"
        echo "  cat /proc/cpuinfo | grep 'model name'"
        echo ""
        exit 1
    fi
fi

echo ""
echo "Step 5: Reinstalling opencv-python-headless..."
pip install --no-cache-dir --index-url https://www.piwheels.org/simple opencv-python-headless

echo ""
echo "Step 6: Reinstalling inference package..."
pip install --no-cache-dir inference>=0.9.0

echo ""
echo "Step 7: Testing full import chain..."
python << 'EOF'
import sys
try:
    print("Testing imports...")
    import numpy as np
    print(f"✓ NumPy {np.__version__}")

    import cv2
    print(f"✓ OpenCV {cv2.__version__}")

    from inference import InferencePipeline
    print("✓ InferencePipeline imported successfully!")

    print("")
    print("All imports successful!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "NumPy and Inference Fix Complete! ✓"
    echo "======================================================"
    echo ""
    echo "You can now run the application:"
    echo "  python app_pi.py"
    echo ""
else
    echo ""
    echo "======================================================"
    echo "Fix Failed - Inference Package Issue"
    echo "======================================================"
    echo ""
    echo "NumPy is now working, but the inference package may"
    echo "still have compatibility issues. Consider:"
    echo ""
    echo "1. Contact Roboflow support about ARM64 compatibility"
    echo "2. Use Roboflow HTTP API instead of InferencePipeline"
    echo "3. Use a different deployment platform"
    echo ""
    exit 1
fi

deactivate 2>/dev/null || true
