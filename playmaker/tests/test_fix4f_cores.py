"""Step 31, fix 4f (Shaun, 28 Nov 2026).

1. A movement can't change what happened before it: a look whose shot or fake goes up before a defender's movement
   reads its fake's follow-up on the board as it stood then, as its contests already do. Both engines read the same
   with it on R1 to R5 and P1 to P5 (tests/test_fix4c_dribble.py and the proofs hold the rest).
2. Several cores give the decision one core gives: E13's turn, its candidate turns handed out to four workers and put
   back in the batch's order, gives the same turns, values and line. (The setups are held the same way in the report's
   runs: E1, E15b and, in a browser, P5's stance search.)
"""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import exam_boards as X                       # noqa: E402
import step_31 as T                           # noqa: E402
from playmaker_engine import value as V       # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@needs_node
def test_both_engines_read_the_same_with_the_follow_up_as_it_stood():
    names = ['R4c', 'P2', 'P4']
    js = T.js([T.req(n, dict(only='value')) for n in names])
    for n, r in zip(names, js):
        # (engine.js reports the number to 4 decimals: Python's, rounded the same way, must equal it exactly)
        assert r['res']['play_on'] == round(V.poss_parts(X.get(n))['V'], 4), (n, r['res']['play_on'])


def _turn(cores):
    import step_31_exam as XM
    env = dict(os.environ)
    env.pop('PM_CORES', None)
    if cores:
        env['PM_CORES'] = str(cores)
    req = T.req('E13', None, fn='searchJSON', profile=XM.PROFILE, max_depth=1)
    p = subprocess.run(['node', '-e', T.NODE, os.path.abspath(ROOT)], input=json.dumps([req]), capture_output=True, text=True, timeout=900, env=env)
    assert p.returncode == 0, p.stderr[-2000:]
    r = json.loads(p.stdout)[0]['res']
    return {k: r[k] for k in ('results', 'pv')}


@needs_node
def test_four_cores_give_the_turn_one_core_gives():
    assert _turn(4) == _turn(0)
