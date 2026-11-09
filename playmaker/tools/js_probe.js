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
  try {
    if (q.search) out.push(JSON.stringify(E.search(q.search)));
    else {
      const p = E.probe(q.state, q.ctx);
      if (q.outcomes) p.react_outcomes = outcomes(q.state, q.ctx);
      out.push(JSON.stringify(p));
    }
  } catch (e) { out.push(JSON.stringify({ error: String(e && e.stack || e) })); }
}
process.stdout.write(out.join('\n') + '\n');
