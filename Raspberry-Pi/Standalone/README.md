# Raspberry Pi Standalone Mode

All-in-One Motion Detection System: Ein Raspberry Pi als **Kamera + Server**.

---

## Übersicht

Im Standalone-Modus läuft alles auf einem einzigen Raspberry Pi:
- ✅ PIR Motion Detection
- ✅ Kamera (CSI oder USB)
- ✅ Flask Server mit Face Recognition
- ✅ Web-Interface
- ✅ SQLite-Datenbank

**Kein separater Server oder PC erforderlich!**

---

## Hardware-Anforderungen

### Empfohlen
- **Raspberry Pi 4 (2GB+)** oder **Raspberry Pi 5**
- CSI Camera Module v2/v3
- PIR-Sensor HC-SR501
- 16GB+ microSD-Karte
- 5V 3A Netzteil

### Auch möglich
- **Raspberry Pi 3** (funktioniert, aber Face Recognition ~2s statt ~500ms)
- USB-Webcam (statt CSI-Kamera)
- Pi Zero 2 W (sehr langsam, nicht empfohlen)

---

## Quick Start

### 1. Einzeilen-Installation

```bash
cd Raspberry-Pi/Standalone
chmod +x setup.sh
./setup.sh
```

**Das Script installiert automatisch:**
1. ✅ System-Dependencies (Python, picamera2, GPIO)
2. ✅ Server (Flask + Face Recognition)
3. ✅ Client (PIR + Kamera)
4. ✅ Face Recognition Models (~5MB Download)
5. ✅ Systemd-Services für Autostart
6. ✅ Konfiguration mit Auth-Token

### 2. Hardware verkabeln

```
PIR HC-SR501:
  VCC → Pi Pin 2 (5V)
  GND → Pi Pin 6 (GND)
  OUT → Pi Pin 11 (GPIO 17, BCM-Nummerierung)

CSI-Kamera:
  - Ribbon-Kabel in CSI-Connector
  - Blaue Seite zu USB-Ports
  - sudo raspi-config → Interface → Camera → Enable
```

### 3. Zugriff

**Vom Raspberry Pi selbst:**
```
http://localhost:5000
```

**Von anderem Gerät im Netzwerk:**
```
http://raspberrypi.local:5000
# Oder direkt mit IP:
http://192.168.1.XXX:5000
```

**Pi-IP herausfinden:**
```bash
hostname -I
```

---

## Was installiert setup.sh?

### Server (auf localhost:5000)

**Installiert nach:** `../../Server/`

- Flask Web-Server
- Face Recognition (YuNet + SFace)
- SQLite-Datenbank
- Event-Management
- Automatic Face Learning

**Konfiguration:** `../../Server/config.yaml`

### Client (verbindet zu localhost:5000)

**Installiert nach:** `../Client/`

- PIR Motion Detection via GPIO 17
- picamera2 für CSI-Kamera
- Upload zu lokalem Server
- Cooldown-Management

**Konfiguration:** `../Client/config.yaml`

### Systemd-Services

Beide Komponenten laufen als systemd-Services:

- `motion-detector-server.service` - Server
- `motion-detector-client.service` - Client (startet nach Server)

**Autostart beim Booten aktiviert!**

---

## Konfiguration

### Server-Konfiguration

Bearbeite: `../../Server/config.yaml`

```yaml
face_recognition:
  enabled: true

  auto_learning:
    max_samples_per_person: 12  # Für Pi-Performance reduziert

notifications:
  backend: 'disabled'  # Headless-Pi hat kein GUI
```

**Performance-Tuning für Pi 3:**
```yaml
face_recognition:
  enabled: false  # Oder deutlich reduziert

  auto_learning:
    max_samples_per_person: 5
```

### Client-Konfiguration

Bearbeite: `../Client/config.yaml`

```yaml
server:
  url: 'http://localhost:5000'  # NICHT ändern!
  auth_token: 'MATCH_SERVER_TOKEN'  # Muss mit Server übereinstimmen

pir:
  gpio_pin: 17  # Standard, ändern falls anderer Pin

camera:
  resolution: [1280, 720]  # Pi 4/5: OK, Pi 3: [640, 480]
  jpeg_quality: 85
```

---

## Service-Verwaltung

### Status prüfen

```bash
# Server-Status
sudo systemctl status motion-detector-server

# Client-Status
sudo systemctl status motion-detector-client
```

### Logs ansehen

```bash
# Server-Logs (live)
sudo journalctl -u motion-detector-server -f

# Client-Logs (live)
sudo journalctl -u motion-detector-client -f

# Letzte 50 Zeilen
sudo journalctl -u motion-detector-server -n 50
```

### Starten/Stoppen/Neustarten

```bash
# Beide Services neu starten
sudo systemctl restart motion-detector-server motion-detector-client

# Nur Server neu starten
sudo systemctl restart motion-detector-server

# Beide stoppen
sudo systemctl stop motion-detector-server motion-detector-client

# Autostart deaktivieren
sudo systemctl disable motion-detector-server motion-detector-client
```

---

## Performance

### Raspberry Pi 5

- **Face Recognition:** ~400ms pro Bild
- **Streaming:** 8-10 fps möglich
- **Status:** ✅ Ausgezeichnet für Standalone

### Raspberry Pi 4 (2GB+)

- **Face Recognition:** ~500ms pro Bild
- **Streaming:** 5-8 fps
- **Status:** ✅ Gut für Standalone

### Raspberry Pi 3

- **Face Recognition:** ~2000ms pro Bild (2 Sekunden!)
- **Streaming:** 2-3 fps
- **Status:** ⚠️ Nutzbar, aber langsam

**Empfehlung für Pi 3:**
- Face Recognition deaktivieren oder stark einschränken
- Niedrigere Kameraauflösung (640×480)
- Weniger Auto-Learning-Samples

### Speicherverbrauch

- Server + Face Recognition: ~300-500 MB RAM
- Client: ~50-100 MB RAM
- **Gesamt:** ~400-600 MB

**Pi mit 1GB RAM:** Face Recognition sollte deaktiviert werden.

---

## Troubleshooting

### Services starten nicht

```bash
# Detaillierte Logs
sudo journalctl -u motion-detector-server -xe
sudo journalctl -u motion-detector-client -xe

# Service-File prüfen
sudo systemctl cat motion-detector-server
```

**Häufige Probleme:**
- WorkingDirectory existiert nicht
- Python-venv fehlt
- Permissions-Fehler

### PIR triggert nicht

```python
# Test-Script
from gpiozero import MotionSensor
pir = MotionSensor(17)

print("Warte auf Bewegung...")
pir.wait_for_motion()
print("Bewegung erkannt!")
```

### Kamera funktioniert nicht

```bash
# Kamera aktivieren
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot

# Testen
libcamera-hello --list-cameras
```

### Web-Interface nicht erreichbar

**Vom Pi selbst:**
```bash
curl http://localhost:5000/health
# Sollte zurückgeben: {"status": "healthy"}
```

**Von anderem Gerät:**
```bash
# Pi-IP finden
hostname -I

# Testen
curl http://PI_IP:5000/health
```

**Firewall prüfen (falls aktiviert):**
```bash
sudo ufw allow 5000/tcp
```

### Out of Memory

**Pi 3 oder 1GB RAM:**

```yaml
# In Server/config.yaml
face_recognition:
  enabled: false

# Oder reduzieren
auto_learning:
  max_samples_per_person: 3
```

---

## Manuelle Installation

Falls `setup.sh` nicht funktioniert:

### 1. Server installieren

```bash
cd ../../Server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt requirements-linux.txt
python models/download_models.py

# config.yaml erstellen und Auth-Token setzen
nano config.yaml
```

### 2. Client installieren

```bash
cd ../Raspberry-Pi/Client
pip3 install -r requirements.txt

# config.yaml erstellen
cp config.yaml.example config.yaml
nano config.yaml
# server.url: 'http://localhost:5000'
# server.auth_token: MATCH_SERVER_TOKEN
```

### 3. Services manuell erstellen

Siehe Standalone-Service-Files oder verwende die Templates aus `setup.sh`.

---

## Weiterführende Dokumentation

- **Raspberry Pi Guide:** [../Raspberry.md](../Raspberry.md)
- **Server-Dokumentation:** [../../Server/README.md](../../Server/README.md)
- **Client-Dokumentation:** [../Client/README.md](../Client/README.md)
- **Face Recognition:** [../../docs/FACE_RECOGNITION.md](../../docs/FACE_RECOGNITION.md)
- **Hauptdokumentation:** [../../README.md](../../README.md)

---

## Quick Reference

### Installation
```bash
./setup.sh
```

### Service-Kontrolle
```bash
sudo systemctl status motion-detector-server
sudo systemctl restart motion-detector-client
sudo journalctl -u motion-detector-server -f
```

### Web-UI
```bash
# Lokal
http://localhost:5000

# Netzwerk
http://$(hostname -I | awk '{print $1}'):5000
```

### Kamera testen
```bash
libcamera-hello
```

### PIR testen
```python
from gpiozero import MotionSensor;
pir = MotionSensor(17);
pir.wait_for_motion();
print("Motion!")
```

---

**Letzte Aktualisierung:** 2025-12-22
**Empfohlene Hardware:** Raspberry Pi 4/5 (2GB+)
