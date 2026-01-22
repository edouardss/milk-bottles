#!/bin/bash

# Deploy Milk Bottle Monitoring to Raspberry Pi using Docker-based Inference
# This is the RECOMMENDED approach for ARM compatibility

PI_HOST="edsspi3.local"
PI_USER="edss"
PROJECT_DIR="milk-bottles"
REPO_URL="https://github.com/edouardss/milk-bottles.git"

echo "======================================================"
echo "Deploying to Raspberry Pi with Docker Inference"
echo "======================================================"
echo ""
echo "Target: ${PI_USER}@${PI_HOST}"
echo "This will use Docker for ARM-compatible inference"
echo ""

# Test SSH connection
echo "Step 1: Testing SSH connection..."
if ssh -o ConnectTimeout=5 ${PI_USER}@${PI_HOST} "echo 'SSH connection successful'" 2>/dev/null; then
    echo "✓ SSH connection successful"
else
    echo "✗ ERROR: Cannot connect to ${PI_HOST}"
    echo "  Make sure your Pi is powered on and connected to the network"
    exit 1
fi

echo ""
echo "Step 2: Cloning repository to Pi..."
ssh ${PI_USER}@${PI_HOST} << ENDSSH
# Remove old directory if it exists
if [ -d "${PROJECT_DIR}" ]; then
    echo "Removing existing ${PROJECT_DIR} directory..."
    rm -rf ${PROJECT_DIR}
fi

# Clone repository
echo "Cloning from GitHub..."
git clone ${REPO_URL} ${PROJECT_DIR}

if [ -d "${PROJECT_DIR}" ]; then
    echo "✓ Repository cloned successfully"
else
    echo "✗ Failed to clone repository"
    exit 1
fi
ENDSSH

echo ""
echo "Step 3: Copying config.env to Pi..."
if [ -f "config.env" ]; then
    scp config.env ${PI_USER}@${PI_HOST}:~/${PROJECT_DIR}/
    echo "✓ config.env copied"
else
    echo "⚠ config.env not found locally - you'll need to create it on the Pi"
fi

echo ""
echo "Step 4: Installing Docker on Pi..."
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/milk-bottles
chmod +x setup_docker_pi.sh
./setup_docker_pi.sh
ENDSSH

echo ""
echo "Step 5: Setting up Python environment..."
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
cd ~/milk-bottles

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install packages
source venv/bin/activate

echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements_pi_docker.txt

echo "✓ Python packages installed"
ENDSSH

echo ""
echo "Step 6: Starting Roboflow Inference Docker container..."
ssh ${PI_USER}@${PI_HOST} << 'ENDSSH'
# Stop any existing inference container
sudo docker stop roboflow-inference 2>/dev/null || true
sudo docker rm roboflow-inference 2>/dev/null || true

# Start new container
echo "Starting Roboflow Inference Server..."
sudo docker run -d \
    --name roboflow-inference \
    --restart unless-stopped \
    -p 9001:9001 \
    roboflow/roboflow-inference-server-arm-cpu:latest

# Wait for container to start
sleep 5

# Check if running
if sudo docker ps | grep -q roboflow-inference; then
    echo "✓ Inference server is running on port 9001"
else
    echo "✗ Failed to start inference server"
    echo "Checking logs:"
    sudo docker logs roboflow-inference
    exit 1
fi
ENDSSH

echo ""
echo "======================================================"
echo "Deployment Complete! ✓"
echo "======================================================"
echo ""
echo "Docker Inference Server: Running on port 9001"
echo "Flask Application: Ready to start"
echo ""
echo "To start the application:"
echo "  ssh ${PI_USER}@${PI_HOST}"
echo "  cd ~/${PROJECT_DIR}"
echo "  source venv/bin/activate"
echo "  python app_pi_docker.py"
echo ""
echo "Then access the dashboard at:"
echo "  http://${PI_HOST}:5050"
echo ""
echo "To check Docker container status:"
echo "  ssh ${PI_USER}@${PI_HOST} 'sudo docker ps'"
echo ""
echo "To view Docker logs:"
echo "  ssh ${PI_USER}@${PI_HOST} 'sudo docker logs -f roboflow-inference'"
echo ""
