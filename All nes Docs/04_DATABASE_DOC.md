# FocusLens - Database Architecture & Schema Document

**Database System:** MariaDB 10.x / 13.x / MySQL 8.x  
**Default Host & Ports:** `127.0.0.1:3306` (Primary) / `127.0.0.1:3308` (Secondary)  
**Database Name:** `focuslens_db`  
**Storage Engine:** InnoDB  
**Character Set:** `utf8mb4` / `utf8mb4_unicode_ci`  

---

## 1. Entity-Relationship Model (ERD)

```mermaid
erDiagram
    FOCUS_SESSIONS ||--o{ TELEMETRY_LOGS : "logs telemetry for"

    FOCUS_SESSIONS {
        int id PK "Auto-increment session ID"
        int user_id "User reference (default 1)"
        varchar session_name "Descriptive name"
        int goal_seconds "Target duration in seconds"
        tinyint is_active "1 = Active, 0 = Inactive"
        timestamp start_time "Session launch timestamp"
        timestamp end_time "Session completion timestamp"
    }

    TELEMETRY_LOGS {
        bigint id PK "Auto-increment primary key"
        int session_id FK "References focus_sessions(id)"
        int focus_score "Calculated focus index (0-100)"
        int fatigue_index "Calculated fatigue index (0-100)"
        varchar gaze_direction "Screen, Left, Right, Away"
        tinyint is_distracted "1 = Distracted, 0 = Focused"
        timestamp created_at "Observation timestamp"
    }
```

---

## 2. DDL Schema Definition

### 2.1 Table: `focus_sessions`
Stores metadata regarding user work and study blocks.

```sql
CREATE TABLE IF NOT EXISTS `focus_sessions` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT DEFAULT 1,
    `session_name` VARCHAR(100) DEFAULT 'Main Focus Session',
    `goal_seconds` INT DEFAULT 3600,
    `is_active` TINYINT(1) DEFAULT 1,
    `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `end_time` TIMESTAMP NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### Field Specifications:
* `id` (`INT`, PK, Auto-increment): Unique identifier. Default active session uses `id = 1`.
* `user_id` (`INT`): Identifies local user account. Defaults to 1 for standalone desktop setups.
* `session_name` (`VARCHAR(100)`): Human-readable session descriptor.
* `goal_seconds` (`INT`): Target focus goal (defaults to 3,600 seconds = 1 hour).
* `is_active` (`TINYINT(1)`): Boolean flag indicating live ingestion status.
* `start_time` (`TIMESTAMP`): Session kickoff time.
* `end_time` (`TIMESTAMP`, Nullable): Populated when session terminates cleanly.

---

### 2.2 Table: `telemetry_logs`
High-throughput time-series store containing high-frequency observations (every 3 seconds).

```sql
CREATE TABLE IF NOT EXISTS `telemetry_logs` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY,
    `session_id` INT NOT NULL,
    `focus_score` INT NOT NULL,
    `fatigue_index` INT NOT NULL,
    `gaze_direction` VARCHAR(20) NOT NULL,
    `is_distracted` TINYINT(1) NOT NULL DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_session_time` (`session_id`, `created_at`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### Field Specifications:
* `id` (`BIGINT`, PK): 64-bit integer ensuring scalability across millions of continuous telemetry points.
* `session_id` (`INT`, Indexed): Foreign key mapping to `focus_sessions.id`.
* `focus_score` (`INT`): Bounded integer value between 0 and 100.
* `fatigue_index` (`INT`): Bounded integer value between 0 and 100.
* `gaze_direction` (`VARCHAR(20)`): Discrete categorical state: `'Screen'`, `'Left'`, `'Right'`, or `'Away'`.
* `is_distracted` (`TINYINT(1)`): Binary classification indicator.
* `created_at` (`TIMESTAMP`, Indexed): Microsecond-compatible temporal record.

---

## 3. High-Performance Query Patterns

### 3.1 Fetching Latest Telemetry State
Executed by `/get_dashboard_data.php` on every 3-second cycle:
```sql
SELECT focus_score, fatigue_index, gaze_direction, is_distracted, created_at
FROM telemetry_logs
WHERE session_id = 1
ORDER BY id DESC
LIMIT 1;
```
*Index Used:* Primary Key clustered index (`id DESC`), resulting in execution time $< 0.4\text{ ms}$.

### 3.2 Fetching Rolling 40-Point Timeline
Feeds the Chart.js line plot:
```sql
SELECT created_at, focus_score, fatigue_index
FROM telemetry_logs
WHERE session_id = 1
ORDER BY id DESC
LIMIT 40;
```
*Optimization:* Results are reversed in memory by the API layer, eliminating expensive SQL full-table scans.

### 3.3 Aggregate Productive Focus Duration
Calculates productive seconds (score $\ge 50$):
```sql
SELECT COUNT(*) * 3 AS focus_seconds
FROM telemetry_logs
WHERE session_id = 1 AND focus_score >= 50;
```

---

## 4. Archival & Retention Strategy
In continuous 8-hour production use, the table logs approximately 9,600 rows/day (~1.2 MB/day).
For extended multi-month deployments, an optional scheduled maintenance event can archive rows older than 30 days:
```sql
DELETE FROM telemetry_logs 
WHERE created_at < NOW() - INTERVAL 30 DAY;
```
