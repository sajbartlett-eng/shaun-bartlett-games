"""The rulebook revision of Nov 2026 (reference/Playmaker_Rulebook.pdf), checked clause by clause against the
engine. Two rulings changed the engine: a lane jump keeps the defender's facing (OQ-76), and 'through you' means
the pass line passes through the square's centre (OQ-13)."""
from conftest import P

from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, approach_moves, mti_approach
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'N', 'N', 'N']


def board(o=TABLE_O, x=TABLE_X, arrows=ARROWS, rules=None, **kw):
    return game_state('Five Out', 'High-Low', o, x, arrows, rules=rules or RC.DEFAULT_RULES, check=False).with_(**kw)


def passed(s, r):
    return apply(s, Action('pass', 'O', s.ball, target=r))


def icpts(s, j=None):
    return [a for a in legal_actions(s) if a.kind == 'intercept' and (j is None or a.piece == j)]


def test_the_rulebook_settings():
    r = RC.Rules()
    assert r.on_line_tolerance == 0                          # through you: the line passes through the centre
    assert r.intercept_rule == 'move_then_intercept' and r.turnover_cost == 'minus5_lose_phase'
    assert r.screen_rule == 'hold_until_move' and r.drive_rule == 'zone' and r.contest_choice == 'player'
    assert r.and_one and not r.carrier_can_screen and r.defence_empty_ends_phase
    assert RC.FAR_CONTEST_PENALTY == 3 and RC.TURNOVER_POINTS == -5 and RC.STEAL_FOUL_BONUS == 5
    assert RC.FT_MULT_TWO == 2 and RC.FT_MULT_THREE == 3 and RC.START_CLOCK == 12 and RC.TOKENS_PER_PHASE == 6
    assert RC.LIMITS['O']['hesitate'] == 1 and RC.LIMITS['X']['pause'] == 1


def test_a_lane_jump_move_keeps_the_facing():
    # pass I11 -> O9; X3 on N8 facing N reaches the line with one straight Move north
    s = passed(board(), 2)
    moves = approach_moves(s, 2)
    assert moves, 'X3 has a lane jump'
    assert all(m.arrow == s.arrows[2] for m in moves if m.kind == 'move')      # the Move keeps his arrow
    m = next(m for m in moves if m.kind == 'move')
    turned = Action('move', 'X', 2, m.dest, (m.arrow + 1) % 8)
    assert not mti_approach(s, turned)                                        # a turn is not a lane jump
    t = apply(s, m)
    assert t.arrows[2] == s.arrows[2] and t.pending and icpts(t) == [Action('intercept', 'X', 2)]
    # the turned Move is a plain movement if it is legal at all: the pass lands before anything else
    if turned in legal_actions(s):
        u = apply(s, turned)
        assert not u.pending and not icpts(u)


def test_through_you_needs_the_line_through_the_centre():
    # pass I11 (8,11) -> O9 (14,9): at column L the line passes y = 10 exactly (L10); at column K it passes y = 10.33 (K10 is off it)
    on = passed(board(x=['L10', 'D8', 'N8', 'G4', 'N4']), 2)
    assert Action('intercept', 'X', 0) in icpts(on)
    off = passed(board(x=['K10', 'D8', 'N8', 'G4', 'N4']), 2)
    assert Action('intercept', 'X', 0) not in icpts(off)
    # the old reading (the middle half of the square) counted K9 as on the line
    old = passed(board(x=['K10', 'D8', 'N8', 'G4', 'N4'], rules=RC.with_rules(on_line_tolerance=0.5)), 2)
    assert Action('intercept', 'X', 0) in icpts(old)
