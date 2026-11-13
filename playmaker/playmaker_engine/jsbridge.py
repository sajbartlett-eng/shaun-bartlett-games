"""Step 3n Part A: the bridge to the JavaScript search core (playmaker_web/static/engine.js).

state_json / ctx_json write a GameState and its Context as plain JSON for the JavaScript engine; action_from turns the
engine's action back into an Action. The Python engine stays the reference: engine.js is a port, proved equal on random
legal states by tools/js_equivalence.py, and plays only the ruled settings (both formats).
"""
from dataclasses import asdict, fields

from . import board as B
from . import rules_config as RC
from .actions import Action

_DEFAULTS = {f.name: getattr(RC.DEFAULT_RULES, f.name) for f in fields(RC.Rules)}
PORTED_FREE = ('digital', 'quarter_possessions', 'bonus_from')


def ported(rules):
    """Does engine.js play these rules? (every setting at its ruled value, except the format and the quarter)"""
    return all(getattr(rules, k) == v for k, v in _DEFAULTS.items() if k not in PORTED_FREE)


def card_json(c):
    return dict(qs=c.qs, r=dict(c.r), bands=dict(c.bands))      # bands (step 16): the card's H, A, L per rating


def ctx_json(ctx, table=None):
    r = asdict(ctx.rules)
    r['reaction_kinds'] = list(r['reaction_kinds'])
    return dict(off=[card_json(c) for c in ctx.off], dfn=[card_json(c) for c in ctx.dfn], rules=r,
                card_clock=ctx.card_clock, inbounder=ctx.inbounder, coach_call=ctx.coach_call, three_only=ctx.three_only,
                two_or_three=ctx.two_or_three, hold_for_one=ctx.hold_for_one, team_fouls=ctx.team_fouls,
                quarter_left=ctx.quarter_left,
                table=table or '/'.join(getattr(ctx, 'levels_key', None) or ('senior', 'pro')))


def state_json(s):
    sq = B.sq
    res = None
    if s.result is not None:
        res = asdict(s.result)
    return dict(o=[sq(p) for p in s.o], x=[sq(p) for p in s.x], arrows=list(s.arrows), ball=s.ball, stage=s.stage,
                side=s.side, clock=s.clock, tok_o=s.tok_o, tok_x=s.tok_x, moved_o=s.moved_o, moved_x=s.moved_x,
                cnt=list(s.cnt), turn_n=s.turn_n, final=s.final, lock_o=s.lock_o, lock_x=s.lock_x,
                screens=[list(t) for t in s.screens], pending=list(s.pending) if s.pending else None,
                approach=s.approach, shot=s.shot, prev_wait=s.prev_wait, beaten=[list(t) for t in s.beaten],
                fouls=s.fouls, bonus5=s.bonus5, tos=s.tos, inbound=s.inbound, target=s.target, result=res,
                zeroed=s.zeroed, phase=s.phase, turn_moved=s.turn_moved, qs_o=s.qs_o, qs_x=s.qs_x, forced=s.forced,
                react_moved=s.react_moved, turn_lead=s.turn_lead, rush_o=s.rush_o, rush_x=s.rush_x, key_o=s.key_o, grd=s.grd,
                turn_x=[[sq(p) for p in s.turn_x[0]], list(s.turn_x[1])] if s.turn_x else [])


def action_from(t):
    """[kind, side, piece, dest square or None, arrow, target, shot] -> Action."""
    kind, side, piece, dest, arrow, target, shot = t
    return Action(kind, side, piece, B.parse_sq(dest) if dest else None, arrow, target, shot or '')


class NodeEngine:
    """engine.js in a long-running Node process, for the server, the tools and the tests (the browser runs it in the
    worker). install() points agent.JS at it; uninstall() restores the Python search."""

    def __init__(self):
        import os
        import subprocess
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.p = subprocess.Popen(['node', os.path.join(here, 'tools', 'js_server.js')], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, bufsize=1)

    def call(self, fn, text):
        import json
        self.p.stdin.write(json.dumps(dict(fn=fn, text=text)) + '\n')
        self.p.stdin.flush()
        out = json.loads(self.p.stdout.readline())
        if 'error' in out:
            raise RuntimeError(out['error'])
        return out['ok']

    def install(self):
        from . import agent as AG
        AG.JS['search'] = lambda t: self.call('searchJSON', t)
        AG.JS['goals'] = lambda t: self.call('goalsJSON', t)
        return self

    @staticmethod
    def uninstall():
        from . import agent as AG
        AG.JS['search'] = AG.JS['goals'] = None

    def close(self):
        self.uninstall()
        try:
            self.p.stdin.close()
            self.p.wait(5)
        except Exception:
            self.p.kill()
