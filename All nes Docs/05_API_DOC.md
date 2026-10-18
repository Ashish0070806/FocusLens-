# FocusLens - API Specification & Endpoint Documentation

**Protocol:** HTTP/1.1  
**Content-Type:** `application/json; charset=utf-8`  
**Base URLs:**
* Standalone Python Daemon: `http://127.0.0.1:8000/`
* Local Apache/PHP Server: `http://127.0.0.1/New%20folder/`

---

## 1. Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/get_dashboard_data.php` | Retrieves current focus score, fatigue index, cumulative focus seconds, distractions, and rolling 40 timeline points. |
| `POST` | `/save_telemetry.php` | Receives client-side UI telemetry events (e.g., break triggered, snooze, breach acknowledgment). |

---

## 2. Detailed Specifications

### 2.1 `GET /get_dashboard_data.php`

Polled every 3,000 ms by `index.html` to update the visual gauge, timeline graph, and analytics counters.

#### Request Headers:
```http
Accept: application/json
Cache-Control: no-cache, no-store
```

#### Query Parameters:
* None (Defaults to active `session_id = 1`).

#### Success Response (HTTP `200 OK`):
```json
{
  "focus_score": 84,
  "fatigue": 22,
  "focus_seconds": 1860,
  "distractions": 2,
  "timeline": [
    {
      "time": "14:34:16",
      "score": 82,
      "fatigue": 20
    },
    {
      "time": "14:34:19",
      "score": 84,
      "fatigue": 22
    }
  ]
}
```

#### Response Field Definitions:
* `focus_score` (`integer`): Real-time normalized focus score ($0–100$).
* `fatigue` (`integer`): Real-time fatigue index ($0–100$).
* `focus_seconds` (`integer`): Cumulative focus seconds accumulated during the session where score $\ge 50$.
* `distractions` (`integer`): Total number of distraction breaches recorded in the current session.
* `timeline` (`array`): Ordered list of up to 40 chronological records (`time` in `HH:MM:SS`, `score`, and `fatigue`) for Chart.js plotting.

#### Error Responses:
* `503 Service Unavailable`: MariaDB offline or connection failed on candidate ports.
  ```json
  {
    "error": "Database connection failed",
    "details": "Could not connect to MariaDB on 127.0.0.1 (ports 3306, 3308)."
  }
  ```

---

### 2.2 `POST /save_telemetry.php`

Invoked by the frontend when user actions take place (e.g. launching a break, snoozing an alert, or confirming breach).

#### Request Headers:
```http
Content-Type: application/json
Accept: application/json
```

#### Request Payload Schema:
```json
{
  "focus_score": 32,
  "fatigue": 70,
  "distractions": 3,
  "focus_seconds": 1840,
  "event": "sample|breach|break_start|break_end|system_on|system_off",
  "system_active": true,
  "timestamp": "2026-10-18T14:02:10.000Z"
}
```

#### Supported Event Types:
* `sample`: Regular telemetry ping from UI.
* `breach`: Triggered when client-side threshold breach is detected ($<40$ focus score for 3 ticks).
* `break_start`: Dispatched when the user clicks **"Start 5-minute break"**.
* `break_end`: Dispatched when the 5-minute break timer completes or is dismissed.
* `system_on` / `system_off`: Dispatched when the monitoring switch is toggled.

#### Success Response (HTTP `200 OK`):
```json
{
  "status": "success",
  "event": "break_start"
}
```

---

## 3. Cross-Origin Resource Sharing (CORS) & Caching

Both endpoints emit standardized security and caching headers:
```http
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Accept
Cache-Control: no-store, no-cache, must-revalidate
```
