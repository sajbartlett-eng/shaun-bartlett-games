"""Step 3n Part A: prove the JavaScript search core gives the Python engine's answers.

Random legal states across ages, standards, formats and phases (random deals, random placements, then random legal
play with the rolls sampled), and for each: the legal actions, every attacker's and defender's reach map (geometric and
the rules' exact reach), each attacker's threat (value, square, route), the best cover (value, the responses chosen and
the residual threats) and the leaf value, with the geometric and the exact read, and the ordering read.

  python3 tools/js_equivalence.py --n 2000 [--seed 1] [--out docs/3n_equivalence.json]
"""
import argparse
import json
import os
import random
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from playmaker_engine import board as B                       # noqa: E402
from playmaker_engine import rules_config as RC               # noqa: E402
from playmaker_engine import levels as L, rosters as R        # noqa: E402
from playmaker_engine.actions import legal_actions            # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode, sample  # noqa: E402
from playmaker_engine.state import Context, GameState         # noqa: E402
from playmaker_engine.decide import Read, attacker_reach, defender_map  # noqa: E402
from playmaker_engine.jsbridge import state_json, ctx_json    # noqa: E402

AGES = ('senior', 'youth', 'junior')
STANDARDS = ('pro', 'semi_pro', 'amateur')


def random_state(rng):
    age, std = rng.choice(AGES), rng.choice(STANDARDS)
    digital = rng.random() < 0.5
    d = R.deal(age, std, seed=rng.randrange(36 ** 6))
    tags = d['tags'] or [None, None]
    off, dfn = L.team(d['rosters'][0], age, tags[0]), L.team(d['rosters'][1], age, tags[1])
    rules = RC.with_rules(digital=digital)
    ctx = Context(off, dfn, rules, team_fouls=rng.randrange(0, 7) if digital else 0,
                  quarter_left=rng.randrange(0, 19) if digital else 0)
    squares = [(x, y) for x in range(B.W) for y in range(1, B.H + 1)]
    # the offence beyond the arc mostly, the defence between them and the rim mostly: positions a game can reach
    pick = rng.sample(squares, 10)
    o, x = tuple(pick[:5]), tuple(pick[5:])
    arrows = tuple(rng.randrange(8) for _ in range(5))
    s = GameState(ctx=ctx, o=o, x=x, arrows=arrows, ball=rng.randrange(5))
    steps = rng.choice((0, 1, 2, 3, 5, 8, 12, 20, 30, 45))
    for _ in range(steps):
        if s.stage == 'over':
            break
        acts = legal_actions(s)
        if not acts:
            break
        a = rng.choice(acts)
        node = apply(s, a)
        if isinstance(node, ChanceNode):
            node, _ = sample(node, rng)
        s = node
    return s, dict(age=age, standard=std, digital=digital, steps=steps)


def py_probe(s):
    mp = lambda m: {B.sq(q): n for q, n in m.items()}
    fx = lambda m: {B.sq(q): {str(a): n for a, n in arrs.items()} for q, arrs in m.items()}
    out = dict(legal=[str(a) for a in legal_actions(s)])
    if s.stage == 'over':
        return out
    out['attacker_reach'] = [mp(attacker_reach(s, i)) for i in range(5)]
    out['defender_reach'] = [[mp(f), fx(x)] for f, x in (defender_map(s, d) for d in range(5))]
    out['defender_exact'] = [[mp(f), fx(x)] for f, x in (defender_map(s, d, exact=True) for d in range(5))]
    if s.stage in ('play', 'reaction'):
        for exact in (False, True):
            r = Read(s, exact=exact)
            cv = r.cover()
            tag = 'exact' if exact else 'geo'
            out['threat_' + tag] = [[r.threat[i]['value'], B.sq(r.threat[i]['sq']) if r.threat[i]['sq'] else None,
                                     r.threat[i]['route']] for i in range(5)]
            out['cover_' + tag] = [cv['value'], sorted([[j, B.sq(resp[0]), resp[1], resp[2]] for j, resp in cv['choice'].items()]),
                                   [cv['residual'][i] for i in range(5)]]
            out['leaf_' + tag] = r.leaf()
        out['quick'] = Read(s, k=0, looks_per=3).leaf()
    return out


def close(a, b, tol=1e-9):
    if isinstance(a, float) or isinstance(b, float):
        return isinstance(a, (int, float)) and isinstance(b, (int, float)) and abs(a - b) <= tol * max(1.0, abs(a))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    return a == b


def run_js(lines):
    p = subprocess.run(['node', os.path.join(HERE, 'js_probe.js')], input='\n'.join(lines) + '\n', capture_output=True,
                       text=True, check=True)
    return [json.loads(ln) for ln in p.stdout.splitlines() if ln.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--n', type=int, default=2000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default=None)
    ap.add_argument('--show', type=int, default=5)
    args = ap.parse_args()
    rng = random.Random(args.seed)
    states, meta, lines = [], [], []
    t0 = time.time()
    while len(states) < args.n:
        s, m = random_state(rng)
        states.append(s)
        meta.append(m)
        lines.append(json.dumps(dict(state=state_json(s), ctx=ctx_json(s.ctx))))
    py = [py_probe(s) for s in states]
    t_py = time.time() - t0
    t1 = time.time()
    js = run_js(lines)
    t_js = time.time() - t1
    fields = ('legal', 'attacker_reach', 'defender_reach', 'defender_exact', 'threat_geo', 'cover_geo', 'leaf_geo',
              'threat_exact', 'cover_exact', 'leaf_exact', 'quick')
    tally = {f: [0, 0] for f in fields}
    bad = []
    stages, phases = {}, {}
    for k, (s, a, b) in enumerate(zip(states, py, js)):
        stages[s.stage] = stages.get(s.stage, 0) + 1
        phases[s.phase] = phases.get(s.phase, 0) + 1
        if 'error' in b:
            bad.append(dict(n=k, field='error', js=b['error'][:400], state=s.encode()))
            continue
        for f in fields:
            if f not in a:
                continue
            tally[f][0] += 1
            if close(a[f], b.get(f)):
                tally[f][1] += 1
            else:
                bad.append(dict(n=k, field=f, state=s.encode(), py=a[f], js=b.get(f)))
    rep = dict(states=len(states), seconds_python=round(t_py, 1), seconds_js=round(t_js, 1),
               by_stage=stages, by_phase=phases,
               by_age={a: sum(1 for m in meta if m['age'] == a) for a in AGES},
               by_standard={a: sum(1 for m in meta if m['standard'] == a) for a in STANDARDS},
               digital=sum(1 for m in meta if m['digital']),
               checks={f: dict(compared=t[0], equal=t[1]) for f, t in tally.items()},
               mismatches=len(bad))
    print(json.dumps(rep, indent=1))
    for b in bad[:args.show]:
        print(json.dumps(b)[:3000])
    if args.out:
        rep['first_mismatches'] = bad[:20]
        json.dump(rep, open(args.out, 'w'), indent=1)
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
