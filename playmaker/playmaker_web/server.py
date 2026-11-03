"""HTTP server: standard library only. One port serves the page and the JSON API.

API (all JSON):
  POST /api/new        {mode: hotseat|remote, scenario?: n, teams?: [off, dfn], full?: bool, seed?: int,
                        ai?: {O: 'greedy'|null, X: 'greedy'|null}}      -> {code, token?}
  POST /api/join       {code, seat: O|X}                                  -> {token}
  GET  /api/state?code=&token=                                            -> state (with legal actions if yours)
  GET  /api/legal?code=&token=                                            -> [actions]
  POST /api/act        {code, token, action}                              -> {rolls, state}
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

from playmaker_engine.cards import TEAMS, TEAM_TAGLINES, FIRST_GAME
from playmaker_engine.scenarios import SCENARIOS

from .game import Game, GameError
from .view import state_json, legal_json

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
TYPES = {'.html': 'text/html; charset=utf-8', '.js': 'application/javascript', '.css': 'text/css', '.png': 'image/png'}


class Manager:
    def __init__(self):
        self.games = {}
        self.lock = threading.Lock()

    def new(self, body):
        g = Game(mode=body.get('mode', 'hotseat'), scenario=body.get('scenario'), teams=body.get('teams'),
                 seed=body.get('seed'), ai=body.get('ai'), full=bool(body.get('full')))
        with self.lock:
            self.games[g.code] = g
        return g

    def get(self, code):
        g = self.games.get((code or '').upper())
        if g is None:
            raise GameError(f'no game {code}')
        return g


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

        def _body(self):
            n = int(self.headers.get('Content-Length') or 0)
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n))
            except ValueError:
                raise GameError('request body is not JSON')

        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path == '/api/state':
                    g = manager.get(q.get('code'))
                    return self._send(200, state_json(g, q.get('token')))
                if u.path == '/api/legal':
                    g = manager.get(q.get('code'))
                    acts = legal_json(g.state, g.legal()) if g.can_act(q.get('token')) else []
                    return self._send(200, acts)
                if u.path == '/api/log':
                    return self._send(200, manager.get(q.get('code')).read_log())
                if u.path == '/api/options':
                    return self._send(200, dict(
                        teams=[dict(name=n, tagline=TEAM_TAGLINES[n], cards=[c.key for c in cs]) for n, cs in TEAMS.items()],
                        first_game=list(FIRST_GAME),
                        scenarios=[dict(n=n, title=s['title'], kind=s['kind'], clock=s['clock'], text=s['text'],
                                        off=s['off'], dfn=s['dfn']) for n, s in SCENARIOS.items()]))
                path = 'index.html' if u.path in ('/', '') else u.path.lstrip('/')
                full = os.path.normpath(os.path.join(STATIC, path))
                if not full.startswith(STATIC) or not os.path.isfile(full):
                    return self._send(404, dict(error='not found'))
                with open(full, 'rb') as f:
                    return self._send(200, raw=f.read(), ctype=TYPES.get(os.path.splitext(full)[1], 'text/plain'))
            except GameError as e:
                return self._send(400, dict(error=str(e)))

        def do_POST(self):
            u = urlparse(self.path)
            try:
                body = self._body()
                if u.path == '/api/new':
                    g = manager.new(body)
                    return self._send(200, dict(code=g.code, token=g.tokens.get('both'), seed=g.seed))
                g = manager.get(body.get('code'))
                tok = body.get('token')
                if u.path == '/api/join':
                    return self._send(200, dict(token=g.join(body.get('seat'))))
                if u.path == '/api/act':
                    res = g.act(tok, body.get('action') or {})
                    g.after_human()
                    return self._send(200, dict(rolls=res['rolls'], state=state_json(g, tok)))
                if u.path == '/api/undo':
                    res = g.do_undo(tok)
                    return self._send(200, dict(res, state=state_json(g, tok)))
                if u.path == '/api/next':
                    g.next_possession(tok)
                    return self._send(200, dict(state=state_json(g, tok)))
                if u.path == '/api/feedback':
                    g.save_feedback(tok, body.get('answers') or {})
                    return self._send(200, dict(ok=True))
                return self._send(404, dict(error='not found'))
            except GameError as e:
                return self._send(400, dict(error=str(e)))

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
