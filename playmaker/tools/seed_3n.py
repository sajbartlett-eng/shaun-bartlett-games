"""Step 3n Part C (and F5, I): engine self-play possessions on the JavaScript core, for the phase table by age and
standard and for the aggregate checks. Dealt rosters at the age and standard (Senior Pro uses the named teams).

  python3 tools/seed_3n.py --age senior --standard pro --n 60 --levels allstar allstar --scale 0.25 \
      [--format digital|tabletop] --workers 2 --store docs/3n_seed_senior_pro.json [--cap 3600]
"""
import argparse
import json
import os
import random
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ENG = None


def _job(args):
    global _ENG
    from playmaker_engine import jsbridge, selfplay, levels as L, rosters as R, rules_config as RC
    from playmaker_engine.cards import register_cards
    if _ENG is None:
        _ENG = jsbridge.NodeEngine().install()
    age, std, levels, seed, scale, fmt = args
    try:
        if (age, std) == ('senior', 'pro'):
            rng = random.Random(seed)
            off, dfn = rng.sample(selfplay.TEAMS6, 2)
        else:
            d = R.deal(age, std, seed=seed)
            tags = d['tags'] or [None, None]
            off = register_cards(f'seed {age} {std} {seed} A', L.team(d['rosters'][0], age, tags[0]))
            dfn = register_cards(f'seed {age} {std} {seed} B', L.team(d['rosters'][1], age, tags[1]))
        r = selfplay.possession(off, dfn, levels, seed, scale, digital=(fmt == 'digital'), levels_key=(age, std))
        r.update(age=age, standard=std, format=fmt)
        return r
    except Exception as e:
        import traceback
        return dict(error=repr(e), trace=traceback.format_exc()[-1500:], seed=seed, age=age, standard=std)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--age', default='senior')
    ap.add_argument('--standard', default='pro')
    ap.add_argument('--n', type=int, default=60)
    ap.add_argument('--levels', nargs=2, default=['allstar', 'allstar'])
    ap.add_argument('--scale', type=float, default=0.25)
    ap.add_argument('--format', default='digital')
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--store', required=True)
    ap.add_argument('--cap', type=float, default=None)
    ap.add_argument('--seed0', type=int, default=1)
    a = ap.parse_args()
    rows = json.load(open(a.store)) if os.path.exists(a.store) else []
    jobs = [(a.age, a.standard, a.levels, a.seed0 + k, a.scale, a.format) for k in range(len(rows), a.n)]
    t0 = time.time()
    with Pool(a.workers) as pool:
        for r in pool.imap(_job, jobs):
            rows.append(r)
            json.dump(rows, open(a.store, 'w'))
            print(len(rows), r.get('score'), r.get('result'), r.get('error', ''), round(time.time() - t0), flush=True)
            if a.cap and time.time() - t0 > a.cap:
                pool.terminate()
                break


if __name__ == '__main__':
    main()
