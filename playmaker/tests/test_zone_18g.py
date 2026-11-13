"""Step 18g (D-167, under test, the app only): the zone of influence. With rules.zone on each defender carries two
arrows 45 degrees apart; a ball handler or shooter on either is covered, a pass can be Intercepted along either, an
adjacent ball handler can't pass through the zone, the zone reaches as far as the movement the defender has left, and
a Dribble won against him breaks it until the phase ends. Off by default: with the switch off nothing changes."""
from conftest import P
from playmaker_engine import board as B
from playmaker_engine import geometry as G
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, intercept_status, zone, sprint_dir
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options

ZONE = RC.with_rules(zone='on')
O = ['I11', 'C9', 'O9', 'A3', 'Q3']
X = ['I10', 'D8', 'N8', 'G4', 'N4']
D = {n: i for i, n in enumerate(B.DIR_NAMES)}


def board(o, x, arrows, rules=None, ball=0, **kw):
    s = game_state('Five Out', 'High-Low', o, x, arrows, ball=ball, rules=rules, check=False)
    return s.with_(**kw) if kw else s


def test_the_zone_is_off_by_default():
    assert RC.with_rules().zone == 'off'
    s = board(O, X, ['N', 'NE', 'NW', 'N', 'N'])
    assert G.lines(s.ctx.rules, s.arrows[0]) == (D['N'],)


def test_the_zone_holds_both_lines_and_the_squares_between_them():
    """X4 on G4 facing N: one line today; under the zone the N line, the NE line and squares strictly between."""
    one = zone(board(O, X, ['N', 'NE', 'NW', 'N', 'N']), 3)
    two = zone(board(O, X, ['N', 'NE', 'NW', 'N', 'N'], ZONE), 3)
    assert set(one) < set(two)
    assert P('H5') in two and P('H5') not in one                       # the second line
    assert P('H6') in two                                              # strictly between the lines
    assert P('F5') not in two and P('H4') not in two                   # outside the angle


def test_the_zone_shrinks_with_the_movement_he_has_left():
    s = board(O, X, ['N', 'NE', 'NW', 'N', 'N'], ZONE).with_(side='X')
    full = zone(s, 3)
    turn = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 3 and a.dest == s.x[3])
    after = zone(apply(s, turn), 3)
    assert len(after) < len(full) and set(after.values()) <= {'qs'}    # his Move is spent: only Quick Step reach is left


def test_a_steal_and_a_contest_are_on_him_along_either_arrow():
    """X1 on I10, O1 with the ball on I11 (N of him). Facing NW his second line (N) is on the ball."""
    steal = lambda rules, a: any(x.kind == 'steal' and x.piece == 0
                                 for x in legal_actions(board(O, X, [a, 'NE', 'NW', 'N', 'N'], rules).with_(side='X')))
    assert steal(None, 'N') and not steal(None, 'NW')
    assert steal(ZONE, 'N') and steal(ZONE, 'NW')                      # N+NE and NW+N: both hold the ball
    assert not steal(ZONE, 'NE')                                       # NE+E: neither does

    def roll(rules, a):
        opt = next(c for c in contest_options(board(O, X, [a, 'NE', 'NW', 'N', 'N'], rules), 0, 'three') if c.defender == 0)
        return not opt.clean
    assert not roll(None, 'N') and roll(None, 'NW')
    assert not roll(ZONE, 'NW')                                        # within the angle: no foul roll
    assert roll(ZONE, 'NE')                                            # outside both arrows: the wrong-angle foul roll


def test_a_ball_handler_caught_by_one_arrow_cannot_cross_the_other_arrows_line():
    """D-170 (Shaun, 13 Nov 2026). O1 on I11, X1 on I10 under him. Facing N and NE: the N arrow has caught O1, so the NE
    line (J11, K12) is barred. He may step onto it, not cross it."""
    legal = lambda rules, a, x1='I10': legal_actions(board(O, [x1] + X[1:], [a, 'NE', 'NW', 'N', 'N'], rules))
    mv = lambda sq: Action('move', 'O', 0, P(sq))
    caught = legal(ZONE, 'N')
    assert mv('J11') in caught                                         # onto the barred arrow's own square: allowed
    assert mv('K11') not in caught and mv('L11') not in caught         # past it, along the row: every path crosses
    assert mv('J12') in caught                                         # J12 is on his own side of the line: no crossing
    assert mv('H11') in caught and mv('G11') in caught                 # away in another direction: free
    assert mv('K11') in legal(None, 'N')                               # today's rules: nothing bars it


def test_a_defender_whose_arrows_do_not_catch_him_bars_nothing():
    """X1 on I10 facing E and SE: neither arrow points at O1 on I11. Step 18g's reading barred the drive through his
    zone; Shaun's words (D-170) bar nothing."""
    drive = Action('move', 'O', 0, P('K9'))
    can = lambda rules, a: drive in legal_actions(board(O, X, [a, 'NE', 'NW', 'N', 'N'], rules))
    assert can(ZONE, 'E')                                              # the zone: not caught, nothing barred
    assert not can(None, 'E')                                          # today's rules: the E arrow's zone bars it


def test_he_is_caught_mid_movement_by_a_help_defenders_arrow():
    """X2 stands two squares off, on K10, facing W and NW: his W arrow points at J10. O1 steps I11 - J10 and is caught
    there, with no reaction; the NW line (J11) is then barred, so he can't go on to K11 or J12 across it."""
    x = ['G4', 'K10', 'N8', 'G5', 'N4']
    s = board(O, x, ['N', 'W', 'NW', 'N', 'N'], ZONE)
    from playmaker_engine.actions import capture_lines, capture_ok
    caps = capture_lines(s, 0)
    assert capture_ok(P('I11'), [P('J10')], caps)                      # he may step onto the arrow's square
    assert not capture_ok(P('I11'), [P('J10'), P('K11')], caps)        # caught there: the corner across the NW line
    assert capture_ok(P('I11'), [P('J10'), P('J9')], caps)             # away from the barred line: free
    assert capture_ok(P('I11'), [P('J11'), P('K11')], caps)            # never touched an arrow's square: not caught
    broken = s.with_(beaten=((0, 1),))
    assert capture_ok(P('I11'), [P('J10'), P('K11')], capture_lines(broken, 0))   # a won Dribble: nothing bars him


def test_a_pass_can_be_intercepted_along_either_arrow():
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['F7', 'P2', 'N4', 'K4', 'Q6']
    pend = lambda rules, a: board(o, x, [a, 'N', 'N', 'N', 'N'], rules).with_(pending=(0, 1), side='X')
    assert intercept_status(pend(None, 'W'), 0) is None
    assert intercept_status(pend(ZONE, 'W'), 0) == 'approach'          # W+NW: the second line crosses the pass
    assert intercept_status(pend(ZONE, 'NE'), 0) is None               # NE+E: neither does


def test_a_dribble_won_against_him_breaks_his_zone_until_the_phase_ends():
    s = board(O, X, ['N', 'NE', 'NW', 'N', 'N'], ZONE)
    assert zone(s, 0)
    broken = s.with_(beaten=((0, 0),))
    assert zone(broken, 0) == {}                                       # the zone is gone
    assert G.lines(ZONE, G.stance(ZONE, broken.arrows[0], True)) == ()
    assert not any(a.kind == 'steal' and a.piece == 0 for a in legal_actions(broken.with_(side='X')))
    opt = next(c for c in contest_options(broken, 0, 'three') if c.defender == 0)
    assert not opt.clean                                               # his Contest is read as no arrow on the shooter
    assert Action('move', 'O', 0, P('K9')) in legal_actions(broken)    # and nothing bars the drive
    same = board(O, X, ['N', 'NE', 'NW', 'N', 'N']).with_(beaten=((0, 0),))
    assert zone(same, 0) == zone(board(O, X, ['N', 'NE', 'NW', 'N', 'N']), 0)   # today's rules: nothing changes


def test_a_sprint_keeps_the_run_as_one_arrow_and_the_defender_picks_the_other():
    o, x = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['K4', 'D8', 'N8', 'G4', 'I10']
    s = board(o, x, ['S', 'NE', 'NW', 'N', 'N'], ZONE).with_(side='X')
    sprints = [a for a in legal_actions(s) if a.kind == 'sprint' and a.piece == 0]
    assert sprints
    dest = sprints[0].dest
    both = [a for a in sprints if a.dest == dest]
    assert len(both) == 2
    run = sprint_dir(s.x[0], dest)
    ends = {G.lines(ZONE, G.stance(ZONE, apply(s, a).arrows[0])) for a in both}
    assert all(run in e for e in ends) and len(ends) == 2, ends
