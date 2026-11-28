"""Step 31, fix 4g: each race names its own answers, held to the exact answer (docs/reports/STEP31_FIX4G_REPORT.md).

R1 to R5: the full reading, the exact answer (_pvAnswers) and the new answer in play. P1 to P5: the exact answer and the
new one. All read live, each with its steps written down (PM_DEBUG): what each step took, what that lowered, and
whether a race on the board named its square. Where the new answer misses the exact one, that says which movement it
missed and why no race named it.

    python3 tools/step_31_fix4g_proof.py [out.json]
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
LONG = ('R4', 'R4c', 'R5b', 'R3', 'P4', 'P4off')


def one(name, answer):
    r = T.js([T.req(name, dict(only='value'))], timeout=3000, answer=answer, debug=answer != 'full')[0]
    v = r['res']
    return dict(value=v['value'], answer=v['answer'], ms=r['ms'], debug=v.get('debug') or [])


def why(ex, new):
    """Each exact step the new answer didn't take: the movement, what it lowered, and whether a race named its square."""
    took = [(m[0], m[1], m[2]) for m in new['answer']]
    out = []
    for st in ex['debug']:
        if st.get('path') != 'exact' or not st.get('took'):
            continue
        t = st['took']
        if (t['d'], t['q'], t['a']) in took:
            continue
        if st.get('named') and t['kind'] == 'move' and st.get('namedArrow') != t['a']:
            reason = 'named (%s of %s, from %s), but a Move there faces the line (arrow %d), not arrow %d' % (st['named'][1], st['named'][0], st['named'][2], st['namedArrow'], t['a'])
        elif st.get('named'):
            reason = 'named (%s of %s); the new answer read it and took another first' % (st['named'][1], st['named'][0])
        elif not st['races']:
            reason = 'no race on the board at that step: it lowers a look on the map, which the map\'s own candidates missed'
        else:
            reason = 'not named: its square is on no race\'s line, in front of it, by its finish, or in its passing lanes'
        out.append(dict(step=st['step'], who='X%d' % (t['d'] + 1), frm=t['from'], to=t['q'], arrow=t['a'], kind=t['kind'], number_after=t['u'],
                        lowers=st.get('lowers'), races=st['races'], reason=reason))
    return out


def main(path):
    jobs = [(n, 'full') for n in R] + [(n, 'answers') for n in R + P] + [(n, None) for n in R + P]
    jobs.sort(key=lambda j: (j[1] is None, j[0] not in LONG))   # (the longest first)
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: one(*j), jobs))
    got = {j: r for j, r in zip(jobs, res)}
    rows = []
    for n in R + P:
        ex_, nw = got[(n, 'answers')], got[(n, None)]
        row = dict(board=n, exact=ex_['value'], exact_answer=ex_['answer'], exact_ms=ex_['ms'], new=nw['value'], new_answer=nw['answer'], new_ms=nw['ms'],
                   gap=round(nw['value'] - ex_['value'], 4), new_steps=[d for d in nw['debug'] if d.get('path') in ('named', 'accept', 'back')],
                   exact_steps=[d for d in ex_['debug'] if d.get('path') == 'exact'])
        if n in R:
            f = got[(n, 'full')]
            row.update(full=f['value'], full_answer=f['answer'], full_ms=f['ms'], exact_is_full=f['value'] == ex_['value'] and f['answer'] == ex_['answer'])
        row['missed'] = why(ex_, nw) if row['gap'] > 1e-4 or nw['answer'] != ex_['answer'] else []
        rows.append(row)
        print(f"{n:9} exact {ex_['value']:8} {ex_['answer']} ({ex_['ms']} ms) | new {nw['value']:8} {nw['answer']} ({nw['ms']} ms) | gap {row['gap']:+}"
              + (f" | full {row['full']} {'= exact' if row['exact_is_full'] else 'DIFFERENT from exact'}" if n in R else ''), flush=True)
        for m in row['missed']:
            print(f"    missed: step {m['step']}, {m['who']} {m['frm']} to {m['to']} (arrow {m['arrow']}, {m['kind']}), number {m['number_after']:.4g}: {m['reason']}")
    json.dump(rows, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4g_proof.json'))
