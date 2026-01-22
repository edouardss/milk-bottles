# Milk Bottle Monitoring - Mac with Pi Camera (RECOMMENDED)

This is the **best solution** that combines:
- ✅ Raspberry Pi camera (located where you need monitoring)
- ✅ Mac processing power (runs inference without ARM issues)
- ✅ Full workflow support (custom Python code works on Mac)
- ✅ Simple setup (minimal Pi dependencies)

## Architecture

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
│  │  - Port 8080              │  │ │
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

## Quick Start

### 1. Setup Pi Camera Server

SSH to your Pi and run:

```bash
ssh edss@edsspi3.local
cd ~/milk-bottles
git pull
chmod +x setup_pi_camera_server.sh
./setup_pi_camera_server.sh
```

Then start the camera server:

```bash
source venv_camera/bin/activate
python camera_server_pi.py
```

The Pi will display:
```
✓ Camera opened successfully
Access from your Mac at:
  http://192.168.1.130:8080
  http://edsspi3.local:8080
```

### 2. Run Application on Mac

On your Mac, add this to `config.env`:

```bash
PI_CAMERA_URL=http://edsspi3.local:8080/video_feed
```

Then run:

```bash
python app_with_pi_camera.py
```

### 3. Access Dashboard

Open browser to: **http://localhost:5050**

## Advantages

✅ **No ARM compatibility issues** - All inference runs on Mac
✅ **Full workflow support** - Custom Python code works perfectly
✅ **Simple Pi setup** - Only needs Flask + OpenCV (no inference package)
✅ **Better performance** - Mac is more powerful than Pi 4
✅ **Easy debugging** - All logs and processing on your Mac
✅ **Flexible camera placement** - Pi can be anywhere on network

## Components

### On Raspberry Pi:
- **camera_server_pi.py** - Simple Flask app that:
  - Captures video from webcam
  - Streams as MJPEG on port 8080
  - Provides health check endpoint
  - Uses only 2 dependencies (flask, opencv)

### On Mac:
- **app_with_pi_camera.py** - Full application that:
  - Connects to Pi camera stream
  - Runs Roboflow Workflow with InferencePipeline
  - Processes all inference
  - Serves web dashboard
  - Saves data to CSV

## Configuration

### config.env (on Mac)

```bash
ROBOFLOW_API_KEY=your_api_key_here
PI_CAMERA_URL=http://edsspi3.local:8080/video_feed  # Default if not set
```

### Camera Settings

Edit `camera_server_pi.py` on Pi to adjust:

```python
CAMERA_INDEX = 0  # Change if using different camera (/dev/video1, etc.)
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30
```

## Network Requirements

- Pi and Mac must be on same network (WiFi/Ethernet)
- Port 8080 must be accessible from Mac to Pi
- Test connectivity: `ping edsspi3.local` from Mac

## Troubleshooting

### Cannot connect to Pi camera

**On Mac:**
```bash
curl http://edsspi3.local:8080/health
# Should return: {"status":"ok","camera":"active"}
```

**On Pi:**
```bash
# Check if camera server is running
ps aux | grep camera_server_pi

# Check camera device
ls /dev/video*

# Test camera manually
python -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### Poor video quality

Adjust JPEG quality in `camera_server_pi.py`:

```python
cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 95])  # Higher quality
```

Or increase resolution:

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

### Camera not detected on Pi

```bash
# List camera devices
ls -l /dev/video*

# Check Pi camera (if using CSI camera)
vcgencmd get_camera

# Check USB camera
lsusb

# Try different camera index
# Edit camera_server_pi.py and change:
CAMERA_INDEX = 1  # or 2, etc.
```

## Running as Services

### Pi Camera Server (Auto-start)

Create `/etc/systemd/system/camera-server.service`:

```ini
[Unit]
Description=Camera Server for Mac
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

Enable:
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

## Performance

### Raspberry Pi 4:
- **CPU**: 5-10% (only video capture)
- **Memory**: ~100MB (minimal Flask app)
- **Network**: ~500KB/s (video streaming)

### Mac:
- **CPU**: 30-50% (inference + processing)
- **Memory**: ~1GB (full inference package)
- **FPS**: 10 frames/second processing

## Comparison with Other Approaches

| Approach | Pi CPU | Mac CPU | Workflow Support | ARM Issues | Complexity |
|----------|--------|---------|------------------|------------|------------|
| **Pi Only** | High | None | Limited | Yes | High |
| **Docker on Pi** | High | None | No | Yes | High |
| **Mac + Pi Camera** ✅ | Low | Medium | Full | None | Low |
| **Mac Only** | None | Medium | Full | None | Low (but camera must be on Mac) |

## Security Notes

- Camera stream is unencrypted HTTP on local network
- For public access, use SSH tunnel or VPN
- Don't expose port 8080 to internet directly

## Next Steps

1. ✅ Setup Pi camera server
2. ✅ Test camera stream from Mac
3. ✅ Run application on Mac
4. ✅ Access dashboard
5. ✅ Set up auto-start services (optional)
6. ✅ Configure ngrok for remote access (optional)

This solution gives you the best of both worlds: flexible camera placement with powerful Mac processing!
