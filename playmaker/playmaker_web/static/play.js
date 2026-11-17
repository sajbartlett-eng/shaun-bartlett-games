// Step 19, stage 1 (Shaun, 17 Nov 2026): moving players and taking actions.
//
//   Tap a player: every square he can reach lights up at once, marked by the movement it takes (solid: Move,
//   dashed: Quick Step, dotted: Sprint). Tap a square: he shows there as a ghost, with his arrow. Confirm beside the
//   board, or tap the same square again. A defender's arrow turns by dragging round the ghost, or with the turn
//   buttons (45° a tap), or the arrow keys; only the directions the rules allow.
//   Turn-ending actions: tap the selected player again (a double-tap does the same), hold him, press A, or the
//   Actions button. The list opens under the board, never over it, with only what he can do now. Choose an action
//   (or tap its target on the board), then confirm the same way.
//   A tap that misses a small square snaps to the nearest legal target within a finger's reach; the ghost and the
//   confirm step catch a wrong snap. Keyboard: Tab to a player, Enter selects, the arrow keys move between his
//   squares, Enter places, Enter confirms, A opens his actions, Escape backs out one step.
//
// Everything here reads the engine's legal actions (state.legal); nothing decides a rule.
'use strict';
const MOVES = ['move', 'qs', 'sprint'];
const MOVE_ORDER = { move: 0, qs: 1, sprint: 2 };
const MOVE_WORD = { move: 'a Move', qs: 'a Quick Step', sprint: 'a Sprint' };
const SHOT_WORD = { layup: 'layup', dunk: 'dunk', post: 'post shot', floater: 'floater', mid: 'mid-range', long: 'long two', three: 'three' };
let pend = null;            // a move: {move: true, dest, use, arrow}; an action: {act}
let listOpen = false;       // the selected player's turn-ending actions
let cursor = null;          // the keyboard's square, [x, y]
let focusWant = null;       // what to focus after the court is drawn again: 'cursor', 'ghost', 'piece:O1'
let hits = [];              // every tappable thing on the court: {x, y, fn, r}
let tapAt = { key: null, t: 0 };

function confirmOn() { try { return localStorage.getItem('pm_confirm') !== '0'; } catch (e) { return true; } }
function playActive() { return !!(st && st.can_act && !st.placing && !replay && !['contest', 'forced', 'target', 'over'].includes(st.stage)); }
function playReset() { pend = null; listOpen = false; cursor = null; }

// ---- what the selected player can do --------------------------------------------------------------------------
function moveSquares(side, i) {
  const out = new Map();
  for (const a of pieceActs(side, i)) {
    if (!MOVES.includes(a.kind)) continue;
    const k = a.dest.join(',');
    if (!out.has(k)) out.set(k, { dest: a.dest, kinds: {} });
    (out.get(k).kinds[a.kind] = out.get(k).kinds[a.kind] || []).push(a);
  }
  for (const m of out.values()) m.primary = Object.keys(m.kinds).sort((p, q) => MOVE_ORDER[p] - MOVE_ORDER[q])[0];
  return out;
}
function enderActs(side, i) {
  const own = pieceActs(side, i).filter(a => !MOVES.includes(a.kind));
  const waits = myActs().filter(a => a.side === side && (a.kind === 'hesitate' || a.kind === 'pause'));
  return own.concat(waits);
}
function actLabel(a) {
  switch (a.kind) {
    case 'pass': return `Pass to O${a.target + 1}`;
    case 'dribble': return `Dribble past X${a.target + 1}`;
    case 'screen': return `Screen, T to the ${COMPASS[a.target]}`;
    case 'shot': return `Shot: ${SHOT_WORD[a.shot] || a.shot}`;
    case 'steal': return 'Steal the ball';
    case 'intercept': return 'Intercept the pass';
    case 'challenge': return `Challenge O${a.target + 1}'s screen`;
    case 'contest': return a.piece >= 0 ? 'Contest: go for the block' : 'No contest';
    case 'hesitate': return 'Hesitate';
    case 'pause': return 'Pause';
    default: return KIND_NAME[a.kind] || a.text;
  }
}
// where an action's target sits on the board (null: none, the action happens where he stands)
function actTarget(a) {
  if (a.kind === 'pass') { const r = st.o[a.target]; return [r.x, r.y]; }
  if (a.kind === 'dribble') { const x = st.x[a.target]; return [x.x, x.y]; }
  if (a.kind === 'challenge') { const o = st.o[a.target]; return [o.x, o.y]; }
  if (a.kind === 'screen') { const p = st.o[a.piece], d = DIRS[a.target]; return [p.x + d[0], p.y + d[1]]; }
  return null;
}
function selPiece() { return sel.side != null ? (sel.side === 'O' ? st.o : st.x)[sel.i] : null; }
function ghostArrows() {
  if (!pend || !pend.move || sel.side !== 'X') return [];
  const m = moveSquares(sel.side, sel.i).get(pend.dest.join(','));
  return m ? [...new Set((m.kinds[pend.use] || []).map(a => a.arrow))] : [];
}
window.PM_GHOST = () => pend && pend.move ? { sq: sqName(pend.dest[0], pend.dest[1]), arrow: pend.arrow, use: pend.use } : null;

// ---- choosing ---------------------------------------------------------------------------------------------------
function playSelect(side, i) {
  const again = sel.side === side && sel.i === i;
  const now = performance.now();
  if (again) {                                   // the second tap on the selected player: his actions
    if (pend) { pend = null; }
    listOpen = !listOpen && enderActs(side, i).length > 0;
    focusWant = listOpen ? 'list' : `piece:${side}${i + 1}`;
    announce(listOpen ? `${side}${i + 1}'s actions: ${enderActs(side, i).map(actLabel).join(', ')}. Choose one, or tap its target on the board.` : `${side}${i + 1}'s actions closed.`);
    render(); return;
  }
  sel = { side, i, kind: null, dest: null };
  compare = { side, i, k: 0 };
  playReset();
  tapAt = { key: side + i, t: now };
  focusWant = `piece:${side}${i + 1}`;
  const n = moveSquares(side, i).size, e = enderActs(side, i).length;
  render();
  announce(`${side}${i + 1} selected. ` + (n || e ? `${n} square${n === 1 ? '' : 's'} to move to${e ? `, ${e} action${e === 1 ? '' : 's'}` : ''}. ` +
    (n ? 'Arrow keys move between his squares, Enter places. ' : '') + (e ? 'Press A for his actions.' : '') : 'No legal action for this player now.'));
}
function placeGhost(dest, use) {
  const m = moveSquares(sel.side, sel.i).get(dest.join(','));
  if (!m) return;
  const same = pend && pend.move && pend.dest.join() === dest.join();
  if (same && !use) return playConfirm();          // the fast path: the same square again
  const u = use || m.primary;
  const p = selPiece();
  const allowed = sel.side === 'X' ? [...new Set(m.kinds[u].map(a => a.arrow))] : [];
  let arrow = sel.side === 'X' ? (allowed.includes(p.arrow) ? p.arrow : nearestArrow(p.arrow, allowed)) : null;
  if (same && pend.arrow != null && allowed.includes(pend.arrow)) arrow = pend.arrow;
  pend = { move: true, dest, use: u, arrow };
  listOpen = false; cursor = dest.slice();
  if (!confirmOn()) return playConfirm();
  focusWant = 'ghost';
  render();
  announce(`${sel.side}${sel.i + 1} to ${sqName(dest[0], dest[1])} by ${MOVE_WORD[u]}` + (arrow != null ? `, arrow ${COMPASS[arrow]}` : '') +
    `. ${allowed.length > 1 ? 'Arrow keys turn him. ' : ''}Press Enter to confirm, Escape to cancel.`);
}
function nearestArrow(cur, allowed) {
  if (!allowed.length) return cur;
  return allowed.slice().sort((a, b) => ringDist(cur, a) - ringDist(cur, b))[0];
}
function ringDist(a, b) { const d = Math.abs(a - b) % 8; return Math.min(d, 8 - d); }
function rotate(step) {
  const allowed = ghostArrows(); if (!pend || allowed.length < 2) return;
  let a = pend.arrow;
  for (let k = 0; k < 8; k++) { a = (a + step + 8) % 8; if (allowed.includes(a)) break; }
  pend.arrow = a; focusWant = 'ghost'; render();
  announce(`Arrow ${COMPASS[a]}.`);
}
function chooseAct(a) {
  if (pend && pend.act === a) return playConfirm();            // the same choice again: confirm
  pend = { act: a };
  if (!confirmOn()) return playConfirm();
  focusWant = 'confirm';
  render();
  const t = actTarget(a);
  announce(`${actLabel(a)}${t ? '' : ''}. ${a.roll && a.roll.length ? 'It goes to the dice. ' : ''}Press Enter to confirm, Escape to cancel.`);
}
function pendingAction() {
  if (!pend) return null;
  if (pend.act) return pend.act;
  const m = moveSquares(sel.side, sel.i).get(pend.dest.join(','));
  if (!m) return null;
  return m.kinds[pend.use].find(a => sel.side === 'O' || a.arrow === pend.arrow) || m.kinds[pend.use][0];
}
async function playConfirm() {
  const a = pendingAction(); if (!a) return;
  const keep = { side: sel.side, i: sel.i };
  const confirmed = confirmOn();
  playReset();
  await submit(a, { confirmed });
  // the same player stays selected while he still has something to do this turn
  if (st && st.can_act && !st.placing && !replay && $('modal').classList.contains('hidden') && pieceActs(keep.side, keep.i).length && st.side_to_act === keep.side) {
    sel = { side: keep.side, i: keep.i, kind: null, dest: null }; compare = { side: keep.side, i: keep.i, k: 0 };
    focusWant = `piece:${keep.side}${keep.i + 1}`; render();
  }
}
function playEscape() {
  if (!playActive() || sel.side == null) return false;
  if (pend) { pend = null; focusWant = cursor ? 'cursor' : `piece:${sel.side}${sel.i + 1}`; render(); announce('Cancelled.'); return true; }
  if (listOpen) { listOpen = false; focusWant = `piece:${sel.side}${sel.i + 1}`; render(); announce('Actions closed.'); return true; }
  if (cursor) { cursor = null; focusWant = `piece:${sel.side}${sel.i + 1}`; render(); return true; }
  const me = `${sel.side}${sel.i + 1}`;
  sel = { side: null }; compare = null; focusWant = `piece:${me}`; render(); announce('Nothing selected.');
  return true;
}

// ---- the board ---------------------------------------------------------------------------------------------------
function hit(x, y, fn, r) { hits.push({ x: px(x) + S / 2, y: py(y) + S / 2, fn, r: r || S * 0.62 }); }
function playDraw(c) {
  hits = [];
  if (!playActive()) return;
  for (const p of (st.side_to_act === 'X' ? st.x : st.o)) if (pieceActs(st.side_to_act, p.i).length) hit(p.x, p.y, () => playSelect(st.side_to_act, p.i), S * 0.72);
  if (sel.side == null || sel.side !== st.side_to_act) return;
  const p = selPiece();
  const squares = moveSquares(sel.side, sel.i);
  for (const m of squares.values()) {
    const [x, y] = m.dest, name = sqName(x, y);
    const onMe = x === p.x && y === p.y;
    const r = onMe ? svg('circle', { class: `target mv-${m.primary} ring-target`, cx: px(x) + S / 2, cy: py(y) + S / 2, r: 18, 'data-sq': name, tabindex: -1, role: 'button', 'pointer-events': 'all',
      'aria-label': `Turn on the spot on ${name}` })
      : svg('rect', { class: `target mv-${m.primary}`, x: px(x) + 3, y: py(y) + 3, width: S - 6, height: S - 6, rx: 5, 'data-sq': name, tabindex: -1, role: 'button',
        'aria-label': `${KIND_NAME[m.primary]} to ${name}` + (Object.keys(m.kinds).length > 1 ? ` (also ${Object.keys(m.kinds).filter(k => k !== m.primary).map(k => KIND_NAME[k]).join(', ')})` : '') });
    const go = () => { cursor = m.dest.slice(); placeGhost(m.dest); };
    r.addEventListener('click', e => { e.stopPropagation(); if (dragged) return; go(); });
    r.addEventListener('pointerdown', e => startDrag(e, m.dest));
    c.append(r);
    hit(x, y, go);
  }
  // D-104: a step a screen blocks shows greyed, with the reason (kept from the old flow)
  const blocked = sel.side === 'X' && st.screen_blocked && st.screen_blocked[sel.i] ? [].concat(...Object.values(st.screen_blocked[sel.i])) : [];
  const seenB = new Set();
  for (const q of blocked) {
    const k = q.x + ',' + q.y; if (seenB.has(k) || squares.has(k)) continue; seenB.add(k);
    const g = svg('g', { class: 'blocked-step', role: 'img', 'aria-label': `${sqName(q.x, q.y)}: Blocked by the screen` });
    g.append(svg('rect', { x: px(q.x) + 3, y: py(q.y) + 3, width: S - 6, height: S - 6, rx: 5, fill: '#9aa0a6', 'fill-opacity': 0.45, stroke: '#6b7075', 'stroke-dasharray': '3 3' }));
    const t = svg('title', {}); t.textContent = 'Blocked by the screen'; g.append(t);
    c.append(g);
  }
  if (listOpen || (pend && pend.act)) {
    for (const a of enderActs(sel.side, sel.i)) {
      const t = actTarget(a); if (!t) continue;
      if (pend && pend.act && pend.act !== a) continue;
      const onPiece = [...st.o, ...st.x].some(q => q.x === t[0] && q.y === t[1]);
      const r = onPiece ? svg('circle', { class: 'target ender-target ring-target', cx: px(t[0]) + S / 2, cy: py(t[1]) + S / 2, r: 18, tabindex: -1, role: 'button', 'aria-label': actLabel(a), 'pointer-events': 'all' })
        : svg('rect', { class: 'target ender-target', x: px(t[0]) + 3, y: py(t[1]) + 3, width: S - 6, height: S - 6, rx: 5, tabindex: -1, role: 'button', 'aria-label': actLabel(a) });
      r.addEventListener('click', e => { e.stopPropagation(); chooseAct(a); });
      c.append(r);
      hit(t[0], t[1], () => chooseAct(a), S * 0.72);
    }
  }
  if (pend && pend.act) drawActLine(c, pend.act);
  if (pend && pend.move) drawGhostMove(c);
  if (cursor && !(pend && pend.move)) {
    const name = sqName(cursor[0], cursor[1]), m = squares.get(cursor.join(','));
    c.append(svg('rect', { class: 'kcursor', id: 'kCursor', x: px(cursor[0]) + 1, y: py(cursor[1]) + 1, width: S - 2, height: S - 2, rx: 6, tabindex: -1, role: 'button',
      'aria-label': m ? `${name}: ${KIND_NAME[m.primary]}. Enter places him here.` : name }));
  }
}
function drawActLine(c, a) {
  const p = selPiece(), t = actTarget(a);
  const ax = px(p.x) + S / 2, ay = py(p.y) + S / 2;
  if (t) {
    const bx = px(t[0]) + S / 2, by = py(t[1]) + S / 2;
    c.append(svg('line', { class: 'pendline', x1: ax, y1: ay, x2: bx, y2: by, 'stroke-dasharray': a.kind === 'pass' ? '8 6' : '' }));
  } else if (a.kind === 'shot') {
    c.append(svg('line', { class: 'pendline', x1: ax, y1: ay, x2: px(8) + S / 2, y2: py(2) + S / 2 }));
  }
}
function drawGhostMove(c) {
  const p = selPiece(), [x, y] = pend.dest;
  const ax = px(p.x) + S / 2, ay = py(p.y) + S / 2, bx = px(x) + S / 2, by = py(y) + S / 2;
  if (p.x !== x || p.y !== y) c.append(svg('line', { class: 'pendline', x1: ax, y1: ay, x2: bx, y2: by }));
  const g = svg('g', { class: 'ghostpiece', id: 'ghostPiece', tabindex: -1, role: 'button',
    'aria-label': `Ghost: ${sel.side}${sel.i + 1} on ${sqName(x, y)}` + (pend.arrow != null ? `, arrow ${COMPASS[pend.arrow]}` : '') + '. Enter confirms. Drag round him to turn his arrow.' });
  // the directions the rules allow, faint, so a player sees where the arrow can go
  const allowed = ghostArrows();
  for (const d of allowed) {
    const [dx, dy] = DIRS[d], len = Math.hypot(dx, dy);
    g.append(svg('line', { class: 'allowdir', x1: bx + dx / len * 20, y1: by - dy / len * 20, x2: bx + dx / len * 30, y2: by - dy / len * 30 }));
  }
  if (sel.side === 'O') PM.pieceO(g, x, y, sel.i + 1, { ball: p.ball });
  else PM.pieceX(g, x, y, sel.i + 1, [pend.arrow]);
  g.addEventListener('click', e => { e.stopPropagation(); if (dragged) return; playConfirm(); });
  g.addEventListener('pointerdown', e => startDrag(e, pend.dest));
  c.append(g);
}

// ---- dragging the arrow round (a press on a lit square or on the ghost; a move of a few pixels starts it) -------
let drag = null, dragged = false;
function svgPoint(c, e) { const pt = c.createSVGPoint(); pt.x = e.clientX; pt.y = e.clientY; return pt.matrixTransform(c.getScreenCTM().inverse()); }
function startDrag(e, dest) {
  if (sel.side !== 'X') return;
  const c = $('court');
  drag = { dest, x0: e.clientX, y0: e.clientY, id: e.pointerId, on: false };
  dragged = false;
  c.setPointerCapture && c.setPointerCapture(e.pointerId);
}
function onDragMove(e) {
  if (!drag || e.pointerId !== drag.id) return;
  if (!drag.on && Math.hypot(e.clientX - drag.x0, e.clientY - drag.y0) < 10) return;
  if (!drag.on) {
    drag.on = true; dragged = true;
    if (!(pend && pend.move && pend.dest.join() === drag.dest.join())) {
      // place the ghost without acting, whatever the confirm setting: the release decides
      const m = moveSquares(sel.side, sel.i).get(drag.dest.join(','));
      const u = m.primary, allowed = [...new Set(m.kinds[u].map(a => a.arrow))];
      pend = { move: true, dest: drag.dest, use: u, arrow: nearestArrow(selPiece().arrow, allowed) };
      cursor = drag.dest.slice(); listOpen = false;
    }
  }
  const c = $('court'), q = svgPoint(c, e);
  const gx = px(pend.dest[0]) + S / 2, gy = py(pend.dest[1]) + S / 2;
  const ang = (Math.atan2(q.x - gx, gy - q.y) * 180 / Math.PI + 360) % 360;
  const want = Math.round(ang / 45) % 8, allowed = ghostArrows();
  const a = allowed.includes(want) ? want : nearestArrow(want, allowed);
  if (a !== pend.arrow) { pend.arrow = a; renderCourt(); }
}
function onDragEnd(e) {
  if (!drag || e.pointerId !== drag.id) return;
  const was = drag.on; drag = null;
  if (!was) return;
  setTimeout(() => { dragged = false; }, 0);
  if (!confirmOn()) { playConfirm(); return; }
  focusWant = 'ghost'; render();
  announce(`${sel.side}${sel.i + 1} to ${sqName(pend.dest[0], pend.dest[1])}, arrow ${COMPASS[pend.arrow]}. Press Enter or Confirm.`);
}

// ---- a tap that misses: the nearest legal target within a finger's reach --------------------------------------
function onCourtTap(e) {
  if (!playActive() || dragged) return;
  if (e.target.closest && e.target.closest('g.piece, .target, .ghostpiece')) return;
  const c = $('court'), q = svgPoint(c, e);
  let best = null, bd = Infinity;
  for (const h of hits) { const d = Math.hypot(h.x - q.x, h.y - q.y); if (d < h.r && d < bd) { bd = d; best = h; } }
  if (best) best.fn();
}

// ---- holding a player opens his actions ------------------------------------------------------------------------
let hold = null, held = false;
function onPieceDown(e) {
  const g = e.target.closest && e.target.closest('g.piece'); if (!g || !playActive()) return;
  const m = (g.getAttribute('aria-label') || '').match(/^([OX])(\d),/); if (!m) return;
  const side = m[1], i = Number(m[2]) - 1;
  if (side !== st.side_to_act || !pieceActs(side, i).length) return;
  held = false;
  hold = setTimeout(() => {
    hold = null; held = true;
    if (!(sel.side === side && sel.i === i)) { sel = { side, i, kind: null, dest: null }; compare = { side, i, k: 0 }; playReset(); }
    listOpen = enderActs(side, i).length > 0; pend = null; focusWant = 'list'; render();
    announce(`${side}${i + 1}'s actions: ${enderActs(side, i).map(actLabel).join(', ')}.`);
  }, 550);
}
function onPieceUp() { if (hold) { clearTimeout(hold); hold = null; } }

// ---- the keyboard on the board -------------------------------------------------------------------------------
function onCourtKey(e) {
  if (!playActive() || sel.side == null || sel.side !== st.side_to_act) return;
  const k = e.key;
  if (k === 'a' || k === 'A') {
    if (!enderActs(sel.side, sel.i).length) return;
    e.preventDefault(); listOpen = true; pend = null; focusWant = 'list'; render();
    announce(`${sel.side}${sel.i + 1}'s actions: ${enderActs(sel.side, sel.i).map(actLabel).join(', ')}.`); return;
  }
  const dirs = { ArrowUp: [0, 1], ArrowDown: [0, -1], ArrowRight: [1, 0], ArrowLeft: [-1, 0] };
  if (dirs[k]) {
    e.preventDefault();
    if (pend && pend.move && ghostArrows().length > 1) { rotate(k === 'ArrowRight' || k === 'ArrowUp' ? 1 : -1); return; }
    const squares = [...moveSquares(sel.side, sel.i).values()].map(m => m.dest);
    if (!squares.length) return;
    const p = selPiece(), from = cursor || [p.x, p.y], [dx, dy] = dirs[k];
    // the nearest legal square in that direction (ahead of the cursor, the straightest first)
    const ahead = squares.filter(q => (q[0] - from[0]) * dx + (q[1] - from[1]) * dy > 0);
    const pick = (ahead.length ? ahead : squares).slice().sort((a, b) => score(a) - score(b))[0];
    function score(q) { const along = (q[0] - from[0]) * dx + (q[1] - from[1]) * dy, side = Math.abs((q[0] - from[0]) * dy) + Math.abs((q[1] - from[1]) * dx); return along + 2 * side; }
    cursor = pick.slice(); pend = null; focusWant = 'cursor'; render();
    const m = moveSquares(sel.side, sel.i).get(cursor.join(','));
    announce(`${sqName(cursor[0], cursor[1])}: ${m ? KIND_NAME[m.primary] : ''}.`);
    return;
  }
  if (k === 'Enter' || k === ' ') {
    const onPiece = e.target.closest && e.target.closest('g.piece');
    if (onPiece && !cursor && !pend) return;           // the piece's own handler selects (or opens the actions)
    e.preventDefault(); e.stopPropagation();
    if (pend) { playConfirm(); return; }
    if (cursor && moveSquares(sel.side, sel.i).has(cursor.join(','))) placeGhost(cursor.slice());
  }
}

// ---- the bar under the board ------------------------------------------------------------------------------------
function renderPlayBar() {
  const bar = $('playBar'); if (!bar) return;
  bar.innerHTML = '';
  if (!st || !playActive()) { bar.classList.add('hidden'); return; }
  bar.classList.remove('hidden');
  const line = el('p', { class: 'playline', id: 'playLine' });
  bar.append(line);
  if (sel.side == null || sel.side !== st.side_to_act) {
    line.textContent = `Tap one of your players${isPhone() ? '' : ' (or Tab to him and press Enter)'}.`;
    return;
  }
  const p = selPiece(), me = `${sel.side}${sel.i + 1}`;
  const squares = moveSquares(sel.side, sel.i), enders = enderActs(sel.side, sel.i);
  const btns = el('div', { class: 'buttons playbtns' });
  if (pend && pend.move) {
    const m = squares.get(pend.dest.join(','));
    line.textContent = `${me} to ${sqName(pend.dest[0], pend.dest[1])} by ${MOVE_WORD[pend.use]}` + (pend.arrow != null ? `, arrow ${COMPASS[pend.arrow]}` : '') + '.';
    btns.append(el('button', { class: 'primary', id: 'confirmBtn', text: 'Confirm', onclick: playConfirm }));
    if (ghostArrows().length > 1) btns.append(
      el('button', { id: 'rotCcw', 'aria-label': 'Turn the arrow left 45 degrees', text: '⟲ Turn left', onclick: () => rotate(-1) }),
      el('button', { id: 'rotCw', 'aria-label': 'Turn the arrow right 45 degrees', text: 'Turn right ⟳', onclick: () => rotate(1) }));
    for (const k of Object.keys(m ? m.kinds : {}).filter(k => k !== pend.use).sort((a, b) => MOVE_ORDER[a] - MOVE_ORDER[b])) {
      btns.append(el('button', { class: 'small', text: `Use ${MOVE_WORD[k]} instead`, onclick: () => placeGhost(pend.dest, k) }));
    }
    btns.append(el('button', { id: 'cancelBtn', text: 'Cancel', onclick: () => { pend = null; focusWant = `piece:${me}`; render(); } }));
    bar.append(btns);
    bar.append(el('p', { class: 'note', text: 'Tap the same square again to confirm.' + (ghostArrows().length > 1 ? ' Drag round him to turn his arrow.' : '') }));
    return;
  }
  if (pend && pend.act) {
    const a = pend.act;
    line.textContent = actLabel(a) + '. Tap it again, or Confirm.';
    bar.append(actDetail(a));
    btns.append(el('button', { class: 'primary', id: 'confirmBtn', text: a.roll && a.roll.length ? 'Confirm and roll' : 'Confirm', onclick: playConfirm }),
      el('button', { id: 'cancelBtn', text: 'Cancel', onclick: () => { pend = null; listOpen = true; focusWant = 'list'; render(); } }));
    bar.append(btns);
    if (actTarget(a)) bar.append(el('p', { class: 'note', text: 'Or tap the target on the board again.' }));
    const list = el('div', { class: 'enderlist', id: 'enderList', role: 'group', 'aria-label': `${me}'s actions` });
    for (const b of enders) list.append(el('div', { class: 'enderrow' }, [el('button', { class: 'ender' + (b === a ? ' active' : ''), 'aria-pressed': b === a ? 'true' : 'false', 'data-act': actLabel(b), text: actLabel(b), onclick: () => chooseAct(b) }), actBrief(b)]));
    bar.append(list);
    return;
  }
  const kinds = new Set([...squares.values()].map(m => m.primary));
  line.textContent = `${me} (${p.card.role}) on ${p.sq}.` + (squares.size ? ' Tap a lit square to move him.' : '');
  if (enders.length) btns.append(el('button', { id: 'actionsBtn', 'aria-pressed': listOpen ? 'true' : 'false',
    text: listOpen ? 'Targets on the board: shown' : 'Show the targets on the board', onclick: () => playSelect(sel.side, sel.i) }));
  btns.append(el('button', { text: 'Clear', onclick: () => { sel = { side: null }; compare = null; playReset(); render(); } }));
  bar.append(btns);
  if (kinds.size) bar.append(el('p', { class: 'note legend', text: ['move', 'qs', 'sprint'].filter(k => kinds.has(k)).map(k => ({ move: 'Solid: Move', qs: 'Dashed: Quick Step', sprint: 'Dotted: Sprint' })[k]).join(' · ') +
    (enders.length && !listOpen ? ` · Tap him again${isPhone() ? ' or hold him' : ' or press A'} to put his actions' targets on the board.` : '') }));
  if (enders.length) {         // step 19: his turn-ending actions, under the board at once (one tap fewer than opening them first)
    const list = el('div', { class: 'enderlist', id: 'enderList', role: 'group', 'aria-label': `${me}'s actions` });
    list.append(el('p', { class: 'listhead', text: 'His actions (each ends the turn):' }));
    for (const a of enders) list.append(el('div', { class: 'enderrow' }, [el('button', { class: 'ender', 'data-act': actLabel(a), text: actLabel(a), onclick: () => chooseAct(a) }), actBrief(a)]));
    bar.append(list);
  }
}
// what the bar says under an action: filled in by stage 2 (the chance and the why); the dice text for now
function actBrief(a) { return window.PMAdvice ? PMAdvice.brief(a) : null; }
function actDetail(a) {
  if (window.PMAdvice) return PMAdvice.detail(a);
  return a.roll && a.roll.length ? el('ul', {}, a.roll.map(t => el('li', { text: t.text }))) : null;
}

// ---- focus after a redraw ------------------------------------------------------------------------------------
function playFocus() {
  const want = focusWant; focusWant = null;
  if (!want) return;
  let t = null;
  if (want === 'cursor') t = $('kCursor');
  else if (want === 'ghost') t = $('ghostPiece');
  else if (want === 'confirm') t = $('confirmBtn');
  else if (want === 'list') t = document.querySelector('#enderList button');
  else if (want.startsWith('piece:')) t = document.querySelector(`#court g.piece[aria-label^="${want.slice(6)},"]`);
  if (t) t.focus({ preventScroll: true });
}

(function installPlay() {
  const c = $('court'); if (!c) return;
  c.addEventListener('click', onCourtTap);
  c.addEventListener('pointermove', onDragMove);
  c.addEventListener('pointerup', onDragEnd);
  c.addEventListener('pointercancel', onDragEnd);
  c.addEventListener('pointerdown', onPieceDown);
  c.addEventListener('pointerup', onPieceUp);
  c.addEventListener('pointerleave', onPieceUp);
  c.addEventListener('keydown', onCourtKey);
  c.addEventListener('contextmenu', e => { if (held) e.preventDefault(); });
  // a click straight after a hold must not also toggle the list
  c.addEventListener('click', e => { if (held) { held = false; e.stopPropagation(); e.preventDefault(); } }, true);
})();
