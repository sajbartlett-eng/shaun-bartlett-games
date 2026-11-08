"""Coach Vision is shown at Learn level only, and there it reads for both sides in the same form (arrange, never
judge: at Scout and Pro the page shows no coach line during play)."""
import json
import os
import shutil
import subprocess

import pytest

from playmaker_web.server import start_background

NODE = r"""
const { chromium } = require('playwright');
const base = process.argv[2];
(async () => {
  const b = await chromium.launch(); const out = {};
  for (const level of ['learn', 'pro', 'scout']) {
    const p = await b.newPage({ viewport: { width: 1380, height: 1000 } });
    await p.goto(base + '/'); await p.waitForTimeout(400);
    await p.click('button.path[data-path=computer]'); await p.waitForTimeout(200);
    await p.selectOption('#kind', 'single'); await p.selectOption('#level', level);
    await p.evaluate(() => { document.getElementById('seed').value = '11'; });
    await p.click('#create'); await p.waitForTimeout(1200);
    for (let k = 0; k < 4; k++) {                                              // the report, then your own setup (step 3k)
      if (await p.$('#modal:not(.hidden) button.primary')) { await p.click('#modal:not(.hidden) button.primary').catch(() => {}); await p.waitForTimeout(600); continue; }
      if (await p.$('#sideButtons button:has-text("standard setup")')) { await p.click('#sideButtons button:has-text("standard setup")').catch(() => {}); await p.waitForTimeout(1500); continue; }
      break;
    }
    out[level] = { coach: (await p.evaluate(() => document.getElementById('coachLine').innerText)).trim(),
                   canAct: await p.evaluate(() => typeof st !== 'undefined' && !!st.can_act) };
    await p.close();
  }
  console.log(JSON.stringify(out)); await b.close();
})();
"""


@pytest.fixture(scope='module')
def web():
    srv, base = start_background()
    yield base
    srv.shutdown()


def test_coach_vision_only_at_learn_and_for_both_sides(web, tmp_path):
    if not shutil.which('node'):
        pytest.skip('node is needed')
    script = tmp_path / 'gate.js'
    script.write_text(NODE)
    r = subprocess.run(['node', str(script), web], capture_output=True, text=True, timeout=180,
                       cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert r.returncode == 0, r.stderr[-800:]
    out = json.loads(r.stdout.strip().splitlines()[-1])
    assert out['learn']['canAct'] and 'Offence read' in out['learn']['coach'] and 'Defence read' in out['learn']['coach'], out['learn']
    assert out['pro']['canAct'] and out['pro']['coach'] == '', out['pro']
    assert out['scout']['coach'] == '', out['scout']
