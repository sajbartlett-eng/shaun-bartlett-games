// Playmaker notation: the coach's whiteboard and hand-drawn basketball notation.
// One library draws the court, the pieces (Os and Xs) and every mark, so the live table, the step-through
// of the other side's turn and the phase diagrams all show the same thing. Nothing here decides a rule.
//
//   Notation (the conventions coaches draw):
//     a cut or movement without the ball   solid line, open arrowhead
//     a dribble                            zigzag line, open arrowhead
//     a pass                               dashed line, open arrowhead
//     a screen                             solid line ending in a short perpendicular bar (the T)
//     a shot                               solid line to the rim with a small ball on it
//     the ball carrier                     a double circle
//     a defender                           an X; its facing a small arrowhead on its edge
//     an intercept / steal / challenge     red marks at the point of contact; a slash when the ball is lost
//     a contest                            a red arc over the shooter (a hand up)
//   Offence marks are black ink, defence marks are red; each mark carries its turn number in a small circle.
'use strict';
window.PMNotation = (function () {
  const S = 36, PADX = 24, PADY = 20, COLS = 'ABCDEFGHIJKLMNOPQ';
  const DIRS = [[0, 1], [1, 1], [1, 0], [1, -1], [0, -1], [-1, -1], [-1, 0], [-1, 1]];
  const INK = '#1d1b18', RED = '#c0392b', NAVY = '#1f2a44', BOARD = '#fdfcf8';
  const WASH = { K: '#cfe8c8', '3': '#d9e4f5', M: '#fff0b3', L: '#fbd6c3', '.': BOARD };
  const ZLBL = { K: 'rim', '3': '3', M: 'mid', L: 'L2', '.': '' };
  const RIM = [8, 2];
  const px = x => PADX + (x + 1) * S, py = y => PADY + (14 - y) * S;
  const cx = x => px(x) + S / 2, cy = y => py(y) + S / 2;
  const W = PADX + 19 * S + 4, H = PADY + 15 * S + 22;

  const svg = (tag, attrs = {}, text) => {
    const e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (const [k, v] of Object.entries(attrs)) if (v != null && v !== false) e.setAttribute(k, v);
    if (text != null) e.textContent = text;
    return e;
  };
  const sqXY = q => [COLS.indexOf(q[0]), Number(q.slice(1))];
  const sqName = (x, y) => (x === -1 ? '@' : x === 17 ? 'R' : COLS[x]) + y;

  // ---- the hand-drawn look: a gentle displacement on strokes (never on text) ------------------------------
  let seed = 7;
  function defs(root, id) {
    const d = svg('defs');
    const f = svg('filter', { id: id || 'hand', x: '-5%', y: '-5%', width: '110%', height: '110%' });
    f.append(svg('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.035', numOctaves: 2, seed: seed++, result: 'n' }));
    f.append(svg('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale: 2.2, xChannelSelector: 'R', yChannelSelector: 'G' }));
    d.append(f);
    const pat = svg('pattern', { id: 'zhatch', width: 6, height: 6, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' });
    pat.append(svg('rect', { width: 6, height: 6, fill: 'rgba(31,42,68,0.05)' }));
    pat.append(svg('line', { x1: 0, y1: 0, x2: 0, y2: 6, stroke: 'rgba(31,42,68,0.34)', 'stroke-width': 1.4 }));
    const pat2 = svg('pattern', { id: 'zsprint', width: 8, height: 8, patternUnits: 'userSpaceOnUse', patternTransform: 'rotate(45)' });
    pat2.append(svg('line', { x1: 0, y1: 0, x2: 0, y2: 8, stroke: 'rgba(31,42,68,0.28)', 'stroke-width': 1.3 }));
    const pat3 = svg('pattern', { id: 'zscreen', width: 6, height: 6, patternUnits: 'userSpaceOnUse' });
    pat3.append(svg('path', { d: 'M0 3 H6 M3 0 V6', stroke: 'rgba(120,40,0,0.5)', 'stroke-width': 1.3 }));
    d.append(pat, pat2, pat3);
    root.append(d);
  }

  // ---- the court ------------------------------------------------------------------------------------------
  function court(root, zones, opts) {
    opts = opts || {};
    root.setAttribute('viewBox', `0 0 ${W} ${H}`);
    defs(root);
    root.append(svg('rect', { class: 'board', x: 0, y: 0, width: W, height: H, rx: 6, fill: BOARD }));
    const g = svg('g', { class: 'squares', 'aria-hidden': 'true' });
    for (let y = 1; y <= 14; y++) {
      for (let x = 0; x < 17; x++) {
        const z = zones[y - 1][x];
        g.append(svg('rect', { class: 'cell', x: px(x), y: py(y), width: S, height: S, fill: WASH[z], stroke: 'rgba(60,55,45,0.18)', 'stroke-width': 0.8 }));
        if (ZLBL[z] && !opts.plain) g.append(svg('text', { class: 'zonelbl', x: px(x) + 2.5, y: py(y) + 10 }, ZLBL[z]));
      }
    }
    root.append(g);
    if (opts.axes !== false) {
      const ax = svg('g', { class: 'axes', 'aria-hidden': 'true' });
      for (let y = 1; y <= 14; y++) ax.append(svg('text', { class: 'axis', x: 4, y: py(y) + S / 2 + 4 }, y));
      for (let x = 0; x < 17; x++) ax.append(svg('text', { class: 'axis', x: px(x) + S / 2 - 4, y: PADY - 5 }, COLS[x]));
      root.append(ax);
    }
    courtLines(root);
    root.append(svg('circle', { class: 'rim', cx: cx(RIM[0]), cy: cy(RIM[1]), r: 9, fill: 'none', stroke: '#c0392b', 'stroke-width': 3, filter: 'url(#hand)' }));
    return root;
  }

  // The printed board's lines, in marker: three-point line, the key, free-throw circle, backboard, half-court
  function courtLines(root) {
    const X = u => PADX + S + u * S, Y = v => PADY + v * S;
    const g = svg('g', { class: 'courtlines', 'aria-hidden': 'true', filter: 'url(#hand)' });
    const line = (u1, v1, u2, v2, extra) => g.append(svg('line', { x1: X(u1), y1: Y(v1), x2: X(u2), y2: Y(v2), ...(extra || {}) }));
    const a = 7.55, b = 5.05, cv = 10;
    g.append(svg('path', { d: `M ${X(8.5 - a)} ${Y(14)} L ${X(8.5 - a)} ${Y(cv)} A ${a * S} ${b * S} 0 0 1 ${X(8.5 + a)} ${Y(cv)} L ${X(8.5 + a)} ${Y(14)}` }));
    g.append(svg('path', { d: `M ${X(6)} ${Y(14)} L ${X(6)} ${Y(8)} L ${X(11)} ${Y(8)} L ${X(11)} ${Y(14)}` }));
    for (const v of [10, 11, 12]) { line(5.8, v, 6, v); line(11, v, 11.2, v); }
    g.append(svg('path', { d: `M ${X(6.5)} ${Y(8)} A ${2 * S} ${2 * S} 0 0 1 ${X(10.5)} ${Y(8)}` }));
    g.append(svg('path', { d: `M ${X(6.5)} ${Y(8)} A ${2 * S} ${2 * S} 0 0 0 ${X(10.5)} ${Y(8)}`, 'stroke-dasharray': '7 6' }));
    line(7.7, 13, 9.3, 13); line(8.5, 12.75, 8.5, 13);
    g.append(svg('path', { d: `M ${X(6.4)} ${Y(0)} A ${2.1 * S} ${2.1 * S} 0 0 0 ${X(10.6)} ${Y(0)}` }));
    root.append(g);
  }

  // ---- pieces ---------------------------------------------------------------------------------------------
  // An O: a marker circle with the number; the ball carrier gets the double circle (and a small ball).
  function pieceO(g, x, y, n, o) {
    o = o || {};
    const X = cx(x), Y = cy(y);
    g.append(svg('circle', { class: 'halo', cx: X, cy: Y, r: 21 }));
    if (o.ball) g.append(svg('circle', { class: 'ballring', cx: X, cy: Y, r: 17.5, fill: 'none', stroke: INK, 'stroke-width': 2, filter: 'url(#hand)' }));
    g.append(svg('circle', { class: 'ring', cx: X, cy: Y, r: 13.5, fill: '#fff', stroke: INK, 'stroke-width': 2.6, filter: 'url(#hand)' }));
    g.append(svg('text', { class: 'num', x: X, y: Y + 5.5, 'text-anchor': 'middle', 'aria-hidden': 'true' }, String(n)));
    if (o.ball) {
      g.append(svg('circle', { class: 'ball', cx: X + 14, cy: Y - 13, r: 6, fill: '#e07a1f', stroke: '#3a1d00', 'stroke-width': 2 }));
      g.append(svg('path', { d: `M${X + 8} ${Y - 13} H${X + 20} M${X + 14} ${Y - 19} V${Y - 7}`, stroke: '#3a1d00', 'stroke-width': 1, fill: 'none' }));
    }
    if (o.screen != null) screenBar(g, X, Y, o.screen, INK, 3.2);
  }
  // An X: two red marker strokes, the number on a small white disc at the crossing, its facing an arrowhead
  // on the edge (a wedge draws two).
  function pieceX(g, x, y, n, arrows, o) {
    o = o || {};
    const X = cx(x), Y = cy(y);
    g.append(svg('circle', { class: 'halo', cx: X, cy: Y, r: 21 }));
    const arms = svg('g', { filter: 'url(#hand)' });
    arms.append(svg('path', { class: 'xarms', d: `M${X - 13} ${Y - 13} L${X + 13} ${Y + 13} M${X - 13} ${Y + 13} L${X + 13} ${Y - 13}`, stroke: RED, 'stroke-width': 4.2, 'stroke-linecap': 'round', fill: 'none' }));
    g.append(arms);
    for (const a of (arrows || [])) {
      const d = DIRS[a], ux = d[0], uy = -d[1], len = Math.hypot(ux, uy);
      const r0 = 17, r1 = S / 2 + S / 4;
      const ax = X + ux / len * r0, ay = Y + uy / len * r0, bx = X + ux / len * r1, by = Y + uy / len * r1;
      const grp = svg('g', { class: 'facing', filter: 'url(#hand)' });
      grp.append(svg('line', { x1: ax, y1: ay, x2: bx, y2: by, stroke: RED, 'stroke-width': 3, 'stroke-linecap': 'round' }));
      chevron(grp, ax, ay, bx, by, RED, 7, 3);
      g.append(grp);
    }
    g.append(svg('circle', { class: 'xdisc', cx: X, cy: Y, r: 8.5, fill: '#fff', stroke: RED, 'stroke-width': 1.4 }));
    g.append(svg('text', { class: 'num xnum', x: X, y: Y + 4, 'text-anchor': 'middle', 'aria-hidden': 'true' }, String(n)));
  }
  function screenBar(g, X, Y, dir, ink, w) {
    const d = DIRS[dir], ux = d[0], uy = -d[1];
    const ex = X + ux * S * 0.66, ey = Y + uy * S * 0.66;
    const grp = svg('g', { class: 'screenmark', filter: 'url(#hand)' });
    grp.append(svg('line', { x1: X + ux * 15, y1: Y + uy * 15, x2: ex, y2: ey, stroke: ink, 'stroke-width': w, 'stroke-linecap': 'round' }));
    const nx = -uy, ny = ux;
    grp.append(svg('line', { x1: ex - nx * 10, y1: ey - ny * 10, x2: ex + nx * 10, y2: ey + ny * 10, stroke: ink, 'stroke-width': w, 'stroke-linecap': 'round' }));
    g.append(grp);
  }
  // Capacity tags (a used Move or Quick Step) and the lock, as small marker tags under the piece.
  function tags(g, x, y, b, locked, growth) {
    const X = cx(x), Y = cy(y);
    if (growth === 'early' || growth === 'late') {     // step 3l: a junior's growth tag, E or L, at the top left
      const tx = X - 23, ty = Y - 23;
      g.append(svg('rect', { class: 'growbadge ' + growth, x: tx, y: ty, width: 13, height: 13, rx: 6.5,
        fill: growth === 'early' ? '#1f6f3f' : '#7a4a12', stroke: '#fff', 'stroke-width': 1.2 }));
      g.append(svg('text', { x: tx + 6.5, y: ty + 10, 'text-anchor': 'middle', 'font-size': 9.5, 'font-weight': 'bold', fill: '#fff', 'aria-hidden': 'true' }, growth === 'early' ? 'E' : 'L'));
    }
    const marks = [];
    if (b && b.move) marks.push('M');
    if (b && b.qs) marks.push('Q');
    marks.forEach((m, k) => {
      const tx = X + 8 + k * 12, ty = Y + 7;
      g.append(svg('rect', { class: 'capbadge captag', x: tx, y: ty, width: 11, height: 11, rx: 2, fill: '#fff', stroke: INK, 'stroke-width': 1 }));
      g.append(svg('text', { x: tx + 5.5, y: ty + 8.8, 'text-anchor': 'middle', 'font-size': 8.5, 'font-weight': 'bold', fill: INK, 'aria-hidden': 'true' }, m));
      g.append(svg('line', { x1: tx + 1, y1: ty + 10, x2: tx + 10, y2: ty + 1, stroke: INK, 'stroke-width': 1.1 }));
    });
    if (locked) {
      g.append(svg('rect', { x: X - 22, y: Y + 7, width: 26, height: 12, rx: 3, fill: '#4a4a4a', stroke: INK, 'stroke-width': 1.2 }));
      g.append(svg('text', { x: X - 9, y: Y + 16.5, 'text-anchor': 'middle', 'font-size': 9, 'font-weight': 'bold', fill: '#fff', 'aria-hidden': 'true' }, 'LOCK'));
    }
  }

  // ---- marks ----------------------------------------------------------------------------------------------
  function chevron(g, ax, ay, bx, by, ink, size, w) {
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
    const nx = -uy, ny = ux;
    g.append(svg('path', { d: `M${bx - ux * size + nx * size * 0.8} ${by - uy * size + ny * size * 0.8} L${bx} ${by} L${bx - ux * size - nx * size * 0.8} ${by - uy * size - ny * size * 0.8}`,
      stroke: ink, 'stroke-width': w, fill: 'none', 'stroke-linecap': 'round', 'stroke-linejoin': 'round' }));
  }
  function zigzag(ax, ay, bx, by, amp, step) {
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, nx = -uy, ny = ux;
    let d = `M${ax} ${ay}`;
    const n = Math.max(2, Math.floor(len / step));
    for (let k = 1; k <= n; k++) {
      const t = k / n, sgn = k % 2 ? 1 : -1, a = k === n ? 0 : amp * sgn;
      d += ` L${ax + dx * t + nx * a} ${ay + dy * t + ny * a}`;
    }
    return d;
  }
  // the end points: from the edge of the piece to just short of the target
  function ends(ax, ay, bx, by, r0, r1) {
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
    return [ax + ux * r0, ay + uy * r0, bx - ux * r1, by - uy * r1];
  }
  let TAG = 1;                        // the turn tags' size (diagrams draw them a little larger than the live board)
  let placedTags = [];                // where tags have gone, so a new one that would land on another nudges aside
  function numberTag(g, x, y, n, ink) {
    const r = 7.5 * TAG, min = 2.1 * r;
    // first the spot asked for, then a ring of eight around it, then a wider ring: the first that sits clear of
    // every other tag and of every piece (pieces carry their own keep-out radius) takes it
    const tries = [[0, 0]];
    for (const k of [1, 1.7]) for (const a of [-90, 90, 180, 0, -135, 45, -45, 135]) tries.push([Math.cos(a * Math.PI / 180) * min * k, Math.sin(a * Math.PI / 180) * min * k]);
    for (const [dx, dy] of tries) {
      if (!placedTags.some(([px0, py0, keep]) => Math.hypot(px0 - (x + dx), py0 - (y + dy)) < (keep || min))) { x += dx; y += dy; break; }
    }
    placedTags.push([x, y]);
    const grp = svg('g', { class: 'turnno' });
    grp.append(svg('circle', { cx: x, cy: y, r: 7.5 * TAG, fill: '#fff', stroke: ink, 'stroke-width': 1.4 * TAG }));
    grp.append(svg('text', { x, y: y + 3.6 * TAG, 'text-anchor': 'middle', 'font-size': 9.5 * TAG, 'font-weight': 'bold', fill: ink, 'aria-hidden': 'true' }, String(n)));
    g.append(grp);
  }
  function tagAlong(g, ax, ay, bx, by, n, ink, side) {
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len, nx = -uy, ny = ux;
    const t = len < 40 ? 0.5 : 0.62, off = 11 * (side || 1);
    numberTag(g, ax + dx * t + nx * off, ay + dy * t + ny * off, n, ink);
  }
  function glyphWait(g, X, Y, ink) {
    const grp = svg('g', { filter: 'url(#hand)' });
    grp.append(svg('path', { d: `M${X - 5} ${Y - 7} H${X + 5} L${X - 5} ${Y + 7} H${X + 5} Z`, stroke: ink, 'stroke-width': 1.8, fill: 'none', 'stroke-linejoin': 'round' }));
    g.append(grp);
  }

  // Draw a list of marks (feed entries' `mark` objects). opts.numbers: show turn numbers (default true).
  function marks(root, list, opts) {
    opts = opts || {};
    TAG = opts.tag || 1;
    placedTags = (opts.avoid || []).map(([x, y]) => [x, y, 14 + 7.5 * TAG + 1]);   // the pieces: a tag never sits on one
    const g = svg('g', { class: 'marks', 'aria-hidden': 'true' });
    const passLines = {};             // receiver square -> the pass line's end, so an intercept can slash it
    for (const m of list) {
      if (!m || !m.frm) continue;
      const ink = m.side === 'O' ? INK : RED;
      const [fx, fy] = sqXY(m.frm), ax = cx(fx), ay = cy(fy);
      const num = opts.numbers === false ? null : m.turn;
      const grp = svg('g', { class: `mark mark-${m.kind} side-${m.side}` });
      const strokes = svg('g', { filter: 'url(#hand)' });
      grp.append(strokes);
      const toXY = m.to ? sqXY(m.to) : null;
      const tgXY = m.target ? sqXY(m.target) : null;
      if (['move', 'qs', 'sprint'].includes(m.kind)) {
        if (m.to && m.to !== m.frm) {
          const [bx, by] = [cx(toXY[0]), cy(toXY[1])];
          const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 14, 10);
          strokes.append(svg('line', { x1, y1, x2, y2, stroke: ink, 'stroke-width': 2.8, 'stroke-linecap': 'round' }));
          chevron(strokes, x1, y1, x2, y2, ink, 9, 2.8);
          if (num != null) tagAlong(grp, x1, y1, x2, y2, num, ink);
        }
        if (m.side === 'X' && m.arrow_to != null && (m.arrow_to !== m.arrow_from || m.to === m.frm) && opts.facing !== false) {
          // the facing after the move: a small arrowhead at the destination, in the new direction
          const [ex, ey] = m.to && m.to !== m.frm ? [cx(toXY[0]), cy(toXY[1])] : [ax, ay];
          const d = DIRS[m.arrow_to], ux = d[0], uy = -d[1], len = Math.hypot(ux, uy);
          const r0 = 16, r1 = 27;
          strokes.append(svg('line', { x1: ex + ux / len * r0, y1: ey + uy / len * r0, x2: ex + ux / len * r1, y2: ey + uy / len * r1, stroke: ink, 'stroke-width': 2.6, 'stroke-linecap': 'round' }));
          chevron(strokes, ex + ux / len * r0, ey + uy / len * r0, ex + ux / len * r1, ey + uy / len * r1, ink, 7, 2.6);
          if (num != null && (!m.to || m.to === m.frm)) numberTag(grp, ex + ux / len * 34, ey + uy / len * 34, num, ink);
        }
      } else if (m.kind === 'pass' && tgXY) {
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 19, 17);
        strokes.append(svg('line', { x1, y1, x2, y2, stroke: ink, 'stroke-width': 2.6, 'stroke-dasharray': '8 6', 'stroke-linecap': 'round' }));
        chevron(strokes, x1, y1, x2, y2, ink, 9, 2.6);
        if (num != null) tagAlong(grp, x1, y1, x2, y2, num, ink);
        passLines[m.target] = [x1, y1, x2, y2];
        if (m.result === 'intercepted' || m.result === 'picked off') {
          const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
          strokes.append(svg('path', { d: `M${mx - 7} ${my + 9} L${mx + 7} ${my - 9}`, stroke: RED, 'stroke-width': 3, 'stroke-linecap': 'round' }));
        }
      } else if (m.kind === 'dribble' && tgXY) {
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 15, 20);
        strokes.append(svg('path', { d: zigzag(x1, y1, x2, y2, 5, 7), stroke: ink, 'stroke-width': 2.6, fill: 'none', 'stroke-linejoin': 'round', 'stroke-linecap': 'round' }));
        chevron(strokes, x1, y1, x2, y2, ink, 9, 2.6);
        if (num != null) tagAlong(grp, x1, y1, x2, y2, num, ink);
        if (m.result === 'lost') strokes.append(svg('path', { d: `M${x2 - 8} ${y2 + 8} L${x2 + 2} ${y2 - 10}`, stroke: RED, 'stroke-width': 3, 'stroke-linecap': 'round' }));
      } else if (m.kind === 'screen' && m.dir != null) {
        screenBar(grp, ax, ay, m.dir, ink, 3.2);
        const d = DIRS[m.dir], ux = d[0], uy = -d[1], nx = -uy, ny = ux;      // the tag sits beside the T bar
        if (num != null) numberTag(grp, ax + ux * S * 0.66 + nx * 16, ay + uy * S * 0.66 + ny * 16, num, ink);
      } else if ((m.kind === 'shot' || m.kind === 'forced_shot') && tgXY) {
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 19, 11);
        strokes.append(svg('line', { x1, y1, x2, y2, stroke: ink, 'stroke-width': 2.6, 'stroke-linecap': 'round' }));
        chevron(strokes, x1, y1, x2, y2, ink, 9, 2.6);
        const tx = x1 + (x2 - x1) * 0.42, ty = y1 + (y2 - y1) * 0.42;
        strokes.append(svg('circle', { cx: tx, cy: ty, r: 5, fill: '#fff', stroke: ink, 'stroke-width': 2 }));
        if (num != null) tagAlong(grp, x1, y1, x2, y2, num, ink, -1);
      } else if (m.kind === 'intercept') {
        // the red X at the point of contact; a slash across the pass when it was picked off
        strokes.append(svg('path', { d: `M${ax - 9} ${ay - 9} L${ax + 9} ${ay + 9} M${ax - 9} ${ay + 9} L${ax + 9} ${ay - 9}`, stroke: RED, 'stroke-width': 3.4, 'stroke-linecap': 'round', fill: 'none' }));
        if (m.result === 'picked off') strokes.append(svg('circle', { cx: ax, cy: ay, r: 14, fill: 'none', stroke: RED, 'stroke-width': 2.2 }));
        if (num != null) numberTag(grp, ax + 15, ay - 15, num, RED);
      } else if (m.kind === 'steal' && tgXY) {
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 16, 22);
        strokes.append(svg('line', { x1, y1, x2, y2, stroke: RED, 'stroke-width': 2.6, 'stroke-linecap': 'round' }));
        strokes.append(svg('circle', { cx: x2, cy: y2, r: 6, fill: 'none', stroke: RED, 'stroke-width': 2.2 }));
        if (m.result === 'stolen') strokes.append(svg('path', { d: `M${x2 - 8} ${y2 + 8} L${x2 + 8} ${y2 - 8}`, stroke: RED, 'stroke-width': 3, 'stroke-linecap': 'round' }));
        if (m.result === 'foul') strokes.append(svg('path', { d: `M${x2 - 7} ${y2 + 9} L${x2 + 7} ${y2 - 9} M${x2 - 7} ${y2 - 9} L${x2 + 7} ${y2 + 9}`, stroke: RED, 'stroke-width': 2, 'stroke-linecap': 'round' }));
        if (num != null) tagAlong(grp, x1, y1, x2, y2, num, RED);
      } else if (m.kind === 'challenge' && tgXY) {
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const [x1, y1, x2, y2] = ends(ax, ay, bx, by, 16, 20);
        strokes.append(svg('line', { x1, y1, x2, y2, stroke: RED, 'stroke-width': 2.6, 'stroke-linecap': 'round' }));
        const dx = x2 - x1, dy = y2 - y1, len = Math.hypot(dx, dy) || 1, nx = -dy / len, ny = dx / len;
        strokes.append(svg('line', { x1: x2 - nx * 9, y1: y2 - ny * 9, x2: x2 + nx * 9, y2: y2 + ny * 9, stroke: RED, 'stroke-width': 2.6, 'stroke-linecap': 'round' }));
        if (m.result === 'beaten') strokes.append(svg('path', { d: `M${x2 - 8} ${y2 + 8} L${x2 + 8} ${y2 - 8}`, stroke: RED, 'stroke-width': 3, 'stroke-linecap': 'round' }));
        if (num != null) tagAlong(grp, x1, y1, x2, y2, num, RED);
      } else if (m.kind === 'contest' && tgXY) {
        // a hand up: an arc over the shooter on the contester's side
        const [bx, by] = [cx(tgXY[0]), cy(tgXY[1])];
        const dx = ax - bx, dy = ay - by, len = Math.hypot(dx, dy) || 1, ux = dx / len, uy = dy / len;
        const r = 23, a0 = Math.atan2(uy, ux) - 0.95, a1 = Math.atan2(uy, ux) + 0.95;
        strokes.append(svg('path', { d: `M${bx + r * Math.cos(a0)} ${by + r * Math.sin(a0)} A${r} ${r} 0 0 1 ${bx + r * Math.cos(a1)} ${by + r * Math.sin(a1)}`, stroke: RED, 'stroke-width': 3, fill: 'none', 'stroke-linecap': 'round' }));
        if (num != null) numberTag(grp, bx + ux * 36, by + uy * 36, num, RED);
      } else if (m.kind === 'hesitate' || m.kind === 'pause') {
        glyphWait(grp, ax + 20, ay + 14, ink);
        if (num != null) numberTag(grp, ax + 32, ay + 24, num, ink);
      }
      g.append(grp);
    }
    root.append(g);
    return g;
  }

  // ---- a phase diagram: the board at the phase's start, every mark of the phase, turn numbers ----------------
  // start: {o: [{sq, ball, screen}], x: [{sq, arrow}]}; entries: the feed entries of the phase (with marks).
  function phaseDiagram(zones, start, entries, opts) {
    opts = opts || {};
    const root = svg('svg', { class: 'diagram', role: 'img', xmlns: 'http://www.w3.org/2000/svg' });
    court(root, zones, { axes: opts.axes !== false, plain: true });
    const marksList = entries.map(e => e.mark).filter(Boolean);
    // a pass that was picked off: the defence's intercept mark says so; mark the pass line too
    for (let k = 0; k < entries.length; k++) {
      const m = entries[k].mark;
      if (m && m.kind === 'pass' && m.result === 'in the air') {
        const nxt = entries.slice(k + 1).find(e => e.mark && ['intercept', 'pass', 'shot'].includes(e.mark.kind) || e.side === 'O' && e.kind !== 'end_turn');
        if (nxt && nxt.mark && nxt.mark.kind === 'intercept' && nxt.mark.result === 'picked off') m.result = 'picked off';
      }
    }
    const pg = svg('g', { class: 'pieces' });
    const arrowsMode = opts.arrowMode === 'wedge';
    start.o.forEach((p, i) => { const [x, y] = sqXY(p.sq); const g = svg('g', { class: 'piece' }); pieceO(g, x, y, i + 1, { ball: p.ball, screen: p.screen ? p.screen.dir : null }); pg.append(g); });
    start.x.forEach((p, i) => { const [x, y] = sqXY(p.sq); const g = svg('g', { class: 'piece' }); pieceX(g, x, y, i + 1, arrowsMode ? [p.arrow, (p.arrow + 1) % 8] : [p.arrow]); pg.append(g); });
    root.append(pg);
    const avoid = [...start.o, ...start.x].map(p => { const [x, y] = sqXY(p.sq); return [cx(x), cy(y)]; });
    marks(root, marksList, { numbers: true, tag: 1.25, avoid });
    if (opts.title) {
      root.setAttribute('viewBox', `0 -34 ${W} ${H + 34}`);
      root.append(svg('text', { class: 'dtitle', x: PADX, y: -12 }, opts.title));
      if (opts.subtitle) root.append(svg('text', { class: 'dsub', x: W - 6, y: -12, 'text-anchor': 'end' }, opts.subtitle));
    }
    const words = [];
    for (const e of entries) if (e.mark && e.text) words.push(`${e.side === 'O' ? 'Offence' : 'Defence'} turn ${e.turn}: ${e.text}`);
    root.setAttribute('aria-label', `${opts.title || 'Phase diagram'}. ${words.join('. ')}`);
    return root;
  }

  // ---- export: the SVG as a PNG (the styles the page gives it are copied inline so the file stands alone) --
  function toPng(svgEl, scale) {
    scale = scale || 2;
    const clone = svgEl.cloneNode(true);
    const css = `
      text { font-family: 'Kalam', 'Patrick Hand', 'Comic Sans MS', 'Segoe Print', cursive; }
      .zonelbl { font-size: 8.5px; fill: #5a554c; } .axis { font-size: 11px; fill: #5a554c; font-weight: 700; }
      .courtlines path, .courtlines line { fill: none; stroke: ${NAVY}; stroke-width: 2.6; stroke-linecap: round; }
      .num { font-size: 16px; font-weight: 700; fill: ${INK}; } .xnum { font-size: 11px; fill: ${RED}; }
      .dtitle { font-size: 19px; font-weight: 700; fill: ${INK}; } .dsub { font-size: 12px; fill: #5a554c; }
      .halo { fill: none; stroke: none; }`;
    const style = document.createElementNS('http://www.w3.org/2000/svg', 'style'); style.textContent = css;
    clone.insertBefore(style, clone.firstChild);
    const vb = (clone.getAttribute('viewBox') || `0 0 ${W} ${H}`).split(' ').map(Number);
    clone.setAttribute('width', vb[2]); clone.setAttribute('height', vb[3]);
    const xml = new XMLSerializer().serializeToString(clone);
    const url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }));
    return new Promise((res, rej) => {
      const img = new Image();
      img.onload = () => {
        const c = document.createElement('canvas'); c.width = vb[2] * scale; c.height = vb[3] * scale;
        const ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, c.width, c.height);
        ctx.drawImage(img, 0, 0, c.width, c.height); URL.revokeObjectURL(url);
        c.toBlob(b => (b ? res(b) : rej(new Error('no image'))), 'image/png');
      };
      img.onerror = () => { URL.revokeObjectURL(url); rej(new Error('could not render the diagram')); };
      img.src = url;
    });
  }

  return { S, PADX, PADY, COLS, DIRS, W, H, INK, RED, NAVY, WASH, px, py, cx, cy, sqXY, sqName, svg, court, defs,
    pieceO, pieceX, tags, screenBar, marks, phaseDiagram, toPng };
})();
