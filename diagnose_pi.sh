#!/bin/bash

# Diagnostic script to identify which package is causing "Illegal instruction"

echo "======================================================"
echo "Diagnosing Illegal Instruction Error"
echo "======================================================"
echo ""

source venv/bin/activate

echo "System Information:"
echo "  Architecture: $(uname -m)"
echo "  OS: $(cat /etc/os-release | grep PRETTY_NAME)"
echo "  Python: $(python --version)"
echo ""

echo "Testing imports one by one..."
echo ""

# Test each package individually
packages=(
    "sys"
    "os"
    "flask"
    "dotenv"
    "csv"
    "time"
    "datetime"
    "threading"
    "numpy"
    "cv2"
    "inference"
)

for pkg in "${packages[@]}"; do
    echo -n "Testing $pkg... "
    python -c "import $pkg; print('✓ OK')" 2>&1 | grep -q "✓ OK"
    if [ $? -eq 0 ]; then
        python -c "import $pkg; print('✓ OK')"
    else
        echo "✗ FAILED"
        python -c "import $pkg" 2>&1
        echo ""
        echo "Found the problem: $pkg is causing the illegal instruction error"
        echo ""

        # Get package info
        pip show $pkg 2>/dev/null || echo "Package $pkg not installed via pip"
        exit 1
    fi
done

echo ""
echo "All packages imported successfully!"
echo ""
echo "Testing numpy operations..."
python << EOF
import numpy as np
import sys

try:
    # Test basic operations
    a = np.array([1, 2, 3])
    b = np.dot(a, a)
    print(f"✓ Numpy operations work: dot product = {b}")

    # Test BLAS operations (often causes issues on ARM)
    x = np.random.rand(100, 100)
    y = np.random.rand(100, 100)
    z = np.dot(x, y)
    print(f"✓ Matrix multiplication works")

except Exception as e:
    print(f"✗ Numpy operation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
EOF

echo ""
echo "======================================================"
echo "Diagnostics Complete"
echo "======================================================"

deactivate 2>/dev/null || true
