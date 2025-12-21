# Raspberry Pi Setup Guide

Complete guide for Raspberry Pi - both as **Camera Client** and **Standalone** (all-in-one).

## Table of Contents

1. [Client Mode](#client-mode) - Pi as camera, server elsewhere
2. [Standalone Mode](#standalone-mode) - Pi runs both camera + server
3. [Hardware Setup](#hardware-setup)
4. [Performance](#performance)
5. [Troubleshooting](#troubleshooting)

---

## Client Mode

Raspberry Pi with camera + PIR → sends to remote server (Windows/Linux).

### Hardware

- Raspberry Pi Zero 2 W / Pi 3 / Pi 4 / Pi 5
- **Camera**: CSI (Camera Module v2/v3) or USB webcam
- **PIR Sensor**: HC-SR501 or similar
- Power supply: 5V 2.5A minimum

### Wiring - PIR Sensor

```
HC-SR501 PIR Sensor:
  VCC  → Pi Pin 2 (5V)
  GND  → Pi Pin 6 (GND)
  OUT  → Pi Pin 11 (GPIO 17)

Or use different GPIO:
  GPIO 17, 27, 22, 23, 24 all work
  Update config.yaml: pir.gpio_pin
```

**GPIO Pinout Reference:**
```
Raspberry Pi GPIO (BCM numbering):
      3V3  (1) (2)  5V       ← PIR VCC
    GPIO2  (3) (4)  5V
    GPIO3  (5) (6)  GND      ← PIR GND
    GPIO4  (7) (8)  GPIO14
      GND  (9) (10) GPIO15
   GPIO17 (11) (12) GPIO18   ← PIR OUT (example)
   GPIO27 (13) (14) GND
   ...
```

### Installation

```bash
# 1. Enable camera (CSI)
sudo raspi-config
# Interface Options → Camera → Enable
# Reboot

# 2. Install system packages
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install python3-picamera2  # For CSI camera
# OR for USB: pip install opencv-python

# 3. Clone/copy client code
cd ~
git clone <repo-url> motion-detector
cd motion-detector/clients/raspi

# 4. Install Python dependencies
pip3 install -r requirements.txt

# 5. Configure
cp config.yaml.example config.yaml
nano config.yaml

# Edit:
#   server.url: 'http://192.168.1.100:5000'  # Your server IP
#   server.auth_token: 'MATCH_SERVER_TOKEN'
#   server.device_id: 'RaspberryPi-CAM-01'
#   pir.gpio_pin: 17
#   camera.resolution: [1280, 720]  # Lower for Pi 3

# 6. Test camera
python3 -c "from picamera2 import Picamera2; cam = Picamera2(); cam.start(); print('Camera OK'); cam.stop()"

# 7. Test PIR
python3 -c "from gpiozero import MotionSensor; pir = MotionSensor(17); print('Wave hand...'); pir.wait_for_motion(); print('Motion detected!')"

# 8. Test client
python3 pir_cam_client.py
# Trigger PIR → Check server receives image

# 9. Setup as service
sudo cp ~/motion-detector/deploy/raspi/client/motion-detector-client.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable motion-detector-client
sudo systemctl start motion-detector-client

# Check status
sudo systemctl status motion-detector-client
sudo journalctl -u motion-detector-client -f
```

### Client Config Tuning

**For Raspberry Pi 3 (slower):**
```yaml
camera:
  resolution: [640, 480]      # Lower resolution
  jpeg_quality: 75            # Lower quality

motion:
  cooldown_seconds: 10        # Longer cooldown

streaming:
  enabled: false              # Disable streaming (save CPU)
```

**For Raspberry Pi 4/5:**
```yaml
camera:
  resolution: [1280, 720]     # Good quality
  jpeg_quality: 85

streaming:
  enabled: true               # Enable live stream
  fps: 5                      # 5 fps realistic
```

---

## Standalone Mode

Single Raspberry Pi runs **both** camera client + server.

### Use Cases

- Portable motion detector
- No separate server available
- All-in-one home security device

### Requirements

- Raspberry Pi 4 (2GB+) or Pi 5 recommended
- Pi 3 works but slower
- Camera Module (CSI)
- PIR Sensor
- 16GB+ SD card

### Installation

```bash
# 1. Setup server (from LINUX_SETUP.md)
sudo mkdir -p /opt/motion-detector
sudo chown pi:pi /opt/motion-detector
cd /opt/motion-detector
git clone <repo-url> .

# Install server
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-linux.txt
python models/download_models.py

# Configure server
cp config.yaml config.yaml.example
nano config.yaml
# Set:
#   notifications.backend: 'disabled'  # No GUI on Pi usually
#   face_recognition.enabled: true

# 2. Setup client
cd /opt/motion-detector/clients/raspi
pip3 install -r requirements.txt

cp config.yaml.example config.yaml
nano config.yaml
# Set:
#   server.url: 'http://localhost:5000'  # Local server
#   server.auth_token: 'MATCH_SERVER_CONFIG'

# 3. Install systemd services
# Server
sudo cp /opt/motion-detector/deploy/linux/systemd/motion-detector-server.service /etc/systemd/system/
# Edit paths in service file to match /opt/motion-detector

# Client
sudo cp /opt/motion-detector/deploy/raspi/client/motion-detector-client.service /etc/systemd/system/
sudo systemctl daemon-reload

# 4. Enable and start
sudo systemctl enable motion-detector-server
sudo systemctl enable motion-detector-client
sudo systemctl start motion-detector-server
sudo systemctl start motion-detector-client

# 5. Check status
sudo systemctl status motion-detector-server
sudo systemctl status motion-detector-client

# 6. Access Web UI
# From Pi browser: http://localhost:5000
# From LAN: http://<pi-ip>:5000
```

### Standalone Performance

| Pi Model | Face Recognition | Streaming FPS | Notes |
|----------|------------------|---------------|-------|
| Pi 5 | ~400ms | 8-10 fps | Excellent |
| Pi 4 | ~500ms | 5-8 fps | Good |
| Pi 3 | ~2s | 2-3 fps | Usable |

### Memory Usage

- **Server + Face Recognition:** ~300-500 MB RAM
- **Client:** ~50-100 MB RAM
- **Total:** ~400-600 MB (fine for 2GB+ Pi)

**Pi 3 (1GB RAM):** Disable face recognition or reduce samples:
```yaml
face_recognition:
  enabled: false  # Or set max_samples_per_person: 5
```

---

## Hardware Setup

### Camera Options

#### Option 1: CSI Camera Module (Recommended)

**Models:**
- **Camera Module v2** (8MP, €25)
- **Camera Module v3** (12MP, €30, better low-light)
- **HQ Camera** (12MP, €50, interchangeable lens)

**Connection:**
1. Locate CSI connector (between HDMI and USB on Pi 4)
2. Pull up plastic clip gently
3. Insert ribbon cable (blue side facing USB ports)
4. Push clip down

**Test:**
```bash
libcamera-hello --list-cameras
libcamera-jpeg -o test.jpg
```

#### Option 2: USB Webcam

**Cheaper but:**
- Lower quality
- Uses USB bandwidth
- Slower

**Test:**
```bash
ls /dev/video*  # Should show /dev/video0
```

**Config:**
```yaml
camera:
  device_index: 0  # /dev/video0
```

### PIR Sensor Tuning

**HC-SR501 has 2 potentiometers:**

1. **Sensitivity (Sx)**: Detection range (3-7m)
   - Clockwise = more sensitive
2. **Time Delay (Tx)**: How long OUT stays HIGH
   - Not critical (firmware has cooldown)

**Jumper:**
- **H**: Repeatable trigger (recommended)
- **L**: Single trigger

---

## Performance

### Benchmark Results

**Camera capture:**
- CSI Camera: 50-100ms
- USB Camera: 100-200ms

**PIR to upload:**
- Pi 5: ~200ms
- Pi 4: ~300ms
- Pi 3: ~500ms

**Streaming (5 fps):**
- Continuous upload every 200ms
- Network limited, not CPU

---

## Troubleshooting

### Camera not detected

**CSI Camera:**
```bash
# Check connection
vcgencmd get_camera
# Should show: supported=1 detected=1

# Enable in config
sudo raspi-config
# Interface Options → Camera → Enable

# Reboot
sudo reboot
```

**USB Camera:**
```bash
# List devices
lsusb

# Check video device
ls -l /dev/video*

# Test with ffmpeg
ffmpeg -f v4l2 -i /dev/video0 -frames 1 test.jpg
```

### PIR not triggering

**Check wiring:**
```python
from gpiozero import MotionSensor
pir = MotionSensor(17)  # Your GPIO pin

print("Waiting for motion...")
pir.wait_for_motion()
print("Motion detected!")
pir.wait_for_no_motion()
print("Motion stopped")
```

**Common issues:**
- VCC connected to 3.3V instead of 5V (some PIRs need 5V)
- GPIO pin mismatch in config
- PIR in calibration phase (wait 30-60s after power-on)

### Permission denied (GPIO/Camera)

```bash
# Add user to groups
sudo usermod -a -G video,gpio pi

# Logout and login
```

### Server connection refused

**Check server running:**
```bash
# Standalone mode
sudo systemctl status motion-detector-server

# External server
curl -I http://192.168.1.100:5000/health
```

**Firewall:**
```bash
# On server
sudo ufw allow 5000/tcp
```

### Out of memory (Pi 3)

**Reduce usage:**
```yaml
# Disable face recognition
face_recognition:
  enabled: false

# Lower resolution
camera:
  resolution: [640, 480]

# Disable streaming
streaming:
  enabled: false
```

---

## Security

**For standalone Pi exposed to LAN:**

1. **Change default password:**
   ```bash
   passwd
   ```

2. **Enable firewall:**
   ```bash
   sudo apt install ufw
   sudo ufw allow 5000/tcp
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

3. **Change auth token:**
   - Edit `server/config.yaml` and `clients/raspi/config.yaml`
   - Use strong random token

4. **Disable SSH password login** (use key-based):
   ```bash
   sudo nano /etc/ssh/sshd_config
   # Set: PasswordAuthentication no
   sudo systemctl restart ssh
   ```

---

## Maintenance

### Update software

```bash
# System
sudo apt update && sudo apt upgrade

# Python packages (client)
pip3 install --upgrade -r requirements.txt

# Python packages (server)
cd /opt/motion-detector/server
source venv/bin/activate
pip install --upgrade -r requirements.txt
```

### Backup

**On standalone Pi:**
```bash
# Database
cp /opt/motion-detector/server/faces.db ~/backup/

# Config
cp /opt/motion-detector/server/config.yaml ~/backup/
cp /opt/motion-detector/clients/raspi/config.yaml ~/backup/
```

### View logs

```bash
# Server
sudo journalctl -u motion-detector-server -f

# Client
sudo journalctl -u motion-detector-client -f
```

---

## Next Steps

- **Tune thresholds:** See `FACE_RECOGNITION.md`
- **Add persons:** Web UI `/persons`
- **Monitor events:** Web UI `/events`
- **Optimize performance:** Adjust resolution, quality, FPS
