"""Step 3i follow-up rulings: screens hold until the screener moves (OQ-29), zones of influence and the wedge,
drives through an adjacent defender's zone, and where a successful interceptor ends up."""
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, zone, is_approach, MOVEMENT
from playmaker_engine.resolve import apply, ChanceNode, force, new_phase
from playmaker_engine.scenarios import game_state

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def table(**kw):
    return game_state('Five Out', 'High-Low', TABLE_O, TABLE_X, ARROWS, check=False).with_(**kw)


def screens_for(s, i):
    return [a for a in legal_actions(s) if a.kind == 'screen' and a.piece == i]


def act(s, a):
    node = apply(s, a)
    while isinstance(node, ChanceNode):
        labels = [lab for _, lab, _ in node.outcomes]
        node = force(node, labels[0])
    return node


def move(s, i, sq, side='O'):
    return next(a for a in legal_actions(s) if a.kind == 'move' and a.side == side and a.piece == i and a.dest == P(sq))


def pass_turn(s):
    """The defence answers with as little as it can: end the turn, Pause, or a defender turning in place."""
    acts = legal_actions(s)
    a = next((x for x in acts if x.kind == 'end_turn'), None) or next((x for x in acts if x.kind == 'pause'), None) or \
        next(x for x in reversed(acts) if x.kind == 'move' and x.dest == s.x[x.piece])
    s = act(s, a)
    if s.side == 'X' and s.stage == 'play':
        s = act(s, next(x for x in legal_actions(s) if x.kind == 'end_turn'))
    return s


def test_the_new_defaults():
    r = RC.Rules()
    assert (r.screen_rule, r.arrow_mode, r.contest_geometry, r.drive_rule, r.intercept_return, r.late_closeout) == \
        ('hold_until_move', 'wedge', 'current', 'zone', True, False)


# ---- screens (OQ-29) ------------------------------------------------------------------------------

def test_a_screen_is_the_first_action_or_the_second_straight_after_the_same_players_move():
    s = table()
    assert screens_for(s, 1)                                    # first action: legal
    after_own = act(s, move(s, 1, 'D10'))
    assert screens_for(after_own, 1)                            # second, after his own Move: legal
    assert not screens_for(after_own, 2)                        # second, after a different player's Move: illegal
    third = act(after_own, move(after_own, 2, 'N10'))
    assert not screens_for(third, 1) and not screens_for(third, 3)      # a third action: illegal


def test_the_ball_carrier_has_no_legal_screen():
    s = table()
    assert not screens_for(s, s.ball)


def _screened():
    """O2 screens with the T to the east (D9), then the defence passes its turn."""
    s = table()
    a = next(x for x in screens_for(s, 1) if x.target == B.DIR_NAMES.index('E'))
    s = act(s, a)
    assert s.side == 'X' and s.is_screening(1)                  # it ends the offence's turn
    return pass_turn(s)


def test_the_screen_survives_the_offences_next_turn_when_the_screener_doesnt_move():
    s = _screened()
    s = act(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 2))
    s = act(s, next(a for a in legal_actions(s) if a.kind == 'end_turn'))
    assert s.side == 'X' and s.is_screening(1)
    s = pass_turn(s)
    assert s.side == 'O' and s.is_screening(1)


def test_the_screeners_move_ends_it_and_he_may_move_at_any_time():
    s = _screened()
    a = move(s, 1, 'B10')                                       # the screener may Move while screening
    t = act(s, a)
    assert not t.is_screening(1) and not t.screens


def test_a_successful_challenge_removes_the_screen_for_every_defender():
    # O2 at D9 screens with the T on X2's square (D8); X2 stands on the T and Challenges
    s = game_state('Five Out', 'High-Low', ['I11', 'D9', 'O9', 'A3', 'Q3'], TABLE_X, ARROWS, check=False)
    s = act(s, next(a for a in screens_for(s, 1) if a.target == B.DIR_NAMES.index('S')))
    ch = next(a for a in legal_actions(s) if a.kind == 'challenge' and a.piece == 1)
    node = apply(s, ch)
    beat = force(node, 'failure')                               # the screen roll fails: the Challenge wins
    held = force(node, 'success')
    assert beat.screens == () and not beat.locked('X', 1)       # gone, for everyone
    assert held.is_screening(1) and held.locked('X', 1)         # a failed Challenge locks the challenger


def test_a_screen_ends_with_the_phase():
    s = _screened()
    assert s.is_screening(1)
    assert new_phase(s, s.clock - RC.PHASE_SECONDS).screens == ()


def test_the_old_two_turn_rule_is_still_available():
    s = game_state('Five Out', 'High-Low', TABLE_O, TABLE_X, ARROWS, rules=RC.with_rules(screen_rule='two_turns'), check=False)
    a = next(x for x in screens_for(s, 1) if x.target == B.DIR_NAMES.index('E'))
    s = act(s, a)
    s = pass_turn(s)
    assert not any(x.kind in MOVEMENT and x.piece == 1 for x in legal_actions(s))    # the screener can't move


# ---- zones of influence -----------------------------------------------------------------------

def test_a_zone_runs_along_both_wedge_lines():
    s = table()
    z = zone(s, 1)                              # X2 on D8, wedge NE + E
    dirs = {B.dir_between(s.x[1], q) if B.adjacent(s.x[1], q) else None for q in z}
    assert P('E9') in z and P('E8') in z and {B.DIR_NAMES.index('NE'), B.DIR_NAMES.index('E')} <= dirs


def test_a_zone_ends_at_an_occupied_square():
    s = table().with_(o=(P('I11'), P('F8')) + tuple(P(q) for q in TABLE_O[2:]))
    z = zone(s, 1)                              # O2 on F8, two squares east of X2
    assert P('E8') in z and P('F8') not in z and P('G8') not in z


def test_a_used_move_shrinks_the_zone_to_quick_step_reach_and_a_lock_keeps_only_that():
    s = table()
    full = zone(s, 0)                           # X1 (High-Low's guard: Quick Step 2)
    moved = zone(s.with_(moved_x=1), 0)
    locked = zone(s.with_(lock_x=1), 0)
    assert set(moved) < set(full) and set(moved.values()) <= {'qs'}
    assert set(locked) == set(moved) and set(locked.values()) <= {'qs'}
    assert 'move' in full.values()


# ---- drives ------------------------------------------------------------------------------------

def _drive_board(beaten=()):
    # O1 has the ball on I8 with X1 next to him on I7, wedge NE + E: his zone runs J8, K9 ... and J7, K7 ...
    return game_state('Five Out', 'High-Low', ['I8', 'C9', 'O9', 'A3', 'Q3'], ['I7', 'D8', 'N8', 'G4', 'N4'],
                      ['NE', 'NE', 'NW', 'N', 'N'], check=False).with_(beaten=beaten)


def can_move(s, sq):
    return any(a.kind in MOVEMENT and a.piece == 0 and a.side == 'O' and a.dest == P(sq) for a in legal_actions(s))


def test_a_drive_through_an_adjacent_defenders_zone_is_refused_and_ending_on_it_is_allowed():
    s = _drive_board()
    assert P('J8') in zone(s, 0)
    assert can_move(s, 'J8')                    # ending on a zone square: allowed
    assert not can_move(s, 'K8')                # I8 -> J8 -> K8 goes through it: refused


def test_the_designers_case_driving_through_the_pointed_at_square_is_refused():
    """In the live test the carrier drove past a defender through the square his arrow pointed at."""
    s = _drive_board()
    pointed = B.add(s.x[0], B.DIRS[s.arrows[0]])
    assert pointed == P('J8') and not can_move(s, 'L8')


def test_a_dribble_win_lifts_the_restriction_for_that_defender():
    assert can_move(_drive_board(beaten=((0, 0),)), 'K8')


def test_off_ball_players_are_not_restricted():
    s = game_state('Five Out', 'High-Low', ['A12', 'I8', 'O9', 'A3', 'Q3'], ['I7', 'D8', 'N8', 'G4', 'N4'],
                   ['NE', 'NE', 'NW', 'N', 'N'], check=False)
    assert any(a.kind == 'move' and a.piece == 1 and a.dest == P('K8') for a in legal_actions(s))


# ---- intercepts --------------------------------------------------------------------------------

def _approach():
    """O1 passes to O3; X3 (on N8, wedge NW + N) steps onto the line and Intercepts."""
    s = table()
    s = act(s, Action('pass', 'O', 0, target=2))
    ap = next(a for a in legal_actions(s) if a.side == 'X' and a.piece == 2 and a.kind in MOVEMENT and is_approach(s, a))
    t = apply(s, ap)
    return s, t


def test_a_successful_intercept_puts_the_interceptor_back_and_the_ball_stays_with_the_passer():
    s, t = _approach()
    start_sq, start_arrow = s.x[2], s.arrows[2]
    assert t.x[2] != start_sq
    node = apply(t, Action('intercept', 'X', 2))
    won = force(node, 'failure')                   # the pass fails: the defence wins
    assert won.ball == 0 and won.tos == s.tos + 1  # -5, the ball with the passer
    assert won.x[2] == start_sq and won.arrows[2] == start_arrow and won.moved('X', 2)


def test_a_failed_intercept_leaves_the_interceptor_on_the_pass_line():
    s, t = _approach()
    node = apply(t, Action('intercept', 'X', 2))
    lost = force(node, 'success')                  # the pass completes
    assert lost.ball == 2 and lost.x[2] == t.x[2]


def test_the_old_engine_left_the_interceptor_on_the_line():
    s = game_state('Five Out', 'High-Low', TABLE_O, TABLE_X, ARROWS, rules=RC.with_rules(intercept_return=False), check=False)
    s = act(s, Action('pass', 'O', 0, target=2))
    ap = next(a for a in legal_actions(s) if a.side == 'X' and a.piece == 2 and a.kind in MOVEMENT and is_approach(s, a))
    t = apply(s, ap)
    won = force(apply(t, Action('intercept', 'X', 2)), 'failure')
    assert won.x[2] == t.x[2]


# ---- the pick and roll, single-action turns -------------------------------------------------------

def test_the_d1_chain_set_answer_use_and_end_answer_roll():
    """Bucket Brigade's O1 (Dribble 19) with X1 on him; O4 (Layup ▲, Screen 18) two squares off. The plan:
    O4 Moves next to X1 and Screens; the defence answers; O1 uses the screen with one movement and ends his
    turn (the screen stays up); the defence answers; O4 is released to roll."""
    from playmaker_engine import guarding
    from playmaker_engine.planner import goals
    from playmaker_engine.solver import apply_play
    s = game_state('Bucket Brigade', 'Lockdown', ['I10', 'C9', 'P9', 'K11', 'Q3'], ['I9', 'D8', 'O8', 'L11', 'N4'],
                   ['N', 'NE', 'NW', 'W', 'N'], check=False)
    m = guarding.initial(s)
    mem = {}
    done = []
    for _ in range(6):
        g = next((x for x in goals(s, 'allstar', mem, matchups=m) if x['entry']['id'] == 'D1' and x['bind']['sc'] == 3), None)
        assert g is not None, done
        step = g['todo'][0]
        plays = [p for p in step['plays']() if apply_play(s, p) is not None]
        assert plays, (step['words'], done)
        done.append(step['id'])
        node = s
        for a in plays[0].actions:
            node = act(node, a)
        if step['id'] == 'use':
            assert node.side == 'X' and node.is_screening(3)        # one movement, the turn over, the screen up
            mem = {'D1': {'used0': True}}
        if step['finish']:
            assert plays[0].actions[0].piece == 3 and not node.is_screening(3)   # released: the roll
            break
        s = pass_turn(node) if node.side == 'X' else node
    assert done == ['screen', 'use', 'release'], done
