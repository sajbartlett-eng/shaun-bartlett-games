// Step 17: playing possessions out with the app's own engine (engine.js), for the rollout labeller, the head-to-head
// harness, self-play and bulk searches. One job file in, one result file out; tools/learn_17.py splits work over the
// cores and gathers the results.
//   node tools/playout.js job.json out.json
// A policy: { profile (a level's settings), depth (team turns ahead), noise (sd added to each turn's value before the
// pick: exploration), set: { switches, reach, budget, advantages, goals, learned } }.
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
const OPEN_DEFAULT = (load('ai_profiles.json').search || {}).open_list;      // null: each level's own setting
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null });

function rng(seed) {                                   // mulberry32: the same dice for the same seed
  let a = seed >>> 0;
  return () => { a = (a + 0x6D2B79F5) >>> 0; let t = a; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
}
function gauss(r) { let u = 0; while (u === 0) u = r(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * r()); }
let current = null;
function apply(set) {                                  // an engine's switches, set before it decides
  const key = JSON.stringify(set || {});
  if (key === current) return;
  current = key;
  set = set || {};
  E.setSearch(Object.assign({ stable: false, quiet_points: false, like_with_like: true, tempo: false, play_on: false, clear_reason: false }, set.switches || {}));
  E.setReach(set.reach !== false);
  E.setBudget(!!set.budget);
  E.setAdvantages(!!set.advantages || !!set.goals);
  E.setGoals(!!set.goals);
  if (E.setLearned) E.setLearned(!!set.learned);
  if (E.setTabletopMap) E.setTabletopMap(set.tabletop_map !== false);
  if (E.setSettle) E.setSettle(set.settle_shots !== false);            // on by default (D-148)
  if (E.setHelp) E.setHelp(!!set.help_readings);                       // step 18c
  if (E.setOpenList) E.setOpenList(set.open_list === undefined ? OPEN_DEFAULT : set.open_list);   // step 18e (unset: the config's)
  if (E.setCalibrated) E.setCalibrated(set.calibrated !== false);      // on by default (D-138)
  if (E.setPrior) E.setPrior(!!set.prior);
}
const key = a => JSON.stringify(E.actionJSON(a));
function searchAt(s, ctx, pol) {
  apply(pol.set);
  return E.search({ stateObj: s, ctxObj: ctx, profile: pol.profile, budget: pol.budget == null ? null : pol.budget, max_depth: pol.depth, stale: null });
}
function decide(s, ctx, pol, r) {                      // one action: the first of the turn the policy picks
  const legal = E.legalActions(s);
  if (legal.length === 1) return legal[0];
  const out = searchAt(s, ctx, pol), sign = E.actor(s) === 'O' ? 1 : -1;
  let best = null, bv = -Infinity;
  for (const [v, t] of out.results) {
    const x = sign * v + (pol.noise ? pol.noise * gauss(pol.rn || r) : 0);     // rn: the engine's own noise, apart from the dice
    if (x > bv) { bv = x; best = t; }
  }
  const want = JSON.stringify(best[0]);
  return legal.find(a => key(a) === want) || legal[0];
}
function sample(node, r) {                             // a roll: one outcome by its chance
  let u = r(), last = null;
  for (const o of node.outcomes) { if (o[0] <= 0) continue; last = o; u -= o[0]; if (u < 0) return o[2]; }
  return last[2];
}
// Play on from a state (or a roll) to the end of the possession. pols: { O, X }. Returns the points, the engine's own
// end value (points and the price of fouls) and the number of decisions; visit(s) sees each decision's state.
function playout(node, ctx, pols, r, visit) {
  let n = 0;
  while (true) {
    if (E.isChance(node)) { node = sample(node, r); continue; }
    if (node.stage === 'over' || n > 300) break;
    if (visit) visit(node);
    node = E.apply(node, decide(node, ctx, pols[E.actor(node)], r));
    n++;
  }
  // how it ended (a shot, free throws, or the clock or a turnover with no shot) and the clock when it did
  return { points: node.stage === 'over' ? E.scoreTotal(node) : 0, value: node.stage === 'over' ? E.terminalValue(node) : 0, decisions: n, over: node.stage === 'over',
    kind: node.stage === 'over' && node.result ? node.result.kind : 'unfinished', clock: node.clock, tokens: node.tok_o };
}
function playTurn(s, turn, r) {                        // a candidate team turn (a list of action JSON), then the dice
  let node = s;
  for (const aj of turn) {
    while (E.isChance(node)) node = sample(node, r);
    if (node.stage === 'over') break;
    const want = JSON.stringify(aj), a = E.legalActions(node).find(x => key(x) === want);
    if (!a) return null;
    node = E.apply(node, a);
  }
  return node;
}
const meanSe = v => { const n = v.length; if (!n) return [0, 0]; const m = v.reduce((a, b) => a + b, 0) / n; let q = 0; for (const x of v) q += (x - m) * (x - m); return [m, n > 1 ? Math.sqrt(q / (n - 1) / n) : 0]; };

const job = JSON.parse(fs.readFileSync(process.argv[2]));
// job.control (step 18d, D-151): play every position under rules.control at that size ('1', '2', '3'; unset: today's rules)
const withControl = c => (job.control != null ? Object.assign({}, c, { rules: Object.assign({}, c.rules, { control: String(job.control) }) }) : c);
const ctxs = (job.contexts || []).map(c => E.makeCtx(withControl(c)));
const state = p => E.stateFrom(p.state, ctxs[p.ctx]);
const out = { kind: job.kind, rows: [] };
const t0 = Date.now();
if (job.kind === 'rollout') {
  // each position: each candidate turn (or the position itself, turn null) played out n times with the same dice per
  // rollout index across the candidates; the values kept so that differences between candidates can be paired
  for (const p of job.positions) {
    const s = state(p), ctx = ctxs[p.ctx], cands = p.turns || [null], row = { id: p.id, turns: [] };
    for (const turn of cands) {
      const vals = [], pts = [];
      for (let k = 0; k < job.n; k++) {
        const r = rng((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0));
        const start = turn ? playTurn(s, turn, r) : s;
        if (start === null) { vals.length = 0; break; }
        const g = playout(start, ctx, job.policies, r);
        vals.push(g.value); pts.push(g.points);
      }
      const [m, se] = meanSe(vals);
      row.turns.push({ turn, mean: m, se, n: vals.length, points: meanSe(pts)[0], values: job.keep ? vals : undefined });
    }
    out.rows.push(row);
  }
} else if (job.kind === 'h2h') {
  // paired possessions: the same start and the same dice, the two engines swapped between offence and defence
  for (const p of job.positions) {
    const s = state(p), ctx = ctxs[p.ctx];
    for (let k = 0; k < job.n; k++) {
      const seed = (job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0);
      // the dice are shared; each engine's pick noise is its own, so an engine against itself is not one game twice
      const A = () => Object.assign({}, job.a, { rn: rng(seed * 31 + 1) }), B = () => Object.assign({}, job.b, { rn: rng(seed * 31 + 2) });
      const a = playout(s, ctx, { O: A(), X: B() }, rng(seed));
      const b = playout(s, ctx, { O: B(), X: A() }, rng(seed));
      out.rows.push({ id: p.id, k, a_offence: a.points, b_offence: b.points, a_value: a.value, b_value: b.value, decisions: a.decisions + b.decisions,
        a_end: [a.kind, a.clock, a.tokens, a.decisions], b_end: [b.kind, b.clock, b.tokens, b.decisions] });
    }
  }
} else if (job.kind === 'selfplay') {
  // noisy play from the starts; every decision's state kept (for labelling and for mining disagreements)
  for (const p of job.positions) {
    const ctx = ctxs[p.ctx];
    for (let k = 0; k < job.n; k++) {
      const seen = [], defence = [];
      // job.features: keep each position as [clock, what is already earned, today's reading, the named readings]
      // (training rows) instead of the whole state
      const g = playout(state(p), ctx, job.policies, rng((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0)), s => {
        if (s.stage !== 'play' || s.pending) return;
        if (job.keepDefence && s.side === 'X' && s.turn_n === 0) defence.push(E.stateJSON(s));   // the defence to act, its turn's start
        if (job.features) seen.push([s.clock, E.bankedOf(s), E.handLeaf(s)].concat(Array.from(E.featuresOf(s))));
        else seen.push(E.stateJSON(s));
      });
      out.rows.push({ id: p.id, k, ctx: p.ctx, points: g.points, value: g.value, decisions: g.decisions, states: seen, end: [g.kind, g.clock, g.tokens],
        defence: defence.length ? defence[Math.floor(defence.length * ((k * 7 + 3 + out.rows.length) % 10) / 10)] : null });
    }
  }
} else if (job.kind === 'trace') {
  // step 18d: self-play with every action kept, for the fidelity measures (who helped and when, what each Contest and
  // shot followed, the extra pass). Per possession: events [phase, stage, side, kind, piece, from, to, target, ball,
  // the ball handler's square]; the board when each shot was declared; how it ended; and each open-play position as
  // [clock, what is earned, today's reading] for the calibrated map's error under the variant.
  for (const p of job.positions) {
    const ctx = ctxs[p.ctx];
    for (let k = 0; k < job.n; k++) {
      const r = rng((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0));
      const pols = { O: Object.assign({}, job.policies.O, { rn: rng(((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0)) * 31 + 1) }),
        X: Object.assign({}, job.policies.X, { rn: rng(((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0)) * 31 + 2) }) };
      let node = state(p), n = 0;
      const events = [], shots = [], reads = [];
      const sqs = a => a.map(q => E.sqName(q));
      while (true) {
        if (E.isChance(node)) { node = sample(node, r); continue; }
        if (node.stage === 'over' || n > 300) break;
        const side = E.actor(node);
        if (node.stage === 'play' && !node.pending) reads.push([node.clock, E.bankedOf(node), E.handLeaf(node), side === 'O' ? 1 : 0]);
        const a = decide(node, ctx, pols[side], r);
        const from = a.piece >= 0 ? E.sqName((a.side === 'O' ? node.o : node.x)[a.piece]) : null;
        events.push([node.phase, node.stage, a.side, a.kind, a.piece, from, a.dest >= 0 ? E.sqName(a.dest) : null, a.target, node.ball, E.sqName(node.o[node.ball]), a.shot || '']);
        if (a.kind === 'shot' || a.kind === 'forced_shot') shots.push({ at: events.length - 1, o: sqs(node.o), x: sqs(node.x), ball: node.ball, phase: node.phase, type: a.shot, forced: a.kind === 'forced_shot' });
        node = E.apply(node, a);
        n++;
      }
      const over = node.stage === 'over';
      out.rows.push({ id: p.id, k, ctx: p.ctx, start: { o: p.state.o, x: p.state.x, ball: p.state.ball }, points: over ? E.scoreTotal(node) : 0, value: over ? E.terminalValue(node) : 0,
        decisions: n, result: over ? node.result : null, end: [over && node.result ? node.result.kind : 'unfinished', node.clock, node.tok_o],
        endX: over ? sqs(node.x) : null, events, shots, reads });
    }
  }
} else if (job.kind === 'search') {
  // one search per position per policy: every root turn with its value, the look-ahead reached, the time
  for (const p of job.positions) {
    const s = state(p), ctx = ctxs[p.ctx], row = { id: p.id, side: E.actor(s), by: {} };
    for (const [name, pol] of Object.entries(job.policies)) {
      const o = searchAt(s, ctx, pol);
      row.by[name] = { results: o.results, reached: o.reached, seconds: o.seconds, explain: o.explain };
    }
    out.rows.push(row);
  }
}
out.seconds = (Date.now() - t0) / 1000;
fs.writeFileSync(process.argv[3], JSON.stringify(out));
