"""Step 3f: passing judgement for the computer offence. A lane is judged after the defence's reply
(pass_risk); a pass is valued (1 - risk) x the catch - risk x 5 x tolerance; a contested pass is weighed
against moving the receiver, moving the passer, a screen and two shorter clean passes. Positions come from
computer playouts (tests/data/pass_positions.json: the start plus every state field)."""
import json
import os

import pytest

from playmaker_engine import computer as C
from playmaker_engine.actions import Action, intercept_status, legal_actions
from playmaker_engine.headtohead import start_state
from playmaker_engine.solver import Play, apply_play

DATA = json.load(open(os.path.join(os.path.dirname(__file__), 'data', 'pass_positions.json')))


def _tup(v):
    return tuple(_tup(x) for x in v) if isinstance(v, list) else v


def position(name):
    d = DATA[name]
    return start_state(d['spec']).with_(**{k: _tup(v) for k, v in d['fields'].items()}), d


def computer(s, level='allstar', habits=()):
    c = C.Computer('O', level, seed=1, budget_s=None, habits=list(habits))
    c._context(s)
    view = C.seen_state(s, 'O', c.seen)
    c._ensure_plan(view)
    return c, view


def value(s, play, level='allstar'):
    c, view = computer(s, level)
    return c._play_value(view, play, apply_play(view, play), c._value_fn())


def test_a_lane_open_now_but_reachable_by_move_then_intercept_is_contested():
    s, d = position('approach')
    r = d['receiver']
    info = C.pass_risk(s, s.ball, r)
    pend = info['pending']
    assert not any(intercept_status(pend, j) == 'direct' for j in range(5))     # nobody on the line now
    assert not info['clean'] and len(info['line']) == 2                        # but a Move, then Intercept
    mv, icpt = info['line']
    assert mv.kind in ('move', 'qs', 'sprint') and icpt.kind == 'intercept' and mv.piece == icpt.piece == info['by']
    # the risk is the roll the defence would get: 1 - P(d20 <= Pass - Intercept)
    gap = s.ctx.off[s.ball].r['pass'] - s.ctx.dfn[info['by']].r['intercept']
    assert abs(info['risk'] - (1 - max(0, min(20, gap)) / 20)) < 1e-9


def test_a_lane_nobody_can_reach_is_clean():
    s, d = position('prefer_clean')
    info = C.pass_risk(s, s.ball, d['clean'])
    assert info['clean'] and info['risk'] == 0 and info['by'] is None


def test_all_star_prefers_the_clean_pass_to_an_equal_threat():
    """Two receivers whose catch is worth the same: one lane clean, one contested."""
    s, d = position('prefer_clean')
    clean = value(s, Play('kick', (Action('pass', 'O', s.ball, target=d['clean']),)))
    contested = value(s, Play('kick', (Action('pass', 'O', s.ball, target=d['contested']),)))
    assert clean > contested
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (a.kind == 'pass' and a.target == d['contested']), a


def test_all_star_takes_the_cut_that_opens_the_lane_over_the_contested_pass():
    s, d = position('cut')
    r = d['receiver']
    cut = next(a for a in legal_actions(s) if str(a) == d['cut'])
    from playmaker_engine.resolve import apply
    assert not C.pass_risk(s, s.ball, r)['clean']                              # contested now
    assert C.pass_risk(apply(s, cut), s.ball, r)['clean']                       # clean after the one-square cut
    assert value(s, Play('relocate', (cut,))) > value(s, Play('kick', (Action('pass', 'O', s.ball, target=r),)))
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (a.kind == 'pass' and a.target == r), a


def test_all_star_prefers_two_clean_passes_to_one_contested():
    s, d = position('two')
    r, m = d['receiver'], d['via']
    assert not C.pass_risk(s, s.ball, r)['clean'] and C.pass_risk(s, s.ball, m)['clean']
    two = value(s, Play('kick', (Action('pass', 'O', s.ball, target=m),)))
    one = value(s, Play('kick', (Action('pass', 'O', s.ball, target=r),)))
    assert two > one, (two, one)                                               # the 3f valuation
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (a.kind == 'pass' and a.target == r), a                         # never the contested one
    # Starter doesn't weigh two-pass routes: its value for the first pass has no follow-up pass in it
    c, view = computer(s, 'starter')
    assert 'two_pass' not in c.cfg['pass_alternatives']


def test_last_phase_a_contested_pass_is_allowed():
    s, d = position('late')
    assert s.clock == 2
    r = int(d['chosen'].split('to O')[1]) - 1
    assert not C.pass_risk(s, s.ball, r)['clean']
    p = Play('kick', (Action('pass', 'O', s.ball, target=r),))
    keep = value(s, Play('hesitate', (Action('hesitate', 'O'),)))
    assert value(s, p) > keep                                                  # allowed: worth more than holding it
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert a.kind in ('pass', 'shot'), a                                       # (since 3g it may finish instead)


def test_habit_forces_passes_throws_to_the_target_through_a_contested_lane():
    s, d = position('habit')
    t = d['target']
    assert not C.pass_risk(s, s.ball, t)['clean']
    without = C.Computer('O', 'rookie', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (without.kind == 'pass' and without.target == t), without
    c = C.Computer('O', 'rookie', seed=1, budget_s=None, habits=['forces_passes'])
    a = c.choose(s)
    assert a.kind == 'pass' and a.target == t and c.stats['habit_fired'].get('forces_passes'), a


def test_levers_and_the_habit_pool():
    L = C.LEVELS['offence']['levels']
    assert [L[k]['pass_risk_tolerance'] for k in ('rookie', 'starter', 'allstar')] == [0.5, 0.8, 1.0]
    assert L['rookie']['pass_alternatives'] == ['receiver']
    assert 'two_pass' not in L['starter']['pass_alternatives'] and 'two_pass' in L['allstar']['pass_alternatives']
    assert any('forces_passes' in C.Computer('O', 'rookie', seed=k).habits for k in range(40))
    assert not any('forces_passes' in C.Computer('O', 'starter', seed=k).habits for k in range(40))


def test_tolerance_makes_a_contested_pass_worth_more():
    s, d = position('habit')
    t = d['target']
    p = Play('kick', (Action('pass', 'O', s.ball, target=t),))
    honest, reckless = computer(s, 'allstar'), computer(s, 'allstar')
    reckless[0].cfg['pass_risk_tolerance'] = 0.5
    vh = honest[0]._play_value(honest[1], p, apply_play(honest[1], p), honest[0]._value_fn())
    vr = reckless[0]._play_value(reckless[1], p, apply_play(reckless[1], p), reckless[0]._value_fn())
    risk = C.pass_risk(s, s.ball, t)['risk']
    assert abs((vr - vh) - risk * 5 * 0.5) < 1e-6
