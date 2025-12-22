# Raspberry Pi Setup-Guide

Vollständige Anleitung für Raspberry Pi - als **Client**, **Server** oder **Standalone** (All-in-One).

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Client-Modus](#client-modus) - Pi als Kamera → Remote-Server
3. [Server-Modus](#server-modus) - Pi als Server für ESP32/andere Clients
4. [Standalone-Modus](#standalone-modus) - Pi als Kamera + Server
5. [Hardware-Setup](#hardware-setup)
6. [Performance](#performance)
7. [Troubleshooting](#troubleshooting)

---

## Übersicht

### Was kann der Raspberry Pi?

| Modus | Beschreibung | Hardware | Use Case |
|-------|--------------|----------|----------|
| **Client** | Pi mit Kamera + PIR → sendet an Remote-Server | Pi Zero 2 W / 3 / 4 / 5 + CSI/USB Kamera + PIR | Verteilte Kameras, existierender Server |
| **Server** | Pi als Server für ESP32-CAMs oder andere Clients | Pi 4 / 5 (2GB+ empfohlen) | Günstiger 24/7-Server |
| **Standalone** | Pi mit Kamera + Server in einem Gerät | Pi 4 / 5 (2GB+ empfohlen) + Kamera + PIR | Portable Lösung, keine separate Hardware |

---

## Client-Modus

Raspberry Pi erfasst Bewegungen und sendet Fotos an einen Remote-Server (Windows/Linux).

### Voraussetzungen

- Raspberry Pi Zero 2 W / 3 / 4 / 5
- CSI-Kamera (empfohlen) oder USB-Webcam
- PIR-Sensor (HC-SR501)
- Remote-Server muss bereits laufen

### Quick Start

```bash
# 1. Repository klonen
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server/Raspberry-Pi/Client

# 2. Automatische Installation
chmod +x setup.sh
./setup.sh

# Script fragt nach:
#   - Server-IP
#   - Auth-Token (vom Server)
#   - Device-ID
```

### Hardware-Verkabelung

```
PIR HC-SR501:
  VCC → Pi Pin 2 (5V)
  GND → Pi Pin 6 (GND)
  OUT → Pi Pin 11 (GPIO 17, BCM-Nummerierung)

CSI-Kamera:
  - Ribbon-Kabel in CSI-Port (blaue Seite zu USB-Ports)
  - raspi-config: Interface Options → Camera → Enable
```

### Manuelle Installation

```bash
# System-Pakete
sudo apt update
sudo apt install python3 python3-pip python3-picamera2 python3-lgpio

# Python-Dependencies
pip3 install -r requirements.txt

# Konfiguration
cp config.yaml.example config.yaml
nano config.yaml
```

**config.yaml anpassen:**
```yaml
server:
  url: 'http://192.168.1.100:5000'  # Server-IP
  auth_token: 'TOKEN_VOM_SERVER'
  device_id: 'RaspberryPi-CAM-01'

pir:
  gpio_pin: 17  # BCM-Nummerierung
```

### Als systemd-Service

```bash
# Service installieren
sudo cp motion-detector-client.service /etc/systemd/system/
sudo systemctl enable motion-detector-client
sudo systemctl start motion-detector-client

# Status prüfen
sudo systemctl status motion-detector-client

# Logs
sudo journalctl -u motion-detector-client -f
```

### Detaillierte Anleitung

Siehe: [Client/README.md](Client/README.md)

---

## Server-Modus

Raspberry Pi 4/5 als Server für ESP32-CAMs oder andere Clients.

### Voraussetzungen

- Raspberry Pi 4 oder 5 (2GB+ RAM empfohlen)
- Kein PIR/Kamera am Server-Pi nötig
- ESP32-CAM(s) oder andere Clients im Netzwerk

### Quick Start

```bash
# Gleiche Installation wie Linux-Server
cd Server
chmod +x setup.sh
./setup.sh
```

### Konfiguration

```yaml
notifications:
  backend: 'disabled'  # Pi hat meist kein GUI
  # Oder 'linux_notify' falls Desktop-Umgebung vorhanden

face_recognition:
  enabled: true
  # Performance-Tuning für Pi:
  auto_learning:
    max_samples_per_person: 10  # Statt 15
```

### Performance-Tipps

**Für Raspberry Pi 3:**
```yaml
face_recognition:
  enabled: false  # Oder nur mit wenigen Samples
camera:
  resolution: [640, 480]  # Niedrigere Auflösung
```

**Für Raspberry Pi 4/5:**
- Face Recognition: ~500ms (akzeptabel)
- Max 3-4 ESP32-CAM Clients gleichzeitig empfohlen

### Detaillierte Anleitung

Siehe: [../Linux/Linux.md](../Linux/Linux.md) (gilt auch für Pi)

---

## Standalone-Modus

Ein Raspberry Pi betreibt **beides**: Kamera + Server.

### Voraussetzungen

- **Raspberry Pi 4 (2GB+) oder Pi 5** empfohlen
- Pi 3 funktioniert, aber langsamer
- CSI-Kamera + PIR-Sensor
- 16GB+ SD-Karte

### Use Case

- Portable Motion-Detection-Lösung
- Kein separater Server verfügbar
- All-in-One Sicherheitskamera

### Quick Start

```bash
cd Raspberry-Pi/Standalone
chmod +x setup.sh
./setup.sh

# Script installiert automatisch:
#   - Server (lokal auf Pi)
#   - Client (verbindet zu localhost:5000)
#   - Beide als systemd-Services
```

### Was passiert?

1. **Server** läuft auf `http://localhost:5000`
2. **Client** verbindet zu `http://localhost:5000`
3. PIR-Trigger → Client sendet Foto an lokalen Server
4. Server: Face Recognition + Web-UI
5. Web-UI erreichbar von anderen Geräten: `http://raspberrypi.local:5000`

### Manuelle Installation

#### 1. Server installieren

```bash
cd Server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-linux.txt
python models/download_models.py

# Config
cp config.yaml.example config.yaml
nano config.yaml
# notifications.backend: 'disabled' (headless) oder 'linux_notify' (Desktop)
```

#### 2. Client installieren

```bash
cd ../Raspberry-Pi/Client
pip3 install -r requirements.txt

# Config
cp config.yaml.example config.yaml
nano config.yaml
# server.url: 'http://localhost:5000'
# server.auth_token: 'MATCH_SERVER_TOKEN'
```

#### 3. Services einrichten

```bash
# Server-Service
sudo cp Server/motion-detector-server.service /etc/systemd/system/
sudo nano /etc/systemd/system/motion-detector-server.service
# WorkingDirectory anpassen!

# Client-Service
sudo cp Raspberry-Pi/Client/motion-detector-client.service /etc/systemd/system/
sudo nano /etc/systemd/system/motion-detector-client.service
# WorkingDirectory anpassen!

# Aktivieren
sudo systemctl daemon-reload
sudo systemctl enable motion-detector-server motion-detector-client
sudo systemctl start motion-detector-server
sleep 5  # Server hochfahren lassen
sudo systemctl start motion-detector-client
```

### Performance

| Pi-Modell | Face Recognition | Streaming FPS | Empfehlung |
|-----------|------------------|---------------|------------|
| Pi 5 | ~400ms | 8-10 fps | ✅ Ausgezeichnet |
| Pi 4 | ~500ms | 5-8 fps | ✅ Gut |
| Pi 3 | ~2s | 2-3 fps | ⚠️ Nutzbar |

### Speicherverbrauch

- Server + Face Recognition: ~300-500 MB RAM
- Client: ~50-100 MB RAM
- **Gesamt:** ~400-600 MB (OK für 2GB+ Pi)

**Pi mit 1GB RAM:**
```yaml
face_recognition:
  enabled: false
```

### Detaillierte Anleitung

Siehe: [Standalone/README.md](Standalone/README.md)

---

## Hardware-Setup

### CSI-Kamera

**Unterstützte Module:**
- Camera Module v2 (8MP, ~25€)
- Camera Module v3 (12MP, ~30€, bessere Low-Light-Performance)
- HQ Camera (12MP, ~50€, Wechselobjektiv)

**Installation:**
1. CSI-Connector finden (zwischen HDMI und USB auf Pi 4)
2. Plastik-Clip vorsichtig hochziehen
3. Ribbon-Kabel einführen (blaue Seite zu USB-Ports)
4. Clip runterdrücken
5. Kamera aktivieren: `sudo raspi-config` → Interface → Camera → Enable
6. Reboot: `sudo reboot`
7. Test: `libcamera-hello --list-cameras` oder `rpicam-hello --list-cameras`

### USB-Webcam (Alternative)

```bash
# Prüfen
ls /dev/video*  # Sollte /dev/video0 zeigen

# In config.yaml
camera:
  device_index: 0
```

### PIR-Sensor HC-SR501

**Potentiometer:**
- **Sx (Sensitivity):** Reichweite 3-7m
- **Tx (Time Delay):** Irrelevant (Software-Cooldown)

**Jumper:** Auf "H" (Repeatable Trigger)

**GPIO-Pinout (BCM-Nummerierung):**
```
Pin-Layout (Raspberry Pi):
  3V3   (1)  (2)  5V  ← PIR VCC
  GPIO2 (3)  (4)  5V
  GPIO3 (5)  (6)  GND ← PIR GND
  ...
  GPIO17(11) (12) GPIO18  ← PIR OUT (Standard)
```

---

## Performance

### Kamera-Upload-Geschwindigkeit

| Pi-Modell | Capture | Upload | Gesamt |
|-----------|---------|--------|--------|
| Pi 5 | 50ms | 100-150ms | ~200ms |
| Pi 4 | 50ms | 200-250ms | ~300ms |
| Pi 3 | 100ms | 300-400ms | ~500ms |
| Pi Zero 2 W | 100ms | 600-800ms | ~800ms |

### Empfohlene Auflösungen

- **Pi 5:** 1920×1080 oder 1280×720
- **Pi 4:** 1280×720
- **Pi 3:** 640×480
- **Pi Zero 2 W:** 640×480

---

## Troubleshooting

### Kamera nicht erkannt

```bash
# CSI-Kamera aktivieren
sudo raspi-config
# Interface Options → Camera → Enable
sudo reboot

# Prüfen
libcamera-hello --list-cameras
# Oder auf älteren Systemen:
vcgencmd get_camera
```

### PIR triggert nicht

```python
# Test-Script
from gpiozero import MotionSensor
pir = MotionSensor(17)

print("Warte auf Bewegung...")
pir.wait_for_motion()
print("Bewegung erkannt!")
```

**Häufige Probleme:**
- VCC an 3.3V statt 5V (einige PIRs brauchen 5V!)
- GPIO-Pin falsch in config.yaml
- PIR-Kalibrierung (warte 30-60s nach Einschalten)

### Permission Denied (GPIO/Kamera)

```bash
# User zu Gruppen hinzufügen
sudo usermod -a -G gpio,video $USER

# Logout und Login
# Oder:
su - $USER
```

### Server-Verbindung fehlgeschlagen (Client-Modus)

```bash
# Server-Erreichbarkeit testen
curl http://SERVER_IP:5000/health

# Sollte zurückgeben: {"status": "healthy"}
```

**Checkliste:**
- [ ] Server läuft
- [ ] Firewall auf Server erlaubt Port 5000
- [ ] Auth-Token stimmt überein
- [ ] Gleicher Router/Netzwerk

### Out of Memory (Pi 3)

```yaml
# Face Recognition deaktivieren
face_recognition:
  enabled: false

# Oder Samples reduzieren
auto_learning:
  max_samples_per_person: 5

# Niedrigere Auflösung
camera:
  resolution: [640, 480]
```

---

## Weiterführende Dokumentation

- **Client-Modus:** [Client/README.md](Client/README.md)
- **Server-Modus:** [../Linux/Linux.md](../Linux/Linux.md)
- **Standalone-Modus:** [Standalone/README.md](Standalone/README.md)
- **Face Recognition:** [../docs/FACE_RECOGNITION.md](../docs/FACE_RECOGNITION.md)
- **Hauptdokumentation:** [../README.md](../README.md)

---

## Quick Reference

### Client-Modus
```bash
cd Raspberry-Pi/Client
./setup.sh
sudo systemctl start motion-detector-client
```

### Server-Modus
```bash
cd Server
./setup.sh
sudo systemctl start motion-detector-server
```

### Standalone-Modus
```bash
cd Raspberry-Pi/Standalone
./setup.sh
# Startet beide Services automatisch
```

### Kamera testen
```bash
libcamera-hello
libcamera-jpeg -o test.jpg
```

### PIR testen
```python
from gpiozero import MotionSensor
pir = MotionSensor(17)
pir.wait_for_motion()
print("Motion!")
```

---

**Letzte Aktualisierung:** 2025-12-22
**Unterstützte Modelle:** Pi Zero 2 W, Pi 3, Pi 4, Pi 5
