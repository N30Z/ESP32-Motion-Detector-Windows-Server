#!/usr/bin/env python3
"""
ESP32 Motion Detector - Windows Server
--------------------------------------
Flask server for receiving motion-triggered photos and live stream frames
from ESP32-CAM with PIR sensor.

Features:
- POST /upload - Receive motion-triggered photos
- GET /stream - MJPEG live stream
- GET /latest - View latest captured image
- Windows Toast notifications with image preview
- Face recognition placeholder
- Rule-based workflow automation placeholder
"""

import os
import sys
import time
import logging
from datetime import datetime
from pathlib import Path
from threading import Lock
from io import BytesIO

from flask import Flask, request, Response, jsonify, render_template_string
import yaml
from winotify import Notification, audio

# Optional imports for face recognition (placeholder)
# from face_recognition_module import FaceRecognitionPipeline

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load config
CONFIG_FILE = Path(__file__).parent / 'config.yaml'
RULES_FILE = Path(__file__).parent / 'rules.yaml'

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config['server']['log_level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config['server']['log_file']),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Directories
STORAGE_DIR = Path(config['storage']['image_dir'])
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Auth
AUTH_TOKEN = config['security']['auth_token']

# Stream state
latest_frame = None
frame_lock = Lock()
latest_image_path = None

# ============================================================================
# FACE RECOGNITION PLACEHOLDER
# ============================================================================

class FaceRecognitionPipeline:
    """
    PLACEHOLDER: Face Recognition Pipeline

    This is a dummy implementation. Replace with actual face recognition:
    - OpenCV + face_recognition library
    - DeepFace
    - Custom trained model

    Expected output format:
    [
        {
            'name': 'Alice',
            'confidence': 0.95,
            'bbox': [x, y, w, h]
        },
        {
            'name': 'Unknown',
            'confidence': 0.60,
            'bbox': [x, y, w, h]
        }
    ]
    """

    def __init__(self):
        logger.info("Face Recognition Pipeline initialized (PLACEHOLDER)")
        self.enabled = config['face_recognition']['enabled']

    def recognize_faces(self, image_bytes):
        """
        TODO: Implement actual face recognition here

        Args:
            image_bytes: JPEG image as bytes

        Returns:
            List of detected persons with confidence scores
        """
        if not self.enabled:
            return []

        # PLACEHOLDER: Simulate face detection
        logger.debug("PLACEHOLDER: Running face recognition (dummy)")

        # Dummy result - replace with actual implementation
        dummy_result = [
            {
                'name': 'Unknown',
                'confidence': 0.0,
                'bbox': [0, 0, 0, 0]
            }
        ]

        # Real implementation would look like:
        # import face_recognition
        # import numpy as np
        # from PIL import Image
        #
        # img = Image.open(BytesIO(image_bytes))
        # img_array = np.array(img)
        # face_locations = face_recognition.face_locations(img_array)
        # face_encodings = face_recognition.face_encodings(img_array, face_locations)
        #
        # results = []
        # for encoding, location in zip(face_encodings, face_locations):
        #     matches = face_recognition.compare_faces(known_encodings, encoding)
        #     name = "Unknown"
        #     if True in matches:
        #         name = known_names[matches.index(True)]
        #     results.append({'name': name, 'bbox': location, ...})

        return dummy_result

# ============================================================================
# WORKFLOW AUTOMATION PLACEHOLDER
# ============================================================================

class WorkflowEngine:
    """
    PLACEHOLDER: Rule-based workflow automation

    Triggers actions based on detected persons and configured rules.
    Current implementation is a placeholder - extend with:
    - Telegram notifications
    - Home Assistant integration
    - Email alerts
    - Custom webhooks
    - Alarm systems
    """

    def __init__(self, rules_file):
        with open(rules_file, 'r') as f:
            self.rules = yaml.safe_load(f)
        logger.info(f"Workflow Engine initialized with {len(self.rules.get('rules', []))} rules")

    def on_person_detected(self, person_name, confidence, image_path):
        """
        TODO: Implement actual workflow actions here

        Args:
            person_name: Name of detected person (or 'Unknown')
            confidence: Detection confidence (0.0 - 1.0)
            image_path: Path to the captured image
        """
        logger.info(f"WORKFLOW TRIGGER: Person='{person_name}', Confidence={confidence:.2f}")

        # Find matching rules
        for rule in self.rules.get('rules', []):
            if self._rule_matches(rule, person_name, confidence):
                logger.info(f"Rule matched: {rule['name']}")
                self._execute_actions(rule['actions'], person_name, image_path)

    def _rule_matches(self, rule, person_name, confidence):
        """Check if rule conditions match"""
        conditions = rule.get('conditions', {})

        # Check person match
        if 'person' in conditions:
            if conditions['person'] != person_name and conditions['person'] != '*':
                return False

        # Check confidence threshold
        if 'min_confidence' in conditions:
            if confidence < conditions['min_confidence']:
                return False

        return True

    def _execute_actions(self, actions, person_name, image_path):
        """Execute workflow actions"""
        for action in actions:
            action_type = action.get('type')

            if action_type == 'log':
                logger.info(f"ACTION[log]: {action.get('message', 'Person detected').format(person=person_name)}")

            elif action_type == 'webhook':
                # PLACEHOLDER: HTTP webhook call
                logger.info(f"ACTION[webhook]: Would POST to {action.get('url')} (PLACEHOLDER)")
                # Real implementation:
                # import requests
                # requests.post(action['url'], json={'person': person_name, 'image': image_path})

            elif action_type == 'telegram':
                # PLACEHOLDER: Telegram notification
                logger.info(f"ACTION[telegram]: Would send to chat_id={action.get('chat_id')} (PLACEHOLDER)")
                # Real implementation:
                # import telegram
                # bot = telegram.Bot(token=action['bot_token'])
                # bot.send_photo(chat_id=action['chat_id'], photo=open(image_path, 'rb'))

            elif action_type == 'email':
                # PLACEHOLDER: Email notification
                logger.info(f"ACTION[email]: Would send to {action.get('to')} (PLACEHOLDER)")
                # Real implementation:
                # import smtplib
                # from email.mime.multipart import MIMEMultipart
                # ...

            elif action_type == 'home_assistant':
                # PLACEHOLDER: Home Assistant webhook
                logger.info(f"ACTION[home_assistant]: Would trigger {action.get('entity_id')} (PLACEHOLDER)")
                # Real implementation:
                # requests.post(f"{ha_url}/api/webhook/{action['webhook_id']}", ...)

            else:
                logger.warning(f"Unknown action type: {action_type}")

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

app = Flask(__name__)
face_recognition = FaceRecognitionPipeline()
workflow_engine = WorkflowEngine(RULES_FILE)

# ============================================================================
# AUTHENTICATION
# ============================================================================

def check_auth():
    """Check if request has valid authentication token"""
    token = request.headers.get('X-Auth-Token')
    if token != AUTH_TOKEN:
        logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
        return False
    return True

# ============================================================================
# WINDOWS TOAST NOTIFICATIONS
# ============================================================================

def show_toast_notification(image_path, device_id="ESP32-CAM"):
    """
    Show Windows Toast notification with image preview

    Args:
        image_path: Path to the captured image
        device_id: ID of the device that triggered motion
    """
    try:
        # Create toast notification
        toast = Notification(
            app_id="ESP32 Motion Detector",
            title="🚨 Motion Detected!",
            msg=f"Camera: {device_id}\nTime: {datetime.now().strftime('%H:%M:%S')}",
            icon=str(image_path.absolute())  # Windows Toast needs absolute path
        )

        # Set image (hero image in toast)
        toast.set_audio(audio.Default, loop=False)

        # Add action button to view in browser
        toast.add_actions(label="View Latest", launch=f"http://localhost:{config['server']['port']}/latest")

        toast.show()
        logger.info(f"Toast notification shown for {image_path}")

    except Exception as e:
        logger.error(f"Failed to show toast notification: {e}")
        # Fallback: simple notification without image
        try:
            toast = Notification(
                app_id="ESP32 Motion Detector",
                title="Motion Detected!",
                msg=f"Device: {device_id} at {datetime.now().strftime('%H:%M:%S')}"
            )
            toast.show()
        except Exception as e2:
            logger.error(f"Fallback notification also failed: {e2}")

# ============================================================================
# FLASK ROUTES
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'uptime': time.process_time()
    })

@app.route('/upload', methods=['POST'])
def upload():
    """
    Handle motion-triggered photo upload from ESP32

    Expected:
        - X-Auth-Token header
        - multipart/form-data with 'image' file
        - Optional: device_id, timestamp fields
    """
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    # Get image from request
    if 'image' not in request.files:
        logger.error("No image in upload request")
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    device_id = request.form.get('device_id', 'ESP32-CAM')

    # Generate filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{device_id}_{timestamp}.jpg"
    filepath = STORAGE_DIR / filename

    # Save image
    image_file.save(filepath)
    logger.info(f"Image saved: {filepath}")

    # Update latest image reference
    global latest_image_path
    latest_image_path = filepath

    # Read image bytes for processing
    with open(filepath, 'rb') as f:
        image_bytes = f.read()

    # FACE RECOGNITION PIPELINE
    detected_persons = face_recognition.recognize_faces(image_bytes)
    logger.info(f"Face recognition result: {detected_persons}")

    # WORKFLOW AUTOMATION
    for person in detected_persons:
        workflow_engine.on_person_detected(
            person['name'],
            person['confidence'],
            filepath
        )

    # Show Windows notification
    if config['notifications']['enabled']:
        show_toast_notification(filepath, device_id)

    return jsonify({
        'status': 'success',
        'filename': filename,
        'timestamp': timestamp,
        'faces_detected': len(detected_persons),
        'persons': [p['name'] for p in detected_persons]
    })

@app.route('/stream_frame', methods=['POST'])
def stream_frame():
    """
    Receive streaming frame from ESP32 for live view

    Expected:
        - X-Auth-Token header
        - Raw JPEG bytes in body
    """
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    global latest_frame

    # Get frame data
    frame_data = request.get_data()

    if len(frame_data) == 0:
        return jsonify({'error': 'Empty frame'}), 400

    # Update latest frame (thread-safe)
    with frame_lock:
        latest_frame = frame_data

    return jsonify({'status': 'ok'})

@app.route('/stream', methods=['GET'])
def stream():
    """
    MJPEG live stream endpoint

    Serves multipart/x-mixed-replace stream for browser viewing
    """
    # Optional: Check auth via query param for browser access
    token = request.args.get('token')
    if config['security']['require_auth_for_stream'] and token != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    def generate():
        """Generator for MJPEG stream"""
        while True:
            with frame_lock:
                if latest_frame is not None:
                    frame = latest_frame
                else:
                    # Send placeholder if no frame available
                    time.sleep(0.1)
                    continue

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            # ~10 fps
            time.sleep(0.1)

    return Response(
        generate(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/latest', methods=['GET'])
def latest():
    """Show latest captured image in browser"""
    if latest_image_path is None or not latest_image_path.exists():
        return "<h1>No images captured yet</h1><p>Waiting for motion event...</p>", 404

    # Simple HTML viewer
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Latest Motion Event</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #4CAF50; }}
            img {{ max-width: 100%; height: auto; border: 2px solid #4CAF50; }}
            .info {{ background: #333; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>🎥 Latest Motion Event</h1>
        <div class="info">
            <strong>File:</strong> {latest_image_path.name}<br>
            <strong>Time:</strong> {datetime.fromtimestamp(latest_image_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}<br>
            <strong>Size:</strong> {latest_image_path.stat().st_size / 1024:.1f} KB
        </div>
        <img src="/image/{latest_image_path.name}" alt="Latest capture">
        <p><a href="/stream?token={AUTH_TOKEN}" style="color: #4CAF50;">View Live Stream</a></p>
    </body>
    </html>
    """
    return html

@app.route('/image/<filename>', methods=['GET'])
def get_image(filename):
    """Serve stored image"""
    filepath = STORAGE_DIR / filename
    if not filepath.exists():
        return "Image not found", 404

    with open(filepath, 'rb') as f:
        return Response(f.read(), mimetype='image/jpeg')

@app.route('/', methods=['GET'])
def index():
    """Main dashboard"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Motion Detector</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #4CAF50; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            .stream-box {{ background: #000; padding: 10px; margin: 20px 0; }}
            img {{ width: 100%; height: auto; }}
            .button {{
                display: inline-block;
                padding: 10px 20px;
                background: #4CAF50;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 5px;
            }}
            .button:hover {{ background: #45a049; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 ESP32 Motion Detector Dashboard</h1>

            <h2>Live Stream (~10 fps)</h2>
            <div class="stream-box">
                <img src="/stream?token={AUTH_TOKEN}" alt="Live Stream">
            </div>

            <h2>Quick Links</h2>
            <a href="/latest" class="button">📸 Latest Capture</a>
            <a href="/health" class="button">💚 Health Check</a>

            <h2>Info</h2>
            <p>Status: <span style="color: #4CAF50;">●</span> Online</p>
            <p>Storage: {STORAGE_DIR}</p>
        </div>
    </body>
    </html>
    """
    return html

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("ESP32 Motion Detector Server Starting")
    logger.info("=" * 60)
    logger.info(f"Server: http://localhost:{config['server']['port']}")
    logger.info(f"Stream: http://localhost:{config['server']['port']}/stream?token={AUTH_TOKEN}")
    logger.info(f"Storage: {STORAGE_DIR}")
    logger.info(f"Auth Token: {AUTH_TOKEN}")
    logger.info("=" * 60)

    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug'],
        threaded=True
    )
