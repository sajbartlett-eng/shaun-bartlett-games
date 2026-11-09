// A long-running engine.js for Python (jsbridge.NodeEngine): one JSON request per line on stdin
// ({fn: 'searchJSON' | 'goalsJSON', text}), one reply line on stdout.
'use strict';
const fs = require('fs');
const path = require('path');
const readline = require('readline');
const E = require(path.join(__dirname, '..', 'playmaker_web', 'static', 'engine.js'));
const root = path.join(__dirname, '..', 'playmaker_engine', 'data');
const load = n => JSON.parse(fs.readFileSync(path.join(root, n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json') });
const rl = readline.createInterface({ input: process.stdin });
rl.on('line', ln => {
  let out;
  try { const q = JSON.parse(ln); out = { ok: E[q.fn](q.text) }; } catch (e) { out = { error: String(e && e.stack || e) }; }
  process.stdout.write(JSON.stringify(out) + '\n');
});
