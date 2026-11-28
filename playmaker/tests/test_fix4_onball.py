"""Step 31, fix 4 (the design's "What on-ball position is worth", D-312).

1. What each defender's stance removes from the ball handler's real options (his shot now, his drives, his passes,
   what holding the ball costs him) is read by the number itself, with that defender lifted off the court. Both
   engines read the same on P1 to P4, pressed and two off.
2. The rules' walls hold inside the drive's race: in the phase of the advantage the ball handler's movement can't
   cross a line a defender's arrows bar him (D-170). On P1, X1 pressed in front with arrows N and NE walls the east
   side, so O1's speed start goes west; with arrows NW and N it goes east.
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
from playmaker_engine import board as B, value as V   # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')
P = ['P1', 'P1off', 'P2', 'P2off', 'P3', 'P3off', 'P4', 'P4off']


def _near(a, b):
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= 0.011)


@needs_node
def test_both_engines_read_the_same_on_ball_reading_on_P1_to_P4():
    js = {r['name']: r['res'] for r in T.js([T.req(n, dict(only='value', onball=True)) for n in P])}
    for n in P:
        a, b = js[n]['onball'], V.onball(X.get(n))
        assert a['on_ball'] == b['on_ball'], (n, a, b)
        assert all(_near(a['options'][k], b['options'][k]) for k in a['options']), (n, a['options'], b['options'])
        for x, y in zip(a['defenders'], b['defenders']):
            assert x['defender'] == y['defender'] and all(_near(x['removes'][k], y['removes'][k]) for k in x['removes']), (n, x, y)
        assert _near(js[n]['value'], a['options']['value']), (n, js[n]['value'], a['options'])


@needs_node
def test_the_speed_start_goes_round_the_pressing_defenders_wall():
    east = X._p('I10', 0, 'I9', 'N', X.P_BASE['P1'])        # arrows N and NE: the east side walled
    west = X._p('I10', 0, 'I9', 'NW', X.P_BASE['P1'])       # arrows NW and N: the west side walled
    out = T.js([T.req('P1', dict(only='value'), state=east), T.req('P1', dict(only='value'), state=west)])
    for res, side in zip(out, ('west', 'east')):
        sp = [rc for rc in res['res']['drive_race'] if rc['advantage'] == 'speed']
        assert sp, res['res']['drive_race']
        col = B.parse_sq(sp[0]['from'])[0]
        assert (col < B.parse_sq('I10')[0]) if side == 'west' else (col > B.parse_sq('I10')[0]), (side, sp[0]['from'])
    for s, res in zip((east, west), out):
        assert round(V.poss_parts(s)['V'], 4) == res['res']['play_on']   # (engine.js reports the number to 4 decimals)
