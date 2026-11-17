// Screen-by-screen capture of the Playmaker app for a UX, legibility and accessibility audit.
// For every screen: a full-page screenshot, the axe-core violations in full, and legibility measures
// (text sizes, small touch targets, overflow). Plus keyboard order, dialog focus and 200% zoom.
const { chromium, devices } = require('playwright');
const fs = require('fs');
const path = require('path');
const [base, axePath, outDir] = process.argv.slice(2);
const AXE = fs.readFileSync(axePath, 'utf8');
fs.mkdirSync(path.join(outDir, 'screens'), { recursive: true });
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })).json();
const get = async p => (await fetch(base + p)).json();
const act = async (g, pred) => { const s = await get(`/api/state?code=${g.code}&token=${g.token}`); const a = s.legal.find(pred); if (!a) throw new Error('no such action'); return post('/api/act', { code: g.code, token: g.token, action: a }); };
const wait = ms => new Promise(r => setTimeout(r, ms));

const MEASURE = () => {
  const vis = el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none'; };
  const sizes = {}; const tiny = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = walker.nextNode())) {
    const t = n.textContent.trim(); if (!t) continue;
    const el = n.parentElement; if (!el || !vis(el)) continue;
    const fs = Math.round(parseFloat(getComputedStyle(el).fontSize));
    sizes[fs] = (sizes[fs] || 0) + t.length;
    if (fs < 12 && tiny.length < 40) tiny.push({ size: fs, text: t.slice(0, 60), where: el.closest('[id]') ? el.closest('[id]').id : el.tagName });
  }
  const small = [];
  for (const el of document.querySelectorAll('button, a[href], select, input, [role=button], g.piece, [tabindex="0"]')) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect();
    if ((r.width < 44 || r.height < 44) && small.length < 60) small.push({ w: Math.round(r.width), h: Math.round(r.height), name: (el.getAttribute('aria-label') || el.textContent || el.id || el.tagName).trim().slice(0, 50) });
  }
  const words = document.body.innerText.split(/\s+/).filter(Boolean).length;
  return { textSizes_px_by_characters: sizes, under12px: tiny, under44px_targets: small, smallTargetCount: small.length,
           wordsOnScreen: words, docWidth: document.documentElement.scrollWidth, viewport: innerWidth, horizontalScroll: document.documentElement.scrollWidth > innerWidth + 1,
           pageHeight: document.documentElement.scrollHeight };
};

async function scan(page) {
  await page.addScriptTag({ content: AXE });
  return page.evaluate(async () => (await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] }))
    .violations.map(v => ({ id: v.id, impact: v.impact, help: v.help, url: v.helpUrl, nodes: v.nodes.slice(0, 8).map(x => ({ target: x.target.join(' '), summary: x.failureSummary })) , count: v.nodes.length })));
}

const results = {};
async function shot(page, name, note) {
  const file = `screens/${name}.png`;
  try {
    await page.waitForTimeout(400);
    await page.screenshot({ path: path.join(outDir, file), fullPage: true });
    const axe = await scan(page);
    const m = await page.evaluate(MEASURE);
    results[name] = { note, file, axe, ...m };
    console.error('ok', name, axe.length, 'axe issues');
  } catch (e) { results[name] = { note, error: String(e).slice(0, 300) }; console.error('fail', name, e.message); }
}
async function step(name, note, fn) {
  try { await fn(); } catch (e) { results[name] = { note, error: 'could not reach: ' + String(e).slice(0, 300) }; console.error('fail', name, e.message); }
}

async function keyboardOrder(page, n) {
  const out = [];
  for (let i = 0; i < n; i++) {
    await page.keyboard.press('Tab');
    out.push(await page.evaluate(() => { const e = document.activeElement; const cs = getComputedStyle(e);
      return { tag: e.tagName.toLowerCase(), id: e.id || null, name: (e.getAttribute('aria-label') || e.textContent || '').trim().slice(0, 60),
               visibleFocus: cs.outlineStyle !== 'none' && parseFloat(cs.outlineWidth) > 0 || cs.boxShadow !== 'none' }; }));
  }
  return out;
}

(async () => {
  const b = await chromium.launch();
  for (const [tag, ctxOpts] of [['laptop', { viewport: { width: 1440, height: 900 } }], ['phone', { ...devices['Galaxy S9+'] }]]) {
    const ctx = await b.newContext({ ...ctxOpts, deviceScaleFactor: tag === 'laptop' ? 1 : ctxOpts.deviceScaleFactor });
    const page = await ctx.newPage();
    page.on('pageerror', e => console.error('pageerror', tag, e.message));
    const S = s => `${tag}_${s}`;
    const home = async () => { await page.goto(base + '/'); await page.waitForTimeout(700); };
    // step 19: the options sit under Advanced settings on the new home screen; the course moved to a link
    const adv = async () => { const s = await page.$('#advanced summary'); if (s && !(await page.evaluate(() => document.getElementById('advanced').open))) { await s.click(); await page.waitForTimeout(250); } };
    const pathBtn = async p => { if (p === 'learn' && !(await page.$('button.path[data-path=learn]'))) return page.click('#rulesBtn'); return page.click(`button.path[data-path=${p}]`); };

    await step(S('01_start'), 'First screen: the four ways in', async () => { await home(); await shot(page, S('01_start'), 'First screen: the four ways in'); });
    for (const [i, p, note] of [[2, 'learn', 'Learn the rules: the guided course, first card'], [3, 'computer', 'Play the computer: set-up'], [4, 'friend', 'Play a friend: set-up'], [5, 'scenario', 'Scenario cards: set-up']]) {
      const nm = S(`0${i}_path_${p}`);
      await step(nm, note, async () => { await home(); await pathBtn(p); await page.waitForTimeout(800); await shot(page, nm, note); });
    }
    await step(S('05b_path_watch'), 'Watch the computer: set-up', async () => { await home(); if (!(await page.$('button.path[data-path=watch]'))) throw new Error('no such choice yet'); await page.click('button.path[data-path=watch]'); await page.waitForTimeout(600); await shot(page, S('05b_path_watch'), 'Watch the computer: set-up'); });
    await step(S('06_course_later'), 'The guided course, a few cards in', async () => {
      await home(); await pathBtn('learn'); await page.waitForTimeout(800);
      for (let i = 0; i < 4; i++) { const nb = await page.$('#course button.primary'); if (!nb) break; await nb.click(); await page.waitForTimeout(500); }
      await shot(page, S('06_course_later'), 'The guided course, a few cards in');
    });
    await step(S('07_players'), 'Players, records and the trainer', async () => { await home(); await page.click('button.path[data-path=computer]'); await page.waitForTimeout(400); await page.click('#playersBtn2'); await page.waitForTimeout(700); await shot(page, S('07_players'), 'Players, records and the trainer'); });
    await step(S('08_levels'), 'Levels and rosters, in short', async () => { await home(); await page.click('button.path[data-path=friend]'); await page.waitForTimeout(400); await adv(); await page.click('#levelsPage'); await page.waitForTimeout(700); await shot(page, S('08_levels'), 'Levels and rosters, in short'); });
    for (const [i, r, note] of [[9, 'build', 'Team builder (rules on)'], [10, 'random', 'Random deal'], [11, 'draft', 'Draft set-up']]) {
      const nm = S(`${i}_roster_${r}`);
      await step(nm, note, async () => { await home(); await page.click('button.path[data-path=friend]'); await page.waitForTimeout(400); await adv(); await page.selectOption('#roster', r); await page.waitForTimeout(700); await shot(page, nm, note); });
    }
    await step(S('12_draft_board'), 'The draft board', async () => { await home(); await page.click('button.path[data-path=friend]'); await page.waitForTimeout(400); await adv(); await page.selectOption('#roster', 'draft'); await page.waitForTimeout(400); await page.click('#draftBtn'); await page.waitForTimeout(900); await shot(page, S('12_draft_board'), 'The draft board'); });

    // In play: hot-seat game against a friend, digital match
    const g = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], seed: 1, level: 'pro' });
    await step(S('13_table_start'), 'The table at tip-off (hot seat)', async () => { await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(1200); await shot(page, S('13_table_start'), 'The table at tip-off (hot seat)'); });
    await step(S('14_piece_selected'), 'A piece selected: its actions', async () => { await page.click('g.piece[aria-label^="O1,"]'); await page.waitForTimeout(500); await shot(page, S('14_piece_selected'), 'A piece selected: its actions'); });
    await step(S('15_pass_choice'), 'Choosing a pass: the pass chips', async () => {
      const pb = await page.$('#kindButtons button:has-text("Pass")'); if (!pb) throw new Error('no Pass button'); await pb.click(); await page.waitForTimeout(500); await shot(page, S('15_pass_choice'), 'Choosing a pass: the pass chips'); });
    await step(S('16_coverage'), 'Coverage: shown', async () => { const gc = await post('/api/new', { mode: 'hotseat', match_format: 'digital', teams: ['Five Out', 'High-Low'], seed: 3, level: 'pro', full: true, per_side: 4 }); await post('/api/place', { code: gc.code, token: gc.token, preview: true }); await page.goto(`${base}/?code=${gc.code}&token=${gc.token}`); await page.waitForTimeout(1200); await shot(page, S('16a_digital_table'), 'A digital match, coverage hidden'); await page.click('#covToggle', { timeout: 8000 }); await page.waitForTimeout(2500); await shot(page, S('16_coverage'), 'Coverage: shown'); });
    if (tag === 'phone') {
      for (const t of ['off', 'def', 'cards', 'log']) {
        const nm = S(`17_tab_${t}`);
        await step(nm, `Phone tab: ${t}`, async () => { await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(900); await page.click(`.tabs button[data-tab=${t}]`); await page.waitForTimeout(500); await shot(page, nm, `Phone tab: ${t}`); });
      }
    }
    // The contest decision
    await step(S('18_contest'), 'The defence decides on a contest', async () => {
      const g2 = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], seed: 2, level: 'pro' });
      await act(g2, a => a.kind === 'move' && a.piece === 0 && a.dest[0] === 9 && a.dest[1] === 10);
      await act(g2, a => a.kind === 'shot'); await act(g2, a => a.kind === 'end_turn');
      await page.goto(`${base}/?code=${g2.code}&token=${g2.token}`); await page.waitForTimeout(1000);
      await shot(page, S('18_contest'), 'The defence decides on a contest');
    });
    // The computer's turns, step by step, then the end of the possession
    await step(S('19_step_bar'), "The computer's turn, one action at a time", async () => {
      const g3 = await post('/api/new', { mode: 'hotseat', scenario: 6, seed: 4, level: 'pro', ai: { O: 'greedy', X: 'greedy' } });
      await page.goto(`${base}/?code=${g3.code}&token=${g3.token}`); await page.waitForTimeout(1000);
      await shot(page, S('19_step_bar'), "The computer's turn, one action at a time");
      for (let i = 0; i < 3; i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(150); }
      await shot(page, S('20_phase_diagram'), 'After a few steps (phase diagram if a phase ended)');
      for (let i = 0; i < 90 && await page.evaluate(() => !document.getElementById('stepBar').classList.contains('hidden')); i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(60); }
      await page.waitForTimeout(600);
      await shot(page, S('21_end_dialog'), 'End of the scenario: the end dialog and feedback');
      if (tag === 'laptop') {
        const trap = [];
        for (let i = 0; i < 12; i++) { await page.keyboard.press('Tab'); trap.push(await page.evaluate(() => !!document.activeElement.closest('#modal'))); }
        results.dialogFocusKeptInside = trap.every(Boolean);
        await page.keyboard.press('Escape'); await page.waitForTimeout(400);
        results.escapeClosesDialog = await page.evaluate(() => document.getElementById('modal').classList.contains('hidden'));
        await shot(page, S('22_after_end'), 'After closing the end dialog: the review of the possession');
      }
    });
    // Scout level: the pick lock and the scout report
    await step(S('23_scout_lock'), 'Scout level: the pick lock before tip-off', async () => {
      const g4 = await post('/api/new', { mode: 'hotseat', teams: ['Ball Movement', 'Twin Towers'], seed: 2, level: 'scout' });
      await page.goto(`${base}/?code=${g4.code}&token=${g4.token}`); await page.waitForTimeout(1000);
      await shot(page, S('23_scout_lock'), 'Scout level: the pick lock before tip-off');
      for (let i = 0; i < 2; i++) { const bt = await page.$('#modal button.primary'); if (bt) { await bt.click(); await page.waitForTimeout(500); } }
      await page.evaluate(() => document.querySelectorAll('#modal details').forEach(d => { d.open = true; }));
      await shot(page, S('24_scout_report'), 'The scout report, all sections open');
    });
    // A digital match against the computer with placement
    await step(S('25_place'), 'Against the computer: placing your side', async () => {
      const g5 = await post('/api/new', { mode: 'hotseat', seed: 3, level: 'learn', match_format: 'digital', per_side: 4, ai: { B: 'rookie' }, place: true });
      await page.goto(`${base}/?code=${g5.code}&token=${g5.token}`); await page.waitForTimeout(1500);
      await shot(page, S('25_place'), 'Against the computer: placing your side (Learn level)');
    });
    // Scenario card in play
    await step(S('26_scenario_card'), 'A scenario card in play', async () => {
      const g6 = await post('/api/new', { mode: 'hotseat', scenario: 3, seed: 5, level: 'pro' });
      await page.goto(`${base}/?code=${g6.code}&token=${g6.token}`); await page.waitForTimeout(1000);
      await shot(page, S('26_scenario_card'), 'A scenario card in play');
    });

    if (tag === 'laptop') {
      await home();
      results.keyboard_start = await keyboardOrder(page, 25);
      await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(1000);
      results.keyboard_table = await keyboardOrder(page, 40);
      results.piece_labels = await page.evaluate(() => [...document.querySelectorAll('g.piece')].map(p => p.getAttribute('aria-label')));
    }
    await ctx.close();
  }
  // 200% zoom: a 720 px wide laptop window
  const z = await (await b.newContext({ viewport: { width: 720, height: 900 } })).newPage();
  const gz = await post('/api/new', { mode: 'hotseat', teams: ['Five Out', 'High-Low'], seed: 1, level: 'pro' });
  await z.goto(base + '/'); await z.waitForTimeout(600); await shot(z, 'zoom200_start', 'Start screen at 200% zoom (720 px)');
  await z.goto(`${base}/?code=${gz.code}&token=${gz.token}`); await z.waitForTimeout(1000); await shot(z, 'zoom200_table', 'Table at 200% zoom (720 px)');
  // Dark-mode and forced-colours requests
  const d = await (await b.newContext({ viewport: { width: 1440, height: 900 }, colorScheme: 'dark' })).newPage();
  await d.goto(`${base}/?code=${gz.code}&token=${gz.token}`); await d.waitForTimeout(1000); await shot(d, 'dark_request_table', 'The table when the device asks for dark mode');
  const f = await (await b.newContext({ viewport: { width: 1440, height: 900 }, forcedColors: 'active' })).newPage();
  await f.goto(`${base}/?code=${gz.code}&token=${gz.token}`); await f.waitForTimeout(1000); await shot(f, 'forced_colours_table', 'The table in forced colours (Windows high contrast)');
  await b.close();
  fs.writeFileSync(path.join(outDir, 'measures.json'), JSON.stringify(results, null, 1));
  console.log('DONE');
})().catch(e => { console.error(e); fs.writeFileSync(path.join(outDir, 'measures.json'), JSON.stringify(results, null, 1)); process.exit(1); });
