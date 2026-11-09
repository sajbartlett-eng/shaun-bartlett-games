"""Step 3m: decision times by difficulty on a throttled phone profile (the static build, Pyodide in a Web Worker,
Chromium at 412 x 915 with a 4x CPU throttle). Reads each computer decision's seconds, search depth and leaves from
the game log. Needs the Pyodide npm package (tests/.pyodide) and Playwright.

  python3 tools/phone_timing.py [out.json]
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

NODE = r"""
const { chromium } = require('playwright');
const [base] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 412, height: 915 } });
  const p = await ctx.newPage();
  const cdp = await ctx.newCDPSession(p);
  await cdp.send('Emulation.setCPUThrottlingRate', { rate: 4 });
  await p.goto(`${base}/site/index.html?pyodide=${base}/pyodide/`);
  await p.waitForFunction(() => !document.getElementById('loading'), null, { timeout: 600000 });
  const out = {};
  for (const level of ['rookie', 'starter', 'allstar']) {
    out[level] = await p.evaluate(async (level) => {
      const t0 = performance.now();
      const g = await window.PM_BACKEND('/api/new', { mode: 'hotseat', ai: { A: level, B: level }, level: 'learn', seed: 3, teams: ['Five Out', 'High-Low'] });
      const wall = (performance.now() - t0) / 1000;
      const log = await window.PM_BACKEND(`/api/log?code=${g.code}`);
      const decs = log.filter(r => r.type === 'computer' && r.event === 'decision');
      return { wall, decisions: decs.map(d => ({ seconds: d.seconds, depth: d.depth, partial: d.partial, leaves: d.leaves })) };
    }, level);
  }
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def main(out_path=None):
    from playmaker_web.build_site import build
    pyo = os.path.join(ROOT, 'tests', '.pyodide', 'node_modules', 'pyodide')
    root = tempfile.mkdtemp()
    build(os.path.join(root, 'site'), os.path.join(root, 'dist'))
    shutil.copytree(pyo, os.path.join(root, 'pyodide'))
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=root))
    httpd.RequestHandlerClass.log_message = lambda *a: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{httpd.server_address[1]}'
    js = os.path.join(root, 'timing.js')
    open(js, 'w').write(NODE)
    r = subprocess.run(['node', js, base], capture_output=True, text=True, timeout=3600, cwd=root)
    httpd.shutdown()
    if r.returncode:
        raise SystemExit(r.stderr[-2000:])
    data = json.loads(r.stdout.strip().splitlines()[-1])
    rows = {}
    for lv, d in data.items():
        ds = d['decisions']
        secs = sorted(x['seconds'] for x in ds)
        deps = sorted(x['depth'] for x in ds)
        rows[lv] = dict(decisions=len(ds), median_s=secs[len(secs) // 2] if secs else None, max_s=max(secs) if secs else None,
                        depth=max((x['depth'] for x in ds), default=0), median_depth=deps[len(deps) // 2] if deps else 0,
                        leaves_per_s=round(sum(x['leaves'] for x in ds) / max(1e-9, sum(x['seconds'] for x in ds)), 1))
    print(json.dumps(rows, indent=1))
    if out_path:
        json.dump(dict(rows=rows, raw=data), open(out_path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
