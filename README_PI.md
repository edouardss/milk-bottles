# Milk Bottle Monitoring - Raspberry Pi 4 Setup

This version is optimized for Raspberry Pi 4 with a USB webcam, using Roboflow's serverless cloud inference to offload the heavy AI processing.

## Hardware Requirements

- **Raspberry Pi 4** (4GB or 8GB RAM recommended)
- **USB Webcam** or Raspberry Pi Camera Module
- **MicroSD Card** (32GB+ recommended)
- **Power Supply** (Official Raspberry Pi power adapter)
- **Cooling** (Heatsinks or fan for continuous operation)

## Quick Start

### 1. Transfer Files to Raspberry Pi

Copy these files to your Raspberry Pi:
```bash
# From your main computer, use scp:
scp app_pi.py requirements_pi.txt setup_pi.sh pi@<raspberry-pi-ip>:~/milk-monitor/
scp -r templates pi@<raspberry-pi-ip>:~/milk-monitor/
```

### 2. Run Setup Script

SSH into your Raspberry Pi and run:
```bash
cd ~/milk-monitor
chmod +x setup_pi.sh
./setup_pi.sh
```

This script will:
- Update system packages
- Install required system libraries
- Install Python dependencies
- Test camera access
- Create config.env template

### 3. Configure API Key

Edit the config.env file with your Roboflow API key:
```bash
nano config.env
```

Add your API key:
```
ROBOFLOW_API_KEY=your_actual_api_key_here
```

### 4. Run the Application

```bash
python3 app_pi.py
```

The application will start and display:
```
======================================
Raspberry Pi 4 Milk Bottle Monitoring System
======================================
Configuration:
  - Inference: Roboflow Cloud (serverless)
  - Camera: USB webcam
  - Max FPS: 5 (optimized for Pi 4)
======================================
```

### 5. Access the Dashboard

From any device on the same network, open a browser and navigate to:
```
http://<raspberry-pi-ip>:5050
```

To find your Raspberry Pi's IP address:
```bash
hostname -I
```

## Key Differences from Desktop Version

### Optimizations for Raspberry Pi 4

1. **Cloud Inference**: Uses Roboflow's serverless cloud instead of local inference
   - No need to run local inference server
   - Significantly reduces CPU/memory usage on Pi
   - Requires stable internet connection

2. **Reduced FPS**: Set to 5 FPS (vs 10 FPS on desktop)
   - Balances responsiveness with Pi's processing capabilities
   - Reduces network bandwidth usage

3. **Same Features**:
   - ✓ Live video feed with detection overlays
   - ✓ Real-time analytics graphs
   - ✓ Alert tracking and history
   - ✓ WebSocket updates
   - ✓ CSV data logging

## Troubleshooting

### Camera Not Detected

Check if camera is recognized:
```bash
ls /dev/video*
```

You should see `/dev/video0` (or similar). If not:
- Check USB connection
- Try different USB port
- Test with: `v4l2-ctl --list-devices`

### Change Camera Device

If your camera is on a different device (e.g., `/dev/video1`), edit `app_pi.py`:
```python
# Line 320 - change from:
video_reference=0

# To:
video_reference="/dev/video1"  # or appropriate device
```

### Low Performance

If the system is slow:
1. Reduce FPS further (edit `max_fps=5` to `max_fps=3` in app_pi.py)
2. Ensure Pi has adequate cooling
3. Close other applications
4. Consider using Pi 4 8GB model

### Network Issues

If inference fails:
- Check internet connection: `ping api.roboflow.com`
- Verify API key in config.env
- Check Roboflow account status

### Permission Errors

If you get camera permission errors:
```bash
sudo usermod -a -G video $USER
# Then logout and login again
```

## Auto-Start on Boot (Optional)

To run the application automatically when Pi boots:

1. Create systemd service file:
```bash
sudo nano /etc/systemd/system/milk-monitor.service
```

2. Add this content:
```ini
[Unit]
Description=Milk Bottle Monitoring Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/milk-monitor
Environment="PATH=/home/pi/.local/bin:/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/python3 /home/pi/milk-monitor/app_pi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

3. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable milk-monitor.service
sudo systemctl start milk-monitor.service
```

4. Check status:
```bash
sudo systemctl status milk-monitor.service
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
│  │  app_pi.py                │  │
│  │  - Captures frames        │  │
│  │  - Sends to Roboflow      │◄─┼──► Roboflow Cloud
│  │  - Receives predictions   │  │    (Serverless Inference)
│  │  - Renders overlays       │  │
│  │  - Streams to web         │  │
│  └───────────────────────────┘  │
│  ┌───────────────────────────┐  │
│  │  Flask Web Server         │  │
│  │  - Video feed             │  │
│  │  - Analytics dashboard    │  │
│  │  - Alert tracking         │  │
│  └───────────────────────────┘  │
└─────────────────┬───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Browser        │
         │  (Any Device)   │
         └─────────────────┘
```

## File Structure

```
milk-monitor/
├── app_pi.py                 # Main application (Pi optimized)
├── requirements_pi.txt       # Python dependencies
├── setup_pi.sh              # Automated setup script
├── config.env               # Configuration (API keys)
├── templates/
│   └── index.html           # Web dashboard
├── milk_bottle_counts.csv   # Data log (created at runtime)
└── milk_bottle_alerts.csv   # Alert log (created at runtime)
```

## Support

For issues or questions:
- Check Roboflow documentation: https://docs.roboflow.com
- Raspberry Pi forums: https://forums.raspberrypi.com
- GitHub Issues: (your repo here)

## License

Same as main project
