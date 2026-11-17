"""Step 21 (Shaun, 17 Nov 2026): how both sides use the map (D-206 to D-209).

The map reads each side as it really is this phase (its tokens and movement, who is locked, rushed or has moved); the
reports keep step 20's like-for-like read for phase starts only. Overloads count numbers: a group of defenders who are
the only cover for more attackers than there are defenders. A pass in the air is read by the rules' chance of the
catch. The search always tries the map's own best answer, which matches all five defenders against every look (no
defender is tied to his man). All-Star's setup chooses within its variety margin. The coverage view and the reports read
the map after every action, and the view, the reports, the replays and the computer read the same number from the same
position."""
import json
import os
import random
import re
import shutil
import sys

import pytest

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import decide as D

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')


@pytest.fixture(scope='module')
def cov():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield AG.coverage
    NodeEngine.uninstall()
    eng.p.kill()


def test_the_rulings_are_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-206', 'D-207', 'D-208', 'D-209'):
        assert f'**{d}.' in text, d
    assert "take the local coverage it can reach this turn" in text and 'Defensive communication becomes organic' in text


# ---- part 1: the defence as it really is -------------------------------------------------------------------------------

def test_a_spent_defence_cant_answer_and_the_fresh_read_is_for_phase_starts():
    import step_21 as T
    s = T.b1()
    real, fresh = D.lasting_of(s), D.lasting_of(s, fresh=True)
    assert real['L'] == pytest.approx(fresh['L'])                     # the defence fresh: the two reads agree
    spent = s.with_(tok_x=0)
    g = D.lasting_of(spent)
    assert g['moves'] == 0 and g['L'] >= real['L'] - 1e-9            # no token left: no answer, and no less is open
    assert D.lasting_of(spent, fresh=True)['L'] == pytest.approx(fresh['L'])     # step 20's read gave it a fresh phase
    locked = s.with_(lock_x=1)                                       # X1 locked (beaten on the dribble): no Move, only
    assert all(m[0] != 0 or m[2] >= 0 for m in D.Read(locked).map_answer())   # the Quick Step a locked player keeps


# ---- part 2: numbers, not just pairs -----------------------------------------------------------------------------------

def test_a_group_of_defenders_can_be_the_only_cover_for_more_attackers_than_there_are_of_them():
    """Shaun's 3 on 2 near the key: X4 and X5 (3 and 4) the only cover for O1, O5 and O3, three apart from each other.
    Whichever two they take, the third is open; the defence takes the two biggest, so the group is worth the third."""
    look = lambda a, c, wd, mask: dict(a=a, c=B.parse_sq(c), t=0, wd=wd, now=wd - 10, mask=mask, order=(0, a))
    both = 1 << 3 | 1 << 4
    g = D.cover_groups([look(0, 'I4', 30, both), look(4, 'L4', 26, both), look(2, 'F4', 22, both)])
    two = [v for v in g if v['ds'] == [3, 4]]
    assert two and two[0]['value'] == 22 and {t['a'] for t in two[0]['threats']} == {0, 2, 4} and two[0]['near_key']
    assert not [v for v in g if len(v['ds']) == 1]                    # neither alone is the only cover for anyone
    # one on two is the smallest case, and three on four follows from the same rule
    one = D.cover_groups([look(0, 'C9', 27, 1 << 2), look(1, 'Q7', 18, 1 << 2)])
    assert one[0]['ds'] == [2] and one[0]['value'] == 18
    three = 1 << 1 | 1 << 3 | 1 << 4
    g3 = D.cover_groups([look(0, 'A3', 30, three), look(1, 'E7', 28, three), look(2, 'I3', 26, three), look(3, 'N4', 24, three)])
    assert [v for v in g3 if v['ds'] == [1, 3, 4]][0]['value'] == 24
    # two attackers within two squares of each other: one defender next to both takes both, so nothing is left
    assert D.cover_groups([look(0, 'I4', 30, 1), look(1, 'J5', 26, 1)]) == []


@needs_node
def test_overloads_on_the_board_follow_the_rule_and_explain_the_gap(cov):
    import step_21 as T
    import step_18d as T18
    for s in (T.b1(), T.b2(), T18.closeout_board()):
        c = cov(s)
        for v in c['overloads']:
            assert len({t['o'] for t in v['threats']}) > len(v['xs'])
            assert 0 < v['value'] <= max(t['worth'] for t in v['threats']) + 1e-9
            assert v['line'] in c['words']
            if len(v['xs']) >= 2:
                assert v['value'] >= c['left_worth'] - 0.01 and ' are the only cover for ' in v['line']
        assert c['lasting'] == pytest.approx(max([c['left_worth']] + [v['value'] for v in c['overloads']]), abs=0.01)


# ---- part 3: rotation falls out of the map -----------------------------------------------------------------------------

def test_the_search_always_tries_the_maps_own_answer_and_ties_nobody_to_his_man():
    import step_21 as T
    from playmaker_engine.search import candidate_actions
    from playmaker_engine.resolve import apply
    for s in (T.b1(), T.b3()):
        r = D.Read(s)
        cands = candidate_actions(s, r)
        for d, q, ar in r.map_answer():
            assert any(a.piece == d and a.dest == q and (ar < 0 and a.kind == 'move' or ar >= 0 and a.kind != 'move' and apply(s, a).arrows[d] == ar)
                       for a in cands), (d, B.sq(q), ar)


def test_a_switch_is_named_when_the_answer_makes_one():
    from playmaker_web.report import rotation_words
    before = dict(covers_now=[0, 1, 2, 3, 4])
    after = dict(covers_now=[0, 0, 1, 3, 4])                        # X1 takes O2 from X2, who picks up O3
    assert rotation_words(before, after) == 'Rotation: X1 took O2; X2 picked up O3.'
    assert rotation_words(before, dict(covers_now=[0, 1, 2, 3, 4])) is None
    assert rotation_words(before, dict(covers_now=[0, 1, 1, 3, 4])) == 'Switch: X2 took O3 from X3.'   # no pick-up
    assert rotation_words(before, dict(covers_now=[0, 1, 1, 3, 4]), movers={3}) is None        # X2 didn't move: no switch


# ---- part 4: a pass in the air -----------------------------------------------------------------------------------------

def test_a_pass_in_the_air_is_read_by_the_rules_chance_of_the_catch():
    import step_21 as T
    s = T.b3().with_(side='X', pending=(0, 1))                       # O1's pass to O2 in the air
    g = D.lasting_of(s)
    base = s.with_(pending=None, approach=-1)
    p = D.cov_pass(base, 1, base.o[1])
    caught = D.lasting_of(base.with_(ball=1))['L']
    lost = D.lasting_of(base, fresh=True)['L']
    assert g['catch'] == pytest.approx(p) and 0 <= p <= 1
    assert g['L'] == pytest.approx(p * caught + (1 - p) * (lost - 5))
    assert D.Read(s)._map_leaf() is not None                          # the search reads it (step 20 fell back)


# ---- part 1 (D-208): variety at the setup ------------------------------------------------------------------------------

def test_all_stars_setup_chooses_within_its_margin(monkeypatch):
    seen = set()
    vals = {}

    def fake_value(make, sq, ball, rng, end):                        # every placement within a point of the others
        k = tuple(sq)
        vals.setdefault(k, 20.0 + (len(vals) % 3) * 0.5)
        return vals[k], [], []
    monkeypatch.setattr(AG, '_o_value', fake_value)
    monkeypatch.setattr(AG, 'Read', lambda s: type('R', (), {'leaf': lambda self: 10.0})())
    make = lambda o, x, a, b: None
    for seed in range(6):
        r = AG._fixed_offence(make, seed, budget=0.05, level='allstar')
        seen.add(tuple(map(tuple, r['squares'])))
    assert len(seen) > 1


# ---- part 5: one map, after every action -------------------------------------------------------------------------------

@needs_node
def test_the_view_the_report_the_replay_and_the_computer_read_the_same_map():
    from playmaker_web.api import Manager, handle
    from playmaker_web import report as R
    from playmaker_web.view import coverage_json
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    assert coverage_engine()
    try:
        m = Manager()
        st, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=5,
                                                         level='pro', full=True, per_side=4))
        g, tok = m.get(r['code']), r['token']
        handle(m, 'POST', '/api/place', body=dict(code=g.code, token=tok, preview=True))
        handle(m, 'POST', '/api/place', body=dict(code=g.code, token=tok, preview=True))
        whens = []
        for _ in range(3):                                            # three actions, one at a time
            assert g.state.stage == 'play'
            v = coverage_json(g, tok)
            whens.append(v['when'])
            s = g.state
            computer = D.Read(s).map_lasting()                        # the computer's own reading (the Python engine)
            report = R.coverage_at(g, s)['L']
            assert v['lasting'] == pytest.approx(report, abs=0.01) == pytest.approx(computer, abs=0.01)
            a = next(x for x in g.legal() if x.kind in ('move', 'pause', 'hesitate'))
            g._apply(a, g.legal(), actor='human')
            n = g.feed[-1]['n']
            after = g.coverage_after(n)                               # the step-through replay of that entry
            if after is not None:
                assert after['lasting'] == pytest.approx(coverage_json(g, tok)['lasting'], abs=0.01)
        assert whens[0] == 'at the start of this phase' and whens[1].startswith('after ')
    finally:
        stop_coverage_engine()


@needs_node
def test_each_action_carries_its_own_change_in_the_report():
    from playmaker_web.api import Manager, handle
    from playmaker_web import report as R
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    assert coverage_engine()
    AG.SCALE['value'] = 1.0
    try:
        m = Manager()
        st, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=8,
                                                         level='pro', full=True, per_side=4, ai=dict(O='rookie', X='rookie')))
        g = m.get(r['code'])
        rep = R.build(g, 1)
        assert rep['checks'] == []
        each = [x for t in rep['turns'] for side in ('offence', 'defence') for x in t['actions'][side] if x['before'] is not None]
        assert each
        for t in rep['turns']:
            for x in t['actions']['offence'] + t['actions']['defence']:
                if x['before'] is not None:
                    piece = f"lasting gap from {x['before']} to {x['after']}" if x['before'] != x['after'] else f"lasting gap at {x['before']}"
                    assert piece in t['offence'] + t['defence']
    finally:
        stop_coverage_engine()
