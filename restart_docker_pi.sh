#!/bin/bash

# Clean up and restart Roboflow Inference Docker container on Pi

echo "======================================================"
echo "Restarting Roboflow Inference Docker Container"
echo "======================================================"
echo ""

echo "Step 1: Stopping and removing any existing inference containers..."

# Stop and remove any containers using the inference image
sudo docker ps -a | grep roboflow-inference | awk '{print $1}' | xargs -r sudo docker stop 2>/dev/null || true
sudo docker ps -a | grep roboflow-inference | awk '{print $1}' | xargs -r sudo docker rm 2>/dev/null || true

# Also check for any other containers using port 9001
echo "Checking for processes using port 9001..."
CONTAINER_ON_PORT=$(sudo docker ps --filter "publish=9001" -q)
if [ ! -z "$CONTAINER_ON_PORT" ]; then
    echo "Found container using port 9001: $CONTAINER_ON_PORT"
    sudo docker stop $CONTAINER_ON_PORT
    sudo docker rm $CONTAINER_ON_PORT
fi

echo "✓ Cleaned up old containers"

echo ""
echo "Step 2: Starting fresh Roboflow Inference container..."

sudo docker run -d \
    --name roboflow-inference \
    --restart unless-stopped \
    -p 9001:9001 \
    roboflow/roboflow-inference-server-arm-cpu:latest

echo ""
echo "Step 3: Waiting for container to start..."
sleep 5

echo ""
echo "Step 4: Checking container status..."

if sudo docker ps | grep -q roboflow-inference; then
    echo "✓ Container is running"
    echo ""
    sudo docker ps | grep roboflow-inference

    echo ""
    echo "Testing API endpoint..."
    sleep 3

    if curl -s http://localhost:9001/ > /dev/null 2>&1; then
        echo "✓ API is responding at http://localhost:9001"
    else
        echo "⚠ API not responding yet, may need more time to initialize"
        echo "  Check logs with: sudo docker logs roboflow-inference"
    fi

    echo ""
    echo "======================================================"
    echo "Roboflow Inference Server is Running! ✓"
    echo "======================================================"
    echo ""
    echo "You can now run the application:"
    echo "  cd ~/milk-bottles"
    echo "  source venv/bin/activate"
    echo "  python app_pi_docker.py"
    echo ""

else
    echo "✗ Container failed to start"
    echo ""
    echo "Checking logs:"
    sudo docker logs roboflow-inference
    exit 1
fi
