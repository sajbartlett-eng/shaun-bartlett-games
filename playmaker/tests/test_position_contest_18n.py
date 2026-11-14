"""Step 18n (Shaun, 14 Nov 2026), the app only. D-189: contest ratings restored. D-191: jump shots are contested by
position only; inside shots keep the hand up and the block, and from in front with the arrow on him the full contest is
automatic and safe. D-192: the new jump-shot contest ratings. D-193: a contesting defender always takes at least 1 off."""
import os
import re

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.cards import CARDS
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import auto_contest, contest_options, score

ON = RC.with_rules(digital=True)
OFF = RC.with_rules(digital=True, position_contest='off')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def board(o1, x1, arrow, rules=ON, x4='N5', x4_arrow='N', **kw):
    s = game_state('Five Out', 'High-Low', [o1, 'C9', 'O9', 'A3', 'Q3'], [x1, 'D8', 'N8', x4, 'N4'],
                   [arrow, 'NE', 'NW', x4_arrow, 'N'], rules=rules, check=False)
    return s.with_(**kw) if kw else s


def declared(s, shot):
    return apply(s, next(a for a in legal_actions(s) if a.kind == 'shot' and a.shot == shot))


def no_action(s, shot):
    r = declared(s, shot)
    return apply(r, next(a for a in legal_actions(r) if a.kind == 'end_turn'))


def blocks(s, shot):
    return [a for a in legal_actions(declared(s, shot)) if a.kind == 'contest']


def test_the_rule_is_the_apps_and_needs_the_soft_contest():
    assert not RC.position_contest(RC.with_rules())                    # nothing for the table
    assert RC.position_contest(ON) and not RC.position_contest(OFF)
    assert not RC.position_contest(RC.with_rules(digital=True, soft_contest='off'))


def test_a_jump_shot_is_contested_by_position_only():
    con = board('I10', 'I9', 'N').ctx.dfn[0].con('three')
    assert con == 3
    for x1, arrow, want in (('I9', 'N', con), ('I9', 'E', con),       # in front: the arrow has no effect
                            ('J10', 'W', con), ('J10', 'N', con),     # beside him: the full rating too
                            ('I11', 'S', max(1, con - 3))):           # behind: 3 less, and never under 1 (D-193)
        s = board('I10', x1, arrow)
        assert auto_contest(s, 0, 'three') == (0, want, 'position'), (x1, arrow)
        assert not blocks(s, 'three')                                  # no Contest action on a jump shot
        end = no_action(s, 'three')
        assert not isinstance(end, ChanceNode)                         # and never a foul roll
        assert end.result.contest == want and end.result.contester == 0 and end.result.kind == 'shot'
        assert end.result.shot_value == 3 * (s.ctx.off[0].shot('three') - want)


def test_a_jump_shots_contest_names_position_in_plain_words():
    assert 'X1 was beside O1, so the three was contested (15% off)' in score(no_action(board('I10', 'J10', 'W'), 'three')).detail
    assert 'X1 was behind O1, so the three was contested (5% off)' in score(no_action(board('I10', 'I11', 'S'), 'three')).detail


def test_a_rushed_defender_contests_a_jump_shot_two_lower():
    s = board('I10', 'I9', 'N', rush_x=RC.RUSH_QS)                     # after a Quick Step
    assert auto_contest(s, 0, 'three')[1] == 3 - 2
    locked = board('I10', 'I9', 'N', lock_x=1)                         # locked is rushed too (D-185)
    assert auto_contest(locked, 0, 'three')[1] == 3 - 2


def test_only_the_best_contest_counts_on_a_jump_shot():
    s = board('I10', 'I11', 'S', x4='I9')                              # X1 behind (1 off), X4 in front (his full rating)
    j, c, kind = auto_contest(s, 0, 'three')
    assert (j, c) == (3, s.ctx.dfn[3].con('three')) and c > 1
    assert no_action(s, 'three').result.contester == 3


def test_inside_from_in_front_with_the_arrow_on_him_the_full_contest_is_automatic_and_safe():
    s = board('I4', 'I3', 'N')
    con = s.ctx.dfn[0].con('layup')
    assert auto_contest(s, 0, 'layup') == (0, con, 'full')
    assert not blocks(s, 'layup')                                      # no choice where it cost nothing
    end = no_action(s, 'layup')
    assert not isinstance(end, ChanceNode) and end.result.contest == con
    assert 'went straight up in front of O1 with his arrow on him' in score(end).detail and 'no foul' in score(end).detail


def test_inside_the_hand_up_is_automatic_and_the_block_risks_the_foul():
    for x1, arrow, behind, rolls in (('I3', 'E', False, 1),            # in front, arrow off him: one foul roll
                                     ('J4', 'W', False, 2),            # from the side: two, whatever the arrow
                                     ('I5', 'N', True, 2)):            # from behind: two, and 3 less
        s = board('I4', x1, arrow)
        con = s.ctx.dfn[0].con('layup')
        hand = max(1, con - 3 - (3 if behind else 0))
        assert auto_contest(s, 0, 'layup') == (0, hand, 'soft'), x1
        assert no_action(s, 'layup').result.contest == hand
        assert [a.piece for a in blocks(s, 'layup')] == [0]
        opt = next(o for o in contest_options(s, 0, 'layup') if o.defender == 0)
        assert opt.contest == con - (3 if behind else 0) and not opt.clean and opt.rolls == rolls and opt.p_foul > 0
        node = apply(declared(s, 'layup'), blocks(s, 'layup')[0])
        assert isinstance(node, ChanceNode)                            # going for the block rolls for the foul


def test_a_contesting_defender_always_takes_at_least_one_off():
    s = board('I4', 'I5', 'N', rush_x=RC.RUSH_QS)                      # behind and rushed: the post hand up is 4 - 3 - 3 - 2
    assert s.ctx.dfn[0].con('post') - 8 < 0
    assert auto_contest(s, 0, 'post') == (0, 1, 'soft')
    assert next(o for o in contest_options(s, 0, 'post') if o.defender == 0).contest == 1      # the block: 4 - 3 - 2, held at 1
    off = board('I4', 'I5', 'N', rules=OFF, rush_x=RC.RUSH_QS)
    assert auto_contest(off, 0, 'post')[:2] == (-1, 0)                 # the rule off: as before, worth nothing


def test_with_the_rule_off_the_soft_and_hard_contest_are_as_before():
    s = board('I10', 'I9', 'N', rules=OFF)
    assert auto_contest(s, 0, 'three') == (-1, 0, '')                  # a three's hand up: 3 less 3
    assert [a.piece for a in blocks(s, 'three')] == [0]                # and the Contest action is there
    rim = board('I4', 'I3', 'N', rules=OFF)
    assert auto_contest(rim, 0, 'layup')[1:] == (rim.ctx.dfn[0].con('layup') - 3, 'soft')


def test_every_contest_rating_matches_the_table():
    rows = {}
    for ln in open(os.path.join(ROOT, 'docs', 'reference', 'JUMP_CONTESTS_14NOV.md')):
        m = re.match(r"\| `(\w+)` \| .*? \| [ABC] \| (\d+) \| (\d+) \| (\d+) \| (\d+) \| (\d+) → \*\*(\d+)\*\* \| (\d+) → \*\*(\d+)\*\* \| (\d+) → \*\*(\d+)\*\* \|", ln)
        if m:
            g = [int(x) for x in m.groups()[1:]]
            rows[m.group(1)] = dict(layup=g[0], dunk=g[1], post=g[2], floater=g[3], mid=g[5], long=g[7], three=g[9], was=(g[4], g[6], g[8]))
    assert set(rows) == set(CARDS) and len(rows) == 81
    jump = {2: 1, 3: 2, 4: 2, 5: 3, 6: 3, 7: 4, 8: 4}                  # D-192
    for k, c in CARDS.items():
        for t in ('layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three'):
            assert c.con(t) == rows[k][t], (k, t)
        assert tuple(jump[v] for v in rows[k]['was']) == (rows[k]['mid'], rows[k]['long'], rows[k]['three']), k


def test_jump_shot_contest_colours_follow_the_new_range():
    from playmaker_engine.data import data as D
    for name in ('con_mid', 'con_long', 'con_three'):
        assert D.RANGES[name] == (2, 3)                                # average from 2, above average from 3
        assert all(c.bands[name] == ('H' if c.r[name] >= 3 else 'A' if c.r[name] >= 2 else 'L') for c in CARDS.values())
