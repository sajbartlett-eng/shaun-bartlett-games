// Reads JSON lines {state, ctx} on stdin and writes engine.js's probe of each (tools/js_equivalence.py compares them
// with the Python engine's).
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const vc = JSON.parse(fs.readFileSync(path.join(root, 'vcoarse.json')));
E.init({ zones: JSON.parse(fs.readFileSync(path.join(root, 'court_zones.json'))), config: JSON.parse(fs.readFileSync(path.join(root, 'ai_profiles.json'))), vcoarse: vc, learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? JSON.parse(fs.readFileSync(path.join(root, 'learned_weights.json'))) : null });
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
const PROFILES = JSON.parse(fs.readFileSync(path.join(root, 'ai_profiles.json'))).profiles;
const lines = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
const out = [];
for (const ln of lines) {
  const q = JSON.parse(ln);
  if (q.leaf_mode) E.setLeafMode(q.leaf_mode);       // step 10: the leaf's mode for this line
  if (q.stable !== undefined) E.setStable(q.stable);   // step 12: the switches
  if (q.speed) E.setSpeed(q.speed);                   // step 13: a speed-up turned off, to prove it changes nothing
  if (q.switches) E.setSearch(q.switches);             // step 13: the stable search's five switches
  if (q.reach !== undefined) E.setReach(q.reach);
  if (q.coverage_budget !== undefined) E.setBudget(q.coverage_budget);
  if (q.advantages !== undefined) E.setAdvantages(q.advantages);         // step 16
  if (q.goals !== undefined) E.setGoals(q.goals);
  if (q.learned !== undefined) E.setLearned(q.learned);
  if (q.settle !== undefined) E.setSettle(q.settle);                    // step 18b
  if (q.help !== undefined) E.setHelp(q.help);                          // step 18c
  if (q.open !== undefined) E.setOpenList(q.open);                      // step 18e (null: each level's own)
  if (q.whole !== undefined) E.setWholeTurns(q.whole);                  // step 18f
  if (q.kept !== undefined) E.setKeptActions(q.kept);
  if (q.calibrated !== undefined) E.setCalibrated(q.calibrated);        // step 17D                  // step 17   // step 13 B
  try {
    if (q.search) out.push(JSON.stringify(E.search(q.search)));
    else {
      const p = E.probe(q.state, q.ctx);
      if (q.state.stage !== 'over') {                     // step 18b: the ceiling (D-145), and a declared shot settled by the rules
        const ctx18 = E.makeCtx(q.ctx), s18 = E.stateFrom(q.state, ctx18);
        p.ceiling = E.ceilingOf(s18);
        if (q.help && s18.stage === 'play' && !s18.pending && E.actor(s18) === 'O') p.floored = new E.Searcher('O', PROFILES.allstar, n => new E.Read(n).leaf(), Infinity).leaf(s18);
        if (q.open && s18.stage === 'play' && s18.side === 'X') {          // step 18e: the open list itself
          const sr = new E.Searcher('X', PROFILES.allstar, n => new E.Read(n).leaf(), Infinity);
          p.open_list = E.turns(s18, 24, null, n => sr.quick(n), null, null, 2, q.open, sr.whole).map(r => [r[0], r[1].map(a => E.actionJSON(a))]);
        }
        if (q.settle && s18.stage !== 'play') {
          const prof = PROFILES.allstar, me = E.actor(s18);
          p.settled = new E.Searcher(me, prof, n => new E.Read(n).leaf(), Infinity).settled(s18);
        }
      }
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
