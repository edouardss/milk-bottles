#!/bin/bash

# Deploy snapshot capture tool to Pi

set -e

PI_HOST="edss@edsspi3.local"
REPO_DIR="milk-bottles"

echo "======================================================"
echo "Deploying Snapshot Capture Tool to Pi"
echo "======================================================"
echo ""

echo "Step 1: Copying script to Pi..."
scp capture_snapshots_pi.py ${PI_HOST}:~/${REPO_DIR}/

echo ""
echo "Step 2: Starting capture tool on Pi..."
ssh ${PI_HOST} << 'ENDSSH'
cd ~/milk-bottles
source venv_camera/bin/activate
echo "Starting snapshot capture server..."
echo "Access from your Mac: http://edsspi3.local:9000"
python capture_snapshots_pi.py
ENDSSH
