# ESP32-CAM Motion Detector - Firmware

Arduino/PlatformIO firmware for ESP32-CAM with PIR motion sensor.

> **💡 Alternative:** Looking for a Raspberry Pi camera solution? See [clients/raspi](../clients/raspi) for Python-based PIR camera client with CSI/USB camera support.

## Hardware Requirements

### ESP32-CAM Board
- **Recommended**: AI-Thinker ESP32-CAM
- **Camera**: OV2640 (included on board)
- **PSRAM**: Recommended for better performance
- **Power**: 5V 2A (important - insufficient power causes crashes!)

### PIR Motion Sensor
- **Type**: HC-SR501 or similar
- **Voltage**: 5V or 3.3V compatible
- **Connection**:
  - VCC → 5V
  - GND → GND
  - OUT → GPIO 13

### Additional Components
- **Programmer**: FTDI USB-to-Serial (3.3V!) or USB-Serial adapter
- **Jumper wires**
- **Power supply**: 5V 2A minimum

## Wiring Diagram

```
ESP32-CAM (AI-Thinker)
┌─────────────────┐
│                 │
│  [OV2640 Camera]│
│                 │
│  GPIO 13 ●------├─── PIR OUT
│  5V      ●------├─── PIR VCC
│  GND     ●------├─── PIR GND
│                 │
│  GPIO 33 ● LED  │
│                 │
│  U0T (TX)●------├─── FTDI RX
│  U0R (RX)●------├─── FTDI TX
│  GND     ●------├─── FTDI GND
│  5V      ●------├─── FTDI 5V (or external)
│                 │
│  IO0     ●      │  (Connect to GND for flashing)
└─────────────────┘

IMPORTANT:
- FTDI must be 3.3V logic level!
- DO NOT connect 5V to 3.3V pin!
- During flashing: Connect IO0 to GND
- During running: Disconnect IO0 from GND
```

## Software Setup

### Option 1: PlatformIO (Recommended)

#### Install PlatformIO

**Visual Studio Code:**
1. Install VS Code: https://code.visualstudio.com/
2. Install PlatformIO extension
3. Restart VS Code

**Command Line:**
```bash
pip install platformio
```

#### Configure Secrets

```bash
cd esp32
cp include/secrets.h.example include/secrets.h
```

Edit `include/secrets.h`:
```cpp
#define WIFI_SSID "YourWiFiName"
#define WIFI_PASSWORD "YourWiFiPassword"
#define SERVER_HOST "192.168.1.100"  // Your Windows PC IP
#define SERVER_PORT 5000
#define AUTH_TOKEN "YOUR_SECRET_TOKEN_CHANGE_ME_12345"  // Match server config
#define DEVICE_ID "ESP32-CAM-01"
```

**Find your Windows PC IP:**
```cmd
ipconfig
```
Look for "IPv4 Address" (e.g., 192.168.1.100)

#### Build and Upload

**VS Code:**
1. Open `esp32` folder in VS Code
2. Click PlatformIO icon (alien head)
3. Click "Upload" under env:esp32cam

**Command Line:**
```bash
cd esp32
pio run --target upload
```

#### Monitor Serial Output

**VS Code:**
- Click "Monitor" in PlatformIO

**Command Line:**
```bash
pio device monitor
```

### Option 2: Arduino IDE

#### Install Arduino IDE

Download: https://www.arduino.cc/en/software

#### Install ESP32 Board Support

1. File → Preferences
2. Additional Board Manager URLs:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Tools → Board → Boards Manager
4. Search "esp32" → Install "esp32 by Espressif Systems"

#### Configure Arduino IDE

1. Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM
2. Tools → Flash Frequency → 80MHz
3. Tools → CPU Frequency → 240MHz
4. Tools → Partition Scheme → Huge APP (3MB No OTA/1MB SPIFFS)
5. Tools → Port → (Select your USB port)

#### Copy Files to Arduino Project

```
Create Arduino project folder: ESP32_Motion_Detector
Copy: src/main.cpp → ESP32_Motion_Detector.ino
Copy: include/secrets.h.example → secrets.h (edit credentials)
```

#### Upload

1. Connect IO0 to GND
2. Press Reset button on ESP32-CAM
3. Click Upload in Arduino IDE
4. Wait for "Leaving... Hard resetting via RTS pin..."
5. Disconnect IO0 from GND
6. Press Reset button

## Configuration

### PIR Sensor Settings

Edit `main.cpp`:

```cpp
// PIR pin (default: GPIO 13)
#define PIR_PIN 13

// Cooldown between triggers (milliseconds)
#define MOTION_COOLDOWN_MS 5000  // 5 seconds

// Adjust if needed:
// - Increase for fewer alerts
// - Decrease for more sensitive detection
```

**PIR Physical Adjustments:**
- **Sensitivity pot**: Adjust detection range (3-7m)
- **Time delay pot**: How long PIR stays HIGH (adjustable, but firmware uses cooldown)

### Camera Settings

Edit `main.cpp` → `CameraModule::init()`:

```cpp
// Resolution options:
config.frame_size = FRAMESIZE_SVGA;  // 800x600 (default)
// FRAMESIZE_VGA;    // 640x480 (faster)
// FRAMESIZE_XGA;    // 1024x768 (slower)
// FRAMESIZE_UXGA;   // 1600x1200 (highest quality, slowest)

// JPEG quality (0-63, lower = better quality, larger file)
config.jpeg_quality = 10;  // Default

// Image adjustments
s->set_brightness(s, 0);     // -2 to 2
s->set_contrast(s, 0);       // -2 to 2
s->set_saturation(s, 0);     // -2 to 2
s->set_vflip(s, 1);          // Flip vertically
s->set_hmirror(s, 1);        // Mirror horizontally
```

### Streaming Settings

```cpp
// Stream FPS (frames per second)
#define STREAM_INTERVAL_MS 100  // 100ms = 10 fps

// Realistic limits:
// - 10 fps: Smooth for monitoring
// - 15 fps: Maximum practical on ESP32-CAM
// - 5 fps: Better for weak WiFi
```

### WiFi Settings

```cpp
// Connection timeout
#define WIFI_TIMEOUT_MS 20000  // 20 seconds

// Retry on disconnect (optional, add to loop)
void checkWiFi() {
    if (WiFi.status() != WL_CONNECTED) {
        connectWiFi();
    }
}
```

## Testing

### 1. Serial Monitor Test

After upload, open Serial Monitor (115200 baud):

**Expected output:**
```
========================================
ESP32-CAM Motion Detector
========================================
Device ID: ESP32-CAM-01
Firmware: v1.0.0
========================================
PSRAM found - using SVGA mode
Camera initialized successfully
=== Connecting to WiFi ===
SSID: YourWiFi
...
✓ WiFi connected!
IP Address: 192.168.1.150
PIR interrupt attached (RISING edge)
========================================
System Ready!
========================================
Server: http://192.168.1.100:5000
Motion cooldown: 5000 ms
Stream FPS: ~10
========================================
Capturing test frame...
✓ Test frame: 45678 bytes
```

### 2. PIR Motion Test

**Trigger motion:**
1. Wave hand in front of PIR sensor
2. Check Serial Monitor:
   ```
   🚨 MOTION DETECTED!
   Frame captured: 45678 bytes, 800x600
   Uploading image to: http://192.168.1.100:5000/upload
   HTTP Response: 200
   ✓ Image uploaded successfully
   ```

3. Check Windows notification popup
4. Check server: http://localhost:5000/latest

### 3. Stream Test

Open browser: `http://YOUR_PC_IP:5000/stream?token=YOUR_TOKEN`

You should see live video (~10 fps).

## Troubleshooting

### Camera Init Failed

**Symptoms:**
```
Camera init failed with error 0x20001
```

**Solutions:**
1. Check camera ribbon cable connection
2. Ensure cable is fully inserted (click)
3. Power cycle ESP32-CAM
4. Try different power supply (2A minimum!)
5. Check for counterfeit OV2640 (try different board)

### WiFi Connection Failed

**Symptoms:**
```
✗ WiFi connection failed!
```

**Solutions:**
1. Verify SSID/password in `secrets.h`
2. Check WiFi is 2.4GHz (ESP32 doesn't support 5GHz)
3. Move ESP32 closer to router
4. Restart router
5. Check WiFi not hidden (or use BSSID)

### Upload Failed / Brown-out Detector

**Symptoms:**
```
Brownout detector was triggered
```

**Solutions:**
1. ⚠️ **Use 5V 2A power supply** (most common issue!)
2. Don't power from USB (insufficient current)
3. Add 100-470µF capacitor across 5V and GND
4. Use shorter USB cable
5. Try external 5V power supply

### Motion Not Detected

**Symptoms:**
- No serial output when waving hand

**Solutions:**
1. Check PIR wiring (VCC, GND, OUT)
2. Verify PIR pin in code matches physical connection
3. Adjust PIR sensitivity pot (turn clockwise)
4. Wait 30-60 seconds after power-on (PIR calibration time)
5. Test PIR separately:
   ```cpp
   void loop() {
       Serial.println(digitalRead(PIR_PIN));
       delay(100);
   }
   ```

### Upload/Upload Failed

**Symptoms:**
```
Failed to connect to ESP32: Wrong boot mode detected
```

**Solutions:**
1. Connect IO0 to GND BEFORE pressing reset
2. Press and hold reset while connecting IO0
3. Release reset
4. Try upload again
5. Disconnect IO0 after upload

### HTTP Upload Failed

**Symptoms:**
```
HTTP Error: connection refused
```

**Solutions:**
1. Verify server is running (`python app.py`)
2. Check server IP in `secrets.h` matches PC IP
3. Check firewall allows port 5000
4. Ping server from another device
5. Verify auth token matches server config

### Guru Meditation Error / Reboot Loop

**Symptoms:**
```
Guru Meditation Error: Core 1 panic'ed
```

**Solutions:**
1. Insufficient power → Use 2A supply
2. Bad camera connection → Reseat cable
3. Corrupted firmware → Re-flash
4. PSRAM issue → Try without PSRAM:
   ```cpp
   config.fb_count = 1;
   config.frame_size = FRAMESIZE_VGA;
   ```

## Advanced Features

### Change PIR Pin

```cpp
// Default: GPIO 13
// Alternative: GPIO 12, 14, 15

#define PIR_PIN 12  // Change to your pin

// Note: Some GPIOs affect boot behavior
// Safe choices: 12, 13, 14, 15
// Avoid: 0, 1, 2, 3, 5, 12, 15 (boot strapping pins)
```

### Add Multiple PIR Sensors

```cpp
#define PIR_PIN_FRONT 13
#define PIR_PIN_BACK 14

void IRAM_ATTR pirFrontHandler() {
    motionDetected = true;
    motionLocation = "front";
}

void setup() {
    attachInterrupt(digitalPinToInterrupt(PIR_PIN_FRONT), pirFrontHandler, RISING);
    attachInterrupt(digitalPinToInterrupt(PIR_PIN_BACK), pirBackHandler, RISING);
}
```

### Enable Deep Sleep

```cpp
// Sleep when no motion for 5 minutes
#define SLEEP_TIMEOUT_MS 300000

void loop() {
    unsigned long now = millis();

    if (now - lastMotionTime > SLEEP_TIMEOUT_MS) {
        Serial.println("Entering deep sleep...");

        // Wake on PIR trigger
        esp_sleep_enable_ext0_wakeup(GPIO_NUM_13, 1);
        esp_deep_sleep_start();
    }
}
```

### OTA Updates (Over-The-Air)

Add to `platformio.ini`:
```ini
upload_protocol = espota
upload_port = 192.168.1.150  ; ESP32 IP
upload_flags =
    --auth=admin
```

Add to firmware:
```cpp
#include <ArduinoOTA.h>

void setup() {
    // ...
    ArduinoOTA.begin();
}

void loop() {
    ArduinoOTA.handle();
    // ...
}
```

## Performance Tips

### Optimize Frame Size

**Trade-offs:**
- **UXGA (1600×1200)**: Best quality, ~1-2 fps, slow upload
- **SVGA (800×600)**: Good quality, ~10 fps, recommended
- **VGA (640×480)**: Lower quality, ~15 fps, fast
- **QVGA (320×240)**: Low quality, ~25 fps, very fast

### Reduce WiFi Power Consumption

```cpp
WiFi.setSleep(WIFI_PS_MIN_MODEM);  // Reduce power, keep connection
// or
WiFi.setSleep(WIFI_PS_NONE);  // Full performance, higher power
```

### Increase Upload Speed

```cpp
// Use raw JPEG body instead of multipart
http.addHeader("Content-Type", "image/jpeg");
int code = http.POST(fb->buf, fb->len);
```

### Disable Streaming When Not Needed

```cpp
// Add button or web endpoint to toggle
streamingEnabled = false;  // Saves bandwidth
```

## Pin Reference

### ESP32-CAM (AI-Thinker) Pinout

```
Available GPIOs (not used by camera):
- GPIO 0  : BOOT button (available, but used for flashing)
- GPIO 2  : Built-in LED (reserved)
- GPIO 3  : U0R (Serial RX, available if not debugging)
- GPIO 12 : Available
- GPIO 13 : Available (default PIR pin)
- GPIO 14 : Available
- GPIO 15 : Available
- GPIO 16 : PSRAM (don't use if PSRAM enabled)

Reserved (used by camera):
- GPIO 4  : LED Flash
- GPIO 5, 18, 19, 21, 23, 25, 26, 27, 32, 35, 36, 39
```

## Power Consumption

**Typical values:**
- Idle (WiFi connected): ~180mA
- Streaming: ~250-300mA
- Camera capture: ~350mA peak
- Deep sleep: ~10-20mA

**Recommendations:**
- Use 5V 2A power supply
- For battery: Use deep sleep mode
- Calculate battery life: `Battery_mAh / Average_mA = Hours`
  - Example: 5000mAh / 250mA = 20 hours

## License

MIT License - See main project README
