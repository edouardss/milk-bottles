#!/bin/bash

# Update camera server on Pi with new resolution settings

set -e

PI_HOST="edss@edsspi3.local"
REPO_DIR="milk-bottles"

echo "======================================================"
echo "Updating Camera Server on Pi"
echo "======================================================"
echo ""

echo "Step 1: Copying updated camera_server_pi.py to Pi..."
scp camera_server_pi.py ${PI_HOST}:~/${REPO_DIR}/

echo ""
echo "Step 2: Restarting camera server..."
ssh ${PI_HOST} << 'ENDSSH'
# Kill existing camera server
pkill -f camera_server_pi.py || true
sleep 1

# Start new camera server
cd ~/milk-bottles
source venv_camera/bin/activate
nohup python camera_server_pi.py > camera_server.log 2>&1 &

# Wait a moment
sleep 2

# Check if it's running
if pgrep -f camera_server_pi.py > /dev/null; then
    echo "✓ Camera server restarted successfully"
    echo "  New resolution: 1280x720"
    echo "  JPEG quality: 85%"
else
    echo "✗ Failed to restart camera server"
    exit 1
fi
ENDSSH

echo ""
echo "======================================================"
echo "Camera Server Updated!"
echo "======================================================"
echo ""
echo "Access from Mac: http://edsspi3.local:8888"
echo ""
