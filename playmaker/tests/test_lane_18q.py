"""Step 18q (Shaun, 15 Nov 2026; D-196, stage 1 again): the way to the rim in the reading (eval.lane, off by default).
The race to the rim by the movement rules: the ball handler gets what he has left this phase and one movement the next;
each defender gets what he has left this phase and the reaction; a body or an arrow in the way counts as it stands; and
the lane is worth what is left after the defence's best single step into it. Design checks 1 and 2 by the reading."""
import json
import os
import subprocess
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.decide import CONFIG, PAINT, Read, _caps
from playmaker_engine.scenarios import game_state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RULES = RC.with_rules(digital=True, zone='on')                    # the app's rules
O_ = ['I11', 'C9', 'O9', 'A3', 'Q3']                              # Shaun's board of 15 November
X_ = ['J10', 'D8', 'O8', 'B4', 'P2']
A_ = ['NW', 'NW', 'N', 'SW', 'NE']


def board(x=None, arrows=None, **kw):
    s = game_state('Five Out', 'High-Low', list(O_), list(x or X_), list(arrows or A_), ball=0, rules=RULES)
    return s.with_(**kw) if kw else s


def with_x(j, sq, arrow):
    return board(X_[:j] + [sq] + X_[j + 1:], A_[:j] + [arrow] + A_[j + 1:])


@pytest.fixture
def lane():
    """The lane reading as step 18q built and proved it: switched on, with the pass chance of its day and without the
    coverage map. Step 18s, stop two replaced that pass chance with the rules' own (eval.pass_rules) and has the
    offence read the map (eval.map); both are set aside here so these checks still test what they were written for."""
    keep = {k: CONFIG['eval'].get(k) for k in ('lane', 'pass_rules', 'map')}
    CONFIG['eval'].update(lane=True, pass_rules=False, map=False)
    yield
    CONFIG['eval'].update(keep)


def test_the_lane_reading_is_off_by_default():
    cfg = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))
    assert cfg['eval']['lane'] is False and CONFIG['eval'].get('lane') is not True


def test_with_it_off_nothing_changes():
    s = board()
    v = Read(s).leaf()
    CONFIG['eval']['lane'] = True
    try:
        Read(s).leaf()
    finally:
        CONFIG['eval']['lane'] = False
    assert Read(s).leaf() == v


def test_design_check_1_a_clear_lane_is_bad_for_the_defence(lane):
    """X1 behind the ball handler and nobody able to get between: the lane reads as an open way to the rim. A body in
    it (X5 on I4) takes that away, and the reading falls."""
    clear = with_x(0, 'I12', 'S')
    helped = board(['I12'] + X_[1:4] + ['I4'], ['S'] + A_[1:4] + ['N'])
    assert Read(clear)._lane_static()[0] > Read(helped)._lane_static()[0]
    # (step 18r: with the rim square barred and the maps refitted under D-198 the map is flatter: the reading before
    # the map keeps a clear margin, and the mapped reading keeps the order)
    assert Read(clear)._hand_leaf() > Read(helped)._hand_leaf() + 1.0
    assert Read(clear).leaf() > Read(helped).leaf() + 0.3


def test_design_check_2_a_defender_in_front_beats_one_beside_or_behind(lane):
    """In front he can still get between the ball and the rim; beside or behind he can't."""
    front = Read(with_x(0, 'I10', 'N')).leaf()
    assert Read(with_x(0, 'J11', 'W')).leaf() > front + 0.5
    assert Read(with_x(0, 'I12', 'S')).leaf() > front + 0.5


def test_a_defence_out_of_tokens_cannot_step_in(lane):
    """Attack before the help arrives: with no token left this phase nobody can get between, so the lane is worth what
    it reads as the pieces stand."""
    s = with_x(0, 'I10', 'N')
    spent = Read(s.with_(tok_x=0))
    assert spent._lane_static()[0] == spent._lane_next()[1]
    assert spent._lane_static()[0] > Read(s)._lane_static()[0]


def test_a_shot_straight_after_a_sprint_is_off_balance(lane):
    """D-151, D-185: a lane square he must Quick Step or Sprint onto gives a rushed shot, 2 lower; one a Move away
    gives a set shot."""
    data = Read(with_x(0, 'I12', 'S'))._lane_data()
    cut = RC.ZONE_POINTS[PAINT] * RC.control_cut(RULES)
    assert cut > 0
    by = {}
    for e in data['cands']:
        by.setdefault(e['c'], {})[e['lk'].rushed] = e['open']
    both = [v for v in by.values() if len(v) == 2]
    assert any(e['lk'].rushed for e in data['cands'])
    for v in both:
        assert all(a > b for a, b in zip(v[False], v[True]))
        assert all(abs((a - b) - cut) < 1e-9 for a, b in zip(v[False], v[True]))


def test_the_cheap_reread_agrees_with_the_reading_where_he_stands(lane):
    s = with_x(0, 'I12', 'S')
    r = Read(s)
    base, excl = r._lane_next()[1], r._lane_static()[1]
    for j in range(5):
        cm, ql = _caps(s, 'X', j)
        assert r.lane_reread(j, s.x[j], s.arrows[j], cm, ql) == min(base, excl[j])


def test_the_cheap_reread_sees_a_step_into_the_lane(lane):
    """The open list's quick look at a defender's own action must see him closing the lane, or the action is never
    read in full."""
    s = with_x(0, 'I12', 'S').with_(tok_x=2)                 # the defence's last turn of the phase
    r = Read(s.with_(tok_x=0))                                # the position its turn leaves: nobody can step in after it
    stay = r.lane_reread(4, s.x[4], s.arrows[4], False, 0)
    step = r.lane_reread(4, B.parse_sq('I4'), 0, False, 0)
    assert step < stay
    out = r.reread(4, B.parse_sq('I4'), 0, False, 0, (False, True))
    assert len(out) == 10 and out[7] == step


def test_both_engines_agree_with_the_lane_on():
    out = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'js_equivalence.py'), '--soft', '--fiba', '--off-balance', 'on',
                          '--position-contest', 'on', '--zone', '--lane', '--n', '24'], cwd=ROOT, capture_output=True, text=True, timeout=600).stdout
    rep = json.loads(out[out.index('{'):])
    assert rep['mismatches'] == 0 and rep['states'] == 24


def test_the_system_map_and_the_confirmed_checks_are_written():
    text = open(os.path.join(ROOT, 'docs', 'plans', 'SYSTEM_MAP.md')).read()
    for part in ('THE SCOUT', 'THE GOALS', 'THE READS', 'THE DECISIONS', 'Constant goals', 'Fluid goals'):
        assert part in text
    plan = open(os.path.join(ROOT, 'docs', 'plans', 'COMPUTER_FIX_PLAN.md')).read()
    assert 'Confirmed by Shaun, 15 Nov 2026' in plan


def test_the_on_ball_defender_only_stays_in_the_race_if_he_wins_the_dribble(lane):
    """X1 on the ball and every other defender out wide, away from the lane. X1 can get between, so the lane as it
    stands is closed; but a Dribble can beat him, and then nobody is behind him. The reading counts that from the
    start, so a big in the lane reads better for the defence before anyone has been beaten."""
    wide, arrows = ['J10', 'B9', 'P9', 'A2', 'Q2'], ['NW', 'E', 'W', 'S', 'S']
    alone = Read(board(wide, arrows))
    lane_now = alone._lane_static()[0]
    beaten, p = alone.lane_dribble(lane_now)
    assert 0 < p < 1 and beaten > lane_now                       # the lane opens if X1 is beaten
    helped = Read(board(wide[:4] + ['I4'], arrows[:4] + ['N']))
    assert helped.lane_dribble(helped._lane_static()[0])[0] < beaten
    assert helped.leaf() < alone.leaf() - 0.3


def test_no_dribble_no_such_chance(lane):
    s = board()
    assert Read(s.with_(tok_o=0)).lane_dribble(0.0) == (-1.0, 0.0)
    far = Read(with_x(0, 'I8', 'N'))                             # nobody next to the ball handler
    assert far.lane_dribble(far._lane_static()[0]) == (-1.0, 0.0)


def test_the_app_switch_turns_it_on_for_a_game_and_the_next_game_sets_it_back():
    """?lane=1: the app's games only; any other game puts the file's own setting back."""
    from playmaker_web.game import Game
    kw = dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, full=True, level='pro')
    try:
        Game(match_format='digital', lane='on', **kw)
        assert CONFIG['eval']['lane'] is True
        Game(match_format='digital', **kw)
        assert CONFIG['eval']['lane'] is False
        Game(lane='on', **kw)                                    # nothing for the table
        assert CONFIG['eval']['lane'] is False
    finally:
        CONFIG['eval']['lane'] = False


def test_the_setup_as_it_was_reads_without_the_lane(lane):
    from playmaker_engine import agent as AG
    seen = []
    AG._as_it_was(lambda: seen.append(CONFIG['eval']['lane']))
    assert seen == [False] and CONFIG['eval']['lane'] is True
