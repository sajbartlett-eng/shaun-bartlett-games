"""The JSON API, independent of transport. The HTTP server and the in-browser (Pyodide) build both
call handle(), so the front end talks to one API whichever back end runs it."""
import json
import threading

from playmaker_engine.cards import TEAMS, TEAM_TAGLINES, FIRST_GAME, PRESCRIBED, CARDS
from playmaker_engine.scenarios import SCENARIOS

from playmaker_engine.scouting import position

from .game import Game, GameError
from .view import state_json, legal_json


class Manager:
    def __init__(self, static=False):
        self.games = {}
        self.drafts = {}                 # step 3l: drafts in progress, by id
        self.static = static
        self.lock = threading.Lock()

    def new(self, body):
        if self.static and body.get('mode') == 'remote':
            raise GameError('remote play needs the server version (python -m playmaker_web)')
        g = Game(mode=body.get('mode', 'hotseat'), scenario=body.get('scenario'), teams=body.get('teams'),
                 seed=body.get('seed'), ai=body.get('ai'), full=bool(body.get('full')),
                 place=body.get('place', bool(body.get('full'))), code=body.get('code'),
                 level=body.get('level', 'scout'), custom=body.get('custom'), timer=body.get('timer'),
                 age=body.get('age', 'senior'), standard=body.get('standard', 'pro'),
                 roster=body.get('roster', 'prescribed'), lineups=body.get('lineups'), deal=body.get('deal'),
                 random_for=body.get('random', 'both'), coherent=bool(body.get('coherent')),
                 draft=self.drafts.get(str(body.get('draft') or '').upper()),
                 match_format=body.get('match_format', 'tabletop'), per_side=int(body.get('per_side') or 8))
        g.static = self.static
        with self.lock:
            self.games[g.code] = g
        return g

    def get(self, code):
        g = self.games.get((code or '').upper())
        if g is None:
            raise GameError(f'no game {code}')
        return g


# ---- step 3l: random deals and the draft ------------------------------------------------------------------------

def deal_json(body):
    """A random deal (B4): new from the dials, or the same deal again from its code. Both teams, the scout report for
    both (growth tags stay face down until setup), the strength totals."""
    from playmaker_engine import rosters as RO, levels as LV
    from playmaker_engine.scouting import report
    from playmaker_engine.cards import register_cards
    try:
        d = RO.deal(body.get('age', 'senior'), body.get('standard', 'pro'), bool(body.get('coherent')),
                    code=(body.get('code') or '').strip().upper() or None)
    except ValueError as e:
        raise GameError(str(e))
    names = []
    for i, ents in enumerate(d['rosters']):
        cards = LV.team(ents, d['age'])
        names.append(register_cards(('Home', 'Away')[i] + ' deal ' + d['code'], cards))
    rep = report(names[0], names[1], 'learn')
    return dict(code=d['code'], age=d['age'], standard=d['standard'], coherent=d['coherent'],
                rosters=[[dict(key=k, slot=s, role=CARDS[k].role, tier=CARDS[k].tier,
                               flex=f'playing the {s}' if CARDS[k].num != s else '') for k, s in r]
                         for r in d['rosters']],
                strength=[RO.strength([k for k, _ in r]) for r in d['rosters']],
                tags_note=LV.GROWTH_BOX if d['tags'] else None, report=rep)


def draft_json(manager, did, dr):
    from playmaker_engine import rosters as RO
    turn = dr.turn
    human = getattr(dr, 'human', {1, 2})
    legal = sorted({k for k, _ in dr.legal_picks(turn)}) if turn in human else []
    return dict(id=did, standard=dict(dr.standards), age=dr.age, done=dr.done(), turn=turn, human=sorted(human),
                order=list(RO.SNAKE), picks=dr.log,
                rosters={str(sd): [dict(key=k, slot=s, role=CARDS[k].role, tier=CARDS[k].tier,
                                        flex=f'playing the {s}' if CARDS[k].num != s else '') for k, s in dr.roster(sd)]
                         for sd in (1, 2)},
                strength={str(sd): RO.strength([k for k, _ in dr.roster(sd)]) for sd in (1, 2)},
                legal=legal,
                slots={k: [s for kk, s in dr.legal_picks(turn) if kk == k] for k in legal} if legal else {})


def draft_call(manager, body):
    """/api/draft: {new: {standard, age, standards?, computer: level, human: 1}} or {id, key, slot}. The computer picks
    for its side straight after the human, each pick logged with its reason."""
    from playmaker_engine import rosters as RO
    if body.get('new') is not None:
        n = body['new'] or {}
        std = n.get('standard', 'pro')
        stds = n.get('standards')
        stds = {1: stds.get('A', std), 2: stds.get('B', std)} if isinstance(stds, dict) else None
        dr = RO.Draft(std, n.get('age', 'senior'), stds)
        level = n.get('computer')
        dr.human = {int(n.get('human', 1))} if level else {1, 2}
        dr.computer = level
        did = f'D{len(manager.drafts) + 1:03d}'
        manager.drafts[did] = dr
    else:
        did = str(body.get('id') or '').upper()
        dr = manager.drafts.get(did)
        if dr is None:
            raise GameError('no draft ' + did)
        try:
            dr.pick(dr.turn, body.get('key'), int(body.get('slot') or 0))
        except (RO.DraftError, ValueError) as e:
            raise GameError(str(e))
    while not dr.done() and dr.turn not in dr.human:
        dr.computer_pick(dr.turn, dr.computer or 'starter')
    return draft_json(manager, did, dr)


def levels_info():
    from playmaker_engine import levels as LV, rosters as RO
    return dict(ages=[dict(id=a, words=LV.AGE_WORDS[a]) for a in LV.AGE_ORDER],
                standards=[dict(id=s, words=LV.STANDARD_WORDS[s], shapes=list(LV.STANDARDS[s]['shapes']))
                           for s in LV.STANDARD_ORDER],
                rosters={k: v for k, v in LV.ROSTER_WORDS.items()}, intro=LV.SHEET_INTRO, standard_note=LV.STANDARD_NOTE, growth_box=LV.GROWTH_BOX,
                growth=dict(early=LV.growth_words('early'), late=LV.growth_words('late')),
                sheet='docs/Playmaker_Playing_Levels.pdf', snake=list(RO.SNAKE))


def options(manager):
    return dict(static=manager.static,
                teams=[dict(name=n, tagline=TEAM_TAGLINES[n], cards=[c.key for c in TEAMS[n]]) for n in PRESCRIBED],
                cards=[dict(key=c.key, role=c.role, tier=c.tier, position=position(c), num=c.num) for c in CARDS.values()],
                first_game=list(FIRST_GAME), levels=levels_info(),
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
            if path == '/api/story':
                return 200, manager.get(q.get('code')).story()
            if path == '/api/options':
                return 200, options(manager)
            return 404, dict(error='not found')
        if path == '/api/deal':
            return 200, deal_json(body)
        if path == '/api/roster':
            from playmaker_engine import rosters as RO
            ents = [(e[0], int(e[1])) for e in (body.get('cards') or [])]
            try:
                bad = RO.problems(ents, body.get('standard', 'pro'), rules=bool(body.get('rules', True)))
            except (KeyError, ValueError):
                bad = ['Unknown card or standard.']
            keys = [k for k, _ in ents if k in CARDS]
            return 200, dict(problems=bad, shape=RO.shape_of(keys) if len(keys) == 5 else None,
                             strength=RO.strength(keys) if len(keys) == 5 else None)
        if path == '/api/draft':
            return 200, draft_call(manager, body)
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
        if path == '/api/scout':
            g.scout(tok, body)
            return 200, dict(state=state_json(g, tok))
        if path == '/api/review':
            return 200, g.review(tok)
        if path == '/api/place':
            g.place(tok, body)
            return 200, dict(state=state_json(g, tok))
        if path == '/api/undo':
            res = g.do_undo(tok)
            return 200, dict(res, state=state_json(g, tok))
        if path == '/api/next':
            g.next_possession(tok)
            return 200, dict(state=state_json(g, tok))
        if path == '/api/timer':
            g.timer_event(tok, body.get('event'))
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
        from playmaker_engine import agent
        # the decision engine's budgets are per decision on the device (ai_profiles.json time_budget_s); the search is
        # anytime, so the browser simply searches less deep in the same time
        agent.SCALE['value'] = agent.CONFIG['eval'].get('browser_budget_scale', 1.0)
    status, obj = handle(_STATIC, method, path, json.loads(query_json or '{}'), json.loads(body_json or '{}'))
    return json.dumps(dict(status=status, body=obj), default=str)
