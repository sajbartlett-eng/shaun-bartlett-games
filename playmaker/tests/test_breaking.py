"""Step 3i: an offence that breaks the arrows. Defender capacity (C1), the goal-directed planner (C2a), the
off-ball movement templates (C2), the overloaded defender (C3), the defence's follow-or-stay choice (C5),
the off-ball threat in the defence's evaluation (Part B fix 1), and the late_closeout rule test."""
import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, MOVEMENT
from playmaker_engine.cards import TEAMS
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import contest_options
from playmaker_engine.state import Context, GameState

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']


# These positions were built for single arrows and the intercept rule of step 3i. Under the wedge (the default since the follow-up
# rulings) every defender covers a second line and the positions mean something else, so they keep the single
# arrow; the screen, drive and intercept rulings apply as everywhere. The wedge is tested in test_rulings_3i.py.
import os as _os
RULES = (RC.Rules() if _os.environ.get('PM_LIVE_RULES')                 # PM_LIVE_RULES=1: under the live rules
         else RC.with_rules(arrow_mode='single', intercept_rule='approach', turnover_cost='legacy',
                            **RC.PRE_RULEBOOK))                                           # the lanes as they were


def board(off, dfn, o, x, arrows, ball=0, **kw):
    return game_state(off, dfn, o, x, arrows, ball=ball, rules=RULES, check=False).with_(**kw)


def lineup(off_cards, dfn_cards, o, x, arrows, ball=0, **kw):
    ctx = Context(off_cards, dfn_cards, RULES, title='step 3i test', kind='GAME', off_team='test', def_team='test')
    return GameState(ctx=ctx, o=tuple(P(q) for q in o), x=tuple(P(q) for q in x),
                     arrows=tuple(B.DIR_NAMES.index(a) for a in arrows), ball=ball, **kw)


def passive_defence(o, s, steps=80):
    """Play the offence computer against a defence that never moves, every roll the offence's way."""
    for _ in range(steps):
        if s.stage == 'over':
            break
        if s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play'):
            a = o.choose(s)
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
                next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul', 'holds') if l in labels), labels[0]))
        s = node
    return s


# ---- C1: capacity ------------------------------------------------------------------------------------

# ---- Part B fix 1: the off-ball threat in the defence's evaluation -------------------------------------

TT = list(TEAMS['Twin Towers'])
WEAK = [TT[0], TT[4], TT[2], TT[3], TT[4]]                       # a poor three-point shooter in O2's slot


# ---- C2a: the goal planner on a hand-built post position ----------------------------------------------
# O5 (High-Low's centre, ▲ post) on the right block against X5 (▼ post). X5 fronts on the line from O1, so
# the strong-side entry is contested. The ball has to swing to the left wing, and both receivers have to
# move first to open their lanes.

BB = TEAMS['Bucket Brigade']
POST_OFF = [TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Iron Wall'][3], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
POST_DFN = [BB[0], BB[1], BB[4], BB[3], BB[2]]
POST_O = ['O8', 'H8', 'C5', 'B3', 'K3']
POST_X = ['M8', 'G6', 'E7', 'A2', 'L4']
POST_ARROWS = ['E', 'E', 'E', 'NE', 'NE']


def post_position(**kw):
    return lineup(POST_OFF, POST_DFN, POST_O, POST_X, POST_ARROWS, **kw)


def test_the_review_shows_both_sides_thinking():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]),
                                            X=dict(level='allstar', name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', possession=1, event='goal_finish',
                 text='Goal: O5 in the post on X5. O2 moved to open the lane, swung the ball to O2, O5 sealed X5, entry to O5.'),
            dict(type='computer', side='X', possession=1, event='objectives', text="Objectives: keep the ball out of O5's post")]
    text = ' '.join(computer_facts(recs))
    assert 'Goal: O5 in the post on X5.' in text and "keep the ball out of O5's post" in text


# ---- C2: off-ball movement --------------------------------------------------------------------------

def _wing(o2, x2, a2, **kw):
    return board('Five Out', 'High-Low', ['I11', o2, 'O9', 'A3', 'Q3'], ['I10', x2, 'N8', 'G4', 'N4'], ['N', a2, 'NW', 'N', 'N'], **kw)


# ---- C3: the overloaded defender ----------------------------------------------------------------------
# From a computer playout (Ball Movement v High-Low): X5 is the only help on O4's drive and the only answer
# to the lane to O2, a ▲ three-point shooter after he shifted away.

def _dilemma():
    return board('Ball Movement', 'High-Low', ['R10', 'A6', 'L11', 'K4', 'F5'], ['Q10', 'C8', 'L10', 'L7', 'G4'],
                 ['E', 'W', 'NE', 'NW', 'NE'], ball=3, clock=8)


def _rotation():
    """From a playout (Bucket Brigade v Lockdown): X5 is the only closeout on O1 and the only answer to the
    lane to O5. X1, X4 and X5 have used their Moves; X2 and X3 have theirs."""
    s = board('Bucket Brigade', 'Lockdown', ['I6', 'D7', 'O9', 'D2', 'Q2'], ['H7', 'D8', 'N8', 'I5', 'J6'],
              ['W', 'SE', 'NW', 'NW', 'W'], clock=10)
    return s.with_(tok_o=1, tok_x=1, moved_o=24, moved_x=25, cnt=(0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1), lock_o=1, phase=2, qs_x=1)


# ---- C5: follow or stay ---------------------------------------------------------------------------------

# ---- the late_closeout rule test -------------------------------------------------------------------

LATE = RC.with_rules(late_closeout=True)


def _contest(shot, o1, x1, a1, moved, rules=LATE):
    s = game_state('Five Out', 'High-Low', [o1, 'C9', 'O9', 'A3', 'Q3'], [x1, 'D8', 'N8', 'G4', 'N4'],
                   [a1, 'NE', 'NW', 'N', 'N'], rules=rules, check=False)
    s = s.with_(react_moved=1 if moved else 0)
    return next(o for o in contest_options(s, 0, shot) if o.defender == 0)


def test_late_closeout_off_by_default():
    assert RC.Rules().late_closeout is False
    set_ = _contest('three', 'J10', 'I10', 'E', False, rules=None)
    late = _contest('three', 'J10', 'I10', 'E', True, rules=None)
    assert set_ == late                                     # the default ignores the reaction movement


def test_a_late_contester_on_a_three_takes_the_minus_three_and_no_foul_roll():
    set_ = _contest('three', 'J10', 'I10', 'E', False)
    late = _contest('three', 'J10', 'I10', 'E', True)
    assert late.clean and late.contest == set_.contest - RC.FAR_CONTEST_PENALTY


def test_a_late_contester_at_the_rim_contests_with_a_foul_roll():
    late = _contest('layup', 'I3', 'H3', 'E', True)
    set_ = _contest('layup', 'I3', 'H3', 'E', False)
    assert set_.clean and not late.clean and late.p_foul > 0


def test_a_reaction_move_to_another_square_marks_the_contester_late():
    from conftest import P as _P
    from playmaker_engine.scenarios import scenario_state
    s = scenario_state(6, rules=LATE)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)))
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot'))
    assert s.stage == 'reaction'
    step = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest != s.x[0])
    t = apply(s, step)
    assert t.react_moved & 1
    turn = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == s.x[0])
    assert not apply(s, turn).react_moved & 1                # turning in place: set, not late


# ---- E1: a ball screen to force a switch (step 3i follow-up) ---------------------------------------------
# O1 (Ball Movement's point guard: Dribble 19) is guarded by X1 (Lockdown's guard: ▼ post contest); O5 (High-Low's
# centre: ▲ post) is guarded by X5 (Twin Towers' centre: Agility 4). If O5's screen makes them switch, O5 posts
# up the small X1 and O1 attacks the slow X5.

E1_OFF = [TEAMS['Ball Movement'][0], TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
E1_DFN = [TEAMS['Lockdown'][0], TEAMS['Lockdown'][1], TEAMS['Lockdown'][2], TEAMS['Lockdown'][3], TEAMS['Twin Towers'][4]]
E1_O = ['J7', 'C8', 'P8', 'B3', 'L5']
E1_X = ['J8', 'D8', 'O8', 'C3', 'L4']
E1_ARROWS = ['S', 'NE', 'NW', 'NE', 'N']


def e1_position(dfn=None):
    return lineup(E1_OFF, dfn or E1_DFN, E1_O, E1_X, E1_ARROWS)


def _offence_turn(s):
    """Pass the defence's turns (it stands still) until the offence is to act."""
    for _ in range(12):
        if s.stage == 'over' or (s.side == 'O' and s.stage == 'play'):
            return s
        acts = legal_actions(s)
        a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
            next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            labels = [lab for _, lab, _ in node.outcomes]
            node = force(node, next((l for l in ('success', 'kept', 'no foul') if l in labels), labels[0]))
        s = node
    return s


# ---- matchups (OQ-67a) -------------------------------------------------------------------------------

