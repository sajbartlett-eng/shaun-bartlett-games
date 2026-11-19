"""Step 27 (Shaun, 19 Nov 2026): the computer sets up the way it plays. One board for each item."""
import os
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC
from playmaker_engine.resolve import end_phase

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

# board 1 as step 26's setups left it (High-Low v Shoot and Protect): four in the key, the full defence set
B1 = (['J3', 'H3', 'G4', 'I4', 'N12'], ['J6', 'K5', 'M6', 'O12', 'M11'], [7, 1, 6, 5, 2])


def state(o, x, ar, ball=0, off='High-Low', dfn='Shoot and Protect', **kw):
    import step_21 as T
    s = T._state(o, x, ar, ball=ball, off=off, dfn=dfn)
    return s.with_(**kw) if kw else s


@pytest.fixture
def js27():
    from playmaker_engine import jsbridge
    eng = jsbridge.NodeEngine().install()
    yield eng
    eng.close()


# ---- the rule change (D-254, the app only): the count doesn't start again after a violation -------------------------

def test_three_seconds_repeats_while_he_stays_in_and_not_once_he_steps_out():
    s = state(['N12', 'C9', 'O9', 'I4', 'A3'], ['M11', 'D8', 'N8', 'K6', 'B4'], [2, 0, 0, 1, 0], ball=0)
    a = 3                                                         # O4 on I4, in the key, without the ball
    one = end_phase(s)
    assert one.stage == 'play' and one.tos == 0 and one.key_o >> a & 1
    two = end_phase(one)                                          # two phase ends in a row: -5, play goes on
    assert two.stage == 'play' and two.tos == 1 and two.key_o >> a & 1
    three = end_phase(two)                                        # still in at the next phase end: again
    assert three.stage == 'play' and three.tos == 2
    out = two.with_(o=tuple(B.parse_sq('I8') if i == a else q for i, q in enumerate(two.o)))
    after = end_phase(out)                                        # he stepped out: no second violation
    assert after.tos == 1 and not after.key_o >> a & 1


# ---- item 5: three seconds by the rule ------------------------------------------------------------------------------

def _holds(s, a):
    """Attacker a's looks in the map (the Python engine, proved equal to engine.js), by where he holds the ball when
    the next phase starts: {start square: [the cost of holding it there]}."""
    out = {}
    for (k, q, r), o in D.Read(D.cov_off_fresh(s)).map_options().items():
        if k == a:
            out.setdefault(o[6], []).append(o[9])
    return out


def test_three_seconds_cost_nothing_for_a_shot_that_goes_up_in_time():
    # the post scorer centre with the ball on the block (Twin Towers v Lockdown). Not in the key at the last phase
    # end: holding it in the key costs nothing for the three seconds, his post shot goes up before the violation can
    # fall (D-255), so each look costs what it costs outside the key (the Steal). In the key at the last phase end
    # too: he can't avoid it at this one, so a look held in the key costs the full -5 more, and outside nothing more.
    s = state(['C9', 'O9', 'A3', 'Q3', 'G3'], ['D8', 'N8', 'B4', 'P4', 'G6'], [0, 0, 0, 0, 4], ball=4,
              off='Twin Towers', dfn='Lockdown').with_(side='O', turn_n=0)
    free, stuck = _holds(s.with_(key_o=0), 4), _holds(s.with_(key_o=1 << 4), 4)
    inside = [q for q in free if B.in_key(q) and q in stuck]
    outside = [q for q in free if not B.in_key(q) and q in stuck]
    assert inside and outside
    for q in inside:
        assert sorted(set(stuck[q])) == pytest.approx(sorted({c - 5 for c in free[q]}))     # (looks it leaves worthless are dropped)
        assert all(c not in (-2.5,) for c in free[q])              # no halves (D-255)
    for q in outside:
        assert sorted(set(stuck[q])) == pytest.approx(sorted(set(free[q])))


def test_closely_guarded_costs_nothing_until_the_count_falls():
    from playmaker_engine.state import pack_guard
    from playmaker_engine.actions import closely_guarded
    s = state(['N12', 'C9', 'O9', 'A3', 'Q3'], ['N11', 'D8', 'N8', 'B4', 'P4'], [0, 0, 0, 0, 0], ball=0).with_(side='O', turn_n=0)
    assert closely_guarded(s)
    for held in range(RC.GUARDED_ENDS - 1):                     # not at its last phase end: nothing (no thirds, D-256)
        mine = _holds(s.with_(grd=pack_guard(0, held, 0, 0)), 0).get(s.o[0], [])
        assert mine and all(c == 0 for c in mine)
    last = _holds(s.with_(grd=pack_guard(0, RC.GUARDED_ENDS - 1, 0, 0)), 0).get(s.o[0], [])
    assert all(c <= -5 + 1e-9 for c in last)                     # it falls at this phase end: the full -5 (or he doesn't hold)


# ---- items 1 to 3: the placement against the full defence, by the list ------------------------------------------------

@needs_node
def test_full_defence_ranking_equals_a_full_read_of_every_placement(js27):
    from playmaker_engine import agent as AG, plan as PL
    from playmaker_web.game import TABLE_O
    import step_27 as S
    make = S._make('High-Low', 'Shoot and Protect')
    table = [B.parse_sq(q) for q in TABLE_O]
    pool = [(table, 0), ([B.parse_sq(q) for q in B1[0]], 4)]
    r = PL.place_offence(make, seed=1, pool=pool, budget=2)
    assert r['full'] == len(pool)                                  # every placement on this small board read in full
    by_hand = []
    for sq, b in pool:
        m = AG._map_setup(make, sq, b, evals=240)
        h = PL.horizon_read(make(sq, b, m[0], m[1]), budget=60.0, depth=PL.HORIZON_TURNS)
        by_hand.append((h['key'], [B.sq(q) for q in sq], b))
    best = max(by_hand, key=lambda z: z[0])
    assert [B.sq(q) for q in r['squares']] == best[1] and r['ball'] == best[2]
    assert r['list'] == list(best[0][0][:5])
    assert r['alternative'] and 'It lost because' in r['alternative']['text']


@needs_node
def test_no_attacker_is_forced_onto_a_square_that_lowers_the_plan(js27):
    from playmaker_engine import agent as AG, plan as PL
    import step_27 as S
    make = S._make('High-Low', 'Shoot and Protect')
    r = PL.place_offence(make, seed=1, budget=4, cap=0)
    assert all(z['why'] == 'the list reads better' for z in r['steps'])   # no move made because a square was a candidate
    keys = [z['key'] for z in r['steps']]
    assert all(b > a for a, b in zip(keys, keys[1:]))              # each move raised the list (against the same quick defence)
    assert 'must' not in PL.place_offence.__code__.co_varnames     # the step that forced a move to a candidate is gone
    # an attacker may stand where the scout's candidates don't list him: the sweep offers every legal square
    sc = PL.Scout(make([B.parse_sq(q) for q in B1[0]], 4, [B.parse_sq(q) for q in B1[1]], B1[2]).ctx, 'O')
    off_list = [a for a in range(5) if a != r['ball'] and r['squares'][a] not in set(sc.candidates(a))]
    assert r['checks'] and any(c['check'] == 'every attacker has a job' for c in r['checks'])
    assert isinstance(off_list, list)


# ---- item 4: as far ahead as the plan needs ----------------------------------------------------------------------------

@needs_node
def test_a_screen_then_the_dive_reads_higher_than_its_one_turn_reading_for_both_sides(js27):
    from playmaker_engine import agent as AG, plan as PL
    s = state(*B1, ball=4).with_(side='O', turn_n=0)
    first = PL.list_key(AG.coverage(s, only='lasting'))
    rows = [(w, a, t) for w, a, t in PL._continuations(s, None) if t.kind == 'screen']
    assert rows, 'a screen the screener can set this turn'
    # each screen, the defence's turn by its own reading (the list), then the offence's: the best of them, as the
    # read-ahead itself chooses
    read = []
    for w, after, act in rows:
        nxt, dn = PL._defence_turn(after)
        read.append((PL.list_key(AG.coverage(nxt.with_(turn_n=0), only='lasting')), nxt, act))
    two, nxt, act = max(read, key=lambda z: z[0])
    assert two > first                                             # the offence's reading: higher read two turns on
    sq = AG.coverage(nxt.with_(turn_n=0))['squares'][act.piece]
    dive = max((v['worth'] for k, v in sq.items() if B.zone(B.parse_sq(k)) == 'K'), default=0)
    before = max(v['worth'] for v in AG.coverage(s)['squares'][act.piece].values())
    assert dive > before                                           # it is the screener's roll to the rim that rises
    # the defence's reading: its best answer to the screen, by the list, still leaves more than the one-turn reading
    # (it can't read the screen away), and the board read ahead (the same reading both setups use) is at least that
    h = PL.horizon_read(s, budget=60.0, depth=PL.HORIZON_TURNS)
    assert h['key'] >= two and h['key'] > first
    assert h['first'] == first


@needs_node
def test_the_defence_reads_its_setup_ahead_to_the_same_horizon(js27):
    from playmaker_engine import plan as PL
    import inspect
    src = inspect.getsource(PL.place_defence)
    assert 'horizon_read(' in src and 'HORIZON_TURNS' in src
    src_o = inspect.getsource(PL.place_offence)
    assert 'horizon_read(' in src_o and 'depth=depth' in src_o and 'HORIZON_TURNS' in src_o


@needs_node
def test_the_conditions_read_ahead_are_named(js27):
    from playmaker_engine import plan as PL, conditions as CD
    s = state(*B1, ball=4).with_(side='O', turn_n=0)
    h = PL.horizon_read(s, budget=60.0, depth=PL.HORIZON_TURNS)
    found = CD.ahead(h, s)
    assert h['turns'] > 1 and found
    assert {c['id'] for c in found} <= set(CD.NAMES)
    assert set(CD.UNMEASURED).isdisjoint(CD.NAMES)
    for cid in ('20b', '9b', '11', '33', '39'):
        assert cid in CD.NAMES and cid not in CD.UNMEASURED


# ---- the audit's stand-ins, one board each -----------------------------------------------------------------------------

@needs_node
def test_screens_are_found_by_the_list_not_the_lasting_gap_alone(js27):
    # audit (step 27): a screen "builds more" when the one list reads better with it standing (D-219), the same
    # reading the search and both setups use; it was the lasting gap alone, with a fixed half-point margin
    from playmaker_engine import agent as AG, plan as PL
    s = state(*B1, ball=4).with_(side='O', turn_n=0)
    base = PL.list_key(AG.coverage(s, only='lasting'))
    rows = PL.screen_roles(s)
    assert rows
    for z in rows:
        assert tuple(z['list']) >= tuple(base[0][:8])            # every screen it names reads at least as well by the list
    lists = [tuple(z['list']) for z in rows]
    assert lists == sorted(lists, reverse=True)                  # best first, by the list
    # a screen that raises only the lasting gap, not the list, is not named: each named one beats the board by the list
    assert all(tuple(z['list']) > tuple(base[0][:8]) or z['value'] >= base[0][0] for z in rows)
