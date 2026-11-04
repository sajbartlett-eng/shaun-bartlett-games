// Playmaker playtest table. Renders from the server's state JSON; never decides a rule itself.
'use strict';
const S = 36, PADX = 24, PADY = 20, COLS = 'ABCDEFGHIJKLMNOPQ';
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
let busy = false, pollTimer = null;
let seenFeed = null;          // feed entries already shown on this screen

const $ = id => document.getElementById(id);
const el = (tag, attrs = {}, kids = []) => {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
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
const px = x => PADX + (x + 1) * S, py = y => PADY + (14 - y) * S;

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
  for (const t of o.teams) { $('teamA').append(el('option', { value: t.name, text: t.name })); $('teamB').append(el('option', { value: t.name, text: t.name })); }
  $('teamA').value = o.first_game[0]; $('teamB').value = o.first_game[1];
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
  $('create').onclick = create; if ($('join')) $('join').onclick = join;
  const q = new URLSearchParams(location.search);
  if (q.get('code') && q.get('token')) { G = { code: q.get('code'), token: q.get('token') }; enterTable(); return; }
  if (q.get('code')) $('joinCode').value = q.get('code');
  const saved = localStorage.getItem('pm_game');
  if (saved && q.has('resume')) { G = JSON.parse(saved); enterTable(); }
}

async function create() {
  const k = $('kind').value, mode = $('mode').value;
  const body = { mode, level: $('level').value, ai: { O: $('aiO').checked ? 'greedy' : null, X: $('aiX').checked ? 'greedy' : null } };
  if ($('seed').value) body.seed = Number($('seed').value);
  if (k === 'scenario') body.scenario = Number($('scenario').value);
  else { body.teams = [$('teamA').value, $('teamB').value]; body.full = k === 'full'; }
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
  const ai = Object.keys(s.ai || {}).map(k => (k === 'O' ? 'offence' : 'defence')).join(' and ');
  $('meta').innerHTML = '';
  $('meta').append(el('div', { text: `${s.mode === 'remote' ? 'Remote' : 'Hot-seat'} · code ${s.code}${s.seat && s.seat !== 'both' ? ' · you: ' + (s.seat === 'O' ? 'Offence' : 'Defence') : ''}` }),
    ...(ai ? [el('div', { text: `Test opponent plays ${ai} (greedy baseline, not strong)` })] : []));
  const sideChip = s.stage === 'over' ? '' : (s.side_to_act === 'O' ? 'OFFENCE TO ACT · ' : s.side_to_act === 'X' ? 'DEFENCE TO ACT · ' : '');
  $('summary').textContent = sideChip + s.summary + (s.can_act ? '' : s.stage === 'over' ? '' : ' · waiting for the other side');
  $('summary').dataset.side = s.side_to_act || '';
  $('offTeam').textContent = s.teams[0] + (s.full ? ` (player ${s.attacker})` : '');
  $('defTeam').textContent = s.teams[1] + (s.full ? ` (player ${s.attacker === 'A' ? 'B' : 'A'})` : '');
  renderCards('offCards', s.o, 'O'); renderCards('defCards', s.x, 'X');
  renderTracker('offTracker', 'O'); renderTracker('defTracker', 'X');
  renderCourt(); renderActions(); renderScenario(); renderRolls(); renderLog(); renderPhoneLists(); renderRecent(); renderCompare();
  if (scoutModalIfDue()) return;
  if (s.placing) return;
  if (showFeedIfNew()) return;          // the other side's turn first; the end screen follows
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
}

function renderCourt() {
  const s = st, c = $('court');
  c.innerHTML = '';
  const W = PADX + 19 * S + 4, H = PADY + 15 * S + 22;
  c.setAttribute('viewBox', `0 0 ${W} ${H}`);
  c.setAttribute('role', 'group');
  c.setAttribute('aria-label', `Court, 17 columns A to Q by 14 rows, rim at I2. ${s.summary}`);
  for (let y = 1; y <= 14; y++) {
    for (let x = 0; x < 17; x++) {
      const z = s.zones[y - 1][x];
      c.append(svg('rect', { class: 'cell', x: px(x), y: py(y), width: S, height: S, fill: ZCOL[z] }));
      if (ZLBL[z]) { const t = svg('text', { class: 'zonelbl', x: px(x) + 2, y: py(y) + 11, 'aria-hidden': 'true' }); t.textContent = ZLBL[z]; c.append(t); }
    }
    const t = svg('text', { class: 'axis', x: 2, y: py(y) + S / 2 + 4 }); t.textContent = y; c.append(t);
  }
  for (let x = 0; x < 17; x++) { const t = svg('text', { class: 'axis', x: px(x) + S / 2 - 4, y: PADY - 6 }); t.textContent = COLS[x]; c.append(t); }
  const rim = svg('circle', { cx: px(8) + S / 2, cy: py(2) + S / 2, r: 9, fill: 'none', stroke: '#c0392b', 'stroke-width': 3 }); c.append(rim);
  // arrow lines the ball carrier can't cross (shown to both players)
  const carrier = s.o.find(p => p.ball);
  if (sel.side === 'O' && carrier && sel.i === carrier.i) {
    for (const l of s.arrow_lines) c.append(svg('line', { x1: px(l.start[0]) + S / 2, y1: py(l.start[1]) + S / 2, x2: px(l.end[0]) + S / 2, y2: py(l.end[1]) + S / 2, stroke: '#222', 'stroke-width': 3, 'stroke-dasharray': '6 4' }));
  }
  // pending pass line
  if (s.pending) {
    const a = s.o[s.pending[0]], b = s.o[s.pending[1]];
    c.append(svg('line', { x1: px(a.x) + S / 2, y1: py(a.y) + S / 2, x2: px(b.x) + S / 2, y2: py(b.y) + S / 2, stroke: '#7a4b00', 'stroke-width': 3, 'stroke-dasharray': '3 3' }));
  }
  for (const p of s.o) drawO(c, p);
  for (const p of s.x) drawX(c, p);
  drawTargets(c);
  placementTargets(c);
}

function pieceLabel(side, p) {
  const z = st.zones[p.y - 1] ? ZONE_WORD[st.zones[p.y - 1][p.x]] : 'off the court';
  const bits = [`${side}${p.i + 1}, ${p.card.role}, on ${p.sq} (${z})`];
  if (side === 'O' && p.ball) bits.push('has the ball');
  if (side === 'O' && p.screen) bits.push(`screening, T to the ${COMPASS[p.screen.dir]}`);
  if (side === 'X') bits.push(`arrow pointing ${COMPASS[p.arrow]}`);
  if (p.locked) bits.push('locked');
  if (sel.side === side && sel.i === p.i) bits.push('selected');
  const n = pieceActs(side, p.i).length;
  if (st.can_act && n) bits.push(`${n} legal action${n === 1 ? '' : 's'}`);
  return bits.join(', ');
}

function pieceGroup(side, i) {
  const p = (side === 'O' ? st.o : st.x)[i];
  const acted = actedPieces().has(side + i);
  const g = svg('g', { class: 'piece' + (sel.side === side && sel.i === i ? ' sel' : '') + (acted ? ' acted' : ''), tabindex: 0, role: 'button',
    'aria-label': pieceLabel(side, p), 'aria-pressed': sel.side === side && sel.i === i ? 'true' : 'false' });
  const choose = () => selectPiece(side, i);
  g.addEventListener('click', choose); g.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); choose(); } });
  return g;
}

function drawO(c, p) {
  const cx = px(p.x) + S / 2, cy = py(p.y) + S / 2, g = pieceGroup('O', p.i);
  if (p.screen) {
    const d = DIRS[p.screen.dir];
    g.append(svg('line', { x1: cx, y1: cy, x2: cx + d[0] * S * 0.62, y2: cy - d[1] * S * 0.62, stroke: '#111', 'stroke-width': 5 }));
    const nx = -d[1], ny = d[0];
    const ex = cx + d[0] * S * 0.62, ey = cy - d[1] * S * 0.62;
    g.append(svg('line', { x1: ex - nx * 9, y1: ey + ny * 9, x2: ex + nx * 9, y2: ey - ny * 9, stroke: '#111', 'stroke-width': 5 }));
  }
  g.append(svg('circle', { class: 'halo', cx, cy, r: 19 }));
  g.append(svg('circle', { class: 'ring', cx, cy, r: 15, fill: '#fff', stroke: '#1d1b18', 'stroke-width': 2.5 }));
  const t = svg('text', { x: cx, y: cy + 6, 'text-anchor': 'middle', 'font-size': 18, 'font-weight': 'bold', 'aria-hidden': 'true' }); t.textContent = p.i + 1; g.append(t);
  if (p.ball) {          // the ball: an orange disc with a dark outline (readable on every zone colour)
    g.append(svg('circle', { cx: cx + 12, cy: cy - 12, r: 7.5, fill: '#e07a1f', stroke: '#3a1d00', 'stroke-width': 2.5 }));
    g.append(svg('path', { d: `M${cx + 4.5} ${cy - 12} H${cx + 19.5} M${cx + 12} ${cy - 19.5} V${cy - 4.5}`, stroke: '#3a1d00', 'stroke-width': 1.2 }));
  }
  if (p.locked) lockBadge(g, cx, cy);
  c.append(g);
}

function drawX(c, p) {
  const cx = px(p.x) + S / 2, cy = py(p.y) + S / 2, g = pieceGroup('X', p.i);
  // the arrow: a wedge from the piece's edge reaching about a third of a square into the next square
  const d = DIRS[p.arrow], ux = d[0], uy = -d[1];
  const reach = S / 2 + S / 3;                                 // edge of this square + a third of the next
  const tip = [cx + ux * reach, cy + uy * reach];
  const len = Math.hypot(ux, uy), nx = -uy / len, ny = ux / len, bx = cx + ux * 9 / len, by = cy + uy * 9 / len;
  g.append(svg('polygon', { class: 'arrowhead', points: `${tip[0]},${tip[1]} ${bx + nx * 11},${by + ny * 11} ${bx - nx * 11},${by - ny * 11}`, fill: '#111', stroke: '#fff', 'stroke-width': 1.5 }));
  g.append(svg('circle', { class: 'halo', cx, cy, r: 19 }));
  g.append(svg('circle', { class: 'ring', cx, cy, r: 14, fill: '#1a1a1a', stroke: '#000', 'stroke-width': 2 }));
  const t = svg('text', { x: cx, y: cy + 6, 'text-anchor': 'middle', 'font-size': 17, 'font-weight': 'bold', fill: '#fff', 'aria-hidden': 'true' }); t.textContent = p.i + 1; g.append(t);
  if (p.locked) lockBadge(g, cx, cy);
  c.append(g);
}

function lockBadge(g, cx, cy) {
  g.append(svg('rect', { x: cx - 21, y: cy + 5, width: 26, height: 13, rx: 3, fill: '#4a4a4a', stroke: '#1d1b18', 'stroke-width': 1.5 }));
  const t = svg('text', { x: cx - 8, y: cy + 15, 'text-anchor': 'middle', 'font-size': 9.5, 'font-weight': 'bold', fill: '#fff', 'aria-hidden': 'true' }); t.textContent = 'LOCK'; g.append(t);
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
          const th = (a.threats || []).map(t => `X${t.defender + 1} ${t.how === 'direct' ? 'on the line' : 'arrow across (must move onto the line first)'}`);
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
    modal([el('h2', { text: a.text }), el('p', { text: 'This action needs a roll. The server rolls the d20 (seeded); you never roll on this page.' }),
      el('ul', {}, a.roll.map(t => el('li', {}, [rollerChip(t.roller), ' ' + t.text]))),
      el('button', { class: 'primary', text: 'Roll', onclick: () => { closeModal(); res(true); } }),
      el('button', { text: 'Cancel', onclick: () => { closeModal(); res(false); } })], () => res(false));
  });
}

function showRolls(rolls) {
  return new Promise(res => {
    const box = [el('h2', { text: 'Roll' })];
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
  const kids = [el('h2', { text: s.full ? `Possession ${s.possession} over` : 'Possession over' }),
    el('p', {}, [el('span', { class: 'band ' + r.band, text: `${r.total} · ${r.band}` })]),
    el('table', { class: 'bk' }, rows.map(([k, v]) => el('tr', {}, [el('td', { text: k }), el('td', { text: String(v) })]))),
    el('p', { text: r.detail || '' })];
  if (s.scenario) kids.push(el('p', { text: `Goal (look 30+): ${r.goal_met ? 'met' : 'missed'} (look ${r.look})` + (r.late_clock ? ` · result: ${r.late_clock}` : '') }));
  if (s.target !== null && s.target !== undefined && s.target !== 'secret' && s.target >= 0) kids.push(el('p', { text: `The secret target was O${s.target + 1}.` }));
  if (s.full && s.possession === 1) kids.push(el('button', { class: 'primary', text: 'Start possession 2 (sides swap)', onclick: async () => { closeModal(); const q = await api('/api/next', { code: G.code, token: G.token }); st = q.state; render(); } }));
  if (s.match) {
    const m = s.match;
    kids.push(el('h3', { text: `Match: A ${m.A} · B ${m.B} → ${m.winner === 'tie' ? 'still tied' : 'player ' + m.winner + ' wins'}` }));
    if (m.tiebreak) kids.push(el('p', { text: `Tiebreak: A rolled ${m.tiebreak.A.roll} (needs ${m.tiebreak.A.need} or less), B rolled ${m.tiebreak.B.roll} (needs ${m.tiebreak.B.need} or less).` }));
  }
  if (s.feedback_due) kids.push(el('section', { id: 'reviewBox', class: 'review' }, [el('h3', { text: 'Review' }),
    s.level === 'pro' ? el('button', { text: 'Show the full review', onclick: loadReview }) : el('p', { class: 'note', text: 'Loading the review…' })]));
  if (s.feedback_due && s.level !== 'pro') setTimeout(loadReview, 0);
  if (s.feedback_due && !s.feedback_done) {
    const areas = s.feedback_questions.map((q, i) => el('label', {}, [el('div', { text: `${i + 1}. ${q}` }), el('textarea', { id: 'fb' + i })]));
    areas.push(el('label', {}, [el('div', { text: 'Was your setup and plan the right one for these two teams?' }), el('textarea', { id: 'fbReflect' })]));
    kids.push(el('h3', { text: 'Feedback (saved with the game log)' }), ...areas,
      el('button', { class: 'primary', text: 'Send feedback', onclick: async () => {
        const answers = {}; s.feedback_questions.forEach((q, i) => { answers[i] = $('fb' + i).value; });
        answers.reflect = $('fbReflect').value;
        await api('/api/feedback', { code: G.code, token: G.token, answers }); st.feedback_done = true; closeModal(); endModal(); } }));
  }
  if (s.feedback_due) kids.push(el('h3', { text: 'Game log' }), el('p', { class: 'note', text: s.static ? 'The log lives in this browser tab. Download it, or copy it to paste into an email.' : `Saved on the server in playtest_logs/${s.log_name}.` }),
    el('button', { text: 'Download log', onclick: downloadLog }), el('button', { text: 'Copy log', onclick: copyLog }));
  kids.push(el('button', { text: 'Close', onclick: closeModal }), el('button', { text: 'New game', onclick: () => { location.href = location.pathname; } }));
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
function modal(kids, cancel) {
  const b = $('modalBox'); b.innerHTML = ''; b.append(...kids);
  const h = b.querySelector('h1, h2, h3');
  if (h) { h.id = 'modalTitle'; $('modal').setAttribute('aria-labelledby', 'modalTitle'); }
  modalReturn = document.activeElement; modalCancel = cancel || null;
  $('modal').classList.remove('hidden'); document.body.classList.add('modal-open');
  for (const id of ['table', 'start']) $(id).setAttribute('aria-hidden', 'true');
  const f = b.querySelector('button, textarea, input'); if (f) f.focus();
}
function closeModal() {
  $('modal').classList.add('hidden'); document.body.classList.remove('modal-open');
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

let place = null;      // {side, squares: [], ball, arrows: []}
function renderPlacement() {
  const s = st, P = s.placing;
  $('selected').textContent = ''; $('kindButtons').innerHTML = ''; $('targetButtons').innerHTML = ''; $('sideButtons').innerHTML = '';
  if (!place || place.side !== P.side) place = { side: P.side, squares: [], ball: null, arrows: [] };
  const who = P.side === 'O' ? 'Offence' : 'Defence';
  if (!P.mine) { $('selected').textContent = P.by_ai ? `The computer is placing the ${who.toLowerCase()}.` : `Waiting: the ${who.toLowerCase()} is placing.`; return; }
  const k = place.squares.length;
  if (k < 5) $('selected').textContent = `${who} setup: place ${P.side}${k + 1}. Click a highlighted square.` + (P.side === 'O' ? ' The ball must start on a player on plain wood beyond the three-point tiles (outlined).' : ' Defenders go on empty squares.');
  else if (P.side === 'O' && place.ball == null) $('selected').textContent = 'Choose who has the ball (on plain wood beyond the three-point tiles):';
  else if (P.side === 'X') $('selected').textContent = 'Set each arrow, then confirm:';
  const tb = $('targetButtons');
  if (k === 5 && P.side === 'O') {
    place.squares.forEach((q, i) => { if (P.ball_squares.includes(q)) tb.append(el('button', { class: place.ball === i ? 'active' : '', text: `Ball to O${i + 1} (${q})`, onclick: () => { place.ball = i; renderPlacement(); renderCourt(); } })); });
  }
  if (k === 5 && P.side === 'X') {
    place.squares.forEach((q, i) => { tb.append(el('div', {}, [el('span', { text: `X${i + 1} on ${q}: ` }), ...DIRN.map((n, d) => el('button', { class: place.arrows[i] === d ? 'active' : '', text: n, onclick: () => { place.arrows[i] = d; renderPlacement(); renderCourt(); } }))])); });
  }
  const ready = k === 5 && (P.side === 'O' ? place.ball != null : place.arrows.filter(a => a != null).length === 5);
  $('sideButtons').append(
    el('button', { class: 'primary', text: `Confirm the ${who.toLowerCase()} setup`, disabled: ready ? null : 'disabled', onclick: confirmPlacement }),
    el('button', { text: 'Start again', onclick: () => { place = null; renderPlacement(); renderCourt(); } }),
    el('button', { text: 'Use the preview table setup (both sides)', onclick: async () => { try { const r = await api('/api/place', { code: G.code, token: G.token, preview: true }); place = null; st = r.state; render(); } catch (e) { $('error').textContent = e.message; } } }));
  if (!ready) $('sideButtons').firstChild.setAttribute('disabled', 'disabled');
}
async function confirmPlacement() {
  try {
    const body = { code: G.code, token: G.token, squares: place.squares };
    if (place.side === 'O') body.ball = place.ball; else body.arrows = place.arrows;
    const r = await api('/api/place', body); place = null; st = r.state; render();
  } catch (e) { $('error').textContent = e.message; }
}
function placementTargets(c) {
  const P = st.placing; if (!P || !P.mine || !place) return;
  const taken = new Set(place.squares);
  for (const q of P.squares) {
    if (taken.has(q) || place.squares.length >= 5) continue;
    const x = COLS.indexOf(q[0]), y = Number(q.slice(1));
    const r = svg('rect', { class: 'target' + (P.side === 'O' && P.ball_squares.includes(q) ? ' ballsq' : ''), x: px(x) + 3, y: py(y) + 3, width: S - 6, height: S - 6, rx: 5, tabindex: 0, role: 'button', 'aria-label': `place on ${q}` });
    const fn = () => { place.squares.push(q); if (place.side === 'X') place.arrows.push(defaultArrow(q)); renderPlacement(); renderCourt(); };
    r.addEventListener('click', fn); r.addEventListener('keydown', e => { if (e.key === 'Enter') fn(); });
    c.append(r);
  }
  place.squares.forEach((q, i) => {
    const x = COLS.indexOf(q[0]), y = Number(q.slice(1));
    const t = svg('text', { x: px(x) + S / 2, y: py(y) + S / 2 + 6, 'text-anchor': 'middle', 'font-size': 16, 'font-weight': 'bold', fill: P.side === 'X' ? '#fff' : '#000' });
    c.append(svg('circle', { cx: px(x) + S / 2, cy: py(y) + S / 2, r: 14, fill: P.side === 'X' ? '#1a1a1a' : '#fff', stroke: '#333', 'stroke-width': 2, 'stroke-dasharray': '3 2' }));
    t.textContent = i + 1; c.append(t);
  });
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
function showFeedIfNew() {
  const fresh = newOtherEntries();
  if (!fresh.length) return false;
  lastOther = fresh;
  const who = sideName(fresh[0].side);
  const kids = [el('h2', { text: `${who}${fresh[0].actor === 'ai' ? ' (computer)' : ''}: what just happened` }),
    ...fresh.map(feedEntry),
    el('button', { class: 'primary', text: 'Continue', onclick: () => { closeModal(); render(); } })];
  announce(fresh.map(e => `${sideName(e.side)}: ${e.text}. ` + e.rolls.map(r => `Rolled ${r.face}: ${r.picked}.`).join(' ') + ' ' + e.outcomes.map(o => o.text).join(' ')).join(' '));
  renderRecent(); renderCourt();
  modal(kids, () => render());
  return true;
}
function renderRecent() {
  const box = $('recent'); if (!box) return;
  box.innerHTML = '';
  if (!lastOther.length) { box.classList.add('hidden'); return; }
  box.classList.remove('hidden');
  box.append(el('h3', { text: `Last turn: ${sideName(lastOther[0].side)}${lastOther[0].actor === 'ai' ? ' (computer)' : ''}` }), ...lastOther.map(feedEntry));
}
function actedPieces() {
  const out = new Set();
  for (const e of lastOther) { const m = e.text.match(/^([OX])(\d)/); if (m) out.add(m[1] + (Number(m[2]) - 1)); }
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

function reportEl(rep) {
  const out = [];
  if (rep.level === 'pro') return out;
  for (const t of rep.teams) {
    const L = t.lists, nums = a => a.length ? a.map(n => '#' + n).join(', ') : 'none';
    out.push(el('h3', { text: t.name }),
      el('p', { class: 'note', text: `Creators (Dribble or Pass ▲): ${nums(L.creators)} · Three ▲: ${nums(L.three_shooters)} · Rim protection (v Layup or v Dunk ▲): ${nums(L.rim_protectors)} · Two or more ▼ on defence: ${nums(L.defensive_liabilities)}` }),
      el('table', { class: 'scout' }, [el('tr', {}, [el('th', { text: '#' }), el('th', { text: 'Player' }), el('th', { text: 'Offence' }), el('th', { text: 'Defence' })]),
        ...t.players.map(p => el('tr', {}, [el('td', { text: p.num }), el('td', { text: `${p.role} (${p.tier})` }), el('td', { text: p.offence.text }), el('td', { text: p.defence.text })]))]));
  }
  if (rep.matchups) out.push(el('h3', { text: 'Matchups on the cards (by position)' }), el('ul', {}, rep.matchups.map(m => el('li', { text: m.text }))));
  if (rep.engine) out.push(el('h3', { text: "The engine's hunt / protect (team sheet)" }), el('p', { text: `Hunt: ${rep.engine.hunt.text}. Protect: ${rep.engine.protect.text}.` }));
  return out;
}

function seenKey(what) { return `pm_${what}_${G.code}`; }
function scoutModalIfDue() {
  const sc = st.scout;
  if (!sc || !$('modal').classList.contains('hidden')) return false;
  const pending = sc.pending.filter(side => st.mode === 'hotseat' || st.seat === side);
  if (pending.length) { pickModal(pending[0]); return true; }
  if (sc.pending.length && st.mode === 'remote') {
    $('summary').textContent = 'Waiting for the other side\'s scouting call before tip-off'; return false;
  }
  let seen = false; try { seen = localStorage.getItem(seenKey('report')) === '1'; } catch (e) { /* private mode */ }
  if (st.level === 'learn' && !seen) {
    modal([el('h2', { text: 'Scout report (Learn level)' }), ...reportEl(sc.report),
      el('button', { class: 'primary', text: 'Tip off', onclick: () => { try { localStorage.setItem(seenKey('report'), '1'); } catch (e) { /* ignore */ } closeModal(); render(); } })]);
    return true;
  }
  return false;
}

function pickModal(side) {
  const sc = st.scout, needs = sc.needs[side];
  const mine = sc.teams[side], theirs = sc.teams[side === 'O' ? 'X' : 'O'];
  const sel = (id, label, prefix) => el('label', {}, [label + ' ', el('select', { id }, [1, 2, 3, 4, 5].map(n => el('option', { value: n, text: `${prefix}${n}` })))]);
  const parts = [el('h2', { text: `${side === 'O' ? 'Offence' : 'Defence'} (${mine}): your scouting call` }),
    el('p', { class: 'note', text: st.mode === 'hotseat' ? `${side === 'O' ? 'Defence' : 'Offence'}, look away. This stays private until the review.` : 'Private until the review.' }),
    ...reportEl(sc.report)];
  if (needs.includes('hunt')) parts.push(el('h3', { text: 'Hunt one matchup' }), el('div', { class: 'picker' }, [sel('pkHuntO', `Your attacker (${mine})`, 'O'), sel('pkHuntX', `v their defender (${theirs})`, 'X')]));
  if (needs.includes('protect')) parts.push(el('h3', { text: 'Protect one weakness' }), el('div', { class: 'picker' }, [sel('pkProtect', `Your defender (${mine})`, '#')]));
  parts.push(el('button', { class: 'primary', text: 'Save my call', onclick: async () => {
    const body = { code: G.code, token: G.token, side };
    if (needs.includes('hunt')) body.hunt = { o: Number($('pkHuntO').value), x: Number($('pkHuntX').value) };
    if (needs.includes('protect')) body.protect = { x: Number($('pkProtect').value) };
    try { const r = await api('/api/scout', body); closeModal(); st = r.state; render(); } catch (e) { alert(e.message); }
  } }));
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
  box.append(el('h4', { text: '4. Reflect' }), el('p', { text: 'Was your setup and plan the right one for these two teams? (Answer it with the feedback below.)' }));
}
