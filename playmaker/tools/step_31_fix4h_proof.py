"""Step 31, fix 4h: the named answers, faster and exact, then three more kinds of answer (docs/reports/STEP31_FIX4H_REPORT.md).

1. The speed is exact: on R1 to R5 and P1 to P5 the answer in play reads the same with its races read by difference and
   its floors (fix 4h) as with every named movement's races read afresh (fix 4g's way), and each race read by difference
   equals it read afresh.
2. The gap to the exact answer after each kind of answer is named: 0, fix 4g's; 1, helpers arriving in time; 2, the
   rim when a drive's line stops short; 3, the two-step routes. The exact answer (_pvAnswers) is fix 4g's recorded run
   (docs/runs/step31/fix4g_proof.json): nothing it reads changed in fix 4h.
3. Both engines, with every kind on: the same number and answer on all 21 boards.

    python3 tools/step_31_fix4h_proof.py [out.json]
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
import step_31 as T                                      # noqa: E402

B = ['R1', 'R2', 'R3', 'R4', 'R4c', 'R5a', 'R5b', 'R5c', 'R5ctl',
     'P1', 'P1off', 'P2', 'P2off', 'P3', 'P3off', 'P4', 'P4off', 'P5', 'P5off', 'P5ctl', 'P5ctloff']


def run(env):
    reqs = [T.req(n, dict(only='value')) for n in B]
    out = T.js(reqs, timeout=3000, env_extra=env)
    return {r['name']: dict(v=r['res']['play_on'], a=r['res']['answer'], ms=r['ms'], rc=r.get('race_check')) for r in out}


def main(path):
    import exam_boards as X
    from playmaker_engine import value as V, board as BD
    ex = {r['board']: r for r in json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4g_proof.json')))}
    jobs = [('fresh', dict(PM_KINDS='0', PM_NAMED_FRESH='1')), ('diff', dict(PM_KINDS='0', PM_RACE_CHECK='1'))] + [('k%d' % k, dict(PM_KINDS=str(k))) for k in (1, 2, 3)]
    with ThreadPoolExecutor(4) as e:
        got = dict(zip([j[0] for j in jobs], e.map(lambda j: run(j[1]), jobs)))
        py = dict(zip(B, e.map(lambda n: V.poss_parts(X.get(n)), B)))
    rows = []
    same = all(got['fresh'][n]['v'] == got['diff'][n]['v'] and got['fresh'][n]['a'] == got['diff'][n]['a'] for n in B)
    rc = [got['diff'][n]['rc'] for n in B]
    print(f"1. by difference and floors against afresh: {'the same' if same else 'DIFFERENT'} on {len(B)} boards; races read by difference "
          f"{sum(x['n'] for x in rc)}, different from afresh {sum(x['bad'] for x in rc)}; time {sum(got['fresh'][n]['ms'] for n in B)} ms afresh, "
          f"{sum(got['diff'][n]['ms'] for n in B) } ms by difference (with the check's own fresh reads)")
    for n in B:
        e_ = ex[n]['exact']
        row = dict(board=n, exact=e_, exact_answer=ex[n]['exact_answer'])
        for k, key in ((0, 'fresh'), (1, 'k1'), (2, 'k2'), (3, 'k3')):
            row['k%d' % k] = dict(v=got[key][n]['v'], answer=got[key][n]['a'], gap=round(got[key][n]['v'] - e_, 4), ms=got[key][n]['ms'])
        pp = py[n]
        row['python'] = dict(v=round(pp['V'], 4), answer=[[d, BD.sq(q), a] for d, q, a in pp['moves']])
        row['engines_same'] = row['python']['v'] == row['k3']['v'] and row['python']['answer'] == row['k3']['answer']
        rows.append(row)
        print(f"{n:9} exact {e_:8} | " + ' | '.join(f"k{k} {row['k%d' % k]['v']:8} ({row['k%d' % k]['gap']:+})" for k in range(4))
              + f" | {row['k3']['answer']} | engines {'same' if row['engines_same'] else 'DIFFERENT'}", flush=True)
    for k in range(4):
        print(f"kind {k}: boards with a gap {sum(1 for r in rows if r['k%d' % k]['gap'] > 1e-4)}, total gap {round(sum(r['k%d' % k]['gap'] for r in rows), 4)}, "
              f"time {sum(r['k%d' % k]['ms'] for r in rows)} ms")
    json.dump(dict(exact_speed=dict(same=same, race_reads=sum(x['n'] for x in rc), different=sum(x['bad'] for x in rc)), boards=rows), open(path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4h_proof.json'))
