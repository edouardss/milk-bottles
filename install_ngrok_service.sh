#!/bin/bash

# Install ngrok as a systemd service for auto-start on boot
# Run this script with: sudo ./install_ngrok_service.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo ./install_ngrok_service.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)
PROJECT_DIR="$USER_HOME/milk-bottles"

echo "======================================================"
echo "Installing ngrok Service"
echo "======================================================"
echo ""
echo "Configuration:"
echo "  User: $ACTUAL_USER"
echo "  Project: $PROJECT_DIR"
echo ""

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "✗ ERROR: ngrok is not installed"
    echo "  Please run ./install_ngrok.sh first"
    exit 1
fi

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "✗ ERROR: Project directory not found at $PROJECT_DIR"
    exit 1
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/ngrok.service"

echo "Creating service file at $SERVICE_FILE..."

cat > $SERVICE_FILE << EOF
[Unit]
Description=ngrok tunnel service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/local/bin/ngrok http 5050 --log=stdout
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo "✓ Service file created"

echo ""
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo ""
echo "Enabling service to start on boot..."
systemctl enable ngrok.service

echo ""
echo "======================================================"
echo "ngrok Service Installation Complete!"
echo "======================================================"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start ngrok"
echo "  Stop:    sudo systemctl stop ngrok"
echo "  Restart: sudo systemctl restart ngrok"
echo "  Status:  sudo systemctl status ngrok"
echo "  Logs:    sudo journalctl -u ngrok -f"
echo ""
echo "To get the ngrok public URL:"
echo "  curl http://localhost:4040/api/tunnels"
echo ""
echo "Or visit: http://localhost:4040"
echo ""
echo "The service will automatically start on boot."
echo ""
read -p "Start the ngrok service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start ngrok.service
    echo ""
    echo "Service started. Waiting 3 seconds for ngrok to initialize..."
    sleep 3

    echo ""
    echo "Checking ngrok status..."
    systemctl status ngrok.service --no-pager

    echo ""
    echo "Fetching public URL..."
    sleep 1

    # Try to get the public URL
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"[^"]*"' | grep https | cut -d'"' -f4 | head -1)

    if [ -n "$PUBLIC_URL" ]; then
        echo ""
        echo "======================================================"
        echo "🌐 Your public URL is ready!"
        echo "======================================================"
        echo ""
        echo "  $PUBLIC_URL"
        echo ""
        echo "Share this URL to access your dashboard from anywhere!"
        echo "======================================================"
    else
        echo ""
        echo "⚠ Could not retrieve public URL automatically"
        echo "  Visit http://localhost:4040 to see your ngrok dashboard"
    fi
fi
echo ""
echo "======================================================"
