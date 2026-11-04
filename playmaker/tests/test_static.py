"""The no-install build: the same seeded game through the server and through Pyodide must give the
same log; and the phone layout must fit a Samsung Galaxy portrait screen."""
import json
import os
import shutil
import subprocess
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

import pytest

from playmaker_engine.policies import play, RandomPolicy
from playmaker_engine.scenarios import scenario_state
from playmaker_web.game import action_to_json
from playmaker_web.server import start_background
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PYODIDE_VERSION = '0.26.4'
VOLATILE = ('time', 'seconds')


def pyodide_dir():
    """A local copy of Pyodide for offline tests: $PYODIDE_DIR, or tests/.pyodide (installed from npm)."""
    d = os.environ.get('PYODIDE_DIR')
    if d and os.path.isfile(os.path.join(d, 'pyodide.js')):
        return d
    local = os.path.join(HERE, '.pyodide')
    target = os.path.join(local, 'node_modules', 'pyodide')
    if not os.path.isfile(os.path.join(target, 'pyodide.js')):
        os.makedirs(local, exist_ok=True)
        r = subprocess.run(['npm', 'install', '--prefix', local, f'pyodide@{PYODIDE_VERSION}', '--no-audit', '--no-fund'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            pytest.skip('Pyodide not available offline: ' + r.stderr[-200:])
    return target


@pytest.fixture(scope='module')
def static_site(tmp_path_factory):
    from playmaker_web.build_site import build
    root = tmp_path_factory.mktemp('static')
    build(str(root / 'site'), str(root / 'dist'))
    shutil.copytree(pyodide_dir(), str(root / 'pyodide'))
    httpd = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(root)))
    httpd.RequestHandlerClass.log_message = lambda *a: None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f'http://127.0.0.1:{httpd.server_address[1]}'
    yield base
    httpd.shutdown()


NODE_PARITY = r"""
const { chromium } = require('playwright');
const [url, actionsFile, outFile, code, seed, scenario] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch(); const page = await b.newPage();
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url);
  await page.waitForSelector('#loading', { state: 'detached', timeout: 120000 });
  const actions = JSON.parse(require('fs').readFileSync(actionsFile, 'utf8'));
  const log = await page.evaluate(async ([actions, code, seed, scenario]) => {
    const g = await window.PM_BACKEND('/api/new', { mode: 'hotseat', scenario: Number(scenario), seed: Number(seed), code, level: 'pro' });
    for (const a of actions) await window.PM_BACKEND('/api/act', { code: g.code, token: g.token, action: a });
    return window.PM_BACKEND(`/api/log?code=${g.code}`);
  }, [actions, code, seed, scenario]);
  require('fs').writeFileSync(outFile, JSON.stringify(log));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def _norm(log):
    return [{k: v for k, v in r.items() if k not in VOLATILE} for r in log]


@pytest.mark.parametrize('scenario,seed', [(15, 33), (1, 9)])
def test_static_build_matches_the_server(static_site, tmp_path, scenario, seed):
    while True:                                 # from the given seed, the first game with a roll in it
        acts = []
        res = play(scenario_state(scenario), RandomPolicy(), RandomPolicy(), seed=seed, check=lambda b, a, s: acts.append(a))
        if any(e[3] for e in res['log']):
            break
        seed += 1
    actions = [action_to_json(a) for a in acts]
    code = f'PAR{scenario:02d}{seed % 10}'
    # server
    srv, base = start_background()
    req = lambda p, b: json.loads(urllib.request.urlopen(urllib.request.Request(
        base + p, json.dumps(b).encode(), {'Content-Type': 'application/json'})).read())
    g = req('/api/new', dict(mode='hotseat', scenario=scenario, seed=seed, code=code, level='pro'))
    for a in actions:
        req('/api/act', dict(code=g['code'], token=g['token'], action=a))
    server_log = json.loads(urllib.request.urlopen(f'{base}/api/log?code={g["code"]}').read())
    srv.shutdown()
    # Pyodide
    (tmp_path / 'parity.js').write_text(NODE_PARITY)
    (tmp_path / 'actions.json').write_text(json.dumps(actions))
    out = tmp_path / 'static_log.json'
    url = f'{static_site}/site/index.html?pyodide={static_site}/pyodide/'
    r = subprocess.run(['node', str(tmp_path / 'parity.js'), url, str(tmp_path / 'actions.json'), str(out), code,
                        str(seed), str(scenario)], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-1000:]
    static_log = json.loads(out.read_text())
    assert len(static_log) == len(server_log) and any(x['type'] == 'roll' for x in server_log)
    assert _norm(static_log) == _norm(server_log)


NODE_PHONE = r"""
const { chromium, devices } = require('playwright');
const [url, shot] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  await page.goto(url);
  await page.waitForSelector('#loading', { state: 'detached', timeout: 120000 });
  await page.selectOption('#kind', 'single'); await page.selectOption('#level', 'pro');
  await page.click('#create'); await page.waitForTimeout(1200);
  await page.click('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(400);
  const res = await page.evaluate(() => {
    const vw = document.documentElement.clientWidth;
    const scroll = document.documentElement.scrollWidth;
    const buttons = [...document.querySelectorAll('button')].filter(b => b.offsetParent !== null);
    const small = buttons.filter(b => b.getBoundingClientRect().height < 44 || b.getBoundingClientRect().width < 44).map(b => b.textContent);
    const outside = buttons.filter(b => { const r = b.getBoundingClientRect(); return r.right > vw + 1 || r.left < -1; }).map(b => b.textContent);
    const tabs = [...document.querySelectorAll('.tabs button')].map(b => b.textContent);
    return { vw, scroll, small, outside, tabs, n: buttons.length };
  });
  for (const t of ['off', 'def', 'cards', 'log']) { await page.click(`.tabs button[data-tab=${t}]`); }
  await page.click('.tabs button[data-tab=off]');
  await page.screenshot({ path: shot, fullPage: true });
  console.log(JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_phone_layout_fits_galaxy_portrait(static_site, tmp_path):
    (tmp_path / 'phone.js').write_text(NODE_PHONE)
    shot = os.path.join(ROOT, 'docs', 'playtest_phone_portrait.png')
    url = f'{static_site}/site/index.html?pyodide={static_site}/pyodide/'
    r = subprocess.run(['node', str(tmp_path / 'phone.js'), url, shot], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-1000:]
    res = json.loads(r.stdout.strip().splitlines()[-1])
    assert res['scroll'] <= res['vw'], res                     # no horizontal scroll
    assert res['outside'] == [], res                          # every control on screen
    assert res['small'] == [], res                            # 44 px touch targets
    assert res['tabs'] == ['Offence tracker', 'Defence tracker', 'Cards', 'Log']
