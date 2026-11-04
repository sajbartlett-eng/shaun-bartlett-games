"""HTTP server: standard library only. One port serves the page and the JSON API.

API (all JSON):
  POST /api/new        {mode: hotseat|remote, scenario?: n, teams?: [off, dfn], full?: bool, seed?: int,
                        ai?: {O: 'greedy'|null, X: 'greedy'|null}}      -> {code, token?}
  POST /api/join       {code, seat: O|X}                                  -> {token}
  GET  /api/state?code=&token=                                            -> state (with legal actions if yours)
  GET  /api/legal?code=&token=                                            -> [actions]
  POST /api/act        {code, token, action}                              -> {rolls, state}
  POST /api/place      {code, token, squares: [5], ball?: i, arrows?: [5]} or {preview: true}
  POST /api/undo       {code, token}
  POST /api/next       {code, token}                                      (full game: second possession)
  POST /api/feedback   {code, token, answers: {"0": "...", ...}}
  GET  /api/log?code=                                                      -> [log records]
  GET  /api/options                                                        -> teams and scenario cards
"""
import json
import os
import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from .api import Manager, handle

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png'}


def make_handler(manager):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, status, obj=None, raw=None, ctype='application/json'):
            data = raw if raw is not None else json.dumps(obj).encode()
            self.send_response(status)
            self.send_header('Content-Type', ctype)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            u = urlparse(self.path)
            if u.path.startswith('/api/'):
                q = {k: v[0] for k, v in parse_qs(u.query).items()}
                return self._send(*handle(manager, 'GET', u.path, q))
            path = 'index.html' if u.path in ('/', '') else u.path.lstrip('/')
            full = os.path.normpath(os.path.join(STATIC, path))
            if not full.startswith(STATIC) or not os.path.isfile(full):
                return self._send(404, dict(error='not found'))
            with open(full, 'rb') as f:
                return self._send(200, raw=f.read(), ctype=TYPES.get(os.path.splitext(full)[1], 'text/plain'))

        def do_POST(self):
            u = urlparse(self.path)
            n = int(self.headers.get('Content-Length') or 0)
            try:
                body = json.loads(self.rfile.read(n)) if n else {}
            except ValueError:
                return self._send(400, dict(error='request body is not JSON'))
            return self._send(*handle(manager, 'POST', u.path, None, body))

    return Handler


def serve(port=8765, host='0.0.0.0'):
    manager = Manager()
    httpd = ThreadingHTTPServer((host, port), make_handler(manager))
    httpd.manager = manager
    return httpd


def start_background(port=0, host='127.0.0.1'):
    """For tests: start on a free port in a thread; returns (server, base_url)."""
    httpd = serve(port, host)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, f'http://{host}:{httpd.server_address[1]}'
