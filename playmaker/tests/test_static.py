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


NODE_AI = r"""
const { chromium, devices } = require('playwright');
const [url, level, side] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch(); const page = await (await b.newContext({ ...devices['Galaxy S9+'] })).newPage();
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url);
  await page.waitForSelector('#loading', { state: 'detached', timeout: 120000 });
  const out = await page.evaluate(async ([lvl, side]) => {
    const t0 = performance.now();
    const g = await window.PM_BACKEND('/api/new', { mode: 'hotseat', scenario: 1, seed: 9, level: 'pro', ai: { [side]: lvl } });
    const times = [];
    for (let i = 0; i < 8; i++) {
      const s = await window.PM_BACKEND(`/api/state?code=${g.code}&token=${g.token}`);
      if (s.stage === 'over' || !s.legal.length) break;
      const a = side === 'X' ? (s.legal.find(x => x.kind === 'pass') || s.legal.find(x => x.kind === 'hesitate') || s.legal[0])
                             : (s.legal.find(x => x.kind === 'pause') || s.legal.find(x => x.kind === 'end_turn') || s.legal[0]);
      const t = performance.now();
      await window.PM_BACKEND('/api/act', { code: g.code, token: g.token, action: a });
      times.push(performance.now() - t);
    }
    const log = await window.PM_BACKEND(`/api/log?code=${g.code}`);
    const ai = log.filter(r => r.type === 'action' && r.actor === 'ai');
    return { times, ai: ai.map(r => r.action.text), think: ai.map(r => r.think_s || 0) };
  }, [level, side]);
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


@pytest.mark.parametrize('side', ['X', 'O'])
@pytest.mark.parametrize('level', ['rookie', 'starter', 'allstar'])
def test_the_computer_runs_in_the_browser_build(static_site, tmp_path, level, side):
    """Each computer level plays in the link version (on the phone profile), on defence and on offence, within
    its thinking budget (computer_levels.json budget_s.browser, with a margin for the step after the deadline)."""
    (tmp_path / 'ai.js').write_text(NODE_AI)
    url = f'{static_site}/site/index.html?pyodide={static_site}/pyodide/'
    r = subprocess.run(['node', str(tmp_path / 'ai.js'), url, level, side], capture_output=True, text=True, timeout=900)
    assert r.returncode == 0, r.stderr[-800:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    print(f'browser {level} {side}: think s per decision', out['think'], 'ms per human action', [round(t) for t in out['times']])
    assert out['ai'], out                                    # the computer acted
    from playmaker_engine.computer import LEVELS
    assert max(out['think']) < LEVELS['budget_s']['browser'] * 1.5, out['think']


def test_every_engine_module_the_game_loads_is_in_the_browser_bundle():
    """A module the link version needs but the bundle leaves out only fails in the browser: play a short
    computer game (which loads the lazy imports), then check every engine module that got loaded."""
    import sys
    from playmaker_web.build_site import ENGINE_FILES
    from playmaker_web.game import Game
    Game(mode='hotseat', scenario=6, seed=3, level='pro', ai=dict(O='allstar', X='allstar'))
    loaded = {m.split('.')[-1] + '.py' for m in sys.modules
              if m.startswith('playmaker_engine.') and m.count('.') == 1}
    research = {'solver_report.py', 'solver_round2.py', 'solver_fixes.py', 'headtohead.py', 'rule_test_3h.py',
                'calibrate.py', 'soak.py', 'defence_check.py', 'pause_examples.py', 'analysis.py',
                'agreement.py', 'matchups.py'}        # loaded by other tests' research tools in a full run
    missing = sorted(loaded - set(ENGINE_FILES) - research)
    assert not missing, missing


NODE_ZONES = r"""
const { chromium } = require('playwright');
const [url, shot] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 412, height: 915 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true });
  const page = await ctx.newPage();
  page.on('pageerror', e => console.error('pageerror', e.message));
  await page.goto(url);
  await page.waitForSelector('#loading', { state: 'detached', timeout: 120000 });
  await page.selectOption('#kind', 'single'); await page.selectOption('#level', 'pro');
  await page.click('#create'); await page.waitForTimeout(1200);
  const count = () => page.evaluate(() => {
    const per = {};
    for (const t of document.querySelectorAll('svg .influence text.zonenum')) per[t.textContent] = (per[t.textContent] || 0) + 1;
    return { zones: document.querySelectorAll('svg .influence rect.zone').length, per,
             badges: document.querySelectorAll('svg rect.capbadge').length,
             vw: document.documentElement.clientWidth, scroll: document.documentElement.scrollWidth };
  });
  const before = await count();
  // the offence Hesitates (its turn ends), then a defender with a zone uses his Move: turns in place
  const moved = await page.evaluate(async () => {
    const s0 = await window.PM_BACKEND(`/api/state?code=${G.code}&token=${G.token}`);
    const h = s0.legal.find(a => a.kind === 'hesitate');
    await window.PM_BACKEND('/api/act', { code: G.code, token: G.token, action: h });
    const s1 = await window.PM_BACKEND(`/api/state?code=${G.code}&token=${G.token}`);
    // the defender with a zone and the shortest Quick Step: his zone shrinks most once his Move is used
    const z = s1.influence.zones.filter(z => z.squares.length).map(z => z.defender);
    const j = z.sort((a, b) => s1.x[a].card.qs - s1.x[b].card.qs || a - b)[0];
    const mv = s1.legal.find(a => a.kind === 'move' && a.piece === j && a.dest[0] === s1.x[j].x && a.dest[1] === s1.x[j].y && a.arrow === s1.x[j].arrow)
            || s1.legal.find(a => a.kind === 'move' && a.piece === j && a.dest[0] === s1.x[j].x && a.dest[1] === s1.x[j].y);
    await window.PM_BACKEND('/api/act', { code: G.code, token: G.token, action: mv });
    await refresh();
    return { j, before: s1.influence.zones[j].squares.length };
  });
  await page.waitForTimeout(600);
  const after = await count();
  await page.screenshot({ path: shot, fullPage: false });
  console.log(JSON.stringify({ before, after, moved }));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_zones_render_shrink_after_a_move_and_fit_a_phone(static_site, tmp_path):
    """The zones of influence are always on: shaded for every defender, shrinking once his Move is used
    (with the M badge), and the board stays inside a 412 x 915 phone screen with no sideways scroll."""
    (tmp_path / 'zones.js').write_text(NODE_ZONES)
    shot = os.path.join(ROOT, 'docs', 'zones_mid_phase.png')
    url = f'{static_site}/site/index.html?pyodide={static_site}/pyodide/'
    r = subprocess.run(['node', str(tmp_path / 'zones.js'), url, shot], capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stderr[-1500:]
    res = json.loads(r.stdout.strip().splitlines()[-1])
    b, a, j = res['before'], res['after'], str(res['moved']['j'] + 1)
    assert b['zones'] > 0 and b['per'].get(j, 0) > 0, res
    assert a['per'].get(j, 0) < b['per'][j], res                     # his zone shrank once his Move was used
    assert a['badges'] > b['badges'], res                           # and his piece shows the used Move
    for v in (b, a):
        assert v['scroll'] <= v['vw'], res                          # nothing scrolls sideways
