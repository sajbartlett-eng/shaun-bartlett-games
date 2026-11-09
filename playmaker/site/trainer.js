// Step 3m Part D, in the page: the possession summary, "Why?", the trainer profile and the head-to-head page.
// Facts and replays only; nothing during play except Learn mode's "Your goal this turn".
'use strict';
const PMTrainer = (() => {
  const h = (tag, attrs, kids) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (k === 'text') e.textContent = v; else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else if (v !== null && v !== undefined) e.setAttribute(k, v);
    }
    for (const c of [].concat(kids || [])) if (c !== null && c !== undefined) e.append(c.nodeType ? c : document.createTextNode(String(c)));
    return e;
  };
  const OFF = ['shot selection', 'clock use', 'passing risk', 'drives', 'off-ball movement and spacing', 'timing and disguise', 'screens'];
  const DEF = ['on-ball containment', 'help and rotation', 'closeouts and contests', 'steal and intercept decisions'];
  const SETUP = ['offence setup', 'defence setup'];
  const median = xs => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

  // the skill table (D6), the same numbers the Python trainer gives
  function skills(groups, last) {
    let gs = groups;
    if (last) { const ids = [...new Set(groups.map(g => g.match))]; const keep = new Set(ids.slice(-last)); gs = groups.filter(g => keep.has(g.match)); }
    const rows = {};
    for (const g of gs) for (const c of g.categories) (rows[c] = rows[c] || []).push(g);
    const out = {};
    for (const [c, xs] of Object.entries(rows)) {
      const losses = xs.map(g => g.loss), half = xs.length >> 1;
      out[c] = { n: xs.length, median: median(losses), best: xs.filter(g => g.loss <= 1e-9).length / xs.length,
        indirect: xs.reduce((a, g) => a + (g.indirect || 0), 0), trend: half >= 1 ? median(losses.slice(half)) - median(losses.slice(0, half)) : 0 };
    }
    return out;
  }
  function weakest(groups) {
    const t = skills(groups, 10); let w = null;
    for (const [c, r] of Object.entries(t)) if (r.n >= 3 && (!w || r.median > t[w].median)) w = c;
    return w;
  }
  // the All-Star's scouting of a human (B8): completed stored games only
  function scouting(groups, games) {
    if (!groups.length) return null;
    const off = groups.filter(g => g.side === 'O'), def = groups.filter(g => g.side === 'X');
    const shots = off.filter(g => g.categories.includes('shot selection'));
    const passes = off.filter(g => g.categories.includes('passing risk'));
    const kind = t => (t.match(/ (Move|Quick Step|Sprint|Pass|Shot|Dribble|Screen|Hesitate|End turn|Steal|Intercept|Challenge|Pause)/) || [])[1];
    const KIND = { 'Move': 'move', 'Quick Step': 'qs', 'Sprint': 'sprint', 'Pass': 'pass', 'Shot': 'shot', 'Dribble': 'dribble', 'Screen': 'screen', 'Hesitate': 'hesitate', 'End turn': 'end_turn', 'Steal': 'steal', 'Intercept': 'intercept', 'Challenge': 'challenge', 'Pause': 'pause' };
    const habit = {};
    for (const [side, gs] of [['O', off], ['X', def]]) {
      const c = {}; for (const g of gs) { const k = KIND[kind(g.first)]; if (k) c[k] = (c[k] || 0) + 1; }
      const top = Object.entries(c).sort((a, b) => b[1] - a[1])[0]; if (top) habit[`play/${side}`] = top[0];
    }
    return { games, early_shot: shots.length ? shots.filter(g => (g.phase || 9) <= 2).length / shots.length : null,
      pass_risk: passes.length ? passes.filter(g => (g.turnover || 0) > 0.2).length / passes.length : null,
      drive: off.length ? off.filter(g => g.categories.includes('drives')).length / off.length : null,
      help: def.length ? def.filter(g => g.categories.includes('help and rotation')).length / def.length : null,
      habit, weight: 0.3 };
  }

  // ---- the possession summary (D5): the best decision first, then at most two needs, each with its replay
  function summaryEl(read, player, onWhy) {
    const p = read && read.players && read.players[player];
    if (!p) return null;
    const pts = p.summary || [];
    // step 3n J: accuracy in words, the bands as words, the format named (K3)
    const BAND = { best: 'best', good: 'slip', inaccuracy: 'slip', mistake: 'mistake', blunder: 'big mistake' };
    const tally = {};
    for (const g of p.groups || []) { const w = BAND[g.grade.band] || 'slip'; tally[w] = (tally[w] || 0) + 1; }
    const order = ['best', 'slip', 'mistake', 'big mistake'];
    const bands = order.filter(w => tally[w]).map(w => `${tally[w]} ${w}${tally[w] > 1 && w !== 'best' ? 's' : ''}`).join(', ');
    const fmt = read.format === 'digital' ? 'Digital game' : 'Tabletop game';
    return h('section', { class: 'trainersum', 'aria-label': `Trainer: possession ${read.possession}` }, [
      h('h3', { text: `Trainer · possession ${read.possession} · ${fmt}` }),
      h('p', { class: 'acc', text: `Decisions: ${Math.round(p.accuracy)}% as good as the best available.` }),
      bands ? h('p', { class: 'note', text: `Your decisions: ${bands}.` }) : null,
      h('ol', {}, pts.map(x => h('li', { class: x.kind }, [h('span', { text: x.text }), ' ',
        h('button', { class: 'small', type: 'button', text: x.kind === 'need' ? 'Replay the better option' : 'Why?', onclick: () => onWhy(read.possession, x.group, player) })]))),
      (read.labels || []).length ? h('p', { class: 'note', text: 'Recognised: ' + [...new Set(read.labels.map(l => l.label))].join(', ') + '.' }) : null]);
  }

  // ---- "Why?" (D5): goals, credits, the defence's reply and the better option, with the board
  function boardEl(enc, better, betterText) {
    const m = /\|O([^|]+)\|X([^|]+)\|b(\d)/.exec(enc || '');
    if (!m) return null;
    const NS = 'http://www.w3.org/2000/svg', svg = document.createElementNS(NS, 'svg');
    const W = 17, H = 14, S = 22;
    svg.setAttribute('viewBox', `0 0 ${W * S + 10} ${H * S + 10}`); svg.setAttribute('class', 'whyboard'); svg.setAttribute('role', 'img');
    const col = c => 'ABCDEFGHIJKLMNOPQ'.indexOf(c);
    const at = q => [5 + (col(q[0]) + 0.5) * S, 5 + (H - Number(q.slice(1)) + 0.5) * S];
    const add = (tag, a) => { const e = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(a)) e.setAttribute(k, v); svg.append(e); return e; };
    add('rect', { x: 5, y: 5, width: W * S, height: H * S, fill: '#fdfcf8', stroke: '#c9c2b3' });
    add('circle', { cx: at('I2')[0], cy: at('I2')[1], r: 7, fill: 'none', stroke: '#c0392b', 'stroke-width': 2 });
    const os = m[1].split(','), xs = m[2].split(',').map(t => t.replace(/[NESW]+$/, '')), ball = Number(m[3]) - 1;
    const labels = [];
    os.forEach((q, i) => { const [x, y] = at(q); add('circle', { cx: x, cy: y, r: 8, fill: '#fff', stroke: '#1d1b18', 'stroke-width': i === ball ? 3 : 1.5 }); const t = add('text', { x, y: y + 4, 'text-anchor': 'middle', 'font-size': 10 }); t.textContent = i + 1; labels.push(`O${i + 1} ${q}`); });
    xs.forEach((q, i) => { const [x, y] = at(q); add('path', { d: `M${x - 6} ${y - 6} L${x + 6} ${y + 6} M${x - 6} ${y + 6} L${x + 6} ${y - 6}`, stroke: '#c0392b', 'stroke-width': 2.4 }); labels.push(`X${i + 1} ${q}`); });
    for (const a of better || []) {
      const mv = /^([OX])(\d) (?:Move|Quick Step|Sprint) to ([A-Q]\d+)/.exec(a);
      if (mv) { const from = at((mv[1] === 'O' ? os : xs)[Number(mv[2]) - 1]), to = at(mv[3]); add('line', { x1: from[0], y1: from[1], x2: to[0], y2: to[1], stroke: '#0b2a5b', 'stroke-width': 2.5, 'stroke-dasharray': '5 3' }); }
      const ps = /^O(\d) Pass to O(\d)/.exec(a);
      if (ps) { const from = at(os[Number(ps[1]) - 1]), to = at(os[Number(ps[2]) - 1]); add('line', { x1: from[0], y1: from[1], x2: to[0], y2: to[1], stroke: '#1d6b2a', 'stroke-width': 2 }); }
    }
    svg.setAttribute('aria-label', `The board before your decision: ${labels.join(', ')}. ${betterText ? 'Dashed: the better option. ' + betterText + '.' : ''}`);
    return svg;
  }
  function whyEl(w) {
    // step 3n J: the play in sentences, whole game points, a change signed, never a code string
    const g = w.group, gr = g.grade;
    const pts = v => String(Math.round(v)), more = v => (Math.round(Math.abs(v)) === 0 ? 'about the same' : `worth ${Math.round(Math.abs(v))} more`);
    const signed = v => { const n = Math.round(v); return n === 0 ? 'no change' : (n > 0 ? '+' : '') + n; };
    const effects = (w.credits || g.credits || []);
    return [h('h2', { text: `Why? Your decision ${g.group + 1}` }),
      boardEl(g.before, gr.better, g.better_text),
      h('p', {}, [h('strong', { text: 'You played: ' }), `${g.actions_text || ''}. After the defence answered, the best look was worth ${pts(gr.value)}.`]),
      gr.better ? h('p', {}, [h('strong', { text: 'Better: ' }), `${g.better_text || ''}: ${gr.side === 'O' ? more(gr.loss) : Math.round(gr.loss) + ' fewer points for the offence'}.`])
        : h('p', { text: 'That was the best option available.' }),
      w.goal && w.goal.yours ? h('p', { text: `You were going for: ${w.goal.yours}.` + (w.goal.same ? ' That was the best aim.' : (w.goal.best ? ` The best aim was: ${w.goal.best}.` : '')) })
        : (w.goal && w.goal.best ? h('p', { text: `The best aim here: ${w.goal.best}.` }) : null),
      w.reply_text ? h('p', { text: `The defence's best answer: ${w.reply_text}.` }) : null,
      effects.length ? h('table', { class: 'credits' }, [h('caption', { text: 'What each action did' }),
        h('tr', {}, ['Action', 'Effect', 'Your own look', 'Space for teammates', 'Risk', 'Defender who answered'].map(t => h('th', { text: t }))),
        ...effects.map(c => h('tr', {}, [c.action_text || c.action, signed(c.phi), signed(c.direct), signed(c.indirect), signed(c.risk),
          c.moved === null || c.moved === undefined ? '' : `X${c.moved + 1}`].map(t => h('td', { text: String(t) }))))]) : null,
      ...((w.flags || g.flags || []).map(f => h('p', { class: 'flag ' + f.kind, text: f.text }))),
      g.reveal ? h('p', { class: 'flag timing', text: `In the other order: ${more(g.reveal.reveal)}.` }) : null];
  }

  // ---- the trainer profile (D6) and head to head (C3)
  function catTable(title, cats, t) {
    // step 3n J: player language: how often, what it typically cost, how often the best choice, the space made
    return h('table', { class: 'skills' }, [h('caption', { text: title }), h('tr', {}, ['Situation', 'Times', 'Typical cost', 'Best choice', 'Space created for teammates', 'Trend (better, steady, worse)'].map(x => h('th', { text: x }))),
      ...cats.map(c => { const r = t[c]; return h('tr', {}, [c, r ? r.n : 0, r ? `${Math.round(r.median)} point${Math.round(r.median) === 1 ? '' : 's'}` : '–', r ? `${Math.round(100 * r.best)}%` : '–', r ? String(Math.round(r.indirect)) : '–',
        r ? (r.trend < -0.1 ? 'better' : r.trend > 0.1 ? 'worse' : 'steady') : '–'].map(x => h('td', { text: String(x) }))); })]);
  }
  async function profileEl(pid) {
    const R = window.PMRecords, p = await R.profile(pid), gs = await R.groupsOf(pid), vc = await R.versusComputer(pid);
    const last = skills(gs, 10), all = skills(gs);
    const LV = { rookie: 'Rookie', starter: 'Starter', allstar: 'All-Star' };
    return [h('h2', { text: `${p.name}: trainer` }),
      h('p', { text: `Rating ${Math.round(p.rating)} (${p.rd > 110 ? 'still settling' : 'settled'}) · ${(p.scores || []).length} rated matches · ${gs.length} decisions read.` }),
      window.PM_practiseTabletop ? h('button', { class: 'small', type: 'button', text: 'Practise for the tabletop game', onclick: () => window.PM_practiseTabletop() }) : null,
      ...(p.suggestions || []).map(s => h('p', { class: 'flag ' + s.kind, text: s.kind === 'practice' ? `Practice: ${s.how} Why: ${s.why}` : s.text })),
      h('div', { class: 'tablewrap' }, [catTable('Offence, last 10 matches', OFF, last), catTable('Defence, last 10 matches', DEF, last), catTable('Setup, last 10 matches', SETUP, last)]),
      h('details', {}, [h('summary', { text: 'All time' }), h('div', { class: 'tablewrap' }, [catTable('Offence, all time', OFF, all), catTable('Defence, all time', DEF, all), catTable('Setup, all time', SETUP, all)])]),
      h('h3', { text: 'Against the computer' }),
      vc.length ? h('div', { class: 'tablewrap' }, [h('table', { class: 'skills' }, [h('tr', {}, ['Level', 'Age', 'Standard', 'Played', 'Won', 'Lost', 'Tied', 'Points for', 'Against'].map(x => h('th', { text: x }))),
        ...vc.map(r => h('tr', {}, [LV[r.level] || r.level, r.age, r.standard.replace('_', '-'), r.played, r.won, r.lost, r.tied, r.for, r.against].map(x => h('td', { text: String(x) }))))])])
        : h('p', { class: 'note', text: 'No finished matches against the computer yet.' })];
  }
  async function headToHeadEl(p1, p2) {
    const R = window.PMRecords, a = await R.profile(p1), b = await R.profile(p2), r = await R.headToHead(p1, p2);
    return [h('h2', { text: `${a.name} v ${b.name}` }),
      h('p', { class: 'h2hline', text: `${a.name} ${r.points[p1]} v ${b.name} ${r.points[p2]}` }),
      h('table', { class: 'skills' }, [h('tr', {}, ['', a.name, b.name].map(x => h('th', { text: x }))),
        h('tr', {}, ['Matches', r.matches, r.matches].map(x => h('td', { text: String(x) }))),
        h('tr', {}, ['Wins', r.wins[p1], r.wins[p2]].map(x => h('td', { text: String(x) }))),
        h('tr', {}, ['Total points', r.points[p1], r.points[p2]].map(x => h('td', { text: String(x) }))),
        h('tr', {}, ['Points per possession', r.ppp[p1].toFixed(1), r.ppp[p2].toFixed(1)].map(x => h('td', { text: String(x) })))]),
      r.ties ? h('p', { text: `Ties: ${r.ties}.` }) : null,
      h('h3', { text: 'Last 5' }),
      r.last.length ? h('ol', {}, r.last.map(m => h('li', { text: `${m.date.slice(0, 10)}: ${a.name} ${m[p1]} v ${b.name} ${m[p2]}${m.winner === 'tie' ? ' (tie)' : ''}` })))
        : h('p', { class: 'note', text: 'No finished matches between these two yet.' })];
  }
  return { skills, weakest, scouting, summaryEl, whyEl, boardEl, profileEl, headToHeadEl, OFF, DEF, SETUP };
})();
if (typeof window !== 'undefined') window.PMTrainer = PMTrainer;
