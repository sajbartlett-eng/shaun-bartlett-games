"""Step 31, fix 1 (Shaun, 26 Nov 2026): after an action, re-read only what it touched, with no decision changed.

Inside the possession's value, each candidate movement of the defence's answer used to read every look again. Now it
reads only the looks that movement touches, and only where a look's ceiling could still change the result
(engine.js possRead: runCand, routeLazy, candTop; value.py poss_read: run_cand, route_diff, cand_top). Each engine
keeps the old every-look reading as a reference, run only under a test switch: these tests read every candidate both
ways and require the two to give the same numbers, to the last bit. tools/step_31_same.py compares whole choices,
values and lines on every exam board before and after."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

import exam_boards as X          # noqa: E402

CHECK_JS = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[1], every = +process.argv[2], setups = JSON.parse(process.argv[3]);
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: load('segments.json'), learned: null });
E._pvCheck(true);
let boards = 0;
for (const b of JSON.parse(fs.readFileSync(0, 'utf8'))) {
  const s = E.stateFrom(b.state, E.makeCtx(b.ctx));
  if (s.stage !== 'play') continue;
  if (setups.includes(b.name)) {                      // the stance search's probe: each defender on every square near him, every arrow
    const sx = q => Math.floor(q / 64) - 20, sy = q => (q % 64) - 20, taken = new Set(s.o.concat(s.x));
    for (let d = 0; d < 5; d++) {
      const c = [];
      for (let dx = -2; dx <= 2; dx++) for (let dy = -2; dy <= 2; dy++) {
        const x = sx(s.x[d]) + dx, y = sy(s.x[d]) + dy, q = (x + 20) * 64 + (y + 20);
        if (x < 0 || x > 16 || y < 1 || y > 14 || (q !== s.x[d] && taken.has(q))) continue;
        for (let a = 0; a < 8; a++) c.push([q, a]);
      }
      E._withMemo(() => E._stanceProbe(s, d, c));
    }
  }
  const all = [s];
  E.legalActions(s).forEach((a, i) => { if (i % every) return; const nx = E.apply(s, a); if (!E.isChance(nx) && nx.stage === 'play') all.push(nx); });
  for (const v of all) { E._withMemo(() => E.possParts(v)); boards++; }
}
process.stdout.write(JSON.stringify(Object.assign({ boards }, E._pvCheck())));
"""


@needs_node
def test_every_candidate_read_by_difference_equals_reading_every_look_javascript():
    """Every exam board and boards one legal action on (every 3rd), and the stance search's probe (each defender on
    every square near him) on three setup boards: every candidate movement read both ways.
    (Fix 3: every 12th became every 3rd, and D2's board joined the probe. The one Move a phase makes the defence's answers shorter, so fewer candidates
    are read per board; more boards keep the check at over 20000 candidates rather than lowering the bar.)"""
    import step_31 as T
    reqs = [T.req(n) for n in X.BOARDS]
    p = subprocess.run(['node', '-e', CHECK_JS, ROOT, '3', json.dumps(['E1', 'E2', 'E3', 'E26'])], input=json.dumps(reqs), capture_output=True, text=True, timeout=900)
    assert p.returncode == 0, p.stderr[-2000:]
    r = json.loads(p.stdout)
    assert r['checked'] > 20000 and r['different'] == 0, r


def test_every_candidate_read_by_difference_equals_reading_every_look_python():
    """The Python engine (value.py), the same on three boards and boards one legal action on (every 5th).
    (Fix 3b: every 20th became every 5th, because the answers are shorter now; the bar of 50 candidates stays.)"""
    from playmaker_engine import value as V
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    V.CHECK[:] = [True, 0, 0]
    try:
        for n in ('E13', 'E21', 'BLK1'):
            s = X.get(n)
            V.poss_parts(s)
            for i, a in enumerate(legal_actions(s)):
                if i % 5:
                    continue
                nx = apply(s, a)
                if not isinstance(nx, ChanceNode) and nx.stage == 'play':
                    V.poss_parts(nx)
        assert V.CHECK[1] > 50 and V.CHECK[2] == 0, V.CHECK
    finally:
        V.CHECK[:] = [False, 0, 0]
