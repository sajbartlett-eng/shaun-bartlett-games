import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402

from playmaker_engine import board as B  # noqa: E402
from playmaker_engine.scenarios import game_state  # noqa: E402


def mk(o_sq, x_sq, arrows, ball=0, off='Five Out', dfn='High-Low', rules=None, **kw):
    """A hand-built state. o_sq/x_sq: lists of square names; arrows: compass names."""
    s = game_state(off, dfn, o_sq, x_sq, arrows, ball=ball, rules=rules, check=False)
    return s.with_(**kw) if kw else s


def P(name):
    return B.parse_sq(name)


def dests(acts, kind, piece, side=None):
    return {B.sq(a.dest) for a in acts if a.kind == kind and a.piece == piece and (side is None or a.side == side)}


@pytest.fixture
def golden():
    from playmaker_engine.soak import golden_setup
    return golden_setup()


import pytest as _pytest


@_pytest.fixture
def legacy_rules(monkeypatch):
    """The rules as they were before the step 3i follow-up rulings (single arrow, two-turn screens, arrow-line
    drives, the interceptor left on the line), for tests that record that behaviour."""
    import os
    from playmaker_engine import rules_config as RC
    if not os.environ.get('PM_LIVE_RULES'):          # PM_LIVE_RULES=1: re-validate under the live rules
        monkeypatch.setattr(RC, 'DEFAULT_RULES', RC.with_rules(**RC.LEGACY_3I))


@_pytest.fixture
def old_intercepts(monkeypatch):
    """The intercept rule before the OQ-72 ruling (on the line; arrow across plus one movement; on the passer only
    through him; a successful interception plays on at -5, a steal on a shot ends the possession), everything
else as it is now."""
    import os
    from playmaker_engine import rules_config as RC
    if not os.environ.get('PM_LIVE_RULES'):          # PM_LIVE_RULES=1: re-validate under the live rules
        monkeypatch.setattr(RC, 'DEFAULT_RULES', RC.with_rules(intercept_rule='approach', turnover_cost='legacy'))
