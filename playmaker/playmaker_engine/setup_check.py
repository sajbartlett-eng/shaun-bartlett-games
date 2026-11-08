"""Step 3k short check (research tool): All-Star v All-Star from the computer's own setups, new against current.
  new:     setup.offence_setup + setup.defence_setup
  current: the fixed formation (TABLE_O, the ball on O1) + the step 3e defence placement (computer.place_defence)
For each possession: points, the offence's top goal at setup and whether it was finished (the final shot taken by the
goal's attacker, of the goal's kind), the defence's matchups, the offence's setup (shape and ball handler), and the
setup decision times.
  python3 -m playmaker_engine.setup_check --arm new --pair 0 --n 40 --store out.json"""
import argparse
import json
import random
import time
from collections import Counter

PAIRINGS = [('Five Out', 'High-Low'), ('Twin Towers', 'Pace and Space'), ('Iron Wall', 'Bucket Brigade')]
FINISH = {'three': {'three'}, 'post': {'post', 'layup', 'dunk'}, 'highlow': {'post', 'layup', 'dunk'},
          'iso': {'layup', 'dunk', 'floater', 'mid'}, 'pnr': {'layup', 'dunk', 'floater', 'mid'},
          'handoff': {'three', 'mid', 'long'}}


def play(arm, off, dfn, seed, budget_s):
    from . import board as B
    from . import setup as SU
    from .computer import Computer, BUDGET, place_defence
    from .resolve import apply, ChanceNode, sample
    from .scenarios import game_state
    from .scoring import score
    BUDGET['active'] = budget_s
    pols = {'O': Computer('O', 'allstar', seed=seed), 'X': Computer('X', 'allstar', seed=seed)}
    make = lambda o_sq, ball, xs, ar: game_state(off, dfn, [B.sq(q) for q in o_sq], [B.sq(q) for q in xs], list(ar), ball=ball, check=False)
    t0 = time.time()
    if arm == 'new':
        r = SU.offence_setup(pols['O'], make, seed=seed)
        o_sq, ball, goal, shape = r['squares'], r['ball'], r['goal'], r['shape']
    else:
        o_sq, ball = [B.parse_sq(q) for q in SU.TABLE_O], 0
        gl = SU.goals(TEAMS_(off), TEAMS_(dfn))
        goal, shape = (gl[0] if gl else None), 'fixed (five out)'
    t_off = time.time() - t0
    t0 = time.time()
    build = lambda xs, ar: make(o_sq, ball, xs, ar)
    if arm == 'new':
        d = SU.defence_setup(pols['X'], o_sq, ball, build)
        xs, arrows, perm = d['xs'], d['arrows'], d['perm']
        pols['X'].setup_perm = tuple(perm)
    else:
        xs, arrows, perm = place_defence(pols['X'], o_sq, ball, build)
    t_def = time.time() - t0
    s = make(o_sq, ball, xs, arrows)
    rng = random.Random(seed * 1009 + 7)
    shot = None
    for _ in range(300):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        a = pols[side].choose(s)
        node = apply(s, a)
        nxt = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
        if a.side == 'O' and a.kind in ('shot', 'forced_shot'):
            shot = dict(shooter=a.piece, type=a.shot)
        s = nxt
    pts = float(score(s).total) if s.stage == 'over' else None
    done = bool(goal and shot and shot['shooter'] == goal['att'] and shot['type'] in FINISH[goal['kind']])
    return dict(seed=seed, points=pts, shot=shot, goal=dict(kind=goal['kind'], att=goal['att'] + 1) if goal else None,
                finished=done, shape=shape, ball=ball + 1, squares=[B.sq(q) for q in o_sq],
                matchup=' '.join(f'X{j + 1}>O{perm[j] + 1}' for j in range(5)), t_off=round(t_off, 2), t_def=round(t_def, 2))


def TEAMS_(name):
    from .cards import TEAMS
    return TEAMS[name]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', default='new'); ap.add_argument('--pair', type=int, default=0)
    ap.add_argument('--n', type=int, default=40); ap.add_argument('--budget', type=float, default=2.0)
    ap.add_argument('--store', default=None)
    args = ap.parse_args()
    off, dfn = PAIRINGS[args.pair]
    rows = []
    if args.store:
        try:
            with open(args.store) as f:
                rows = json.load(f)['rows']               # resume a run that was stopped
        except (OSError, ValueError, KeyError):
            rows = []
    t0 = time.time()
    for seed in range(len(rows) + 1, args.n + 1):
        rows.append(play(args.arm, off, dfn, seed, args.budget))
        if args.store:
            with open(args.store, 'w') as f:
                json.dump(dict(arm=args.arm, off=off, dfn=dfn, rows=rows), f, indent=1)
    n = len(rows)
    pts = [r['points'] or 0 for r in rows]
    print(f'{off} v {dfn} [{args.arm}] {n} possessions, {round(time.time() - t0)} s')
    print(f'points: {sum(pts) / n:.1f} a possession; top goal finished: {sum(r["finished"] for r in rows)}/{n}')
    print('setups:', dict(Counter(f"{r['shape']}, ball O{r['ball']}" for r in rows).most_common(4)))
    print('matchups:', dict(Counter(r['matchup'] for r in rows).most_common(3)))
    print(f"setup time: offence max {max(r['t_off'] for r in rows):.2f} s, defence max {max(r['t_def'] for r in rows):.2f} s")


if __name__ == '__main__':
    main()
