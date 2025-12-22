# Docker Deployment

Run the Motion Detector Server in Docker containers.

---

## Quick Start

### 1. Setup

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
# Set AUTH_TOKEN (generate with: openssl rand -base64 32)
```

### 2. Start Server

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f server

# Check status
docker-compose ps
```

### 3. Access

- **Web UI:** http://localhost:5000
- **Health Check:** http://localhost:5000/health

---

## Configuration

### Environment Variables (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `AUTH_TOKEN` | (required) | Authentication token for clients |
| `SERVER_PORT` | 5000 | Web interface port |
| `NOTIFICATION_BACKEND` | disabled | Notification backend (disabled in Docker) |
| `FACE_RECOGNITION_ENABLED` | true | Enable face recognition |
| `ADMINER_PORT` | 8080 | Database admin port (--profile admin) |

### Persistent Data

Docker volumes store:
- `motion-detector-db` - SQLite database
- `motion-detector-faces` - Face samples
- `motion-detector-images` - Captured images
- `motion-detector-models` - Face recognition models
- `motion-detector-logs` - Application logs

**Backup:**
```bash
docker run --rm -v motion-detector-db:/data -v $(pwd):/backup \
    busybox tar czf /backup/motion-detector-backup-$(date +%Y%m%d).tar.gz /data
```

**Restore:**
```bash
docker run --rm -v motion-detector-db:/data -v $(pwd):/backup \
    busybox tar xzf /backup/motion-detector-backup-YYYYMMDD.tar.gz -C /
```

---

## Advanced Usage

### Database Admin Interface

Start with Adminer for database inspection:

```bash
docker-compose --profile admin up -d
```

Access: http://localhost:8080

- System: SQLite 3
- Database: `/app/faces.db` (in server container)

### Custom Configuration

Override default config.yaml:

```bash
# Create custom config
cp Server/config.yaml docker/config.custom.yaml

# Edit docker-compose.yml:
# volumes:
#   - ./docker/config.custom.yaml:/app/config.yaml:ro
```

### View Logs

```bash
# All logs
docker-compose logs -f

# Server only
docker-compose logs -f server

# Last 100 lines
docker-compose logs --tail=100 server
```

### Restart Server

```bash
docker-compose restart server
```

### Update

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

---

## ESP32/Client Configuration

Configure ESP32 or Raspberry Pi client to connect to Docker server:

### ESP32 secrets.h

```cpp
#define SERVER_HOST "192.168.1.100"  // Your Docker host IP
#define SERVER_PORT 5000
#define AUTH_TOKEN "YOUR_TOKEN_FROM_ENV"  // Match .env
```

### Raspberry Pi config.yaml

```yaml
server:
  url: 'http://192.168.1.100:5000'  # Docker host IP
  auth_token: 'YOUR_TOKEN_FROM_ENV'  # Match .env
```

**Find Docker host IP:**
```bash
# Linux
hostname -I

# Windows (WSL2)
ip route show | grep -i default | awk '{ print $3}'

# macOS
ipconfig getifaddr en0
```

---

## Limitations

### Notifications

**Desktop notifications don't work in Docker containers.**

- Windows Toast: ❌ Not available
- Linux notify-send: ❌ Requires X11/Wayland access

**Workaround:** Access events via Web UI (`/events`, `/latest`)

### GPIO Access

**Raspberry Pi GPIO not available in Docker.**

**Solution:** Run Raspberry Pi Client natively (not in Docker):
```bash
cd Raspberry-Pi/Client
./setup.sh
```

Only run **Server** in Docker, **Client** natively.

---

## Troubleshooting

### Port Already in Use

```bash
# Check what's using port 5000
sudo lsof -i :5000

# Change port in .env
SERVER_PORT=5001
docker-compose up -d
```

### Models Not Downloading

```bash
# Download manually
docker-compose exec server python models/download_models.py

# Or download on host and mount
cd Server
python models/download_models.py
# Models in Server/models/ will be used by container
```

### Database Locked

```bash
# Only one server instance should run
docker-compose ps

# Stop all
docker-compose down

# Restart
docker-compose up -d
```

### Face Recognition Not Working

```bash
# Check models exist
docker-compose exec server ls -la models/*.onnx

# Check face_recognition.enabled in config
docker-compose exec server cat config.yaml | grep enabled
```

---

## Production Deployment

### Security

1. **Change AUTH_TOKEN** - Use strong random token
2. **Firewall** - Only allow port 5000 from trusted IPs
3. **HTTPS** - Use reverse proxy (nginx, Caddy, Traefik)

### Reverse Proxy Example (Nginx)

```nginx
server {
    listen 80;
    server_name motion.example.com;

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service (Auto-Start)

Create `/etc/systemd/system/motion-detector-docker.service`:

```ini
[Unit]
Description=Motion Detector Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/motion-detector
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Enable:
```bash
sudo systemctl enable motion-detector-docker
sudo systemctl start motion-detector-docker
```

---

## Reference

- **Docker Compose Docs:** https://docs.docker.com/compose/
- **Main Documentation:** [../README.md](../README.md)
- **Server Configuration:** [../Server/README.md](../Server/README.md)

---

**Last Updated:** 2025-12-22
