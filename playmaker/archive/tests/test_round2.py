"""Step 2b sections 5-6: the round-2 results read, classify and report (from the saved runs)."""
import os

import pytest

from playmaker_engine import solver_round2 as R2
from playmaker_engine.solver_report import STALE_3D, SOLVE_ORDER

pytestmark = pytest.mark.skipif(not os.path.exists(os.path.join(R2.RESULTS, 'runs_r2.json')), reason='no round-2 results')


def test_every_card_is_classified_with_the_new_teams_for_the_six():
    R = R2.runs()
    S = R2.classify(R)
    assert set(S) == set(SOLVE_ORDER) and all(S[n] for n in SOLVE_ORDER)
    assert all(S[n]['label'] in ('exact', 'estimated', 'unstable') for n in SOLVE_ORDER)
    new = R2._load('runs_3d.json')
    for n in STALE_3D:                                 # the six come from the re-solve with the step-3d teams
        m = R2.main_run(R, n, R2.LONG)
        assert any(v.get('job') == m['job'] and v['value'] == m['value'] for v in new.values())


def test_six_card_comparison_and_report(tmp_path):
    rows = R2.six_card_comparison()
    assert [r['n'] for r in rows] == STALE_3D and all(r['old'] and r['new'] for r in rows)
    p = R2.write_report(path=str(tmp_path / 'r.md'))
    text = open(p).read()
    for head in ('## Summary', 'six re-solved', 'Proposed card fixes', 'Plan-change rate', 'Dead rules', 'The Pause result',
                 'OQ-7', "secret's value"):
        assert head in text, head
    assert '(stale)' not in text


def test_no_stale_marks_left():
    import json
    d = json.load(open(os.path.join(R2.RESULTS, 'STALE.json')))
    assert d['stale'] == []
