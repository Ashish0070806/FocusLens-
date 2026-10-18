# FocusLens - Design Document

**System:** FocusLens Cognitive Engine & Dashboard  
**Classification:** Core System Design & Mathematical Specification  
**Version:** 1.0.0  

---

## 1. Design Philosophy
FocusLens is built upon three foundational tenets:
1. **Biological Reality over Arbitrary Rules:** Work rhythm should be driven by the user's autonomic and ocular status, not a rigid 25-minute clock.
2. **Frictionless Non-Intrusiveness:** Hardware requirements are restricted to standard 720p/1080p laptop webcams. No sensors, wearables, or manual logging required.
3. **Absolute Privacy Sovereignty:** The camera is treated strictly as an ephemeral optical sensor. Only scalar telemetry is persisted.

---

## 2. Mathematical Formulations & Biometric Modeling

### 2.1 Eye Aspect Ratio (EAR) & Blink Mechanics
Eye openness is derived from vertical and horizontal Euclidean distances between opposing eye landmarks:
$$\text{EAR} = \frac{\|p_2 - p_6\| + \|p_3 - p_5\|}{2 \|p_1 - p_4\|}$$
* Normal wakeful open eye: $\text{EAR} \in [0.28, 0.38]$
* Active blink: $\text{EAR} < 0.18$ for $\le 250\text{ ms}$
* Micro-sleep / Severe Fatigue: $\text{EAR} < 0.18$ for $> 600\text{ ms}$

### 2.2 PERCLOS (Percentage of Eyelid Closure)
Per NASA/NHTSA aviation fatigue criteria, PERCLOS quantifies cumulative drowsiness over rolling 60-second windows:
$$\text{PERCLOS} = \left( \frac{\sum_{t=1}^{N} \mathbb{I}(\text{EAR}_t < 0.20 \cdot \text{EAR}_{\text{baseline}})}{N} \right) \times 100$$
A sustained PERCLOS value $>12\%$ elevates the **Fatigue Index** into the High warning threshold ($\ge 65$).

### 2.3 Mathematical Gaze & Head Yaw Ratio
To compute horizontal orientation without requiring intensive 3D rendering engines, FocusLens calculates the normalized displacement of the nose tip relative to the horizontal midpoint of the eyes:
$$\mu_{\text{eyes}, x} = \frac{x_{\text{right\_eye}} + x_{\text{left\_eye}}}{2}$$
$$D_{\text{interocular}} = |x_{\text{left\_eye}} - x_{\text{right\_eye}}|$$
$$\text{Yaw Ratio} = \frac{x_{\text{nose}} - \mu_{\text{eyes}, x}}{D_{\text{interocular}}}$$

### 2.4 Personalized Neutral Calibration Offset
To accommodate different desk heights, chair ergonomics, and laptop screen angles:
$$\Delta\text{Yaw} = \text{Yaw}_{\text{smoothed}} - \text{Yaw}_{\text{calibrated}}$$
$$\Delta\text{Vert} = \text{Vert}_{\text{smoothed}} - \text{Vert}_{\text{calibrated}}$$
Where:
* $|\Delta\text{Yaw}| \le 0.30 \implies \text{Gaze} = \text{'Screen'}$
* $\Delta\text{Yaw} > 0.30 \implies \text{Gaze} = \text{'Left'}$
* $\Delta\text{Yaw} < -0.30 \implies \text{Gaze} = \text{'Right'}$
* $\Delta\text{Vert} \notin [-0.65, 0.70] \implies \text{Gaze} = \text{'Away'}$

### 2.5 Exponential Moving Average (EMA) Smoothing
To eliminate sensor jitter caused by blue-light coating reflections or CMOS sensor noise:
$$S_t = \alpha \cdot X_t + (1 - \alpha) \cdot S_{t-1} \quad (\alpha = 0.25)$$

---

## 3. Cognitive State Machine Architecture

FocusLens models human cognition across four continuous, sequential states:

```mermaid
stateDiagram-v2
    [*] --> StateA
    StateA --> StateB: Fatigue climbs, natural micro-decay
    StateB --> StateC: Sustained off-screen gaze or drop below 40
    StateC --> StateD: User launches 5-minute break
    StateD --> StateA: Post-break rebound into flow
    
    state "State A: Deep Focus" as StateA {
        Focus: 75-95
        Fatigue: 10-25
        Gaze: Screen
    }
    state "State B: Mild Fatigue" as StateB {
        Focus: 50-70
        Fatigue: 40-55
        Gaze: Screen/Left/Right
    }
    state "State C: Distraction Breach" as StateC {
        Focus: 25-38
        Fatigue: 65-80
        Gaze: Away
        Distracted: 1
    }
    state "State D: Recovery/Post-Break" as StateD {
        Focus: 80-90
        Fatigue: 15-20
        Gaze: Screen
    }
```

---

## 4. User Experience & Dashboard Design

### 4.1 Color Palette
* **Deep Space Background:** `#0D1B2A`
* **Card Panels:** `#13263A` / `#192F46`
* **Optic Green (Deep Flow):** `#4CAF50` (Focus $\ge 70$, Low Fatigue)
* **Amber Warning (Caution / Fatigue):** `#FFC107` (Focus $40–69$, Moderate Fatigue)
* **Critical Coral Red (Breach):** `#E5484D` (Focus $< 40$, High Fatigue)

### 4.2 Interactive Elements
* **Hero Radial Arc Gauge:** 270° visible stroke with SVG `stroke-dasharray` interpolation and numerical readout.
* **Smart Toast Intervention:** Triggers after 3 consecutive samples $<40$ focus score, presenting options to begin a 5-minute break or snooze for 2 minutes.
* **Animated Breathing Modal:** Box breathing ring running an 8-second CSS scale animation ($0.85 \leftrightarrow 1.08$) to guide autonomic regulation during breaks.
