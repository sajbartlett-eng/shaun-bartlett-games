"""Step 31, fix 4h (Shaun, 28 Nov 2026): the named answers, faster and exact, and three more kinds of answer.

1. The speed is exact. Each named movement's races are read by difference from the board's race kit (fix 4e's), or
   kept when it changes nothing they read; a movement whose number with every race gone (its floor) is above the cap
   isn't read further. On R1 and P2 the answer reads the same as with every named movement's races read afresh, and
   each race read by difference equals it read afresh.
2. The new kinds, both engines the same answer at the same number, each where it closes a gap to the exact answer:
   R5b (a switch: X3's Sprint to J8 gives him the ball handler), P1 two off (a helper arriving in time), P4 (a
   two-step route: X2's step to D6 stops O2's closeout-then-fake-and-drive) and P2 two off (a switch, then a two-step
   route).
(The proof against the exact answer on R1 to R5 and P1 to P5: tools/step_31_fix4h_proof.py.)
"""
import os
import shutil
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import exam_boards as X                       # noqa: E402
import step_31 as T                           # noqa: E402
from playmaker_engine import board as B       # noqa: E402
from playmaker_engine import value as V       # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

EXACT = {'R5b': (29, [[2, 'J8', 6]]), 'P1off': (28.5, None), 'P4': (30, [[1, 'D6', 7]]), 'P2off': (30, None)}


@needs_node
def test_the_named_answers_read_by_difference_read_as_afresh():
    names = ['R1', 'P2']
    diff = T.js([T.req(n, dict(only='value')) for n in names], env_extra=dict(PM_RACE_CHECK='1'))
    fresh = T.js([T.req(n, dict(only='value')) for n in names], env_extra=dict(PM_NAMED_FRESH='1'))
    for a, b in zip(diff, fresh):
        assert a['res']['play_on'] == b['res']['play_on'] and a['res']['answer'] == b['res']['answer'], (a['name'], a['res']['answer'], b['res']['answer'])
    rc = diff[-1]['race_check']
    assert rc['n'] > 0 and rc['bad'] == 0, rc


@needs_node
def test_the_new_kinds_close_the_gaps_in_both_engines():
    names = list(EXACT)
    js = T.js([T.req(n, dict(only='value')) for n in names], timeout=1200)
    for n, r in zip(names, js):
        pp = V.poss_parts(X.get(n))
        v, ans = EXACT[n]
        assert r['res']['play_on'] == round(pp['V'], 4) == v, (n, r['res']['play_on'], pp['V'])
        assert r['res']['answer'] == [[d, B.sq(q), a] for d, q, a in pp['moves']], (n, r['res']['answer'], pp['moves'])
        if ans is not None:
            assert r['res']['answer'] == ans, (n, r['res']['answer'])
