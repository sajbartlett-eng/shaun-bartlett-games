'use strict';
// How good is the offence's reply list inside the search? For stored offence positions: the best reply value found by
// (A) today's reply list (whole turns, 3 firsts followed, ranked as ended turns), (B2a) the same but the firsts to
// follow chosen by the reading with the second action still in hand, (B2b) step 18e's list valued as ended turns,
// (C) today's root list (8 firsts followed).
const fs = require('fs'), path = require('path');
const PM = path.join(__dirname, '..');
const E = require(path.join(PM, 'playmaker_web/static/engine.js'));
const root = path.join(PM, 'playmaker_engine/data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
const CONFIG = load('ai_profiles.json');
E.init({ zones: load('court_zones.json'), config: CONFIG, vcoarse: load('vcoarse.json'), learned: load('learned_weights.json') });
const [VMIN, VMAX] = CONFIG.eval.value_bounds;
const job = JSON.parse(fs.readFileSync(process.argv[2]));
const prof = job.policies.allstar.profile;
if (E.setLevel) E.setLevel(prof.level);                // step 18h: read as the level's own search would
const ctxs = job.contexts.map(c => E.makeCtx(c));
const res = [];
for (const p of job.positions) {
  const s = E.stateFrom(p.state, ctxs[p.ctx]);
  if (s.stage !== 'play' || s.pending || E.actor(s) !== 'O' || s.turn_n !== 0) continue;
  const srch = new E.Searcher('X', prof, E.makeEvaluate(prof, 'X', null), Infinity);
  const quick = n => srch.quick(n);
  const lv = t => { const m = E.playTurn(s, t); return E.isChance(m) ? srch.value(m, 0, VMIN, VMAX) : srch.leaf(srch.playT(s, t)); };
  const best = ts => { let b = -1e9, bt = null; for (const [, t] of ts) { const v = lv(t); if (v > b) { b = v; bt = t; } } return [b, bt]; };
  if (E.setRankInHand) E.setRankInHand(false);        // step 18h: the list as step 18f's default built it (rank_in_hand is on since D-160)
  const A = best(E.turns(s, prof.beam, null, quick, null, 3, 1, srch.open, true, srch.width));
  if (E.setRankInHand) E.setRankInHand(true);
  const C = best(E.turns(s, prof.beam, null, quick, null, 8, 2, srch.open, true, srch.width));
  const B2b = best(E.turns(s, prof.beam, null, quick, null, 3, 1, srch.open, false, srch.width));
  // B2a: firsts to follow by the mid-turn reading; the list's values as today
  const first = E.candidateActions(s, null);
  const sc = first.map(a => { const nxt = E.apply(s, a); return [quick(nxt), quick(E.endedTurn(s, nxt)), a, nxt]; });
  const out = sc.slice().sort((x, y) => y[1] - x[1]).slice(0, prof.beam).map(x => [x[1], [x[2]]]);
  for (const [, , a, nxt] of sc.slice().sort((x, y) => y[0] - x[0]).slice(0, 3)) {
    if (E.isChance(nxt) || nxt.stage !== 'play' || E.actor(nxt) !== 'O') continue;
    for (const b of E.candidateActions(nxt, null, 1)) { if (b.kind === 'end_turn' || b.kind === 'forfeit') continue; out.push([quick(E.apply(nxt, b)), [a, b]]); }
  }
  out.sort((x, y) => y[0] - x[0]);
  const B2a = best(out.slice(0, prof.beam));
  res.push({ id: p.id, A: A[0], B2a: B2a[0], B2b: B2b[0], C: C[0], At: A[1].map(E.actionStr).join(' + '), Ct: C[1].map(E.actionStr).join(' + '), Bt: B2a[1].map(E.actionStr).join(' + '),
    Aj: A[1].map(E.actionJSON), Cj: C[1].map(E.actionJSON), state: p.state, ctx: job.contexts[p.ctx] });
}
const mean = k => res.reduce((a, r) => a + r[k], 0) / res.length;
const cnt = (k, d) => res.filter(r => r[k] - r.A > d).length, lose = (k, d) => res.filter(r => r.A - r[k] > d).length;
console.log('positions', res.length, 'mean best reply: A', mean('A').toFixed(3), 'B2a', mean('B2a').toFixed(3), 'B2b', mean('B2b').toFixed(3), 'C', mean('C').toFixed(3));
for (const k of ['B2a', 'B2b', 'C']) console.log(k, 'finds more than A by >0.5 on', cnt(k, 0.5), '; less by >0.5 on', lose(k, 0.5), '; mean gain', (mean(k) - mean('A')).toFixed(3));
fs.writeFileSync(process.argv[3], JSON.stringify(res, null, 1));
