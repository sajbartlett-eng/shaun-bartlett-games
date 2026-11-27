"""Step 31, fix 4c (D-314): a failed created Dribble costs what the rules say.

Lost, the ball handler is locked (no Move, Sprint, Dribble or arrow turn; a Quick Step still his) and rushed for the
rest of that phase: he may shoot or pass, rushed, against a defence that has that phase to act freely. A new phase
clears the lock and the rush; he may try again then, against the defence as it has set itself (its help counted from
the failure), as the clock allows. The race's worth is the chance times the win's race, plus the rest times that line.
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
from playmaker_engine import value as V       # noqa: E402

needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@needs_node
def test_a_failed_dribble_is_read_by_the_rules_in_both_engines():
    names = ['R5ctl', 'R4']
    out = {r['name']: r['res'] for r in T.js([T.req(n, dict(only='value')) for n in names])}
    for n in names:
        v = out[n]
        dr = [x for x in v['drive_race'] if x['advantage'] in ('Dribble', 'Dribble next phase')]
        assert dr, v['drive_race']
        x = dr[0]
        p, f = x['win_chance'], x['if_lost']
        assert 0 < p < 1 and x['worth'] == pytest.approx(p * x['win_worth'] + (1 - p) * f['worth'], abs=0.02), x
        # the phase he loses it: locked and rushed; a later try is at the fresh chance (a new phase clears both)
        assert f['phase'] == 0 and f['locked_on'] == x['from'], f
        if f['then']:
            s = X.get(n)
            fresh = max(0, min(20, s.ctx.off[s.ball].r['dribble'] - s.ctx.dfn[0].r['agility'])) / 20
            assert f['then']['phase'] == 1 and f['then']['win_chance'] == pytest.approx(fresh), f['then']
        assert abs(V.poss_parts(X.get(n))['V'] - v['play_on']) <= 1e-6
