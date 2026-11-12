// Step 18d: a line of play read step by step. For one position: the search's own choice 1 pair ahead (no pick noise),
// the best few turns it looked at, and the value of each named turn when it is searched; with the position after each
// named turn, so the next step can be asked. On engine.js.
//   node tools/line_18d.js job.json out.json
// job: { state, ctx, profile, control ('1', '2', '3' or unset), turns: [{name, turn: [action JSON, ...]}], top }
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
if (job.open_list != null && E.setOpenList) E.setOpenList(job.open_list);        // step 18e (search.open_list)
for (const [k, fn] of [['whole_turns', 'setWholeTurns'], ['kept_actions', 'setKeptActions'], ['split_ties', 'setSplitTies']]) if (job[k] != null && E[fn]) E[fn](job[k]);   // step 18f
if (job.leaf_mode != null && E.setLeafMode) E.setLeafMode(job.leaf_mode);
const cj = job.control != null ? Object.assign({}, job.ctx, { rules: Object.assign({}, job.ctx.rules, { control: String(job.control) }) }) : job.ctx;
const ctx = E.makeCtx(cj), s = E.stateFrom(job.state, ctx);
const key = a => JSON.stringify(E.actionJSON(a));
const words = t => t.map(a => E.actionStr(a)).join(', then ');
const out = { control: job.control || 'off', stage: s.stage, side: null, rows: [], named: [] };
if (s.stage !== 'over') {
  const me = E.actor(s), sign = me === 'O' ? 1 : -1;
  out.side = me;
  const srch = new E.Searcher(me, job.profile, E.makeEvaluate(job.profile, me, null), Infinity);
  const value = n => (E.isChance(n) ? srch.value(n, 1, VMIN, VMAX) : n.stage === 'over' ? E.terminalValue(n) : srch.value(n, srch.childDepth(s, n, 2), VMIN, VMAX));
  const read = new E.Read(s, { exact: true });
  const ts = s.stage === 'play' ? E.turns(s, job.profile.beam, read, n => srch.quick(n), null, null, 2, srch.open) : srch.turnsOf(s);
  const done = n => (srch.whole && E.endedTurn ? E.endedTurn(s, n) : n);     // step 18f (search.whole_turns)
  const rows = ts.map(([, t]) => [value(done(E.playTurn(s, t))), t]);
  rows.sort((x, y) => sign * (y[0] - x[0]));
  out.listed = rows.length;
  out.rows = rows.slice(0, job.top || 6).map(r => ({ words: words(r[1]), value: r[0], turn: r[1].map(a => E.actionJSON(a)) }));
  const onList = new Map(rows.map((r, k) => [r[1].map(key).join('|'), k + 1]));
  for (const item of job.turns || []) {
    let n = s; const acts = [];
    let ok = true;
    for (const aj of item.turn) {
      if (E.isChance(n) || n.stage === 'over') { ok = false; break; }
      const a = E.legalActions(n).find(x => key(x) === JSON.stringify(aj));
      if (!a) { ok = false; break; }
      acts.push(a); n = E.apply(n, a);
    }
    if (!ok) { out.named.push({ name: item.name, legal: false }); continue; }
    const v = value(done(n));
    // the best shot the ball handler can release at once from the position after the turn (the offence to act), by the rules
    let shotNow = null;
    if (!E.isChance(n) && n.stage === 'play' && !n.pending && E.actor(n) === 'O') {
      const f = new E.Searcher('O', job.profile, E.makeEvaluate(job.profile, 'O', null), Infinity);
      const fv = f.floor(n, -1e9), hit = f.fcache.get(E.zobrist(n));
      if (fv > -1e8) shotNow = { value: fv, square: hit && hit[1] >= 0 ? E.sqName(hit[1]) : null, shot: hit ? hit[2] : null };
    }
    out.named.push({ name: item.name, legal: true, words: words(acts), value: v, behind_the_choice: sign * (rows[0][0] - v),
      list_rank: onList.get(acts.map(key).join('|')) || onList.get(acts.slice().reverse().map(key).join('|')) || null, shot_now: shotNow, after: E.isChance(n) ? null : E.stateJSON(n) });
  }
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
