"""Step 18j (Shaun, 13 Nov 2026), the app only. D-177: next to the shooter is a soft contest (the contest rating less
3, no action, never a foul); a Contest action is a hard contest (the full rating; from the side or behind it rolls
twice for a foul, as a Steal does). D-179: a steal foul outside the penalty gives no +5. D-180: a scenario card that
sets a foul situation plays under the app's rules."""
from conftest import P
from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import game_state, scenario_state
from playmaker_engine.scoring import contest_options, soft_contest, score

ON = RC.with_rules(digital=True, soft_contest='on', fiba_steal_foul='on')
OFF = RC.with_rules(digital=True, soft_contest='off', fiba_steal_foul='off')
O = ['I10', 'C9', 'O9', 'A3', 'Q3']                                    # O1 shoots the three from I10


def board(x1, arrow, rules=ON, x4='G4', o1='I10', **kw):
    s = game_state('Five Out', 'High-Low', [o1] + O[1:], [x1, 'D8', 'N8', x4, 'N4'], [arrow, 'NE', 'NW', 'N', 'N'], rules=rules, check=False)
    return s.with_(**kw) if kw else s


def rim(x1, arrow, rules=ON, **kw):
    """Step 18l, re-recorded for the D-184 cards: a three's contest rating is now 2 or 3, so next to a jump shooter a
    soft contest (the rating less 3) is nothing. The soft-contest tests moved to a layup: O1 on I4, the rim at I2."""
    return board(x1, arrow, rules=rules, x4='N5', o1='I4', **kw)


def shoot(s, shot='three'):
    return apply(s, next(a for a in legal_actions(s) if a.kind == 'shot' and a.shot == shot))


def no_contest(s, shot='three'):
    """The shot with the reaction ended at once: no Contest action."""
    r = shoot(s, shot)
    return apply(r, next(a for a in legal_actions(r) if a.kind in ('end_turn', 'forfeit')))


def hard(s, j=0):
    r = shoot(s)
    return apply(r, next(a for a in legal_actions(r) if a.kind == 'contest' and a.piece == j))


def test_the_two_rules_are_the_apps():
    for name in ('soft_contest', 'fiba_steal_foul'):
        assert not RC.app_rule(RC.with_rules(), name)                  # nothing for the table
        assert RC.app_rule(RC.with_rules(digital=True), name)          # on by default in the app's format
        assert RC.app_rule(ON, name) and not RC.app_rule(OFF, name)


def test_next_to_the_shooter_is_a_soft_contest_with_no_action_and_no_foul():
    s = rim('I3', 'E')                                                 # X1 in front of O1, his arrow off him
    con = s.ctx.dfn[0].con('layup')
    assert con - 3 > 0                                                 # D-184 cards: at the rim a hand up still counts
    end = no_contest(s, 'layup')
    assert not isinstance(end, ChanceNode)                             # it never fouls: nothing is rolled
    r = end.result
    assert r.kind == 'shot' and r.soft and r.contester == 0 and r.contest == con - 3
    assert r.shot_value == 2 * (s.ctx.off[0].shot('layup') - (con - 3))
    assert "soft contest, a hand up from in front" in score(end).detail
    off = no_contest(rim('I3', 'E', rules=OFF), 'layup')               # the rule off: no Contest action, no contest
    assert off.result.contest == 0 and not off.result.soft
    three = no_contest(board('I9', 'E'))                               # D-184 cards: next to a three, nothing
    assert three.result.contest == 0 and not three.result.soft


def test_from_behind_either_contest_is_three_lower_again():
    front, behind = rim('I3', 'N'), rim('I5', 'S')                     # re-recorded at the rim: D-184 cards
    con = front.ctx.dfn[0].con('layup')
    assert con - 6 > 0
    assert soft_contest(front, 0, 'layup') == (0, con - 3)
    assert soft_contest(behind, 0, 'layup') == (0, con - 6)
    hard_front = next(c for c in contest_options(front, 0, 'layup') if c.defender == 0)
    hard_behind = next(c for c in contest_options(behind, 0, 'layup') if c.defender == 0)
    assert hard_front.contest == con and hard_behind.contest == con - 3


def test_a_hard_contest_rolls_for_a_foul_by_where_it_comes_from():
    opt = lambda x1, arrow: next(c for c in contest_options(board(x1, arrow), 0, 'three') if c.defender == 0)
    assert opt('I9', 'N').clean                                        # in front, arrow on him: no foul roll
    off = opt('I9', 'E')
    assert not off.clean and off.rolls == 1                            # in front, arrow off him: one
    side = opt('J10', 'W')
    assert B.dist_rim(P('J10')) == B.dist_rim(P('I10'))                # level with him: the side
    assert not side.clean and side.rolls == 2                          # from the side, arrow on him: two, as a Steal
    assert not opt('I11', 'S').clean and opt('I11', 'S').rolls == 2    # from behind: two
    old = next(c for c in contest_options(board('J10', 'W', rules=OFF), 0, 'three') if c.defender == 0)
    assert old.clean                                                   # before: the arrow on him was enough


def test_a_hard_contest_is_the_full_rating():
    s = board('I9', 'N')
    end = hard(s)
    assert not isinstance(end, ChanceNode) and not end.result.soft
    assert end.result.contest == s.ctx.dfn[0].con('three')
    assert "hard contest from in front" in score(end).detail


def test_only_the_defences_best_contest_counts():
    """X4 (a poor contester here) takes the hard contest from behind; X1 stands in front with a hand up. If X1's soft
    contest is the larger, it is the one that counts."""
    s = board('I9', 'E', x4='I11')
    s = s.with_(arrows=s.arrows[:3] + (4,) + s.arrows[4:])             # X4 on I11 facing S: on the shooter, from behind
    soft_j, soft_c = soft_contest(s, 0, 'three')
    node = hard(s, 3)
    made = [n for _p, label, n in node.flatten() if n.result.kind == 'shot'] if isinstance(node, ChanceNode) else [node]
    h = next(c for c in contest_options(s, 0, 'three') if c.defender == 3)
    for n in made:
        assert n.result.contest == max(h.contest, soft_c)
        assert n.result.soft == (soft_c > h.contest)


def test_a_soft_contest_is_never_below_nothing():
    s = board('I11', 'S')                                              # behind him: the rating less 6
    c = s.ctx.dfn[0].con('three') - 6
    j, got = soft_contest(s, 0, 'three')
    assert got == max(0, c) and (j == 0) == (c > 0)


def test_a_rushed_defenders_soft_contest_is_two_lower():
    s = rim('I3', 'N')                                                 # re-recorded at the rim: D-184 cards
    rushed = s.with_(rush_x=RC.RUSH_QS)                                # X1's last movement was a Quick Step
    assert soft_contest(s, 0, 'layup')[1] > RC.control_size(ON)
    assert soft_contest(rushed, 0, 'layup')[1] == soft_contest(s, 0, 'layup')[1] - RC.control_size(ON)


def test_the_forced_shots_contest_is_unchanged():
    s = board('J10', 'W')
    forced = next(c for c in contest_options(s, 0, 'three', True) if c.defender == 0)
    assert forced.clean                                                # today's rule: the arrow on him, no foul roll


# ---- the steal foul (D-179) -----------------------------------------------------------------------------------------

def steal_foul(rules, fouls=0, left=10):
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                   ['N', 'NE', 'NW', 'N', 'N'], rules=rules, check=False, team_fouls=fouls, quarter_left=left).with_(side='X')
    node = apply(s, next(a for a in legal_actions(s) if a.kind == 'steal'))
    return next(n for _p, label, n in node.flatten() if label == 'foul')


def test_a_steal_foul_outside_the_penalty_gives_no_plus_five():
    n = steal_foul(ON)
    assert n.stage == 'play' and n.bonus5 == 0 and n.fouls == 1        # a team foul, play on, no +5
    assert n.locked('X', 0)                                            # and the defender is locked
    old = steal_foul(OFF)
    assert old.bonus5 == 1 and not old.locked('X', 0)                  # before: +5, no lock


def test_in_the_penalty_a_steal_foul_is_two_free_throws_and_nothing_more():
    n = steal_foul(ON, fouls=4)
    assert n.stage == 'over' and n.result.kind == 'free_throws' and n.bonus5 == 0          # D-181: no +5 on any foul in the app
    assert n.result.free_throws == 2 * n.ctx.off[0].r['free_throw']
    assert score(n).total == score(steal_foul(OFF, fouls=4)).total - 5                    # before: the +5 as well


def test_the_table_keeps_its_plus_five():
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                   ['N', 'NE', 'NW', 'N', 'N'], check=False).with_(side='X')
    node = apply(s, next(a for a in legal_actions(s) if a.kind == 'steal'))
    assert next(n for _p, label, n in node.flatten() if label == 'foul').bonus5 == 1


def test_a_scenario_card_that_sets_a_foul_situation_plays_under_the_apps_rules():
    assert scenario_state(12).ctx.rules.digital and scenario_state(13).ctx.rules.digital       # D-180
    assert not scenario_state(6).ctx.rules.digital                                             # a card that sets none
