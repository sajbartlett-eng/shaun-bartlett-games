"""The setup screen in a real browser: each piece is drawn once (its start is a faint ring), and both
Confirm buttons work."""
import json
import subprocess

from playmaker_web.server import start_background

NODE = r"""
const { chromium } = require('playwright');
const [base] = process.argv.slice(2);
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })).json();
(async () => {
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 412, height: 915 }, isMobile: true, hasTouch: true })).newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  const g = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], full: true, place: true, seed: 1, level: 'pro' });
  await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(900);
  const look = () => page.evaluate(() => ({ pieces: document.querySelectorAll('#court g.piece').length, ghosts: document.querySelectorAll('#court g.ghost').length,
    disabled: document.querySelector('#sideButtons button.primary').disabled, nulls: document.getElementById('actionsPanel').textContent.includes('null') }));
  const out = { start: await look() };
  await page.tap('g.piece[aria-label^="O2,"]'); await page.selectOption('#placeSq', 'E10');
  await page.tap('g.piece[aria-label^="O1,"]'); await page.click('rect.target[aria-label="move O1 to H12"]');
  out.moved = await look();
  await page.click('#sideButtons button.primary'); await page.waitForTimeout(700);
  out.defence = await look();
  await page.tap('g.piece[aria-label^="X1,"]'); await page.selectOption('#placeSq', 'H11');
  out.xmoved = await look();
  await page.click('#sideButtons button.primary'); await page.waitForTimeout(700);
  const s = await (await fetch(`${base}/api/state?code=${g.code}&token=${g.token}`)).json();
  out.final = { placing: s.placing, o: s.o.map(p => p.sq), x: s.x.map(p => p.sq) };
  out.errs = errs;
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_setup_moves_pieces_and_confirms(tmp_path):
    srv, base = start_background()
    try:
        (tmp_path / 'p.js').write_text(NODE)
        r = subprocess.run(['node', str(tmp_path / 'p.js'), base], capture_output=True, text=True, timeout=120)
        assert r.returncode == 0, r.stderr[-500:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert out['errs'] == []
    assert out['start'] == dict(pieces=5, ghosts=0, disabled=False, nulls=False)        # the offence only, ready to confirm
    assert out['moved']['pieces'] == 5 and out['moved']['ghosts'] == 2                  # moved, not duplicated
    assert out['defence']['pieces'] == 10 and not out['defence']['disabled']           # offence fixed, defence movable
    assert out['xmoved']['pieces'] == 10 and out['xmoved']['ghosts'] == 1
    f = out['final']
    assert f['placing'] is None and f['o'][:2] == ['H12', 'E10'] and f['x'][0] == 'H11'
