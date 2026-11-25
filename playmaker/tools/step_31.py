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


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
