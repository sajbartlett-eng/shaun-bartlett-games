"""Step 3e: the computer opponent at three levels. It chooses among legal actions only, sees only what a
human sees, values contests after the defence's legal reaction, and its levels make named mistakes."""
import json
import os

import pytest
from conftest import P

from playmaker_engine import board as B
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import scenario_state, game_state
from playmaker_engine.state import CI

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def table(off='Five Out', dfn='High-Low'):
    return game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS)


def shot_declared():
    """Scenario 6: O1 steps to J10 and declares a three. X1 on I10 faces N, not the shooter (E)."""
    s = scenario_state(6)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)))
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot'))
    assert s.stage == 'reaction' and s.arrows[0] != B.dir_between(s.x[0], s.o[0])
    return s


def entry(rc, d):
    return next((e for e in rc if e['defender'] == d), None)


# ---- section 1: the reaction ----------------------------------------------------------------------

# ---- sections 2-5: reserve, help, comfort line, paint, setup ------------------------------------

def test_setup_matchups_and_arrows_come_from_the_evaluation():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, place=True, seed=1, level='pro', ai=dict(X='allstar'))
    g.place(g.tokens['both'], dict(squares=TABLE_O, ball=0))
    assert g.placing is None
    rec = [r for r in g.read_log() if r['type'] == 'computer' and r.get('event') == 'setup']
    assert rec and len(rec[0]['matchup']) == 5
    from playmaker_engine.defence import arrow_job
    assert any(arrow_job(g.state, j) != 'on_man' for j in range(5))


# ---- section 7: the offence -------------------------------------------------------------------------

def _log_3a9c33():
    """Playtest log 3A9C33, possession 1: O1 passes to O2 at clock 12 and the defence pauses. O2's three
    is worth 27 with X4's clean contest; the old Starter took it at once."""
    from playmaker_engine.resolve import force
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['J10', 'D8', 'O8', 'B4', 'P2'],
                   ['NW', 'NW', 'N', 'SW', 'NE'])
    s = force(apply(s, Action('pass', 'O', 0, target=1)), 'success')
    return apply(s, next(a for a in legal_actions(s) if a.kind == 'pause'))


# ---- section 8: levels, habits, tunnel vision, card reading, no cheating -------------------------

# Retired in step 3m (the decision engine replaces the step 3e to 3k computer inside games): test_about_the_computer_names_the_habits_and_missing_concepts


def test_about_the_computer_waits_for_the_end():
    from playmaker_web.game import Game, GameError
    g = Game(mode='hotseat', scenario=6, seed=4, level='pro', ai=dict(X='starter'))
    with pytest.raises(GameError):
        g.review(g.tokens['both'])
    from playmaker_web.view import state_json
    assert 'About the computer' not in json.dumps(state_json(g, g.tokens['both']))


# Retired in step 3m (the decision engine replaces the step 3e to 3k computer inside games): test_help_the_golden_setup_still_contests_every_kick_out_cleanly


# ---- playtest log D7D923 (All-Star v All-Star): two uncontested shots one offence turn away ---------

def _d7d923():
    from playmaker_engine.review import replay_states
    recs = [json.loads(l) for l in open(os.path.join(os.path.dirname(__file__), 'data', 'log_D7D923.jsonl'))]
    return replay_states(recs)


def test_a_play_cannot_run_past_the_end_of_its_turn():
    from playmaker_engine.solver import Play, apply_play
    s0 = _d7d923()[18][0]                             # X has already taken one of its two actions
    p = Play('closeout', (Action('move', 'X', 0, P('L10'), 4), Action('qs', 'X', 0, P('N8'))))
    assert apply(s0, p.actions[0]).side == 'O' and apply_play(s0, p) is None


# ---- playtest log 82866B (Rookie v Rookie): the offence looped from clock 8 to clock 2 ----------------

def _82866b():
    from playmaker_engine.review import replay_states
    recs = [json.loads(l) for l in open(os.path.join(os.path.dirname(__file__), 'data', 'log_82866B.jsonl'))]
    return replay_states(recs)


