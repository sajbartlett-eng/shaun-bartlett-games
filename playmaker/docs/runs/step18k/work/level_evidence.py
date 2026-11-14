"""Step 18k: what evidence splits turns the computer reads level? For one position: each turn the All-Star reads level
with its choice, its played-out value, and the readings that could split them: the reading one turn shorter (before the
offence's reply), the place the spread of replies gives it today, and a deeper look (the offence's best reply after
the defence has answered it). Searches only; the play-outs are the set's answers."""
import json, os, sys
sys.path.insert(0, 'tools')
os.environ.setdefault('SENSE_RUN', 'step18k'); os.environ.setdefault('SENSE_18K', '1')
import sense_18h as S
L = S.L
pid = sys.argv[1]
sw = S._switches(sys.argv[2:])
positions, answers = S.load()
p = next(q for q in positions if q['id'] == pid)
res = answers['results'].get(pid, {})
flat = lambda v: [x for c in v for x in c]
def search(depth, items=None):
    pol = {'p': L.policy('allstar', depth, 0.0, **sw)}
    jobs = items or [dict(id='0', state=p['state'], ctx=0)]
    rows, _ = L.run_jobs('search', jobs, [p['ctx']], policies=pol, **S.RULE)
    return rows
r2 = search(2)[0]['by']['p']['results']
r1 = {S.key(t): v for v, t in search(1)[0]['by']['p']['results']}
level = [(k, t) for k, (v, t) in enumerate(r2) if abs(v - r2[0][0]) < 1e-9]
deep = {r['id']: r['by']['p']['results'][0][0] for r in search(2, items=[dict(id=S.key(t), state=p['state'], ctx=0, pre=t) for _, t in level])}
rows = []
for k, t in level:
    v = res.get(S.key(t))
    played = sum(flat(v)) / len(flat(v)) if v and flat(v) else None
    rows.append(dict(place=k + 1, turn=S.words(t), played=None if played is None else round(played, 1), shorter=round(r1.get(S.key(t), float('nan')), 2), deeper=round(deep.get(S.key(t), float('nan')), 2)))
print(pid, '| side', p['side'], '| level turns', len(level), 'at', round(r2[0][0], 2), '| switches', sw)
for r in rows:
    print('  ', str(r['place']).rjust(2), str(r['played']).rjust(5), '| one turn shorter', str(r['shorter']).rjust(6), '| deeper', str(r['deeper']).rjust(6), '|', r['turn'][:70])
have = [r for r in rows if r['played'] is not None]
if len(have) > 2:
    import statistics as st
    def corr(a, b):
        ma, mb = st.mean(a), st.mean(b); da = [x - ma for x in a]; db = [y - mb for y in b]
        den = (sum(x * x for x in da) * sum(y * y for y in db)) ** 0.5
        return round(sum(x * y for x, y in zip(da, db)) / den, 2) if den else None
    pl = [r['played'] for r in have]
    print('   average played', round(st.mean(pl), 1), '| best', min(pl) if p['side'] == 'X' else max(pl), '| today picks place 1:', have[0]['played'])
    for name in ('place', 'shorter', 'deeper'):
        xs = [r[name] for r in have]
        pick = (min if p['side'] == 'X' else max)(have, key=lambda r: (r[name], r['place'])) if name != 'place' else have[0]
        print('   ', name.ljust(8), 'goes with play:', corr(xs, pl), '| its pick plays', pick['played'], '|', pick['turn'][:50])
json.dump(dict(position=pid, switches=sw, rows=rows), open(os.path.join(S.RUN, 'level_' + pid.replace(' ', '_').replace(',', '') + ('_' + '_'.join(sys.argv[2:]) if sw else '') + '.json'), 'w'), indent=1)
