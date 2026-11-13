"""Step 18j: seeing a Steal that a movement sets up. search.dice_in_hand, eval.ball_loss and search.keep_settled, each
off unless the gate passed it. Nothing names the turn to play: these change what a list keeps and what a stopped
position is worth, from the rules' own chances."""
from conftest import P
from playmaker_engine import rules_config as RC
from playmaker_engine import search as SE
from playmaker_engine.scenarios import game_state

APP = RC.with_rules(digital=True)
O = ['I11', 'C9', 'O9', 'A3', 'Q3']


def board(x, arrows, **kw):
    s = game_state('Five Out', 'High-Low', O, x, arrows, rules=APP, check=False, ball=3)      # O4 has the ball on A3
    return s.with_(side='X', **kw)


def test_a_defender_with_his_arrow_on_the_ball_handler_can_steal_from_where_he_stands():
    s = board(['I10', 'D8', 'B4', 'G4', 'N4'], ['N', 'NE', 'SW', 'N', 'N'])          # X3 on B4 facing SW: on A3
    assert SE.steal_spot(s, 2) == (P('B4'), 5)


def test_a_defender_with_his_move_in_hand_can_step_in_and_face_him():
    s = board(['I10', 'D8', 'E4', 'G4', 'N4'], ['N', 'NE', 'W', 'N', 'N'])           # X3 on E4: a Move reaches B4
    spot = SE.steal_spot(s, 2)
    assert spot is not None and spot[0] in (P('B4'), P('B3'), P('B2'), P('A4'), P('A2'))
    from playmaker_engine import board as B
    assert B.dir_between(spot[0], P('A3')) == spot[1]                                 # he faces the ball handler there


def test_a_defender_who_has_spent_his_move_and_cannot_quick_step_there_cannot():
    s = board(['I10', 'D8', 'E4', 'G4', 'N4'], ['N', 'NE', 'W', 'N', 'N'], moved_x=1 << 2)
    assert SE.steal_spot(s, 2) is None                                                # his Move is gone: no step in
    far = board(['I10', 'D8', 'F4', 'G4', 'N4'], ['N', 'NE', 'W', 'N', 'N'])
    assert SE.steal_spot(far, 4) is None                                              # X5 on N4: nowhere near


def test_the_three_switches_are_off_unless_the_gate_passed_them():
    cfg = SE.CONFIG
    for group, name in (('search', 'dice_in_hand'), ('search', 'keep_settled'), ('eval', 'ball_loss')):
        assert cfg[group].get(name) in (True, False, 'offence')
