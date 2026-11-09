"""Head-to-head calibration of the computer levels (step 3e, revised).

Each offence level plays each defence level from the same starts with the same seeds. A possession is
scored as the game scores it (shot quality, bonuses, turnovers: score(final).total); the d20 rolls for
steals, intercepts and fouls are drawn from the seed. No judge search, so it runs at play speed.

While playing it also records, for the defence: each moved defender's arrow job at the end of its turn,
the comfort line's share of its choices, and at every declared shot whether the reaction could still
change the contest, and whether the contest ended clean, with a foul roll, or not at all.
"""
import json
import math
import os
import random
import time
from concurrent.futures import ProcessPoolExecutor

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docs', 'runs', 'solver')
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']
LEVELS = ('rookie', 'starter', 'allstar')


def starts(random_n=20):
    from .cards import PRESCRIBED
    from .scenarios import SCENARIOS
    rng = random.Random(99)
    out = [['card', n] for n in sorted(SCENARIOS)]
    for _ in range(random_n):
        a, b = rng.sample(PRESCRIBED, 2)
        out.append(['teams', [a, b]])
    return out


def start_state(spec):
    from .scenarios import scenario_state, game_state
    kind, v = spec
    if kind == 'card':
        return scenario_state(v)
    if kind == 'state':                      # an explicit start: [off, dfn, o squares, x squares, arrows]
        return game_state(v[0], v[1], v[2], v[3], v[4])
    return game_state(v[0], v[1], TABLE_O, TABLE_X, TABLE_ARROWS)


def play_one(o_level, x_level, spec, seed, overrides=None, budget_s=None, record=True):
    from . import board as B
    from .actions import legal_actions, MOVEMENT
    from .computer import Computer, BUDGET, reachable_contest, reaction_budget
    from .defence import arrow_job
    from .resolve import apply, ChanceNode, sample
    from .scoring import score, contest_options
    if budget_s is not None:
        BUDGET['active'] = budget_s
    ov = overrides or {}
    pols = {'O': Computer('O', o_level, seed=seed, overrides=ov.get('O', {}).get(o_level)),
            'X': Computer('X', x_level, seed=seed, overrides=ov.get('X', {}).get(x_level))}
    rng = random.Random(seed * 1009 + 7)
    s = start_state(spec)
    jobs = {}
    react = dict(shots=0, no_tokens=0, no_change=0, clean=0, foul=0, none=0)
    shot = None                              # the offence's shot: clock when declared, contestable or not
    moved = {}
    t0 = time.time()
    for _ in range(300):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        a = pols[side].choose(s)
        if record and s.stage == 'contest':
            opts = {o.defender: o for o in contest_options(s, s.ball, s.shot, s.forced)}
            o = opts.get(a.piece)
            react['clean' if (o and a.piece >= 0 and o.clean) else 'foul' if a.piece >= 0 else 'none'] += 1
        node = apply(s, a)
        nxt = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
        if record:
            if a.side == 'X' and a.kind in MOVEMENT:
                moved[a.piece] = s.stage
            if moved and a.side == 'X' and (nxt.stage != s.stage or nxt.side != 'X' or nxt.stage == 'over'):
                ref = s if nxt.stage == 'over' else nxt
                for j, stg in moved.items():
                    if stg == 'reaction' or B.on_board(ref.o[ref.ball]):
                        k = f'{stg}:{arrow_job(ref, j)}'
                        jobs[k] = jobs.get(k, 0) + 1
                moved = {}
            if s.stage != 'reaction' and nxt.stage == 'reaction':
                react['shots'] += 1
                if reaction_budget(nxt) == 0:
                    react['no_tokens'] += 1
                else:
                    now = reachable_contest(nxt, budget=0)
                    later = reachable_contest(nxt)
                    if (now[0]['value'] if now else None) == (later[0]['value'] if later else None):
                        react['no_change'] += 1
        if shot is None and s.stage == 'play' and s.side == 'O' and not isinstance(nxt, ChanceNode) \
                and nxt.stage in ('reaction', 'contest') and nxt.shot:
            shot = dict(clock=nxt.clock, contested=bool(reachable_contest(nxt, nxt.ball, nxt.shot)))
        s = nxt
    st = pols['X'].stats
    return dict(o=o_level, x=x_level, spec=spec, seed=seed, points=float(score(s).total) if s.stage == 'over' else None,
                jobs=jobs, react=react, comfort=st['comfort_decided'], x_decisions=st['decisions'],
                think_max=max(max(p.stats['seconds'] or [0]) for p in pols.values()),
                habits={k: p.habits for k, p in pols.items()}, shot=shot, wall=round(time.time() - t0, 2))


def _job(args):
    return play_one(*args)


def run(pairs=None, seeds=(1, 2, 3), random_n=20, workers=2, store='headtohead.json', overrides=None,
        budget_s=1.0, starts_list=None):
    pairs = pairs or [(o, x) for o in LEVELS for x in LEVELS]
    jobs = [(o, x, sp, sd, overrides, budget_s) for sp in (starts_list or starts(random_n)) for sd in seeds
            for o, x in pairs]
    t0 = time.time()
    rows = []
    path = os.path.join(RESULTS, store)
    with ProcessPoolExecutor(workers) as ex:
        for r in ex.map(_job, jobs, chunksize=2):
            rows.append(r)
            if len(rows) % 20 == 0 or len(rows) == len(jobs):
                with open(path, 'w') as f:
                    json.dump(dict(rows=rows, seconds=round(time.time() - t0, 1), overrides=overrides,
                                   budget_s=budget_s), f)
    return rows, time.time() - t0


def mean_ci(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (n - 1)) if n > 1 else 0.0
    return m, 1.96 * sd / math.sqrt(n), n


def matrix(rows):
    out = {}
    for r in rows:
        if r['points'] is not None:
            out.setdefault((r['o'], r['x']), []).append(r['points'])
    return {k: mean_ci(v) for k, v in out.items()}


def paired_diff(rows, a, b):
    """Mean difference (pairing a minus pairing b) over the same start and seed, with a 95% interval."""
    by = {}
    for r in rows:
        by.setdefault((r['o'], r['x']), {})[(json.dumps(r['spec']), r['seed'])] = r['points']
    keys = set(by.get(a, {})) & set(by.get(b, {}))
    d = [by[a][k] - by[b][k] for k in keys if by[a][k] is not None and by[b][k] is not None]
    return mean_ci(d) if len(d) > 1 else (0.0, 0.0, len(d))


def reaction_summary(rows, o_level='allstar'):
    out = {}
    for r in rows:
        if r['o'] != o_level:
            continue
        d = out.setdefault(r['x'], dict(shots=0, no_tokens=0, no_change=0, clean=0, foul=0, none=0,
                                        comfort=0, x_decisions=0, jobs={}))
        for k, v in r['react'].items():
            d[k] += v
        d['comfort'] += r['comfort']
        d['x_decisions'] += r['x_decisions']
        for k, v in r['jobs'].items():
            d['jobs'][k] = d['jobs'].get(k, 0) + v
    return out


def shot_summary(rows):
    """Per offence level: shots declared, the share at the first phase (clock 12), the share contested,
    and the mean clock when the shot went up."""
    out = {}
    for r in rows:
        d = out.setdefault(r['o'], dict(n=0, shots=0, first=0, contested=0, first_contested=0, clock=0))
        d['n'] += 1
        sh = r.get('shot')
        if not sh:
            continue
        d['shots'] += 1
        d['clock'] += sh['clock']
        d['first'] += sh['clock'] >= 12
        d['contested'] += sh['contested']
        d['first_contested'] += sh['clock'] >= 12 and sh['contested']
    for d in out.values():
        k = max(1, d['shots'])
        d.update(first=round(d['first'] / k, 2), contested=round(d['contested'] / k, 2),
                 first_contested=round(d['first_contested'] / k, 2), clock=round(d['clock'] / k, 1))
    return out
