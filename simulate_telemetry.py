"""
FocusLens - Real-Time Telemetry Simulation Engine
Injects realistic cognitive focus and fatigue telemetry into MariaDB/MySQL.

Features:
- Connects to local MariaDB/MySQL (ports 3306 / 3308 with auto-fallback)
- Auto-verifies focuslens_db database and tables
- Checks/initializes active session (ID = 1) in focus_sessions
- 4 organic 5-minute states:
    1. State A: Deep Focus (Score: 75-95, Fatigue: 10->25, Gaze: Screen, Distracted: 0)
    2. State B: Mild Fatigue (Score: 50-70, Fatigue: 40-55, Gaze: Left/Right/Screen, Distracted: 0)
    3. State C: Distraction/Breach (Score: 25-38, Fatigue: 65-80, Gaze: Away, Distracted: 1)
    4. State D: Recovery/Post-Break (Score: 80-90, Fatigue: 15-20, Gaze: Screen, Distracted: 0)
- High-performance INSERT statements matching dashboard telemetry schema
- Color-coded diagnostic terminal output with state banners
- Robust error handling with auto-reconnection and failover
"""

import sys
import time
import math
import random
import argparse
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

# Ensure compatibility across mysql-connector-python and mariadb
try:
    import mysql.connector
    from mysql.connector import errorcode
    DB_DRIVER = "mysql.connector"
except ImportError:
    try:
        import mariadb as mysql
        DB_DRIVER = "mariadb"
    except ImportError:
        print("\033[91m[ERROR] Neither 'mysql-connector-python' nor 'mariadb' library is installed.\033[0m")
        print("Please install via: pip install mysql-connector-python")
        sys.exit(1)

# ==========================================
# ANSI Color Codes for Terminal Output
# ==========================================
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Text Colors
GREEN = "\033[92m"
AMBER = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"

# Background Colors
BG_GREEN = "\033[42m\033[30m"
BG_AMBER = "\033[43m\033[30m"
BG_RED = "\033[41m\033[97m"
BG_BLUE = "\033[44m\033[97m"
BG_CYAN = "\033[46m\033[30m"

# Configuration Defaults
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORTS = [3306, 3308]
DEFAULT_USER = "root"
DEFAULT_PASSWORD = ""
DEFAULT_DB = "focuslens_db"
DEFAULT_SESSION_ID = 1
POLL_INTERVAL = 3.0  # seconds, matching dashboard refresh
STATE_DURATION_SECONDS = 300  # 5 minutes per state


class DatabaseManager:
    """Manages connection, schema initialization, and queries with MariaDB/MySQL."""

    def __init__(self, host: str, ports: list, user: str, password: str, database: str):
        self.host = host
        self.ports = ports
        self.user = user
        self.password = password
        self.database = database
        self.active_port: Optional[int] = None
        self.connection = None

    def connect(self) -> bool:
        """Attempts connection to MariaDB server across specified candidate ports."""
        errors = []
        for port in self.ports:
            try:
                # 1. Connect to MySQL server (without selecting DB first to ensure it exists)
                conn = mysql.connector.connect(
                    host=self.host,
                    port=port,
                    user=self.user,
                    password=self.password,
                    connect_timeout=3
                )
                cursor = conn.cursor()
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                cursor.close()
                conn.close()

                # 2. Connect directly to the target database
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    autocommit=True
                )
                self.active_port = port
                print(f"{GREEN}[OK] Connected to MariaDB/MySQL on {self.host}:{port} (Database: {self.database}){RESET}")
                return True
            except Exception as e:
                errors.append(f"Port {port}: {str(e).strip()}")

        print(f"{RED}[FAIL] Could not connect to MariaDB on host '{self.host}' (tried ports: {self.ports}){RESET}")
        for err in errors:
            print(f"  {DIM}-> {err}{RESET}")
        return False

    def is_connected(self) -> bool:
        """Verifies if the current connection is still alive."""
        if not self.connection:
            return False
        try:
            return self.connection.is_connected()
        except Exception:
            return False

    def reconnect(self, max_retries: int = 5, retry_delay: float = 3.0) -> bool:
        """Graceful reconnection loop when database drops or restarts."""
        print(f"{AMBER}[WARN] Database connection lost. Attempting to reconnect...{RESET}")
        for attempt in range(1, max_retries + 1):
            print(f"{DIM}[RETRY] Reconnection attempt {attempt}/{max_retries}...{RESET}")
            if self.connect():
                return True
            time.sleep(retry_delay)
        return False

    def initialize_schema(self):
        """Ensures focus_sessions and telemetry_logs tables exist with high performance indices."""
        cursor = self.connection.cursor()
        
        # Table 1: focus_sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS `focus_sessions` (
            `id` INT AUTO_INCREMENT PRIMARY KEY,
            `user_id` INT DEFAULT 1,
            `session_name` VARCHAR(100) DEFAULT 'Main Focus Session',
            `goal_seconds` INT DEFAULT 3600,
            `is_active` TINYINT(1) DEFAULT 1,
            `start_time` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            `end_time` TIMESTAMP NULL DEFAULT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)

        # Table 2: telemetry_logs
        cursor.execute("""
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
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """)
        cursor.close()

    def ensure_active_session(self, session_id: int = 1) -> bool:
        """
        Technical Requirement 1:
        Check if a session with ID = session_id exists in focus_sessions.
        If it doesn't, automatically insert a new active session row.
        """
        cursor = self.connection.cursor()
        cursor.execute("SELECT id, is_active FROM `focus_sessions` WHERE id = %s", (session_id,))
        row = cursor.fetchone()

        if row:
            # Session exists; ensure it's marked active
            if not row[1]:
                cursor.execute("UPDATE `focus_sessions` SET is_active = 1 WHERE id = %s", (session_id,))
            print(f"{CYAN}[SESSION] Found active session #{session_id} in 'focus_sessions'. Ready to stream.{RESET}")
        else:
            # Auto-insert active session with ID = 1
            cursor.execute("""
            INSERT INTO `focus_sessions` (id, user_id, session_name, goal_seconds, is_active, start_time)
            VALUES (%s, 1, 'FocusLens Session 1', 3600, 1, NOW())
            """, (session_id,))
            print(f"{GREEN}[SESSION] Session #{session_id} not found. Created new active session row successfully.{RESET}")

        cursor.close()
        return True

    def insert_telemetry(self, session_id: int, focus_score: int, fatigue_index: int, gaze_direction: str, is_distracted: int) -> int:
        """
        Technical Requirement 4:
        High-performance SQL INSERT query matching exact schema fields:
        session_id, focus_score, fatigue_index, gaze_direction, is_distracted
        """
        query = """
        INSERT INTO `telemetry_logs` (session_id, focus_score, fatigue_index, gaze_direction, is_distracted)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (session_id, focus_score, fatigue_index, gaze_direction, is_distracted))
        row_id = cursor.lastrowid
        cursor.close()
        return row_id

    def close(self):
        """Safely close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()


class OrganicTelemetrySimulator:
    """
    Data Science Simulation Model:
    Generates biologically plausible, smooth cognitive telemetry across 4 sequential 5-minute states.
    """

    STATES = [
        {"name": "State A: Deep Focus", "code": "A", "color": GREEN, "bg": BG_GREEN},
        {"name": "State B: Mild Fatigue", "code": "B", "color": AMBER, "bg": BG_AMBER},
        {"name": "State C: Distraction/Breach", "code": "C", "color": RED, "bg": BG_RED},
        {"name": "State D: Recovery/Post-Break", "code": "D", "color": CYAN, "bg": BG_CYAN},
    ]

    def __init__(self, state_duration_sec: float = 300, tick_interval_sec: float = 3.0):
        self.state_duration_sec = state_duration_sec
        self.tick_interval_sec = tick_interval_sec
        self.ticks_per_state = max(1, int(state_duration_sec / tick_interval_sec))

        self.current_state_idx = 0
        self.tick_in_state = 0
        self.global_tick = 0

        # Stateful continuous values for low-pass smooth transitions
        self.focus_score = 85.0
        self.fatigue_index = 12.0
        self.last_state_idx = -1

    def step(self) -> Dict[str, Any]:
        """
        Computes the next telemetry sample according to the active 5-minute cognitive state.
        Returns dictionary containing computed telemetry values.
        """
        # Determine current state based on duration ticks
        state_idx = (self.global_tick // self.ticks_per_state) % len(self.STATES)
        t_progress = (self.global_tick % self.ticks_per_state) / float(self.ticks_per_state)
        state_info = self.STATES[state_idx]

        is_new_state = (state_idx != self.last_state_idx)
        self.last_state_idx = state_idx

        # -------------------------------------------------------------
        # State A (Deep Focus):
        # - Focus Score fluctuates smoothly between 75-95.
        # - Fatigue Index climbs slowly from 10 to 25.
        # - Gaze fixed on 'Screen'.
        # - is_distracted = 0.
        # -------------------------------------------------------------
        if state_idx == 0:
            target_focus = 85.0 + 8.0 * math.sin(self.global_tick * 0.15) + random.uniform(-2.5, 2.5)
            target_focus = max(75.0, min(95.0, target_focus))
            # Smooth low-pass filter
            self.focus_score = 0.7 * self.focus_score + 0.3 * target_focus
            
            # Fatigue climbs slowly from 10 to 25 over the 5 minutes
            base_fatigue = 10.0 + (15.0 * t_progress)
            self.fatigue_index = max(10.0, min(25.0, base_fatigue + random.uniform(-0.6, 0.6)))
            
            gaze_direction = "Screen"
            is_distracted = 0

        # -------------------------------------------------------------
        # State B (Mild Fatigue):
        # - Focus Score decays between 50-70.
        # - Fatigue Index jumps to 40-55.
        # - Gaze shifts occasionally to 'Left' or 'Right'.
        # - is_distracted = 0.
        # -------------------------------------------------------------
        elif state_idx == 1:
            # Gradual decay from 70 down towards 50
            decay_curve = 68.0 - (16.0 * t_progress) + 4.0 * math.sin(self.global_tick * 0.2)
            target_focus = max(50.0, min(70.0, decay_curve + random.uniform(-2.0, 2.0)))
            self.focus_score = 0.75 * self.focus_score + 0.25 * target_focus
            
            # Fatigue elevated into 40-55 range
            target_fatigue = 40.0 + (13.0 * t_progress) + random.uniform(-1.5, 1.5)
            self.fatigue_index = 0.8 * self.fatigue_index + 0.2 * max(40.0, min(55.0, target_fatigue))
            
            # Gaze shifts occasionally
            rnd = random.random()
            if rnd < 0.72:
                gaze_direction = "Screen"
            elif rnd < 0.86:
                gaze_direction = "Left"
            else:
                gaze_direction = "Right"
            is_distracted = 0

        # -------------------------------------------------------------
        # State C (Distraction / Breach):
        # - Focus Score plummets below the threshold (between 25-38).
        # - Fatigue Index hits 65-80.
        # - Gaze points 'Away'.
        # - is_distracted = 1.
        # -------------------------------------------------------------
        elif state_idx == 2:
            # Rapid drop under threshold (threshold is 40 in dashboard)
            target_focus = 31.0 + 5.0 * math.sin(self.global_tick * 0.25) + random.uniform(-2.0, 2.0)
            target_focus = max(25.0, min(38.0, target_focus))
            self.focus_score = 0.65 * self.focus_score + 0.35 * target_focus
            
            # Fatigue peaks at 65-80
            target_fatigue = 65.0 + (13.0 * t_progress) + random.uniform(-2.0, 2.0)
            self.fatigue_index = 0.75 * self.fatigue_index + 0.25 * max(65.0, min(80.0, target_fatigue))
            
            # Gaze points 'Away' predominantly
            rnd = random.random()
            if rnd < 0.82:
                gaze_direction = "Away"
            elif rnd < 0.91:
                gaze_direction = "Left"
            else:
                gaze_direction = "Right"
            is_distracted = 1

        # -------------------------------------------------------------
        # State D (Recovery / Post-Break):
        # - Focus Score rebounds smoothly back to 80-90.
        # - Fatigue Index resets to fresh 15-20 range.
        # - Gaze returns to 'Screen'.
        # - is_distracted = 0.
        # -------------------------------------------------------------
        else:
            # Rebound back to 80-90
            target_focus = 84.0 + 4.0 * math.sin(self.global_tick * 0.18) + random.uniform(-2.0, 2.0)
            target_focus = max(80.0, min(90.0, target_focus))
            self.focus_score = 0.7 * self.focus_score + 0.3 * target_focus
            
            # Fatigue resets to 15-20
            target_fatigue = 15.0 + (5.0 * t_progress) + random.uniform(-1.0, 1.0)
            self.fatigue_index = 0.7 * self.fatigue_index + 0.3 * max(15.0, min(20.0, target_fatigue))
            
            gaze_direction = "Screen"
            is_distracted = 0

        self.global_tick += 1
        self.tick_in_state = (self.tick_in_state + 1) % self.ticks_per_state

        return {
            "state_info": state_info,
            "state_idx": state_idx,
            "is_new_state": is_new_state,
            "progress_pct": int(t_progress * 100),
            "focus_score": int(round(self.focus_score)),
            "fatigue_index": int(round(self.fatigue_index)),
            "gaze_direction": gaze_direction,
            "is_distracted": is_distracted
        }


def print_banner(host: str, port: int, db: str, session_id: int, interval: float, state_dur: float):
    """Displays a clean launch banner in the console."""
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}{WHITE}   FocusLens — Real-Time Telemetry Simulation Engine (MariaDB/MySQL){RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}")
    print(f" {DIM}Database Target :{RESET} {WHITE}{host}:{port} / {db}{RESET}")
    print(f" {DIM}Active Session  :{RESET} {WHITE}Session ID #{session_id}{RESET}")
    print(f" {DIM}Refresh Cadence :{RESET} {WHITE}Every {interval:.1f}s (synchronized with dashboard){RESET}")
    print(f" {DIM}Cognitive Cycle :{RESET} {WHITE}4 x {state_dur/60:.1f}-minute states (Total: {(state_dur*4)/60:.0f} min/cycle){RESET}")
    print(f" {DIM}Simulation Logic:{RESET} {GREEN}A (Deep Focus){RESET} -> {AMBER}B (Mild Fatigue){RESET} -> {RED}C (Breach){RESET} -> {CYAN}D (Recovery){RESET}")
    print(f"{CYAN}-------------------------------------------------------------------------{RESET}\n")


def print_state_transition(state_info: dict, dur_sec: float):
    """Displays an eye-catching header when switching cognitive states."""
    name = state_info["name"]
    color = state_info["color"]
    bg = state_info["bg"]
    print(f"\n{bg}  TRANSITION >>> {name.upper()}  {RESET} {color}(Duration: {dur_sec/60:.1f}m){RESET}")
    print(f"{color}{'-' * 60}{RESET}")


def format_log_line(sample: dict, row_id: int) -> str:
    """
    Technical Requirement 5:
    Print clean, color-coded diagnostic strings directly into terminal:
    e.g. "[LOG] Focus: 85% | Fatigue: 20 | Gaze: Screen -> Inserted Successfully"
    """
    f_score = sample["focus_score"]
    fatigue = sample["fatigue_index"]
    gaze = sample["gaze_direction"]
    distracted = sample["is_distracted"]
    state = sample["state_info"]["name"].split(":")[1].strip()

    # Colorize metrics
    if f_score >= 70:
        f_str = f"{GREEN}{f_score:>2}%{RESET}"
    elif f_score >= 40:
        f_str = f"{AMBER}{f_score:>2}%{RESET}"
    else:
        f_str = f"{RED}{f_score:>2}%{RESET}"

    if fatigue < 35:
        fat_str = f"{GREEN}{fatigue:>2}{RESET}"
    elif fatigue < 60:
        fat_str = f"{AMBER}{fatigue:>2}{RESET}"
    else:
        fat_str = f"{RED}{fatigue:>2}{RESET}"

    gaze_color = GREEN if gaze == "Screen" else AMBER if gaze in ("Left", "Right") else RED
    g_str = f"{gaze_color}{gaze:<6}{RESET}"

    dist_str = f"{RED}YES{RESET}" if distracted else f"{DIM}No{RESET}"

    now = datetime.now().strftime("%H:%M:%S")
    return (
        f"{DIM}[{now}]{RESET} "
        f"{BOLD}[LOG]{RESET} "
        f"State: {WHITE}{state:<14}{RESET} | "
        f"Focus: {f_str} | "
        f"Fatigue: {fat_str} | "
        f"Gaze: {g_str} | "
        f"Distracted: {dist_str} -> "
        f"{GREEN}Inserted Successfully (id: {row_id}){RESET}"
    )


def main():
    # Ensure immediate flushing across Windows terminals and pipes
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(description="FocusLens MariaDB Telemetry Simulator")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"MariaDB host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=None, help="Explicit port (e.g. 3306 or 3308). Default probes both.")
    parser.add_argument("--user", default=DEFAULT_USER, help=f"Database user (default: {DEFAULT_USER})")
    parser.add_argument("--password", default=DEFAULT_PASSWORD, help="Database password (default: empty)")
    parser.add_argument("--database", default=DEFAULT_DB, help=f"Database name (default: {DEFAULT_DB})")
    parser.add_argument("--session-id", type=int, default=DEFAULT_SESSION_ID, help=f"Session ID (default: {DEFAULT_SESSION_ID})")
    parser.add_argument("--interval", type=float, default=POLL_INTERVAL, help=f"Seconds between telemetry ticks (default: {POLL_INTERVAL}s)")
    parser.add_argument("--state-duration", type=float, default=STATE_DURATION_SECONDS, help=f"Seconds per cognitive state (default: {STATE_DURATION_SECONDS}s = 5 min)")
    parser.add_argument("--fast", action="store_true", help="Demo fast-forward mode (10s per state, 1s tick)")

    args = parser.parse_args()

    interval = 1.0 if args.fast else args.interval
    state_dur = 10.0 if args.fast else args.state_duration

    candidate_ports = [args.port] if args.port else DEFAULT_PORTS

    # Step 1: Establish Database Connection
    db = DatabaseManager(
        host=args.host,
        ports=candidate_ports,
        user=args.user,
        password=args.password,
        database=args.database
    )

    if not db.connect():
        print(f"\n{RED}{BOLD}[FATAL] Could not establish connection with MariaDB/MySQL.{RESET}")
        print(f"{AMBER}Troubleshooting Check:{RESET}")
        print("  1. Is XAMPP / MariaDB running? Start MySQL/MariaDB from XAMPP Control Panel or Windows Services.")
        print("  2. Verify your port (configured to try 3306 and 3308).")
        print("  3. Run script with custom port if needed: python simulate_telemetry.py --port 3306")
        sys.exit(1)

    # Step 2: Initialize Schema and Verify Active Session (Requirement 1)
    try:
        db.initialize_schema()
        db.ensure_active_session(session_id=args.session_id)
    except Exception as e:
        print(f"{RED}[ERROR] Schema or session check failed: {e}{RESET}")
        db.close()
        sys.exit(1)

    print_banner(args.host, db.active_port, args.database, args.session_id, interval, state_dur)

    # Step 3: Initialize Simulation Engine (Requirements 2 & 3)
    simulator = OrganicTelemetrySimulator(
        state_duration_sec=state_dur,
        tick_interval_sec=interval
    )

    # Step 4: Infinite Telemetry Execution Loop (Requirement 2)
    print(f"{GREEN}[RUNNING] Real-time telemetry generator started. Press Ctrl+C to terminate cleanly.{RESET}\n")

    try:
        while True:
            # Advance simulation step
            sample = simulator.step()

            if sample["is_new_state"]:
                print_state_transition(sample["state_info"], state_dur)

            # Insert sample into MariaDB (Requirement 4)
            try:
                row_id = db.insert_telemetry(
                    session_id=args.session_id,
                    focus_score=sample["focus_score"],
                    fatigue_index=sample["fatigue_index"],
                    gaze_direction=sample["gaze_direction"],
                    is_distracted=sample["is_distracted"]
                )
                # Print clean color-coded diagnostic string (Requirement 5)
                log_line = format_log_line(sample, row_id)
                print(log_line)

            except Exception as insert_err:
                print(f"{RED}[INSERT ERROR] Failed to insert telemetry row: {insert_err}{RESET}")
                # Check connection and attempt auto-reconnect
                if not db.is_connected():
                    reconnected = db.reconnect()
                    if not reconnected:
                        print(f"{RED}[FATAL] Database connection could not be recovered. Pausing 10s...{RESET}")
                        time.sleep(10)

            # Cadence sleep matching dashboard refresh
            time.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n{AMBER}[SHUTDOWN] Terminating simulation loop gracefully (received Ctrl+C)...{RESET}")
    finally:
        db.close()
        print(f"{GREEN}[EXIT] Database connection closed cleanly. Goodbye!{RESET}")


if __name__ == "__main__":
    main()
