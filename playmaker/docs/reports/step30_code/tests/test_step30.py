"""Step 30: after a successful block (D-276), the two app-only cards' block ratings (D-277), and the fake read ahead in
the setup's reading (item 3). Shaun's playtest is the gate: these check the rules as built, not results of play."""
import json
import os
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply, ChanceNode

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

from test_step29 import state, rim, act, narrow, THREE_O, THREE_X, THREE_AR, RIM_O, RIM_AR  # noqa: E402


def sq(n):
    return B.parse_sq(n)


def push(c, *others):
    return B.sq(B.pushed(sq(c), {sq(q) for q in others}))


# ---- the shooter forced 3 back (D-276) ---------------------------------------------------------------------------------

def test_forced_back_along_a_column():
    assert B.DIR_NAMES[B.push_dir(sq('I4'))] == 'N' and push('I4') == 'I7'


def test_forced_back_along_a_row():
    assert B.DIR_NAMES[B.push_dir(sq('J2'))] == 'E' and push('J2') == 'M2'


def test_forced_back_along_a_diagonal():
    assert B.DIR_NAMES[B.push_dir(sq('M6'))] == 'NE' and push('M6') == 'P9'


def test_stopped_short_by_a_player():
    assert push('M6', 'O8') == 'N7'                 # the last open square before him
    assert push('M6', 'N7') == 'M6'                 # the first square taken: he stays


def test_stopped_short_by_the_courts_edge():
    assert push('C9') == 'A11'                      # two diagonal steps, then the sideline
    assert push('A3') == 'A3'                       # the first square off the court: he stays


def test_no_tie_between_a_line_and_a_diagonal_on_any_square():
    # D-276's tie rule (take the diagonal) is built, but on whole squares no tie can happen: the gap is never 0
    for x in range(B.W):
        for y in range(B.H):
            c = (x, y)
            if not B.on_board(c) or c == B.RIM:
                continue
            vx, vy = x - B.RIM[0], y - B.RIM[1]
            ks = sorted((dx * vx + dy * vy) / (2 ** 0.5 if dx and dy else 1) for dx, dy in B.DIRS)
            assert ks[-1] - ks[-2] > 1e-6


# ---- the block and the reset (D-276) -----------------------------------------------------------------------------------

def _blocked(s):
    r = apply(s, act(s, 'shot'))
    node = apply(r, next(a for a in legal_actions(r) if a.kind == 'contest' and a.piece == 4 and a.shot == 'hard'))
    return r, next(sub for _, l, sub in node.outcomes if l == 'blocked')


def test_a_block_forces_the_shooter_back_then_the_blocker_resets():
    s = rim()
    r, b = _blocked(s)
    assert b.stage == 'reset' and b.side == 'X' and b.reset == 4
    assert b.tos == r.tos + 1 and b.phase == r.phase + 1                      # -5, the phase lost
    occ = (set(s.o) | set(s.x)) - {s.o[s.ball]}
    assert b.o[s.ball] == B.pushed(s.o[s.ball], occ) and b.o[s.ball] != s.o[s.ball]
    assert b.x == s.x and [q for i, q in enumerate(b.o) if i != s.ball] == [q for i, q in enumerate(s.o) if i != s.ball]


def test_the_blockers_resets_every_open_square_within_3_and_staying():
    s = rim()
    _, b = _blocked(s)
    acts = legal_actions(b)
    assert acts and all(a.kind == 'reset' and a.piece == 4 for a in acts)
    here = b.x[4]
    taken = set(b.o) | {q for j, q in enumerate(b.x) if j != 4}
    want = {(x, y) for x in range(B.W) for y in range(B.H) if B.on_board((x, y)) and B.cheb((x, y), here) <= RC.BLOCK_RESET
            and (x, y) not in taken}
    assert {a.dest for a in acts} == want and here in want                   # within 3 by the square count; may stay
    assert {a.arrow for a in acts if a.dest == here} == set(range(8))         # any arrow


def test_after_the_reset_the_shooter_has_the_ball_as_if_he_just_caught_it():
    s = rim()
    _, b = _blocked(s)
    a = next(a for a in legal_actions(b) if a.dest != b.x[4])
    n = apply(b, a)
    assert n.stage == 'play' and n.side == 'O' and n.reset == -1
    assert n.x[4] == a.dest and n.arrows[4] == a.arrow and n.x[:4] == b.x[:4]
    assert n.grd == 0 and not n.picked_up() and n.ball == s.ball           # dribble alive, closely guarded count from nothing


def test_a_block_in_the_last_phase_ends_the_possession():
    s = rim().with_(clock=RC.PHASE_SECONDS)
    _, b = _blocked(s)
    assert b.stage == 'over'


def test_the_line_shaun_asked_for():
    from playmaker_web.game import consequences
    s = rim()
    _, b = _blocked(s)
    a = next(a for a in legal_actions(b) if a.dest != b.x[4])
    words = consequences(b, apply(b, a), a)[0][1]
    assert words == f'Blocked by X5. O5 is forced back to {B.sq(b.o[4])}; X5 resets to {B.sq(a.dest)}.'


# ---- the search past a block, both engines -----------------------------------------------------------------------------
# Each board after a block is a new phase the map reads afresh (about 10 seconds a reading in Python), so these use the
# rim board with the shooter off a Sprint (no fake, so no mix), X5 square in front of him and the others away from the
# ball and unable to move: the same rules, fewer replies to read.

def tiny():
    s = state(RIM_O, ['B12', 'B9', 'P4', 'N9', 'H3'], [0, 0, 0, 0, 0], ball=4, rush_o=RC.RUSH_SPRINT << 8)
    return s.with_(moved_x=0b11111, qs_x=0b11111)


@needs_node
def test_both_engines_read_the_reset_the_same():
    from test_step29 import _js_search, _py_search
    from playmaker_engine.jsbridge import NodeEngine
    _, b = _blocked(tiny())
    eng = NodeEngine()
    try:
        out, ag = _js_search(eng, b, 1)
        sr, res, reached = _py_search(b, 1, ag)
        assert reached == out['reached']
        assert [round(v, 9) for v, _ in res] == [round(v, 9) for v, _ in out['results']]
    finally:
        eng.close()


@needs_node
def test_both_engines_value_a_block_at_the_horizon_the_same():
    # the reply to the shot: the search reads the block's chance node, then the reset at the horizon (reset_choice)
    from test_step29 import _js_search, _py_search
    from playmaker_engine.jsbridge import NodeEngine
    s = tiny()
    r = apply(s, act(s, 'shot'))
    eng = NodeEngine()
    try:
        out, ag = _js_search(eng, r, 1)
        sr, res, reached = _py_search(r, 1, ag)
        assert [round(v, 9) for v, _ in res] == [round(v, 9) for v, _ in out['results']]
    finally:
        eng.close()


def test_the_reset_at_the_horizon_is_the_defences_best_by_its_reading():
    from playmaker_engine.search import reset_choice, reset_candidates
    _, b = _blocked(rim())
    cands = reset_candidates(b)
    assert b.x[4] in {a.dest for a in cands}                                  # staying is read
    far = max(cands, key=lambda a: B.cheb(a.dest, b.o[b.ball]))
    pick = reset_choice(b, lambda n: -B.cheb(n.x[4], n.o[n.ball]))             # a value that favours the defence far away
    assert pick.dest == far.dest or B.cheb(pick.dest, b.o[b.ball]) == B.cheb(far.dest, b.o[b.ball])
    assert reset_choice(b, lambda n: 0.0) == cands[0]                          # all equal: the earliest


# ---- the two app-only cards (D-277) ------------------------------------------------------------------------------------

@pytest.mark.parametrize('key,want', [('slsfA', (9, 11)), ('slsfB', (8, 12)), ('slsfC', (7, 12)),
                                      ('swcA', (10, 5)), ('swcB', (9, 6)), ('swcC', (8, 7))])
def test_the_two_app_only_cards(key, want):
    from playmaker_engine.data.data import block_of, BLOCK_STAND_IN
    assert block_of(key) == want and not BLOCK_STAND_IN


def test_the_ratings_sheet_carries_both_with_a_note():
    import csv
    rows = list(csv.DictReader(open(os.path.join(ROOT, 'docs', 'reference', 'step29', 'BLOCK_RATINGS.csv'))))
    text = json.dumps(rows)
    assert 'APP-SW' in text and 'APP-SC' in text and 'D-277' in text


# ---- the fake read ahead (item 3) --------------------------------------------------------------------------------------
# Read with the JavaScript engine installed, as the setup runs (the map and the search in Python take minutes a board).

@pytest.fixture
def js(monkeypatch):
    from playmaker_engine import agent as AG, plan as PL
    from playmaker_engine.jsbridge import NodeEngine
    monkeypatch.setitem(AG.FIXED, 'depth', 1)
    monkeypatch.setattr(PL, 'FAKE_LEVEL', 'starter')
    eng = NodeEngine().install()
    yield eng
    eng.close()


@needs_node
def test_the_read_ahead_reads_the_fake(js, monkeypatch):
    """The setup's read ahead tries each fake, reads the defence's reply by its own mix and the list after it."""
    from playmaker_engine import plan as PL
    calls = []
    real = PL._fake_continuations

    def spy(st):
        out = real(st)
        calls.append(out)
        return out
    monkeypatch.setattr(PL, '_fake_continuations', spy)
    s = narrow(state(THREE_O, THREE_X, THREE_AR))
    PL.horizon_read(s, None, budget=600.0, depth=2)
    assert calls and calls[0]
    words, nxt, dn, a, key = calls[0][0]
    assert 'fakes' in words and a.arrow == 1 and nxt.stage == 'play' and nxt.side == 'O' and nxt.fake == 0
    assert isinstance(key[0], tuple) and key[0]


@needs_node
def test_the_fakes_reply_is_read_from_the_public_board(js, monkeypatch):
    """The defence's reply in the read ahead never reads the hidden choice: the real and the fake declaration give it
    the same mix."""
    from playmaker_engine import plan as PL, agent as AG
    from playmaker_engine.search import is_fake
    seen = []
    real = AG.Agent._mix_cols

    def spy(self, s, budget):
        out = real(self, s, budget)
        seen.append((out, real(self, s.with_(fake=0), budget)))
        return out
    monkeypatch.setattr(AG.Agent, '_mix_cols', spy)
    s = narrow(state(THREE_O, THREE_X, THREE_AR))
    out = PL._fake_continuations(s)
    assert out and seen and all(a == b for a, b in seen)
    assert all(is_fake(r[3]) for r in out)
