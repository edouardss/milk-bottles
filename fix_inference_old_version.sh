#!/bin/bash

# Try using an older version of inference package that might work on ARM

set -e

echo "======================================================"
echo "Trying Older Inference Package Version for ARM"
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

echo "Step 1: Uninstalling all packages..."
pip uninstall -y numpy scipy pandas opencv-python-headless opencv-python inference inference-sdk onnxruntime onnxruntime-gpu 2>/dev/null || true

echo ""
echo "Step 2: Installing ARM-optimized numpy..."
pip install --no-cache-dir "numpy==1.24.3"

echo ""
echo "Step 3: Installing compatible OpenCV..."
pip install --no-cache-dir "opencv-python-headless==4.8.1.78"

echo ""
echo "Step 4: Installing older inference package (0.9.10 - known to work on some ARM systems)..."
pip install --no-cache-dir "inference==0.9.10"

echo ""
echo "Step 5: Testing imports..."
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
    echo "Success! Older Inference Version Works! ✓"
    echo "======================================================"
    echo ""
    echo "You can now run the application:"
    echo "  python app_pi.py"
    echo ""
else
    echo ""
    echo "======================================================"
    echo "Inference Package Incompatible with ARM64"
    echo "======================================================"
    echo ""
    echo "The Roboflow inference package does not work on your"
    echo "Raspberry Pi's ARM64 processor, even with older versions."
    echo ""
    echo "SOLUTION: We need to use Roboflow's HTTP API instead"
    echo "of the InferencePipeline. This requires modifying app_pi.py"
    echo "to make direct HTTP requests to Roboflow's cloud API."
    echo ""
    echo "Would you like me to create an alternative version?"
    echo ""
    exit 1
fi

deactivate 2>/dev/null || true
