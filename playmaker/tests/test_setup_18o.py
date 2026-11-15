"""Step 18o (Shaun, 15 Nov 2026), D-195: the setup must fit the players. Both sides' setups, and the setup proposed to a
human, searched from no starting answer (any square, any arrow), shortlisted by the quick reading and the shortlist
judged by the search's played-out reading. Built behind a switch that is off: played out, the placements it finds give
up more than the old setup's (docs/reports/STEP18O_REPORT.md)."""
import json
import random
import shutil
import time

import pytest

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.decide import CONFIG
from playmaker_engine.scenarios import game_state, setup_errors

RULES = RC.with_rules(digital=True)


def make(o, x, arrows, ball):
    return game_state('Five Out', 'High-Low', list(o), list(x), list(arrows), ball=ball, rules=RULES)


def test_the_switch_is_off_and_the_setup_is_as_it_was():
    assert CONFIG['setup']['search'] is False and not AG.setup_search()
    r = AG.propose_offence(make, 3, budget=0.2, level='starter')
    assert 'screened' in r['text']                                    # the setup as it was: sampled placements, refined
    d = AG.propose_defence(make, r['squares'], r['ball'], 4, budget=0.2, level='starter')
    assert d['text'].startswith('Placed by best cover')


def test_the_search_places_both_sides_legally_inside_its_time():
    for level, budget in (('rookie', 0.12), ('allstar', 0.4)):
        t0 = time.time()
        r = AG.propose_offence(make, 5, budget=budget, level=level, search=True)
        took = time.time() - t0
        assert AG._legal_o(r['squares'], r['ball']) and 'no starting answer' in r['text']
        d = AG.propose_defence(make, r['squares'], r['ball'], 6, budget=budget, level=level, search=True)
        assert not setup_errors(tuple(r['squares']), tuple(d['squares']), r['ball'])
        assert all(a in range(8) for a in d['arrows']) and all(i in range(5) for i in d['perm'])
        assert took < budget + 1.5                                    # the Python search (no JavaScript engine here) finishes a reading it has begun


def test_nothing_is_a_starting_answer_and_every_square_and_arrow_can_be_drawn():
    """No placement is named: a search starts from a draw, and a change is drawn alike over the whole court."""
    rng = random.Random(1)
    starts = {tuple(AG._random_x([(8, 11), (2, 9), (14, 9), (0, 3), (16, 3)], rng)[0]) for _ in range(20)}
    assert len(starts) == 20                                          # twenty searches, twenty different starts
    arrows, squares, near = set(), set(), 0
    sq = [(9, 10), (3, 8), (14, 8), (1, 4), (15, 2)]
    for _ in range(4000):
        ch = AG._change(sq, set(), rng)
        arrows.add(rng.randrange(8))
        if ch:
            squares.add(ch[1])
            near += B.cheb(ch[1], sq[ch[0]]) <= 1
    assert arrows == set(range(8))
    assert len(squares) > 0.95 * B.W * B.H                            # any square of the court
    assert 0.3 < near / 4000 < 0.7                                    # and squares next to his own, in like measure


def test_the_searches_of_a_game_are_carried_to_the_next_setup():
    mem = {}
    a = AG.propose_defence(make, [B.parse_sq(q) for q in ('I11', 'C9', 'O9', 'A3', 'Q3')], 0, 1, budget=0.15, level='starter', memory=mem, search=True)
    held = [list(c['xs']) for c in mem['X']]
    assert len(held) == AG.SETUP['chains']
    b = AG.propose_defence(make, [B.parse_sq(q) for q in ('I11', 'C9', 'O9', 'A3', 'Q3')], 0, 2, budget=0.15, level='starter', memory=mem, search=True)
    assert b['reads'] > 0 and len(mem['X']) == AG.SETUP['chains']
    # carried on, never drawn again: a search only ever keeps a change the reading says is better for the defence
    for c, was in zip(mem['X'], held):
        assert c['key'] is not None
    # a carried defender whose square the offence now stands on is drawn again, and only he
    xs = AG._legalise([(8, 11), (2, 9)], [(8, 11), (5, 5), (6, 6), (7, 7), (9, 9)], random.Random(0))
    assert xs[1:] == [(5, 5), (6, 6), (7, 7), (9, 9)] and xs[0] not in ((8, 11), (2, 9))


def test_the_readings_parts_order_placements_for_each_side():
    assert AG._better((20.0, 6.0, 3.0), (21.0, 0.0, 0.0), -1)         # the defence: the lower value first
    assert AG._better((20.0, 5.0, 3.0), (20.0, 6.0, 0.0), -1)         # level: the best look its cover leaves, then the next
    assert AG._better((20.0, 6.0, 0.0), (20.0, 5.0, 3.0), 1)          # the offence: the other way
    assert not AG._better((20.0, 5.0, 3.0), (20.0, 5.0, 3.0), 1) and not AG._better((20.0, 5.0, 3.0), (20.0, 5.0, 3.0), -1)


@pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')
def test_the_two_engines_give_the_same_reading_of_a_setup():
    from playmaker_engine.jsbridge import NodeEngine
    rng = random.Random(7)
    items = []
    for _ in range(12):
        o = AG._random_o(rng)
        xs, ar = AG._random_x(o, rng)
        items.append((o, 0, xs, ar))
    mk = lambda o, b, x, a: make([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), b)
    py = AG._reads(mk, items)
    eng = NodeEngine().install()
    try:
        js = AG._reads(mk, items)
    finally:
        NodeEngine.uninstall()
        eng.p.kill()
    assert all(a is not None and b is not None and len(a) == len(b) == 6 for a, b in zip(py, js))
    assert all(abs(u - v) < 1e-9 for a, b in zip(py, js) for u, v in zip(a, b))


def test_a_game_asks_for_the_search_and_offers_a_human_its_proposal():
    from playmaker_web.game import Game, TABLE_O
    AG.SCALE['value'] = 0.1
    kw = dict(mode='hotseat', teams=['Five Out', 'High-Low'], seed=3, ai=dict(X='starter'), full=True, place=True, level='pro')
    try:
        plain = Game(match_format='digital', **kw)
        assert plain.setup_search is False
        plain.place(plain.tokens['both'], dict(preview=True))
        assert [B.sq(q) for q in plain.state.o] == TABLE_O             # off: the table's squares, as before
        g = Game(match_format='digital', setup='search', **kw)
        assert g.setup_search is True
        prop = g.proposal('O')
        g.place(g.tokens['both'], dict(preview=True))
        assert list(g.state.o) == [tuple(q) for q in prop['squares']]  # on: the standard setup is the engine's proposal
        assert not g.placing and g.state.stage == 'play'               # and the computer placed its defence by the search
        assert any(r.get('event') == 'setup' and 'no starting answer' in r.get('text', '') for r in g.read_log() if r.get('type') == 'computer')
        assert Game(setup='search', **kw).setup_search is False        # the app's format only
    finally:
        AG.SCALE['value'] = 1.0
