"""Step 18k. D-181: no foul gives +5 in the app. D-182: when nothing sets a foul situation the app plays a typical
mid-quarter one, 2 team fouls each with 8 possessions left, and a foul's price is the penalty it brings nearer. The
table keeps its +5 and has no quarter. search.keep_in_hand: in the defence's list two turns are not copies when they
leave a defender different things he can still do this phase."""
from dataclasses import replace

from playmaker_engine import rules_config as RC
from playmaker_engine import search as SE
from playmaker_engine.actions import Action
from playmaker_engine.decide import foul_marginal, foul_table
from playmaker_engine.resolve import apply
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import score
from playmaker_web.game import Game

APP = RC.with_rules(digital=True)
TABLE = RC.with_rules(digital=False)
O = ['I11', 'C9', 'O9', 'A3', 'Q3']
X = ['I10', 'D8', 'N8', 'G4', 'N4']
ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def steal_foul(rules, team_fouls):
    s = game_state('Five Out', 'High-Low', O, X, ARROWS, rules=rules, check=False, team_fouls=team_fouls, quarter_left=8)
    node = apply(s.with_(side='X'), Action('steal', 'X', 0))
    return next(n for _p, label, n in node.flatten() if label == 'foul')


def test_no_steal_foul_gives_plus_five_in_the_app():
    before, penalty = steal_foul(APP, 2), steal_foul(APP, 4)
    assert before.stage == 'play' and before.bonus5 == 0 and before.fouls == 1 and before.locked('X', 0)
    assert penalty.stage == 'over' and penalty.result.kind == 'free_throws' and penalty.bonus5 == 0
    sc = score(penalty)
    assert sc.bonus == 0 and sc.total == sc.free_throws == 2 * penalty.ctx.off[0].r['free_throw']


def test_the_table_keeps_its_plus_five_on_every_steal_foul():
    first = steal_foul(TABLE, 0)
    assert first.stage == 'play' and first.bonus5 == 1
    s = game_state('Five Out', 'High-Low', O, X, ARROWS, rules=TABLE, check=False)
    second = next(n for _p, label, n in apply(s.with_(side='X', fouls=1, bonus5=1), Action('steal', 'X', 0)).flatten() if label == 'foul')
    assert second.stage == 'over' and second.bonus5 == 2 and score(second).bonus == 10


def test_a_fouls_price_in_the_app_is_the_penalty_it_brings_nearer():
    s = game_state('Five Out', 'High-Low', O, X, ARROWS, rules=APP, check=False, team_fouls=2, quarter_left=8)
    ctx = s.ctx
    C, _F = foul_table(ctx)
    ft2 = sum(RC.FT_MULT_TWO * c.r['free_throw'] for c in ctx.off) / len(ctx.off)
    # the penalty foul against an ordinary one: two free throws against play on, and no +5 on either side of it
    assert C[3][1] == 0 and foul_marginal(ctx, 4, 8) == 0     # the 5th is the penalty foul itself: paid now, not later
    from playmaker_engine.decide import CONFIG
    q, cont = CONFIG['eval']['fouls_per_possession'], CONFIG['eval']['play_on_value']
    assert abs(C[4][1] - q * (ft2 - cont)) < 1e-9
    assert foul_marginal(ctx, 2, 8) != 0                      # at 2 team fouls a foul now brings the penalty nearer


def test_with_nothing_set_the_app_plays_two_team_fouls_and_eight_possessions_left():
    g = Game(ai={'A': 'starter', 'B': 'starter'}, level='learn', seed=3, match_format='digital', per_side=4, place=True)
    assert RC.DEFAULT_FOUL_SITUATION == (2, 8)
    first = [r for r in g.read_log() if r['type'] == 'quarter']
    ctx = g.state.ctx
    assert (ctx.team_fouls >= 2 and ctx.quarter_left <= 8) or first      # the possession in play started from 2 and 8
    fresh = Game(level='learn', seed=3, match_format='digital', per_side=4)
    assert fresh.quarter['fouls'] == dict(A=2, B=2)
    assert fresh.quarter_context() == (2, 8)
    words = fresh.quarter_words()
    assert words['left'] == 8 and words['text'].startswith('Team fouls 2') and '8 possessions left' in words['text']


def test_a_situation_that_is_set_is_kept():
    g = Game(level='learn', seed=3, match_format='digital', per_side=4,
             quarter=dict(fouls=dict(A=4, B=1), poss=dict(A=15, B=15), number=1))
    assert g.quarter['fouls'] == dict(A=4, B=1) and g.quarter_words()['left'] == 3


def test_the_table_has_no_quarter():
    g = Game(level='learn', seed=3)
    assert g.quarter_context() == (0, 0)


def test_turns_that_leave_different_things_in_hand_are_not_copies(monkeypatch):
    # O4 has the ball on A3; X3 on F5 is two movements from him
    s = game_state('Five Out', 'High-Low', O, ['I10', 'D8', 'F5', 'G4', 'N4'], ['N', 'NE', 'W', 'N', 'N'], rules=APP, check=False, ball=3)
    s = s.with_(side='X')

    def every_turn(on):
        monkeypatch.setitem(SE.CONFIG['search'], 'keep_in_hand', on)
        got = SE.open_turns_x(s, 2000, lambda n: 0.0, None, None, whole=True)
        return [t for _v, t in got]

    off, on = every_turn(False), every_turn(True)
    assert len(on) > len(off)                                 # turns the quick reading can't tell apart are kept
    monkeypatch.setitem(SE.CONFIG['search'], 'keep_in_hand', False)


def test_the_switch_is_a_plain_on_or_off():
    assert SE.CONFIG['search'].get('keep_in_hand') in (True, False)
    assert SE.CONFIG['search'].get('keep_settled') is True     # D-183: on by default
