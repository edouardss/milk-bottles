# Training Data Capture Guide

## Configuration

All components are configured to use **1280x720 @ 85% JPEG quality** to ensure training data matches production inference.

### System Settings:
- **Resolution**: 1280x720
- **JPEG Quality**: 85%
- **FPS**: 30 (may drop to 10-15 with higher resolution)

## Step 1: Update Pi Camera Server

Deploy the updated camera server with new resolution:

```bash
./update_camera_server.sh
```

Or manually:
```bash
ssh edss@edsspi3.local
cd ~/milk-bottles
source venv_camera/bin/activate
pkill -f camera_server_pi.py  # Stop old server
python camera_server_pi.py     # Start with new resolution
```

## Step 2: Capture Training Snapshots

On your Mac:

```bash
python capture_snapshots.py
```

### Usage:
1. Live video feed will open in a window
2. The script will verify resolution matches (1280x720)
3. Position milk bottles in front of the camera
4. **Press SPACEBAR** to capture a snapshot
5. Move bottles, change angles, lighting, etc.
6. Repeat to capture diverse examples
7. **Press Q** to quit

### Tips for Good Training Data:
- Capture 30-50 images per bottle type minimum
- Vary angles (straight on, tilted, from side)
- Vary distances (close up, far away)
- Vary lighting conditions
- Include bottles alone and in groups
- Include partially visible bottles (edges of frame)
- Include bottles at different heights in frame

### Snapshots Location:
All snapshots are saved to: `training_snapshots/`

Filenames: `snapshot_YYYYMMDD_HHMMSS_mmm.jpg`

## Step 3: Upload to Roboflow

1. Go to your Roboflow project
2. Upload all images from `training_snapshots/`
3. Label each bottle type:
   - Whole Milk
   - 1% Milk
   - 2% Milk
4. Generate dataset with train/val/test split
5. Train new model version

## Step 4: Update Workflow

Once you have a new model version:

1. Update the workflow in Roboflow UI to use the new model
2. No code changes needed - the workflow API automatically uses the latest version

## Verification

To verify your snapshots are correct resolution:

```bash
cd training_snapshots
file snapshot_*.jpg | head -1
# Should show: JPEG image data, ..., 1280 x 720, ...
```

Or with Python:
```python
import cv2
img = cv2.imread('training_snapshots/snapshot_20260125_*.jpg')
print(f"Resolution: {img.shape[1]}x{img.shape[0]}")  # Should be 1280x720
```

## Troubleshooting

### Resolution mismatch warning
If you see "⚠ WARNING: Resolution mismatch!" when running `capture_snapshots.py`:

1. Check `camera_server_pi.py` has:
   ```python
   FRAME_WIDTH = 1280
   FRAME_HEIGHT = 720
   ```

2. Restart the camera server on Pi

### Low FPS
If streaming is laggy:
- This is normal at higher resolution
- FPS may drop to 10-15 (still fine for training capture)
- Network bandwidth: ~3-6 Mbps needed

### Camera server won't start
Check logs on Pi:
```bash
ssh edss@edsspi3.local
cd ~/milk-bottles
cat camera_server.log
```

## Configuration Files

- **Pi Camera Server**: `camera_server_pi.py` (lines 14-17)
- **Snapshot Capture**: `capture_snapshots.py` (lines 19-21)
- **Production Inference**: Uses same stream from Pi camera server

All three use identical resolution and quality settings!
