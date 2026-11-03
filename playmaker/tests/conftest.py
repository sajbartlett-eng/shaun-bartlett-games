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
