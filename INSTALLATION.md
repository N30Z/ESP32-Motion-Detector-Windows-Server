# Installation & Troubleshooting Guide

## 🚀 Quick Installation

### Windows Server

```bash
git clone <repository-url>
cd ESP32-Motion-Detector-Windows-Server/Server
setup.bat
```

**That's it!** The script will:
- Check Python installation
- Install all dependencies
- Download face recognition models
- Create configuration file with auth token
- Test server startup

### Linux Server

```bash
git clone <repository-url>
cd ESP32-Motion-Detector-Windows-Server/Server
chmod +x setup.sh
./setup.sh
```

### Raspberry Pi Client

```bash
git clone <repository-url>
cd ESP32-Motion-Detector-Windows-Server/Raspberry-Pi/Client
chmod +x setup.sh
./setup.sh
```

### Raspberry Pi Standalone

```bash
git clone <repository-url>
cd ESP32-Motion-Detector-Windows-Server/Raspberry-Pi/Standalone
chmod +x setup.sh
./setup.sh
```

---

## 🔍 Common Installation Issues & Solutions

### 1. Python Not Found

**Error:**
```
'python' is not recognized as an internal or external command
Python 3 is not installed!
```

**Solutions:**

**Windows:**
1. Download Python from [python.org](https://www.python.org/downloads/)
2. During installation: **CHECK "Add Python to PATH"** ✓
3. Restart command prompt
4. Verify: `python --version`

**Linux/Raspberry Pi:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Verify
python3 --version
```

---

### 2. Python Version Too Old

**Error:**
```
Python 3.8 or higher is required (found: 3.7.3)
```

**Solutions:**

**Ubuntu/Debian:**
```bash
# Install newer Python from deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3-pip

# Use python3.10 instead of python3
python3.10 --version
```

**Raspberry Pi:**
```bash
# Update to latest Raspberry Pi OS (Bookworm has Python 3.11)
sudo apt update && sudo apt full-upgrade

# Or compile Python from source (advanced)
```

**Windows:**
- Uninstall old Python from "Apps & Features"
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)

---

### 3. pip Installation Fails

**Error:**
```
ERROR: Could not install packages due to an OSError
Permission denied
```

**Solutions:**

**Option 1: Use Virtual Environment (Recommended)**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate.bat  # Windows
pip install -r requirements.txt
```

**Option 2: User Installation**
```bash
pip install --user -r requirements.txt
```

**Option 3: Fix Permissions (Linux only)**
```bash
sudo chown -R $USER:$USER ~/.local
```

---

### 4. opencv-contrib-python Build Errors

**Error:**
```
Building wheel for opencv-contrib-python... error
Failed to build opencv-contrib-python
```

**Solutions:**

**Raspberry Pi:**
```bash
# Install pre-built OpenCV from system packages (faster!)
sudo apt install python3-opencv

# Update requirements.txt: comment out opencv-contrib-python
# (system package will be used instead)
```

**Linux:**
```bash
# Install build dependencies
sudo apt install build-essential cmake pkg-config
sudo apt install libgtk-3-dev libavcodec-dev libavformat-dev libswscale-dev

# Then retry pip install
pip install opencv-contrib-python
```

**Windows:**
- Update pip: `python -m pip install --upgrade pip`
- Install Microsoft C++ Build Tools from [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- Retry installation

---

### 5. Model Download Fails

**Error:**
```
Failed to download face_detection_yunet_2023mar.onnx
urllib.error.URLError: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED]>
```

**Solutions:**

**Option 1: Fix SSL Certificates (Recommended)**
```bash
# Ubuntu/Debian
sudo apt install ca-certificates
sudo update-ca-certificates

# macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Windows
# Install certificates via pip
pip install --upgrade certifi
```

**Option 2: Manual Download**
```bash
cd Server/models

# Download YuNet
curl -L -o face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

# Download SFace
curl -L -o face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

**Option 3: Download from Browser**
1. Open URLs in browser (see above)
2. Save files to `Server/models/` directory
3. Verify filenames match exactly

---

### 6. Windows Toast Notifications Don't Work

**Error:**
```
Toast notification not shown
```

**Solutions:**

1. **Check Focus Assist:**
   - Settings → System → Focus Assist
   - Set to "Off" or "Priority only"

2. **Enable Notifications for Python:**
   - Settings → System → Notifications & actions
   - Find "Python" in the list
   - Enable notifications

3. **Run as Administrator (if needed):**
   - Right-click Command Prompt
   - "Run as Administrator"
   - Run setup.bat again

4. **Check Windows 10/11 Version:**
   - Toast notifications require Windows 10 version 1903+
   - Update Windows if needed

5. **Disable if Problematic:**
   - Edit `config.yaml`: `notifications.enabled: false`
   - Or use: `notifications.backend: 'disabled'`

---

### 7. Linux Notifications Don't Work

**Error:**
```
notify-send: command not found
```

**Solutions:**

1. **Install libnotify:**
```bash
# Ubuntu/Debian
sudo apt install libnotify-bin

# Fedora
sudo dnf install libnotify

# Test
notify-send "Test" "Message"
```

2. **Check DISPLAY variable (for SSH/headless):**
```bash
echo $DISPLAY  # Should show :0 or similar

# If empty, set it:
export DISPLAY=:0
notify-send "Test" "Message"
```

3. **For Headless Servers:**
   - Notifications won't work without Desktop Environment
   - Use `notifications.backend: 'disabled'` in config.yaml
   - Access events via Web UI: `http://server:5000/events`

---

### 8. Raspberry Pi Camera Not Detected

**Error:**
```
Camera test failed
Failed to initialize camera
```

**Solutions:**

1. **Enable Camera Interface:**
```bash
sudo raspi-config
# Interface Options → Camera → Enable → Reboot
```

2. **Check Camera Connection:**
   - Power off Raspberry Pi
   - Ensure ribbon cable is fully inserted (blue side up on Pi 4/5)
   - Power on and test:
```bash
libcamera-hello --list-cameras
# or on older systems:
vcgencmd get_camera
```

3. **Update Firmware:**
```bash
sudo apt update
sudo apt full-upgrade
sudo reboot
```

4. **Check config.txt:**
```bash
sudo nano /boot/firmware/config.txt  # or /boot/config.txt

# Ensure these lines exist:
camera_auto_detect=1
# dtoverlay=vc4-kms-v3d  # Comment out if camera doesn't work
```

5. **Use USB Webcam Instead:**
   - Edit `Raspberry-Pi/Client/config.yaml`:
   - Set `camera.device_index: 0`
   - Install opencv: `pip install opencv-python`

---

### 9. GPIO Permission Denied

**Error:**
```
PermissionError: [Errno 13] Permission denied: '/dev/gpiomem'
```

**Solutions:**

1. **Add User to gpio Group:**
```bash
sudo usermod -a -G gpio $USER
# Logout and login again, or:
su - $USER
```

2. **Modern Raspberry Pi OS (Bookworm):**
```bash
# Use lgpio instead of deprecated RPi.GPIO
pip install lgpio
# gpiozero will automatically use lgpio backend
```

3. **Run as Root (Not Recommended):**
```bash
sudo python3 pir_cam_client.py
```

---

### 10. Port 5000 Already in Use

**Error:**
```
OSError: [Errno 98] Address already in use
Port 5000 is already in use
```

**Solutions:**

1. **Find and Kill Process:**
```bash
# Linux
sudo lsof -i :5000
sudo kill -9 <PID>

# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

2. **Change Port:**
   - Edit `Server/config.yaml`:
   - `server.port: 5001` (or any free port)
   - Update client configuration accordingly

---

### 11. Firewall Blocks Connection

**Error:**
```
Connection refused
ESP32/Client cannot reach server
```

**Solutions:**

**Windows:**
```powershell
# Add firewall rule
netsh advfirewall firewall add rule name="ESP32 Motion Server" dir=in action=allow protocol=TCP localport=5000

# Or use GUI:
# Windows Security → Firewall → Allow an app
# Add Python and allow on Private/Public networks
```

**Linux:**
```bash
# UFW
sudo ufw allow 5000/tcp
sudo ufw enable

# firewalld
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload

# iptables
sudo iptables -A INPUT -p tcp --dport 5000 -j ACCEPT
sudo iptables-save
```

**Test Connection:**
```bash
# From client device
curl http://SERVER_IP:5000/health

# Should return: {"status": "ok"}
```

---

### 12. Virtual Environment Issues

**Error:**
```
venv/Scripts/activate.bat is not recognized
source: command not found
```

**Solutions:**

**Windows:**
```batch
REM Use correct activation script:
venv\Scripts\activate.bat   REM Command Prompt
venv\Scripts\Activate.ps1   REM PowerShell

REM If PowerShell script execution is blocked:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/Mac:**
```bash
# Use correct source command
source venv/bin/activate

# If 'source' not found (some shells):
. venv/bin/activate
```

**Deactivate:**
```bash
deactivate  # Works on all platforms
```

---

## 🧪 Verification Steps

### Test Server Installation

```bash
cd Server

# Check Python version
python --version  # or python3 --version

# Check packages
pip list | grep -i flask
pip list | grep -i opencv
pip list | grep -i numpy

# Check models
ls -lh models/*.onnx

# Test import
python -c "import cv2; print(cv2.__version__)"
python -c "import flask; print(flask.__version__)"

# Start server (should not error)
python app.py
# Press Ctrl+C after seeing "Running on http://..."
```

### Test Client Installation (Raspberry Pi)

```bash
cd Raspberry-Pi/Client

# Check camera
libcamera-hello --list-cameras

# Check GPIO permissions
groups | grep gpio

# Test imports
python3 -c "from picamera2 import Picamera2; print('Camera OK')"
python3 -c "from gpiozero import MotionSensor; print('GPIO OK')"

# Test server connection
SERVER_IP="192.168.1.100"  # Replace with your server IP
curl http://$SERVER_IP:5000/health
```

---

## 📚 Additional Resources

### Platform-Specific Guides

- **Windows:** [Windows/Windows.md](Windows/Windows.md) - Complete Windows installation guide
- **Linux:** [Linux/Linux.md](Linux/Linux.md) - Complete Linux installation guide
- **Raspberry Pi:** [Raspberry-Pi/Raspberry.md](Raspberry-Pi/Raspberry.md) - All Pi modes (Client/Server/Standalone)
- **ESP32:** [ESP32/ESP32.md](ESP32/ESP32.md) - ESP32-CAM firmware guide

### Technical Documentation

- **Main README:** [README.md](README.md) - Project overview and quick start
- **Face Recognition:** [docs/FACE_RECOGNITION.md](docs/FACE_RECOGNITION.md) - Deep-dive into FR system
- **Server API:** [Server/README.md](Server/README.md) - Server configuration and API
- **Changelog:** [CHANGELOG.md](CHANGELOG.md) - Version history and migration guides

---

## 💡 Tips for Smooth Installation

1. ✅ **Use Virtual Environments** - Isolates dependencies, prevents conflicts
2. ✅ **Update System First** - `sudo apt update && sudo apt upgrade` (Linux)
3. ✅ **Check Python Version** - Must be 3.8 or higher
4. ✅ **Read Error Messages** - They usually tell you what's wrong
5. ✅ **Test Step-by-Step** - Don't skip verification steps
6. ✅ **Check Network** - Server and client must be on same LAN
7. ✅ **Save Auth Token** - You'll need it for client configuration
8. ✅ **Restart After Changes** - Reboot after enabling camera/GPIO

---

## 🐛 Still Having Issues?

1. **Check logs:**
   ```bash
   # Server
   cat Server/server.log

   # Raspberry Pi Client (systemd)
   sudo journalctl -u motion-detector-client -n 50

   # Raspberry Pi Standalone (both services)
   sudo journalctl -u motion-detector-server -n 50
   sudo journalctl -u motion-detector-client -n 50
   ```

2. **Enable debug mode:**
   ```yaml
   # config.yaml
   server:
     debug: true
     log_level: 'DEBUG'
   ```

3. **Open an issue:**
   - GitHub Issues: [Project Repository](https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server/issues)
   - Include: OS, Python version, error message, log excerpt

---

**Last Updated:** 2025-12-22
