"""
Flask web application for monitoring milk bottle counts in real-time.
Provides a web interface with two tabs: Live Video and Analytics Graph.
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

# Alert cooldown period (in seconds) - should match Roboflow's SMS cooldown
ALERT_COOLDOWN_SECONDS = 10

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
last_alert_time = 0  # Track when the last alert was sent

# Initialize CSV files if they don't exist
if not os.path.exists(csv_file_path):
    with open(csv_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'flavor', 'count'])

if not os.path.exists(alerts_csv_path):
    with open(alerts_csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'missing_categories'])

def save_counts_to_csv(timestamp, counts):
    """Save counts to CSV file."""
    with open(csv_file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for flavor in ["whole", "1pct", "2pct"]:
            count = counts.get(flavor, 0)
            writer.writerow([timestamp, flavor, count])

def save_alert_to_csv(timestamp, missing_categories):
    """Save alert to CSV file."""
    category_names = {
        "whole": "Whole Milk",
        "1pct": "1% Milk",
        "2pct": "2% Milk"
    }
    missing_names = [category_names.get(m, m) for m in missing_categories]
    missing_text = ", ".join(missing_names)

    with open(alerts_csv_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([timestamp, missing_text])

def get_recent_alerts(limit=50):
    """Get recent alerts from CSV file."""
    alerts = []
    try:
        with open(alerts_csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                alerts.append(row)
        # Return most recent alerts first
        return list(reversed(alerts[-limit:]))
    except FileNotFoundError:
        return []

def get_graph_data():
    """Get data for plotting (past hour only)."""
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
        # An alert is sent only if:
        # 1. There are missing categories
        # 2. Cooldown period has passed since last alert
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

        # Draw count box in top-left corner
        box_x, box_y = 10, 10
        box_width = 250
        line_height = 35
        padding = 15

        # Calculate box height based on number of categories
        num_lines = 3  # whole, 1pct, 2pct
        box_height = padding * 2 + line_height * num_lines

        # Draw semi-transparent background for counts
        overlay = display_image.copy()
        cv2.rectangle(overlay, (box_x, box_y), (box_x + box_width, box_y + box_height), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, display_image, 0.3, 0, display_image)

        # Draw border
        cv2.rectangle(display_image, (box_x, box_y), (box_x + box_width, box_y + box_height), (255, 255, 255), 2)

        # Display counts
        y_offset = box_y + padding + 25
        categories = [
            ("whole", "Whole Milk"),
            ("1pct", "1% Milk"),
            ("2pct", "2% Milk")
        ]

        for key, label in categories:
            count = counts.get(key, 0)
            text = f"{label}: {count}"
            cv2.putText(display_image, text, (box_x + padding, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += line_height

        # Display missing categories alert if any
        if missing:
            img_height = display_image.shape[0]
            alert_height = 80
            alert_y = img_height - alert_height - 20
            alert_x = 10
            alert_width = display_image.shape[1] - 20

            # Draw red alert box
            overlay = display_image.copy()
            cv2.rectangle(overlay, (alert_x, alert_y), (alert_x + alert_width, alert_y + alert_height), (0, 0, 200), -1)
            cv2.addWeighted(overlay, 0.8, display_image, 0.2, 0, display_image)

            # Draw border
            cv2.rectangle(display_image, (alert_x, alert_y), (alert_x + alert_width, alert_y + alert_height), (0, 0, 255), 3)

            # Format missing categories
            category_names = {
                "whole": "Whole Milk",
                "1pct": "1% Milk",
                "2pct": "2% Milk"
            }
            missing_names = [category_names.get(m, m) for m in missing]
            missing_text = ", ".join(missing_names)

            # Draw "MISSING:" label
            cv2.putText(display_image, "MISSING:", (alert_x + 20, alert_y + 35),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)

            # Draw missing category names
            cv2.putText(display_image, missing_text, (alert_x + 20, alert_y + 65),
                       cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)

        # Store frame for web streaming
        with frame_lock:
            last_frame = display_image.copy()

def generate_frames():
    """Generator function to stream video frames."""
    while True:
        with frame_lock:
            if last_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', last_frame)
                if ret:
                    frame = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def index():
    """Render main page."""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/graph_data')
def graph_data():
    """API endpoint for graph data."""
    return jsonify(get_graph_data())

@app.route('/alerts')
def alerts():
    """API endpoint for alerts data."""
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
    """Start the Roboflow inference pipeline."""
    os.environ["LOCAL_INFERENCE_API_URL"] = "http://localhost:9001"

    pipeline = InferencePipeline.init_with_workflow(
        api_key=os.environ.get("ROBOFLOW_API_KEY"),
        workspace_name="edss",
        workflow_id="count-milk-alerts",
        video_reference=0,
        max_fps=10,
        on_prediction=my_sink
    )

    pipeline.start()
    pipeline.join()

if __name__ == '__main__':
    # Start inference pipeline in a separate thread
    from threading import Thread
    pipeline_thread = Thread(target=start_pipeline, daemon=True)
    pipeline_thread.start()

    # Start Flask-SocketIO server
    print("=" * 60)
    print("Flask server starting...")
    print("Access the application at:")
    print("  - http://localhost:5050")
    print("  - http://127.0.0.1:5050")
    print("=" * 60)
    socketio.run(app, host='0.0.0.0', port=5050, debug=False, allow_unsafe_werkzeug=True)
