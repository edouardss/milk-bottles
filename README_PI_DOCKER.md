# Milk Bottle Monitoring - Raspberry Pi with Docker (RECOMMENDED)

This is the **recommended approach** for running on Raspberry Pi 4 with ARM architecture. It uses Roboflow's official Docker container which has all ARM-compatible dependencies pre-built.

## Why Docker?

The Roboflow `inference` Python package has ARM compatibility issues when installed via pip due to binary dependencies (ONNX runtime, etc.) that don't work on all ARM processors. The official solution from Roboflow is to **use their Docker container** which has everything pre-compiled for ARM.

## Quick Start

From your Mac/PC, run:

```bash
./deploy_docker_to_pi.sh
```

This single command will:
- ✓ Clone repo to your Pi
- ✓ Install Docker on your Pi
- ✓ Pull Roboflow ARM inference container
- ✓ Set up Python virtual environment
- ✓ Install Python dependencies (only lightweight SDK, not full package)
- ✓ Start the inference server in Docker

Then SSH to your Pi and start the app:

```bash
ssh edss@edsspi3.local
cd ~/milk-bottles
source venv/bin/activate
python app_pi_docker.py
```

## Architecture

```
┌─────────────────┐
│  USB Webcam     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│  Raspberry Pi 4                         │
│  ┌───────────────────────────────────┐  │
│  │  app_pi_docker.py                 │  │
│  │  - Captures webcam frames         │  │
│  │  - Sends to local Docker API ────────┼──┐
│  │  - Renders overlays               │  │  │
│  │  - Web dashboard                  │  │  │
│  └───────────────────────────────────┘  │  │
│                                          │  │
│  ┌───────────────────────────────────┐  │  │
│  │  Docker Container                 │◄─┼──┘
│  │  roboflow-inference-server-arm-cpu│  │
│  │  - Runs on port 9001              │  │
│  │  - ARM-optimized binaries         │  │
│  │  - Executes Workflows             │  │
│  └───────────────────────────────────┘  │
└─────────────────┬───────────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  Web Browser    │
         │  :5050          │
         └─────────────────┘
```

## Components

### app_pi_docker.py
Python Flask application that:
- Captures video from webcam using OpenCV
- Sends frames to local Docker inference server (HTTP API)
- Processes Workflow results
- Serves web dashboard

### Docker Container
Roboflow's official `roboflow-inference-server-arm-cpu` container:
- Pre-built for ARM64 architecture
- Runs Workflows locally on your Pi
- No "Illegal instruction" errors
- Handles all complex dependencies

### Python Requirements
Only need lightweight packages:
- `flask`, `flask-socketio` - Web server
- `opencv-python-headless` - Camera capture
- `inference-sdk` - HTTP client (NOT full inference package)
- `numpy<2.0` - Array processing

## Manual Setup

If you prefer manual setup:

### 1. Install Docker on Pi

```bash
ssh edss@edsspi3.local
cd ~/milk-bottles
./setup_docker_pi.sh
```

### 2. Start Inference Server

```bash
sudo docker run -d \
    --name roboflow-inference \
    --restart unless-stopped \
    -p 9001:9001 \
    roboflow/roboflow-inference-server-arm-cpu:latest
```

### 3. Install Python Dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_pi_docker.txt
```

### 4. Run Application

```bash
python app_pi_docker.py
```

## Docker Management

### Check container status
```bash
sudo docker ps
```

### View container logs
```bash
sudo docker logs -f roboflow-inference
```

### Stop container
```bash
sudo docker stop roboflow-inference
```

### Start container
```bash
sudo docker start roboflow-inference
```

### Remove container
```bash
sudo docker stop roboflow-inference
sudo docker rm roboflow-inference
```

### Update container
```bash
sudo docker pull roboflow/roboflow-inference-server-arm-cpu:latest
sudo docker stop roboflow-inference
sudo docker rm roboflow-inference
# Then run the docker run command again
```

## Configuration

Create `config.env` with:

```bash
ROBOFLOW_API_KEY=your_api_key_here
INFERENCE_SERVER_URL=http://localhost:9001
NGROK_AUTH_TOKEN=your_ngrok_token  # Optional
```

The `INFERENCE_SERVER_URL` defaults to `http://localhost:9001` if not set.

## Performance

On Raspberry Pi 4 (4GB):
- **FPS**: 5 frames/second processing (configurable in app_pi_docker.py:275)
- **CPU**: 40-60% (Docker + Python + OpenCV)
- **Memory**: ~800MB (Docker container + Python app)
- **Latency**: ~200ms per frame

On Raspberry Pi 5:
- **FPS**: Can likely increase to 10-15 FPS
- **Performance**: ~4x faster according to Roboflow docs

## Troubleshooting

### "Cannot connect to Docker daemon"

```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group
sudo usermod -aG docker $USER
# Then log out and back in
```

### "Connection refused to localhost:9001"

Check if container is running:
```bash
sudo docker ps
```

If not running, start it:
```bash
sudo docker start roboflow-inference
```

View logs for errors:
```bash
sudo docker logs roboflow-inference
```

### "Illegal instruction" error

This shouldn't happen with Docker! If it does:
1. Confirm you're using 64-bit Raspberry Pi OS: `uname -m` should show `aarch64`
2. Update Docker: `sudo apt update && sudo apt upgrade docker`
3. Pull latest container: `sudo docker pull roboflow/roboflow-inference-server-arm-cpu:latest`

### Camera not detected

```bash
ls /dev/video*
# Should show /dev/video0
```

If using different camera device, edit `app_pi_docker.py` line 236:
```python
cap = cv2.VideoCapture(0)  # Change 0 to correct device number
```

### Low FPS / Poor performance

1. Reduce processing FPS in `app_pi_docker.py` line 275:
```python
fps_limit = 3  # Reduce from 5 to 3
```

2. Check Docker resource usage:
```bash
sudo docker stats roboflow-inference
```

## Comparison: Docker vs Direct Python Install

| Aspect | Docker (Recommended) | Direct pip install |
|--------|---------------------|-------------------|
| **ARM Compatibility** | ✓ Pre-built binaries | ✗ "Illegal instruction" errors |
| **Setup Complexity** | Simple | Complex, many fixes needed |
| **Dependencies** | All included | Manual troubleshooting |
| **Updates** | `docker pull` | Reinstall everything |
| **Isolation** | Clean isolation | Can affect system |
| **Resource Usage** | +200MB overhead | Lighter |

## Sources

Based on official Roboflow documentation:
- [Install on Raspberry Pi - Roboflow Inference](https://inference.roboflow.com/install/raspberry-pi/)
- [Deploy Computer Vision Models to Raspberry Pi with Docker](https://blog.roboflow.com/deploy-computer-vision-models-raspberry-pi-docker/)
- [Roboflow + Raspberry Pi](https://roboflow.com/integration/raspberry-pi)

## Auto-Start on Boot

To run automatically when Pi boots:

```bash
cd ~/milk-bottles
sudo ./install_service_docker.sh
```

This sets up systemd services for both Docker container and Flask app.

## Next Steps

1. ✅ Deploy with `./deploy_docker_to_pi.sh`
2. ✅ Test at http://edsspi3.local:5050
3. ✅ Verify camera and inference working
4. ✅ Set up auto-start service
5. ✅ Optional: Configure ngrok for remote access
