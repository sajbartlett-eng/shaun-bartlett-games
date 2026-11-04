"""Random-vs-random soak with invariants checked after every apply."""
import math
import os
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from . import board as B
from . import rules_config as RC
from .actions import TOKEN_FREE
from .policies import RandomPolicy, play
from .scenarios import SCENARIOS, scenario_state, game_state
from .state import CI


class InvariantError(AssertionError):
    pass


def check_invariants(before, action, after):
    """Raise InvariantError if a transition breaks a structural rule."""
    def fail(msg):
        raise InvariantError(f'{msg}\n  action: {action}\n  before: {before.encode()}\n  after:  {after.encode()}')

    allp = list(after.o) + list(after.x)
    if len(set(allp)) != len(allp):
        fail('shared square')
    for i, p in enumerate(after.x):
        if not B.on_board(p):
            fail(f'X{i + 1} off the board')
    for i, p in enumerate(after.o):
        if not B.on_board(p) and not (i == after.ctx.inbounder and p == before.o[i]):
            fail(f'O{i + 1} off the board')
    if after.clock < 0:
        fail('negative clock')
    if not (0 <= after.tok_o <= RC.TOKENS_PER_PHASE and 0 <= after.tok_x <= RC.TOKENS_PER_PHASE):
        fail('token pool out of range')
    for side in ('O', 'X'):
        for kind, lim in RC.LIMITS[side].items():
            if after.count(side, kind) > lim:
                fail(f'{side} {kind} limit exceeded')
    # tokens conserved: within a phase, a token action moves exactly one token out of the pool
    same_phase = after.phase == before.phase and after.stage != 'over'
    if same_phase and action.kind not in TOKEN_FREE:
        spent = (before.tok_o - after.tok_o) if action.side == 'O' else (before.tok_x - after.tok_x)
        other = (before.tok_x - after.tok_x) if action.side == 'O' else (before.tok_o - after.tok_o)
        if spent != 1 or other != 0:
            fail('token not conserved')
    if same_phase and action.kind == 'end_turn' and (before.tok_o, before.tok_x) != (after.tok_o, after.tok_x):
        fail('end_turn spent a token')
    if after.phase != before.phase and after.stage != 'over':
        if (after.tok_o, after.tok_x) != (RC.TOKENS_PER_PHASE,) * 2:
            fail('reset did not refill the pools')
        if after.lock_o or after.lock_x:
            fail('reset did not clear locks')
    # locked players never Move or Sprint
    if action.kind in ('move', 'sprint') and before.locked(action.side, action.piece):
        fail('locked player moved')
    # a Move is once per player per phase
    if action.kind in ('move', 'sprint') and before.moved(action.side, action.piece):
        fail('second Move in a phase')
    if after.stage == 'over':
        from .scoring import score
        sc = score(after)
        if not isinstance(sc.total, int) or not math.isfinite(sc.total):
            fail('score not finite')


SETUPS = list(SCENARIOS) + ['game']


def golden_setup():
    return game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'],
                      ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'], ball=0)


def _setup(k):
    return golden_setup() if k == 'game' else scenario_state(k)


def _run(args):
    lo, hi = args
    stats = Counter()
    totals = []
    steps = 0
    for g in range(lo, hi):
        k = SETUPS[g % len(SETUPS)]
        res = play(_setup(k), RandomPolicy(), RandomPolicy(), seed=g, check=check_invariants)
        steps += res['steps']
        r = res['final'].result
        stats[r.kind if r else 'none'] += 1
        totals.append(res['score'].total)
    return stats, totals, steps


def run_soak(games=10000, workers=1):
    chunks = max(1, workers * 8)
    size = math.ceil(games / chunks)
    jobs = [(i, min(games, i + size)) for i in range(0, games, size)]
    stats, totals, steps = Counter(), [], 0
    if workers > 1:
        with ProcessPoolExecutor(workers) as ex:
            outs = list(ex.map(_run, jobs))
    else:
        outs = [_run(j) for j in jobs]
    for st, tt, sp in outs:
        stats += st
        totals += tt
        steps += sp
    ok = len(totals) == games
    mean = sum(totals) / len(totals) if totals else 0
    summary = (f'soak: {len(totals)} games, {steps} applies checked, 0 invariant failures; '
               f'endings {dict(sorted(stats.items()))}; score min {min(totals)} max {max(totals)} mean {mean:.2f}')
    return dict(ok=ok, games=len(totals), steps=steps, endings=dict(stats), summary=summary,
                min=min(totals), max=max(totals), mean=mean)
