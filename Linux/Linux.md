# Linux Installation & Setup

Vollständige Anleitung für die Installation des Motion Detector Servers auf Linux (Ubuntu/Debian/Fedora).

---

## Inhaltsverzeichnis

1. [Quick Start](#quick-start)
2. [Manuelle Installation](#manuelle-installation)
3. [Als systemd-Service einrichten](#als-systemd-service-einrichten)
4. [Desktop-Benachrichtigungen](#desktop-benachrichtigungen)
5. [Headless-Server](#headless-server)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Automatische Installation

```bash
cd ESP32-Motion-Detector-Windows-Server/Server
chmod +x setup.sh
./setup.sh
```

**Das Script:**
- ✅ Prüft Python-Version (3.8+)
- ✅ Installiert System-Dependencies
- ✅ Erstellt Virtual Environment
- ✅ Installiert Python-Pakete
- ✅ Lädt Face Recognition Models
- ✅ Erstellt config.yaml mit Auth-Token
- ✅ Bietet Service-Installation an

---

## Manuelle Installation

### 1. System-Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install libnotify-bin  # Für Desktop-Benachrichtigungen
```

**Fedora:**
```bash
sudo dnf install python3 python3-pip
sudo dnf install libnotify  # Für Desktop-Benachrichtigungen
```

### 2. Virtual Environment

```bash
cd Server
python3 -m venv venv
source venv/bin/activate
```

### 3. Python-Dependencies

```bash
pip install -r requirements.txt
pip install -r requirements-linux.txt
```

### 4. Face Recognition Models

```bash
python models/download_models.py

# Verifizieren
ls models/*.onnx
```

### 5. Konfiguration

```bash
cp config.yaml.example config.yaml  # Falls vorhanden
nano config.yaml
```

```yaml
security:
  auth_token: 'IHR_TOKEN'  # Generieren mit: python -c "import secrets; print(secrets.token_urlsafe(32))"

notifications:
  enabled: true
  backend: 'linux_notify'  # Für Desktop, 'disabled' für headless
  sound: true

face_recognition:
  enabled: true
```

### 6. Server starten

```bash
source venv/bin/activate
python app.py
```

Server läuft auf: `http://0.0.0.0:5000`

---

## Als systemd-Service einrichten

### 1. Service-File erstellen

```bash
sudo cp Linux/Server/motion-detector-server.service /etc/systemd/system/
```

### 2. Service-File anpassen

```bash
sudo nano /etc/systemd/system/motion-detector-server.service
```

**Wichtige Anpassungen:**
- `User=` und `Group=` auf Ihren Benutzer setzen
- `WorkingDirectory=` auf Ihr Server-Verzeichnis setzen
- `ExecStart=` Pfad zum Python und app.py anpassen

Beispiel:
```ini
[Service]
User=ihrbenutzername
Group=ihrbenutzername
WorkingDirectory=/home/ihrbenutzername/motion-detector/Server
ExecStart=/home/ihrbenutzername/motion-detector/Server/venv/bin/python app.py
```

### 3. Service aktivieren und starten

```bash
sudo systemctl daemon-reload
sudo systemctl enable motion-detector-server
sudo systemctl start motion-detector-server
```

### 4. Status prüfen

```bash
sudo systemctl status motion-detector-server
```

### 5. Logs ansehen

```bash
# Live-Logs
sudo journalctl -u motion-detector-server -f

# Letzte 100 Zeilen
sudo journalctl -u motion-detector-server -n 100
```

---

## Desktop-Benachrichtigungen

### Ubuntu/Debian

```bash
# libnotify installieren
sudo apt install libnotify-bin

# Testen
notify-send "Test" "Motion detected"
```

### Konfiguration

```yaml
notifications:
  enabled: true
  backend: 'linux_notify'
  sound: true
```

### Troubleshooting

**Problem:** Keine Benachrichtigungen

**Prüfen:**
```bash
# DISPLAY-Variable gesetzt?
echo $DISPLAY  # Sollte :0 oder ähnlich zeigen

# notify-send vorhanden?
which notify-send

# Testen
notify-send "Test" "Message"
```

**Lösung für SSH/headless:**
```bash
export DISPLAY=:0
```

Oder in config.yaml:
```yaml
notifications:
  backend: 'disabled'
```

---

## Headless-Server

Für Server ohne GUI:

### Konfiguration

```yaml
notifications:
  enabled: false
  backend: 'disabled'
```

### Web-UI nutzen

Events sind trotzdem verfügbar unter:
- `http://server-ip:5000/events`
- `http://server-ip:5000/latest`
- `http://server-ip:5000/`

---

## Troubleshooting

### Python-Version zu alt

**Problem:** Python < 3.8

**Lösung (Ubuntu/Debian):**
```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv
python3.10 -m venv venv
```

### Port 5000 bereits belegt

```bash
# Prozess finden
sudo lsof -i :5000

# Prozess beenden
sudo kill -9 PID

# Oder Port in config.yaml ändern
```

### Firewall blockiert

**UFW:**
```bash
sudo ufw allow 5000/tcp
sudo ufw enable
```

**firewalld:**
```bash
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

### Face Recognition langsam

Auf älteren Systemen/Raspberry Pi:

```yaml
face_recognition:
  auto_learning:
    max_samples_per_person: 10  # Statt 15

  threshold_strict: 0.40  # Höher = schneller
```

---

## Weiterführende Dokumentation

- **Server-API:** [../Server/README.md](../Server/README.md)
- **Face Recognition:** [../docs/FACE_RECOGNITION.md](../docs/FACE_RECOGNITION.md)
- **Hauptdokumentation:** [../README.md](../README.md)

---

## Quick Reference

### Server starten
```bash
cd Server
source venv/bin/activate
python app.py
```

### systemd-Service
```bash
sudo systemctl start motion-detector-server
sudo systemctl status motion-detector-server
sudo journalctl -u motion-detector-server -f
```

### Server-IP herausfinden
```bash
hostname -I
ip addr show
```

### Firewall konfigurieren
```bash
sudo ufw allow 5000/tcp
```

---

**Letzte Aktualisierung:** 2025-12-22
**Platform:** Linux (Ubuntu/Debian/Fedora)
