"""Step 22 (Shaun, 18 Nov 2026): "Just ask it to fix it. Merge it. And let me test it." (D-210 to D-213)

The defence's setup is the map's own best answer to the offence's placement; the map reads the offence's whole first
turn of the next phase; the three-second rule's -5 is counted; the offence's search tries the moves that make the map's
looks."""
import os
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


def test_the_rulings_are_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-210', 'D-211', 'D-212', 'D-213'):
        assert f'**{d}.' in text, d
    assert 'Just ask it to fix it. Merge it. And' in text


@needs_node
def test_the_defences_setup_is_never_worse_than_the_hug_and_packs_the_paint(js):
    import step_21 as T
    from playmaker_web.game import TABLE_O, man_to_man
    o = [B.parse_sq(q) for q in TABLE_O]
    make = lambda oo, b, x, a: T._state([B.sq(q) for q in oo], [B.sq(q) for q in x], list(a), ball=b)
    hug, ar = man_to_man(o, 0)
    before = D.lasting_of(make(o, 0, hug, ar))['L']
    xs, arrows, L = AG._map_setup(make, o, 0)[:3]
    assert L <= before + 1e-9
    assert L < before                                                  # on the table's board it finds a better one
    assert D.lasting_of(make(o, 0, xs, arrows))['L'] == pytest.approx(L)          # the engines read it the same
    assert any(B.in_key(q) for q in xs)                                # someone in the key
    assert len(set(xs)) == 5 and not set(xs) & set(o)


def test_three_seconds_owed_counts_who_cant_get_out():
    import step_21 as T
    s = T.b1()
    a = next(i for i in range(5) if B.in_key(s.o[i]))                # O1 has driven into the key
    assert D.three_seconds_owed(s.with_(key_o=0)) == 0
    stuck = s.with_(key_o=1 << a, tok_o=0)                            # in the key at the last phase end, no token left
    assert D.three_seconds_owed(stuck) == 1
    assert D.three_seconds_owed(s.with_(key_o=1 << a)) == 0 or s.tok_o == 0      # with a token he can still get out
    assert D.lasting_of(stuck)['L'] == pytest.approx(D.lasting_of(s.with_(key_o=0, tok_o=0))['L'] - 5)


def test_the_offences_search_tries_the_moves_that_make_the_maps_looks():
    import step_21 as T
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.search import candidate_actions
    s = T.b2()
    assert s.side == 'O'
    r = D.Read(s)
    r.cfg = dict(r.cfg, map=True)
    cands = {str(c) for c in candidate_actions(s, r)}
    threats = r.map_threats()
    assert threats
    for ta, q0 in threats:
        def hit(a):
            if ta == s.ball or q0 != s.o[ta]:
                return a.kind in ('move', 'qs', 'sprint') and a.piece == ta and a.dest == q0
            return a.kind == 'pass' and a.target == ta
        legal = [str(a) for a in legal_actions(s) if hit(a)]
        assert not legal or set(legal) <= cands, (ta, B.sq(q0))
