"""Step 22b (D-214 to D-216, Shaun, 18 Nov 2026): what each defender's position and arrows do, and setup over every
square. Step 22b, continued (D-219): the one list replaced ranked drivers b to d, so the tests of those drivers went
with them; the list's own tests are in tests/test_two_responsibilities_22b.py."""
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
def test_the_reading_comes_with_the_map_and_the_engines_agree_on_the_answer(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    r = AG.coverage(s, only='lasting')
    d = r['drivers']
    assert d['L'] == pytest.approx(r['L']) and d['n'] == r['moves']
    assert d['list'] == sorted(d['list'], reverse=True)
    g = D.lasting_of(s)
    assert g['L'] == pytest.approx(r['L'], abs=0.01) and g['moves'] == r['moves']


@needs_node
def test_each_defender_has_plain_words_for_what_he_is_playing_for(js):
    from playmaker_engine import plain as P
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    roles = AG.coverage(s, only='roles')['roles']
    assert [r['x'] for r in roles] == [0, 1, 2, 3, 4]
    for r in roles:
        assert r['line'].startswith(f"X{r['x'] + 1}: ")
        assert not any(re.search(r'\b' + re.escape(w) + r'\b', r['line'], re.I) for w in P.BANNED), r['line']
        assert '—' not in r['line']
    assert roles[3]['gap'] and B.in_key(B.parse_sq(roles[3]['gap']['sq']))       # X4 in the lane holds a square of the key


@needs_node
def test_the_defences_setup_tries_every_square_and_says_what_decided(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    r = AG.coverage(s, only='setup', evals=120)
    assert all(z['by'] in ('the list', 'the lasting gap', 'efficiency', 'level', 'the quick re-read') for z in r['steps'])
    assert len(set(r['x'])) == 5 and sorted(r['perm']) == [0, 1, 2, 3, 4]


@needs_node
def test_the_offence_sweep_reads_every_empty_square_for_one_attacker(js):
    s = table(['J10', 'D8', 'O8', 'I6', 'P2'], [7, 7, 0, 0, 1])
    rows = AG.coverage(s, only='offsweep', piece=1, keep=500)
    taken = {B.parse_sq(q) for q in ['I11', 'O9', 'A3', 'Q3', 'J10', 'D8', 'O8', 'I6', 'P2']}
    free = [q for q in AG._court() if q not in taken]
    assert len(rows) >= 0.9 * len(free)                               # (the last phase or a square off the map reads none)
    L = [z['drivers']['L'] for z in rows]
    assert L == sorted(L, reverse=True)                               # the offence's mirror: the lasting gap, then the list
