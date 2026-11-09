// Reads JSON lines {state, ctx} on stdin and writes engine.js's probe of each (tools/js_equivalence.py compares them
// with the Python engine's).
'use strict';
const fs = require('fs');
const path = require('path');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const vc = JSON.parse(fs.readFileSync(path.join(root, 'vcoarse.json')));
E.init({ zones: JSON.parse(fs.readFileSync(path.join(root, 'court_zones.json'))), config: JSON.parse(fs.readFileSync(path.join(root, 'ai_profiles.json'))), vcoarse: vc });
const lines = fs.readFileSync(0, 'utf8').split('\n').filter(Boolean);
const out = [];
for (const ln of lines) {
  const q = JSON.parse(ln);
  try {
    if (q.search) out.push(JSON.stringify(E.search(q.search)));
    else out.push(JSON.stringify(E.probe(q.state, q.ctx)));
  } catch (e) { out.push(JSON.stringify({ error: String(e && e.stack || e) })); }
}
process.stdout.write(out.join('\n') + '\n');
