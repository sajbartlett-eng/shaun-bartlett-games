// Step 18h, part 1: the floor shown. For each position of the sense-check set and each candidate turn: the reading's
// parts in the position the turn leaves (the best shot that can go up now, the looks the cover leaves, "play on"),
// which of them today's reading returns, and the reading with eval.no_floor off and on.
//   node tools/floor_18h.js tools/sense_set/positions.json out.json
'use strict';
const fs = require('fs'), path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), learned: load('learned_weights.json') });
E.setLevel('allstar');
const positions = JSON.parse(fs.readFileSync(process.argv[2]));
const key = a => JSON.stringify(E.actionJSON(a));
const out = [];
for (const p of positions) {
  const ctx = E.makeCtx(p.ctx), s = E.stateFrom(p.state, ctx);
  const row = { id: p.id, side: p.side, candidates: [] };
  for (const c of p.candidates) {
    let n = s, ok = true;
    for (const aj of c.turn) {
      if (E.isChance(n) || n.stage === 'over') { ok = false; break; }
      const a = E.legalActions(n).find(x => key(x) === JSON.stringify(aj));
      if (!a) { ok = false; break; }
      n = E.apply(n, a);
    }
    if (ok && !E.isChance(n) && n.stage === 'play') n = E.endedTurn(s, n);
    if (!ok || E.isChance(n) || n.stage !== 'play' || n.pending) { row.candidates.push({ name: c.name, read: null }); continue; }
    const f = E.featuresOf(n), banked = E.bankedOf(n), raw = E.handLeaf(n) - banked;
    const shot = Math.max(f[0], f[1]);
    E.setNoFloor(false); const today = new E.Read(n).leaf() - banked;
    E.setNoFloor(true); const kept = new E.Read(n).leaf() - banked;
    E.setNoFloor(false);
    row.candidates.push({ name: c.name, to_act: E.actor(n), shot_now: shot, best_look_left: f[2], second_look_left: f[3], todays_reading_before_the_map: raw,
      returns: shot > 0 && shot >= raw - 1e-9 ? 'the shot now' : 'play on', today, no_floor: kept });
  }
  out.push(row);
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
