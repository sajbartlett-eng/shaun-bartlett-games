// Fix 4f (Shaun, 28 Nov 2026): several cores for engine.js in Node. Each worker is a thread with its own engine, given
// the same data; engine.js hands a batch of independent readings to the workers (PMEngine.setPool) and waits for all
// of them, then puts the results back in the batch's own order, so the decision is the one a single core makes.
//   const pool = require('./engine_pool.js').makePool(root, n);   E.setPool(pool);   ...   pool.close();
// The wait is synchronous (Atomics.wait on memory the workers share), because engine.js reads synchronously.
const path = require('path');
const { Worker } = require('worker_threads');
const CAP = 32 * 1024 * 1024;                          // the room for one worker's results (they are numbers and small lists)

function makePool(root, n) {
  const workers = [];
  for (let k = 0; k < n; k++) {
    const sab = new SharedArrayBuffer(8 + CAP), flag = new Int32Array(sab, 0, 2), buf = new Uint8Array(sab, 8);
    // (each worker held to the memory a phone's browser gives one engine: 256 MB, PM_WORKER_MB to change it)
    const w = new Worker(__filename.replace(/engine_pool\.js$/, 'engine_pool_worker.js'), { workerData: { root, sab }, resourceLimits: { maxOldGenerationSizeMb: +process.env.PM_WORKER_MB || 256 } });
    w.on('error', e => { Atomics.store(flag, 0, 3); Atomics.notify(flag, 0); console.error('engine worker failed:', e && e.message); });
    w.unref();
    workers.push({ w, flag, buf });
  }
  const dec = new TextDecoder();
  return {
    size: n,
    runAll(texts) {                                    // texts[k] to worker k, all at once; their answers in the same order
      for (let k = 0; k < texts.length; k++) { Atomics.store(workers[k].flag, 0, 0); workers[k].w.postMessage(texts[k]); }
      const out = [];
      for (let k = 0; k < texts.length; k++) {
        const { flag, buf } = workers[k];
        while (Atomics.load(flag, 0) === 0) Atomics.wait(flag, 0, 0, 1000);
        if (Atomics.load(flag, 0) === 2) throw new Error('a worker\'s answer is larger than its room');
        if (Atomics.load(flag, 0) === 3) throw new Error('a worker failed (out of memory?)');
        out.push(dec.decode(buf.slice(0, Atomics.load(flag, 1))));
      }
      return out;
    },
    close() { for (const x of workers) x.w.terminate(); },
  };
}
module.exports = { makePool };
