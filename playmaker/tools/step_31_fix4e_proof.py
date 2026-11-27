"""Step 31, fix 4e: the answer that answers every look and race, held to the full reading (docs/reports/STEP31_FIX4E_REPORT.md).

R1 to R5: each board read with fix 4e's answer, side by side with fix 4d's full reading as recorded
(docs/runs/step31/fix4d_full_reading.json): the number, the answer's movements and every race must be the same.
P1 to P5: each board as written, read with the answer as played (before) and with fix 4e's (after).

    python3 tools/step_31_fix4e_proof.py [out.json]
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
    return T.js([T.req(name, dict(only='value'))], timeout=1800, answer=answer)[0]


def races(v):
    return [(x['advantage'], x['beaten'], x['from'], x['worth']) for x in v.get('drive_race') or []]


def main(path):
    full = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4d_full_reading.json')))
    jobs = [(n, 'answers') for n in R] + [(n, None) for n in P] + [(n, 'answers') for n in P]
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: one(*j), jobs))
    got = {(n, a): r for (n, a), r in zip(jobs, res)}
    rows = {'R': [], 'P': []}
    for n in R:
        a, f = got[(n, 'answers')], full[n]
        va, vf = a['res'], f['res']
        same = va['value'] == vf['value'] and va['answer'] == vf['answer'] and races(va) == races(vf)
        rows['R'].append(dict(board=n, full=vf['value'], full_answer=vf['answer'], full_ms=f['ms'], new=va['value'], new_answer=va['answer'], new_ms=a['ms'], races=races(va), same=same))
        print(f"{n:6} full {vf['value']:8} {vf['answer']} ({f['ms']} ms) | fix 4e {va['value']:8} {va['answer']} ({a['ms']} ms) | {'SAME' if same else 'DIFFERENT'}")
    for n in P:
        b, a = got[(n, None)], got[(n, 'answers')]
        rows['P'].append(dict(board=n, before=b['res']['value'], before_answer=b['res']['answer'], before_ms=b['ms'], after=a['res']['value'], after_answer=a['res']['answer'], after_ms=a['ms'], races_after=races(a['res'])))
        print(f"{n:9} before {b['res']['value']:8} {b['res']['answer']} ({b['ms']} ms) | after {a['res']['value']:8} {a['res']['answer']} ({a['ms']} ms)")
    json.dump(rows, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4e_proof.json'))
