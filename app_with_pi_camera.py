"""
Flask web application for monitoring milk bottle counts in real-time.
This version uses a camera connected to Raspberry Pi but runs inference on Mac.
Camera streaming from Pi, all processing on Mac.
"""

import os
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import cv2
import time
from datetime import datetime, timedelta
import csv
from threading import Lock
from inference import InferencePipeline
import requests

# Load environment variables
load_dotenv("config.env")

# Configuration
PI_CAMERA_URL = os.environ.get("PI_CAMERA_URL", "http://edsspi3.local:8080/video_feed")

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'milk-bottle-monitoring-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
csv_file_path = "milk_bottle_counts.csv"
alerts_csv_path = "milk_bottle_alerts.csv"
last_save_time = 0
last_frame = None
frame_lock = Lock()

# Alert cooldown period (in seconds)
ALERT_COOLDOWN_SECONDS = 500

# Data storage for plotting (in-memory for past hour)
data_history = {
    "whole": [],
    "1pct": [],
    "2pct": []
}
timestamps = []
data_lock = Lock()

# Alerts tracking
alerts_history = []
alerts_lock = Lock()
last_alert_time = 0

# Initialize CSV files if they don't exist
def init_csv_files():
    """Create CSV files with headers if they don't exist."""
    if not os.path.exists(csv_file_path):
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'whole', '1pct', '2pct'])

    if not os.path.exists(alerts_csv_path):
        with open(alerts_csv_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['timestamp', 'missing_categories'])

init_csv_files()

def save_counts_to_csv(timestamp, counts):
    """Save bottle counts to CSV file."""
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            timestamp,
            counts.get('whole', 0),
            counts.get('1pct', 0),
            counts.get('2pct', 0)
        ])

def save_alert_to_csv(timestamp, missing_categories):
    """Save alert for missing categories to CSV file."""
    with open(alerts_csv_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, ', '.join(missing_categories)])

def get_recent_alerts():
    """Get recent alerts from memory."""
    with alerts_lock:
        return alerts_history[-20:]  # Last 20 alerts

def get_graph_data():
    """Get graph data for the past hour."""
    with data_lock:
        one_hour_ago = datetime.now() - timedelta(hours=1)

        graph_data = {
            "timestamps": [],
            "whole": [],
            "1pct": [],
            "2pct": []
        }

        for i, ts in enumerate(timestamps):
            if ts >= one_hour_ago:
                graph_data["timestamps"].append(ts.strftime('%Y-%m-%d %H:%M:%S'))
                for flavor in ["whole", "1pct", "2pct"]:
                    if i < len(data_history[flavor]):
                        graph_data[flavor].append(data_history[flavor][i])
                    else:
                        graph_data[flavor].append(0)

        return graph_data

def my_sink(result, video_frame):
    """Process predictions from Roboflow workflow."""
    global last_save_time, last_frame, timestamps, last_alert_time

    if result.get("annotated_image"):
        # Get the annotated image
        display_image = result["annotated_image"].numpy_image.copy()

        # Get counts and missing categories
        counts = result.get("counts", {})
        missing = result.get("missing", [])

        # Track alerts with cooldown logic
        current_time = time.time()
        if missing and (current_time - last_alert_time >= ALERT_COOLDOWN_SECONDS):
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')

            # Save alert to CSV
            save_alert_to_csv(timestamp_str, missing)

            # Add to in-memory alerts history
            with alerts_lock:
                category_names = {
                    "whole": "Whole Milk",
                    "1pct": "1% Milk",
                    "2pct": "2% Milk"
                }
                missing_names = [category_names.get(m, m) for m in missing]
                alerts_history.append({
                    "timestamp": timestamp_str,
                    "missing_categories": ", ".join(missing_names)
                })
                # Keep only last 100 alerts in memory
                if len(alerts_history) > 100:
                    alerts_history.pop(0)

            # Emit alert update to all connected clients
            socketio.emit('alert_update', {
                "timestamp": timestamp_str,
                "missing_categories": ", ".join(missing_names)
            })

            # Update last alert time
            last_alert_time = current_time

        # Save data every 5 seconds
        current_time = time.time()
        if current_time - last_save_time >= 5:
            timestamp = datetime.now()

            # Save to CSV
            save_counts_to_csv(timestamp.strftime('%Y-%m-%d %H:%M:%S'), counts)

            # Update in-memory data for plotting
            with data_lock:
                timestamps.append(timestamp)
                for flavor in ["whole", "1pct", "2pct"]:
                    data_history[flavor].append(counts.get(flavor, 0))

                # Remove data older than 1 hour
                one_hour_ago = datetime.now() - timedelta(hours=1)
                while timestamps and timestamps[0] < one_hour_ago:
                    timestamps.pop(0)
                    for flavor in ["whole", "1pct", "2pct"]:
                        if data_history[flavor]:
                            data_history[flavor].pop(0)

            # Emit graph update to all connected clients
            socketio.emit('graph_update', get_graph_data())

            last_save_time = current_time

        # Update last frame for MJPEG stream
        with frame_lock:
            last_frame = display_image

def generate_frames():
    """Generate frames for MJPEG streaming."""
    while True:
        with frame_lock:
            if last_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', last_frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def index():
    """Serve the main dashboard page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/data')
def get_data():
    """API endpoint to get current counts data."""
    return jsonify(get_graph_data())

@app.route('/api/alerts')
def get_alerts():
    """API endpoint to get recent alerts."""
    return jsonify(get_recent_alerts())

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print('Client connected')
    # Send initial graph data
    emit('graph_update', get_graph_data())
    # Send initial alerts data
    emit('alerts_initial', get_recent_alerts())

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print('Client disconnected')

def start_pipeline():
    """Start the Roboflow inference pipeline using camera from Pi."""
    # Remove any local inference environment variable if set
    if "LOCAL_INFERENCE_API_URL" in os.environ:
        del os.environ["LOCAL_INFERENCE_API_URL"]

    print("Initializing pipeline with Roboflow cloud inference...")
    print(f"Camera: Raspberry Pi at {PI_CAMERA_URL}")
    print("Inference: Roboflow serverless cloud (running on Mac)")

    pipeline = InferencePipeline.init_with_workflow(
        api_key=os.environ.get("ROBOFLOW_API_KEY"),
        workspace_name="edss",
        workflow_id="count-milk-alerts",
        video_reference=PI_CAMERA_URL,  # Stream from Pi
        max_fps=10,  # Full FPS on Mac
        on_prediction=my_sink
    )

    print("Pipeline initialized. Starting video stream from Pi...")
    pipeline.start()
    pipeline.join()

if __name__ == '__main__':
    # Check if Pi camera is accessible
    print("=" * 60)
    print("Milk Bottle Monitoring System (Mac + Pi Camera)")
    print("=" * 60)
    print("")
    print("Testing connection to Pi camera...")

    try:
        response = requests.get(PI_CAMERA_URL.replace('/video_feed', '/health'), timeout=5)
        if response.status_code == 200:
            print(f"✓ Pi camera accessible at {PI_CAMERA_URL}")
        else:
            print(f"⚠ Pi responded but camera may not be ready")
    except Exception as e:
        print(f"✗ ERROR: Cannot connect to Pi camera at {PI_CAMERA_URL}")
        print(f"  Error: {e}")
        print("")
        print("Make sure camera_server_pi.py is running on your Pi:")
        print("  ssh edss@edsspi3.local")
        print("  cd ~/milk-bottles")
        print("  source venv/bin/activate")
        print("  python camera_server_pi.py")
        print("")
        exit(1)

    print("")

    # Start inference pipeline in a separate thread
    from threading import Thread
    pipeline_thread = Thread(target=start_pipeline, daemon=True)
    pipeline_thread.start()

    # Start Flask-SocketIO server
    print("Flask server starting...")
    print("Access the application at:")
    print("  - http://localhost:5050")
    print("  - http://127.0.0.1:5050")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)
