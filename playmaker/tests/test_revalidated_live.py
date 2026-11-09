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

def test_engine_ceilings_under_the_live_rules(monkeypatch):
    """Recorded under the live rules (single arrow, move then intercept). Late Clock Reset's first-turn ceiling is
    12.75, as under the step 3i rules (the wedge had it at 8: a second line covered the step). Step 6: the ceilings
    (analysis.py) count the free contest after the reaction, so the record runs with the rules before 9 Nov 2026."""
    if not os.environ.get('PM_LIVE_RULES'):
        monkeypatch.setattr(RC, 'DEFAULT_RULES', RC.with_rules(**RC.PRE_RULEBOOK, **RC.PRE_9NOV))
    from fractions import Fraction as F
    from playmaker_engine.analysis import engine_ceilings
    eng = engine_ceilings([6, 10, 14])
    assert eng[6][0][0] == 9 and eng[6][1][0] == 30
    assert eng[10][0][0] == F(51, 4)
    assert eng[14] == (None, None)


def test_the_reaction_closes_the_gap_under_the_live_rules(monkeypatch):
    """Late Clock Reset: with two reaction actions (a Move that sets the arrow, then a Quick Step in) O1's three
    is contested clean: 3. Step 6: recorded with the free contest after the reaction (the rules before 9 Nov 2026)."""
    if not os.environ.get('PM_LIVE_RULES'):
        monkeypatch.setattr(RC, 'DEFAULT_RULES', RC.with_rules(**RC.PRE_RULEBOOK, **RC.PRE_9NOV))
    from playmaker_engine.analysis import two_action_ceilings
    gift = two_action_ceilings([10], parts=('gift',))[10][0]
    assert gift[0] == 3


# ---- passing judgement (test_passing) ---------------------------------------------------------------------

DATA = json.load(open(os.path.join(os.path.dirname(__file__), 'data', 'pass_positions.json')))


def _tup(v):
    return tuple(_tup(x) for x in v) if isinstance(v, list) else v


# ---- the reading defence's arrow jobs (test_defence) -----------------------------------------------------

def _share(c, *keys):
    return sum(c[k] for k in keys) / max(1, sum(c.values()))


