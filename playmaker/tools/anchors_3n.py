"""Step 3n Part H: computer anchor ratings from self-play between levels. Rookie v Starter, Starter v All-Star and
Rookie v All-Star; 12 matches of 4 possessions each (2 a side) per pairing at Senior Pro (digital), within a cap.
Each match gives the first level a match score (trainer.match_score); the rating gaps are fitted to the expected
scores (the Glicko-2 / Elo curve) and the anchors are set around Starter's.

  python3 tools/anchors_3n.py out.json [--cap 5400] [--scale 0.25]
"""
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PAIRS = (('rookie', 'starter'), ('starter', 'allstar'), ('rookie', 'allstar'))


def main():
    from playmaker_engine import jsbridge, selfplay, trainer as TR
    out = sys.argv[1]
    cap = float(sys.argv[sys.argv.index('--cap') + 1]) if '--cap' in sys.argv else 5400
    scale = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 0.25
    eng = jsbridge.NodeEngine().install()
    rows = json.load(open(out))['rows'] if os.path.exists(out) else []
    done = {(r['a'], r['b'], r['match']) for r in rows}
    t0 = time.time()
    teams = selfplay.TEAMS6
    for m in range(12):
        for a, b in PAIRS:
            if (a, b, m) in done:
                continue
            if time.time() - t0 > cap:
                break
            ta, tb = teams[m % len(teams)], teams[(m + 4) % len(teams)]
            tot = dict(A=0, B=0)
            for k in range(4):            # A attacks on 0 and 2 with level a; B attacks on 1 and 3 with level b
                if k % 2 == 0:
                    r = selfplay.possession(ta, tb, (a, b), 3000 + 10 * m + k, scale)
                    tot['A'] += r['score']
                else:
                    r = selfplay.possession(tb, ta, (b, a), 3000 + 10 * m + k, scale)
                    tot['B'] += r['score']
            sc = TR.match_score(tot['A'], tot['B'], 2)
            rows.append(dict(a=a, b=b, match=m, totals=tot, score_a=sc))
            json.dump(dict(rows=rows), open(out, 'w'), indent=1)
            print(a, b, m, tot, round(sc, 3), round(time.time() - t0), flush=True)
    eng.close()
    rep = fit(rows)
    print(json.dumps(rep, indent=1))
    json.dump(dict(rows=rows, report=rep), open(out, 'w'), indent=1)


def fit(rows):
    gap = {}
    for a, b in PAIRS:
        xs = [r['score_a'] for r in rows if (r['a'], r['b']) == (a, b)]
        if not xs:
            continue
        e = min(0.97, max(0.03, sum(xs) / len(xs)))
        gap[(a, b)] = dict(matches=len(xs), score=round(sum(xs) / len(xs), 3), gap=round(-400 * math.log10(1 / e - 1), 1))
    # least squares for r_rookie, r_starter, r_allstar with r_starter fixed: gaps g_ab = r_a - r_b
    import itertools
    best = None
    for dr in range(-600, 1, 5):              # rookie - starter
        for da in range(0, 601, 5):           # allstar - starter
            r = dict(rookie=dr, starter=0, allstar=da)
            err = sum((r[a] - r[b] - g['gap']) ** 2 for (a, b), g in gap.items())
            if best is None or err < best[0]:
                best = (err, r)
    base = 1600
    anchors = {lv: base + d for lv, d in best[1].items()}
    return dict(pairings={f'{a} v {b}': g for (a, b), g in gap.items()}, senior_anchors=anchors)


if __name__ == '__main__':
    main()
