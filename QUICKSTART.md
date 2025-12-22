# 🚀 Quick Start Guide

## Choose Your Setup

### 🖥️ Windows Server + ESP32-CAM

**1. Install Server (One Command):**
```bash
git clone https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server.git
cd ESP32-Motion-Detector-Windows-Server/Server
setup.bat
```

**2. Configure ESP32:**
```bash
cd ../ESP32/Client
# Copy and edit secrets
copy include\secrets.h.example include\secrets.h
notepad include\secrets.h

# Set in secrets.h:
#   WIFI_SSID, WIFI_PASSWORD
#   SERVER_HOST (get from ipconfig)
#   AUTH_TOKEN (shown by setup.bat)

# Upload firmware
pio run --target upload
```

**3. Wire Hardware:**
```
PIR HC-SR501:
  VCC → ESP32-CAM 5V
  GND → ESP32-CAM GND
  OUT → ESP32-CAM GPIO 13
```

**4. Done! 🎉**
- Open: http://localhost:5000
- Trigger PIR and see toast notifications

---

### 🐧 Linux Server + ESP32-CAM

**1. Install Server (One Command):**
```bash
git clone https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server.git
cd ESP32-Motion-Detector-Windows-Server/Server
chmod +x setup.sh
./setup.sh
```

**2. Configure ESP32:**
```bash
cd ../ESP32/Client
cp include/secrets.h.example include/secrets.h
nano include/secrets.h

# Set:
#   WIFI_SSID, WIFI_PASSWORD
#   SERVER_HOST (from hostname -I)
#   AUTH_TOKEN (from setup.sh output)

# Upload firmware
pio run --target upload
```

**3. Wire Hardware:** (same as Windows)

**4. Done! 🎉**
- Server: http://your-server-ip:5000
- Desktop notifications enabled

---

### 🍓 Raspberry Pi Client → Remote Server

**Server Setup:** (Use Windows or Linux guide above)

**Client Setup (One Command):**
```bash
# On Raspberry Pi
git clone https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server.git
cd ESP32-Motion-Detector-Windows-Server/Raspberry-Pi/Client
chmod +x setup.sh
./setup.sh

# Script will ask for:
#   - Server IP
#   - Auth token (from server)
#   - Device ID
```

**Wire PIR Sensor:**
```
PIR HC-SR501:
  VCC → Pi Pin 2 (5V)
  GND → Pi Pin 6 (GND)
  OUT → Pi Pin 11 (GPIO 17)
```

**Connect Camera:**
- CSI Camera Module: Insert ribbon cable (blue side up)
- USB Webcam: Just plug in

**Done! 🎉**

---

### 🍓 Raspberry Pi Standalone (All-in-One)

**Install Server on Pi (One Command):**
```bash
git clone https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server.git
cd ESP32-Motion-Detector-Windows-Server/Server
chmod +x setup.sh
./setup.sh

# When asked for notification backend:
#   - 'linux_notify' if using Desktop
#   - 'disabled' for headless
```

**Install Client on Same Pi:**
```bash
cd ../clients/raspi
chmod +x setup.sh
./setup.sh

# Server IP: 127.0.0.1 (localhost)
# Auth token: from server setup
```

**Hardware:** (same as Pi Client above)

**Done! 🎉**
- Access Web UI: http://raspberrypi.local:5000

---

## ⚡ Super Quick Reference

| Setup | Install Command |
|-------|----------------|
| **Windows Server** | `cd server && setup.bat` |
| **Linux Server** | `cd server && ./setup.sh` |
| **Raspberry Pi Client** | `cd clients/raspi && ./setup.sh` |
| **ESP32** | Manual: Copy `secrets.h.example` → `secrets.h` |

---

## 🔧 First Run Checklist

- [ ] Server is running (see `http://localhost:5000`)
- [ ] Auth token is set in both server and client/ESP32
- [ ] Server IP is correct in client/ESP32 configuration
- [ ] Firewall allows port 5000
- [ ] Camera is detected (Raspberry Pi: `libcamera-hello --list-cameras`)
- [ ] PIR sensor is connected
- [ ] Server and client are on same network

---

## 🐛 Problems?

**Server won't start:**
```bash
# Check logs
cat server/server.log

# Test Python
python --version  # Should be 3.8+

# Reinstall
pip install -r requirements.txt
```

**ESP32/Client can't connect:**
```bash
# Test server from client
curl http://SERVER_IP:5000/health
# Should return: {"status": "ok"}

# Check firewall (Windows)
netsh advfirewall firewall add rule name="ESP32 Server" dir=in action=allow protocol=TCP localport=5000
```

**More help:** See [INSTALLATION.md](INSTALLATION.md)

---

## 📖 Full Documentation

- **Complete README:** [README.md](README.md)
- **Installation & Troubleshooting:** [INSTALLATION.md](INSTALLATION.md)
- **Face Recognition:** [docs/FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md)
- **Linux Server:** [Linux/Linux.md](Linux/Linux.md)
- **Raspberry Pi:** [Raspberry-Pi/Raspberry.md](Raspberry-Pi/Raspberry.md)
- **ESP32 Firmware:** [ESP32/ESP32.md](ESP32/ESP32.md)

---

**Need help?** Open an issue on [GitHub](https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server/issues)
