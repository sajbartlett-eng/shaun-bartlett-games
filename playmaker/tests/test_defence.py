"""Step 3e: the computer defence reads the board. Arrows do one of four jobs (on the ball, wall, lane,
help); a defender with their Move left can still face the shooter as a reaction, so keeping every arrow
on the ball is no longer the default."""
import os

import pytest

from playmaker_engine.defence import ReadingDefence
from playmaker_engine.policies import GreedyPolicy
from playmaker_engine.scenarios import scenario_state

@pytest.fixture(scope='module')
def profiles():
    """46 possessions (30 table-setup games across team pairings, the 16 scenario cards), greedy offence.
    Played under the intercept rule before the OQ-72 ruling: since it, a greedy offence's first contested pass
    usually ends the possession (a successful Intercept ends it at -5), leaving a handful of defence moves."""
    from playmaker_engine import rules_config as RC
    from playmaker_engine.defence_check import job_profile
    from playmaker_engine.computer import Computer
    with pytest.MonkeyPatch.context() as mp:
        if not os.environ.get('PM_LIVE_RULES'):
            mp.setattr(RC, 'DEFAULT_RULES', RC.with_rules(intercept_rule='approach', turnover_cost='legacy'))
        return dict(greedy=job_profile(GreedyPolicy()), reader=job_profile(ReadingDefence(budget_s=None)),
                    starter=job_profile(Computer('X', 'starter', seed=1, habits=[], overrides={'randomness': 0.0}, budget_s=None)))


def _share(c, *keys):
    return sum(c[k] for k in keys) / max(1, sum(c.values()))


def test_arrow_on_the_ball_no_longer_dominates_in_play(profiles):
    g, r = profiles['greedy'][0]['play'], profiles['reader'][0]['play']
    # (the absolute share moved with OQ-52: one Quick Step per player shrinks what a reaction can fix)
    assert _share(r, 'on_ball') < _share(g, 'on_ball'), (g, r)


def test_walls_lanes_and_help_rise(profiles):
    g, r = profiles['greedy'][0]['play'], profiles['reader'][0]['play']
    assert _share(r, 'wall', 'lane', 'help') > _share(g, 'wall', 'lane', 'help'), (g, r)


def test_the_reaction_still_faces_the_shooter(profiles):
    r = profiles['reader'][0]['reaction']
    assert _share(r, 'on_ball') >= 0.9, r


def test_the_offence_scores_less_against_it(profiles):
    assert profiles['reader'][1] < profiles['greedy'][1], (profiles['greedy'][1], profiles['reader'][1])


def test_setup_arrows_are_chosen_not_all_on_the_man():
    from playmaker_web.game import Game
    from playmaker_engine.defence import arrow_job
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], full=True, place=True, seed=1, level='pro', ai=dict(X='allstar'))
    g.place(g.tokens['both'], dict(squares=['I11', 'C9', 'O9', 'A3', 'Q3'], ball=0))
    jobs = [arrow_job(g.state, j) for j in range(5)]
    assert g.placing is None and set(jobs) != {'on_man'} and jobs.count('on_ball') + jobs.count('on_man') < 5, jobs


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
    from playmaker_engine.defence_check import PATH, grade, load
    if not os.path.exists(PATH):
        pytest.skip('defence_set.json not built (python -c "from playmaker_engine.defence_check import build; build()")')
    rows = load()
    g, r = grade(GreedyPolicy(), rows), grade(ReadingDefence(budget_s=None), rows)
    assert r['missing'] == 0 and g['missing'] == 0
    assert r['agree'] >= g['agree'] and r['mean_gap'] <= g['mean_gap'], (g, r)


def test_the_computer_defence_in_a_game_logs_arrow_jobs():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', scenario=6, seed=3, level='pro', ai=dict(O='greedy', X='greedy'))
    acts = [r for r in g.read_log() if r['type'] == 'action' and r['action']['side'] == 'X'
            and r['action']['kind'] in ('move', 'qs', 'sprint')]
    assert g.state.stage == 'over' and all('arrow_job' in r for r in acts)   # every defender move is labelled
    assert type(g.policies['X']).__name__ == 'Computer' and g.policies['X'].level == 'starter'
    b = Game(mode='hotseat', scenario=6, seed=3, level='pro', ai=dict(X='baseline'))
    assert type(b.policies['X']).__name__ == 'GreedyPolicy'


def test_the_defence_plays_closer_to_the_solver_mid_phase():
    """50 defence turns from the scenario cards in play, graded by a fixed-depth solver search (the value
    the offence gets after the defence's whole turn, against the best of the solver's own plays)."""
    import json
    from playmaker_engine.defence_check import PLAY_PATH, summary_play
    if not os.path.exists(PLAY_PATH):
        pytest.skip('defence_play_set.json not built (defence_check.build_play())')
    rows = json.load(open(PLAY_PATH))
    s = summary_play(rows)
    assert s['reader']['n'] == 50
    assert s['reader']['mean_gap'] < s['greedy']['mean_gap'] and s['reader']['agree'] > s['greedy']['agree'], s


def test_the_starter_computer_spreads_its_arrows_too(profiles):
    g, r = profiles['greedy'][0]['play'], profiles['starter'][0]['play']
    assert _share(r, 'on_ball') < _share(g, 'on_ball') and _share(r, 'wall', 'lane', 'help') > _share(g, 'wall', 'lane', 'help'), (g, r)
