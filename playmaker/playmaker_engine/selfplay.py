"""Step 3m: engine self-play, for two jobs only:
  1. seed the coarse value table (B4) by backward induction over the phases (decide.solve_coarse), then refine it
     from stored games;
  2. the aggregate check against REFERENCE_real_basketball_targets.md (B9): a small All-Star v All-Star run.
Never to calibrate ratings or rules.

  python3 -m playmaker_engine.selfplay seed --n 240 --workers 2 --scale 0.25
  python3 -m playmaker_engine.selfplay aggregate --n 100 --workers 2 --cap 3600 --store agg.json
"""
import argparse
import json
import os
import random
import time
from multiprocessing import Pool

from . import board as B
from . import rules_config as RC
from .resolve import apply, ChanceNode, sample
from .scenarios import game_state
from .search import actor
from .decide import coarse_key, solve_coarse, HERE, Read

TEAMS6 = ['Five Out', 'High-Low', 'Twin Towers', 'Pace and Space', 'Iron Wall', 'Bucket Brigade', 'Ball Movement',
          'Run and Gun', 'Shoot and Protect']


def possession(off, dfn, levels, seed, scale, setup_budget=0.3):
    """One digital possession between two agents. Returns dict(keys, score, snapshots, events)."""
    from . import agent as AG
    AG.SCALE['value'] = scale
    rules = RC.with_rules(digital=True)
    make = lambda o, x, a, b: game_state(off, dfn, o, x, a, ball=b, rules=rules, check=False)
    rng = random.Random(seed)
    po = AG.propose_offence(make, seed, budget=setup_budget, level=levels[0])
    pd = AG.propose_defence(make, po['squares'], po['ball'], seed + 1, budget=setup_budget, level=levels[1])
    s = make([B.sq(q) for q in po['squares']], [B.sq(q) for q in pd['squares']], pd['arrows'], po['ball'])
    agents = {'O': AG.Agent('O', levels[0], seed=seed), 'X': AG.Agent('X', levels[1], seed=seed + 7)}
    keys, snaps, events = [], [], []
    for _ in range(400):
        if s.stage == 'over':
            break
        side = actor(s)
        if side == 'O' and s.stage == 'play' and s.turn_n == 0:
            keys.append(coarse_key(s))
            snaps.append(s.encode())
        a = agents[side].choose(s)
        node = apply(s, a)
        rolled = None
        if isinstance(node, ChanceNode):
            nxt, label = sample(node, rng)
        else:
            nxt, label = node, None
        events.append(dict(state=s.encode(), action=str(a), kind=a.kind, side=a.side, piece=a.piece,
                           clock=s.clock, phase=s.phase, roll=label, o=[B.sq(q) for q in s.o],
                           x=[B.sq(q) for q in s.x], ball=s.ball,
                           shot=dict(contest=nxt.result.contest, points=nxt.result.points, kind=nxt.result.kind,
                                     contester=nxt.result.contester)
                           if not isinstance(nxt, ChanceNode) and nxt.stage == 'over' and nxt.result else None))
        s = nxt
    from .scoring import score
    sc = score(s).total if s.stage == 'over' else 0
    return dict(off=off, dfn=dfn, seed=seed, keys=keys, score=sc, result=s.result.kind if s.result else None,
                snapshots=snaps, events=events,
                decisions=[n for ag in agents.values() for n in ag.notes if n.get('event') == 'decision'])


def _job(args):
    off, dfn, levels, seed, scale = args
    try:
        return possession(off, dfn, levels, seed, scale)
    except Exception as e:                                   # a crash is reported, never hidden
        return dict(error=repr(e), off=off, dfn=dfn, seed=seed)


def run(n, levels, scale, workers=2, cap=None, store=None, seed0=1):
    jobs = []
    rng = random.Random(seed0)
    for k in range(n):
        off, dfn = rng.sample(TEAMS6, 2)
        jobs.append((off, dfn, levels, seed0 + k, scale))
    rows = []
    if store and os.path.exists(store):
        rows = json.load(open(store))
        jobs = jobs[len(rows):]
    t0 = time.time()
    with Pool(workers) as pool:
        for r in pool.imap(_job, jobs):
            rows.append(r)
            if store:
                json.dump(rows, open(store, 'w'))
            if cap and time.time() - t0 > cap:
                pool.terminate()
                break
    return rows


def write_table(rows, key='senior/pro'):
    recs = [(r['keys'], r['score']) for r in rows if 'keys' in r and r['keys']]
    V = solve_coarse(recs)
    path = os.path.join(HERE, 'data', 'vcoarse.json')
    allt = json.load(open(path)) if os.path.exists(path) else {}
    allt['_about'] = ('Step 3m B4: coarse values (ball zone | defended | phase | offence tokens bucket), solved by '
                      'backward induction over the phases from engine self-play possessions; refine from stored games.')
    allt[key] = V
    allt.setdefault('_sources', {})[key] = dict(possessions=len(recs))
    json.dump(allt, open(path, 'w'), indent=1, sort_keys=True)
    return V


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['seed', 'aggregate'])
    ap.add_argument('--n', type=int, default=100)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--cap', type=float, default=None)
    ap.add_argument('--store', default=None)
    ap.add_argument('--levels', default='starter,starter')
    a = ap.parse_args()
    levels = tuple(a.levels.split(','))
    rows = run(a.n, levels, a.scale, a.workers, a.cap, a.store)
    bad = [r for r in rows if 'error' in r]
    print(f'{len(rows)} possessions, {len(bad)} errors', bad[:3])
    if a.what == 'seed':
        V = write_table([r for r in rows if 'error' not in r])
        print('phase means', {k: v for k, v in V.items() if k.startswith('_phase')})


if __name__ == '__main__':
    main()
