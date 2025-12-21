/*
 * ESP32-CAM Motion Detector with Live Stream
 * ===========================================
 *
 * Features:
 * - PIR motion sensor with interrupt-based detection
 * - Capture and upload JPEG on motion event
 * - Continuous frame streaming for live view
 * - Debounce and cooldown to prevent spam
 * - Modular camera abstraction for easy board changes
 *
 * Hardware:
 * - ESP32-CAM (AI-Thinker) with OV2640 camera
 * - PIR sensor on GPIO 13 (configurable)
 * - Built-in LED for status indication
 *
 * Author: Senior Embedded Engineer
 * License: MIT
 */

#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include "esp_camera.h"
#include "esp_timer.h"
#include "esp_log.h"
#include "secrets.h"

// ============================================================================
// CONFIGURATION
// ============================================================================

// PIR Sensor Pin (GPIO 13 on ESP32-CAM is interrupt-capable)
#define PIR_PIN 13

// Built-in LED (usually GPIO 33 on ESP32-CAM)
#define LED_PIN 33

// Motion detection cooldown (milliseconds)
#define MOTION_COOLDOWN_MS 5000  // 5 seconds between triggers

// Stream frame interval (milliseconds) - target ~10 fps
#define STREAM_INTERVAL_MS 100  // 100ms = 10 fps

// HTTP timeouts
#define HTTP_TIMEOUT_MS 10000

// Serial baud rate
#define SERIAL_BAUD 115200

// ============================================================================
// CAMERA PINS - ESP32-CAM (AI-Thinker)
// ============================================================================
// NOTE: If using different board, only modify this section!

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// ============================================================================
// GLOBAL STATE
// ============================================================================

// Motion detection state
volatile bool motionDetected = false;
unsigned long lastMotionTime = 0;

// Streaming state
bool streamingEnabled = true;
unsigned long lastStreamTime = 0;

// WiFi status
bool wifiConnected = false;

// ============================================================================
// CAMERA MODULE (Encapsulated for easy board changes)
// ============================================================================

class CameraModule {
public:
    bool init() {
        camera_config_t config;
        config.ledc_channel = LEDC_CHANNEL_0;
        config.ledc_timer = LEDC_TIMER_0;
        config.pin_d0 = Y2_GPIO_NUM;
        config.pin_d1 = Y3_GPIO_NUM;
        config.pin_d2 = Y4_GPIO_NUM;
        config.pin_d3 = Y5_GPIO_NUM;
        config.pin_d4 = Y6_GPIO_NUM;
        config.pin_d5 = Y7_GPIO_NUM;
        config.pin_d6 = Y8_GPIO_NUM;
        config.pin_d7 = Y9_GPIO_NUM;
        config.pin_xclk = XCLK_GPIO_NUM;
        config.pin_pclk = PCLK_GPIO_NUM;
        config.pin_vsync = VSYNC_GPIO_NUM;
        config.pin_href = HREF_GPIO_NUM;
        config.pin_sscb_sda = SIOD_GPIO_NUM;
        config.pin_sscb_scl = SIOC_GPIO_NUM;
        config.pin_pwdn = PWDN_GPIO_NUM;
        config.pin_reset = RESET_GPIO_NUM;
        config.xclk_freq_hz = 20000000;
        config.pixel_format = PIXFORMAT_JPEG;

        // Frame size and quality settings
        // FRAMESIZE_SVGA = 800x600 (good balance for motion detection + streaming)
        // FRAMESIZE_VGA = 640x480 (better for streaming performance)
        // FRAMESIZE_UXGA = 1600x1200 (high quality but slower)

        if(psramFound()){
            config.frame_size = FRAMESIZE_SVGA;  // 800x600
            config.jpeg_quality = 10;  // 0-63, lower = higher quality
            config.fb_count = 2;
            Serial.println("PSRAM found - using SVGA mode");
        } else {
            config.frame_size = FRAMESIZE_VGA;  // 640x480
            config.jpeg_quality = 12;
            config.fb_count = 1;
            Serial.println("No PSRAM - using VGA mode");
        }

        // Initialize camera
        esp_err_t err = esp_camera_init(&config);
        if (err != ESP_OK) {
            Serial.printf("Camera init failed with error 0x%x\n", err);
            return false;
        }

        // Camera sensor adjustments for better quality
        sensor_t * s = esp_camera_sensor_get();
        if (s != NULL) {
            // Flip image vertically if needed
            // s->set_vflip(s, 1);
            // Mirror image horizontally if needed
            // s->set_hmirror(s, 1);

            // Adjust exposure and gain for indoor/outdoor
            s->set_brightness(s, 0);     // -2 to 2
            s->set_contrast(s, 0);       // -2 to 2
            s->set_saturation(s, 0);     // -2 to 2
            s->set_special_effect(s, 0); // 0 = No effect
            s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
            s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
            s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled
            s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
            s->set_aec2(s, 0);           // 0 = disable , 1 = enable
            s->set_ae_level(s, 0);       // -2 to 2
            s->set_aec_value(s, 300);    // 0 to 1200
            s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
            s->set_agc_gain(s, 0);       // 0 to 30
            s->set_gainceiling(s, (gainceiling_t)0);  // 0 to 6
            s->set_bpc(s, 0);            // 0 = disable , 1 = enable
            s->set_wpc(s, 1);            // 0 = disable , 1 = enable
            s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
            s->set_lenc(s, 1);           // 0 = disable , 1 = enable
            s->set_dcw(s, 1);            // 0 = disable , 1 = enable
            s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
        }

        Serial.println("Camera initialized successfully");
        return true;
    }

    camera_fb_t* captureFrame() {
        // Capture frame from camera
        camera_fb_t* fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Camera capture failed");
            return nullptr;
        }
        return fb;
    }

    void releaseFrame(camera_fb_t* fb) {
        if (fb) {
            esp_camera_fb_return(fb);
        }
    }
};

// Global camera instance
CameraModule camera;

// ============================================================================
// WIFI MODULE
// ============================================================================

void connectWiFi() {
    Serial.println("\n=== Connecting to WiFi ===");
    Serial.printf("SSID: %s\n", WIFI_SSID);

    WiFi.mode(WIFI_STA);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    unsigned long startAttempt = millis();
    while (WiFi.status() != WL_CONNECTED && millis() - startAttempt < WIFI_TIMEOUT_MS) {
        delay(500);
        Serial.print(".");
    }

    if (WiFi.status() == WL_CONNECTED) {
        wifiConnected = true;
        Serial.println("\n✓ WiFi connected!");
        Serial.printf("IP Address: %s\n", WiFi.localIP().toString().c_str());
        Serial.printf("Signal: %d dBm\n", WiFi.RSSI());

        // Blink LED to indicate success
        for(int i = 0; i < 3; i++) {
            digitalWrite(LED_PIN, HIGH);
            delay(100);
            digitalWrite(LED_PIN, LOW);
            delay(100);
        }
    } else {
        wifiConnected = false;
        Serial.println("\n✗ WiFi connection failed!");
        Serial.println("Check SSID/password in secrets.h");
    }
}

void checkWiFi() {
    if (WiFi.status() != WL_CONNECTED) {
        if (wifiConnected) {
            Serial.println("WiFi connection lost! Reconnecting...");
            wifiConnected = false;
        }
        connectWiFi();
    }
}

// ============================================================================
// HTTP COMMUNICATION
// ============================================================================

bool uploadImage(camera_fb_t* fb) {
    if (!fb || !wifiConnected) {
        return false;
    }

    HTTPClient http;
    String url = String("http://") + SERVER_HOST + ":" + String(SERVER_PORT) + "/upload";

    Serial.printf("Uploading image to: %s\n", url.c_str());

    http.begin(url);
    http.setTimeout(HTTP_TIMEOUT_MS);

    // Add authentication header
    http.addHeader("X-Auth-Token", AUTH_TOKEN);

    // Create multipart form data
    String boundary = "----ESP32CAMBoundary";
    String contentType = "multipart/form-data; boundary=" + boundary;

    http.addHeader("Content-Type", contentType);

    // Build multipart body
    String bodyStart = "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n";
    bodyStart += String(DEVICE_ID) + "\r\n";
    bodyStart += "--" + boundary + "\r\n";
    bodyStart += "Content-Disposition: form-data; name=\"image\"; filename=\"capture.jpg\"\r\n";
    bodyStart += "Content-Type: image/jpeg\r\n\r\n";

    String bodyEnd = "\r\n--" + boundary + "--\r\n";

    uint32_t totalLen = bodyStart.length() + fb->len + bodyEnd.length();

    // Allocate buffer for full request
    uint8_t* buffer = (uint8_t*)malloc(totalLen);
    if (!buffer) {
        Serial.println("Failed to allocate upload buffer");
        http.end();
        return false;
    }

    // Copy data to buffer
    memcpy(buffer, bodyStart.c_str(), bodyStart.length());
    memcpy(buffer + bodyStart.length(), fb->buf, fb->len);
    memcpy(buffer + bodyStart.length() + fb->len, bodyEnd.c_str(), bodyEnd.length());

    // Send POST request
    int httpResponseCode = http.POST(buffer, totalLen);

    free(buffer);

    // Check response
    bool success = false;
    if (httpResponseCode > 0) {
        Serial.printf("HTTP Response: %d\n", httpResponseCode);
        if (httpResponseCode == 200) {
            String response = http.getString();
            Serial.printf("Server response: %s\n", response.c_str());
            success = true;
        }
    } else {
        Serial.printf("HTTP Error: %s\n", http.errorToString(httpResponseCode).c_str());
    }

    http.end();
    return success;
}

bool sendStreamFrame(camera_fb_t* fb) {
    if (!fb || !wifiConnected) {
        return false;
    }

    HTTPClient http;
    String url = String("http://") + SERVER_HOST + ":" + String(SERVER_PORT) + "/stream_frame";

    http.begin(url);
    http.setTimeout(5000);  // Shorter timeout for streaming

    // Add authentication header
    http.addHeader("X-Auth-Token", AUTH_TOKEN);
    http.addHeader("Content-Type", "image/jpeg");

    // Send frame as raw JPEG
    int httpResponseCode = http.POST(fb->buf, fb->len);

    bool success = (httpResponseCode == 200);

    if (!success && httpResponseCode != 0) {
        Serial.printf("Stream frame upload failed: %d\n", httpResponseCode);
    }

    http.end();
    return success;
}

// ============================================================================
// PIR INTERRUPT HANDLER
// ============================================================================

void IRAM_ATTR pirInterruptHandler() {
    // Check cooldown to prevent spam
    unsigned long now = millis();
    if (now - lastMotionTime > MOTION_COOLDOWN_MS) {
        motionDetected = true;
        lastMotionTime = now;
    }
}

// ============================================================================
// MOTION HANDLER
// ============================================================================

void handleMotionEvent() {
    Serial.println("\n🚨 MOTION DETECTED!");

    // LED on during capture
    digitalWrite(LED_PIN, HIGH);

    // Capture photo
    camera_fb_t* fb = camera.captureFrame();

    if (fb) {
        Serial.printf("Frame captured: %d bytes, %dx%d\n", fb->len, fb->width, fb->height);

        // Upload to server
        bool uploaded = uploadImage(fb);

        if (uploaded) {
            Serial.println("✓ Image uploaded successfully");
        } else {
            Serial.println("✗ Image upload failed");
        }

        camera.releaseFrame(fb);
    } else {
        Serial.println("✗ Failed to capture frame");
    }

    // LED off
    digitalWrite(LED_PIN, LOW);

    // Reset flag
    motionDetected = false;
}

// ============================================================================
// STREAMING HANDLER
// ============================================================================

void handleStreaming() {
    unsigned long now = millis();

    // Check if it's time to send next frame
    if (now - lastStreamTime < STREAM_INTERVAL_MS) {
        return;
    }

    lastStreamTime = now;

    // Capture and send frame
    camera_fb_t* fb = camera.captureFrame();
    if (fb) {
        sendStreamFrame(fb);  // Fire-and-forget, don't block on errors
        camera.releaseFrame(fb);
    }
}

// ============================================================================
// SETUP
// ============================================================================

void setup() {
    // Initialize serial
    Serial.begin(SERIAL_BAUD);
    delay(1000);

    Serial.println("\n\n");
    Serial.println("========================================");
    Serial.println("ESP32-CAM Motion Detector");
    Serial.println("========================================");
    Serial.printf("Device ID: %s\n", DEVICE_ID);
    Serial.printf("Firmware: v1.0.0\n");
    Serial.println("========================================");

    // Initialize LED
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, LOW);

    // Initialize PIR sensor
    pinMode(PIR_PIN, INPUT);
    Serial.printf("PIR sensor on GPIO %d\n", PIR_PIN);

    // Initialize camera
    Serial.println("\nInitializing camera...");
    if (!camera.init()) {
        Serial.println("✗ Camera initialization failed!");
        Serial.println("Check camera connections and reboot.");
        while(1) {
            delay(1000);
        }
    }

    // Connect to WiFi
    connectWiFi();

    if (!wifiConnected) {
        Serial.println("✗ Cannot continue without WiFi");
        Serial.println("Update secrets.h and reboot.");
        while(1) {
            delay(1000);
        }
    }

    // Attach PIR interrupt
    attachInterrupt(digitalPinToInterrupt(PIR_PIN), pirInterruptHandler, RISING);
    Serial.println("PIR interrupt attached (RISING edge)");

    Serial.println("\n========================================");
    Serial.println("System Ready!");
    Serial.println("========================================");
    Serial.printf("Server: http://%s:%d\n", SERVER_HOST, SERVER_PORT);
    Serial.printf("Motion cooldown: %d ms\n", MOTION_COOLDOWN_MS);
    Serial.printf("Stream FPS: ~%d\n", 1000 / STREAM_INTERVAL_MS);
    Serial.println("========================================\n");

    // Initial test capture
    Serial.println("Capturing test frame...");
    camera_fb_t* test_fb = camera.captureFrame();
    if (test_fb) {
        Serial.printf("✓ Test frame: %d bytes\n", test_fb->len);
        camera.releaseFrame(test_fb);
    }
}

// ============================================================================
// MAIN LOOP
// ============================================================================

void loop() {
    // Check WiFi connection
    checkWiFi();

    // Handle motion events (priority)
    if (motionDetected && wifiConnected) {
        handleMotionEvent();
    }

    // Handle streaming (continuous)
    if (streamingEnabled && wifiConnected) {
        handleStreaming();
    }

    // Small delay to prevent watchdog timeout
    delay(10);
}
