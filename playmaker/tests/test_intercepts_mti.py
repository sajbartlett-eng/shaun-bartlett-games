"""The interception ruling as refined (intercept_rule='move_then_intercept', the default) and what a turnover costs
(turnover_cost='minus5_lose_phase', the default, intercepts and steals alike): jumping the lane with one straight
movement along the arrow, then the Intercept; through you; anything else first lands the pass; the passer's
ring; the pass angle; the cost; steals in play and on a shot; the catch spot; the pass-lane marks.
The positions were built under the earlier reading of "on the line" (the middle half of the square) and a lane-jump
Move that could turn; they are pinned to that reading (RC.PRE_RULEBOOK). tests/test_rulebook_nov.py holds the
rulebook reading: the line through the centre, and the facing kept."""
from fractions import Fraction as F

import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, lane_marks, approach_moves, mti_approach, MOVEMENT
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import score

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']
# The positions were built under the wedge (two arrow lines give more to test); the rule's mechanics are the same
# under the single arrow, which is the default, and the single-arrow case is tested too.
WEDGE = RC.with_rules(arrow_mode='wedge', **RC.PRE_RULEBOOK)     # the positions were built under the pre-rulebook line reading


def board(o=TABLE_O, x=TABLE_X, arrows=ARROWS, rules=None, **kw):
    return game_state('Five Out', 'High-Low', o, x, arrows, rules=rules or WEDGE, check=False).with_(**kw)


def passed(s, r):
    return apply(s, Action('pass', 'O', s.ball, target=r))


def icpts(s, j=None):
    return [a for a in legal_actions(s) if a.kind == 'intercept' and (j is None or a.piece == j)]


def mv(s, j, sq, kind='move', arrow=None):
    return next(a for a in legal_actions(s) if a.kind == kind and a.piece == j and a.dest == P(sq)
                and (arrow is None or a.arrow == B.DIR_NAMES.index(arrow)))


def test_the_defaults_and_the_kept_settings():
    r = RC.Rules()
    assert r.intercept_rule == 'move_then_intercept' and r.turnover_cost == 'minus5_lose_phase' and r.arrow_mode == 'single'
    assert r.intercept_cost == r.turnover_cost                                       # the old name
    assert RC.with_rules(intercept_cost='minus10').turnover_cost == 'minus10'
    assert set(RC.INTERCEPT_RULES) >= {'move_then_intercept', 'ring_jump', 'approach'}
    assert set(RC.TURNOVER_COSTS) >= {'minus5_lose_phase', 'minus5', 'minus10', 'lose_phase', 'end_possession'}


# ---- jump the lane --------------------------------------------------------------------------------------

def test_a_straight_move_along_the_arrow_onto_the_line_then_intercept():
    # pass I11 -> O9; X3 on N8 (wedge NW + N): N9 on his N line, L10 on his NW line are where they meet it
    s = passed(board(), 2)
    assert not icpts(s)                                    # nobody is on the line: no Intercept yet
    assert {m.dest for m in approach_moves(s, 2)} == {P('N9'), P('L10')}
    t = apply(s, mv(s, 2, 'N9'))
    assert t.pending and t.approach == 2 and icpts(t) == [Action('intercept', 'X', 2)]


def test_a_straight_quick_step_and_a_sprint_along_the_arrow_also_open_it():
    # High-Low's X1 (Quick Step 2) on I8 facing N (wedge N + NE): his NE line meets I11 -> O9 on K10
    s = passed(board(x=['I8', 'D8', 'N8', 'G4', 'N4']), 2)
    kinds = {m.kind for m in approach_moves(s, 0) if m.dest == P('K10')}
    assert kinds == {'move', 'qs', 'sprint'}
    t = apply(s, mv(s, 0, 'K10', 'qs'))
    assert t.approach == 0 and Action('intercept', 'X', 0) in icpts(t)
    # from G6 facing N: K10 is four squares up his NE line, a Sprint, which keeps his facing
    s = passed(board(x=['G6', 'D8', 'N8', 'G4', 'N4']), 2)
    sp = [m for m in approach_moves(s, 0) if m.kind == 'sprint']
    assert sp and all(m.dest == P('K10') for m in sp)
    t = apply(s, sp[0])
    assert t.arrows[0] == s.arrows[0] and Action('intercept', 'X', 0) in icpts(t)
    turned = [m for m in legal_actions(s) if m.kind == 'sprint' and m.piece == 0 and m.dest == P('K10') and m not in sp]
    assert turned and all(not mti_approach(s, m) for m in turned)        # a Sprint that turns him doesn't


def test_under_the_single_arrow_only_the_one_line_meets_the_pass():
    s = passed(board(rules=RC.with_rules(**RC.PRE_RULEBOOK)), 2)   # the single arrow: X3's single arrow NW meets I11 -> O9 on L10
    assert {m.dest for m in approach_moves(s, 2)} == {P('L10')}
    t = apply(s, mv(s, 2, 'L10'))
    assert t.approach == 2 and icpts(t) == [Action('intercept', 'X', 2)]


def test_off_the_arrow_a_turned_path_or_two_movements_do_not():
    single = RC.with_rules(arrow_mode='single', **RC.PRE_RULEBOOK)
    s = passed(board(rules=single), 2)                     # single arrow NW: N9 is off his arrow
    t = apply(s, mv(s, 2, 'N9'))
    assert not t.pending and t.ball == 2 and not icpts(t)
    s = passed(board(), 2)
    bent = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 2 and a.dest == P('M10'))
    assert B.on_segment(P('M10'), P('I11'), P('O9'), 0.5) and not mti_approach(s, bent)    # 1 diagonal + 1 straight
    t = apply(s, bent)
    assert not t.pending and not icpts(t)
    # one movement onto the line, then a second movement: the pass lands before it, no Intercept after
    t = apply(s, mv(s, 2, 'N9'))
    second = next(a for a in legal_actions(t) if a.kind in MOVEMENT and a.piece == 4)
    u = apply(t, second)
    assert not isinstance(u, ChanceNode) and not u.pending and u.ball == 2


# ---- through you -------------------------------------------------------------------------------------------

def test_through_you_is_the_first_action_whatever_the_facing():
    for arrow in B.DIR_NAMES:
        s = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=[arrow, 'NE', 'NW', 'N', 'N']), 1)
        assert Action('intercept', 'X', 0) in icpts(s), arrow


def test_through_you_is_gone_after_any_other_first_action():
    s = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=['W', 'NE', 'NW', 'N', 'N']), 1)
    first = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 4)
    t = apply(s, first)
    assert not t.pending and t.ball == 1 and not icpts(t)


# ---- anything else first --------------------------------------------------------------------------------

@pytest.mark.parametrize('kind', ['pause', 'move', 'steal'])
def test_any_other_first_action_completes_the_pass_before_it(kind):
    # X1 on G10 has the line through him; X2 on D8 faces the receiver's square, C9: a Steal is his once it lands
    s = passed(board(x=['G10', 'D8', 'N8', 'G4', 'N4'], arrows=['W', 'NW', 'NW', 'N', 'N']), 1)
    acts = [a for a in legal_actions(s) if a.kind == kind and not (kind == 'move' and mti_approach(s, a))]
    assert acts, kind
    t = apply(s, acts[0])
    t = t if not isinstance(t, ChanceNode) else force(t, t.outcomes[0][1])
    while isinstance(t, ChanceNode):
        t = force(t, t.outcomes[-1][1])
    assert not t.pending and (t.stage == 'over' or t.ball == 1)
    if t.stage == 'play' and t.side == 'X':
        assert not icpts(t)


# ---- the passer's ring ---------------------------------------------------------------------------------

def test_no_intercept_on_any_square_next_to_the_passer():
    for arrow in B.DIR_NAMES:
        s = passed(board(o=['I11', 'C9', 'I5', 'A3', 'Q3'], arrows=[arrow, 'NE', 'NW', 'N', 'N']), 2)
        assert not icpts(s, 0), arrow                       # X1 on I10: the line runs through him, in the ring
    # a movement ending in the ring opens nothing either
    s = passed(board(x=['Q14', 'H9', 'N8', 'G4', 'N4'], arrows=['N', 'N', 'NW', 'N', 'N']), 1)
    assert not any(m.dest in {P('H10'), P('H11'), P('H12')} for m in approach_moves(s, 1))


def test_the_corner_slip_fix():
    from playmaker_engine.actions import lane_meet
    # pass C3 -> I9 (a diagonal); a path from G4 going NW slips between F5 and E6: it meets the pass on E6
    assert lane_meet(P('G4'), B.DIR_NAMES.index('NW'), P('C3'), P('I9')) == 2


# ---- the pass angle -----------------------------------------------------------------------------------

def test_a_receiver_moving_toward_the_passer_removes_a_crossing_that_moving_away_creates():
    far = passed(board(), 2)                                           # O3 on O9: X3 meets it on N9 or L10
    near = passed(board(o=['I11', 'C9', 'L11', 'A3', 'Q3']), 2)        # O3 on L11, toward the passer
    assert approach_moves(far, 2) and not approach_moves(near, 2)


# ---- the cost of a successful Intercept ---------------------------------------------------------------

def _jumped(**kw):
    s = passed(board(**kw), 2)
    t = apply(s, mv(s, 2, 'N9', arrow='N'))
    return s, t, apply(t, Action('intercept', 'X', 2))


def test_a_successful_intercept_costs_minus_5_and_a_phase_and_play_goes_on():
    s, t, node = _jumped()
    o, x = s.ctx.off[0], s.ctx.dfn[2]
    p = F(max(0, min(20, o.r['pass'] - x.r['intercept'])), 20)
    assert {lab: pr for pr, lab, _ in node.outcomes} == {'success': p, 'failure': 1 - p}
    won = force(node, 'failure')
    assert won.stage == 'play' and won.side == 'O' and won.ball == 0 and won.tos == 1
    assert won.clock == s.clock - 2 and won.phase == s.phase                        # the phase goes on
    assert won.tok_o == s.tok_o and won.tok_x == t.tok_x - 1 and won.cnt == apply(t, Action('intercept', 'X', 2)).outcomes[1][2].cnt
    assert won.x[2] == P('N8') and won.arrows[2] == s.arrows[2] and won.moved('X', 2)   # back where he started
    assert won.count('O', 'pass') == 1                                               # the pass still counts


def test_in_the_final_phase_the_possession_scores_0():
    s, t, node = _jumped(clock=2)
    won = force(node, 'failure')
    assert won.stage == 'over' and score(won).total == 0


def test_a_failed_intercept_strands_him_on_the_line_with_his_move_used():
    s, t, node = _jumped()
    missed = force(node, 'success')
    assert missed.ball == 2 and missed.x[2] == P('N9') and missed.moved('X', 2)
    # through you: he is already there; his Move counts as used too
    s = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=['W', 'NE', 'NW', 'N', 'N']), 1)
    missed = force(apply(s, Action('intercept', 'X', 0)), 'success')
    assert missed.ball == 1 and missed.x[0] == P('G10') and missed.moved('X', 0)


@pytest.mark.parametrize('cost,tos,clock_lost,ends', [('minus5', 1, 0, False), ('minus10', 2, 0, False),
                                                      ('lose_phase', 0, 2, False), ('end_possession', 1, 0, True)])
def test_the_other_costs(cost, tos, clock_lost, ends):
    s, t, node = _jumped(rules=RC.with_rules(turnover_cost=cost, arrow_mode='wedge', **RC.PRE_RULEBOOK))
    won = force(node, 'failure')
    assert won.tos == tos and (won.stage == 'over') == ends
    if not ends:
        assert won.clock == s.clock - clock_lost and won.ball == 0


# ---- steals -------------------------------------------------------------------------------------------------

def _steal_node(**kw):
    s = board(side='X', **kw)                      # X1 on I10, arrow N on the carrier on I11
    return s, apply(s, Action('steal', 'X', 0))


def test_a_successful_steal_in_play_costs_minus_5_and_a_phase():
    s, node = _steal_node()
    stolen = force(node, 'no foul', 'stolen')
    assert stolen.stage == 'play' and stolen.ball == 0 and stolen.tos == 1 and stolen.clock == s.clock - 2
    assert stolen.tok_o == s.tok_o and stolen.phase == s.phase


def test_a_steal_in_the_final_phase_scores_0():
    s, node = _steal_node(clock=2)
    stolen = force(node, 'no foul', 'stolen')
    assert stolen.stage == 'over' and score(stolen).total == 0


def test_a_stolen_shot_is_cancelled_and_the_phase_keeps_its_shot():
    s = board(o=['I9', 'C9', 'O9', 'A3', 'Q3'], x=['I8', 'D8', 'N8', 'G4', 'N4'])
    r = apply(s, Action('shot', 'O', 0, shot='long'))
    t = apply(r, Action('move', 'X', 0, P('I8'), 0))
    stolen = force(apply(t, Action('steal', 'X', 0)), 'no foul', 'stolen')
    assert stolen.stage == 'play' and stolen.side == 'O' and stolen.ball == 0 and stolen.shot is None
    assert stolen.tos == 1 and stolen.clock == s.clock - 2 and stolen.count('O', 'shot') == 0
    assert any(a.kind == 'shot' for a in legal_actions(stolen))          # he may shoot again this phase


def test_steal_fouls_are_unchanged():
    s, node = _steal_node()
    first = force(node, 'foul')
    assert first.stage == 'play' and first.bonus5 == 1 and first.tos == 0 and first.clock == s.clock
    s2, node2 = _steal_node(fouls=1, bonus5=1)
    end = force(node2, 'foul')
    assert end.stage == 'over' and score(end).free_throws == 2 * s2.ctx.off[0].r['free_throw']


def test_the_shot_clock_expiry_is_unchanged():
    from playmaker_engine.resolve import end_phase
    s = board(clock=2)
    out = end_phase(s)
    assert out.tos == s.tos + 1 and out.clock == 0 and not out.zeroed       # -5 and the forced shot, as before


# ---- the catch spot ---------------------------------------------------------------------------------------

# ---- the marks the interface shows -------------------------------------------------------------------

@pytest.mark.parametrize('x,arrows', [(TABLE_X, ARROWS), (['I8', 'D8', 'N8', 'G4', 'N4'], ARROWS),
                                      (['G10', 'D12', 'N8', 'G4', 'N4'], ['W', 'NE', 'NW', 'N', 'N'])])
def test_the_pass_lane_marks_match_exactly_what_the_engine_allows(x, arrows):
    s = board(x=x, arrows=arrows)
    for r in range(1, 5):
        pend = passed(s, r)
        if isinstance(pend, ChanceNode) or not pend.pending:
            continue
        marks, ring = lane_marks(pend)
        assert set(ring) == {B.add(pend.o[0], d) for d in B.DIRS}
        through = {(a.piece, pend.x[a.piece]) for a in icpts(pend)}
        jumps = set()
        for m in legal_actions(pend):
            if m.kind not in MOVEMENT:
                continue
            t = apply(pend, m)
            if not isinstance(t, ChanceNode) and t.pending and Action('intercept', 'X', m.piece) in icpts(t):
                jumps.add((m.piece, m.dest))
        assert {(k['defender'], k['sq']) for k in marks if k['how'] == 'through'} == through, r
        assert {(k['defender'], k['sq']) for k in marks if k['how'] == 'jump'} == jumps, r
