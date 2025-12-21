# ESP32 Motion Detector - Windows Server

Python-based Flask server for receiving motion-triggered photos and live stream from ESP32-CAM.

## Features

- ✅ **Motion Event Handling**: Receive JPEG photos via HTTP POST
- ✅ **Windows Toast Notifications**: Popup alerts with image preview
- ✅ **Live MJPEG Stream**: ~10 fps browser-viewable stream
- ✅ **Face Recognition Ready**: Placeholder pipeline for OpenCV/face_recognition
- ✅ **Workflow Automation**: Rule-based actions (Telegram, webhooks, etc.)
- ✅ **Secure**: Token-based authentication
- ✅ **Logging**: Comprehensive event logging

## Requirements

- **OS**: Windows 10/11
- **Python**: 3.8 or higher
- **Network**: Same WiFi/LAN as ESP32

## Quick Start

### 1. Install Python

Download Python from [python.org](https://www.python.org/downloads/)

During installation, **check "Add Python to PATH"**!

### 2. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 3. Configure Server

Edit `config.yaml`:

```yaml
security:
  auth_token: 'YOUR_SECRET_TOKEN_CHANGE_ME_12345'  # ⚠️ CHANGE THIS!
```

**Generate a secure token:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Run Server

```bash
python app.py
```

Server starts on `http://0.0.0.0:5000`

### 5. Test Server

Open browser: `http://localhost:5000`

You should see the dashboard with live stream view.

## Endpoints

### `GET /`
Main dashboard with live stream

### `POST /upload`
Receive motion-triggered photos from ESP32

**Headers:**
- `X-Auth-Token`: Your auth token

**Body:**
- `multipart/form-data` with `image` file
- Optional: `device_id` field

**Response:**
```json
{
  "status": "success",
  "filename": "ESP32-CAM_20240101_123045.jpg",
  "faces_detected": 1,
  "persons": ["Unknown"]
}
```

### `POST /stream_frame`
Receive streaming frames from ESP32

**Headers:**
- `X-Auth-Token`: Your auth token

**Body:**
- Raw JPEG bytes

### `GET /stream?token=YOUR_TOKEN`
MJPEG live stream for browsers

Open in browser: `http://localhost:5000/stream?token=YOUR_SECRET_TOKEN_CHANGE_ME_12345`

### `GET /latest`
View latest captured image

### `GET /health`
Server health check

## Configuration

### `config.yaml`

```yaml
server:
  host: '0.0.0.0'      # Listen on all interfaces
  port: 5000           # HTTP port
  debug: false         # Enable Flask debug mode
  log_level: 'INFO'    # DEBUG, INFO, WARNING, ERROR

security:
  auth_token: 'CHANGE_ME'
  require_auth_for_stream: true

storage:
  image_dir: './captured_images'
  max_images: 1000
  max_age_days: 30

notifications:
  enabled: true
  sound: true

face_recognition:
  enabled: false       # Set to true when implementing
  min_confidence: 0.6

stream:
  target_fps: 10
  jpeg_quality: 80
```

### `rules.yaml`

Define automated workflows:

```yaml
rules:
  - name: "Alert Unknown Person"
    conditions:
      person: "Unknown"
      min_confidence: 0.5
    actions:
      - type: log
        message: "⚠️ Unknown person detected"

      - type: telegram
        bot_token: "YOUR_BOT_TOKEN"
        chat_id: "YOUR_CHAT_ID"
        message: "Unknown person at door!"
```

See `rules.yaml` for more examples.

## Testing

### Test Upload with curl

```bash
curl -X POST http://localhost:5000/upload ^
  -H "X-Auth-Token: YOUR_SECRET_TOKEN_CHANGE_ME_12345" ^
  -F "image=@test.jpg" ^
  -F "device_id=TEST"
```

### Test Health

```bash
curl http://localhost:5000/health
```

### Test Stream in Browser

```
http://localhost:5000/stream?token=YOUR_SECRET_TOKEN_CHANGE_ME_12345
```

## Troubleshooting

### Toast Notifications Not Showing

**Problem**: No popup appears on motion event

**Solutions:**
1. Check Windows Focus Assist settings (should be OFF or allow priority)
2. Check Windows Notifications settings (enable for Python)
3. Run server as Administrator (right-click → Run as administrator)
4. Check logs: `server.log`

### "winotify" Installation Failed

**Problem**: `pip install winotify` fails

**Solution:**
```bash
pip install --upgrade pip
pip install winotify --no-cache-dir
```

### Firewall Blocking Connections

**Problem**: ESP32 can't connect to server

**Solutions:**
1. Open Windows Firewall
2. Add inbound rule for port 5000
3. Or temporarily disable firewall for testing

**PowerShell command:**
```powershell
New-NetFirewallRule -DisplayName "ESP32 Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Port Already in Use

**Problem**: `Address already in use`

**Solution:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

Or change port in `config.yaml`.

### Stream Freezes or Lags

**Possible causes:**
1. WiFi signal weak → Move ESP32 closer to router
2. Network congestion → Use 5GHz WiFi if possible
3. Server CPU overload → Close other apps
4. ESP32 overheating → Add cooling

**Check logs:**
```
tail -f server.log
```

## Extending Face Recognition

### Install face_recognition Library

```bash
pip install opencv-python
pip install face-recognition
pip install dlib
```

**Note:** `dlib` requires Visual Studio C++ Build Tools on Windows.

Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/

### Add Known Faces

1. Create folder: `known_faces/PersonName/`
2. Add photos: `person1.jpg`, `person2.jpg`, etc.
3. Enable in `config.yaml`:
   ```yaml
   face_recognition:
     enabled: true
   ```

### Implement Recognition

Edit `app.py` → `FaceRecognitionPipeline.recognize_faces()`:

```python
import face_recognition
import numpy as np
from PIL import Image

def recognize_faces(self, image_bytes):
    img = Image.open(BytesIO(image_bytes))
    img_array = np.array(img)

    face_locations = face_recognition.face_locations(img_array)
    face_encodings = face_recognition.face_encodings(img_array, face_locations)

    results = []
    for encoding, location in zip(face_encodings, face_locations):
        # Compare with known faces
        matches = face_recognition.compare_faces(self.known_encodings, encoding)
        name = "Unknown"

        if True in matches:
            match_index = matches.index(True)
            name = self.known_names[match_index]

        results.append({
            'name': name,
            'confidence': 0.95 if name != "Unknown" else 0.5,
            'bbox': location
        })

    return results
```

## Workflow Automation

### Add Telegram Notifications

1. Create bot with [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat_id (use [@userinfobot](https://t.me/userinfobot))
4. Install library:
   ```bash
   pip install python-telegram-bot
   ```
5. Edit `rules.yaml`:
   ```yaml
   - type: telegram
     bot_token: "123456:ABC-DEF..."
     chat_id: "123456789"
   ```
6. Implement in `app.py` → `WorkflowEngine._execute_actions()`:
   ```python
   import telegram
   bot = telegram.Bot(token=action['bot_token'])
   bot.send_photo(chat_id=action['chat_id'], photo=open(image_path, 'rb'))
   ```

### Add Webhooks

```yaml
- type: webhook
  url: "https://maker.ifttt.com/trigger/motion/with/key/YOUR_KEY"
  method: "POST"
```

Implement:
```python
import requests
requests.post(action['url'], json={'person': person_name, 'image': str(image_path)})
```

## Performance Optimization

### Reduce Image Size

Edit `config.yaml`:
```yaml
stream:
  jpeg_quality: 60  # Lower = smaller files, faster transfer
```

Edit ESP32 firmware → `framesize`:
```cpp
config.frame_size = FRAMESIZE_VGA;  // 640x480 instead of 800x600
```

### Increase FPS

**Warning:** ESP32-CAM realistic limit is ~10-15 fps

Reduce ESP32 `STREAM_INTERVAL_MS`:
```cpp
#define STREAM_INTERVAL_MS 66  // ~15 fps
```

### Auto-Cleanup Old Images

Add to `app.py`:
```python
import os
import time

def cleanup_old_images():
    max_age = config['storage']['max_age_days'] * 86400
    now = time.time()

    for filepath in STORAGE_DIR.glob('*.jpg'):
        if now - filepath.stat().st_mtime > max_age:
            filepath.unlink()
            logger.info(f"Deleted old image: {filepath}")
```

## Security Best Practices

1. ✅ **Change default token** in `config.yaml`
2. ✅ **Use strong WiFi password**
3. ✅ **Keep server on LAN only** (don't expose to internet)
4. ✅ **Enable Windows Firewall** with port 5000 rule
5. ⚠️ **Don't commit `secrets.h`** to Git
6. ⚠️ **Use HTTPS** if exposing server (requires reverse proxy)

## Production Deployment

### Run as Windows Service

Use `NSSM` (Non-Sucking Service Manager):

1. Download: https://nssm.cc/download
2. Install service:
   ```cmd
   nssm install ESP32Server "C:\Python310\python.exe" "C:\path\to\server\app.py"
   ```
3. Start service:
   ```cmd
   nssm start ESP32Server
   ```

### Auto-Start on Boot

Create batch file `start_server.bat`:
```batch
@echo off
cd /d C:\path\to\server
python app.py
pause
```

Add to Windows Startup folder:
```
C:\Users\YourUser\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
```

## Support

### Logs

Check `server.log` for errors:
```bash
type server.log
```

### Enable Debug Mode

Edit `config.yaml`:
```yaml
server:
  debug: true
  log_level: 'DEBUG'
```

**⚠️ Disable in production!**

## License

MIT License - See main project README
