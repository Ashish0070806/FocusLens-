# FocusLens 👁️🧠
### AI-Powered Focus Monitoring & Personalized Productivity Optimization System

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-YuNet%20Deep%20Learning-green.svg)](https://opencv.org/)
[![MariaDB](https://img.shields.io/badge/Database-MariaDB%20%2F%20MySQL-orange.svg)](https://mariadb.org/)
[![Hackathon](https://img.shields.io/badge/INNOVISE-Problem%20Statement%201-purple.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-Zero--Pixel%20Retention-brightgreen.svg)]()

> **INNOVISE Hackathon · Problem Statement 1:**  
> *Research an AI-powered productivity system exploring how computer vision and machine learning assess focus, fatigue, and stress indicators to suggest personalized productivity strategies and healthier work habits.*

---

## 🌟 Overview

**FocusLens** is an intelligent, edge-computed cognitive monitoring system that transforms your ordinary laptop webcam into a real-time focus, fatigue, and distraction sensor—**with 100% on-device privacy (zero video frames stored or transmitted)**.

Unlike legacy Pomodoro timers that arbitrarily interrupt deep flow, FocusLens is **behavior-adaptive**:
1. **Flow Guardian:** Silences alerts when you are in deep focus ($>80\%$).
2. **Early Burnout Prevention:** Intervenes with dynamic 5-minute guided breathing and ocular relaxation only when genuine biological fatigue or prolonged distraction is detected.
3. **1-Key Personal Calibration (`c`-key):** Adapts instantaneously to your exact laptop tilt angle, desk height, and prescription glasses.

---

## 🚀 Quickstart (1-Click Run)

### 1. Launch the Live AI Webcam Tracker
Double-click:
```text
run_webcam.bat
```
*(Or in PowerShell: `python3.13 webcam_telemetry.py`)*  
*Look at your screen and press **`c`** to calibrate your neutral screen gaze.*

### 2. Launch the Web Dashboard
Double-click:
```text
run_dashboard.bat
```
*(Or in PowerShell: `python3.13 serve_dashboard.py`)*

### 3. Open the Dashboard in Your Browser
Visit: **[http://localhost:8000/index.html](http://localhost:8000/index.html)**

---

## 🛠️ Alternative: Synthetic Telemetry Simulation Mode
If you want to demo or test the dashboard without opening your webcam:
```powershell
python3.13 simulate_telemetry.py --fast
```
This runs an autonomous stochastic digital twin cycling through the 4 cognitive states (Deep Focus $\rightarrow$ Mild Fatigue $\rightarrow$ Distraction Breach $\rightarrow$ Post-Break Recovery).

---

## 📂 Project Structure

```text
c:\Users\Aadmin\New folder\
│
├── webcam_telemetry.py         # Live Edge AI webcam ingestion engine (YuNet ONNX)
├── simulate_telemetry.py       # Organic 4-state stochastic telemetry simulator
├── serve_dashboard.py          # Standalone lightweight Python web server
│
├── index.html                  # Executive web dashboard with radial gauge & Chart.js
├── get_dashboard_data.php      # Native PHP endpoint returning real-time telemetry
├── save_telemetry.php          # Native PHP event ingestion endpoint
├── db_config.php               # Shared PDO connection with dual-port (3306/3308) probing
│
├── run_webcam.bat              # 1-click launcher for webcam AI tracker
├── run_simulator.bat           # 1-click launcher for telemetry simulator
├── run_dashboard.bat           # 1-click launcher for web dashboard server
│
├── face_detection_yunet_2023mar.onnx # OpenCV YuNet Deep Neural Network weights
├── FocusLens_Research_Presentation_v2.pptx # Enhanced Hackathon Pitch Deck
│
└── All nes Docs/               # Complete engineering & architectural documentation
    ├── 01_PROJECT_REQUIREMENTS_DOC.md
    ├── 02_DESIGN_DOC.md
    ├── 03_ARCHITECTURE_DOC.md
    ├── 04_DATABASE_DOC.md
    ├── 05_API_DOC.md
    ├── 06_AGENTS_DOC.md
    ├── 07_README.md
    ├── 08_PROJECT_IMPLEMENTATION_DOC.md
    ├── 09_SETUP_AND_INSTALLATION_DOC.md
    ├── 10_FEATURE_DEVELOPMENT_DOC.md
    ├── 11_AUTHENTICATION_AND_SECURITY_DOC.md
    ├── 12_MCP_INTEGRATION_DOC.md
    ├── 13_SYSTEM_INTEGRATION_DOC.md
    ├── 14_TESTING_AND_QA_DOC.md
    └── 15_DEBUGGING_AND_TROUBLESHOOTING_DOC.md
```

---

## 🔬 Scientific Foundations
1. **Soukupová & Čech (2016)**: Real-Time Eye Blink Detection using Facial Landmarks (*Eye Aspect Ratio - EAR*).
2. **Wu et al. (2023)**: YuNet Tiny Deep Neural Network for Edge Landmark Detection (*IEEE TPAMI*).
3. **Dinges et al. (1998)**: NASA/NHTSA PERCLOS criteria for psychophysiological alertness.
4. **Zagermann et al. (2018)**: Measuring Cognitive Load via Gaze Tracking (*ACM ISS*).
5. **Coles-Brennan et al. (2019)**: Management of Digital Screen Fatigue via Dynamic Micro-Breaks (*BMJ Open*).

---

## 👤 Author
**Ashish Jha** · Team CLASSIC SOLO  
INNOVISE Hackathon 2026
