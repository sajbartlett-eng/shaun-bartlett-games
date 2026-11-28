"""Step 31, fix 4f: the answer that answers every look and race, held to the corrected full reading
(docs/reports/STEP31_FIX4F_REPORT.md). The fake's follow-up of a look whose shot or fake goes up before a movement now
reads the board as it stood then, in both readings, so both are read again here, live.

R1 to R5: the number, the answer's movements and every race, the full reading against fix 4e's answer.
P1 to P5: each board as written, the answer as played (before) and fix 4e's (after).

    python3 tools/step_31_fix4f_proof.py [out.json]
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import step_31 as T                                      # noqa: E402

R = ['R1', 'R2', 'R3', 'R4', 'R4c', 'R5a', 'R5b', 'R5c', 'R5ctl']
P = ['P1', 'P1off', 'P2', 'P2off', 'P3', 'P3off', 'P4', 'P4off', 'P5', 'P5off', 'P5ctl', 'P5ctloff']


def one(name, answer):
    return T.js([T.req(name, dict(only='value'))], timeout=3000, answer=answer)[0]


def races(v):
    return [(x['advantage'], x['beaten'], x['from'], x['worth']) for x in v.get('drive_race') or []]


def main(path):
    jobs = [(n, 'full') for n in R] + [(n, 'answers') for n in R] + [(n, None) for n in P] + [(n, 'answers') for n in P]
    jobs.sort(key=lambda j: 0 if j[0] in ('R4', 'R4c', 'R5b') else 1)        # (the longest first)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: one(*j), jobs))
    got = {j: r for j, r in zip(jobs, res)}
    rows = {'R': [], 'P': []}
    for n in R:
        f, a = got[(n, 'full')], got[(n, 'answers')]
        vf, va = f['res'], a['res']
        same = va['value'] == vf['value'] and va['answer'] == vf['answer'] and races(va) == races(vf)
        rows['R'].append(dict(board=n, full=vf['value'], full_answer=vf['answer'], full_ms=f['ms'], new=va['value'], new_answer=va['answer'], new_ms=a['ms'], races=races(va), same=same))
        print(f"{n:6} full {vf['value']:8} {vf['answer']} ({f['ms']} ms) | fix 4e's answer {va['value']:8} {va['answer']} ({a['ms']} ms) | {'SAME' if same else 'DIFFERENT'}")
    for n in P:
        b, a = got[(n, None)], got[(n, 'answers')]
        rows['P'].append(dict(board=n, before=b['res']['value'], before_answer=b['res']['answer'], before_ms=b['ms'], after=a['res']['value'], after_answer=a['res']['answer'], after_ms=a['ms'],
                              races_after=races(a['res']), looks_after=a['res'].get('looks', [])[:6], looks_before=b['res'].get('looks', [])[:6]))
        print(f"{n:9} before {b['res']['value']:8} {b['res']['answer']} ({b['ms']} ms) | after {a['res']['value']:8} {a['res']['answer']} ({a['ms']} ms)")
    json.dump(rows, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4f_proof.json'))
