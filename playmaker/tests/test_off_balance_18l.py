"""Step 18l, D-185 (rules.off_balance, the app only): a player is rushed if his last movement this phase was a Quick
Step or a Sprint, or he is locked. Rushed is 2 off every rating he rolls, foul ratings aside. A Move resets it; a
locked player can't Move, so it lasts the phase. So a missed Steal leaves the defender easier to drive past."""
from dataclasses import replace

from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import p_success, p_foul, rolled

APP = RC.with_rules(digital=True)
OFF = replace(APP, off_balance='off')
TABLE = RC.with_rules(digital=False)
O = ['I11', 'C9', 'O9', 'A3', 'Q3']
X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def board(rules=APP, **kw):
    return game_state('Five Out', 'High-Low', O, X, ARROWS, rules=rules, check=False).with_(**kw)


def chance_of(node, label):
    return sum(p for p, lab, _n in node.outcomes if lab == label)


def test_the_rule_is_the_apps():
    assert RC.off_balance_cut(APP) == 2 and RC.off_balance_cut(OFF) == 0 and RC.off_balance_cut(TABLE) == 0


def test_a_locked_player_is_rushed_and_a_move_resets_a_quick_step():
    s = board()
    assert not s.rushed('X', 0) and s.with_(lock_x=1).rushed('X', 0) and s.with_(lock_o=1).rushed('O', 0)
    assert not board(OFF, lock_x=1).rushed('X', 0) and not board(TABLE, lock_x=1).rushed('X', 0)
    qs = s.with_(rush_x=RC.RUSH_QS << 2)                      # X2's last movement was a Quick Step
    assert qs.rushed('X', 1)
    move = next(a for a in legal_actions(qs.with_(side='X')) if a.kind == 'move' and a.piece == 1)
    assert not apply(qs.with_(side='X'), move).rushed('X', 1)  # a Move puts him back in control


def test_every_rolled_rating_is_two_lower_when_rushed_and_fouls_are_not():
    s = board(lock_x=1, rush_o=RC.RUSH_SPRINT)                 # X1 locked; O1 came off a Sprint
    for name in ('agility', 'steal', 'intercept', 'challenge'):
        assert rolled(s, 'X', 0, name) == s.ctx.dfn[0].r[name] - 2
        assert rolled(s, 'X', 1, name) == s.ctx.dfn[1].r[name]
    for name in ('dribble', 'pass', 'screen'):
        assert rolled(s, 'O', 0, name) == s.ctx.off[0].r[name] - 2
        assert rolled(s, 'O', 1, name) == s.ctx.off[1].r[name]
    off = board(OFF, lock_x=1, rush_o=RC.RUSH_SPRINT)
    assert rolled(off, 'X', 0, 'agility') == off.ctx.dfn[0].r['agility'] and rolled(off, 'O', 0, 'dribble') == off.ctx.off[0].r['dribble']


def test_a_drive_at_a_rushed_defender_is_easier_and_a_rushed_drive_is_harder():
    s = board()
    d, g = s.ctx.off[0].r['dribble'], s.ctx.dfn[0].r['agility']
    drive = Action('dribble', 'O', 0, target=0)
    assert chance_of(apply(s, drive), 'success') == p_success(d - g, APP)
    assert chance_of(apply(s.with_(lock_x=1), drive), 'success') == p_success(d - (g - 2), APP)             # he reached and missed
    assert chance_of(apply(s.with_(rush_x=RC.RUSH_SPRINT), drive), 'success') == p_success(d - (g - 2), APP)  # a Sprint closeout
    assert chance_of(apply(s.with_(rush_o=RC.RUSH_SPRINT), drive), 'success') == p_success((d - 2) - g, APP)  # a Sprint drive
    assert chance_of(apply(board(OFF, lock_x=1), drive), 'success') == p_success(d - g, OFF)


def test_a_steal_rolls_with_both_sides_off_balance_and_its_foul_roll_is_untouched():
    s = board(side='X')
    d, k = s.ctx.off[0].r['dribble'], s.ctx.dfn[0].r['steal']

    def kept(node):                                            # the chance the ball is kept, whatever the foul roll gave
        tot = 0
        for p, lab, n in node.outcomes:
            if hasattr(n, 'outcomes'):
                tot += p * sum(q for q, l2, _ in n.outcomes if l2 == 'kept') / sum(q for q, _l, _ in n.outcomes)
        return tot

    def fouled(node):
        return chance_of(node, 'foul')

    steal = Action('steal', 'X', 0)
    plain, rushed_d, rushed_o = apply(s, steal), apply(s.with_(rush_x=RC.RUSH_QS), steal), apply(s.with_(rush_o=RC.RUSH_QS), steal)
    assert fouled(plain) == fouled(rushed_d) == fouled(rushed_o)            # foul ratings are not rolled lower
    inner = lambda node: next(n for _p, lab, n in node.outcomes if hasattr(n, 'outcomes'))
    assert chance_of(inner(plain), 'kept') == p_success(d - k, APP)
    assert chance_of(inner(rushed_d), 'kept') == p_success(d - (k - 2), APP)
    assert chance_of(inner(rushed_o), 'kept') == p_success((d - 2) - k, APP)


def test_a_missed_steal_leaves_the_defender_easier_to_drive_past():
    s = board(side='X')
    node = apply(s, Action('steal', 'X', 0))
    missed = [n for n in _leaves(node) if n.stage == 'play' and n.locked('X', 0) and n.fouls == 0]
    assert missed                                              # he reached, no foul, the ball was kept: he is locked
    after = missed[0].with_(side='O', turn_n=0)
    assert after.rushed('X', 0)
    d, g = after.ctx.off[0].r['dribble'], after.ctx.dfn[0].r['agility']
    drive = next(a for a in legal_actions(after) if a.kind == 'dribble' and a.target == 0)
    assert chance_of(apply(after, drive), 'success') == p_success(d - (g - 2), APP)


def _leaves(node):
    if hasattr(node, 'outcomes'):
        for _p, _lab, n in node.outcomes:
            yield from _leaves(n)
    else:
        yield node


def test_the_marker_shows_on_a_locked_player_and_the_rule_is_one_sentence():
    from playmaker_web.view import _rush_mark
    s = board(lock_x=1, rush_o=RC.RUSH_SPRINT)
    assert _rush_mark(s, 'X', 0) == 3 and _rush_mark(s, 'O', 0) == 2 and _rush_mark(s, 'X', 1) == 0
    assert _rush_mark(board(OFF, lock_x=1), 'X', 0) == 0
    import os
    app = open(os.path.join(os.path.dirname(__file__), '..', 'playmaker_web', 'static', 'app.js')).read()
    assert 'Rushed: after a Quick Step or Sprint, or while locked, every roll you make is ${n} worse (not fouls) until you Move.' in app
    rules = open(os.path.join(os.path.dirname(__file__), '..', 'RULES_CURRENT.md')).read()
    assert 'ushed: after a Quick Step or Sprint, or while locked, every roll you make is 2 worse (not fouls) until you Move.' in rules
