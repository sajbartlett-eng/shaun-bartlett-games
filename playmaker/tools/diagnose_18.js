// Step 18a: the candidate diagnosis. For one decision: what the search's own list of team turns holds, and what it
// leaves out. On engine.js (the app's search).
//   node tools/diagnose_18.js job.json out.json
// job: { state, ctx, profile, judge: {name, ...}, keep, keep_accepted, cap_s, switches: {play_on: true, ...} }
// The search builds its list in stages: (1) a short list of each side's actions (candidateActions); (2) the best few
// of those are followed by a second action; (3) the best `beam` turns by the one-action reading are kept. This tool
// rebuilds those stages (and checks its rebuild gives the engine's own list), then values EVERY legal team turn one
// team turn ahead, and the best `keep` of them (and the best `keep_accepted` the board accepts) 1 pair ahead, with
// the search's own replies. So for any turn it can say: was it on the list, where was it cut, and does it win when
// it is searched.
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
const CONFIG = load('ai_profiles.json');
E.init({ zones: load('court_zones.json'), config: CONFIG, vcoarse: load('vcoarse.json'), learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null });
const [VMIN, VMAX] = CONFIG.eval.value_bounds;
const MOVEMENT = new Set(['move', 'qs', 'sprint']);
const now = () => Date.now() / 1000;
const xy = i => { const n = E.sqName(i); return [n.charCodeAt(0) - 65, parseInt(n.slice(1), 10)]; };
const cheb = (a, b) => { const p = xy(a), q = xy(b); return Math.max(Math.abs(p[0] - q[0]), Math.abs(p[1] - q[1])); };
const turnKey = t => t.length === 2 && MOVEMENT.has(t[0].kind) && MOVEMENT.has(t[1].kind) ? 'S' + [t[0].id, t[1].id].sort((p, q) => p - q).join(',') : 'T' + t.map(a => a.id).join(',');
const tj = t => t.map(a => E.actionJSON(a));
const words = t => t.map(a => E.actionStr(a)).join(', then ');

// The boards' judges that read only the turn (word for word from exam.py; the Python judge re-checks every turn this
// tool reports). A judge that needs the computer's reading (board 1) is done in Python on the reported turns; here it
// has a stand-in that only picks which turns to report.
function judgeOf(j, s) {
  const mv = a => MOVEMENT.has(a.kind);
  if (j.name === 'help_and_rotate') return (t, n) => {            // board 3
    if (E.isChance(n)) return false;
    const movers = [...new Set(t.filter(mv).map(a => a.piece))];
    const helper = movers.filter(k => cheb(n.x[k], n.o[0]) <= 1 && cheb(s.x[k], s.o[0]) > 1);
    return helper.length > 0 && movers.some(k => !helper.includes(k));
  };
  if (j.name === 'acts_at_once') return t => t[0].piece === j.piece && (t[0].kind === 'shot' || t[0].kind === 'dribble' || mv(t[0]));   // board 6
  if (j.name === 'cut') return t => t.some(a => a.piece === j.piece && mv(a) && j.rim[E.sqName(a.dest)] <= j.rim[E.sqName(s.o[j.piece])] - 2);   // board 8
  if (j.name === 'kick_or_relocate') return t => t.some(a => (a.kind === 'pass' && a.target === j.piece) || (a.piece === j.piece && mv(a)));     // board 9
  if (j.name === 'steal') return t => t.some(a => a.kind === 'steal');
  if (j.name === 'no_steal') return t => !t.some(a => a.kind === 'steal');
  if (j.name === 'no_pass_to') return t => !t.some(a => a.kind === 'pass' && a.target === j.piece);
  if (j.name === 'pass') return t => t.some(a => a.kind === 'pass');
  if (j.name === 'drive_closer') return (t, n) => t[0].kind !== 'shot' && !E.isChance(n) && n.stage !== 'over' && t.some(a => a.piece === j.piece && (mv(a) || a.kind === 'dribble')) && j.rim[E.sqName(n.o[j.piece])] < j.rim[E.sqName(s.o[j.piece])];   // board 5, closed out
  if (j.name === 'shot_or_move') return t => t[0].kind === 'shot' || (!t.some(a => a.kind === 'shot') && t.some(a => a.piece === j.piece && (mv(a) || a.kind === 'dribble')));   // board 5, stopped short: a stand-in (the open spot is judged in Python)
  if (j.name === 'first_not_shot') return t => t[0].kind !== 'shot';
  if (j.name === 'first_shot') return t => t[0].kind === 'shot';
  if (j.name === 'on_lane') {                                      // board 1's stand-in: a defender steps onto the ball-rim line near the ball
    const lane = new Set(j.lane);
    return (t, n) => !E.isChance(n) && t.some(a => mv(a) && lane.has(E.sqName(a.dest)) && cheb(a.dest, s.o[s.ball]) <= 3);
  }
  return null;
}

const job = JSON.parse(fs.readFileSync(process.argv[2]));
if (job.settle_shots !== undefined && E.setSettle) E.setSettle(job.settle_shots);      // step 18b
if (job.switches) E.setSearch(Object.assign({ stable: false, quiet_points: false, like_with_like: true, tempo: false, play_on: false, clear_reason: false }, job.switches));
const ctx = E.makeCtx(job.ctx), s = E.stateFrom(job.state, ctx);
const me = E.actor(s), sign = me === 'O' ? 1 : -1;
const t0 = now(), cap = t0 + (job.cap_s || 1200);
const prof = job.profile;
const srch = new E.Searcher(me, prof, E.makeEvaluate(prof, me, null), Infinity);
const endsTurn = (st, nxt) => E.isChance(nxt) || nxt.stage === 'over' || E.actor(nxt) !== me || nxt.stage !== st.stage;
const judge = judgeOf(job.judge || {}, s);

// ---- the search's own list, stage by stage (turns() in engine.js, rebuilt) ------------------------------------------
const rootRead = new E.Read(s, { exact: true });
const legal = E.legalActions(s);
const cand = E.candidateActions(s, rootRead);
const candIds = new Set(cand.map(a => a.id));
const scored = cand.map(a => [sign * srch.quick(E.apply(s, a)), [a]]);
scored.sort((x, y) => y[0] - x[0]);
const beam = prof.beam, nexp = Math.max(3, Math.floor(beam / 3));
const pool = scored.slice(0, beam);
const followed = new Map();                             // first action id -> the ids of the second actions generated
scored.slice(0, nexp).forEach(([, t]) => {
  const a = t[0], nxt = E.apply(s, a);
  if (endsTurn(s, nxt)) return;
  const seconds = new Set();
  for (const b of E.candidateActions(nxt, null, 2)) {
    if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;
    seconds.add(b.id);
    pool.push([sign * srch.quick(E.apply(nxt, b)), [a, b]]);
  }
  followed.set(a.id, seconds);
});
pool.sort((x, y) => y[0] - x[0]);
const rank = new Map(), list = [];
for (const [v, t] of pool) { const k = turnKey(t); if (!rank.has(k)) { rank.set(k, rank.size); if (list.length < beam) list.push([v, t]); } }
const own = E.turns(s, beam, rootRead, n => srch.quick(n), null, null, 2);
const rebuilt_equal = own.length === list.length && own.every((r, k) => turnKey(r[1]) === turnKey(list[k][1]));

// where a turn stands: 4 on the list; 3 generated but ranked below the list's length; 2 its second action wasn't
// generated; 1 its first action was generated but not followed by a second; 0 its first action wasn't generated
function stage(t) {
  const k = turnKey(t);
  if (rank.has(k)) return rank.get(k) < list.length ? [4, rank.get(k) + 1] : [3, rank.get(k) + 1];
  if (t.length === 1) return candIds.has(t[0].id) ? [3, scored.findIndex(r => r[1][0].id === t[0].id) + 1] : [0, null];   // a single action below the list's length among the single actions
  let best = 0;
  for (const [a, b] of (k[0] === 'S' ? [[t[0], t[1]], [t[1], t[0]]] : [[t[0], t[1]]])) {
    if (!candIds.has(a.id)) continue;
    best = Math.max(best, followed.has(a.id) ? 2 : 1);
  }
  return [best, null];
}
const STAGES = ['first action not generated', 'first action not followed by a second', 'second action not generated', 'generated, cut by the list\'s length', 'on the list'];

// one team turn ahead, as the search's own root reads it (Searcher.root)
const v1 = n => (srch.quiet || srch.playOn) ? srch.value(n, srch.childDepth(s, n, 1), VMIN, VMAX) : E.isChance(n) ? srch.value(n, 0, VMIN, VMAX) : (n.stage === 'over' ? E.terminalValue(n) : srch.leaf(n));
const v2 = n => srch.value(n, srch.childDepth(s, n, 2), VMIN, VMAX);

// ---- every legal team turn, one team turn ahead -------------------------------------------------------------------
const all = [];                                          // [v1 (the side's own view), turn, accepted]
const seen = new Set();
const tally = [0, 0, 0, 0, 0], tallyAcc = [0, 0, 0, 0, 0];
let capped = false, nAcc = 0;
const visit = (t, n) => {
  const k = turnKey(t);
  if (seen.has(k)) return;
  seen.add(k);
  const acc = judge ? !!judge(t, n) : null;
  const st = stage(t)[0];
  tally[st]++;
  if (acc) { tallyAcc[st]++; nAcc++; }
  all.push([sign * v1(n), t, acc]);
};
outer:
for (const a of legal) {
  const n1 = E.apply(s, a);
  visit([a], n1);
  if (a.kind === 'end_turn' || a.kind === 'forfeit' || endsTurn(s, n1)) continue;
  for (const b of E.legalActions(n1)) {
    if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;
    if (now() > cap) { capped = true; break outer; }
    visit([a, b], E.apply(n1, b));
  }
}
const tEnum = now() - t0;
all.sort((x, y) => y[0] - x[0]);
all.forEach((r, k) => r.push(k + 1));                    // the rank by the one-turn reading

// ---- the best of them, 1 pair ahead (the search's own replies) ----------------------------------------------------------
const pick = new Map();
const take = r => { const k = turnKey(r[1]); if (!pick.has(k)) pick.set(k, r); };
const byKey = new Map(all.map(r => [turnKey(r[1]), r]));
for (const [, t] of list) take(byKey.get(turnKey(t)));
all.slice(0, job.keep || 300).forEach(take);
let ka = 0;
for (const r of all) { if (r[2]) { take(r); if (++ka >= (job.keep_accepted || 50)) break; } }
const rows = [];
for (const r of pick.values()) {
  const [w1, t, acc, rk] = r, n = E.playTurn(s, t, false), st = stage(t);
  rows.push({ turn: tj(t), words: words(t), one_turn: sign * w1, one_turn_rank: rk, pair: v2(n), stage: st[0], where: STAGES[st[0]], list_rank: st[1], accepted: acc });
}
rows.sort((x, y) => sign * (y.pair - x.pair));
const out = {
  side: me, legal_first_actions: legal.length, generated_first_actions: cand.length, followed_first_actions: followed.size,
  generated_turns: rank.size, list_length: list.length, rebuilt_equal, all_turns: all.length, capped,
  turns_by_stage: Object.fromEntries(STAGES.map((n, k) => [n, tally[k]])),
  accepted_turns: judge ? nAcc : null, accepted_by_stage: judge ? Object.fromEntries(STAGES.map((n, k) => [n, tallyAcc[k]])) : null,
  judge: (job.judge || {}).name || null, rows, seconds: now() - t0, seconds_enumerating: tEnum,
};
fs.writeFileSync(process.argv[3], JSON.stringify(out));
