# FocusLens - Authentication, Security & Ethical AI Document

**Document:** Security Model, Data Privacy & Ethical AI Compliance  
**Classification:** Information Security & Privacy Architecture  
**Version:** 1.0.0  

---

## 1. Privacy by Design: The "Zero-Pixel Retention" Policy

The paramount ethical risk in computer vision productivity software is unauthorized surveillance, employee eavesdropping, or video leakage. FocusLens neutralizes this by enforcing strict **Zero-Pixel Retention**:

```
[ Camera Hardware ] ──> Volatile Memory (RAM Buffer)
                               │
                        OpenCV YuNet AI
                               │
                       5 Numeric Coordinates
                               │
         ┌─────────────────────┴─────────────────────┐
         ▼                                           ▼
[ RAM Frame Overwritten ]                   Scalar SQL Ingestion
(Destroyed in <16 ms)                      (No image bytes exist)
```

### Technical Enforcements:
1. **Volatile RAM Processing Only:** Video frames exist exclusively in ephemeral numpy arrays in heap memory.
2. **Zero Disk I/O for Video:** No `.jpg`, `.png`, or `.mp4` file is ever written to disk or temporary system folders.
3. **No Network Egress for Media:** The camera pipeline has no HTTP client, WebSocket stream, or remote telemetry uplink.

---

## 2. Network & Host Security

### 2.1 Localhost Isolation
* The API daemon binds strictly to loopback interface `127.0.0.1` (not `0.0.0.0`).
* Telemetry endpoints reject non-local requests by default, preventing external devices on local LAN/Wi-Fi from querying cognitive status.

### 2.2 SQL Injection Prevention
All database queries utilize strict parameterized prepared statements:
```python
# Fully parameterized - zero concatenation
cursor.execute("""
    INSERT INTO telemetry_logs (session_id, focus_score, fatigue_index, gaze_direction, is_distracted)
    VALUES (%s, %s, %s, %s, %s)
""", (session_id, focus_score, fatigue_index, gaze_direction, is_distracted))
```
This guarantees mathematical immunity against SQL injection attacks regardless of client payload.

---

## 3. Session Authentication & Multi-Tenancy

### 3.1 Current Local Workstation Model
* Operating in single-tenant local workstation mode:
  * Default user is identified by `user_id = 1`.
  * Active session token binds to `session_id = 1`.

### 3.2 Enterprise Multi-Tenant Architecture (Roadmap)
For cloud or enterprise deployments, the architecture is designed to integrate:
* **JSON Web Tokens (JWT):** Bearer tokens transmitted via `Authorization: Bearer <token>` headers.
* **Role-Based Access Control (RBAC):**
  * `Role: Individual User` $\rightarrow$ Full read access to personal telemetry.
  * `Role: Aggregate Manager` $\rightarrow$ Access to anonymized, group-level fatigue indexes (no individual granularity).

---

## 4. Ethical AI & User Sovereignty

FocusLens aligns with IEEE 7000 and EU AI Act principles for affective computing:
* **Explicit User Agency:** The user can instantly pause tracking via the UI switch (`System active` / `Standby`) or by pressing `q` in the camera window.
* **Optical LED Awareness:** Standard laptop hardware LEDs illuminate when the camera is engaged, ensuring no hidden background capture can occur.
* **Non-Punitive Design:** FocusLens is explicitly architected as a self-care productivity aid, not a punitive boss-ware surveillance tool.
