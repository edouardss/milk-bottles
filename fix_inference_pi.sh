#!/bin/bash

# Fix inference package on Raspberry Pi by reinstalling with compatible dependencies

set -e

echo "======================================================"
echo "Fixing Roboflow Inference Package on Raspberry Pi"
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

echo "Step 1: Uninstalling inference and related packages..."
pip uninstall -y inference inference-sdk inference-cli inference-gpu onnxruntime onnxruntime-gpu 2>/dev/null || true

echo ""
echo "Step 2: Installing compatible ONNX runtime for ARM64..."
# ONNX runtime is often the culprit for illegal instruction on ARM
pip install --no-cache-dir onnxruntime==1.16.3

echo ""
echo "Step 3: Reinstalling inference package..."
pip install --no-cache-dir inference>=0.9.0

echo ""
echo "Step 4: Testing inference import..."
python << EOF
import sys
try:
    print("Testing inference import...")
    from inference import InferencePipeline
    print("✓ InferencePipeline imported successfully!")
    sys.exit(0)
except Exception as e:
    print(f"✗ Import still failing: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================================"
    echo "Inference Fix Complete! ✓"
    echo "======================================================"
    echo ""
    echo "You can now run the application:"
    echo "  python app_pi.py"
    echo ""
else
    echo ""
    echo "======================================================"
    echo "Fix Failed - Alternative Approach Needed"
    echo "======================================================"
    echo ""
    echo "The inference package may not be compatible with your"
    echo "Raspberry Pi's CPU. Consider:"
    echo ""
    echo "1. Use a different Raspberry Pi OS version"
    echo "2. Contact Roboflow support about ARM64 compatibility"
    echo "3. Use a different deployment platform"
    echo ""
    exit 1
fi

deactivate 2>/dev/null || true
