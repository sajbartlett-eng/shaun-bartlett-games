"""The JSON API, independent of transport. The HTTP server and the in-browser (Pyodide) build both
call handle(), so the front end talks to one API whichever back end runs it."""
import json
import threading

from playmaker_engine.cards import TEAMS, TEAM_TAGLINES, FIRST_GAME
from playmaker_engine.scenarios import SCENARIOS

from .game import Game, GameError
from .view import state_json, legal_json


class Manager:
    def __init__(self, static=False):
        self.games = {}
        self.static = static
        self.lock = threading.Lock()

    def new(self, body):
        if self.static and body.get('mode') == 'remote':
            raise GameError('remote play needs the server version (python -m playmaker_web)')
        g = Game(mode=body.get('mode', 'hotseat'), scenario=body.get('scenario'), teams=body.get('teams'),
                 seed=body.get('seed'), ai=body.get('ai'), full=bool(body.get('full')),
                 place=body.get('place', bool(body.get('full'))), code=body.get('code'))
        g.static = self.static
        with self.lock:
            self.games[g.code] = g
        return g

    def get(self, code):
        g = self.games.get((code or '').upper())
        if g is None:
            raise GameError(f'no game {code}')
        return g


def options(manager):
    return dict(static=manager.static,
                teams=[dict(name=n, tagline=TEAM_TAGLINES[n], cards=[c.key for c in cs]) for n, cs in TEAMS.items()],
                first_game=list(FIRST_GAME),
                scenarios=[dict(n=n, title=s['title'], kind=s['kind'], clock=s['clock'], text=s['text'],
                                off=s['off'], dfn=s['dfn']) for n, s in SCENARIOS.items()])


def handle(manager, method, path, query=None, body=None):
    """Returns (status, object)."""
    q = query or {}
    body = body or {}
    try:
        if method == 'GET':
            if path == '/api/state':
                g = manager.get(q.get('code'))
                return 200, state_json(g, q.get('token'))
            if path == '/api/legal':
                g = manager.get(q.get('code'))
                return 200, (legal_json(g.state, g.legal()) if g.can_act(q.get('token')) else [])
            if path == '/api/log':
                return 200, manager.get(q.get('code')).read_log()
            if path == '/api/options':
                return 200, options(manager)
            return 404, dict(error='not found')
        if path == '/api/new':
            g = manager.new(body)
            return 200, dict(code=g.code, token=g.tokens.get('both'), seed=g.seed)
        g = manager.get(body.get('code'))
        tok = body.get('token')
        if path == '/api/join':
            return 200, dict(token=g.join(body.get('seat')))
        if path == '/api/act':
            res = g.act(tok, body.get('action') or {})
            g.after_human()
            return 200, dict(rolls=res['rolls'], state=state_json(g, tok))
        if path == '/api/place':
            g.place(tok, body)
            return 200, dict(state=state_json(g, tok))
        if path == '/api/undo':
            res = g.do_undo(tok)
            return 200, dict(res, state=state_json(g, tok))
        if path == '/api/next':
            g.next_possession(tok)
            return 200, dict(state=state_json(g, tok))
        if path == '/api/feedback':
            g.save_feedback(tok, body.get('answers') or {})
            return 200, dict(ok=True)
        return 404, dict(error='not found')
    except GameError as e:
        return 400, dict(error=str(e))


# ---- the in-browser entry point (Pyodide) ----------------------------------------------------------

_STATIC = None


def dispatch(method, path, query_json='{}', body_json='{}'):
    """Called from JavaScript in the static build; returns a JSON string {status, body}."""
    global _STATIC
    if _STATIC is None:
        _STATIC = Manager(static=True)
    status, obj = handle(_STATIC, method, path, json.loads(query_json or '{}'), json.loads(body_json or '{}'))
    return json.dumps(dict(status=status, body=obj), default=str)
