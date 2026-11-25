"""Step 31: the exam's harness. One reading of one board, in the JavaScript engine (and Python where asked).

  python3 tools/step_31.py dump              every exam board as JSON (docs/runs/step31/boards.json)
  python3 tools/step_31.py value [names...]  the possession's value of each board, with its routes
"""
import json
import os
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
RUN = os.path.join(ROOT, 'docs', 'runs', 'step31')
os.makedirs(RUN, exist_ok=True)

NODE = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[1];
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: load('segments.json'),
  learned: fs.existsSync(path.join(root, 'playmaker_engine', 'data', 'learned_weights.json')) ? load('learned_weights.json') : null });
const reqs = JSON.parse(fs.readFileSync(0, 'utf8'));
const out = [];
for (const r of reqs) {
  const t0 = Date.now();
  let res;
  try { res = JSON.parse(E[r.fn || 'coverageJSON'](JSON.stringify({ state: r.state, ctx: r.ctx, options: r.options || null, profile: r.profile, budget: null, max_depth: r.max_depth, stale: null }))); }
  catch (e) { res = { error: String(e && e.stack || e) }; }
  out.push({ name: r.name, ms: Date.now() - t0, res });
}
process.stdout.write(JSON.stringify(out));
"""


def js(reqs, timeout=600):
    """Each request {name, state, ctx, options} read by engine.js in one Node process -> [{name, ms, res}]."""
    p = subprocess.run(['node', '-e', NODE, os.path.abspath(ROOT)], input=json.dumps(reqs), capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[-3000:])
    return json.loads(p.stdout)


def req(name, options=None, state=None, **kw):
    import exam_boards as X
    from playmaker_engine import jsbridge
    s = state if state is not None else X.get(name)
    return dict(name=name, state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), options=options, **kw)


def cmd_dump():
    import exam_boards as X
    out = {k: X.as_json(k) for k in X.BOARDS}
    json.dump(out, open(os.path.join(RUN, 'boards.json'), 'w'))
    print(len(out), 'boards')


def cmd_value(*names):
    import exam_boards as X
    names = names or [k for k in X.BOARDS if k not in X.SETUP]
    for r in js([req(n, dict(only='value')) for n in names]):
        v = r['res']
        if 'error' in v:
            print(r['name'], 'ERROR', v['error'][:600])
            continue
        print(r['name'], r['ms'], 'ms value', v['value'], '| shot now', v['shot_now'], '| play on', v['play_on'], '(before the answer', v['before_answer'], ') bars', v['bars'], 'answer', v['answer'])
        for z in v['looks'][:5]:
            print('    O%d %s (ball at %s) p=%s open %s, as stands %s, after the answer %s%s' % (z['a'] + 1, z['c'], z['q0'], z['p'], z['open'], z['before'], z['worth'], ' dribble' if z['dribble'] else ''))


def cmd_search(depth='1', *names):
    """Each board's decision by the JavaScript search at a fixed look-ahead (All-Star, no clock)."""
    import exam_boards as X
    prof = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))['profiles']['allstar']
    names = names or [k for k in X.BOARDS if k not in X.SETUP]
    for r in js([req(n, None, fn='searchJSON', profile=prof, max_depth=int(depth)) for n in names], timeout=3000):
        v = r['res']
        if 'error' in v:
            print(r['name'], 'ERROR', v['error'][:600])
            continue
        top = v['results'][:3]
        print(r['name'], r['ms'], 'ms reached', v['reached'], 'leaves', v['leaves'], '|', ' ; '.join('%.2f %s' % (val, ' + '.join('%s%s%s' % (a[0], ('' if a[2] is None else ' %s%d' % (a[1], a[2] + 1)), ('' if not a[3] else ' ' + a[3]) + ('' if not a[6] else ' ' + a[6])) for a in t)) for val, t in top))


def cmd_both(*names):
    """Check B2 for the value: every board read by both engines (the value, the bar, the defence's answer)."""
    import time
    import exam_boards as X
    from playmaker_engine import board as B, decide as D, value as V
    names = names or list(X.BOARDS)
    rows, bad = [], 0
    jsr = {r['name']: r for r in js([req(n, dict(only='value')) for n in names])}
    for n in names:
        s = X.get(n)
        t = time.time()
        if s.stage == 'play':
            v = D.Read(s).leaf()
            pp = V.poss_parts(s)
            py = dict(value=round(v, 4), play_on=round(pp['V'], 4), bars=[round(b, 2) for b in pp['bars']], answer=[[d, B.sq(q), a] for d, q, a in pp['moves']])
        else:
            py = None
        j = jsr[n]['res']
        same = py is not None and 'error' not in j and abs(py['value'] - j['value']) < 1e-6 and abs(py['play_on'] - j['play_on']) < 1e-6 and py['bars'] == j['bars'] and py['answer'] == j['answer']
        bad += 0 if same else 1
        rows.append(dict(board=n, same=same, js_ms=jsr[n]['ms'], py_s=round(time.time() - t, 1), js=None if 'error' in j else dict(value=j['value'], play_on=j['play_on'], bars=j['bars'], answer=j['answer']), py=py, error=j.get('error')))
        print(n, 'same' if same else 'DIFFERENT', '' if same else json.dumps(rows[-1])[:700], flush=True)
    json.dump(rows, open(os.path.join(RUN, 'both_value.json'), 'w'), indent=1)
    print(json.dumps(dict(boards=len(rows), different=bad)))


def cmd_weight(*names):
    """The team's weight map of each board (as the pieces stand): its centre, the base centre, the lumps, the heaviest entries."""
    import exam_boards as X
    names = names or list(X.BOARDS)
    for r in js([req(n, dict(only='weight')) for n in names]):
        w = r['res'].get('weight') if 'error' not in r['res'] else None
        if not w:
            print(r['name'], 'ERROR' if 'error' in r['res'] else 'no map', (r['res'].get('error') or '')[:500])
            continue
        print(r['name'], r['ms'], 'ms centre', w['centre']['sq'], (w['centre']['x'], w['centre']['y']), 'total', w['centre']['total'], '| left', w['centre_left']['sq'], w['centre_left']['total'],
              '| base', w['base_centre']['sq'], '| lumps', [(z['sq'], z['weight'], 'O%d %s' % (z['top']['a'] + 1, z['top']['c'])) for z in w['lumps'][:4]])
        for e in sorted(w['entries'], key=lambda e: -e['weight'])[:6]:
            print('    O%d %s %s reach %s open %s contested %s (X%d) saving %s weight %s left %s' % (e['a'] + 1, e['seg'], e['c'], e['reach'], e['open'], e['contested'], e['by'] + 1, e['saving'], e['weight'], e['left']))


def cmd_bothweight(*names):
    """Check B2 for the weight map: every board's map by both engines (the centre, the entries, the lumps)."""
    import time
    import exam_boards as X
    from playmaker_engine import weight as W
    names = names or list(X.BOARDS)
    jsr = {r['name']: r for r in js([req(n, dict(only='weight')) for n in names])}
    bad, rows = 0, []
    for n in names:
        t = time.time()
        py = W.weight_json(X.get(n))
        j = jsr[n]['res'].get('weight') if 'error' not in jsr[n]['res'] else None
        same = py == j
        bad += 0 if same else 1
        why = ''
        if not same and py and j:
            why = [k for k in py if py[k] != j.get(k)]
            if 'entries' in why:
                why.append(next(((a, b) for a, b in zip(py['entries'], j['entries']) if a != b), (len(py['entries']), len(j['entries']))))
        rows.append(dict(board=n, same=same, py_s=round(time.time() - t, 1), why=str(why)[:600], error=jsr[n]['res'].get('error')))
        print(n, 'same' if same else 'DIFFERENT', str(why)[:600], (jsr[n]['res'].get('error') or '')[:300], flush=True)
    json.dump(rows, open(os.path.join(RUN, 'both_weight.json'), 'w'), indent=1)
    print(json.dumps(dict(boards=len(rows), different=bad)))


def cmd_stances(*names):
    """The defence's five stances on each board, from the base positions (the JavaScript engine)."""
    import exam_boards as X
    names = names or [k for k, v in X.SETUP.items() if v == 'defence']
    for r in js([req(n, dict(only='stances')) for n in names], timeout=3000):
        v = r['res']
        if 'error' in v:
            print(r['name'], 'ERROR', v['error'][:700])
            continue
        s = X.get(r['name'])
        from playmaker_engine import board as B
        print(r['name'], r['ms'], 'ms value', v['value'], 'answer moves', v['answer'], 'routes', v['routes'], 'rounds', v['rounds'], 'reads', v['reads'], 'steps', len(v['steps']))
        print('    offence', ' '.join('O%d %s' % (i + 1, B.sq(q)) for i, q in enumerate(s.o)), '| ball O%d' % (s.ball + 1))
        print('    base   ', ' '.join('X%d %s' % (i + 1, q) for i, q in enumerate(v['base']['x'])))
        print('    stances', ' '.join('X%d %s %s' % (i + 1, q, B.DIR_NAMES[v['arrows'][i]] + '+' + B.DIR_NAMES[(v['arrows'][i] + 1) % 8]) for i, q in enumerate(v['x'])))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
