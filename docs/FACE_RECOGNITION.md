# Face Recognition System - Documentation

**Lightweight Face Recognition mit YuNet + SFace für ESP32 Motion Detector**

## Inhaltsverzeichnis

1. [Architektur](#architektur)
2. [Setup & Installation](#setup--installation)
3. [Wie es funktioniert](#wie-es-funktioniert)
4. [Matching-Logik & Confidence](#matching-logik--confidence)
5. [Thresholds Tuning](#thresholds-tuning)
6. [Auto-Learning](#auto-learning)
7. [Personenverwaltung](#personenverwaltung)
8. [Datenbank-Design](#datenbank-design)
9. [Troubleshooting](#troubleshooting)
10. [Datenschutz](#datenschutz)

---

## Architektur

### Warum YuNet + SFace?

**Design-Entscheidung:** Minimale Dependencies, keine ML-Frameworks.

| Library | Pro | Contra | Entscheidung |
|---------|-----|--------|--------------|
| `face_recognition` (dlib) | Einfach, bekannt | dlib-Kompilierung schwierig auf Windows, groß | ❌ Abgelehnt |
| PyTorch + FaceNet | Beste Accuracy | Riesige Dependencies (>500 MB) | ❌ Overkill |
| **YuNet + SFace** | Lightweight, ONNX, nur OpenCV | Etwas weniger genau | ✅ **Gewählt** |

**YuNet:** Face Detector (ONNX, ~200 KB)
**SFace:** Face Embedder (ONNX, ~5 MB)

### Datenfluss

```
ESP32 → Upload JPEG
    ↓
Server: app.py
    ↓
YuNet: Detect Faces (bbox + landmarks)
    ↓
SFace: Extract Embeddings (128-dim vector)
    ↓
Matching: Compare with DB embeddings
    ↓
Result: GREEN / YELLOW / UNKNOWN
    ↓
Actions:
 - UNKNOWN → Create new Person
 - GREEN → Auto-Learning
 - All → Windows Toast Notification
```

---

## Setup & Installation

### 1. Dependencies installieren

```bash
cd server
pip install -r requirements.txt
```

**Installiert:**
- `opencv-contrib-python` (YuNet + SFace Support)
- `numpy`, `Pillow`
- `Flask`, `PyYAML`, `winotify`

### 2. Models downloaden

```bash
python models/download_models.py
```

**Downloaded:**
- `face_detection_yunet_2023mar.onnx` (~200 KB)
- `face_recognition_sface_2021dec.onnx` (~5 MB)

**Speicherort:** `server/models/`

### 3. Config aktivieren

Editiere `config.yaml`:

```yaml
face_recognition:
  enabled: true  # ← Auf true setzen
```

### 4. Server starten

```bash
python app.py
```

**Prüfe Logs:**
```
✓ YuNet and SFace models loaded successfully
Face Recognition: ENABLED
```

---

## Wie es funktioniert

### 1. Face Detection (YuNet)

```python
faces = detector.detect(image)
# Returns: [x, y, w, h, landmarks..., confidence]
```

**Output:**
- **bbox**: `[x, y, w, h]` (Face location)
- **landmarks**: 5 Punkte (Augen, Nase, Mundwinkel)
- **score**: Detection confidence (0.0-1.0)

### 2. Embedding Extraction (SFace)

```python
aligned_face = recognizer.alignCrop(image, landmarks)
embedding = recognizer.feature(aligned_face)
# Returns: 128-dim L2-normalized vector
```

**Output:** `np.ndarray(128,)` – eindeutiger "Fingerabdruck" des Gesichts

### 3. Matching gegen Datenbank

```python
distance = recognizer.match(query_emb, known_emb, dis_type=COSINE)
# Returns: Cosine distance (0.0 = identisch, 1.0 = komplett verschieden)
```

**Für jede bekannte Person:** Vergleiche Query-Embedding mit allen Samples.

**Best Match:** Niedrigste Distanz `d1` zu Person A
**Second Best:** Zweitniedrigste Distanz `d2` zu Person B

**Margin:** `margin = d2 - d1` (wie viel besser ist A als B?)

---

## Matching-Logik & Confidence

### Status-Bestimmung (GREEN / YELLOW / UNKNOWN)

```
GREEN (Zuverlässig):
  d1 < threshold_strict (default: 0.35)
  UND
  margin > margin_strict (default: 0.15)

YELLOW (Unsicher):
  d1 < threshold_loose (default: 0.50)
  UND
  margin > margin_loose (default: 0.08)

UNKNOWN:
  Keine Bedingung erfüllt
```

### Confidence-Berechnung (0-100%)

**Nicht-magischer Algorithmus:**

```python
if d1 < threshold_strict:
    base_conf = (threshold_loose - d1) / (threshold_loose - threshold_strict) * 100
else:
    base_conf = max(0, (threshold_loose - d1) / threshold_loose * 50)

# Margin-Bonus (höhere Margin = deutlicher Match)
margin_bonus = min(margin / margin_strict * 20, 20)

confidence = min(100, base_conf + margin_bonus)
```

**Interpretation:**
- `95-100%`: Sehr sicher (d1 sehr klein, margin sehr groß)
- `70-95%`: Gut (GREEN Match)
- `50-70%`: Unsicher (YELLOW Match)
- `<50%`: Unzuverlässig (UNKNOWN)

**Wichtig:** Confidence ist **kein** wissenschaftlich kalibrierter Wert, sondern eine **nützliche UI-Metrik** basierend auf Distanz + Margin.

---

## Thresholds Tuning

### Problem-Diagnose

| Symptom | Ursache | Lösung |
|---------|---------|--------|
| **Zu viele YELLOW** | threshold_strict zu niedrig | `threshold_strict` erhöhen (z.B. 0.35 → 0.40) |
| **Bekannte Person als UNKNOWN** | threshold_loose zu niedrig | `threshold_loose` erhöhen (z.B. 0.50 → 0.60) |
| **FALSE POSITIVES** (falsche Person erkannt) | threshold_strict zu hoch | `threshold_strict` senken (z.B. 0.35 → 0.30) |
| **Margin immer niedrig** | Zu wenig diverse Samples | Mehr Samples unter verschiedenen Bedingungen sammeln |

### Tuning-Prozess

**1. Testphase starten (7 Tage)**

- Lass das System laufen mit Default-Werten
- Sammle Auto-Learning Samples

**2. Events analysieren**

```bash
# In Web-UI: /events
# Schaue Dir Status-Verteilung an:
# - GREEN: X%
# - YELLOW: Y%
# - UNKNOWN: Z%
```

**Ziel:**
- **GREEN**: 80-90% (bei bekannten Personen)
- **YELLOW**: 5-10%
- **UNKNOWN**: 5-10% (neue Personen)

**3. Thresholds anpassen**

Gehe zu `/config` und ändere Werte inkrementell:

```yaml
# Beispiel-Tuning für 3 Personen im Haushalt
threshold_strict: 0.38   # Leicht erhöht (weniger YELLOW)
threshold_loose: 0.55    # Erhöht (weniger UNKNOWN bei Bekannten)
margin_strict: 0.12      # Leicht gesenkt (mehr GREEN)
margin_loose: 0.06       # Leicht gesenkt (mehr YELLOW statt UNKNOWN)
```

**4. Iterieren**

- Ändere **maximal 0.05** pro Schritt
- Teste 2-3 Tage
- Prüfe Events
- Wiederhole

### Advanced: Person-spezifische Samples

Wenn **Person A** immer YELLOW ist:

1. Gehe zu `/persons/A`
2. Prüfe Samples:
   - Sind alle ähnlich? (gleiche Beleuchtung, Winkel)
   - Quality Scores niedrig?
3. **Lösung:**
   - Lösche schlechte Samples
   - Sammle neue unter diversen Bedingungen:
     - Frontansicht, Seitenansicht
     - Hell, dunkel
     - Mit/ohne Brille

---

## Auto-Learning

### Wie es funktioniert

Bei jedem **GREEN Match**:

1. **Qualitäts-Check:**
   - Face Size > `min_face_size` (default: 10.000 px = 100×100)
   - Quality Score > `min_quality_score` (default: 0.6)

2. **Cooldown-Check:**
   - Letzte Learning-Session > `cooldown_seconds` (default: 60s)

3. **Limit-Check:**
   - Aktuelle Samples < `max_samples_per_person` (default: 15)
   - Wenn Limit erreicht → Ältestes Sample löschen

4. **Sample hinzufügen:**
   - Face-Crop speichern in `faces_db/person_X/`
   - Embedding in DB speichern

### Config

```yaml
auto_learning:
  enabled: true
  max_samples_per_person: 15
  cooldown_seconds: 60
  only_green_matches: true
  replace_strategy: 'oldest'  # oldest | lowest_quality
```

### Best Practices

**DO:**
- ✅ Lass Auto-Learning für erste 7 Tage laufen
- ✅ Sammle natürliche Variationen (Beleuchtung, Winkel)
- ✅ Cooldown mindestens 60s (verhindert Duplikate)

**DON'T:**
- ❌ `max_samples_per_person` > 20 (unnötig groß)
- ❌ `only_green_matches: false` (lernt von unsicheren Matches)
- ❌ `cooldown_seconds` < 30 (zu viele ähnliche Samples)

---

## Personenverwaltung

### Automatische Person-Erstellung

Wenn Face als **UNKNOWN** erkannt wird:

```yaml
auto_create_person: true
```

→ Erstellt automatisch neue Person mit Namen `"Unbekannt #N"`

**Ablauf:**
1. UNKNOWN Match
2. Erstelle Person in DB
3. Speichere erstes Sample
4. Toast Notification: "🆕 Neue Person erkannt!"

### Personen umbenennen

**Web-UI:** `/persons/<id>`

```html
<form method="POST" action="/persons/12/rename">
  <input type="text" name="name" value="Unbekannt #12">
  <button>Speichern</button>
</form>
```

→ Umbenennen in z.B. "Alice"

### Merge (Doppel-Anlage beheben)

**Problem:** Person wurde zweimal als UNKNOWN angelegt.

**Lösung:**

1. Gehe zu `/persons`
2. Wähle:
   - **Von:** "Unbekannt #12" (wird gelöscht)
   - **In:** "Alice" (bleibt erhalten)
3. Klicke "Merge durchführen"

**Effekt:**
- Alle Samples von #12 → Alice
- Alle Events von #12 → Alice
- #12 wird als `is_merged_into = Alice.id` markiert

**Rückgängig machen:**

SQL (nur für Fortgeschrittene):

```sql
-- Samples zurückschieben
UPDATE face_sample SET person_id = 12 WHERE person_id = 1;

-- Merge zurücksetzen
UPDATE person SET is_merged_into = NULL WHERE id = 12;
```

⚠️ **Vorsicht:** Keine UI-Funktion dafür. Besser: Vorsichtig mergen.

---

## Datenbank-Design

### Tabellen

**`person`**
```sql
id INTEGER PRIMARY KEY
name TEXT                  -- "Alice" oder "Unbekannt #12"
created_at TIMESTAMP
updated_at TIMESTAMP
is_merged_into INTEGER     -- NULL oder Person-ID
```

**`face_sample`**
```sql
id INTEGER PRIMARY KEY
person_id INTEGER          -- FK zu person
embedding BLOB             -- 128-dim float32 vector (512 bytes)
image_path TEXT            -- z.B. "faces_db/person_1/event_42.jpg"
quality_score REAL         -- 0.0-1.0
bbox TEXT                  -- JSON: [x, y, w, h]
created_at TIMESTAMP
```

**`event`**
```sql
id INTEGER PRIMARY KEY
timestamp TIMESTAMP
person_id INTEGER          -- FK zu person (NULL bei UNKNOWN)
confidence REAL            -- 0.0-1.0
distance REAL              -- Cosine distance
margin REAL                -- d2 - d1
status TEXT                -- GREEN, YELLOW, UNKNOWN, NO_FACE
image_path TEXT            -- Original-Bild
device_id TEXT             -- "ESP32-CAM-01"
```

### Speicherstruktur

```
server/
├── faces.db                     # SQLite DB
├── captured_images/             # Original-Uploads vom ESP32
│   ├── ESP32-CAM_20240101_120000.jpg
│   └── ESP32-CAM_20240101_120500.jpg
└── faces_db/                    # Face-Crops pro Person
    ├── person_1/
    │   ├── event_42_20240101_120000.jpg
    │   └── event_43_20240101_120500.jpg
    ├── person_2/
    └── person_3/
```

### Datenvolumen

**Pro Person (15 Samples):**
- Embeddings: 15 × 512 bytes = 7.5 KB
- Face-Crops: 15 × ~20 KB = 300 KB

**3 Personen:** ~1 MB (DB + Crops)

**1000 Events:** ~50 MB (Original-Bilder)

---

## Troubleshooting

### 1. "YuNet model not found"

**Problem:** Models nicht heruntergeladen.

**Lösung:**
```bash
python server/models/download_models.py
```

Prüfe: `server/models/face_detection_yunet_2023mar.onnx` existiert.

### 2. "No faces detected" (obwohl Gesicht sichtbar)

**Mögliche Ursachen:**
- Face zu klein (min. ~80×80 px empfohlen)
- Starke Überbelichtung / Unterbelichtung
- Extrem seitlicher Winkel (>45°)

**Lösung:**
- ESP32-CAM: Bessere Beleuchtung, Kamera näher
- YuNet `score_threshold` senken (in `face_recognition_cv.py:82`):
  ```python
  score_threshold=0.5,  # Default: 0.6
  ```

### 3. Alle Matches sind UNKNOWN

**Mögliche Ursachen:**
- Keine Samples in DB
- Thresholds zu streng

**Debug:**
```python
# In app.py nach Matching:
logger.info(f"Best distance: {d1}, margin: {margin}")
```

**Typische Werte:**
- **Same Person:** d1 = 0.15-0.35
- **Different Person:** d1 = 0.60-0.90

Wenn d1 bei bekannter Person > 0.50 → Samples schlecht oder Person verändert (Bart, Brille).

### 4. Face Recognition sehr langsam (>2s pro Bild)

**Ursache:** CPU-basierte Inference.

**Optimierung:**
- Reduziere Anzahl Samples pro Person (weniger Vergleiche)
- Downscale Bild vor Detection:
  ```python
  img = cv2.resize(img, (640, 480))  # Statt 1280x720
  ```

**Typische Performance:**
- Detection: 50-100 ms
- Embedding: 30-50 ms
- Matching (15 Samples): 5-10 ms

**Total:** ~100-200 ms pro Face auf modernem PC

### 5. Auto-Learning erstellt zu viele ähnliche Samples

**Lösung:**
```yaml
auto_learning:
  cooldown_seconds: 120  # Statt 60 → weniger häufig
```

Oder manuell alte Samples löschen (Web-UI in Zukunft).

---

## Datenschutz

### DSGVO-Konformität (Deutschland)

**Rechtsgrundlage:** Hausrecht (Art. 6 Abs. 1 lit. f DSGVO) für Hausflur.

**Pflichten:**

1. **Hinweisschild anbringen:**
   ```
   ⚠️ Videoüberwachung mit Gesichtserkennung
   Verantwortlich: [Name, Adresse]
   Zweck: Zugangskontrolle
   Kontakt: [E-Mail]
   ```

2. **Nur Hausflur überwachen** (nicht öffentlichen Gehweg)

3. **Zugriff beschränken:**
   - Server nur im LAN (nicht Internet-exponiert)
   - Starkes Auth-Token
   - Regelmäßige Updates

4. **Speicherfrist beachten:**
   ```yaml
   storage:
     max_age_days: 7  # Bilder nach 7 Tagen löschen
   ```

5. **Auskunftsrecht gewähren:**
   - Bewohner können anfragen: "Welche Daten habt ihr über mich?"
   - Export aus DB: `SELECT * FROM face_sample WHERE person_id = X`

### Empfehlungen

- ✅ **Nur Haushaltsmitglieder** als Personen anlegen
- ✅ **Gäste informieren** vor Betreten
- ✅ **Daten nicht weitergeben** (kein Cloud-Upload)
- ❌ **Keine Kinder** ohne Eltern-Zustimmung

### Auto-Delete (Optional)

Füge Cron-Job hinzu (Windows Task Scheduler):

```python
# cleanup.py
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

db = sqlite3.connect('faces.db')
cursor = db.cursor()

# Events älter als 7 Tage
cutoff = datetime.now() - timedelta(days=7)
cursor.execute("SELECT image_path FROM event WHERE timestamp < ?", (cutoff,))
for row in cursor.fetchall():
    Path(row[0]).unlink(missing_ok=True)

cursor.execute("DELETE FROM event WHERE timestamp < ?", (cutoff,))
db.commit()
```

---

## Zusammenfassung

✅ **Minimal:** YuNet + SFace, nur OpenCV, keine ML-Frameworks
✅ **Präzise:** Distance + Margin Matching mit GREEN/YELLOW/UNKNOWN
✅ **Wartbar:** SQLite, YAML-Config, Web-UI für Tuning
✅ **Auto-Learning:** Max 15 Samples, Cooldown, Quality-Filter
✅ **Datenschutz:** Lokal, kein Cloud, Löschfristen

**Nächste Schritte:**
1. Models downloaden (`python models/download_models.py`)
2. `face_recognition.enabled: true` setzen
3. Server starten, erste Personen erfassen
4. Nach 7 Tagen Thresholds tunen (`/config`)
5. Doppel-Personen mergen (`/persons`)

**Support:** Siehe `server/README.md` und Hauptprojekt-README.
