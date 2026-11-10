"""Step 13, part A: the report's tables from docs/runs/step13/ (stability, the exam with cheap on, the levels on the
clock, the speed-ups). Writes docs/runs/step13/summary.json and prints the tables.

  python3 tools/exam_13_summary.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, 'docs', 'runs', 'step13')
RUN12 = os.path.join(ROOT, 'docs', 'runs', 'step12')
BOARDS = [str(n) for n in range(1, 18)] + ['C1', 'C2']


def load(name, run=RUN):
    p = os.path.join(run, name)
    return json.load(open(p)) if os.path.exists(p) else None


def first(t):
    return t[0] if t else None


def stability():
    """Per decision: the first action at each completed depth, the seconds each depth was reached at, and whether the
    first action changes between like-with-like depths (1 and 3, 2 and 4)."""
    out = {}
    for st in ('off', 'cheap'):
        d = load(f'stability_{st}.json') or {'boards': {}}
        per = {}
        for name, v in d['boards'].items():
            tr = {dd: t for dd, t, _ in (v.get('trace') or [])}
            pairs = [(a, a + 2) for a in (1, 2) if a in tr and a + 2 in tr]
            changed = [f'{a} to {b}' for a, b in pairs if first(tr[a]) != first(tr[b])]
            per[name] = dict(depths=sorted(tr), choices={str(k): ' ; '.join(t) for k, t in tr.items()},
                             seconds={str(k): x for k, x in (v.get('depth_seconds') or [])},
                             compared=[f'{a} to {b}' for a, b in pairs], changed=changed)
        n_cmp = sum(1 for v in per.values() if v['compared'])
        n_chg = sum(1 for v in per.values() if v['changed'])
        n13 = [v for v in per.values() if '1 to 3' in v['compared']]
        n24 = [v for v in per.values() if '2 to 4' in v['compared']]
        out[st] = dict(decisions=per, compared=n_cmp, changed=n_chg,
                       one_to_three=[sum('1 to 3' in v['changed'] for v in n13), len(n13)],
                       two_to_four=[sum('2 to 4' in v['changed'] for v in n24), len(n24)])
    return out


def exam_rows(name, run=RUN):
    d = load(name, run)
    return {r['board']: r for r in d['rows']} if d else {}


def mark(r, full=None):
    if r is None or r.get('not_run'):
        return 'not run'
    m = 'P' if r['ok'] else 'F'
    if full and r.get('depth_min') and r['depth_min'] < full:
        m += f" ({r['depth_min']})"
    return m


def exam():
    cols = [('Off: 1 pair [step 12]', exam_rows('cut_exam_off_1pair.json', RUN12), 2),
            ('Off: clock [step 12]', exam_rows('cut_exam_off_clock.json', RUN12), None),
            ('Cheap: 1 pair', exam_rows('exam_cheap_1pair.json'), 2),
            ('Cheap: clock', exam_rows('exam_cheap_clock.json'), None)]
    lines = ['| Board | ' + ' | '.join(c[0] for c in cols) + ' |', '|---|' + '---|' * len(cols)]
    tot = [[0, 0] for _ in cols]
    for b in BOARDS:
        cells = [mark(rows.get(b), full) for _, rows, full in cols]
        for k, c in enumerate(cells):
            if c != 'not run':
                tot[k][0] += c.startswith('P')
                tot[k][1] += 1
        lines.append(f'| {b} | ' + ' | '.join(cells) + ' |')
    lines.append('| **Passes** | ' + ' | '.join(f'**{a} of {n}**' if n else '-' for a, n in tot) + ' |')
    secs = {c[0]: round(sum(r.get('seconds', 0) for r in c[1].values())) for c in cols}
    return '\n'.join(lines), secs


def levels():
    out = {}
    for st in ('off', 'cheap', 'cheap_play_on', 'cheap_reach'):
        d = load(f'levels_{st}.json')
        if d:
            out[st] = {k: {f: v[f] for f in v if f != 'rows'} for k, v in d['results'].items()}
    return out


def main():
    table, secs = exam()
    summary = dict(stability=stability(), exam_table=table, exam_seconds=secs, levels=levels(),
                   speedups={k: load(f'speed_{k}.json') for k in ('reach_cache', 'forcing', 'quiet_read', 'tt_order', 'all')},
                   equivalence={f[len('js_equivalence_'):-5]: (lambda e: dict(mismatches=e['mismatches'], states=e['states'],
                                                                                searches=e.get('searches')))(load(f))
                                for f in sorted(os.listdir(RUN)) if f.startswith('js_equivalence_')})
    json.dump(summary, open(os.path.join(RUN, 'summary.json'), 'w'), indent=1)
    for st, v in summary['stability'].items():
        print(st, 'changed', v['changed'], 'of', v['compared'], '| 1 to 3:', v['one_to_three'], '| 2 to 4:', v['two_to_four'])
        for name, r in v['decisions'].items():
            print('  ', name, r['choices'], r['seconds'], r['changed'])
    print(table)
    print(secs)
    for st, v in summary['levels'].items():
        for k, r in v.items():
            print(st, k, r)
    print(json.dumps(summary['equivalence']))


if __name__ == '__main__':
    main()
