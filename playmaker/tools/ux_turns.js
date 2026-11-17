// Step 19: taps and an estimate of the seconds for five common turns, on a laptop and a phone.
//
//   node tools/ux_turns.js <server address> <before|after> <out.json>
//
// Each turn starts from the same position (a fresh game, the same seed, the preview setup), prepared through the API,
// and is then played by tapping the page as a player would. For every tap: the target's size and the distance from the
// last tap. The seconds are an estimate from Fitts' law with typical touch values (0.2 s a tap plus 0.15 s for each
// doubling of distance over target size) and 1 s for every scroll needed to bring the target into view. They compare
// one layout with another; they are not a stopwatch.
'use strict';
const { chromium, devices } = require('playwright');
const fs = require('fs');
const [base, version, outFile] = process.argv.slice(2);
const post = async (p, b) => (await fetch(base + p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b) })).json();
const get = async p => (await fetch(base + p)).json();
const A = 0.2, B = 0.15, SCROLL = 1.0;

async function fresh() {
  const g = await post('/api/new', { mode: 'hotseat', match_format: 'digital', teams: ['Five Out', 'High-Low'], seed: 3, level: 'pro', full: true, per_side: 4 });
  await post('/api/place', { code: g.code, token: g.token, preview: true });
  return g;
}
async function act(g, pred) {
  const s = await get(`/api/state?code=${g.code}&token=${g.token}`);
  const a = s.legal.find(pred); if (!a) throw new Error('no such action');
  return post('/api/act', { code: g.code, token: g.token, action: a });
}
const sq = (x, y) => 'ABCDEFGHIJKLMNOPQ'[x] + y;

// The turns: a preparation through the API (when the turn needs one), and the tap targets as a function of the version.
const TURNS = [
  { name: 'A move (O3 to the first square he can Move to)', prep: async () => null,
    pick: s => s.legal.find(a => a.kind === 'move' && a.piece === 2) },
  { name: 'A move and a pass (O2 moves, then O1 passes to him)', prep: async () => null,
    pick: s => s.legal.find(a => a.kind === 'move' && a.piece === 1), then: s => s.legal.find(a => a.kind === 'pass' && a.piece === 0 && a.target === 1) },
  { name: 'A screen (O4, the T to the north)', prep: async () => null,
    pick: s => s.legal.find(a => a.kind === 'screen' && a.piece === 3 && a.target === 0) },
  { name: 'A shot (O1, who has stepped into the three-point zone)', prep: async g => act(g, a => a.kind === 'move' && a.piece === 0 && sq(...a.dest) === 'H10'),
    pick: s => s.legal.find(a => a.kind === 'shot' && a.piece === 0) },
  { name: "A defender's move with a new arrow (X2)", prep: async g => act(g, a => a.kind === 'hesitate'),
    pick: s => s.legal.find(a => a.kind === 'move' && a.piece === 1 && sq(...a.dest) !== s.x[1].sq && a.arrow !== s.x[1].arrow) },
];

// ---- the old flow: the piece, the kind of action, the target (and the arrow button for a defender's move)
async function beforeTaps(page, s, a, tap) {
  await tap(`g.piece[aria-label^="${a.side}${a.piece + 1},"]`);
  const kindName = { move: 'Move', qs: 'Quick Step', sprint: 'Sprint', pass: 'Pass', screen: 'Screen', shot: 'Shot', dribble: 'Dribble' }[a.kind];
  const kinds = new Set(s.legal.filter(x => x.side === a.side && x.piece === a.piece).map(x => x.kind));
  if (kinds.size > 1) await tap(`#kindButtons button:text-matches("^${kindName}( \\\\(ends turn\\\\))?$")`);
  if (['move', 'qs', 'sprint'].includes(a.kind)) {
    await tap(`#court rect.target[aria-label="${kindName} to ${sq(...a.dest)}"]`);
    if (a.side === 'X') await tap(`#targetButtons button:text-matches("^face ${['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][a.arrow]}$")`);
  } else if (a.kind === 'pass') await tap(`#court [aria-label="pass to O${a.target + 1}"]`);
  else if (a.kind === 'screen') await tap(`#court [aria-label="T to the ${['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'][a.target]}"]`);
  else if (a.kind === 'shot') await tap(`#targetButtons button:has-text("Shoot: ${a.shot}")`);
}

// ---- the new flow (step 19, stage 1): the piece, the square or the action, then confirm
async function afterTaps(page, s, a, tap, drag) {
  const me = `${a.side}${a.piece + 1}`;
  const selected = await page.evaluate(m => { const g = document.querySelector(`g.piece[aria-label^="${m},"]`); return !!g && g.classList.contains('sel'); }, me);
  if (!selected) await tap(`g.piece[aria-label^="${me},"]`);
  if (['move', 'qs', 'sprint'].includes(a.kind)) {
    if (a.side === 'X' && (version === 'after_drag' || version === 'after_quick')) {
      await drag(`#court [data-sq="${sq(...a.dest)}"].target`, a.arrow);    // one gesture: press on the square, drag round to the arrow
      if (version === 'after_drag') await tap('#ghostPiece');
      return;
    }
    await tap(`#court [data-sq="${sq(...a.dest)}"].target`);
    if (version === 'after_quick') return;                                    // "Confirm each action: off": the tap acts
    if (a.side === 'X') {
      const cur = await page.evaluate(() => window.PM_GHOST ? window.PM_GHOST().arrow : null);
      // the rotate control, one tap for each 45°, the shorter way round
      let d = ((a.arrow - cur) % 8 + 8) % 8;
      const btn = d <= 4 ? '#rotCw' : '#rotCcw'; d = d <= 4 ? d : 8 - d;
      for (let k = 0; k < d; k++) await tap(btn);
    }
    await tap("#ghostPiece");                                                   // the fast path: the same square again (the ghost sits on it)
  } else {
    const SW = { layup: 'layup', dunk: 'dunk', post: 'post shot', floater: 'floater', mid: 'mid-range', long: 'long two', three: 'three' };
    const label = a.kind === 'pass' ? `Pass to O${a.target + 1}` : a.kind === 'screen' ? `Screen, T to the ${['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'][a.target]}`
      : a.kind === 'shot' ? `Shot: ${SW[a.shot] || a.shot}` : a.text;
    await tap(`#enderList button[data-act="${label}"]`);
    if (version === 'after_quick') {                                          // a roll still asks before the dice
      if (await page.locator('#modal:not(.hidden) button:text-is("Roll")').count()) await tap('#modal:not(.hidden) button:text-is("Roll")');
      return;
    }
    await tap(`#enderList button[data-act="${label}"]`);                        // the same choice again confirms
  }
}

async function run(device) {
  const b = await chromium.launch();
  const ctx = await b.newContext(device === 'phone' ? { ...devices['Galaxy S9+'] } : { viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  page.on('dialog', d => d.accept());
  const out = [];
  for (const T of TURNS) {
    const g = await fresh();
    await T.prep(g);
    await page.goto(`${base}/?code=${g.code}&token=${g.token}`); await page.waitForTimeout(1200);
    let last = null; const taps = [];
    const tap = async sel => {
      const loc = page.locator(sel).first();
      await loc.waitFor({ state: 'attached', timeout: 8000 });
      const vis = await loc.evaluate(e => { const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight && r.left >= 0 && r.right <= innerWidth; });
      if (!vis) await loc.scrollIntoViewIfNeeded();
      const r = await loc.boundingBox();
      const c = [r.x + r.width / 2, r.y + r.height / 2], w = Math.max(1, Math.min(r.width, r.height));
      const dist = last ? Math.hypot(c[0] - last[0], c[1] - last[1]) : 0;
      const t = A + B * Math.log2(dist / w + 1) + (vis ? 0 : SCROLL);
      taps.push({ sel, size: [Math.round(r.width), Math.round(r.height)], dist: Math.round(dist), scrolled: !vis, seconds: +t.toFixed(2) });
      last = c;
      await loc.click(); await page.waitForTimeout(350);
      if (await page.locator('#modal:not(.hidden) button.primary').count()) {      // a roll's result: Continue
        await page.locator('#modal:not(.hidden) button.primary').first().click(); await page.waitForTimeout(250);
      }
    };
    const drag = async (sel, dir) => {
      const loc = page.locator(sel).first();
      await loc.waitFor({ state: 'attached', timeout: 8000 });
      const vis = await loc.evaluate(e => { const r = e.getBoundingClientRect(); return r.top >= 0 && r.bottom <= innerHeight; });
      if (!vis) await loc.scrollIntoViewIfNeeded();
      const r = await loc.boundingBox(), c = [r.x + r.width / 2, r.y + r.height / 2], w = Math.max(1, Math.min(r.width, r.height));
      const dist = last ? Math.hypot(c[0] - last[0], c[1] - last[1]) : 0;
      const t = A + B * Math.log2(dist / w + 1) + 0.3 + (vis ? 0 : SCROLL);       // the press, plus a short drag
      taps.push({ sel: 'drag ' + sel, size: [Math.round(r.width), Math.round(r.height)], dist: Math.round(dist), scrolled: !vis, seconds: +t.toFixed(2) });
      const [dx, dy] = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]][dir];
      await page.mouse.move(c[0], c[1]); await page.mouse.down();
      for (const f of [0.4, 0.8, 1.2]) await page.mouse.move(c[0] + dx * 40 * f, c[1] - dy * 40 * f);
      await page.mouse.up(); await page.waitForTimeout(400);
      last = [c[0] + dx * 48, c[1] - dy * 48];
    };
    if (version === 'after_quick') await page.evaluate(() => localStorage.setItem('pm_confirm', '0')); else await page.evaluate(() => localStorage.removeItem('pm_confirm'));
    let s = await get(`/api/state?code=${g.code}&token=${g.token}`);
    const flow = version === 'before' ? beforeTaps : afterTaps;
    try {
      await flow(page, s, T.pick(s), tap, drag);
      if (T.then) { await page.waitForTimeout(500); s = await get(`/api/state?code=${g.code}&token=${g.token}`); await flow(page, s, T.then(s), tap, drag); }
      await page.waitForTimeout(500);
      const after = await get(`/api/state?code=${g.code}&token=${g.token}`);
      const want = T.then ? T.then(s) : T.pick(s);
      const played = (after.feed || []).some(e => e.text === want.text);
      out.push({ turn: T.name, taps: taps.length, seconds: +taps.reduce((n, x) => n + x.seconds, 0).toFixed(1), scrolls: taps.filter(x => x.scrolled).length,
        played, detail: taps });
    } catch (e) { out.push({ turn: T.name, error: String(e).slice(0, 300), detail: taps }); }
  }
  await b.close();
  return out;
}

(async () => {
  const res = { version, laptop: await run('laptop'), phone: await run('phone') };
  fs.writeFileSync(outFile, JSON.stringify(res, null, 1));
  for (const d of ['laptop', 'phone']) for (const r of res[d]) console.log(d, '|', r.turn, '|', r.error ? 'ERROR ' + r.error : `${r.taps} taps, ${r.seconds} s, ${r.scrolls} scrolls${r.played ? '' : ' NOT PLAYED'}`);
})().catch(e => { console.error(e); process.exit(1); });
