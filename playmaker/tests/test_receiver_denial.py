"""Receiver denial (the designer's ruling, receiver_denial=True by default): a pass may not travel through the square of
a defender next to the receiver; the lane is blocked, not interceptable, whatever his facing. "Through" is the pass line
within half a square of his centre. Defenders elsewhere on the line are unchanged (through-you intercept, the roll as
normal). Pass I11 (8,11) -> O9 (14,9) in these positions."""
import pytest

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, denier, denied_lanes, why_illegal, MOVEMENT
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']


def board(x3, arrow='N', rules=None):
    x = ['I10', 'D8', x3, 'G4', 'N4']
    return game_state('Five Out', 'High-Low', TABLE_O, x, ['N', 'NE', arrow, 'N', 'N'], rules=rules, check=False)


PASS_TO_O3 = Action('pass', 'O', 0, target=2)


def test_the_default_and_the_setting():
    assert RC.Rules().receiver_denial is True and RC.Rules().receiver_denial_tol == 0.5
    s = board('N9', rules=RC.with_rules(receiver_denial=False))
    assert PASS_TO_O3 in legal_actions(s)                      # without the ruling the lane is open


@pytest.mark.parametrize('arrow', B.DIR_NAMES)
def test_a_pass_through_a_defender_next_to_the_receiver_is_illegal_whatever_his_facing(arrow):
    # N9 (13,9) is next to O9 and the line passes 0.32 of a square from its centre
    s = board('N9', arrow)
    assert denier(s, 0, 2) == 2 and dict(receiver=2, defender=2) in denied_lanes(s)
    assert PASS_TO_O3 not in legal_actions(s)
    assert 'denied' in why_illegal(s, PASS_TO_O3) and 'X3' in why_illegal(s, PASS_TO_O3)
    with pytest.raises(ValueError, match='denied'):
        apply(s, PASS_TO_O3, check=True)


def test_a_pass_beside_him_is_legal():
    # N10 (13,10) is next to O9 but the line passes 0.63 of a square from its centre: not through him
    s = board('N10')
    assert denier(s, 0, 2) is None and PASS_TO_O3 in legal_actions(s)


def test_a_defender_not_next_to_the_receiver_is_still_a_through_you_intercept():
    # L10 (11,10) is on the line (through its centre) but three squares from O9
    s = board('L10')
    assert denier(s, 0, 2) is None and PASS_TO_O3 in legal_actions(s)
    t = apply(s, PASS_TO_O3)
    assert t.pending == (0, 2) and Action('intercept', 'X', 2) in legal_actions(t)


