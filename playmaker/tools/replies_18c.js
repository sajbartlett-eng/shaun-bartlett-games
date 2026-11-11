// Step 18c, part 1: boards 1 and 3 taken apart. For a defence turn: what the search believes the offence's best
// reply is worth (from the reply list it searches), against the offence's best reply when every legal reply is read.
//   node tools/replies_18c.js job.json out.json
// job: { state, ctx, profile, turns: [{name, turn}], settle_shots, help_readings, keep }
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
const job = JSON.parse(fs.readFileSync(process.argv[2]));
if (job.settle_shots != null && E.setSettle) E.setSettle(job.settle_shots);
if (job.help_readings != null && E.setHelp) E.setHelp(job.help_readings);
const ctx = E.makeCtx(job.ctx), s = E.stateFrom(job.state, ctx), me = E.actor(s);
const key = a => JSON.stringify(E.actionJSON(a));
const words = t => t.map(a => E.actionStr(a)).join(', then ');
const turnKey = t => t.length === 2 && MOVEMENT.has(t[0].kind) && MOVEMENT.has(t[1].kind) ? 'S' + [t[0].id, t[1].id].sort((p, q) => p - q).join(',') : 'T' + t.map(a => a.id).join(',');
const srch = new E.Searcher(me, job.profile, E.makeEvaluate(job.profile, me, null), Infinity);
const out = { side: me, rows: [] };
for (const item of job.turns) {
  let n = s;
  for (const aj of item.turn) { const want = JSON.stringify(aj); n = E.apply(n, E.legalActions(n).find(a => key(a) === want)); }
  const row = { name: item.name, after: E.isChance(n) ? 'a roll' : n.stage + ', ' + E.actor(n) + ' to act', read_now: E.isChance(n) ? null : srch.leaf(n) };
  if (!E.isChance(n) && n.stage === 'play') {
    const side = E.actor(n), sign = side === 'O' ? 1 : -1;
    const v0 = st => srch.value(st, 0, VMIN, VMAX);
    // the replies the search looks at
    const list = srch.turnsOf(n).map(([q, t]) => [v0(E.playTurn(n, t)), t, q]);
    list.sort((x, y) => sign * (y[0] - x[0]));
    const inList = new Set(list.map(r => turnKey(r[1])));
    row.searched_replies = list.length;
    row.best_searched_reply = { words: words(list[0][1]), value: list[0][0] };
    // every legal reply
    const all = [], seen = new Set();
    for (const a of E.legalActions(n)) {
      const n1 = E.apply(n, a);
      const one = [a]; if (!seen.has(turnKey(one))) { seen.add(turnKey(one)); all.push([v0(n1), one]); }
      if (a.kind === 'end_turn' || a.kind === 'forfeit' || E.isChance(n1) || n1.stage === 'over' || E.actor(n1) !== side || n1.stage !== n.stage) continue;
      for (const b of E.legalActions(n1)) {
        if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;
        const t = [a, b], k = turnKey(t); if (seen.has(k)) continue; seen.add(k);
        all.push([v0(E.apply(n1, b)), t]);
      }
    }
    all.sort((x, y) => sign * (y[0] - x[0]));
    row.legal_replies = all.length;
    row.best_legal_reply = { words: words(all[0][1]), value: all[0][0], searched: inList.has(turnKey(all[0][1])) };
    row.hidden = sign * (all[0][0] - list[0][0]);        // what the reply list hides from the side that moved
    row.better_than_searched = all.filter(r => sign * (r[0] - list[0][0]) > 0.005).length;
    row.top_legal = all.slice(0, job.keep || 6).map(r => ({ words: words(r[1]), value: r[0], searched: inList.has(turnKey(r[1])) }));
  }
  out.rows.push(row);
}
fs.writeFileSync(process.argv[3], JSON.stringify(out, null, 1));
