"""The preview pack's golden game, regression ceilings, play() determinism and the soak."""
import pytest
import os
import re
import subprocess
import sys
from fractions import Fraction as F

from conftest import P

from playmaker_engine import board as B
from playmaker_engine.actions import Action, legal_actions, MOVEMENT
from playmaker_engine.resolve import apply, force, ChanceNode
from playmaker_engine.policies import play, GreedyPolicy, RandomPolicy
from playmaker_engine.scenarios import SCENARIOS, scenario_state
from playmaker_engine.scoring import choose_contest

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'playmaker_engine', 'data')


@pytest.mark.usefixtures('old_intercepts')   # the intercept rule before the OQ-72 ruling (a scripted line)
def test_golden_game(old_intercepts, golden):
    s = golden
    assert s.ctx.off_team == 'Five Out' and s.ctx.def_team == 'High-Low'
    # Offence: O1 passes to O3.
    s = apply(s, Action('pass', 'O', 0, target=2), check=True)
    # Defence: X3 Moves N8 -> L10 onto the line and Intercepts; the roll succeeds for the offence.
    s = apply(s, Action('move', 'X', 2, P('L10'), 7), check=True)
    assert s.approach == 2
    node = apply(s, Action('intercept', 'X', 2), check=True)
    s = force(node, 'success')
    assert s.ball == 2 and s.side == 'O'
    # Offence: O3 Moves O9 -> N7; O1 Moves I11 -> G10.
    s = apply(s, Action('move', 'O', 2, P('N7')), check=True)
    s = apply(s, Action('move', 'O', 0, P('G10')), check=True)
    # Defence: X5 Moves N4 -> N6; X1 Moves I10 -> H9.
    s = apply(s, Action('move', 'X', 4, P('N6'), 0), check=True)
    s = apply(s, Action('move', 'X', 0, P('H9'), 7), check=True)
    assert s.side == 'O'
    # Offence 3 tokens left, defence 2.
    assert (s.tok_o, s.tok_x) == (3, 2)
    # A pass from O3 to O5 crosses no arrow line.
    a, b = s.o[2], s.o[4]
    assert not any(B.arrow_crosses(xp, d, a, b) for xp, d in zip(s.x, s.arrows))
    # No defender can legally become adjacent to Q3 this phase.
    s2 = apply(s, Action('pass', 'O', 2, target=4), check=True)
    assert s2.side == 'X'
    assert not [a for a in legal_actions(s2) if a.kind == 'intercept']
    seen = set()
    frontier = [s2]
    reached = set()
    for depth in range(2):
        nxt = []
        for st in frontier:
            if isinstance(st, ChanceNode) or st.side != 'X' or st.stage != 'play':
                continue
            for act in legal_actions(st):
                if act.kind not in MOVEMENT:
                    continue
                reached.add(act.dest)
                child = apply(st, act)
                key = (child.x if not isinstance(child, ChanceNode) else None)
                if key not in seen:
                    seen.add(key)
                    nxt.append(child)
        frontier = nxt
    assert not any(B.adjacent(q, P('Q3')) for q in reached)
    # So a three by O5 is contested at 0.
    land = apply(s2, Action('move', 'X', 3, P('G5'), 0))         # any defence turn: the pass lands
    assert land.ball == 4
    assert choose_contest(land, 4, 'three').contest == 0


# ---- regression: first-turn ceilings ------------------------------------------------------

def legacy_script_numbers():
    out = subprocess.run([sys.executable, os.path.join(DATA, 'scenario_tests.py')], capture_output=True, text=True,
                         cwd=DATA).stdout
    res = {}
    lines = out.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r'\s*(\d+) .*first-turn (?:PASS|GIFT): (.*)', line)
        if m:
            n = int(m.group(1))
            g = re.match(r'best (-?\d+)', m.group(2))
            top = int(re.search(r'reachable ceiling (-?\d+)', lines[i + 1]).group(1))
            res[n] = (int(g.group(1)) if g else None, top)
    return res


def test_legacy_ceilings_reproduced_exactly():
    from playmaker_engine.analysis import legacy_ceilings
    script = legacy_script_numbers()
    mine = legacy_ceilings()
    assert len(script) == 16
    for n, (g, top) in script.items():
        assert (mine[n][0], mine[n][2]) == (g, top), n


@pytest.mark.usefixtures('legacy_rules')   # recorded under the rules before the step 3i follow-up rulings
def test_engine_ceilings_recorded():
    from playmaker_engine.analysis import engine_ceilings
    eng = engine_ceilings([6, 10, 14])
    assert eng[6][0][0] == 9 and eng[6][1][0] == 30
    assert eng[10][0][0] == F(51, 4)            # 12.75: see REGRESSION.md
    assert eng[14] == (None, None)              # Hold for One: no shot before the final phase


@pytest.mark.usefixtures('legacy_rules')   # recorded under the rules before the step 3i follow-up rulings
def test_two_action_reaction_closes_the_gap():
    # Late Clock Reset: one reaction action leaves O1's three worth 12.75; with two actions X4
    # Moves (arrow set) and Quick Steps in to contest clean: 3.
    from playmaker_engine.analysis import two_action_ceilings
    gift = two_action_ceilings([10], parts=('gift',))[10][0]
    assert gift[0] == 3 and 'then' in gift[1]


# ---- play() -------------------------------------------------------------------------------

def test_play_same_seed_same_game():
    a = play(5, RandomPolicy(), RandomPolicy(), seed=11)
    b = play(5, RandomPolicy(), RandomPolicy(), seed=11)
    assert a['log'] == b['log'] and a['score'] == b['score']


def test_greedy_plays_every_scenario():
    for n in SCENARIOS:
        res = play(n, GreedyPolicy(), GreedyPolicy(), seed=1)
        assert res['final'].stage == 'over'


def test_states_hashable_and_encoded(golden):
    s1 = apply(golden, Action('move', 'O', 1, P('C10')))
    s2 = apply(golden, Action('move', 'O', 1, P('C10')))
    assert s1 == s2 and hash(s1) == hash(s2) and s1.encode() == s2.encode()
    assert len({s1, s2, golden}) == 2


# ---- soak ---------------------------------------------------------------------------------

def test_soak_random_v_random():
    from playmaker_engine.soak import run_soak
    games = int(os.environ.get('PLAYMAKER_SOAK_GAMES', '10000'))
    rep = run_soak(games, workers=os.cpu_count() or 1)
    print(rep['summary'])
    assert rep['ok'] and rep['games'] == games
