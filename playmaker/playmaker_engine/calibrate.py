"""Calibrate the computer levels (step 3e, section 8.4).

A level's measure is the value it gives up per possession against the solver, by the review's logic: at
each of its decisions, the gap between the solver's value of its preferred action and of the action the
computer chose (the solver's values are estimates from a short search), summed per possession.
"""
import json
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solver_results')
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def starts(random_n=20):
    from .cards import PRESCRIBED
    from .scenarios import SCENARIOS
    rng = random.Random(99)
    out = [('card', n) for n in sorted(SCENARIOS)]
    for _ in range(random_n):
        a, b = rng.sample(PRESCRIBED, 2)
        out.append(('teams', (a, b)))
    return out


def start_state(spec):
    from .scenarios import scenario_state, game_state
    kind, v = spec
    return scenario_state(v) if kind == 'card' else game_state(v[0], v[1], TABLE_O, TABLE_X, TABLE_ARROWS)


def solver_gap(state, a, budget_s):
    """The solver's estimate (a fixed depth-2 search over its candidate plays) of how much choosing `a`
    gives up at `state` (0 if it agrees, or if `a` scores at least as well)."""
    from .solver import Searcher, expected
    from .solver_config import with_config
    from .resolve import apply
    se = Searcher(with_config(eval_turns=1, top_k_raw=0, endgame_tokens=-1))
    depth = 2                                   # fixed depth: the judge is the same at every decision
    se.root_depth = depth
    se.value(state, depth)
    e = se.tt.get((state, depth))
    if e is None or not e.children:
        return 0.0
    maximise = (state.side == 'O' and state.stage != 'reaction') or state.stage in ('target', 'pick', 'forced')
    vals = [(p, v[0].ev) for p, v in e.children]
    best = max(v for _, v in vals) if maximise else min(v for _, v in vals)
    mine = [v for p, v in vals if p.actions[0] == a]
    cv = mine[0] if mine else expected(apply(state, a), se.ev)[0].ev
    gap = (best - cv) if maximise else (cv - best)
    return max(0.0, gap)


def _job(job):
    from .computer import Computer, BUDGET
    from .resolve import apply, ChanceNode, sample
    from .actions import legal_actions
    o_level, x_level, spec, seed, review_s, overrides = job
    BUDGET['active'] = BUDGET['server']
    st = start_state(spec)
    pols = {'O': Computer('O', o_level, seed=seed, overrides=(overrides or {}).get('O')),
            'X': Computer('X', x_level, seed=seed, overrides=(overrides or {}).get('X'))}
    rng = random.Random(seed)
    gaps = {'O': 0.0, 'X': 0.0}
    n = {'O': 0, 'X': 0}
    t0 = time.time()
    s = st
    for _ in range(200):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        acts = legal_actions(s)
        a = pols[side].choose(s)
        if review_s and len(acts) > 1 and s.stage != 'target':
            gaps[side] += solver_gap(s, a, review_s)
            n[side] += 1
        node = apply(s, a)
        s = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
    from .scoring import score
    secs = {k: p.stats['seconds'] for k, p in pols.items()}
    return dict(o=o_level, x=x_level, spec=list(spec) if spec[0] == 'card' else [spec[0], list(spec[1])], seed=seed,
                score=float(score(s).total) if s.stage == 'over' else None, gap=gaps, decisions=n,
                think_max={k: max(v) if v else 0 for k, v in secs.items()},
                think_mean={k: sum(v) / len(v) if v else 0 for k, v in secs.items()},
                comfort_decided=pols['X'].stats['comfort_decided'], x_decisions=pols['X'].stats['decisions'],
                habits={k: p.habits for k, p in pols.items()}, wall=round(time.time() - t0, 1))


def run(store='calibration.json', levels=('rookie', 'starter', 'allstar'), seeds=(1, 2), review_s=0.5,
        workers=2, cross=False, overrides=None, random_n=20):
    jobs = []
    for sp in starts(random_n):
        for sd in seeds:
            for lv in levels:
                jobs.append((lv, lv, sp, sd, review_s, overrides))
            if cross:
                for o in levels:
                    for x in levels:
                        if o != x:
                            jobs.append((o, x, sp, sd, 0, overrides))
    path = os.path.join(RESULTS, store)
    rows = []
    with ProcessPoolExecutor(workers) as ex:
        for r in ex.map(_job, jobs):
            rows.append(r)
            with open(path, 'w') as f:
                json.dump(rows, f, indent=0)
    return rows


def summary(rows):
    out = {}
    for r in rows:
        if r['o'] != r['x']:
            continue
        lv = r['o']
        d = out.setdefault(lv, dict(n=0, O=0.0, X=0.0, score=0.0, think_max=0.0, comfort=0, xdec=0))
        d['n'] += 1
        d['O'] += r['gap']['O']
        d['X'] += r['gap']['X']
        d['score'] += r['score'] or 0
        d['think_max'] = max(d['think_max'], r['think_max']['O'], r['think_max']['X'])
        d['comfort'] += r['comfort_decided']
        d['xdec'] += r['x_decisions']
    for lv, d in out.items():
        n = d['n']
        d.update(O=round(d['O'] / n, 2), X=round(d['X'] / n, 2), score=round(d['score'] / n, 2))
    return out


def cross_table(rows):
    t = {}
    for r in rows:
        t.setdefault((r['o'], r['x']), []).append(r['score'] or 0)
    return {f'{o} offence v {x} defence': round(sum(v) / len(v), 2) for (o, x), v in t.items()}
