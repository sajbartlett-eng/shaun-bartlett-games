// Fix 4f: one worker of tools/engine_pool.js: the same engine and data, reading the batches it is given.
const fs = require('fs'), path = require('path');
const { parentPort, workerData } = require('worker_threads');
const root = workerData.root, flag = new Int32Array(workerData.sab, 0, 2), buf = new Uint8Array(workerData.sab, 8);
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: process.env.PM_SEGMENTS ? JSON.parse(fs.readFileSync(process.env.PM_SEGMENTS)) : load('segments.json'),
  learned: fs.existsSync(path.join(root, 'playmaker_engine', 'data', 'learned_weights.json')) ? load('learned_weights.json') : null });
E._worker(true);
const enc = new TextEncoder();
parentPort.on('message', text => {
  const out = enc.encode(E.workJSON(text));
  if (out.length > buf.length) { Atomics.store(flag, 0, 2); Atomics.notify(flag, 0); return; }
  buf.set(out); Atomics.store(flag, 1, out.length); Atomics.store(flag, 0, 1); Atomics.notify(flag, 0);
});
