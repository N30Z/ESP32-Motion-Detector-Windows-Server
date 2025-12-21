# Motion Detector Server - Multi-Platform

Python-based Flask server for receiving motion-triggered photos and live stream from ESP32-CAM or Raspberry Pi camera clients.

## Features

- ✅ **Multi-Platform**: Windows 10/11 and Linux support
- ✅ **Motion Event Handling**: Receive JPEG photos via HTTP POST
- ✅ **Desktop Notifications**: Windows Toast or Linux notify-send
- ✅ **Live MJPEG Stream**: ~10 fps browser-viewable stream
- ✅ **Face Recognition**: YuNet + SFace (OpenCV) with auto-learning
- ✅ **Person Management**: Web UI for managing persons and face samples
- ✅ **Event Tracking**: SQLite database with full history
- ✅ **Workflow Automation**: Rule-based actions (Telegram, webhooks, etc.)
- ✅ **Secure**: Token-based authentication
- ✅ **Logging**: Comprehensive event logging

## Platform Support

| Platform | Notifications | systemd Service | Status |
|----------|---------------|-----------------|--------|
| Windows 10/11 | Toast | ❌ | ✅ Fully supported |
| Linux Desktop | notify-send | ✅ | ✅ Fully supported |
| Linux Headless | Disabled | ✅ | ✅ Fully supported |
| Raspberry Pi | Disabled/notify-send | ✅ | ✅ Fully supported |

## Requirements

- **Python**: 3.8 or higher
- **OS**: Windows 10/11 or Linux (Ubuntu/Debian/Raspberry Pi OS)
- **Network**: Same WiFi/LAN as camera clients
- **Storage**: ~500MB for models and database

## Quick Start

### Windows

#### 1. Install Python

Download Python from [python.org](https://www.python.org/downloads/)

During installation, **check "Add Python to PATH"**!

#### 2. Install Dependencies

```bash
cd server
pip install -r requirements.txt
pip install -r requirements-windows.txt
```

#### 3. Download Face Recognition Models

```bash
python models/download_models.py
```

This downloads YuNet (~200KB) and SFace (~5MB) from OpenCV Zoo.

#### 4. Configure Server

Edit `config.yaml`:

```yaml
security:
  auth_token: 'YOUR_SECRET_TOKEN_CHANGE_ME_12345'  # ⚠️ CHANGE THIS!

notifications:
  enabled: true
  backend: 'windows_toast'  # Windows Toast notifications
  sound: true

face_recognition:
  enabled: true
```

**Generate a secure token:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 5. Run Server

```bash
python app.py
```

Server starts on `http://0.0.0.0:5000`

#### 6. Test Server

Open browser: `http://localhost:5000`

You should see the dashboard with live stream view.

### Linux

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install libnotify-bin  # For desktop notifications (optional)
```

#### 2. Create Virtual Environment

```bash
cd server
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-linux.txt  # Linux-specific packages
```

#### 4. Download Face Recognition Models

```bash
python models/download_models.py
```

#### 5. Configure Server

```bash
cp config.yaml.example config.yaml  # If needed
nano config.yaml
```

Edit:
```yaml
security:
  auth_token: 'YOUR_SECRET_TOKEN_CHANGE_ME_12345'  # ⚠️ CHANGE THIS!

notifications:
  enabled: true
  backend: 'linux_notify'  # Desktop: linux_notify, Headless: disabled
  sound: true

face_recognition:
  enabled: true
```

#### 6. Run Server

```bash
python app.py
```

#### 7. Install as systemd Service (Optional)

See [docs/LINUX_SETUP.md](../docs/LINUX_SETUP.md) for complete instructions.

**Quick install:**
```bash
sudo cp ../deploy/linux/systemd/motion-detector-server.service /etc/systemd/system/
sudo systemctl enable motion-detector-server
sudo systemctl start motion-detector-server
```

## Web Interface

### Dashboard (`/`)

- Live MJPEG stream from active cameras
- Latest motion events
- Quick stats (events today, known persons, etc.)

### Configuration (`/config`)

- Face recognition threshold tuning
- Auto-learning settings
- Notification preferences
- View current settings

### Persons (`/persons`)

- List all known persons
- Rename persons (Unknown → Actual Name)
- View sample count per person
- Merge duplicate persons
- Delete persons

### Person Detail (`/persons/<id>`)

- View all face samples for a person
- Sample thumbnails with quality scores
- Event history for this person
- Delete individual samples
- Delete person

### Events (`/events`)

- Complete event history
- Filter by date, person, device
- View captured images
- Face recognition results

## API Endpoints

### `GET /`
Main dashboard with live stream

### `POST /upload`
Receive motion-triggered photos from camera clients

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
  "face_recognition": {
    "enabled": true,
    "faces_detected": 1,
    "results": [
      {
        "person_id": 1,
        "person_name": "John Doe",
        "status": "GREEN",
        "confidence": 0.92,
        "bbox": [100, 150, 200, 250]
      }
    ]
  }
}
```

### `POST /stream_frame`
Receive streaming frames from camera clients

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

**Response:**
```json
{
  "status": "healthy",
  "uptime_seconds": 3600,
  "face_recognition": "enabled",
  "database": "connected"
}
```

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
  backend: 'windows_toast'  # windows_toast, linux_notify, disabled
  sound: true

face_recognition:
  enabled: true
  threshold_strict: 0.35   # Distance for GREEN match (reliable)
  threshold_loose: 0.50    # Distance for YELLOW match (uncertain)
  margin_strict: 0.15      # Margin for GREEN (d2-d1)
  margin_loose: 0.08       # Margin for YELLOW

  auto_learning:
    enabled: true
    max_samples_per_person: 15
    min_quality_score: 0.6
    cooldown_seconds: 60

  auto_create_person:
    enabled: true          # Create new person for unknown faces

stream:
  target_fps: 10
  jpeg_quality: 80
```

### `rules.yaml`

Define automated workflows (optional):

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

## Face Recognition

### How It Works

The server uses a **two-stage pipeline**:

1. **YuNet Face Detector**: Finds faces in images (~200KB ONNX model)
2. **SFace Embedder**: Extracts 128-dim feature vectors (~5MB ONNX model)

### Matching Algorithm

Uses **distance + margin** approach:

- **Distance (d1)**: Cosine distance to closest known person
- **Margin (d2-d1)**: Gap to second-closest person
- **Status**:
  - **GREEN**: d1 < 0.35 AND margin > 0.15 (reliable match)
  - **YELLOW**: d1 < 0.50 AND margin > 0.08 (uncertain match)
  - **UNKNOWN**: No match found

### Auto-Learning

When enabled, the system automatically collects face samples:

- Maximum 15 samples per person
- Quality filtering (face size, sharpness, alignment)
- Cooldown period prevents spam (default: 60 seconds)
- Improves recognition accuracy over time

### Person Management Workflow

1. **Unknown person detected** → System auto-creates `Person #1`
2. **System collects samples** → Auto-learning gathers 15 high-quality samples
3. **Rename person** → Use Web UI `/persons` to rename to actual name
4. **Merge duplicates** → If same person created twice, use merge function

### Threshold Tuning

Use Web UI `/config` to adjust thresholds:

- **Too many false positives?** → Decrease `threshold_loose` or increase `margin_strict`
- **Missing correct matches?** → Increase `threshold_loose` or decrease `margin_strict`
- **Wrong person matched?** → Increase `margin_strict`

See [docs/FACE_RECOGNITION.md](../docs/FACE_RECOGNITION.md) for complete guide with examples.

## Testing

### Test Upload with curl

**Windows:**
```cmd
curl -X POST http://localhost:5000/upload ^
  -H "X-Auth-Token: YOUR_SECRET_TOKEN_CHANGE_ME_12345" ^
  -F "image=@test.jpg" ^
  -F "device_id=TEST"
```

**Linux:**
```bash
curl -X POST http://localhost:5000/upload \
  -H "X-Auth-Token: YOUR_SECRET_TOKEN_CHANGE_ME_12345" \
  -F "image=@test.jpg" \
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

### Windows: Toast Notifications Not Showing

**Problem**: No popup appears on motion event

**Solutions:**
1. Check Windows Focus Assist settings (should be OFF or allow priority)
2. Check Windows Notifications settings (enable for Python)
3. Run server as Administrator (right-click → Run as administrator)
4. Check logs: `server.log`

### Linux: notify-send Not Found

**Problem**: `Command 'notify-send' not found`

**Solution:**
```bash
sudo apt install libnotify-bin
```

Or disable notifications:
```yaml
notifications:
  backend: 'disabled'
```

### Face Recognition Not Working

**Problem**: No faces detected or always UNKNOWN

**Solutions:**
1. Check models downloaded: `ls models/*.onnx`
2. Re-download models: `python models/download_models.py`
3. Check `face_recognition.enabled: true` in config
4. Check image quality (faces should be >80×80 pixels)
5. Check logs for errors: `tail -f server.log`

### Database Locked Error

**Problem**: `database is locked`

**Solutions:**
1. Only one server instance should run
2. Check for zombie processes: `ps aux | grep app.py`
3. Delete lock file: `rm faces.db-journal` (if server not running)

### Firewall Blocking Connections

**Problem**: Camera clients can't connect to server

**Windows:**
```powershell
New-NetFirewallRule -DisplayName "Motion Detector Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

**Linux:**
```bash
sudo ufw allow 5000/tcp
sudo ufw enable
```

### Port Already in Use

**Problem**: `Address already in use`

**Windows:**
```bash
# Find process using port 5000
netstat -ano | findstr :5000

# Kill process (replace PID)
taskkill /PID <PID> /F
```

**Linux:**
```bash
# Find process
sudo lsof -i :5000

# Kill process
sudo kill <PID>
```

Or change port in `config.yaml`.

## Performance Optimization

### Face Recognition Speed

**Typical performance:**
- Windows (Intel i5): ~200-300ms per image
- Linux (i5): ~200-300ms per image
- Raspberry Pi 5: ~400ms per image
- Raspberry Pi 4: ~500ms per image
- Raspberry Pi 3: ~2s per image

**To improve:**
- Disable auto-learning if not needed
- Reduce max_samples_per_person
- Use lower resolution images from cameras

### Database Maintenance

**Auto-cleanup old images:**

Add cron job (Linux) or Task Scheduler (Windows):

```bash
# Delete images older than 30 days
find ./captured_images -name "*.jpg" -mtime +30 -delete
```

**Vacuum database:**

```bash
sqlite3 faces.db "VACUUM;"
```

## Security Best Practices

1. ✅ **Change default token** in `config.yaml`
2. ✅ **Use strong WiFi password**
3. ✅ **Keep server on LAN only** (don't expose to internet without VPN)
4. ✅ **Enable firewall** with port 5000 rule only
5. ⚠️ **Don't commit secrets** to Git (config.yaml, secrets.h)
6. ⚠️ **Use HTTPS** if exposing server (requires reverse proxy like nginx)
7. ✅ **Regular backups** of database and config

## Production Deployment

### Windows: Run as Service

Use `NSSM` (Non-Sucking Service Manager):

1. Download: https://nssm.cc/download
2. Install service:
   ```cmd
   nssm install MotionDetectorServer "C:\Python310\python.exe" "C:\path\to\server\app.py"
   nssm set MotionDetectorServer AppDirectory "C:\path\to\server"
   ```
3. Start service:
   ```cmd
   nssm start MotionDetectorServer
   ```

### Linux: systemd Service

See [docs/LINUX_SETUP.md](../docs/LINUX_SETUP.md) for complete guide.

**Quick setup:**

```bash
# Copy service file
sudo cp ../deploy/linux/systemd/motion-detector-server.service /etc/systemd/system/

# Edit paths in service file
sudo nano /etc/systemd/system/motion-detector-server.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable motion-detector-server
sudo systemctl start motion-detector-server

# Check status
sudo systemctl status motion-detector-server

# View logs
sudo journalctl -u motion-detector-server -f
```

## Backup and Restore

### Backup

**Database:**
```bash
cp faces.db faces.db.backup
```

**Config:**
```bash
cp config.yaml config.yaml.backup
```

**Complete backup:**
```bash
tar -czf motion-detector-backup-$(date +%Y%m%d).tar.gz \
  faces.db config.yaml rules.yaml captured_images/
```

### Restore

```bash
# Extract backup
tar -xzf motion-detector-backup-20240101.tar.gz

# Or restore individual files
cp faces.db.backup faces.db
```

## Documentation

- **[Face Recognition Guide](../docs/FACE_RECOGNITION.md)**: Complete guide to face recognition system
- **[Linux Setup Guide](../docs/LINUX_SETUP.md)**: Linux-specific deployment instructions
- **[Raspberry Pi Guide](../docs/RASPBERRY_PI.md)**: Raspberry Pi client and standalone setup
- **[Main README](../README.md)**: Project overview and multi-platform scenarios

## Support

### Logs

**Check server.log for errors:**

```bash
# Windows
type server.log

# Linux
tail -f server.log
```

### Enable Debug Mode

Edit `config.yaml`:
```yaml
server:
  debug: true
  log_level: 'DEBUG'
```

**⚠️ Disable in production!**

### Database Browser

Use DB Browser for SQLite to inspect database:

Download: https://sqlitebrowser.org/

Open `faces.db` to view persons, face_samples, and events tables.

## License

MIT License - See main project [LICENSE](../LICENSE)
