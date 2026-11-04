"""The computer defence that reads the board (step 3e).

The greedy baseline scores a defensive action by the carrier's shot *right now*, judged from the current
arrow facings. That makes "arrow on the shooter" win almost every time, although any defender with their
Move and a token left can turn (or step in) to face the shooter as a reaction once the shot is declared.

This defence scores each candidate turn with the solver's evaluation instead, which already counts
reaction-reachable contests (a defender whose Move is unused, who is not locked, with a token in the
pool, can still get adjacent and facing as a reaction) and looks one offence turn ahead (shoot now,
drive, or pass and then shoot). Walls and lanes start to score, and holding a reaction back is valued.

It plays only from the legal actions, reads only the board and the cards (what a human sees), and never
looks at the offence's secret Coach's Call target.
"""
from . import board as B
from .actions import legal_actions
from .policies import Policy, GreedyPolicy, expected
from .resolve import apply, ChanceNode


def arrow_job(state, j):
    """What defender j's arrow is doing, in the rules' four jobs (for logs, tests and the review):
    'on_ball' (on the ball carrier: Steal and a clean contest), 'wall' (adjacent to the carrier, line
    across the carrier's way to the rim), 'lane' (the line crosses a pass from the carrier to a teammate),
    'help' (the line crosses the carrier's drive path to the rim), 'on_man' (on the nearest other
    attacker) or 'other'."""
    xp, a = state.x[j], state.arrows[j]
    cp = state.o[state.ball]          # off the court during an inbound: only the lanes matter then
    inside = B.on_board(cp)
    if B.adjacent(xp, cp) and a == B.dir_between(xp, cp):
        return 'on_ball'
    rim = B.RIM
    if inside and B.adjacent(xp, cp) and B.arrow_crosses(xp, a, cp, rim):
        return 'wall'
    for i, op in enumerate(state.o):
        if i != state.ball and B.on_board(op) and B.arrow_crosses(xp, a, cp, op):
            return 'lane'
    if inside and B.arrow_crosses(xp, a, cp, rim):
        return 'help'
    others = [op for i, op in enumerate(state.o) if i != state.ball and B.on_board(op)]
    if others:
        near = min(others, key=lambda op: B.cheb(op, xp))
        if B.adjacent(xp, near) and a == B.dir_between(xp, near):
            return 'on_man'
    return 'other'


DEFAULT_BUDGET_S = 2.5          # thinking time per decision (the in-browser build sets a lower one)


class ReadingDefence(Policy):
    """Defence: the candidate turn (the solver's defence plays, plus every single legal action for the
    reaction and the contest choice) with the lowest value under the solver's two-turn evaluation.
    Offence: the greedy baseline (unchanged)."""
    name = 'reader'

    def __init__(self, eval_turns=1, budget_s='default'):
        budget_s = DEFAULT_BUDGET_S if budget_s == 'default' else budget_s
        self.budget_s = budget_s      # thinking time per decision; the best play so far is used after that
        from .solver import Evaluator, Generator
        from .solver_config import with_config
        self.cfg = with_config(eval_turns=eval_turns)
        self._Evaluator, self._Generator = Evaluator, Generator
        self._ctx = None
        self._fresh()
        self.offence = GreedyPolicy()

    def _fresh(self):
        # the solver's caches key positions without their context (teams, rules): one set per context
        self.ev = self._Evaluator(self.cfg)
        self.gen = self._Generator(self.cfg, self.ev)
        self.plan = None

    def _context(self, state):
        if state.ctx is not self._ctx:
            self._ctx = state.ctx
            self._fresh()

    def reset(self, seed):
        self.offence.reset(seed)
        self.plan = None

    def choose(self, state):
        acts = legal_actions(state)
        if len(acts) == 1:
            return acts[0]
        defending = state.stage in ('contest', 'reaction') or (state.stage == 'play' and state.side == 'X')
        if not defending:
            return self.offence.choose(state)
        self._context(state)
        if self.plan and self.plan[0] == state and self.plan[1]:
            a = self.plan[1][0]
            if a in acts:
                self._advance(state, a, self.plan[1][1:])
                return a
        self.plan = None
        best = self.best_play(state, acts)
        if best is None:
            return GreedyPolicy().choose(state)
        a = best.actions[0]
        self._advance(state, a, best.actions[1:])
        return a

    def _advance(self, state, a, rest):
        nxt = apply(state, a)
        self.plan = (nxt, rest) if rest and not isinstance(nxt, ChanceNode) else None

    def value(self, node):
        return expected(node, lambda s: self.ev(s)[0].ev)

    def best_play(self, state, acts=None):
        from .solver import Play, apply_play
        self._context(state)
        acts = acts if acts is not None else legal_actions(state)
        plays = self.gen.plays(state, shallow=False)
        if state.stage in ('reaction', 'contest') or state.pending:
            have = {p.actions for p in plays}
            plays += [Play('single', (a,)) for a in acts if (a,) not in have]
        import time
        stop = time.time() + self.budget_s if self.budget_s else None
        best, best_v = None, None
        for p in plays:
            if stop is not None and best is not None and time.time() > stop:
                break
            node = apply_play(state, p)
            if node is None:
                continue
            v = self.value(node)
            # spend a token only for a real gain: ties go to the play with fewer actions
            v += sum(a.kind != 'end_turn' for a in p.actions) * 1e-6
            if best_v is None or v < best_v:
                best, best_v = p, v
        return best


def choose_arrows(state, passes=2):
    """Setup arrows for a placed defence: start from each defender facing its man, then (coordinate
    descent) turn one defender at a time to the facing that leaves the offence the lowest value under the
    solver's evaluation. Squares are not changed."""
    from .solver import Evaluator
    from .solver_config import with_config
    ev = Evaluator(with_config(eval_turns=1))
    arrows = list(state.arrows)
    best = ev(state)[0].ev
    for _ in range(passes):
        changed = False
        for j in range(5):
            for d in range(8):
                if d == arrows[j]:
                    continue
                trial = arrows[:j] + [d] + arrows[j + 1:]
                v = ev(state.with_(arrows=tuple(trial)))[0].ev
                if v < best - 1e-9:
                    best, arrows, changed = v, trial, True
        if not changed:
            break
    return arrows
