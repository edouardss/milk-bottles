#!/bin/bash

# Deploy Milk Bottle Monitoring System to Raspberry Pi
# This script clones the repo and sets up everything in a virtual environment

set -e  # Exit on error

echo "======================================================"
echo "Deploying Milk Bottle Monitor to Raspberry Pi"
echo "======================================================"
echo ""

# Configuration
PI_HOST="edsspi3.local"
PI_USER="edss"
PROJECT_DIR="milk-bottles"
REPO_URL="https://github.com/edouardss/milk-bottles.git"
VENV_NAME="venv"

echo "Configuration:"
echo "  Host: ${PI_HOST}"
echo "  User: ${PI_USER}"
echo "  Project: ~/${PROJECT_DIR}"
echo "  Repository: ${REPO_URL}"
echo ""

# Check if we can reach the Pi
echo "Step 1: Testing connection to Raspberry Pi..."
if ping -c 1 -W 2 ${PI_HOST} > /dev/null 2>&1; then
    echo "✓ Raspberry Pi is reachable at ${PI_HOST}"
else
    echo "⚠ WARNING: Cannot ping ${PI_HOST}"
    echo "  Trying to continue anyway..."
fi

echo ""
echo "Step 2: Checking if project already exists on Pi..."
if ssh ${PI_USER}@${PI_HOST} "test -d ${PROJECT_DIR}"; then
    echo "✓ Project directory exists"
    echo ""
    read -p "Project already exists. Update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Updating repository..."
        ssh ${PI_USER}@${PI_HOST} "cd ${PROJECT_DIR} && git pull"
        echo "✓ Repository updated"
    else
        echo "Skipping git pull"
    fi
else
    echo "Project directory does not exist. Cloning repository..."
    ssh ${PI_USER}@${PI_HOST} "git clone ${REPO_URL} ${PROJECT_DIR}"
    if [ $? -eq 0 ]; then
        echo "✓ Repository cloned successfully"
    else
        echo "✗ ERROR: Failed to clone repository"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Make sure Git is installed on Pi: sudo apt install git"
        echo "  2. Check network connection on Pi"
        echo "  3. Verify repository URL: ${REPO_URL}"
        exit 1
    fi
fi

echo ""
echo "Step 3: Checking for config.env..."
if ssh ${PI_USER}@${PI_HOST} "test -f ${PROJECT_DIR}/config.env"; then
    echo "✓ config.env exists on Pi"
else
    echo "⚠ config.env not found on Pi"
    echo ""
    read -p "Copy your local config.env to Pi? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f config.env ]; then
            scp config.env ${PI_USER}@${PI_HOST}:${PROJECT_DIR}/
            echo "✓ config.env copied to Pi"
        else
            echo "✗ ERROR: config.env not found locally"
            echo "  You'll need to create it manually on the Pi"
        fi
    else
        echo "⚠ Remember to create config.env on the Pi before running the app"
    fi
fi

echo ""
echo "Step 4: Running setup script on Pi..."
echo "This will install dependencies and set up virtual environment..."
ssh ${PI_USER}@${PI_HOST} "cd ${PROJECT_DIR} && chmod +x setup_pi.sh && ./setup_pi.sh"

if [ $? -eq 0 ]; then
    echo "✓ Setup completed successfully"
else
    echo "✗ ERROR: Setup failed"
    exit 1
fi

echo ""
echo "Step 5: Installing ngrok (optional)..."
read -p "Install ngrok for public URL access? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing ngrok on Pi..."
    ssh ${PI_USER}@${PI_HOST} "cd ${PROJECT_DIR} && chmod +x install_ngrok.sh && ./install_ngrok.sh"

    if [ $? -eq 0 ]; then
        echo "✓ ngrok installed successfully"

        echo ""
        read -p "Set up ngrok as auto-start service? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            ssh ${PI_USER}@${PI_HOST} "cd ${PROJECT_DIR} && chmod +x install_ngrok_service.sh && sudo ./install_ngrok_service.sh"
            echo "✓ ngrok service configured"
        fi
    else
        echo "⚠ ngrok installation failed (non-critical)"
    fi
else
    echo "Skipping ngrok installation"
fi

echo ""
echo "======================================================"
echo "Deployment Complete! ✓"
echo "======================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. SSH into your Raspberry Pi:"
echo "   ssh ${PI_USER}@${PI_HOST}"
echo ""
echo "2. Navigate to the project:"
echo "   cd ${PROJECT_DIR}"
echo ""
echo "3. Start the application:"
echo "   ${VENV_NAME}/bin/python app_pi.py"
echo ""
echo "4. Access the dashboard:"
echo "   Local:  http://${PI_HOST}:5050"
if command -v curl &> /dev/null; then
    NGROK_RUNNING=$(ssh ${PI_USER}@${PI_HOST} "curl -s http://localhost:4040/api/tunnels 2>/dev/null" | grep -o '"public_url":"[^"]*"' | grep https | cut -d'"' -f4 | head -1)
    if [ -n "$NGROK_RUNNING" ]; then
        echo "   Public: $NGROK_RUNNING"
    fi
fi
echo ""
echo "======================================================"
echo ""
echo "Optional: Set up auto-start services"
echo "   ssh ${PI_USER}@${PI_HOST}"
echo "   cd ${PROJECT_DIR}"
echo "   sudo ./install_service.sh        # App auto-start"
echo "   sudo ./install_ngrok_service.sh  # ngrok auto-start"
echo ""
echo "======================================================"
