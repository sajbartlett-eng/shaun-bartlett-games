"""Step 3n Part C: rebuild the coarse phase table from the self-play possessions (docs/3n_seed/*.json and, for Senior
Pro, the F5 and aggregate runs) and write playmaker_engine/data/vcoarse.json. Reports V by phase per age and standard,
and, apart from it, the points by the phase a possession ended (a selection effect).

  python3 tools/phase_table_3n.py [extra senior/pro row files...] > docs/3n_phase_table.json
"""
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from playmaker_engine.decide import solve_phase_table, points_by_end_phase   # noqa: E402


def rows_of(path):
    d = json.load(open(path))
    return d['rows'] if isinstance(d, dict) else d


def main():
    by = {}
    for p in sorted(glob.glob(os.path.join(ROOT, 'docs', '3n_seed', '*.json'))):
        age, std = os.path.basename(p)[:-5].split('_', 1)
        by.setdefault(f'{age}/{std}', []).extend(r for r in rows_of(p) if 'keys' in r and r['keys'])
    for p in sys.argv[1:]:
        by.setdefault('senior/pro', []).extend(r for r in rows_of(p) if 'keys' in r and r['keys'] and r.get('format', 'digital') == 'digital')
    path = os.path.join(ROOT, 'playmaker_engine', 'data', 'vcoarse.json')
    allt = json.load(open(path))
    rep = {}
    for key, rows in sorted(by.items()):
        recs = [(r['keys'], r['score']) for r in rows]
        V = solve_phase_table(recs)
        se = {}
        for k in range(1, 7):
            alive = [r['score'] for r in rows if any(int(x.split('|')[2]) == k for x in r['keys'])]
            if len(alive) > 1:
                m = sum(alive) / len(alive)
                se[str(k)] = round(math.sqrt(sum((x - m) ** 2 for x in alive) / (len(alive) - 1) / len(alive)), 2)
        V['_se'] = se
        # like for like: the same mix of positions (ball zone, defended, tokens, capacity) valued at each phase
        from collections import Counter
        shapes = Counter()
        for r in rows:
            for x in r['keys']:
                f = x.split('|')
                shapes['|'.join(f[:2] + f[3:])] += 1
        def look(shape, k):
            f = shape.split('|')
            full = '|'.join(f[:2] + [str(k)] + f[2:])
            short = '|'.join(f[:2] + [str(k)] + f[2:3])
            return V.get(full, V.get(short, V.get(f'_phase{k}', 0.0)))
        tot = sum(shapes.values())
        for k in range(1, 7):
            V[f'_std{k}'] = round(sum(n * look(sh, k) for sh, n in shapes.items()) / tot, 2)
        allt[key] = V
        allt.setdefault('_sources', {})[key] = dict(possessions=len(recs), how='step 3n: alive at the start of the phase')
        ends = points_by_end_phase([(r.get('end_phase') or int(r['keys'][-1].split('|')[2]), r['score']) for r in rows])
        rep[key] = dict(possessions=len(recs), V_by_phase={k: V.get(f'_phase{k}') for k in range(1, 7)},
                        like_for_like={k: V.get(f'_std{k}') for k in range(1, 7)},
                        alive={k: V.get(f'_alive{k}') for k in range(1, 7)}, standard_error=se,
                        points_by_end_phase_selection_effect=ends)
    allt['_about'] = ('Step 3n C: coarse values (ball zone | defended | phase | offence tokens | capacity): the expected final '
                      'value of every possession alive at the start of the phase, by backward induction over the phases, '
                      'from engine self-play (turnovers and expiry included at 0); _phaseK = V_k, _se = its standard error.')
    json.dump(allt, open(path, 'w'), indent=1, sort_keys=True)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    main()
