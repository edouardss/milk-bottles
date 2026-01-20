from inference_sdk import InferenceHTTPClient
import cv2
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_replenish_email(categories_with_zero):
    """
    Send an email notification when categories have zero counts.
    
    Args:
        categories_with_zero: List of category names that have zero counts
    """
    if not categories_with_zero:
        return
    
    # Email configuration
    sender = "edouardss+milk@gmail.com"
    recipient = "edouardss+roboflow@gmail.com"
    subject = f"replenish {', '.join(categories_with_zero)}"
    
    # Create email message
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    
    # Email body
    body = f"The following milk categories need to be replenished: {', '.join(categories_with_zero)}"
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        # Connect to Gmail SMTP server
        # Note: You may need to use an app-specific password if 2FA is enabled
        # Get password from environment variable or replace with your app password
        import os
        email_password = os.getenv('GMAIL_APP_PASSWORD', '')  # Set GMAIL_APP_PASSWORD env var
        
        if not email_password:
            print("Warning: GMAIL_APP_PASSWORD not set. Email not sent.")
            return
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, email_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent: {subject}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        # Don't raise - allow the program to continue even if email fails

# Connect to local Docker inference server
client = InferenceHTTPClient(
    api_url="http://localhost:9001",  # Local Docker container (use http:// not https://)
    api_key="OH6UuyaQOXGMccE2j6AT"  # From Roboflow dashboard
)

# Use API v0 for serverless (supports project/version format)
client.select_api_v0()

# Track email sending to avoid spamming
last_email_state = None
last_email_time = None
EMAIL_COOLDOWN_SECONDS = 10  # 10 second cooldown between emails
CONSECUTIVE_ZEROS_REQUIRED = 10  # Number of consecutive frames with 0 count before sending email

# Track startup time for initial cooldown period
startup_time = time.time()

# Track consecutive zero counts for each category
consecutive_zeros = {category: 0 for category in ["whole", "1pct", "2pct"]}

# Open video
cap = cv2.VideoCapture(0)  # 0 for webcam (must be integer, not string)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    
    # Run inference
    # For serverless API v0, use "project/version" format (workspace determined by API key)
    result = client.infer(frame, model_id="milk-detector-lkq28/3")
    
    # Define the three classes we want to track
    classes_to_track = ["whole", "1pct", "2pct"]
    
    # Initialize counts for all classes (start at 0)
    counts = {class_name: 0 for class_name in classes_to_track}
    
    # Count detections from predictions
    for prediction in result['predictions']:
        flavor = prediction['class']
        if flavor in counts:
            counts[flavor] += 1
    
    # Update consecutive zero counts for each category
    current_time = time.time()
    categories_with_zero = []
    
    for flavor in classes_to_track:
        if counts[flavor] == 0:
            consecutive_zeros[flavor] += 1
            # Only add to categories_with_zero if it has been 0 for required consecutive frames
            if consecutive_zeros[flavor] >= CONSECUTIVE_ZEROS_REQUIRED:
                categories_with_zero.append(flavor)
        else:
            # Reset consecutive count if category is no longer 0
            consecutive_zeros[flavor] = 0
    
    # Check startup cooldown period (no emails for first 10 seconds)
    startup_cooldown_passed = (current_time - startup_time) >= EMAIL_COOLDOWN_SECONDS
    
    # Send email if any category has zero count (with startup cooldown and email cooldown)
    if categories_with_zero and startup_cooldown_passed:
        current_state = tuple(sorted(categories_with_zero))
        
        # Check if state changed and email cooldown period has passed
        state_changed = current_state != last_email_state
        email_cooldown_passed = (last_email_time is None or 
                                 (current_time - last_email_time) >= EMAIL_COOLDOWN_SECONDS)
        
        if state_changed and email_cooldown_passed:
            send_replenish_email(categories_with_zero)
            last_email_state = current_state
            last_email_time = current_time
    
    # Display counts for all three classes (always show, even if 0)
    y_offset = 30
    for flavor in classes_to_track:
        count = counts[flavor]
        text = f"{flavor}: {count}"
        cv2.putText(frame, text, (10, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        y_offset += 40
    
    # Draw bounding boxes
    for pred in result['predictions']:
        x, y, w, h = pred['x'], pred['y'], pred['width'], pred['height']
        x1, y1 = int(x - w/2), int(y - h/2)
        x2, y2 = int(x + w/2), int(y + h/2)
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, pred['class'], (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    cv2.imshow('Yogurt Counter', frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()