# Milk Bottle Monitoring System

Real-time milk bottle inventory monitoring using computer vision with Roboflow Workflows.

## Architecture

This system uses a **hybrid approach** combining Raspberry Pi camera with Mac processing:

```
┌─────────────────┐
│  USB Webcam     │ (Connected to Pi)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Raspberry Pi                   │
│  ┌───────────────────────────┐  │
│  │  camera_server_pi.py      │  │
│  │  - Captures video         │  │
│  │  - Streams MJPEG ────────────┼─┐
│  │  - Port 8888              │  │ │
│  └───────────────────────────┘  │ │
└─────────────────────────────────┘ │
                                    │
         Network (WiFi/Ethernet)    │
                                    │
┌─────────────────────────────────┐ │
│  Mac                            │ │
│  ┌───────────────────────────┐  │ │
│  │  app_with_pi_camera.py    │◄─┼─┘
│  │  - Receives video stream  │  │
│  │  - Runs Roboflow Workflow │  │
│  │  - Web dashboard :5050    │  │
│  └───────────────────────────┘  │
└─────────────────┬───────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Web Browser    │
         │  :5050          │
         └─────────────────┘
```

**Why this architecture?**
- ✅ No ARM compatibility issues - All inference runs on Mac
- ✅ Full workflow support - Custom Python code works perfectly
- ✅ Simple Pi setup - Only needs Flask + OpenCV (no inference package)
- ✅ Better performance - Mac is more powerful than Pi 4
- ✅ Flexible camera placement - Pi can be anywhere on network

## Quick Start

### 1. Setup Raspberry Pi Camera Server

SSH to your Pi:

```bash
ssh edss@edsspi3.local
```

Clone and setup:

```bash
git clone https://github.com/edouardss/milk-bottles.git
cd milk-bottles
chmod +x setup_pi_camera_server.sh
./setup_pi_camera_server.sh
```

Start the camera server:

```bash
source venv_camera/bin/activate
python camera_server_pi.py
```

The Pi will display:
```
✓ Camera opened successfully
Access from your Mac at:
  http://192.168.1.XXX:8888
  http://edsspi3.local:8888
```

### 2. Setup Mac Application

On your Mac, clone the repository:

```bash
git clone https://github.com/edouardss/milk-bottles.git
cd milk-bottles
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `config.env` from the example:

```bash
cp config.env.example config.env
```

Edit `config.env` and add your credentials:

```bash
ROBOFLOW_API_KEY=your_api_key_here
PI_CAMERA_URL=http://192.168.1.XXX:8888/video_feed  # Use IP if .local doesn't work
```

**Important:** Use the Pi's IP address if hostname resolution (`.local`) doesn't work on your Mac.

### 3. Run the Application

```bash
python app_with_pi_camera.py
```

Access the dashboard at: **http://localhost:5050**

## Features

- **Real-time Video Feed** - Live camera stream from Pi with bounding boxes
- **Inventory Counts** - Live count overlay for Whole Milk, 1% Milk, and 2% Milk
- **Missing Stock Alerts** - Red alert box when any milk variant is missing
- **Real-time Graphs** - Historical data visualization (past hour)
- **CSV Data Logging** - Automatic saving of counts and alerts
- **Web Dashboard** - Clean interface with SocketIO real-time updates

## Configuration

### Pi Camera Settings

Edit `camera_server_pi.py` on the Pi:

```python
CAMERA_INDEX = 0  # Change if using different camera (/dev/video1, etc.)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30
```

### Mac Application Settings

Edit `config.env` on Mac:

```bash
# Required
ROBOFLOW_API_KEY=your_api_key_here

# Pi camera URL (use IP address if .local doesn't resolve)
PI_CAMERA_URL=http://192.168.1.XXX:8888/video_feed

# Optional: Ngrok for public access
NGROK_AUTH_TOKEN=your_ngrok_token_here
```

## Troubleshooting

### Cannot connect to Pi camera

**Test from Mac:**
```bash
# Try with IP address first
curl http://192.168.1.XXX:8888/health
# Should return: {"status":"ok","camera":"active"}

# If that works but .local doesn't, use IP in config.env
```

**Check on Pi:**
```bash
# Verify camera server is running
ps aux | grep camera_server_pi

# Check camera device
ls /dev/video*

# Test camera access
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### Port 8888 already in use

If you get "Address already in use" error on the Pi:

```bash
# Find what's using port 8888
sudo lsof -i :8888

# Kill the process if needed
sudo kill <PID>
```

**Note:** Port 8080 is used by Viam Robotics if installed, so we use 8888 instead.

### Poor video quality

Adjust JPEG quality in `camera_server_pi.py`:

```python
cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])  # Higher quality (70-95)
```

Or increase resolution (may impact FPS):

```python
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
```

### Network lag

Reduce FPS or resolution on Pi:

```python
FPS = 15  # Lower FPS
FRAME_WIDTH = 480
FRAME_HEIGHT = 360
```

Or reduce processing FPS on Mac in `app_with_pi_camera.py`:

```python
max_fps=5  # Process fewer frames
```

## Running as Services

### Pi Camera Server (Auto-start on boot)

Create `/etc/systemd/system/camera-server.service`:

```ini
[Unit]
Description=Camera Server for Milk Bottle Monitoring
After=network.target

[Service]
Type=simple
User=edss
WorkingDirectory=/home/edss/milk-bottles
Environment="PATH=/home/edss/milk-bottles/venv_camera/bin"
ExecStart=/home/edss/milk-bottles/venv_camera/bin/python camera_server_pi.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable camera-server
sudo systemctl start camera-server
sudo systemctl status camera-server
```

### Mac Application (LaunchAgent)

Create `~/Library/LaunchAgents/com.user.milk-monitor.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.milk-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/edss/Documents/Roboflow Projects/milk bottles/app_with_pi_camera.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/edss/Documents/Roboflow Projects/milk bottles</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.user.milk-monitor.plist
```

## Public Access with Ngrok

To access the dashboard remotely:

```bash
# On Mac (with application running)
ngrok http 5050
```

This creates a public URL like `https://xyz.ngrok-free.dev` that you can access from anywhere.

## Performance

### Raspberry Pi 4:
- **CPU**: 5-10% (only video capture)
- **Memory**: ~100MB (minimal Flask app)
- **Network**: ~500KB/s (video streaming)

### Mac:
- **CPU**: 30-50% (inference + processing)
- **Memory**: ~1GB (full inference package)
- **FPS**: 10 frames/second processing

## Files Structure

```
milk-bottles/
├── README.md                      # This file
├── README_MAC_WITH_PI_CAMERA.md  # Detailed technical documentation
├── config.env.example            # Configuration template
├── requirements.txt              # Mac dependencies
├── requirements_pi_camera.txt    # Pi minimal dependencies
│
├── app_with_pi_camera.py         # Mac application (main)
├── camera_server_pi.py           # Pi camera server
├── setup_pi_camera_server.sh     # Pi setup script
│
├── app.py                        # Original Mac-only version (reference)
├── BottleCountWorkflow.py        # Workflow definition
└── templates/
    └── index.html                # Web dashboard UI
```

## Development

### Testing locally without Pi

You can test the Mac application with a local webcam by setting:

```bash
PI_CAMERA_URL=0  # Uses local webcam
```

### Viewing logs

Mac application logs are visible in the terminal. For systemd services:

```bash
# Pi camera server logs
ssh edss@edsspi3.local "sudo journalctl -u camera-server -f"
```

## Common Issues & Lessons Learned

1. **Hostname resolution**: If `edsspi3.local` doesn't work, always use IP address
2. **Port conflicts**: Port 8080 is commonly used (Viam, etc.), using 8888 avoids conflicts
3. **Virtual environment**: Always install packages AFTER creating venv, not before
4. **ARM compatibility**: Running inference on Pi requires ARM-compatible builds - avoid by using Mac
5. **Ngrok conflicts**: Only run ngrok on one machine (Mac) to avoid endpoint conflicts

## License

MIT

## Support

For issues or questions, please open an issue on GitHub.
