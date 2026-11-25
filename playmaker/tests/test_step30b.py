"""Step 30b: speed foundations. A memory that lasts one think: a remembered reading always equals a fresh one, its key
changes whenever anything in the state changes, and nothing outlives the think. (The same-decisions checks on the three
profiled boards are in tools/step_30b.py and the report: they replay every request the engine received.)"""
import dataclasses
import json
import os
import random
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

JS = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[2];
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'),
  learned: fs.existsSync(path.join(root, 'playmaker_engine', 'data', 'learned_weights.json')) ? load('learned_weights.json') : null });
const reqs = JSON.parse(fs.readFileSync(process.argv[3]));
const out = { same: 0, n: 0, hits: 0, keyMisses: [], diff: [] };
for (const r of reqs) {
  const ctx = E.makeCtx(r.ctx), s = E.stateFrom(r.state, ctx);
  for (const only of ['lasting', null]) {
    const opts = only ? { only } : null;
    const fresh = JSON.stringify(E.coverage(s, opts));                     // a direct call: no memory open
    const remembered = E.coverageJSON(JSON.stringify({ state: r.state, ctx: r.ctx, options: opts }));
    out.n++;
    if (fresh === remembered) out.same++; else if (out.diff.length < 2) out.diff.push([only, fresh.slice(0, 200), remembered.slice(0, 200)]);
  }
  // inside one memory: two equal states (separate objects) share one map; the shared map reads as a fresh one does
  E._withMemo(() => {
    const f1 = E.covOffFresh(s), f2 = E.covOffFresh(s);
    const m1 = E._covBuild(f1, true, null), m2 = E._covBuild(f2, true, null);
    if (m1 === m2) out.hits++;
  });
  // the key: change any one field of the state and it changes
  const base = E._stateKey(s);
  for (const k of Object.keys(s)) {
    if (k === 'ctx' || k[0] === '_') continue;
    const t = Object.assign(Object.create(Object.getPrototypeOf(s)), s);
    const v = s[k];
    t[k] = typeof v === 'number' ? v + 1 : typeof v === 'boolean' ? !v : typeof v === 'string' ? v + 'z'
      : Array.isArray(v) ? v.concat([0]) : v === null ? 0 : Object.assign({}, v, { _changed: 1, changed: 1 });
    if (E._stateKey(t) === base) out.keyMisses.push(k);
  }
}
process.stdout.write(JSON.stringify(out));
"""


def _states(n, seed=30):
    """Boards a game reaches: the two starting boards below, then a few legal actions picked at random (dice rolled)."""
    from playmaker_engine import jsbridge
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode, sample
    import step_21 as T
    rng = random.Random(seed)
    starts = [_board(), T._state(['H4', 'C9', 'O9', 'A3', 'Q9'], ['D8', 'B8', 'N8', 'B3', 'H3'], [0] * 5, ball=0)]
    out = []
    while len(out) < n:
        s = starts[len(out) % len(starts)]
        for _ in range(rng.randrange(6)):
            acts = legal_actions(s) if s.stage == 'play' else []
            if not acts:
                break
            node = apply(s, rng.choice(acts))
            s = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
        if s.stage == 'play':
            out.append(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx)))
    return out


@needs_node
def test_a_remembered_reading_equals_a_fresh_one_and_the_key_misses_no_field(tmp_path):
    reqs = _states(12)
    script, data = tmp_path / 'memo.js', tmp_path / 'reqs.json'
    script.write_text(JS)
    data.write_text(json.dumps(reqs))
    r = subprocess.run(['node', str(script), ROOT, str(data)], capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    out = json.loads(r.stdout)
    assert out['n'] == 24 and out['same'] == out['n'], out['diff']
    assert out['hits'] == len(reqs)                 # equal boards, separate objects: one map, read once
    assert out['keyMisses'] == []                   # every field of the state is in its key


def test_the_python_key_is_every_field_of_the_state():
    from playmaker_engine.state import GameState
    left_out = [f.name for f in dataclasses.fields(GameState) if not f.compare]
    assert left_out == ['ctx']                       # the memory adds the context's identity itself (decide.map_read)


def _board():
    import step_21 as T
    return T._state(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'B4', 'P4'], [0, 7, 1, 7, 1], ball=0)


def test_the_python_memory_reads_as_a_fresh_reading():
    from playmaker_engine import decide as D, memo
    s = _board()
    for t in (s, s.with_(tok_o=4, moved_o=1), s.with_(side='X', turn_n=1)):
        fresh = (D.top_of(t), D.lasting_of(t)['L'])
        with memo.think():
            first = (D.top_of(t), D.lasting_of(t)['L'])
            again = (D.top_of(t), D.lasting_of(t)['L'])        # read again inside the think: from the memory
        assert fresh == first == again


def test_the_memory_lasts_one_think_and_never_crosses_to_the_next():
    from playmaker_engine import memo
    assert not memo.is_open()
    made = []
    with memo.think():
        memo.get('call', 'a', lambda: made.append(1) or 'x')
        with memo.think():                                     # a reading inside the think (its model of the other side)
            memo.get('call', 'a', lambda: made.append(1) or 'x')
        assert memo.is_open()
    assert not memo.is_open() and len(made) == 1
    with memo.think():                                         # the next think starts empty
        memo.get('call', 'a', lambda: made.append(1) or 'x')
    assert len(made) == 2
    memo.get('call', 'a', lambda: made.append(1) or 'x')       # outside a think nothing is remembered
    memo.get('call', 'a', lambda: made.append(1) or 'x')
    assert len(made) == 4


def test_a_repeated_request_is_answered_once_and_each_caller_gets_its_own_copy(monkeypatch):
    from playmaker_engine import agent as AG, memo, jsbridge
    calls = []
    monkeypatch.setitem(AG.JS, 'coverage', lambda text: calls.append(text) or json.dumps(dict(L=1.0, list=[3, 2])))
    monkeypatch.setattr(jsbridge, 'ported', lambda rules: True)
    s = _board()
    with memo.think():
        a, b = AG.coverage(s, only='lasting'), AG.coverage(s, only='lasting')
        a['list'].append(9)                                    # one caller changing its copy never reaches the other
        assert b == dict(L=1.0, list=[3, 2]) and len(calls) == 1
        AG.coverage(s.with_(tok_o=5), only='lasting')          # any difference in the state is a new request
        assert len(calls) == 2
    AG.coverage(s, only='lasting')
    assert len(calls) == 3                                      # the think is over: asked again


def test_a_computer_turn_and_both_setups_think_inside_one_memory():
    import inspect
    from playmaker_engine import agent as AG, plan as PL
    assert 'memo.think()' in inspect.getsource(AG.Agent.choose)
    assert 'memo.think()' in inspect.getsource(PL.place_offence)
    assert 'memo.think()' in inspect.getsource(PL.place_defence)
    assert 'memo.think()' in inspect.getsource(PL.read_plan)          # the coach's line reads the plan on its own
