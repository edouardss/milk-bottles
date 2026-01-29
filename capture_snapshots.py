"""
Snapshot capture tool for collecting training images from Pi camera.
Displays live feed from Pi and saves snapshots when spacebar is pressed.

IMPORTANT: This captures at the SAME resolution and quality as inference:
- Resolution: 1280x720
- JPEG Quality: 85%
- This ensures training data matches production inference conditions.
"""

import cv2
import os
from datetime import datetime
import requests
import numpy as np

# Configuration
PI_CAMERA_URL = "http://192.168.1.130:8888/video_feed"  # Update with your Pi's IP
SNAPSHOTS_DIR = "training_snapshots"

# Expected stream parameters (should match camera_server_pi.py)
EXPECTED_WIDTH = 1280
EXPECTED_HEIGHT = 720
EXPECTED_QUALITY = 85  # JPEG quality percentage

def create_snapshots_directory():
    """Create directory for snapshots if it doesn't exist."""
    if not os.path.exists(SNAPSHOTS_DIR):
        os.makedirs(SNAPSHOTS_DIR)
        print(f"Created directory: {SNAPSHOTS_DIR}")
    else:
        print(f"Using existing directory: {SNAPSHOTS_DIR}")

def decode_mjpeg_stream(url):
    """
    Generator that yields frames from MJPEG stream.
    """
    stream = requests.get(url, stream=True, timeout=5)
    if stream.status_code != 200:
        raise Exception(f"Failed to connect to camera: HTTP {stream.status_code}")

    bytes_data = b''
    for chunk in stream.iter_content(chunk_size=1024):
        bytes_data += chunk
        a = bytes_data.find(b'\xff\xd8')  # JPEG start
        b = bytes_data.find(b'\xff\xd9')  # JPEG end
        if a != -1 and b != -1:
            jpg = bytes_data[a:b+2]
            bytes_data = bytes_data[b+2:]
            frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
            if frame is not None:
                yield frame

def main():
    """Main snapshot capture loop."""
    print("=" * 60)
    print("Pi Camera Snapshot Capture Tool")
    print("=" * 60)
    print(f"Camera URL: {PI_CAMERA_URL}")
    print(f"Expected Resolution: {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
    print(f"Expected Quality: {EXPECTED_QUALITY}%")
    print("")
    print("Controls:")
    print("  SPACEBAR - Capture snapshot")
    print("  Q        - Quit")
    print("=" * 60)
    print("")

    # Create snapshots directory
    create_snapshots_directory()

    # Test connection
    print("Connecting to Pi camera...")
    try:
        response = requests.get(PI_CAMERA_URL.replace('/video_feed', '/health'), timeout=5)
        if response.status_code == 200:
            print("✓ Connected to Pi camera")
        else:
            print("⚠ Pi responded but camera may not be ready")
    except Exception as e:
        print(f"✗ ERROR: Cannot connect to Pi camera")
        print(f"  Error: {e}")
        print("")
        print("Make sure camera_server_pi.py is running on your Pi")
        return

    print("")
    print("Starting live view...")
    print("")

    snapshot_count = 0
    resolution_verified = False

    try:
        # Create window
        cv2.namedWindow('Pi Camera - Press SPACEBAR to capture', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Pi Camera - Press SPACEBAR to capture', 800, 600)

        # Stream frames
        for frame in decode_mjpeg_stream(PI_CAMERA_URL):
            # Keep a clean copy for saving
            clean_frame = frame.copy()

            # Verify resolution on first frame
            height, width = frame.shape[:2]
            if not resolution_verified:
                if width == EXPECTED_WIDTH and height == EXPECTED_HEIGHT:
                    print(f"✓ Resolution verified: {width}x{height}")
                else:
                    print(f"⚠ WARNING: Resolution mismatch!")
                    print(f"  Expected: {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}")
                    print(f"  Actual: {width}x{height}")
                    print(f"  Update camera_server_pi.py to match!")
                resolution_verified = True

            # Add instruction overlay (on display copy, not clean_frame)
            overlay = frame.copy()

            # Semi-transparent bar at top
            cv2.rectangle(overlay, (0, 0), (width, 60), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

            # Instructions text
            cv2.putText(frame, f"Snapshots: {snapshot_count} | Press SPACEBAR to capture | Q to quit",
                       (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

            # Display frame with overlay
            cv2.imshow('Pi Camera - Press SPACEBAR to capture', frame)

            # Wait for key press (1ms to keep stream smooth)
            key = cv2.waitKey(1) & 0xFF

            if key == ord(' '):  # Spacebar
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                filename = f"snapshot_{timestamp}.jpg"
                filepath = os.path.join(SNAPSHOTS_DIR, filename)

                # Save the clean frame (without overlay)
                cv2.imwrite(filepath, clean_frame)
                snapshot_count += 1
                print(f"✓ Saved: {filename}")

                # Show visual feedback (white flash)
                flash = frame.copy()
                cv2.rectangle(flash, (0, 0), (width, height), (255, 255, 255), 30)
                cv2.imshow('Pi Camera - Press SPACEBAR to capture', flash)
                cv2.waitKey(100)  # Brief flash

            elif key == ord('q') or key == ord('Q'):  # Q to quit
                print("")
                print("Quitting...")
                break

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
    finally:
        cv2.destroyAllWindows()
        print("")
        print("=" * 60)
        print(f"Session complete! Captured {snapshot_count} snapshots")
        print(f"Snapshots saved to: {SNAPSHOTS_DIR}/")
        print("=" * 60)

if __name__ == '__main__':
    main()
