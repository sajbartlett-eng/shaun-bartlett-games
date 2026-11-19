"""Step 24 (Shaun, 19 Nov 2026): the setup plan. The scout's case table against the contest rules; each side thinks
alone; the plan's parts."""
import itertools
import os
import shutil
import sys
from fractions import Fraction

import pytest

from playmaker_engine import board as B
from playmaker_engine import geometry as G
from playmaker_engine import plan as PL
from playmaker_engine import rules_config as RC
from playmaker_engine import scoring as SC
from playmaker_engine.scenarios import game_state

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')
RULES = RC.with_rules(digital=True, zone='on')
FAR_O = ['A14', 'B14', 'C14', 'D14']
FAR_X = ['N14', 'O14', 'P14', 'Q14']


def _spot(zone):
    """A square of the zone with a square in front (nearer the rim), beside (level) and behind (further) next to it."""
    for x in range(B.W):
        for y in range(2, B.H + 1):
            c = (x, y)
            if not B.on_board(c) or B.zone(c) != zone or c == RC.RIM:
                continue
            nb = [(x + dx, y + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0) and B.on_board((x + dx, y + dy))]
            f = [q for q in nb if B.dist_rim(q) < B.dist_rim(c)]
            s = [q for q in nb if B.dist_rim(q) == B.dist_rim(c)]
            h = [q for q in nb if B.dist_rim(q) > B.dist_rim(c)]
            if f and s and h:
                return c, f[0], s[0], h[0]
    raise AssertionError(zone)


def _engine(off, dfn, i, j, t, where, how, s_rushed, d_rushed, front=True):
    """The case's value by the game's own rules (scoring), on a board built for it."""
    c, f, s, h = _spot(PL.SHOT_ZONE[t])
    if where == 'open':
        dq, arrow = B.parse_sq('M14'), 0
    else:
        dq = f if (where == 'square' or (where == 'side' and front)) else s if where == 'side' else h
        rules = RULES
        on = [a for a in range(8) if G.faces(rules, G.stance(rules, a, False), dq, c)]
        off_ = [a for a in range(8) if a not in on]
        arrow = on[0] if (where == 'square' or dq != f) else off_[0]
    o = [B.sq(c) if k == i else FAR_O.pop(0) if False else None for k in range(5)]
    spare_o, spare_x = list(FAR_O), list(FAR_X)
    o = [B.sq(c) if k == i else spare_o.pop(0) for k in range(5)]
    x = [B.sq(dq) if k == j else spare_x.pop(0) for k in range(5)]
    st = game_state(off, dfn, o, x, [arrow if k == j else 0 for k in range(5)], ball=i, rules=RULES, check=False)
    st = st.with_(rush_o=(1 << (2 * i)) if s_rushed else 0, rush_x=(1 << (2 * j)) if d_rushed else 0)
    if where == 'open' or how == 'hand':
        opt = SC.soft_option(st, i, t)
        assert (opt.defender == j) == (where != 'open')
        return Fraction(opt.ev), opt
    # (step 28, D-261: each defender has a normal and a hard Contest; the block is the hard one)
    opt = next(q for q in SC.contest_options(st, i, t) if q.defender == j and (q.hard or not RC.contest_costs(RULES)))
    plus5 = RC.STEAL_FOUL_BONUS if RC.app_rule(RULES, 'points_play_on') else 0
    return Fraction(opt.ev) + opt.p_foul * plus5, opt


def test_the_scouts_case_table_is_14_cases_a_jump_shot_and_22_an_inside_shot():
    for t in RC.JUMP_SHOTS:
        assert len(PL.cases_for(t)) * 2 == 14
    for t in PL.INSIDE:
        assert len(PL.cases_for(t)) * 2 == 22
    assert set(PL.INSIDE) == {'layup', 'dunk', 'post', 'floater'} and set(PL.SHOT_ZONE) == set(PL.INSIDE) | set(RC.JUMP_SHOTS)


@pytest.mark.parametrize('off,dfn', [('Five Out', 'High-Low'), ('Shoot and Protect', 'Lockdown'), ('High-Low', 'Run and Gun')])
def test_every_case_in_the_table_matches_the_contest_rules(off, dfn):
    from playmaker_engine.cards import TEAMS
    ocards, dcards = TEAMS[off], TEAMS[dfn]
    seen = 0
    for i, j in itertools.product(range(5), range(5)):
        for t in PL.SHOT_ZONE:
            rows = PL.shot_review(ocards[i], dcards[j], t, RULES)
            assert len(rows) == (14 if t in RC.JUMP_SHOTS else 22)
            for r in rows:
                s_r, d_r = r['shooter'] == 'rushed', r['defender'] == 'rushed'
                if r['where'] == 'side' and r['how'] == 'block':
                    for front, key in ((True, 'value_front'), (False, 'value_beside')):
                        v, opt = _engine(off, dfn, i, j, t, 'side', 'block', s_r, d_r, front)
                        assert v == r[key], (i, j, t, r, front)
                        assert opt.rolls == (1 if front else 2)
                else:
                    v, opt = _engine(off, dfn, i, j, t, r['where'], r['how'], s_r, d_r)
                    assert v == r['value'], (i, j, t, r)
                    if r['how'] == 'block':
                        assert opt.rolls == 2
                    if r['where'] != 'open':
                        assert opt.contest == r['contest'] >= 1          # D-193: every contest takes at least 1
                seen += 1
    assert seen == 25 * (3 * 14 + 4 * 22)


def test_a_square_defender_on_an_inside_shot_never_fouls_and_a_jump_shot_has_no_block():
    from playmaker_engine.cards import TEAMS
    c, f, s, h = _spot('K')
    on = next(a for a in range(8) if G.faces(RULES, G.stance(RULES, a, False), f, c))
    st = game_state('Five Out', 'High-Low', [B.sq(c)] + FAR_O, [B.sq(f)] + FAR_X, [on, 0, 0, 0, 0], ball=0, rules=RULES, check=False)
    # Re-recorded in step 28 (D-261): the contest is an action now, so the square defender has a Contest to press (it
    # read: no Contest action, the full contest automatic). It is his full rating and never a foul, and he has no block.
    mine = [q for q in SC.contest_options(st, 0, 'layup') if q.defender == 0]
    assert len(mine) == 1 and mine[0].clean and not mine[0].hard and mine[0].p_foul == 0
    c3, f3, _, _ = _spot('3')
    st3 = game_state('Five Out', 'High-Low', [B.sq(c3)] + FAR_O, [B.sq(f3)] + FAR_X, [0] * 5, ball=0, rules=RULES, check=False)
    # a jump shot: his Contest is the position table, never a foul, and there is no block (it read: no Contest at all)
    jump = [q for q in SC.contest_options(st3, 0, 'three') if q.defender >= 0]
    assert all(q.clean and not q.hard for q in jump)
    assert all(r['how'] in (None, 'hand') for r in PL.shot_review(TEAMS['Five Out'][0], TEAMS['High-Low'][0], 'three', RULES))


# ---- the scout: movement, tolerance, the spec ---------------------------------------------------------------------------

@pytest.fixture(scope='module')
def js():
    from playmaker_engine.jsbridge import NodeEngine
    eng = NodeEngine().install()
    yield eng
    eng.close()


def _board():
    import step_22b as S
    return S._board()


@needs_node
def test_a_won_dribble_is_worth_more_at_the_top_of_the_key_than_in_the_green_zone(js):
    s = _board()
    sc = PL.Scout(s.ctx, 'O')
    top, green = sc.beat(s, 0, 4, B.parse_sq('I11')), sc.beat(s, 0, 4, B.parse_sq('I4'))
    assert top['chance'] == green['chance'] == pytest.approx(sc.beat_chance(0, 4))      # the chance is the cards', anywhere
    assert top['grows'] > 3 * green['grows'] and top['squares'] > green['squares']      # what it opens is the court's


def test_the_acceptance_spec_falls_out_of_the_bar_and_the_scouts_cases():
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'B4', 'P4'], [0] * 5, rules=RULES, check=False)
    sc = PL.Scout(s.ctx, 'O')
    rows = sc.shots(1, 0, 'three')
    open_v = float(rows[0]['value'])
    for bar in (0, 12, 20, 26, open_v, open_v + 1):
        spec = PL.acceptance(sc, 1, 'three', bar)
        assert spec['open'] == (open_v >= bar)
        for d in range(5):
            ok = {(w, df) for w, df in map(tuple, spec['by'].get(d, []))}
            for r in sc.shots(1, d, 'three'):
                if r['shooter'] == 'set' and r['where'] != 'open':
                    assert ((r['where'], r['defender']) in ok) == (float(r['value']) >= bar)
    hard = PL.acceptance(sc, 1, 'three', open_v - 1)
    assert hard['refused'] == [0, 1, 2, 3, 4] and hard['words'].startswith('Create a three for O2: open accepted')
    assert 'contested by X1, X2, X3, X4 or X5 not accepted' in hard['words']             # Shaun's form


def test_no_prediction_is_carried_from_one_possession_to_the_next():
    # Step 25 (D-245): the two-possessions rule is removed. A scout holds no predictions of the other side; each
    # possession predicts fresh from what it can see.
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'B4', 'P4'], [0] * 5, rules=RULES, check=False)
    sc = PL.Scout(s.ctx, 'O')
    assert not hasattr(sc, 'predict') and not hasattr(sc, 'observe') and not hasattr(PL, 'EVIDENCE')


# ---- each side thinks alone ---------------------------------------------------------------------------------------------

@needs_node
def test_changing_one_sides_private_goals_never_changes_the_other_sides_choice(js):
    import step_22b as S
    from playmaker_engine import agent as AG
    from playmaker_engine.agent import Agent
    monkey = AG.FIXED['depth']
    AG.FIXED['depth'] = 1                                          # the same look-ahead every time: a choice never turns on the clock
    try:
        _separate(S, Agent)
    finally:
        AG.FIXED['depth'] = monkey


def _separate(S, Agent):
    s = _board()
    sc_o = PL.Scout(s.ctx, 'O')
    plan_a = PL.read_plan(s, sc_o)
    plan_b = dict(plan_a, o=(plan_a['o'] + 1) % 5, shot='layup', sq='I3')
    # the defence's choice on the same board, whatever the offence privately plans
    picks = []
    for plan in (plan_a, plan_b, None):
        off = Agent('O', 'allstar', seed=3)
        off.setup_plan, off.scout = plan, sc_o
        dfn = Agent('X', 'allstar', seed=3)
        picks.append(str(dfn.choose(s.with_(side='X', turn_n=0))))
        assert dfn.setup_plan is None                             # nothing of the offence's is ever on the defence's computer
    assert len(set(picks)) == 1
    # the offence's choice on the same board, whatever the defence privately reads
    picks = []
    for perm, predict in (([0, 1, 2, 3, 4], {}), ([4, 3, 2, 1, 0], {1: 3})):
        dfn = Agent('X', 'allstar', seed=3)
        dfn.setup_perm, dfn.assign = tuple(perm), list(perm)
        dfn.scout = PL.Scout(s.ctx, 'X')
        off = Agent('O', 'allstar', seed=3)
        off.setup_plan, off.scout = plan_a, PL.Scout(s.ctx, 'O')
        picks.append(str(off.choose(s.with_(side='O', turn_n=0))))
    assert len(set(picks)) == 1
    # and the setups: the defence sets up the same whatever the offence's private plan
    make = lambda o, b, x, a: S._board([B.sq(q) for q in x], list(a), [B.sq(q) for q in o])
    o_sq = [B.parse_sq(q) for q in S.SHAUN_O]
    d1 = PL.place_defence(make, o_sq, 0, seed=1, scout=PL.Scout(s.ctx, 'X'))
    d2 = PL.place_defence(make, o_sq, 0, seed=1, scout=PL.Scout(s.ctx, 'X'))
    assert (d1['squares'], d1['arrows'], d1['perm']) == (d2['squares'], d2['arrows'], d2['perm'])


@needs_node
def test_the_computers_private_plan_is_never_shown_to_the_human_playing_it_and_the_buttons_place_a_draft():
    from playmaker_engine import agent as AG
    from playmaker_engine import plain as P
    from playmaker_web.api import Manager, handle
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    import re
    assert coverage_engine()
    AG.SCALE['value'] = 1.0
    try:
        m = Manager()
        _, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=5,
                                                        level='pro', full=True, per_side=4, place=True))
        code, tok = r['code'], r['token']
        _, s = handle(m, 'GET', '/api/state', query=dict(code=code, token=tok))
        assert s['placing']['side'] == 'O' and s['setup_info'] == {} and len(s['candidates']) == 5
        _, r = handle(m, 'POST', '/api/place', body=dict(code=code, token=tok, computer=True))
        s = r['state']
        d = s['placing']['draft']
        assert s['placing']['side'] == 'O' and d['computer'] and d['nth'] == 0          # a draft on the board: nothing is confirmed
        info = s['setup_info']['O']
        assert info['words'][0].startswith('Plan: ') and any(w.startswith('Attention: ') for w in info['words'])
        for w in info['words'] + [info['spec']]:
            assert not any(re.search(r'\b' + re.escape(b) + r'\b', w, re.I) for b in P.BANNED), w
            assert '—' not in w
        _, r = handle(m, 'POST', '/api/place', body=dict(code=code, token=tok, squares=d['squares'], ball=d['ball']))
        assert r['state']['placing']['side'] == 'X'
        _, r = handle(m, 'POST', '/api/place', body=dict(code=code, token=tok, computer=True))
        s = r['state']
        dx = s['placing']['draft']
        read = s['setup_info']['X']['read']
        # (re-recorded in step 26, D-252: a defender who can't contest his man's look this turn reads "sags off")
        assert len(read) == 5 and all(re.match(r'X\d (on|sags off) O\d', t) for t in read)
        _, r = handle(m, 'POST', '/api/place', body=dict(code=code, token=tok, squares=dx['squares'], arrows=dx['arrows']))
        assert r['state']['placing'] is None and r['state']['plan_line']['coaching'] is True
        # against the computer: its defence's read is its own
        _, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=5,
                                                        level='pro', full=True, per_side=4, place=True, ai=dict(X='rookie')))
        code, tok = r['code'], r['token']
        _, s = handle(m, 'GET', '/api/state', query=dict(code=code, token=tok))
        _, r = handle(m, 'POST', '/api/place', body=dict(code=code, token=tok, squares=d['squares'], ball=d['ball']))
        s = r['state']
        assert s['placing'] is None and 'X' not in s['setup_info']                       # the computer set up its defence: its read stays with it
        g = m.get(code)
        assert 'X' in g._setup_info[g.possession] and g.policies['X'].setup_plan is None
    finally:
        stop_coverage_engine()


# ---- step 25: Shaun's rulings on step 24 ------------------------------------------------------------------------------

@pytest.fixture
def js25():
    from playmaker_engine.jsbridge import NodeEngine        # (its own engine: a test above stops the shared one)
    eng = NodeEngine().install()
    yield eng
    eng.close()

@needs_node
def test_a_defender_covers_every_look_he_can_still_contest_and_an_overload_needs_looks_he_cannot(js25):
    from playmaker_engine import decide as D
    s = _board()
    covers = D.covers_too_of(s)
    near, far = B.parse_sq('H3'), B.parse_sq('Q8')
    a1 = B.parse_sq('I3')
    assert covers(4, a1, near)                                   # one square apart: from beside the first he still contests the second
    assert not covers(4, a1, far)                                # across the court: he can't, so covering one leaves the other open
    looks = lambda c2: [dict(a=0, c=a1, t=0, wd=20.0, now=20.0, mask=1 << 4, order=(0,)), dict(a=1, c=c2, t=0, wd=18.0, now=18.0, mask=1 << 4, order=(1,))]
    assert D.cover_groups(covers, looks(near)) == []             # bunched: no overload
    g = D.cover_groups(covers, looks(far))
    assert g and g[0]['value'] == pytest.approx(18.0)            # spread: he takes the 20, the 18 is left


@needs_node
def test_the_bar_falls_slowly_then_faster_and_is_nothing_in_the_last_phase(js25):
    import step_22b as S
    from playmaker_engine import agent as AG, decide as D
    # (re-recorded in step 26, D-249: with the defence's reach along the real paths the morning board's settled shape
    # offers nothing better at a chance, so its bar is flat; this is board 1 of step 26, High-Low against Shoot and
    # Protect as the two setup buttons left it, where the shape shows)
    import step_21 as T
    s = T._state(['J3', 'H3', 'G4', 'I4', 'N12'], ['J6', 'K5', 'M6', 'O12', 'M11'], [7, 1, 6, 5, 2], ball=4, off='High-Low', dfn='Shoot and Protect')
    js_b = [b['bar'] for b in AG.coverage(s, only='bars')['bars']]
    py_b = [b['bar'] for b in D.bars_of(s)]
    assert js_b == pytest.approx(py_b, abs=0.01)                 # both engines count it the same
    assert js_b[-1] == 0 and len(js_b) == s.clock // RC.PHASE_SECONDS
    drops = [u - v for u, v in zip(js_b, js_b[1:])]
    assert all(d >= -1e-9 for d in drops) and drops[0] < drops[-2] < drops[-1]     # barely drops early, faster late
    assert js_b[-2] == pytest.approx(AG.coverage(s, only='lasting')['L'])        # one phase left: the sure look
    flat = [b['bar'] for b in AG.coverage(_board(), only='bars')['bars']]
    assert flat[-1] == 0 and all(b == pytest.approx(flat[0]) for b in flat[:-1])     # nothing better at a chance on this board: flat


@needs_node
def test_a_dribble_beat_counts_everything_the_offence_threatens_before_and_after(js25):
    s = _board()
    sc = PL.Scout(s.ctx, 'O')
    top, paint = sc.beat(s, 0, 4, B.parse_sq('I11')), sc.beat(s, 0, 4, B.parse_sq('I4'))
    for b in (top, paint):
        assert b['grows'] == pytest.approx(b['after'] - b['before'], abs=0.2)      # the whole picture, after less before
    assert top['squares'] > paint['squares'] and paint['shot_after'] > paint['shot_before']    # many small at the top, one large inside
    assert top['grows'] > paint['grows'] > 0


@needs_node
def test_the_conditions_are_read_from_the_map_and_ruled_in_or_out_by_the_bar(js25):
    from playmaker_engine import conditions as CD
    import step_21 as T
    pr = T._state(['I11', 'C9', 'Q3', 'A3', 'K12'], ['I10', 'D8', 'P4', 'B4', 'K11'], [0, 7, 1, 7, 0], off='High-Low', dfn='Run and Gun').with_(side='O', turn_n=0)
    sc = PL.Scout(pr.ctx, 'O')
    r = CD.read(pr, sc, bar=20.0)
    assert r['found'] and set(c['id'] for c in r['found']) <= set(CD.NAMES)
    for c in r['found']:
        if c['id'] in ('54', '55', '57', '18'):
            continue
        assert bool(c.get('ruled_in')) == (c['worth'] > 20.0)
    assert set(CD.UNMEASURED).isdisjoint(CD.NAMES)
    assert any(c['id'] in ('13', '47') and 2 in c['o'] for c in r['found'])      # the corner player's cut is read
