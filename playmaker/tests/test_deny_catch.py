"""The designer's report on Five Out v High-Low: every possession ended with a pass to O2 for a contested three
(Three 13▲ v X2's contest 3▼ = 30) because the defence never took the catch away. The computer defence (Starter and
All-Star, not Rookie) now denies an elite shooter's catch: when an off-ball attacker's best look after the reaction is
the offence's top threat and his own defender can't contest it well, it prefers a body on the lane to him (through
him, or one straight movement along an arrow onto it), the face-guard or top-lock, and help shaded toward him, valued
by what the offence is left with: the next-best option after the reaction. No rule changes."""
import pytest

from playmaker_engine import board as B
from playmaker_engine import computer as C
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.capacity import lane_reach
from playmaker_engine.headtohead import TABLE_O, TABLE_X, TABLE_ARROWS
from playmaker_engine.planner import elite_threat, defence_objectives, level_objectives, objective_plays
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import game_state

O2 = 1


def start():
    return game_state('Five Out', 'High-Low', TABLE_O, TABLE_X, TABLE_ARROWS)


def after_offence_move(s):
    """The offence's first action, a one-square lift by the carrier, then the defence to act."""
    a = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == B.parse_sq('I12'))
    t = apply(s, a)
    end = next(x for x in legal_actions(t) if x.kind == 'end_turn')
    return apply(t, end)


def defence_turn(s, level, seed=1):
    comp = C.Computer('X', level, seed=seed, habits=[], budget_s=None)
    for _ in range(3):
        if s.stage != 'play' or s.side != 'X':
            break
        a = comp.choose(s)
        s = apply(s, a)
        assert not isinstance(s, ChanceNode)
    return s


def lanes_to(s, att):
    """For each attacker who could pass to att (the carrier now, the others if they held the ball): is some defender
    on the lane or able to reach it with one straight movement along his arrow?"""
    out = {}
    for p in range(5):
        if p == att or not B.on_board(s.o[p]):
            continue
        h = s.with_(ball=p, side='O', stage='play', turn_n=0, pending=None, approach=-1, tok_o=max(1, s.tok_o))
        out[p] = any(lane_reach(h, j, p, att) for j in range(5))
    return out


def test_levels():
    assert 'DO-denycatch' not in level_objectives('rookie')
    assert 'DO-denycatch' in level_objectives('starter') and 'DO-denycatch' in level_objectives('allstar')


def test_the_pairing_has_an_elite_threat_to_deny():
    s = start()
    et = elite_threat(s)
    assert et and et['shot'] == 'three' and et['att'] in (O2, 3)       # O2 (13▲ v a 3▼) or O4 (11▲, nobody near)
    objs = defence_objectives(after_offence_move(s), 'allstar')
    assert objs[0]['id'] == 'DO-denycatch'
    plays = objective_plays(after_offence_move(s), objs[0], legal_actions(after_offence_move(s)))
    assert plays and all(p.concept == 'deny the catch' for p in plays)


def test_all_star_defence_puts_a_body_on_the_lanes_to_the_threat():
    s = after_offence_move(start())
    et = elite_threat(s)
    t = defence_turn(s, 'allstar')
    lanes = lanes_to(t, et['att'])
    assert lanes[t.ball], f"the carrier's lane to O{et['att'] + 1} is open after the defence's turn: {lanes}"
    assert sum(lanes.values()) >= 2, f"lanes to O{et['att'] + 1} covered: {lanes}"   # two Moves a turn: the ball's lane and a swing


def test_rookie_defence_does_not_use_it():
    s = after_offence_move(start())
    objs = defence_objectives(s, 'rookie')
    assert all(o['id'] != 'DO-denycatch' for o in objs)


def test_all_star_placement_covers_the_lane_to_the_threat():
    """Setup step 5: the defence places after the offence. The computer's placement answers the lane from the ball
    to the elite threat before the first pass is thrown."""
    from playmaker_engine.computer import place_defence
    o_sq = [B.parse_sq(q) for q in TABLE_O]
    build = lambda xq, ar: game_state('Five Out', 'High-Low', TABLE_O, [B.sq(q) for q in xq], list(ar), check=False)
    comp = C.Computer('X', 'allstar', seed=1, habits=[], budget_s=None)
    xs, arrows, perm = place_defence(comp, o_sq, 0, build, budget_s=20)
    s = build(xs, arrows)
    et = elite_threat(s)
    if et is None:
        return                                           # the placement itself removed the threat: fine
    assert any(lane_reach(s, j, 0, et['att']) for j in range(5)), f"O1's lane to O{et['att'] + 1} is open at setup: {[B.sq(q) for q in xs]} {arrows}"
