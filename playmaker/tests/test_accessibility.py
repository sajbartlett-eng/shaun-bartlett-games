"""Accessibility checks on the playtest page: axe-core (WCAG 2.1 A/AA plus best practice) on the key
screens, focus kept inside dialogs, Escape closes them, and every court piece has a full name."""
import json
import os
import subprocess

import pytest

from playmaker_web.server import start_background

HERE = os.path.dirname(os.path.abspath(__file__))
AXE_VERSION = '4.10.2'


def axe_path():
    local = os.path.join(HERE, '.a11y')
    path = os.path.join(local, 'node_modules', 'axe-core', 'axe.min.js')
    if not os.path.isfile(path):
        os.makedirs(local, exist_ok=True)
        r = subprocess.run(['npm', 'install', '--prefix', local, f'axe-core@{AXE_VERSION}', '--no-audit', '--no-fund'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            pytest.skip('axe-core not available offline')
    return path


NODE = r"""
const { chromium } = require('playwright');
const fs = require('fs');
const [base, axePath] = process.argv.slice(2);
const AXE = fs.readFileSync(axePath, 'utf8');
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(p === '/api/new' && !b.level ? { ...b, level: 'pro' } : b) })).json();
const get = async p => (await fetch(base + p)).json();
const act = async (g, pred) => { const s = await get(`/api/state?code=${g.code}&token=${g.token}`); return post('/api/act', { code: g.code, token: g.token, action: s.legal.find(pred) }); };
async function scan(page) {
  await page.addScriptTag({ content: AXE });
  return page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'best-practice'] })).violations.map(v => v.id));
}
(async () => {
  const out = {};
  const b = await chromium.launch();
  for (const [w, h, tag] of [[1440, 900, 'laptop'], [412, 915, 'phone']]) {
    const page = await (await b.newContext({ viewport: { width: w, height: h } })).newPage();
    await page.goto(base + '/'); await page.waitForTimeout(500);
    out[tag + ' start'] = await scan(page);
    const g = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], seed: 1 });
    await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(900);
    out[tag + ' table'] = await scan(page);
    out[tag + ' labels'] = await page.evaluate(() => [...document.querySelectorAll('g.piece')].map(p => p.getAttribute('aria-label')));
  }
  const page = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  const g2 = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], seed: 2 });
  await act(g2, a => a.kind === 'move' && a.piece === 0 && a.dest[0] === 9 && a.dest[1] === 10);
  await act(g2, a => a.kind === 'shot'); await act(g2, a => a.kind === 'end_turn');
  await page.goto(`${base}/?code=${g2.code}&token=${g2.token}`); await page.waitForTimeout(900);
  out['contest'] = await scan(page);
  const g3 = await post('/api/new', { mode: 'hotseat', scenario: 6, seed: 4, ai: { O: 'greedy', X: 'greedy' } });
  await page.goto(`${base}/?code=${g3.code}&token=${g3.token}`); await page.waitForTimeout(900);
  // the computer's turns come one action at a time in the step bar, then the end screen
  out['step bar'] = await scan(page);
  out['steps'] = [];
  for (let i = 0; i < 80 && await page.evaluate(() => !document.getElementById('stepBar').classList.contains('hidden')); i++) {
    out['steps'].push(await page.evaluate(() => [document.querySelector('#stepBar .step-count').textContent, document.activeElement.id,
      document.querySelectorAll('#recent .fe').length, !!document.querySelector('#court .ghost') || null,
      document.querySelector('#stepBar .fe-head').textContent]));
    await page.keyboard.press('Enter'); await page.waitForTimeout(60);
  }
  out['end dialog'] = await scan(page);
  const trap = [];
  for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); trap.push(await page.evaluate(() => !!document.activeElement.closest('#modal'))); }
  out['trap'] = trap;
  // the end screen; Escape closes it
  const heading = () => page.evaluate(() => document.getElementById('modal').classList.contains('hidden') ? null : (document.querySelector('#modalBox h2') || {}).textContent);
  out['dialogs'] = [await heading()];
  for (let i = 0; i < 3 && (await heading()); i++) { await page.keyboard.press('Escape'); await page.waitForTimeout(250); out['dialogs'].push(await heading()); }
  out['escape closes'] = (await heading()) === null;
  // step 3d screens: the pick lock, the unlocked report, the custom team builder (phone width)
  const ph = await (await b.newContext({ viewport: { width: 412, height: 915 } })).newPage();
  const g4 = await post('/api/new', { mode: 'hotseat', teams: ['Ball Movement', 'Twin Towers'], seed: 2, level: 'scout' });
  await ph.goto(`${base}/?code=${g4.code}&token=${g4.token}`); await ph.waitForTimeout(900);
  out['pick lock'] = await scan(ph);
  for (let i = 0; i < 2; i++) { await ph.click('#modal button.primary'); await ph.waitForTimeout(500); }
  await ph.evaluate(() => document.querySelectorAll('#modal details').forEach(d => { d.open = true; }));
  out['scout report'] = await scan(ph);
  await ph.goto(base + '/'); await ph.waitForTimeout(500);
  await ph.click('button.path[data-path=friend]'); await ph.waitForTimeout(300);
  await ph.selectOption('#age', 'junior'); await ph.selectOption('#roster', 'free'); await ph.waitForTimeout(600);
  out['team builder'] = await scan(ph);
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_accessibility(tmp_path):
    axe = axe_path()
    srv, base = start_background()
    try:
        (tmp_path / 'a11y.js').write_text(NODE)
        r = subprocess.run(['node', str(tmp_path / 'a11y.js'), base, axe], capture_output=True, text=True, timeout=300)
        assert r.returncode == 0, r.stderr[-800:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    for screen in ('laptop start', 'laptop table', 'phone start', 'phone table', 'contest', 'step bar', 'end dialog',
                   'pick lock', 'scout report', 'team builder'):
        assert out[screen] == [], (screen, out[screen])
    assert all(out['trap']), 'focus left the dialog'
    assert out['escape closes'], out['dialogs']
    assert out['step bar'] == [], out['step bar']
    steps = out['steps']                                      # every action, in order, with OK focused
    # step 3m: a long computer turn can cross a phase, and the phase diagram's Continue takes focus between steps
    assert len(steps) >= 3 and all(f in ('stepOk', 'phaseContinue') for _, f, _, _, _ in steps), steps
    assert sum(f == 'stepOk' for _, f, _, _, _ in steps) >= len(steps) - 2, steps
    for k, (count, _, shown, _, _) in enumerate(steps):       # "so far": the actions before this one, never after
        assert shown == int(count.split('action ')[1].split(' of')[0]) - 1, steps
    for _, _, _, ghost, text in steps:                        # a moved piece leaves a ghost where it was
        if any(w in text for w in (' Move to ', ' Quick Step to ', ' Sprint to ')):
            assert ghost, (text, steps)
    assert steps[0][0].endswith(f"action 1 of {steps[0][0].split(' of ')[-1]}") and '(computer)' in steps[0][0]
    assert any(d and 'over' in d for d in out['dialogs'])
    labels = out['laptop labels']
    assert len(labels) == 10
    assert all(',' in l and ' on ' in l for l in labels)
    assert any('has the ball' in l for l in labels) and any('arrow pointing' in l for l in labels)
