"""Step 3i behaviours under the live rules (single arrow, hold-until-move screens, zone drives, move-then-intercept and
the minus5_lose_phase turnover cost). test_breaking.py keeps the step 3i positions as the record, and 31 of its 39 tests
pass unchanged under the live rules too (PM_LIVE_RULES=1). These are the other 8, rebuilt where the live rules changed
what a position shows: the post-entry chain (X1 now intercepts through his square on the swing lanes, so he stands
off them, facing the baseline), the rotation (X2 faces up the wing), and the goal score's clock-aware pick-off.

The rulebook revision of Nov 2026 narrowed 'through you' to the line through the square's centre (OQ-13) and kept a
lane jump's facing (OQ-76); these positions were built under the earlier reading of the line, so they are pinned to it
as the record (PM_LIVE_RULES=1 re-validates them under the current reading)."""
import os
import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.cards import TEAMS
from playmaker_engine.resolve import apply, ChanceNode, force
from playmaker_engine.scenarios import game_state
from playmaker_engine.state import Context, GameState

LIVE = RC.Rules() if os.environ.get('PM_LIVE_RULES') else RC.with_rules(**RC.PRE_RULEBOOK)
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']


def board(off, dfn, o, x, arrows, ball=0, **kw):
    return game_state(off, dfn, o, x, arrows, ball=ball, rules=LIVE, check=False).with_(**kw)


def lineup(off_cards, dfn_cards, o, x, arrows, ball=0, **kw):
    ctx = Context(off_cards, dfn_cards, LIVE, title='live test', kind='GAME', off_team='test', def_team='test')
    return GameState(ctx=ctx, o=tuple(P(q) for q in o), x=tuple(P(q) for q in x),
                     arrows=tuple(B.DIR_NAMES.index(a) for a in arrows), ball=ball, **kw)


def settle(node, prefer=('success', 'kept', 'no foul', 'holds')):
    while isinstance(node, ChanceNode):
        labels = [lab for _, lab, _ in node.outcomes]
        node = force(node, next((l for l in prefer if l in labels), labels[0]))
    return node


def passive_defence(o, s, steps=80):
    """The offence computer against a defence that never moves, every roll the offence's way."""
    for _ in range(steps):
        if s.stage == 'over':
            break
        if s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play'):
            a = o.choose(s)
        else:
            acts = legal_actions(s)
            a = next((x for x in acts if x.kind in ('pause', 'end_turn')), None) or \
                next((x for x in acts if x.kind == 'contest' and x.piece < 0), acts[0])
        s = settle(apply(s, a))
    return s


def test_these_are_the_live_rules():
    assert LIVE.intercept_rule == 'move_then_intercept' and LIVE.turnover_cost == 'minus5_lose_phase'
    assert LIVE.arrow_mode == 'single'
    # the positions are pinned to the pre-rulebook line reading; everything else is the live default
    assert RC.with_rules(**RC.PRE_RULEBOOK) == LIVE or LIVE == RC.DEFAULT_RULES


# ---- the goal chain on the post position ----------------------------------------------------------------
# The step 3i post position (O5, ▲ post, on the right block against a ▼ post X5 fronting him), with O2 a square
# higher and X1 facing the baseline: X1 can't jump either swing lane from where he stands, so the chain is the
# full one: both receivers open their lanes, two swings, the seal, the entry.

BB = TEAMS['Bucket Brigade']
POST_OFF = [TEAMS['Iron Wall'][0], TEAMS['Lockdown'][0], TEAMS['Iron Wall'][3], TEAMS['Twin Towers'][3], TEAMS['High-Low'][4]]
POST_DFN = [BB[0], BB[1], BB[4], BB[3], BB[2]]
POST_O = ['O8', 'H8', 'C5', 'B3', 'K3']
POST_O = ['O8', 'H9', 'C5', 'B3', 'K3']
POST_X = ['M8', 'G6', 'E7', 'A2', 'L4']
POST_ARROWS = ['S', 'E', 'E', 'NE', 'NE']
CHAIN = ['O2 moved to open the lane', 'O3 moved to open the lane', 'swung the ball to O2', 'swung the ball to O3', 'O5 sealed X5', 'entry to O5']


def post_position(**kw):
    return lineup(POST_OFF, POST_DFN, POST_O, POST_X, POST_ARROWS, **kw)


def _events(o):
    return [n for n in o.notes if n['event'] in ('goal', 'goal_step', 'goal_reassess', 'goal_finish')]


# ---- rotations -------------------------------------------------------------------------------------------
# The step 3i playout position (Bucket Brigade v Lockdown); X1, X4 and X5 have used their Moves. Under the live
# rules X3 is the one with two jobs: help on O1's drive and the lane to O3. X2 (Move left) faces up the wing;
# turning him takes the lane off X3.

def _rotation():
    s = board('Bucket Brigade', 'Lockdown', ['I6', 'D7', 'O9', 'D2', 'Q2'], ['H7', 'D8', 'N8', 'I5', 'J6'],
              ['W', 'N', 'NW', 'NW', 'W'], clock=10)
    return s.with_(tok_o=1, tok_x=2, moved_o=24, moved_x=25, cnt=(0, 0, 1, 1, 1, 0, 1, 0, 0, 0, 1), lock_o=1, phase=2, qs_x=1)


