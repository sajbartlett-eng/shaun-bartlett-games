// In-browser back end: runs the unchanged Python engine and API in Pyodide, behind the same calls the server
// answers. Loaded only by the static build (site/ and dist/playmaker.html). Step 3m: the engine runs in a Web
// Worker, so the page stays responsive while the computer searches (an anytime search: its time budget holds).
'use strict';
(function () {
  const PYODIDE_VERSION = '0.26.4';
  const params = new URLSearchParams(location.search);
  if (params.get('speedtest')) return;                    // step 13C: the speed test runs instead of the game (speedtest.js)
  const base = new URL(params.get('pyodide') || `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`, location.href).href;
  const overlay = document.createElement('div');
  overlay.id = 'loading';
  overlay.innerHTML = '<div><h2>Loading the rules engine…</h2><p>About 10 MB the first time; it is cached after that.</p></div>';
  document.addEventListener('DOMContentLoaded', () => document.body.append(overlay));
  // the worker's source, inlined so the single-file build needs nothing but the Pyodide CDN
  const WORKER = `
    let dispatch = null;
    // fix 4f (Shaun, 28 Nov 2026): several cores. Each sub-worker is the same engine with the same data; engine.js hands
    // it a batch of independent readings and waits for the answers in shared memory, so the decision is the one a single
    // core makes. Shared memory needs the page to be cross-origin isolated; without it the engine reads on one core.
    const SUB = "self.onmessage = (ev) => { const m = ev.data; if (m.type === 'init') { self.PMEngine.init(m.data); self.PMEngine._worker(true); if (m.qsab) self.PMEngine._queue(m.qsab); self.F = new Int32Array(m.sab, 0, 2); self.B = new Uint8Array(m.sab, 8); self.postMessage('ready'); return; }" +
      " const out = new TextEncoder().encode(self.PMEngine.workJSON(m.text)); if (out.length > self.B.length) { Atomics.store(self.F, 0, 2); Atomics.notify(self.F, 0); return; }" +
      " self.B.set(out); Atomics.store(self.F, 1, out.length); Atomics.store(self.F, 0, 1); Atomics.notify(self.F, 0); };";
    // (it resolves once every sub-worker has started: a worker blocked waiting for them would never let them start)
    async function makeWebPool(engineJs, data, n) {
      const url = URL.createObjectURL(new Blob([engineJs, '\n', SUB], { type: 'text/javascript' })), ws = [], dec = new TextDecoder(), up = [];
      const qsab = new SharedArrayBuffer(4), q = new Int32Array(qsab);   // (fix 4i: the counter the sub-workers take readings from)
      for (let k = 0; k < n; k++) {
        const sab = new SharedArrayBuffer(8 + 32 * 1024 * 1024), w = new Worker(url);
        up.push(new Promise(res => { w.onmessage = () => res(); }));
        w.postMessage({ type: 'init', data, sab, qsab });
        ws.push({ w, flag: new Int32Array(sab, 0, 2), buf: new Uint8Array(sab, 8) });
      }
      await Promise.all(up);
      return { size: n, queue: true, resetQueue() { Atomics.store(q, 0, 0); }, runAll(texts) {
        for (let k = 0; k < texts.length; k++) { Atomics.store(ws[k].flag, 0, 0); ws[k].w.postMessage({ type: 'run', text: texts[k] }); }
        const out = [];
        for (let k = 0; k < texts.length; k++) {
          const { flag, buf } = ws[k];
          while (Atomics.load(flag, 0) === 0) Atomics.wait(flag, 0, 0, 1000);
          if (Atomics.load(flag, 0) === 2) throw new Error("a sub-worker's answer is larger than its room");
          out.push(dec.decode(buf.slice(0, Atomics.load(flag, 1))));
        }
        return out;
      } };
    }
    self.onmessage = async (ev) => {
      const m = ev.data;
      if (m.type === 'init') {
        try {
          importScripts(m.base + 'pyodide.js');
          const py = await loadPyodide({ indexURL: m.base });
          for (const [path, text] of Object.entries(m.bundle.files)) {
            const parts = ('/pm/' + path).split('/'); let dir = '';
            for (const part of parts.slice(1, -1)) { dir += '/' + part; try { py.FS.mkdir(dir); } catch (e) { /* exists */ } }
            py.FS.writeFile('/pm/' + path, text);
          }
          py.runPython("import sys, os\\nsys.path.insert(0, '/pm')\\nos.chdir('/pm')\\nfrom playmaker_web.api import dispatch as pm_dispatch");
          dispatch = py.globals.get('pm_dispatch');
          if (m.bundle.engine_js) {
            // step 3n: the search core in JavaScript; the Python agent calls it for each decision
            importScripts(URL.createObjectURL(new Blob([m.bundle.engine_js], { type: 'text/javascript' })));
            const f = m.bundle.files, dataf = n => JSON.parse(f['playmaker_engine/data/' + n]);
            const initData = { zones: dataf('court_zones.json'), config: dataf('ai_profiles.json'), vcoarse: dataf('vcoarse.json'), segments: dataf('segments.json'),
              learned: (() => { try { return dataf('learned_weights.json'); } catch (e) { return null; } })() };   // step 17
            self.PMEngine.init(initData);
            const cores = Math.min(4, (self.navigator && self.navigator.hardwareConcurrency) || 1);
            if (self.crossOriginIsolated && cores > 1) self.PMEngine.setPool(await makeWebPool(m.bundle.engine_js, initData, cores));   // (fix 4f)
            py.runPython("import js\\nfrom playmaker_engine import agent as _AG\\n_AG.JS['search'] = js.PMEngine.searchJSON\\n_AG.JS['goals'] = js.PMEngine.goalsJSON\\n_AG.JS['reads'] = js.PMEngine.readsJSON\\n_AG.JS['coverage'] = js.PMEngine.coverageJSON");
          }
          self.postMessage({ type: 'ready' });
        } catch (e) { self.postMessage({ type: 'failed', error: String(e && e.message || e) }); }
        return;
      }
      if (m.type === 'call') {
        try { self.postMessage({ type: 'reply', id: m.id, out: dispatch(m.method, m.path, m.query, m.body) }); }
        catch (e) { self.postMessage({ type: 'reply', id: m.id, out: JSON.stringify({ status: 500, body: { error: String(e && e.message || e) } }) }); }
      }
    };`;
  let worker = null, nextId = 1;
  const waiting = new Map();
  const ready = (async () => {
    const bundle = window.PM_BUNDLE || await (await fetch('engine_bundle.json')).json();
    worker = new Worker(URL.createObjectURL(new Blob([WORKER], { type: 'text/javascript' })));
    await new Promise((res, rej) => {
      worker.onmessage = ev => {
        const m = ev.data;
        if (m.type === 'ready') res();
        else if (m.type === 'failed') rej(new Error(m.error));
        else if (m.type === 'reply') { const w = waiting.get(m.id); waiting.delete(m.id); if (w) w(m.out); }
      };
      worker.postMessage({ type: 'init', base, bundle });
    });
    overlay.remove();
  })();
  ready.catch(e => { overlay.innerHTML = `<div><h2>Could not start the engine</h2><p>${e.message}</p></div>`; });
  window.PM_BACKEND = async (path, body) => {
    await ready;
    const [p, qs] = path.split('?');
    const q = Object.fromEntries(new URLSearchParams(qs || ''));
    const id = nextId++;
    const raw = await new Promise(res => { waiting.set(id, res); worker.postMessage({ type: 'call', id, method: body ? 'POST' : 'GET', path: p, query: JSON.stringify(q), body: JSON.stringify(body || {}) }); });
    const out = JSON.parse(raw);
    if (out.status !== 200) throw new Error(out.body.error || 'error');
    return out.body;
  };
})();
