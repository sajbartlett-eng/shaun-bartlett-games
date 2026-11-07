// Coach Vision and the Referee: the two voices of Playmaker. The coach teaches reads (scouting, goals,
// mismatches, shot quality); the referee makes the calls (rolls, fouls, turnovers, the clock). They write; nothing is spoken. The guided rules course is a sequence of lessons, each
// with a whiteboard drawn by the notation library. Nothing here decides a rule.
'use strict';
window.PMCoach = (function () {
  const PM = window.PMNotation;
  const el = (tag, attrs = {}, kids = []) => {
    const e = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (v == null || v === false) continue;
      if (k === 'class') e.className = v; else if (k === 'text') e.textContent = v;
      else if (k.startsWith('on')) e.addEventListener(k.slice(2), v); else e.setAttribute(k, v);
    }
    for (const k of [].concat(kids)) if (k != null) e.append(k);
    return e;
  };
  const svg = PM.svg;

  // ---- the characters (inline SVG, marker style) ----------------------------------------------------------
  function avatar(who, size) {
    size = size || 84;
    const g = svg('svg', { viewBox: '0 0 100 100', width: size, height: size, class: 'avatar avatar-' + who, 'aria-hidden': 'true', focusable: 'false' });
    const defs = svg('defs');
    const f = svg('filter', { id: 'av-' + who, x: '-10%', y: '-10%', width: '120%', height: '120%' });
    f.append(svg('feTurbulence', { type: 'fractalNoise', baseFrequency: '0.04', numOctaves: 2, seed: who === 'coach' ? 3 : 9, result: 'n' }));
    f.append(svg('feDisplacementMap', { in: 'SourceGraphic', in2: 'n', scale: 1.6, xChannelSelector: 'R', yChannelSelector: 'G' }));
    defs.append(f); g.append(defs);
    const ink = '#1d1b18', skin = who === 'coach' ? '#e8b48a' : '#c98a5e';
    const body = svg('g', { filter: `url(#av-${who})`, stroke: ink, 'stroke-width': 2.4, 'stroke-linecap': 'round', 'stroke-linejoin': 'round' });
    if (who === 'coach') {
      // Coach Vision: a cap, big round glasses, a whistle, a clipboard
      body.append(svg('path', { d: 'M22 100 Q22 72 50 70 Q78 72 78 100 Z', fill: '#1f2a44' }));                 // tracksuit top
      body.append(svg('path', { d: 'M36 82 L26 100 M64 82 L74 100', fill: 'none', stroke: '#fff', 'stroke-width': 1.6 }));
      body.append(svg('rect', { x: 60, y: 76, width: 24, height: 30, rx: 3, fill: '#d9b98a', transform: 'rotate(-12 72 91)' }));  // clipboard
      body.append(svg('rect', { x: 64, y: 73, width: 16, height: 6, rx: 2, fill: '#444', transform: 'rotate(-12 72 91)' }));
      body.append(svg('path', { d: 'M65 84 L79 84 M65 89 L79 89 M65 94 L75 94', stroke: '#1f2a44', 'stroke-width': 1.5, transform: 'rotate(-12 72 91)' }));
      body.append(svg('circle', { cx: 50, cy: 46, r: 21, fill: skin }));                                          // head
      body.append(svg('path', { d: 'M29 42 Q50 16 71 42 Z', fill: '#c0392b' }));                                   // cap
      body.append(svg('path', { d: 'M28 42 L78 42', stroke: '#c0392b', 'stroke-width': 5 }));
      body.append(svg('circle', { cx: 41, cy: 49, r: 7, fill: '#fff' })); body.append(svg('circle', { cx: 59, cy: 49, r: 7, fill: '#fff' }));  // glasses
      body.append(svg('path', { d: 'M48 49 L52 49 M34 47 L30 45 M66 47 L70 45', fill: 'none' }));
      body.append(svg('circle', { cx: 41, cy: 50, r: 2.2, fill: ink })); body.append(svg('circle', { cx: 59, cy: 50, r: 2.2, fill: ink }));
      body.append(svg('path', { d: 'M42 60 Q50 66 58 60', fill: 'none' }));                                         // smile
      body.append(svg('path', { d: 'M50 68 L50 80', fill: 'none', 'stroke-width': 1.6 }));                           // lanyard
      body.append(svg('path', { d: 'M46 80 h9 a4 4 0 0 1 0 8 h-6 a4 4 0 0 1 -3 -8 z', fill: '#f1c40f' }));            // whistle
    } else {
      // the Referee: a striped shirt, a cap, a whistle in the mouth, one arm up making the call
      body.append(svg('path', { d: 'M22 100 Q22 72 50 70 Q78 72 78 100 Z', fill: '#fff' }));
      for (const x of [30, 40, 50, 60, 70]) body.append(svg('path', { d: `M${x} 72 L${x - 2} 100`, stroke: ink, 'stroke-width': 4.5 }));
      body.append(svg('path', { d: 'M78 78 L92 50', stroke: skin, 'stroke-width': 7 }));                            // arm up
      body.append(svg('circle', { cx: 92, cy: 47, r: 5, fill: skin }));
      body.append(svg('circle', { cx: 50, cy: 46, r: 21, fill: skin }));
      body.append(svg('path', { d: 'M29 40 Q50 18 71 40 Z', fill: ink }));
      body.append(svg('path', { d: 'M28 40 L76 40', stroke: ink, 'stroke-width': 5 }));
      body.append(svg('circle', { cx: 42, cy: 49, r: 2.2, fill: ink })); body.append(svg('circle', { cx: 58, cy: 49, r: 2.2, fill: ink }));
      body.append(svg('path', { d: 'M37 44 L45 46 M63 44 L55 46', fill: 'none' }));                                    // a firm brow
      body.append(svg('path', { d: 'M44 61 h8 a3.5 3.5 0 0 1 0 7 h-5 a3.5 3.5 0 0 1 -3 -7 z', fill: '#1f2a44' }));   // whistle
    }
    g.append(body);
    return g;
  }

  // ---- no speech: the characters write, they don't talk ----------------------------------------------
  const speech = { on() { return false; }, set() {}, available() { return false; }, stop() {}, say() {} };

  // A character's line: avatar, name tag, the words in a bubble (also read to screen readers).
  function line(who, text, opts) {
    opts = opts || {};
    const name = who === 'coach' ? 'Coach Vision' : 'Referee';
    const box = el('div', { class: `speak speak-${who}` + (opts.compact ? ' compact' : '') }, [
      el('div', { class: 'speak-av' }, [avatar(who, opts.compact ? 48 : 84), el('div', { class: 'speak-name', text: name })]),
      el('div', { class: 'bubble', role: opts.live === false ? null : 'status', 'aria-live': opts.live === false ? null : 'polite' }, [el('p', { text })])]);
    return box;
  }

  // ---- the rules course -----------------------------------------------------------------------------------
  // Each lesson: who speaks, the words, and a whiteboard (pieces at squares; marks in notation).
  const DIRN = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const DIR = n => DIRN.indexOf(n);
  const O = (sq, extra) => Object.assign({ sq, ball: false, screen: null }, extra || {});
  const X = (sq, arrow) => ({ sq, arrow: typeof arrow === 'string' ? DIR(arrow) : arrow });
  const M = (kind, side, piece, frm, to, extra) => Object.assign({ kind, side, piece, frm, to, target: null, turn: 1, result: null }, extra || {});
  const SET = { o: [O('I11', { ball: true }), O('C9'), O('O9'), O('A3'), O('Q3')], x: [X('I10', 'N'), X('D8', 'NE'), X('N8', 'NW'), X('G4', 'N'), X('N4', 'N')] };

  const LESSONS = [
    { id: 'board', who: 'coach', title: 'The whiteboard',
      text: "Welcome to the clipboard. This is how coaches draw basketball: circles are our five, Xs are their five. The double circle has the ball. The court is squares, and the colours are shot zones: green at the rim, yellow mid-range, peach long twos, blue the three-point line. Every rule is decided on these squares.",
      board: SET },
    { id: 'tempo', who: 'ref', title: 'The clock and the tokens',
      text: "Here is how time works. The shot clock starts at 12 and each phase is two seconds. In a phase each side has six tokens, one per action. A turn is at most two actions, then the other side answers. Passing, screening, dribbling, shooting and hesitating end your turn; moving does not.",
      board: SET },
    { id: 'move', who: 'coach', title: 'Moving without the ball',
      text: "A Move goes up to three squares straight or two on the diagonal, once per player each phase. A Quick Step is a short burst, as many squares as the card says. A Sprint is a Move plus the Quick Step in one straight line. Solid lines with an arrowhead are cuts: here O2 cuts in and O4 lifts.",
      board: { o: SET.o, x: SET.x, marks: [M('move', 'O', 1, 'C9', 'E7'), M('qs', 'O', 3, 'A3', 'A5')] } },
    { id: 'arrows', who: 'coach', title: 'Defenders face one way',
      text: "Each X has an arrow: the way he is facing. It decides what he can contest, who he can steal from, and where he can jump a pass. The hatched squares are his reach along that arrow this phase. Read the arrows before every pass: a defender facing away from the lane is a defender who is not there.",
      board: { o: SET.o, x: [X('I10', 'N'), X('D8', 'E'), X('N8', 'NW'), X('G4', 'N'), X('N4', 'N')], reach: [['E8', 2], ['F8', 2], ['G8', 2], ['M9', 3], ['L10', 3], ['J10', 1], ['I9', 1]] } },
    { id: 'pass', who: 'coach', title: 'Passing and the lane',
      text: "A pass is a dashed line. Once you declare it, the pass line is fixed and the defence answers before it lands. A defender standing on the line can intercept, whatever he faces. One who can reach the line with a single straight movement along his arrow may jump the lane, then intercept. The squares next to you are safe: nobody intercepts there, though they can try a steal.",
      board: { o: SET.o, x: SET.x, marks: [M('pass', 'O', 0, 'I11', 'I11', { target: 'O9' }), M('move', 'X', 2, 'N8', 'L10', { arrow_from: 7, arrow_to: 7 }), M('intercept', 'X', 2, 'L10', 'L10', { target: 'O9', pass_from: 'I11' })] } },
    { id: 'pickoff', who: 'ref', title: 'The call on a pick-off',
      text: "When a defender intercepts, we roll. Pass rating against Intercept rating: the pass completes on a twenty-sided die roll at or under the difference. If it is picked off: minus five, the clock loses two seconds, the ball goes back to the passer and play goes on. In the last phase a pick-off ends the possession at nothing.",
      board: { o: SET.o, x: SET.x, marks: [M('pass', 'O', 0, 'I11', 'I11', { target: 'O9', result: 'picked off' }), M('intercept', 'X', 2, 'L10', 'L10', { target: 'O9', result: 'picked off' })] } },
    { id: 'dribble', who: 'coach', title: 'The dribble',
      text: "The zigzag is a dribble: you attack the defender in front of you. Your Dribble against his Agility. Win it and he is locked, frozen for the phase, and you may drive through his zone. Lose it and you are locked instead: no more dribbling, so pass or shoot.",
      board: { o: SET.o, x: SET.x, marks: [M('dribble', 'O', 0, 'I11', 'I11', { target: 'I10', result: 'won' })] } },
    { id: 'screen', who: 'coach', title: 'Screens',
      text: "A screen is a line ending in a bar, the T. The screener stands still and the T square blocks the defender from cutting through the corner. Set it as your first action, or second straight after your own Move; it ends your turn and holds until you move again. The defence can challenge it: his Challenge against your Screen rating.",
      board: { o: [O('I11', { ball: true }), O('J10', { screen: { dir: DIR('W') } }), O('O9'), O('A3'), O('Q3')], x: SET.x, marks: [M('screen', 'O', 1, 'J10', 'J10', { target: 'I10', dir: DIR('W') })] } },
    { id: 'shot', who: 'ref', title: 'Shots and the contest',
      text: "Declare a shot and the defence gets a reaction: up to two actions. Then one defender next to the shooter may contest. Facing the shooter, the contest is clean: the look is the points times the shot rating less the contest rating. Facing away, he risks a foul. We do not roll for makes; we score the quality of the look. Thirty or more is Excellent.",
      board: { o: SET.o, x: SET.x, marks: [M('shot', 'O', 0, 'I11', 'I11', { target: 'I2', shot: 'three' }), M('contest', 'X', 0, 'I10', 'I10', { target: 'I11' })] } },
    { id: 'steal', who: 'ref', title: 'Steals',
      text: "A defender next to the ball with his arrow on the carrier may try a steal. First a foul roll on his Foul rating: a foul gives the offence five, and a second one gives free throws. Then his Steal against the carrier's Dribble. Stolen: minus five and two seconds, and the ball stays with the carrier. On a declared shot a steal cancels the shot.",
      board: { o: SET.o, x: SET.x, marks: [M('steal', 'X', 0, 'I10', 'I10', { target: 'I11', result: 'stolen' })] } },
    { id: 'cards', who: 'coach', title: 'Scouting the cards',
      text: "Every player is a card. The triangles are what matters: up is above average, down is below. Scouting is finding the pairings where our up meets their down. Hunt that matchup. And find where their up meets our down, and protect it.",
      board: SET, cards: true },
    { id: 'goals', who: 'coach', title: 'Goals, mismatches, shot quality',
      text: "Good offence is a goal, not a guess. Pick a goal that creates a mismatch or an advantage, then build it: a screen to force a switch, a cut that catches the ball where no arrow can reach the lane, a drive that pulls the help and opens a shooter. Every step should raise the quality of the shot you end with.",
      board: { o: [O('J8', { ball: true }), O('C9'), O('O9'), O('A3'), O('L5')], x: [X('J7', 'N'), X('D8', 'NE'), X('N8', 'NW'), X('G4', 'N'), X('L4', 'N')],
        marks: [M('move', 'O', 4, 'L5', 'K7', { turn: 1 }), M('screen', 'O', 4, 'K7', 'K7', { target: 'J7', dir: DIR('W'), turn: 1 }), M('move', 'O', 0, 'J8', 'H6', { turn: 2 }), M('move', 'X', 4, 'L4', 'J6', { arrow_from: 0, arrow_to: 7, turn: 2 }), M('shot', 'O', 0, 'H6', 'H6', { target: 'I2', shot: 'mid', turn: 3 })] } },
    { id: 'story', who: 'coach', title: 'Reading the story',
      text: "At the end of every phase the whiteboard shows what happened: black for us, red for them, and each line carries its turn number, one for the first exchange, two for the second, and so on. Read it like a coach: where did the advantage come from, and did we cash it in?",
      board: { o: SET.o, x: SET.x, marks: [M('pass', 'O', 0, 'I11', 'I11', { target: 'C9', turn: 1 }), M('move', 'X', 1, 'D8', 'C8', { arrow_from: 1, arrow_to: 0, turn: 1 }), M('move', 'O', 2, 'O9', 'L11', { turn: 2 }), M('move', 'X', 2, 'N8', 'M10', { arrow_from: 7, arrow_to: 7, turn: 2 }), M('shot', 'O', 1, 'C9', 'C9', { target: 'I2', shot: 'three', turn: 3 }), M('contest', 'X', 1, 'C8', 'C8', { target: 'C9', turn: 3 })] } },
    { id: 'go', who: 'coach', title: 'Ready to play',
      text: "That is the game. Start against the computer at Rookie to practise your reads, or sit a friend down across the clipboard. I will be on the sideline with the scout report, and the referee makes every call. Let's play.",
      board: SET },
  ];

  const ZONES = (() => {   // the court's zones as the engine prints them (a copy for the course; the engine is the source)
    const rows = ['.................', '.................', '.................', '.................', '....333333333....', '..333LLLLLLL333..', '.33LLLLLLLLLLL33.',
      '33LLLMMMMMMMLLL33', '3LLLMMMMMMMMMLLL3', '3LLMMMMMMMMMMMLL3', '3LLMMMKKKKKMMMLL3', '3LLMMMKKKKKMMMLL3', '3LLMMMKKKKKMMMLL3', '.................'];
    return rows.slice().reverse().map(r => r.split(''));
  })();

  function board(lesson) {
    const b = lesson.board;
    const root = svg('svg', { class: 'diagram lesson', role: 'img', 'aria-label': lesson.title + ' diagram' });
    PM.court(root, ZONES, { axes: true });
    const pg = svg('g');
    b.o.forEach((p, i) => { const [x, y] = PM.sqXY(p.sq); const g = svg('g', { class: 'piece' }); PM.pieceO(g, x, y, i + 1, { ball: p.ball, screen: p.screen ? p.screen.dir : null }); pg.append(g); });
    b.x.forEach((p, i) => { const [x, y] = PM.sqXY(p.sq); const g = svg('g', { class: 'piece' }); PM.pieceX(g, x, y, i + 1, [p.arrow]); pg.append(g); });
    if (b.reach) {                   // a defender's reach along his arrow, as the live board hatches it
      const g = svg('g', { 'aria-hidden': 'true' });
      for (const [sq, n] of b.reach) {
        const [x, y] = PM.sqXY(sq);
        g.append(svg('rect', { x: PM.px(x) + 1, y: PM.py(y) + 1, width: PM.S - 2, height: PM.S - 2, fill: 'url(#zhatch)', stroke: 'rgba(31,42,68,0.45)', 'stroke-width': 1 }));
        g.append(svg('text', { class: 'zonenum', x: PM.px(x) + 3, y: PM.py(y) + PM.S - 4 }, String(n)));
      }
      root.append(g);
    }
    root.append(pg);
    if (b.marks) PM.marks(root, b.marks, { numbers: true });
    return root;
  }

  // Mount the course into a container; onDone is called when the learner finishes or skips.
  function course(container, opts) {
    opts = opts || {};
    let k = opts.start || 0;
    container.innerHTML = '';
    const box = el('section', { class: 'course', role: 'dialog', 'aria-modal': 'true', 'aria-labelledby': 'courseTitle' });
    container.append(box);
    function show() {
      const L = LESSONS[k];
      box.innerHTML = '';
      box.append(el('div', { class: 'course-head' }, [el('h2', { id: 'courseTitle', text: `${k + 1}. ${L.title}` }), el('span', { class: 'course-count', text: `${k + 1} of ${LESSONS.length}` })]));
      box.append(el('div', { class: 'course-body' }, [line(L.who, L.text), el('div', { class: 'course-board diagrambox' }, [board(L)])]));
      if (L.cards && opts.cardsEl) box.append(opts.cardsEl());
      box.append(el('div', { class: 'course-nav' }, [
        el('button', { text: 'Back', disabled: k === 0 ? 'disabled' : null, onclick: () => { k = Math.max(0, k - 1); show(); } }),
        el('button', { class: 'primary', id: 'courseNext', text: k === LESSONS.length - 1 ? 'Finish' : 'Next', onclick: () => { if (k === LESSONS.length - 1) finish(); else { k += 1; show(); } } }),
        el('button', { text: 'Skip the course', onclick: finish })]));
      const n = box.querySelector('#courseNext'); if (n) n.focus({ preventScroll: true });
      try { localStorage.setItem('pm_course_at', String(k)); } catch (e) { /* ignore */ }
    }
    function finish() { speech.stop(); document.removeEventListener('keydown', keys); try { localStorage.setItem('pm_course_done', '1'); } catch (e) { /* ignore */ } if (opts.onDone) opts.onDone(); }
    function keys(e) {
      if (e.key === 'ArrowRight') { if (k < LESSONS.length - 1) { k += 1; show(); } else finish(); }
      else if (e.key === 'ArrowLeft') { if (k > 0) { k -= 1; show(); } }
      else if (e.key === 'Escape') finish();
    }
    document.addEventListener('keydown', keys);
    show();
    return { show, finish };
  }

  return { avatar, speech, line, course, LESSONS, board, ZONES };
})();
