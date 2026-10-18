"""
FocusLens - Real-Time Webcam Telemetry Ingestion Engine
Powered by OpenCV YuNet Deep Neural Network Face & Landmark Detector.

Calibrated specifically for laptop webcam setups:
- Personalized 1-Key Neutral Calibration (Press 'c' anytime to calibrate to your screen)
- Exponential Moving Average (EMA) Landmark Filtering eliminates glasses jitter
- Generous natural desk/laptop viewing cone (no false distraction while facing screen)
- 3-second distraction debouncing: momentary glances never trigger alarms
- Real-time on-screen HUD with calibration status and focus zones
"""

import os
import sys
import time
import math
import urllib.request
from datetime import datetime
import cv2
import numpy as np

# Ensure stdout flushes immediately
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)

# Database Connection
try:
    import mysql.connector
except ImportError:
    print("\033[91m[ERROR] mysql-connector-python is required.\033[0m")
    sys.exit(1)

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
GREEN = "\033[92m"
AMBER = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
WHITE = "\033[97m"

# Configuration
DB_HOST = "127.0.0.1"
DB_PORTS = [3306, 3308]
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "focuslens_db"
SESSION_ID = 1
POLL_INTERVAL = 3.0  # seconds between database commits

YUNET_MODEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_detection_yunet_2023mar.onnx")
YUNET_URL = "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx"


def ensure_model():
    """Download the official lightweight (330 KB) OpenCV YuNet model if missing."""
    if not os.path.exists(YUNET_MODEL_FILE):
        print(f"{CYAN}[AI MODEL] Downloading OpenCV YuNet Deep Learning Model (330 KB)...{RESET}")
        try:
            urllib.request.urlretrieve(YUNET_URL, YUNET_MODEL_FILE)
            print(f"{GREEN}[AI MODEL] Download complete! Model saved to {YUNET_MODEL_FILE}{RESET}")
        except Exception as e:
            print(f"{RED}[ERROR] Failed to download model: {e}{RESET}")
            sys.exit(1)


def connect_database():
    """Connect to MariaDB across candidate ports (3306 / 3308)."""
    for port in DB_PORTS:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=port,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                autocommit=True,
                connect_timeout=2
            )
            print(f"{GREEN}[OK] Connected to MariaDB on {DB_HOST}:{port} (Database: {DB_NAME}){RESET}")
            return conn, port
        except Exception:
            continue
    return None, None


def ensure_session(conn, session_id=1):
    """Ensure active session row exists in focus_sessions."""
    cur = conn.cursor()
    cur.execute("SELECT id, is_active FROM focus_sessions WHERE id = %s", (session_id,))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO focus_sessions (id, user_id, session_name, goal_seconds, is_active, start_time)
            VALUES (%s, 1, 'Webcam Live Session', 3600, 1, NOW())
        """, (session_id,))
        print(f"{GREEN}[SESSION] Created active session #{session_id} for live webcam feed.{RESET}")
    else:
        cur.execute("UPDATE focus_sessions SET is_active = 1 WHERE id = %s", (session_id,))
        print(f"{CYAN}[SESSION] Found active session #{session_id}. Ready for live stream.{RESET}")
    cur.close()


def main():
    print(f"\n{BOLD}{CYAN}========================================================================={RESET}")
    print(f"{BOLD}{WHITE}   FocusLens — Deep Learning AI Webcam Monitor (YuNet Face & Gaze){RESET}")
    print(f"{BOLD}{CYAN}========================================================================={RESET}\n")

    conn, active_port = connect_database()
    if not conn:
        print(f"{RED}[FATAL] Could not connect to MariaDB on ports {DB_PORTS}. Is MariaDB running?{RESET}")
        sys.exit(1)

    ensure_session(conn, SESSION_ID)
    ensure_model()

    print(f"{CYAN}[WEBCAM] Opening laptop camera (Index 0)...{RESET}")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print(f"{RED}[ERROR] Could not access webcam. Ensure no other application (Zoom, Teams) is using it.{RESET}")
        conn.close()
        sys.exit(1)

    frame_w = 640
    frame_h = 480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frame_w)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_h)

    detector = cv2.FaceDetectorYN.create(
        model=YUNET_MODEL_FILE,
        config="",
        input_size=(frame_w, frame_h),
        score_threshold=0.45,
        nms_threshold=0.3,
        top_k=5000
    )
    print(f"{GREEN}[AI ENGINE] YuNet Neural Network initialized successfully!{RESET}")
    print(f"{CYAN}[TIP] Look comfortably at your screen and press 'c' anytime to auto-calibrate.{RESET}")
    print(f"{AMBER}Controls: Press 'q' or 'ESC' to exit | Press 'c' to recalibrate neutral gaze.{RESET}\n")

    # Personal Calibration Offsets (Initialized to standard defaults)
    calibrated_yaw = 0.05
    calibrated_vert = 1.15
    is_calibrating = False
    calib_samples = []

    # Filtered smoothed metrics (EMA)
    smooth_yaw = 0.05
    smooth_vert = 1.15

    # Telemetry State Variables
    focus_score = 88.0
    fatigue_index = 15.0
    distraction_timer_start = None
    gaze_direction = "Screen"
    is_distracted = 0
    last_db_commit = time.time()

    fps_start_time = time.time()
    fps_counter = 0
    fps = 30.0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            print(f"{RED}[WARN] Failed to read frame from webcam.{RESET}")
            break

        # Flip horizontally for natural mirror feel
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        detector.setInputSize((w, h))
        _, faces = detector.detect(frame)

        face_detected = False

        if faces is not None and len(faces) > 0:
            faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
            primary_face = faces[0]
            conf = float(primary_face[14])

            if conf >= 0.40:
                face_detected = True

                fx, fy, fw, fh = int(primary_face[0]), int(primary_face[1]), int(primary_face[2]), int(primary_face[3])
                fx = max(0, fx)
                fy = max(0, fy)
                fw = min(w - fx, fw)
                fh = min(h - fy, fh)

                right_eye = (float(primary_face[4]), float(primary_face[5]))
                left_eye = (float(primary_face[6]), float(primary_face[7]))
                nose_tip = (float(primary_face[8]), float(primary_face[9]))
                right_mouth = (float(primary_face[10]), float(primary_face[11]))
                left_mouth = (float(primary_face[12]), float(primary_face[13]))

                # Eye and mouth midpoints
                eye_mid_x = (right_eye[0] + left_eye[0]) / 2.0
                eye_mid_y = (right_eye[1] + left_eye[1]) / 2.0
                mouth_mid_y = (right_mouth[1] + left_mouth[1]) / 2.0

                eye_dist = max(1.0, abs(left_eye[0] - right_eye[0]))
                raw_yaw = (nose_tip[0] - eye_mid_x) / eye_dist

                nose_eye_y = nose_tip[1] - eye_mid_y
                mouth_nose_y = max(1.0, mouth_mid_y - nose_tip[1])
                raw_vert = nose_eye_y / mouth_nose_y

                # Exponential Smoothing (EMA) to eliminate noise & glasses reflections
                smooth_yaw = 0.75 * smooth_yaw + 0.25 * raw_yaw
                smooth_vert = 0.75 * smooth_vert + 0.25 * raw_vert

                # Auto-calibration collection
                if is_calibrating:
                    calib_samples.append((raw_yaw, raw_vert))
                    if len(calib_samples) >= 20:  # ~0.6 seconds of data
                        calibrated_yaw = float(np.median([s[0] for s in calib_samples]))
                        calibrated_vert = float(np.median([s[1] for s in calib_samples]))
                        is_calibrating = False
                        calib_samples = []
                        print(f"{GREEN}[CALIBRATION] Neutral screen gaze saved! (Yaw: {calibrated_yaw:.2f}, Vert: {calibrated_vert:.2f}){RESET}")

                # Compute deviation from personalized neutral screen gaze
                delta_yaw = smooth_yaw - calibrated_yaw
                delta_vert = smooth_vert - calibrated_vert

                # Generous natural focus cone for desktop/laptop work
                # Looking Left or Right requires distinct intentional head rotation (> 0.28)
                if delta_yaw < -0.30:
                    gaze_direction = "Right"
                elif delta_yaw > 0.30:
                    gaze_direction = "Left"
                elif delta_vert > 0.70 or delta_vert < -0.65:
                    gaze_direction = "Away"
                else:
                    gaze_direction = "Screen"

                # Distraction Debounce Logic:
                # Requires at least 2.5 consecutive seconds looking away before marking distracted
                if gaze_direction != "Screen":
                    if distraction_timer_start is None:
                        distraction_timer_start = time.time()
                    elif time.time() - distraction_timer_start >= 2.5:
                        is_distracted = 1
                        focus_score = max(20.0, focus_score - 0.7)
                else:
                    distraction_timer_start = None
                    is_distracted = 0
                    focus_score = min(98.0, focus_score + 0.4)
                    fatigue_index = max(10.0, fatigue_index - 0.05)

                # Visual Landmarks on Frame
                box_color = (76, 175, 80) if gaze_direction == "Screen" else (7, 193, 255) if gaze_direction in ("Left", "Right") else (77, 72, 229)
                cv2.rectangle(frame, (fx, fy), (fx + fw, fy + fh), box_color, 2)

                # Landmark dots
                cv2.circle(frame, (int(right_eye[0]), int(right_eye[1])), 4, (0, 255, 255), -1)
                cv2.circle(frame, (int(left_eye[0]), int(left_eye[1])), 4, (0, 255, 255), -1)
                cv2.circle(frame, (int(nose_tip[0]), int(nose_tip[1])), 5, (0, 200, 255), -1)
                cv2.circle(frame, (int(right_mouth[0]), int(right_mouth[1])), 3, (255, 100, 255), -1)
                cv2.circle(frame, (int(left_mouth[0]), int(left_mouth[1])), 3, (255, 100, 255), -1)

                cv2.putText(frame, f"Gaze: {gaze_direction}", (fx, max(20, fy - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, box_color, 2)

        if not face_detected:
            # Face not visible -> Looking completely away or stepped out
            if distraction_timer_start is None:
                distraction_timer_start = time.time()
            elif time.time() - distraction_timer_start >= 2.0:
                gaze_direction = "Away"
                is_distracted = 1
                focus_score = max(15.0, focus_score - 1.2)
                fatigue_index = min(95.0, fatigue_index + 0.2)

        # -------------------------------------------------------------
        # Periodic Commit to MariaDB Every 3 Seconds
        # -------------------------------------------------------------
        now = time.time()
        if now - last_db_commit >= POLL_INTERVAL:
            try:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO telemetry_logs (session_id, focus_score, fatigue_index, gaze_direction, is_distracted)
                    VALUES (%s, %s, %s, %s, %s)
                """, (SESSION_ID, int(round(focus_score)), int(round(fatigue_index)), gaze_direction, is_distracted))
                row_id = cur.lastrowid
                cur.close()

                ts = datetime.now().strftime("%H:%M:%S")
                f_color = GREEN if focus_score >= 70 else AMBER if focus_score >= 40 else RED
                g_color = GREEN if gaze_direction == "Screen" else AMBER if gaze_direction in ("Left", "Right") else RED
                dist_str = f"{RED}YES{RESET}" if is_distracted else f"{DIM}No{RESET}"

                print(
                    f"{DIM}[{ts}]{RESET} {BOLD}[LIVE CAM]{RESET} "
                    f"Focus: {f_color}{int(focus_score):>2}%{RESET} | "
                    f"Fatigue: {AMBER}{int(fatigue_index):>2}{RESET} | "
                    f"Gaze: {g_color}{gaze_direction:<6}{RESET} | "
                    f"Distracted: {dist_str} -> "
                    f"{GREEN}Committed (id: {row_id}){RESET}"
                )
            except Exception as e:
                print(f"{RED}[DB ERROR] Failed to insert telemetry: {e}{RESET}")

            last_db_commit = now

        # FPS
        fps_counter += 1
        if time.time() - fps_start_time >= 1.0:
            fps = fps_counter
            fps_counter = 0
            fps_start_time = time.time()

        # -------------------------------------------------------------
        # On-Screen HUD Overlay
        # -------------------------------------------------------------
        cv2.rectangle(frame, (0, 0), (w, 65), (13, 27, 42), -1)
        cv2.putText(frame, "FocusLens AI Vision (Calibrated YuNet)", (15, 24), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        f_hud = (76, 175, 80) if focus_score >= 70 else (7, 193, 255) if focus_score >= 40 else (77, 72, 229)
        cv2.putText(frame, f"Focus: {int(focus_score)}%", (15, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.65, f_hud, 2)
        cv2.putText(frame, f"Fatigue: {int(fatigue_index)}", (175, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 193, 7), 2)
        cv2.putText(frame, f"Gaze: {gaze_direction}", (335, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        if is_distracted:
            cv2.rectangle(frame, (w - 170, 12), (w - 10, 52), (0, 0, 200), -1)
            cv2.putText(frame, "! DISTRACTED", (w - 160, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)

        if is_calibrating:
            cv2.rectangle(frame, (w // 2 - 160, h // 2 - 25), (w // 2 + 160, h // 2 + 25), (0, 140, 255), -1)
            cv2.putText(frame, "Calibrating Screen Gaze...", (w // 2 - 145, h // 2 + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)

        cv2.putText(frame, "Press 'c' to Calibrate to your screen | Press 'q' to exit", (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("FocusLens - Live Laptop Webcam Monitor", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') or key == ord('C'):
            is_calibrating = True
            calib_samples = []
            print(f"{CYAN}[CALIBRATION] Calibrating neutral gaze... Keep looking at screen!{RESET}")
        elif key == ord('q') or key == 27:
            print(f"\n{AMBER}[SHUTDOWN] Stopping webcam monitoring...{RESET}")
            break

    cap.release()
    cv2.destroyAllWindows()
    conn.close()
    print(f"{GREEN}[EXIT] Webcam stream stopped cleanly.{RESET}")


if __name__ == "__main__":
    main()
