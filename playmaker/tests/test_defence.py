"""Step 3e: the computer defence reads the board. Arrows do one of four jobs (on the ball, wall, lane,
help); a defender with their Move left can still face the shooter as a reaction, so keeping every arrow
on the ball is no longer the default."""
import os

import pytest

from playmaker_engine.defence import ReadingDefence
from playmaker_engine.policies import GreedyPolicy
from playmaker_engine.scenarios import scenario_state

def _share(c, *keys):
    return sum(c[k] for k in keys) / max(1, sum(c.values()))


# Retired in step 3m (the decision engine replaces the step 3e to 3k computer inside games): test_setup_arrows_are_chosen_not_all_on_the_man


def test_a_reaction_turns_to_face_the_shooter():
    """Scenario 6: O1 steps to J10 and declares a three. X1 on I10 faces N, away from the shooter, with its
    Move unused: the reaction turns it to face J10, so the contest is clean, not a foul roll."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    s = scenario_state(6)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == (9, 10)))
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'shot'))
    assert s.stage == 'reaction' and s.arrows[0] != 2          # X1 does not face E (J10) yet
    d = ReadingDefence()
    for _ in range(4):
        if s.stage != 'reaction':
            break
        s = apply(s, d.choose(s))
    assert s.stage == 'contest'
    from playmaker_engine.scoring import contest_options
    chosen = d.choose(s)
    opt = {o.defender: o for o in contest_options(s, s.ball, s.shot, s.forced)}[chosen.piece]
    assert chosen.piece >= 0 and opt.clean, (chosen, opt)


@pytest.mark.usefixtures('old_intercepts')   # defence_set.json was built (and solved) under the old intercept rule
def test_the_defence_agrees_with_the_solver_more_often():
    from helpers import PATH, grade, load
    if not os.path.exists(PATH):
        pytest.skip('defence_set.json not built (python -c "from playmaker_engine.defence_check import build; build()")')
    rows = load()
    g, r = grade(GreedyPolicy(), rows), grade(ReadingDefence(budget_s=None), rows)
    assert r['missing'] == 0 and g['missing'] == 0
    assert r['agree'] >= g['agree'] and r['mean_gap'] <= g['mean_gap'], (g, r)


def test_the_defence_plays_closer_to_the_solver_mid_phase():
    """50 defence turns from the scenario cards in play, graded by a fixed-depth solver search (the value
    the offence gets after the defence's whole turn, against the best of the solver's own plays)."""
    import json
    from helpers import PLAY_PATH, summary_play
    if not os.path.exists(PLAY_PATH):
        pytest.skip('defence_play_set.json not built (defence_check.build_play())')
    rows = json.load(open(PLAY_PATH))
    s = summary_play(rows)
    assert s['reader']['n'] == 50
    assert s['reader']['mean_gap'] < s['greedy']['mean_gap'] and s['reader']['agree'] > s['greedy']['agree'], s


