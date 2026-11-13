"""Step 18i (Shaun, 13 Nov 2026): FIBA rules for single possessions, the app only. Time is counted in phase ends
(D-171). Three seconds (D-172): an attacker in the key at two phase ends in a row. Closely guarded (D-173): a ball
handler holding the ball with a defender on him at three phase ends in a row; after dribbling, two idle phases and he
has picked the ball up. The fouled shot (D-174): the contested shot plus the free throws that follow, on average."""
from conftest import P
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, closely_guarded
from playmaker_engine.resolve import apply, end_phase, ChanceNode
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options, foul_on_shot_points, score

ON = RC.with_rules(digital=True, three_seconds='on', closely_guarded='on', fiba_fouled_shot='on')
OFF = RC.with_rules(digital=True, three_seconds='off', closely_guarded='off', fiba_fouled_shot='off')
O = ['I11', 'C9', 'O9', 'A3', 'Q3']
X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']
AWAY = ['E', 'NE', 'NW', 'N', 'N']                                    # X1 next to O1 with his arrow off him: not closely guarded


def board(o=O, x=X, arrows=ARROWS, rules=ON, ball=0, **kw):
    s = game_state('Five Out', 'High-Low', o, x, arrows, ball=ball, rules=rules, check=False)
    return s.with_(**kw) if kw else s


def win(node):
    """The branch of a Dribble where it is won."""
    return next(n for _p, label, n in node.flatten() if n.beaten) if isinstance(node, ChanceNode) else node


# ---- the settings ---------------------------------------------------------------------------------------------------

def test_the_three_rules_are_the_apps_and_never_the_tables():
    table, app = RC.with_rules(), RC.with_rules(digital=True)
    for name in ('three_seconds', 'closely_guarded', 'fiba_fouled_shot'):
        assert not RC.app_rule(table, name)                            # nothing for the table
        assert RC.app_rule(app, name)                                  # on by default in the app's format
        assert RC.app_rule(ON, name) and not RC.app_rule(OFF, name)
    # 'app' means on in the app's format only
    assert RC.app_rule(RC.with_rules(digital=True, three_seconds='app'), 'three_seconds')
    assert not RC.app_rule(RC.with_rules(digital=False, three_seconds='app'), 'three_seconds')


# ---- three seconds (D-172) ------------------------------------------------------------------------------------------

def test_the_key_is_the_lane_as_drawn():
    assert B.in_key(P('G1')) and B.in_key(P('K6')) and B.in_key(P('I3'))
    assert not B.in_key(P('F3')) and not B.in_key(P('L3')) and not B.in_key(P('I7'))


def test_an_attacker_in_the_key_at_two_phase_ends_in_a_row_is_a_violation():
    s = board(o=['I11', 'C9', 'O9', 'H3', 'Q3'], arrows=AWAY)          # O4 stands in the key
    one = end_phase(s)
    assert one.stage == 'play' and one.key_o == 1 << 3                 # the first phase end: counted, play goes on
    two = end_phase(one)
    assert two.stage == 'over' and two.result.kind == 'turnover_end'
    assert two.result.violation == 'three_seconds' and two.result.violator == 3
    assert score(two).total == 0                                       # a turnover: the possession scores 0
    assert 'three seconds' in score(two).detail


def test_leaving_the_key_before_the_phase_ends_clears_his_count():
    s = end_phase(board(o=['I11', 'C9', 'O9', 'H3', 'Q3'], arrows=AWAY))
    out = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 3 and not B.in_key(a.dest)))
    after = end_phase(out)
    assert after.stage == 'play' and after.key_o == 0
    back = after.with_(o=after.o[:3] + (P('H3'),) + after.o[4:])
    assert end_phase(back).stage == 'play'                             # back in: his count starts again at one


def test_defenders_have_no_three_second_rule_and_the_rule_can_be_off():
    s = board(o=O, x=['I10', 'D8', 'N8', 'H3', 'I3'], arrows=AWAY)     # two defenders camp in the key
    assert end_phase(end_phase(end_phase(s))).stage == 'play'
    off = board(o=['I11', 'C9', 'O9', 'H3', 'Q3'], arrows=AWAY, rules=OFF)
    assert end_phase(end_phase(off)).stage == 'play' and end_phase(off).key_o == 0


# ---- closely guarded (D-173) ----------------------------------------------------------------------------------------

def test_closely_guarded_is_a_defender_next_to_him_with_an_arrow_on_him():
    assert closely_guarded(board())                                    # X1 under O1, facing N: on him
    assert not closely_guarded(board(arrows=AWAY))                     # next to him, arrow elsewhere
    assert not closely_guarded(board(x=['I8', 'D8', 'N8', 'G4', 'N4']))        # arrow his way, two squares off


def test_holding_the_ball_closely_guarded_at_three_phase_ends_in_a_row_is_a_violation():
    s = board()
    one = end_phase(s)
    two = end_phase(one)
    assert (one.guard()[1], two.guard()[1]) == (1, 2) and two.stage == 'play'
    three = end_phase(two)
    assert three.stage == 'over' and three.result.violation == 'closely_guarded' and three.result.violator == 0
    assert score(three).total == 0


def test_the_count_starts_again_when_nobody_closely_guards_him_at_a_phase_end():
    two = end_phase(end_phase(board()))
    turned = two.with_(arrows=(2,) + two.arrows[1:])                   # X1 turns away: not closely guarded
    fresh = end_phase(turned)
    assert fresh.guard()[1] == 0
    again = end_phase(end_phase(fresh.with_(arrows=two.arrows)))       # closely guarded again: the count is at two
    assert again.stage == 'play' and again.guard()[1] == 2


def test_moving_with_the_ball_or_a_dribble_starts_his_dribble_and_a_dribble_is_never_counted():
    two = end_phase(end_phase(board()))
    mv = next(a for a in legal_actions(two) if a.kind == 'move' and a.piece == 0)
    moved = apply(two, mv)
    assert moved.guard() == (1, 0, 0, 1)                               # dribbling, the count gone, active this phase
    drib = win(apply(two, next(a for a in legal_actions(two) if a.kind == 'dribble')))
    assert drib.guard()[0] == 1
    live = two.with_(grd=1)                                            # dribbling, still next to X1 with his arrow on him
    s = live
    for _ in range(1):
        s = end_phase(s)
    assert s.stage == 'play' and s.guard()[1] == 0                     # closely guarded, but a live dribble: no count


def test_two_idle_phases_after_dribbling_and_he_has_picked_the_ball_up():
    s = board(grd=1 | 1 << 6)                                          # dribbling; he acted this phase
    a = end_phase(s)                                                   # the phase he acted in doesn't count
    b = end_phase(a)                                                   # one full idle phase
    assert not b.picked_up()
    c = end_phase(b)                                                   # two: he has picked the ball up
    assert c.picked_up() and c.stage == 'play'
    kinds = {x.kind for x in legal_actions(c) if x.piece == 0}
    assert not kinds & {'move', 'qs', 'sprint', 'dribble'}             # he may only pass or shoot
    assert 'pass' in kinds
    d = end_phase(end_phase(c))                                        # and the closely guarded count runs
    assert d.guard()[1] == 2
    assert end_phase(d).result.violation == 'closely_guarded'


def test_a_teammates_action_or_a_hesitate_does_not_keep_him_active():
    s = board(grd=1)
    other = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 1))
    assert other.guard()[3] == 0
    hes = apply(s, next(a for a in legal_actions(s) if a.kind == 'hesitate'))
    assert hes.guard()[3] == 0


def test_a_catch_starts_the_new_holders_count():
    two = end_phase(end_phase(board()))
    from playmaker_engine.resolve import complete_pass
    caught = complete_pass(two.with_(pending=(0, 1)))
    assert caught.ball == 1 and caught.grd == 0


def test_with_the_rule_off_nothing_is_counted():
    s = board(rules=OFF)
    for _ in range(4):
        s = end_phase(s)
    assert s.stage == 'play' and s.grd == 0


# ---- the fouled shot (D-174) ----------------------------------------------------------------------------------------

def test_a_fouled_shot_scores_the_contested_shot_plus_the_free_throws_that_follow():
    s = board()
    card = s.ctx.off[0]
    three, ft = card.shot('three'), card.r['free_throw']
    # a three left at rating 6 by the Contest: 3 x 6 for the shot; it goes in 6 times in 20 (1 free throw), misses 14 (3)
    want = (20 * 3 * 6 + ft * (6 + 14 * 3) + 10) // 20
    assert foul_on_shot_points(card, 'three', 3, ON, three, 3 * 6, 6) == (want, False)
    # with no Contest at all (a foul on a Steal at the shooter): the open shot plus the free throws
    open_ = (20 * 3 * three + ft * (three + (20 - three) * 3) + 10) // 20
    assert foul_on_shot_points(card, 'three', 3, ON, three)[0] == open_
    # today's rule: the free throws, or the open shot if that is higher
    assert foul_on_shot_points(card, 'three', 3, OFF, three)[0] == max(3 * ft, 3 * three)


def test_each_contest_carries_its_own_fouled_value():
    s = board(o=['I10', 'C9', 'O9', 'A3', 'Q3'], x=['I9', 'D8', 'N8', 'G4', 'N4'], arrows=AWAY, ball=2)
    s = s.with_(o=s.o[:2] + (P('O9'),) + s.o[3:], x=(P('O8'),) + s.x[1:])       # X1 under O3 on the arc, arrow off him
    opt = next(c for c in contest_options(s, 2, 'three') if c.defender == 0)
    card = s.ctx.off[2]
    left = card.shot('three') - opt.contest
    assert not opt.clean and opt.p_foul > 0
    assert opt.ft == foul_on_shot_points(card, 'three', 3, ON, card.shot('three'), opt.value, left)[0]
    assert opt.ft > opt.value                                          # the free throws come on top of the shot


# ---- the foul situation, set by the scenario (D-175) ---------------------------------------------------------------

def situation(fouls, left):
    return game_state('Five Out', 'High-Low', O, X, ARROWS, rules=ON, check=False, team_fouls=fouls, quarter_left=left)


def test_a_fouls_later_cost_comes_from_bringing_the_penalty_nearer():
    from playmaker_engine.decide import foul_marginal
    early, near, last = situation(0, 10).ctx, situation(4, 10).ctx, situation(4, 1).ctx
    assert foul_marginal(early, 0, 10) != 0                                 # a foul now brings the penalty a foul nearer
    assert foul_marginal(near, 4, 10) == 0                                  # the 5th is the penalty foul itself: paid now, not later
    assert foul_marginal(last, 4, 1) == 0                                   # no possessions after this one: no later cost


def test_from_the_fifth_team_foul_a_steal_foul_gives_two_free_throws_and_ends_the_possession():
    """FIBA Article 41: the penalty. X1 next to O1 with his arrow on him: a Steal."""
    def foul_branch(fouls):
        s = situation(fouls, 10).with_(side='X')
        node = apply(s, next(a for a in legal_actions(s) if a.kind == 'steal'))
        return next(n for _p, label, n in node.flatten() if label == 'foul')
    play_on, penalty = foul_branch(0), foul_branch(4)
    assert play_on.stage == 'play' and play_on.bonus5 == 1                  # +5 and play on
    assert penalty.stage == 'over' and penalty.result.kind == 'free_throws'
    assert penalty.result.free_throws == 2 * penalty.ctx.off[0].r['free_throw']


def test_two_scenario_cards_set_a_foul_situation_in_plain_words():
    from playmaker_engine.scenarios import scenario_state, situation_words, SCENARIOS
    a, b = scenario_state(12), scenario_state(13)
    assert (a.ctx.team_fouls, a.ctx.quarter_left) == (4, 3) and (b.ctx.team_fouls, b.ctx.quarter_left) == (4, 1)
    assert situation_words(SCENARIOS[12]) == 'The defence has 4 team fouls; the offence has 1. 3 possessions left in the quarter.'
    assert scenario_state(6).ctx.team_fouls == 0 and situation_words(SCENARIOS[6]) is None     # a card that sets none


def test_the_app_shows_what_the_dice_made_of_a_fouled_shot_and_scores_its_expected_value():
    import random
    from playmaker_web.game import fouled_shot_dice
    from playmaker_engine.state import Result
    s = board(o=['I10', 'C9', 'O9', 'A3', 'Q3'], x=['I9', 'D8', 'N8', 'G4', 'N4'])
    over = s.with_(stage='over', result=Result('free_throws', 2, 'three', 3, 13, 4, 0, 27, 55, False))
    out = fouled_shot_dice(over, random.Random(3))
    assert len(out) == 1 and out[0]['text'].startswith("On the dice: O3's three")
    assert 'free throw' in out[0]['text'] and 'on average' in out[0]['text']
    assert fouled_shot_dice(over.with_(ctx=board(rules=OFF).ctx), random.Random(3)) == []       # the rule off: nothing
