"""Step 22b (D-214 to D-216, Shaun, 18 Nov 2026): the ranked drivers, what each defender's position and arrows do, and
setup over every square."""
import os
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
def js():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield eng
    eng.close()


def table(xs, arrows):
    import step_21 as T
    from playmaker_web.game import TABLE_O
    return T._state(list(TABLE_O), list(xs), list(arrows), ball=0)


def test_the_rulings_are_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-214', 'D-215', 'D-216', 'D-217'):
        assert f'**{d}.' in text, d


@needs_node
def test_the_drivers_come_with_the_map_and_the_engines_agree_on_the_answer(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    r = AG.coverage(s, only='lasting')
    d = r['drivers']
    assert d['L'] == pytest.approx(r['L']) and d['n'] == r['moves']
    assert all(0 <= p <= 1 for p in d['rs']) and d['dbl'] >= 0 and d['acts'] >= 0
    g = D.lasting_of(s)
    assert g['L'] == pytest.approx(r['L'], abs=0.01) and g['moves'] == r['moves']     # (b) chose the same answer


def test_on_a_level_gap_the_answer_with_fewer_actions_wins():
    s = table(['E7', 'D8', 'O8', 'I6', 'P2'], [0, 7, 0, 0, 1])
    g = D.lasting_of(s)
    assert g['moves'] == 0                                            # it holds the gap by position and arrows


def test_ties_are_put_in_the_drivers_order_and_nothing_else_moves(js, monkeypatch):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1]).with_(side='X', turn_n=0)
    from playmaker_engine.actions import legal_actions
    acts = [a for a in legal_actions(s) if a.kind in ('move', 'pause')][:6]
    res = [(10.0, [acts[0]]), (5.0, [acts[1]]), (5.0, [acts[2]]), (5.0, [acts[3]]), (1.0, [acts[4]])]
    out = AG._driver_order(s, 'X', res)
    assert out[0] == res[0] and out[-1] == res[-1]                    # only the tied turns can change places
    assert sorted(map(str, (t[0] for _, t in out[1:4]))) == sorted(map(str, (t[0] for _, t in res[1:4])))
    monkeypatch.setitem(AG.JS, 'coverage', None)
    assert AG._driver_order(s, 'X', res) == res                       # without the map nothing changes


@needs_node
def test_each_defender_has_plain_words_for_what_he_protects_and_allows(js):
    from playmaker_engine import plain as P
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    roles = AG.coverage(s, only='roles')
    assert [r['x'] for r in roles] == [0, 1, 2, 3, 4]
    for r in roles:
        assert r['line'].startswith(f"X{r['x'] + 1}: ")
        assert not any(re.search(r'\b' + re.escape(w) + r'\b', r['line'], re.I) for w in P.BANNED), r['line']
        assert '—' not in r['line']
    x4 = roles[3]
    assert x4['body'] and any(z['o'] == 0 for z in x4['body'])        # X4 in the lane takes away O1's way to the rim


@needs_node
def test_the_defences_setup_tries_every_square_and_says_which_driver_decided(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    r = AG.coverage(s, only='setup', evals=120)
    assert r['L'] <= r['start'] + 1e-9
    assert all(z['by'] in ('a', 'b', 'c', 'd', 'looks behind') for z in r['steps'])


@needs_node
def test_the_offence_sweep_reads_every_empty_square_for_one_attacker(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    rows = AG.coverage(s, only='offsweep', piece=1, keep=500)
    taken = {B.parse_sq(q) for q in ['I11', 'O9', 'A3', 'Q3', 'J10', 'D8', 'O8', 'I6', 'P2']}
    free = [q for q in AG._court() if q not in taken]
    assert len(rows) >= 0.9 * len(free)                               # (the last phase or a square off the map reads none)
    L = [z['drivers']['L'] for z in rows]
    assert L == sorted(L, reverse=True)
