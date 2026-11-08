// In-browser back end: runs the unchanged Python engine and API in Pyodide, behind the same calls the server
// answers. Loaded only by the static build (site/ and dist/playmaker.html). Step 3m: the engine runs in a Web
// Worker, so the page stays responsive while the computer searches (an anytime search: its time budget holds).
'use strict';
(function () {
  const PYODIDE_VERSION = '0.26.4';
  const params = new URLSearchParams(location.search);
  const base = new URL(params.get('pyodide') || `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`, location.href).href;
  const overlay = document.createElement('div');
  overlay.id = 'loading';
  overlay.innerHTML = '<div><h2>Loading the rules engine…</h2><p>About 10 MB the first time; it is cached after that.</p></div>';
  document.addEventListener('DOMContentLoaded', () => document.body.append(overlay));
  // the worker's source, inlined so the single-file build needs nothing but the Pyodide CDN
  const WORKER = `
    let dispatch = null;
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
