"""
High-resolution snapshot capture tool that runs on the Raspberry Pi.
Saves full-resolution images directly on the Pi when triggered via web interface.
"""

from flask import Flask, render_template_string, jsonify, send_from_directory
import cv2
import os
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Configuration
CAMERA_INDEX = 0
SNAPSHOTS_DIR = "training_snapshots"
FRAME_WIDTH = 1920  # Full HD width
FRAME_HEIGHT = 1080  # Full HD height

# Global variables
camera = None
snapshot_count = 0
latest_frame = None
frame_lock = threading.Lock()

def init_camera():
    """Initialize camera with high resolution."""
    global camera
    camera = cv2.VideoCapture(CAMERA_INDEX)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, 30)

    # Verify settings
    actual_width = camera.get(cv2.CAP_PROP_FRAME_WIDTH)
    actual_height = camera.get(cv2.CAP_PROP_FRAME_HEIGHT)
    print(f"Camera resolution: {int(actual_width)}x{int(actual_height)}")

    return camera.isOpened()

def create_snapshots_directory():
    """Create directory for snapshots if it doesn't exist."""
    if not os.path.exists(SNAPSHOTS_DIR):
        os.makedirs(SNAPSHOTS_DIR)
        print(f"Created directory: {SNAPSHOTS_DIR}")

def camera_loop():
    """Continuously capture frames for preview."""
    global latest_frame
    while True:
        ret, frame = camera.read()
        if ret:
            with frame_lock:
                latest_frame = frame
        time.sleep(0.033)  # ~30 FPS

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera Snapshot Capture</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        header h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .content {
            padding: 30px;
        }
        .preview {
            text-align: center;
            margin-bottom: 20px;
        }
        .preview img {
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .controls {
            text-align: center;
            margin: 30px 0;
        }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 20px 50px;
            font-size: 1.5em;
            border-radius: 50px;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 25px rgba(102, 126, 234, 0.6);
        }
        .btn:active {
            transform: translateY(0);
        }
        .stats {
            display: flex;
            gap: 20px;
            margin-top: 30px;
        }
        .stat-card {
            flex: 1;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-card h3 {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
        }
        .instructions {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
        }
        .instructions h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .instructions ul {
            margin-left: 20px;
        }
        .instructions li {
            margin: 5px 0;
        }
        .flash {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: white;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.1s;
            z-index: 9999;
        }
        .flash.active {
            opacity: 0.8;
        }
    </style>
</head>
<body>
    <div class="flash" id="flash"></div>
    <div class="container">
        <header>
            <h1>📸 High-Resolution Snapshot Capture</h1>
            <p>Raspberry Pi Camera Tool</p>
        </header>
        <div class="content">
            <div class="preview">
                <img id="preview" src="/preview" alt="Camera preview">
            </div>

            <div class="controls">
                <button class="btn" onclick="captureSnapshot()" id="captureBtn">
                    📷 CAPTURE (Spacebar)
                </button>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <h3>Snapshots Captured</h3>
                    <div class="value" id="count">0</div>
                </div>
                <div class="stat-card">
                    <h3>Resolution</h3>
                    <div class="value" style="font-size: 1.5em;">{{ width }}x{{ height }}</div>
                </div>
                <div class="stat-card">
                    <h3>Saved Location</h3>
                    <div class="value" style="font-size: 1em;">{{ snapshots_dir }}/</div>
                </div>
            </div>

            <div class="instructions">
                <h3>Instructions</h3>
                <ul>
                    <li><strong>Press SPACEBAR</strong> on your keyboard to capture</li>
                    <li><strong>Click the button</strong> to capture with mouse</li>
                    <li>Images are saved at full resolution ({{ width }}x{{ height }})</li>
                    <li>Access this page from your Mac: <strong>http://edsspi3.local:9000</strong></li>
                    <li>Snapshots are saved on the Pi in: <strong>~/milk-bottles/{{ snapshots_dir }}/</strong></li>
                </ul>
            </div>
        </div>
    </div>

    <script>
        let snapshotCount = 0;

        // Update preview image every 100ms
        setInterval(() => {
            document.getElementById('preview').src = '/preview?' + new Date().getTime();
        }, 100);

        // Capture snapshot
        function captureSnapshot() {
            fetch('/capture')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        snapshotCount++;
                        document.getElementById('count').textContent = snapshotCount;

                        // Flash effect
                        const flash = document.getElementById('flash');
                        flash.classList.add('active');
                        setTimeout(() => flash.classList.remove('active'), 100);

                        console.log('Captured:', data.filename);
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        // Keyboard shortcut - spacebar
        document.addEventListener('keydown', (event) => {
            if (event.code === 'Space') {
                event.preventDefault();
                captureSnapshot();
            }
        });

        // Get initial count
        fetch('/count')
            .then(response => response.json())
            .then(data => {
                snapshotCount = data.count;
                document.getElementById('count').textContent = snapshotCount;
            });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the capture interface."""
    return render_template_string(
        HTML_TEMPLATE,
        width=int(camera.get(cv2.CAP_PROP_FRAME_WIDTH)),
        height=int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        snapshots_dir=SNAPSHOTS_DIR
    )

@app.route('/preview')
def preview():
    """Serve preview image (low quality for fast updates)."""
    global latest_frame
    with frame_lock:
        if latest_frame is not None:
            # Resize for preview
            preview_frame = cv2.resize(latest_frame, (640, 360))
            _, buffer = cv2.imencode('.jpg', preview_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            return buffer.tobytes(), 200, {'Content-Type': 'image/jpeg'}
    return '', 204

@app.route('/capture')
def capture():
    """Capture and save a high-resolution snapshot."""
    global snapshot_count

    # Capture frame at full resolution
    ret, frame = camera.read()
    if not ret:
        return jsonify({'success': False, 'error': 'Failed to capture frame'})

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
    filename = f"snapshot_{timestamp}.jpg"
    filepath = os.path.join(SNAPSHOTS_DIR, filename)

    # Save at maximum quality
    cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
    snapshot_count += 1

    print(f"✓ Saved: {filename}")

    return jsonify({
        'success': True,
        'filename': filename,
        'count': snapshot_count
    })

@app.route('/count')
def get_count():
    """Get current snapshot count."""
    return jsonify({'count': snapshot_count})

@app.route('/snapshots/<filename>')
def download_snapshot(filename):
    """Download a specific snapshot."""
    return send_from_directory(SNAPSHOTS_DIR, filename)

if __name__ == '__main__':
    print("=" * 60)
    print("Pi Camera High-Resolution Snapshot Capture Tool")
    print("=" * 60)
    print("")

    # Create snapshots directory
    create_snapshots_directory()

    # Initialize camera
    print("Initializing camera...")
    if not init_camera():
        print("✗ ERROR: Failed to open camera")
        exit(1)

    print("✓ Camera initialized")
    print("")

    # Start camera loop in background
    camera_thread = threading.Thread(target=camera_loop, daemon=True)
    camera_thread.start()

    print("Starting web server...")
    print("Access from your Mac:")
    print("  http://edsspi3.local:9000")
    print("  or")
    print("  http://192.168.1.XXX:9000")
    print("")
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host='0.0.0.0', port=9000, debug=False, threaded=True)
