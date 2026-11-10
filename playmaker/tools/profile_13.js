// Step 13 A3: where a search's time goes. Runs the requests (tools/exam_13.py dump) with the given switches, with
// V8's sampling profiler, and prints each part's share: its own time by function, and the time under chosen functions.
//   node tools/profile_13.js requests.json '{"play_on":true}' <reach true|false> [out.json] [budget]
'use strict';
const fs = require('fs');
const path = require('path');
const inspector = require('inspector');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), learned: fs.existsSync(path.join(root, 'learned_weights.json')) ? load('learned_weights.json') : null });
const reqs = JSON.parse(fs.readFileSync(process.argv[2]));
E.setSearch(process.argv[3] || '{}');
E.setReach(process.argv[4] === 'true');
if (process.argv[6]) E.setBudget(process.argv[6] === 'budget');   // step 13 B: coverage as a budget
const UNDER = ['extend', 'unsettled', 'turnsOf', 'turns', 'quick', 'leaf', 'evaluate', 'Read', 'cover', 'responses', '_looks', '_contest',
  'defenderReachExact', 'exactOne', 'laneP', 'legalActions', 'apply', 'movementDests', 'candidateActions', 'chance', 'zobrist',
  'attackerReachExact', 'contestMap', 'twoActions', 'budget', 'budgetTables', 'lpMax', 'possession', 'shotNow', 'continuation', 'isLegal', 'playTurn', 'pathsTo', 'blocksPath'];
const session = new inspector.Session();
session.connect();
session.post('Profiler.enable', () => session.post('Profiler.start', () => {
  const t0 = Date.now(), per = {};
  for (const [name, req] of Object.entries(reqs)) {
    const t = Date.now();
    const o = E.search(req);
    per[name] = { seconds: (Date.now() - t) / 1000, leaves: o.leaves, nodes: o.nodes, extensions: o.extensions, reached: o.reached };
  }
  const total = (Date.now() - t0) / 1000;
  session.post('Profiler.stop', (err, { profile }) => {
    const byId = new Map(profile.nodes.map(n => [n.id, n]));
    const parent = new Map();
    for (const n of profile.nodes) for (const c of n.children || []) parent.set(c, n.id);
    const self = new Map(), under = new Map();
    let all = 0;
    for (const n of profile.nodes) {
      const h = n.hitCount || 0;
      if (!h) continue;
      all += h;
      const f = n.callFrame.functionName || '(anonymous)';
      self.set(f, (self.get(f) || 0) + h);
      const seen = new Set();
      for (let id = n.id; id !== undefined; id = parent.get(id)) seen.add(byId.get(id).callFrame.functionName);
      for (const u of UNDER) if (seen.has(u)) under.set(u, (under.get(u) || 0) + h);
    }
    const pct = h => Math.round(1000 * h / all) / 10;
    const out = { seconds: total, boards: per,
      own_time: [...self].sort((a, b) => b[1] - a[1]).slice(0, 30).map(([f, h]) => [f, pct(h)]),
      time_under: [...under].sort((a, b) => b[1] - a[1]).map(([f, h]) => [f, pct(h)]) };
    if (process.argv[5]) fs.writeFileSync(process.argv[5], JSON.stringify(out, null, 1));
    console.log(JSON.stringify(out, null, 1));
  });
}));
