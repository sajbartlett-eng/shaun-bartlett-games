"""Step 18r (Shaun, 16 Nov 2026), D-198: in the app fouls and turnovers are priced in points and play goes on. A foul
is +5 (a shooting foul: +5 and its free throws); a steal, an intercepted pass, three seconds, closely guarded and the
shot clock are each -5, the phase ends there and the next begins; after an intercepted pass the passer keeps the ball
and the defender goes back to where he began the phase; step 18i's foul pricing is retired; no shot from the rim's own
square. The table keeps its own rules."""
import json
import os
import subprocess
import sys

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import legal_actions
from playmaker_engine.decide import Read, foul_externality, turnover_value
from playmaker_engine.resolve import ChanceNode, apply, end_phase
from playmaker_engine.scenarios import game_state
from playmaker_engine.scoring import score as possession_score

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = RC.with_rules(digital=True, zone='on')
OLD = RC.with_rules(digital=True, zone='on', points_play_on='off', no_rim_shot='off')
O_, X_, A_ = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['J10', 'D8', 'O8', 'B4', 'P2'], ['NW', 'NW', 'N', 'SW', 'NE']


def board(rules=APP, o=None, x=None, arrows=None, **kw):
    s = game_state('Five Out', 'High-Low', list(o or O_), list(x or X_), list(arrows or A_), ball=0, rules=rules, check=False)
    return s.with_(**kw) if kw else s


def with_ctx(s, **kw):
    import copy
    ctx = copy.copy(s.ctx)
    for k, v in kw.items():
        setattr(ctx, k, v)
    return s.with_(ctx=ctx)


def leaves(node, label=''):
    if isinstance(node, ChanceNode):
        out = []
        for p, lab, sub in node.outcomes:
            out += leaves(sub, f'{label}/{lab}')
        return out
    return [(label, node)]


def reach(s):
    s = s.with_(side='X')
    return dict(leaves(apply(s, next(a for a in legal_actions(s) if a.kind == 'steal'))))


def test_the_switches_are_the_apps_only():
    assert RC.app_rule(APP, 'points_play_on') and RC.app_rule(APP, 'no_rim_shot')
    assert not RC.app_rule(RC.Rules(), 'points_play_on') and not RC.app_rule(RC.Rules(), 'no_rim_shot')
    assert RC.turnover_counts(APP) and RC.turnover_counts(RC.Rules()) and not RC.turnover_counts(OLD)


def test_a_steal_is_minus_five_the_phase_ends_and_play_goes_on():
    s = board()
    out = reach(s)
    stolen = out['/no foul/stolen']
    assert stolen.stage == 'play' and stolen.tos == 1 and stolen.ball == s.ball
    assert stolen.phase == s.phase + 1 and stolen.clock == s.clock - RC.PHASE_SECONDS
    assert stolen.side == 'O' and stolen.tok_o == RC.TOKENS_PER_PHASE and stolen.tok_x == RC.TOKENS_PER_PHASE and stolen.lock_x == 0
    kept = out['/no foul/kept']
    assert kept.phase == s.phase and kept.tos == 0 and kept.locked('X', 0)      # a missed reach still locks him
    assert reach(board(OLD))['/no foul/stolen'].stage == 'over'                  # as it was: the possession ended


def test_a_foul_is_plus_five_and_play_goes_on_with_no_penalty():
    s = board()
    foul = reach(s)['/foul']
    assert foul.stage == 'play' and foul.bonus5 == 1 and foul.fouls == 1 and foul.phase == s.phase and foul.locked('X', 0)
    deep = with_ctx(board(), team_fouls=9)                                       # far past the old penalty line
    foul = reach(deep)['/foul']
    assert foul.stage == 'play' and foul.bonus5 == 1                              # no free throws for team fouls
    assert reach(board(OLD))['/foul'].bonus5 == 0                                # as it was (D-179)


def test_a_turnover_in_the_last_phase_ends_the_possession_on_what_it_has_banked():
    s = board(clock=RC.PHASE_SECONDS, bonus5=1)
    stolen = reach(s)['/no foul/stolen']
    assert stolen.stage == 'over' and not stolen.zeroed and stolen.tos == 1
    assert possession_score(stolen).total == 0                                 # +5 and -5
    stolen = reach(board(clock=RC.PHASE_SECONDS))['/no foul/stolen']
    assert possession_score(stolen).total == -5


def test_the_shot_clock_is_minus_five_and_the_possession_is_over():
    s = end_phase(board(clock=RC.PHASE_SECONDS))
    assert s.stage == 'over' and s.result.violation == 'shot_clock' and not s.zeroed
    assert possession_score(s).total == -5


def test_a_shooting_foul_is_plus_five_and_its_free_throws():
    s = board(o=['I4'] + O_[1:], x=['I5'] + X_[1:], arrows=['S'] + A_[1:])      # a defender behind the shooter: the hard contest can foul
    shot = next(a for a in legal_actions(s) if a.kind == 'shot')
    node = apply(s, shot)
    seen = False
    while not isinstance(node, ChanceNode) and node.stage != 'over':
        acts = legal_actions(node)
        # (step 28, D-261: the block is the hard Contest; a normal Contest never fouls)
        pick = (next((a for a in acts if a.kind == 'contest' and a.shot == 'hard'), None) or next((a for a in acts if a.kind == 'contest'), None)
                or next(a for a in acts if a.kind in ('end_turn', 'pause')))
        node = apply(node, pick)
    for label, n in leaves(node):
        if n.stage == 'over' and n.result.kind == 'free_throws':
            seen = True
            assert n.bonus5 == 1 and possession_score(n).total >= 5
    assert seen


def test_three_seconds_and_closely_guarded_are_minus_five_and_play_goes_on():
    s = board(o=['I4'] + O_[1:], x=['I12'] + X_[1:], arrows=['S'] + A_[1:])     # the ball handler in the key, nobody on him
    one = end_phase(s)
    assert one.tos == 0 and one.key_o & 1
    two = end_phase(one)
    # Re-recorded in step 27 (D-254, the app only): after the violation his count doesn't start again (it read cleared):
    # still in the key at the next phase end, he commits it again
    assert two.stage == 'play' and two.tos == 1 and two.phase == s.phase + 2 and two.key_o & 1
    assert end_phase(two).tos == 2
    old = end_phase(end_phase(board(OLD, o=['I4'] + O_[1:], x=['I12'] + X_[1:], arrows=['S'] + A_[1:])))
    assert old.stage == 'over'
    g = board()                                                                  # X1 next to him with an arrow on him
    for _ in range(RC.GUARDED_ENDS - 1):
        g = end_phase(g)
        assert g.tos == 0
    g = end_phase(g)
    assert g.stage == 'play' and g.tos == 1 and g.guard()[1] == 0


def test_an_intercepted_pass_goes_back_to_the_passer_and_the_defender_to_where_he_began_the_phase():
    s = board(x=['I8', 'D8', 'N8', 'B4', 'P2'], arrows=['N', 'NW', 'N', 'SW', 'NE'])   # X3 a step off the lane from O1 to O3, facing it
    start = (s.x, s.arrows)
    s = apply(s, next(a for a in legal_actions(s) if a.kind == 'pass' and a.target == 2))
    done = False
    for a in legal_actions(s):
        if a.piece != 2 or a.kind not in ('move', 'qs', 'sprint', 'intercept'):
            continue
        n = apply(s, a)
        if a.kind != 'intercept':
            if isinstance(n, ChanceNode) or n.stage != 'play':
                continue
            ic = next((b for b in legal_actions(n) if b.kind == 'intercept' and b.piece == 2), None)
            if ic is None:
                continue
            assert n.x[2] != start[0][2]                                         # he stepped into the lane first
            n = apply(n, ic)
        for label, leaf in leaves(n):
            if leaf.tos == 1:
                done = True
                assert leaf.stage == 'play' and leaf.ball == 0 and leaf.pending is None
                assert leaf.phase == s.phase + 1 and leaf.clock == s.clock - RC.PHASE_SECONDS
                assert leaf.x[2] == start[0][2] and leaf.arrows[2] == start[1][2]
        if done:
            break
    assert done


def test_the_foul_price_of_step_18i_is_retired():
    assert foul_externality(with_ctx(board(fouls=2), team_fouls=3, quarter_left=10)) == 0.0
    assert foul_externality(with_ctx(board(OLD, fouls=2), team_fouls=3, quarter_left=10)) > 0.0


def test_what_is_banked_counts_turnovers_and_the_reading_sees_it():
    s = board()
    assert abs(Read(s.with_(tos=1)).leaf() - (Read(s).leaf() - 5)) < 1e-9
    assert turnover_value(s) < Read(s).leaf()
    assert turnover_value(board(clock=RC.PHASE_SECONDS)) == -5.0


def test_no_shot_from_the_rims_own_square():
    s = board(o=['I2'] + O_[1:])
    assert B.sq(RC.RIM) == 'I2' and not [a for a in legal_actions(s) if a.kind == 'shot']
    assert [a for a in legal_actions(board(o=['I3'] + O_[1:])) if a.kind == 'shot']
    assert [a for a in legal_actions(board(OLD, o=['I2'] + O_[1:])) if a.kind == 'shot']
    assert [a for a in legal_actions(board(RC.Rules(), o=['I2'] + O_[1:])) if a.kind == 'shot']      # the table keeps it
    r = Read(board(o=['I4'] + O_[1:]))
    assert all(lk.c != RC.RIM for lks in r.looks.values() for lk in lks)


def test_the_reach_is_no_longer_the_defences_best_turn_by_itself():
    """D-198, point 6: nothing sets how often to reach; it falls out of +5 and -5. On these cards a reach fouls 3 times
    in 10 and wins the ball 2 times in 10, so by the points alone it favours the offence."""
    s = board().with_(side='X')
    ev = 0.0

    def walk(node, p):
        nonlocal ev
        if isinstance(node, ChanceNode):
            for q, _, sub in node.outcomes:
                walk(sub, p * float(q))
        else:
            ev += p * (5 * node.bonus5 - 5 * node.tos)
    walk(apply(s, next(a for a in legal_actions(s) if a.kind == 'steal')), 1.0)
    assert ev > 0


def test_both_engines_agree_under_the_new_rules():
    out = subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'js_equivalence.py'), '--soft', '--fiba', '--off-balance', 'on',
                          '--position-contest', 'on', '--zone', '--n', '60'], cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    rep = json.loads(out[out.index('{'):])
    assert rep['mismatches'] == 0 and rep['states'] == 60


def test_d198_is_recorded():
    text = open(os.path.join(ROOT, 'DECISIONS.md')).read()
    assert '**D-198.' in text and 'Shaun, 16 Nov 2026' in text
