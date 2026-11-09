"""Live-rule replacements for tests pinned to the old rules (legacy_rules / old_intercepts) that no longer show what
they were written to check under the live rules (move-then-intercept, minus5_lose_phase, the wedge). The pinned
copies stay as the record. Pinned tests that still pass under the live rules (the golden game and its API line,
the inbound intercepts, the reserve, the cut that opens a lane, ...) are not repeated; rule-mechanics records
whose live versions exist elsewhere (test_intercepts_mti.py, test_rulings_3i.py, test_wedge.py) neither.

The rulebook revision of Nov 2026 narrowed 'through you' to the line through the square's centre (OQ-13) and kept a
lane jump's facing (OQ-76). These positions were built under the earlier reading of the line, so they run pinned to it
as the record (RC.PRE_RULEBOOK); PM_LIVE_RULES=1 re-validates them under the current reading."""
import json
import os

import pytest

from playmaker_engine import computer as C
from playmaker_engine import rules_config as RC


@pytest.fixture(autouse=True)
def _pre_rulebook_line(monkeypatch):
    if not os.environ.get('PM_LIVE_RULES'):
        monkeypatch.setattr(RC, 'DEFAULT_RULES', RC.with_rules(**RC.PRE_RULEBOOK))
from playmaker_engine.actions import Action
from playmaker_engine.solver import Play, apply_play

X1, X2, X3, X4, X5 = 1, 2, 4, 8, 16


def test_these_tests_run_under_the_live_rules():
    r = RC.DEFAULT_RULES                     # the live rules, pinned only to the pre-rulebook reading of the line
    assert r.intercept_rule == 'move_then_intercept' and r.turnover_cost == 'minus5_lose_phase' and r.arrow_mode == 'single'


# ---- ceilings (test_golden_and_regression) ----------------------------------------------------------------

def test_engine_ceilings_under_the_live_rules():
    """Recorded under the live rules (single arrow, move then intercept). Late Clock Reset's first-turn ceiling is
    12.75, as under the step 3i rules (the wedge had it at 8: a second line covered the step)."""
    from fractions import Fraction as F
    from playmaker_engine.analysis import engine_ceilings
    eng = engine_ceilings([6, 10, 14])
    assert eng[6][0][0] == 9 and eng[6][1][0] == 30
    assert eng[10][0][0] == F(51, 4)
    assert eng[14] == (None, None)


def test_the_reaction_closes_the_gap_under_the_live_rules():
    """Late Clock Reset: with two reaction actions (a Move that sets the arrow, then a Quick Step in) O1's three
    is contested clean: 3."""
    from playmaker_engine.analysis import two_action_ceilings
    gift = two_action_ceilings([10], parts=('gift',))[10][0]
    assert gift[0] == 3


# ---- passing judgement (test_passing) ---------------------------------------------------------------------

DATA = json.load(open(os.path.join(os.path.dirname(__file__), 'data', 'pass_positions.json')))


def _tup(v):
    return tuple(_tup(x) for x in v) if isinstance(v, list) else v


def position(name, **kw):
    from playmaker_engine.headtohead import start_state
    d = DATA[name]
    return start_state(d['spec']).with_(**{k: _tup(v) for k, v in d['fields'].items()}).with_(**kw), d


def test_a_lane_nobody_can_reach_is_clean():
    """The step 3f position with X1 spent (Move and Quick Step): under the live rules nobody can reach the lane
    to O2 with one straight movement along his arrow, while the pass to O4 still runs through X1."""
    s, d = position('prefer_clean', moved_x=X1, qs_x=X1)
    info = C.pass_risk(s, s.ball, d['clean'])
    assert info['clean'] and info['risk'] == 0 and info['by'] is None
    assert not C.pass_risk(s, s.ball, d['contested'])['clean']


def test_last_phase_a_contested_pass_is_priced_at_the_whole_possession():
    """The step 3f late position (no turnovers banked). Earlier in the possession a pick-off costs -5 and two
    seconds and the passer keeps the ball; in the final phase it costs the whole possession. The All-Star
    holds rather than throw the contested pass there."""
    s, d = position('late', tos=0)
    assert s.clock == 2
    r = int(d['chosen'].split('to O')[1]) - 1
    assert not C.pass_risk(s, s.ball, r)['clean']
    c = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[])
    c._context(s)
    late, early = c._pick_off_value(s, True), c._pick_off_value(s.with_(clock=8), True)
    assert late == 0.0 and early == RC.TURNOVER_POINTS + c._keep(s.with_(clock=8)) and early > late
    a = C.Computer('O', 'allstar', seed=1, budget_s=None, habits=[]).choose(s)
    assert not (a.kind == 'pass' and not C.pass_risk(s, s.ball, a.target)['clean']), a


# ---- the reading defence's arrow jobs (test_defence) -----------------------------------------------------

@pytest.fixture(scope='module')
def live_profiles():
    """Ten table-setup starts against a Rookie offence (the greedy offence of the pinned profile shoots or loses
    the ball so fast under the live rules that the defence makes a handful of moves in 46 possessions)."""
    from playmaker_engine.defence import ReadingDefence
    from playmaker_engine.defence_check import job_profile, profile_starts
    from playmaker_engine.policies import GreedyPolicy
    mp = pytest.MonkeyPatch()                      # module scope: the pin above is function-scoped
    if not os.environ.get('PM_LIVE_RULES'):
        mp.setattr(RC, 'DEFAULT_RULES', RC.with_rules(**RC.PRE_RULEBOOK))
    try:
        starts = profile_starts()[:10]
        off = lambda: C.Computer('O', 'rookie', seed=1, habits=[], overrides={'randomness': 0.0}, budget_s=None)
        yield dict(greedy=job_profile(GreedyPolicy(), starts, offence=off()),
                   reader=job_profile(ReadingDefence(budget_s=None), starts, offence=off()))
    finally:
        mp.undo()


def _share(c, *keys):
    return sum(c[k] for k in keys) / max(1, sum(c.values()))


def test_walls_lanes_and_help_rise(live_profiles):
    g, r = live_profiles['greedy'][0]['play'], live_profiles['reader'][0]['play']
    assert sum(r.values()) >= 20 and sum(g.values()) >= 20, (g, r)
    assert _share(r, 'wall', 'lane', 'help') > _share(g, 'wall', 'lane', 'help') + 0.2, (g, r)
    assert _share(r, 'on_ball') < _share(g, 'on_ball'), (g, r)

