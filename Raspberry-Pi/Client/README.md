# Raspberry Pi Camera Client

Python-based motion detector client for Raspberry Pi with PIR sensor and camera.

## Features

- PIR motion detection via GPIO
- CSI Camera Module or USB webcam support
- JPEG capture and upload to server
- Optional live streaming
- Configurable cooldown and quality
- systemd service for auto-start

## Quick Start

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3-pip python3-picamera2
pip3 install -r requirements.txt

# 2. Configure
cp config.yaml.example config.yaml
nano config.yaml
# Edit: server URL, auth token, GPIO pin

# 3. Test run
python3 pir_cam_client.py

# 4. Install as service
sudo cp ../../deploy/raspi/client/motion-detector-client.service /etc/systemd/system/
sudo systemctl enable motion-detector-client
sudo systemctl start motion-detector-client
```

## Hardware Setup

### PIR Wiring

```
HC-SR501:
  VCC → Pi Pin 2 (5V)
  GND → Pi Pin 6 (GND)
  OUT → Pi Pin 11 (GPIO 17)
```

### Camera

**CSI Camera Module** (recommended):
- Enable via `sudo raspi-config` → Interface Options → Camera
- Test: `libcamera-hello`

**USB Webcam**:
- Plug in
- Test: `ls /dev/video*`
- Set in config: `camera.device_index: 0`

## Configuration

See `config.yaml.example` for all options.

**Key settings:**

- `server.url`: Your server address
- `pir.gpio_pin`: GPIO pin for PIR (BCM numbering)
- `camera.resolution`: [width, height]
- `motion.cooldown_seconds`: Prevent spam

## Troubleshooting

**Camera not found:**
```bash
# Enable camera
sudo raspi-config
# Reboot
sudo reboot
```

**PIR not triggering:**
```python
# Test PIR
from gpiozero import MotionSensor
pir = MotionSensor(17)
pir.wait_for_motion()
print("Motion!")
```

**Permission denied:**
```bash
sudo usermod -a -G video,gpio $USER
# Logout and login
```

## Performance

| Pi Model | Upload Speed | Recommended Resolution |
|----------|--------------|------------------------|
| Pi 5 | ~200ms | 1920x1080 |
| Pi 4 | ~300ms | 1280x720 |
| Pi 3 | ~500ms | 640x480 |
| Pi Zero 2 W | ~800ms | 640x480 |

## Full Documentation

See `../../docs/RASPBERRY_PI.md` for complete guide including standalone mode.
