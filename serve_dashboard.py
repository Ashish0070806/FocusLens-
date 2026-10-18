"""
FocusLens - Python Dashboard Server
Serves index.html and provides /get_dashboard_data.php and /save_telemetry.php
endpoints backed directly by the MariaDB database without needing Apache/PHP.
"""

import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime
import mysql.connector

HOST = "127.0.0.1"
PORT = 8000
DB_HOST = "127.0.0.1"
DB_PORTS = [3306, 3308]
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "focuslens_db"
SESSION_ID = 1


def get_db_connection():
    for p in DB_PORTS:
        try:
            conn = mysql.connector.connect(
                host=DB_HOST,
                port=p,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME,
                connect_timeout=2
            )
            return conn
        except Exception:
            continue
    return None


class FocusLensHandler(SimpleHTTPRequestHandler):

    def do_GET(self):
        # Route: get_dashboard_data.php
        if self.path.startswith("/get_dashboard_data.php"):
            self.handle_get_dashboard_data()
            return

        # Default: serve index.html or other static files
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        # Route: save_telemetry.php
        if self.path.startswith("/save_telemetry.php"):
            self.handle_save_telemetry()
            return
        self.send_error(404, "Endpoint not found")

    def handle_get_dashboard_data(self):
        conn = get_db_connection()
        if not conn:
            self.send_response(503)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Database unavailable"}).encode("utf-8"))
            return

        try:
            cur = conn.cursor(dictionary=True)

            # 1. Latest telemetry
            cur.execute("""
                SELECT focus_score, fatigue_index, gaze_direction, is_distracted, created_at
                FROM telemetry_logs
                WHERE session_id = %s
                ORDER BY id DESC
                LIMIT 1
            """, (SESSION_ID,))
            latest = cur.fetchone()

            if not latest:
                payload = {
                    "focus_score": 85,
                    "fatigue": 15,
                    "focus_seconds": 0,
                    "distractions": 0,
                    "timeline": []
                }
            else:
                # 2. Last 40 timeline points
                cur.execute("""
                    SELECT created_at, focus_score, fatigue_index
                    FROM telemetry_logs
                    WHERE session_id = %s
                    ORDER BY id DESC
                    LIMIT 40
                """, (SESSION_ID,))
                timeline_rows = cur.fetchall()
                timeline_rows.reverse()

                timeline = [
                    {
                        "time": row["created_at"].strftime("%H:%M:%S") if isinstance(row["created_at"], datetime) else str(row["created_at"]),
                        "score": int(row["focus_score"]),
                        "fatigue": int(row["fatigue_index"])
                    }
                    for row in timeline_rows
                ]

                # 3. Focus seconds (score >= 50)
                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM telemetry_logs
                    WHERE session_id = %s AND focus_score >= 50
                """, (SESSION_ID,))
                focus_seconds = cur.fetchone()["c"] * 3

                # 4. Distractions count
                cur.execute("""
                    SELECT COUNT(*) AS c
                    FROM telemetry_logs
                    WHERE session_id = %s AND is_distracted = 1
                """, (SESSION_ID,))
                distractions = cur.fetchone()["c"]

                payload = {
                    "focus_score": int(latest["focus_score"]),
                    "fatigue": int(latest["fatigue_index"]),
                    "focus_seconds": int(focus_seconds),
                    "distractions": int(distractions),
                    "timeline": timeline
                }

            cur.close()
            conn.close()

            data_bytes = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data_bytes)))
            self.end_headers()
            self.wfile.write(data_bytes)

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

    def handle_save_telemetry(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            data = json.loads(body.decode("utf-8"))
            event = data.get("event", "sample")
            score = data.get("focus_score", 70)
            fatigue = data.get("fatigue", 20)
            is_distracted = 1 if (event == "breach" or score < 40) else 0
            gaze = "Away" if is_distracted else "Screen"

            if event in ("breach", "break_start", "break_end"):
                conn = get_db_connection()
                if conn:
                    cur = conn.cursor()
                    cur.execute("""
                        INSERT INTO telemetry_logs (session_id, focus_score, fatigue_index, gaze_direction, is_distracted)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (SESSION_ID, score, fatigue, gaze, is_distracted))
                    conn.commit()
                    cur.close()
                    conn.close()

            res = json.dumps({"status": "success", "event": event}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(res)))
            self.end_headers()
            self.wfile.write(res)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def run():
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    server_address = (HOST, PORT)
    httpd = HTTPServer(server_address, FocusLensHandler)
    print(f"\033[92m[FocusLens Web Server] Serving on http://{HOST}:{PORT}/index.html\033[0m")
    print(f"\033[96mPress Ctrl+C to stop the server.\033[0m\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[93m[Server] Stopped cleanly.\033[0m")
        httpd.server_close()


if __name__ == "__main__":
    run()
