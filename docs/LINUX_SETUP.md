# Linux Server Setup Guide

Complete deployment guide for running the Motion Detector Server on Linux (Ubuntu/Debian/Raspberry Pi OS).

## Quick Start

```bash
# 1. Install dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv libnotify-bin

# 2. Create directory
sudo mkdir -p /opt/motion-detector
sudo chown $USER:$USER /opt/motion-detector

# 3. Copy server files
cd /opt/motion-detector
git clone <repo-url> .
# Or manually copy server/ directory

# 4. Setup Python environment
cd server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-linux.txt  # notify2

# 5. Download models
python models/download_models.py

# 6. Configure
cp config.yaml config.yaml.backup
nano config.yaml
# Set:
#   - auth_token
#   - face_recognition.enabled: true
#   - notifications.backend: 'linux_notify' (or 'disabled' for headless)

# 7. Test run
python app.py
# Open browser: http://localhost:5000

# 8. Setup systemd service
sudo cp ../deploy/linux/systemd/motion-detector-server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable motion-detector-server
sudo systemctl start motion-detector-server

# Check status
sudo systemctl status motion-detector-server
sudo journalctl -u motion-detector-server -f
```

## Notifications on Linux

### Desktop (with GUI)

**Requirements:**
```bash
sudo apt install libnotify-bin
```

**Config:**
```yaml
notifications:
  enabled: true
  backend: 'linux_notify'
```

**Test:**
```bash
notify-send "Test" "Motion detected" --icon=camera-video
```

### Headless Server

**Config:**
```yaml
notifications:
  enabled: false
  backend: 'disabled'
```

Events visible in Web UI: `http://server:5000/events`

## Performance

| Hardware | Face Recognition | FPS | Notes |
|----------|------------------|-----|-------|
| Ubuntu Desktop (i5) | ~100ms | 10 fps | Ideal |
| Raspberry Pi 4 | ~500ms | 5 fps | Acceptable |
| Raspberry Pi 3 | ~2s | 2 fps | Slow but works |

**Optimization for Pi:**
```yaml
face_recognition:
  threshold_strict: 0.40  # Slightly higher (faster matching)

camera:
  resolution: [640, 480]  # Lower resolution
  jpeg_quality: 75
```

## Firewall

```bash
# Allow port 5000
sudo ufw allow 5000/tcp

# Or restrict to LAN
sudo ufw allow from 192.168.1.0/24 to any port 5000
```

## Troubleshooting

### No notifications showing

**Check:**
```bash
# Desktop environment running?
echo $DISPLAY  # Should show :0 or similar

# notify-send works?
notify-send "Test" "Message"
```

**Fix:** Login to GUI session or set `backend: 'disabled'`

### Permission denied (GPIO/Camera)

For standalone Pi:
```bash
sudo usermod -a -G video,gpio $USER
# Logout and login again
```

### Models not found

```bash
cd /opt/motion-detector/server
source venv/bin/activate
python models/download_models.py

# Verify
ls models/*.onnx
```

## Security

**Production checklist:**
- ✅ Change `auth_token` in config.yaml
- ✅ Enable firewall (ufw)
- ✅ Use non-root user for service
- ✅ Set restrictive file permissions:
  ```bash
  chmod 600 config.yaml
  ```
- ✅ Regular updates:
  ```bash
  source venv/bin/activate
  pip install --upgrade -r requirements.txt
  ```

## Auto-Start on Boot

Service already configured in systemd unit.

**Enable:**
```bash
sudo systemctl enable motion-detector-server
```

**Disable:**
```bash
sudo systemctl disable motion-detector-server
```

## Logs

**View live:**
```bash
sudo journalctl -u motion-detector-server -f
```

**Last 100 lines:**
```bash
sudo journalctl -u motion-detector-server -n 100
```

**App log file:**
```bash
tail -f /opt/motion-detector/server/server.log
```

## Backup

**Database:**
```bash
cp /opt/motion-detector/server/faces.db ~/backup/faces_$(date +%Y%m%d).db
```

**Config:**
```bash
cp /opt/motion-detector/server/config.yaml ~/backup/
```

## Uninstall

```bash
sudo systemctl stop motion-detector-server
sudo systemctl disable motion-detector-server
sudo rm /etc/systemd/system/motion-detector-server.service
sudo systemctl daemon-reload
sudo rm -rf /opt/motion-detector
```
