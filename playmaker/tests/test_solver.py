"""Solver correctness: brute force, candidate coverage, determinism, golden position, terminal values."""
import random

import pytest
from conftest import mk, P

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions
from playmaker_engine.resolve import apply, force, ChanceNode
from playmaker_engine.scoring import score
from playmaker_engine.solver import (Searcher, Evaluator, Generator, exact_solve, terminal_vals, apply_play,
                                     expected, pruned_actions)
from playmaker_engine.solver_config import with_config
from playmaker_engine.state import CI, ZERO_COUNTS

FILL_O = ['A14', 'C14', 'E14', 'G14']
FILL_X = ['Q14', 'O14', 'M14', 'K14']


def micro(o_act, x_act, ball=0, tok_o=1, tok_x=1, side='O', stage='play', clock=2, shot=None, **kw):
    """A small position: the listed pieces play; the rest are parked, locked and already moved.
    o_act: {index: square}; x_act: {index: (square, arrow)}. Quick Steps and Screens are spent."""
    o = [None] * 5
    x = [None] * 5
    arr = ['N'] * 5
    fo, fx = iter(FILL_O), iter(FILL_X)
    for i in range(5):
        o[i] = o_act.get(i) or next(fo)
        if i in x_act:
            x[i], arr[i] = x_act[i]
        else:
            x[i] = next(fx)
    frozen_o = sum(1 << i for i in range(5) if i not in o_act)
    frozen_x = sum(1 << i for i in range(5) if i not in x_act)
    cnt = list(ZERO_COUNTS)
    cnt[CI['o_qs']] = cnt[CI['x_qs']] = 2
    cnt[CI['screen']] = 2
    lock_o = kw.pop('lock_o', 0) | frozen_o
    s = mk(o, x, arr, ball=ball, clock=clock, tok_o=tok_o, tok_x=tok_x, side=side, stage=stage,
           moved_o=frozen_o, moved_x=frozen_x, lock_o=lock_o, lock_x=frozen_x, cnt=tuple(cnt), shot=shot, **kw)
    return s


def brute(node):
    """Plain expectimax over every legal action: no transposition table, no pruning."""
    if isinstance(node, ChanceNode):
        return sum(float(p) * brute(sub) for p, _, sub in node.outcomes)
    if node.stage == 'over':
        return float(score(node).total)
    vals = [brute(apply(node, a)) for a in legal_actions(node)]
    return max(vals) if node.side == 'O' else min(vals)


MICROS = [
    # offence to act, 1 token each, final phase
    lambda: micro({0: 'J10'}, {0: ('J8', 'N')}),
    lambda: micro({0: 'I7', 1: 'M9'}, {0: ('I6', 'N'), 1: ('L8', 'W')}),
    # shot already declared: the defence reacts with up to two actions
    lambda: micro({0: 'H9'}, {0: ('H7', 'E'), 1: ('K9', 'N')}, side='X', stage='reaction', tok_x=2, shot='long'),
    # locked ball carrier, two offence tokens
    lambda: micro({0: 'I8', 1: 'C9'}, {0: ('I7', 'N'), 1: ('D8', 'NE')}, tok_o=2, lock_o=0b1),
]


@pytest.mark.parametrize('k', range(len(MICROS)))
def test_exact_solver_matches_brute_force(k):
    s = MICROS[k]()
    exact, _ = exact_solve(s)
    assert exact.ev == pytest.approx(brute(s), abs=1e-9)
    exact_np, _ = exact_solve(s, prune=False)
    assert exact_np.ev == pytest.approx(exact.ev, abs=1e-9)          # pruning is exact


@pytest.mark.parametrize('k', range(len(MICROS)))
def test_guided_search_within_half_a_point(k):
    s = MICROS[k]()
    exact, _ = exact_solve(s)
    se = Searcher(with_config(endgame_tokens=0, beam=30, root_beam=100))
    r = se.search(s, max_depth=5)
    assert abs(r['vals'][0].ev - exact.ev) <= 0.5, (r['vals'][0].ev, exact.ev)


def random_endgame(rng):
    squares = [(x, y) for x in range(B.W) for y in range(2, 12)]
    picks = rng.sample(squares, 4)
    o_act = {0: B.sq(picks[0]), 1: B.sq(picks[1])}
    x_act = {0: (B.sq(picks[2]), rng.choice(B.DIR_NAMES)), 1: (B.sq(picks[3]), rng.choice(B.DIR_NAMES))}
    if rng.random() < 0.5:
        return micro(o_act, x_act)
    s = micro(o_act, x_act, side='X', stage='reaction', tok_x=2)
    z = B.zone(s.o[0])
    if z == '.':
        return micro(o_act, x_act)
    return s.with_(shot=RC.ZONE_SHOTS[z][0])


def _exact_node(node):
    if isinstance(node, ChanceNode):
        return sum(float(p) * _exact_node(sub) for p, _, sub in node.outcomes)
    return exact_solve(node)[0].ev if node.stage != 'over' else float(score(node).total)


def test_candidate_coverage():
    rng = random.Random(7)
    cfg = with_config()
    hits, misses = 0, []
    for i in range(50):
        s = random_endgame(rng)
        best, per = exact_solve(s)
        maximise = s.side == 'O'
        gen = Generator(cfg, Evaluator(cfg))
        cands = gen.plays(s, shallow=True)
        vals = []
        for p in cands:
            node = apply_play(s, p)
            if node is not None:
                vals.append(_exact_node(node))
        got = (max(vals) if maximise else min(vals)) if vals else None
        if got is not None and abs(got - best.ev) <= 0.5:
            hits += 1
        else:
            misses.append((s.encode(), best.ev, got))
    print(f'candidate coverage: {hits}/50; misses: {misses}')
    assert hits >= 48, misses


def test_determinism():
    from playmaker_engine.solver_report import solve_card
    a = solve_card(13, budget_s=None, max_depth=2)
    b = solve_card(13, budget_s=None, max_depth=2)
    assert a['value'] == b['value'] and a['line'] == b['line']


def golden_position():
    from playmaker_engine.soak import golden_setup
    s = golden_setup()
    s = apply(s, Action('pass', 'O', 0, target=2))
    s = apply(s, Action('move', 'X', 2, P('L10'), 7))
    s = force(apply(s, Action('intercept', 'X', 2)), 'success')
    s = apply(s, Action('move', 'O', 2, P('N7')))
    s = apply(s, Action('move', 'O', 0, P('G10')))
    s = apply(s, Action('move', 'X', 4, P('N6'), 0))
    return apply(s, Action('move', 'X', 0, P('H9'), 7))


def test_golden_position_kick_out_and_what_beats_it():
    s = golden_position()
    se = Searcher()
    r = se.search(s, max_depth=2)
    kids = {p.text(): v[0] for p, v in r['entry'].children}
    o5 = s.ctx.off[4].shot('three')
    o3 = s.ctx.off[2].shot('three')
    # The kick-out to O5 is uncontested: 3 x O5's three rating.
    assert kids['O3 Pass to O5'].ev == 3 * o5 == 24
    # It is beaten by O3 stepping to the corner (O8) for its own uncontested three: 3 x 9 = 27.
    assert r['vals'][0].ev == 3 * o3 == 27
    assert kids['O3 Quick Step to O8 then O3 Shot (three)'].ev == 27


def test_terminal_values_agree_with_score():
    from playmaker_engine.scenarios import scenario_state
    # Coach's Call bonus
    s = scenario_state(8, target=0)
    s = s.with_(o=(P('J10'),) + s.o[1:], x=(P('A14'),) + s.x[1:])
    end = apply(apply(s, Action('shot', 'O', 0, shot='three')), Action('end_turn', 'X'))
    assert terminal_vals(end, (None,))[0].ev == score(end).total
    assert Evaluator()(end)[0].ev == score(end).total
    # and-one foul
    s2 = mk(['I4', 'C9', 'O9', 'A3', 'A14'], ['I3', 'D8', 'N8', 'G4', 'N4'], ['E', 'NE', 'NW', 'N', 'N'],
            off='High-Low', dfn='Five Out')
    node = apply(apply(s2, Action('shot', 'O', 0, shot='post')), Action('end_turn', 'X'))
    for _, _, leaf in (node.flatten() if isinstance(node, ChanceNode) else [(1, '', node)]):
        assert terminal_vals(leaf, (None,))[0].ev == score(leaf).total
    # floors: a declared shot worth less than 0
    s3 = mk(['I14', 'A14', 'C14', 'Q3', 'E14'], ['A13', 'P3', 'M14', 'K14', 'O14'], ['N', 'E', 'N', 'N', 'N'],
            ball=3, off='Twin Towers', dfn='Shoot and Protect')
    end3 = apply(apply(s3, Action('shot', 'O', 3, shot='three')), Action('end_turn', 'X'))
    assert terminal_vals(end3, (None,))[0].ev == score(end3).total == 0


def test_evaluation_matches_two_action_ceiling():
    # Late Clock Reset: the regression's two-action gift is 3; the evaluation of the start agrees.
    from playmaker_engine.scenarios import scenario_state
    v = Evaluator()(scenario_state(10))[0]
    assert v.ev == pytest.approx(3.0, abs=0.01)
