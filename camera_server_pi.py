"""
Simple camera server for Raspberry Pi.
Captures video from webcam and streams it over HTTP.
Run this on the Pi, and have your Mac connect to it.
"""

from flask import Flask, Response
import cv2
import os

app = Flask(__name__)

# Camera configuration
CAMERA_INDEX = 0  # Change if using different camera
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
FPS = 30

def generate_frames():
    """Capture frames from camera and yield as MJPEG stream."""
    camera = cv2.VideoCapture(CAMERA_INDEX)

    # Set camera properties
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    camera.set(cv2.CAP_PROP_FPS, FPS)

    if not camera.isOpened():
        print("✗ ERROR: Could not open camera")
        return

    print(f"✓ Camera opened successfully")
    print(f"  Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}")
    print(f"  FPS: {FPS}")

    try:
        while True:
            success, frame = camera.read()

            if not success:
                print("✗ Failed to read frame")
                break

            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

            if not ret:
                continue

            frame_bytes = buffer.tobytes()

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    finally:
        camera.release()
        print("Camera released")

@app.route('/')
def index():
    """Info page."""
    return f"""
    <html>
    <head><title>Pi Camera Server</title></head>
    <body style="font-family: monospace; padding: 20px;">
        <h1>Raspberry Pi Camera Server</h1>
        <p>Status: <strong style="color: green;">Running</strong></p>
        <p>Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}</p>
        <p>FPS: {FPS}</p>
        <hr>
        <h2>Camera Feed:</h2>
        <img src="/video_feed" style="max-width: 100%; border: 2px solid #333;">
        <hr>
        <p>Use this URL in your Mac application: <code>http://{os.popen('hostname -I').read().strip().split()[0]}:8888/video_feed</code></p>
    </body>
    </html>
    """

@app.route('/video_feed')
def video_feed():
    """Video streaming route."""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok', 'camera': 'active'}

if __name__ == '__main__':
    print("=" * 60)
    print("Raspberry Pi Camera Server")
    print("=" * 60)
    print("")
    print("Starting server on port 8888...")
    print("This will stream camera feed to your Mac")
    print("(Port 8080 is used by Viam)")
    print("")
    print("Access from your Mac at:")

    # Get Pi's IP address
    import socket
    hostname = socket.gethostname()
    try:
        ip = socket.gethostbyname(hostname)
        print(f"  http://{ip}:8888")
    except:
        pass

    print(f"  http://edsspi3.local:8888")
    print("")
    print("=" * 60)

    # Run Flask server
    app.run(host='0.0.0.0', port=8888, debug=False, threaded=True)
