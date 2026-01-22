# Milk Bottle Monitoring - Raspberry Pi 4 Deployment

This version is optimized for Raspberry Pi 4 with a USB webcam, using Roboflow's serverless cloud inference to offload the heavy AI processing.

## Hardware Requirements

- **Raspberry Pi 4** (4GB or 8GB RAM recommended)
- **USB Webcam** or Raspberry Pi Camera Module
- **MicroSD Card** (32GB+ recommended)
- **Power Supply** (Official Raspberry Pi power adapter)
- **Cooling** (Heatsinks or fan for continuous operation)
- **Network Connection** (WiFi or Ethernet)

## Quick Deployment

### From Your Mac/PC

1. **Clone and push this repository to GitHub** (if not already done)

2. **Run the deployment script:**
   ```bash
   ./deploy_to_pi.sh
   ```

This single command will:
- ✓ Clone the repository to your Raspberry Pi
- ✓ Copy your `config.env` (if you choose)
- ✓ Install all system dependencies
- ✓ Create a Python virtual environment
- ✓ Install Python packages
- ✓ Test camera access
- ✓ Set up configuration

### What the Deployment Does

The `deploy_to_pi.sh` script:
1. Tests SSH connection to `edsspi.local`
2. Clones repository from GitHub to `~/milk-bottles`
3. Optionally copies your local `config.env`
4. Runs `setup_pi.sh` on the Pi to install everything
5. Creates isolated virtual environment at `~/milk-bottles/venv`

## Manual Setup (if needed)

If you prefer to set up manually:

### 1. SSH into Your Pi
```bash
ssh edss@edsspi.local
```

### 2. Clone Repository
```bash
cd ~
git clone https://github.com/edouardss/milk-bottles.git
cd milk-bottles
```

### 3. Create config.env
```bash
cp config.env.example config.env
nano config.env
# Add your ROBOFLOW_API_KEY
```

### 4. Run Setup
```bash
chmod +x setup_pi.sh
./setup_pi.sh
```

This installs all dependencies and creates a virtual environment.

## Running the Application

### Option 1: Manual Start
```bash
cd ~/milk-bottles
source venv/bin/activate
python app_pi.py
```

### Option 2: Direct Execution
```bash
cd ~/milk-bottles
venv/bin/python app_pi.py
```

### Option 3: Auto-Start Service (Recommended)

Set up the application to start automatically on boot:

```bash
cd ~/milk-bottles
sudo ./install_service.sh
```

Service commands:
```bash
sudo systemctl start milk-monitor    # Start
sudo systemctl stop milk-monitor     # Stop
sudo systemctl restart milk-monitor  # Restart
sudo systemctl status milk-monitor   # Check status
sudo journalctl -u milk-monitor -f   # View logs
```

## Accessing the Dashboard

From any device on the same network:
- **http://edsspi.local:5050**
- **http://[pi-ip-address]:5050**

To find your Pi's IP:
```bash
hostname -I
```

## Project Structure

```
~/milk-bottles/
├── venv/                     # Virtual environment (created by setup)
├── app_pi.py                 # Main application (Pi optimized)
├── requirements_pi.txt       # Python dependencies
├── setup_pi.sh              # Setup script
├── install_service.sh       # Systemd service installer
├── config.env               # Configuration (API keys)
├── config.env.example       # Template
├── templates/
│   └── index.html           # Web dashboard
├── milk_bottle_counts.csv   # Data log (created at runtime)
└── milk_bottle_alerts.csv   # Alert log (created at runtime)
```

## Key Differences from Desktop Version

### Optimizations for Raspberry Pi 4

1. **☁️ Cloud Inference**: Uses Roboflow's serverless cloud
   - No local inference server needed
   - Significantly reduces CPU/memory on Pi
   - Requires stable internet connection

2. **⚡ Performance**: Reduced to 5 FPS (vs 10 FPS)
   - Balances responsiveness with Pi capabilities
   - Reduces network bandwidth

3. **📦 Virtual Environment**: Isolated dependencies
   - Clean separation from system Python
   - Easy to update or reset

4. **🔄 Auto-Start**: Systemd service support
   - Starts automatically on boot
   - Restarts on crashes
   - Easy monitoring with journalctl

## Troubleshooting

### Camera Not Detected

Check if camera is recognized:
```bash
ls /dev/video*
# Should show /dev/video0
```

Test camera:
```bash
v4l2-ctl --list-devices
```

### Change Camera Device

Edit `app_pi.py` line 320:
```python
# Change from:
video_reference=0

# To:
video_reference="/dev/video1"  # or appropriate device
```

### Virtual Environment Issues

Recreate the virtual environment:
```bash
cd ~/milk-bottles
rm -rf venv
./setup_pi.sh
```

### Network/Inference Issues

Test internet connection:
```bash
ping api.roboflow.com
```

Verify API key in `config.env`:
```bash
grep ROBOFLOW_API_KEY config.env
```

### Low Performance

Reduce FPS in `app_pi.py`:
```python
max_fps=3  # Change from 5 to 3
```

### Permission Errors

Add user to video group:
```bash
sudo usermod -a -G video $USER
# Then logout and login
```

### Service Won't Start

Check logs:
```bash
sudo journalctl -u milk-monitor -n 50
```

Check service status:
```bash
sudo systemctl status milk-monitor
```

## Updating the Application

```bash
cd ~/milk-bottles
git pull
source venv/bin/activate
pip install -r requirements_pi.txt
sudo systemctl restart milk-monitor  # If using service
```

## Performance Expectations

On Raspberry Pi 4 (4GB):
- **CPU Usage**: 30-50% (vs 80%+ with local inference)
- **Memory Usage**: ~500MB (vs 2GB+ with local inference)
- **Network Usage**: ~100-300 KB/s (for cloud inference)
- **Latency**: 200-500ms per frame (internet dependent)

## Architecture

```
┌─────────────────┐
│  USB Webcam     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Raspberry Pi 4                 │
│  ┌───────────────────────────┐  │
│  │  venv/                    │  │
│  │  └── app_pi.py            │  │
│  │      - Captures frames    │  │
│  │      - Sends to cloud     │◄─┼──► Roboflow Cloud
│  │      - Renders overlays   │  │    (Serverless)
│  │      - Web dashboard      │  │
│  └───────────────────────────┘  │
└─────────────────┬───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Web Browser    │
         │  (Any Device)   │
         │  :5050          │
         └─────────────────┘
```

## Security Notes

- `config.env` contains API keys - keep it secure
- Dashboard is accessible on local network only
- For external access, use VPN or ngrok (like your current setup)

## Support

- Roboflow Docs: https://docs.roboflow.com
- Raspberry Pi Forums: https://forums.raspberrypi.com
- GitHub Issues: https://github.com/edouardss/milk-bottles/issues

## Next Steps

After deployment:
1. ✅ Test the dashboard: http://edsspi.local:5050
2. ✅ Verify camera detection and inference
3. ✅ Check alerts are working
4. ✅ Set up auto-start service
5. ✅ Monitor performance and adjust FPS if needed
