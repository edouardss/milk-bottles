#!/bin/bash

# Run the numpy fix on the Raspberry Pi remotely from your Mac

PI_HOST="edsspi3.local"
PI_USER="edss"
PROJECT_DIR="milk-bottles"

echo "======================================================"
echo "Running NumPy Fix on Raspberry Pi"
echo "======================================================"
echo ""

echo "Connecting to ${PI_USER}@${PI_HOST}..."
echo ""

ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/milk-bottles

echo "Pulling latest changes from GitHub..."
git pull

echo ""
echo "Making script executable..."
chmod +x fix_numpy_pi.sh

echo ""
echo "Running fix_numpy_pi.sh..."
./fix_numpy_pi.sh

echo ""
echo "======================================================"
echo "Fix complete! Try running the app:"
echo "  python app_pi.py"
echo "======================================================"
ENDSSH

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Fix completed successfully on the Pi!"
    echo ""
    echo "Next steps:"
    echo "1. SSH into your Pi: ssh ${PI_USER}@${PI_HOST}"
    echo "2. Navigate to project: cd ~/milk-bottles"
    echo "3. Activate venv: source venv/bin/activate"
    echo "4. Run the app: python app_pi.py"
    echo ""
else
    echo ""
    echo "✗ Fix failed. Please check the output above."
    echo ""
fi
