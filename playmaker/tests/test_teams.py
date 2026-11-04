"""Team data (step 3d part A): positions, tier shapes, unique cards, the four jobs."""
import importlib.util
import os

from playmaker_engine.cards import TEAMS as _ALL, CARDS, TEAMS_MOD, DATA_DIR, PRESCRIBED
from playmaker_engine.scouting import position

TEAMS = {n: _ALL[n] for n in PRESCRIBED}      # prescribed only (custom lineups may be registered too)
SHAPES = {'BBBBB', 'ABBBC', 'AABCC'}


def _teamtools():
    spec = importlib.util.spec_from_file_location('teamtools', os.path.join(DATA_DIR, 'teamtools.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_one_card_per_position_and_a_legal_shape():
    for name, cards in TEAMS.items():
        assert [position(c) for c in cards] == ['PG', 'SG', 'SF', 'PF', 'C'], name
        assert ''.join(sorted(c.tier for c in cards)) in SHAPES, name


def test_no_card_in_two_teams():
    keys = [c.key for cs in TEAMS.values() for c in cs]
    assert len(keys) == len(set(keys)) == 50 and all(k in CARDS for k in keys)


def test_four_jobs_covered_except_the_declared_drop():
    tt = _teamtools()
    for name, cards in TEAMS.items():
        jobs = [tt.jobs(c.key) for c in cards]
        have = {j: any(x[j] for x in jobs) for j in ('creator', 'shooter', 'anchor', 'stopper')}
        dropped = TEAMS_MOD.DROPS.get(name)
        assert all(v for j, v in have.items() if j != dropped), (name, have)


def test_step3d_rebuilds():
    assert [c.key for c in TEAMS['Twin Towers']] == ['spgC', 'twA', 'scsfA', 'pspfC', 'pscB']
    assert [c.key for c in TEAMS['Ball Movement']] == ['ppgA', 'shsC', 'pfsfB', 'arpfA', 'pscC']
