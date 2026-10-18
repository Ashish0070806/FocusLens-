# FocusLens - Setup and Installation Guide

**Operating Environment:** Windows 10 / Windows 11  
**Target Hardware:** Any standard laptop or desktop with webcam  
**Database Prerequisites:** MariaDB (standalone) or XAMPP (MySQL)  
**Version:** 1.0.0  

---

## 1. System Prerequisites

Before running FocusLens, ensure your workstation has:
1. **Python 3.10 – 3.13:** Available on system PATH as `python` or `python3.13`.
2. **Database Engine:** MariaDB or MySQL running locally on port `3306` (standard XAMPP) or `3308` (standard MariaDB Windows installer).
3. **Webcam:** Any built-in laptop camera or external USB webcam.
4. **Web Browser:** Google Chrome, Microsoft Edge, Brave, or Mozilla Firefox.

---

## 2. Step-by-Step Installation

### Step 1: Open PowerShell in Project Directory
Navigate to the root directory where FocusLens is installed:
```powershell
cd "c:\Users\Aadmin\New folder"
```

### Step 2: Install Python Dependencies
Run the following pip command using your Python executable:
```powershell
python3.13 -m pip install mysql-connector-python opencv-python numpy
```

*(Note: In PowerShell, you can run `Set-Alias python python3.13` if you prefer typing plain `python`.)*

### Step 3: Verify or Start MariaDB / MySQL
Ensure your local MariaDB or XAMPP MySQL service is running:
* **If using XAMPP:** Open *XAMPP Control Panel* and click **Start** next to MySQL.
* **If using Standalone MariaDB:** Verify service status via Windows Services (`services.msc` $\rightarrow$ MariaDB).

---

## 3. Database Initialization

You do **not** need to manually run SQL scripts. The Python runtime automatically executes:
```sql
CREATE DATABASE IF NOT EXISTS focuslens_db;
```
And auto-provisions both `focus_sessions` and `telemetry_logs` tables with high-performance indices on cold start.

*(Optional Manual Verification via MariaDB CLI):*
```sql
CREATE DATABASE IF NOT EXISTS focuslens_db;
USE focuslens_db;
SHOW TABLES;
```

---

## 4. Running the Application Stack

### Mode A: Full Real-Time AI Webcam Tracking (Recommended)

1. **Start the AI Vision Ingestion Engine:**
   Double-click **`run_webcam.bat`** (or execute `python3.13 webcam_telemetry.py`).
   *A live camera preview window will launch.*
2. **Calibrate Your Screen Gaze:**
   Look comfortably at your monitor and press **`c`** on your keyboard.
3. **Launch the Dashboard Server:**
   Double-click **`run_dashboard.bat`** (or execute `python3.13 serve_dashboard.py`).
4. **Open Dashboard:**
   Navigate in your browser to: **`http://localhost:8000/index.html`**

---

### Mode B: Synthetic Telemetry Simulation (No Camera Required)

If you are presenting, running automated tests, or in a privacy-restricted room without webcam access:
1. Double-click **`run_simulator.bat`** (or execute `python3.13 simulate_telemetry.py`).
2. Double-click **`run_dashboard.bat`**.
3. Open **`http://localhost:8000/index.html`**.

---

## 5. Verification Checklist

| Checkpoint | Expected Result | Action if Failed |
| :--- | :--- | :--- |
| Database Port Check | Terminal logs: `[OK] Connected to MariaDB on 127.0.0.1:3306` | Start MySQL in XAMPP or specify `--port 3308`. |
| Camera Initialization | Camera LED activates; preview window displays | Ensure no background app (Teams, Zoom) has locked the webcam. |
| Dashboard Link State | Top header pill displays green: **`Backend connected`** | Verify `serve_dashboard.py` is running on port 8000. |
| Gauge Telemetry | Radial arc updates values every 3 seconds | Confirm rows are inserting into `telemetry_logs`. |
