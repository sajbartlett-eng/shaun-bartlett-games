"""Step 19: the UX, legibility and accessibility overhaul.

Stage 1: tap a player, tap a square, confirm; the actions under the board; double-tap, hold, drag and their single-tap
and keyboard alternatives. Stage 2: every option's chance and "why" are the engine's own, in plain advantage words.
Later stages add their own checks below."""
import json
import os
import random
import re
import subprocess

import pytest

from playmaker_engine.actions import legal_actions
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_web import advice as ADV
from playmaker_web import view as V
from playmaker_web.game import Game

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _positions(n_games=4, steps=24):
    """Positions from a few seeded possessions played with random legal actions (the rules choose what is legal)."""
    out = []
    for seed in range(n_games):
        g = Game(teams=['Five Out', 'High-Low'] if seed % 2 == 0 else ['Ball Movement', 'Twin Towers'], seed=seed,
                 match_format='digital', full=True, per_side=4, place=False)
        s = g.state
        rng = random.Random(seed)
        for _ in range(steps):
            if s.stage == 'over':
                break
            acts = legal_actions(s)
            if not acts:
                break
            out.append(s)
            a = rng.choice(acts)
            node = apply(s, a)
            while isinstance(node, ChanceNode):
                node = rng.choice(node.outcomes)[2]
            s = node
    return out


POS = None


def positions():
    global POS
    if POS is None:
        POS = _positions()
    return POS


# ---- stage 2: true to the engine --------------------------------------------------------------------------------

def test_every_why_names_the_band_on_the_card_and_every_chance_is_the_engines():
    from playmaker_engine import decide as D
    from playmaker_engine.scoring import shot_ev
    seen = set()
    for s in positions():
        for d, a in zip(V.legal_json(s, legal_actions(s)), legal_actions(s)):
            adv = d.get('advice')
            if not adv:
                continue
            seen.add(a.kind)
            for b in adv['why_bands']:                     # the band it names is the band on the card
                side, i = b['who'][0], int(b['who'][1:]) - 1
                card = (s.ctx.off if side == 'O' else s.ctx.dfn)[i]
                assert card.bands[b['rating']] == b['band'], (a, b)
            if a.kind == 'pass' and adv['chance'] is not None:
                assert adv['chance'] == pytest.approx(float(D._pass_prob(s, a.target)))
            if a.kind in ('shot', 'forced_shot'):
                assert adv['value'] == round(float(shot_ev(s, a.piece, a.shot, a.kind == 'forced_shot')))
            if a.kind in ('dribble', 'intercept', 'challenge', 'steal'):
                node = apply(s, a)
                assert isinstance(node, ChanceNode)
                assert 0.0 <= adv['chance'] <= 1.0
                # the chance is a sum over the referee's own dice tree
                assert adv['chance'] == pytest.approx(ADV.chance_for(s, a))
    assert {'pass', 'dribble', 'screen'} <= seen, seen


def test_the_words_read_plainly_one_idea_a_line_and_no_banned_term():
    from playmaker_engine.plain import check
    lines = []
    for s in positions():
        for d in V.legal_json(s, legal_actions(s)):
            if d.get('advice'):
                lines.append(('why', d['advice']['why']))
        for m in ADV.matchup_lines(s, V.matchups(s)):
            lines += [('hunt', h) for h in m['hunt']] + [('guard', g) for g in m['guard']] + ([('help', m['help'])] if m['help'] else [])
        for c in list(s.ctx.off) + list(s.ctx.dfn):
            w = ADV.card_words(c, 'O') if c in s.ctx.off else ADV.card_words(c, 'X')
            lines += [('card', t) for t in w['plus'] + w['minus']]
    assert lines
    for kind, t in lines:
        assert not check(t), (kind, t)
        assert len(t.split()) <= 20, (kind, t)                       # no line over about 20 words in play
        assert len(re.findall(r'[.!?](\s|$)', t)) <= 1, (kind, t)    # one idea: one sentence
        assert not re.search(r'\d+\s*v\s*\d+', t), (kind, t)          # no "x versus y" by default


def test_the_new_interface_files_use_plain_words():
    from playmaker_engine.plain import check
    lit = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`", re.S)
    bad = []
    for f in ('play.js', 'advice.js'):
        src = re.sub(r'^\s*//.*$', '', open(os.path.join(ROOT, 'playmaker_web', 'static', f)).read(), flags=re.M)
        for m in lit.finditer(src):
            t = m.group(0)[1:-1]
            if ' ' in t.strip() and check(t):
                bad.append((f, t[:100], check(t)))
    assert not bad, bad


# ---- stage 1 (and 2's switch): the flows in a browser ------------------------------------------------------------

NODE_FLOWS = r"""
const { chromium, devices } = require('playwright');
const [base] = process.argv.slice(2);
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })).json();
const get = async p => (await fetch(base + p)).json();
async function fresh(page, prep) {
  const g = await post('/api/new', { mode: 'hotseat', match_format: 'digital', teams: ['Five Out', 'High-Low'], seed: 3, level: 'pro', full: true, per_side: 4 });
  await post('/api/place', { code: g.code, token: g.token, preview: true });
  if (prep) await prep(g);
  await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(1000);
  return g;
}
const feed = async g => (await get(`/api/state?code=${g.code}&token=${g.token}`)).feed.map(e => e.text);
(async () => {
  const out = {};
  const b = await chromium.launch();
  const page = await (await b.newContext({ viewport: { width: 1440, height: 900 } })).newPage();
  page.on('pageerror', e => { out.errors = (out.errors || []).concat(e.message); });
  // 1. tap, ghost, confirm: nothing is sent before the confirm
  let g = await fresh(page);
  await page.click('g.piece[aria-label^="O3,"]'); await page.waitForTimeout(300);
  out.lit = await page.locator('#court .target[data-sq]').count();
  await page.click('#court [data-sq="O10"].target'); await page.waitForTimeout(300);
  out.ghost = await page.evaluate(() => window.PM_GHOST());
  out.sentBeforeConfirm = (await feed(g)).length;
  await page.click('#confirmBtn'); await page.waitForTimeout(500);
  out.afterConfirm = await feed(g);
  out.stillSelected = await page.evaluate(() => !!document.querySelector('#court g.piece.sel[aria-label^="O3,"]'));
  // 2. the fast path: the same square again
  g = await fresh(page);
  await page.click('g.piece[aria-label^="O3,"]'); await page.waitForTimeout(300);
  await page.click('#court [data-sq="O10"].target'); await page.waitForTimeout(300);
  await page.click('#ghostPiece'); await page.waitForTimeout(500);
  out.fastPath = await feed(g);
  // 3. the actions under the board, the double-tap (targets on the board), choose and confirm a pass
  g = await fresh(page);
  await page.click('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(300);
  out.listItems = await page.locator('#enderList button').allInnerTexts();
  out.listOverBoard = await page.evaluate(() => { const l = document.getElementById('enderList').getBoundingClientRect(), c = document.getElementById('court').getBoundingClientRect(); return l.top < c.bottom && l.bottom > c.top && l.left < c.right && l.right > c.left; });
  await page.dblclick('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(400);
  out.boardTargets = await page.locator('#court .ender-target').count();
  await page.click('#court .ender-target[aria-label="Pass to O2"]'); await page.waitForTimeout(300);
  out.pendingPass = await page.locator('#playLine').innerText();
  out.whyShown = await page.locator('#playBar .advwhy').first().innerText();
  await page.click('#confirmBtn'); await page.waitForTimeout(600);
  out.passed = await feed(g);
  // 4. a defender: the rotate buttons and then drag; only the allowed arrows
  g = await fresh(page, async g => { const s = await get(`/api/state?code=${g.code}&token=${g.token}`); await post('/api/act', { code: g.code, token: g.token, action: s.legal.find(a => a.kind === 'hesitate') }); });
  await page.click('g.piece[aria-label^="X2,"]'); await page.waitForTimeout(300);
  const s4 = await get(`/api/state?code=${g.code}&token=${g.token}`);
  const dest = s4.legal.find(a => a.kind === 'move' && a.piece === 1 && 'ABCDEFGHIJKLMNOPQ'[a.dest[0]] + a.dest[1] !== s4.x[1].sq);
  const dsq = 'ABCDEFGHIJKLMNOPQ'[dest.dest[0]] + dest.dest[1];
  const allowed = [...new Set(s4.legal.filter(a => a.kind === dest.kind && a.piece === 1 && a.dest[0] === dest.dest[0] && a.dest[1] === dest.dest[1]).map(a => a.arrow))].sort();
  await page.click(`#court [data-sq="${dsq}"].target`); await page.waitForTimeout(300);
  const a0 = (await page.evaluate(() => window.PM_GHOST())).arrow;
  if (await page.locator('#rotCw').count()) { await page.click('#rotCw'); await page.waitForTimeout(250); }
  const a1 = (await page.evaluate(() => window.PM_GHOST())).arrow;
  out.rotate = { allowed, a0, a1, inAllowed: allowed.includes(a1) };
  // drag round to the south-west of the ghost
  const gb = await page.locator('#ghostPiece').boundingBox();
  const cx = gb.x + gb.width / 2, cy = gb.y + gb.height / 2;
  await page.mouse.move(cx, cy); await page.mouse.down();
  for (const f of [0.3, 0.7, 1]) await page.mouse.move(cx - 40 * f, cy + 40 * f);
  await page.mouse.up(); await page.waitForTimeout(300);
  out.dragArrow = (await page.evaluate(() => window.PM_GHOST())).arrow;
  out.dragInAllowed = allowed.includes(out.dragArrow);
  await page.click('#confirmBtn'); await page.waitForTimeout(600);
  const f4 = await feed(g);
  out.defenderMoved = f4[f4.length - 1];
  // 5. the keyboard: Tab to a player, Enter, arrow keys, Enter, Enter
  g = await fresh(page);
  await page.focus('g.piece[aria-label^="O3,"]'); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  await page.keyboard.press('ArrowUp'); await page.waitForTimeout(250);
  out.cursorFocused = await page.evaluate(() => document.activeElement && document.activeElement.id);
  out.announceAfterArrow = await page.locator('#announce').innerText();
  await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  out.ghostByKeys = await page.evaluate(() => window.PM_GHOST());
  out.announceGhost = await page.locator('#announce').innerText();
  await page.keyboard.press('Escape'); await page.waitForTimeout(250);
  out.escapedGhost = await page.evaluate(() => window.PM_GHOST());
  await page.keyboard.press('Enter'); await page.waitForTimeout(250); await page.keyboard.press('Enter'); await page.waitForTimeout(600);
  out.keyMoved = (await feed(g)).length;
  // A opens O1's actions with the keyboard
  await page.focus('g.piece[aria-label^="O1,"]'); await page.keyboard.press('Enter'); await page.waitForTimeout(300);
  await page.keyboard.press('a'); await page.waitForTimeout(300);
  out.aFocus = await page.evaluate(() => document.activeElement && document.activeElement.closest('#enderList') ? document.activeElement.textContent : null);
  // 6. a hold on a phone opens the actions; the court asks the browser not to zoom on a double-tap
  const ph = await (await b.newContext({ ...devices['Galaxy S9+'] })).newPage();
  g = await fresh(ph);
  out.touchAction = await ph.evaluate(() => getComputedStyle(document.getElementById('court')).touchAction);
  const pb = await ph.locator('g.piece[aria-label^="O1,"]').boundingBox();
  await ph.mouse.move(pb.x + pb.width / 2, pb.y + pb.height / 2); await ph.mouse.down(); await ph.waitForTimeout(800); await ph.mouse.up(); await ph.waitForTimeout(300);
  out.holdTargets = await ph.locator('#court .ender-target').count();
  // a tap that misses a small square by a little lands on the nearest one
  g = await fresh(ph);
  await ph.click('g.piece[aria-label^="O3,"]'); await ph.waitForTimeout(300);
  const t = await ph.locator('#court [data-sq="O10"].target').boundingBox();
  await ph.mouse.click(t.x + t.width / 2 + t.width * 0.55, t.y + t.height / 2 - t.height * 0.55); await ph.waitForTimeout(300);
  out.snapped = await ph.evaluate(() => window.PM_GHOST());
  // 7. "Show the numbers": off by default (no "x v y"), on brings them back
  g = await fresh(page);
  await page.click('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(300);
  out.numbersOff = await page.locator('#playBar').innerText();
  await page.click('#numbersToggle'); await page.waitForTimeout(300);
  await page.click('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(300);
  out.numbersOn = await page.locator('#playBar').innerText();
  await page.click('#numbersToggle'); await page.waitForTimeout(300);
  console.log(JSON.stringify(out));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


def test_tap_confirm_double_tap_hold_drag_keyboard_and_the_numbers_switch(tmp_path):
    from playmaker_web.server import start_background
    srv, base = start_background()
    try:
        (tmp_path / 'flows.js').write_text(NODE_FLOWS)
        r = subprocess.run(['node', str(tmp_path / 'flows.js'), base], capture_output=True, text=True, timeout=400,
                           env=dict(os.environ, NODE_PATH=subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True).stdout.strip()))
        assert r.returncode == 0, r.stderr[-1500:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert not out.get('errors'), out.get('errors')
    # tap, ghost, confirm; nothing sent before the confirm; the player stays selected
    assert out['lit'] > 5 and out['ghost']['sq'] == 'O10'
    assert out['afterConfirm'][-1] == 'O3 Move to O10' and out['sentBeforeConfirm'] == len(out['afterConfirm']) - 1
    assert out['stillSelected']
    assert out['fastPath'][-1] == 'O3 Move to O10'
    # the actions: under the board, never over it; the double-tap puts their targets on the board
    assert 'Pass to O2' in out['listItems'] and 'Hesitate' in out['listItems'] and not out['listOverBoard']
    assert out['boardTargets'] >= 4 and out['pendingPass'].startswith('Pass to O2') and out['whyShown']
    assert out['passed'][-1] == 'O1 Pass to O2'
    # the arrow: turning and dragging stay inside what the rules allow
    assert out['rotate']['inAllowed'] and out['dragInAllowed']
    assert out['defenderMoved'].startswith('X2 ')
    # the keyboard and what it announces
    assert out['cursorFocused'] == 'kCursor' and out['ghostByKeys'] and 'Press Enter to confirm' in out['announceGhost']
    assert out['escapedGhost'] is None and out['keyMoved'] >= 1
    assert out['aFocus']
    # a hold, no zoom on a double-tap, and the snap to the nearest square
    assert out['holdTargets'] >= 1 and out['touchAction'] == 'manipulation'
    assert out['snapped'] and out['snapped']['sq'] in ('O10', 'P11', 'O11', 'P10')
    # the numbers: off by default, on brings the "x v y" lines back
    assert not re.search(r'\d+.? v [A-Z]', out['numbersOff']) and '%' in out['numbersOff']
    assert re.search(r'Pass \d+.? v Intercept', out['numbersOn'])


# ---- stage 3: turn by turn, the assessments, the report ---------------------------------------------------------

needs_node = pytest.mark.skipif(not __import__('shutil').which('node'), reason='needs Node for the coverage map')


@needs_node
def test_the_report_is_turn_by_turn_and_true_to_the_coverage_map():
    """A computer-against-computer possession on the server (the coverage map in Node): every turn has a line for
    each team; every number in a line is the map's own measure at that moment; the possession's assessment has the
    shot breakdown, the verdict and a keep or change for the sides; plain words throughout."""
    from playmaker_engine import agent as AG
    from playmaker_engine.plain import check
    from playmaker_web.api import Manager, handle
    from playmaker_web import report as R
    from playmaker_web.server import coverage_engine, stop_coverage_engine
    assert coverage_engine()
    try:
        m = Manager()
        code, g = None, None
        for seed in (11, 5):
            st, r = handle(m, 'POST', '/api/new', body=dict(mode='hotseat', match_format='digital', teams=['Five Out', 'High-Low'], seed=seed,
                                                             level='pro', full=True, per_side=4, ai=dict(O='rookie', X='rookie')))
            g = m.get(r['code'])
            if g.state.stage == 'over':
                break
        st, rep = handle(m, 'GET', '/api/report', query=dict(code=g.code, possession='1'))
        assert st == 200 and rep['over'] and rep['turns']
        steps = [x for x in g._trails[1] if x[1] is not None]
        for t in rep['turns']:
            assert t['offence'].startswith('Offence: ') and t['defence'].startswith('Defence: ')
            first = next(b for b, a, n, tn in steps if b.phase == t['phase'] and tn == t['turn'])
            c = AG.coverage(first) if first.stage == 'play' else None
            if c is not None:
                assert t['numbers']['before'] == round(c['strength'])          # the line's number is the map's
                if t['numbers']['before'] is not None and str(t['numbers']['before']) in t['offence']:
                    assert f"from {t['numbers']['before']}" in t['offence'] or f"at {t['numbers']['before']}" in t['offence']
        sm = rep['summary']
        assert sm['verdict'].split(':')[0] in ('Good', 'Weak', 'Wasted') and sm['score'].startswith('Scored ')
        assert sm['shot'] and (sm['best'] or sm['shot'] == 'No shot went up.')
        texts = [t['offence'] for t in rep['turns']] + [t['defence'] for t in rep['turns']]
        for p in rep['phases']:
            texts += p['offence'] + p['defence'] + ([p['next']] if p['next'] else [])
        texts += [x for x in (sm['shot'], sm['score'], sm['best'], sm['trend'], sm['verdict']) if x]
        texts += [x for side in ('offence', 'defence') for x in sm[side].values() if x]
        for x in texts:
            assert not check(x), x
    finally:
        stop_coverage_engine()
    assert AG.JS.get('coverage') is None
