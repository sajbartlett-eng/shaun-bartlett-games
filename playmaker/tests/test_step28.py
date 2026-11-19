"""Step 28 (Shaun, 19 Nov 2026): the contest costs an action, one reading everywhere, and the defender's stance."""
import os
import shutil
import sys

import pytest

from playmaker_engine import board as B
from playmaker_engine import decide as D
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

# Shaun's case (D-261): O1 shoots a three from C9; X1 on H11 needs two movements to get next to him (a Quick Step,
# then a Move that changes direction); everyone else far off
SHOOT_O = ['C9', 'O9', 'Q3', 'K12', 'I6']
SHOOT_X = ['H11', 'N8', 'P4', 'L11', 'J5']


def state(o, x, ar, ball=0, off='High-Low', dfn='Run and Gun', rules=None, **kw):
    from playmaker_engine.scenarios import game_state
    import step_18o as O
    s = game_state(off, dfn, list(o), list(x), list(ar), ball=ball, rules=RC.with_rules(digital=True, zone='on', **(rules or {})),
                   check=False, **O.T.FOULS)
    s.ctx.levels_key = ('senior', 'pro')
    return s.with_(**kw) if kw else s


def shoot(s, i=0, t=None):
    a = next(a for a in legal_actions(s) if a.kind == 'shot' and a.piece == i and (t is None or a.shot == t))
    return apply(s.with_(side='O', turn_n=0), a)


def _two_movements(r, d):
    """Every way defender d gets next to the shooter with two movements, as (first, second)."""
    out = []
    for a in legal_actions(r):
        if a.piece == d and a.kind in ('move', 'qs', 'sprint'):
            r2 = apply(r, a)
            if getattr(r2, 'stage', None) != 'reaction':
                continue
            for b in legal_actions(r2):
                if b.piece == d and b.kind in ('move', 'qs', 'sprint') and B.adjacent(b.dest, r.o[r.ball]):
                    out.append((a, b))
    return out


# ---- item 1: the contest is a defence action ---------------------------------------------------------------------------

def test_two_movements_leave_no_contest():
    s = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    assert RC.contest_costs(s.ctx.rules)
    r = shoot(s)
    assert r.stage == 'reaction' and r.shot == 'three'
    one = [a for a in legal_actions(r) if a.piece == 0 and a.kind in ('move', 'qs', 'sprint') and B.adjacent(a.dest, r.o[0])]
    assert not one                                               # no single movement gets X1 next to him
    ways = _two_movements(r, 0)
    assert ways                                                  # two do
    a, b = ways[0]
    end = apply(apply(r, a), b)                                  # his two actions are spent: the reply is over
    assert end.stage == 'over' and end.result.contest == 0 and end.result.contester == -1
    # before D-261 the same two movements ended in a free hand up
    old = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0], rules=dict(contest_costs='off')).with_(side='O', turn_n=0)
    ro = shoot(old)
    eo = apply(apply(ro, a), b)
    assert eo.stage == 'over' and eo.result.contest > 0


def test_a_teammate_with_one_movement_can_still_contest():
    s = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    r = shoot(s)
    near = [a for a in legal_actions(r) if a.piece == 1 and a.kind == 'move' and B.adjacent(a.dest, r.o[0])]
    assert near
    r2 = apply(r, near[0])
    cons = [a for a in legal_actions(r2) if a.kind == 'contest' and a.piece == 1]
    assert cons                                                  # one movement and the Contest: the reply's two actions
    end = apply(r2, cons[0])
    assert end.stage == 'over' and end.result.contester == 1 and end.result.contest >= RC.CONTEST_FLOOR


@pytest.mark.parametrize('jump', [True, False])
def test_the_contest_costs_an_action_jump_and_inside_normal_and_hard(jump):
    if jump:      # O1 shoots a three from C9, X1 next to him on D10 (in front, square), X2 beside him on C8
        s = state(['C9', 'O9', 'Q3', 'K12', 'I6'], ['D10', 'B9', 'P4', 'L11', 'J5'], [B.dir_between(B.parse_sq('D10'), B.parse_sq('C9')), 0, 0, 0, 0])
    else:         # O5 lays it up from H3, X5 beside him on G3 with his arrow off, X1 behind on H4
        s = state(['N12', 'O9', 'Q3', 'K12', 'H3'], ['H4', 'D8', 'P4', 'L11', 'G3'], [0, 0, 0, 0, 0], ball=4)
    s = s.with_(side='O', turn_n=0)
    r = shoot(s, s.ball, 'three' if jump else 'layup')
    cons = [a for a in legal_actions(r) if a.kind == 'contest']
    assert cons and all(a.piece >= 0 for a in cons)
    hard = [a for a in cons if a.shot == 'hard']
    assert (not hard) if jump else hard                          # the block only inside
    normal = [a for a in cons if a.shot != 'hard']
    for a in normal + hard:
        after = apply(r, a)
        node = after if getattr(after, 'stage', None) else after.outcomes[-1][2]
        if hasattr(after, 'outcomes'):                           # a hard Contest's foul roll: the no-foul branch
            node = [o for o in after.outcomes if o[1] == 'no foul'][-1][2]
            while hasattr(node, 'outcomes'):
                node = [o for o in node.outcomes if o[1] == 'no foul'][-1][2]
        assert node.stage == 'over' and node.result.contester == a.piece
        assert node.tok_x == r.tok_x - 1                          # it took a token: one of the reply's actions
    # nobody presses Contest: the shot goes up open
    open_ = apply(r, next(a for a in legal_actions(r) if a.kind == 'end_turn'))
    assert open_.stage == 'over' and open_.result.contest == 0


def test_after_one_movement_and_a_contest_the_reply_is_spent():
    s = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    r = shoot(s)
    near = next(a for a in legal_actions(r) if a.piece == 1 and a.kind == 'move' and B.adjacent(a.dest, r.o[0]))
    r2 = apply(r, near)
    assert r2.stage == 'reaction' and r2.turn_n == 1
    assert not [a for a in legal_actions(r2) if a.kind in ('move', 'qs', 'sprint') and a.piece == 1 and False]
    # a second movement ends the reply: no Contest after it
    mv = next(a for a in legal_actions(r2) if a.kind in ('move', 'qs', 'sprint'))
    end = apply(r2, mv)
    assert end.stage == 'over' and end.result.contest == 0


@needs_node
def test_the_map_reads_shauns_shot_as_open(js28):
    from playmaker_engine import agent as AG
    s = state(SHOOT_O, SHOOT_X, [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    sq = AG.coverage(s)['squares'][0]
    lk = sq.get('C9')
    assert lk and lk['cover'] == -1 and lk['worth'] == pytest.approx(lk['value'])      # nobody can contest it in time
    t = state(SHOOT_O, ['H11', 'E7', 'P4', 'L11', 'J5'], [5, 0, 0, 0, 0]).with_(side='O', turn_n=0)
    lk2 = AG.coverage(t)['squares'][0].get('C9')
    assert lk2 and lk2['cover'] == 1 and lk2['worth'] < lk2['value']                   # a teammate one movement away contests


@pytest.fixture
def js28():
    from playmaker_engine import jsbridge
    eng = jsbridge.NodeEngine().install()
    yield eng
    eng.close()


# ---- item 3: the defender's stance, from his square and arrows ---------------------------------------------------------

def _with_x(s, d, q, arrow):
    return s.with_(x=tuple(q if j == d else p for j, p in enumerate(s.x)), arrows=tuple(arrow if j == d else a for j, a in enumerate(s.arrows)))


def _at(q, k):
    return (q[0] + B.DIRS[k][0], q[1] + B.DIRS[k][1])


def test_each_stance_is_read_from_squares_and_arrows():
    from playmaker_engine import conditions as CD
    # O5 posts on H4 (the paint); the ball with O1 at the top on I11; X5 is moved around him
    s = state(['I11', 'C9', 'O9', 'Q3', 'H4'], ['I10', 'D8', 'N8', 'P4', 'H3'], [4, 0, 0, 0, 0], ball=0, off='Twin Towers', dfn='Lockdown')
    post, bq = s.o[4], s.o[0]
    tb = CD._dir_to(post, bq)
    on_him = lambda q: B.dir_between(q, post)
    f = _at(post, tb)
    assert CD.stance(_with_x(s, 4, f, on_him(f)), 4, 4) == 'front'              # between him and the ball, on the line
    tq = _at(post, (tb + 1) % 8)
    assert CD.stance(_with_x(s, 4, tq, on_him(tq)), 4, 4) == 'three-quarter'    # the ball's side, one direction off
    bh = _at(post, (tb + 4) % 8)
    assert B.dist_rim(bh) < B.dist_rim(post)
    assert CD.stance(_with_x(s, 4, bh, on_him(bh)), 4, 4) == 'behind'           # nearer the rim, further from the ball
    far = (post[0] + 3, post[1] + 3)
    assert CD.stance(_with_x(s, 4, far, 0), 4, 4) == 'off'
    # a wing denied: O2 on C9, X2 one direction off the line to the ball, nearer it, arrow on him
    w = s.o[1]
    tw = CD._dir_to(w, bq)
    dq = next(_at(w, (tw + k) % 8) for k in (1, 7) if B.cheb(_at(w, (tw + k) % 8), bq) < B.cheb(w, bq))
    assert CD.stance(_with_x(s, 1, dq, B.dir_between(dq, w)), 1, 1) == 'deny'
    # over and under a screener: X1 next to O5 set on I5 as the screener, the ball handler's man
    t = s.with_(o=(B.parse_sq('I8'),) + s.o[1:4] + (B.parse_sq('I7'),))
    over = (B.parse_sq('I7')[0], B.parse_sq('I7')[1] + 1)
    under = (B.parse_sq('I7')[0] + 1, B.parse_sq('I7')[1] - 1)
    assert CD.screen_stance(_with_x(t, 0, over, 4), 0, 4) == 'over'
    assert CD.screen_stance(_with_x(t, 0, under, 0), 0, 4) == 'under'


@needs_node
def test_the_stances_unlock_their_conditions(js28):
    from playmaker_engine import agent as AG, conditions as CD, plan as PL
    s = state(['I11', 'C9', 'O9', 'Q3', 'H4'], ['I10', 'D8', 'N8', 'P4', 'H3'], [4, 0, 0, 0, 0], ball=0, off='Twin Towers', dfn='Lockdown').with_(side='O', turn_n=0)
    post, bq = s.o[4], s.o[0]
    f = _at(post, CD._dir_to(post, bq))
    fr = _with_x(s, 4, f, B.dir_between(f, post))
    perm = [0, 1, 2, 3, 4]
    assert any(z['stance'] == 'front' and z['x'] == 4 for z in CD.stances(fr, perm))
    roles = dict(perm=perm, roles=[])
    found = {c['id'] for c in CD.read(fr, PL.Scout(fr.ctx, 'O'), roles=roles)['found']}
    assert found & {'2', '2b'}                                      # the entry against the front: another angle, or over the top
    w = s.o[1]
    tw = CD._dir_to(w, bq)
    dq = next(_at(w, (tw + k) % 8) for k in (1, 7) if B.cheb(_at(w, (tw + k) % 8), bq) < B.cheb(w, bq))
    dn = _with_x(s, 1, dq, B.dir_between(dq, w))
    found2 = {c['id'] for c in CD.read(dn, PL.Scout(dn.ctx, 'O'), roles=roles)['found']}
    assert '14' in found2                                           # the denial opens the backdoor
    assert set(CD.UNMEASURED).isdisjoint(CD.NAMES)
    for cid in ('2', '3', '14', '19c', '21', '24', '25', '26'):
        assert cid in CD.NAMES and cid not in CD.UNMEASURED


# ---- item 2: Shaun's rulings on step 27 --------------------------------------------------------------------------------

B1 = (['J3', 'H3', 'G4', 'I4', 'N12'], ['J6', 'K5', 'M6', 'O12', 'M11'], [7, 1, 6, 5, 2])


@needs_node
def test_the_maps_answer_leads_by_the_list(js28):
    import step_22b as S
    for st in (state(*B1, ball=4, off='High-Low', dfn='Shoot and Protect').with_(side='O', turn_n=0), S._board().with_(side='O', turn_n=0)):
        a = S._js(st, only='lasting', answer=True)
        g = S._js(st, only='lasting', answer=True, answer_lead='gap')
        assert tuple(a['drivers']['list']) <= tuple(g['drivers']['list'])     # the list first: it leaves no more by the list
        assert g['L'] <= a['L'] + 1e-9                                         # the gap-led one is only ever lower on the gap
    from playmaker_engine.agent import CONFIG
    assert CONFIG['eval'].get('answer_lead', 'list') == 'list'


@needs_node
def test_the_read_ahead_counts_both_outcomes_of_a_pass(js28):
    from playmaker_engine import agent as AG, plan as PL
    s = state(*B1, ball=4, off='High-Low', dfn='Shoot and Protect').with_(side='O', turn_n=0)
    seen = 0
    for w, after, act in PL._continuations(s, None):
        if act.kind != 'pass' or not after.pending:
            continue
        nxt, dn = PL._defence_turn(after)
        caught = PL.list_key(AG.coverage(nxt.with_(turn_n=0), only='lasting'))
        k, p = PL._both_outcomes(after, caught)
        assert p is not None and 0 <= p <= 1
        if p < 1 - 1e-9:
            seen += 1
            from playmaker_engine.resolve import _turnover
            stop = _turnover(after.with_(pending=None, approach=-1))
            sk = PL.list_key(AG.coverage(stop.with_(side='O', turn_n=0), only='lasting')) if stop.stage == 'play' else ((), 0.0, 0)
            n = max(len(caught[0]), len(sk[0]))
            u = list(caught[0]) + [0.0] * (n - len(caught[0]))
            v = list(sk[0]) + [0.0] * (n - len(sk[0]))
            want = sorted((p * a + (1 - p) * (b + RC.TURNOVER_POINTS) for a, b in zip(u, v)), reverse=True)
            assert list(k[0]) == pytest.approx(want, abs=1e-5)
            assert k[0][0] < caught[0][0]                          # a pass that may be stopped reads below a sure catch
        else:
            assert k == caught
    assert seen


@needs_node
def test_the_plan_line_is_the_route(js28):
    from playmaker_engine import plan as PL
    s = state(*B1, ball=4, off='High-Low', dfn='Shoot and Protect').with_(side='O', turn_n=0)
    h = PL.horizon_read(s, budget=60.0, depth=PL.HORIZON_TURNS)
    assert h['turns'] > 1
    plan = PL.route_plan(s, PL.Scout(s.ctx, 'O'), None, h)
    assert plan['target'].startswith('Plan: ' + h['path'][0]['offence'])     # the route the computer chases comes first
    assert plan['route'] == h['path'][0]['act']
    assert plan['needs'].startswith('Needs: ')
    words = ' '.join(PL.plan_words(plan))
    assert 'Read ahead' not in words                                      # one plan on screen, not a plan beside a route


@needs_node
def test_the_wider_search_reaches_the_post(js28):
    from playmaker_engine import agent as AG, plan as PL
    from playmaker_engine import scouting as SCT
    make = lambda o, b, x, a: state([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), ball=b, off='High-Low', dfn='Shoot and Protect')
    sq = [B.parse_sq(q) for q in ['I11', 'C9', 'O9', 'A3', 'Q3']]          # the table squares: the Post Scorer C in the corner
    seen = {}

    def read(sq_, b):
        k = (tuple(sq_), b)
        if k not in seen:
            m = AG._map_setup(make, list(sq_), b, evals=0)
            seen[k] = (PL._okey(m), m) if m else None
        return seen[k]
    jobs = PL._job_variants(make, read, sq, 0, float('inf'))
    st = make(sq, 0, *read(sq, 0)[1][:2])
    c = next(a for a in range(5) if SCT.position(st.ctx.off[a]) == 'C')
    posts = [z for z in jobs if z['o'] == c and z['job'] in ('post', 'roll')]
    assert posts and all(B.zone(z['q']) == 'K' for z in posts)             # his best post and roll squares, in the paint
    assert all(z['r'] for z in posts)                                      # each read the same quick way as the rest
