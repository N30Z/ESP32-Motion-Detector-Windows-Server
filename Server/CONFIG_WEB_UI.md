# Web-Konfigurationsoberfläche

## Übersicht

Die Web-Konfigurationsoberfläche ermöglicht es Ihnen, **alle** Server- und Client-Einstellungen direkt über den Webbrowser anzupassen, ohne manuell YAML-Dateien bearbeiten zu müssen.

## Zugriff

1. Server starten: `python app.py`
2. Browser öffnen: `http://localhost:5000/config`
3. Anmelden (falls aktiviert)

## Konfigurationsbereiche

### 🖥️ Server Einstellungen

- **Host**: Server-Adresse (Standard: `0.0.0.0` = alle Interfaces)
- **Port**: Server-Port (Standard: `5000`)
- **Debug-Modus**: Nur für Entwicklung aktivieren
- **Log Level**: DEBUG, INFO, WARNING, ERROR
- **Log-Datei**: Pfad zur Log-Datei

### 🔒 Sicherheit

- **Auth Token**: Authentifizierungs-Token (muss mit Client übereinstimmen!)
- **Stream-Authentifizierung**: Authentifizierung für Live-Stream erforderlich

### 💾 Speicher

- **Bild-Verzeichnis**: Pfad für gespeicherte Bilder
- **Max. Anzahl Bilder**: Maximale Anzahl gespeicherter Bilder
- **Max. Alter**: Automatische Löschung nach X Tagen

### 🔔 Benachrichtigungen

- **Benachrichtigungen aktivieren**: System-Benachrichtigungen ein/aus
- **Backend**:
  - `windows_toast`: Windows 10/11 Toast-Benachrichtigungen
  - `linux_notify`: Linux Desktop-Benachrichtigungen
  - `disabled`: Deaktiviert (für Headless-Server)
- **Ton abspielen**: Sound bei Benachrichtigungen

### 👤 Gesichtserkennung

#### Grundeinstellungen
- **Gesichtserkennung aktivieren**: Hauptschalter (erfordert ML-Modelle!)
- **Datenbank-Pfad**: Pfad zur SQLite-Datenbank
- **Gesichter-Verzeichnis**: Verzeichnis für Gesichts-Crops

#### Recognition Thresholds
- **Threshold Strict (GREEN)**: Distanz für zuverlässige Erkennung (niedriger = strenger)
- **Threshold Loose (YELLOW)**: Distanz für unsichere Erkennung
- **Margin Strict (GREEN)**: Mindest-Margin (d2-d1) für zuverlässige Erkennung
- **Margin Loose (YELLOW)**: Mindest-Margin für unsichere Erkennung

#### Qualitäts-Einstellungen
- **Minimale Gesichtsgröße**: Minimale Fläche in Pixeln für Auto-Learning (z.B. 10000 = 100x100px)
- **Minimale Qualität**: Minimaler Qualitäts-Score für Auto-Learning (0-1)

#### Auto-Learning
- **Auto-Learning aktivieren**: Automatisch neue Samples von GREEN matches lernen
- **Max Samples pro Person**: Maximale Anzahl gespeicherter Samples
- **Cooldown**: Wartezeit zwischen Auto-Learning-Events (Sekunden)
- **Nur GREEN Matches lernen**: Nur von sicheren Erkennungen lernen
- **Ersetzungs-Strategie**: `oldest` oder `lowest_quality`

#### Person Management
- **Automatisch neue Personen erstellen**: Bei UNKNOWN automatisch neue Person anlegen
- **Neuer Personen-Name Template**: Template für neue Personen (z.B. "Unbekannt #{count}")

### 📹 Stream

- **Ziel-FPS**: Ziel-Framerate für Live-Stream
- **JPEG-Qualität**: JPEG-Komprimierung (1-100, höher = besser)

### 📱 Client-Konfiguration (Template)

Diese Einstellungen dienen als Vorlage für neue Clients.

#### Server-Verbindung
- **Server URL**: URL des Servers (wird von Client verwendet)
- **Device ID Template**: Template für Client Device ID (z.B. `Client-{hostname}`)

#### PIR Sensor
- **GPIO Pin**: GPIO-Pin für PIR-Sensor (BCM-Nummerierung)

#### Motion Detection
- **Cooldown**: Wartezeit zwischen Motion-Events (Sekunden)

#### Kamera
- **Auflösung**: Breite und Höhe in Pixel
- **JPEG-Qualität**: JPEG-Komprimierung (1-100)
- **USB Device Index**: USB-Kamera Index (nur für OpenCV)

#### Streaming
- **Streaming aktivieren**: Kontinuierliches Frame-Streaming für Live-View
- **Streaming FPS**: Ziel-FPS für Streaming

#### Logging
- **Log Level**: DEBUG, INFO, WARNING, ERROR
- **Log-Datei**: Pfad zur Client Log-Datei

## API-Endpoint für Clients

Clients können ihre Konfiguration automatisch vom Server abrufen:

```bash
curl -H "X-Auth-Token: YOUR_TOKEN" http://localhost:5000/api/client/config
```

Dies gibt die Client-Konfiguration als JSON zurück, inklusive des aktuellen Auth-Tokens.

## Dateien

- **Server-Konfiguration**: `Server/config.yaml` (wird automatisch aktualisiert)
- **Client-Template**: `Server/client_config_template.yaml` (wird automatisch erstellt/aktualisiert)

## Wichtige Hinweise

⚠️ **Auth Token**: Der Auth Token wird automatisch zwischen Server- und Client-Konfiguration synchronisiert.

⚠️ **Server-Neustart**: Einige Änderungen (z.B. Port, Host) erfordern einen Server-Neustart.

⚠️ **Sicherheit**: Ändern Sie den Auth Token vor dem produktiven Einsatz!

## Erfolgreiche Speicherung

Nach dem Speichern erscheint eine grüne Erfolgsmeldung. Bei Fehlern wird eine rote Fehlermeldung angezeigt.
