"""Step 3n Part E: calibrate the accuracy constant k. Each level plays 12 possessions against All-Star (6 on offence,
6 on defence; the search in JavaScript), its own turn groups are graded by the trainer (the All-Star search), and k is
chosen so the possession accuracies average about 90 (All-Star), 75 (Starter) and 55 (Rookie).

  python3 tools/accuracy_3n.py out.json [--n 12] [--scale 0.25] [--workers 2]
"""
import argparse
import json
import math
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET = dict(allstar=90.0, starter=75.0, rookie=55.0)
_ENG = None


def _job(args):
    global _ENG
    from playmaker_engine import jsbridge, selfplay, trainer as TR
    if _ENG is None:
        _ENG = jsbridge.NodeEngine().install()
    level, k, scale = args
    off, dfn = selfplay.TEAMS6[k % len(selfplay.TEAMS6)], selfplay.TEAMS6[(k + 3) % len(selfplay.TEAMS6)]
    side = 'O' if k % 2 == 0 else 'X'
    levels = (level, 'allstar') if side == 'O' else ('allstar', level)
    try:
        r = selfplay.possession(off, dfn, levels, 500 + k, scale, keep=True)
        out = []
        for _, s, acts in TR.turn_groups(r['triples'], side):
            if s.stage not in ('play', 'reaction'):
                continue
            res = TR.root_turns(s)
            g = TR.grade_group(s, acts, results=res)
            out.append((g['loss'], g['volatility']))
        return dict(level=level, k=k, side=side, decisions=out, score=r['score'])
    except Exception as e:
        return dict(level=level, k=k, error=repr(e))


def calibrate(rows):
    from playmaker_engine.trainer import accuracy
    best = None
    for k10 in range(5, 401, 5):
        kk = k10 / 10.0
        avgs = {}
        for lv in TARGET:
            accs = [accuracy([l for l, _ in r['decisions']], k=kk, weights=[w for _, w in r['decisions']])
                    for r in rows if r.get('level') == lv and r.get('decisions')]
            avgs[lv] = sum(accs) / len(accs) if accs else None
        if any(v is None for v in avgs.values()):
            continue
        err = sum((avgs[lv] - TARGET[lv]) ** 2 for lv in TARGET)
        if best is None or err < best[0]:
            best = (err, kk, avgs)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('--n', type=int, default=12)
    ap.add_argument('--scale', type=float, default=0.25)
    ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    rows = json.load(open(a.out))['rows'] if os.path.exists(a.out) else []
    done = {(r['level'], r['k']) for r in rows}
    jobs = [(lv, k, a.scale) for lv in TARGET for k in range(a.n) if (lv, k) not in done]
    t0 = time.time()
    with Pool(a.workers) as pool:
        for r in pool.imap_unordered(_job, jobs):
            rows.append(r)
            json.dump(dict(rows=rows), open(a.out, 'w'))
            print(r.get('level'), r.get('k'), len(r.get('decisions', [])), r.get('error', ''), round(time.time() - t0), flush=True)
    best = calibrate(rows)
    per = {lv: round(sum(math.exp(-l / best[1]) * 100 for r in rows if r.get('level') == lv for l, _ in r.get('decisions', [])) /
                     max(1, sum(len(r.get('decisions', [])) for r in rows if r.get('level') == lv)), 1) for lv in TARGET}
    rep = dict(k=best[1], possession_accuracy={lv: round(v, 1) for lv, v in best[2].items()}, decision_accuracy=per,
               targets=TARGET, decisions={lv: sum(len(r.get('decisions', [])) for r in rows if r.get('level') == lv) for lv in TARGET})
    print(json.dumps(rep, indent=1))
    json.dump(dict(rows=rows, report=rep), open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
