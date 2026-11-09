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


def possession(off, dfn, levels, seed, scale, setup_budget=0.3, digital=True, levels_key=None, team_fouls=0,
               quarter_left=0, keep=False):
    """One possession between two agents (digital by default; step 3n: either format, the defence's team fouls and
    possessions left in the quarter, the age and standard's phase table). Returns dict(keys, score, snapshots, events)."""
    from . import agent as AG
    from .actions import legal_actions
    AG.SCALE['value'] = scale
    rules = RC.with_rules(digital=digital)

    def make(o, x, a, b):
        st = game_state(off, dfn, o, x, a, ball=b, rules=rules, check=False, team_fouls=team_fouls,
                        quarter_left=quarter_left)
        if levels_key:
            st.ctx.levels_key = tuple(levels_key)
        return st
    rng = random.Random(seed)
    po = AG.propose_offence(make, seed, budget=setup_budget, level=levels[0])
    pd = AG.propose_defence(make, po['squares'], po['ball'], seed + 1, budget=setup_budget, level=levels[1])
    s = make([B.sq(q) for q in po['squares']], [B.sq(q) for q in pd['squares']], pd['arrows'], po['ball'])
    agents = {'O': AG.Agent('O', levels[0], seed=seed), 'X': AG.Agent('X', levels[1], seed=seed + 7)}
    keys, snaps, events, triples, geo = [], [], [], [], []
    for _ in range(400):
        if s.stage == 'over':
            break
        side = actor(s)
        if side == 'O' and s.stage == 'play' and s.turn_n == 0:
            keys.append(coarse_key(s))
            snaps.append(s.encode())
            geo.append(positions(s))
        a = agents[side].choose(s)
        node = apply(s, a)
        rolled = None
        if isinstance(node, ChanceNode):
            nxt, label = sample(node, rng)
        else:
            nxt, label = node, None
        extra = {}
        if a.kind == 'steal':
            # step 3n F5: where the reach came from, and the team fouls at the time
            dp, cp = s.x[a.piece], s.o[s.ball]
            front = B.dist_rim(dp) < B.dist_rim(cp)
            moved = bool((s.moved_x | s.qs_x) >> a.piece & 1)
            extra = dict(reach='front, after moving' if front and moved else 'front, from a standstill' if front
                         else 'level or behind', team_fouls=s.ctx.team_fouls + s.fouls)
        if side == 'X' and s.pending and s.turn_n == 0 and s.stage == 'play':
            # a pass in the air: could the defence Intercept, and did it
            acts = legal_actions(s)
            extra = dict(pass_answer=True, intercepts=sum(1 for b in acts if b.kind == 'intercept'),
                         jumps=sum(1 for b in acts if b.kind in ('move', 'qs', 'sprint') and
                                   __import__('playmaker_engine.actions', fromlist=['is_approach']).is_approach(s, b)))
        events.append(dict(extra, locks=bin(s.lock_o).count('1') + bin(s.lock_x).count('1'), fouls=s.fouls, state=s.encode(), action=str(a), kind=a.kind, side=a.side, piece=a.piece,
                           clock=s.clock, phase=s.phase, roll=label, o=[B.sq(q) for q in s.o],
                           x=[B.sq(q) for q in s.x], ball=s.ball,
                           shot=dict(contest=nxt.result.contest, points=nxt.result.points, kind=nxt.result.kind,
                                     contester=nxt.result.contester)
                           if not isinstance(nxt, ChanceNode) and nxt.stage == 'over' and nxt.result else None))
        triples.append((s, a, nxt))
        s = nxt
    from .scoring import score
    from .labels import recognise, unnamed
    sc = score(s).total if s.stage == 'over' else 0
    try:
        labs = recognise(triples)
        un = unnamed(triples, labs)
    except Exception as e:                                  # reported, never hidden
        labs, un = [], [dict(label='recogniser error', text=repr(e))]
    if keep:
        return dict(triples=triples, score=sc, seed=seed)
    return dict(off=off, dfn=dfn, seed=seed, keys=keys, score=sc, result=s.result.kind if s.result else None,
                fouls=s.fouls, tos=s.tos, end_phase=s.phase, team_fouls=team_fouls, quarter_left=quarter_left,
                locks_max=max((e.get('locks', 0) for e in events), default=0),
                snapshots=snaps, events=events, geometry=geo, labels=[l['label'] for l in labs], unnamed=un,
                decisions=[n for ag in agents.values() for n in ag.notes if n.get('event') == 'decision'])


def positions(s):
    """Franks-style geometry at an offence decision: the on-ball defender (nearest the ball) against the ball-rim
    line, and each help defender's depth (0 = at the rim, 1 = at his man) and shading toward the ball. A defender's
    man is the attacker nearest him (each attacker once)."""
    import math
    rim = RC.RIM
    bp = s.o[s.ball]
    onb = min(range(5), key=lambda j: (B.cheb(s.x[j], bp), j))
    out = {}
    vx, vy = bp[0] - rim[0], bp[1] - rim[1]
    L = math.hypot(vx, vy) or 1.0
    q = s.x[onb]
    t = ((q[0] - rim[0]) * vx + (q[1] - rim[1]) * vy) / (L * L)
    off = abs((q[0] - rim[0]) * vy - (q[1] - rim[1]) * vx) / L
    out['onball'] = dict(t=round(t, 3), off_line=round(off, 3), on_line=off <= 0.5 and 0 < t < 1)
    taken = {s.ball}
    helps = []
    for j in sorted(range(5), key=lambda j: B.cheb(s.x[j], bp)):
        if j == onb:
            continue
        man = min((i for i in range(5) if i not in taken), key=lambda i: (B.cheb(s.x[j], s.o[i]), i), default=None)
        if man is None:
            continue
        taken.add(man)
        m = s.o[man]
        mx, my = m[0] - rim[0], m[1] - rim[1]
        Lm = math.hypot(mx, my) or 1.0
        p = s.x[j]
        depth = ((p[0] - rim[0]) * mx + (p[1] - rim[1]) * my) / (Lm * Lm)
        cross = ((p[0] - rim[0]) * my - (p[1] - rim[1]) * mx) / Lm
        ball_side = ((bp[0] - rim[0]) * my - (bp[1] - rim[1]) * mx)
        shade = cross * (1 if ball_side < 0 else -1) * -1
        helps.append(dict(depth=round(depth, 3), shade=round(shade, 3)))
    out['help'] = helps
    return out


def aggregate(rows):
    """The aggregate check (B9) against REFERENCE_real_basketball_targets.md: averages over the possessions."""
    import statistics as st
    from collections import Counter
    ok = [r for r in rows if 'error' not in r]
    geo = [g for r in ok for g in r['geometry']]
    helps = [h for g in geo for h in g['help']]
    onb = [g['onball'] for g in geo]
    shots = [(e['phase'], e['shot']) for r in ok for e in r['events'] if e['shot']]
    by_phase = {}
    for ph, sh in shots:
        d = by_phase.setdefault(ph, dict(n=0, tight=0, points=0))
        d['n'] += 1
        d['tight'] += 1 if sh['contester'] >= 0 and sh['contest'] >= 3 else 0
    ppp = {}
    for r in ok:
        ph = r['events'][-1]['phase'] if r['events'] else 0
        ppp.setdefault(ph, []).append(r['score'])
    ev = [e for r in ok for e in r['events']]
    steals = [e for e in ev if e['kind'] == 'steal']
    ints = [e for e in ev if e['kind'] == 'intercept']
    dribbles = [e for e in ev if e['kind'] == 'dribble']
    lab = Counter(l for r in ok for l in r['labels'])
    un = [dict(seed=r['seed'], off=r['off'], dfn=r['dfn'], **u) for r in ok for u in r['unnamed']]
    return dict(
        possessions=len(ok), errors=len(rows) - len(ok),
        points_per_possession=round(st.mean(r['score'] for r in ok), 2) if ok else None,
        help_depth=round(st.mean(h['depth'] for h in helps), 3) if helps else None,
        help_shade=round(st.mean(h['shade'] for h in helps), 3) if helps else None,
        onball_on_line=round(sum(o['on_line'] for o in onb) / len(onb), 3) if onb else None,
        onball_depth=round(st.mean(o['t'] for o in onb), 3) if onb else None,
        drive_success=round(sum('success' in (e['roll'] or '') for e in dribbles) / len(dribbles), 3) if dribbles else None,
        dribbles=len(dribbles),
        tight_by_phase={ph: round(d['tight'] / d['n'], 3) for ph, d in sorted(by_phase.items())},
        shots_by_phase={ph: d['n'] for ph, d in sorted(by_phase.items())},
        points_by_end_phase={ph: round(st.mean(v), 1) for ph, v in sorted(ppp.items())},
        steal_attempts=len(steals), steal_success=sum((e['roll'] or '').endswith('stolen') for e in steals),
        intercept_attempts=len(ints), intercept_success=sum('failure' in (e['roll'] or '') for e in ints),
        turnovers_per_possession=round(sum(r['result'] in ('turnover_end', 'steal') for r in ok) / len(ok), 3) if ok else None,
        labels=dict(lab.most_common()), unnamed=un)


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
    if a.what == 'aggregate':
        rep = aggregate(rows)
        print(json.dumps({k: v for k, v in rep.items() if k != 'unnamed'}, indent=1))
        print('unnamed actions:', len(rep['unnamed']))
        if a.store:
            json.dump(rep, open(a.store.replace('.json', '_report.json'), 'w'), indent=1)
    if a.what == 'seed':
        V = write_table([r for r in rows if 'error' not in r])
        print('phase means', {k: v for k, v in V.items() if k.startswith('_phase')})


if __name__ == '__main__':
    main()
