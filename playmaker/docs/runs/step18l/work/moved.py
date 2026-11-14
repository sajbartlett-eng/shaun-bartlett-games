"""Step 18l: each scored position's best answer by play under step 18k's rules and cards (answers_18k.json) and under
this step's (answers_18l.json): which moved. Run from playmaker/: python3 docs/runs/step18l/work/moved.py"""
import json, os, sys
os.environ['SENSE_RUN'] = 'step18l'
sys.path.insert(0, 'tools')
out = {}
for tag, env in (('18k', dict(SENSE_18K='1', SENSE_18L='0')), ('18l', dict(SENSE_18L='1'))):
    for k in ('SENSE_18K', 'SENSE_18L'):
        os.environ.pop(k, None)
    os.environ.update(env)
    for m in [m for m in sys.modules if m in ('sense_18h', 'step_18k', 'step_18j')]:
        del sys.modules[m]
    import sense_18h as S
    positions, answers = S.load()
    for one in S.table(positions, answers):
        rows = sorted(one['rows'], key=lambda r: r['behind_the_best'])
        out.setdefault(one['id'], {})[tag] = dict(best=one['best'], scored=next(r['scored'] for r in one['rows'] if r['name'] == one['best']),
                                                  level=[r['name'] for r in rows if r['is_best_or_level']], n=len(rows),
                                                  rows={r['name']: (r['scored'], r['play_outs'], r['behind_the_best'], r['behind_interval']) for r in one['rows']})
moved = []
for pid, d in out.items():
    if '18k' in d and '18l' in d:
        same = d['18k']['best'] == d['18l']['best']
        still = d['18k']['best'] in d['18l']['level']
        print(('same   ' if same else 'level  ' if still else 'MOVED  '), pid, '| 18k best:', d['18k']['best'][:60], d['18k']['scored'], '| 18l best:', d['18l']['best'][:60], d['18l']['scored'])
        if not same:
            moved.append(pid)
json.dump(out, open('docs/runs/step18l/answers_moved.json', 'w'), indent=1)
print(len(out), 'positions;', len(moved), 'with another best answer')
