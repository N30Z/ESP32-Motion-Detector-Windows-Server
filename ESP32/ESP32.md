# ESP32-CAM Client

Dokumentation für ESP32-CAM als Motion Detection Camera Client.

---

## Überblick

Der ESP32-CAM Client erfasst Bewegungen über einen PIR-Sensor und sendet Fotos an den Server (Windows/Linux).

### Features

- ✅ PIR Motion Detection über GPIO
- ✅ OV2640 Kamera (800×600 bis 1600×1200)
- ✅ MJPEG Live-Streaming (~10 fps)
- ✅ WiFi-Upload zum Server
- ✅ Konfigurierbarer Cooldown
- ✅ Niedriger Stromverbrauch (optional Deep Sleep)

### Hardware

- **ESP32-CAM Board** (AI-Thinker empfohlen)
- **PIR-Sensor** (HC-SR501 oder ähnlich)
- **Stromversorgung** 5V 2A (wichtig!)
- **FTDI-Programmer** (3.3V) für Upload

---

## Quick Start

### 1. Firmware konfigurieren

```bash
cd ESP32/Client

# Secrets-Datei erstellen
cp include/secrets.h.example include/secrets.h

# Editieren
nano include/secrets.h  # Linux
notepad include\secrets.h  # Windows
```

**Erforderliche Einstellungen:**
```cpp
#define WIFI_SSID "IhrWiFi"
#define WIFI_PASSWORD "IhrPasswort"
#define SERVER_HOST "192.168.1.100"  // Server-IP
#define SERVER_PORT 5000
#define AUTH_TOKEN "MATCH_SERVER_TOKEN"  // Aus server config.yaml
#define DEVICE_ID "ESP32-CAM-01"
```

### 2. Firmware hochladen

**Mit PlatformIO (empfohlen):**
```bash
pio run --target upload
pio device monitor  # Serial Monitor
```

**Mit Arduino IDE:**
- Siehe [Client/README.md](Client/README.md)

### 3. Hardware verkabeln

```
PIR HC-SR501:
  VCC → ESP32-CAM 5V
  GND → ESP32-CAM GND
  OUT → ESP32-CAM GPIO 13

Stromversorgung:
  5V 2A Netzteil → ESP32-CAM VCC + GND
```

**⚠️ Wichtig:**
- Verwenden Sie ein 2A-Netzteil!
- NICHT über USB vom PC betreiben (zu wenig Strom)

---

## Konfiguration

### PIR-Sensor

**In `src/main.cpp`:**
```cpp
#define PIR_PIN 13             // GPIO-Pin (Standard: 13)
#define MOTION_COOLDOWN_MS 5000  // Cooldown 5 Sekunden
```

**PIR-Sensor Einstellung (Potentiometer):**
- **Sx (Sensitivity):** Reichweite 3-7m einstellen
- **Tx (Time Delay):** Egal (Firmware hat eigenen Cooldown)
- **Jumper:** Auf "H" (Repeatable Trigger)

### Kamera

**In `src/main.cpp` → `CameraModule::init()`:**
```cpp
// Auflösung
config.frame_size = FRAMESIZE_SVGA;  // 800×600 (Standard)
// Alternativen: FRAMESIZE_VGA (640×480), FRAMESIZE_XGA (1024×768)

// JPEG-Qualität (0-63, niedriger = besser)
config.jpeg_quality = 10;

// Bildanpassungen
s->set_brightness(s, 0);   // -2 bis +2
s->set_contrast(s, 0);     // -2 bis +2
s->set_vflip(s, 1);        // Vertikal spiegeln
s->set_hmirror(s, 1);      // Horizontal spiegeln
```

### Streaming

**FPS einstellen:**
```cpp
#define STREAM_INTERVAL_MS 100  // 100ms = 10 fps
```

---

## Troubleshooting

### Kamera-Initialisierung fehlgeschlagen

**Fehler:** `Camera init failed with error 0x20001`

**Lösungen:**
1. Kamera-Kabel prüfen (klick-Verbindung)
2. Stromversorgung prüfen (2A!)
3. ESP32-CAM neu starten
4. Anderes Board versuchen

### WiFi-Verbindung fehlschlägt

**Fehler:** `WiFi connection failed`

**Lösungen:**
1. SSID/Passwort in `secrets.h` prüfen
2. Nur 2.4 GHz WiFi (ESP32 unterstützt KEIN 5 GHz!)
3. ESP32 näher an Router
4. Router neu starten

### Brown-out Detector

**Fehler:** `Brownout detector was triggered`

**Lösung:** Verwenden Sie ein 5V 2A Netzteil! Häufigster Fehler.

Optional: 100-470µF Kondensator zwischen 5V und GND.

### Upload fehlgeschlagen

**Fehler:** `Failed to connect to ESP32`

**Lösung:**
1. **IO0 mit GND verbinden** BEVOR Sie reset drücken
2. Reset-Taste drücken
3. Upload starten
4. **IO0 von GND trennen** nach Upload
5. Erneut Reset drücken

### Server Upload fehlschlägt

**Fehler:** `HTTP Error: connection refused`

**Checkliste:**
- [ ] Server läuft (`python app.py`)
- [ ] SERVER_HOST = richtige IP
- [ ] AUTH_TOKEN stimmt überein
- [ ] Firewall erlaubt Port 5000
- [ ] Gleicher Router/WLAN

**Testen:**
```bash
# Vom PC (Server-IP durch Ihre ersetzen)
curl http://192.168.1.100:5000/health
```

---

## Erweiterte Features

### Deep Sleep (Stromsparmodus)

```cpp
#define SLEEP_TIMEOUT_MS 300000  // 5 Minuten

void loop() {
    if (millis() - lastMotionTime > SLEEP_TIMEOUT_MS) {
        esp_sleep_enable_ext0_wakeup(GPIO_NUM_13, 1);  // Aufwachen bei PIR
        esp_deep_sleep_start();
    }
}
```

### OTA-Updates (Over-The-Air)

Firmware per WiFi aktualisieren:

**platformio.ini:**
```ini
upload_protocol = espota
upload_port = 192.168.1.150  ; ESP32-IP
```

**main.cpp:**
```cpp
#include <ArduinoOTA.h>

void setup() {
    // ... existing setup
    ArduinoOTA.begin();
}

void loop() {
    ArduinoOTA.handle();
    // ... existing loop
}
```

### Mehrere PIR-Sensoren

```cpp
#define PIR_PIN_FRONT 13
#define PIR_PIN_BACK 14

volatile bool motionFront = false;
volatile bool motionBack = false;

void IRAM_ATTR pirFrontISR() { motionFront = true; }
void IRAM_ATTR pirBackISR() { motionBack = true; }

void setup() {
    attachInterrupt(digitalPinToInterrupt(PIR_PIN_FRONT), pirFrontISR, RISING);
    attachInterrupt(digitalPinToInterrupt(PIR_PIN_BACK), pirBackISR, RISING);
}
```

---

## Technische Details

### Stromverbrauch

- Idle (WiFi an): ~180mA
- Streaming: ~250-300mA
- Foto-Aufnahme: ~350mA (Peak)
- Deep Sleep: ~10-20mA

**Batteriebetrieb:**
Laufzeit (Stunden) = Batterie-mAh / Durchschnitt-mA
Beispiel: 5000mAh / 250mA = 20 Stunden

### GPIO-Pinout (AI-Thinker)

**Verfügbare Pins:**
- GPIO 0: Boot-Button (verfügbar nach Boot)
- GPIO 12, 13, 14, 15: Frei nutzbar
- GPIO 16: **NICHT nutzen** (PSRAM)

**Belegt durch Kamera:**
- GPIO 4: LED Flash
- GPIO 5, 18, 19, 21, 23, 25, 26, 27, 32, 35, 36, 39

---

## Weiterführende Dokumentation

- **Detaillierte Anleitung:** [Client/README.md](Client/README.md)
- **Server-Setup:** [../Windows/Windows.md](../Windows/Windows.md) oder [../Linux/Linux.md](../Linux/Linux.md)
- **Hauptdokumentation:** [../README.md](../README.md)

---

## Quick Reference

### Firmware hochladen
```bash
cd ESP32/Client
pio run --target upload
```

### Serial Monitor
```bash
pio device monitor
```

### Server-IP finden
```bash
# Windows
ipconfig

# Linux
hostname -I
```

### ESP32-IP finden
Serial Monitor: Zeigt IP nach WiFi-Verbindung

---

**Letzte Aktualisierung:** 2025-12-22
**Hardware:** ESP32-CAM (AI-Thinker), OV2640
