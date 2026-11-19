"""Step 22b, continued (D-218 to D-222, Shaun, 18 Nov 2026): the defence's two responsibilities.

Each attacker's best look as the defence stands (a walled path priced at the Dribble's chance; a contest reached by a
Quick Step or Sprint off balance), every square's gap, one list settled across the team, assignments that stand until a
switch covers more."""
import json
import os
import shutil
import sys

import pytest

from playmaker_engine import agent as AG
from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

# Re-recorded in step 22c (D-224, D-228): the settlement was ['F7', 'A2', 'Q2', 'N7', 'J3'], arrows [0, 1, 0, 0, 0]
# under step 22b's gaps (the average of all five whatever the reach). With gaps a race, stagnation counted and the
# last pass around each defender's square, Shaun's board settles here.
# Re-recorded again in step 25 (D-241): X3's arrow on H10 was 3 (SE); with a defender covering every look he can reach in
# time, the settlement is the same squares with X3 facing N.
SETTLED_X, SETTLED_A = ['G7', 'N5', 'H10', 'K7', 'G3'], [0, 0, 0, 0, 0]


@pytest.fixture(scope='module')
def js():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield eng
    eng.close()


def board(xs=None, arrows=None):
    import step_22b as S
    return S._board(xs, arrows)


def cov(s, **opts):
    import step_22b as S
    return S._js(s, **opts)


def test_the_rulings_and_shauns_words_are_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    for d in ('D-218', 'D-219', 'D-220', 'D-221', 'D-222'):
        assert f'**{d}.' in text, d
    assert "The defender's primary responsibility is their\nassigned player" in text
    assert 'Switching has to improve the overall defensive coverage to be worth it' in text
    assert 'D-217 (addendum)' in text and "a screened defender can't wall the ball handler" in text


# ---- item 1a: each attacker's look as the defence stands ----------------------------------------------------------------

def test_a_walled_path_is_priced_at_the_dribbles_chance_and_a_lost_dribble_costs_no_five():
    s = board(['I10', 'D8', 'O8', 'I6', 'P2'], [0, 7, 0, 0, 1])       # X1 in front of the ball handler (I11), his arrows N and NE
    r = D.Read(D.cov_off_fresh(s))
    opts = r.map_options()
    drib = [o for (a, c, rushed), o in opts.items() if a == 0 and o[8] == 0]
    assert drib, 'some square the ball handler reaches only by beating the defender beside him'
    chances = {round(r._beat_chance(j), 9) for j in range(5) if B.adjacent(s.x[j], s.o[0])}
    for o in drib:
        assert 0 < o[0] < 1 and round(o[0], 9) in chances
        assert o[2] == pytest.approx(o[0] * o[1])                    # value times reach: nothing taken off for the miss
    assert all(o[8] == 5 for (a, c, rushed), o in opts.items() if a != 0)      # a lost pass is still -5


def test_a_contest_reached_by_a_quick_step_or_sprint_is_off_balance():
    s = board()
    r = D.Read(D.cov_off_fresh(s))
    rules = s.ctx.rules
    cm = D._cmap2(rules, B.parse_sq('F7'), 0, s.ctx.dfn[0].qs, 1)
    near = next(c for c, pair in sorted(cm.items()) if pair[3] and B.zone(c) in RC.ZONE_POINTS)        # set for it
    far = next(c for c, pair in sorted(cm.items()) if pair[2] and not pair[3] and B.zone(c) == B.zone(near))   # needs the second movement
    lk = lambda c: r._gap_info()['looks'][r._gap_info()['idx'][c]][1]
    v_near, v_far = r._vals_map(lk(near), 0, cm[near]), r._vals_map(lk(far), 0, cm[far])
    ty = lk(near).types[0]
    assert v_far[ty] - v_near[ty] == pytest.approx(RC.ZONE_POINTS[B.zone(near)] * RC.control_cut(rules, ty))   # every roll 2 lower


# ---- item 1b: the zone gaps ---------------------------------------------------------------------------------------------

def test_a_gap_is_a_square_an_attacker_wins_the_race_to_worth_his_shot_there_by_the_cards():
    # Re-recorded in step 22c (D-228, Shaun, 18 Nov 2026): this test read "a gap is the average shooter there less the
    # best contest, and nobody near leaves it full". Shaun replaced that: a square is a gap only when an attacker can
    # get there with the ball before any defender can arrive to contest it (tests/test_step22c.py has the race itself).
    import step_22b as S
    s = board()
    r = D.Read(D.cov_off_fresh(s))
    g = r._gap_info()
    k = g['idx'][B.parse_sq('I3')]
    pts, types = RC.ZONE_POINTS[B.zone(g['sq'][k])], RC.ZONE_SHOTS[B.zone(g['sq'][k])]
    assert g['open'][k] == pytest.approx([max(pts * c.shot(t) for t in types) for c in s.ctx.off])     # the cards, nothing by hand
    st = r._lg_root(r.map_options())
    assert max(r._gap_vec(st)) == 0                                   # as the defence stood, somebody is set on every square in time
    far = S._board(['A1', 'B1', 'A2', 'B2', 'A3'], [0, 0, 0, 0, 0], ['I9', 'H9', 'J9', 'I10', 'I8'])   # the defence in a corner
    r2 = D.Read(D.cov_off_fresh(far))
    gv = r2._gap_vec(r2._lg_root(r2.map_options()))
    k2 = max(range(len(gv)), key=lambda i: gv[i])
    assert 0 < gv[k2] <= max(g['open'][k2]) + 1e-9                    # a square won is worth no more than the winner's own shot there
    green, arc = max(g['open'][k]), max(g['open'][g['idx'][B.parse_sq('A3')]])
    assert green > arc                                                # the pull of the green zone falls out of the cards


# ---- item 3: one list, settled across the team --------------------------------------------------------------------------

def test_the_list_is_every_attackers_look_and_every_gap_largest_first_and_leads_the_reading():
    s = board()
    g = D.lasting_of(s)
    lst = g['list']
    assert lst == sorted(lst, reverse=True) and len(lst) == 5 + len(D.Read(s)._gap_info()['sq'])
    assert D.top_of(s) == pytest.approx(lst[0])
    assert D.CONFIG['eval']['map_lead'] == 'list'
    r = D.Read(s)
    assert r._map_leaf() == pytest.approx(max(r.map_shot(), lst[0]))  # (nothing banked on this board)


@needs_node
def test_both_engines_read_the_same_list_and_settle_the_same_moves(js):
    import step_21 as T
    for s in (board(), T.b1(), T.b3()):
        j = cov(s, only='lasting', settle=True)
        g = D.lasting_of(s)
        assert j['L'] == pytest.approx(g['L'], abs=0.01) and j['top'] == pytest.approx(D.top_of(s))
        assert j['drivers']['list'] == pytest.approx(g['list'], abs=0.011)
        assert j['settle'] == [[d, B.sq(q), a] for d, q, a in D.Read(s).map_settle()]


def test_the_search_always_tries_the_settlements_own_moves():
    import step_21 as T
    from playmaker_engine.search import candidate_actions
    from playmaker_engine.resolve import apply
    s = T.b1()
    r = D.Read(s)
    cands = candidate_actions(s, r)
    assert all(z in r.map_answer() for z in r.map_settle())
    for d, q, ar in r.map_settle():
        assert any(a.piece == d and a.dest == q and (ar < 0 and a.kind == 'move' or ar >= 0 and a.kind != 'move' and apply(s, a).arrows[d] == ar) for a in cands)


@needs_node
def test_the_settlement_leaves_less_than_shauns_board_nobody_is_spare_and_the_order_listed_never_matters(js):
    import step_22b as S
    from playmaker_engine import jsbridge
    s0 = board()
    z = cov(s0, only='setup', evals=240)
    assert z['x'] == SETTLED_X and z['arrows'] == SETTLED_A           # (the report's board: update both together)
    assert tuple(z['drivers']['list']) < tuple(cov(s0, only='lasting')['drivers']['list'])
    st = board(z['x'], z['arrows'])
    assert all(q['worse'] for q in cov(st, only='without'))           # no two fill the same gap while another is empty
    key = lambda s_, zz: sorted((json.dumps(jsbridge.card_json(s_.ctx.dfn[d]), sort_keys=True), zz['x'][d], zz['arrows'][d]) for d in range(5))
    for order in ([4, 3, 2, 1, 0], [2, 0, 4, 1, 3]):
        s2 = S._relabel(s0, order)
        assert key(s2, cov(s2, only='setup', evals=240)) == key(s0, z)


# ---- item 4: assignments, chasing, switching ----------------------------------------------------------------------------

@needs_node
def test_assignments_stand_on_a_tie_and_each_defender_has_plain_words(js):
    import re
    from playmaker_engine import plain as P
    st = board(SETTLED_X, SETTLED_A)
    free = cov(st, only='roles')
    assert sorted(free['perm']) == [0, 1, 2, 3, 4]
    kept = cov(st, only='roles', prev=free['perm'])
    assert kept['perm'] == free['perm'] and kept['switched'] is None
    other = [free['perm'][1], free['perm'][0]] + free['perm'][2:]     # two men swapped: read as given, nothing called
    assert cov(st, only='roles', prev=other, fixed=True)['perm'] == other
    assert cov(st, only='lasting', prev=free['perm'])['kept'] is True
    # Re-recorded in step 22d (D-230, D-231): this read "the Sharpshooter's defender is on him" (his job line's kind
    # 'man' or 'both'). Matchups are now named by the nearest defender who takes something off a look, and Shaun ruled
    # the check is measured by position: the pass to the Sharpshooter is cut.
    assert D.cov_pass(st, 1, st.o[1]) < 1 - 1e-9
    for r in free['roles']:
        assert r['line'].startswith(f"X{r['x'] + 1}")
        assert not any(re.search(r'\b' + re.escape(w) + r'\b', r['line'], re.I) for w in P.BANNED), r['line']


@needs_node
def test_level_turns_go_to_the_reading_and_only_their_order_changes(js, monkeypatch):
    from playmaker_engine.actions import legal_actions
    s = board(SETTLED_X, SETTLED_A).with_(side='X', turn_n=0)
    acts = [a for a in legal_actions(s) if a.kind in ('move', 'pause')][:5]
    res = [(10.0, [acts[0]]), (5.0, [acts[1]]), (5.0, [acts[2]]), (5.0, [acts[3]]), (1.0, [acts[4]])]
    out = AG._driver_order(s, 'X', res, prev=[1, 3, 4, 2, 0])
    assert out[0] == res[0] and out[-1] == res[-1]
    assert sorted(str(t[0]) for _, t in out[1:4]) == sorted(str(t[0]) for _, t in res[1:4])
    monkeypatch.setitem(AG.JS, 'coverage', None)
    assert AG._driver_order(s, 'X', res) == res
