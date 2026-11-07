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
  for (const id of ['teamA', 'teamB']) $(id).append(el('option', { value: '__custom', text: 'Custom team…' }));
  $('teamA').value = o.first_game[0]; $('teamB').value = o.first_game[1];
  for (const [id, slot] of [['teamA', 0], ['teamB', 1]]) $(id).addEventListener('change', () => builder(slot));
  builder(0); builder(1);
  for (const s of o.scenarios) $('scenario').append(el('option', { value: s.n, text: `${s.n}. ${s.title} (${s.kind}, clock ${s.clock})` }));
  const showKind = () => {
    const k = $('kind').value;
    $('scenarioRow').classList.toggle('hidden', k !== 'scenario');
    $('teamsRow').classList.toggle('hidden', k === 'scenario');
    const s = o.scenarios.find(x => String(x.n) === $('scenario').value);
    $('scenarioText').textContent = k === 'scenario' && s ? `${s.text} O: ${s.off}. X: ${s.dfn}.` :
      k === 'full' ? 'Two possessions on the preview table setup; each player attacks once. Higher total wins.' :
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
  let done = false; try { done = localStorage.getItem('pm_course_done') === '1'; } catch (e) { /* ignore */ }
  if (done) choosePath('computer', showKind, true);
}
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
  if (computer) $('mode').value = 'hotseat';
  if (scenario) { $('aiLevel').insertBefore(el('option', { value: '', text: 'nobody: two players' }), $('aiLevel').firstChild); $('aiLevel').value = $('aiLevel').value || 'rookie'; }
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

// ---------------------------------------------------------------- custom team builder (step 3d)
let OPTS = null;
const POS = ['PG', 'SG', 'SF', 'PF', 'C'];
const LEGAL_SHAPES = ['BBBBB', 'ABBBC', 'AABCC'];
function customCards(slot) { return POS.map(p => $(`b${slot}${p}`).value); }
function builder(slot) {
  const box = $(`builder${slot}`), on = $(slot ? 'teamB' : 'teamA').value === '__custom';
  box.classList.toggle('hidden', !on);
  if (!on) { builderStatus(); return; }
  if (box.dataset.built) { builderStatus(); return; }
  box.dataset.built = '1';
  const load = el('select', { id: `bLoad${slot}`, onchange: () => {
    const t = OPTS.teams.find(x => x.name === load.value); if (!t) return;
    POS.forEach((p, i) => { $(`b${slot}${p}`).value = t.cards[i]; }); builderStatus();
  } }, [el('option', { value: '', text: 'Start from a prescribed team…' }), ...OPTS.teams.map(t => el('option', { value: t.name, text: t.name }))]);
  box.append(el('h3', { text: `Custom team ${slot ? 'B' : 'A'}` }),
    el('label', {}, ['Name ', el('input', { id: `bName${slot}`, value: 'Custom', maxlength: 30 })]),
    el('label', {}, ['Load ', load]),
    ...POS.map(p => el('label', {}, [`${p} `, el('select', { id: `b${slot}${p}`, onchange: builderStatus },
      OPTS.cards.filter(c => c.position === p).map(c => el('option', { value: c.key, text: `${c.role} (${c.tier})` })))])),
    el('p', { class: 'note', id: `bShape${slot}`, role: 'status' }));
  const start = OPTS.teams.find(t => t.name === OPTS.first_game[slot]);
  POS.forEach((p, i) => { $(`b${slot}${p}`).value = start.cards[i]; });
  builderStatus();
}
function builderStatus() {
  const tier = k => OPTS.cards.find(c => c.key === k).tier;
  const cardsOf = slot => {
    const v = $(slot ? 'teamB' : 'teamA').value;
    if (v === '__custom') return $(`b${slot}PG`) ? customCards(slot) : [];
    const t = OPTS.teams.find(x => x.name === v); return t ? t.cards : [];
  };
  for (const slot of [0, 1]) {
    const p = $(`bShape${slot}`); if (!p || $(slot ? 'teamB' : 'teamA').value !== '__custom') continue;
    const shape = customCards(slot).map(tier).sort().join('');
    p.textContent = LEGAL_SHAPES.includes(shape) ? `Tier shape ${shape}: a legal shape.` :
      `Tier shape ${shape}: not a legal shape (BBBBB, ABBBC or AABCC). Allowed, but the game is labelled experimental in the log.`;
    p.classList.toggle('exp', !LEGAL_SHAPES.includes(shape));
  }
  const a = cardsOf(0), b = cardsOf(1), both = a.filter(k => b.includes(k));
  $('builderWarn').textContent = both.length ? `Both sides use ${both.map(k => OPTS.cards.find(c => c.key === k).role + ' (' + tier(k) + ')').join(', ')}: the table game would need two card sets. Allowed here.` : '';
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
  const tA = $('timerA').value ? Number($('timerA').value) : null;
  const hc = $('hcA').checked && $('hcB').checked;
  const tB = hc ? ($('timerB').value ? Number($('timerB').value) : null) : tA;
  if (tA || tB) body.timer = { A: tA, B: tB, handicap: hc };
  try { localStorage.setItem('pm_sound', $('timerSound').checked ? '1' : '0'); } catch (e) { /* ignore */ }
  if (k === 'scenario') body.scenario = Number($('scenario').value);
  else {
    body.teams = [$('teamA').value, $('teamB').value]; body.full = k === 'full';
    body.custom = [0, 1].filter(i => body.teams[i] === '__custom').map(i => ({ slot: i, name: $(`bName${i}`).value || 'Custom', cards: customCards(i) }));
    body.custom.forEach(c => { body.teams[c.slot] = c.name; });
  }
  try {
    const r = await api('/api/new', body);
    G = { code: r.code, token: r.token };
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
  $('poss').textContent = s.full ? `${s.possession} of 2` : '1';
  if (s.full) { const t = s.scores.map(x => `${x.attacker}: ${x.total}`).join(' · '); $('score').textContent = t || '0'; }
  else $('score').textContent = String(s.bonus - 5 * s.turnovers);
  const LV = { rookie: 'Rookie (makes beginner mistakes you can learn to spot)', starter: 'Starter (solid, with one habit to find)', allstar: 'All-Star (plays the full read)', baseline: 'baseline' };
  const ai = Object.entries(s.ai || {}).map(([k, v]) => `${k === 'O' ? 'offence' : 'defence'}: ${LV[v] || v}`).join('; ');
  $('meta').innerHTML = '';
  $('meta').append(el('div', { text: `${s.mode === 'remote' ? 'Remote' : 'Hot-seat'} · code ${s.code}${s.seat && s.seat !== 'both' ? ' · you: ' + (s.seat === 'O' ? 'Offence' : 'Defence') : ''}` }),
    ...(ai ? [el('div', { text: `Computer ${ai}` })] : []),
    ...(s.timer ? [el('div', { text: s.timer.handicap ? `Timer (handicap): player A ${s.timer.setting.A || 'off'}${s.timer.setting.A ? ' s' : ''}, player B ${s.timer.setting.B || 'off'}${s.timer.setting.B ? ' s' : ''}` : `Timer: ${s.timer.setting.A} s per decision` })] : []),
    ...((s.experimental || []).length ? [el('div', { class: 'exp', text: `Experimental lineup: ${s.experimental.join(', ')}` })] : []),
    ...(s.scout && s.scout.report && s.scout.report.level !== 'pro' ? [el('button', { class: 'small', text: 'Scout report', onclick: () => showReport('Scout report') })] : []),
    el('button', { class: 'small', text: 'Play story', onclick: showStory }),
    el('button', { class: 'small', 'aria-pressed': playVoice() ? 'true' : 'false', text: playVoice() ? 'Referee voice: on' : 'Referee voice: off', onclick: e => { try { localStorage.setItem('pm_voice_play', playVoice() ? '0' : '1'); } catch (x) { /* ignore */ } render(); } }));
  renderCoachLine();
  const sideChip = s.stage === 'over' ? '' : (s.side_to_act === 'O' ? 'OFFENCE TO ACT · ' : s.side_to_act === 'X' ? 'DEFENCE TO ACT · ' : '');
  $('summary').textContent = replay ? `${sideName(replay.entries[replay.k].side).toUpperCase()} ACTED · ${s.summary}`
    : sideChip + s.summary + (s.can_act ? '' : s.stage === 'over' ? '' : ' · waiting for the other side');
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

function cardEl(c, side, label, extra) {
  const head = el('div', { class: 'head' }, [el('span', { text: `${label} ${c.role} (${c.tier})` }), el('span', { text: `QS ${c.qs}` })]);
  const groups = c.groups.map(g => el('table', { class: 'grp', 'aria-label': g.name }, [
    el('tr', {}, [el('th', { class: 'gname', text: g.name === 'Actions' ? 'Act' : g.name === 'Shots' ? 'Shot' : 'Con' }),
      ...g.ratings.map(r => el('th', { text: SHORT[r.name] || r.name, title: r.name }))]),
    el('tr', {}, [el('td'), ...g.ratings.map(r => el('td', { class: 'r ' + r.band, text: `${r.value}${r.mark}`,
      'aria-label': `${r.name} ${r.value} ${r.band === 'H' ? 'above average' : r.band === 'L' ? 'below average' : 'average'}` }))])]));
  return el('div', { class: `card ${side === 'O' ? 'offence' : 'defence'}` }, [head, ...groups, extra || null]);
}

function renderCards(id, pieces, side) {
  const box = $(id); box.innerHTML = '';
  box.append(el('div', { class: 'key' }, [el('span', { class: 'H', text: '▲ above average' }), ' ', el('span', { text: 'plain = average' }), ' ', el('span', { class: 'L', text: '▼ below average' })]));
  for (const p of pieces) {
    const c = p.card;
    const head = el('div', { class: 'head' }, [el('span', { text: `${side}${p.i + 1} ${c.role} (${c.tier})` }), el('span', { text: `QS ${c.qs}` })]);
    const groups = c.groups.map(g => el('table', { class: 'grp', 'aria-label': g.name }, [
      el('tr', {}, [el('th', { class: 'gname', text: g.name === 'Actions' ? 'Act' : g.name === 'Shots' ? 'Shot' : 'Con' }),
        ...g.ratings.map(r => el('th', { text: SHORT[r.name] || r.name, title: r.name }))]),
      el('tr', {}, [el('td'), ...g.ratings.map(r => el('td', { class: 'r ' + r.band, text: `${r.value}${r.mark}`,
        'aria-label': `${r.name} ${r.value} ${r.band === 'H' ? 'above average' : r.band === 'L' ? 'below average' : 'average'}` }))])]));
    const note = side === 'O' && st.inbound_note && p.i === st.inbounder ? el('div', { class: 'inbnote', text: st.inbound_note }) : null;
    box.append(el('div', { class: `card ${side === 'O' ? 'offence' : 'defence'}${sel.side === side && sel.i === p.i ? ' focus' : ''}` }, [head, ...groups, note]));
  }
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
  const lim = el('div', { class: 'limits' }, s.limits[side].map(l => el('span', { class: l.used >= l.limit ? 'full' : '', text: `${KIND_NAME[l.kind] || l.kind} ${l.used}/${l.limit}` })));
  box.append(el('div', { text: 'Per-phase limits used (Move: once per player)' }), lim);
  const wk = side === 'X' ? 'pause' : 'hesitate', w = s.limits[side].find(l => l.kind === wk);
  if (w) box.append(el('div', { class: 'waits', text: `${KIND_NAME[wk]}: ${w.limit} a phase (${w.used >= w.limit ? 'used' : 'not used yet'})` }));
  const rules = el('details', { class: 'rulesbox' }, [el('summary', { text: 'Rule reminders' }),
    el('div', { class: 'waits interceptrule' }, [
      el('div', { text: 'Through you: a pass through your square can be challenged, whatever your facing.' }),
      el('div', { text: 'Jump the lane: one straight Move, Quick Step or Sprint along your arrow onto the pass line, then Intercept.' }),
      el('div', { text: 'Next to the passer: no intercept on any square around him. Steal instead.' }),
      el('div', { text: 'Picked off: −5 and lose 2 seconds. On the last phase, the possession scores 0.' })]),
    el('div', { class: 'waits stealrule', text: 'Stolen (in play or on a shot): −5 and lose 2 seconds; the ball stays with you, and a stolen shot is cancelled. On the last phase, the possession scores 0.' }),
    side === 'O' ? el('div', { class: 'waits screenrule', text: s.screen_rule === 'two_turns'
      ? "Screen: ends your turn. The screener can't move; it flips back after your next turn."
      : "Screen: First action, or second after your own Move. Ends your turn. Lasts until you move or it's beaten." }) : null]);
  box.append(rules);
}

// The defender reach (zones of influence) can be hidden by a player who finds it busy; the rules don't change.
function showReach() { try { return localStorage.getItem('pm_reach') !== '0'; } catch (e) { return true; } }

function renderCourt() {
  const s = st, c = $('court');
  c.innerHTML = '';
  PM.court(c, s.zones, { axes: true });
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
  PM.marks(c, turnMarks(), { numbers: true });          // the turn in play, in notation (resets when the turn ends)
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
  if (side === 'O' && p.ball) bits.push('has the ball');
  if (side === 'O' && p.screen) bits.push(`screening, T to the ${COMPASS[p.screen.dir]}`);
  if (side === 'X') bits.push(`arrow pointing ${COMPASS[p.arrow]}`);
  if (p.locked) bits.push('locked');
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
  const b = st.influence && st.influence.badges && st.influence.badges.O[p.i];
  PM.tags(g, p.x, p.y, b, p.locked);
  c.append(g);
}

function drawX(c, p, opts) {
  const g = pieceGroup('X', p.i, opts);
  const wedge = st.influence && st.influence.arrow_mode === 'wedge';
  PM.pieceX(g, p.x, p.y, p.i + 1, wedge ? [p.arrow, (p.arrow + 1) % 8] : [p.arrow]);
  const b = st.influence && st.influence.badges && st.influence.badges.X[p.i];
  PM.tags(g, p.x, p.y, b, p.locked);
  c.append(g);
}

// Zones of influence (every defender, along his arrow line, out to his current reach), active screens and the
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
        stroke: 'rgba(31,42,68,0.6)', 'stroke-width': 1, 'stroke-dasharray': sprint ? '3 2' : '' }));
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
    for (const k of [...new Set(acts.map(a => a.kind))]) {
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
            if (thr.length) parts.push(`through his square (${thr[0].sq})`);
            if (jmp.length) parts.push('one straight movement along his arrow onto the line at ' + [...new Set(jmp.map(t => `${t.sq} (${t.by})`))].join(' or ') + ', then Intercept');
            if (fol.length) parts.push(`moves, then jumps (${new Set(fol.map(t => t.sq)).size} crossing square${new Set(fol.map(t => t.sq)).size === 1 ? '' : 's'})`);
            const old = ts.filter(t => t.how === 'direct' || t.how === 'approach');
            if (old.length) parts.push(old[0].how === 'direct' ? 'on the line' : 'arrow across (must move onto the line first)');
            return `X${Number(j) + 1} ${parts.join('; ')}`;
          });
          tb.append(el('div', { class: 'opt' }, [actionButton(a, `Pass to O${a.target + 1}`), el('span', { class: 'note', text: th.length ? ' Can intercept: ' + th.join('; ') : ' No defender can intercept this pass' }), chips(a)]));
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
  if (s.stage === 'over') return;
  if (s.mode === 'hotseat' && s.can_undo) $('sideButtons').append(el('button', { text: 'Undo (only before a roll)', onclick: undo }));
  if (s.mode === 'remote' && s.can_undo) $('sideButtons').append(el('button', { text: s.undo_votes.length ? `Undo requested by ${s.undo_votes.join(', ')}: agree` : 'Request undo (both must agree)', onclick: undo }));
}

async function undo() {
  try { const r = await api('/api/undo', { code: G.code, token: G.token }); st = r.state; sel = { side: null }; render(); }
  catch (e) { $('error').textContent = e.message; }
}

async function submit(a) {
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
    modal([el('h2', { text: a.text }), PMCoach.line('ref', 'This one goes to the dice. ' + a.roll.map(t => t.text.replace(/^(Offence|Defence) rolls: /, '')).join(' Then ') + '.', { compact: true, speak: playVoice(), live: false }),
      el('ul', {}, a.roll.map(t => el('li', {}, [rollerChip(t.roller), ' ' + t.text]))),
      el('button', { class: 'primary', text: 'Roll', onclick: () => { closeModal(); res(true); } }),
      el('button', { text: 'Cancel', onclick: () => { closeModal(); res(false); } })], () => res(false));
  });
}

function playVoice() { try { return localStorage.getItem('pm_voice_play') === '1'; } catch (e) { return false; } }
function showRolls(rolls) {
  return new Promise(res => {
    const call = rolls.map(r => `${r.what.replace(/ \(.*\)$/, '')}: rolled ${r.face}, ${r.picked}.`).join(' ');
    const box = [el('h2', { text: 'The call' }), PMCoach.line('ref', call, { compact: true, speak: playVoice(), live: false })];
    for (const r of rolls) {
      const ok = r.face <= r.need;
      box.push(el('div', {}, [rollerChip(r.roller), el('span', { class: 'die roll' + (r.roller === 'X' ? ' black' : ''), text: r.face }), el('span', { text: `${r.text} → rolled ${r.face}: ${r.picked}` })]));
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
    PMCoach.line('coach', verdict, { compact: true, speak: playVoice(), live: false }),
    el('table', { class: 'bk' }, rows.map(([k, v]) => el('tr', {}, [el('td', { text: k }), el('td', { text: String(v) })])))];
  if (s.scenario) kids.push(el('p', { text: `Goal (look 30+): ${r.goal_met ? 'met' : 'missed'} (look ${r.look})` + (r.late_clock ? ` · result: ${r.late_clock}` : '') }));
  if (s.target !== null && s.target !== undefined && s.target !== 'secret' && s.target >= 0) kids.push(el('p', { text: `The secret target was O${s.target + 1}.` }));
  if (s.match) {
    const m = s.match;
    kids.push(el('h3', { text: `Match: A ${m.A} · B ${m.B} → ${m.winner === 'tie' ? 'still tied' : 'player ' + m.winner + ' wins'}` }));
    if (m.tiebreak) kids.push(el('p', { text: `Tiebreak: A rolled ${m.tiebreak.A.roll} (needs ${m.tiebreak.A.need} or less), B rolled ${m.tiebreak.B.roll} (needs ${m.tiebreak.B.need} or less).` }));
  }
  const nav = el('div', { class: 'buttons' }, [
    s.full && s.possession === 1 ? el('button', { class: 'primary', text: 'Start possession 2 (sides swap)', onclick: async () => { closeModal(); const q = await api('/api/next', { code: G.code, token: G.token }); st = q.state; phasesInit = false; render(); } }) : null,
    el('button', { class: s.full && s.possession === 1 ? '' : 'primary', text: 'The story of the play', onclick: () => { closeModal(); showStory(); } }),
    el('button', { text: 'Close', onclick: closeModal }),
    el('button', { text: 'New game', onclick: () => { location.href = location.pathname; } })]);
  kids.push(nav);
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
      else if (r.type === 'roll') ol.append(el('li', {}, [rollerChip(r.roller), ` rolled ${r.face}: ${r.text.replace(/^(Offence|Defence) rolls: /, '')} → ${r.picked}`]));
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
  $('sideButtons').append(confirm,
    el('button', { text: 'Start again', onclick: () => { place = null; renderPlacement(); renderCourt(); } }),
    el('button', { text: 'Use the preview table setup (both sides)', onclick: async () => { try { const r = await api('/api/place', { code: G.code, token: G.token, preview: true }); place = null; st = r.state; render(); } catch (e) { $('error').textContent = e.message; } } }),
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
      ` ${r.what}: ${r.first} on ${r.need} or less → rolled ${r.face}: `, el('strong', { text: r.picked.toUpperCase() })]));
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
  bar.append(el('div', { class: 'step-count', text: `${sideName(e.side)}${e.actor === 'ai' ? ' (computer)' : ''} · action ${replay.k + 1} of ${n}` }),
    feedEntry(e), el('button', { class: 'primary', id: 'stepOk', text: label, onclick: stepOn }));
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
  const how = opp ? (side === 'O' ? (st.x[opps[k]].arrow !== undefined && opps.length && isArrowOn(st.x[opps[k]], mine) ? 'arrow on him' : 'nearest defender')
                                  : (isArrowOn(mine, opp) ? 'his arrow is on this player' : 'nearest attacker')) : '';
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
  const rows = t.players.filter(p => p[side].strengths.length || p[side].weaknesses.length).map(p =>
    el('div', { class: 'prow' }, [chartEl(p.chart[side], `${side === 'off' ? 'Shooting' : 'Contests'} chart for ${p.num} ${p.short}`),
      el('div', { class: 'ptext' }, [el('div', { class: 'pname', text: `${p.num} ${p.short}` }), ...phraseLines(p[side])])]));
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
  box.append(el('h3', { text: 'Review' }));
  const sides = ['O', 'X'];
  const pickText = (side, p) => [p.hunt ? `hunt O${p.hunt.o} v X${p.hunt.x}` : null, p.protect ? `protect #${p.protect.x}` : null].filter(Boolean).join('; ');
  box.append(el('h4', { text: '1. Your plan against the board' }), el('ul', {}, sides.map(side => el('li', { text:
    `${side === 'O' ? 'Offence' : 'Defence'}: ${r.picks[side] ? 'your call: ' + pickText(side, r.picks[side]) : 'no call made'} · team sheet: ${[r.engine[side].hunt ? 'hunt ' + r.engine[side].hunt.text : null, r.engine[side].protect ? 'protect ' + r.engine[side].protect.text : null].filter(Boolean).join('; ')}` }))));
  box.append(el('h4', { text: '2. What the board offered' }), el('p', { class: 'note', text: 'The biggest ▲ shot edges against the contester eligible at that moment, at any decision point.' }),
    el('ul', {}, r.advantages.length ? r.advantages.map(a => el('li', { text: `${a.text} (clock ${a.clock}): ${a.used ? 'used (that shot was taken)' : 'not used'}` })) : [el('li', { text: 'No ▲ shot was on the board.' })]));
  box.append(el('h4', { text: '3. Where the solver disagreed (estimates)' }), el('p', { class: 'note', text: r.solver_note }));
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
  box.append(el('h4', { text: '4. Reflect' }), el('p', { text: 'Was your setup and plan the right one for these two teams? (Answer it with the feedback below.)' }));
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
let coachSaid = null;
function renderCoachLine() {
  const box = $('coachLine'); if (!box) return;
  box.innerHTML = '';
  const s = st; if (!s || !s.can_act || s.stage === 'over' || replay) return;
  const side = s.side_to_act, mine = s.scout && s.scout.mine;
  let text = null;
  if (side === 'O' && mine && mine.hunt) text = `Your call was to hunt O${mine.hunt.o} against X${mine.hunt.x}. Get him the ball where no arrow can reach the lane, then make X${mine.hunt.x} guard him.`;
  else if (side === 'X' && mine && mine.protect) text = `Your call was to protect X${mine.protect.x}. Don't leave him with two jobs: keep help beside him and his arrow on his man.`;
  else if (side === 'O' && s.level === 'learn') text = 'Pick a goal before you pick an action: which matchup is ours, and what shot does it lead to?';
  else if (side === 'X' && s.level === 'learn') text = 'Read the arrows: every pass lane either has a defender who can reach it, or it doesn\'t.';
  if (!text) return;
  const key = `${s.possession}:${s.phase}:${side}`;
  box.append(PMCoach.line('coach', text, { compact: true, speak: false, live: coachSaid !== key }));
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
    el('p', { class: 'note', text: 'Every action of the phase in coaching notation: black for the offence, red for the defence, each marked with its turn number. The board shows where the phase started.' }),
    el('div', { class: 'diagrambox' }, [dia]),
    words.length ? el('ul', { class: 'phasewords' }, words.map(w => el('li', { text: w }))) : null,
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
      el('ul', { class: 'phasewords' }, p.entries.filter(e => e.mark).map(e => el('li', { text: `${e.side === 'O' ? 'O' : 'X'} turn ${e.turn}: ${e.text}` })))]));
  }
  if (!dias.length) kids.push(el('p', { text: 'No phase has been played yet.' }));
  kids.push(el('div', { class: 'buttons' }, [
    dias.length ? el('button', { text: 'Save all as images', onclick: async () => { for (const [d, p] of dias) await saveDiagram(d, `${st.code}_possession${p.possession}_phase${p.phase}.png`); } }) : null,
    el('button', { class: 'primary', text: 'Close', onclick: () => { closeModal(); render(); } })]));
  modal(kids, () => render());
}
