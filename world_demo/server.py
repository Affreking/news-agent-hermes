"""WELISPEAK local-only demonstration. No SMTP, outbound HTTP or payment SDK."""
import argparse
import json
import mimetypes
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import sqlite3
import tempfile
import time
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
REGISTRY = json.loads((ROOT / 'destinations.json').read_text())
ALL = [REGISTRY['base']] + REGISTRY['destinations']
VALID = {d['code'] for d in ALL}


def verify_future_payment_webhook(payload, headers):
    """Future authentic provider integration MUST verify signature/replay/idempotency.

    Deliberately fail closed. This hook cannot grant entitlements in this demo.
    """
    return False


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Never log request data, contact information or session identifiers.

    def reply(self, status, value, content_type='application/json; charset=utf-8'):
        body = json.dumps(value, ensure_ascii=False).encode() if isinstance(value, (dict, list)) else value
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if getattr(self, 'new_cookie', None):
            self.send_header('Set-Cookie', f'world_session={self.new_cookie}; HttpOnly; SameSite=Strict; Path=/; Max-Age=86400')
        self.end_headers()
        self.wfile.write(body)

    def allowed_host(self):
        return self.headers.get('Host', '') in {
            f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}

    def session(self):
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
        except Exception:
            pass
        sid = cookie['world_session'].value if 'world_session' in cookie else ''
        with sqlite3.connect(self.server.db_path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute('SELECT * FROM sessions WHERE sid=? AND expires>?', (sid, time.time())).fetchone()
            if row is None:
                sid, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                db.execute('DELETE FROM sessions WHERE expires<=?', (time.time(),))
                db.execute('INSERT INTO sessions VALUES(?,?,?,?,?,?,?,?)',
                           (sid, csrf, 0, 0, 0, 'fr', '["CI"]', time.time() + 86400))
                row = db.execute('SELECT * FROM sessions WHERE sid=?', (sid,)).fetchone()
                self.new_cookie = sid
        return dict(row)

    def session_view(self, row):
        return {k: bool(row[k]) for k in ('paid', 'registered', 'discover_world')} | {
            'csrf': row['csrf'], 'language': row['language'],
            'destinations': json.loads(row['destinations']), 'demo_enabled': self.server.demo_enabled}

    def do_GET(self):
        if not self.allowed_host():
            return self.reply(403, {'error': 'Local Host required'})
        path = urlsplit(self.path).path
        row = self.session()
        if path == '/api/session':
            return self.reply(200, self.session_view(row))
        if path == '/api/overview':
            return self.reply(200, REGISTRY)
        if path == '/api/ci':
            return self.reply(200, json.loads((ROOT / 'archive_20261022.json').read_text()))
        if path == '/api/catalogue':
            if not row['paid']:
                return self.reply(403, {'error': 'Édition Monde entitlement required / Accès Monde requis'})
            editions = [d | {'demonstration': True, 'content_fr': 'Démonstration de structure uniquement. Aucun article, fait récent ou source attribuée pour cette destination.',
                              'content_en': 'Structure demonstration only. No article, recent factual claim or attributed source for this destination.'} for d in ALL]
            return self.reply(200, {'editions': editions})
        files = {'/': 'index.html', '/index.html': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css', '/mailMonde.eml': 'mailMonde.eml'}
        if path.startswith('/assets/') and path[8:] in {'logo.png', 'editorial-1.png', 'editorial-2.png', 'editorial-3.png', 'editorial-4.png', 'editorial-5.png', 'editorial-6.png'}:
            files[path] = path[1:]
        if path in files and (ROOT / files[path]).is_file():
            target = ROOT / files[path]
            mime = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
            return self.reply(200, target.read_bytes(), mime + ('; charset=utf-8' if mime.startswith('text/') else ''))
        return self.reply(404, {'error': 'Not found'})

    def do_POST(self):
        if not self.allowed_host():
            return self.reply(403, {'error': 'Local Host required'})
        origin = self.headers.get('Origin')
        if origin and origin not in {f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}'}:
            return self.reply(403, {'error': 'Cross-origin request rejected'})
        path = urlsplit(self.path).path
        if path == '/api/webhook':
            return self.reply(501, {'error': 'Unconfigured authentic payment interface: all events rejected'})
        row = self.session()
        if not secrets.compare_digest(self.headers.get('X-CSRF-Token', ''), row['csrf']):
            return self.reply(403, {'error': 'CSRF token required'})
        try:
            size = int(self.headers.get('Content-Length', '0'))
            if size < 1 or size > 4096:
                raise ValueError()
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError()
        except (ValueError, TypeError):
            return self.reply(400, {'error': 'Invalid JSON'})
        updates = {}
        if path == '/api/register':
            if set(data) != {'discover_world'} or type(data['discover_world']) is not bool:
                return self.reply(400, {'error': 'Only demo opt-in allowed; no email accepted'})
            updates = {'registered': 1, 'discover_world': int(data['discover_world'])}
        elif path == '/api/demo/activate':
            if not self.server.demo_enabled or data != {'confirm': True}:
                return self.reply(403, {'error': 'Explicit local demo simulation disabled or not confirmed'})
            updates = {'paid': 1}
        elif path == '/api/preferences':
            if not row['paid']:
                return self.reply(403, {'error': 'Monde access required'})
            choices, language = data.get('destinations'), data.get('language')
            if (set(data) != {'destinations', 'language'} or not isinstance(choices, list)
                    or not choices or not all(isinstance(c, str) and c in VALID for c in choices)
                    or len(set(choices)) != len(choices) or language not in ('fr', 'en', 'both')):
                return self.reply(400, {'error': 'Choose unique valid destinations and fr/en/both'})
            updates = {'destinations': json.dumps(choices), 'language': language}
        else:
            return self.reply(404, {'error': 'Not found'})
        with sqlite3.connect(self.server.db_path) as db:
            db.execute('UPDATE sessions SET ' + ','.join(k + '=?' for k in updates) + ' WHERE sid=?', [*updates.values(), row['sid']])
        row.update(updates)
        return self.reply(200, self.session_view(row))


def create_server(port=8011, db_path=None, demo_enabled=False):
    if db_path is None:
        db_path = ROOT / '.runtime' / 'sessions.sqlite'
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS sessions (sid TEXT PRIMARY KEY, csrf TEXT NOT NULL, paid INTEGER NOT NULL DEFAULT 0, registered INTEGER NOT NULL DEFAULT 0, discover_world INTEGER NOT NULL DEFAULT 0, language TEXT NOT NULL, destinations TEXT NOT NULL, expires REAL NOT NULL)')
    db_path.chmod(0o600)
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.db_path, server.demo_enabled = db_path, demo_enabled
    return server


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8011)
    parser.add_argument('--db', type=Path, help='Optional session DB; default disposable DB under world_demo/.runtime')
    parser.add_argument('--demo-activation', action='store_true', help='Explicitly permit local payment-free activation simulation')
    args = parser.parse_args()
    temporary = None
    if args.db is None:
        runtime = ROOT / '.runtime'
        runtime.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(prefix='session-', dir=runtime)
        args.db = Path(temporary.name) / 'sessions.sqlite'
    httpd = create_server(args.port, args.db, args.demo_activation)
    print(f'DEMONSTRATION ONLY — http://127.0.0.1:{httpd.server_port} — no payments or sending', flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        if temporary:
            temporary.cleanup()
