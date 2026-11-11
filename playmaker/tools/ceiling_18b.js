// Step 18b, part 1 and part 4: how often a reading at the search's horizon is above the ceiling (D-145): the most the
// possession can still earn against the defence's best reply = what is already earned + the best open shot any
// attacker's card can score (+ the Coach's Call bonus where that card is in play). On engine.js.
//   node tools/ceiling_18b.js job.json out.json
// job: { positions: [{id, state, ctx}], contexts, profile, set: {switches, settle_shots, calibrated} }
// For each position: the search's own list of team turns, each searched 1 pair ahead, with every horizon reading
// recorded once (per position reached): its phase, whether a shot is declared there, today's reading before the
// calibrated map, the reading the search used, what is already earned, and the ceiling.
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
const CONFIG = load('ai_profiles.json');
E.init({ zones: load('court_zones.json'), config: CONFIG, vcoarse: load('vcoarse.json'), learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null });
const [VMIN, VMAX] = CONFIG.eval.value_bounds;
const job = JSON.parse(fs.readFileSync(process.argv[2]));
const set = job.set || {};
E.setSearch(Object.assign({ stable: false, quiet_points: false, like_with_like: true, tempo: false, play_on: false, clear_reason: false }, set.switches || {}));
E.setCalibrated(set.calibrated !== false);
if (E.setSettle && set.settle_shots != null) E.setSettle(set.settle_shots);
if (E.setHelp && set.help_readings != null) E.setHelp(set.help_readings);
const COACH = { Poor: 0, Okay: 2, Good: 5, Great: 8, Excellent: 10 };
const band = v => (v >= 30 ? 'Excellent' : v >= 25 ? 'Great' : v >= 20 ? 'Good' : v >= 15 ? 'Okay' : 'Poor');
function ceilingOf(ctxj, target) {                     // from the cards alone: 3 x the three, 2 x any other shot
  let best = 0;
  ctxj.off.forEach((c, i) => {
    let m = 0;
    for (const [k, v] of Object.entries(c.r)) if (k.startsWith('shot_')) m = Math.max(m, (k === 'shot_three' ? 3 : 2) * v);
    if (ctxj.coach_call && i === target) m += COACH[band(m)];
    best = Math.max(best, m);
  });
  return best;
}
const out = { rows: [] };
const t0 = Date.now();
for (const p of job.positions) {
  const cj = job.contexts[p.ctx], ctx = E.makeCtx(cj), s = E.stateFrom(p.state, ctx), me = E.actor(s);
  const srch = new E.Searcher(me, job.profile, E.makeEvaluate(job.profile, me, null), Infinity);
  const seen = new Map();
  const inner = srch.leaf.bind(srch);
  srch.leaf = st => {
    const v = inner(st);
    const key = E.zobrist(st) + '|' + st.stage + '|' + (st.pending ? 1 : 0);
    if (!seen.has(key)) {
      const banked = E.bankedOf(st), raw = st.stage === 'play' || st.stage === 'reaction' || st.stage === 'contest' ? E.handLeaf(st) : v;
      seen.set(key, [Math.min(6, Math.max(1, Math.floor((12 - st.clock) / 2) + 1)), st.stage === 'play' ? (st.pending ? 'pass in the air' : 'open play') : 'shot declared',
        raw - banked, v - banked, ceilingOf(cj, st.target), Math.abs(v - raw) > 1e-9 ? 1 : 0]);
    }
    return v;
  };
  const read = new E.Read(s, { exact: true });
  const ts = E.turns(s, job.profile.beam, read, n => srch.quick(n), null, null, 2);
  let best = null;
  for (const [, t] of ts) {
    const n = E.playTurn(s, t);
    const v = srch.value(n, srch.childDepth(s, n, 2), VMIN, VMAX);
    if (best === null || (me === 'O' ? v > best : v < best)) best = v;
  }
  out.rows.push({ id: p.id, side: me, value: best, banked: E.bankedOf(s), ceiling: ceilingOf(cj, s.target), readings: [...seen.values()] });
}
out.seconds = (Date.now() - t0) / 1000;
fs.writeFileSync(process.argv[3], JSON.stringify(out));
