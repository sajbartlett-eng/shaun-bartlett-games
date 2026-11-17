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
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png',
         '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8'}


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


_COVERAGE_ENGINE = []


def coverage_engine():
    """Step 19, stage 6: the server shows what the link version shows, the coverage view included. The coverage map
    lives in the fast engine (engine.js); the server runs it in Node for the coach's view and the reports only. The
    computer's play is untouched: its search stays where it was."""
    import shutil
    from playmaker_engine import agent as AG
    if _COVERAGE_ENGINE or AG.JS.get('coverage') is not None or not shutil.which('node'):
        return bool(_COVERAGE_ENGINE) or AG.JS.get('coverage') is not None
    from playmaker_engine.jsbridge import NodeEngine
    eng, lock = NodeEngine(), threading.Lock()

    def cov(text):
        with lock:                               # one request at a time down the one pipe
            return eng.call('coverageJSON', text)
    AG.JS['coverage'] = cov
    _COVERAGE_ENGINE.append(eng)
    return True


def stop_coverage_engine():
    from playmaker_engine import agent as AG
    while _COVERAGE_ENGINE:
        _COVERAGE_ENGINE.pop().close()            # close() puts every agent.JS entry back to None
    AG.JS['coverage'] = None


def serve(port=8765, host='0.0.0.0', coverage=True):
    if coverage:
        coverage_engine()
    manager = Manager()
    httpd = ThreadingHTTPServer((host, port), make_handler(manager))
    httpd.manager = manager
    return httpd


def start_background(port=0, host='127.0.0.1', coverage=False):
    """For tests: start on a free port in a thread; returns (server, base_url). coverage: also run the coverage map
    (the fast engine in Node), as the real server does; stop it with stop_coverage_engine()."""
    httpd = serve(port, host, coverage)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    return httpd, f'http://{host}:{httpd.server_address[1]}'
