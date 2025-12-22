# Changelog

Alle wesentlichen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

---

## [2.0.0] - 2025-12-22

### 🚨 **BREAKING CHANGES** - Repository Umstrukturierung

Das Repository wurde vollständig umstrukturiert für bessere Organisation und Klarheit. **Bestehende Klone müssen neu geklont oder manuell aktualisiert werden.**

### 🏗️ **Strukturelle Änderungen**

#### Neue Plattform-basierte Struktur

**Vorher:**
```
├── server/
├── esp32/
├── clients/raspi/
├── deploy/
└── docs/
```

**Nachher:**
```
├── Windows/
│   ├── Windows.md
│   └── Server/
├── Linux/
│   ├── Linux.md
│   └── Server/
├── Raspberry-Pi/
│   ├── Raspberry.md
│   ├── Client/
│   ├── Server/
│   └── Standalone/
├── ESP32/
│   ├── ESP32.md
│   └── Client/
├── Server/ (zentral)
└── docs/
```

### ✨ **Neue Features**

#### Plattform-Hauptdokumentationen
- **NEU:** `Windows/Windows.md` - Komplette Windows-Anleitung (350+ Zeilen)
- **NEU:** `Linux/Linux.md` - Komplette Linux-Anleitung (300+ Zeilen)
- **NEU:** `ESP32/ESP32.md` - Komplette ESP32-Anleitung (350+ Zeilen)
- **NEU:** `Raspberry-Pi/Raspberry.md` - Komplette Raspberry-Pi-Anleitung (450+ Zeilen)

#### Raspberry Pi Standalone-Modus
- **NEU:** `Raspberry-Pi/Standalone/` - Vollständiger Standalone-Modus
- **NEU:** `Raspberry-Pi/Standalone/setup.sh` - Automatisierte Installation (350+ Zeilen)
- **NEU:** `Raspberry-Pi/Standalone/README.md` - Vollständige Anleitung (400+ Zeilen)
- Installiert Server + Client auf einem Raspberry Pi
- Ein-Kommando-Installation
- Systemd-Services automatisch konfiguriert

#### Dokumentations-Verbesserungen
- **NEU:** `AUDIT_REPORT.md` - Vollständiger Audit-Report mit 23 identifizierten Problemen
- **NEU:** `CHANGELOG.md` - Diese Datei
- Alle Dokumentationen auf neue Struktur aktualisiert
- Links in allen Markdown-Dateien korrigiert

### 📦 **Verschobene Dateien**

| Alt | Neu | Begründung |
|-----|-----|------------|
| `server/` | `Server/` | Zentraler Server-Code (shared) |
| `esp32/` | `ESP32/Client/` | Plattformspezifische Hierarchie |
| `clients/raspi/` | `Raspberry-Pi/Client/` | Plattformspezifische Hierarchie |
| `deploy/linux/systemd/motion-detector-server.service` | `Linux/Server/` | Bei Plattform |
| `deploy/raspi/client/motion-detector-client.service` | `Raspberry-Pi/Client/` | Bei Plattform |
| `docs/LINUX_SETUP.md` | `Linux/Linux.md` | Integriert in Plattform-Docs |
| `docs/RASPBERRY_PI.md` | `Raspberry-Pi/Raspberry.md` | Integriert in Plattform-Docs |

### 🗑️ **Entfernte Verzeichnisse**

- `clients/` (leer nach Verschiebung)
- `deploy/` (leer nach Verschiebung)

### 🐛 **Behobene Fehler**

#### Dokumentationsfehler (8 Fehler)
- **Fix:** README.md Projektstruktur auf aktuelle Struktur aktualisiert
- **Fix:** Broken Anchor-Links zu Raspberry Pi Modi korrigiert
- **Fix:** Fehlende Windows-Zentral-Dokumentation erstellt
- **Fix:** Fehlende Raspberry Pi Standalone-Dokumentation erstellt
- **Fix:** Veraltete Pfade in allen Dokumenten aktualisiert

#### Link-Fehler (4 Fehler)
- **Fix:** Alle ESP32-Pfad-Links von `esp32/` auf `ESP32/Client/` aktualisiert
- **Fix:** Alle Raspberry-Pi-Links von `clients/raspi/` auf `Raspberry-Pi/Client/` aktualisiert
- **Fix:** Server-Links von `server/` auf `Server/` aktualisiert
- **Fix:** Docs-Links aktualisiert

#### Strukturelle Probleme (5 Fehler)
- **Fix:** ESP32-Code in plattformspezifisches Verzeichnis verschoben
- **Fix:** Raspberry-Pi-Code in eigene Plattformstruktur verschoben
- **Fix:** Fehlende Standalone-Struktur für Raspberry Pi erstellt
- **Fix:** Systemd-Services in Plattformverzeichnisse verschoben

### 📝 **Aktualisierte Dokumentationen**

- `README.md` - Projektstruktur, alle Links, Deployment-Scenarios
- `QUICKSTART.md` - Pfade und Links aktualisiert
- `INSTALLATION.md` - Links aktualisiert (teilweise)
- Alle neuen Plattform-Dokumentationen erstellt

### ⚙️ **Migration für bestehende Benutzer**

#### Wenn Sie das Repository bereits geklont haben:

**Option 1: Neu klonen (Empfohlen)**
```bash
# Backup alter Clone (falls Konfigurationen vorhanden)
mv ESP32-Motion-Detector-Windows-Server ESP32-Motion-Detector-Windows-Server.old

# Neu klonen
git clone <repo-url>
cd ESP32-Motion-Detector-Windows-Server

# Konfigurationen kopieren
cp ../ESP32-Motion-Detector-Windows-Server.old/Server/config.yaml Server/
cp ../ESP32-Motion-Detector-Windows-Server.old/Server/faces.db Server/
```

**Option 2: Manuell aktualisieren**
```bash
cd ESP32-Motion-Detector-Windows-Server

# Stash lokale Änderungen
git stash

# Pull neueste Änderungen
git pull origin claude/audit-restructure-docs-oIYvI

# Konfigurationen an neue Pfade anpassen
# - server/config.yaml → Server/config.yaml
# - esp32/include/secrets.h → ESP32/Client/include/secrets.h
# - clients/raspi/config.yaml → Raspberry-Pi/Client/config.yaml
```

#### Systemd-Services aktualisieren

**Server (Linux):**
```bash
# Service-File aktualisieren
sudo cp Linux/Server/motion-detector-server.service /etc/systemd/system/

# WorkingDirectory in Service anpassen
sudo nano /etc/systemd/system/motion-detector-server.service
# Ändere: WorkingDirectory=/path/to/Server (statt /path/to/server)

sudo systemctl daemon-reload
sudo systemctl restart motion-detector-server
```

**Raspberry Pi Client:**
```bash
# Service-File aktualisieren
sudo cp Raspberry-Pi/Client/motion-detector-client.service /etc/systemd/system/

# WorkingDirectory prüfen
sudo nano /etc/systemd/system/motion-detector-client.service

sudo systemctl daemon-reload
sudo systemctl restart motion-detector-client
```

### ⚠️ **Bekannte Probleme**

1. **Externe Links:** GitHub-Links zu alten Pfaden funktionieren nicht mehr
2. **Systemd-Services:** Müssen manuell aktualisiert werden (siehe Migration)
3. **IDE-Konfigurationen:** PlatformIO/Arduino-Projekte müssen neu geöffnet werden

### 🎯 **Nächste Schritte**

Zukünftige Verbesserungen (nicht in diesem Release):
- [ ] Docker Compose Setup
- [ ] Migration-Script für automatisches Update
- [ ] GitHub-Redirects für alte Pfade
- [ ] Windows-Setup-Dokumentation weiter ausbauen

---

## [1.5.0] - 2024-12-22 (Vor Umstrukturierung)

### Letzte Version vor großer Umstrukturierung

- Automated installation scripts (`setup.sh`, `setup.bat`)
- Face Recognition mit YuNet + SFace
- Multi-Platform support (Windows, Linux, Raspberry Pi)
- ESP32-CAM und Raspberry Pi Camera support
- Web-UI mit Person-Management
- Auto-Learning für Face Recognition

---

## Versionsschema

Dieses Projekt folgt [Semantic Versioning](https://semver.org/):

- **MAJOR** (X.0.0): Breaking Changes (wie diese Umstrukturierung)
- **MINOR** (0.X.0): Neue Features (rückwärtskompatibel)
- **PATCH** (0.0.X): Bugfixes

---

**Für vollständige Änderungshistorie:** Siehe [Git Commits](https://github.com/N30Z/ESP32-Motion-Detector-Windows-Server/commits/)
