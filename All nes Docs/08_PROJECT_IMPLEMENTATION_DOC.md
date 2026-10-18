# FocusLens - Project Implementation Document

**System:** FocusLens Full-Stack Implementation  
**Language Stack:** Python 3.13, PHP 8.2, Vanilla JavaScript (ES6+), Modern HTML5/CSS3  
**Version:** 1.0.0  

---

## 1. Codebase Overview & Implementation Mapping

FocusLens is organized into three interoperating modules:

| Source File | Technical Role | Key Libraries / Technologies |
| :--- | :--- | :--- |
| `webcam_telemetry.py` | Edge AI Computer Vision Ingestion | `OpenCV 5/4`, `cv2.FaceDetectorYN`, `numpy`, `mysql.connector` |
| `simulate_telemetry.py` | Stochastic Telemetry Generator | `math`, `random`, `mysql.connector`, ANSI terminal escape sequences |
| `serve_dashboard.py` | Standalone Python Dashboard Daemon | `http.server`, `json`, `mysql.connector` |
| `index.html` | Real-Time Executive Web Interface | HTML5, CSS Grid, SVG, Chart.js 4.4.1, Native Fetch API |
| `db_config.php` | Dual-Port Database Connector | PHP 8 PDO, UTF-8mb4, MySQL Native Driver |
| `get_dashboard_data.php` | High-Performance Data Feed API | PDO Prepared Statements, JSON encoder |
| `save_telemetry.php` | Event Ingestion Listener | `file_get_contents('php://input')`, PDO |

---

## 2. In-Depth Module Implementation

### 2.1 The Webcam Ingestion Engine (`webcam_telemetry.py`)

#### Pipeline Step 1: Model Initialization & Dual-Port Discovery
The engine initializes by verifying model file `face_detection_yunet_2023mar.onnx`. If absent, it downloads the official weights from OpenCV Model Zoo.
```python
detector = cv2.FaceDetectorYN.create(
    model=YUNET_MODEL_FILE,
    config="",
    input_size=(frame_w, frame_h),
    score_threshold=0.45,
    nms_threshold=0.3,
    top_k=5000
)
```

#### Pipeline Step 2: Gaze Vectoring & Mathematical Yaw
In each frame, the 5 landmarks are extracted:
```python
eye_mid_x = (right_eye[0] + left_eye[0]) / 2.0
eye_mid_y = (right_eye[1] + left_eye[1]) / 2.0
mouth_mid_y = (right_mouth[1] + left_mouth[1]) / 2.0

eye_dist = max(1.0, abs(left_eye[0] - right_eye[0]))
raw_yaw = (nose_tip[0] - eye_mid_x) / eye_dist
```

#### Pipeline Step 3: Low-Pass Exponential Smoothing (EMA)
Prevents glasses reflection flicker:
```python
smooth_yaw = 0.75 * smooth_yaw + 0.25 * raw_yaw
smooth_vert = 0.75 * smooth_vert + 0.25 * raw_vert
```

#### Pipeline Step 4: 1-Key Neutral Calibration (`c`-key)
When the user sits comfortably and hits `c`, the calibration buffers 20 frames (~0.6s) and locks the median values:
```python
if is_calibrating:
    calib_samples.append((raw_yaw, raw_vert))
    if len(calib_samples) >= 20:
        calibrated_yaw = float(np.median([s[0] for s in calib_samples]))
        calibrated_vert = float(np.median([s[1] for s in calib_samples]))
        is_calibrating = False
```

#### Pipeline Step 5: Distraction Debounce Timer
Prevents momentary glances away from falsely penalizing the focus score:
```python
if gaze_direction != "Screen":
    if distraction_timer_start is None:
        distraction_timer_start = time.time()
    elif time.time() - distraction_timer_start >= 2.5:
        is_distracted = 1
        focus_score = max(20.0, focus_score - 0.7)
else:
    distraction_timer_start = None
    is_distracted = 0
    focus_score = min(98.0, focus_score + 0.4)
```

---

### 2.2 The Telemetry Simulator Engine (`simulate_telemetry.py`)

#### Organic 4-State Cycle Formulation:
Implemented in `OrganicTelemetrySimulator`:
* **State A (Deep Focus):** $F_t = 0.7 F_{t-1} + 0.3 [85 + 8\sin(t \cdot 0.15) + \mathcal{U}(-2.5, 2.5)]$
* **State B (Mild Fatigue):** Decays from 70 to 50 with occasional random shifts to `Left` / `Right`.
* **State C (Distraction Breach):** Drops focus to 25–38, elevated fatigue 65–80, gaze `Away`, sets `is_distracted = 1`.
* **State D (Recovery / Post-Break):** Rebounds focus smoothly back to 80–90, fatigue resets to 15–20.

---

### 2.3 Web Dashboard Server (`serve_dashboard.py`)

Implements a native Python `HTTPServer` with custom request routing in `FocusLensHandler`:
* Maps `GET /` to `/index.html`.
* Maps `GET /get_dashboard_data.php` to real-time MariaDB queries executing:
  ```python
  cur.execute("SELECT focus_score, fatigue_index, gaze_direction, is_distracted, created_at FROM telemetry_logs WHERE session_id = %s ORDER BY id DESC LIMIT 1", (SESSION_ID,))
  ```
* Maps `POST /save_telemetry.php` to capture client-side break and snooze confirmations.
* Emits CORS headers (`Access-Control-Allow-Origin: *`) and explicit cache invalidation headers.
