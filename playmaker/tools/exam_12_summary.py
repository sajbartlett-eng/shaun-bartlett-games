"""Step 12: the report's tables from docs/runs/step12/.

The cut-down measurement (Shaun's instruction after the stop): both switches off and both on; 1 team-turn pair ahead
(cut_exam_*_1pair.json) and the clock (cut_exam_*_clock.json); depth stability on boards 2, 7, 9, 10 and 16
(cut_stability_*.json); the sensitivity pairs (cut_sensitivity.json). From the runs completed before the stop:
long_exam_*_2pairs.json (2 pairs ahead: off complete, stable and reach part-way), the equivalence checks, the measures.

  python3 tools/exam_12_summary.py        writes docs/runs/step12/summary.json and prints the tables
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, 'docs', 'runs', 'step12')
BOARDS = [str(n) for n in range(1, 18)] + ['C1', 'C2']


def load(name):
    p = os.path.join(RUN, name)
    return json.load(open(p)) if os.path.exists(p) else None


def rows(name):
    d = load(name)
    return {r['board']: r for r in d['rows']} if d else {}


def mark(r, full=None):
    if r is None:
        return 'not run'
    m = 'P' if r['ok'] else 'F'
    if full and r.get('depth_min') and r['depth_min'] < full:
        m += f" ({r['depth_min']})"
    return m


def first(t):
    return t[0] if t else None


def stability(trace):
    """(changed between like-with-like depths, by the first action; changed between consecutive depths)."""
    tr = {d: tuple(t) for d, t, _ in (trace or [])}
    like = any(first(tr[d]) != first(tr[d - 2]) for d in tr if d - 2 in tr)
    nxt = any(first(tr[d]) != first(tr[d - 1]) for d in tr if d - 1 in tr)
    return like, nxt, len(tr)


def main():
    cut = {('off', 'pair'): rows('cut_exam_off_1pair.json'), ('off', 'clock'): rows('cut_exam_off_clock.json'),
           ('both', 'pair'): rows('cut_exam_both_1pair.json'), ('both', 'clock'): rows('cut_exam_both_clock.json')}
    long_ = {st: rows(f'long_exam_{st}_2pairs.json') for st in ('off', 'stable', 'reach')}
    lines = ['| Board | Off: 1 pair | Off: clock | Both on: 1 pair | Both on: clock | Before the stop, off: 2 pairs |'
             ' Before the stop, stable: 2 pairs | Before the stop, reach: 2 pairs |', '|---|---|---|---|---|---|---|---|']
    tot = {}
    for b in BOARDS:
        cells = [mark(cut[('off', 'pair')].get(b), 2), mark(cut[('off', 'clock')].get(b)),
                 mark(cut[('both', 'pair')].get(b), 2), mark(cut[('both', 'clock')].get(b))]
        cells += [mark(long_[st].get(b), 4) for st in ('off', 'stable', 'reach')]
        for k, c in enumerate(cells):
            if c != 'not run':
                t = tot.setdefault(k, [0, 0])
                t[0] += c.startswith('P')
                t[1] += 1
        lines.append(f'| {b} | ' + ' | '.join(cells) + ' |')
    lines.append('| **Passes** | ' + ' | '.join(f'**{tot[k][0]} of {tot[k][1]}**' if k in tot else '-'
                                             for k in range(7)) + ' |')
    stab = {}
    for st in ('off', 'both'):
        d = load(f'cut_stability_{st}.json') or {'boards': {}}
        per = {}
        for name, v in d['boards'].items():
            like, nxt, n = stability(v.get('trace'))
            per[name] = dict(depth_used=v.get('depth_used'), depths=n, changed_like_with_like=like,
                             changed_next_depth=nxt, seconds=v.get('seconds'), stable=v.get('stable'),
                             choices={str(dd): ' ; '.join(t) for dd, t, _ in (v.get('trace') or [])})
        stab[st] = per
    summary = dict(exam_table='\n'.join(lines), stability=stab, sensitivity=load('cut_sensitivity.json'),
                   measures=load('stable_measures.json'),
                   equivalence={st: (lambda e: e and dict(mismatches=e['mismatches'], states=e['states'],
                                                           searches=e.get('searches')))(load(f'js_equivalence_{st}_200.json'))
                                for st in ('off', 'stable', 'reach', 'both')})
    json.dump(summary, open(os.path.join(RUN, 'summary.json'), 'w'), indent=1)
    print(summary['exam_table'])
    for st, per in stab.items():
        for name, v in per.items():
            print(st, name, v['depth_used'], v['depths'], 'like', v['changed_like_with_like'], 'next', v['changed_next_depth'],
                  v['choices'])


if __name__ == '__main__':
    main()
