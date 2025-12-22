# Windows Installation & Setup

Vollständige Anleitung für die Installation und Konfiguration des Motion Detector Servers auf Windows 10/11.

---

## Inhaltsverzeichnis

1. [Überblick](#überblick)
2. [Server Installation](#server-installation)
3. [ESP32-CAM Setup](#esp32-cam-setup)
4. [Toast Notifications](#toast-notifications)
5. [Firewall-Konfiguration](#firewall-konfiguration)
6. [Troubleshooting](#troubleshooting)
7. [Als Windows-Service einrichten](#als-windows-service-einrichten)

---

## Überblick

### Was wird installiert?

- **Python Server** (Flask-basiert)
- **Face Recognition** (YuNet + SFace)
- **Windows Toast Notifications**
- **Web-Interface** auf Port 5000

### Voraussetzungen

- Windows 10 Version 1903+ oder Windows 11
- Python 3.8 oder höher
- ca. 500 MB Festplattenspeicher
- Netzwerkverbindung (LAN/WLAN)

---

## Server Installation

### 1. Python installieren

1. Download von [python.org](https://www.python.org/downloads/)
2. **Wichtig:** Während der Installation **"Add Python to PATH"** aktivieren!
3. Installation durchführen
4. Verifizieren:
   ```cmd
   python --version
   ```

### 2. Automatische Installation (Empfohlen)

```cmd
cd ESP32-Motion-Detector-Windows-Server\Server
setup.bat
```

**Das Script führt automatisch aus:**
- ✅ Python-Version prüfen
- ✅ Virtual Environment erstellen
- ✅ Dependencies installieren (Flask, OpenCV, etc.)
- ✅ Face Recognition Models downloaden
- ✅ Konfigurationsdatei mit Auth-Token erstellen
- ✅ Server-Test anbieten

### 3. Manuelle Installation

Falls setup.bat nicht funktioniert:

```cmd
cd Server

REM Virtual Environment erstellen
python -m venv venv
venv\Scripts\activate.bat

REM Dependencies installieren
pip install -r requirements.txt
pip install -r requirements-windows.txt

REM Face Recognition Models downloaden
python models\download_models.py

REM Auth Token generieren
python -c "import secrets; print(secrets.token_urlsafe(32))"

REM config.yaml bearbeiten und Token eintragen
notepad config.yaml
```

### 4. Konfiguration

Bearbeite `Server/config.yaml`:

```yaml
security:
  auth_token: 'IHR_GENERIERTES_TOKEN'  # ⚠️ WICHTIG: Ändern!

notifications:
  enabled: true
  backend: 'windows_toast'  # Windows Toast Notifications
  sound: true

face_recognition:
  enabled: true  # Nach Model-Download auf true setzen
```

### 5. Server starten

```cmd
cd Server
venv\Scripts\activate.bat  # Falls Virtual Environment verwendet
python app.py
```

Server läuft auf: `http://localhost:5000`

---

## ESP32-CAM Setup

### 1. Firmware vorbereiten

```cmd
cd ..\ESP32\Client

REM Secrets-Datei erstellen
copy include\secrets.h.example include\secrets.h

REM Secrets bearbeiten
notepad include\secrets.h
```

### 2. Secrets konfigurieren

```cpp
#define WIFI_SSID "IhrWLAN"
#define WIFI_PASSWORD "IhrWLANPasswort"
#define SERVER_HOST "192.168.1.100"  # Ihre PC-IP (siehe ipconfig)
#define SERVER_PORT 5000
#define AUTH_TOKEN "IHR_GENERIERTES_TOKEN"  # Aus config.yaml
#define DEVICE_ID "ESP32-CAM-01"
```

**PC-IP herausfinden:**
```cmd
ipconfig
```
Suchen Sie nach "IPv4-Adresse" (z.B. 192.168.1.100)

### 3. Firmware hochladen

**Mit PlatformIO:**
```cmd
cd ESP32\Client
pio run --target upload
```

**Mit Arduino IDE:**
- Siehe [ESP32/Client/README.md](../ESP32/Client/README.md)

### 4. Hardware-Verkabelung

```
PIR HC-SR501:
  VCC → ESP32-CAM 5V
  GND → ESP32-CAM GND
  OUT → ESP32-CAM GPIO 13

Stromversorgung:
  5V 2A Netzteil → ESP32-CAM VCC/GND
```

**⚠️ Wichtig:** Ausreichende Stromversorgung (2A) verwenden!

---

## Toast Notifications

### Einrichten

Windows Toast Notifications werden automatisch von `setup.bat` konfiguriert.

### Troubleshooting

**Problem:** Notifications erscheinen nicht

**Lösung 1: Focus Assist prüfen**
1. Einstellungen → System → Fokushilfe
2. Auf "Aus" stellen

**Lösung 2: Benachrichtigungen für Python aktivieren**
1. Einstellungen → System → Benachrichtigungen
2. "Python" in der Liste finden
3. Benachrichtigungen aktivieren

**Lösung 3: Als Administrator ausführen**
```cmd
REM Rechtsklick auf Eingabeaufforderung → "Als Administrator ausführen"
cd Server
python app.py
```

**Lösung 4: Deaktivieren**
Falls Probleme bestehen, in `config.yaml`:
```yaml
notifications:
  enabled: false
```

---

## Firewall-Konfiguration

### Automatisch (PowerShell als Administrator)

```powershell
New-NetFirewallRule -DisplayName "Motion Detector Server" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

### Manuell (GUI)

1. Windows-Sicherheit → Firewall & Netzwerkschutz
2. "Erweiterte Einstellungen"
3. "Eingehende Regeln" → "Neue Regel..."
4. Regeltyp: **Port**
5. Protokoll: **TCP**, Port: **5000**
6. Aktion: **Verbindung zulassen**
7. Profile: **Privat** aktivieren
8. Name: "Motion Detector Server"

### Verbindung testen

Von einem anderen Gerät im Netzwerk:
```bash
curl http://IHRE_PC_IP:5000/health
```

---

## Troubleshooting

### Python nicht gefunden

**Fehler:** `'python' is not recognized as an internal or external command`

**Lösung:**
1. Python neu installieren
2. **"Add Python to PATH"** aktivieren
3. CMD neu starten

### Port 5000 bereits belegt

**Fehler:** `Address already in use`

**Lösung:**
```cmd
REM Port-Nutzung prüfen
netstat -ano | findstr :5000

REM Prozess beenden (PID durch die gefundene Nummer ersetzen)
taskkill /PID 1234 /F

REM Oder Port in config.yaml ändern
```

### Face Recognition Models fehlen

**Fehler:** `YuNet model not found`

**Lösung:**
```cmd
cd Server
python models\download_models.py

REM Verifizieren
dir models\*.onnx
```

### ESP32 kann Server nicht erreichen

**Checkliste:**
- [ ] Server läuft (`python app.py`)
- [ ] Firewall-Regel aktiv
- [ ] PC-IP korrekt in `secrets.h`
- [ ] Auth-Token stimmt überein
- [ ] Gleicher WLAN-Router
- [ ] Ping testen: `ping IHRE_PC_IP`

---

## Als Windows-Service einrichten

Für Autostart beim Systemstart mit **NSSM** (Non-Sucking Service Manager):

### 1. NSSM installieren

Download: https://nssm.cc/download

### 2. Service installieren

```cmd
REM NSSM entpacken und als Administrator ausführen

nssm install MotionDetectorServer "C:\Python310\python.exe" "C:\Pfad\zu\Server\app.py"
nssm set MotionDetectorServer AppDirectory "C:\Pfad\zu\Server"
nssm set MotionDetectorServer DisplayName "Motion Detector Server"
nssm set MotionDetectorServer Description "ESP32 Motion Detector Server with Face Recognition"
```

### 3. Service starten

```cmd
nssm start MotionDetectorServer

REM Status prüfen
nssm status MotionDetectorServer
```

### 4. Service verwalten

```cmd
REM Stoppen
nssm stop MotionDetectorServer

REM Neu starten
nssm restart MotionDetectorServer

REM Deinstallieren
nssm remove MotionDetectorServer confirm
```

---

## Weiterführende Dokumentation

- **Server-API:** [../Server/README.md](../Server/README.md)
- **ESP32 Firmware:** [../ESP32/Client/README.md](../ESP32/Client/README.md)
- **Face Recognition:** [../docs/FACE_RECOGNITION.md](../docs/FACE_RECOGNITION.md)
- **Hauptdokumentation:** [../README.md](../README.md)

---

## Quick Reference

### Server starten
```cmd
cd Server
venv\Scripts\activate.bat
python app.py
```

### PC-IP herausfinden
```cmd
ipconfig
```

### Auth-Token generieren
```cmd
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Firewall-Regel hinzufügen (PowerShell)
```powershell
New-NetFirewallRule -DisplayName "Motion Detector" -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```

---

**Letzte Aktualisierung:** 2025-12-22
**Platform:** Windows 10/11
