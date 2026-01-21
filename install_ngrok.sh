#!/bin/bash

# Install and configure ngrok on Raspberry Pi
# This script sets up ngrok to provide public URL access to the dashboard

set -e  # Exit on error

echo "======================================================"
echo "Installing ngrok on Raspberry Pi"
echo "======================================================"
echo ""

# Configuration
NGROK_VERSION="v3"
ARCH="arm64"  # Use arm64 for 64-bit Pi OS, or arm for 32-bit

# Detect architecture
if [ "$(uname -m)" = "aarch64" ]; then
    ARCH="arm64"
elif [ "$(uname -m)" = "armv7l" ]; then
    ARCH="arm"
else
    echo "⚠ WARNING: Unknown architecture $(uname -m), defaulting to arm64"
    ARCH="arm64"
fi

echo "Detected architecture: $ARCH"
echo ""

# Check if ngrok is already installed
if command -v ngrok &> /dev/null; then
    echo "✓ ngrok is already installed"
    ngrok version
    read -p "Reinstall ngrok? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Skipping ngrok installation"
        SKIP_INSTALL=true
    fi
fi

if [ "$SKIP_INSTALL" != "true" ]; then
    echo "Step 1: Downloading ngrok for Linux ARM ($ARCH)..."
    NGROK_URL="https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-${NGROK_VERSION}-stable-linux-${ARCH}.tgz"

    wget -O /tmp/ngrok.tgz "$NGROK_URL"

    if [ $? -eq 0 ]; then
        echo "✓ Download complete"
    else
        echo "✗ ERROR: Failed to download ngrok"
        exit 1
    fi

    echo ""
    echo "Step 2: Extracting ngrok..."
    tar xvzf /tmp/ngrok.tgz -C /tmp/

    echo ""
    echo "Step 3: Installing ngrok to /usr/local/bin..."
    sudo mv /tmp/ngrok /usr/local/bin/
    sudo chmod +x /usr/local/bin/ngrok

    echo "✓ ngrok installed"
    ngrok version

    # Cleanup
    rm -f /tmp/ngrok.tgz
fi

echo ""
echo "Step 4: Configuring ngrok authentication..."

# Check if config.env exists
if [ ! -f config.env ]; then
    echo "✗ ERROR: config.env not found"
    echo "  Please create config.env with your NGROK_AUTH_TOKEN"
    exit 1
fi

# Load NGROK_AUTH_TOKEN from config.env
source config.env

if [ -z "$NGROK_AUTH_TOKEN" ] || [ "$NGROK_AUTH_TOKEN" = "YOUR_NGROK_TOKEN_HERE" ]; then
    echo "✗ ERROR: NGROK_AUTH_TOKEN not set in config.env"
    echo ""
    echo "Please add your ngrok auth token to config.env:"
    echo "  NGROK_AUTH_TOKEN=your_token_here"
    echo ""
    echo "Get your token at: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

# Configure ngrok with auth token
ngrok config add-authtoken "$NGROK_AUTH_TOKEN"

if [ $? -eq 0 ]; then
    echo "✓ ngrok authentication configured"
else
    echo "✗ ERROR: Failed to configure ngrok authentication"
    exit 1
fi

echo ""
echo "Step 5: Testing ngrok..."
ngrok config check

if [ $? -eq 0 ]; then
    echo "✓ ngrok configuration is valid"
else
    echo "⚠ WARNING: ngrok configuration check failed"
fi

echo ""
echo "======================================================"
echo "ngrok Installation Complete!"
echo "======================================================"
echo ""
echo "To start ngrok manually:"
echo "  ngrok http 5050"
echo ""
echo "To set up ngrok as a service (auto-start on boot):"
echo "  sudo ./install_ngrok_service.sh"
echo ""
echo "======================================================"
