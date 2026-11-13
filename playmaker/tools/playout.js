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
const SEARCH_DEFAULT = load('ai_profiles.json').search || {}, EVAL_DEFAULT = load('ai_profiles.json').eval || {};
const SWITCHES_18F = [['whole_turns', 'setWholeTurns'], ['kept_actions', 'setKeptActions'], ['split_ties', 'setSplitTies'], ['rank_in_hand', 'setRankInHand'], ['dice_in_hand', 'setDiceInHand'], ['ball_loss', 'setBallLoss'], ['keep_settled', 'setKeepSettled'], ['no_floor', 'setNoFloor'], ['exact_shot', 'setExactShot']];      // step 18f: [the policy's setting, the engine's setter]
const LEARNED = fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null;
// step 18f: a policy's `map: 'start'` plays with the map as it stood at the start of the step (the end re-measure's other side)
const START_FILE = path.join(__dirname, '..', 'docs', 'runs', 'step18f', 'start_of_step_weights.json');
const START_MAP = fs.existsSync(START_FILE) ? JSON.parse(fs.readFileSync(START_FILE)).calibration : null;
const FILE_MAP = LEARNED ? LEARNED.calibration : null, FILE_LEVELS = LEARNED ? LEARNED.calibration_levels : null;
// step 18h: a policy's `map: 'reference'` plays with the map the sense-check set's answers were measured with
const REF_FILE = path.join(__dirname, 'sense_set', 'reference_weights.json');
const REF_MAP = fs.existsSync(REF_FILE) ? JSON.parse(fs.readFileSync(REF_FILE)).calibration : null;
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), learned: LEARNED });

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
  if (LEARNED) LEARNED.calibration = set.map === 'start' && START_MAP ? START_MAP : set.map === 'reference' && REF_MAP ? REF_MAP : FILE_MAP;
  if (LEARNED) LEARNED.calibration_levels = set.map ? undefined : FILE_LEVELS;     // a named map is the one map for every level      // before setLeafMode, which clears the stored reads
  if (E.setLeafMode) E.setLeafMode(set.leaf_mode === undefined ? (EVAL_DEFAULT.leaf_mode || 'floor') : set.leaf_mode);   // step 18f (unset: the config's)
  for (const [k, fn] of SWITCHES_18F) if (E[fn]) E[fn](set[k] === undefined ? (SEARCH_DEFAULT[k] || EVAL_DEFAULT[k] || false) : set[k]);   // step 18f (unset: the config's)
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
  const split = !!(E.splitOn && E.splitOn());            // step 18f (search.split_ties): turns that read the same get one draw
  let prev = null, nz = 0;
  for (const [v, t] of out.results) {
    if (!split || prev === null || Math.abs(v - prev) >= 1e-9) nz = pol.noise ? pol.noise * gauss(pol.rn || r) : 0;     // rn: the engine's own noise, apart from the dice
    prev = v;
    const x = sign * v + nz;
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
function playout(node, ctx, pols, r, visit, log) {
  let n = 0;
  while (true) {
    if (E.isChance(node)) { node = sample(node, r); continue; }
    if (node.stage === 'over' || n > 300) break;
    if (visit) visit(node);
    const act = decide(node, ctx, pols[E.actor(node)], r);
    if (log) log.push(E.actionStr(act));                 // step 18g: the play-out's actions, for a sense check
    node = E.apply(node, act);
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
// job.zone (step 18g, D-167): play every position under rules.zone 'on' (the zone of influence)
// job.rules (step 18i): rule settings laid over every position's own, e.g. { three_seconds: 'on' }
// job.fouls (step 18i, D-175): the foul situation laid over every position's own: { team_fouls, quarter_left }
const withControl = c => {
  if (job.control == null && !job.zone && !job.rules && !job.fouls) return c;
  const r = Object.assign({}, c.rules, job.rules || {});
  if (job.fouls) c = Object.assign({}, c, job.fouls);
  if (job.control != null) r.control = String(job.control);
  if (job.zone) r.zone = 'on';
  return Object.assign({}, c, { rules: r });
};
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
      const vals = [], pts = [], ends = [], lines = [];
      for (let k = 0; k < job.n; k++) {
        const r = rng((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0));
        const start = turn ? playTurn(s, turn, r) : s;
        if (start === null) { vals.length = 0; break; }
        const lg = job.lines && k < job.lines ? [] : null;
        const g = playout(start, ctx, job.policies, r, null, lg);
        vals.push(g.value); pts.push(g.points); ends.push(g.kind);
        if (lg) lines.push(lg);
      }
      const [m, se] = meanSe(vals);
      row.turns.push({ turn, mean: m, se, n: vals.length, points: meanSe(pts)[0], values: job.keep ? vals : undefined,
        ends: job.ends ? ends : undefined, lines: job.lines ? lines : undefined });
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
      const reactions = [];
      const g = playout(state(p), ctx, job.policies, rng((job.seed || 1) * 1000003 + k * 7919 + (p.seed || 0)), s => {
        if (job.keepReactions && s.stage === 'reaction' && E.actor(s) === 'X' && s.turn_n === 0) reactions.push(E.stateJSON(s));   // step 18h: the defence's answer to a shot
        if (s.stage !== 'play' || s.pending) return;
        if (job.keepDefence && s.side === 'X' && s.turn_n === 0) defence.push(E.stateJSON(s));   // the defence to act, its turn's start
        if (job.features) seen.push([s.clock, E.bankedOf(s), E.handLeaf(s)].concat(Array.from(E.featuresOf(s))).concat(job.looks && E.looksLeaf ? [E.looksLeaf(s)] : []));   // job.looks (step 18f): the looks reading, last
        else seen.push(E.stateJSON(s));
      });
      out.rows.push({ id: p.id, k, ctx: p.ctx, points: g.points, value: g.value, decisions: g.decisions, states: seen, reactions: job.keepReactions ? reactions : undefined, end: [g.kind, g.clock, g.tokens],
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
      // step 18g: the stance rows (the offence's turn starts: [phase, its movements so far, its passes so far, whether
      // the ball has just been caught, then engine.stanceFacts]) and each Dribble [phase, won]
      const stances = [], dribbles = [], examples = [], guards = [];
      let movesB = 0, passesB = 0, lastBall = node.ball, drib = null;
      const sqs = a => a.map(q => E.sqName(q));
      while (true) {
        if (E.isChance(node)) {
          node = sample(node, r);
          if (drib && !E.isChance(node)) { dribbles.push([drib[0], node.beaten.some(b => b[0] === drib[1] && b[1] === drib[2]) ? 1 : 0]); drib = null; }
          continue;
        }
        if (node.stage === 'over' || n > 300) break;
        const side = E.actor(node);
        if (job.stances && side === 'O' && node.stage === 'play' && !node.pending && node.turn_n === 0) {
          guards.push([events.length, node.phase, node.ball, E.closelyGuarded(node) ? 1 : 0, node.grd, node.key_o]);   // step 18i
          const ex = [];
          stances.push([node.phase, movesB, passesB, node.ball !== lastBall ? 1 : 0].concat(E.stanceFacts(node, ex)));
          for (const e of ex) examples.push([events.length, node.phase].concat(e));
          lastBall = node.ball;
        }
        if (node.stage === 'play' && !node.pending) reads.push([node.clock, E.bankedOf(node), E.handLeaf(node), side === 'O' ? 1 : 0].concat(job.looks && E.looksLeaf ? [E.looksLeaf(node)] : []).concat(job.features ? Array.from(E.featuresOf(node)) : []));   // job.features (step 18h): the named readings, last   // job.looks (step 18f): the looks reading, last
        const a = decide(node, ctx, pols[side], r);
        const from = a.piece >= 0 ? E.sqName((a.side === 'O' ? node.o : node.x)[a.piece]) : null;
        events.push([node.phase, node.stage, a.side, a.kind, a.piece, from, a.dest >= 0 ? E.sqName(a.dest) : null, a.target, node.ball, E.sqName(node.o[node.ball]), a.shot || '']);
        if (a.kind === 'shot' || a.kind === 'forced_shot') shots.push({ at: events.length - 1, o: sqs(node.o), x: sqs(node.x), ball: node.ball, phase: node.phase, type: a.shot, forced: a.kind === 'forced_shot' });
        if (a.side === 'O' && (a.kind === 'move' || a.kind === 'qs' || a.kind === 'sprint')) movesB++;
        if (a.kind === 'pass') passesB++;
        if (a.kind === 'dribble') drib = [node.phase, node.ball, a.target];
        node = E.apply(node, a);
        n++;
      }
      const over = node.stage === 'over';
      out.rows.push({ id: p.id, k, ctx: p.ctx, start: { o: p.state.o, x: p.state.x, ball: p.state.ball }, points: over ? E.scoreTotal(node) : 0, value: over ? E.terminalValue(node) : 0,
        decisions: n, fouls: node.fouls, bonus5: node.bonus5, result: over ? node.result : null, end: [over && node.result ? node.result.kind : 'unfinished', node.clock, node.tok_o],
        endX: over ? sqs(node.x) : null, events, shots, reads, stances: job.stances ? stances : undefined, dribbles: job.stances ? dribbles : undefined, examples: job.stances ? examples : undefined, guards: job.stances ? guards : undefined });
    }
  }
} else if (job.kind === 'split') {
  // step 18i: an action's value in its parts. p.pre: the turn up to and including the action that rolls (a Steal).
  // Each way the roll can come out: its chance and what the possession is then worth to the offence (finished: its
  // score with the foul situation's cost; still going: the policy's own search from there).
  for (const p of job.positions) {
    let node = state(p);
    const ctx = ctxs[p.ctx], parts = [];
    for (const aj of p.pre) {
      const want = JSON.stringify(aj), a = E.isChance(node) ? null : E.legalActions(node).find(x => key(x) === want);
      if (!a) { node = null; break; }
      node = E.apply(node, a);
    }
    const walk = (n, pr, label) => {
      if (E.isChance(n)) { for (const o of n.outcomes) if (o[0] > 0) walk(o[2], pr * o[0], label ? label + ' / ' + o[1] : o[1]); return; }
      const v = n.stage === 'over' ? E.terminalValue(n) : searchAt(n, ctx, job.policies.p).results[0][0];
      parts.push({ label, p: pr, value: v, over: n.stage === 'over', fouls: n.fouls, bonus5: n.bonus5, ended: n.result ? n.result.kind : null });
    };
    if (node) walk(node, 1, '');
    out.rows.push({ id: p.id, parts });
  }
} else if (job.kind === 'search') {
  // one search per position per policy: every root turn with its value, the look-ahead reached, the time
  for (const p of job.positions) {
    // p.pre (step 18g): a turn played first (its actions need no dice), so the reply to a candidate can be read
    const s = p.pre ? playTurn(state(p), p.pre, rng(1)) : state(p), ctx = ctxs[p.ctx], row = { id: p.id, side: E.actor(s), by: {} };
    for (const [name, pol] of Object.entries(job.policies)) {
      const o = searchAt(s, ctx, pol);
      row.by[name] = { results: o.results, reached: o.reached, seconds: o.seconds, explain: o.explain, same_top: o.same_top };
    }
    out.rows.push(row);
  }
}
out.seconds = (Date.now() - t0) / 1000;
fs.writeFileSync(process.argv[3], JSON.stringify(out));
