# ESP32 Motion Detector - Multi-Platform System

**Production-ready motion detection system** with face recognition, supporting multiple platforms: Windows, Linux, ESP32-CAM, and Raspberry Pi.

[![Platform](https://img.shields.io/badge/platform-ESP32%20%7C%20Raspberry%20Pi-blue.svg)](https://www.espressif.com/en/products/socs/esp32)
[![Server](https://img.shields.io/badge/server-Windows%20%7C%20Linux-green.svg)](https://www.python.org/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## 🎯 Overview

Complete motion detection system with **face recognition** (YuNet + SFace), supporting multiple deployment scenarios:

- **Camera Clients:** ESP32-CAM (C++) or Raspberry Pi (Python)
- **Server:** Windows or Linux
- **Standalone:** All-in-one Raspberry Pi (camera + server)

**Key Features:**
- ✅ PIR motion detection with photo capture
- ✅ Live MJPEG streaming (~5-10 fps)
- ✅ Face recognition with auto-learning (OpenCV YuNet/SFace)
- ✅ Person management (rename, merge, track)
- ✅ Platform-specific notifications (Windows Toast / Linux Desktop)
- ✅ Web UI for configuration and monitoring
- ✅ Rule-based workflow automation
- ✅ Multi-camera support

---

## 📋 Deployment Scenarios

### 1️⃣ **Windows Server + ESP32-CAM** (Original)

Classic setup: ESP32-CAM with PIR → Windows PC server.

- **Camera:** ESP32-CAM (AI-Thinker) with OV2640
- **Server:** Windows 10/11 with Toast notifications
- **Performance:** ~100ms face recognition
- **Best for:** Windows users, minimal setup

**Quick Start:** [Windows + ESP32 Guide](#quick-start-windows--esp32)

---

### 2️⃣ **Linux Server + ESP32-CAM**

ESP32-CAM → Linux server (Ubuntu/Debian).

- **Camera:** ESP32-CAM (same as Windows)
- **Server:** Ubuntu/Debian with Desktop notifications or headless
- **Performance:** ~100ms face recognition
- **Best for:** Linux users, headless servers

**Quick Start:** [Linux/Linux.md](Linux/Linux.md)

---

### 3️⃣ **Server + Raspberry Pi Camera Client**

Raspberry Pi with camera + PIR → Remote server (Windows/Linux).

- **Camera:** Raspberry Pi (Zero 2 W / 3 / 4 / 5) + CSI Camera Module
- **Server:** Windows or Linux (separate device)
- **Performance:** ~200-500ms upload (Pi model dependent)
- **Best for:** Distributed cameras, existing server

**Quick Start:** [Raspberry-Pi/Raspberry.md → Client Mode](Raspberry-Pi/Raspberry.md#client-modus)

---

### 4️⃣ **Standalone Raspberry Pi** (All-in-One)

Single Raspberry Pi runs both camera + server.

- **Device:** Raspberry Pi 4/5 (Pi 3 works but slower)
- **Features:** Camera, PIR, server, face recognition, Web UI
- **Performance:** ~400-500ms face recognition (Pi 4)
- **Best for:** Portable, single-device solution

**Quick Start:** [Raspberry-Pi/Standalone/README.md](Raspberry-Pi/Standalone/README.md)

---

## ⚡ Quick Installation

### One-Command Setup

**Windows Server:**
```bash
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server/Server
setup.bat
```

**Linux Server:**
```bash
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server/Server
./setup.sh
```

**Raspberry Pi Client:**
```bash
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server/Raspberry-Pi/Client
./setup.sh
```

**That's it!** The setup script automatically:
- ✅ Checks Python version and dependencies
- ✅ Installs all required packages
- ✅ Downloads face recognition models
- ✅ Creates configuration with auth token
- ✅ Sets up platform-specific notifications
- ✅ Tests the installation

**Troubleshooting?** See [INSTALLATION.md](INSTALLATION.md) for detailed solutions to common issues.

---

## 🚀 Manual Setup (Windows + ESP32)

<details>
<summary>Click to expand manual installation steps</summary>

### Prerequisites

- **Hardware:**
  - ESP32-CAM (AI-Thinker)
  - PIR sensor (HC-SR501)
  - FTDI programmer (3.3V)
  - 5V 2A power supply
- **Software:**
  - Python 3.8+
  - PlatformIO or Arduino IDE

### 1. Server Setup (Windows)

```bash
# Install Python from python.org

# Clone repository
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server/Server

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-windows.txt  # Windows Toast

# Download face recognition models
python models/download_models.py

# Generate auth token
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Configure
notepad config.yaml
# Set:
#   security.auth_token: <generated_token>
#   notifications.backend: 'windows_toast'
#   face_recognition.enabled: true

# Start server
python app.py
```

**Server URL:** `http://localhost:5000`

### 2. ESP32 Firmware Upload

```bash
cd ../ESP32/Client

# Copy secrets
cp include/secrets.h.example include/secrets.h

# Edit secrets.h
notepad include/secrets.h
# Set:
#   WIFI_SSID, WIFI_PASSWORD
#   SERVER_HOST: "192.168.1.100" (your PC IP - run 'ipconfig')
#   AUTH_TOKEN: <same as config.yaml>

# Upload (PlatformIO)
pio run --target upload

# Monitor
pio device monitor
# Should show: "System Ready!"
```

**Important:** Connect IO0 to GND before uploading, disconnect after.

### 3. Hardware Wiring

```
PIR HC-SR501:
  VCC → ESP32-CAM 5V
  GND → ESP32-CAM GND
  OUT → ESP32-CAM GPIO 13

Power:
  5V 2A → ESP32-CAM VCC/GND
```

### 4. Test

1. Trigger PIR (wave hand)
2. Check Windows Toast notification
3. Open `http://localhost:5000/latest`
4. View live stream: `http://localhost:5000`

**✅ System operational!**

</details>

---

## 📁 Project Structure

```
ESP32-Motion-Detector-Windows-Server/
│
├── Windows/                         # Windows-specific files
│   ├── Windows.md                   # Complete Windows guide
│   └── Server/                      # Windows server setup references
│
├── Linux/                           # Linux-specific files
│   ├── Linux.md                     # Complete Linux guide
│   ├── Server/                      # Linux server setup
│   │   ├── motion-detector-server.service
│   │   └── README.md
│   └── Client/                      # Future: Native Linux client
│
├── Raspberry-Pi/                    # Raspberry Pi configurations
│   ├── Raspberry.md                 # Complete Raspberry Pi guide
│   ├── Client/                      # Pi as camera client
│   │   ├── pir_cam_client.py
│   │   ├── config.yaml.example
│   │   ├── setup.sh
│   │   ├── motion-detector-client.service
│   │   └── README.md
│   ├── Server/                      # Pi as server (references)
│   └── Standalone/                  # All-in-one Pi setup
│       ├── setup.sh                 # Automated installation
│       └── README.md
│
├── ESP32/                           # ESP32-CAM client
│   ├── ESP32.md                     # Complete ESP32 guide
│   └── Client/                      # ESP32-CAM firmware (C++)
│       ├── src/main.cpp
│       ├── include/secrets.h.example
│       ├── platformio.ini
│       └── README.md
│
├── Server/                          # Central server code (shared)
│   ├── app.py                       # Main Flask application
│   ├── database.py                  # SQLite database layer
│   ├── face_recognition_cv.py       # Face recognition pipeline
│   ├── config.yaml                  # Server configuration
│   ├── rules.yaml                   # Workflow automation
│   ├── requirements.txt             # Base Python dependencies
│   ├── requirements-windows.txt     # Windows-specific (winotify)
│   ├── requirements-linux.txt       # Linux-specific (notify-send)
│   ├── setup.sh                     # Linux/Pi setup script
│   ├── setup.bat                    # Windows setup script
│   ├── models/                      # YuNet/SFace ONNX models
│   ├── templates/                   # Web UI templates
│   ├── static/                      # CSS/JS assets
│   ├── notifications/               # Platform-specific notification backends
│   └── README.md
│
├── docs/                            # Additional documentation
│   └── FACE_RECOGNITION.md          # Complete FR guide (600+ lines)
│
├── README.md                        # This file
├── INSTALLATION.md                  # Installation troubleshooting guide
├── QUICKSTART.md                    # Quick start for all platforms
└── AUDIT_REPORT.md                  # Repository restructure documentation
```

---

## 🎨 Features in Detail

### Face Recognition (YuNet + SFace)

**Lightweight OpenCV-based pipeline:**

- **Detection:** YuNet (~200 KB ONNX model)
- **Embedding:** SFace (~5 MB ONNX model)
- **No heavy dependencies:** No PyTorch, no dlib, only opencv-contrib-python
- **Performance:** ~100-200ms per face (desktop), ~500ms (Pi 4)

**Features:**
- ✅ Automatic person differentiation (UNKNOWN → new person)
- ✅ Auto-learning (up to 15 samples per person)
- ✅ Distance + Margin matching (GREEN/YELLOW/UNKNOWN)
- ✅ Confidence calculation (0-100%, non-magical)
- ✅ Web UI for person management (rename, merge, delete)

**Status Meaning:**
- **GREEN (✅):** Reliable match (d1 < 0.35, margin > 0.15)
- **YELLOW (⚠️):** Uncertain match (d1 < 0.50, margin > 0.08)
- **UNKNOWN (❓):** No match → auto-creates new person

**See:** [docs/FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md)

### Platform-Specific Notifications

**Windows:**
- Toast notifications with image preview (winotify)
- Click to open `/latest` in browser
- Sound alerts (configurable)

**Linux:**
- Desktop notifications via `notify-send` (libnotify)
- Image icon support
- Works on Ubuntu/Debian/Fedora with Desktop Environment

**Headless:**
- Notifications disabled
- Events visible in Web UI (`/events`, `/latest`)

**Config:**
```yaml
notifications:
  enabled: true
  backend: 'windows_toast'  # or 'linux_notify' or 'disabled'
  sound: true
```

### Web UI

**Endpoints:**

- `/` - Dashboard with live stream + stats
- `/latest` - Latest motion event with face info
- `/stream` - MJPEG live stream (~5-10 fps)
- `/config` - Threshold tuning, auto-learning settings
- `/persons` - Person list, rename, merge
- `/persons/<id>` - Person details, samples, events
- `/events` - Event history
- `/health` - Server health check

**Features:**
- Dark theme, responsive design
- Inline help for threshold tuning
- Sample thumbnails with quality scores
- Real-time statistics

### Workflow Automation (Placeholder)

**Current:** Log-based actions with clear extension points.

**Future:** Telegram, email, webhooks, Home Assistant, etc.

**Example rule:**
```yaml
rules:
  - name: "Alert Unknown Person"
    conditions:
      person: "Unknown"
      min_confidence: 0.5
    actions:
      - type: log
        message: "⚠️ Unknown person detected"
      - type: telegram  # PLACEHOLDER
        bot_token: "YOUR_BOT_TOKEN"
        chat_id: "YOUR_CHAT_ID"
```

**See:** [server/rules.yaml](server/rules.yaml)

---

## 🔧 Configuration

### Server Config (`server/config.yaml`)

**Key sections:**

```yaml
server:
  host: '0.0.0.0'
  port: 5000
  debug: false

security:
  auth_token: 'YOUR_SECRET_TOKEN'  # ⚠️ CHANGE THIS!

notifications:
  backend: 'windows_toast'  # or 'linux_notify', 'disabled'
  enabled: true

face_recognition:
  enabled: true  # Set to true after downloading models
  threshold_strict: 0.35   # Distance for GREEN match
  threshold_loose: 0.50    # Distance for YELLOW match
  margin_strict: 0.15      # Margin for GREEN match
  margin_loose: 0.08       # Margin for YELLOW match

  auto_learning:
    enabled: true
    max_samples_per_person: 15
    cooldown_seconds: 60
```

**Full reference:** [server/config.yaml](server/config.yaml)

### Raspberry Pi Client Config (`clients/raspi/config.yaml`)

```yaml
server:
  url: 'http://192.168.1.100:5000'
  auth_token: 'MATCH_SERVER_TOKEN'
  device_id: 'RaspberryPi-CAM-01'

pir:
  gpio_pin: 17  # BCM numbering

camera:
  resolution: [1280, 720]
  jpeg_quality: 85

streaming:
  enabled: false  # Set true for live stream
  fps: 5
```

---

## 📊 Performance Benchmarks

### Face Recognition

| Platform | Detection | Embedding | Matching | Total |
|----------|-----------|-----------|----------|-------|
| Windows Desktop (i5) | 50-100ms | 30-50ms | 5-10ms | **~100-200ms** |
| Linux Desktop (i5) | 50-100ms | 30-50ms | 5-10ms | **~100-200ms** |
| Raspberry Pi 5 | 150-200ms | 150-200ms | 5-10ms | **~400ms** |
| Raspberry Pi 4 | 200-250ms | 200-250ms | 5-10ms | **~500ms** |
| Raspberry Pi 3 | 800ms-1s | 800ms-1s | 5-10ms | **~2s** |

### Camera Upload Latency

| Camera Client | Capture | Upload | Total |
|---------------|---------|--------|-------|
| ESP32-CAM | 100-200ms | 300-500ms | **~400-700ms** |
| Raspberry Pi 5 | 50-100ms | 100-150ms | **~200ms** |
| Raspberry Pi 4 | 50-100ms | 200-250ms | **~300ms** |
| Raspberry Pi 3 | 100-200ms | 300-400ms | **~500ms** |

### Streaming FPS (Realistic)

| Camera | FPS | Notes |
|--------|-----|-------|
| ESP32-CAM | 8-12 fps | SVGA (800×600) |
| Raspberry Pi 5 | 10-15 fps | 1280×720 |
| Raspberry Pi 4 | 5-10 fps | 1280×720 |
| Raspberry Pi 3 | 2-5 fps | 640×480 recommended |

---

## 🐛 Troubleshooting

### Common Issues

**1. "YuNet model not found"**
```bash
cd server
python models/download_models.py
ls models/*.onnx  # Verify
```

**2. Windows Toast not showing**
- Check Focus Assist settings (OFF)
- Enable notifications for Python in Windows Settings
- Run server as Administrator (try)

**3. Linux notifications not working**
```bash
# Install libnotify
sudo apt install libnotify-bin

# Test
notify-send "Test" "Message"

# Check $DISPLAY
echo $DISPLAY  # Should show :0 or similar
```

**4. Raspberry Pi camera not detected**
```bash
# Enable camera
sudo raspi-config
# Interface Options → Camera → Enable → Reboot

# Test
libcamera-hello
libcamera-jpeg -o test.jpg
```

**5. Permission denied (GPIO/Camera on Pi)**
```bash
sudo usermod -a -G video,gpio $USER
# Logout and login again
```

### Platform-Specific Guides

- **Windows:** [Windows/Windows.md](Windows/Windows.md)
- **Linux:** [Linux/Linux.md](Linux/Linux.md)
- **Raspberry Pi:** [Raspberry-Pi/Raspberry.md](Raspberry-Pi/Raspberry.md)
- **ESP32:** [ESP32/ESP32.md](ESP32/ESP32.md)

---

## 🔒 Security

### Implemented

- ✅ Token-based authentication (all endpoints)
- ✅ Input validation
- ✅ Secure defaults
- ✅ systemd security hardening (Linux)
- ✅ No cloud dependencies (fully local)

### Recommendations

**Change auth token:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy to config.yaml and secrets.h
```

**Firewall (Windows):**
```powershell
New-NetFirewallRule -DisplayName "ESP32 Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

**Firewall (Linux):**
```bash
sudo ufw allow 5000/tcp
sudo ufw enable
```

**HTTPS (optional, via reverse proxy):**
- Use nginx or Caddy for HTTPS
- Not included (LAN-only use case)

**Privacy:**
- Household use only (GDPR: legitimate interest)
- Post signage if monitoring common areas
- Don't expose server to internet without HTTPS + strong auth
- Regular cleanup: `max_age_days: 7` in config

---

## 📖 Documentation

### Complete Guides

| Document | Description | Lines |
|----------|-------------|-------|
| [README.md](README.md) | This file - overview and quick start | 800+ |
| [docs/FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md) | Face recognition deep-dive, tuning, troubleshooting | 600+ |
| [Linux/Linux.md](Linux/Linux.md) | Linux server deployment, systemd, notifications | 200+ |
| [Raspberry-Pi/Raspberry.md](Raspberry-Pi/Raspberry.md) | Raspberry Pi client + standalone setup | 400+ |
| [Server/README.md](Server/README.md) | Server API, configuration, extensions | 500+ |
| [ESP32/Client/README.md](ESP32/Client/README.md) | ESP32 firmware, wiring, troubleshooting | 400+ |
| [Raspberry-Pi/Client/README.md](Raspberry-Pi/Client/README.md) | Raspberry Pi client quick start | 100+ |

### Quick Links

- **Architecture:** Why YuNet/SFace? → [FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md#architektur)
- **Threshold Tuning:** GREEN/YELLOW/UNKNOWN → [FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md#threshold-tuning)
- **Auto-Learning:** How it works → [FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md#auto-learning)
- **Merge Persons:** Duplicate handling → [FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md#merge-funktion)
- **Linux systemd:** Service setup → [LINUX_SETUP.md](docs/LINUX_SETUP.md#systemd)
- **Pi Wiring:** GPIO diagrams → [RASPBERRY_PI.md](docs/RASPBERRY_PI.md#hardware-setup)

---

## 🛠️ Advanced Features

### Multi-Camera Setup

**Supported:**
- Mix ESP32-CAM + Raspberry Pi clients
- Each with unique `device_id`
- All upload to same server
- Face recognition runs centrally

**Example:**
```yaml
# ESP32 #1
DEVICE_ID "ESP32-CAM-Front"

# ESP32 #2
DEVICE_ID "ESP32-CAM-Back"

# Raspberry Pi
device_id: 'RaspberryPi-CAM-Door'
```

### OTA Updates (ESP32)

Add to `main.cpp`:
```cpp
#include <ArduinoOTA.h>

void setup() {
    // ... existing setup
    ArduinoOTA.begin();
}

void loop() {
    ArduinoOTA.handle();
    // ... existing loop
}
```

Upload via WiFi: `pio run --target upload --upload-port <ESP32_IP>`

### Deep Sleep (ESP32)

Save power on battery:
```cpp
#define SLEEP_TIMEOUT_MS 300000  // 5 min

void loop() {
    if (millis() - lastMotionTime > SLEEP_TIMEOUT_MS) {
        esp_sleep_enable_ext0_wakeup(GPIO_NUM_13, 1);  // Wake on PIR
        esp_deep_sleep_start();
    }
}
```

### Custom Workflows

See [server/rules.yaml](server/rules.yaml) for examples.

**Extend in `app.py`:**
```python
elif action_type == 'telegram':
    import telegram
    bot = telegram.Bot(token=action['bot_token'])
    bot.send_photo(chat_id=action['chat_id'], photo=open(image_path, 'rb'))
```

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- [ ] Add HTTPS support (reverse proxy guide)
- [ ] DeepFace integration (alternative to YuNet/SFace)
- [ ] Mobile app (React Native / Flutter)
- [ ] MQTT support for Home Assistant
- [ ] Docker Compose setup
- [ ] Support more ESP32 camera boards (M5Stack, WROVER)
- [ ] Person tracking (motion between cameras)
- [ ] Web push notifications (for headless servers)

**How to contribute:**
1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file.

Free for personal and commercial use.

---

## 🙏 Acknowledgments

- **Espressif** - ESP32 platform and camera drivers
- **Raspberry Pi Foundation** - Raspberry Pi and picamera2
- **OpenCV** - YuNet and SFace models
- **Flask** - Web framework
- **Contributors** - See GitHub contributors page

---

## 💬 Support

### Get Help

1. **Check documentation** - Most questions answered in docs
2. **Search issues** - Someone may have asked before
3. **Open issue** - Describe problem with logs/screenshots

**Issues:** https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server/issues

### FAQ

**Q: Can I use only Raspberry Pi (no ESP32)?**
A: Yes! See [docs/RASPBERRY_PI.md](docs/RASPBERRY_PI.md) for client or standalone setup.

**Q: Does it work with USB webcam instead of CSI camera?**
A: Yes! Raspberry Pi client supports both. Set `camera.device_index: 0` in config.

**Q: Can I run server on Raspberry Pi?**
A: Yes! Pi 4/5 recommended. See [docs/RASPBERRY_PI.md → Standalone](docs/RASPBERRY_PI.md#standalone-mode).

**Q: How to disable face recognition?**
A: Set `face_recognition.enabled: false` in `config.yaml`.

**Q: Is internet required?**
A: No! Fully local. Only needs LAN connection between camera and server.

**Q: Can I use multiple servers?**
A: Not directly. Each camera connects to one server. Use load balancer if needed.

**Q: GDPR compliant?**
A: For household use: yes (legitimate interest). Post signage for common areas. Don't expose to public.

---

## ⚡ Quick Reference

### Start Server (Windows)
```bash
cd server
python app.py
```

### Start Server (Linux)
```bash
sudo systemctl start motion-detector-server
sudo journalctl -u motion-detector-server -f
```

### Upload ESP32 Firmware
```bash
cd esp32
pio run --target upload
pio device monitor
```

### Start Raspberry Pi Client
```bash
sudo systemctl start motion-detector-client
sudo journalctl -u motion-detector-client -f
```

### View Stream
```
http://localhost:5000/stream?token=YOUR_TOKEN
```

### Generate Token
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Get Server IP
```bash
# Windows
ipconfig

# Linux/Pi
hostname -I
```

---

**Built with ❤️ for the maker community**

**Status:** ✅ Production Ready | 🌍 Multi-Platform | 🤖 Face Recognition: YuNet + SFace | 📸 Cameras: ESP32 + Raspberry Pi

**Installation Guide:** [INSTALLATION.md](INSTALLATION.md) - Complete troubleshooting and solutions

**Last Updated:** 2024-12-22
