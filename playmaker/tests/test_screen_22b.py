"""Step 22b (D-217, Shaun, 18 Nov 2026): the screen stops the path around it, for the defender's body and his arrows
alike. While he stands on a screen's T square, his arrow pointing diagonally (the way the screen stops him stepping)
walls no drive and jumps no passing lane; his other arrow and his contest are unchanged. The block ends when he leaves
the T square, wins a Challenge, the screener moves or the phase ends."""
import json
import os
import shutil
import subprocess
import sys

import pytest

from playmaker_engine import actions as A
from playmaker_engine import board as B
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


def screened():
    """S3's board after O5's screen with the T on the on-ball defender (X1 on I10, facing N: lines N and NE)."""
    import step_18s as S
    s0 = S.screen_board()
    s1 = apply(s0, next(a for a in legal_actions(s0) if str(a) == 'O5 Screen, T W'))
    return s0, s1.with_(side='O', turn_n=0)


def o1_moves(s):
    return {str(a) for a in legal_actions(s) if a.side == 'O' and a.piece == 0 and a.kind in ('move', 'qs', 'sprint')}


def test_the_ruling_is_recorded_and_in_the_rules_text():
    assert '**D-217.' in open(os.path.join(ROOT, 'DECISIONS.md')).read()
    assert 'loses his arrow that points diagonally' in open(os.path.join(ROOT, 'RULES_CURRENT.md')).read()


def test_on_the_t_square_the_diagonal_arrow_is_blocked_and_the_straight_one_is_not():
    _, s = screened()
    assert B.sq(s.x[0]) == 'I10' and A.t_square(s, s.screens[0]) == s.x[0]
    assert A.arrows_blocked(s, 0) == A.DIAGONALS
    assert A.live_lines(s, 0) == (0,)                                  # N stays, NE is blocked
    for j in range(1, 5):                                              # nobody else is on the T
        assert A.arrows_blocked(s, j) == frozenset()


def test_a_blocked_arrow_walls_no_drive_so_the_ball_handler_can_use_the_screen(monkeypatch):
    _, s = screened()
    assert all(c[0] != s.x[0] for c in A.capture_lines(s, 0))          # X1 no longer catches O1
    now = o1_moves(s)
    monkeypatch.setattr(A, 'arrows_blocked', lambda *a, **k: frozenset())
    before = o1_moves(s)
    assert before < now and 'O1 Move to K11' in now - before          # around the screen, to the screener's side


def test_his_contest_is_unchanged():
    from playmaker_engine import geometry as G
    _, s = screened()
    st = A.stance(s, 0)
    assert st == 8 + s.arrows[0]                                       # the stance the contest reads is untouched
    assert G.lines(s.ctx.rules, st) == (0, 1)


def test_the_block_ends_when_he_leaves_wins_a_challenge_the_screener_moves_or_the_phase_ends():
    _, s = screened()
    off = s.with_(x=(B.parse_sq('H9'),) + s.x[1:])                     # he has left the T square
    assert A.arrows_blocked(off, 0) == frozenset()
    sc = s.screens[0]
    beat = s.with_(screens=((sc[0], sc[1], sc[2], sc[3] | 1),))        # he beat it with a Challenge
    assert A.arrows_blocked(beat, 0) == frozenset()
    gone = s.with_(screens=())                                         # the screener moved or the phase ended
    assert A.arrows_blocked(gone, 0) == frozenset()
    assert A.arrows_blocked(s, 0, B.parse_sq('H9')) == frozenset()     # read at another square


def test_a_blocked_arrow_jumps_no_passing_lane():
    _, s = screened()
    assert all(d % 2 == 0 for d in A.live_lines(s, 0))
    pend = s.with_(side='X', turn_n=0, pending=(0, 1))
    for a in legal_actions(pend):
        if a.kind == 'intercept' and a.piece == 0 and a.dest is not None and a.dest != pend.x[0]:
            dx, dy = a.dest[0] - pend.x[0][0], a.dest[1] - pend.x[0][1]
            assert dx == 0 or dy == 0, str(a)                          # never along the blocked diagonal


@needs_node
def test_both_engines_agree_on_the_screened_board():
    from playmaker_engine import jsbridge
    js = ('const E=require("./playmaker_web/static/engine.js");const fs=require("fs");const r="./playmaker_engine/data/";'
          'const L=n=>JSON.parse(fs.readFileSync(r+n));E.init({zones:L("court_zones.json"),config:L("ai_profiles.json"),'
          'vcoarse:L("vcoarse.json"),learned:null});const q=JSON.parse(fs.readFileSync(0,"utf8"));const ctx=E.makeCtx(q.ctx),'
          's=E.stateFrom(q.state,ctx);console.log(JSON.stringify(E.legalActions(s).map(a=>E.actionStr(a))))')
    _, s = screened()
    for n in (s, s.with_(side='X', turn_n=0, pending=(0, 1))):
        p = subprocess.run(['node', '-e', js], cwd=ROOT, capture_output=True, text=True,
                           input=json.dumps(dict(state=jsbridge.state_json(n), ctx=jsbridge.ctx_json(n.ctx))))
        assert sorted(json.loads(p.stdout)) == sorted(str(a) for a in legal_actions(n)), p.stderr[-400:]
