# 1. Configure to use local Docker inference server
import os
os.environ["LOCAL_INFERENCE_API_URL"] = "http://localhost:9001"

# Load environment variables from config.env
from dotenv import load_dotenv
load_dotenv("config.env")

# 2. Import the InferencePipeline library
from inference import InferencePipeline
import cv2
import time
from twilio.rest import Client
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import csv
from collections import defaultdict
import threading

# Twilio configuration
TWILIO_API_KEY_SID = os.environ.get("TWILIO_API_KEY_SID")
TWILIO_API_KEY_SECRET = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")  # Your main Account SID (starts with AC)
TWILIO_FROM_NUMBER = os.environ.get("TWILIO_FROM_NUMBER")
TWILIO_TO_NUMBER = os.environ.get("TWILIO_TO_NUMBER")
SMS_COOLDOWN_SECONDS = 10

# Initialize Twilio client with API Key
twilio_client = Client(TWILIO_API_KEY_SID, TWILIO_API_KEY_SECRET, TWILIO_ACCOUNT_SID)

# Track last SMS sent time
last_sms_time = 0
# Track last print time for results
last_print_time = 0
# Track last data save time (5 second intervals)
last_save_time = 0
# CSV file path
csv_file_path = "milk_bottle_counts.csv"

# Data storage for plotting (in-memory for past hour)
data_history = {
    "whole": [],
    "1pct": [],
    "2pct": []
}
timestamps = []

# Initialize CSV file if it doesn't exist
if not os.path.exists(csv_file_path):
    with open(csv_file_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'flavor', 'count'])

# Set up matplotlib for real-time plotting
plt.ion()
fig, ax = plt.subplots(figsize=(10, 6))
colors = {
    "whole": "blue",
    "1pct": "green",
    "2pct": "red"
}
category_names = {
    "whole": "Whole Milk",
    "1pct": "1% Milk",
    "2pct": "2% Milk"
}

def save_counts_to_csv(timestamp, counts):
    """Save counts to CSV file."""
    with open(csv_file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        for flavor in ["whole", "1pct", "2pct"]:
            count = counts.get(flavor, 0)
            writer.writerow([timestamp, flavor, count])

def update_plot():
    """Update the matplotlib plot with latest data."""
    ax.clear()

    # Filter data to only show past hour
    one_hour_ago = datetime.now() - timedelta(hours=1)

    for flavor in ["whole", "1pct", "2pct"]:
        # Filter timestamps and data for past hour
        filtered_times = []
        filtered_counts = []

        for i, ts in enumerate(timestamps):
            if ts >= one_hour_ago:
                filtered_times.append(ts)
                filtered_counts.append(data_history[flavor][i] if i < len(data_history[flavor]) else 0)

        if filtered_times:
            ax.plot(filtered_times, filtered_counts,
                   label=category_names[flavor],
                   color=colors[flavor],
                   linewidth=2,
                   marker='o',
                   markersize=4)

    ax.set_xlabel('Time')
    ax.set_ylabel('Count')
    ax.set_title('Milk Bottle Counts (Past Hour)')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Format x-axis to show time nicely
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    plt.xticks(rotation=45)
    plt.tight_layout()

    try:
        plt.pause(0.01)
    except:
        pass

def send_sms_alert(missing_categories):
    """Send SMS alert for missing milk categories with cooldown."""
    global last_sms_time

    current_time = time.time()

    # Check if cooldown period has passed
    if current_time - last_sms_time < SMS_COOLDOWN_SECONDS:
        return

    # Format missing categories for SMS
    category_names = {
        "whole": "Whole Milk",
        "1pct": "1% Milk",
        "2pct": "2% Milk"
    }
    missing_names = [category_names.get(m, m) for m in missing_categories]
    missing_text = ", ".join(missing_names)

    # Send SMS
    try:
        message = twilio_client.messages.create(
            body=f"ALERT: Missing milk bottles detected!\n\nMissing: {missing_text}",
            from_=TWILIO_FROM_NUMBER,
            to=TWILIO_TO_NUMBER
        )
        last_sms_time = current_time
        print(f"SMS sent successfully! SID: {message.sid}")
        print(f"Status: {message.status}")

        # Fetch updated message status after a moment
        import time as time_module
        time_module.sleep(2)
        updated_message = twilio_client.messages(message.sid).fetch()
        print(f"Updated Status: {updated_message.status}")
        if updated_message.error_code:
            print(f"Error Code: {updated_message.error_code}")
            print(f"Error Message: {updated_message.error_message}")
            # Twilio error 30032 typically means:
            # - Trial account trying to send to unverified number
            # - From number not SMS-capable
            # Check: https://www.twilio.com/docs/api/errors/30032
            print(f"From: {TWILIO_FROM_NUMBER}, To: {TWILIO_TO_NUMBER}")
            print(f"Is {TWILIO_TO_NUMBER} verified in your Twilio console?")
    except Exception as e:
        print(f"Error sending SMS: {e}")

def my_sink(result, video_frame):
    global last_print_time, last_save_time, timestamps

    if result.get("annotated_image"):
        # Get the annotated image
        display_image = result["annotated_image"].numpy_image.copy()

        # Get counts and missing categories
        counts = result.get("counts", {})
        missing = result.get("missing", [])

        # Save data every 5 seconds
        current_time = time.time()
        if current_time - last_save_time >= 5:
            timestamp = datetime.now()

            # Save to CSV
            save_counts_to_csv(timestamp.strftime('%Y-%m-%d %H:%M:%S'), counts)

            # Update in-memory data for plotting
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

            # Update plot
            update_plot()

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

            # Send SMS alert
            #send_sms_alert(missing)

        # Display the image
        cv2.imshow("Workflow Image", display_image)
        cv2.waitKey(1)

    # Print results every 2 seconds
    current_time = time.time()
    if current_time - last_print_time >= 2:
        print(result)
        last_print_time = current_time


# 2. Initialize a pipeline object
pipeline = InferencePipeline.init_with_workflow(
    api_key=os.environ.get("ROBOFLOW_API_KEY"),
    workspace_name="edss",
    workflow_id="count-milk-alerts",
    video_reference=0, # Path to video, device id (int, usually 0 for built in webcams), or RTSP stream url
    max_fps=10,
    on_prediction=my_sink
)

# 3. Start the pipeline and wait for it to finish
pipeline.start()
pipeline.join()
