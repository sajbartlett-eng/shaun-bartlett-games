"""Step 31, fix 4i: exact speed only (docs/reports/STEP31_FIX4I_REPORT.md). Every answer the same as fix 4h's.

1. The JavaScript engine on R1 to R5 and P1 to P5, with the fake's follow-up read by difference (fix 4i) and read
   afresh: the same number and answer as fix 4h's recorded run (docs/runs/step31/fix4h_proof.json) on all 21.
2. Python's engine is unchanged in fix 4i, so it reads as fix 4h's proof found (the same as the JavaScript on all 21).
   It is read again here on the boards it reads fastest (PY below); the others are listed as skipped.

    python3 tools/step_31_fix4i_proof.py [out.json]
"""
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.join(ROOT, 'tests'))
import step_31 as T                                      # noqa: E402

B = ['R1', 'R2', 'R3', 'R4', 'R4c', 'R5a', 'R5b', 'R5c', 'R5ctl',
     'P1', 'P1off', 'P2', 'P2off', 'P3', 'P3off', 'P4', 'P4off', 'P5', 'P5off', 'P5ctl', 'P5ctloff']
PY = ['R5c', 'R5ctl', 'P3', 'P5', 'P5off']               # (the boards Python reads fastest; the rest skipped to fit the time)


def run(env):
    out = T.js([T.req(n, dict(only='value')) for n in B], timeout=3000, env_extra=env)
    return {r['name']: dict(v=r['res']['play_on'], a=r['res']['answer'], ms=r['ms']) for r in out}


def main(path):
    import exam_boards as X
    from playmaker_engine import value as V, board as BD
    ref = {r['board']: r['k3'] for r in json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4h_proof.json')))['boards']}
    t0 = time.time()
    with ThreadPoolExecutor(4) as e:
        fj = [e.submit(run, {}), e.submit(run, dict(PM_FU_FRESH='1'))]
        py = dict(zip(PY, e.map(lambda n: V.poss_parts(X.get(n)), PY)))
        diff, fresh = fj[0].result(), fj[1].result()
    rows, bad = [], []
    for n in B:
        r = dict(board=n, fix4h=ref[n]['v'], fix4h_answer=ref[n]['answer'], diff=diff[n], fresh=fresh[n])
        r['same'] = diff[n]['v'] == fresh[n]['v'] == ref[n]['v'] and diff[n]['a'] == fresh[n]['a'] == ref[n]['answer']
        if n in py:
            pp = py[n]
            r['python'] = dict(v=round(pp['V'], 4), answer=[[d, BD.sq(q), a] for d, q, a in pp['moves']])
            r['same'] = r['same'] and r['python']['v'] == ref[n]['v'] and r['python']['answer'] == ref[n]['answer']
        if not r['same']:
            bad.append(n)
        rows.append(r)
        print(f"{n:9} fix 4h {ref[n]['v']:8} {ref[n]['answer']} | by difference {diff[n]['v']:8} ({diff[n]['ms']} ms) | afresh {fresh[n]['v']:8} ({fresh[n]['ms']} ms)"
              + (f" | Python {r['python']['v']}" if n in py else '') + f" | {'same' if r['same'] else 'DIFFERENT'}", flush=True)
    print(f"the same as fix 4h on {len(B) - len(bad)} of {len(B)} boards{'; different: ' + ', '.join(bad) if bad else ''}; "
          f"JavaScript {sum(diff[n]['ms'] for n in B)} ms by difference, {sum(fresh[n]['ms'] for n in B)} ms afresh; Python on {len(PY)} boards "
          f"({', '.join(PY)}), skipped {len(B) - len(PY)}; {round(time.time() - t0)} s")
    json.dump(dict(boards=rows, python_boards=PY, different=bad), open(path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4i_proof.json'))
