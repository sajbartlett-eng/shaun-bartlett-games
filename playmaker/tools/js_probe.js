// Reads JSON lines {state, ctx} on stdin and writes engine.js's probe of each (tools/js_equivalence.py compares them
// with the Python engine's).
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const vc = JSON.parse(fs.readFileSync(path.join(root, 'vcoarse.json')));
E.init({ zones: JSON.parse(fs.readFileSync(path.join(root, 'court_zones.json'))), config: JSON.parse(fs.readFileSync(path.join(root, 'ai_profiles.json'))), vcoarse: vc });
// step 7: in a shot reaction, what each Contest, Steal and ending the reaction resolves to: every leaf of the roll tree
// with its probability, its stage, and the score (a finished possession) or the clock and turnovers (play goes on)
function outcomes(js, ctxJs) {
  const ctx = E.makeCtx(ctxJs), s = E.stateFrom(js, ctx), res = {};
  const leaves = (n, p, out) => {
    if (E.isChance(n)) { for (const [q, , sub] of n.outcomes) leaves(sub, p * q, out); return out; }
    out.push(n.stage === 'over' ? [Math.round(p * 1e12) / 1e12, 'over', E.scoreTotal(n)] : [Math.round(p * 1e12) / 1e12, n.stage, n.clock, n.tos]);
    return out;
  };
  for (const a of E.legalActions(s)) {
    if (!['contest', 'steal', 'end_turn'].includes(a.kind)) continue;
    res[E.actionStr(a)] = leaves(E.apply(s, a), 1, []).sort((x, y) => JSON.stringify(x) < JSON.stringify(y) ? -1 : 1);
  }
  return res;
}
const lines = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
const out = [];
for (const ln of lines) {
  const q = JSON.parse(ln);
  if (q.leaf_mode) E.setLeafMode(q.leaf_mode);       // step 10: the leaf's mode for this line
  if (q.stable !== undefined) E.setStable(q.stable);   // step 12: the switches
  if (q.speed) E.setSpeed(q.speed);                   // step 13: a speed-up turned off, to prove it changes nothing
  if (q.switches) E.setSearch(q.switches);             // step 13: the stable search's five switches
  if (q.reach !== undefined) E.setReach(q.reach);
  try {
    if (q.search) out.push(JSON.stringify(E.search(q.search)));
    else {
      const p = E.probe(q.state, q.ctx);
      if (q.outcomes) p.react_outcomes = outcomes(q.state, q.ctx);
      if (q.reach_map && q.state.stage !== 'over') {      // step 12: the reach map, square by square
        const m = E.reachMap(E.stateFrom(q.state, E.makeCtx(q.ctx))), rm = {};
        for (const [k, row] of Object.entries(m)) { const o = {}; for (const [sq, v] of row) o[E.sqName(sq)] = v; rm[k] = o; }
        p.reach_map = rm;
      }
      out.push(JSON.stringify(p));
    }
  } catch (e) { out.push(JSON.stringify({ error: String(e && e.stack || e) })); }
}
process.stdout.write(out.join('\n') + '\n');
