"""The first interception ruling (OQ-72, intercept_rule='ring_jump'): the passer's ring, through you, jumping the
lane, follow then jump, the outcomes, and the pass-lane marks. Kept as the record of that rule (old logs replay
under it); the live rule, move_then_intercept, is tested in test_intercepts_mti.py."""
from fractions import Fraction as F

from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import (Action, legal_actions, lane_crossing, passer_ring, lane_marks, follow_jumps,
                                      MOVEMENT)
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import score

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']


RJ = RC.with_rules(intercept_rule='ring_jump', turnover_cost='legacy', arrow_mode='wedge')   # built for the wedge


def board(o=TABLE_O, x=TABLE_X, arrows=ARROWS, **kw):
    return game_state('Five Out', 'High-Low', o, x, arrows, rules=RJ, check=False).with_(**kw)


def passed(s, r):
    return apply(s, Action('pass', 'O', s.ball, target=r))


def icpts(s, j=None):
    return [a for a in legal_actions(s) if a.kind == 'intercept' and (j is None or a.piece == j)]


def test_the_rule_is_kept():
    assert RJ.intercept_rule == 'ring_jump' and 'ring_jump' in RC.INTERCEPT_RULES


# ---- the passer's ring --------------------------------------------------------------------------------

def test_a_defender_next_to_the_passer_has_no_intercept_whatever_his_facing():
    # the pass from I11 straight down to I5 runs through X1 on I10, next to the passer
    for arrow in B.DIR_NAMES:
        s = passed(board(o=['I11', 'C9', 'I5', 'A3', 'Q3'], arrows=[arrow, 'NE', 'NW', 'N', 'N']), 2)
        assert s.pending and P('I10') in passer_ring(s)
        assert not icpts(s, 0), arrow


def test_a_lane_jump_cannot_end_on_a_ring_square():
    # pass I11 -> C9; X2 on H9 facing N: his ray meets the pass on H11, next to the passer
    s = passed(board(x=['Q14', 'H9', 'N8', 'G4', 'N4'], arrows=['N', 'N', 'NW', 'N', 'N']), 1)
    k = lane_crossing(P('H9'), B.DIR_NAMES.index('N'), P('I11'), P('C9'))
    assert B.add(P('H9'), (0, k)) == P('H11') and P('H11') in passer_ring(s)
    assert not any(a.dest == P('H11') for a in icpts(s, 1))


def test_inside_the_ring_the_pass_cant_be_challenged_but_further_along_it_can():
    # pass I11 -> C9 passes H11 (in the ring) and G10 (outside it)
    near = passed(board(x=['H11', 'D12', 'N8', 'G4', 'N4'], arrows=['W', 'NE', 'NW', 'N', 'N']), 1)
    far = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=['W', 'NE', 'NW', 'N', 'N']), 1)
    assert not icpts(near, 0)
    assert Action('intercept', 'X', 0) in icpts(far, 0)


# ---- through you -----------------------------------------------------------------------------------------

def test_through_you_any_facing_outside_the_ring():
    for arrow in B.DIR_NAMES:
        s = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=[arrow, 'NE', 'NW', 'N', 'N']), 1)
        assert Action('intercept', 'X', 0) in icpts(s, 0), arrow


# ---- jumping the lane --------------------------------------------------------------------------------------

def test_a_lane_jump_is_one_straight_move_along_either_wedge_line_to_the_crossing_square():
    # pass I11 -> O9; X3 (Quick Step 0) on N8, wedge NW + N: each line meets the pass two squares out
    s = passed(board(), 2)
    got = {(a.dest, a.target) for a in icpts(s, 2)}
    assert got == {(P('L10'), 0), (P('N10'), 0)}           # NW to L10, N to N10, both by his Move


def test_no_lane_jump_by_sprint_by_turning_or_off_the_arrow():
    # X3 on N7, wedge NW + N: the crossing on the N line is three squares up (N10), past a diagonal Move's reach
    # on the NW line, and his Quick Step is 0: only the straight N Move reaches it
    s = passed(board(x=['Q14', 'D8', 'N7', 'G4', 'N4'], arrows=['N', 'NE', 'NW', 'N', 'N']), 2)
    assert {a.dest for a in icpts(s, 2)} == {P('N10')}
    # facing S, nothing reaches the pass along his arrow: a Move onto the line is only a movement
    away = passed(board(x=['Q14', 'D8', 'N8', 'G4', 'N4'], arrows=['N', 'NE', 'S', 'N', 'N']), 2)
    assert not icpts(away, 2)
    onto = next(a for a in legal_actions(away) if a.kind == 'move' and a.piece == 2 and a.dest == P('N10'))
    t = apply(away, onto)
    assert t.pending and not icpts(t, 2)                    # on the line by a turn and a Move: no Intercept
    assert not any(a.dest for a in icpts(away) if a.piece == 2)


def test_the_jump_spends_the_movement_it_uses():
    s = passed(board(), 2)
    jump = next(a for a in icpts(s, 2) if a.dest == P('N10'))
    node = apply(s, jump)
    caught = force(node, 'success')                          # the pass completes
    assert caught.x[2] == P('N10') and caught.moved('X', 2) and caught.arrows[2] == s.arrows[2]
    # a Quick Step jump: X1 (Quick Step 2) on L9 facing N with his Move used: N ray meets O1 -> O3 on L10
    q = passed(board(x=['L9', 'D8', 'P6', 'G4', 'N4'], arrows=['N', 'NE', 'NW', 'N', 'N'], moved_x=1), 2)
    qj = [a for a in icpts(q, 0) if a.dest is not None]
    assert qj and all(a.target == 1 for a in qj)
    after = force(apply(q, qj[0]), 'success')
    assert after.quick_stepped('X', 0) and after.count('X', 'qs') == 1


def test_follow_then_jump_and_no_intercept_after_a_move_into_the_ring():
    s = passed(board(), 1)                                   # O1 on I11 -> O2 on C9; X1 starts in the ring
    assert not icpts(s, 0)
    pairs = [(m, a) for m, a in follow_jumps(s) if m.piece == 0]
    assert pairs
    m, a = pairs[0]
    t = apply(s, m)
    assert t.pending and a in icpts(t, 0) and a.target == 1  # moved, then a straight Quick Step jump
    ring_move = next(x for x in legal_actions(s) if x.kind == 'move' and x.piece == 0 and x.dest in passer_ring(s)
                     and x.dest != s.x[0])
    assert not icpts(apply(s, ring_move), 0)                 # his movement ends in the ring: no Intercept


def test_a_diagonal_pass_crossing_a_diagonal_ray_between_corner_squares_is_caught_at_the_crossing_square():
    # pass C3 -> I9 (NE diagonal); a ray from G4 going NW passes F5, E6 ... and the pass slips between F5 and
    # E6 (it runs through E5 and F6): the crossing square is E6, the first ray square past the intersection
    a, b = P('C3'), P('I9')
    k = lane_crossing(P('G4'), B.DIR_NAMES.index('NW'), a, b)
    assert k == 2 and B.add(P('G4'), (-2, 2)) == P('E6')


def test_under_the_wedge_each_arrow_line_can_jump_a_lane():
    s = passed(board(), 2)
    lines = {B.dir_between(s.x[2], B.add(s.x[2], ((a.dest[0] - s.x[2][0]) // 2, (a.dest[1] - s.x[2][1]) // 2)))
             for a in icpts(s, 2)}
    assert lines == {B.DIR_NAMES.index('NW'), B.DIR_NAMES.index('N')}
    single = passed(game_state('Five Out', 'High-Low', TABLE_O, TABLE_X, ARROWS, rules=RC.with_rules(arrow_mode='single', intercept_rule='ring_jump', turnover_cost='legacy'), check=False), 2)
    assert {a.dest for a in icpts(single, 2)} == {P('L10')}          # one arrow: NW only


# ---- outcomes ---------------------------------------------------------------------------------------------

def test_a_successful_intercept_ends_the_possession_at_minus_5():
    s = passed(board(), 2)
    jump = next(a for a in icpts(s, 2) if a.dest == P('N10'))
    node = apply(s, jump)
    o, x = s.ctx.off[0], s.ctx.dfn[2]
    p = F(max(0, min(20, o.r['pass'] - x.r['intercept'])), 20)
    assert {lab: pr for pr, lab, _ in node.outcomes} == {'success': p, 'failure': 1 - p}
    won = force(node, 'failure')
    assert won.stage == 'over' and score(won).total == -5


def test_a_failed_intercept_leaves_him_on_the_crossing_square_with_his_move_used():
    s = passed(board(x=['G10', 'D12', 'N8', 'G4', 'N4'], arrows=['W', 'NE', 'NW', 'N', 'N']), 1)
    missed = force(apply(s, Action('intercept', 'X', 0)), 'success')        # through his square, the pass completes
    assert missed.ball == 1 and missed.x[0] == P('G10') and missed.moved('X', 0)


# ---- the Steal is unchanged ------------------------------------------------------------------------

def test_a_ring_defender_with_his_arrow_on_the_carrier_may_steal():
    s = board(side='X')                                       # X1 on I10, arrow N at the carrier on I11
    assert any(a.kind == 'steal' and a.piece == 0 for a in legal_actions(s))


# ---- the marks the interface shows ------------------------------------------------------------------

def test_the_pass_lane_marks_match_exactly_what_the_engine_allows():
    s = board()
    for r in range(1, 5):
        pend = passed(s, r)
        marks, ring = lane_marks(pend)
        assert set(ring) == passer_ring(pend)
        now = {(a.piece, a.dest if a.dest else pend.x[a.piece]) for a in icpts(pend)}
        assert {(m['defender'], m['sq']) for m in marks if m['how'] in ('through', 'jump')} == now
        # follow then jump: every movement the engine allows, then every Intercept it allows from there
        later = set()
        for m in legal_actions(pend):
            if m.kind not in MOVEMENT:
                continue
            t = apply(pend, m)
            if isinstance(t, ChanceNode) or not t.pending or t.side != 'X':
                continue
            later |= {(a.piece, a.dest) for a in icpts(t, m.piece) if a.dest is not None}
        assert {(m['defender'], m['sq']) for m in marks if m['how'] == 'follow'} == later, r


def test_a_teammates_movement_does_not_open_a_jump():
    """X1 on M9 blocks X3's NW line (N8 -> M9 -> L10) to the pass O1 -> O3; X3 can only jump north, to N10.
    X1 moves out of the way: X3's NW jump to L10 would now be clear, but it would follow a teammate's movement,
    not his own, so it isn't legal. X1 himself, having moved, may jump from his new square."""
    s = passed(board(x=['M9', 'D8', 'N8', 'G4', 'N4'], arrows=['S', 'NE', 'NW', 'N', 'N']), 2)
    assert {a.dest for a in icpts(s, 2)} == {P('N10')}
    path = {P('M9'), P('L10'), P('N9'), P('N10')}
    away = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest not in path
                and a.dest not in passer_ring(s) and B.cheb(a.dest, P('M9')) >= 2)
    t = apply(s, away)
    assert t.pending and t.turn_n == 1
    assert not icpts(t, 2)                                   # no jump for X3 after X1's movement
    from playmaker_engine.actions import lane_jumps
    assert P('L10') in {q for q, _ in lane_jumps(t, 2)}       # though the geometry would allow it now
    marks, _ = lane_marks(s)
    assert (2, P('L10')) not in {(m['defender'], m['sq']) for m in marks}
