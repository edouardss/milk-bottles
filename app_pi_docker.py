"""
Flask web application for monitoring milk bottle counts in real-time on Raspberry Pi 4.
This version uses Roboflow Inference Server running in Docker (ARM-compatible).
Optimized for low-power ARM devices with webcam input.
"""

import os
from flask import Flask, render_template, Response, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import cv2
import time
from datetime import datetime, timedelta
import csv
from threading import Lock, Thread
from inference_sdk import InferenceHTTPClient
import base64
import numpy as np

# Load environment variables
load_dotenv("config.env")

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

def process_workflow_result(result, frame):
    """Process predictions from Roboflow workflow running in Docker."""
    global last_save_time, last_frame, timestamps, last_alert_time

    # Extract data from workflow result
    outputs = result.get("outputs", [{}])
    if not outputs:
        return frame

    output = outputs[0]

    # Get the annotated image (base64 encoded)
    annotated_image_b64 = output.get("annotated_image", {}).get("value")

    if annotated_image_b64:
        # Decode base64 image
        img_bytes = base64.b64decode(annotated_image_b64.split(',')[1] if ',' in annotated_image_b64 else annotated_image_b64)
        img_array = np.frombuffer(img_bytes, dtype=np.uint8)
        display_image = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    else:
        display_image = frame.copy()

    # Get counts and missing categories from workflow
    counts = output.get("counts", {}).get("value", {})
    missing = output.get("missing", {}).get("value", [])

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

    return display_image

def capture_and_process():
    """Capture video frames and process them with Roboflow Workflow via Docker HTTP API."""
    global last_frame

    # Initialize Inference HTTP Client (connects to Docker container)
    client = InferenceHTTPClient(
        api_url=os.environ.get("INFERENCE_SERVER_URL", "http://localhost:9001"),
        api_key=os.environ.get("ROBOFLOW_API_KEY")
    )

    # Open webcam
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("✗ ERROR: Could not open webcam")
        return

    print("✓ Webcam opened successfully")
    print(f"✓ Connected to Inference Server at {os.environ.get('INFERENCE_SERVER_URL', 'http://localhost:9001')}")

    frame_count = 0
    fps_limit = 5  # Process 5 frames per second
    frame_interval = 1.0 / fps_limit
    last_process_time = 0

    while True:
        ret, frame = cap.read()

        if not ret:
            print("✗ Failed to read frame from webcam")
            time.sleep(0.1)
            continue

        # Limit processing to target FPS
        current_time = time.time()
        if current_time - last_process_time < frame_interval:
            time.sleep(0.01)
            continue

        last_process_time = current_time
        frame_count += 1

        try:
            # Encode frame as JPEG for sending to inference server
            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode('utf-8')

            # Run workflow on Docker inference server
            result = client.run_workflow(
                workspace_name="edss",
                workflow_id="count-milk-alerts",
                images={"image": frame_b64},
                parameters={}
            )

            # Process the result
            processed_frame = process_workflow_result(result, frame)

        except Exception as e:
            print(f"✗ Error processing frame {frame_count}: {e}")
            processed_frame = frame.copy()

            # Add error message to frame
            cv2.putText(processed_frame, f"Error: {str(e)[:50]}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            with frame_lock:
                last_frame = processed_frame

        time.sleep(0.01)  # Small delay to prevent CPU hammering

    cap.release()

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
        time.sleep(0.033)  # ~30 FPS for display (independent of processing FPS)

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

if __name__ == '__main__':
    print("=" * 60)
    print("Raspberry Pi 4 Milk Bottle Monitoring System (Docker)")
    print("=" * 60)
    print("")
    print("Requirements:")
    print("  1. Docker must be running")
    print("  2. Roboflow Inference Server must be running:")
    print("     sudo docker run -d -p 9001:9001 \\")
    print("       roboflow/roboflow-inference-server-arm-cpu")
    print("")
    print("Starting camera capture and processing...")

    # Start video capture and processing in background thread
    capture_thread = Thread(target=capture_and_process, daemon=True)
    capture_thread.start()

    # Start Flask-SocketIO server
    print("Flask server starting...")
    print("Access the application at:")
    print("  - http://localhost:5050")
    print("  - http://127.0.0.1:5050")
    print("  - http://<raspberry-pi-ip>:5050")
    print("=" * 60)

    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)
