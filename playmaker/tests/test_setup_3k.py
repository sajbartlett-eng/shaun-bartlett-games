"""Step 3k: the computer's setup, offence and defence (no rule changes). The offence places first from the cards alone
and anticipates the defence's best response; the defence sees the offence's placement, searches all 120 matchups and
gives each defender a job, then checks the whole defence. Scenario cards keep their fixed setups."""
import inspect
import time

import pytest

from playmaker_engine import board as B
from playmaker_engine.actions import denier, movement_dests
from playmaker_engine.cards import TEAMS
from playmaker_engine.scenarios import game_state, scenario_state, setup_errors

PAIRINGS = [('Five Out', 'High-Low'), ('Twin Towers', 'Pace and Space'), ('Iron Wall', 'Bucket Brigade')]
def maker(off, dfn):
    return lambda o_sq, ball, xs, ar: game_state(off, dfn, [B.sq(q) for q in o_sq], [B.sq(q) for q in xs], list(ar), ball=ball, check=False)


# ---- matchups ------------------------------------------------------------------------------------------------------

# Retired in step 3m (the decision engine replaces the step 3e to 3k computer inside games): test_the_defence_setup_starts_the_matchup_record


def _log(g):
    import json
    with open(g.log_path) as f:
        return [json.loads(l) for l in f]


# ---- the ball handler and variety ---------------------------------------------------------------------------------

# ---- legality ------------------------------------------------------------------------------------------------------

def test_scenario_cards_keep_their_fixed_setups():
    from playmaker_web.game import Game
    for n in (1, 6, 13):
        g = Game(mode='hotseat', scenario=n, ai={'X': 'allstar'}, place=True, seed=1)
        assert not g.place_on and g.placing is None
        assert g.state.encode() == scenario_state(n, rules=g.rules).encode()


# ---- jobs ----------------------------------------------------------------------------------------------------------

# ---- coherence -----------------------------------------------------------------------------------------------------

# ---- no hidden information, speed, the review ----------------------------------------------------------------------

def test_the_review_explains_the_setup():
    from playmaker_engine.review import computer_facts
    recs = [dict(type='setup', computer=dict(O=dict(name='All-Star', habits=[], concepts_off=[]),
                                             X=dict(name='All-Star', habits=[], concepts_off=[]))),
            dict(type='computer', side='O', event='setup', possession=1,
                 text=['Started the ball with O3 (best creator) for a pick and roll for O3; four out, one in.']),
            dict(type='computer', side='X', event='setup', possession=1,
                 text=["Put X1 on O2: X2 couldn't close out on him (three contest 3 against 5).", 'X5 sagged off O5.'])]
    lines = computer_facts(recs)
    assert any('Started the ball with O3 (best creator)' in l for l in lines)
    assert any("Put X1 on O2: X2 couldn't close out on him" in l and 'X5 sagged off O5' in l for l in lines)


# Step 3m Part 0: the step 3k setup timing test is replaced by the B8 time budgets (tests/test_step3m.py:
# test_the_agent_only_plays_legal_actions_within_its_budget); setup itself now comes from the decision engine.
