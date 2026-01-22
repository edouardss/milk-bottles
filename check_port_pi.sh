#!/bin/bash

# Check what's using port 9001 on Raspberry Pi

echo "======================================================"
echo "Checking Port 9001 Usage"
echo "======================================================"
echo ""

echo "Checking if port 9001 is in use..."
echo ""

# Check with netstat
if command -v netstat &> /dev/null; then
    echo "Using netstat:"
    sudo netstat -tlnp | grep :9001 || echo "No process found using port 9001"
    echo ""
fi

# Check with ss (more modern)
if command -v ss &> /dev/null; then
    echo "Using ss:"
    sudo ss -tlnp | grep :9001 || echo "No process found using port 9001"
    echo ""
fi

# Check with lsof
if command -v lsof &> /dev/null; then
    echo "Using lsof:"
    sudo lsof -i :9001 || echo "No process found using port 9001"
    echo ""
fi

# Check Docker containers
echo "Checking Docker containers:"
if command -v docker &> /dev/null; then
    sudo docker ps -a | grep -E "(CONTAINER|9001)" || echo "No Docker containers found"
else
    echo "Docker not installed"
fi

echo ""
echo "======================================================"
echo "Checking for Viam processes:"
echo "======================================================"
ps aux | grep -i viam | grep -v grep || echo "No Viam processes found"

echo ""
echo "======================================================"
echo "Alternative Ports Available:"
echo "======================================================"
echo ""
echo "If port 9001 is in use by Viam, we can use a different port"
echo "for Roboflow Inference, such as:"
echo "  - 9002"
echo "  - 9003"
echo "  - 8001"
echo ""
echo "To use a different port, we'll update:"
echo "  1. Docker container port mapping"
echo "  2. INFERENCE_SERVER_URL in config.env"
echo ""
