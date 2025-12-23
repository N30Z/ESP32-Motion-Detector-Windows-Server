# Face Recognition Models

## Erforderliche Modelle

Für die Gesichtserkennung werden zwei ONNX-Modelle von OpenCV benötigt:

1. **YuNet** - Gesichtsdetektion (ca. 200 KB)
2. **SFace** - Gesichtserkennung (ca. 5 MB)

## Automatischer Download (empfohlen)

Führen Sie das Download-Script aus:

```bash
cd Server/models
python download_models.py
```

Das Script lädt beide Modelle automatisch herunter.

## Manueller Download

Falls das automatische Download-Script nicht funktioniert, können Sie die Modelle manuell herunterladen:

### YuNet (Gesichtsdetektion)

```bash
wget -O face_detection_yunet_2023mar.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
```

**Oder im Browser öffnen:**
https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx

### SFace (Gesichtserkennung)

```bash
wget -O face_recognition_sface_2021dec.onnx \
  https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx
```

**Oder im Browser öffnen:**
https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx

## Platzierung der Modelle

Die heruntergeladenen Dateien müssen in diesem Verzeichnis gespeichert werden:
```
ESP32-Motion-Detector-Windows-Server/
└── Server/
    └── models/
        ├── face_detection_yunet_2023mar.onnx    ← YuNet-Modell
        ├── face_recognition_sface_2021dec.onnx  ← SFace-Modell
        ├── download_models.py
        └── README.md
```

## Überprüfung

Nach dem Download sollten beide Dateien vorhanden sein:

```bash
ls -lh
```

**Erwartete Ausgabe:**
```
-rw-r--r-- 1 user user 200K ... face_detection_yunet_2023mar.onnx
-rw-r--r-- 1 user user 5.0M ... face_recognition_sface_2021dec.onnx
```

## Aktivierung

Die Gesichtserkennung ist in `Server/config.yaml` bereits aktiviert:

```yaml
face_recognition:
  enabled: true  # ✓ Aktiviert
```

Nach dem Download der Modelle starten Sie den Server neu:

```bash
cd Server
python app.py
```

## Fehlerbehebung

### "Face recognition model not found"

**Problem:** Die Modelle wurden nicht gefunden.

**Lösung:**
1. Überprüfen Sie, ob die Dateien im richtigen Verzeichnis liegen
2. Stellen Sie sicher, dass die Dateinamen korrekt sind (keine .1, .tmp Endungen)
3. Starten Sie den Server neu

### "Face recognition disabled"

**Problem:** Face Recognition ist in der Konfiguration deaktiviert.

**Lösung:**
Öffnen Sie `Server/config.yaml` und setzen Sie:
```yaml
face_recognition:
  enabled: true
```

### Download-Fehler (Proxy/Firewall)

**Problem:** Downloads schlagen mit 403 Forbidden fehl.

**Lösung:**
1. Laden Sie die Dateien manuell im Browser herunter (Links oben)
2. Speichern Sie sie im `Server/models/` Verzeichnis
3. Benennen Sie sie korrekt (falls der Browser .txt oder andere Endungen hinzufügt)

## Weitere Informationen

- [OpenCV Zoo Repository](https://github.com/opencv/opencv_zoo)
- [YuNet Dokumentation](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)
- [SFace Dokumentation](https://github.com/opencv/opencv_zoo/tree/main/models/face_recognition_sface)
