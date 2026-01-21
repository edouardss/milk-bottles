#!/bin/bash

# Install systemd service for auto-start on boot
# Run this script with: sudo ./install_service.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Please run with sudo: sudo ./install_service.sh"
    exit 1
fi

# Get the actual user (not root when using sudo)
ACTUAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$ACTUAL_USER)
PROJECT_DIR="$USER_HOME/milk-bottles"
VENV_PATH="$PROJECT_DIR/venv"

echo "======================================================"
echo "Installing Milk Bottle Monitor Service"
echo "======================================================"
echo ""
echo "Configuration:"
echo "  User: $ACTUAL_USER"
echo "  Project: $PROJECT_DIR"
echo "  Virtual Env: $VENV_PATH"
echo ""

# Check if project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "✗ ERROR: Project directory not found at $PROJECT_DIR"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "✗ ERROR: Virtual environment not found at $VENV_PATH"
    echo "  Please run ./setup_pi.sh first"
    exit 1
fi

# Create systemd service file
SERVICE_FILE="/etc/systemd/system/milk-monitor.service"

echo "Creating service file at $SERVICE_FILE..."

cat > $SERVICE_FILE << EOF
[Unit]
Description=Milk Bottle Monitoring Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$ACTUAL_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin"
ExecStart=$VENV_PATH/bin/python $PROJECT_DIR/app_pi.py
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
systemctl enable milk-monitor.service

echo ""
echo "======================================================"
echo "Service Installation Complete!"
echo "======================================================"
echo ""
echo "Service commands:"
echo "  Start:   sudo systemctl start milk-monitor"
echo "  Stop:    sudo systemctl stop milk-monitor"
echo "  Restart: sudo systemctl restart milk-monitor"
echo "  Status:  sudo systemctl status milk-monitor"
echo "  Logs:    sudo journalctl -u milk-monitor -f"
echo ""
echo "The service will automatically start on boot."
echo ""
read -p "Start the service now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    systemctl start milk-monitor.service
    echo ""
    echo "Service started. Checking status..."
    sleep 2
    systemctl status milk-monitor.service --no-pager
    echo ""
    echo "Dashboard should be available at:"
    echo "  http://$(hostname -I | awk '{print $1}'):5050"
    echo "  http://$(hostname).local:5050"
fi
echo ""
echo "======================================================"
