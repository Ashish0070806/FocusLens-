# FocusLens - Feature Development & Roadmap Document

**Project:** FocusLens  
**Scope:** Current Capabilities & Future Feature Roadmap  
**Version:** 1.0.0  

---

## 1. Implemented Features Matrix (Phase 1 - Production Ready)

| Feature | Component | Status | Technical Description |
| :--- | :--- | :---: | :--- |
| **YuNet Edge AI Detection** | `webcam_telemetry.py` | Complete | Runs local ONNX model detecting face box + 5 facial landmarks at 30+ FPS. |
| **Mathematical Yaw Estimation** | `webcam_telemetry.py` | Complete | Computes normalized nose-to-eye midpoint ratio for gaze classification. |
| **1-Key Personal Calibration** | `webcam_telemetry.py` | Complete | Pressing `c` buffers 20 frames to calculate user-specific neutral screen baseline. |
| **Exponential Smoothing (EMA)** | `webcam_telemetry.py` | Complete | Low-pass filter eliminates flicker caused by blue-light glasses reflections. |
| **Distraction Debouncing** | `webcam_telemetry.py` | Complete | Enforces a 2.5-second persistence rule before setting `is_distracted = 1`. |
| **Time-Series Ingestion** | MariaDB | Complete | Commits parameter-safe telemetry logs every 3 seconds to `focuslens_db`. |
| **Dual-Port Auto-Probing** | All DB Scripts | Complete | Automatically probes ports 3306 and 3308, eliminating manual config hurdles. |
| **Executive Radial Gauge** | `index.html` | Complete | 270° SVG arc with real-time numerical score and dynamic color transitions. |
| **Chart.js 40-Point Timeline** | `index.html` | Complete | Live dual-dataset trend visualizer with threshold benchmark line. |
| **Dynamic Guided Break Modal** | `index.html` | Complete | Contextual toast launches an 8-second animated box breathing ring. |
| **Synthetic Simulation Engine** | `simulate_telemetry.py`| Complete | 4-state autonomous digital twin with organic sinusoidal noise. |

---

## 2. Feature Roadmap (Phase 2 - Planned Enhancements)

### 2.1 rPPG Non-Contact Heart Rate & HRV Stress Estimator
* **Concept:** Blood volume pulses cause minute color fluctuations in the facial epidermis. By isolating the Green channel in regions of interest (cheeks and forehead) and computing Fast Fourier Transforms (FFT), FocusLens can extract instantaneous Heart Rate (BPM) and Heart Rate Variability (HRV).
* **Target Delivery:** Q2 2026.
* **Benefit:** Objective, physiological stress estimation without requiring Apple Watch or smartbands.

### 2.2 Formal NASA PERCLOS Engine
* **Concept:** Maintain an active 60-second circular buffer storing binary eye closure states ($1 = \text{EAR} < 0.20 \cdot \text{baseline}$).
* **Formula:** $\text{PERCLOS} = \frac{\text{Closed Frame Count}}{\text{Total Frames in 60s}} \times 100$.
* **Target Delivery:** Q2 2026.

### 2.3 Yawn Detection via Mouth Aspect Ratio (MAR)
* **Concept:** Measure the vertical opening between inner lip landmarks normalized by horizontal mouth width.
* **Formula:** $\text{MAR} = \frac{\|p_{\text{lip\_top}} - p_{\text{lip\_bottom}}\|}{\|p_{\text{mouth\_left}} - p_{\text{mouth\_right}}\|}$.
* **Target Delivery:** Q3 2026.

### 2.4 Unsupervised Circadian Chronotype Profiling
* **Concept:** Machine learning job executing weekly over historic MariaDB sessions:
  * Clusters focus scores by time of day ($k=3$: Peak, Moderate, Slump).
  * Auto-generates weekly productivity advice: *"Schedule high-cognitive architecture between 10:15 AM – 12:00 PM; reserve 2:30 PM for admin tasks."*
* **Target Delivery:** Q3 2026.

### 2.5 Adaptive Audio Soundscape Integration
* **Concept:** Dynamic audio synthesizer that shifts from 40Hz Gamma binaural beats during deep flow to 10Hz Alpha calming waves during micro-breaks.
* **Target Delivery:** Q4 2026.
