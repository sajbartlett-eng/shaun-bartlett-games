"""Step 29 (Shaun, 20 Nov 2026): the block, shot and pass fakes, the pivot and deep range (D-269 to D-274)."""
import json
import os
import re
import shutil
import sys
from fractions import Fraction

import pytest

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scoring import contest_options, shot_zone, card_shot
from playmaker_engine.search import mix_game, worlds, fake_world, Searcher
from playmaker_engine.state import pack_guard

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


def state(o, x, ar, ball=0, off='High-Low', dfn='Run and Gun', rules=None, deep=None, **kw):
    from playmaker_engine.scenarios import game_state
    import step_18o as O
    s = game_state(off, dfn, list(o), list(x), list(ar), ball=ball, rules=RC.with_rules(digital=True, zone='on', **(rules or {})),
                   check=False, **O.T.FOULS)
    s.ctx.levels_key = ('senior', 'pro')
    if deep is not None:
        s.ctx.deep_rows = deep
    return s.with_(side='O', turn_n=0, **kw)


def leaves(node):
    """Every end of a node: [(chance, state)]."""
    if isinstance(node, ChanceNode):
        return [(p * q, t) for p, _, sub in node.outcomes for q, t in leaves(sub)]
    return [(Fraction(1), node)]


def act(s, kind, piece=None, fake=False, hard=None):
    for a in legal_actions(s):
        if a.kind == kind and (piece is None or a.piece == piece) and ((a.arrow == 1) == fake or kind not in ('shot', 'pass')) \
                and (hard is None or (a.shot == 'hard') == hard):
            return a
    raise AssertionError(f'no {kind} for {piece}')


# The three board (fakes): O1 has the ball on C9 at the three-point line; X1 on D10 behind him, his arrow on him
THREE_O = ['C9', 'O9', 'Q3', 'K12', 'I6']
THREE_X = ['D10', 'B9', 'P4', 'L11', 'J5']
THREE_AR = [B.dir_between(B.parse_sq('D10'), B.parse_sq('C9')), 0, 0, 0, 0]

# The rim board (the block): O5 has the ball on H4; X5 square in front on H3 (his arrow on him), X4 beside on G4,
# X1 behind on H5
RIM_O = ['C12', 'O9', 'Q3', 'K12', 'H4']
RIM_X = ['H5', 'B9', 'P4', 'G4', 'H3']
RIM_AR = [4, 0, 0, 0, 0]


def narrow(s, keep=(0,)):
    """The board with every other defender locked (no Move or Sprint, no arrow turn): fewer replies to read, the
    rules unchanged."""
    return s.with_(lock_x=sum(1 << j for j in range(5) if j not in keep), moved_x=sum(1 << j for j in range(5) if j not in keep),
                   qs_x=sum(1 << j for j in range(5) if j not in keep))


def rim(**kw):
    return state(RIM_O, RIM_X, RIM_AR, ball=4, **kw)


def blocks(s, t='layup'):
    return {o.defender: o for o in contest_options(s, s.ball, t) if o.defender >= 0 and o.hard}


# ---- the block (D-271) -------------------------------------------------------------------------------------------------

def test_one_contest_or_block_per_shot():
    s = rim()
    r = apply(s, act(s, 'shot'))
    cons = [a for a in legal_actions(r) if a.kind == 'contest']
    assert {a.piece for a in cons if a.shot == 'hard'} == {0, 3, 4}           # every defender next to him may block
    assert {a.piece for a in cons if a.shot != 'hard'} == {0, 3, 4}           # or contest
    for a in cons:
        for _, end in leaves(apply(r, a)):
            assert end.stage != 'reaction'                                    # either one ends the reply: never both


def test_the_block_is_on_every_shot_threes_included():
    s = state(THREE_O, THREE_X, THREE_AR)
    r = apply(s, act(s, 'shot'))
    assert r.shot == 'three' and any(a.kind == 'contest' and a.shot == 'hard' for a in legal_actions(r))


def test_the_blocks_position_and_rushed_reductions():
    s = rim()
    b = blocks(s)
    blk = {j: s.ctx.dfn[j].r['block'] for j in range(5)}
    assert b[4].block == blk[4] and b[4].rolls == 0                          # square: the full Block, no foul roll
    assert b[3].block == max(1, blk[3] - 3) and b[3].rolls == 2              # beside: 3 less, two foul rolls
    assert b[0].block == max(1, blk[0] - 6) and b[0].rolls == 2              # behind: 6 less, two foul rolls
    off = rim().with_(arrows=(4, 0, 0, 0, 2))                                # X5 in front, arrow off him
    assert blocks(off)[4].block == max(1, blk[4] - 3) and blocks(off)[4].rolls == 1
    rushed = s.with_(rush_x=RC.RUSH_QS << 8)                                 # X5 arrived with a Quick Step
    assert blocks(rushed)[4].block == max(1, blk[4] - 2)
    con = s.ctx.dfn[4].con('layup')
    assert b[4].contest == con and blocks(rushed)[4].contest == max(1, con - 2)     # a miss: his full contest, rushed 2 less
    assert b[0].contest == max(1, s.ctx.dfn[0].con('layup') - 3)            # from behind 3 less


def test_the_blocks_order_foul_then_block_then_the_contest():
    s = rim()
    r = apply(s, act(s, 'shot'))
    node = apply(r, next(a for a in legal_actions(r) if a.kind == 'contest' and a.piece == 3 and a.shot == 'hard'))
    assert isinstance(node, ChanceNode) and node.what.startswith('Block foul')          # fouls first
    fouled = next(sub for _, l, sub in node.outcomes if l == 'foul')
    assert fouled.stage == 'over' and fouled.result.kind == 'free_throws' and fouled.bonus5 == r.bonus5 + 1   # a shooting foul
    clean = next(sub for _, l, sub in node.outcomes if l == 'no foul')
    clean = next(sub for _, l, sub in clean.outcomes if l == 'no foul')                  # the second roll from beside
    assert isinstance(clean, ChanceNode) and clean.what.startswith('Block ')             # then the Block roll
    missed = next(sub for _, l, sub in clean.outcomes if l == 'not blocked')
    assert missed.result.kind == 'shot' and missed.result.contest == blocks(s)[3].contest  # then the shot, against his contest


def test_a_successful_block_is_a_turnover():
    s = rim()
    r = apply(s, act(s, 'shot'))
    node = apply(r, next(a for a in legal_actions(r) if a.kind == 'contest' and a.piece == 4 and a.shot == 'hard'))
    blocked = next(sub for _, l, sub in node.outcomes if l == 'blocked')                 # square: no foul roll first
    assert blocked.stage == 'play' and blocked.side == 'O' and blocked.tos == r.tos + 1    # -5, play on
    assert blocked.phase == r.phase + 1 and blocked.clock == r.clock - RC.PHASE_SECONDS   # the phase is lost
    assert blocked.ball == s.ball and blocked.o == s.o                                    # the ball with the shooter, as after a Steal


# ---- fakes (D-272) -----------------------------------------------------------------------------------------------------

def test_the_reply_is_the_same_reply_to_a_real_or_fake_shot_and_pass():
    s = state(THREE_O, THREE_X, THREE_AR)
    for kind in ('shot', 'pass'):
        real, fake = apply(s, act(s, kind)), apply(s, act(s, kind, fake=True))
        assert real.decl == fake.decl == 1 and real.fake == 0 and fake.fake in (1, 2)
        assert legal_actions(real) == legal_actions(fake)
        assert real.with_(fake=0) == fake.with_(fake=0)                  # nothing public tells them apart


def few_turns(monkeypatch):
    """The Python search's reply generator reads every reply in full (minutes at a shot); for the tests that only
    need the decision path, the replies tried are the first few single actions, the same both ways."""
    from playmaker_engine import search as SE

    def turns(s, *a, **k):
        acts = [x for x in legal_actions(s.with_(fake=0)) if not SE.is_fake(x)]
        pick = [x for x in acts if x.kind in ('contest', 'steal', 'intercept', 'pause', 'end_turn')][:4] + \
               [x for x in acts if x.kind == 'move'][:3]
        return [(0.0, (x,)) for x in pick]
    monkeypatch.setattr(SE, 'turns', turns)


def test_the_defence_reply_never_reads_the_hidden_choice(monkeypatch):
    """Same board, same seed: the defence's computer replies the same to a real shot and to a fake (Python search)."""
    from playmaker_engine import agent as AG
    few_turns(monkeypatch)
    s = state(THREE_O, THREE_X, THREE_AR)
    monkeypatch.setitem(AG.FIXED, 'depth', 1)
    for kind in ('shot', 'pass'):
        real, fake = apply(s, act(s, kind)), apply(s, act(s, kind, fake=True))
        a1 = AG.Agent('X', 'starter', seed=7).choose(real)
        a2 = AG.Agent('X', 'starter', seed=7).choose(fake)
        assert a1 == a2, (kind, a1, a2)


@needs_node
def test_the_defence_reply_never_reads_the_hidden_choice_in_javascript():
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import NodeEngine
    s = narrow(state(THREE_O, THREE_X, THREE_AR))
    eng = NodeEngine().install()
    old = dict(AG.FIXED)
    AG.FIXED['depth'] = 1
    try:
        for kind in ('shot', 'pass'):
            real, fake = apply(s, act(s, kind)), apply(s, act(s, kind, fake=True))
            assert AG.Agent('X', 'starter', seed=7).choose(real) == AG.Agent('X', 'starter', seed=7).choose(fake), kind
    finally:
        AG.FIXED.clear()
        AG.FIXED.update(old)
        eng.close()


def test_no_reading_reads_the_hidden_choice():
    """The code check: the readings (decide, plan, conditions, goals) never touch .fake; in engine.js only the rules
    (apply and its reveal), the state's own copy and the search's two worlds do."""
    word = re.compile(r'\.fake\b')
    for f in ('decide.py', 'plan.py', 'conditions.py', 'goals.py', 'scouting.py'):
        assert not word.search(open(os.path.join(ROOT, 'playmaker_engine', f)).read()), f
    allowed = re.compile(r'(this\.fake = s\.fake|fake: js\.fake|fake: s\.fake|mix\(s\.fake\)|s\.fake === 1|s\.fake === 2|'
                         r'W_\(s, \{ fake: s\.stage|fake: a\.arrow === 1|fake: 0)')
    for line in open(os.path.join(ROOT, 'playmaker_web', 'static', 'engine.js')):
        if word.search(line):
            assert allowed.search(line), line.strip()


def test_the_reply_to_a_fake_is_the_defences_turn():
    s = state(THREE_O, THREE_X, THREE_AR)
    f = apply(s, act(s, 'shot', fake=True))
    m = next(a for a in legal_actions(f) if a.kind == 'move' and a.piece == 1)
    f2 = apply(f, m)
    assert f2.stage == 'reaction' and f2.turn_n == 1                       # a movement stands; the reply goes on
    done = apply(f2, next(a for a in legal_actions(f2) if a.kind == 'contest' and a.piece == 0 and a.shot != 'hard'))
    assert done.stage == 'play' and done.side == 'O' and done.turn_n == 0  # then the offence: no second defence turn
    assert done.x[1] == m.dest and done.tok_x == s.tok_x - 2 and not done.lock_x   # an honest contest on a fake: free
    assert done.count('O', 'hesitate') == 1 and done.count('O', 'shot') == 0


def test_a_block_on_a_fake_locks_and_rolls_for_an_ordinary_foul():
    s = state(THREE_O, THREE_X, THREE_AR)
    f = apply(s, act(s, 'shot', fake=True))
    node = apply(f, next(a for a in legal_actions(f) if a.kind == 'contest' and a.piece == 0 and a.shot == 'hard'))
    ends = leaves(node)
    assert sum(p for p, _ in ends) == 1 and len(ends) == 3                 # behind: two foul rolls
    for p, e in ends:
        assert e.stage == 'play' and e.side == 'O' and e.lock_x & 1       # locked either way, play on
        assert e.result is None                                           # no free throws: no shot went up
    fouled = [e for _, e in ends if e.fouls == f.fouls + 1]
    assert fouled and all(e.bonus5 == f.bonus5 + 1 for e in fouled)       # +5, a team foul counted
    pf = 1 - (1 - Fraction(min(20, s.ctx.dfn[0].r['foul_block']), 20)) ** 2
    assert sum(p for p, e in ends if e.fouls == f.fouls + 1) == pf        # the block's geometry and Foul (Block)


def test_a_pass_fake_locks_a_steal_or_intercept_and_costs_a_held_lane_nothing():
    s = state(THREE_O, THREE_X, THREE_AR)
    f = apply(s, act(s, 'pass', piece=0, fake=True))
    assert f.pending and f.fake == 2
    end = apply(f, next(a for a in legal_actions(f) if a.kind == 'pause'))     # holding: no reach for the ball
    assert end.ball == 0 and end.side == 'O' and not end.pending and not end.lock_x and end.count('O', 'pass') == 0
    steal = [a for a in legal_actions(f) if a.kind in ('steal', 'intercept')]
    for a in steal:
        e = apply(f, a)
        assert not isinstance(e, ChanceNode) and e.lock_x >> a.piece & 1 and e.ball == 0 and e.side == 'O'


def test_no_fake_when_rushed():
    s = state(THREE_O, THREE_X, THREE_AR)
    assert any(a.arrow == 1 for a in legal_actions(s) if a.kind == 'shot')
    rushed = s.with_(rush_o=RC.RUSH_QS)
    assert not any(a.arrow == 1 for a in legal_actions(rushed) if a.kind in ('shot', 'pass'))


def test_one_hesitate_or_fake_a_phase_never_both():
    s = state(THREE_O, THREE_X, THREE_AR)
    h = apply(s, act(s, 'hesitate'))                                      # a Hesitate ends the offence's turn
    h = apply(h, next(a for a in legal_actions(h) if a.kind == 'move' and a.piece == 2))
    h = apply(h, next(a for a in legal_actions(h) if a.kind == 'end_turn'))
    assert h.side == 'O' and not any(a.arrow == 1 for a in legal_actions(h) if a.kind in ('shot', 'pass'))
    f = apply(s, act(s, 'shot', fake=True))
    f = apply(f, next(a for a in legal_actions(f) if a.kind == 'end_turn'))
    acts = legal_actions(f)
    assert f.side == 'O' and not any(a.kind == 'hesitate' for a in acts) and not any(a.arrow == 1 for a in acts if a.kind in ('shot', 'pass'))


def test_a_fake_after_movement_picks_the_ball_up_from_a_standstill_it_doesnt():
    s = state(THREE_O, THREE_X, THREE_AR)
    moving = s.with_(grd=pack_guard(1, 0, 0, 0))                          # he has moved with the ball: a live dribble
    f = apply(moving, act(moving, 'shot', fake=True))
    f = apply(f, next(a for a in legal_actions(f) if a.kind == 'end_turn'))
    assert f.picked_up() and not f.guard()[3]                             # picked up, and not made active
    assert not any(a.kind in ('dribble', 'move', 'sprint') and a.piece == 0 for a in legal_actions(f))
    still = s.with_(grd=pack_guard(0, 0, 0, 0))
    g = apply(still, act(still, 'shot', fake=True))
    g = apply(g, next(a for a in legal_actions(g) if a.kind == 'end_turn'))
    assert not g.picked_up() and any(a.kind == 'move' and a.piece == 0 for a in legal_actions(g))


def test_a_fake_doesnt_keep_him_active_under_the_closely_guarded_rule():
    s = state(THREE_O, THREE_X, THREE_AR).with_(grd=pack_guard(1, 0, 1, 0))     # dribbling, one idle phase already
    f = apply(s, act(s, 'shot', fake=True))
    f = apply(f, next(a for a in legal_actions(f) if a.kind == 'end_turn'))
    assert f.guard()[3] == 0                                              # the fake isn't an action that keeps him active


# ---- the pivot (D-273) -------------------------------------------------------------------------------------------------

def test_the_pivot_quick_step_after_a_pick_up():
    s = state(THREE_O, THREE_X, THREE_AR).with_(grd=pack_guard(2, 0, 0, 0))
    assert s.ctx.off[0].qs > 0
    acts = legal_actions(s)
    pv = [a for a in acts if a.piece == 0 and a.kind in ('move', 'qs', 'sprint')]
    assert pv and all(a.kind == 'qs' for a in pv) and all(B.cheb(a.dest, s.o[0]) == 1 for a in pv)
    t = apply(s, pv[0])
    assert t.picked_up() and t.pivoted() and t.rushed('O', 0)            # still picked up, rushed
    after = legal_actions(t)
    assert not any(a.piece == 0 and a.kind in ('move', 'qs', 'sprint', 'dribble') for a in after)    # no second step
    assert any(a.kind in ('pass', 'shot') and a.piece == 0 for a in after)                           # pass or shoot


def test_no_pivot_without_a_quick_step_on_his_card():
    s = state(THREE_O, THREE_X, THREE_AR).with_(grd=pack_guard(2, 0, 0, 0))
    i = next((i for i in range(5) if s.ctx.off[i].qs == 0), None)
    if i is None:
        from playmaker_engine import cards as CD
        slow = next(k for k, c in CD.CARDS.items() if c.qs == 0)
        s = state(THREE_O, THREE_X, THREE_AR, off=CD.register_team('Slow 29', [slow] + [c.key for c in CD.TEAMS['High-Low'][1:]]))
        s, i = s.with_(grd=pack_guard(2, 0, 0, 0)), 0
    s = s.with_(ball=i)
    assert not any(a.piece == i and a.kind in ('move', 'qs', 'sprint') for a in legal_actions(s))


# ---- deep range (D-274) ------------------------------------------------------------------------------------------------

def test_deep_range_by_square_matches_shauns_board():
    sq = lambda n: B.deep(B.parse_sq(n))
    assert [sq(f'A{y}') for y in range(8, 14)] == [1, 2, 3, 4, 5, 0]      # the corner: 1 to 5 off, row 13 never
    assert [sq(f'B{y}') for y in range(9, 13)] == [1, 2, 3, 4]
    assert [sq(f'D{y}') for y in range(10, 13)] == [1, 2, 3]
    assert [sq(f'I{y}') for y in range(11, 15)] == [1, 2, 0, 0]           # the top: 1 and 2 off, then no shot
    assert sq('I10') == 0 and sq('A7') == 0                               # the band itself is a three as ever


@pytest.mark.parametrize('rows,ok', [(5, {1, 2, 3, 4, 5}), (2, {1, 2}), (1, {1}), (0, set())])
def test_deep_range_by_level(rows, ok):
    s = state(THREE_O, THREE_X, THREE_AR, deep=rows)
    for n in ('A8', 'A9', 'A10', 'A11', 'A12'):
        d = B.deep(B.parse_sq(n))
        st = s.with_(o=(B.parse_sq(n),) + s.o[1:])
        shots = [a for a in legal_actions(st) if a.kind == 'shot' and a.arrow != 1]
        assert bool(shots) == (d in ok), (n, rows)
        if d in ok:
            assert shot_zone(st.ctx, st.o[0]) == '3'
            assert card_shot(st.ctx, st.ctx.off[0], 'three', st.o[0]) == max(1, st.ctx.off[0].shot('three') - d)


def test_the_playing_levels_rows():
    assert RC.deep_rows_for('senior', 'pro') == 5 and RC.deep_rows_for('senior', 'semi_pro') == 2
    assert RC.deep_rows_for('senior', 'amateur') == 1 and RC.deep_rows_for('youth', 'pro') == 1
    assert RC.deep_rows_for('junior', 'pro') == 0 and RC.deep_rows_for('senior', None) == 5     # no level: Senior Pro
    from playmaker_web.game import Game

    class G:
        levels = dict(age='senior', standard=dict(A='pro', B='amateur'))
    g = G()
    g.possession = 1
    assert Game.deep_rows_for_offence(g) == 5                             # each shooter uses his own team's rows
    g.possession = 2
    assert Game.deep_rows_for_offence(g) == 1


# ---- the mixed choice (D-272) ------------------------------------------------------------------------------------------

def _equilibrium(cols):
    v, p, q = mix_game(cols)
    real = sum(w * cols[j][0] for j, w in q.items())
    fake = sum(w * cols[j][1] for j, w in q.items())
    assert real <= v + 1e-9 and fake <= v + 1e-9                           # no fixed offence habit beats the defence's mix
    for a, b in cols:
        assert (1 - p) * a + p * b >= v - 1e-9                              # no fixed defence reply beats the offence's mix
    return v, p, q


def test_the_mix_by_hand():
    # contest the shot: the real shot is held to 10, the fake beats him for 16; hold: the shot is 18, the fake 6
    v, p, q = _equilibrium([(10.0, 16.0), (18.0, 6.0)])
    assert 0 < p < 1 and abs(v - (10 * (1 - p) + 16 * p)) < 1e-9
    assert _equilibrium([(10.0, 4.0), (12.0, 5.0)])[1] == 0.0             # a fake that never pays is never made


def test_the_fake_mix_cant_be_beaten_by_a_fixed_habit_on_a_small_board(monkeypatch):
    from playmaker_engine import agent as AG
    few_turns(monkeypatch)
    s = state(THREE_O, THREE_X, THREE_AR)
    r = apply(s, act(s, 'shot'))
    assert fake_world(r)
    ag = AG.Agent('X', 'starter', seed=3)
    sr = Searcher('X', ag.p, ag._evaluate(r), float('inf'))
    sr.root(r, 1, 1)
    cols = [c for c, _ in sr.mix_cols]
    assert len(cols) >= 2
    _equilibrium(cols)


# ---- the two engines side by side --------------------------------------------------------------------------------------

def _js_search(eng, s, depth):
    from playmaker_engine import agent as AG
    from playmaker_engine.jsbridge import state_json, ctx_json
    ag = AG.Agent(('X' if s.stage == 'reaction' or s.pending else s.side), 'starter')
    return json.loads(eng.call('searchJSON', json.dumps(dict(state=state_json(s), ctx=ctx_json(s.ctx), profile=ag.p,
                                                              budget=None, max_depth=depth)))), ag


def _py_search(s, depth, ag):
    from playmaker_engine.search import actor
    sr = Searcher(actor(s), ag.p, ag._evaluate(s), float('inf'))
    res, reached = sr.root(s, depth, depth)
    return sr, res, reached


@needs_node
@pytest.mark.parametrize('board', ['block', 'fake', 'pivot', 'deep'])
def test_both_engines_make_the_same_decision(board):
    from playmaker_engine.jsbridge import NodeEngine
    if board == 'block':
        s = narrow(rim(), keep=(3, 4))
        s = apply(s, act(s, 'shot'))                                       # the defence's reply: contest or block
    elif board == 'fake':
        s = narrow(state(THREE_O, THREE_X, THREE_AR))
        s = apply(s, act(s, 'shot'))                                       # the reply to a shot that may be a fake: the mix
    elif board == 'pivot':
        s = narrow(state(THREE_O, THREE_X, THREE_AR)).with_(grd=pack_guard(2, 0, 0, 0))
    else:
        s = narrow(state(['A10', 'O9', 'Q3', 'K12', 'I6'], ['D8', 'B4', 'P4', 'L11', 'J5'], [0, 0, 0, 0, 0], deep=5))
    eng = NodeEngine()
    try:
        out, ag = _js_search(eng, s, 1)
        sr, res, reached = _py_search(s, 1, ag)
        assert reached == out['reached']
        assert [round(v, 9) for v, _ in res] == [round(v, 9) for v, _ in out['results']]
        if board == 'fake':
            assert [[round(a, 9), round(b, 9)] for (a, b), _ in sr.mix_cols] == [[round(a, 9), round(b, 9)] for a, b in out['mix']]
    finally:
        eng.close()
