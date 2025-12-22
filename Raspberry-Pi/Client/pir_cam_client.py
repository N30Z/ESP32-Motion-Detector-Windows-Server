#!/usr/bin/env python3
"""
Raspberry Pi Motion Detector Client
====================================
PIR sensor + Camera → Upload to server on motion detection.

Hardware:
- Raspberry Pi Zero 2 W / Pi 3 / Pi 4 / Pi 5
- PIR sensor (HC-SR501 or similar) on GPIO
- Camera: CSI (Raspberry Pi Camera Module) or USB webcam

Dependencies:
- picamera2 (for CSI camera) or opencv-python (for USB)
- gpiozero (for PIR)
- requests (for HTTP upload)
- PyYAML (for config)
"""

import sys
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from io import BytesIO
import signal

import yaml
import requests
from gpiozero import MotionSensor
from PIL import Image

# Try picamera2 first (CSI camera), fallback to OpenCV (USB)
try:
    from picamera2 import Picamera2
    CAMERA_TYPE = 'picamera2'
except ImportError:
    try:
        import cv2
        CAMERA_TYPE = 'opencv'
    except ImportError:
        print("ERROR: No camera library found!")
        print("Install: sudo apt install python3-picamera2  (for CSI)")
        print("     OR: pip install opencv-python  (for USB)")
        sys.exit(1)

# ============================================================================
# CONFIGURATION
# ============================================================================

CONFIG_FILE = Path(__file__).parent / 'config.yaml'

if not CONFIG_FILE.exists():
    print(f"ERROR: Config file not found: {CONFIG_FILE}")
    print("Copy config.yaml.example to config.yaml and edit")
    sys.exit(1)

with open(CONFIG_FILE, 'r') as f:
    config = yaml.safe_load(f)

# Setup logging
logging.basicConfig(
    level=getattr(logging, config['logging']['level']),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(config['logging']['file']),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# CAMERA CLASS
# ============================================================================

class CameraInterface:
    """Abstract camera interface"""

    def __init__(self, config):
        self.config = config
        self.resolution = tuple(config['camera']['resolution'])
        self.jpeg_quality = config['camera']['jpeg_quality']

    def capture_jpeg(self) -> bytes:
        """Capture and return JPEG bytes"""
        raise NotImplementedError

    def close(self):
        """Cleanup camera resources"""
        pass


class PiCamera2Interface(CameraInterface):
    """Raspberry Pi Camera Module (CSI) via picamera2"""

    def __init__(self, config):
        super().__init__(config)
        logger.info("Initializing Picamera2 (CSI camera)...")

        self.camera = Picamera2()

        # Configure camera
        camera_config = self.camera.create_still_configuration(
            main={"size": self.resolution, "format": "RGB888"}
        )
        self.camera.configure(camera_config)
        self.camera.start()

        # Warm-up
        time.sleep(2)
        logger.info(f"Camera ready: {self.resolution[0]}x{self.resolution[1]}")

    def capture_jpeg(self) -> bytes:
        """Capture JPEG from CSI camera"""
        # Capture array
        array = self.camera.capture_array()

        # Convert to PIL Image
        img = Image.fromarray(array)

        # Encode to JPEG
        buffer = BytesIO()
        img.save(buffer, format='JPEG', quality=self.jpeg_quality)

        return buffer.getvalue()

    def close(self):
        """Stop camera"""
        self.camera.stop()
        logger.info("Camera stopped")


class OpenCVCameraInterface(CameraInterface):
    """USB webcam via OpenCV"""

    def __init__(self, config):
        super().__init__(config)
        logger.info("Initializing OpenCV camera (USB)...")

        camera_index = config['camera'].get('device_index', 0)
        self.camera = cv2.VideoCapture(camera_index)

        if not self.camera.isOpened():
            raise RuntimeError(f"Failed to open camera device {camera_index}")

        # Set resolution
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.resolution[0])
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.resolution[1])

        # Warm-up
        for _ in range(5):
            self.camera.read()
        time.sleep(1)

        logger.info(f"Camera ready: {self.resolution[0]}x{self.resolution[1]}")

    def capture_jpeg(self) -> bytes:
        """Capture JPEG from USB camera"""
        ret, frame = self.camera.read()

        if not ret:
            raise RuntimeError("Failed to capture frame from camera")

        # Encode to JPEG
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
        _, buffer = cv2.imencode('.jpg', frame, encode_param)

        return buffer.tobytes()

    def close(self):
        """Release camera"""
        self.camera.release()
        logger.info("Camera released")


def get_camera_interface(config) -> CameraInterface:
    """Factory: Get camera interface based on available library"""
    if CAMERA_TYPE == 'picamera2':
        return PiCamera2Interface(config)
    elif CAMERA_TYPE == 'opencv':
        return OpenCVCameraInterface(config)
    else:
        raise RuntimeError("No camera interface available")

# ============================================================================
# MOTION DETECTOR CLIENT
# ============================================================================

class MotionDetectorClient:
    """Main motion detector client"""

    def __init__(self, config):
        self.config = config
        self.running = False

        # Server config
        self.server_url = config['server']['url'].rstrip('/')
        self.auth_token = config['server']['auth_token']
        self.device_id = config['server']['device_id']

        # Motion config
        self.cooldown_seconds = config['motion']['cooldown_seconds']
        self.last_motion_time = None

        # Streaming config
        self.streaming_enabled = config['streaming']['enabled']
        self.stream_interval = 1.0 / config['streaming']['fps']
        self.last_stream_time = None

        # Initialize PIR
        pir_pin = config['pir']['gpio_pin']
        logger.info(f"Initializing PIR sensor on GPIO {pir_pin}...")
        self.pir = MotionSensor(pir_pin)

        # Initialize camera
        self.camera = get_camera_interface(config)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()

    def upload_image(self, jpeg_bytes: bytes, event_type: str = 'motion') -> bool:
        """
        Upload image to server

        Args:
            jpeg_bytes: JPEG image data
            event_type: 'motion' or 'stream'

        Returns:
            True if upload successful
        """
        try:
            endpoint = f"{self.server_url}/upload" if event_type == 'motion' else f"{self.server_url}/stream_frame"

            files = {'image': ('capture.jpg', jpeg_bytes, 'image/jpeg')} if event_type == 'motion' else None
            data = {'device_id': self.device_id} if event_type == 'motion' else jpeg_bytes
            headers = {'X-Auth-Token': self.auth_token}

            if event_type == 'stream':
                headers['Content-Type'] = 'image/jpeg'

            response = requests.post(
                endpoint,
                files=files if event_type == 'motion' else None,
                data=data,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.debug(f"Upload successful ({event_type}): {len(jpeg_bytes)} bytes")
                return True
            else:
                logger.error(f"Upload failed ({event_type}): HTTP {response.status_code}")
                return False

        except requests.exceptions.Timeout:
            logger.error(f"Upload timeout ({event_type})")
            return False
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error ({event_type})")
            return False
        except Exception as e:
            logger.error(f"Upload error ({event_type}): {e}")
            return False

    def handle_motion_event(self):
        """Handle PIR motion detection"""
        # Check cooldown
        now = datetime.now()
        if self.last_motion_time:
            elapsed = (now - self.last_motion_time).total_seconds()
            if elapsed < self.cooldown_seconds:
                logger.debug(f"Motion ignored (cooldown: {elapsed:.1f}s < {self.cooldown_seconds}s)")
                return

        logger.info("🚨 MOTION DETECTED!")

        try:
            # Capture photo
            jpeg_bytes = self.camera.capture_jpeg()
            logger.info(f"Photo captured: {len(jpeg_bytes)} bytes")

            # Upload
            success = self.upload_image(jpeg_bytes, event_type='motion')

            if success:
                logger.info("✓ Photo uploaded successfully")
                self.last_motion_time = now
            else:
                logger.warning("✗ Photo upload failed")

        except Exception as e:
            logger.error(f"Motion handling error: {e}")

    def handle_streaming(self):
        """Handle continuous frame streaming"""
        if not self.streaming_enabled:
            return

        now = time.time()

        # Check if it's time to send next frame
        if self.last_stream_time and (now - self.last_stream_time) < self.stream_interval:
            return

        try:
            # Capture frame
            jpeg_bytes = self.camera.capture_jpeg()

            # Upload (fire-and-forget, don't block)
            self.upload_image(jpeg_bytes, event_type='stream')

            self.last_stream_time = now

        except Exception as e:
            logger.debug(f"Stream error: {e}")

    def run(self):
        """Main loop"""
        self.running = True

        logger.info("=" * 60)
        logger.info("Raspberry Pi Motion Detector Client")
        logger.info("=" * 60)
        logger.info(f"Server: {self.server_url}")
        logger.info(f"Device ID: {self.device_id}")
        logger.info(f"PIR GPIO: {self.config['pir']['gpio_pin']}")
        logger.info(f"Camera: {CAMERA_TYPE}")
        logger.info(f"Cooldown: {self.cooldown_seconds}s")
        logger.info(f"Streaming: {'ON' if self.streaming_enabled else 'OFF'}")
        logger.info("=" * 60)
        logger.info("System ready! Waiting for motion...")
        logger.info("=" * 60)

        # Attach PIR callback
        self.pir.when_motion = self.handle_motion_event

        # Main loop
        while self.running:
            # Handle streaming
            if self.streaming_enabled:
                self.handle_streaming()

            # Small delay
            time.sleep(0.01)

    def stop(self):
        """Stop client"""
        logger.info("Stopping client...")
        self.running = False
        self.camera.close()
        logger.info("Client stopped")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    try:
        client = MotionDetectorClient(config)
        client.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
