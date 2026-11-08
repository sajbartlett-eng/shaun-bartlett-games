// Playmaker playtest table. Renders from the server's state JSON; never decides a rule itself.
'use strict';
const PM = window.PMNotation;
const S = PM.S, PADX = PM.PADX, PADY = PM.PADY, COLS = PM.COLS;
const DIRS = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]];
const DIRN = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
const ZCOL = { K: 'var(--rim)', '3': 'var(--three)', M: 'var(--mid)', L: 'var(--long)', '.': 'var(--wood)' };
const ZLBL = { K: 'rim', '3': '3', M: 'mid', L: 'L2', '.': '' };
const SIDE_KINDS = ['end_turn', 'forfeit', 'hesitate', 'pause', 'target', 'pick', 'contest', 'forced_shot'];
const ENDERS = ['pass', 'screen', 'dribble', 'hesitate', 'shot', 'intercept', 'challenge', 'steal', 'pause'];
const SHORT = { 'Quick Step': 'QS', Dribble: 'Drb', Pass: 'Pass', Screen: 'Scr', Layup: 'Lay', Dunk: 'Dunk', Post: 'Post',
  Mid: 'Mid', Floater: 'Flt', 'Long 2': 'L2', Three: '3PT', FT: 'FT', Agility: 'Agi', Intercept: 'Int', Challenge: 'Chl',
  Steal: 'Stl', 'Foul (steal)': 'F·S', 'v Layup': 'Lay', 'v Dunk': 'Dunk', 'v Post': 'Post', 'v Mid': 'Mid',
  'v Floater': 'Flt', 'v Long 2': 'L2', 'v Three': '3PT', 'Foul (contest)': 'F·C' };
const COMPASS = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
const ZONE_WORD = { K: 'rim zone', '3': 'three-point zone', M: 'mid-range zone', L: 'long-two zone', '.': 'plain wood' };
const isPhone = () => window.matchMedia('(max-width: 820px)').matches;
const KIND_NAME = { contest: 'Contest', forced_shot: 'Forced shot', move: 'Move', qs: 'Quick Step', sprint: 'Sprint', pass: 'Pass', screen: 'Screen', dribble: 'Dribble',
  shot: 'Shot', intercept: 'Intercept', challenge: 'Challenge Screen', steal: 'Steal', hesitate: 'Hesitate', pause: 'Pause',
  end_turn: 'End turn', forfeit: 'Forfeit tokens', target: 'Target', pick: 'Give the ball' };

let G = null;        // {code, token}
let st = null;       // last state
let sel = { side: null, i: null, kind: null, dest: null };
let busy = false, pollTimer = null, lastSelKind = null, lastTimerNote = null;
let seenFeed = null;          // feed entries already shown on this screen

const $ = id => document.getElementById(id);
const el = (tag, attrs = {}, kids = []) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;           // an absent attribute, never the string "null"
    if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v;
    else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
  }
  for (const k of [].concat(kids)) if (k != null) e.append(k);
  return e;
};
const svg = (tag, attrs = {}) => {
  const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
};
const sqName = (x, y) => (x === -1 ? '@' : x === 17 ? 'R' : COLS[x]) + y;
const px = PM.px, py = PM.py;

async function api(path, body) {
  if (window.PM_BACKEND) return window.PM_BACKEND(path, body);      // the in-browser (Pyodide) build
  const opt = body ? { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {};
  const r = await fetch(path, opt);
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}

// ---------------------------------------------------------------- start screen
async function initStart() {
  const o = await api('/api/options');
  if (o.static) {
    $('mode').querySelector('option[value=remote]').disabled = true;
    $('joinBox').innerHTML = '<h2>Remote play</h2><p class="note">Remote play (two browsers, one game) needs the server version: <code>python -m playmaker_web</code>. This link version plays hot-seat and against the computer.</p>';
  }
  OPTS = o;
  for (const t of o.teams) { $('teamA').append(el('option', { value: t.name, text: t.name })); $('teamB').append(el('option', { value: t.name, text: t.name })); }
  $('teamA').value = o.first_game[0]; $('teamB').value = o.first_game[1];
  initLevels();
  fillProfiles();
  for (const id of ['playersBtn', 'playersBtn2']) if ($(id)) $(id).onclick = () => playersPage();
  for (const id of ['profA', 'profB']) $(id).addEventListener('change', async () => {
    if ($(id).value !== '__new') return;
    const name = prompt('Name for the new player'); if (!name) { $(id).value = ''; return; }
    const p = await PMRecords.createProfile(name); await fillProfiles(); $(id).value = p.id;
  });
  $('format').addEventListener('change', () => { $('perSideRow').classList.toggle('hidden', $('format').value !== 'digital'); });
  for (const s of o.scenarios) $('scenario').append(el('option', { value: s.n, text: `${s.n}. ${s.title} (${s.kind}, clock ${s.clock})` }));
  const showKind = () => {
    const k = $('kind').value;
    $('scenarioRow').classList.toggle('hidden', k !== 'scenario');
    $('teamsRow').classList.toggle('hidden', k === 'scenario');
    $('levelsRow').classList.toggle('hidden', k === 'scenario');
    $('formatRow').classList.toggle('hidden', k !== 'full');
    $('perSideRow').classList.toggle('hidden', $('format').value !== 'digital');
    const s = o.scenarios.find(x => String(x.n) === $('scenario').value);
    $('scenarioText').textContent = k === 'scenario' && s ? `${s.text} O: ${s.off}. X: ${s.dfn}.` :
      k === 'full' ? 'Sides swap every possession; the higher total wins. Digital: several possessions each and a turnover scores 0. Tabletop: one possession each, the printed rules.' :
      'One possession on the preview table setup.';
  };
  $('kind').onchange = showKind; $('scenario').onchange = showKind; showKind();
  const showHc = () => { $('timerBRow').classList.toggle('hidden', !($('hcA').checked && $('hcB').checked)); };
  $('hcA').onchange = showHc; $('hcB').onchange = showHc;
  $('create').onclick = create; if ($('join')) $('join').onclick = join;
  initPaths(showKind);
  const q = new URLSearchParams(location.search);
  if (q.get('code') && q.get('token')) { G = { code: q.get('code'), token: q.get('token') }; enterTable(); return; }
  if (q.get('code')) $('joinCode').value = q.get('code');
  const saved = localStorage.getItem('pm_game');
  if (saved && q.has('resume')) { G = JSON.parse(saved); enterTable(); }
}

// ---------------------------------------------------------------- the paths: learn, the computer, a friend, a card
let path = null;
function initPaths(showKind) {
  const greet = PMCoach.line('coach', "Welcome to the clipboard. New here? Take the course and I'll walk you through the whiteboard, the rules and how to read a matchup. Otherwise pick a game.", { speak: false, live: false });
  $('startCoach').append(greet);
  document.querySelectorAll('button.path').forEach(b => b.addEventListener('click', () => choosePath(b.dataset.path, showKind)));
  let done = false, saved = null; try { done = localStorage.getItem('pm_course_done') === '1'; saved = JSON.parse(localStorage.getItem('pm_game') || 'null'); } catch (e) { /* ignore */ }
  if (saved && saved.code) $('resumeRow').append(el('button', { text: `Resume the last game (${saved.code})`, onclick: async () => {
    try { await api(`/api/state?code=${saved.code}&token=${saved.token}`); G = saved; enterTable(); } catch (e) { $('resumeRow').innerHTML = ''; $('resumeRow').append(el('p', { class: 'note', text: 'That game is no longer on this server.' })); } } }));
  if (done) choosePath('computer', showKind, true);
}
// Setup, step 2 of the rulebook: roll the d20; the higher roll attacks first (player A, the offence tracker).
if ($('rollFirst')) $('rollFirst').addEventListener('click', () => {
  let a, b; do { a = 1 + Math.floor(Math.random() * 20); b = 1 + Math.floor(Math.random() * 20); } while (a === b);
  $('rollResult').textContent = `Rolled ${a} and ${b}: the ${a > b ? 'first' : 'second'} roller attacks first and is player A, on the offence tracker.`;
});
function choosePath(which, showKind, quiet) {
  path = which;
  document.querySelectorAll('button.path').forEach(b => b.setAttribute('aria-pressed', b.dataset.path === which ? 'true' : 'false'));
  if (which === 'learn') { startCourse(showKind); return; }
  $('setup').classList.remove('hidden');
  const scenario = which === 'scenario', computer = which === 'computer';
  $('kind').value = scenario ? 'scenario' : 'full';
  $('aiRow').classList.toggle('hidden', !computer && !scenario);
  $('aiSeatRow').classList.toggle('hidden', !computer);
  $('modeRow').classList.toggle('hidden', computer);
  $('profBRow').classList.toggle('hidden', which !== 'friend');
  $('profARow').firstChild.textContent = which === 'friend' ? 'Player A ' : 'Your profile ';
  $('rollRow').classList.toggle('hidden', which !== 'friend');      // the rulebook's setup: the higher d20 attacks first
  if (computer) $('mode').value = 'hotseat';
  // the last game's choices come back: the computer's level, your seat and the scouting level
  try {
    const last = JSON.parse(localStorage.getItem('pm_setup') || 'null');
    if (last) {
      if (computer && last.aiLevel && $('aiLevel').querySelector(`option[value="${last.aiLevel}"]`)) $('aiLevel').value = last.aiLevel;
      if (computer && last.aiSeat) $('aiSeat').value = last.aiSeat;
      if (last.level && $('level').querySelector(`option[value="${last.level}"]`)) $('level').value = last.level;
    }
  } catch (e) { /* private mode */ }
  if (scenario && !$('aiLevel').querySelector('option[value=""]')) $('aiLevel').insertBefore(el('option', { value: '', text: 'nobody: two players' }), $('aiLevel').firstChild);
  if (!scenario) { const none = $('aiLevel').querySelector('option[value=""]'); if (none) none.remove(); }
  $('setupTitle').textContent = which === 'computer' ? 'Play the computer' : which === 'friend' ? 'Play a friend' : 'Pick a scenario card';
  showKind();
  if (!quiet) { $('setup').scrollIntoView({ behavior: 'smooth', block: 'start' }); const f = $('setup').querySelector('select'); if (f) f.focus({ preventScroll: true }); }
}
function startCourse(showKind) {
  const box = $('course'); box.classList.remove('hidden');
  $('start').setAttribute('aria-hidden', 'true');
  PMCoach.course(box, { cardsEl: courseCards, onDone: () => { box.classList.add('hidden'); box.innerHTML = ''; $('start').removeAttribute('aria-hidden'); choosePath('computer', showKind); $('level').value = 'learn'; showLevelNote(); } });
}
function courseCards() {
  if (!OPTS) return null;
  const t = OPTS.teams.find(x => x.name === OPTS.first_game[0]) || OPTS.teams[0];
  const cards = t.cards.slice(0, 2).map(k => OPTS.cards.find(c => c.key === k)).filter(Boolean);
  return el('p', { class: 'note', text: `For example, ${t.name}'s cards: ${cards.map(c => `${c.role} (${c.tier})`).join(', ')}. In a game the cards sit beside the court with every rating.` });
}

// ---------------------------------------------------------------- step 3l: the two dials and the roster modes
let OPTS = null;
const POS = ['PG', 'SG', 'SF', 'PF', 'C'];
const TIER_V = { A: 1, B: 0, C: -1 };
const STD_NAME = { pro: 'pro', semi_pro: 'semi-pro', amateur: 'amateur' };
let lastDeal = null, draftId = null, draftState = null;
const card = k => OPTS.cards.find(c => c.key === k);
const signed = n => (n > 0 ? '+' : n < 0 ? '−' : '') + Math.abs(n);
function rosterMode() { return $('roster').value; }
function teamName(i) { return i ? 'Away' : 'Home'; }
function stdOf(i) { return i && $('handicap').checked && ['build', 'draft'].includes(rosterMode()) ? $('standardB').value : $('standard').value; }
function initLevels() {
  const L = OPTS.levels;
  const words = (list, id) => (list.find(x => x.id === id) || {}).words || '';
  const show = () => {
    $('ageNote').textContent = words(L.ages, $('age').value);
    $('standardNote').textContent = words(L.standards, $('standard').value) +
      (rosterMode() === 'prescribed' ? ' The prescribed teams are pro teams: the standard applies to built, random and drafted teams.' : '');
    const m = rosterMode();
    $('rosterNote').textContent = L.rosters[m] || '';
    $('prescribedRow').classList.toggle('hidden', m !== 'prescribed' && !(m === 'random' && $('randomFor').value !== 'both'));
    $('buildRow').classList.toggle('hidden', m !== 'build' && m !== 'free' && m !== 'draft');
    $('handicapRow').classList.toggle('hidden', m !== 'build' && m !== 'draft');
    $('standardBRow').classList.toggle('hidden', !((m === 'build' || m === 'draft') && $('handicap').checked));
    $('buildRow').querySelector('.builders').classList.toggle('hidden', m === 'draft');
    $('randomRow').classList.toggle('hidden', m !== 'random');
    $('draftRow').classList.toggle('hidden', m !== 'draft');
    if (m === 'build' || m === 'free') { builder(0); builder(1); }
    builderStatus();
  };
  for (const id of ['age', 'standard', 'standardB', 'roster', 'handicap', 'randomFor', 'teamA', 'teamB']) $(id).addEventListener('change', () => {
    if (['age', 'standard', 'roster'].includes(id)) { lastDeal = null; $('dealOut').innerHTML = ''; }
    if (['age', 'standard', 'standardB', 'roster', 'handicap'].includes(id)) { draftId = null; draftState = null; $('draftBoard').innerHTML = ''; }
    show();
  });
  $('levelsPage').onclick = levelsPage;
  $('dealBtn').onclick = () => doDeal();
  $('challengeBtn').onclick = () => { $('coherent').value = '0'; $('randomFor').value = 'both'; show(); doDeal(); };
  $('dealCodeBtn').onclick = () => doDeal($('dealCode').value);
  $('draftBtn').onclick = startDraft;
  show();
}
function levelsPage() {
  const L = OPTS.levels;
  modal([el('h2', { text: 'Levels and rosters' }),
    el('p', { text: L.intro }),
    el('h3', { text: 'Age' }), ...L.ages.map(a => el('p', { text: a.words })),
    el('h3', { text: 'Standard' }), ...L.standards.map(x => el('p', { text: x.words })), el('p', { class: 'note', text: L.standard_note }),
    el('h3', { text: 'Growth tags (junior)' }), el('div', { class: 'growbox' }, [el('p', { text: L.growth_box }), el('p', { text: L.growth.early }), el('p', { text: L.growth.late }),
      el('p', { text: 'Each tag stays face down until setup begins, then all ten are turned up before the offence places. A tag changes the numbers, never the marks.' })]),
    el('h3', { text: 'Picking the teams' }), ...Object.values(L.rosters).map(w => el('p', { text: w })),
    el('p', {}, [el('a', { href: L.sheet, target: '_blank', rel: 'noopener', text: 'The full playing levels sheet (PDF)' })]),
    el('button', { class: 'primary', text: 'Close', onclick: closeModal })], closeModal);
}

// Build (rules on) and Your team (rules off): one select per slot; the slot sets the piece number.
function slotOptions(slot, free) {
  const opts = [];
  for (const c of OPTS.cards) {
    const off = Math.abs(c.num - slot);
    if (!free && off > 1) continue;
    opts.push(el('option', { value: c.key, text: `${c.role} (${c.tier})${c.num !== slot ? ` · playing the ${slot}` : ''}` }));
  }
  if (free) return opts;
  return opts.sort((x, y) => (card(x.value).num !== slot) - (card(y.value).num !== slot));
}
function builderCards(i) { return [1, 2, 3, 4, 5].map(s => [$(`b${i}s${s}`).value, s]); }
function builder(i) {
  const box = $(`builder${i}`), free = rosterMode() === 'free', junior = $('age').value === 'junior';
  const sig = `${free}-${junior}`;
  if (box.dataset.built === sig) return;
  const keep = box.dataset.built ? builderCards(i) : null, name = box.dataset.built ? $(`bName${i}`).value : teamName(i);
  box.dataset.built = sig; box.innerHTML = '';
  const load = el('select', { id: `bLoad${i}`, onchange: () => {
    const t = OPTS.teams.find(x => x.name === load.value); if (!t) return;
    t.cards.forEach((k, n) => { $(`b${i}s${n + 1}`).value = k; }); builderStatus();
  } }, [el('option', { value: '', text: 'Start from a prescribed team…' }), ...OPTS.teams.map(t => el('option', { value: t.name, text: t.name }))]);
  box.append(el('h3', { text: `${teamName(i)} team` }),
    el('label', {}, ['Name ', el('input', { id: `bName${i}`, value: name, maxlength: 24 })]),
    el('label', {}, ['Load ', load]),
    ...[1, 2, 3, 4, 5].map(s => el('div', { class: 'slotrow' }, [
      el('label', {}, [`Slot ${s} (${POS[s - 1]}) `, el('select', { id: `b${i}s${s}`, onchange: builderStatus }, slotOptions(s, free))]),
      free && junior ? el('label', { class: 'tagpick' }, ['Growth ', el('select', { id: `b${i}t${s}`, 'aria-label': `Slot ${s} growth tag` },
        [['on_time', 'On time'], ['early', 'Early'], ['late', 'Late']].map(([v, t]) => el('option', { value: v, text: t })))]) : null])),
    el('p', { class: 'note', id: `bShape${i}`, role: 'status' }));
  const start = OPTS.teams.find(t => t.name === OPTS.first_game[i]);
  [1, 2, 3, 4, 5].forEach(s => { $(`b${i}s${s}`).value = keep ? keep[s - 1][0] : start.cards[s - 1]; if (!$(`b${i}s${s}`).value) $(`b${i}s${s}`).selectedIndex = 0; });
}
let checkSeq = 0;
async function builderStatus() {
  const m = rosterMode(), seq = ++checkSeq;
  const tiers = keys => keys.reduce((n, k) => n + TIER_V[card(k).tier], 0);
  let totals = null;
  if (m === 'build' || m === 'free') {
    totals = [];
    for (const i of [0, 1]) {
      const ents = builderCards(i);
      const r = await api('/api/roster', { cards: ents, standard: stdOf(i), rules: m === 'build' });
      if (seq !== checkSeq) return;
      const p = $(`bShape${i}`);
      const head = `Tier shape ${r.shape} · strength ${signed(r.strength)}${m === 'build' ? ` (${STD_NAME[stdOf(i)]})` : ''}. `;
      p.textContent = head + (r.problems.length ? r.problems.join(' ') : m === 'build' ? 'A legal roster.' : 'Ready.');
      p.classList.toggle('exp', r.problems.length > 0);
      totals.push(r.strength);
    }
  } else if (m === 'random' && lastDeal) totals = lastDeal.strength;
  else if (m === 'draft' && draftState && draftState.done) totals = [draftState.strength['1'], draftState.strength['2']];
  const w = $('builderWarn'); w.textContent = '';
  if (totals) {
    const d = totals[0] - totals[1];
    w.textContent = `Strength: Home ${signed(totals[0])}, Away ${signed(totals[1])}.` + (d ? ` Uneven teams: ${d > 0 ? 'Home' : 'Away'} +${Math.abs(d)}.` : ' Even teams.');
    w.classList.toggle('exp', d !== 0);
  }
}

// Random deal (B4): the code reproduces the rosters and the growth tags; the scout report opens before setup.
function rosterList(r) {
  return el('ol', { class: 'rosterlist' }, r.map(e => el('li', { text: `${e.role} (${e.tier})${e.flex ? ' · ' + e.flex : ''}` })));
}
async function doDeal(code) {
  try {
    const d = await api('/api/deal', code ? { code } : { age: $('age').value, standard: $('standard').value, coherent: $('coherent').value === '1' });
    lastDeal = d;
    if (code) { $('age').value = d.age; $('standard').value = d.standard; $('coherent').value = d.coherent ? '1' : '0'; }
    const out = $('dealOut'); out.innerHTML = '';
    out.append(el('p', {}, ['Deal code ', el('strong', { class: 'dealcode', text: d.code }), ` · ${d.coherent ? 'coherent' : 'pure'} · ${STD_NAME[d.standard]} · ${d.age}`]),
      el('div', { class: 'dealteams' }, [el('div', {}, [el('h3', { text: `Home (strength ${signed(d.strength[0])})` }), rosterList(d.rosters[0])]),
        el('div', {}, [el('h3', { text: `Away (strength ${signed(d.strength[1])})` }), rosterList(d.rosters[1])])]),
      d.tags_note ? el('p', { class: 'note', text: d.tags_note }) : null,
      el('p', {}, [el('button', { type: 'button', text: 'Scout report for both teams', onclick: () => dealReport(d) })]));
    builderStatus();
    dealReport(d);
  } catch (e) { $('dealOut').textContent = e.message; }
}
function dealReport(d) {
  modal([el('h2', { text: `Scout report: deal ${d.code}` }),
    el('p', { class: 'note', text: 'Both teams as dealt. Read them before setup.' + (d.tags_note ? ' Growth tags stay face down until setup begins.' : '') }),
    ...reportEl(d.report),
    el('button', { class: 'primary', text: 'Start the game', onclick: () => { closeModal(); create(); } }),
    el('button', { text: 'Close', onclick: closeModal })], closeModal);
}

// Draft (B5): snake order; each pick names its slot; the computer gives its reason for every pick.
function draftHuman() { return path === 'computer' && $('aiLevel').value ? ($('aiSeat').value === 'O' ? 1 : 2) : null; }
async function startDraft() {
  const stds = $('handicap').checked ? { A: $('standard').value, B: $('standardB').value } : null;
  const h = draftHuman();
  try {
    draftState = await api('/api/draft', { new: { standard: $('standard').value, standards: stds, age: $('age').value,
      computer: h ? $('aiLevel').value : null, human: h || 1 } });
    draftId = draftState.id; renderDraft();
  } catch (e) { $('draftBoard').textContent = e.message; }
}
async function draftPick(key, slot) {
  try { draftState = await api('/api/draft', { id: draftId, key, slot }); renderDraft(); }
  catch (e) { renderDraft(e.message); }
}
function renderDraft(err) {
  const d = draftState, box = $('draftBoard'); box.innerHTML = '';
  if (!d) return;
  const side = n => (n === 1 ? 'Home' : 'Away');
  const taken = new Set([...d.rosters['1'], ...d.rosters['2']].map(e => e.key));
  box.append(el('p', { class: 'draftturn', role: 'status', text: d.done ? 'Draft done. Start the game when ready.' :
    `Pick ${d.picks.length + 1} of ${d.order.length}: ${side(d.turn)}${d.human.includes(d.turn) ? '' : ' (computer)'}` }));
  if (err) box.append(el('p', { class: 'error', role: 'alert', text: err }));
  box.append(el('div', { class: 'draftteams' }, [1, 2].map(n => el('div', { class: 'draftteam' }, [
    el('h3', { text: `${side(n)} (${STD_NAME[d.standard[n]]})` }),
    el('ol', {}, [1, 2, 3, 4, 5].map(s => { const e = d.rosters[String(n)].find(x => x.slot === s);
      return el('li', { text: `Slot ${s}: ${e ? `${e.role} (${e.tier})${e.flex ? ' · ' + e.flex : ''}` : '—'}` }); }))]))));
  if (!d.done && d.human.includes(d.turn)) {
    const mine = d.rosters[String(d.turn)].map(e => e.slot);
    for (const [n, p] of POS.entries()) {
      const cards = OPTS.cards.filter(c => c.num === n + 1 && !taken.has(c.key));
      const det = el('details', { class: 'draftpos' }, [el('summary', { text: `${p}: ${cards.length} left` }),
        el('ul', {}, cards.map(c => el('li', {}, [el('span', { class: 'dcard', text: `${c.role} (${c.tier})` }),
          ...[c.num - 1, c.num, c.num + 1].filter(s => s >= 1 && s <= 5 && !mine.includes(s)).map(s => {
            const ok = (d.slots[c.key] || []).includes(s);
            return el('button', { type: 'button', class: 'small' + (ok ? '' : ' dim'), 'aria-label': `${c.role} (${c.tier}) in slot ${s}${s !== c.num ? `, playing the ${s}` : ''}${ok ? '' : ', not allowed'}`,
              text: s === c.num ? `Slot ${s}` : `Slot ${s} · playing the ${s}`, onclick: () => draftPick(c.key, s) });
          })])))]);
      box.append(det);
    }
  }
  if (d.picks.length) box.append(el('details', { class: 'draftlog', open: '' }, [el('summary', { text: 'Picks so far' }),
    el('ol', {}, d.picks.map(p => el('li', { text: `${side(p.side)}: ${p.role} (${p.tier}), slot ${p.slot}${p.reason ? '. ' + p.reason : ''}` })))]));
  builderStatus();
}

async function create() {
  const k = $('kind').value, mode = $('mode').value;
  const body = { mode, level: $('level').value, ai: { O: $('aiO').value || null, X: $('aiX').value || null } };
  if (path === 'computer' && $('aiLevel').value) {
    const me = $('aiSeat').value;                      // the computer is the other player; it follows the swap
    body.ai = { [me === 'O' ? 'B' : 'A']: $('aiLevel').value };
  } else if (path === 'scenario' && $('aiLevel').value) {
    body.ai = { X: $('aiLevel').value };               // on a card the human attacks; the computer defends
  }
  if ($('seed').value) body.seed = Number($('seed').value);
  try { localStorage.setItem('pm_setup', JSON.stringify({ aiLevel: $('aiLevel').value, aiSeat: $('aiSeat').value, level: $('level').value })); } catch (e) { /* ignore */ }
  const tA = $('timerA').value ? Number($('timerA').value) : null;
  const hc = $('hcA').checked && $('hcB').checked;
  const tB = hc ? ($('timerB').value ? Number($('timerB').value) : null) : tA;
  if (tA || tB) body.timer = { A: tA, B: tB, handicap: hc };
  try { localStorage.setItem('pm_sound', $('timerSound').checked ? '1' : '0'); } catch (e) { /* ignore */ }
  if (k === 'scenario') body.scenario = Number($('scenario').value);
  else {
    body.teams = [$('teamA').value, $('teamB').value]; body.full = k === 'full';
    if (k === 'full') { body.match_format = $('format').value; body.per_side = Number($('perSide').value); }
    if (path === 'computer') body.place = true;      // step 3k: the computer sets up its own side; you place yours
    const m = rosterMode();
    body.age = $('age').value; body.roster = m;
    body.standard = m === 'build' && $('handicap').checked ? { A: $('standard').value, B: $('standardB').value } : $('standard').value;
    if (m === 'build' || m === 'free') body.lineups = [0, 1].map(i => ({ name: $(`bName${i}`).value || teamName(i), cards: builderCards(i),
      tags: m === 'free' && body.age === 'junior' ? [1, 2, 3, 4, 5].map(s => $(`b${i}t${s}`).value) : null }));
    if (m === 'random') {
      if (!lastDeal) { await doDeal(); return; }     // deal first: the scout report for both teams opens before setup
      body.deal = lastDeal.code; body.random = $('randomFor').value; body.coherent = lastDeal.coherent;
    }
    if (m === 'draft') {
      if (!draftState || !draftState.done) { alert('Finish the draft first.'); return; }
      body.draft = draftId;
    }
  }
  const humans = matchPlayers(body);
  if (path === 'computer' && $('aiLevel').value === 'allstar' && humans.mine && humans.mine.profile) {
    try {                                          // the All-Star scouts the human's completed stored games (B8)
      const done = (await PMRecords.matches()).filter(m => m.done && PMRecords.sideOf(m, humans.mine.profile));
      if (done.length) body.scouting = PMTrainer.scouting(await PMRecords.groupsOf(humans.mine.profile), done.length);
    } catch (e) { /* no records in this browser */ }
  }
  try {
    const r = await api('/api/new', body);
    G = { code: r.code, token: r.token };
    try { G.rec = await startRecord(r.code, body, humans.players); } catch (e) { G.rec = null; }
    if (mode === 'remote') {
      const seat = await askSeat(r.code);
      G.token = (await api('/api/join', { code: r.code, seat })).token;
    }
    localStorage.setItem('pm_game', JSON.stringify(G));
    enterTable();
  } catch (e) { alert(e.message); }
}

function askSeat(code) {
  return new Promise(res => {
    modal([el('h2', { text: `Remote game ${code}` }), el('p', { text: 'Share this code with the other player. Which seat are you?' }),
      el('button', { class: 'primary', text: 'Offence', onclick: () => { closeModal(); res('O'); } }),
      el('button', { class: 'primary', text: 'Defence', onclick: () => { closeModal(); res('X'); } })]);
  });
}

async function join() {
  try {
    const code = $('joinCode').value.trim().toUpperCase();
    const r = await api('/api/join', { code, seat: $('joinSeat').value });
    G = { code, token: r.token };
    localStorage.setItem('pm_game', JSON.stringify(G));
    enterTable();
  } catch (e) { alert(e.message); }
}

function enterTable() {
  $('start').classList.add('hidden'); $('table').classList.remove('hidden');
  refresh(); pollTimer = setInterval(() => { if (!busy) refresh(true); }, 1500);
}

async function refresh(quiet) {
  try {
    const s = await api(`/api/state?code=${G.code}&token=${G.token}`);
    if (replay) { replay.live = s; return; }       // stepping through the other side's turn: keep the frame
    if (quiet && st && s.version === st.version) return;
    st = s; render();
  } catch (e) { if (!quiet) $('error').textContent = e.message; }
}

// ---------------------------------------------------------------- render
function render() {
  const s = st;
  $('title').textContent = (s.scenario ? `${s.scenario.n}. ${s.scenario.title}` : s.title);
  document.title = `${$('title').textContent} · Playmaker playtest`;
  $('clock').textContent = s.inbound ? `${s.clock} (frozen)` : s.clock;
  $('phase').textContent = s.phase + (s.inbound ? ` · inbound ${s.inbound}` : '');
  $('poss').textContent = s.full ? `${s.possession} of ${s.n_poss || 2}` : '1';
  if (s.full && s.strip) $('score').textContent = `A ${s.strip.totals.A} · B ${s.strip.totals.B}`;
  else if (s.full) { const t = s.scores.map(x => `${x.attacker}: ${x.total}`).join(' · '); $('score').textContent = t || '0'; }
  else $('score').textContent = String(s.bonus - 5 * s.turnovers);
  renderStrip(s);
  if (s.scores && s.scores.length > (trainerSeen || 0)) onPossessionOver(s);
  const LV = { rookie: 'Rookie', starter: 'Starter', allstar: 'All-Star', baseline: 'baseline' };
  const ai = Object.entries(s.ai || {}).map(([k, v]) => `${k === 'O' ? 'offence' : 'defence'}: ${LV[v] || v}`).join('; ');
  $('meta').innerHTML = '';
  $('meta').append(el('div', { text: `${s.mode === 'remote' ? 'Remote' : 'Hot-seat'} · code ${s.code}${s.seat && s.seat !== 'both' ? ' · you: ' + (s.seat === 'O' ? 'Offence' : 'Defence') : ''}` }),
    ...(ai ? [el('div', { text: `Computer ${ai}` })] : []),
    ...(s.timer ? [el('div', { text: s.timer.handicap ? `Timer (handicap): player A ${s.timer.setting.A || 'off'}${s.timer.setting.A ? ' s' : ''}, player B ${s.timer.setting.B || 'off'}${s.timer.setting.B ? ' s' : ''}` : `Timer: ${s.timer.setting.A} s per decision` })] : []),
    ...((s.experimental || []).length ? [el('div', { class: 'exp', text: `Experimental lineup: ${s.experimental.join(', ')}` })] : []),
    ...(s.scout && s.scout.report && s.scout.report.level !== 'pro' ? [el('button', { class: 'small', text: 'Scout report', onclick: () => showReport('Scout report') })] : []),
    el('button', { class: 'small', text: 'Play story', onclick: showStory }));
  renderCoachLine();
  const sideChip = s.stage === 'over' ? '' : (s.side_to_act === 'O' ? 'OFFENCE TO ACT · ' : s.side_to_act === 'X' ? 'DEFENCE TO ACT · ' : '');
  $('summary').textContent = replay ? `${sideName(replay.entries[replay.k].side).toUpperCase()} ACTED · ${s.summary}`
    : sideChip + briefSummary(s) + (s.can_act ? '' : s.stage === 'over' ? '' : ' · waiting for the other side');
  if (s.placing) $('summary').textContent = `SETUP · the ${s.placing.side === 'O' ? 'offence' : 'defence'} places its pieces` + (s.placing.mine ? '' : s.placing.by_ai ? ' (the computer)' : ' · waiting for the other side');
  if (s.timer && s.timer.note) $('summary').textContent += ` · ${s.timer.note}`;
  if (s.timer && s.timer.note && s.timer.note !== lastTimerNote) announce(s.timer.note);
  lastTimerNote = s.timer ? s.timer.note : null;
  $('summary').dataset.side = s.side_to_act || '';
  $('offTeam').textContent = s.teams[0] + (s.full ? ` (player ${s.attacker})` : '');
  $('defTeam').textContent = s.teams[1] + (s.full ? ` (player ${s.attacker === 'A' ? 'B' : 'A'})` : '');
  renderCards('offCards', s.o, 'O'); renderCards('defCards', s.x, 'X');
  renderTracker('offTracker', 'O'); renderTracker('defTracker', 'X');
  renderCourt(); renderActions(); renderScenario(); renderRolls(); renderLog(); renderPhoneLists(); renderRecent(); renderCompare();
  $('phoneTimer').innerHTML = ''; if (s.timer && s.timer.mode !== 'idle' && s.timer.side) $('phoneTimer').append(timerEl());
  timerRecv();
  const k = sel.kind || null;
  if (s.timer && s.can_act && k !== lastSelKind && !busy) timerEvent(k ? 'select' : 'cancel');
  lastSelKind = k;
  $('actionsPanel').classList.toggle('hidden', !!replay);
  if (replay) { renderStep(); diagramDue(); return; }
  if (scoutModalIfDue()) return;
  if (s.placing) return;
  if (showFeedIfNew()) return;          // the other side's turn first, one action at a time; the end screen follows
  if (diagramDue()) return;             // a phase just ended: its diagram, then Continue
  if (readyIfDue()) return;
  if (s.stage === 'target' && s.can_act) targetModal();
  else if (s.stage === 'over') endModal();
}

// Step 3l: what the level changes on a card: 'U16 · TIER A' / 'U20 · TIER A', the growth tag (E or L) and a flex slot.
function levelBits(c) {
  const out = [];
  if (c.label && c.label !== `TIER ${c.tier}`) out.push(el('span', { class: 'agelabel', text: c.label }));
  if (c.growth) out.push(el('span', { class: 'growchip ' + c.growth, title: c.growth_words, text: c.growth === 'early' ? 'E' : 'L',
    'aria-label': `growth tag ${c.growth}` }));
  if (c.flex) out.push(el('span', { class: 'flexchip', text: c.flex }));
  return out;
}
function cardEl(c, side, label, extra) {
  const head = el('div', { class: 'head' }, [el('span', { text: `${label} ${c.role} (${c.tier})` }), ...levelBits(c), el('span', { text: `QS ${c.qs}` })]);
  const groups = c.groups.map(g => el('table', { class: 'grp', 'aria-label': g.name }, [
    el('tr', {}, [el('th', { class: 'gname', text: g.name === 'Actions' ? 'Act' : g.name === 'Shots' ? 'Shot' : 'Con' }),
      ...g.ratings.map(r => el('th', { text: SHORT[r.name] || r.name, title: r.name }))]),
    el('tr', {}, [el('td'), ...g.ratings.map(r => el('td', { class: 'r ' + r.band, text: `${r.value}${r.mark}`,
      'aria-label': `${r.name} ${r.value} ${r.band === 'H' ? 'above average' : r.band === 'L' ? 'below average' : 'average'}` }))])]));
  const grow = c.growth_words ? el('div', { class: 'grownote', text: c.growth_words }) : null;
  return el('div', { class: `card ${side === 'O' ? 'offence' : 'defence'}` }, [head, ...groups, grow, extra || null]);
}

const pinnedCards = new Set();          // cards a player opened by hand (the rest show one line until they matter)
function openCards() {
  // the pair that matters now: the selected piece (or the one being compared, or the ball carrier) and its matchup
  const open = new Set(pinnedCards);
  const focus = sel.side && sel.i != null ? { side: sel.side, i: sel.i } : compare ? { side: compare.side, i: compare.i }
    : (st.o.find(p => p.ball) ? { side: 'O', i: st.o.find(p => p.ball).i } : null);
  if (focus) {
    open.add(focus.side + focus.i);
    const js = ((st.matchups || {})[focus.side] || [])[focus.i] || [];
    if (js.length) open.add((focus.side === 'O' ? 'X' : 'O') + js[0]);
  }
  return open;
}
function cardSummary(c) {
  const ups = [], downs = [];
  for (const g of c.groups) for (const r of g.ratings) { if (r.band === 'H') ups.push(`${SHORT[r.name] || r.name} ${r.value}`); else if (r.band === 'L') downs.push(`${SHORT[r.name] || r.name} ${r.value}`); }
  const bits = [];
  if (ups.length) bits.push(el('span', { class: 'H', text: '▲ ' + ups.slice(0, 4).join(', ') + (ups.length > 4 ? '…' : '') }));
  if (downs.length) bits.push(el('span', { class: 'L', text: '▼ ' + downs.slice(0, 4).join(', ') + (downs.length > 4 ? '…' : '') }));
  if (!bits.length) bits.push(el('span', { text: 'average across the card' }));
  return el('div', { class: 'cardsum' }, bits.flatMap((b, k) => k ? [' · ', b] : [b]));
}
function renderCards(id, pieces, side) {
  const box = $(id); box.innerHTML = '';
  box.append(el('div', { class: 'key' }, [el('span', { class: 'H', text: '▲ above average' }), ' ', el('span', { text: 'plain = average' }), ' ', el('span', { class: 'L', text: '▼ below average' })]));
  const open = openCards();
  for (const p of pieces) {
    const c = p.card, key = side + p.i, isOpen = open.has(key);
    const head = el('button', { class: 'head', type: 'button', 'aria-expanded': isOpen ? 'true' : 'false',
      onclick: () => { if (pinnedCards.has(key)) pinnedCards.delete(key); else if (isOpen) pinnedCards.add('-' + key); else pinnedCards.add(key); if (pinnedCards.has('-' + key) && !isOpen) pinnedCards.delete('-' + key); render(); } },
      [el('span', { text: `${side}${p.i + 1} ${c.role} (${c.tier})` }), ...levelBits(c), el('span', { text: `QS ${c.qs}` }),
        el('span', { class: 'sr-only', text: isOpen ? ', full card; press to fold' : ', one line; press to open the card' })]);
    const groups = c.groups.map(g => el('table', { class: 'grp', 'aria-label': g.name }, [
      el('tr', {}, [el('th', { class: 'gname', text: g.name === 'Actions' ? 'Act' : g.name === 'Shots' ? 'Shot' : 'Con' }),
        ...g.ratings.map(r => el('th', { text: SHORT[r.name] || r.name, title: r.name }))]),
      el('tr', {}, [el('td'), ...g.ratings.map(r => el('td', { class: 'r ' + r.band, text: `${r.value}${r.mark}`,
        'aria-label': `${r.name} ${r.value} ${r.band === 'H' ? 'above average' : r.band === 'L' ? 'below average' : 'average'}` }))])]));
    const note = side === 'O' && st.inbound_note && p.i === st.inbounder ? el('div', { class: 'inbnote', text: st.inbound_note }) : null;
    const folded = pinnedCards.has('-' + key) || !isOpen;           // '-' + key: folded by hand although it matters now
    const grow = c.growth_words && !folded ? el('div', { class: 'grownote', text: c.growth_words }) : null;
    box.append(el('div', { class: `card ${side === 'O' ? 'offence' : 'defence'}${sel.side === side && sel.i === p.i ? ' focus' : ''}${folded ? ' collapsed' : ''}` },
      [head, folded ? cardSummary(c) : null, ...groups, grow, note]));
  }
}

let lastTurnKey = null, turnsSeen = 0;
function briefSummary(s) {
  // the state stays; the rule reminders ("a turn-ender ends it now", "Hesitate: 1 a phase") drop off once a player
  // has seen six turns in this browser (the full line stays in the bar's tooltip)
  const key = `${s.possession}:${s.phase}:${s.side_to_act}:${s.turn}`;
  if (key !== lastTurnKey) { lastTurnKey = key; try { turnsSeen = Number(localStorage.getItem('pm_turns') || 0) + 1; localStorage.setItem('pm_turns', String(turnsSeen)); } catch (e) { turnsSeen += 1; } }
  const parts = (s.summary || '').split(' · ');
  if (turnsSeen <= 6 || parts.length <= 2) { $('summary').removeAttribute('title'); return s.summary; }
  $('summary').setAttribute('title', s.summary);
  return parts.slice(0, 2).join(' · ');
}
function renderTracker(id, side) {
  const s = st, box = $(id); box.innerHTML = '';
  const pool = el('div', { class: 'pool', title: `${s.tokens[side]} of 6 tokens left` });
  for (let k = 0; k < 6; k++) pool.append(el('span', { class: 'tok ' + (k < s.tokens[side] ? 'full' : 'spent') }));
  box.append(el('div', { text: `Action pool: ${s.tokens[side]} of 6 left` }), pool);
  if (s.timer && s.timer.side === side && s.timer.mode !== 'idle') box.prepend(timerEl());
  const tb = el('table', { class: 'slots' });
  for (const p of (side === 'O' ? s.o : s.x)) {
    const chips = p.slots.map(k => el('span', { class: 'chip', text: KIND_NAME[k] || k }));
    if (p.locked) chips.push(el('span', { class: 'chip lock', text: 'LOCK' }));
    if (p.screen) chips.push(el('span', { class: 'chip', text: `T ${DIRN[p.screen.dir]}` }));
    tb.append(el('tr', {}, [el('td', { text: `${side}${p.i + 1}` }), el('td', {}, chips.length ? chips : ['–'])]));
  }
  box.append(tb);
  const used = s.limits[side].filter(l => l.used > 0);
  if (used.length) {
    const lim = el('div', { class: 'limits' }, used.map(l => el('span', { class: l.used >= l.limit ? 'full' : '', text: `${KIND_NAME[l.kind] || l.kind} ${l.used}/${l.limit}` })));
    box.append(el('div', { text: 'Per-phase limits used' }), lim);
  } else box.append(el('div', { class: 'note', text: 'No per-phase limits used yet (Move: once per player).' }));
  const wk = side === 'X' ? 'pause' : 'hesitate', w = s.limits[side].find(l => l.kind === wk);
  if (w) box.append(el('div', { class: 'waits', text: `${KIND_NAME[wk]}: ${w.limit} a phase (${w.used >= w.limit ? 'used' : 'not used yet'})` }));
  const rules = el('details', { class: 'rulesbox' }, [el('summary', { text: 'Rule reminders' }),
    el('div', { class: 'waits interceptrule' }, [
      el('div', { text: 'Through you: a pass through your square can be challenged, whatever your facing.' }),
      el('div', { text: 'Jump the lane: one straight Move, Quick Step or Sprint along your arrow onto the pass line, then Intercept.' }),
      el('div', { text: 'Next to the passer: no intercept on any square around the passer. Steal instead.' }),
      el('div', { text: "Denied: a pass can't go through a defender next to the receiver." }),
      el('div', { text: 'Picked off: −5 and lose 2 seconds. On the last phase, the possession scores 0.' })]),
    el('div', { class: 'waits stealrule', text: 'Stolen (in play or on a shot): −5 and lose 2 seconds; the ball stays with you, and a stolen shot is cancelled. On the last phase, the possession scores 0.' }),
    side === 'O' ? el('div', { class: 'waits screenrule', text: s.screen_rule === 'two_turns'
      ? "Screen: ends your turn. The screener can't move; it flips back after your next turn."
      : "Screen: First action, or second after your own Move. Ends your turn. Lasts until you move or it's beaten." }) : null]);
  box.append(rules);
}

// The defender reach (zones of influence) can be hidden by a player who finds it busy; the rules don't change.
function showReach() { try { return localStorage.getItem('pm_reach') !== '0'; } catch (e) { return true; } }
// the shot-zone labels: on when a shot is on offer, or when the player asks for them; the colours stay
function zonesShown() {
  let pref = null; try { pref = localStorage.getItem('pm_zones'); } catch (e) { /* ignore */ }
  if (pref === '1') return true;
  if (pref === '0') return false;
  return !!(st && (st.legal || []).some(a => a.kind === 'shot' || a.kind === 'forced_shot'));
}

function renderCourt() {
  const s = st, c = $('court');
  c.innerHTML = '';
  PM.court(c, s.zones, { axes: true, plain: !zonesShown() });
  c.setAttribute('role', 'group');
  c.setAttribute('aria-label', `Court, 17 columns A to Q by 14 rows, rim at I2. ${s.summary}`);
  drawInfluence(c);
  // arrow lines the ball carrier can't cross (the old drive rule only)
  const carrier = s.o.find(p => p.ball);
  if (sel.side === 'O' && carrier && sel.i === carrier.i) {
    for (const l of s.arrow_lines) c.append(svg('line', { x1: px(l.start[0]) + S / 2, y1: py(l.start[1]) + S / 2, x2: px(l.end[0]) + S / 2, y2: py(l.end[1]) + S / 2, stroke: '#222', 'stroke-width': 3, 'stroke-dasharray': '6 4' }));
  }
  if (s.placing && s.placing.mine) { placementPieces(c); placementTargets(c); return; }
  drawGhost(c);
  PM.marks(c, turnMarks(), { numbers: true, avoid: [...st.o, ...st.x].map(p => [px(p.x) + S / 2, py(p.y) + S / 2]) });          // the turn in play, in notation (resets when the turn ends)
  // a pass still in the air that no mark covers yet (the defence is answering it)
  if (s.pending && !turnMarks().some(m => m.kind === 'pass')) {
    const a = s.o[s.pending[0]], b = s.o[s.pending[1]];
    c.append(svg('line', { x1: px(a.x) + S / 2, y1: py(a.y) + S / 2, x2: px(b.x) + S / 2, y2: py(b.y) + S / 2, stroke: PM.INK, 'stroke-width': 2.6, 'stroke-dasharray': '8 6', opacity: 0.85 }));
  }
  for (const p of s.o) drawO(c, p);
  for (const p of s.x) drawX(c, p);
  drawTargets(c);
}

// The marks of the turn in play: the acting side's actions so far in its current turn. During the step-through
// of the other side's turn, the actions stepped so far of that turn. They reset when the turn ends.
function turnMarks() {
  if (replay) {
    const e = replay.entries[replay.k];
    return replay.entries.slice(0, replay.k + 1).filter(x => x.possession === e.possession && x.phase === e.phase && x.turn === e.turn && x.side === e.side)
      .map(x => x.mark).filter(Boolean);
  }
  const side = st.side_to_act;
  if (!side || st.stage === 'over' || st.turn == null) return [];
  const out = [];
  for (let k = (st.feed || []).length - 1; k >= 0; k--) {
    const e = st.feed[k];
    if (e.side !== side || e.possession !== st.possession || e.phase !== st.phase || e.turn !== st.turn) break;
    if (e.mark) out.unshift(e.mark);
  }
  return out;
}

function pieceLabel(side, p) {
  const z = st.zones[p.y - 1] ? ZONE_WORD[st.zones[p.y - 1][p.x]] : 'off the court';
  const bits = [`${side}${p.i + 1}, number ${p.i + 1}, ${p.card.role}, on ${p.sq} (${z})`];
  if (p.card && p.card.growth) bits.push(`growth tag ${p.card.growth}`);
  if (p.card && p.card.flex) bits.push(p.card.flex);
  if (side === 'O' && p.ball) bits.push('has the ball');
  if (side === 'O' && p.screen) bits.push(`screening, T to the ${COMPASS[p.screen.dir]}`);
  if (side === 'X') bits.push(`arrow pointing ${COMPASS[p.arrow]}`);
  if (p.locked) bits.push('locked');
  const b = st.influence && st.influence.badges && st.influence.badges[side] && st.influence.badges[side][p.i];
  if (b && b.move) bits.push('Move used');
  if (b && b.qs) bits.push('Quick Step used');
  if (sel.side === side && sel.i === p.i) bits.push('selected');
  const n = pieceActs(side, p.i).length;
  if (st.can_act && n) bits.push(`${n} legal action${n === 1 ? '' : 's'}`);
  return bits.join(', ');
}

function pieceGroup(side, i, opts) {
  opts = opts || {};
  const p = opts.piece || (side === 'O' ? st.o : st.x)[i];
  const acted = !opts.piece && actedPieces().has(side + i);
  const on = opts.piece ? !!opts.selected : (sel.side === side && sel.i === i);
  const g = svg('g', { class: 'piece' + (on ? ' sel' : '') + (acted ? ' acted' : '') + (opts.inert ? ' inert' : ''), tabindex: opts.inert ? -1 : 0, role: 'button',
    'aria-label': opts.label || pieceLabel(side, p), 'aria-pressed': on ? 'true' : 'false' });
  if (opts.inert) { g.removeAttribute('role'); g.removeAttribute('aria-pressed'); g.setAttribute('aria-hidden', 'true'); return g; }
  const choose = opts.onClick || (() => selectPiece(side, i));
  g.addEventListener('click', choose); g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); } });
  return g;
}

function drawO(c, p, opts) {
  const g = pieceGroup('O', p.i, opts);
  PM.pieceO(g, p.x, p.y, p.i + 1, { ball: p.ball, screen: p.screen ? p.screen.dir : null });
  c.append(g);
  const b = st.influence && st.influence.badges && st.influence.badges.O[p.i];
  const tg = svg('g', { class: 'tags', 'aria-hidden': 'true' }); PM.tags(tg, p.x, p.y, b, p.locked, p.card && p.card.growth); c.append(tg);
}

function drawX(c, p, opts) {
  const g = pieceGroup('X', p.i, opts);
  const wedge = st.influence && st.influence.arrow_mode === 'wedge';
  PM.pieceX(g, p.x, p.y, p.i + 1, wedge ? [p.arrow, (p.arrow + 1) % 8] : [p.arrow]);
  c.append(g);
  const b = st.influence && st.influence.badges && st.influence.badges.X[p.i];
  const tg = svg('g', { class: 'tags', 'aria-hidden': 'true' }); PM.tags(tg, p.x, p.y, b, p.locked, p.card && p.card.growth); c.append(tg);
}

// Zones of influence (every defender, along the arrow line, out to the current reach), active screens and the
// diagonal steps they block, the passer's ring and intercept marks when a pass is being chosen, and the selected
// attacker's movement reach. Patterns, not colour alone; each zone square numbered for its defender.
function drawInfluence(c) {
  const inf = st.influence;
  if (!inf) return;
  const g = svg('g', { class: 'influence', 'aria-hidden': 'true' });
  const count = {};
  for (const z of (showReach() ? inf.zones : [])) {
    for (const q of z.squares) {
      const k = count[q.sq] = (count[q.sq] || 0) + 1, inset = 1 + (k - 1) * 3;
      const sprint = q.kind === 'sprint';
      g.append(svg('rect', { class: 'zone ' + (sprint ? 'zone-sprint' : 'zone-move'), x: px(q.x) + inset, y: py(q.y) + inset,
        width: S - 2 * inset, height: S - 2 * inset, fill: `url(#${sprint ? 'zsprint' : 'zhatch'})`,
        stroke: 'rgba(31,42,68,0.45)', 'stroke-width': 1, 'stroke-dasharray': sprint ? '3 2' : '' }));
      const t = svg('text', { class: 'zonenum', x: px(q.x) + 3 + (k - 1) * 8, y: py(q.y) + S - 4 }); t.textContent = z.defender + 1; g.append(t);
    }
  }
  for (const sc of inf.screens) {
    g.append(svg('rect', { class: 'screen-t', x: px(sc.t.x) + 2, y: py(sc.t.y) + 2, width: S - 4, height: S - 4, fill: 'url(#zscreen)', stroke: '#783c00', 'stroke-width': 1.5 }));
    const t = svg('text', { class: 'zonenum', x: px(sc.t.x) + S - 9, y: py(sc.t.y) + 11, fill: '#783c00' }); t.textContent = 'T'; g.append(t);
    for (const [ax, ay, bx, by] of sc.blocked) {
      const mx = (px(ax) + px(bx)) / 2 + S / 2, my = (py(ay) + py(by)) / 2 + S / 2;
      g.append(svg('path', { class: 'screen-block', d: `M${mx - 4} ${my - 4} L${mx + 4} ${my + 4} M${mx - 4} ${my + 4} L${mx + 4} ${my - 4}`, stroke: '#783c00', 'stroke-width': 2 }));
    }
  }
  if (sel.side === 'O' && sel.kind === 'pass') {
    const passes = (st.legal || []).filter(a => a.kind === 'pass' && a.piece === sel.i);
    const ring = (passes[0] && passes[0].ring) || [];
    for (const q of ring) {
      g.append(svg('rect', { class: 'ring-free', x: px(q.x) + 3, y: py(q.y) + 3, width: S - 6, height: S - 6, fill: 'rgba(40,140,60,0.12)',
        stroke: '#1b5e20', 'stroke-width': 1.5, 'stroke-dasharray': '1 3' }));
      const t = svg('text', { x: px(q.x) + S / 2, y: py(q.y) + S - 5, 'text-anchor': 'middle', 'font-size': 7.5, fill: '#1b5e20' }); t.textContent = 'safe'; g.append(t);
    }
    const from = st.o[sel.i];
    for (const d of (st.denied || [])) {
      const r = st.o[d.receiver], x = st.x[d.defender];
      const ax = px(from.x) + S / 2, ay = py(from.y) + S / 2, bx = px(x.x) + S / 2, by = py(x.y) + S / 2;
      const len = Math.hypot(bx - ax, by - ay) || 1, ux = (bx - ax) / len, uy = (by - ay) / len;
      const ex = bx - ux * 14, ey = by - uy * 14;
      g.append(svg('line', { class: 'denied-lane', x1: ax + ux * 16, y1: ay + uy * 16, x2: ex, y2: ey, stroke: PM.RED, 'stroke-width': 2.2, 'stroke-dasharray': '6 5', opacity: 0.85 }));
      g.append(svg('line', { class: 'denied-bar', x1: ex - uy * 10, y1: ey + ux * 10, x2: ex + uy * 10, y2: ey - ux * 10, stroke: PM.RED, 'stroke-width': 3.5, 'stroke-linecap': 'round' }));
      g.append(svg('circle', { class: 'denier', cx: bx, cy: by, r: 16, fill: 'none', stroke: PM.RED, 'stroke-width': 2.4 }));
      const t = svg('text', { x: px(r.x) + S / 2, y: py(r.y) - 3, 'text-anchor': 'middle', 'font-size': 9, 'font-weight': 'bold', fill: PM.RED }); t.textContent = 'denied'; g.append(t);
    }
    for (const a of passes) for (const th of (a.threats || [])) {
      if (th.x === undefined) continue;
      const cx = px(th.x) + S / 2, cy = py(th.y) + S / 2;
      g.append(svg('circle', { class: 'icpt-mark icpt-' + th.how, cx, cy, r: 8, fill: '#fff', stroke: PM.RED, 'stroke-width': 2,
        'stroke-dasharray': th.how === 'through' ? '' : '4 2' }));
      const t = svg('text', { x: cx, y: cy + 3.5, 'text-anchor': 'middle', 'font-size': 9, 'font-weight': 'bold', fill: PM.RED }); t.textContent = th.defender + 1; g.append(t);
    }
  }
  if (sel.side === 'O' && sel.i !== null && sel.i !== undefined && inf.reach[sel.i]) {
    for (const q of inf.reach[sel.i]) {
      g.append(svg('circle', { class: 'reach', cx: px(q.x) + S / 2, cy: py(q.y) + S / 2, r: 5, fill: 'none', stroke: '#1b5e20', 'stroke-width': 2, 'stroke-dasharray': '2 2' }));
    }
  }
  c.append(g);
}

// ---------------------------------------------------------------- selection and actions
function myActs() { return st.legal || []; }
function pieceActs(side, i) { return myActs().filter(a => a.side === side && a.piece === i && !SIDE_KINDS.includes(a.kind)); }

let compare = null;     // {side, i, k}: the card panel and which matchup is showing
function selectPiece(side, i) {
  sel = { side, i, kind: null, dest: null };
  compare = { side, i, k: 0 };
  const kinds = [...new Set(pieceActs(side, i).map(a => a.kind))];
  if (kinds.length === 1) sel.kind = kinds[0];
  render();
  const first = $('kindButtons').querySelector('button') || $('targetButtons').querySelector('button');
  if (first) first.focus();
}

function drawTargets(c) {
  if (sel.kind == null) return;
  const acts = pieceActs(sel.side, sel.i).filter(a => a.kind === sel.kind);
  const mark = (x, y, label, fn) => {
    const onPiece = st.o.some(p => p.x === x && p.y === y) || st.x.some(p => p.x === x && p.y === y);
    // on a piece: a ring around it (so its number stays readable); on an empty square: a filled tile
    const r = onPiece
      ? svg('circle', { class: 'target ring-target', cx: px(x) + S / 2, cy: py(y) + S / 2, r: 18, tabindex: 0, role: 'button', 'aria-label': label, 'pointer-events': 'all' })
      : svg('rect', { class: 'target', x: px(x) + 3, y: py(y) + 3, width: S - 6, height: S - 6, rx: 5, tabindex: 0, role: 'button', 'aria-label': label });
    r.addEventListener('click', fn); r.addEventListener('keydown', e => { if (e.key === 'Enter') fn(); });
    c.append(r);
  };
  if (['move', 'qs', 'sprint'].includes(sel.kind)) {
    const seen = new Set();
    for (const a of acts) {
      const k = a.dest.join(','); if (seen.has(k)) continue; seen.add(k);
      mark(a.dest[0], a.dest[1], `${KIND_NAME[a.kind]} to ${sqName(a.dest[0], a.dest[1])}`, () => chooseDest(a.dest));
    }
  } else if (sel.kind === 'pass') {
    for (const a of acts) { const r = st.o[a.target]; mark(r.x, r.y, `pass to O${a.target + 1}`, () => submit(a)); }
  } else if (sel.kind === 'dribble') {
    for (const a of acts) { const x = st.x[a.target]; mark(x.x, x.y, `dribble v X${a.target + 1}`, () => submit(a)); }
  } else if (sel.kind === 'screen') {
    const p = st.o[sel.i];
    for (const a of acts) { const d = DIRS[a.target]; mark(p.x + d[0], p.y + d[1], `T to the ${DIRN[a.target]}`, () => submit(a)); }
  }
}

function chooseDest(dest) {
  const acts = pieceActs(sel.side, sel.i).filter(a => a.kind === sel.kind && a.dest[0] === dest[0] && a.dest[1] === dest[1]);
  if (acts.length === 1) return submit(acts[0]);
  sel.dest = dest; renderActions();
}

function actionButton(a, label) {
  const ender = ENDERS.includes(a.kind);
  return el('button', { class: ender ? 'ender' : '', text: label + (ender ? ' (ends turn)' : ''), onclick: () => submit(a), title: a.text });
}

function renderActions() {
  const s = st;
  if (s.placing) return renderPlacement();
  $('selected').textContent = ''; $('kindButtons').innerHTML = ''; $('targetButtons').innerHTML = ''; $('sideButtons').innerHTML = '';
  if (!s.can_act) { $('selected').textContent = s.stage === 'over' ? '' : 'Not your move.'; addUndo(); return; }
  if (sel.side != null) {
    const acts = pieceActs(sel.side, sel.i);
    const p = (sel.side === 'O' ? s.o : s.x)[sel.i];
    $('selected').textContent = `${sel.side}${sel.i + 1} (${p.card.role}) on ${p.sq}` + (acts.length ? '' : ': no legal action for this player now');
    const kinds = [...new Set(acts.map(a => a.kind))];
    if (sel.side === 'O' && p.ball && (s.denied || []).length && !kinds.includes('pass')) kinds.unshift('pass');   // every lane denied: still show why
    for (const k of kinds) {
      const b = el('button', { class: (sel.kind === k ? 'active ' : '') + (ENDERS.includes(k) ? 'ender' : ''), text: KIND_NAME[k] + (ENDERS.includes(k) ? ' (ends turn)' : ''),
        onclick: () => { sel.kind = k; sel.dest = null; render(); } });
      $('kindButtons').append(b);
    }
    if (sel.kind) {
      const ka = acts.filter(a => a.kind === sel.kind), tb = $('targetButtons');
      if (['move', 'qs', 'sprint'].includes(sel.kind)) {
        if (sel.dest) {
          tb.append(el('span', { text: `Arrow at ${sqName(sel.dest[0], sel.dest[1])}: ` }));
          for (const a of ka.filter(a => a.dest[0] === sel.dest[0] && a.dest[1] === sel.dest[1])) tb.append(actionButton(a, `face ${DIRN[a.arrow]}`));
        } else tb.append(el('span', { class: 'note', text: `Click a highlighted square (${new Set(ka.map(a => a.dest.join())).size} legal). Movement doesn't end the turn.` }));
      } else if (sel.kind === 'pass') {
        for (const a of ka) {
          const by = {};
          for (const t of (a.threats || [])) (by[t.defender] = by[t.defender] || []).push(t);
          const th = Object.keys(by).sort().map(j => {
            const ts = by[j], parts = [];
            const thr = ts.filter(t => t.how === 'through'), jmp = ts.filter(t => t.how === 'jump'), fol = ts.filter(t => t.how === 'follow');
            if (thr.length) parts.push(`through X${j}'s own square (${thr[0].sq})`);
            if (jmp.length) parts.push('one straight movement along the arrow onto the line at ' + [...new Set(jmp.map(t => `${t.sq} (${t.by})`))].join(' or ') + ', then Intercept');
            if (fol.length) parts.push(`moves, then jumps (${new Set(fol.map(t => t.sq)).size} crossing square${new Set(fol.map(t => t.sq)).size === 1 ? '' : 's'})`);
            const old = ts.filter(t => t.how === 'direct' || t.how === 'approach');
            if (old.length) parts.push(old[0].how === 'direct' ? 'on the line' : 'arrow across (must move onto the line first)');
            return `X${Number(j) + 1} ${parts.join('; ')}`;
          });
          tb.append(el('div', { class: 'opt' }, [actionButton(a, `Pass to O${a.target + 1}`), el('span', { class: 'note', text: th.length ? ' Can intercept: ' + th.join('; ') : ' No defender can intercept this pass' }), chips(a)]));
        }
        for (const d of (s.denied || [])) {
          tb.append(el('div', { class: 'opt denied' }, [el('button', { disabled: 'disabled', text: `Pass to O${d.receiver + 1}: denied` }),
            el('span', { class: 'note', text: ` Blocked: X${d.defender + 1} on ${d.dsq} is next to O${d.receiver + 1} and the pass would go through that square. Move O${d.receiver + 1} off the line, cut backdoor, change the passer's angle, or screen X${d.defender + 1}.` })]));
        }
      } else if (sel.kind === 'shot') {
        for (const a of ka) tb.append(el('div', { class: 'opt' }, [actionButton(a, `Shoot: ${a.shot}`), chips(a)]));
      } else if (sel.kind === 'screen') {
        for (const a of ka) tb.append(el('div', { class: 'opt inline' }, [actionButton(a, `T ${DIRN[a.target]}`), chips(a)]));
      } else if (sel.kind === 'dribble') {
        for (const a of ka) tb.append(el('div', { class: 'opt' }, [actionButton(a, `Dribble v X${a.target + 1}`), chips(a)]));
      } else if (sel.kind === 'challenge') {
        for (const a of ka) tb.append(el('div', { class: 'opt' }, [actionButton(a, `Challenge O${a.target + 1}'s screen`), chips(a)]));
      } else for (const a of ka) tb.append(el('div', { class: 'opt' }, [actionButton(a, KIND_NAME[a.kind]), chips(a)]));
    }
  } else $('selected').textContent = 'Select one of your players (click or Tab + Enter).';
  if (s.stage === 'contest' || s.stage === 'forced') {
    $('selected').textContent = s.stage === 'contest' ? 'The defence chooses the contest:' : 'The offence chooses the forced shot:';
    for (const a of myActs()) {
      const b = el('button', { class: 'choice ' + (a.kind === 'contest' ? (a.piece < 0 ? 'none' : a.clean ? 'clean' : 'foul') : ''), text: a.option || (a.kind === 'forced_shot' ? `Forced shot: ${a.shot}` : a.text), onclick: () => submit(a) });
      $('targetButtons').append(el('div', { class: 'opt' }, [b, a.kind === 'forced_shot' ? chips(a) : null]));
    }
    return;
  }
  for (const a of myActs().filter(a => SIDE_KINDS.includes(a.kind) && a.kind !== 'target')) {
    const label = a.kind === 'pick' ? `Give the ball to O${a.target + 1}` : KIND_NAME[a.kind] + (a.kind === 'end_turn' && s.stage === 'reaction' ? ' (go to the contest)' : '');
    $('sideButtons').append(actionButton(a, label));
  }
  addUndo();
}

function addUndo() {
  const s = st;
  $('sideButtons').append(el('button', { class: 'small', 'aria-pressed': showReach() ? 'true' : 'false', text: showReach() ? 'Defender reach: shown' : 'Defender reach: hidden',
    onclick: () => { try { localStorage.setItem('pm_reach', showReach() ? '0' : '1'); } catch (e) { /* ignore */ } render(); } }));
  $('sideButtons').append(el('button', { class: 'small', 'aria-pressed': zonesShown() ? 'true' : 'false', text: zonesShown() ? 'Shot zones: labelled' : 'Shot zones: colours only',
    onclick: () => { try { localStorage.setItem('pm_zones', zonesShown() ? '0' : '1'); } catch (e) { /* ignore */ } render(); } }));
  if (s.stage === 'over') return;
  if (s.mode === 'hotseat' && s.can_undo) $('sideButtons').append(el('button', { text: 'Undo (only before a roll)', onclick: undo }));
  if (s.mode === 'remote' && s.can_undo) $('sideButtons').append(el('button', { text: s.undo_votes.length ? `Undo requested by ${s.undo_votes.join(', ')}: agree` : 'Request undo (both must agree)', onclick: undo }));
}

async function undo() {
  try { const r = await api('/api/undo', { code: G.code, token: G.token }); st = r.state; sel = { side: null }; render(); }
  catch (e) { $('error').textContent = e.message; }
}

async function submit(a) {
  if (busy) return;                      // a second tap while the first action is in flight is ignored, not sent stale
  $('error').textContent = '';
  if (a.roll && a.roll.length) {
    const ok = await confirmRoll(a);
    if (!ok) return;
  }
  busy = true;
  try {
    const r = await api('/api/act', { code: G.code, token: G.token, action: a });
    sel = { side: null, i: null, kind: null, dest: null };
    lastOther = [];
    if (r.rolls && r.rolls.length) await showRolls(r.rolls);
    st = r.state; render();
    announce(`${a.text}. ${st.summary}`);
    if ($('modal').classList.contains('hidden')) $('actionsPanel').focus();   // keyboard users continue from the actions
  } catch (e) { $('error').textContent = e.message; }
  busy = false;
}

function confirmRoll(a) {
  return new Promise(res => {
    modal([el('h2', { text: a.text }), PMCoach.line('ref', a.roll.length > 1 ? 'This one goes to the dice, twice.' : 'This one goes to the dice.', { compact: true, speak: false, live: false }),
      el('ul', {}, a.roll.map(t => el('li', {}, [rollerChip(t.roller), ' ' + t.text.replace(/^(Offence|Defence) rolls: /, '')]))),
      el('button', { class: 'primary', text: 'Roll', onclick: () => { closeModal(); res(true); } }),
      el('button', { text: 'Cancel', onclick: () => { closeModal(); res(false); } })], () => res(false));
  });
}

function showRolls(rolls) {
  return new Promise(res => {
    const call = rolls.map(r => `${r.what.replace(/ \(.*\)$/, '')}: rolled ${r.face}, ${r.picked}.`).join(' ');
    const box = [el('h2', { text: 'The call' }), PMCoach.line('ref', call, { compact: true, speak: false, live: false })];
    for (const r of rolls) {
      const ok = r.face <= r.need;
      box.push(el('div', { class: 'rollrow' }, [rollerChip(r.roller), el('span', { class: 'die roll' + (r.roller === 'X' ? ' black' : ''), text: r.face }),
        el('span', {}, [r.text.replace(/^(Offence|Defence) rolls: /, '') + ' ', el('strong', { text: `Rolled ${r.face}: ${r.picked}.` })])]));
    }
    box.push(el('button', { class: 'primary', text: 'Continue', onclick: () => { closeModal(); res(); } }));
    announce(rolls.map(r => `${r.text}. Rolled ${r.face}: ${r.picked}.`).join(' '));
    modal(box, () => res());
  });
}

function targetModal() {
  if (!$('modal').classList.contains('hidden')) return;
  const acts = myActs().filter(a => a.kind === 'target');
  modal([el('h2', { text: "Coach's Call: secret target" }),
    el('p', { text: st.mode === 'hotseat' ? 'Defence: look away now. Offence: pick the player you want to score. It stays secret until the shot.' : 'Pick the player you want to score. The defence does not see it until the shot.' }),
    ...acts.map(a => el('button', { class: 'primary', text: `O${a.target + 1} ${st.o[a.target].card.role}`, onclick: () => { closeModal(); submit(a); } }))]);
}

function endModal() {
  if (!$('modal').classList.contains('hidden')) return;
  const r = st.result, s = st;
  const rows = [['Shot value', r.shot_value], ['Free throws (or and-one)', r.free_throws], ['Foul bonus', r.bonus],
    ['Turnovers', `${r.turnovers} (${r.turnover_points})`], ["Coach's Call bonus", r.coach_bonus]];
  const verdict = r.band === 'Excellent' ? 'An Excellent look: that is the shot every goal is built for.' :
    r.band === 'Great' ? 'A Great look. One more step of the plan and it is Excellent.' :
    r.band === 'Good' ? 'A Good look. Ask where the better shot was: a mismatch you set up but did not use?' :
    r.band === 'Okay' ? 'An Okay look. The defence kept its shape; next time build the advantage before the clock builds the pressure.' :
    'A Poor result. Look at the story: where did the possession lose its goal?';
  const kids = [el('h2', { text: s.full ? `Possession ${s.possession} over` : 'Possession over' }),
    el('p', {}, [el('span', { class: 'band ' + r.band, text: `${r.total} · ${r.band}` }), ' ', el('span', { class: 'note', text: r.detail || '' })]),
    PMCoach.line('coach', verdict, { compact: true, speak: false, live: false }),
    el('table', { class: 'bk' }, rows.map(([k, v]) => el('tr', {}, [el('td', { text: k }), el('td', { text: String(v) })])))];
  if (s.scenario) kids.push(el('p', { text: `Goal (look 30+): ${r.goal_met ? 'met' : 'missed'} (look ${r.look})` + (r.late_clock ? ` · result: ${r.late_clock}` : '') }));
  if (s.target !== null && s.target !== undefined && s.target !== 'secret' && s.target >= 0) kids.push(el('p', { text: `The secret target was O${s.target + 1}.` }));
  if (s.match) {
    const m = s.match;
    kids.push(el('h3', { text: `Match: A ${m.A} · B ${m.B} → ${m.winner === 'tie' ? 'still tied' : 'player ' + m.winner + ' wins'}` }));
    if (m.tiebreak) kids.push(el('p', { text: `Tiebreak: A rolled ${m.tiebreak.A.roll} (needs ${m.tiebreak.A.need} or less), B rolled ${m.tiebreak.B.roll} (needs ${m.tiebreak.B.need} or less).` }));
  }
  const nav = el('div', { class: 'buttons' }, [
    s.full && s.possession < (s.n_poss || 2) ? el('button', { class: 'primary', id: 'nextPoss', text: `Start possession ${s.possession + 1} of ${s.n_poss || 2} (sides swap)`, onclick: async () => { closeModal(); const q = await api('/api/next', { code: G.code, token: G.token }); st = q.state; phasesInit = false; render(); } }) : null,
    el('button', { class: s.full && s.possession < (s.n_poss || 2) ? '' : 'primary', text: 'The story of the play', onclick: () => { closeModal(); showStory(); } }),
    el('button', { text: 'Close', onclick: closeModal }),
    el('button', { text: 'New game', onclick: () => { location.href = location.pathname; } })]);
  kids.push(nav);
  kids.splice(2, 0, el('div', { id: 'trainerBox' }, trainerBoxKids(s.possession)));
  if (s.match && G.rec) kids.splice(3, 0, el('div', { id: 'ratingBox' }, ratingKids()));
  if (s.feedback_due) {
    const rv = el('details', { class: 'endsec' }, [el('summary', { text: 'Review: your plan against the board' }), el('section', { id: 'reviewBox', class: 'review' }, [
      s.level === 'pro' ? el('button', { text: 'Show the full review', onclick: loadReview }) : el('p', { class: 'note', text: 'Loading the review…' })])]);
    rv.addEventListener('toggle', () => { if (rv.open && s.level !== 'pro' && !rv.dataset.loaded) { rv.dataset.loaded = '1'; loadReview(); } });
    kids.push(rv);
    if (!s.feedback_done) {
      const areas = s.feedback_questions.map((q, i) => el('label', {}, [el('div', { text: `${i + 1}. ${q}` }), el('textarea', { id: 'fb' + i })]));
      areas.push(el('label', {}, [el('div', { text: 'Was your setup and plan the right one for these two teams?' }), el('textarea', { id: 'fbReflect' })]));
      kids.push(el('details', { class: 'endsec' }, [el('summary', { text: 'Feedback for the designer (saved with the game log)' }), ...areas,
        el('button', { class: 'primary', text: 'Send feedback', onclick: async () => {
          const answers = {}; s.feedback_questions.forEach((q, i) => { answers[i] = $('fb' + i).value; });
          answers.reflect = $('fbReflect').value;
          await api('/api/feedback', { code: G.code, token: G.token, answers }); st.feedback_done = true; closeModal(); endModal(); } })]));
    }
    kids.push(el('details', { class: 'endsec' }, [el('summary', { text: 'Game log' }), el('p', { class: 'note', text: s.static ? 'The log lives in this browser tab. Download it, or copy it to paste into an email.' : `Saved on the server in playtest_logs/${s.log_name}.` }),
      el('button', { text: 'Download log', onclick: downloadLog }), el('button', { text: 'Copy log', onclick: copyLog })]));
  }
  announce(`Possession over: ${r.total}, ${r.band}.`);
  modal(kids, () => {});
}

function renderScenario() {
  const box = $('scenarioCard'), sc = st.scenario;
  if (!sc) { box.classList.add('hidden'); return; }
  box.classList.remove('hidden'); box.innerHTML = '';
  box.append(el('h3', { text: `${sc.n}. ${sc.title} · ${sc.kind} · clock ${sc.clock}` }), el('p', { text: sc.text }),
    el('p', { text: `Goal: ${sc.goal}` }), el('ul', {}, sc.rules.map(r => el('li', { text: r }))),
    el('p', { class: 'note', text: `O: ${sc.off} · X: ${sc.dfn}` + (st.target === 'secret' ? " · Coach's Call target: secret" : '') }));
}

function renderRolls() {
  const box = $('rolls'); box.innerHTML = '';
  for (const r of st.rolls || []) box.append(el('div', {}, [rollerChip(r.roller), el('span', { class: 'die' + (r.roller === 'X' ? ' black' : ''), text: r.face }), ` ${r.text.replace(/^(Offence|Defence) rolls: /, '')} → ${r.picked}`]));
  if (!(st.rolls || []).length) box.append(el('div', { class: 'note', text: 'No roll on the last action.' }));
}

async function renderLog() {
  try {
    const log = await api(`/api/log?code=${G.code}`);
    const ol = $('log'); ol.innerHTML = '';
    for (const r of log.slice(-60)) {
      if (r.type === 'action') ol.append(el('li', { text: `[${r.actor}] ${r.action.text}` }));
      else if (r.type === 'roll') ol.append(el('li', {}, [rollerChip(r.roller), ` ${r.text.replace(/^(Offence|Defence) rolls: /, '')}. `, el('strong', { text: `Rolled ${r.face}: ${r.picked}.` })]));
      else if (r.type === 'placement') ol.append(el('li', { text: `[${r.actor}] ${r.side === 'O' ? 'Offence' : 'Defence'} placed: ${r.squares.join(' ')}` }));
      else if (r.type === 'end') ol.append(el('li', { text: `Possession ${r.possession}: ${r.score.total} (${r.score.band})` }));
      else if (r.type === 'possession') ol.append(el('li', { text: 'Second possession: sides swap' }));
    }
    ol.scrollTop = ol.scrollHeight;
  } catch (e) { /* log is optional */ }
}

let modalReturn = null, modalCancel = null;
let modalPaused = false;
function modal(kids, cancel, opts) {
  opts = opts || {};
  if (!opts.noTimer && !modalPaused && st && st.timer && st.can_act && ['main', 'grace'].includes(st.timer.mode)) { modalPaused = true; timerEvent('pause'); }
  $('modal').classList.toggle('readyscreen', !!opts.ready);
  const b = $('modalBox'); b.innerHTML = ''; b.append(...kids.filter(k => k != null));
  const h = b.querySelector('h1, h2, h3');
  if (h) { h.id = 'modalTitle'; h.setAttribute('tabindex', '-1'); $('modal').setAttribute('aria-labelledby', 'modalTitle'); }
  modalReturn = document.activeElement; modalCancel = cancel || null;
  $('modal').classList.remove('hidden'); document.body.classList.add('modal-open');
  for (const id of ['table', 'start']) $(id).setAttribute('aria-hidden', 'true');
  b.scrollTop = 0;
  const f = b.querySelector('button, textarea, input');
  if (opts.focus) opts.focus.focus(); else if (h && b.scrollHeight > b.clientHeight) h.focus({ preventScroll: true }); else if (f) f.focus({ preventScroll: true });
}
function closeModal() {
  if (modalPaused) { modalPaused = false; timerEvent('resume'); }
  $('modal').classList.remove('readyscreen');
  $('modal').classList.add('hidden'); document.body.classList.remove('modal-open');
  $('modalBox').innerHTML = '';
  for (const id of ['table', 'start']) $(id).removeAttribute('aria-hidden');
  if (modalReturn && document.contains(modalReturn)) modalReturn.focus();
  modalCancel = null;
}
document.addEventListener('keydown', e => {
  const open = !$('modal').classList.contains('hidden');
  if (open && e.key === 'Tab') {                 // keep focus inside the dialog
    const f = [...$('modalBox').querySelectorAll('button, textarea, input, select, a[href]')].filter(x => !x.disabled);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    else if (!$('modalBox').contains(document.activeElement)) { e.preventDefault(); first.focus(); }
    return;
  }
  if (e.key === 'Escape') {
    if (open) { if (modalCancel) { const c = modalCancel; closeModal(); c(); } return; }
    sel = { side: null }; if (st) render();
  }
});
// ---------------------------------------------------------------- decision timer (step 3d part C)
let tmRecv = { at: 0, v: null }, tmWarned = null, tmFull = null;
function timerEvent(event) {
  api('/api/timer', { code: G.code, token: G.token, event }).then(r => {
    if (event === 'ready') { st = r.state; render(); }
    else if (r.state && r.state.timer) { st.timer = r.state.timer; timerRecv(true); }
  }).catch(() => {});
}
function timerRecv(force) {
  if (!st || !st.timer) return;
  const key = JSON.stringify([st.version, st.timer.mode, st.timer.left, st.timer.grace_left, st.timer.paused]);
  if (force || key !== tmRecv.v) tmRecv = { at: performance.now(), v: key };
}
function timerNow() {
  const t = st.timer, dt = (performance.now() - tmRecv.at) / 1000;
  const run = !t.paused;
  const left = t.mode === 'main' && run ? Math.max(0, t.left - dt) : t.left;
  const grace = t.mode === 'grace' ? (run ? Math.max(0, t.grace_left - dt) : t.grace_left) : null;
  return { left, grace };
}
function ring(frac, r, cls, label) {
  const c = 2 * Math.PI * r, g = svg('svg', { viewBox: '0 0 44 44', class: 'ring ' + cls, 'aria-hidden': 'true' });
  g.append(svg('circle', { cx: 22, cy: 22, r, class: 'track' }), svg('circle', { cx: 22, cy: 22, r, class: 'bar',
    'stroke-dasharray': `${(c * Math.max(0, Math.min(1, frac))).toFixed(1)} ${c.toFixed(1)}`, transform: 'rotate(-90 22 22)' }));
  const tx = svg('text', { x: 22, y: 26, 'text-anchor': 'middle' }); tx.textContent = label; g.append(tx);
  return g;
}
function timerEl() {
  const t = st.timer, box = el('div', { class: 'timer', 'data-timer': '1' });
  timerPaint(box);
  return box;
}
function timerPaint(box) {
  const t = st.timer; if (!t) return;
  const { left, grace } = timerNow();
  const warn = t.mode === 'main' && left <= t.warn_at;
  box.innerHTML = '';
  box.classList.toggle('warn', warn);
  const who = t.side === 'O' ? 'Offence' : 'Defence';
  const words = t.mode === 'ready' ? `${who}: timer starts when you tap Ready` :
    t.paused ? `${who}: timer paused` :
    t.mode === 'grace' ? `${who}: finish the action (${Math.ceil(grace)} s grace; main timer paused at ${Math.ceil(left)} s)` :
    `${who}: ${Math.ceil(left)} s to act` + (t.token_free ? ' (no token lost: the default applies)' : '') + (warn ? ' · 10 seconds or less' : '');
  box.append(ring(left / t.period, 18, warn ? 'main warn' : 'main', String(Math.ceil(left))));
  if (t.mode === 'grace') box.append(ring(grace / t.grace, 12, 'grace', String(Math.ceil(grace))));
  box.append(el('span', { class: 'twords', text: words }));
}
setInterval(() => {
  if (!st || !st.timer || !st.timer.side) return;
  for (const b of document.querySelectorAll('[data-timer]')) timerPaint(b);
  const t = st.timer, { left, grace } = timerNow(), key = `${st.version}:${t.side}:${t.note}`;
  if (t.mode === 'main' && !t.paused && st.can_act) {
    if (tmFull !== key) { tmFull = key; announce(`${t.side === 'O' ? 'Offence' : 'Defence'}: ${t.period} seconds to act.`); }
    if (left <= t.warn_at && tmWarned !== key) {
      tmWarned = key; announce(`${Math.ceil(left)} seconds left.`);
      try { if (navigator.vibrate) navigator.vibrate(200); } catch (e) { /* not supported */ }
      try { if (localStorage.getItem('pm_sound') === '1') beep(); } catch (e) { /* ignore */ }
    }
    if (left <= 0) timerRefresh();
  }
  if (t.mode === 'grace' && grace <= 0) timerRefresh();
}, 250);
let tmRefreshAt = 0;
function timerRefresh() {
  const now = performance.now();
  if (busy || now - tmRefreshAt < 1000) return;
  tmRefreshAt = now; refresh(true);
}
function beep() {
  const A = window.AudioContext || window.webkitAudioContext; if (!A) return;
  const ctx = new A(), o = ctx.createOscillator(), g = ctx.createGain();
  o.frequency.value = 660; g.gain.value = 0.08; o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.15);
}
function readyIfDue() {
  const t = st.timer;
  if (!t || t.mode !== 'ready' || !st.can_act || st.mode !== 'hotseat' || !$('modal').classList.contains('hidden')) return false;
  const who = t.side === 'O' ? 'Offence' : 'Defence';
  modal([el('h2', { text: `${who} to act` }), el('p', { text: `Hand over to the ${who.toLowerCase()}. The board is hidden; your ${t.period}-second timer starts when you tap Ready.` }),
    el('button', { class: 'primary', text: 'Ready', onclick: () => { closeModal(); timerEvent('ready'); } })], null, { noTimer: true, ready: true });
  return true;
}

function announce(text) { const a = $('announce'); if (!a) return; a.textContent = ''; setTimeout(() => { a.textContent = text; }, 50); }

initStart();


// ---------------------------------------------------------------- logs, roller chips, placement, phone lists
async function logText() { const log = await api(`/api/log?code=${G.code}`); return log.map(r => JSON.stringify(r)).join('\n') + '\n'; }
async function downloadLog() {
  const blob = new Blob([await logText()], { type: 'application/x-ndjson' });
  const a = el('a', { href: URL.createObjectURL(blob), download: st.log_name }); document.body.append(a); a.click(); a.remove();
}
async function copyLog() {
  const t = await logText();
  try { await navigator.clipboard.writeText(t); alert('Log copied: paste it into an email.'); }
  catch (e) { modal([el('p', { text: 'Copy this text:' }), el('textarea', { rows: 10, text: t }), el('button', { text: 'Close', onclick: closeModal })]); }
}
function rollerChip(r) {
  if (!r) return '';
  return el('span', { class: 'roller ' + (r === 'O' ? 'off' : 'def'), text: r === 'O' ? 'Offence rolls' : 'Defence rolls' });
}

let place = null;      // {side, squares: [sq or null] x5, ball, arrows: [d] x5, pick, orig}
const sqXY = q => [COLS.indexOf(q[0]), Number(q.slice(1))];
function placeInit(P) {
  if (P.side === 'O') {
    const squares = st.o.map(p => p.sq);
    place = { side: 'O', squares, ball: st.o.findIndex(p => p.ball), arrows: [], pick: null, orig: squares.slice() };
  } else {
    const occ = new Set(P.offence || []);
    if (P.draft) {                                   // man-to-man against the offence on the floor
      place = { side: 'X', squares: P.draft.squares.slice(), ball: null, arrows: P.draft.arrows.slice(), pick: null, orig: P.draft.squares.slice() };
      return;
    }
    const squares = st.x.map(p => (occ.has(p.sq) ? null : p.sq));
    place = { side: 'X', squares, ball: null, arrows: st.x.map((p, i) => (squares[i] ? p.arrow : null)), pick: null, orig: st.x.map(p => p.sq) };
  }
}
function placeOpen(P) {
  // the squares a piece may move to: empty of the placing side's other pieces (and, for the defence, of the offence)
  const mine = new Set(place.squares.filter((q, i) => q && i !== place.pick));
  return P.squares.filter(q => !mine.has(q));
}
function placeMove(i, q) {
  place.squares[i] = q;
  if (place.side === 'X') place.arrows[i] = defaultArrow(q);
  place.pick = null;
  renderPlacement(); renderCourt();
  announce(`${place.side}${i + 1} moved to ${q}.`);
}
function placePick(i) {
  place.pick = place.pick === i ? null : i;
  renderPlacement(); renderCourt();
}
function placeProblem(P) {
  const who = place.side;
  const missing = place.squares.map((q, i) => (q ? null : `${who}${i + 1}`)).filter(Boolean);
  if (missing.length) return `Place ${missing.join(', ')}: ${missing.length === 1 ? 'its square is' : 'their squares are'} taken by the offence.`;
  if (new Set(place.squares).size !== 5) return 'Two pieces share a square.';
  if (who === 'O' && (place.ball == null || !P.ball_squares.includes(place.squares[place.ball])))
    return 'Choose who has the ball: a player on plain wood beyond the three-point tiles.';
  if (who === 'X' && place.arrows.some(a => a == null)) return 'Set every arrow.';
  return null;
}
function renderPlacement() {
  const s = st, P = s.placing;
  $('selected').textContent = ''; $('kindButtons').innerHTML = ''; $('targetButtons').innerHTML = ''; $('sideButtons').innerHTML = '';
  const who = P.side === 'O' ? 'Offence' : 'Defence';
  if (!P.mine) { place = null; $('selected').textContent = P.by_ai ? `The computer is placing the ${who.toLowerCase()}.` : `Waiting: the ${who.toLowerCase()} is placing.`; return; }
  if (!place || place.side !== P.side) placeInit(P);
  const k = place.pick;
  $('selected').textContent = k == null
    ? `${who} setup: tap one of your players, then tap its new square. ${P.side === 'O' ? 'Then choose who has the ball.' : 'Then set the arrows.'}`
    : `Moving ${P.side}${k + 1}${place.squares[k] ? ` (now on ${place.squares[k]})` : ''}: tap a highlighted square, or tap ${P.side}${k + 1} again to leave it.`;
  const tb = $('targetButtons');
  // every piece as a button (phones, keyboards), and the open squares as a list when one is picked
  tb.append(el('div', { class: 'buttons' }, place.squares.map((q, i) => el('button', { class: k === i ? 'active' : '', 'aria-pressed': k === i ? 'true' : 'false',
    text: `${P.side}${i + 1} ${q ? 'on ' + q : '(needs a square)'}`, onclick: () => placePick(i) }))));
  if (k != null) {
    const pick = el('select', { id: 'placeSq', 'aria-label': `New square for ${P.side}${k + 1}` }, [el('option', { value: '', text: 'Choose a square…' }),
      ...placeOpen(P).map(q => el('option', { value: q, text: q + (P.side === 'O' && P.ball_squares.includes(q) ? ' (ball allowed)' : '') }))]);
    pick.onchange = () => { if (pick.value) placeMove(k, pick.value); };
    tb.append(el('label', {}, [`Move ${P.side}${k + 1} to `, pick]));
  }
  if (P.side === 'O') {
    tb.append(el('div', { class: 'buttons' }, [el('span', { text: 'Ball: ' }), ...place.squares.map((q, i) => (q && P.ball_squares.includes(q)) ?
      el('button', { class: place.ball === i ? 'active' : '', text: `O${i + 1} (${q})`, onclick: () => { place.ball = i; renderPlacement(); renderCourt(); } }) : null)]));
  } else {
    const arrows = el('div', { class: 'arrowpicks' });
    place.squares.forEach((q, i) => {
      if (!q) return;
      const sel = el('select', { 'aria-label': `X${i + 1} on ${q}: arrow direction` }, DIRN.map((n, d) => el('option', { value: d, text: n })));
      sel.value = String(place.arrows[i]);
      sel.onchange = () => { place.arrows[i] = Number(sel.value); renderPlacement(); renderCourt(); };
      arrows.append(el('label', {}, [`X${i + 1} faces `, sel]));
    });
    tb.append(arrows);
  }
  const problem = placeProblem(P);
  const confirm = el('button', { class: 'primary', text: `Confirm the ${who.toLowerCase()} setup`, onclick: confirmPlacement });
  if (problem) confirm.setAttribute('disabled', 'disabled');
  const fast = async body => { try { const r = await api('/api/place', Object.assign({ code: G.code, token: G.token }, body)); place = null; st = r.state; render(); } catch (e) { $('error').textContent = e.message; } };
  $('sideButtons').append(confirm,
    el('button', { text: 'Accept the proposed setup', onclick: () => fast({ propose: true }) }),
    el('button', { text: 'Repeat my last setup', onclick: () => fast({ repeat: true }) }),
    el('button', { text: 'Start again', onclick: () => { place = null; renderPlacement(); renderCourt(); } }),
    el('button', { text: Object.keys(s.ai || {}).length ? 'Use the standard setup for my side' : 'Use the preview table setup (both sides)', onclick: async () => { try { const r = await api('/api/place', { code: G.code, token: G.token, preview: true }); place = null; st = r.state; render(); } catch (e) { $('error').textContent = e.message; } } }),
    ...(problem ? [el('p', { class: 'note', role: 'status', text: problem })] : []));
}
async function confirmPlacement() {
  if (!place || placeProblem(st.placing)) return;
  try {
    const body = { code: G.code, token: G.token, squares: place.squares };
    if (place.side === 'O') body.ball = place.ball; else body.arrows = place.arrows;
    const r = await api('/api/place', body); place = null; st = r.state; render();
    announce(`${r.state.placing ? 'Offence placed. The defence places next.' : 'Setup confirmed.'}`);
  } catch (e) { $('error').textContent = e.message; }
}
function placementPieces(c) {
  const P = st.placing;
  if (!place || place.side !== P.side) placeInit(P);
  // where each moved piece started: a faint dashed ring, not a second piece
  place.orig.forEach((q, i) => {
    if (!q || q === place.squares[i]) return;
    const [x, y] = sqXY(q);
    const g = svg('g', { class: 'ghost', 'aria-hidden': 'true' });
    g.append(svg('circle', { cx: px(x) + S / 2, cy: py(y) + S / 2, r: 14 }));
    const t = svg('text', { x: px(x) + S / 2, y: py(y) + S / 2 + 5, 'text-anchor': 'middle' }); t.textContent = i + 1; g.append(t);
    c.append(g);
  });
  if (P.side === 'X') {          // the offence as placed, fixed while the defence sets up
    (P.offence || []).forEach((q, i) => { const [x, y] = sqXY(q); { const op = { ...st.o[i], sq: q, x, y, ball: i === P.ball, screen: null, locked: false }; drawO(c, op, { piece: op, inert: true }); } });
  }
  place.squares.forEach((q, i) => {
    if (!q) return;
    const [x, y] = sqXY(q);
    const base = (place.side === 'O' ? st.o : st.x)[i];
    const p = { ...base, sq: q, x, y, screen: null, locked: false, ball: place.side === 'O' && i === place.ball, arrow: place.side === 'X' ? place.arrows[i] : base.arrow };
    const label = `${place.side}${i + 1}, ${base.card.role}, on ${q}${p.ball ? ', has the ball' : ''}. ${place.pick === i ? 'Selected: choose its new square.' : 'Select to move.'}`;
    (place.side === 'O' ? drawO : drawX)(c, p, { piece: p, selected: place.pick === i, label, onClick: () => placePick(i) });
  });
}
function placementTargets(c) {
  const P = st.placing; if (!P || !P.mine || !place || place.pick == null) return;
  for (const q of placeOpen(P)) {
    if (q === place.squares[place.pick]) continue;
    const [x, y] = sqXY(q);
    const r = svg('rect', { class: 'target' + (P.side === 'O' && P.ball_squares.includes(q) ? ' ballsq' : ''), x: px(x) + 3, y: py(y) + 3, width: S - 6, height: S - 6, rx: 5, tabindex: 0, role: 'button', 'aria-label': `move ${P.side}${place.pick + 1} to ${q}` });
    const fn = () => placeMove(place.pick, q);
    r.addEventListener('click', fn); r.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); fn(); } });
    c.insertBefore(r, c.querySelector('g.piece') || null);
  }
}
function defaultArrow(q) {
  const o = st.placing.offence || []; const x = COLS.indexOf(q[0]), y = Number(q.slice(1));
  let best = null, bd = 1e9;
  for (const s of o) { const ox = COLS.indexOf(s[0]), oy = Number(s.slice(1)); const d = Math.max(Math.abs(ox - x), Math.abs(oy - y)); if (d < bd) { bd = d; best = [ox - x, oy - y]; } }
  if (!best) return 0;
  const ang = (Math.atan2(best[0], best[1]) * 180 / Math.PI + 360) % 360;
  return Math.round(ang / 45) % 8;
}

// Phone: every court choice is also a full-size button (court squares are too small to tap reliably).
function renderPhoneLists() {
  const box = $('phoneLists'); if (!box) return; box.innerHTML = '';
  if (!isPhone() || !st.can_act || st.placing) return;
  const mine = myActs();
  const side = st.side === 'O' || st.stage === 'target' || st.stage === 'pick' || st.stage === 'forced' ? 'O' : 'X';
  const pieces = (side === 'O' ? st.o : st.x).filter(p => mine.some(a => a.side === side && a.piece === p.i));
  if (sel.side == null) {
    box.append(el('div', { class: 'note', text: 'Pick a player:' }), ...pieces.map(p => el('button', { text: `${side}${p.i + 1} on ${p.sq}`, onclick: () => selectPiece(side, p.i) })));
  } else if (sel.kind && ['move', 'qs', 'sprint'].includes(sel.kind) && !sel.dest) {
    const acts = pieceActs(sel.side, sel.i).filter(a => a.kind === sel.kind);
    const seen = new Set();
    box.append(el('div', { class: 'note', text: 'Or pick the square here:' }));
    for (const a of acts) { const k = a.dest.join(); if (seen.has(k)) continue; seen.add(k); box.append(el('button', { text: sqName(a.dest[0], a.dest[1]), onclick: () => chooseDest(a.dest) })); }
  }
  box.append(el('button', { text: 'Clear selection', onclick: () => { sel = { side: null }; render(); } }));
}

// Phone tabs
function initTabs() {
  document.querySelectorAll('.tabs button').forEach(b => b.addEventListener('click', () => {
    document.querySelectorAll('.tabs button').forEach(x => x.classList.toggle('active', x === b));
    document.body.dataset.tab = b.dataset.tab;
  }));
  document.body.dataset.tab = 'off';
}
initTabs();


// ---------------------------------------------------------------- the other side's turn, made visible
function otherSide(e) {
  if (e.actor === 'system') return false;
  if (e.actor === 'ai') return true;
  return st.mode === 'remote' && st.seat && st.seat !== 'both' && e.side !== st.seat;
}
function sideName(side) { return side === 'O' ? 'Offence' : side === 'X' ? 'Defence' : ''; }
function feedEntry(e) {
  const kids = [el('div', { class: 'fe-head' }, [el('span', { class: 'roller ' + (e.side === 'O' ? 'off' : 'def'), text: sideName(e.side) + (e.actor === 'ai' ? ' (computer)' : '') }), ' ' + e.text])];
  for (const r of e.rolls) {
    const ok = r.face <= r.need;
    kids.push(el('div', { class: 'fe-roll' }, [rollerChip(r.roller), el('span', { class: 'die small' + (r.roller === 'X' ? ' black' : ''), text: r.face }),
      el('span', {}, [`${r.what}: ${r.first} on ${r.need} or less. `, el('strong', { text: `Rolled ${r.face}: ${r.picked}.` })])]));
  }
  for (const o of e.outcomes) kids.push(el('div', { class: 'fe-out ' + o.tone, text: o.text }));
  return el('div', { class: 'fe' + (e.rolls.length || e.outcomes.some(o => o.tone !== 'info') ? ' big' : '') }, kids);
}
function newOtherEntries() {
  const feed = st.feed || [];
  if (seenFeed === null) {           // just opened: show the other side's moves since your last one
    const mine = feed.filter(e => !otherSide(e));
    seenFeed = mine.length ? mine[mine.length - 1].n : 0;
  }
  const fresh = feed.filter(e => e.n > seenFeed);
  seenFeed = st.feed_n;
  return fresh.filter(otherSide);
}
let lastOther = [];
// The other side's turn, one action at a time: the board as it stood after each action, a ghost where
// the piece came from, what it did and what happened. OK shows the next action, then your turn.
let replay = null;            // {entries, k, live, start}
let replayPaused = false;
function frameState(live, e) {
  const b = e.board;
  return Object.assign({}, live, {
    o: live.o.map((p, i) => Object.assign({}, p, b.o[i])), x: live.x.map((p, i) => Object.assign({}, p, b.x[i])),
    arrow_lines: b.arrow_lines, influence: b.influence || live.influence, clock: b.clock, phase: b.phase, tokens: b.tokens, pending: b.pending, inbound: b.inbound,
    shot: b.shot, bonus: b.bonus, turnovers: b.turnovers, summary: b.summary, legal: [], can_act: false, turn: e.turn,
    side_to_act: null, stage: b.stage === 'over' ? 'replay' : b.stage, result: null });
}
function showFeedIfNew() {
  const fresh = newOtherEntries().filter(e => e.board);
  if (!fresh.length) return false;
  lastOther = fresh;
  const before = (st.feed || []).find(e => e.n === fresh[0].n - 1);      // the board just before the turn
  replay = { entries: fresh, k: 0, live: st, start: before && before.board && before.possession === fresh[0].possession ? before.board : (fresh[0].before || null) };
  if (st.timer && st.can_act && ['main', 'grace'].includes(st.timer.mode)) { replayPaused = true; timerEvent('pause'); }
  sel = { side: null, i: null, kind: null, dest: null };
  st = frameState(replay.live, fresh[0]);
  render();
  return true;
}
function replayPrev() {
  return replay.k > 0 ? replay.entries[replay.k - 1].board : replay.start;
}
function stepOn() {
  replay.k += 1;
  if (replay.k < replay.entries.length) { st = frameState(replay.live, replay.entries[replay.k]); render(); return; }
  const live = replay.live;
  replay = null; st = live;
  $('stepBar').classList.add('hidden'); $('stepBar').innerHTML = '';
  if (replayPaused) { replayPaused = false; timerEvent('resume'); }
  render();
  if ($('modal').classList.contains('hidden')) $('actionsPanel').focus();
}
function renderStep() {
  const e = replay.entries[replay.k], n = replay.entries.length, last = replay.k === n - 1;
  const bar = $('stepBar'); bar.innerHTML = ''; bar.classList.remove('hidden');
  const yours = last && replay.live.can_act && replay.live.stage !== 'over';
  const label = !last ? 'OK: next action' : yours ? 'OK: your turn' : replay.live.stage === 'over' ? 'OK: see the result' : 'OK';
  const calls = e.outcomes.filter(o => o.tone !== 'info').map(o => o.text);
  const call = e.rolls.length ? e.rolls.map(r => `${r.what.replace(/ \(.*\)$/, '')}: rolled ${r.face}, ${r.picked}.`).join(' ') + (calls.length ? ' ' + calls.join(' ') : '') : calls.join(' ');
  bar.append(...[el('div', { class: 'step-count', text: `${sideName(e.side)}${e.actor === 'ai' ? ' (computer)' : ''} · action ${replay.k + 1} of ${n}` }),
    feedEntry(e), call ? PMCoach.line('ref', call, { compact: true, speak: false, live: false }) : null,
    el('button', { class: 'primary', id: 'stepOk', text: label, onclick: stepOn })].filter(Boolean));   // no call, no referee line (and never a "null")
  announce(`${sideName(e.side)}: ${e.text}. ` + e.rolls.map(r => `Rolled ${r.face}: ${r.picked}.`).join(' ') + ' ' + e.outcomes.map(o => o.text).join(' '));
  $('stepOk').focus();
}
// where the acting piece came from: a dashed ring and a dashed line to where it is now
function drawGhost(c) {
  if (!replay) return;
  const e = replay.entries[replay.k], prev = replayPrev(), m = e.text.match(/^([OX])(\d)/);
  if (!prev || !m) return;
  const side = m[1], i = Number(m[2]) - 1;
  const was = (side === 'O' ? prev.o : prev.x)[i], now = (side === 'O' ? st.o : st.x)[i];
  if (!was || !now) return;
  const ax = px(was.x) + S / 2, ay = py(was.y) + S / 2, bx = px(now.x) + S / 2, by = py(now.y) + S / 2;
  if (was.sq !== now.sq) {
    c.append(svg('line', { class: 'ghost', x1: ax, y1: ay, x2: bx, y2: by }));
    c.append(svg('circle', { class: 'ghost', cx: ax, cy: ay, r: 14 }));
  } else if (side === 'X' && was.arrow !== now.arrow) {       // turned on the spot: the old arrow, faint
    const d = DIRS[was.arrow];
    c.append(svg('line', { class: 'ghost', x1: ax, y1: ay, x2: ax + d[0] * S * 0.8, y2: ay - d[1] * S * 0.8 }));
  }
}
function renderRecent() {
  const box = $('recent'); if (!box) return;
  box.innerHTML = '';
  const shown = replay ? replay.entries.slice(0, replay.k) : lastOther;     // never the actions still to come
  if (!shown.length) { box.classList.add('hidden'); return; }
  box.classList.remove('hidden');
  box.append(el('h3', { text: `${replay ? 'So far' : 'Last turn'}: ${sideName(shown[0].side)}${shown[0].actor === 'ai' ? ' (computer)' : ''}` }), ...shown.map(feedEntry));
}
function actedPieces() {
  const out = new Set();
  for (const e of (replay ? [replay.entries[replay.k]] : lastOther)) { const m = e.text.match(/^([OX])(\d)/); if (m) out.add(m[1] + (Number(m[2]) - 1)); }
  return out;
}


// ---------------------------------------------------------------- scouting: arrange, never judge
function chips(a) {
  if (!a.chips || !a.chips.length) return null;
  return el('div', { class: 'chips' }, a.chips.map(c => el('span', { class: 'vchip', text: c })));
}

function renderCompare() {
  const box = $('compare'); if (!box) return;
  box.innerHTML = '';
  if (!compare || !st) { box.classList.add('hidden'); return; }
  const side = compare.side, i = compare.i;
  const mine = (side === 'O' ? st.o : st.x)[i];
  const oppSide = side === 'O' ? 'X' : 'O';
  const opps = (st.matchups[side] || [])[i] || [];
  const k = Math.min(compare.k, Math.max(0, opps.length - 1));
  const opp = opps.length ? (oppSide === 'O' ? st.o : st.x)[opps[k]] : null;
  const how = opp ? (side === 'O' ? (st.x[opps[k]].arrow !== undefined && opps.length && isArrowOn(st.x[opps[k]], mine) ? 'arrow on this player' : 'nearest defender')
                                  : (isArrowOn(mine, opp) ? 'arrow on this player' : 'nearest attacker')) : '';
  box.classList.remove('hidden');
  box.append(el('div', { class: 'cmp-head' }, [el('h3', { text: `${side}${i + 1} on ${mine.sq}` + (opp ? `  ·  matchup: ${oppSide}${opps[k] + 1} on ${opp.sq} (${how})` : '') }),
    opps.length > 1 ? el('button', { text: `Next matchup (${k + 1} of ${opps.length})`, onclick: () => { compare.k = (k + 1) % opps.length; renderCompare(); } }) : null,
    el('button', { text: 'Close card', onclick: () => { compare = null; renderCompare(); } })]),
    el('div', { class: 'cmp-cards' }, [cardEl(mine.card, side, `${side}${i + 1}`), opp ? cardEl(opp.card, oppSide, `${oppSide}${opps[k] + 1}`) : null]));
}
function isArrowOn(x, o) { const d = [o.x - x.x, o.y - x.y]; return Math.max(Math.abs(d[0]), Math.abs(d[1])) === 1 && DIRS[x.arrow][0] === d[0] && DIRS[x.arrow][1] === d[1]; }

// ---------------------------------------------------------------- scout report (step 3d)
// Words only: no ratings, no numbers, no marks. Team lines first, then players by side.
function chartEl(chart, label) {
  const W = 17, H = 14, c = 4;
  const zs = (st && st.zones) || [];
  const g = svg('svg', { viewBox: `0 0 ${W * c} ${H * c}`, class: 'chart', role: 'img', 'aria-label': `${label}. ${chart.alt}` });
  const defs = svg('defs');
  const pat = svg('pattern', { id: 'hatch', width: 3, height: 3, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' });
  pat.append(svg('rect', { width: 3, height: 3, fill: '#f6f1e7' }), svg('line', { x1: 0, y1: 0, x2: 0, y2: 3, stroke: '#1d1b18', 'stroke-width': 1.4 }));
  defs.append(pat); g.append(defs);
  for (let y = 1; y <= H; y++) for (let x = 0; x < W; x++) {
    const z = zs[y - 1] ? zs[y - 1][x] : '.';
    const m = chart.marks[z];
    const at = { x: x * c, y: (H - y) * c, width: c, height: c };
    if (m === 'L') g.append(svg('rect', { ...at, fill: 'url(#hatch)' }));
    else g.append(svg('rect', { ...at, fill: z === '.' ? '#f6f1e7' : ZCOL[z], 'fill-opacity': m === 'H' ? 1 : 0.22 }));
  }
  g.append(svg('rect', { x: 0.25, y: 0.25, width: W * c - 0.5, height: H * c - 0.5, fill: 'none', stroke: '#6b6357', 'stroke-width': 0.5 }));
  const btn = el('button', { class: 'chartbtn', 'aria-label': `${label}: ${chart.alt} Tap to enlarge.`, title: chart.alt,
    onclick: e => { e.currentTarget.classList.toggle('big'); } });
  btn.append(g);
  return btn;
}

function phraseLines(ph) {
  const out = [];
  if (ph.strengths.length) out.push(el('div', { class: 'plus' }, [el('span', { class: 'sign', 'aria-label': 'strengths', text: '+' }), ' ' + ph.strengths.map(x => x.text).join(', ')]));
  if (ph.weaknesses.length) out.push(el('div', { class: 'minus' }, [el('span', { class: 'sign', 'aria-label': 'weaknesses', text: '−' }), ' ' + ph.weaknesses.map(x => x.text).join(', ')]));
  return out;
}

function teamLinesEl(t) {
  const none = !t.strengths.length && !t.weaknesses.length;
  return el('div', { class: 'teamread' }, [el('h3', { text: t.name.toUpperCase() }),
    none ? el('p', { text: t.nothing }) : null,
    t.strengths.length ? el('p', {}, [el('b', { text: 'Strengths: ' }), t.strengths.join(' · ')]) : null,
    t.weaknesses.length ? el('p', {}, [el('b', { text: 'Weaknesses: ' }), t.weaknesses.join(' · ')]) : null]);
}

function sideListEl(t, side) {
  // all five, in order: a player with nothing to say on this side still gets a row, so the report never looks short
  const rows = t.players.map(p =>
    el('div', { class: 'prow' }, [chartEl(p.chart[side], `${side === 'off' ? 'Shooting' : 'Contests'} chart for ${p.num} ${p.short}`),
      el('div', { class: 'ptext' }, [el('div', { class: 'pname', text: `${p.num} ${p.short}` }),
        ...(p[side].strengths.length || p[side].weaknesses.length ? phraseLines(p[side])
          : [el('div', { class: 'note', text: side === 'off' ? 'Average everywhere on offence: no edge to hunt, none to hide.' : 'Average everywhere on defence: nothing to attack, nothing to lean on.' })])])]));
  const d = el('details', { class: 'sidelist' }, [el('summary', { text: `${t.name}: on ${side === 'off' ? 'offence' : 'defence'}` }),
    ...(rows.length ? rows : [el('p', { class: 'note', text: 'Nobody stands out on this side.' })])]);
  return d;
}

function reportEl(rep) {
  if (!rep || rep.level === 'pro') return [];
  const out = [el('div', { class: 'reads' }, rep.teams.map(teamLinesEl)),
    el('p', { class: 'note', text: 'Charts: solid = strong zone, hatched = weak zone, pale = neither. Tap a chart to enlarge it.' })];
  for (const t of rep.teams) out.push(sideListEl(t, 'off'), sideListEl(t, 'def'));
  if (rep.mismatches) {
    out.push(el('h3', { text: 'Mismatches (by numbered pairing)' }));
    for (const m of rep.mismatches) {
      out.push(el('h4', { text: `When ${m.attacking} has the ball` }),
        el('p', { class: 'note', text: `${m.attacking} on offence:` }),
        el('ul', {}, (m.offence.length ? m.offence : ['None on the cards.']).map(x => el('li', { text: x }))),
        el('p', { class: 'note', text: `${m.defending} on defence:` }),
        el('ul', {}, (m.defence.length ? m.defence : ['None on the cards.']).map(x => el('li', { text: x }))));
    }
  }
  return out;
}

function seenKey(what) { return `pm_${what}_${G.code}`; }
function seen(what) { try { return localStorage.getItem(seenKey(what)) === '1'; } catch (e) { return false; } }
function markSeen(what) { try { localStorage.setItem(seenKey(what), '1'); } catch (e) { /* private mode */ } }

function showReport(title, intro, done) {
  modal([el('h2', { text: title }), intro ? el('p', { class: 'note', text: intro }) : null, ...reportEl(st.scout.report),
    el('button', { class: 'primary', text: done || 'Close', onclick: () => { closeModal(); render(); } })], () => { closeModal(); render(); });
}

function scoutModalIfDue() {
  const sc = st.scout;
  if (!sc || !$('modal').classList.contains('hidden')) return false;
  const pending = sc.pending.filter(side => st.mode === 'hotseat' || st.seat === side);
  if (pending.length) { pickModal(pending[0]); return true; }
  if (sc.pending.length && st.mode === 'remote') {
    $('summary').textContent = 'Waiting for the other side\'s scouting call before tip-off'; return false;
  }
  if (sc.report && sc.report.level !== 'pro' && !seen('report')) {
    markSeen('report');
    if (st.level === 'learn') showReport('Scout report (Learn level)', null, 'Tip off');
    else {
      const mine = sc.mine ? ' Your call: ' + [sc.mine.hunt ? `hunt O${sc.mine.hunt.o} v X${sc.mine.hunt.x}` : null, sc.mine.protect ? `protect #${sc.mine.protect.x}` : null].filter(Boolean).join('; ') + '.' : '';
      showReport('Scout report unlocked', 'Your scouting call is locked. Check your read against the report.' + mine, 'Tip off');
    }
    return true;
  }
  return false;
}

function pickModal(side) {
  const sc = st.scout, needs = sc.needs[side];
  const mine = sc.teams[side], theirs = sc.teams[side === 'O' ? 'X' : 'O'];
  const sel = (id, label, prefix) => el('label', {}, [label + ' ', el('select', { id }, [1, 2, 3, 4, 5].map(n => el('option', { value: n, text: `${prefix}${n}` })))]);
  const cards = (pieces, s) => el('div', { class: 'pickcards' }, pieces.map(p => cardEl(p.card, s, `${s}${p.i + 1}`)));
  const parts = [el('h2', { text: `${side === 'O' ? 'Offence' : 'Defence'} (${mine}): your scouting call` }),
    el('p', { class: 'note', text: (st.mode === 'hotseat' ? `${side === 'O' ? 'Defence' : 'Offence'}, look away. ` : '') +
      'Read the cards first: make your call from the cards alone. It locks when you save it, and the scout report unlocks after that. The other side sees your call only in the review.' })];
  if (needs.includes('hunt')) parts.push(el('h3', { text: 'Hunt one matchup' }), el('div', { class: 'picker' }, [sel('pkHuntO', `Your attacker (${mine})`, 'O'), sel('pkHuntX', `v their defender (${theirs})`, 'X')]));
  if (needs.includes('protect')) parts.push(el('h3', { text: 'Protect one weakness' }), el('div', { class: 'picker' }, [sel('pkProtect', `Your defender (${mine})`, '#')]));
  parts.push(el('button', { class: 'primary', text: 'Lock my call', onclick: async () => {
    const body = { code: G.code, token: G.token, side };
    if (needs.includes('hunt')) body.hunt = { o: Number($('pkHuntO').value), x: Number($('pkHuntX').value) };
    if (needs.includes('protect')) body.protect = { x: Number($('pkProtect').value) };
    try { const r = await api('/api/scout', body); closeModal(); st = r.state; render(); } catch (e) { alert(e.message); }
  } }));
  parts.push(el('h3', { text: `Offence: ${st.teams[0]}` }), cards(st.o, 'O'), el('h3', { text: `Defence: ${st.teams[1]}` }), cards(st.x, 'X'));
  modal(parts);
}

async function loadReview() {
  const box = $('reviewBox'); if (!box) return;
  box.innerHTML = ''; box.append(el('h3', { text: 'Review' }), el('p', { class: 'note', text: 'Working out the review (a few seconds)…' }));
  let r; try { r = await api('/api/review', { code: G.code, token: G.token }); } catch (e) { box.append(el('p', { text: e.message })); return; }
  box.innerHTML = '';
  const sides = ['O', 'X'];
  const pickText = (side, p) => [p.hunt ? `hunt O${p.hunt.o} v X${p.hunt.x}` : null, p.protect ? `protect X${p.protect.x}` : null].filter(Boolean).join('; ');
  // the coach reads the review first: the call you made against the biggest edge the board offered
  const best = r.advantages[0];
  const calls = sides.filter(side => r.picks[side]).map(side => `${side === 'O' ? 'offence' : 'defence'}, ${pickText(side, r.picks[side])}`).join('; on ');
  const read = (calls ? `Your call: on ${calls}. ` : 'No call was made before tip-off. ')
    + (best ? `The biggest edge the board offered was ${best.text} at clock ${best.clock}, and it was ${best.used ? 'taken' : 'not taken'}.` : 'No ▲ shot came onto the board: the defence kept its shape all possession.')
    + (r.solver && r.solver.length ? ` The solver would have played ${r.solver.length === 1 ? 'one decision' : r.solver.length + ' decisions'} differently; the list is below.` : '');
  box.append(PMCoach.line('coach', read, { compact: true, speak: false, live: false }));
  // the plan against the team sheet: one row a side
  box.append(el('h4', { text: 'The plan against the team sheet' }), el('table', { class: 'bk' }, sides.map(side => el('tr', {}, [
    el('td', { text: side === 'O' ? 'Offence' : 'Defence' }),
    el('td', { text: r.picks[side] ? pickText(side, r.picks[side]) : 'no call made' }),
    el('td', { class: 'note', text: 'team sheet: ' + ([r.engine[side].hunt ? 'hunt ' + r.engine[side].hunt.text : null, r.engine[side].protect ? 'protect ' + r.engine[side].protect.text : null].filter(Boolean).join('; ') || 'none') })]))));
  box.append(el('h4', { text: 'What the board offered' }), el('p', { class: 'note', text: 'The biggest ▲ shot edges against the contester eligible at that moment, at any decision point.' }),
    el('ul', {}, r.advantages.length ? r.advantages.map(a => el('li', { text: `${a.text} (clock ${a.clock}): ${a.used ? 'taken' : 'not taken'}` })) : [el('li', { text: 'No ▲ shot was on the board.' })]));
  box.append(el('h4', { text: 'Where the solver disagreed (estimates)' }), el('p', { class: 'note', text: r.solver_note }));
  if (r.solver) box.append(el('ul', {}, r.solver.length ? r.solver.map(x => el('li', { text: `Estimate · clock ${x.clock}, ${x.side === 'O' ? 'offence' : 'defence'}: played "${x.played}"; the solver preferred "${x.solver}" (about ${x.gap.toFixed(1)} points, estimate)` }))
    : [el('li', { text: 'Estimate: no decision differed by more than half a point.' })]));
  if (r.computer && r.computer.length) {
    box.append(el('h4', { text: 'About the computer' }));
    for (const c of r.computer) box.append(el('p', { text: c }));
  }
  if (r.timer && r.timer.length) box.append(el('h4', { text: 'The timer' }), el('ul', {}, r.timer.map(t => el('li', { text: t }))));
  if (r.in_play) {
    const pk = sides.filter(side => r.picks[side]).map(side => `${side === 'O' ? 'Offence' : 'Defence'}: ${pickText(side, r.picks[side])}`).join(' · ');
    box.append(el('h4', { text: 'The report in play' }), el('p', { class: 'note', text: 'Counts from the log for each line of the scout report. Facts only.' + (pk ? ' Your calls: ' + pk + '.' : '') }));
    for (const t of r.in_play) box.append(el('p', {}, [el('b', { text: t.team })]), el('ul', { class: 'inplay' }, t.items.map(it =>
      el('li', { class: it.tested ? '' : 'untested', text: `${it.who === t.team ? t.team : it.who} ${it.line}: ${it.text}` }))));
  }
}

// Detail level: a short option name, explained underneath (long option text overflows phone screens).
const LEVEL_NOTE = {
  learn: 'Learn: the full scout report, the matchups on the cards and the team-sheet hunt / protect.',
  scout: 'Scout: strengths and liabilities; each side makes a private hunt / protect call.',
  pro: 'Pro: cards only; the score at the end and the full review on request.',
};
function showLevelNote() { const n = $('levelNote'); if (n) n.textContent = LEVEL_NOTE[$('level').value] || ''; }
if ($('level')) { $('level').addEventListener('change', showLevelNote); showLevelNote(); }


// ---------------------------------------------------------------- Coach Vision on the sideline
// The coach reads the board from the cards both players can see: for each attacker and the defender on that attacker
// (the matchup the squares and arrows show), the shot where the attacker's rating beats the contest by most,
// counted as points x (shot - contest). That edge is the mismatch; the line names it and the shot it leads to.
const SHOT_PTS = { Layup: 2, Dunk: 2, Post: 2, Mid: 2, Floater: 2, 'Long 2': 2, Three: 3 };
const SHOT_WHERE = { Layup: 'at the rim', Dunk: 'at the rim', Post: 'on the block', Mid: 'from mid-range', Floater: 'from the paint', 'Long 2': 'from a long two', Three: 'behind the arc' };
function boardEdges(s) {
  const out = [];
  const rating = (card, name) => { for (const g of card.groups) for (const r of g.ratings) if (r.name === name) return r; return null; };
  for (const o of s.o) {
    const js = (s.matchups.O || [])[o.i] || []; if (!js.length || !o.card) continue;
    const x = s.x[js[0]];
    for (const name of Object.keys(SHOT_PTS)) {
      const sh = rating(o.card, name), con = rating(x.card, 'v ' + name);
      if (!sh || !con) continue;
      const edge = SHOT_PTS[name] * (sh.value - con.value);
      out.push({ o: o.i, x: x.i, shot: name, edge, sh, con, mismatch: sh.band === 'H' && con.band !== 'H' || con.band === 'L' && sh.band !== 'L' });
    }
  }
  return out.sort((a, b) => b.edge - a.edge);
}
let coachSaid = null;
function renderCoachLine() {
  const box = $('coachLine'); if (!box) return;
  box.innerHTML = '';
  const s = st; if (!s || !s.can_act || s.stage === 'over' || replay || s.placing || !s.matchups) return;
  if (s.level !== 'learn') return;             // arrange, never judge: the coach reads the board at Learn level only
  const side = s.side_to_act, mine = s.scout && s.scout.mine;
  const edges = boardEdges(s), best = edges.find(e => e.mismatch) || edges[0];
  const show = e => `O${e.o + 1}'s ${e.shot.toLowerCase()} ${e.sh.value}${e.sh.mark} against X${e.x + 1}'s contest ${e.con.value}${e.con.mark}: a clean look ${SHOT_WHERE[e.shot]} is worth ${SHOT_PTS[e.shot]} × ${e.sh.value - e.con.value} = ${e.edge}`;
  let text = null;
  const pick = sel.side === side && sel.i != null ? sel : null;
  if (pick) {                                   // a piece is selected: the read for that matchup, cue then rule
    const e = edges.find(x => (side === 'O' ? x.o : x.x) === pick.i);
    if (e) {
      const o = s.o[e.o], x = s.x[e.x], on = isArrowOn(x, o), near = Math.max(Math.abs(o.x - x.x), Math.abs(o.y - x.y)) === 1;
      if (side === 'O') {
        text = `O${e.o + 1} v X${e.x + 1}: ${e.shot.toLowerCase()} ${e.sh.value}${e.sh.mark} against contest ${e.con.value}${e.con.mark}, worth ${e.edge} ${SHOT_WHERE[e.shot]}. `
          + (on ? `X${e.x + 1}'s arrow is on O${e.o + 1}: a steal is on and the contest is clean. Move the arrow first: a cut, a screen, or the ball to someone else.`
            : near ? `X${e.x + 1} is next to O${e.o + 1} but facing away: a catch here is clean, and a contest risks a foul.`
            : `X${e.x + 1} is off O${e.o + 1}: the catch is clean. Get the ball there and shoot before the arrow comes.`);
      } else {
        text = `X${e.x + 1} on O${e.o + 1}: their ${e.shot.toLowerCase()} ${e.sh.value}${e.sh.mark} against your contest ${e.con.value}${e.con.mark}${e.edge > 0 ? `, worth ${e.edge} to them` : ', nothing for them'}. `
          + (on ? `Your arrow is on O${e.o + 1}: you contest cleanly and may steal. Hold it.`
            : near ? `You are next to O${e.o + 1} but facing away: turn the arrow with your Move, or the contest costs a foul roll.`
            : `You are off O${e.o + 1}: one straight movement along your arrow onto the lane picks the pass off; otherwise close out before the catch.`);
      }
    }
  }
  if (text) { /* the selection read stands */ } else if (best && best.edge > 0) {
    const carrier = (s.o.find(p => p.ball) || {}).i === best.o;
    text = `The mismatch on the board: ${show(best)}. `
      + `Offence read: O${best.o + 1} is the threat; ${carrier ? 'the spot with no arrow on O' + (best.o + 1) + ' is the look' : 'the catch where no arrow reaches the lane is the look'}. `
      + `Defence read: O${best.o + 1}'s catch is the problem; a body on the lane to O${best.o + 1}, or an arrow on O${best.o + 1} before the ball arrives.`;
    if (side === 'O' && mine && mine.hunt && mine.hunt.o - 1 !== best.o) text += ` (Your call was O${mine.hunt.o} v X${mine.hunt.x}; the board says this one is bigger right now.)`;
    if (side === 'X' && mine && mine.protect) text += ` (Your call was to protect X${mine.protect.x}.)`;
  } else text = 'No mismatch on the board right now. Offence read: move the defence first, a screen or a cut that makes a defender choose. Defence read: keep the shape, every lane answered, every arrow on a man.';
  if (!text) return;
  const key = `${s.possession}:${s.phase}:${side}:${s.turn}`;
  box.append(PMCoach.line('coach', text, { compact: true, live: coachSaid !== key }));
  coachSaid = key;
}

// ---------------------------------------------------------------- the play story: one diagram per phase
// When a phase ends its diagram appears (every turn's actions in notation, numbered by turn), and Continue
// moves on. The story so far is always a tap away; each diagram can be saved as an image.
let lastShown = {};               // possession -> the highest phase whose diagram has been shown
let diagramOpen = false, phasesInit = false;
function pendingPhase() {
  if (!st || st.placing || !st.possession) return null;
  const limit = st.stage === 'over' ? st.phase : st.phase - 1;
  if (!phasesInit) { phasesInit = true; lastShown[st.possession] = st.stage === 'over' ? st.phase : limit; return null; }
  const done = lastShown[st.possession] || 0;
  return done < limit ? { possession: st.possession, phase: done + 1 } : null;
}
function diagramDue() {
  const due = pendingPhase();
  if (!due || diagramOpen) return !!due;
  if (!$('modal').classList.contains('hidden')) return true;    // another dialog first (a roll, a handover)
  diagramOpen = true;
  showPhaseDiagram(due).catch(() => { diagramOpen = false; lastShown[due.possession] = due.phase; });
  return true;
}
function phaseTitle(p) { return `Phase ${p.phase}`; }
// the feedback loop: the best ▲ look the board offered in the phase, and whether it was taken
function lookLine(p) {
  if (p.look === undefined) return null;          // the possession is still being played: no judgement during play
  if (!p.look) return PMCoach.line('coach', 'No ▲ look came onto the board this phase: the defence kept every shooter covered, or nobody was in a shot zone.', { compact: true, live: false });
  const L = p.look;
  return PMCoach.line('coach', `The best look this phase: ${L.text}, at clock ${L.clock}. ` + (L.taken ? 'Taken: that is the read.' : 'Not taken. Next time that is the shot to build towards.'), { compact: true, live: false });
}
function phaseSub(p) { return `clock ${p.clock}${p.end_clock != null && p.end_clock !== p.clock ? ' to ' + p.end_clock : ''}${p.over ? ' · possession over' : ''}`; }
function phaseWords(p) {
  const out = [];
  for (const e of p.entries) for (const o of (e.outcomes || [])) if (o.tone !== 'info' || /lands|New phase/.test(o.text)) out.push(o.text);
  return out;
}
async function showPhaseDiagram(due) {
  const story = await api(`/api/story?code=${G.code}`);
  const p = story.phases.find(x => x.possession === due.possession && x.phase === due.phase);
  if (!p || !p.start) { diagramOpen = false; lastShown[due.possession] = due.phase; render(); return; }
  const dia = PM.phaseDiagram(st.zones, p.start, p.entries, { title: phaseTitle(p), subtitle: phaseSub(p), arrowMode: story.arrow_mode });
  const words = phaseWords(p);
  const kids = [el('h2', { text: `${phaseTitle(p)} on the whiteboard` }),
    el('div', { class: 'diagrambox' }, [dia]),
    el('p', { class: 'note small', text: 'Black: offence. Red: defence. Each mark carries its turn number; the board is where the phase started.' }),
    lookLine(p), words.length ? el('ul', { class: 'phasewords' }, words.map(w => el('li', { text: w }))) : null,
    el('div', { class: 'buttons' }, [
      el('button', { class: 'primary', id: 'phaseContinue', text: 'Continue', onclick: () => { lastShown[due.possession] = due.phase; diagramOpen = false; closeModal(); render(); } }),
      el('button', { text: 'Save as image', onclick: () => saveDiagram(dia, `${st.code}_possession${p.possession}_phase${p.phase}.png`) }),
      el('button', { text: 'The story so far', onclick: () => { lastShown[due.possession] = due.phase; diagramOpen = false; closeModal(); showStory(); } })])];
  modal(kids, () => { lastShown[due.possession] = due.phase; diagramOpen = false; render(); });
  announce(`${phaseTitle(p)} over. ${words.join(' ')}`);
  const b = $('phaseContinue'); if (b) b.focus();
}
async function saveDiagram(dia, name) {
  try {
    const blob = await PM.toPng(dia, 2);
    const a = el('a', { href: URL.createObjectURL(blob), download: name }); document.body.append(a); a.click(); a.remove();
  } catch (e) { alert(e.message); }
}
async function showStory() {
  let story; try { story = await api(`/api/story?code=${G.code}`); } catch (e) { alert(e.message); return; }
  const kids = [el('h2', { text: 'The story of the play' }),
    el('p', { class: 'note', text: `${story.teams[0]} v ${story.teams[1]}. One diagram a phase (two seconds of play); each action carries its turn number.` })];
  const dias = [];
  for (const p of story.phases) {
    if (!p.start) continue;
    const dia = PM.phaseDiagram(st.zones, p.start, p.entries, { title: `Possession ${p.possession} · ${phaseTitle(p)}`, subtitle: phaseSub(p), arrowMode: story.arrow_mode });
    dias.push([dia, p]);
    kids.push(el('section', { class: 'storyphase' }, [el('div', { class: 'diagrambox' }, [dia]),
      lookLine(p), el('ul', { class: 'phasewords' }, p.entries.filter(e => e.mark).map(e => el('li', { text: `${e.side === 'O' ? 'O' : 'X'} turn ${e.turn}: ${e.text}` })))]));
  }
  if (!dias.length) kids.push(el('p', { text: 'No phase has been played yet.' }));
  kids.push(el('div', { class: 'buttons' }, [
    dias.length ? el('button', { text: 'Save all as images', onclick: async () => { for (const [d, p] of dias) await saveDiagram(d, `${st.code}_possession${p.possession}_phase${p.phase}.png`); } }) : null,
    el('button', { class: 'primary', text: 'Close', onclick: () => { closeModal(); render(); } })]));
  modal(kids, () => render());
}


// ---------------------------------------------------------------- step 3m: the match strip, records and the trainer
let trainerSeen = null;                  // how many finished possessions the trainer has read for this page
const trainerReads = {};                 // possession -> the trainer's read
function renderStrip(s) {
  const box = $('strip'); if (!box) return;
  box.innerHTML = '';
  if (!s.full || !s.strip) return;
  for (const e of s.strip.entries) box.append(el('span', { class: `chip ${e.attacker} ${e.mark === 'TO' ? 'to' : e.mark === 'FT' ? 'ft' : ''}`, title: `Possession ${e.possession}: player ${e.attacker} ${e.mark === 'TO' ? 'turned it over' : e.mark === 'FT' ? 'went to the line' : 'scored ' + e.total}`,
    text: `${e.attacker} ${e.mark === 'FT' ? 'FT ' + e.total : e.mark}` }));
  const left = (s.n_poss || 2) - s.strip.entries.length;
  for (let k = 0; k < left; k++) box.append(el('span', { class: 'chip empty', 'aria-hidden': 'true', text: '·' }));
}
async function fillProfiles() {
  let ps = [];
  try { ps = await PMRecords.profiles(); } catch (e) { ps = []; }
  for (const id of ['profA', 'profB']) {
    const cur = $(id).value; $(id).innerHTML = '';
    $(id).append(el('option', { value: '', text: 'No profile' }), ...ps.map(p => el('option', { value: p.id, text: `${p.name} (${Math.round(p.rating)})` })),
      el('option', { value: '__new', text: 'New player…' }));
    if (cur && ps.some(p => p.id === cur)) $(id).value = cur;
  }
  try { const last = JSON.parse(localStorage.getItem('pm_profiles') || 'null'); if (last) { if (last.A && ps.some(p => p.id === last.A)) $('profA').value = last.A; if (last.B && ps.some(p => p.id === last.B)) $('profB').value = last.B; } } catch (e) { /* ignore */ }
}
function matchPlayers(body) {
  const pa = $('profA').value && $('profA').value !== '__new' ? $('profA').value : null;
  const pb = $('profB').value && $('profB').value !== '__new' ? $('profB').value : null;
  try { localStorage.setItem('pm_profiles', JSON.stringify({ A: pa, B: pb })); } catch (e) { /* ignore */ }
  const name = id => { const o = id && document.querySelector(`#profA option[value="${id}"]`); return o ? o.textContent.replace(/ \(\d+\)$/, '') : null; };
  const LV = { rookie: 'Rookie', starter: 'Starter', allstar: 'All-Star' };
  const players = { A: { profile: null, name: 'Player A' }, B: { profile: null, name: 'Player B' } };
  let mine = null;
  if (path === 'computer' && body.ai && (body.ai.A || body.ai.B)) {
    const me = body.ai.A ? 'B' : 'A', other = me === 'A' ? 'B' : 'A';
    players[me] = { profile: pa, name: name(pa) || 'You' }; players[other] = { computer: body.ai[other], name: `Computer (${LV[body.ai[other]]})` };
    mine = players[me];
  } else {
    players.A = { profile: pa, name: name(pa) || 'Player A' }; players.B = { profile: pb, name: name(pb) || 'Player B' };
  }
  return { players, mine };
}
async function startRecord(code, body, players) {
  if (!players.A.profile && !players.B.profile) return null;
  const rec = { id: `m${Date.now().toString(36)}${code}`, code, date: new Date().toISOString(), format: body.match_format || 'tabletop',
    per_side: body.per_side || (body.full ? 1 : 1), settings: { age: body.age || 'senior', standard: typeof body.standard === 'string' ? body.standard : 'pro',
      roster: body.roster || 'prescribed', deal: body.deal || null, level: body.level, mode: body.mode, teams: body.teams || null },
    players, trainer: {}, scores: [], totals: { A: 0, B: 0 }, done: false };
  await PMRecords.saveMatch(rec);
  return rec.id;
}
function humanPlayers() { return ['A', 'B'].filter(p => !(st.ai && Object.keys(st.ai).length === 2) && !isComputer(p)); }
function isComputer(p) {
  const side = st.attacker === p ? 'O' : 'X';
  return !!(st.ai && st.ai[side]);
}
function trainerBoxKids(poss) {
  const read = trainerReads[poss];
  if (!read) return Object.keys(st.ai || {}).length === 2 ? [] : [el('p', { class: 'note', role: 'status', text: 'The trainer is reading this possession…' })];
  const out = [];
  for (const p of Object.keys(read.players || {})) {
    if (!summaryDue(p, poss)) continue;
    const e = PMTrainer.summaryEl(read, p, openWhy); if (e) out.push(e);
  }
  if (!out.length && Object.keys(read.players || {}).length) out.push(el('p', { class: 'note', text: 'The trainer read this possession (in the match review).' }));
  return out;
}
let profileRatings = {};
function summaryDue(player, poss) {
  // fade the summaries as the player's rating rises: every possession at first, then every 2 or 3 (D5)
  const r = profileRatings[player] || 1500, fade = (OPTS && OPTS.trainer && OPTS.trainer.fade) || [[0, 1600, 1], [1600, 1800, 2], [1800, 9999, 3]];
  const n = (fade.find(([lo, hi]) => r >= lo && r < hi) || [0, 0, 1])[2];
  return n <= 1 || poss % n === 0 || poss === (st.n_poss || 2);
}
async function onPossessionOver(s) {
  const n = s.scores.length;
  if (trainerSeen === null) { trainerSeen = n - 1; }
  if (n <= trainerSeen) return;
  trainerSeen = n;
  const poss = s.scores[n - 1].possession;
  let rec = null;
  try { rec = G.rec ? await PMRecords.match(G.rec) : null; } catch (e) { rec = null; }
  if (rec) { for (const p of ['A', 'B']) if (rec.players[p] && rec.players[p].profile) { const pr = await PMRecords.profile(rec.players[p].profile); if (pr) profileRatings[p] = pr.rating; } }
  if (Object.keys(s.ai || {}).length < 2) {
    try { trainerReads[poss] = await api('/api/trainer', { code: G.code, token: G.token, possession: poss }); }
    catch (e) { trainerReads[poss] = { possession: poss, players: {}, error: e.message }; }
    const box = $('trainerBox'); if (box && st.possession === poss) { box.innerHTML = ''; box.append(...trainerBoxKids(poss)); }
  }
  if (rec) {
    rec.scores = s.scores.map(x => ({ possession: x.possession, attacker: x.attacker, total: x.total, ended: x.ended }));
    rec.totals = s.strip ? s.strip.totals : rec.totals;
    if (trainerReads[poss]) rec.trainer[poss] = trainerReads[poss];
    if (s.match) await finishRecord(rec, s);
    await PMRecords.saveMatch(rec);
  }
}
let ratingNotes = [];
async function finishRecord(rec, s) {
  if (rec.done) return;
  rec.done = true; rec.winner = s.match.winner; rec.totals = { A: s.match.A, B: s.match.B };
  ratingNotes = [];
  for (const p of ['A', 'B']) {
    const me = rec.players[p]; if (!me || !me.profile) continue;
    const pr = await PMRecords.profile(me.profile); if (!pr) continue;
    const o = rec.players[p === 'A' ? 'B' : 'A'];
    let opponent = null;
    if (o && o.profile) { const op = await PMRecords.profile(o.profile); if (op) opponent = { rating: op.rating, rd: op.rd }; }
    const gs = await PMRecords.groupsOf(pr.id);
    const losses = gs.slice(-60).map(g => g.loss).sort((a, b) => a - b);
    const med = losses.length ? losses[losses.length >> 1] : 9.9;
    try {
      const r = await api('/api/rate', { player: { rating: pr.rating, rd: pr.rd, vol: pr.vol }, opponent, my_total: rec.totals[p], opp_total: rec.totals[p === 'A' ? 'B' : 'A'],
        possessions: rec.per_side, level: o && o.computer ? o.computer : null, age: rec.settings.age, median_loss: med,
        recent_scores: (pr.scores || []).slice(-4), weakest: PMTrainer.weakest(gs) });
      ratingNotes.push(`${pr.name}: rating ${Math.round(pr.rating)} → ${Math.round(r.player.rating)} (± ${Math.round(r.player.rd)}); match score ${r.score.toFixed(2)}.`);
      for (const sgg of r.suggestions) ratingNotes.push(sgg.kind === 'practice' ? `Practice for ${pr.name}: ${sgg.how} ${sgg.why}` : sgg.text);
      Object.assign(pr, r.player); pr.scores = (pr.scores || []).concat([r.score]); pr.suggestions = r.suggestions;
      await PMRecords.saveProfile(pr);
    } catch (e) { ratingNotes.push(`${pr.name}: the rating could not be updated (${e.message}).`); }
  }
  const box = $('ratingBox'); if (box) { box.innerHTML = ''; box.append(...ratingKids()); }
}
function ratingKids() { return ratingNotes.length ? [el('h3', { text: 'Ratings' }), ...ratingNotes.map(t => el('p', { text: t }))] : []; }
async function openWhy(poss, group, player) {
  modal([el('p', { class: 'note', role: 'status', text: 'Reading the turn group…' })], closeModal);
  try {
    const w = await api('/api/why', { code: G.code, token: G.token, possession: poss, group, player });
    modal([...PMTrainer.whyEl(w), el('button', { class: 'primary', text: 'Close', onclick: () => { closeModal(); if (st.stage === 'over') endModal(); } })], closeModal);
  } catch (e) { modal([el('p', { text: e.message }), el('button', { text: 'Close', onclick: closeModal })], closeModal); }
}
async function playersPage() {
  const ps = await PMRecords.profiles();
  const list = el('ul', { class: 'profiles' }, ps.map(p => el('li', {}, [el('strong', { text: p.name }), ` rating ${Math.round(p.rating)} ± ${Math.round(p.rd)} `,
    el('button', { class: 'small', text: 'Trainer', onclick: async () => modal([...(await PMTrainer.profileEl(p.id)), el('button', { class: 'primary', text: 'Back', onclick: playersPage })], closeModal) }),
    el('button', { class: 'small', text: 'Rename', onclick: async () => { const n = prompt('New name', p.name); if (n) { await PMRecords.renameProfile(p.id, n); await fillProfiles(); playersPage(); } } }),
    el('button', { class: 'small', text: 'Delete', onclick: async () => { if (confirm(`Delete ${p.name}? Their matches stay in the records.`)) { await PMRecords.deleteProfile(p.id); await fillProfiles(); playersPage(); } } })])));
  const sel = id => el('select', { id }, ps.map(p => el('option', { value: p.id, text: p.name })));
  const s1 = sel('h2hA'), s2 = sel('h2hB'); if (ps.length > 1) s2.value = ps[1].id;
  const file = el('input', { type: 'file', accept: 'application/json,.json', id: 'importFile', 'aria-label': 'Records file to import' });
  modal([el('h2', { text: 'Players and records' }),
    ps.length ? list : el('p', { class: 'note', text: 'No players yet.' }),
    el('button', { text: 'New player', onclick: async () => { const n = prompt('Name for the new player'); if (n) { await PMRecords.createProfile(n); await fillProfiles(); playersPage(); } } }),
    el('h3', { text: 'Head to head' }),
    ps.length > 1 ? el('p', {}, [s1, ' v ', s2, ' ', el('button', { text: 'Show', onclick: async () => modal([...(await PMTrainer.headToHeadEl(s1.value, s2.value)), el('button', { class: 'primary', text: 'Back', onclick: playersPage })], closeModal) })])
      : el('p', { class: 'note', text: 'Two players are needed.' }),
    el('h3', { text: 'Export and import' }),
    el('p', { class: 'note', text: 'One JSON file holds every player and match on this device. Importing it reproduces them exactly.' }),
    el('button', { text: 'Export records', onclick: async () => {
      const data = JSON.stringify(await PMRecords.exportAll());
      const a = el('a', { href: URL.createObjectURL(new Blob([data], { type: 'application/json' })), download: `playmaker_records_${new Date().toISOString().slice(0, 10)}.json` });
      document.body.append(a); a.click(); a.remove(); } }),
    el('label', {}, ['Import ', file]),
    el('button', { text: 'Import (replace these records)', onclick: async () => {
      const f = file.files && file.files[0]; if (!f) { alert('Choose a records file first.'); return; }
      try { const r = await PMRecords.importAll(JSON.parse(await f.text()), true); alert(`Imported ${r.profiles} players and ${r.matches} matches.`); await fillProfiles(); playersPage(); }
      catch (e) { alert(e.message); } } }),
    el('button', { class: 'primary', text: 'Close', onclick: closeModal })], closeModal);
}
