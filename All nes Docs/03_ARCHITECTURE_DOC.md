# FocusLens - System Architecture Document

**System:** FocusLens Real-Time Cognitive Engine  
**Document:** End-to-End System Architecture & Component Interactions  
**Version:** 1.0.0  

---

## 1. High-Level Component Topology

FocusLens implements a multi-tier, decoupled architecture designed for local execution without cloud dependencies:

```mermaid
graph TD
    subgraph Client Perception
        WC[Laptop Webcam 30 FPS] --> CV[OpenCV Frame Ingestion]
        CV --> YN[YuNet Deep Neural Net ONNX]
        YN --> LM[5 Facial Landmarks & Bounding Box]
    end

    subgraph State & Math Engine
        LM --> CAL[1-Key Neutral Calibrator]
        CAL --> EMA[Exponential Moving Average Filter]
        EMA --> GZ[Gaze Vector: Yaw / Pitch]
        EMA --> FT[Fatigue & PERCLOS Estimator]
        GZ --> DBNC[Distraction Debouncer 2.5s]
        FT --> DBNC
    end

    subgraph Persistence Layer
        DBNC -->|Parametric SQL INSERT| MDB[(MariaDB / MySQL focuslens_db)]
        MDB --> SESS[focus_sessions]
        MDB --> LOGS[telemetry_logs]
    end

    subgraph Application & Serving
        MDB -->|Query Latest & Rolling 40| SRV[Dashboard Server: Python HTTP / PHP PDO]
        SRV -->|JSON Contract| UI[index.html Web Dashboard]
    end

    subgraph Interventions & UI
        UI --> GAUGE[Live Focus Radial Gauge]
        UI --> CHT[Chart.js 40-Point Timeline]
        UI --> BRK[Interactive 5-Min Guided Breathing Modal]
    end
```

---

## 2. Layer-by-Layer Architecture

### 2.1 The Perception Layer (`webcam_telemetry.py`)
* **Hardware Ingestion:** `cv2.VideoCapture(0)` initializes at $640\times 480$ resolution. Horizontal flipping creates an intuitive mirror-like preview.
* **Neural Inference Engine:** Loads `face_detection_yunet_2023mar.onnx` via `cv2.FaceDetectorYN`. It executes forward passes in $<18\text{ ms}$ on CPU, returning face bounding box and 5 coordinates:
  1. Right Eye $(x, y)$
  2. Left Eye $(x, y)$
  3. Nose Tip $(x, y)$
  4. Right Mouth Corner $(x, y)$
  5. Left Mouth Corner $(x, y)$
  6. Confidence Score ($0.0 – 1.0$)

### 2.2 Telemetry & Calibration Layer
* **Neutral Baseline Register:** Stores baseline $(\text{Yaw}_0, \text{Vert}_0)$ captured when the user presses `c`.
* **Landmark Smoother:** Implements continuous EMA to eliminate high-frequency jitter.
* **Temporal Debouncer:** Maintains a timer when gaze deviates from `Screen`. Flags `is_distracted = 1` only when deviation persists $>2.5$ seconds continuously.

### 2.3 Storage & Persistence Layer (`focuslens_db`)
* Directly managed via MariaDB connector (`mysql.connector` or `mariadb`).
* Auto-probes ports `3306` (standard XAMPP) and `3308` (standalone MariaDB), eliminating environment setup friction.
* Automatically verifies schema and auto-initializes session `#1` on launch.

### 2.4 Application & Dashboard Layer (`serve_dashboard.py` / PHP)
* Dual-compatible serving strategy:
  1. **Python Lightweight Web Server:** Standalone `HTTPServer` serving on `http://127.0.0.1:8000/index.html`. Handles `/get_dashboard_data.php` and `/save_telemetry.php` internally.
  2. **Apache/PHP Stack:** Directly executable via XAMPP with identical SQL contracts.
* **Frontend Dashboard (`index.html`):** Built with Vanilla JavaScript, CSS custom properties, SVG gauge primitives, and Chart.js 4.4.1.

---

## 3. End-to-End Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Cam as Laptop Webcam
    participant Engine as webcam_telemetry.py (YuNet)
    participant DB as MariaDB (focuslens_db)
    participant Server as serve_dashboard.py
    participant UI as index.html Dashboard

    User->>Cam: Sits in front of laptop
    Cam->>Engine: Stream 30 FPS video frames
    User->>Engine: Presses 'c' (Calibrate Neutral Screen Gaze)
    Engine->>Engine: Lock neutral baseline (Yaw_0, Pitch_0)
    
    loop Every 3.0 Seconds
        Engine->>Engine: Compute smoothed Focus, Fatigue, Gaze
        Engine->>DB: INSERT INTO telemetry_logs (session_id, focus, fatigue, gaze, distracted)
        UI->>Server: GET /get_dashboard_data.php
        Server->>DB: SELECT latest row + last 40 timeline points
        DB-->>Server: Telemetry records
        Server-->>UI: JSON {focus_score, fatigue, focus_seconds, timeline}
        UI->>UI: Update Gauge, Chart.js & Analytics Cards
    end

    opt Focus Score < 40 for 3 consecutive ticks
        UI->>User: Display Smart Toast (Threshold Breach Detected)
        User->>UI: Click "Start 5-minute break"
        UI->>UI: Open Breathing Ring Modal & Start 5:00 Timer
        UI->>Server: POST /save_telemetry.php {event: "break_start"}
    end
```
