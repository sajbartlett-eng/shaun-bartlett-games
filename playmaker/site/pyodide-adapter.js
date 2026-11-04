// In-browser back end: runs the unchanged Python engine and API in Pyodide, behind the same calls
// the server answers. Loaded only by the static build (site/ and dist/playmaker.html).
'use strict';
(function () {
  const PYODIDE_VERSION = '0.26.4';
  const params = new URLSearchParams(location.search);
  const base = params.get('pyodide') || `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`;
  const overlay = document.createElement('div');
  overlay.id = 'loading';
  overlay.innerHTML = '<div><h2>Loading the rules engine…</h2><p>About 10 MB the first time; it is cached after that.</p></div>';
  document.addEventListener('DOMContentLoaded', () => document.body.append(overlay));
  const loadScript = src => new Promise((res, rej) => { const s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = () => rej(new Error('could not load ' + src)); document.head.append(s); });
  const ready = (async () => {
    await loadScript(base + 'pyodide.js');
    const py = await loadPyodide({ indexURL: base });
    const bundle = window.PM_BUNDLE || await (await fetch('engine_bundle.json')).json();
    for (const [path, text] of Object.entries(bundle.files)) {
      const parts = ('/pm/' + path).split('/'); let dir = '';
      for (const part of parts.slice(1, -1)) { dir += '/' + part; try { py.FS.mkdir(dir); } catch (e) { /* exists */ } }
      py.FS.writeFile('/pm/' + path, text);
    }
    py.runPython("import sys, os\nsys.path.insert(0, '/pm')\nos.chdir('/pm')\nfrom playmaker_web.api import dispatch as pm_dispatch");
    overlay.remove();
    return py.globals.get('pm_dispatch');
  })();
  ready.catch(e => { overlay.innerHTML = `<div><h2>Could not start the engine</h2><p>${e.message}</p></div>`; });
  window.PM_BACKEND = async (path, body) => {
    const dispatch = await ready;
    const [p, qs] = path.split('?');
    const q = Object.fromEntries(new URLSearchParams(qs || ''));
    const out = JSON.parse(dispatch(body ? 'POST' : 'GET', p, JSON.stringify(q), JSON.stringify(body || {})));
    if (out.status !== 200) throw new Error(out.body.error || 'error');
    return out.body;
  };
})();
