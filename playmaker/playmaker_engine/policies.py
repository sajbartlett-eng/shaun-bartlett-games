"""Agents and the game loop. No rule logic lives here: policies only pick from legal_actions."""
import random
from fractions import Fraction

from .actions import legal_actions, MOVEMENT
from .resolve import apply, sample, ChanceNode
from .scoring import score, is_terminal, shot_ev


class Policy:
    """choose(state) -> one of legal_actions(state)."""
    name = 'policy'

    def reset(self, seed):
        pass

    def choose(self, state):
        raise NotImplementedError


class RandomPolicy(Policy):
    name = 'random'

    def __init__(self, seed=0):
        self.rng = random.Random(seed)

    def reset(self, seed):
        self.rng = random.Random(seed)

    def choose(self, state):
        return self.rng.choice(legal_actions(state))


def expected(node, fn):
    """Expected value of fn over a node's outcomes."""
    if isinstance(node, ChanceNode):
        return sum(Fraction(p) * expected(s, fn) for p, _, s in node.outcomes)
    return Fraction(fn(node))


def immediate_shot_value(state):
    """Best value the ball carrier could get by shooting right now (no defensive reaction)."""
    from . import board as B
    from . import rules_config as RC
    if state.stage == 'over':
        return score(state).total
    p = state.o[state.ball]
    if not B.on_board(p):
        return 0
    types = RC.ZONE_SHOTS[B.zone(p)]
    if not types:
        return 0
    return max(shot_ev(state, state.ball, t) for t in types)


class GreedyPolicy(Policy):
    """Baseline. Offence: take the best shot available this turn (shoot now, or one
    movement action then shoot); otherwise drift toward a better shot. Defence: answer
    a pass with the best intercept, then pick the action that leaves the carrier the
    worst immediate shot (and contest a declared shot as well as it can)."""
    name = 'greedy'

    def choose(self, state):
        acts = legal_actions(state)
        if len(acts) == 1:
            return acts[0]
        if state.stage == 'target':
            return max(acts, key=lambda a: max(state.ctx.off[a.target].r[k] for k in state.ctx.off[a.target].r if k.startswith('shot_')))
        if state.side == 'O':
            return self._offence(state, acts)
        return self._defence(state, acts)

    def _offence(self, state, acts):
        shots = [a for a in acts if a.kind == 'shot']
        best_now = max(shots, key=lambda a: shot_ev(state, a.piece, a.shot)) if shots else None
        v_now = shot_ev(state, best_now.piece, best_now.shot) if best_now else None
        best_mv, v_mv = None, None
        for a in acts:
            if a.kind not in MOVEMENT or a.piece != state.ball:
                continue
            nxt = apply(state, a)
            if isinstance(nxt, ChanceNode) or nxt.side != 'O' or nxt.stage != 'play':
                continue
            v = immediate_shot_value(nxt)
            if v_mv is None or v > v_mv:
                best_mv, v_mv = a, v
        if best_now and (v_mv is None or v_now >= v_mv):
            return best_now
        if best_mv is not None:
            return best_mv
        if best_now:
            return best_now
        for kind in ('end_turn', 'hesitate', 'pass'):
            for a in acts:
                if a.kind == kind:
                    return a
        return acts[0]

    def _defence(self, state, acts):
        icpt = [a for a in acts if a.kind == 'intercept']
        if icpt:
            o = state.ctx.off[state.pending[0]]
            return min(icpt, key=lambda a: o.r['pass'] - state.ctx.dfn[a.piece].r['intercept'])
        best, best_v = None, None
        for a in acts:
            nxt = apply(state, a)
            v = expected(nxt, immediate_shot_value)
            if a.kind not in ('end_turn',):
                v += Fraction(1, 1000)        # spend tokens only for a real gain
            if best_v is None or v < best_v:
                best, best_v = a, v
        return best


POLICIES = {'random': RandomPolicy, 'greedy': GreedyPolicy}


def play(setup, offence_policy, defence_policy, seed=0, max_steps=5000, check=None):
    """Play one possession. setup: a GameState or a scenario number.
    Returns dict(log=[...], score=Score, final=GameState, states=n). Same seed, same game.
    check: optional callable(state) run after every apply (invariants)."""
    from .scenarios import scenario_state
    state = scenario_state(setup) if isinstance(setup, int) else setup
    rng = random.Random(seed)
    offence_policy.reset(seed * 2 + 1)
    defence_policy.reset(seed * 2 + 2)
    log = []
    steps = 0
    while not is_terminal(state):
        steps += 1
        if steps > max_steps:
            raise RuntimeError('game did not terminate')
        pol = offence_policy if state.side == 'O' or state.stage == 'target' else defence_policy
        a = pol.choose(state)
        before = state
        nxt = apply(state, a)
        label = ''
        if isinstance(nxt, ChanceNode):
            nxt, label = sample(nxt, rng)
        log.append((before.clock, before.phase, str(a), label))
        state = nxt
        if check:
            check(before, a, state)
    return dict(log=log, score=score(state), final=state, steps=steps)


def format_log(result):
    lines = []
    for clock, phase, a, label in result['log']:
        lines.append(f'[phase {phase}, clock {clock:>2}] {a}' + (f'  -> {label}' if label else ''))
    lines.append(f'Score: {result["score"]}')
    return '\n'.join(lines)
