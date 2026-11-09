// Step 9: the exam evidence searches, on engine.js (the app's search, proved equal to search.Searcher by
// tools/js_equivalence.py). One JSON request per line on stdin, one reply line on stdout (as tools/js_server.js).
//
// request: {state, ctx, profile, depths: [d, ...], cap_s, accepted: [turn], keep, extra: [turn]}
//   turn: [[kind, side, piece, dest, arrow, target, shot], ...] (jsbridge's action form)
// reply:   {first: [[value, i]] one move ahead for every accepted turn (sorted, the side's best first),
//           depths: [{depth, seconds, top: [[value, turn]], kept: [[value, i]], extra: [[value, i]]}],
//           capped: depth or null, reached_in_cap: deepest root reached when capped}
// Values are the offence's view, in game points. A depth is listed only when the root and every kept accepted turn
// were searched to it within the cap.
'use strict';
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
const CONFIG = load('ai_profiles.json');
E.init({ zones: load('court_zones.json'), config: CONFIG, vcoarse: load('vcoarse.json') });
const [VMIN, VMAX] = CONFIG.eval.value_bounds;
const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000;   // the engine's own clock

// legal actions by JSON form, cached per position (accepted lists run to tens of thousands of turns)
const LEGAL = new Map();
function legalMap(s) {
  const z = E.zobrist(s);
  let m = LEGAL.get(z);
  if (!m) { m = new Map(E.legalActions(s).map(a => [JSON.stringify(E.actionJSON(a)), a])); LEGAL.set(z, m); }
  return m;
}
const NEXT = new Map();
function turnFrom(s, tj) {
  const out = [];
  let node = s;
  for (const j of tj) {
    if (E.isChance(node) || node.stage === 'over') break;
    const key = JSON.stringify(j);
    const a = legalMap(node).get(key);
    if (!a) throw new Error('not legal: ' + key);
    out.push(a);
    const nk = E.zobrist(node) + '|' + key;
    let nx = NEXT.get(nk);
    if (nx === undefined) { nx = E.apply(node, a); if (out.length === 1) NEXT.set(nk, nx); }
    node = nx;
  }
  return out;
}

function evidence(req) {
  E.setLeafMode(req.leaf_mode || 'floor');           // step 10: the leaf's mode
  const ctx = E.makeCtx(req.ctx);
  const s = E.stateFrom(req.state, ctx);
  const me = E.actor(s), sign = me === 'O' ? 1 : -1;
  const t0 = now();
  const srch = new E.Searcher(me, req.profile, E.makeEvaluate(req.profile, me, null), t0 + req.cap_s);
  const acc = req.accepted.map(tj => turnFrom(s, tj));
  const extra = (req.extra || []).map(tj => turnFrom(s, tj));
  const valueAt = (t, d) => {
    const n = E.playTurn(s, t, false);
    if (d <= 1) return E.isChance(n) ? srch.value(n, 0, VMIN, VMAX) : (n.stage === 'over' ? E.terminalValue(n) : srch.leaf(n));
    return srch.value(n, d - 1, VMIN, VMAX);
  };
  // one move ahead for every accepted turn, to pick the ones worth searching deeper
  const first = [];
  const firstEnd = t0 + (req.first_cap_s || req.cap_s / 3);
  let firstDone = acc.length;
  for (let i = 0; i < acc.length; i++) {
    if (now() > firstEnd) { firstDone = i; break; }
    first.push([valueAt(acc[i], 1), i, srch.quick(E.playTurn(s, acc[i], false))]);
  }
  // the best one move ahead first; ties (common: the phase table is the floor of the read) broken by the search's own
  // ordering read, as the search orders its turns
  first.sort((a, b) => sign * (b[0] - a[0]) || sign * (b[2] - a[2]));
  const kept = first.slice(0, req.keep).map(r => r[1]);
  const out = { first: first.slice(0, 50), n_accepted: acc.length, n_first: firstDone, depths: [], capped: null, reached_in_cap: null };
  for (const d of req.depths) {
    const td = now();
    const [res, reached] = srch.root(s, d);
    if (reached < d) { out.capped = d; out.reached_in_cap = reached; break; }
    try {
      const kv = kept.map(i => [valueAt(acc[i], d), i]);
      const xv = extra.map((t, i) => [valueAt(t, d), i]);
      out.depths.push({ depth: d, seconds: now() - td, top: res.slice(0, 10).map(([v, t]) => [v, t.map(E.actionJSON)]),
        n_root: res.length, kept: kv, extra: xv });
    } catch (e) {
      if (!e || !e.timeout) throw e;
      out.capped = d; out.reached_in_cap = d;      // the root reached it, but not every accepted turn
      break;
    }
  }
  out.seconds = now() - t0;
  return out;
}

const rl = readline.createInterface({ input: process.stdin });
rl.on('line', ln => {
  let out;
  try { out = { ok: evidence(JSON.parse(ln)) }; } catch (e) { out = { error: String(e && e.stack || e) }; }
  process.stdout.write(JSON.stringify(out) + '\n');
});
