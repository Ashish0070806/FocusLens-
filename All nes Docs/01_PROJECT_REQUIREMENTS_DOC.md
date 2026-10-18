# FocusLens - Project Requirements Document (PRD)

**Project Name:** FocusLens  
**Hackathon:** INNOVISE · AI/ML Problem Statement 1  
**Problem Statement:** AI-Powered Focus Monitoring and Personalized Productivity Optimization System  
**Version:** 1.0.0  
**Author:** Ashish Jha · Team CLASSIC SOLO  
**Status:** Approved & Implemented  

---

## 1. Executive Summary
FocusLens is an intelligent, edge-computed cognitive monitoring and personalized productivity optimization system. It bridges the critical divide between legacy, static time-management utilities (e.g., standard Pomodoro timers, screen-time loggers) and biological reality. By leveraging local computer vision, deep learning neural networks, and mathematical gaze vectoring, FocusLens continuously evaluates user attention, ocular fatigue, and distraction states in real time—without transmitting or recording raw video—and prescribes dynamic, physiological micro-breaks precisely when cognitive exhaustion occurs.

---

## 2. Business & Academic Problem Statement
Modern knowledge workers, programmers, and students face an epidemic of digital eye strain (asthenopia), context fragmentation, and cognitive fatigue. 

### Core Deficiencies in Existing Solutions:
1. **Dumb, Rigid Timers (e.g., standard Pomodoro):** Arbitrarily force breaks when a user is in deep flow, or fail to intervene early when a user experiences severe cognitive collapse 15 minutes into a session.
2. **Passive Application/Site Blockers (e.g., Forest, Freedom):** Track what window is in the foreground, entirely blind to whether the user is actually reading, zoning out, nodding off, or checking a phone.
3. **Invasive or Expensive Hardware Trackers (e.g., Tobii, EEG headbands):** Require prohibitive $200–$1,000+ specialized peripherals or raise severe workplace surveillance concerns.

FocusLens solves this with commodity laptop hardware using non-intrusive edge AI and behavioral feedback loops.

---

## 3. High-Level Requirements

### 3.1 Functional Requirements (FR)
* **FR-1: Real-Time Face & Landmark Acquisition:** System must capture laptop webcam frames at $\ge 25\text{ FPS}$ and isolate 5 primary facial landmarks (eyes, nose, mouth corners) with $\ge 90\%$ confidence across varied ambient lighting.
* **FR-2: Mathematical Gaze & Head Yaw Estimation:** System must compute normalized head rotation and gaze deviation to classify orientation into `Screen`, `Left`, `Right`, or `Away`.
* **FR-3: Ocular Fatigue & PERCLOS Monitoring:** System must monitor eyelid dynamics, blink rates, and compute a rolling Fatigue Index ($0–100$).
* **FR-4: Dynamic Focus Scoring:** System must calculate a continuous Focus Score ($0–100$) reflecting ongoing visual and mental engagement.
* **FR-5: High-Frequency Telemetry Ingestion:** System must ingest telemetry samples into a local MariaDB database every 3.0 seconds matching dashboard refresh cadences.
* **FR-6: Active Session Validation:** System must check and maintain session integrity, auto-provisioning session `#1` in `focus_sessions` upon cold start.
* **FR-7: Real-Time Executive Dashboard:** System must provide a responsive web interface displaying live gauge arcs, 40-point timeline charts, session duration counters, and breach tallies.
* **FR-8: Intelligent Breach Detection & Interventions:** System must detect cognitive breach (score $<40$ or sustained absence) and launch interactive 5-minute guided breathing and recovery sequences.
* **FR-9: 1-Key Personalized Calibration:** System must allow the user to press `c` to calibrate their neutral screen gaze, adapting to individual seating postures, laptop tilt angles, and eyeglasses.

### 3.2 Non-Functional Requirements (NFR)
* **NFR-1 (Privacy by Design):** Zero-pixel retention. Video frames must reside strictly in volatile RAM, processed in $<16\text{ ms}$, and discarded immediately. No image or video stream may be written to disk or transmitted over the network.
* **NFR-2 (Low Latency & High FPS):** The entire facial inference and gaze calculation pipeline must run locally at $<35\text{ ms}$ per frame on standard quad-core laptop CPUs without requiring dedicated GPUs.
* **NFR-3 (Data Integrity & Fault Tolerance):** Database reconnection logic must execute exponential backoff during MariaDB restarts or transient port switches between 3306 and 3308.
* **NFR-4 (Platform Independence):** Web telemetry visualization must operate across any modern Chromium or WebKit browser with zero proprietary browser extensions.

---

## 4. Key Stakeholders & Personas
1. **Software Engineers & Data Scientists:** Require uninterrupted deep flow intervals for algorithmic reasoning and architecture design; need protection against digital eye strain.
2. **Students & Remote Researchers:** Suffer from involuntary context switching (social media, mobile phone glances) during asynchronous learning.
3. **Ergonomic & Health Evaluators:** Seek verifiable, anonymized compliance with workplace ocular guidelines (e.g., 20-20-20 rule).

---

## 5. Scope & Limitations

### In-Scope:
* Edge-computed facial landmark tracking via OpenCV YuNet ONNX.
* Mathematical head pose yaw/pitch estimation.
* Continuous MariaDB telemetry persistence.
* Dual-backend web serving (Standalone Python HTTP server + Native PHP/Apache endpoints).
* Interactive breathing modal and break management.
* Synthetic telemetry fallback engine for testing.

### Out-of-Scope (Future Expansion):
* Clinical medical diagnosis of chronic neurological fatigue or ADHD.
* Multi-user facial recognition / enterprise biometric surveillance.
* Native mobile iOS/Android camera hooks (Desktop-first).
