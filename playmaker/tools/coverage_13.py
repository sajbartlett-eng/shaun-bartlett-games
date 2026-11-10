"""Step 13 B1: the allocation methods compared on the exam's boards. For every exam decision (boards 1 to 16, every
copy, and C2) and every position one action later: the exact linear program (the one built, decide.Read.budget) and a
greedy allocation, from the same tables; each one's value and time, and the greedy's gap above the exact.

The greedy: take the offence's best look; give it the answer that lowers it most, as much as is needed to bring it
down to the next look or as much as the defender, the look and the movement actions have left; repeat until the best
look can't be lowered. Every step keeps within the same limits as the exact method, so its answer is one the defence
could really choose: it can never be below the exact value, only equal or above (the gap).

  python3 tools/coverage_13.py out.json
"""
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from playmaker_engine import exam as EX                                   # noqa: E402
from playmaker_engine.decide import CONFIG, Read                          # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode                    # noqa: E402
from playmaker_engine.search import candidate_actions                     # noqa: E402


def greedy(looks, cols, movers):
    v = [o for _, _, o in looks]
    look_left = [1.0] * len(looks)
    man_left = {}
    for _ in range(200):
        top = max(range(len(v)), key=lambda l: (v[l], -l)) if v else None
        if top is None:
            break
        best = None
        for k, (j, i, kind, falls) in enumerate(cols):
            f = falls.get(top, 0.0)
            room = min([man_left.get(j, 1.0)] + [look_left[l] for l in falls] + ([movers] if kind == 'move' else []))
            if f > 1e-9 and room > 1e-9 and (best is None or f > best[0]):
                best = (f, k, room)
        if best is None:
            break
        f, k, room = best
        j, i, kind, falls = cols[k]
        nxt = max((x for l, x in enumerate(v) if x < v[top] - 1e-9), default=0.0)
        share = min(room, (v[top] - nxt) / f)
        if share <= 1e-9:
            break
        for l, fl in falls.items():
            v[l] -= share * fl
            look_left[l] -= share
        man_left[j] = man_left.get(j, 1.0) - share
        if kind == 'move':
            movers -= share
    return max(v, default=0.0)


def main(out):
    CONFIG['eval']['coverage_budget'] = True
    states = []
    for n in range(1, 17):
        _, b, _ = EX.POSITIONS[n - 1]()
        states += list(b.values()) if isinstance(b, dict) else [b]
    states.append(EX.c2()[1])
    more = []
    for s in states:
        for a in candidate_actions(s):
            nxt = apply(s, a)
            if not isinstance(nxt, ChanceNode) and nxt.stage == 'play' and not nxt.pending:
                more.append(nxt)
    rows = []
    for k, s in enumerate(states + more):
        r = Read(s)
        looks, cols = r.budget_tables()
        t0 = time.perf_counter()
        exact = r.budget()['value']
        t1 = time.perf_counter()
        g = greedy(looks, cols, float(min(2, s.tok_x)))
        t2 = time.perf_counter()
        rows.append(dict(exam_decision=k < len(states), looks=len(looks), answers=len(cols), exact=exact, greedy=g,
                         old=max(r.cover()['residual'].values(), default=0.0),
                         ms_exact=1000 * (t1 - t0), ms_greedy=1000 * (t2 - t1)))
    gaps = [r['greedy'] - r['exact'] for r in rows]
    rep = dict(positions=len(rows), exam_decisions=len(states),
               greedy_never_below_exact=all(g > -1e-9 for g in gaps),
               greedy_equal=sum(1 for g in gaps if g <= 1e-9), gap_mean=round(statistics.mean(gaps), 3),
               gap_max=round(max(gaps), 2), gap_over_margin=sum(1 for g in gaps if g > 0.92),
               ms_exact_median=round(statistics.median(r['ms_exact'] for r in rows), 2),
               ms_greedy_median=round(statistics.median(r['ms_greedy'] for r in rows), 2),
               answers_median=statistics.median(r['answers'] for r in rows), looks_median=statistics.median(r['looks'] for r in rows),
               budget_above_old_mean=round(statistics.mean(r['exact'] - r['old'] for r in rows), 2), rows=rows)
    json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


if __name__ == '__main__':
    main(sys.argv[1])
