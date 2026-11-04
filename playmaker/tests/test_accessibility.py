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
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })).json();
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
  out['end dialog'] = await scan(page);
  const trap = [];
  for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); trap.push(await page.evaluate(() => !!document.activeElement.closest('#modal'))); }
  out['trap'] = trap;
  await page.keyboard.press('Escape'); await page.waitForTimeout(200);
  out['escape closes'] = await page.evaluate(() => document.getElementById('modal').classList.contains('hidden'));
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
    for screen in ('laptop start', 'laptop table', 'phone start', 'phone table', 'contest', 'end dialog'):
        assert out[screen] == [], (screen, out[screen])
    assert all(out['trap']), 'focus left the dialog'
    assert out['escape closes']
    labels = out['laptop labels']
    assert len(labels) == 10
    assert all(',' in l and ' on ' in l for l in labels)
    assert any('has the ball' in l for l in labels) and any('arrow pointing' in l for l in labels)
