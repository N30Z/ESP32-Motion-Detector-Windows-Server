#!/usr/bin/env python3
"""
ESP32 Motion Detector - Windows Server with Face Recognition
=============================================================
Flask server with YuNet/SFace face recognition, person management, and auto-learning.

Features:
- POST /upload - Receive motion-triggered photos with face recognition
- GET /stream - MJPEG live stream
- GET /latest - View latest captured image
- GET /config - Configuration UI
- GET /persons - Person management UI
- Windows Toast notifications with person info
- Auto-learning and person differentiation
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from io import BytesIO

from flask import Flask, request, Response, jsonify, render_template, redirect, url_for
import yaml

# Import our modules
from database import Database
from face_recognition_cv import FaceRecognitionCV
from notifications import get_notification_backend

# ============================================================================
# CONFIGURATION
# ============================================================================

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

FACES_DIR = Path(config['face_recognition']['faces_dir'])
FACES_DIR.mkdir(parents=True, exist_ok=True)

# Auth
AUTH_TOKEN = config['security']['auth_token']

# Stream state
latest_frame = None
frame_lock = Lock()
latest_image_path = None
latest_event_id = None

# Auto-learning cooldown tracking
learning_cooldown = {}  # {person_id: last_learning_timestamp}

# ============================================================================
# INITIALIZE COMPONENTS
# ============================================================================

app = Flask(__name__)
db = Database(config['face_recognition']['db_path'])
face_rec = FaceRecognitionCV(config)

# Initialize notification backend
notification_backend = None
if config['notifications']['enabled']:
    backend_type = config['notifications']['backend']
    notification_backend = get_notification_backend(backend_type, config)
    logger.info(f"Notification backend initialized: {backend_type}")

# ============================================================================
# WORKFLOW AUTOMATION (kept from original)
# ============================================================================

class WorkflowEngine:
    """Rule-based workflow automation"""

    def __init__(self, rules_file):
        with open(rules_file, 'r') as f:
            self.rules = yaml.safe_load(f)
        logger.info(f"Workflow Engine initialized with {len(self.rules.get('rules', []))} rules")

    def on_person_detected(self, person_name, confidence, status, image_path):
        """Execute workflow actions"""
        logger.info(f"WORKFLOW: Person='{person_name}', Confidence={confidence:.1f}%, Status={status}")

        for rule in self.rules.get('rules', []):
            if self._rule_matches(rule, person_name, confidence):
                logger.info(f"Rule matched: {rule['name']}")
                self._execute_actions(rule['actions'], person_name, image_path)

    def _rule_matches(self, rule, person_name, confidence):
        """Check if rule conditions match"""
        conditions = rule.get('conditions', {})

        if 'person' in conditions:
            if conditions['person'] != person_name and conditions['person'] != '*':
                return False

        if 'min_confidence' in conditions:
            if confidence < conditions['min_confidence'] * 100:
                return False

        return True

    def _execute_actions(self, actions, person_name, image_path):
        """Execute workflow actions (placeholder implementations)"""
        for action in actions:
            action_type = action.get('type')

            if action_type == 'log':
                logger.info(f"ACTION[log]: {action.get('message', '').format(person=person_name)}")

            elif action_type == 'webhook':
                logger.info(f"ACTION[webhook]: Would POST to {action.get('url')} (PLACEHOLDER)")

            elif action_type == 'telegram':
                logger.info(f"ACTION[telegram]: Would send to {action.get('chat_id')} (PLACEHOLDER)")

            else:
                logger.warning(f"Unknown action type: {action_type}")

workflow_engine = WorkflowEngine(RULES_FILE)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def check_auth():
    """Check if request has valid authentication token"""
    token = request.headers.get('X-Auth-Token')
    if token != AUTH_TOKEN:
        logger.warning(f"Unauthorized access attempt from {request.remote_addr}")
        return False
    return True

def save_face_crop(person_id: int, face_crop_bytes: bytes, event_id: int) -> Path:
    """Save face crop to disk"""
    person_dir = FACES_DIR / f"person_{person_id}"
    person_dir.mkdir(parents=True, exist_ok=True)

    filename = f"event_{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = person_dir / filename

    with open(filepath, 'wb') as f:
        f.write(face_crop_bytes)

    return filepath

def can_auto_learn(person_id: int) -> bool:
    """Check if auto-learning is allowed (cooldown check)"""
    if not config['face_recognition']['auto_learning']['enabled']:
        return False

    cooldown_seconds = config['face_recognition']['auto_learning']['cooldown_seconds']
    last_learning = learning_cooldown.get(person_id)

    if last_learning is None:
        return True

    elapsed = (datetime.now() - last_learning).total_seconds()
    return elapsed >= cooldown_seconds

def auto_learn_face(person_id: int, face_result: dict, event_id: int):
    """Auto-learn face sample if quality is good"""
    auto_learning = config['face_recognition']['auto_learning']

    if not auto_learning['enabled']:
        return

    # Check match status (only GREEN if configured)
    if auto_learning['only_green_matches']:
        if face_result['match_result']['status'] != 'GREEN':
            logger.debug(f"Auto-learning skipped: not GREEN match")
            return

    # Check quality
    if not face_rec.is_quality_acceptable({'bbox': face_result['bbox'], 'quality_score': face_result['quality_score']}):
        logger.debug(f"Auto-learning skipped: low quality")
        return

    # Check cooldown
    if not can_auto_learn(person_id):
        logger.debug(f"Auto-learning skipped: cooldown active")
        return

    # Check sample limit
    current_count = db.count_face_samples(person_id)
    max_samples = auto_learning['max_samples_per_person']

    if current_count >= max_samples:
        # Replace oldest or lowest quality
        if auto_learning['replace_strategy'] == 'oldest':
            old_sample_id = db.get_oldest_face_sample(person_id)
            if old_sample_id:
                db.delete_face_sample(old_sample_id)
                logger.info(f"Replaced oldest sample for person {person_id}")

    # Save face crop
    face_crop_path = save_face_crop(person_id, face_result['face_crop'], event_id)

    # Add to database
    db.add_face_sample(
        person_id=person_id,
        embedding=face_result['embedding'],
        image_path=str(face_crop_path),
        quality_score=face_result['quality_score'],
        bbox=face_result['bbox']
    )

    # Update cooldown
    learning_cooldown[person_id] = datetime.now()

    logger.info(f"✓ Auto-learned new sample for person {person_id} (quality={face_result['quality_score']:.2f})")

def show_notification(person_name: str, confidence: float, status: str, image_path: Path, is_new_person: bool = False):
    """Show notification with person info using configured backend"""
    if not notification_backend:
        return

    try:
        # Determine message based on status
        if is_new_person:
            title = "🆕 Neue Person erkannt!"
            msg = f"Person: {person_name}\nStatus: Neu erstellt"
        elif status == 'GREEN':
            title = "✅ Person erkannt"
            msg = f"Person: {person_name}\nConfidence: {confidence:.0f}%\nStatus: Zuverlässig"
        elif status == 'YELLOW':
            title = "⚠️ Person erkannt (unsicher)"
            msg = f"Person: {person_name}\nConfidence: {confidence:.0f}%\nStatus: Unsicher"
        else:
            title = "❓ Unbekannte Person"
            msg = f"Keine Übereinstimmung gefunden"

        # Show notification via backend
        url = f"http://localhost:{config['server']['port']}/latest"
        notification_backend.show_notification(title, msg, image_path, url)
        logger.info(f"Notification shown: {person_name} ({status})")

    except Exception as e:
        logger.error(f"Failed to show notification: {e}")

# ============================================================================
# FLASK ROUTES - API
# ============================================================================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    stats = db.get_stats()
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'face_recognition_enabled': face_rec.enabled,
        'database_stats': stats
    })

@app.route('/api/client/config', methods=['GET'])
def get_client_config():
    """
    API endpoint for clients to fetch their configuration
    Returns the client configuration template with auth token from server config
    """
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    # Load client config template
    client_config_file = Path(__file__).parent / 'client_config_template.yaml'
    if client_config_file.exists():
        with open(client_config_file, 'r') as f:
            client_config = yaml.safe_load(f)
    else:
        # Return default client config if template doesn't exist
        client_config = {
            'server': {
                'url': f"http://{config['server']['host']}:{config['server']['port']}",
                'auth_token': config['security']['auth_token'],
                'device_id': 'Client-{hostname}'
            },
            'pir': {'gpio_pin': 17},
            'motion': {'cooldown_seconds': 5},
            'camera': {
                'resolution': [1280, 720],
                'jpeg_quality': 85,
                'device_index': 0
            },
            'streaming': {'enabled': False, 'fps': 5},
            'logging': {'level': 'INFO', 'file': './logs/client.log'}
        }

    # Always sync auth token with server
    client_config['server']['auth_token'] = config['security']['auth_token']

    logger.info("Client configuration requested")
    return jsonify(client_config)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle motion-triggered photo upload with face recognition"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    if 'image' not in request.files:
        logger.error("No image in upload request")
        return jsonify({'error': 'No image provided'}), 400

    image_file = request.files['image']
    device_id = request.form.get('device_id', 'ESP32-CAM')

    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{device_id}_{timestamp}.jpg"
    filepath = STORAGE_DIR / filename

    # Save image
    image_file.save(filepath)
    logger.info(f"Image saved: {filepath}")

    # Update latest image reference
    global latest_image_path, latest_event_id
    latest_image_path = filepath

    # Read image bytes for processing
    with open(filepath, 'rb') as f:
        image_bytes = f.read()

    # FACE RECOGNITION PIPELINE
    faces_detected = []
    event_id = None

    if face_rec.enabled:
        # Get all known embeddings from DB
        known_embeddings = db.get_all_embeddings()

        # Process image
        face_results = face_rec.process_image(image_bytes, known_embeddings)

        if face_results:
            # Process each detected face
            for face_result in face_results:
                match = face_result['match_result']
                person_id = match['person_id']
                person_name = None
                is_new_person = False

                # Create event record
                event_id = db.create_event(
                    image_path=str(filepath),
                    person_id=person_id,
                    confidence=match['confidence'] / 100.0,
                    distance=match['distance'],
                    margin=match['margin'],
                    status=match['status'],
                    device_id=device_id
                )

                latest_event_id = event_id

                if match['status'] == 'UNKNOWN' and config['face_recognition']['auto_create_person']:
                    # Create new person
                    person_id = db.create_person()
                    person = db.get_person(person_id)
                    person_name = person['name']
                    is_new_person = True

                    # Save face crop and add sample
                    face_crop_path = save_face_crop(person_id, face_result['face_crop'], event_id)
                    db.add_face_sample(
                        person_id=person_id,
                        embedding=face_result['embedding'],
                        image_path=str(face_crop_path),
                        quality_score=face_result['quality_score'],
                        bbox=face_result['bbox']
                    )

                    # Update event with new person
                    db.conn.execute(
                        "UPDATE event SET person_id = ? WHERE id = ?",
                        (person_id, event_id)
                    )
                    db.conn.commit()

                    logger.info(f"✨ Created new person: {person_name} (ID: {person_id})")

                elif person_id:
                    # Existing person matched
                    person = db.get_person(person_id)
                    person_name = person['name']

                    # Auto-learning
                    auto_learn_face(person_id, face_result, event_id)

                else:
                    person_name = "Unknown"

                faces_detected.append({
                    'person_id': person_id,
                    'person_name': person_name,
                    'confidence': match['confidence'],
                    'status': match['status'],
                    'is_new': is_new_person
                })

                # Workflow automation
                workflow_engine.on_person_detected(
                    person_name,
                    match['confidence'],
                    match['status'],
                    filepath
                )

                # Notification (only for first face)
                if config['notifications']['enabled'] and len(faces_detected) == 1:
                    show_notification(
                        person_name,
                        match['confidence'],
                        match['status'],
                        filepath,
                        is_new_person
                    )

        else:
            # No faces detected
            event_id = db.create_event(
                image_path=str(filepath),
                status='NO_FACE',
                device_id=device_id
            )
            latest_event_id = event_id
            logger.info("No faces detected in image")

    else:
        # Face recognition disabled
        logger.debug("Face recognition disabled")

    return jsonify({
        'status': 'success',
        'filename': filename,
        'timestamp': timestamp,
        'faces_detected': len(faces_detected),
        'faces': faces_detected
    })

@app.route('/stream_frame', methods=['POST'])
def stream_frame():
    """Receive streaming frame from ESP32"""
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    global latest_frame
    frame_data = request.get_data()

    if len(frame_data) == 0:
        return jsonify({'error': 'Empty frame'}), 400

    with frame_lock:
        latest_frame = frame_data

    return jsonify({'status': 'ok'})

@app.route('/stream', methods=['GET'])
def stream():
    """MJPEG live stream endpoint"""
    token = request.args.get('token')
    if config['security']['require_auth_for_stream'] and token != AUTH_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401

    def generate():
        while True:
            with frame_lock:
                if latest_frame is not None:
                    frame = latest_frame
                else:
                    time.sleep(0.1)
                    continue

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.1)

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/latest', methods=['GET'])
def latest():
    """Show latest captured image with face recognition results"""
    if latest_event_id is None:
        return "<h1>No events yet</h1><p>Waiting for motion...</p>", 404

    event = db.get_latest_event()

    if not event:
        return "<h1>No events yet</h1>", 404

    # Build face info HTML
    faces_html = ""
    if event['person_id']:
        person = db.get_person(event['person_id'])
        status_emoji = {'GREEN': '✅', 'YELLOW': '⚠️', 'UNKNOWN': '❓'}.get(event['status'], '❓')

        faces_html = f"""
        <div class="face-info {event['status'].lower()}">
            <h3>{status_emoji} Person erkannt</h3>
            <p><strong>Name:</strong> {person['name']}</p>
            <p><strong>Confidence:</strong> {event['confidence'] * 100:.1f}%</p>
            <p><strong>Status:</strong> {event['status']}</p>
            <p><strong>Distance:</strong> {event['distance']:.3f}</p>
            <p><strong>Margin:</strong> {event['margin']:.3f}</p>
            <p><a href="/persons/{person['id']}">Person Details →</a></p>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Latest Event</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #1a1a1a; color: #fff; }}
            h1 {{ color: #4CAF50; }}
            img {{ max-width: 100%; height: auto; border: 2px solid #4CAF50; }}
            .info {{ background: #333; padding: 15px; margin: 15px 0; border-radius: 5px; }}
            .face-info {{ background: #2a2a2a; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #4CAF50; }}
            .face-info.green {{ border-left-color: #4CAF50; }}
            .face-info.yellow {{ border-left-color: #FFC107; }}
            .face-info.unknown {{ border-left-color: #999; }}
            a {{ color: #4CAF50; text-decoration: none; }}
            a:hover {{ text-decoration: underline; }}
        </style>
    </head>
    <body>
        <h1>🎥 Latest Motion Event</h1>
        <div class="info">
            <strong>Time:</strong> {event['timestamp']}<br>
            <strong>Device:</strong> {event['device_id'] or 'Unknown'}<br>
            <strong>Image:</strong> {Path(event['image_path']).name}
        </div>

        {faces_html}

        <img src="/image/{Path(event['image_path']).name}" alt="Latest capture">

        <p><a href="/">← Dashboard</a> | <a href="/persons">Personen verwalten</a></p>
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

# ============================================================================
# FLASK ROUTES - WEB UI
# ============================================================================

@app.route('/', methods=['GET'])
def index():
    """Main dashboard"""
    stats = db.get_stats()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>ESP32 Motion Detector</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h1>🎥 ESP32 Motion Detector</h1>

            <div class="stats">
                <div class="stat-box">
                    <h3>{stats['total_persons']}</h3>
                    <p>Personen</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['total_samples']}</h3>
                    <p>Samples</p>
                </div>
                <div class="stat-box">
                    <h3>{stats['total_events']}</h3>
                    <p>Events</p>
                </div>
            </div>

            <h2>Live Stream (~10 fps)</h2>
            <div class="stream-box">
                <img src="/stream?token={AUTH_TOKEN}" alt="Live Stream" style="width:100%">
            </div>

            <h2>Quick Links</h2>
            <a href="/latest" class="button">📸 Latest Event</a>
            <a href="/persons" class="button">👥 Personen verwalten</a>
            <a href="/config" class="button">⚙️ Konfiguration</a>
            <a href="/events" class="button">📋 Event-Historie</a>
            <a href="/health" class="button">💚 Health Check</a>

            <h2>Status</h2>
            <p>Face Recognition: <span class="{'status-on' if face_rec.enabled else 'status-off'}">{' ON' if face_rec.enabled else 'OFF'}</span></p>
            <p>Storage: {STORAGE_DIR}</p>
        </div>
    </body>
    </html>
    """
    return html

@app.route('/config', methods=['GET', 'POST'])
def config_page():
    """Configuration page"""
    # Load or create client config template
    client_config_file = Path(__file__).parent / 'client_config_template.yaml'
    if client_config_file.exists():
        with open(client_config_file, 'r') as f:
            client_config = yaml.safe_load(f)
    else:
        # Default client config template
        client_config = {
            'server': {
                'url': 'http://localhost:5000',
                'device_id': 'Client-{hostname}'
            },
            'pir': {'gpio_pin': 17},
            'motion': {'cooldown_seconds': 5},
            'camera': {
                'resolution': [1280, 720],
                'jpeg_quality': 85,
                'device_index': 0
            },
            'streaming': {'enabled': False, 'fps': 5},
            'logging': {'level': 'INFO', 'file': './logs/client.log'}
        }

    if request.method == 'POST':
        # Save config
        try:
            # Server settings
            config['server']['host'] = request.form.get('server_host', '0.0.0.0')
            config['server']['port'] = int(request.form.get('server_port', 5000))
            config['server']['debug'] = request.form.get('server_debug') == 'on'
            config['server']['log_level'] = request.form.get('server_log_level', 'INFO')
            config['server']['log_file'] = request.form.get('server_log_file', 'server.log')

            # Security settings
            config['security']['auth_token'] = request.form.get('auth_token', 'YOUR_SECRET_TOKEN_CHANGE_ME_12345')
            config['security']['require_auth_for_stream'] = request.form.get('require_auth_for_stream') == 'on'

            # Storage settings
            config['storage']['image_dir'] = request.form.get('storage_image_dir', './captured_images')
            config['storage']['max_images'] = int(request.form.get('storage_max_images', 1000))
            config['storage']['max_age_days'] = int(request.form.get('storage_max_age_days', 30))

            # Notification settings
            config['notifications']['enabled'] = request.form.get('notifications_enabled') == 'on'
            config['notifications']['backend'] = request.form.get('notifications_backend', 'windows_toast')
            config['notifications']['sound'] = request.form.get('notifications_sound') == 'on'

            # Face recognition settings
            config['face_recognition']['enabled'] = request.form.get('face_recognition_enabled') == 'on'
            config['face_recognition']['db_path'] = request.form.get('face_db_path', './faces.db')
            config['face_recognition']['faces_dir'] = request.form.get('faces_dir', './faces_db')
            config['face_recognition']['threshold_strict'] = float(request.form.get('threshold_strict', 0.35))
            config['face_recognition']['threshold_loose'] = float(request.form.get('threshold_loose', 0.50))
            config['face_recognition']['margin_strict'] = float(request.form.get('margin_strict', 0.15))
            config['face_recognition']['margin_loose'] = float(request.form.get('margin_loose', 0.08))
            config['face_recognition']['min_face_size'] = int(request.form.get('min_face_size', 10000))
            config['face_recognition']['min_quality_score'] = float(request.form.get('min_quality_score', 0.6))
            config['face_recognition']['auto_learning']['enabled'] = request.form.get('auto_learning_enabled') == 'on'
            config['face_recognition']['auto_learning']['max_samples_per_person'] = int(request.form.get('max_samples', 15))
            config['face_recognition']['auto_learning']['cooldown_seconds'] = int(request.form.get('cooldown_seconds', 60))
            config['face_recognition']['auto_learning']['only_green_matches'] = request.form.get('only_green_matches') == 'on'
            config['face_recognition']['auto_learning']['replace_strategy'] = request.form.get('replace_strategy', 'oldest')
            config['face_recognition']['auto_create_person'] = request.form.get('auto_create_person') == 'on'
            config['face_recognition']['new_person_name_template'] = request.form.get('new_person_name_template', 'Unbekannt #{count}')

            # Stream settings
            config['stream']['target_fps'] = int(request.form.get('stream_target_fps', 10))
            config['stream']['jpeg_quality'] = int(request.form.get('stream_jpeg_quality', 80))

            # Client config template
            client_config['server']['url'] = request.form.get('client_server_url', 'http://localhost:5000')
            client_config['server']['auth_token'] = config['security']['auth_token']  # Always sync with server auth token
            client_config['server']['device_id'] = request.form.get('client_device_id', 'Client-{hostname}')
            client_config['pir']['gpio_pin'] = int(request.form.get('client_pir_gpio_pin', 17))
            client_config['motion']['cooldown_seconds'] = int(request.form.get('client_motion_cooldown', 5))
            client_config['camera']['resolution'] = [
                int(request.form.get('client_camera_width', 1280)),
                int(request.form.get('client_camera_height', 720))
            ]
            client_config['camera']['jpeg_quality'] = int(request.form.get('client_camera_jpeg_quality', 85))
            client_config['camera']['device_index'] = int(request.form.get('client_camera_device_index', 0))
            client_config['streaming']['enabled'] = request.form.get('client_streaming_enabled') == 'on'
            client_config['streaming']['fps'] = int(request.form.get('client_streaming_fps', 5))
            client_config['logging']['level'] = request.form.get('client_logging_level', 'INFO')
            client_config['logging']['file'] = request.form.get('client_logging_file', './logs/client.log')

            # Save server config to file
            with open(CONFIG_FILE, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)

            # Save client config template to file
            with open(client_config_file, 'w') as f:
                yaml.dump(client_config, f, default_flow_style=False)

            logger.info("Configuration saved successfully")
            return render_template('config.html', config=config, client_config=client_config,
                                 message="Konfiguration erfolgreich gespeichert!", message_type="success")

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return render_template('config.html', config=config, client_config=client_config,
                                 message=f"Fehler beim Speichern: {e}", message_type="error")

    return render_template('config.html', config=config, client_config=client_config)

@app.route('/persons', methods=['GET'])
def persons_list():
    """List all persons"""
    persons = db.get_all_persons(include_merged=False)

    # Get sample counts
    for person in persons:
        person['sample_count'] = db.count_face_samples(person['id'])

    return render_template('persons.html', persons=persons)

@app.route('/persons/<int:person_id>', methods=['GET'])
def person_detail(person_id):
    """Person detail page"""
    person = db.get_person(person_id)

    if not person:
        return "Person not found", 404

    samples = db.get_face_samples(person_id)
    events = db.get_events(limit=20, person_id=person_id)

    return render_template('person_detail.html', person=person, samples=samples, events=events)

@app.route('/persons/<int:person_id>/rename', methods=['POST'])
def rename_person(person_id):
    """Rename person"""
    new_name = request.form.get('name', '').strip()

    if not new_name:
        return "Name required", 400

    if db.update_person_name(person_id, new_name):
        logger.info(f"Renamed person {person_id} to '{new_name}'")
        return redirect(url_for('person_detail', person_id=person_id))
    else:
        return "Failed to rename", 500

@app.route('/persons/merge', methods=['POST'])
def merge_persons():
    """Merge two persons"""
    from_id = int(request.form.get('from_id'))
    into_id = int(request.form.get('into_id'))

    if from_id == into_id:
        return "Cannot merge person into itself", 400

    if db.merge_persons(from_id, into_id):
        logger.info(f"Merged person {from_id} into {into_id}")
        return redirect(url_for('persons_list'))
    else:
        return "Failed to merge", 500

@app.route('/persons/<int:person_id>/delete', methods=['POST'])
def delete_person(person_id):
    """Delete person"""
    if db.delete_person(person_id):
        logger.info(f"Deleted person {person_id}")
        return redirect(url_for('persons_list'))
    else:
        return "Failed to delete", 500

@app.route('/events', methods=['GET'])
def events_list():
    """Event history"""
    events = db.get_events(limit=100)

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Event History</title>
        <link rel="stylesheet" href="/static/style.css">
    </head>
    <body>
        <div class="container">
            <h1>📋 Event History</h1>
            <table>
                <tr>
                    <th>Time</th>
                    <th>Person</th>
                    <th>Confidence</th>
                    <th>Status</th>
                    <th>Device</th>
                </tr>
    """

    for event in events:
        person_name = event.get('person_name') or 'Unknown'
        confidence = f"{event['confidence'] * 100:.0f}%" if event['confidence'] else '-'
        status_emoji = {'GREEN': '✅', 'YELLOW': '⚠️', 'UNKNOWN': '❓', 'NO_FACE': '🚫'}.get(event['status'], '❓')

        html += f"""
                <tr>
                    <td>{event['timestamp']}</td>
                    <td>{person_name}</td>
                    <td>{confidence}</td>
                    <td>{status_emoji} {event['status']}</td>
                    <td>{event['device_id'] or '-'}</td>
                </tr>
        """

    html += """
            </table>
            <p><a href="/">← Dashboard</a></p>
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
    logger.info("ESP32 Motion Detector Server with Face Recognition")
    logger.info("=" * 60)
    logger.info(f"Server: http://localhost:{config['server']['port']}")
    logger.info(f"Face Recognition: {'ENABLED' if face_rec.enabled else 'DISABLED'}")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Storage: {STORAGE_DIR}")
    logger.info("=" * 60)

    app.run(
        host=config['server']['host'],
        port=config['server']['port'],
        debug=config['server']['debug'],
        threaded=True
    )
