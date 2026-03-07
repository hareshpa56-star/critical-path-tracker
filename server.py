"""
Critical Path Tracker Server
Local:  python server.py
Cloud:  Set DATABASE_URL env var for persistent Postgres storage
Auth:   Set APP_PASSWORD env var to require login (optional)
"""
import http.server
import json
import os
import threading
import hashlib
import secrets
import time
from datetime import datetime

PORT = int(os.environ.get('PORT', 8080))
DATABASE_URL = os.environ.get('DATABASE_URL', '')
APP_PASSWORD = os.environ.get('APP_PASSWORD', '')
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'critical_path_data.json')
LOCK = threading.Lock()

# Simple token store: token -> expiry timestamp
TOKENS = {}
TOKEN_LIFETIME = 86400 * 7  # 7 days


def generate_token():
    token = secrets.token_hex(32)
    TOKENS[token] = time.time() + TOKEN_LIFETIME
    return token


def is_valid_token(token):
    if not token:
        return False
    expiry = TOKENS.get(token)
    if not expiry:
        return False
    if time.time() > expiry:
        del TOKENS[token]
        return False
    return True


def check_auth(handler):
    """Returns True if request is authorized. If APP_PASSWORD is not set, always returns True."""
    if not APP_PASSWORD:
        return True
    token = handler.headers.get('X-Auth-Token', '')
    return is_valid_token(token)


# ── Storage: Postgres if DATABASE_URL is set, otherwise local JSON file ──

def init_db():
    if not DATABASE_URL:
        return
    import psycopg2
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_data (
            id INTEGER PRIMARY KEY DEFAULT 1,
            tasks JSONB NOT NULL DEFAULT '[]'::jsonb
        )
    """)
    cur.execute("INSERT INTO app_data (id, tasks) VALUES (1, '[]') ON CONFLICT (id) DO NOTHING")
    conn.commit()
    cur.close()
    conn.close()


def load_data():
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT tasks FROM app_data WHERE id = 1")
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row[0] if row else []
    else:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []


def save_data(data):
    if DATABASE_URL:
        import psycopg2
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("UPDATE app_data SET tasks = %s WHERE id = 1", [json.dumps(data)])
        conn.commit()
        cur.close()
        conn.close()
    else:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def send_unauthorized(self):
        self.send_json(401, {"error": "Unauthorized"})

    def do_GET(self):
        if self.path == '/':
            self.path = '/critical_path.html'
            return super().do_GET()
        elif self.path == '/api/auth-required':
            self.send_json(200, {"required": bool(APP_PASSWORD)})
        elif self.path == '/api/tasks':
            if not check_auth(self):
                return self.send_unauthorized()
            with LOCK:
                data = load_data()
            self.send_json(200, data)
        else:
            return super().do_GET()

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)

        if self.path == '/api/login':
            try:
                payload = json.loads(body)
                password = payload.get('password', '')
                if password == APP_PASSWORD:
                    token = generate_token()
                    self.send_json(200, {"ok": True, "token": token})
                else:
                    self.send_json(403, {"ok": False, "error": "Wrong password"})
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Invalid JSON"})

        elif self.path == '/api/tasks':
            if not check_auth(self):
                return self.send_unauthorized()
            try:
                tasks = json.loads(body)
                with LOCK:
                    save_data(tasks)
                self.send_json(200, {"ok": True})
            except json.JSONDecodeError:
                self.send_json(400, {"error": "Invalid JSON"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Auth-Token')
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")


if __name__ == '__main__':
    import socket

    if DATABASE_URL:
        init_db()
        print("Storage: PostgreSQL (persistent)")
    else:
        if not os.path.exists(DATA_FILE):
            print("No data file found. It will be created on first save.")
        print(f"Storage: Local file ({DATA_FILE})")

    if APP_PASSWORD:
        print(f"Auth:    Password required (set via APP_PASSWORD)")
    else:
        print(f"Auth:    None (open access)")

    hostname = socket.gethostname()
    try:
        local_ip = socket.gethostbyname(hostname)
    except socket.gaierror:
        local_ip = 'unknown'

    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    print(f"Critical Path Tracker running!")
    print(f"  Local:   http://localhost:{PORT}")
    if local_ip != 'unknown':
        print(f"  Network: http://{local_ip}:{PORT}")
    print(f"  Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()
