// Step 3n Part A: the search core in JavaScript (rules, the board read, the leaf value, the search), a line-for-line
// port of the Python engine (playmaker_engine: board, actions, resolve, scoring, decide, search), which stays the
// reference. It covers the ruled settings (both formats); any other rule setting is refused and the Python engine
// plays instead. tools/js_equivalence.py proves the two give the same answers on random legal states.
'use strict';
const PMEngine = (() => {
  // ---- board ------------------------------------------------------------------------------------------------------
  // A square is an integer: (x + 20) * 64 + (y + 20), so comparing codes compares (x, y) as Python compares tuples.
  const W = 17, H = 14, RIMX = 8, RIMY = 2, OFF = 20, WID = 64, NSQ = WID * WID;
  const SX = new Int8Array(NSQ), SY = new Int8Array(NSQ), ONB = new Uint8Array(NSQ), DR = new Int8Array(NSQ);
  const ZN = new Uint8Array(NSQ);            // 0 '.', 1 K, 2 M, 3 L, 4 '3'
  const ZCH = ['.', 'K', 'M', 'L', '3'];
  const C = (x, y) => (x + OFF) * WID + (y + OFF);
  for (let c = 0; c < NSQ; c++) {
    const x = (c >> 6) - OFF, y = (c & 63) - OFF;
    SX[c] = x; SY[c] = y;
    ONB[c] = (x >= 0 && x < W && y >= 1 && y <= H) ? 1 : 0;
    DR[c] = Math.max(Math.abs(x - RIMX), Math.abs(y - RIMY));
  }
  const RIM = C(RIMX, RIMY);
  const BI = new Int16Array(NSQ).fill(-1); let NB = 0;       // on-board index 0..237
  for (let c = 0; c < NSQ; c++) if (ONB[c]) BI[c] = NB++;
  const AWAY = C(-9, -9);                   // the 'leaving' square of decide.responses
  const DX = [0, 1, 1, 1, 0, -1, -1, -1], DY = [1, 1, 0, -1, -1, -1, 0, 1];
  const DSTEP = DX.map((dx, d) => dx * WID + DY[d]);
  const DIR_NAMES = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'];
  const ORTH = [0, 2, 4, 6], DIAG = [1, 3, 5, 7], ALLD = [0, 1, 2, 3, 4, 5, 6, 7];
  const COLS = 'ABCDEFGHIJKLMNOPQ';
  const cheb = (a, b) => Math.max(Math.abs(SX[a] - SX[b]), Math.abs(SY[a] - SY[b]));
  const adjacent = (a, b) => cheb(a, b) === 1;
  const STEPDIR = new Map(DSTEP.map((v, d) => [v, d]));
  const dirBetween = (a, b) => (cheb(a, b) === 1 ? STEPDIR.get(b - a) : -1);
  function sqName(c) { const x = SX[c], y = SY[c]; return `${x === -1 ? '@' : x === W ? 'R' : COLS[x]}${y}`; }
  function parseSq(s) { const ch = s[0], r = parseInt(s.slice(1), 10); return C(ch === '@' ? -1 : ch === 'R' ? W : COLS.indexOf(ch), r); }
  function nearestDir(frm, to) {
    const vx = SX[to] - SX[frm], vy = SY[to] - SY[frm];
    let a = Math.atan2(vx, vy) * 180 / Math.PI; a = ((a % 360) + 360) % 360;
    let best = 0, bv = Infinity;
    for (let d = 0; d < 8; d++) { const e = Math.abs(d * 45 - a), v = Math.min(e, 360 - e); if (v < bv) { bv = v; best = d; } }
    return best;
  }
  function onSegment(p, a, b, tol) {
    if (p === a || p === b) return false;
    const vx = SX[b] - SX[a], vy = SY[b] - SY[a], wx = SX[p] - SX[a], wy = SY[p] - SY[a];
    const L2 = vx * vx + vy * vy, dot = wx * vx + wy * vy;
    if (dot <= 0 || dot >= L2) return false;
    const cross = vx * wy - vy * wx;
    if (tol === 0) return cross === 0;
    if (tol === 0.5) return 4 * cross * cross < L2;
    return cross * cross < tol * tol * L2;
  }
  function straightPaths(p, dirs, maxLen, minLen, out) {
    for (const d of dirs) {
      const path = [];
      for (let n = 1; n <= maxLen; n++) { path.push(p + DSTEP[d] * n); if (n >= minLen) out.push([d, path.slice()]); }
    }
    return out;
  }
  const _MP = new Map();
  function movePaths(p) {
    let hit = _MP.get(p); if (hit) return hit;
    const out = straightPaths(p, ORTH, 3, 1, []).map(r => r[1]);
    for (const r of straightPaths(p, DIAG, 2, 1, [])) out.push(r[1]);
    for (const a of ORTH) for (const b of DIAG) {
      const m = p + DSTEP[a]; out.push([m, m + DSTEP[b]]);
      const m2 = p + DSTEP[b]; out.push([m2, m2 + DSTEP[a]]);
    }
    hit = out.filter(path => path[path.length - 1] !== p); _MP.set(p, hit); return hit;
  }
  const _QP = new Map();
  function qsPaths(p, qs) {
    if (qs <= 0) return [];
    const k = p * 8 + qs; let hit = _QP.get(k); if (hit) return hit;
    hit = straightPaths(p, ALLD, qs, 1, []).map(r => r[1]); _QP.set(k, hit); return hit;
  }
  const _SP = new Map();
  function sprintPaths(p, qs) {
    if (qs <= 0) return [];
    const k = p * 8 + qs; let hit = _SP.get(k); if (hit) return hit;
    hit = straightPaths(p, ORTH, 3 + qs, 1, []); straightPaths(p, DIAG, 2 + qs, 1, hit); _SP.set(k, hit); return hit;
  }
  function diagStepBanned(a, b, t) {
    if (SX[a] === SX[b] || SY[a] === SY[b]) return false;
    if (a === t) return true;
    return C(SX[a], SY[b]) === t || C(SX[b], SY[a]) === t;
  }

  // ---- data: zones, cards, rules, tables -----------------------------------------------------------------------------
  const D = { config: null, vcoarse: {}, ready: false, learned: null };
  // step 17: the named readings, in the weights file's order (decide.FEATURES); a file with other names is refused
  const FEATURE_NAMES = ['shot_now', 'look_now', 'best_look_after_cover', 'second_look_after_cover', 'best_look_before_cover',
    'best_look_after_shares', 'paint_next_phase', 'free_looks', 'mismatches_two_bands', 'mismatches_one_band', 'offence_tokens',
    'defence_tokens', 'offence_to_act', 'defenders_moved', 'attackers_moved'];
  function init(data) {
    for (const [k, v] of Object.entries(data.zones)) ZN[parseSq(k)] = ZCH.indexOf(v);
    D.config = data.config; D.vcoarse = data.vcoarse || {}; D.ready = true;
    D.learned = data.learned || null;
    if (D.learned && JSON.stringify(D.learned.features) !== JSON.stringify(FEATURE_NAMES)) throw new Error('learned_weights.json names other readings than this engine makes');
    VMIN = D.config.eval.value_bounds[0]; VMAX = D.config.eval.value_bounds[1];
  }
  let VMIN = -10, VMAX = 60;
  const ZONE_SHOTS = [[], ['layup', 'dunk', 'post'], ['mid', 'floater'], ['long'], ['three']];
  const ZONE_POINTS = [0, 2, 2, 2, 3];
  const SHOT_TYPES = ['', 'layup', 'dunk', 'post', 'mid', 'floater', 'long', 'three'];
  // The ruled settings this port plays (rules_config.Rules defaults); 'digital' may be either.
  const RULED = { turnover_play_on: 'play_on', pass_resolution: 'defence_turn', sprint_orth_base: 3, sprint_diag_base: 2,
    natural_rolls: false, floor_declared_shot: true, reaction_may_decline: true, defence_empty_ends_phase: true,
    wait_chain_block: true, screen_geometry: 'from_t_or_corner', screen_rule: 'hold_until_move', arrow_line_strict: true,
    drive_rule: 'zone', intercept_return: true, intercept_rule: 'move_then_intercept', turnover_cost: 'minus5_lose_phase',
    move_either_order: true, contest_choice: 'player', on_line_tolerance: 0, lane_jump_keeps_facing: true,
    receiver_denial: true, receiver_denial_tol: 0.5, qs_up_to: true, sprint_needs_qs: true, qs_once_per_player: true,
    arrow_mode: 'single', contest_geometry: 'current', carrier_can_screen: false, late_closeout: false, challenge_who: 'on_t',
    locked_can_dribble: false, inbounder_pass_only: true, floor_contest_zero: true, forfeit_when_stuck: true,
    three_only_ft_on_twos: false, coach_bonus_on_forced: true, diag_move_straight: true, inbound_tie: 'offence',
    forced_shot_choice: 'player', inbound_resolves: 'after_defence_turn', and_one: true, steal_lock: true,
    reach_angle_fouls: true, contest_action: true, turnover_floor: true, steal_foul_always_plus5: true };
  const CONTROL = { off: 0, 0: 0, 1: 1, 2: 2, 3: 3 }, CONTROL_APP = 2;   // D-153: the app's size
  // rules_config.control_size: 'app' (the default) is size 2 in the app's format and off at the table
  const controlSize = r => { const c = r && r.control !== undefined ? String(r.control) : 'app'; return c === 'app' ? (r && r.digital ? CONTROL_APP : 0) : CONTROL[c]; };
  function checkRules(r) {
    if (r.control !== undefined && r.control !== 'app' && !(String(r.control) in CONTROL)) throw new Error(`rule control=${r.control} is not ported`);
    for (const [k, v] of Object.entries(RULED)) {
      if (k in r && JSON.stringify(r[k]) !== JSON.stringify(v)) throw new Error(`rule ${k}=${JSON.stringify(r[k])} is not ported`);
    }
    const rk = r.reaction_kinds;
    if (rk && JSON.stringify([...rk].sort()) !== JSON.stringify(['move', 'qs', 'sprint', 'steal'])) throw new Error('reaction_kinds not ported');
  }
  function makeCard(c) {
    const r = c.r, sh = {}, cn = {};
    for (const t of SHOT_TYPES.slice(1)) { sh[t] = r['shot_' + t]; cn[t] = r['con_' + t]; }
    return { qs: c.qs, r, sh, cn, b: c.bands || {} };     // b (step 16): the card's bands (H, A, L) per rating
  }
  let _CTXN = 0;
  function makeCtx(c) {
    checkRules(c.rules || {});
    return { id: ++_CTXN, off: c.off.map(makeCard), dfn: c.dfn.map(makeCard), digital: !!(c.rules && c.rules.digital),
      bonus_from: (c.rules && c.rules.bonus_from) || 5, quarter_possessions: (c.rules && c.rules.quarter_possessions) || 18,
      card_clock: c.card_clock, inbounder: c.inbounder, coach_call: !!c.coach_call, three_only: !!c.three_only,
      two_or_three: !!c.two_or_three, hold_for_one: !!c.hold_for_one, team_fouls: c.team_fouls || 0,
      quarter_left: c.quarter_left || 0, table: c.table || 'senior/pro',
      control: controlSize(c.rules) };                    // D-151, D-153: the size, in rating steps (0: the rule is off)
  }
  // D-151, D-153 (rules.control): the reduction a rushed shot, or a rushed Contest of it, takes
  const controlOn = ctx => ctx.control > 0;
  const controlCut = (ctx, t) => ctx.control;            // one size, for every shot type and for the Contest alike
  // two bits a player in rush_o / rush_x: 1 his last movement this phase was a Quick Step, 2 a Sprint, 0 set
  const rushedO = (s, i) => ((s.rush_o >> (2 * i)) & 3) !== 0;
  const rushedX = (s, j) => ((s.rush_x >> (2 * j)) & 3) !== 0;
  const shotRating = (s, shooter, t) => s.ctx.off[shooter].sh[t] - (controlOn(s.ctx) && rushedO(s, shooter) ? controlCut(s.ctx, t) : 0);

  // ---- state --------------------------------------------------------------------------------------------------------
  // cnt indices: o_qs pass screen dribble hesitate shot x_qs intercept challenge steal pause
  const CI = { o_qs: 0, pass: 1, screen: 2, dribble: 3, hesitate: 4, shot: 5, x_qs: 6, intercept: 7, challenge: 8, steal: 9, pause: 10 };
  const cidx = (side, kind) => (kind === 'qs' ? (side === 'O' ? 0 : 6) : CI[kind]);
  const LIMITS = { O: { qs: 2, pass: 2, screen: 2, dribble: 2, hesitate: 1, shot: 1 }, X: { qs: 2, intercept: 2, challenge: 2, steal: 2, pause: 1, contest: 1 } };
  const TURN_ENDERS = new Set(['pass', 'screen', 'dribble', 'hesitate', 'shot', 'intercept', 'challenge', 'steal', 'pause', 'contest']);
  const MOVEMENT = new Set(['move', 'qs', 'sprint']);
  const TOKEN_FREE = new Set(['target', 'pick', 'end_turn', 'forfeit', 'contest', 'forced_shot']);
  const count = (s, side, kind) => s.cnt[cidx(side, kind)];
  const tokens = (s, side) => (side === 'O' ? s.tok_o : s.tok_x);
  const isLocked = (s, side, i) => (((side === 'O' ? s.lock_o : s.lock_x) >> i) & 1) === 1;
  const hasMoved = (s, side, i) => (((side === 'O' ? s.moved_o : s.moved_x) >> i) & 1) === 1;
  const quickStepped = (s, side, i) => (((side === 'O' ? s.qs_o : s.qs_x) >> i) & 1) === 1;
  const screenOf = (s, i) => { for (const sc of s.screens) if (sc[0] === i) return sc; return null; };
  class St {
    constructor(s) {
      this.ctx = s.ctx;
      this.o = s.o;
      this.x = s.x;
      this.arrows = s.arrows;
      this.ball = s.ball;
      this.stage = s.stage;
      this.side = s.side;
      this.clock = s.clock;
      this.tok_o = s.tok_o;
      this.tok_x = s.tok_x;
      this.moved_o = s.moved_o;
      this.moved_x = s.moved_x;
      this.cnt = s.cnt;
      this.turn_n = s.turn_n;
      this.final = s.final;
      this.lock_o = s.lock_o;
      this.lock_x = s.lock_x;
      this.screens = s.screens;
      this.pending = s.pending;
      this.approach = s.approach;
      this.shot = s.shot;
      this.prev_wait = s.prev_wait;
      this.beaten = s.beaten;
      this.fouls = s.fouls;
      this.bonus5 = s.bonus5;
      this.tos = s.tos;
      this.inbound = s.inbound;
      this.target = s.target;
      this.result = s.result;
      this.zeroed = s.zeroed;
      this.phase = s.phase;
      this.turn_moved = s.turn_moved;
      this.qs_o = s.qs_o;
      this.qs_x = s.qs_x;
      this.forced = s.forced;
      this.react_moved = s.react_moved;
      this.turn_lead = s.turn_lead;
      this.turn_x = s.turn_x;
      this.rush_o = s.rush_o || 0;                       // D-151: last movement this phase was a Quick Step or Sprint
      this.rush_x = s.rush_x || 0;
      this._occ = s._occ || null;
      this._dre = null;                                  // step 13: this state's exact reach, per defender
    }
  }
  const W_ = (s, ch) => { const n = new St(s); for (const k in ch) n[k] = ch[k]; if (ch.o !== undefined || ch.x !== undefined) n._occ = null; return n; };
  const occAt = (s, q) => { const o = s.o, x = s.x; return o[0] === q || o[1] === q || o[2] === q || o[3] === q || o[4] === q || x[0] === q || x[1] === q || x[2] === q || x[3] === q || x[4] === q; };
  const occupied = s => { if (s._occ) return s._occ; const o = new Set(s.o); for (const p of s.x) o.add(p); s._occ = o; return o; };
  const setAt = (arr, i, v) => { const a = arr.slice(); a[i] = v; return a; };

  function stateFrom(js, ctx) {
    const sq = v => (v == null ? -1 : parseSq(v));
    const s = { ctx, o: js.o.map(sq), x: js.x.map(sq), arrows: js.arrows.slice(), ball: js.ball, stage: js.stage, side: js.side,
      clock: js.clock, tok_o: js.tok_o, tok_x: js.tok_x, moved_o: js.moved_o, moved_x: js.moved_x, cnt: js.cnt.slice(),
      turn_n: js.turn_n, final: js.final, lock_o: js.lock_o, lock_x: js.lock_x,
      screens: js.screens.map(t => [t[0], t[1], !!t[2], t[3]]), pending: js.pending ? js.pending.slice() : null,
      approach: js.approach, shot: js.shot || null, prev_wait: js.prev_wait || '', beaten: js.beaten.map(t => t.slice()),
      fouls: js.fouls, bonus5: js.bonus5, tos: js.tos, inbound: js.inbound, target: js.target, result: js.result || null,
      zeroed: js.zeroed, phase: js.phase, turn_moved: js.turn_moved, qs_o: js.qs_o, qs_x: js.qs_x, forced: js.forced,
      react_moved: js.react_moved, turn_lead: js.turn_lead, rush_o: js.rush_o || 0, rush_x: js.rush_x || 0,
      turn_x: js.turn_x && js.turn_x.length ? [js.turn_x[0].map(sq), js.turn_x[1].slice()] : null };
    return new St(s);
  }
  // Step 17: a state back to the form stateFrom reads (for the tools that play positions out and store them)
  function stateJSON(s) {
    const sq = v => (v < 0 || !ONB[v] ? null : sqName(v));
    return { o: s.o.map(sq), x: s.x.map(sq), arrows: s.arrows.slice(), ball: s.ball, stage: s.stage, side: s.side, clock: s.clock,
      tok_o: s.tok_o, tok_x: s.tok_x, moved_o: s.moved_o, moved_x: s.moved_x, cnt: Array.from(s.cnt), turn_n: s.turn_n, final: s.final,
      lock_o: s.lock_o, lock_x: s.lock_x, screens: s.screens.map(t => t.slice()), pending: s.pending ? s.pending.slice() : null,
      approach: s.approach, shot: s.shot || null, prev_wait: s.prev_wait || '', beaten: s.beaten.map(t => t.slice()), fouls: s.fouls,
      bonus5: s.bonus5, tos: s.tos, inbound: s.inbound, target: s.target, result: s.result || null, zeroed: s.zeroed, phase: s.phase,
      turn_moved: s.turn_moved, qs_o: s.qs_o, qs_x: s.qs_x, forced: s.forced, react_moved: s.react_moved, turn_lead: s.turn_lead,
      rush_o: s.rush_o, rush_x: s.rush_x, turn_x: s.turn_x ? [s.turn_x[0].map(sq), s.turn_x[1].slice()] : null };
  }

  // ---- actions --------------------------------------------------------------------------------------------------------
  const ORDER = ['target', 'pick', 'forced_shot', 'contest', 'end_turn', 'forfeit', 'shot', 'pass', 'dribble', 'screen', 'hesitate',
    'intercept', 'steal', 'challenge', 'pause', 'move', 'qs', 'sprint'];
  const OIDX = Object.fromEntries(ORDER.map((k, i) => [k, i]));
  function A(kind, side, piece = -1, dest = -1, arrow = -1, target = -1, shot = '') {
    const id = ((((((OIDX[kind] * 2 + (side === 'O' ? 0 : 1)) * 8 + piece + 1) * 4097 + dest + 1) * 16 + arrow + 1) * 16 + target + 1) * 8)
      + SHOT_TYPES.indexOf(shot);
    return { kind, side, piece, dest, arrow, target, shot, id };
  }
  function actionJSON(a) { return [a.kind, a.side, a.piece, a.dest >= 0 ? sqName(a.dest) : null, a.arrow, a.target, a.shot]; }
  function actionStr(a) {
    const who = a.piece >= 0 ? `${a.side}${a.piece + 1}` : a.side, k = a.kind;
    if (k === 'move') return `${who} Move to ${sqName(a.dest)}` + (a.arrow >= 0 ? ` facing ${DIR_NAMES[a.arrow]}` : '');
    if (k === 'qs') return `${who} Quick Step to ${sqName(a.dest)}`;
    if (k === 'sprint') return `${who} Sprint to ${sqName(a.dest)}`;
    if (k === 'pass') return `${who} Pass to O${a.target + 1}`;
    if (k === 'screen') return `${who} Screen, T ${DIR_NAMES[a.target]}`;
    if (k === 'dribble') return `${who} Dribble vs X${a.target + 1}`;
    if (k === 'shot') return `${who} Shot (${a.shot})`;
    if (k === 'intercept') return `${who} Intercept`;
    if (k === 'challenge') return `${who} Challenge screen of O${a.target + 1}`;
    if (k === 'steal') return `${who} Steal`;
    if (k === 'target') return `Coach's Call target O${a.target + 1}`;
    if (k === 'contest') return a.piece >= 0 ? `${who} contests` : "X: don't contest";
    if (k === 'forced_shot') return `${who} forced shot (${a.shot})`;
    if (k === 'pick') return `Failed inbound: ball to O${a.target + 1}`;
    if (k === 'end_turn') return `${who} End turn`;
    if (k === 'forfeit') return `${who} Forfeit tokens (no legal action)`;
    return `${who} ${k[0].toUpperCase()}${k.slice(1)}`;
  }
  const tSquare = (s, scr) => s.o[scr[0]] + DSTEP[scr[1]];

  function canMoveKind(s, side, i, kind) {
    if (tokens(s, side) <= 0) return false;
    if (side === 'O' && i === s.ctx.inbounder && s.inbound) return false;
    if (kind === 'move' || kind === 'sprint') { if (hasMoved(s, side, i) || isLocked(s, side, i)) return false; }
    if (kind === 'qs' || kind === 'sprint') {
      if (count(s, side, 'qs') >= LIMITS[side].qs) return false;
      if (quickStepped(s, side, i)) return false;
    }
    return true;
  }
  function zoneOf(s, j, vacated, taken) {            // vacated, taken (step 13C): one attacker's square moved
    // actions.zone: the squares along his arrow he reaches with one movement left to him (only membership is used).
    // Only the straight path reaches a square on the arrow ray, so the walk checks that path directly.
    const start = s.x[j], card = s.ctx.dfn[j], d = s.arrows[j], diag = d & 1, step = DSTEP[d];
    const mvR = canMoveKind(s, 'X', j, 'move') ? (diag ? 2 : 3) : 0;
    const qsR = canMoveKind(s, 'X', j, 'qs') && card.qs > 0 ? card.qs : 0;
    const spR = canMoveKind(s, 'X', j, 'sprint') && card.qs > 0 ? (diag ? 2 : 3) + card.qs : 0;
    const maxR = Math.max(mvR, qsR, spR), out = [];
    let q = start;
    for (let n = 1; n <= maxR; n++) {
      const prev = q; q += step;
      if (!ONB[q] || q === taken || (q !== vacated && occAt(s, q))) break;
      let ok = true;
      for (const scr of s.screens) {
        const tsq = tSquare(s, scr);
        if ((scr[3] >> j) & 1) { if (q === tsq) { ok = false; break; } }
        else if (diagStepBanned(prev, q, tsq)) { ok = false; break; }
      }
      if (!ok) break;
      out.push(q);
    }
    return out;
  }
  function carrierZones(s, i) {
    const start = s.o[i], out = new Set();
    for (let j = 0; j < 5; j++) {
      if (!adjacent(s.x[j], start)) continue;
      if (s.beaten.some(b => b[0] === i && b[1] === j)) continue;
      for (const q of zoneOf(s, j)) out.add(q);
    }
    return out;
  }
  function pathOk(s, side, i, path, occ, zones) {
    const start = side === 'O' ? s.o[i] : s.x[i];
    for (const q of path) if (!ONB[q] || (occ ? occ.has(q) : occAt(s, q))) return false;
    if (side === 'X') {
      if (!s.screens.length) return true;
      for (const scr of s.screens) {
        const tsq = tSquare(s, scr);
        if ((scr[3] >> i) & 1) { if (path[path.length - 1] === tsq) return false; continue; }
        let a = start;
        for (const b of path) { if (diagStepBanned(a, b, tsq)) return false; a = b; }
      }
      return true;
    }
    if (i === s.ball) {
      if (zones == null) zones = carrierZones(s, i);
      for (let n = 0; n < path.length - 1; n++) if (zones.has(path[n])) return false;
    }
    return true;
  }
  function movementDests(s, side, i, kind) {
    const card = (side === 'O' ? s.ctx.off : s.ctx.dfn)[i];
    const start = side === 'O' ? s.o[i] : s.x[i];
    let paths;
    if (kind === 'move') paths = movePaths(start).map(p => [-1, p]);
    else if (kind === 'qs') paths = qsPaths(start, card.qs).map(p => [-1, p]);
    else paths = sprintPaths(start, card.qs);
    const out = new Map();
    const zs = side === 'O' && i === s.ball ? carrierZones(s, i) : null;
    for (const [d, path] of paths) {
      const dest = path[path.length - 1];
      if (out.has(dest)) continue;
      if (pathOk(s, side, i, path, null, zs)) out.set(dest, d);
    }
    return out;
  }
  function movementActions(s, side) {
    const acts = [], pieces = side === 'O' ? s.o : s.x;
    for (const kind of ['move', 'qs', 'sprint']) {
      for (let i = 0; i < 5; i++) {
        if (!canMoveKind(s, side, i, kind)) continue;
        const dests = movementDests(s, side, i, kind);
        if (side === 'X' && kind === 'move') {
          const start = pieces[i], cur = s.arrows[i];
          for (let d = 0; d < 8; d++) if (d !== cur) acts.push(A('move', 'X', i, start, d));
          for (const dest of dests.keys()) for (let d = 0; d < 8; d++) acts.push(A('move', 'X', i, dest, d));
        } else {
          for (const dest of dests.keys()) acts.push(A(kind, side, i, dest));
        }
      }
    }
    return acts;
  }
  function denier(s, passer, receiver) {
    if (passer === receiver) return -1;
    const a = s.o[passer], b = s.o[receiver];
    if (!(ONB[a] && ONB[b])) return -1;
    let best = -1, bk = Infinity;
    for (let j = 0; j < 5; j++) {
      const xp = s.x[j];
      if (adjacent(xp, b) && onSegment(xp, a, b, 0.5)) { const k = cheb(xp, b) * 8 + j; if (k < bk) { bk = k; best = j; } }
    }
    return best;
  }
  const inRing = (s, q) => cheb(q, s.o[s.pending[0]]) === 1;     // the passer's ring: the 8 squares round him
  function laneMeet(p, d, a, b) {
    const dx = DX[d], dy = DY[d], ex = SX[b] - SX[a], ey = SY[b] - SY[a];
    const den = dx * ey - dy * ex;
    if (den === 0) return 0;
    const wx = SX[a] - SX[p], wy = SY[a] - SY[p];
    const t = (wx * ey - wy * ex) / den, u = (wx * dy - wy * dx) / den;
    if (u <= 1e-9 || u >= 1 - 1e-9) return 0;
    const n = Math.floor(t + 0.5 + 1e-9);
    return n >= 1 ? n : 0;
  }
  function throughYou(s, j) {
    const p = s.x[j];
    if (inRing(s, p) || ((s.turn_moved >> j) & 1)) return false;
    return onSegment(p, s.o[s.pending[0]], s.o[s.pending[1]], 0);
  }
  function mtiApproach(s, a) {
    if (!(s.pending && a.side === 'X' && MOVEMENT.has(a.kind) && s.turn_n === 0 && s.stage === 'play')) return false;
    if (count(s, 'X', 'intercept') >= LIMITS.X.intercept || s.tok_x < 2) return false;
    const j = a.piece, p = s.x[j], q = a.dest;
    if (inRing(s, q)) return false;
    const dx = SX[q] - SX[p], dy = SY[q] - SY[p], n = Math.max(Math.abs(dx), Math.abs(dy));
    if (n === 0 || (dx !== -n && dx !== 0 && dx !== n) || (dy !== -n && dy !== 0 && dy !== n)) return false;
    const d = STEPDIR.get((dx / n) * WID + dy / n);
    if (d !== s.arrows[j]) return false;
    if (laneMeet(p, d, s.o[s.pending[0]], s.o[s.pending[1]]) !== n) return false;
    if (a.kind === 'sprint') { if (d !== s.arrows[j]) return false; }
    else if (a.kind === 'move' && a.arrow !== s.arrows[j]) return false;
    const path = []; for (let k = 1; k <= n; k++) path.push(p + DSTEP[d] * k);
    return pathOk(s, 'X', j, path, null);
  }
  const isInboundPass = s => !!s.pending && !!s.inbound && s.pending[0] === s.ctx.inbounder;
  const completedView = s => W_(s, { ball: s.pending[1], pending: null, approach: -1 });

  function offenceActions(s, shotsOnly) {               // shotsOnly (step 13): the shots alone, nothing else generated
    const acts = [], ctx = s.ctx;
    if (s.tok_o <= 0) return acts;
    const carrier = s.ball, cpos = s.o[carrier];
    const inbounderHasIt = s.inbound && carrier === ctx.inbounder;
    if (shotsOnly) {
      const z0 = ZN[cpos];
      if (!inbounderHasIt && ONB[cpos] && z0 !== 0 && count(s, 'O', 'shot') < LIMITS.O.shot && !(ctx.hold_for_one && s.clock > 2)) {
        for (const t of ZONE_SHOTS[z0]) acts.push(A('shot', 'O', carrier, -1, -1, -1, t));
      }
      return acts;
    }
    if (count(s, 'O', 'pass') < LIMITS.O.pass) {
      for (let r = 0; r < 5; r++) if (r !== carrier && denier(s, carrier, r) < 0) acts.push(A('pass', 'O', carrier, -1, -1, r));
    }
    const passOnly = !!inbounderHasIt;
    const z = ZN[cpos];
    if (!passOnly && ONB[cpos] && z !== 0 && count(s, 'O', 'shot') < LIMITS.O.shot && !(ctx.hold_for_one && s.clock > 2)) {
      for (const t of ZONE_SHOTS[z]) acts.push(A('shot', 'O', carrier, -1, -1, -1, t));
    }
    if (!passOnly && count(s, 'O', 'dribble') < LIMITS.O.dribble && !isLocked(s, 'O', carrier)) {
      for (let j = 0; j < 5; j++) if (adjacent(s.x[j], cpos)) acts.push(A('dribble', 'O', carrier, -1, -1, j));
    }
    if (count(s, 'O', 'screen') < LIMITS.O.screen) {
      for (let i = 0; i < 5; i++) {
        const p = s.o[i];
        if (!ONB[p] || screenOf(s, i)) continue;
        if (!(s.turn_n === 0 || (s.turn_n === 1 && s.turn_lead === i))) continue;
        if (i === ctx.inbounder && s.inbound) continue;
        if (i === carrier) continue;
        for (let d = 0; d < 8; d++) if (ONB[p + DSTEP[d]]) acts.push(A('screen', 'O', i, -1, -1, d));
      }
    }
    if (count(s, 'O', 'hesitate') < LIMITS.O.hesitate && s.prev_wait !== 'P') acts.push(A('hesitate', 'O'));
    for (const a of movementActions(s, 'O')) acts.push(a);
    return acts;
  }
  function defenceActions(s, kinds) {
    const acts = [];
    if (s.tok_x <= 0) return acts;
    const cpos = s.o[s.ball];
    const ok = k => !kinds || kinds.has(k);
    if (ok('steal') && count(s, 'X', 'steal') < LIMITS.X.steal) {
      for (let j = 0; j < 5; j++) if (adjacent(s.x[j], cpos) && dirBetween(s.x[j], cpos) === s.arrows[j]) acts.push(A('steal', 'X', j));
    }
    if (ok('challenge') && count(s, 'X', 'challenge') < LIMITS.X.challenge) {
      for (const scr of s.screens) for (let j = 0; j < 5; j++) {
        if ((scr[3] >> j) & 1) continue;
        if (s.x[j] !== tSquare(s, scr)) continue;
        acts.push(A('challenge', 'X', j, -1, -1, scr[0]));
      }
    }
    if (ok('pause') && count(s, 'X', 'pause') < LIMITS.X.pause && s.prev_wait !== 'H') acts.push(A('pause', 'X'));
    if (kinds && !(kinds.has('move') || kinds.has('qs') || kinds.has('sprint'))) return acts;   // no movement asked for
    let mv = movementActions(s, 'X');
    if (kinds) mv = mv.filter(a => kinds.has(a.kind));
    for (const a of mv) acts.push(a);
    return acts;
  }
  const REACTION = new Set(['move', 'qs', 'sprint', 'steal']);
  function legalActions(s) {
    if (s.stage === 'over') return [];
    if (s.stage === 'target') return [0, 1, 2, 3, 4].map(i => A('target', 'O', -1, -1, -1, i));
    if (s.stage === 'contest') return contestOptions(s, s.ball, s.shot, s.forced).map(o => A('contest', 'X', o.defender));
    if (s.stage === 'forced') return ZONE_SHOTS[ZN[s.o[s.ball]]].map(t => A('forced_shot', 'O', s.ball, -1, -1, -1, t));
    if (s.stage === 'pick') return inboundTieCandidates(s).map(i => A('pick', 'O', -1, -1, -1, i));
    const side = s.side;
    let acts = [];
    if (s.stage === 'reaction') {
      acts = defenceActions(s, REACTION);
      if (s.tok_x > 0) {                                  // D-18: a Contest by a defender next to the shooter, the last action
        for (const o of contestOptions(s, s.ball, s.shot, false)) if (o.defender >= 0) acts.push(A('contest', 'X', o.defender));
      }
      acts.push(A('end_turn', 'X'));
    } else if (side === 'O') {
      acts = offenceActions(s);
      if (s.turn_n >= 1) acts.push(A('end_turn', 'O'));
    } else if (s.pending) {
      const canIcpt = count(s, 'X', 'intercept') < LIMITS.X.intercept && s.tok_x > 0;
      if (s.turn_n === 0 && canIcpt) for (let j = 0; j < 5; j++) if (throughYou(s, j)) acts.push(A('intercept', 'X', j));
      if (s.turn_n === 1 && s.approach >= 0 && canIcpt) acts.push(A('intercept', 'X', s.approach));
      if (isInboundPass(s)) {
        for (const a of defenceActions(s)) if (a.kind !== 'steal') acts.push(a);
        if (s.turn_n >= 1) acts.push(A('end_turn', 'X'));
      } else {
        for (const a of defenceActions(completedView(s))) acts.push(a);
        if (s.turn_n >= 1) acts.push(A('end_turn', 'X'));
      }
    } else {
      acts = defenceActions(s);
      if (s.turn_n >= 1) acts.push(A('end_turn', 'X'));
    }
    if (!acts.length && tokens(s, side) > 0) acts = [A('forfeit', side)];
    const rest = acts.filter(a => !MOVEMENT.has(a.kind)), mv = acts.filter(a => MOVEMENT.has(a.kind));
    rest.sort((a, b) => OIDX[a.kind] - OIDX[b.kind]);
    return mv.length ? rest.concat(mv) : rest;
  }
  function inboundTieCandidates(s) {
    const ib = s.ctx.inbounder, cands = [];
    for (let i = 0; i < 5; i++) if (i !== ib && ONB[s.o[i]]) cands.push(i);
    let far = -1; for (const i of cands) far = Math.max(far, DR[s.o[i]]);
    return cands.filter(i => DR[s.o[i]] === far);
  }
  const isLegal = (s, a) => legalActions(s).some(b => b.id === a.id);
  // Step 13 (a speed-up that changes no result): the forcing replies the stable search plays on with, generated
  // without the movement: exactly legalActions(s) filtered to those kinds, in the same order.
  const FORCE_DEF = new Set(['steal', 'pause']);
  function forcingActions(s, why) {
    if (s.stage !== 'play' && s.stage !== 'reaction') return legalActions(s);      // a contest choice, a forced shot: all
    let acts;
    if (why === 'shot') acts = s.side === 'O' ? offenceActions(s, true) : null;
    else if (s.stage === 'reaction') {
      acts = defenceActions(s, FORCE_DEF).filter(a => a.kind === 'steal');           // the reaction's kinds: movement and Steal
      if (s.tok_x > 0) for (const o of contestOptions(s, s.ball, s.shot, false)) if (o.defender >= 0) acts.push(A('contest', 'X', o.defender));
      acts.push(A('end_turn', 'X'));
    } else if (s.side === 'X' && s.pending) {
      acts = [];
      const canIcpt = count(s, 'X', 'intercept') < LIMITS.X.intercept && s.tok_x > 0;
      if (s.turn_n === 0 && canIcpt) for (let j = 0; j < 5; j++) if (throughYou(s, j)) acts.push(A('intercept', 'X', j));
      if (s.turn_n === 1 && s.approach >= 0 && canIcpt) acts.push(A('intercept', 'X', s.approach));
      if (isInboundPass(s)) { for (const a of defenceActions(s, FORCE_DEF)) if (a.kind !== 'steal') acts.push(a); }
      else for (const a of defenceActions(completedView(s), FORCE_DEF)) acts.push(a);
      if (s.turn_n >= 1) acts.push(A('end_turn', 'X'));
    } else acts = null;
    if (acts === null) {                                   // any other case: the full list, filtered
      const kinds = why === 'shot' ? SHOT_ONLY : FORCING;
      return legalActions(s).filter(a => kinds.has(a.kind));
    }
    acts.sort((a, b) => OIDX[a.kind] - OIDX[b.kind]);
    return acts;
  }

  // ---- scoring ----------------------------------------------------------------------------------------------------
  const clampT = t => Math.max(0, Math.min(20, t));
  const pS = t => clampT(t) / 20;                         // P(d20 <= t), as Python's float(Fraction(t, 20))
  const pNot = t => (20 - clampT(t)) / 20;                // 1 - that, exactly as Fraction arithmetic gives it
  const foulRolls = (dpos, target) => (DR[dpos] < DR[target] ? 1 : 2);
  const pFouls = (k, rolls) => { k = clampT(k); return rolls === 1 ? k / 20 : (400 - (20 - k) * (20 - k)) / 400; };
  const shotPoints = pos => ZONE_POINTS[ZN[pos]];
  const freeThrows = (card, points) => (points === 3 ? 3 : 2) * card.r.free_throw;
  function footPoints(card, t, pts, rating) {             // scoring.foul_on_shot_points: [points, and_one]; rating: reduced (D-151)
    const ft = freeThrows(card, pts);
    if (t) { const open = pts * (rating === undefined ? card.sh[t] : rating); if (open > ft) return [open, true]; }
    return [ft, false];
  }
  function contestOptions(s, shooter, t, forced) {
    const ctx = s.ctx, spos = s.o[shooter], card = ctx.off[shooter], pts = shotPoints(spos), rating = shotRating(s, shooter, t);
    const ft = footPoints(card, t, pts, rating)[0];
    const cut = controlOn(ctx) ? controlCut(ctx, t) : 0;
    const val = c => Math.max(0, pts * (rating - c));
    const opts = [{ defender: -1, contest: 0, clean: true, k: 0, rolls: 0, value: val(0), ft }];
    for (let j = 0; j < 5; j++) {
      const xp = s.x[j];
      if (!adjacent(xp, spos)) continue;
      let c = ctx.dfn[j].cn[t];
      if (DR[xp] > DR[spos]) c -= 3;
      c = Math.max(0, c);
      let clean = dirBetween(xp, spos) === s.arrows[j];
      if (cut && rushedX(s, j)) c = Math.max(0, c - cut);       // D-151, D-154: a rushed Contest, no extra foul roll
      const rolls = foulRolls(xp, spos);
      opts.push({ defender: j, contest: c, clean, k: clean ? 0 : clampT(ctx.dfn[j].r.foul_contest), rolls: clean ? 0 : rolls, value: val(c), ft });
    }
    return opts;
  }
  function band(score) { return score >= 30 ? 'Excellent' : score >= 25 ? 'Great' : score >= 20 ? 'Good' : score >= 15 ? 'Okay' : 'Poor'; }
  const COACH_BONUS = { Poor: 0, Okay: 2, Good: 5, Great: 8, Excellent: 10 };
  function scoreTotal(s) {
    const ctx = s.ctx, r = s.result;
    let sv = 0, ft = 0;
    const pts = r ? r.points : 0;
    if (r) { sv = r.shot_value; ft = r.free_throws; if (ctx.three_only && pts !== 3) { sv = 0; ft = 0; } }
    const look = r && r.kind === 'free_throws' ? ft : sv;
    let coach = 0;
    if (ctx.coach_call && r && r.shooter >= 0 && r.shooter === s.target && (r.kind === 'shot' || r.kind === 'forced' || r.kind === 'free_throws')) coach = COACH_BONUS[band(look)];
    const total = sv + ft + 5 * s.bonus5 - 5 * s.tos + coach;
    return s.zeroed ? (r ? r.floor : 0) : total;           // D-82: a zeroing turnover scores min(0, banked before it)
  }
  const Result = (kind, shooter = -1, shot_type = '', points = 0, rating = 0, contest = 0, contester = -1, shot_value = 0, free_throws = 0, and_one = false, floor = 0) =>
    ({ kind, shooter, shot_type, points, rating, contest, contester, shot_value, free_throws, and_one, floor });

  // ---- resolve ----------------------------------------------------------------------------------------------------
  const isChance = n => n.outcomes !== undefined;
  function chance(outcomes) {
    const outs = outcomes.filter(o => o[0] > 0);
    if (outs.length === 1) return outs[0][2];
    return { outcomes: outs };
  }
  const inc = (s, side, kind) => { const c = s.cnt.slice(); c[cidx(side, kind)] += 1; return W_(s, { cnt: c }); };
  const spend = (s, side) => (side === 'O' ? W_(s, { tok_o: s.tok_o - 1 }) : W_(s, { tok_x: s.tok_x - 1 }));
  const lock = (s, side, i) => (side === 'O' ? W_(s, { lock_o: s.lock_o | (1 << i) }) : W_(s, { lock_x: s.lock_x | (1 << i) }));
  const terminal = (s, result, zeroed = false) => {
    if (zeroed && !s.zeroed) result = Object.assign({}, result, { floor: Math.min(0, 5 * s.bonus5 - 5 * (s.tos - 1)) });   // D-82
    return W_(s, { stage: 'over', side: '-', result, zeroed: s.zeroed || zeroed, pending: null, shot: null });
  };
  const ZERO = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
  function pickoff(s) {
    s = W_(s, { tos: s.tos + 1 });
    if (s.ctx.hold_for_one || s.ctx.digital) return terminal(s, Result('turnover_end'), true);
    if (s.clock <= 2) return terminal(s, Result('turnover_end'), true);
    return W_(s, { clock: s.clock - 2 });
  }
  function newPhase(s, clock) {
    return W_(s, { screens: [], clock, turn_lead: -1, turn_x: null, tok_o: 6, tok_x: 6, moved_o: 0, moved_x: 0, cnt: ZERO, turn_n: 0,
      final: false, lock_o: 0, lock_x: 0, approach: -1, prev_wait: '', beaten: [], side: 'O', phase: s.phase + 1, pending: null,
      turn_moved: 0, qs_o: 0, qs_x: 0, react_moved: 0, rush_o: 0, rush_x: 0 });
  }
  function completePass(s) {
    const passer = s.pending[0], recv = s.pending[1];
    s = W_(s, { ball: recv, pending: null, approach: -1 });
    if (s.inbound && passer === s.ctx.inbounder) s = newPhase(W_(s, { inbound: 0 }), s.ctx.card_clock);
    return s;
  }
  function resolveShot(s, forced = false) {
    const spos = s.o[s.ball];
    if (forced) {
      if (!ONB[spos] || ZN[spos] === 0) return terminal(s, Result('forced', s.ball, '', 0));
      const types = ZONE_SHOTS[ZN[spos]];
      if (types.length > 1) return W_(s, { stage: 'forced', side: 'O', shot: null, forced: true, turn_n: 0, pending: null });
      s = W_(s, { shot: types[0], forced: true });
    }
    if (!forced) return contestOutcome(W_(s, { forced: false, pending: null }), contestOptions(s, s.ball, s.shot, false)[0], false);   // D-18
    return W_(s, { stage: 'contest', side: 'X', turn_n: 0, forced, pending: null });
  }
  function contestOutcome(s, opt, forced) {
    const shooter = s.ball, spos = s.o[shooter], card = s.ctx.off[shooter], t = s.shot, pts = shotPoints(spos);
    const rating = shotRating(s, shooter, t);            // D-151: reduced when the shooter is rushed
    const made = terminal(s, Result(forced ? 'forced' : 'shot', shooter, t, pts, rating, opt.contest, opt.defender, opt.value, 0));
    if (opt.clean || opt.k === 0) return made;
    const and1 = footPoints(card, t, pts, rating)[1];
    const fouled = terminal(W_(s, { fouls: s.fouls + 1 }),
      Result('free_throws', shooter, t, pts, rating, opt.contest, opt.defender, 0, opt.ft, and1));
    const one = opt.k / 20, no = (20 - opt.k) / 20;
    if (opt.rolls === 2) {
      const second = chance([[one, 'foul', fouled], [no, 'no foul', made]]);
      return chance([[one, 'foul', fouled], [no, 'no foul', second]]);
    }
    return chance([[one, 'foul', fouled], [no, 'no foul', made]]);
  }
  function endPhase(s) {
    if (s.stage === 'over') return s;
    if (s.pending) { const ph = s.phase; s = completePass(s); if (s.phase !== ph) return s; }
    if (s.inbound) {
      if (s.inbound < 2) return W_(newPhase(s, s.clock), { inbound: s.inbound + 1 });
      s = W_(s, { tos: s.tos + 1 });
      if (s.ctx.hold_for_one) return terminal(s, Result('turnover_end'), true);
      const ib = s.ctx.inbounder, cands = [];
      for (let i = 0; i < 5; i++) if (i !== ib && ONB[s.o[i]]) cands.push(i);
      let far = -1; for (const i of cands) far = Math.max(far, DR[s.o[i]]);
      const tied = cands.filter(i => DR[s.o[i]] === far);
      s = newPhase(W_(s, { inbound: 0 }), s.ctx.card_clock);
      if (tied.length > 1) return W_(s, { stage: 'pick' });
      return W_(s, { ball: tied[0] });
    }
    const clock = s.clock - 2;
    if (clock <= 0) {
      s = W_(s, { clock: 0, tos: s.tos + 1 });
      if (s.ctx.hold_for_one || s.ctx.digital) return terminal(s, Result('turnover_end'), true);
      return resolveShot(s, true);
    }
    return newPhase(s, clock);
  }
  function endTurn(s, side, kind = '') {
    if (s.stage === 'over') return s;
    if (s.stage === 'reaction') return resolveShot(s);
    if (side === 'O') {
      s = W_(s, { side: 'X', turn_n: 0, prev_wait: kind === 'hesitate' ? 'H' : '', final: s.tok_o === 0, turn_moved: 0, turn_lead: -1,
        turn_x: [s.x, s.arrows] });
      if (s.tok_x <= 0) return endPhase(s);
      return s;
    }
    const ph = s.phase;
    if (s.pending) { s = completePass(s); if (s.phase !== ph) return s; }
    s = W_(s, { prev_wait: kind === 'pause' ? 'P' : '', approach: -1 });
    if (s.final) return endPhase(s);
    return W_(s, { side: 'O', turn_n: 0, turn_lead: -1, turn_x: null });
  }
  function after(prev, s, side, kind) {
    if (s.stage === 'over' || s.phase !== prev.phase) return s;
    if (kind === 'end_turn') return endTurn(s, side, kind);
    if (kind === 'forfeit') {
      if (side === 'X') return s.stage === 'reaction' ? resolveShot(s) : endPhase(s);
      return endTurn(s, side, kind);
    }
    s = W_(s, { turn_n: s.turn_n + 1 });
    if (s.stage === 'reaction') {
      if (TURN_ENDERS.has(kind) || s.turn_n >= 2 || s.tok_x <= 0) return resolveShot(s);
      return s;
    }
    if (side === 'X' && s.tok_x <= 0) return endPhase(s);
    if (TURN_ENDERS.has(kind) || s.turn_n >= 2 || tokens(s, side) <= 0) return endTurn(s, side, kind);
    return s;
  }
  function apply(state, a) {
    let s = state;
    const side = a.side, k = a.kind;
    if (k === 'target') return W_(s, { target: a.target, stage: 'play' });
    if (k === 'pick') return W_(s, { ball: a.target, stage: 'play' });
    if (k === 'forced_shot') return W_(s, { shot: a.shot, stage: 'contest', side: 'X', forced: true });
    if (k === 'contest') {
      const opt = contestOptions(s, s.ball, s.shot, s.forced).find(o => o.defender === a.piece);
      if (!opt) throw new Error(`X${a.piece + 1} cannot contest this shot`);
      if (s.stage === 'reaction') s = W_(spend(s, side), { turn_n: s.turn_n + 1 });   // D-18: the reaction's last action, a token
      return contestOutcome(s, opt, s.forced);
    }
    if (!TOKEN_FREE.has(k)) s = spend(s, side);
    if (k === 'forfeit') s = side === 'O' ? W_(s, { tok_o: 0 }) : W_(s, { tok_x: 0 });
    if (k === 'end_turn' || k === 'forfeit') return after(state, s, side, k);
    if (side === 'X' && s.pending && !isInboundPass(state)) {
      const answering = k === 'intercept' || (MOVEMENT.has(k) && mtiApproach(state, a));
      if (!answering) { const ph = s.phase; s = completePass(s); if (s.phase !== ph) return s; }
    }
    if (MOVEMENT.has(k)) {
      if (side === 'O') {
        s = W_(s, { o: setAt(s.o, a.piece, a.dest) });
        if (screenOf(s, a.piece)) s = W_(s, { screens: s.screens.filter(x => x[0] !== a.piece) });
        if (k === 'move' && state.turn_n === 0 && state.side === 'O' && state.stage === 'play') s = W_(s, { turn_lead: a.piece });
      } else {
        const arr = s.arrows.slice();
        if (k === 'move') arr[a.piece] = a.arrow;
        else if (k === 'sprint') {
          const st = state.x[a.piece], dx = SX[a.dest] - SX[st], dy = SY[a.dest] - SY[st], n = Math.max(Math.abs(dx), Math.abs(dy));
          arr[a.piece] = STEPDIR.get((dx / n) * WID + dy / n);
        }
        s = W_(s, { x: setAt(s.x, a.piece, a.dest), arrows: arr });
        if (state.stage === 'reaction' && a.dest !== state.x[a.piece]) s = W_(s, { react_moved: s.react_moved | (1 << a.piece) });
        if (mtiApproach(state, a)) s = W_(s, { approach: a.piece });
        if (state.pending) s = W_(s, { turn_moved: s.turn_moved | (1 << a.piece) });
      }
      if (k === 'move' || k === 'sprint') s = side === 'O' ? W_(s, { moved_o: s.moved_o | (1 << a.piece) }) : W_(s, { moved_x: s.moved_x | (1 << a.piece) });
      if (k === 'qs' || k === 'sprint') {
        s = inc(s, side, 'qs');
        s = side === 'O' ? W_(s, { qs_o: s.qs_o | (1 << a.piece) }) : W_(s, { qs_x: s.qs_x | (1 << a.piece) });
      }
      if (controlOn(s.ctx)) {                            // D-151: a Quick Step or a Sprint leaves him rushed; a Move restores control
        const sh = 2 * a.piece, code = k === 'move' ? 0 : (k === 'sprint' ? 2 : 1);
        if (side === 'O') s = W_(s, { rush_o: (s.rush_o & ~(3 << sh)) | (code << sh) });
        else s = W_(s, { rush_x: (s.rush_x & ~(3 << sh)) | (code << sh) });
      }
      return after(state, s, side, k);
    }
    s = inc(s, side, k);
    const O = s.ctx.off, X = s.ctx.dfn;
    if (k === 'pass') return after(state, W_(s, { pending: [a.piece, a.target], approach: -1 }), side, k);
    if (k === 'screen') {
      const scr = s.screens.concat([[a.piece, a.target, true, 0]]);
      scr.sort((p, q) => p[0] - q[0] || p[1] - q[1] || (p[2] === q[2] ? 0 : p[2] ? 1 : -1) || p[3] - q[3]);
      return after(state, W_(s, { screens: scr }), side, k);
    }
    if (k === 'hesitate' || k === 'pause') return after(state, s, side, k);
    if (k === 'shot') {
      s = W_(s, { stage: 'reaction', shot: a.shot, side: 'X', turn_n: 0 });
      if (s.tok_x <= 0) return resolveShot(s);
      return s;
    }
    if (k === 'dribble') {
      const t = O[s.ball].r.dribble - X[a.target].r.agility;
      const nb = s.beaten.filter(b => !(b[0] === s.ball && b[1] === a.target)).concat([[s.ball, a.target]]);
      nb.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
      const win = W_(lock(s, 'X', a.target), { beaten: nb });
      const lose = lock(s, 'O', s.ball);
      return chance([[pS(t), 'success', after(state, win, side, k)], [pNot(t), 'failure', after(state, lose, side, k)]]);
    }
    if (k === 'intercept') {
      const passer = s.pending[0], j = a.piece;
      const t = O[passer].r.pass - X[j].r.intercept;
      const ok = completePass(W_(s, { moved_x: s.moved_x | (1 << j) }));
      const okNode = ok.phase !== s.phase ? ok : after(state, ok, side, k);
      let back = s;
      if (state.turn_x) {
        const sx = state.turn_x[0], sa = state.turn_x[1];
        back = W_(s, { x: setAt(s.x, j, sx[j]), arrows: setAt(s.arrows, j, sa[j]) });
      }
      const lost = pickoff(W_(back, { pending: null, approach: -1, moved_x: back.moved_x | (1 << j) }));
      const lostNode = lost.stage === 'over' ? lost : after(state, lost, side, k);
      return chance([[pS(t), 'success', okNode], [pNot(t), 'failure', lostNode]]);
    }
    if (k === 'challenge') {
      const t = O[a.target].r.screen - X[a.piece].r.challenge;
      const holds = lock(s, 'X', a.piece);
      const fails = W_(s, { screens: s.screens.filter(x => x[0] !== a.target) });
      return chance([[pS(t), 'success', after(state, holds, side, k)], [pNot(t), 'failure', after(state, fails, side, k)]]);
    }
    if (k === 'steal') {
      const carrier = s.ball, fk = X[a.piece].r.foul_steal, tk = O[carrier].r.dribble - X[a.piece].r.steal;
      // D-89: every steal foul is +5; on a shooter it is a shooting foul, free throws only (step 7)
      const fs = W_(s, { fouls: s.fouls + 1, bonus5: s.bonus5 + (s.stage === 'reaction' ? 0 : 1) });
      let foulNode, stolenNode;
      if (s.stage === 'reaction') {
        const pts = shotPoints(s.o[carrier]), card = O[carrier];
        const rating = shotRating(s, carrier, s.shot);   // D-151
        const [fpts, and1] = footPoints(card, s.shot, pts, rating);
        foulNode = terminal(fs, Result('free_throws', carrier, s.shot, pts, rating, 0, a.piece, 0, fpts, and1));
        if (s.ctx.digital) {
          stolenNode = terminal(W_(s, { tos: s.tos + 1 }), Result('steal', carrier, s.shot, pts), true);
        } else {
          const cnt = s.cnt.slice(); cnt[5] = Math.max(0, cnt[5] - 1);
          const st = pickoff(W_(s, { stage: 'play', shot: null, cnt }));
          stolenNode = st.stage === 'over' ? st : after(W_(state, { stage: 'play' }), st, side, k);
        }
      } else {
        const inBonus = s.ctx.digital ? (s.ctx.team_fouls + fs.fouls >= s.ctx.bonus_from) : fs.fouls >= 2;
        if (inBonus) foulNode = terminal(fs, Result('free_throws', carrier, '', 2, 0, 0, a.piece, 0, freeThrows(O[carrier], 2)));
        else foulNode = after(state, fs, side, k);
        const st = pickoff(s);
        stolenNode = st.stage === 'over' ? st : after(state, st, side, k);
      }
      const keptNode = after(state, lock(s, 'X', a.piece), side, k);
      const inner = chance([[pS(tk), 'kept', keptNode], [pNot(tk), 'stolen', stolenNode]]);
      const pf = clampT(fk) / 20, pn = (20 - clampT(fk)) / 20;
      if (foulRolls(s.x[a.piece], s.o[carrier]) === 2) {
        const second = chance([[pf, 'foul', foulNode], [pn, 'no foul', inner]]);
        return chance([[pf, 'foul', foulNode], [pn, 'no foul', second]]);
      }
      return chance([[pf, 'foul', foulNode], [pn, 'no foul', inner]]);
    }
    throw new Error(`unknown action ${k}`);
  }

  // ---- decide: reach (B1) -----------------------------------------------------------------------------------------
  const INF = 99;
  const _GP = new Map();
  function geoPaths(kind, frm, qs) {                    // decide._geo_paths: Map dest -> run direction (-1 none)
    const key = (frm * 8 + qs) * 3 + (kind === 'move' ? 0 : kind === 'qs' ? 1 : 2);
    let hit = _GP.get(key); if (hit) return hit;
    let raw;
    if (kind === 'move') raw = movePaths(frm).map(p => [-1, p]);
    else if (kind === 'qs') raw = qsPaths(frm, qs).map(p => [-1, p]);
    else raw = sprintPaths(frm, qs);
    hit = new Map();
    for (const [dr, p] of raw) {
      let ok = true; for (const q of p) if (!ONB[q]) { ok = false; break; }
      const dest = p[p.length - 1];
      if (ok && !hit.has(dest)) hit.set(dest, dr);
    }
    _GP.set(key, hit); return hit;
  }
  const EMPTY = new Map();
  const _GR = new Map();
  function geoReach(frm, arrow, qs, canMove, qsLeft) {
    const key = ((((frm * 8 + arrow) * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3) + qsLeft;
    let hit = _GR.get(key); if (hit) return hit;
    const free = new Map(), fixed = new Map([[frm, new Map([[arrow, 0]])]]);
    const addFree = (q, n) => { const c = free.get(q); if (c === undefined || c > n) free.set(q, n); };
    const addFixed = (q, a, n) => { let cur = fixed.get(q); if (!cur) { cur = new Map(); fixed.set(q, cur); } const c = cur.get(a); if (c === undefined || c > n) cur.set(a, n); };
    const qsOk = qsLeft >= 1 && qs > 0;
    const moves = canMove ? geoPaths('move', frm, qs) : EMPTY;
    const qss = qsOk ? geoPaths('qs', frm, qs) : EMPTY;
    const sprints = canMove && qsOk ? geoPaths('sprint', frm, qs) : EMPTY;
    if (canMove) {
      addFree(frm, 1);
      for (const q of moves.keys()) { addFree(q, 1); if (qsOk) for (const q2 of geoPaths('qs', q, qs).keys()) addFree(q2, 2); }
    }
    for (const q of qss.keys()) { addFixed(q, arrow, 1); if (canMove) for (const q2 of geoPaths('move', q, qs).keys()) addFree(q2, 2); }
    for (const [q, dr] of sprints) addFixed(q, dr, 1);
    hit = [free, fixed]; _GR.set(key, hit); return hit;
  }
  function caps(s, side, i) {
    if (tokens(s, side) <= 0) return [false, 0];
    const canMove = !hasMoved(s, side, i) && !isLocked(s, side, i);
    if (side === 'O' && i === s.ctx.inbounder && s.inbound) return [false, 0];
    let qsLeft = LIMITS[side].qs - count(s, side, 'qs');
    qsLeft = quickStepped(s, side, i) ? 0 : Math.min(qsLeft, 1);
    return [canMove, qsLeft];
  }
  // Step 13 (a speed-up that changes no result): a defender's exact reach depends only on his own square, arrow and
  // what he has left, on the pieces standing on the squares his paths can cross (his envelope) and on the screens. It
  // is kept under exactly that key, so it is computed once for a position (every lane and contest of every reading
  // of it shares the answer) and it survives any move that doesn't touch his envelope: the reach map, updated only
  // where a move changes it. The answer also carries its one-action squares (.one) and its contest map (.cm).
  const _ENV = new Map();
  function reachEnvelope(start, qs, canMove, qsLeft, two) {      // every square a path of his may cross (Uint8Array by cell)
    const key = (((start * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3 + qsLeft) * 2 + (two ? 1 : 0);
    let env = _ENV.get(key); if (env) return env;
    env = new Uint8Array(ONB.length);
    const hop = (frm, kind) => {
      const out = [];
      const raw = kind === 'move' ? movePaths(frm) : kind === 'qs' ? qsPaths(frm, qs) : sprintPaths(frm, qs).map(r => r[1]);
      for (const p of raw) {
        let on = true; for (const q of p) if (!ONB[q]) { on = false; break; }
        if (!on) continue;
        for (const q of p) env[q] = 1;
        out.push(p[p.length - 1]);
      }
      return out;
    };
    // the same hops as defenderReachBuild, with nothing in the way
    const moves = canMove ? hop(start, 'move') : [];
    const qss = qsLeft >= 1 && qs > 0 ? hop(start, 'qs') : [];
    if (canMove && qsLeft >= 1) hop(start, 'sprint');
    if (two) {
      if (qsLeft >= 1 && qs > 0) { for (const m of moves) hop(m, 'qs'); }
      if (canMove) for (const q1 of qss) hop(q1, 'move');
    }
    _ENV.set(key, env); return env;
  }
  let REACH = new Map(), REACH_OLD = new Map();
  const REACH_STATS = { calls: 0, same_state: 0, kept: 0, built: 0 };
  // Step 13: the speed-ups that change no result. Each can be turned off by a tool (setSpeed), to time it and to prove
  // the search gives the same choices and values with and without it. All are on in play.
  const SPEED = { reach_cache: true, forcing: true, quiet_read: true, tt_order: true, two_direct: true, two_bound: true, path_block: true };
  function setSpeed(json) {
    const q = typeof json === 'string' ? JSON.parse(json) : json;
    for (const k in SPEED) if (q[k] !== undefined) SPEED[k] = q[k] === true || q[k] === 'true';
    REACH = new Map(); REACH_OLD = new Map();
    return Object.assign({}, SPEED);
  }
  function defenderReachExact(s, d) {
    if (!SPEED.reach_cache) return defenderReachBuild(s, d);
    REACH_STATS.calls++;
    const memo = s._dre || (s._dre = [null, null, null, null, null]);
    if (memo[d]) { REACH_STATS.same_state++; return memo[d]; }
    const start = s.x[d], qs = s.ctx.dfn[d].qs;
    let key;
    if (s.tok_x <= 0) key = 'n' + start + ',' + s.arrows[d];
    else {
      let qsLeft = 2 - count(s, 'X', 'qs');
      if (quickStepped(s, 'X', d)) qsLeft = 0;
      qsLeft = Math.min(qsLeft, 1);
      const canMove = !hasMoved(s, 'X', d) && !isLocked(s, 'X', d), two = s.tok_x >= 2;
      const env = reachEnvelope(start, qs, canMove, qsLeft, two);
      const occ = [];
      for (let i = 0; i < 5; i++) { const q = s.o[i]; if (env[q]) occ.push(q); }
      for (let j = 0; j < 5; j++) { const q = s.x[j]; if (j !== d && env[q]) occ.push(q); }
      occ.sort((a, b) => a - b);
      // the true Quick Steps left decide the second action (qsLeft >= 2 in the build is never true: it is capped at 1)
      key = start + ',' + s.arrows[d] + ',' + qs + ',' + (canMove ? 1 : 0) + qsLeft + (two ? 1 : 0) + '|' + occ.join(',');
      if (s.screens.length) key += '|' + s.screens.map(sc => tSquare(s, sc) + ':' + ((sc[3] >> d) & 1)).join(',');
    }
    let hit = REACH.get(key);
    if (hit === undefined) {
      hit = REACH_OLD.get(key);
      if (hit === undefined) { hit = defenderReachBuild(s, d); REACH_STATS.built++; } else REACH_STATS.kept++;
      if (REACH.size >= 4000) { REACH_OLD = REACH; REACH = new Map(); }
      REACH.set(key, hit);
    } else REACH_STATS.kept++;
    memo[d] = hit;
    return hit;
  }
  function defenderReachBuild(s, d) {                   // solver.defender_reach(s, d, 2), as action counts
    const start = s.x[d], arrow = s.arrows[d];
    const free = new Map(), fixed = new Map([[start, new Map([[arrow, 0]])]]);
    if (s.tok_x <= 0) return [free, fixed];
    const qs = s.ctx.dfn[d].qs;
    const occ = new Set(occupied(s)); occ.delete(start);
    const scr = s.screens.map(sc => [tSquare(s, sc), ((sc[3] >> d) & 1) === 1]);
    let qsLeft = 2 - count(s, 'X', 'qs');
    if (quickStepped(s, 'X', d)) qsLeft = 0;
    qsLeft = Math.min(qsLeft, 1);
    const canMove = !hasMoved(s, 'X', d) && !isLocked(s, 'X', d);
    const two = s.tok_x >= 2;
    const ok = (frm, path) => {
      if (scr.length) {
        let prev = frm;
        for (const q of path) { for (const [tsq, beat] of scr) if (!beat && diagStepBanned(prev, q, tsq)) return false; prev = q; }
        for (const [tsq, beat] of scr) if (beat && path[path.length - 1] === tsq) return false;
      }
      return true;
    };
    const dests = (frm, kind) => {
      const out = new Map();
      let raw;
      if (kind === 'move') raw = movePaths(frm).map(p => [-1, p]);
      else if (kind === 'qs') raw = qsPaths(frm, qs).map(p => [-1, p]);
      else raw = sprintPaths(frm, qs);
      for (const [dr, p] of raw) {
        let on = true; for (const q of p) if (!ONB[q]) { on = false; break; }
        if (!on) continue;
        const dest = p[p.length - 1];
        if (out.has(dest)) continue;
        let dis = true; for (const q of p) if (occ.has(q)) { dis = false; break; }
        if (dis && (!scr.length || ok(frm, p))) out.set(dest, dr);
      }
      return out;
    };
    const addFixed = (q, a, n) => { let cur = fixed.get(q); if (!cur) { cur = new Map(); fixed.set(q, cur); } const c = cur.get(a); if (c === undefined || n < c) cur.set(a, n); };
    const addFree = (q, n) => { const c = free.get(q); if (c === undefined || n < c) free.set(q, n); };
    const moves = canMove ? dests(start, 'move') : EMPTY;
    const qss = qsLeft >= 1 && qs > 0 ? dests(start, 'qs') : EMPTY;
    const sprints = canMove && qsLeft >= 1 ? dests(start, 'sprint') : EMPTY;
    if (canMove) addFree(start, 1);
    for (const q of moves.keys()) addFree(q, 1);
    for (const q of qss.keys()) addFixed(q, arrow, 1);
    for (const [q, dr] of sprints) addFixed(q, dr, 1);
    if (two) {
      if (qsLeft >= 1 && qs > 0) {
        const ms = [...moves.keys()]; if (canMove) ms.push(start);
        for (const m of ms) for (const q of dests(m, 'qs').keys()) addFree(q, 2);
      }
      for (const q1 of qss.keys()) {
        if (canMove) for (const q of dests(q1, 'move').keys()) addFree(q, 2);
        if (qsLeft >= 2) {
          for (const q of dests(q1, 'qs').keys()) addFixed(q, arrow, 2);
          if (canMove) for (const [q, dr] of dests(q1, 'sprint')) addFixed(q, dr, 2);
        }
      }
      if (qsLeft >= 2 && qs > 0) for (const [q1, dr1] of sprints) for (const q of dests(q1, 'qs').keys()) addFixed(q, dr1, 2);
    }
    return [free, fixed];
  }
  function defenderMap(s, d, exact) {
    if (exact) return defenderReachExact(s, d);
    const [canMove, qsLeft] = caps(s, 'X', d);
    if (s.tok_x <= 0) return [new Map(), new Map([[s.x[d], new Map([[s.arrows[d], 0]])]])];
    return geoReach(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, canMove, qsLeft);
  }
  function attackerReach(s, i) {
    const out = new Map([[s.o[i], 0]]);
    const [canMove, qsLeft] = caps(s, 'O', i);
    if (!ONB[s.o[i]] || s.tok_o <= 0) return out;
    const [free, fixed] = geoReach(s.o[i], 0, s.ctx.off[i].qs, canMove, qsLeft);
    for (const [q, n] of free) if (!out.has(q)) out.set(q, n);
    for (const [q, arrs] of fixed) {
      let n = INF; for (const v of arrs.values()) if (v < n) n = v;
      const c = out.get(q); if (c === undefined || c > n) out.set(q, n);
    }
    const res = new Map();
    for (const [q, n] of out) if (n === 0 || !occAt(s, q)) res.set(q, n);
    return res;
  }
  // ---- step 12: the reach map (reach.py) --------------------------------------------------------------------------
  const reachOn = () => !!D.config.eval.reach;
  function geoDests(kind, frm, qs) {                   // decide._geo_paths: destinations ignoring other pieces
    const raw = kind === 'move' ? movePaths(frm) : qsPaths(frm, qs);
    const out = new Set();
    for (const p of raw) if (p.every(q => ONB[q])) out.add(p[p.length - 1]);
    return out;
  }
  function attackerReachExact(s, i) {                  // decide.attacker_reach(exact=True)
    const out = new Map([[s.o[i], 0]]);
    const [canMove] = caps(s, 'O', i);
    if (!ONB[s.o[i]] || s.tok_o <= 0) return out;
    const card = s.ctx.off[i];
    for (const kind of ['move', 'qs', 'sprint']) {
      if (!canMoveKind(s, 'O', i, kind)) continue;
      for (const q of movementDests(s, 'O', i, kind).keys()) if (!out.has(q)) out.set(q, 1);
    }
    if (s.tok_o >= 2) {
      const ones = [...out].filter(([, n]) => n === 1).map(([q]) => q);
      for (const q of ones) for (const q2 of geoDests(canMove ? 'qs' : 'move', q, card.qs)) {
        if (!out.has(q2) && !s.x.includes(q2) && !s.o.includes(q2)) out.set(q2, 2);
      }
    }
    return out;
  }
  // Step 13 B2 (decide.two_actions): the squares attacker i reaches with exactly two movement actions (a Move then a
  // Quick Step, or a Quick Step then a Move), each by the rules' own movement from where the first leaves him. Sorted.
  function twoActions(s, i, one, keep) {               // keep(square): only these are wanted
    if (s.tok_o < 2 || !ONB[s.o[i]]) return [];
    const bit = 1 << i, out = new Set(), old = s.o[i], card = s.ctx.off[i], carrier = i === s.ball;
    // step 13C (a speed-up that changes no result): the second action is read straight from the paths and the pieces,
    // with his own square moved, instead of building a new position for every first square. The plain way is kept
    // for the tools (SPEED.two_direct off) and for an attacker holding a screen.
    const plain = !SPEED.two_direct || s.screens.some(sc => sc[0] === i);
    for (const [first, second] of [['move', 'qs'], ['qs', 'move']]) {
      if (!canMoveKind(s, 'O', i, first)) continue;
      let can2 = null;
      for (const q1 of movementDests(s, 'O', i, first).keys()) {
        if (plain || can2 === null) {
          const s2 = W_(s, first === 'move' ? { o: setAt(s.o, i, q1), moved_o: s.moved_o | bit } : { o: setAt(s.o, i, q1), qs_o: s.qs_o | bit });
          can2 = canMoveKind(s2, 'O', i, second);         // the same for every first square: it reads no position
          if (plain) {
            if (can2) for (const q2 of movementDests(s2, 'O', i, second).keys()) if (!one.has(q2) && (!keep || keep(q2))) out.add(q2);
            continue;
          }
        }
        if (!can2) break;
        let zones = null;                                  // the zones of the defenders next to his new square
        if (carrier) {
          for (let j = 0; j < 5; j++) {
            if (!adjacent(s.x[j], q1) || s.beaten.some(b => b[0] === i && b[1] === j)) continue;
            const z = zoneOf(s, j, old, q1);
            if (z.length) zones = zones ? zones.concat(z) : z;
          }
        }
        for (const path of (second === 'qs' ? qsPaths(q1, card.qs) : movePaths(q1))) {
          const dest = path[path.length - 1];
          if (one.has(dest) || out.has(dest) || (keep && !keep(dest))) continue;
          let ok = true;
          for (const q of path) if (!ONB[q] || q === q1 || (q !== old && occAt(s, q))) { ok = false; break; }
          if (ok && zones) for (let n = 0; n < path.length - 1; n++) if (zones.includes(path[n])) { ok = false; break; }
          if (ok) out.add(dest);
        }
      }
    }
    return [...out].sort((a, b) => (SX[a] - SX[b]) || (SY[a] - SY[b]));
  }
  // decide.lp_max: maximise c.x subject to A.x <= b, x >= 0, every b >= 0; the simplex method, Bland's rule, the same
  // steps as the Python
  function lpMax(c, A, b) {
    const m = A.length, n = c.length, W = n + m + 1;
    const T = A.map((row, r) => { const t = new Float64Array(W); for (let k = 0; k < n; k++) t[k] = row[k]; t[n + r] = 1.0; t[W - 1] = b[r]; return t; });
    const obj = new Float64Array(W); for (let k = 0; k < n; k++) obj[k] = -c[k];
    const basis = []; for (let r = 0; r < m; r++) basis.push(n + r);
    for (let it = 0; it < 500; it++) {
      let col = -1;
      for (let k = 0; k < n + m; k++) if (obj[k] < -1e-12) { col = k; break; }
      if (col < 0) break;
      let row = -1, best = 0.0;
      for (let r = 0; r < m; r++) {
        if (T[r][col] > 1e-12) {
          const ratio = T[r][W - 1] / T[r][col];
          if (row < 0 || ratio < best - 1e-12 || (ratio <= best + 1e-12 && basis[r] < basis[row])) { row = r; best = ratio; }
        }
      }
      if (row < 0) break;
      const pr = T[row], pv = pr[col];
      for (let k = 0; k < W; k++) pr[k] = pr[k] / pv;
      for (let r = 0; r < m; r++) {
        if (r !== row && T[r][col] !== 0.0) { const tr = T[r], f = tr[col]; for (let k = 0; k < W; k++) tr[k] = tr[k] - f * pr[k]; }
      }
      const f = obj[col];
      for (let k = 0; k < W; k++) obj[k] = obj[k] - f * pr[k];
      basis[row] = col;
    }
    const x = new Float64Array(n);
    for (let r = 0; r < m; r++) if (basis[r] < n) x[basis[r]] = T[r][W - 1];
    return [obj[W - 1], x];
  }
  function minCounts(free, fixed) {
    const out = new Map(free);
    for (const [q, arrs] of fixed) { let n = INF; for (const v of arrs.values()) if (v < n) n = v; const c = out.get(q); if (c === undefined || c > n) out.set(q, n); }
    return out;
  }
  function playerReach(s, side, i) { return side === 'X' ? minCounts(...defenderReachExact(s, i)) : attackerReachExact(s, i); }
  function reachMap(s) {                               // {side+i: Map(square -> [this phase, next phase, earliest turn])}
    const fresh = newPhase(s, s.clock), out = {};
    for (const side of ['O', 'X']) for (let i = 0; i < 5; i++) {
      const start = (side === 'O' ? s.o : s.x)[i];
      const cur = playerReach(s, side, i), nxt = playerReach(fresh, side, i), row = new Map();
      for (const q of new Set([...cur.keys(), ...nxt.keys()])) {
        const a = cur.has(q) ? cur.get(q) : null, b = nxt.has(q) ? nxt.get(q) : null;
        row.set(q, [a, b, q === start ? 0 : a !== null ? 1 : b !== null ? 2 : null]);
      }
      out[side + i] = row;
    }
    return out;
  }
  const _PT = new Map();
  function pathsTo(start, c, qs) {                     // reach.paths_to: movement geometry from start ending on c
    const key = (start * 4096 + c) * 8 + qs; let hit = _PT.get(key); if (hit) return hit;
    hit = [];
    const ok = p => p[p.length - 1] === c && p.every(q => ONB[q]);
    for (const p of movePaths(start)) if (ok(p)) hit.push(p);
    for (const p of qsPaths(start, qs)) if (ok(p)) hit.push(p);
    for (const [, p] of sprintPaths(start, qs)) if (ok(p)) hit.push(p);
    _PT.set(key, hit); return hit;
  }
  function blocksPath(q, start, c, qs) {
    if (q === c) return true;
    const ps = pathsTo(start, c, qs);
    if (!SPEED.path_block) return ps.length > 0 && ps.every(p => p.slice(0, -1).includes(q));
    // step 13C (a speed-up that changes no result): the squares every path crosses, worked out once per pair of squares
    let blk = ps.block;
    if (blk === undefined) {
      blk = new Set();
      if (ps.length) for (const x of ps[0].slice(0, -1)) if (ps.every(p => p.slice(0, -1).includes(x))) blk.add(x);
      ps.block = blk;
    }
    return blk.has(q);
  }
  const PATH_ROUTES = new Set(['drive', 'later', 'cut']);
  // step 16: the cards' bands as tiers; the paint (the zone of layups, dunks and post shots) and its squares
  const BAND = { L: 0, A: 1, H: 2 }, ADV_KINDS = ['separation', 'mismatch', 'numbers', 'penetration'];
  const PAINT = ZONE_SHOTS.findIndex(z => z.includes('layup'));
  let _PSQ = null;
  const paintSquares = () => { if (!_PSQ) { _PSQ = []; for (let c = 0; c < ONB.length; c++) if (ONB[c] && ZN[c] === PAINT) _PSQ.push(c); _PSQ.sort((a, b) => (SX[a] - SX[b]) || (SY[a] - SY[b])); } return _PSQ; };
  function exactOne(s, d) {                            // decide._exact_one, as the bitset oneAction returns
    const r = defenderReachExact(s, d);
    if (r.one) return r.one;
    const [free, fixed] = r, hit = new Uint32Array(8);
    const put = q => { const b = BI[q]; if (b >= 0) hit[b >> 5] |= 1 << (b & 31); };
    put(s.x[d]);
    for (const [q, n] of free) if (n <= 1) put(q);
    for (const [q, arr] of fixed) { let m = INF; for (const v of arr.values()) if (v < m) m = v; if (m <= 1) put(q); }
    if (SPEED.reach_cache) r.one = hit;
    return hit;
  }
  // attackerReach's squares within one action, in its order, from geometry alone (the occupancy filter is per state)
  const _RL = new Map();
  function reachList(frm, qs, canMove, qsLeft) {
    const key = (((frm * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3) + qsLeft;
    let hit = _RL.get(key); if (hit) return hit;
    const out = new Map([[frm, 0]]);
    const [free, fixed] = geoReach(frm, 0, qs, canMove, qsLeft);
    for (const [q, n] of free) if (!out.has(q)) out.set(q, n);
    for (const [q, arrs] of fixed) {
      let n = INF; for (const v of arrs.values()) if (v < n) n = v;
      const c = out.get(q); if (c === undefined || c > n) out.set(q, n);
    }
    const lst = [];
    for (const [q, n] of out) if (n <= 1) lst.push(q, n);
    hit = Int16Array.from(lst); _RL.set(key, hit); return hit;
  }
  // contest kinds (penalty, foul roll, two foul rolls): KINDS order of decide.py
  const KPEN = [false, false, false, true, true, true], KFOUL = [false, true, true, false, true, true], KTWO = [false, false, true, false, true, false];
  function kindOf(q, c, pen, foul) {
    if (pen) return foul ? 4 : 3;
    if (!foul) return 0;
    return DR[q] >= DR[c] ? 2 : 1;
  }
  function contestMap(free, fixed) {                    // Int8Array(board index * 6 + kind): fewest actions
    const out = new Int8Array(NB * 6).fill(INF);
    const put = (q, a, n, anyArrow) => {
      for (let d = 0; d < 8; d++) {
        const c = q + DSTEP[d];
        if (!ONB[c]) continue;
        const foul = anyArrow ? false : d !== a;
        const k = BI[c] * 6 + kindOf(q, c, DR[q] > DR[c], foul);
        if (out[k] > n) out[k] = n;
      }
    };
    for (const [q, n] of free) put(q, -1, n, true);
    for (const [q, arrs] of fixed) for (const [a, n] of arrs) put(q, a, n, false);
    // the kinds he reaches within 0, 1 or 2 reaction actions, per square (bit k = KINDS[k])
    out.masks = [0, 1, 2].map(react => {
      const m = new Uint8Array(NB);
      for (let b = 0; b < NB; b++) { let v = 0; for (let k = 0; k < 6; k++) if (out[b * 6 + k] <= react) v |= 1 << k; m[b] = v; }
      return m;
    });
    return out;
  }
  const _CM = new Map();
  function cmapCached(frm, arrow, qs, canMove, qsLeft) {
    const key = ((((frm * 8 + arrow) * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3) + qsLeft;
    let hit = _CM.get(key); if (hit) return hit;
    const [free, fixed] = geoReach(frm, arrow, qs, canMove, qsLeft);
    hit = contestMap(free, fixed); _CM.set(key, hit); return hit;
  }

  // ---- decide: lanes and passes -----------------------------------------------------------------------------------
  const _LS = new Map();
  function laneSquares(a, c) {                         // tol 0.5 (both uses): Set of squares strictly between a and c
    const key = a * 4096 + c; let hit = _LS.get(key); if (hit) return hit;
    hit = [];
    const vx = SX[c] - SX[a], vy = SY[c] - SY[a], L2 = vx * vx + vy * vy;
    if (L2 !== 0) {
      for (let x = Math.min(SX[a], SX[c]); x <= Math.max(SX[a], SX[c]); x++) {
        for (let y = Math.min(SY[a], SY[c]); y <= Math.max(SY[a], SY[c]); y++) {
          const p = C(x, y);
          if (p === a || p === c) continue;
          const wx = x - SX[a], wy = y - SY[a], dot = wx * vx + wy * vy;
          if (dot <= 0 || dot >= L2) continue;
          const cross = vx * wy - vy * wx;
          if (cross * cross < 0.25 * L2) hit.push(p);
        }
      }
    }
    hit = new Set(hit); hit.bi = Int16Array.from([...hit].map(q => BI[q])); _LS.set(key, hit); return hit;
  }
  const _OA = new Map();
  function oneAction(frm, arrow, qs, canMove, qsLeft) {
    const key = ((((frm * 8 + arrow) * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3) + qsLeft;
    let hit = _OA.get(key); if (hit) return hit;
    const [free, fixed] = geoReach(frm, arrow, qs, canMove, qsLeft);
    hit = new Uint32Array(8);
    const put = q => { const b = BI[q]; if (b >= 0) hit[b >> 5] |= 1 << (b & 31); };
    put(frm);
    for (const [q, n] of free) if (n <= 1) put(q);
    for (const [q, arr] of fixed) { let m = INF; for (const v of arr.values()) if (v < m) m = v; if (m <= 1) put(q); }
    _OA.set(key, hit); return hit;
  }
  function laneP(s, i, c, reach) {
    const a = s.o[s.ball];
    if (!(ONB[a] && ONB[c])) return 0;
    const den = laneSquares(a, c);
    for (const xp of s.x) if (den.has(xp) && adjacent(xp, c)) return 0;
    const lane = den;
    if (!lane.size) return 1;
    const passer = s.ctx.off[s.ball].r.pass;
    let worst = 0;
    const exact = reach === undefined ? reachOn() : reach;
    for (let d = 0; d < 5; d++) {
      const [canMove, qsLeft] = caps(s, 'X', d);
      const one = exact ? exactOne(s, d) : oneAction(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, canMove, qsLeft);
      let hit = false; for (const b of lane.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { hit = true; break; }
      if (!hit) continue;
      const pi = 1 - pS(passer - s.ctx.dfn[d].r.intercept);
      if (pi > worst) worst = pi;
    }
    return 1 - worst;
  }
  function passProb(s, i) {
    const st = W_(s, { side: 'O', stage: 'play', turn_n: 0, tok_o: Math.max(1, s.tok_o), pending: null });
    const a = A('pass', 'O', s.ball, -1, -1, i);
    try {
      if (!isLegal(st, a)) return 0;
      const nxt = apply(st, a);
      let worst = 0;
      if (!isChance(nxt) && nxt.stage === 'play' && nxt.side === 'X' && nxt.pending) {
        for (const b of legalActions(nxt)) {
          if (b.kind === 'intercept') worst = Math.max(worst, 1 - pS(s.ctx.off[s.ball].r.pass - s.ctx.dfn[b.piece].r.intercept));
        }
      }
      return 1 - worst;
    } catch (e) { return 0; }
  }

  // ---- team fouls across the quarter (F4) -------------------------------------------------------------------------
  const _FOUL = new Map();
  function foulTable(ctx) {
    let hit = _FOUL.get(ctx.id); if (hit) return hit;
    const q = D.config.eval.fouls_per_possession ?? 0.25;
    let ft2 = 0; for (const c of ctx.off) ft2 += 2 * c.r.free_throw; ft2 /= ctx.off.length;
    const cont = D.config.eval.play_on_value ?? 20.0;
    const extra = ft2 + 5 - (5 + cont);                   // D-89: the bonus foul is +5 as well
    const N = ctx.quarter_possessions + 1, F = ctx.bonus_from + 12;
    const Cm = []; for (let f = 0; f < F + 2; f++) Cm.push(new Float64Array(N + 1));
    for (let n = 1; n <= N; n++) for (let f = F; f >= 0; f--) {
      const x = f + 1 >= ctx.bonus_from ? extra : 0.0;
      Cm[f][n] = (1 - q) * Cm[f][n - 1] + q * (x + Cm[Math.min(F, f + 1)][n - 1]);
    }
    hit = [Cm, F]; _FOUL.set(ctx.id, hit); return hit;
  }
  function foulMarginal(ctx, f, n) {
    if (!ctx.digital || n <= 0) return 0.0;
    const [Cm, F] = foulTable(ctx), n1 = Math.max(0, n - 1);
    return Cm[Math.min(F, f + 1)][n1] - Cm[Math.min(F, f)][n1];
  }
  function foulExternality(s) {
    const ctx = s.ctx;
    if (!ctx.digital || !s.fouls || !ctx.quarter_left) return 0.0;
    let t = 0; for (let i = 0; i < s.fouls; i++) t += foulMarginal(ctx, ctx.team_fouls + i, ctx.quarter_left);
    return t;
  }

  // ---- the coarse table -------------------------------------------------------------------------------------------
  function capacityOf(s) {
    if (s.tok_x <= 0) return [0, 0];
    let per = 0, paint = 0;
    for (let j = 0; j < 5; j++) {
      const q = s.x[j];
      const canMove = !((s.moved_x >> j) & 1) && !((s.lock_x >> j) & 1);
      const canQs = s.cnt[6] < 2 && !((s.qs_x >> j) & 1);
      if (!(canMove || canQs) || !ONB[q]) continue;
      if (ZN[q] === 1 || ZN[q] === 2) paint++; else per++;
    }
    return [Math.min(per, 3), Math.min(paint, 2)];
  }
  function coarseKey(s) {
    const bp = s.o[s.ball];
    let defended = 0; for (const xp of s.x) if (adjacent(xp, bp)) { defended = 1; break; }
    const z = ONB[bp] ? ZCH[ZN[bp]] : '.';
    const tok = s.tok_o <= 0 ? 0 : s.tok_o <= 2 ? 1 : s.tok_o <= 4 ? 2 : 3;
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    const cap = capacityOf(s);
    return [`${z}|${defended}|${phase}|${tok}`, `${cap[0]}${cap[1]}`, phase];
  }
  function vcoarse(s) {
    const tab = D.vcoarse[s.ctx.table] || D.vcoarse['senior/pro'] || {};
    const [short, cap, phase] = coarseKey(s);
    const k = short + '|' + cap;
    if (k in tab) return tab[k];
    if (short in tab) return tab[short];
    const pk = '_phase' + phase;
    return pk in tab ? tab[pk] : 0.0;
  }
  // step 10: the average continuation read of the phase table's own positions at this position's phase
  // (decide.relative_average); leaf_mode 'relative' reads a position against it
  function relativeAverage(s, budget) {
    const tab = (budget && D.config.eval.relative_average_budget) || D.config.eval.relative_average || {};
    const row = tab[s.ctx.table] || tab['senior/pro'] || {};
    const v = row[String(coarseKey(s)[2])];
    return v === undefined ? 0.0 : v;
  }
  function leafOf(s, banked, sn, now, cont, coarse, budget) {
    if ((D.config.eval.leaf_mode || 'floor') === 'relative') return banked + Math.max(sn || 0.0, now, coarse + cont - relativeAverage(s, budget));
    return banked + Math.max(sn || 0.0, now, cont, coarse);
  }
  function setLeafMode(mode) { D.config.eval.leaf_mode = mode; return mode; }
  // step 17: the learned judgement (eval.learned, off): what is left to earn, from the named readings and the weights
  // file (learned_weights.json): per phase, intercept + sum of weight x (reading - mean) / sd, in the file's order
  function setLearned(on) { D.config.eval.learned = on === true || on === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.learned; }
  const learnedOn = () => D.config.eval.learned === true && D.learned !== null;
  // step 17D: the calibrated reading (eval.calibrated; on by default since D-138): today's reading of what is left to earn, passed through a
  // map fitted to what positions went on to earn, per phase and side to act (the weights file's calibration block:
  // knots x -> y, straight lines between and beyond them)
  function setCalibrated(on) { D.config.eval.calibrated = on === true || on === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.calibrated; }
  // step 18b: eval.settle_shots (on by default since D-148). (1) A declared shot at the search's horizon is valued by playing the reaction out
  // (Searcher.settled); (2) D-145: no reading is above the ceiling, before or after the calibrated map.
  function setSettle(on) { D.config.eval.settle_shots = on === true || on === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.settle_shots; }
  const settleOn = () => D.config.eval.settle_shots === true;
  // The ceiling (decide.ceiling): the most the possession can still earn beyond what it has already earned, against the
  // defence's best reply: the best open shot any attacker's card can score (points x rating); with Coach's Call in
  // play the target's shot also earns the bonus for its look.
  function ceilingOf(s) {
    const ctx = s.ctx, tg = ctx.coach_call ? s.target : -1;
    if (ctx._ceil === undefined) ctx._ceil = new Map();
    let best = ctx._ceil.get(tg);
    if (best !== undefined) return best;
    best = 0.0;
    for (let i = 0; i < ctx.off.length; i++) {
      const card = ctx.off[i];
      let m = 0.0;
      for (let z = 1; z < ZONE_POINTS.length; z++) {
        const pts = ZONE_POINTS[z];
        for (const ty of ZONE_SHOTS[z]) { const v = pts * card.sh[ty]; if (v > m) m = v; }
      }
      if (ctx.coach_call && i === s.target) m = m + COACH_BONUS[band(m)];
      if (m > best) best = m;
    }
    ctx._ceil.set(tg, best);
    return best;
  }
  // step 18c: eval.help_readings (off). The floor: with the offence to act, a position is worth at least the best
  // shot the ball handler can release this turn, settled by the rules (Searcher.floor)
  function setHelp(on) { D.config.eval.help_readings = on === true || on === 'true'; return D.config.eval.help_readings; }
  const helpOn = () => D.config.eval.help_readings === true;
  let TABLETOP_MAP = true;                               // a measuring hook: false reads the table with the app's map
  function setTabletopMap(on) { TABLETOP_MAP = !(on === false || on === 'false'); READS = new Map(); READS_OLD = new Map(); return TABLETOP_MAP; }
  const calibratedOn = () => D.config.eval.calibrated === true && D.learned !== null && !!D.learned.calibration && !learnedOn();
  // step 18a: the map was fitted on Senior Pro play; another age and standard scales it by its own phase table value
  // over Senior Pro's at the same phase, as D-114 does for the averages (decide.calibration_scale). Senior Pro is 1.
  function calibrationScale(s, phase) {
    if (s.ctx.table === 'senior/pro') return 1.0;
    const own = D.vcoarse[s.ctx.table] || D.vcoarse['senior/pro'] || {}, base = D.vcoarse['senior/pro'] || {};
    const a = own['_phase' + phase], b = base['_phase' + phase];
    if (!a || !b || a <= 0 || b <= 0) return 1.0;
    return a / b;
  }
  function calibrate(s, oToAct, r) {
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    // D-141: under the table's rules, the table's own map (fitted on tabletop-rules play) when the file has one
    const cal = (!s.ctx.digital && TABLETOP_MAP && D.learned.calibration_tabletop) || D.learned.calibration;
    const m = cal.maps[String(phase) + (oToAct ? 'O' : 'X')];
    if (!m) return r;
    const q = calibrationScale(s, phase);
    if (q !== 1.0) r = r / q;
    const x = m.x, y = m.y, n = x.length;
    let v;
    if (n === 1) v = y[0];
    else {
      let k = 0;
      while (k < n - 2 && r > x[k + 1]) k++;
      v = y[k] + (y[k + 1] - y[k]) * (r - x[k]) / (x[k + 1] - x[k]);
    }
    return q === 1.0 ? v : q * v;
  }
  function learnedValue(s, f) {
    const m = D.learned.phases[String(Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1)))];
    if (!m) return null;
    let v = m.intercept;
    for (let i = 0; i < f.length; i++) v += m.weights[i] * (f[i] - m.mean[i]) / m.sd[i];
    return v;
  }
  // step 13 B: coverage as a budget (eval.coverage_budget, off by default)
  // step 16: the goals switches (eval.advantages, search.goals; both off by default)
  function setAdvantages(on) { D.config.eval.advantages = on === true || on === 'true'; return D.config.eval.advantages; }
  function setGoals(on) { D.config.search = D.config.search || {}; D.config.search.goals = on === true || on === 'true'; return D.config.search.goals; }
  function setBudget(on) { D.config.eval.coverage_budget = on === true || on === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.coverage_budget; }
  const budgetCfg = () => !!D.config.eval.coverage_budget;
  // step 12: the switches, for the tools (text 'true' / 'false')
  function setStable(on) { D.config.search = D.config.search || {}; D.config.search.stable = on === true || on === 'true'; return D.config.search.stable; }
  // Step 13: the stable search's five parts, each its own switch (off by default); search.stable is the shorthand
  // that turns on all five.
  const STABLE_PARTS = ['quiet_points', 'like_with_like', 'tempo', 'play_on', 'clear_reason'];
  function stableParts() {
    const sc = D.config.search || {}, every = sc.stable === true, out = {};
    for (const k of STABLE_PARTS) out[k] = every || sc[k] === true;
    return out;
  }
  // setSearch('{"quiet_points": true, ...}'): sets the named search switches (stable and the five parts)
  function setSearch(json) {
    const q = typeof json === 'string' ? JSON.parse(json) : json;
    D.config.search = D.config.search || {};
    for (const k of ['stable'].concat(STABLE_PARTS)) if (q[k] !== undefined) D.config.search[k] = q[k] === true || q[k] === 'true';
    return stableParts();
  }
  function setReach(on) { D.config.eval.reach = on === true || on === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.reach; }
  function turnoverValue(s) {
    if (s.ctx.digital || s.ctx.hold_for_one || s.clock <= 2) return Math.min(0, 5 * s.bonus5 - 5 * s.tos);   // D-82
    return 5 * s.bonus5 - 5 * (s.tos + 1) + vcoarse(W_(s, { clock: s.clock - 2 }));
  }

  // ---- decide: THREAT and COVERAGE (B2, B3) and the leaf (B4) -------------------------------------------------------
  const SHOOT = z => z !== 0;
  function makeLook(i, c, route, p, now, replies) {
    return { i, c, route, p, now, replies: replies == null ? (now ? 0 : 1) : replies, types: null, open: null, vals: null, minex: null, base: 0, rushed: false };
  }
  function finishLook(lk) {
    const nt = lk.types.length;
    const mx = lk.minex = new Float64Array(5 * nt);
    for (let j = 0; j < 5; j++) {
      for (let t = 0; t < nt; t++) {
        let v = lk.open[t];
        for (let d = 0; d < 5; d++) { const vals = lk.vals[d]; if (d !== j && vals && vals[t] < v) v = vals[t]; }
        mx[j * nt + t] = v;
      }
    }
    let best = 0.0;
    for (let t = 0; t < nt; t++) {
      let v = lk.open[t];
      for (let d = 0; d < 5; d++) { const vals = lk.vals[d]; if (vals && vals[t] < v) v = vals[t]; }
      best = Math.max(best, v);
    }
    lk.base = lk.p * best;
  }
  // Step 13 B3 (decide.Read.look_split), reporting only: a look's value as its finisher (the card: the value of his best
  // shot type there with nobody near) times its quality (the position: the chance it arrives and what the best Contest
  // leaves of it). [finisher, quality]; finisher x quality is the look's value.
  function lookSplit(lk) {
    let fin = 0.0; for (let t = 0; t < lk.open.length; t++) if (lk.open[t] > fin) fin = lk.open[t];
    return [fin, fin > 0 ? lk.base / fin : 0.0];
  }
  function swapped(lk, j, vals, p) {
    const mx = lk.minex, nt = lk.types.length, o = j * nt;
    let best = 0.0;
    for (let t = 0; t < nt; t++) {
      let v = mx[o + t];
      if (vals && vals[t] < v) v = vals[t];
      if (v > best) best = v;
    }
    return (p == null ? lk.p : p) * best;
  }
  function round6(x) {
    const y = x * 1e6, f = y - Math.floor(y);
    if (Math.abs(f - 0.5) < 1e-4) return parseFloat(x.toFixed(6));
    return Math.round(y) / 1e6;
  }
  const keyLess = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);

  const LEFT = new Float64Array(5);
  class Read {
    constructor(s, opts = {}) {
      this.s = s;
      this.exact = !!opts.exact;
      this.cfg = D.config.eval;
      this.k = opts.k != null ? opts.k : this.cfg.responses_per_defender;
      this.L = opts.looks_per || this.cfg.looks_per_attacker || 6;
      const att = opts.attention || [[0, 1, 2, 3, 4], [0, 1, 2, 3, 4]];
      this.att_o = att[0].slice(); this.att_x = att[1].slice();
      this.dcards = s.ctx.dfn;
      this.o_to_act = s.side === 'O' && s.stage === 'play';
      this.react = s.tok_x > 0 ? Math.min(2, s.tok_x) : 0;
      if (s.stage === 'reaction') this.react = Math.max(0, Math.min(2 - s.turn_n, s.tok_x));   // the reaction's actions so far count
      this.react_moves = this.react - 1;                  // D-18: the Contest is one of the reaction's actions
      this._cm = [0, 1, 2, 3, 4].map(d => this._contest(d));
      this.looks = new Array(5).fill(null);
      this.threat = new Array(5).fill(null);
      for (const i of this.att_o) this.looks[i] = this._looks(i);
      for (const i of this.att_o) this.threat[i] = this._best(this.looks[i]);
      this._cover = null;
      this._budget = null;
      this._adv = null;
    }
    _contest(d, at = -1, arrow = -1, used = null) {
      const s = this.s;
      if (!ONB[s.x[d]]) return null;
      if (at < 0 && (this.exact || reachOn())) {
        const r = defenderMap(s, d, true);
        if (r.cm) return r.cm;
        const cm = contestMap(r[0], r[1]);
        if (SPEED.reach_cache) r.cm = cm;
        return cm;
      }
      let [canMove, qsLeft] = caps(s, 'X', d);
      let frm = s.x[d], a = s.arrows[d];
      if (at >= 0) {
        frm = at; a = arrow;
        if (used === 'move') canMove = false;
        else if (used === 'qs' || used === 'sprint') { qsLeft = 0; canMove = canMove && used === 'qs'; }
        if (s.tok_x <= 2) { canMove = false; qsLeft = 0; }
      } else if (s.tok_x <= 0) {
        return contestMap(new Map(), new Map([[frm, new Map([[a, 0]])]]));
      }
      return cmapCached(frm, a, s.ctx.dfn[d].qs, canMove, qsLeft);
    }
    _vals(lk, d, cm, moves) {                   // moves (step 13C): at most that many reaction movements; 0 = where he stands
      if (!cm || this.react_moves < 0) return null;
      const mask = cm.masks[moves === undefined ? this.react_moves : Math.min(moves, this.react_moves)][BI[lk.c]];
      if (!mask) return null;
      const ctx = this.s.ctx;
      if (controlOn(ctx)) {
        // D-151 (rules.control), as the reading takes it (decide.Read._vals): the kinds he reaches standing are rushed
        // if his last movement was a Quick Step or Sprint; the kinds he must move for are rushed if his Move is used
        const s = this.s, m0 = cm.masks[0][BI[lk.c]] & mask;
        const flags = (lk.rushed ? 1 : 0) | (rushedX(s, d) ? 2 : 0) | (hasMoved(s, 'X', d) ? 4 : 0);
        const vc2 = ctx._vc2 || (ctx._vc2 = new Map());
        const key2 = (((((lk.i * NB + BI[lk.c]) * 5 + d) * 64 + mask) * 64 + m0) * 8) + flags;
        let hit2 = vc2.get(key2);
        if (hit2 === undefined) { hit2 = this._valsCalc(lk, d, mask, m0, flags); vc2.set(key2, hit2); }
        return hit2;
      }
      const vc = ctx._vc || (ctx._vc = new Array(5 * NB * 5 * 64));
      const key = ((lk.i * NB + BI[lk.c]) * 5 + d) * 64 + mask;
      let hit = vc[key];
      if (hit === undefined) { hit = this._valsCalc(lk, d, mask); vc[key] = hit; }
      return hit;
    }
    _valsCalc(lk, d, mask, m0, flags) {         // m0, flags: only under rules.control (D-151)
      const ctx = this.s.ctx, card = ctx.off[lk.i], pts = ZONE_POINTS[ZN[lk.c]], dc = this.dcards[d];
      const out = new Float64Array(lk.types.length);
      const control = flags !== undefined;
      let any = false;
      for (let t = 0; t < lk.types.length; t++) {
        const ty = lk.types[t];
        let r = card.sh[ty];
        const cut = control ? controlCut(ctx, ty) : 0, shooterCut = cut > 0 && (flags & 1) === 1;
        if (shooterCut) r -= cut;
        let best = null;
        for (let k = 0; k < 6; k++) {
          if (!((mask >> k) & 1)) continue;
          let con = dc.cn[ty] - (KPEN[k] ? 3 : 0);
          con = Math.max(0, con);
          const foul = KFOUL[k], two = KTWO[k];
          if (cut > 0 && (((m0 >> k) & 1) ? (flags & 2) : (flags & 4))) {       // a rushed Contest
            con = Math.max(0, con - cut);                                        // no extra foul roll (D-154)
          }
          let v = Math.max(0, pts * (r - con));
          if (foul) {
            const ft = footPoints(card, ty, pts, shooterCut ? r : undefined)[0];
            const pf = pFouls(dc.r.foul_contest, two ? 2 : 1);
            v = pf * ft + (1 - pf) * v;
          }
          if (best === null || v < best) best = v;
        }
        if (best !== null) { out[t] = best; any = true; }
      }
      return any ? out : null;
    }
    passP(i, c) {
      const s = this.s;
      if (i === s.ball) return 1.0;
      if (count(s, 'O', 'pass') >= 2) return 0.0;
      if (this.exact && c === s.o[i]) return passProb(s, i);
      return this._lane(c).p;
    }
    _lane(c) {                                   // laneP(s, ., c) and its parts per defender, for the moved re-reads
      const lp = this._lp || (this._lp = new Map());
      let r = lp.get(c);
      if (r) return r;
      const s = this.s, a = s.o[s.ball];
      r = { off: !(ONB[a] && ONB[c]), den: null, denies: [false, false, false, false, false], hit: [false, false, false, false, false], pi: [0, 0, 0, 0, 0], p: 0 };
      if (!r.off) {
        const den = laneSquares(a, c); r.den = den;
        const passer = s.ctx.off[s.ball].r.pass;
        for (let d = 0; d < 5; d++) {
          const xp = s.x[d];
          r.denies[d] = den.has(xp) && adjacent(xp, c);
          if (den.size) {
            const [canMove, qsLeft] = caps(s, 'X', d);
            const one = oneAction(xp, s.arrows[d], s.ctx.dfn[d].qs, canMove, qsLeft);
            let hit = false; for (const b of den.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { hit = true; break; }
            r.hit[d] = hit;
            r.pi[d] = 1 - pS(passer - s.ctx.dfn[d].r.intercept);
          }
        }
        // step 12 (eval.reach): who can step into the pass, by the reach map's exact movement (the moved re-reads keep
        // the geometry, as decide.responses does)
        const hitP = r.hit.slice();
        if (reachOn() && den.size) for (let d = 0; d < 5; d++) {
          const one = exactOne(s, d); let h = false; for (const b of den.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { h = true; break; }
          hitP[d] = h;
        }
        if (r.denies.some(x => x)) r.p = 0;
        else if (!den.size) r.p = 1;
        else { let worst = 0; for (let d = 0; d < 5; d++) if (hitP[d] && r.pi[d] > worst) worst = r.pi[d]; r.p = 1 - worst; }
        // the parts without each defender j: the others' denial and their worst intercept chance
        r.dx = [false, false, false, false, false]; r.wx = new Float64Array(5);
        for (let j = 0; j < 5; j++) {
          let w = 0, dn = false;
          for (let d = 0; d < 5; d++) if (d !== j) { if (r.denies[d]) dn = true; if (r.hit[d] && r.pi[d] > w) w = r.pi[d]; }
          r.dx[j] = dn; r.wx[j] = w;
        }
        r.bits = new Uint32Array(8); for (const b of den.bi) r.bits[b >> 5] |= 1 << (b & 31);
      }
      lp.set(c, r); return r;
    }
    _laneMoved(c, j, q, oneJ) {                  // laneP with defender j at q (decide.responses' moved state)
      const r = this._lane(c);
      if (r.off) return 0;
      if (r.dx[j]) return 0;
      const b = BI[q];
      if (b >= 0 && ((r.bits[b >> 5] >>> (b & 31)) & 1) && adjacent(q, c)) return 0;
      if (!r.den.size) return 1;
      let hit = false; for (const z of r.den.bi) if ((oneJ[z >> 5] >>> (z & 31)) & 1) { hit = true; break; }
      let worst = r.wx[j];
      if (hit && r.pi[j] > worst) worst = r.pi[j];
      return 1 - worst;
    }
    _looks(i, s = this.s, cm = this._cm) {
      if (!ONB[s.o[i]]) return [];
      const card = s.ctx.off[i];
      const leftNow = this.o_to_act ? 2 - s.turn_n : 2;
      const shotOk = count(s, 'O', 'shot') < 1;
      const out = [];
      let reach;
      if (i === s.ball) {
        reach = new Map([[s.o[i], 0]]);
        for (const kind of ['move', 'qs', 'sprint']) {
          if (canMoveKind(s, 'O', i, kind)) for (const q of movementDests(s, 'O', i, kind).keys()) if (!reach.has(q)) reach.set(q, 1);
        }
      } else {
        reach = new Map();
        if (ONB[s.o[i]] && s.tok_o > 0) {
          const [canMove, qsLeft] = caps(s, 'O', i);
          const lst = reachList(s.o[i], s.ctx.off[i].qs, canMove, qsLeft);
          for (let n = 0; n < lst.length; n += 2) { const q = lst[n]; if (lst[n + 1] === 0 || !occAt(s, q)) reach.set(q, lst[n + 1]); }
        } else reach.set(s.o[i], 0);
      }
      const add = (c, n) => {
        const z = ZN[c];
        if (!SHOOT(z)) return;
        let lk;
        if (i === s.ball) {
          if (n === 0 && shotOk && leftNow >= 1) lk = makeLook(i, c, 'shoot', 1.0, this.o_to_act);
          else if (n === 1 && shotOk && leftNow >= 2 && s.tok_o >= 2) lk = makeLook(i, c, 'drive', 1.0, this.o_to_act);
          else lk = makeLook(i, c, 'later', this.cfg.later_p, false, this.o_to_act ? 1 : 2);
        } else {
          const p = this.passP(i, c);
          if (p <= 0) return;
          if (n === 0) lk = makeLook(i, c, 'catch', p, false, 1);
          else if (leftNow >= 2 && s.tok_o >= 2 && this.o_to_act) lk = makeLook(i, c, 'cut', p, false, 1);
          else lk = makeLook(i, c, 'cut', p * this.cfg.later_p, false, 2);
        }
        lk.types = ZONE_SHOTS[z];
        const pts = ZONE_POINTS[z];
        if (controlOn(s.ctx)) lk.rushed = n === 0 ? rushedO(s, i) : hasMoved(s, 'O', i);      // D-151 (decide.Read._looks)
        lk.open = lk.rushed ? lk.types.map(t => pts * (card.sh[t] - controlCut(s.ctx, t))) : lk.types.map(t => pts * card.sh[t]);
        lk.vals = [null, null, null, null, null];
        for (const d of this.att_x) { const v = this._vals(lk, d, cm[d]); if (v) lk.vals[d] = v; }
        finishLook(lk);
        out.push(lk);
      };
      for (const [c, n] of reach) add(c, n);
      if (i === s.ball && budgetCfg()) {
        // step 13 B2 (D-115): the squares two actions away. Step 13C (a speed-up that changes no result): such a look is
        // worth at most later_p times his best shot from its zone, and the list keeps the best L looks, earlier ones
        // first when level. So a square whose most can't beat the L-th look already found is never built or searched.
        let floor = -Infinity;
        if (SPEED.two_bound && out.length >= this.L) { const bs = out.map(l => l.base).sort((a, b) => b - a); floor = bs[this.L - 1]; }
        const most = new Map();
        const keep = c => {
          const z = ZN[c];
          if (!SHOOT(z)) return false;
          let m = most.get(z);
          if (m === undefined) { m = 0.0; const pts = ZONE_POINTS[z]; for (const t of ZONE_SHOTS[z]) { const v = pts * card.sh[t]; if (v > m) m = v; } m = this.cfg.later_p * m; most.set(z, m); }
          return m > floor;
        };
        for (const q of twoActions(s, i, reach, keep)) add(q, 2);
      }
      out.sort((a, b) => b.base - a.base);
      return out.slice(0, this.L);
    }
    _best(looks) {
      let best = 0.0, arg = null;
      for (const lk of looks) { const v = lk.base; if (v > best + 1e-9) { best = v; arg = lk; } }
      if (!arg) return { value: 0.0, sq: -1, route: 'none', p: 0.0, now: false };
      let tb = 0; for (let t = 1; t < arg.types.length; t++) if (arg.open[t] > arg.open[tb]) tb = t;
      return { value: best, sq: arg.c, route: arg.route, p: arg.p, now: arg.now, type: arg.types[tb] };
    }
    responses(j) {
      const s = this.s;
      const base = new Float64Array(5);
      for (const i of this.att_o) base[i] = this.threat[i].value;
      const still = [[s.x[j], s.arrows[j], null], base];
      let anyLater = false;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (!lk.now) { anyLater = true; break; }
      if (this.k <= 0 || s.tok_x <= 0 || !ONB[s.x[j]] || !anyLater) return [still];
      const capsJ = caps(s, 'X', j), canMove = capsJ[0], qsLeft = capsJ[1];
      const [free, fixed] = geoReach(s.x[j], s.arrows[j], s.ctx.dfn[j].qs, canMove, qsLeft);
      const occ = occupied(s);
      const spots = [];
      for (const i of this.att_o) { const ls = this.looks[i]; for (let n = 0; n < Math.min(3, ls.length); n++) if (!ls[n].now) spots.push(ls[n].c); }
      const bp = s.o[s.ball];
      const lanes = new Set();
      for (const i of this.att_o) {
        const ls = this.looks[i];
        for (let n = 0; n < Math.min(2, ls.length); n++) {
          const lk = ls[n];
          if ((lk.route === 'catch' || lk.route === 'cut') && ONB[bp]) for (const q of laneSquares(bp, lk.c)) lanes.add(q);
        }
      }
      if (ONB[bp]) for (const q of laneSquares(bp, RIM)) lanes.add(q);
      const reach = reachOn(), paths = new Map();
      if (reach) for (const i of this.att_o) for (const lk of this.looks[i]) {
        if (lk.now || !PATH_ROUTES.has(lk.route)) continue;
        let set = paths.get(i); if (!set) { set = new Set(); paths.set(i, set); }
        for (const p of pathsTo(s.o[i], lk.c, s.ctx.off[i].qs)) for (const q of p) { set.add(q); lanes.add(q); }
      }
      const cands = [];
      for (const [q, n] of free) {
        if (n > 1 || (occ.has(q) && q !== s.x[j])) continue;
        let near = spots.filter(c => cheb(q, c) <= 2 && c !== q);
        if (!near.length && lanes.has(q)) near = q !== bp ? [bp] : [];
        if (!near.length) continue;
        let c0 = near[0], k0 = cheb(q, c0);
        for (let m = 1; m < near.length; m++) { const c = near[m], kk = cheb(q, c); if (kk < k0 || (kk === k0 && c < c0)) { c0 = c; k0 = kk; } }
        cands.push([q, nearestDir(q, c0), 'move']);
      }
      for (const [q, arrs] of fixed) {
        if (occ.has(q) && q !== s.x[j]) continue;
        for (const [a, n] of arrs) if (n === 1 && spots.some(c => cheb(q, c) <= 2)) cands.push([q, a, 'qs']);
      }
      const nearOf = (i, q) => { for (const lk of this.looks[i]) if (!lk.now && cheb(q, lk.c) <= 3) return true; return reach && paths.has(i) && paths.get(i).has(q); };
      const carrier = s.ball;
      const carrierIn = this.att_o.includes(carrier);
      const front = p => carrierIn && cheb(p, s.o[carrier]) <= 2 && DR[p] < DR[s.o[carrier]];
      let leave = null;
      const out = [];
      for (const [q, a, used] of cands) {
        const cm = this._contest(j, q, a, used);
        const left = LEFT; left.set(base);
        let oneJ = null;
        let gain = 0.0;
        const into = q !== s.x[j] && front(q), outOf = q !== s.x[j] && front(s.x[j]) && !front(q);
        const blocks = into || outOf;
        if (blocks) {
          if (outOf && leave !== null) left[carrier] = leave;
          else {
            const at = into ? q : AWAY;
            const moved = W_(s, { x: setAt(s.x, j, at), arrows: setAt(s.arrows, j, a) });
            const cm2 = this._cm.slice(); cm2[j] = into ? cm : null;
            const lks = this._looks(carrier, moved, cm2);
            left[carrier] = lks.length ? Math.max(...lks.map(l => l.base)) : 0.0;
            if (outOf) leave = left[carrier];
          }
          gain += Math.max(0.0, base[carrier] - left[carrier]);
        }
        for (const i of this.att_o) {
          if (i === carrier && blocks) continue;
          if (!nearOf(i, q)) continue;
          let best = 0.0;
          for (const lk of this.looks[i]) {
            let v;
            if (lk.now) v = lk.base;
            else if (reach && q !== s.x[j] && PATH_ROUTES.has(lk.route) && blocksPath(q, s.o[i], lk.c, s.ctx.off[i].qs)) v = 0.0;
            else {
              let pNew = null;
              if ((lk.route === 'catch' || lk.route === 'cut') && q !== s.x[j]) {
                if (!oneJ) oneJ = oneAction(q, a, s.ctx.dfn[j].qs, used === 'move' ? false : capsJ[0], capsJ[1]);
                pNew = this._laneMoved(lk.c, j, q, oneJ);
              }
              v = swapped(lk, j, this._vals(lk, j, cm), pNew);
            }
            if (v > best) best = v;
          }
          left[i] = best;
          gain += Math.max(0.0, base[i] - best);
        }
        if (gain > 1e-9) out.push([gain, [q, a, used], Float64Array.from(left)]);
      }
      out.sort((x, y) => y[0] - x[0]);
      return [still].concat(out.slice(0, this.k).map(r => [r[1], r[2]]));
    }
    cover() {
      if (this._cover) return this._cover;
      const s = this.s, movers = Math.min(2, s.tok_x);
      const R = new Array(5).fill(null);
      for (const j of this.att_x) R[j] = this.responses(j);
      const threats = this.att_o;
      const base = new Float64Array(5);
      for (const i of threats) base[i] = this.threat[i].value;
      const keyOf = res => { let mx = 0.0, sm = 0.0, first = true; for (const i of threats) { if (first || res[i] > mx) mx = res[i]; first = false; sm += res[i]; } return [round6(threats.length ? mx : 0.0), round6(sm)]; };
      let best = [keyOf(base), [], Float64Array.from(base)];
      const opts = [];
      for (const j of this.att_x) for (let idx = 1; idx < R[j].length; idx++) opts.push([j, idx]);
      const score = chosen => {
        const res = new Float64Array(5);
        for (const i of threats) {
          let v = base[i];
          for (const [j, idx] of chosen) { const lv = R[j][idx][1][i]; if (lv < v) v = lv; }
          res[i] = v;
        }
        return [keyOf(res), res];
      };
      for (let a = 0; a < opts.length; a++) {
        const ch = [opts[a]];
        let [k, res] = score(ch);
        if (keyLess(k, best[0])) best = [k, ch, res];
        if (movers >= 2) {
          for (let b = a + 1; b < opts.length; b++) {
            if (opts[b][0] === opts[a][0]) continue;
            const ch2 = [opts[a], opts[b]];
            [k, res] = score(ch2);
            if (keyLess(k, best[0])) best = [k, ch2, res];
          }
        }
      }
      const choice = new Map(); for (const [j, idx] of best[1]) choice.set(j, R[j][idx][0]);
      this._cover = { value: best[0][0], choice, residual: best[2], R };
      return this._cover;
    }
    // ---- step 17: the named readings a learned judgement is built from (decide.Read.features, FEATURES' order) ------
    features() {
      const s = this.s;
      const sn = this.shotNow() || 0.0;
      let now = 0.0;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && lk.base > now) now = lk.base;
      const cv = this.cover().residual, res = [];
      for (const i of this.att_o) res.push(cv[i]);
      res.sort((a, b) => b - a);
      let opened = 0.0;
      for (const i of this.att_o) if (this.threat[i].value > opened) opened = this.threat[i].value;
      const tgt = this._paintNext();
      let free = 0, two = 0, one = 0;
      for (const i of this.att_o) {
        if (!this.looks[i].length) continue;
        const lk = this.looks[i][0];
        let top = -1.0, shot = null, who = -1;
        for (let t = 0; t < lk.types.length; t++) {
          let v = lk.open[t], d0 = -1;
          for (let d = 0; d < 5; d++) { const vals = lk.vals[d]; if (vals && vals[t] < v) { v = vals[t]; d0 = d; } }
          if (v > top) { top = v; shot = lk.types[t]; who = d0; }
        }
        if (who < 0) free++;
        else { const gap = BAND[s.ctx.off[i].b['shot_' + shot]] - BAND[s.ctx.dfn[who].b['con_' + shot]]; if (gap >= 2) two++; else if (gap === 1) one++; }
      }
      const pop = m => { let n = 0; for (let k = 0; k < 5; k++) n += (m >> k) & 1; return n; };
      return [sn, now, res.length ? res[0] : 0.0, res.length > 1 ? res[1] : 0.0, opened, this.budget().value, tgt ? tgt[1] : 0.0, free, two, one,
        s.tok_o, s.tok_x, this.o_to_act ? 1.0 : 0.0, pop(s.moved_x), pop(s.moved_o)];
    }
    // ---- step 16, stage 3: advantages (decide.Read.advantages, _paint_next, phi). Reading and recording only. --------
    advantages() {
      if (this._adv) return this._adv;
      const s = this.s, out = [];
      this._adv = out;
      if (s.stage !== 'play' || s.pending) return out;
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) return out;   // no offence turn is left: nothing can be built
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      const nowWorth = this.leaf() - banked;
      const best = new Map();
      const put = (kind, i, j, sq, stage, value, chance, worth, gap) => {
        const key = i * 8 + ADV_KINDS.indexOf(kind), cur = best.get(key);
        if (!cur || worth > cur.worth + 1e-9 || (Math.abs(worth - cur.worth) <= 1e-9 && value * chance > cur.value * cur.chance + 1e-9)) {
          best.set(key, { kind, i, j, sq, stage, value, chance, worth, gap: gap || 0 });
        }
      };
      for (const i of this.att_o) {
        for (const lk of this.looks[i]) {
          let top = -1.0, shot = null, who = -1;
          for (let t = 0; t < lk.types.length; t++) {
            let v = lk.open[t], d0 = -1;
            for (let d = 0; d < 5; d++) { const vals = lk.vals[d]; if (vals && vals[t] < v) { v = vals[t]; d0 = d; } }
            if (v > top) { top = v; shot = lk.types[t]; who = d0; }
          }
          if (shot === null || lk.p <= 0) continue;
          const stage = lk.now ? 'convert' : 'keep', worth = Math.max(0.0, lk.base - nowWorth);
          if (who < 0) put('separation', i, -1, lk.c, stage, top, lk.p, worth);
          else {
            const gap = BAND[s.ctx.off[i].b['shot_' + shot]] - BAND[s.ctx.dfn[who].b['con_' + shot]];
            if (gap >= 1) put('mismatch', i, who, lk.c, stage, top, lk.p, worth, gap);
          }
          if (i === s.ball && ZN[lk.c] === PAINT) put('penetration', i, who, lk.c, stage, top, lk.p, worth);
        }
      }
      if (this.budgetOn()) {
        const bd = this.budget(), res = this.cover().residual;
        let full = 0.0, first = true;
        for (const i of this.att_o) { if (first || res[i] > full) full = res[i]; first = false; }
        if (bd.value > full + 1e-9) {
          for (const i of this.att_o) {
            const left = bd.left[i] === undefined ? 0.0 : bd.left[i];
            if (left >= bd.value - 1e-9) put('numbers', i, -1, this.threat[i].sq, 'keep', bd.left[i], 1.0, Math.max(0.0, bd.left[i] - nowWorth));
          }
        }
      }
      const tgt = this._paintNext();
      if (tgt) {
        const nxt = W_(s, { clock: s.clock - 2 });
        const ahead = vcoarse(nxt) + this.cfg.continuation * tgt[1] - relativeAverage(nxt, this.budgetOn());
        put('penetration', s.ball, -1, tgt[0], 'create', tgt[1], 1.0, Math.max(0.0, ahead - nowWorth));
      }
      for (const key of [...best.keys()].sort((a, b) => a - b)) out.push(best.get(key));
      return out;
    }
    _paintNext() {
      const s = this.s, i = s.ball;
      if (s.clock <= 2 || !this.att_o.includes(i) || !ONB[s.o[i]] || s.tok_o <= 0) return null;
      const one = new Map([[s.o[i], 0]]);
      for (const kind of ['move', 'qs', 'sprint']) {
        if (canMoveKind(s, 'O', i, kind)) for (const q of movementDests(s, 'O', i, kind).keys()) if (!one.has(q)) one.set(q, 1);
      }
      const stops = [...one.keys()].concat(twoActions(s, i, one));
      const here = new Set(stops), old = s.o[i], card = s.ctx.off[i], qs = card.qs;
      const blocked = q => q !== old && occAt(s, q);
      let best = null;
      for (const c of paintSquares()) {
        if (here.has(c) || blocked(c)) continue;
        let ok = false;
        for (const q0 of stops) {
          for (const p of pathsTo(q0, c, qs)) { let free = true; for (const q of p) if (blocked(q)) { free = false; break; } if (free) { ok = true; break; } }
          if (ok) break;
        }
        if (!ok) continue;
        const lk = makeLook(i, c, 'later', 1.0, false);
        lk.types = ZONE_SHOTS[PAINT];
        const vals = [null, null, null, null, null];
        for (const d of this.att_x) { const cm = this._cm[d]; if (cm) { const mask = cm.masks[2][BI[c]]; if (mask) vals[d] = this._valsCalc(lk, d, mask); } }
        let top = 0.0;
        for (let t = 0; t < lk.types.length; t++) {
          let v = ZONE_POINTS[PAINT] * card.sh[lk.types[t]];
          for (const d of this.att_x) if (vals[d] && vals[d][t] < v) v = vals[d][t];
          if (v > top) top = v;
        }
        if (best === null || top > best[1] + 1e-9) best = [c, top];
      }
      return best;
    }
    phi() {
      const top = [0, 0, 0, 0, 0];
      for (const a of this.advantages()) if (a.worth > top[a.i]) top[a.i] = a.worth;
      let sum = 0.0; for (let i = 0; i < 5; i++) sum += top[i];
      return sum;
    }
    // ---- step 13 B1: coverage as a budget (decide.Read.budget_tables, budget) ----------------------------------------
    budgetOn() { return budgetCfg() && this.k > 0; }
    budgetTables() {                            // decide.Read.budget_tables (D-125: the Contest from where he stands is free)
      const s = this.s, reach = reachOn();
      const best = (lk, p, rows) => {
        let top = 0.0;
        for (let t = 0; t < lk.types.length; t++) {
          let v = lk.open[t];
          for (const vals of rows) if (vals && vals[t] < v) v = vals[t];
          if (v > top) top = v;
        }
        return p * top;
      };
      const looks = [], first = [0, 0, 0, 0, 0], free = [];
      for (const i of this.att_o) {
        first[i] = looks.length;
        for (const lk of this.looks[i]) {
          const f0 = [null, null, null, null, null];
          if (!lk.now) for (const j of this.att_x) f0[j] = this._vals(lk, j, this._cm[j], 0);
          free.push(f0);
          looks.push([i, lk, lk.now ? lk.base : best(lk, lk.p, f0)]);
        }
      }
      const R = this.cover().R, cols = [];
      for (const j of this.att_x) {
        for (const i of this.att_o) {
          const falls = new Map(), ls = this.looks[i];
          for (let n = 0; n < ls.length; n++) {
            const lk = ls[n], l = first[i] + n;
            if (!lk.now && lk.vals[j]) { const f = looks[l][2] - best(lk, lk.p, free[l].concat([lk.vals[j]])); if (f > 1e-9) falls.set(l, f); }
          }
          if (falls.size) cols.push([j, i, 'react', falls]);
        }
        const capsJ = caps(s, 'X', j), Rj = R[j];
        for (let r = 1; r < Rj.length; r++) {
          const q = Rj[r][0][0], a = Rj[r][0][1], used = Rj[r][0][2];
          const cm = this._contest(j, q, a, used);
          let oneJ = null, any = false;
          const stand = new Map(), extra = [null, null, null, null, null];
          for (let l = 0; l < looks.length; l++) {
            const i = looks[l][0], lk = looks[l][1], o = looks[l][2];
            if (lk.now) continue;
            let w0, w1;
            if (reach && q !== s.x[j] && PATH_ROUTES.has(lk.route) && blocksPath(q, s.o[i], lk.c, s.ctx.off[i].qs)) w0 = w1 = 0.0;
            else {
              let p = lk.p;
              if ((lk.route === 'catch' || lk.route === 'cut') && q !== s.x[j]) {
                if (!oneJ) oneJ = oneAction(q, a, s.ctx.dfn[j].qs, used === 'move' ? false : capsJ[0], capsJ[1]);
                p = this._laneMoved(lk.c, j, q, oneJ);
              }
              const others = free[l].slice(); others[j] = null;
              w0 = best(lk, p, others.concat([this._vals(lk, j, cm, 0)]));
              w1 = best(lk, p, others.concat([this._vals(lk, j, cm)]));
            }
            if (Math.abs(o - w0) > 1e-9) { stand.set(l, o - w0); if (o - w0 > 1e-9) any = true; }
            if (w1 < w0 - 1e-9) { if (!extra[i]) extra[i] = new Map(); extra[i].set(l, o - w1); }
          }
          if (any) cols.push([j, -1, 'move', stand]);
          for (const i of this.att_o) {
            if (!extra[i]) continue;
            const falls = new Map(stand);
            for (const [l, f] of extra[i]) falls.set(l, f);
            cols.push([j, i, 'move', falls]);
          }
        }
      }
      return [looks, cols];
    }
    budget() {
      if (this._budget) return this._budget;
      const [looks, cols] = this.budgetTables();
      let top = 0.0; for (const l of looks) if (l[2] > top) top = l[2];
      const n = cols.length;
      const cov = new Set(); for (const c of cols) for (const l of c[3].keys()) cov.add(l);
      const covered = [...cov].sort((a, b) => a - b);
      const A = [], b = [];
      const rowOf = f => { const r = new Float64Array(n + 1); for (let k = 0; k < n; k++) r[k] = f(cols[k]); return r; };
      let free = 0.0; looks.forEach((l, k) => { if (!cov.has(k) && l[2] > free) free = l[2]; });
      { const r = rowOf(() => 0.0); r[n] = 1.0; A.push(r); b.push(top - free); }
      for (const l of covered) { const r = rowOf(c => -(c[3].get(l) || 0.0)); r[n] = 1.0; A.push(r); b.push(top - looks[l][2]); }
      const up = (c, l) => (c[3].get(l) || 0.0) > 0.0;     // an answer that lowers look l
      for (const l of covered) { let m = 0; for (const c of cols) if (up(c, l)) m++; if (m > 1) { A.push(rowOf(c => (up(c, l) ? 1.0 : 0.0))); b.push(1.0); } }
      for (const j of this.att_x) if (cols.some(c => c[0] === j)) { A.push(rowOf(c => (c[0] === j ? 1.0 : 0.0))); b.push(1.0); }
      if (cols.some(c => c[2] === 'move')) { A.push(rowOf(c => (c[2] === 'move' ? 1.0 : 0.0))); b.push(Math.min(2, this.s.tok_x)); }
      const cvec = new Float64Array(n + 1); cvec[n] = 1.0;
      const [z, x] = lpMax(cvec, A, b);
      const left = {}, opened = {};
      looks.forEach((lk, l) => {
        let sum = 0.0;
        for (let k = 0; k < n; k++) sum += x[k] * (cols[k][3].get(l) || 0.0);
        const v = lk[2] - sum;
        const i = lk[0];
        if (left[i] === undefined || v > left[i]) left[i] = v;
        if (opened[i] === undefined || lk[2] > opened[i]) opened[i] = lk[2];
      });
      const shares = []; cols.forEach((c, k) => { if (x[k] > 1e-9) shares.push([c[0], c[1], c[2], x[k]]); });
      this._budget = { value: top - z, left, open: opened, shares };
      return this._budget;
    }
    shotNow() {
      if (!this.o_to_act) return null;
      for (const lk of this.looks[this.s.ball] || []) if (lk.route === 'shoot') return lk.base;
      return null;
    }
    // step 12 (decide.Read.possession): the leaf without the ball handler's shot now
    possession() {
      const s = this.s;
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      let now = 0.0;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && !(i === s.ball && lk.route === 'shoot') && lk.base > now) now = lk.base;
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) return banked + now;
      const cv = this.cover(), res = cv.residual;
      let top = 0.0, first = true;
      for (const i of this.att_o) { if (first || res[i] > top) top = res[i]; first = false; }
      if (!this.att_o.length) top = 0.0;
      let sum = 0.0, nt = 0;
      for (const i of this.att_o) if (res[i] >= top - 1e-9) { sum += res[i]; nt++; }
      const bud = this.budgetOn();                       // step 13 B1: after the defence's best shares
      const cont = (bud ? this.budget().value : (nt ? sum / nt : 0.0)) * this.cfg.continuation, coarse = vcoarse(s);
      if ((D.config.eval.leaf_mode || 'floor') === 'relative') return banked + Math.max(now, coarse + cont - relativeAverage(s, bud));
      return banked + Math.max(now, cont, coarse);
    }
    quickLeaf() {
      // Read(s, k=0, looks_per=3).leaf() from this read (attention all, looks_per 6): the first three looks of each
      // attacker are that read's looks, its threats are these, and with k = 0 the cover leaves every threat.
      if (this._quick !== undefined) return this._quick;
      const s = this.s;
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      let v;
      if (s.pending) {
        const passer = s.pending[0], recv = s.pending[1];
        const p = laneP(W_(s, { ball: passer }), recv, s.o[recv]);
        v = p * readOf(W_(s, { ball: recv, pending: null })).quickLeaf() + (1 - p) * turnoverValue(s);
      } else {
        let sn = null;
        if (this.o_to_act) { const ls = this.looks[s.ball] || []; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].route === 'shoot') { sn = ls[n].base; break; } }
        let now = 0.0;
        for (const i of this.att_o) { const ls = this.looks[i]; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].now && ls[n].base > now) now = ls[n].base; }
        let top = 0.0, first = true;
        for (const i of this.att_o) { const t = this.threat[i].value; if (first || t > top) top = t; first = false; }
        let sum = 0.0, nt = 0;
        for (const i of this.att_o) { const t = this.threat[i].value; if (t >= top - 1e-9) { sum += t; nt++; } }
        const cont = (nt ? sum / nt : 0.0) * this.cfg.continuation;
        if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) v = banked + Math.max(sn || 0.0, now);
        else v = leafOf(s, banked, sn, now, cont, vcoarse(s));
      }
      if (settleOn()) {
        // step 18b: the ordering reading on the leaf's own scale (the ceiling, the calibrated map, the ceiling), so a
        // settled shot and a position that plays on are ranked together (decide.Read.leaf with k = 0)
        const top = ceilingOf(s);
        if (v - banked > top) v = banked + top;
        if (calibratedOn() && s.stage === 'play' && !s.pending && !(!this.o_to_act && s.tok_o <= 0 && s.clock <= 2)) {
          let r = calibrate(s, this.o_to_act, v - banked);
          if (r > top) r = top;
          v = banked + r;
        }
      }
      this._quick = v;
      return v;
    }
    // Step 13 (a speed-up that changes no result): Read(s, k=0, looks_per=3): is the ball handler's shot now worth more
    // than the possession without it? From this read, as quickLeaf is (the offence to act, no pass in the air).
    quickShotFirst() {
      if (this._qshot !== undefined) return this._qshot;
      const s = this.s;
      let sn = null;
      if (this.o_to_act) { const ls = this.looks[s.ball] || []; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].route === 'shoot') { sn = ls[n].base; break; } }
      if (sn === null) return (this._qshot = false);
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      let now = 0.0;
      for (const i of this.att_o) {
        const ls = this.looks[i];
        for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].now && !(i === s.ball && ls[n].route === 'shoot') && ls[n].base > now) now = ls[n].base;
      }
      let poss;
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) poss = banked + now;
      else {
        let top = 0.0, first = true;
        for (const i of this.att_o) { const t = this.threat[i].value; if (first || t > top) top = t; first = false; }
        let sum = 0.0, nt = 0;
        for (const i of this.att_o) { const t = this.threat[i].value; if (t >= top - 1e-9) { sum += t; nt++; } }
        const cont = (nt ? sum / nt : 0.0) * this.cfg.continuation, coarse = vcoarse(s);
        if ((D.config.eval.leaf_mode || 'floor') === 'relative') poss = banked + Math.max(now, coarse + cont - relativeAverage(s));
        else poss = banked + Math.max(now, cont, coarse);
      }
      return (this._qshot = sn > poss + 1e-9);
    }
    leaf() {
      if (this._leaf !== undefined) return this._leaf;
      return (this._leaf = this._leafCalc());
    }
    _leafCalc() {
      let v = this._handLeaf();
      const s = this.s;
      let top = null;
      if (settleOn()) {                              // step 18b (D-145): the ceiling, before the map
        let b0 = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
        b0 += foulExternality(s);
        top = ceilingOf(s);
        if (v - b0 > top) v = b0 + top;
      }
      if (!calibratedOn() || (this.k <= 0 && top === null) || s.stage !== 'play' || s.pending || (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2)) return v;
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      let r = calibrate(s, this.o_to_act, v - banked);                // step 17D: the same reading, calibrated
      if (top !== null && r > top) r = top;                           // and after it
      return banked + r;
    }
    _handLeaf() {                                 // today's hand-combined reading
      const s = this.s;
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      if (s.pending) {
        const passer = s.pending[0], recv = s.pending[1];
        const p = laneP(W_(s, { ball: passer }), recv, s.o[recv]);
        const att = this.att_o.length === 5 ? null : [this.att_o, this.att_x];
        const ns = W_(s, { ball: recv, pending: null });
        const caught = (this.pooled ? readOf(ns) : new Read(ns, { attention: att, k: this.k, looks_per: this.L })).leaf();
        return p * caught + (1 - p) * turnoverValue(s);
      }
      if (learnedOn() && this.k > 0 && s.stage === 'play' && !(!this.o_to_act && s.tok_o <= 0 && s.clock <= 2)) {
        const lv = learnedValue(s, this.features());       // step 17: the learned judgement in place of the hand-combined one
        if (lv !== null) return banked + lv;
      }
      const sn = this.shotNow();
      let now = 0.0;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && lk.base > now) now = lk.base;
      const cv = this.cover(), res = cv.residual;
      let top = 0.0, first = true;
      for (const i of this.att_o) { if (first || res[i] > top) top = res[i]; first = false; }
      if (!this.att_o.length) top = 0.0;
      let sum = 0.0, nt = 0;
      for (const i of this.att_o) if (res[i] >= top - 1e-9) { sum += res[i]; nt++; }
      const bud = this.budgetOn();                       // step 13 B1: after the defence's best shares
      const cont = (bud ? this.budget().value : (nt ? sum / nt : 0.0)) * this.cfg.continuation;
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) return banked + Math.max(sn || 0.0, now);
      return leafOf(s, banked, sn, now, cont, vcoarse(s), bud);
    }
  }

  // The default read of a position (attention all, k and looks_per from the config), shared by the search's candidate
  // turns, its move ordering (quickLeaf) and the All-Star leaf: the same object, so each is computed once per position.
  let READS = new Map(), READS_OLD = new Map();
  function readOf(s, z) {
    const key = z === undefined ? zobrist(s) : z;
    let r = READS.get(key);
    if (r === undefined) {
      r = READS_OLD.get(key);
      if (r === undefined) { r = new Read(s); r.pooled = true; }
      if (READS.size >= 3000) { READS_OLD = READS; READS = new Map(); }
      READS.set(key, r);
    }
    return r;
  }

  // ---- search (B6) ------------------------------------------------------------------------------------------------
  let _rs = 20261108 >>> 0;
  const rnd32 = () => { _rs = (_rs + 0x6D2B79F5) >>> 0; let t = _rs; t = Math.imul(t ^ (t >>> 15), t | 1); t ^= t + Math.imul(t ^ (t >>> 7), t | 61); return (t ^ (t >>> 14)) | 0; };
  const ZP = new Int32Array(2 * 10 * NSQ); for (let n = 0; n < ZP.length; n++) ZP[n] = rnd32();
  const ZA = new Int32Array(2 * 40); for (let n = 0; n < ZA.length; n++) ZA[n] = rnd32();
  const ZB = new Int32Array(2 * 5); for (let n = 0; n < ZB.length; n++) ZB[n] = rnd32();
  const STAGES = { target: 1, play: 2, reaction: 3, over: 4, contest: 5, forced: 6, pick: 7 };
  const RKINDS = { shot: 1, free_throws: 2, steal: 3, turnover_end: 4, forced: 5 };
  function zobrist(s) {
    let h1 = ZB[s.ball * 2], h2 = ZB[s.ball * 2 + 1];
    for (let i = 0; i < 5; i++) { const k = (i * NSQ + s.o[i]) * 2; h1 ^= ZP[k]; h2 ^= ZP[k + 1]; }
    for (let i = 0; i < 5; i++) {
      const k = ((5 + i) * NSQ + s.x[i]) * 2, ka = (i * 8 + s.arrows[i]) * 2;
      h1 ^= ZP[k] ^ ZA[ka]; h2 ^= ZP[k + 1] ^ ZA[ka + 1];
    }
    let a = 0x811C9DC5 | 0, b = 0x2545F491 | 0;
    const mix = v => { a = Math.imul(a ^ v, 0x01000193); b = Math.imul((b ^ v) + 0x7F4A7C15, 0x85EBCA6B); b ^= b >>> 13; };
    mix(STAGES[s.stage] || 0); mix(s.side === 'O' ? 1 : s.side === 'X' ? 2 : 3); mix(s.clock); mix(s.tok_o); mix(s.tok_x);
    mix(s.moved_o); mix(s.moved_x); for (const c of s.cnt) mix(c); mix(s.turn_n); mix(s.final ? 1 : 0); mix(s.lock_o); mix(s.lock_x);
    mix(100 + s.screens.length); for (const sc of s.screens) { mix(sc[0]); mix(sc[1]); mix(sc[2] ? 1 : 0); mix(sc[3]); }
    if (s.pending) { mix(s.pending[0]); mix(s.pending[1]); } else mix(-1);
    mix(SHOT_TYPES.indexOf(s.shot || '')); mix(s.prev_wait === 'H' ? 1 : s.prev_wait === 'P' ? 2 : 0);
    mix(200 + s.beaten.length); for (const bt of s.beaten) { mix(bt[0]); mix(bt[1]); }
    mix(s.fouls); mix(s.bonus5); mix(s.tos); mix(s.qs_o); mix(s.qs_x); mix(s.phase); mix(s.inbound); mix(s.target); mix(s.approach);
    mix(s.turn_lead);
    if (s.turn_x) { for (const q of s.turn_x[0]) mix(q); for (const q of s.turn_x[1]) mix(q); } else mix(-7);
    mix(s.react_moved); mix(s.forced ? 1 : 0); mix(s.rush_o); mix(s.rush_x);
    if (s.result) { const r = s.result; mix(RKINDS[r.kind] || 9); mix(r.shooter); mix(SHOT_TYPES.indexOf(r.shot_type || '')); mix(r.points); mix(r.rating); mix(r.contest); mix(r.contester); mix(r.shot_value); mix(r.free_throws); mix(r.and_one ? 1 : 0); } else mix(-3);
    h1 ^= a; h2 ^= b;
    return (h1 >>> 0) * 65536 + ((h2 >>> 0) & 0xFFFF);          // 48 bits: ttKey stays an exact integer
  }
  const ttKey = (z, depth) => z * 16 + depth;          // a Map key: equal keys mean equal (state, depth)
  const actor = s => (s.stage === 'target' || s.stage === 'pick' || s.stage === 'forced') ? 'O' : (s.stage === 'reaction' || s.stage === 'contest') ? 'X' : s.side;
  const terminalValue = s => scoreTotal(s) + foulExternality(s);
  const TIMEOUT = { timeout: true };
  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000;
  const turnKey = t => t.map(a => a.id).join(',');

  function waitOf(acts) {
    for (const k of ['hesitate', 'pause', 'end_turn', 'forfeit']) for (const a of acts) if (a.kind === k) return a;
    return null;
  }
  const FIRSTS = new Set(['shot', 'pass', 'dribble', 'steal', 'intercept', 'challenge', 'forced_shot', 'contest']);
  function candidateActions(s, read, perPlayer = 3) {
    const acts = legalActions(s), side = actor(s);
    if (s.stage === 'contest' || s.stage === 'forced' || s.stage === 'target' || s.stage === 'pick' || acts.length <= 12) return acts;
    const keep = [], seen = new Set();
    const add = a => { if (!seen.has(a.id)) { seen.add(a.id); keep.push(a); } };
    for (const a of acts) if (FIRSTS.has(a.kind)) add(a);
    const w = waitOf(acts); if (w) add(w);
    read = read || readOf(s);
    const moves = acts.filter(a => MOVEMENT.has(a.kind));
    if (side === 'O') {
      const want = new Array(5).fill(null);
      for (const i of read.att_o) want[i] = new Set(read.looks[i].slice(0, perPlayer).map(lk => lk.c));
      for (const a of moves) if (want[a.piece] && want[a.piece].has(a.dest)) add(a);
      const bp = s.o[s.ball];
      for (let i = 0; i < 5; i++) {
        if (i === s.ball) continue;
        const mine = moves.filter(a => a.piece === i && a.kind === 'move');
        mine.sort((a, b) => (cheb(b.dest, bp) - cheb(a.dest, bp)) || (a.dest - b.dest));
        if (mine.length) add(mine[0]);
      }
      const scr = acts.filter(a => a.kind === 'screen');
      const sk = a => { const t = s.o[a.piece] + DSTEP[a.target]; let m = INF; for (const xp of s.x) m = Math.min(m, cheb(t, xp)); return m; };
      scr.sort((a, b) => sk(a) - sk(b));
      for (const a of scr.slice(0, 4)) add(a);
    } else {
      if (s.stage === 'reaction') {                       // D-18: the closeouts (a Move facing the shooter), so a Contest can follow
        const sp = s.o[s.ball];
        for (const a of moves) if (adjacent(a.dest, sp) && (a.kind !== 'move' || a.arrow === dirBetween(a.dest, sp))) add(a);
      }
      const cv = read.cover();
      const targets = new Array(5).fill(null).map(() => []);
      for (const [j, resp] of cv.choice) targets[j].push(resp);
      for (const j of read.att_x) for (const r of cv.R[j].slice(1, perPlayer + 1)) targets[j].push(r[0]);
      for (const a of moves) {
        for (const [q, arrow] of targets[a.piece]) if (a.dest === q && (a.kind !== 'move' || a.arrow === arrow)) add(a);
      }
      const spots = [];
      for (const i of read.att_o) for (const lk of read.looks[i].slice(0, 1)) spots.push(lk.c);
      if (!spots.length) spots.push(s.o[s.ball]);
      for (let j = 0; j < 5; j++) {
        const mine = moves.filter(a => a.piece === j);
        if (mine.length && !keep.some(a => a.piece === j && MOVEMENT.has(a.kind))) {
          const dk = a => { let m = INF; for (const c of spots) m = Math.min(m, cheb(a.dest, c)); return m; };
          mine.sort((a, b) => (dk(a) - dk(b)) || ((a.kind !== 'move') - (b.kind !== 'move')) || (a.dest - b.dest) || (a.arrow - b.arrow));
          add(mine[0]);
        }
      }
    }
    return keep.length ? keep : acts;
  }
  const endsTurn = (s, nxt, side) => isChance(nxt) || nxt.stage === 'over' || actor(nxt) !== side || nxt.stage !== s.stage;
  function turns(s, beam, read, evaluate, deadline, expand, second) {
    const side = actor(s), sign = side === 'O' ? 1 : -1;
    const first = candidateActions(s, read);
    const scored = [];
    for (const a of first) {
      if (deadline && now() > deadline) throw TIMEOUT;
      const nxt = apply(s, a);
      scored.push([sign * (evaluate ? evaluate(nxt) : 0.0), [a]]);
    }
    scored.sort((x, y) => y[0] - x[0]);
    const out = scored.slice(0, beam);
    const nexp = expand != null ? expand : Math.max(3, Math.floor(beam / 3));
    for (const [, t] of scored.slice(0, nexp)) {
      const a = t[0], nxt = apply(s, a);
      if (endsTurn(s, nxt, side)) continue;
      for (const b of candidateActions(nxt, null, second)) {
        if (deadline && now() > deadline) throw TIMEOUT;
        if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;
        const n2 = apply(nxt, b);
        out.push([sign * (evaluate ? evaluate(n2) : 0.0), [a, b]]);
      }
    }
    out.sort((x, y) => y[0] - x[0]);
    const seen = new Set(), fin = [];
    for (const [v, t] of out) {
      const key = t.length === 2 && MOVEMENT.has(t[0].kind) && MOVEMENT.has(t[1].kind) ? 'S' + [t[0].id, t[1].id].sort((p, q) => p - q).join(',') : 'T' + turnKey(t);
      if (seen.has(key)) continue;
      seen.add(key); fin.push([v, t]);
      if (fin.length >= beam) break;
    }
    return fin;
  }
  function playTurn(s, t, trusted = true) {   // trusted: t was generated from s (legal by construction)
    let node = s;
    for (const a of t) {
      if (isChance(node) || node.stage === 'over') break;
      if (!trusted && !isLegal(node, a)) break;
      node = apply(node, a);
    }
    return node;
  }
  const PASSIVE = new Set(['end_turn', 'pause', 'hesitate', 'forfeit']);
  class Searcher {
    constructor(me, profile, evaluate, deadline) {
      this.me = me; this.p = profile; this.evaluate = evaluate; this.deadline = deadline;
      this.tt = new Map(); this.tcache = new Map(); this.lcache = new Map(); this.qcache = new Map(); this.killers = new Map(); this.history = new Map();
      this.nodes = 0; this.leaves = 0; this.lam = profile.opponent_model; this.habit = null; this.habit_weight = 0.0; this.partial = 0;
      const sc = D.config.search || {}, on = stableParts();   // step 13: the stable search's five switches (all off)
      this.quiet = on.quiet_points; this.like = on.like_with_like; this.tempoOn = on.tempo; this.playOn = on.play_on;
      this.clear = on.clear_reason;
      this.stable = this.quiet || this.like || this.tempoOn || this.playOn || this.clear;
      this.extCap = sc.extension_cap == null ? 2 : sc.extension_cap;
      this.margin = sc.stable_margin || {}; this.tempo = sc.tempo_gap || {};
      this.extensions = 0; this.capHits = 0; this.trace = []; this.kept = 0;
      this.goals = sc.goals === true && D.config.eval.advantages === true;   // step 16, stage 4 (search.Searcher)
      this.phis = new Map(); this.touches = new Map();
      this.depthSeconds = []; this.t0 = now();   // step 13: the time each completed depth was reached at
      this.settleShots = settleOn(); this.scache = new Map();   // step 18b (eval.settle_shots)
      this.help = helpOn(); this.fcache = new Map();            // step 18c (eval.help_readings, off)
    }
    check() { if (now() > this.deadline) throw TIMEOUT; }
    leaf(s, z) {
      this.leaves++;
      if (this.settleShots && !isChance(s) && s.stage !== 'play' && s.stage !== 'over') return this.settled(s, z);
      const key = z === undefined ? zobrist(s) : z;
      let v = this.lcache.get(key);
      if (v === undefined) { v = this.evaluate(s); this.lcache.set(key, v); }
      if (this.help && !isChance(s) && s.stage === 'play' && !s.pending && actor(s) === 'O') v = this.floor(s, v, key);   // step 18c
      if (this.tempoOn && !isChance(s) && s.stage === 'play') {
        const t = this.tempo[phaseOf(s)] || 0.0;
        v += actor(s) === 'O' ? -t / 2 : t / 2;
      }
      if (this.goals) v += this.phi(s, key);
      return v;
    }
    // step 18b (search.Searcher.settled): a position with a shot declared, valued by the rules themselves: the side to
    // act takes its best legal action until the possession ends or open play resumes, the dice at their chances. In
    // the reaction's first action only movements ending next to the shooter are played, and after a movement only a
    // Contest, a Steal or ending it (no other movement can change the Contest or a Steal: the reaction is at most two
    // actions and those are its last).
    // step 18c (search.Searcher.floor), the first help reading: the drive priced by the rules. With the offence to act
    // in open play the possession is worth at least the best shot the ball handler can release this turn: his shot
    // from where he stands, or after one movement, each settled by the rules. The reading names the candidates (its
    // looks released now, best first); a candidate whose reading is no better than the value so far can't raise it.
    floor(s, v, z) {
      const key = z === undefined ? zobrist(s) : z;
      const hit = this.fcache.get(key);
      if (hit !== undefined) return hit[0];
      let banked = 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos);
      banked += foulExternality(s);
      let best = [v, -1, ''], acts = null;
      const looks = readOf(s).looks[s.ball] || [];
      for (const lk of looks) {
        if (!lk.now) continue;
        if (banked + lk.base <= best[0]) break;
        let n = s;
        if (lk.route !== 'shoot') {
          if (acts === null) acts = legalActions(s);
          const a = acts.find(x => MOVEMENT.has(x.kind) && x.piece === s.ball && x.dest === lk.c);
          if (!a) continue;
          n = apply(s, a);
          if (isChance(n) || n.stage !== 'play' || actor(n) !== 'O') continue;
        }
        for (const b of legalActions(n)) {
          if (b.kind !== 'shot') continue;
          const w = this.settleNode(apply(n, b));
          if (w > best[0]) best = [w, lk.c, b.shot];
        }
      }
      this.fcache.set(key, best);
      return best[0];
    }
    settled(s, z) {
      const key = z === undefined ? zobrist(s) : z;
      let v = this.scache.get(key);
      if (v !== undefined) return v;
      const side = actor(s);
      let acts;
      if (s.stage === 'reaction') {
        // a second movement can't be followed by a Contest or a Steal (two actions at most): only those and ending count
        if (s.turn_n >= 1) acts = forcingActions(s, 'stage');
        else { const sp = s.o[s.ball]; acts = legalActions(s).filter(a => !MOVEMENT.has(a.kind) || adjacent(a.dest, sp)); }
      } else acts = legalActions(s);
      let best = null;
      for (const a of acts) {
        const w = this.settleNode(apply(s, a));
        if (best === null || (side === 'O' ? w > best : w < best)) best = w;
      }
      v = best === null ? this.evaluate(s) : best;
      this.scache.set(key, v);
      return v;
    }
    settleNode(n) {
      if (isChance(n)) { let t = 0; for (const o of n.outcomes) t += o[0] * this.settleNode(o[2]); return t; }
      if (n.stage === 'over') return terminalValue(n);
      if (n.stage === 'play') return this.leaf(n);
      return this.settled(n);
    }
    phi(s, z) {
      if (isChance(s) || s.stage !== 'play') return 0.0;
      const key = z === undefined ? zobrist(s) : z;
      let v = this.phis.get(key);
      if (v === undefined) {
        if (s.pending) v = laneP(W_(s, { ball: s.pending[0] }), s.pending[1], s.o[s.pending[1]]) * this.phi(W_(s, { ball: s.pending[1], pending: null }));
        else v = readOf(s, key).phi();
        this.phis.set(key, v);
      }
      return v;
    }
    touch(s, z) {
      let g = this.touches.get(z);
      if (g === undefined) {
        g = [];
        if (s.stage === 'play' && !s.pending) {
          const top = [null, null, null, null, null];
          for (const a of readOf(s, z).advantages()) if (a.sq >= 0 && a.worth > 1e-9 && a.worth > (top[a.i] ? top[a.i][0] : 0.0)) top[a.i] = [a.worth, a.sq];
          for (let i = 0; i < 5; i++) if (top[i]) g.push([i, top[i][1]]);
        }
        this.touches.set(z, g);
      }
      return g;
    }
    unsettled(s) {
      if (s.stage !== 'play') return this.playOn ? 'stage' : null;
      if (s.pending) return this.playOn ? 'pass' : null;
      if (midTurn(s) && this.quiet) return 'mid';
      if (this.playOn && actor(s) === 'O') {
        if (SPEED.quiet_read) return readOf(s).quickShotFirst() ? 'shot' : null;   // the same reading, from the shared read
        const r = new Read(s, { k: 0, looks_per: 3 });
        const sn = r.shotNow();
        if (sn !== null && sn > r.possession() + 1e-9) return 'shot';
      }
      return null;
    }
    extend(s, why, depth) {
      const side = actor(s);
      let list;
      if (why === 'mid') list = this.turnsOf(s).map(r => r[1]);
      else {
        const kinds = why === 'shot' ? SHOT_ONLY : FORCING;
        if (SPEED.forcing) list = forcingActions(s, why).map(a => [a]);
        else list = legalActions(s).filter(a => kinds.has(a.kind) || (why === 'stage' && s.stage !== 'reaction')).map(a => [a]);
      }
      if (!list.length) return this.leaf(s);
      this.extensions++;
      let best = why === 'shot' ? readOf(s).possession() : null;
      for (const t of list) {
        const child = playTurn(s, t, false);
        const d = (why === 'mid' || (this.quiet && !isChance(child) && child.stage !== 'over' && actor(child) === side && midTurn(child))) ? depth : depth - 1;
        const v = this.value(child, d, VMIN, VMAX);
        if (best === null || (side === 'O' ? v > best : v < best)) best = v;
      }
      return best;
    }
    value(node, depth, alpha, beta) {
      this.check();
      if (isChance(node)) return this.chance(node, depth, alpha, beta);
      const s = node;
      if (s.stage === 'over') return terminalValue(s);
      if (depth <= 0) {
        if (this.settleShots && s.stage !== 'play') return this.leaf(s);      // step 18b: the declared shot is settled by the rules
        if (this.quiet || this.playOn) {
          const why = this.unsettled(s);
          if (why !== null) {
            if (depth <= -this.extCap && why !== 'mid') { this.capHits++; return this.leaf(s); }
            return this.extend(s, why, depth);
          }
        }
        return this.leaf(s);
      }
      const z = zobrist(s), key = ttKey(z, depth);
      const hit = this.tt.get(key);
      if (hit !== undefined) {
        const v = hit[0], flag = hit[1];
        if (flag === 0 || (flag === 1 && v >= beta) || (flag === -1 && v <= alpha)) return v;
      }
      const side = actor(s);
      let ts = this.turnsOf(s, z);
      if (!ts.length) return this.leaf(s);
      ts = this.order(ts, depth, z, s);
      this.nodes++;
      const a0 = alpha, b0 = beta;
      let best = null;
      const opponent = side !== this.me;
      const mix = opponent && (this.lam < 1.0 || !!this.habit);
      let passive = null;
      if (mix) {
        const w = ts.filter(r => PASSIVE.has(r[1][0].kind)).map(r => r[1]);
        passive = w.length ? this.value(playTurn(s, w[0]), depth - 1, VMIN, VMAX) : null;
      }
      for (const [, t] of ts) {
        const child = playTurn(s, t);
        const d = (this.quiet && !isChance(child) && child.stage !== 'over' && actor(child) === side && midTurn(child)) ? depth : depth - 1;
        const v = this.value(child, d, mix ? VMIN : alpha, mix ? VMAX : beta);
        if (side === 'O') { if (best === null || v > best[0]) best = [v, t]; if (!mix) alpha = Math.max(alpha, v); }
        else { if (best === null || v < best[0]) best = [v, t]; if (!mix) beta = Math.min(beta, v); }
        if (!mix && alpha >= beta) {
          this.killer(depth, t);
          this.history.set(t[0].id, (this.history.get(t[0].id) || 0) + depth * depth);
          break;
        }
      }
      let v = best[0];
      if (mix && passive !== null) v = this.lam * v + (1 - this.lam) * passive;
      if (mix && this.habit) {
        const kind = this.habit[s.stage + '/' + side];
        let hv = null;
        for (const [, t] of ts) if (t[0].kind === kind) { hv = this.value(playTurn(s, t), depth - 1, VMIN, VMAX); break; }
        if (hv !== null) v = (1 - this.habit_weight) * v + this.habit_weight * hv;
      }
      let flag = 0;
      if (!mix) flag = v >= b0 ? 1 : v <= a0 ? -1 : 0;
      this.tt.set(key, [v, flag, best[1]]);
      return v;
    }
    chance(node, depth, alpha, beta) {
      const outs = node.outcomes, n = outs.length;
      const probs = outs.map(o => o[0]);
      const lo = new Array(n).fill(VMIN), hi = new Array(n).fill(VMAX);
      for (let k = 0; k < n; k++) {
        const sub = outs[k][2];
        if (probs[k] === 0 || isChance(sub)) continue;
        if (sub.stage === 'over') { lo[k] = hi[k] = terminalValue(sub); continue; }
        const z = zobrist(sub);
        const hit = this.tt.get(ttKey(z, depth));
        if (hit !== undefined && hit[1] === 0) { lo[k] = hi[k] = hit[0]; continue; }
        if (depth <= 0) continue;
        const ts = this.turnsOf(sub, z);
        if (!ts.length) continue;
        const first = this.order(ts, depth, z, sub)[0][1];
        const v = this.value(playTurn(sub, first), depth - 1, VMIN, VMAX);
        if (actor(sub) === 'O') lo[k] = Math.max(lo[k], v); else hi[k] = Math.min(hi[k], v);
      }
      let L = 0, Hh = 0;
      for (let k = 0; k < n; k++) { L += probs[k] * lo[k]; }
      for (let k = 0; k < n; k++) { Hh += probs[k] * hi[k]; }
      if (Hh <= alpha) return Hh;
      if (L >= beta) return L;
      let total = 0.0;
      for (let k = 0; k < n; k++) {
        const pf = probs[k];
        if (pf === 0) continue;
        let v;
        if (lo[k] === hi[k]) v = lo[k];
        else {
          let rl = 0, rh = 0;
          for (let m = k + 1; m < n; m++) rl += probs[m] * lo[m];
          for (let m = k + 1; m < n; m++) rh += probs[m] * hi[m];
          const a = (alpha - total - rh) / pf, b = (beta - total - rl) / pf;
          v = this.value(outs[k][2], depth, Math.max(VMIN, a), Math.min(VMAX, b));
        }
        total += pf * v;
        lo[k] = hi[k] = v;
        let dl = total, dh = total;
        for (let m = k + 1; m < n; m++) dl += probs[m] * VMIN;
        for (let m = k + 1; m < n; m++) dh += probs[m] * VMAX;
        if (dh <= alpha) return dh;
        if (dl >= beta) return dl;
      }
      return total;
    }
    quick(node) {
      if (isChance(node)) { let t = 0; for (const o of node.outcomes) t += o[0] * this.quick(o[2]); return t; }
      if (node.stage === 'over') return terminalValue(node);
      if (this.settleShots && node.stage !== 'play') return this.settled(node);   // step 18b: ordered by its settled value
      return readOf(node).quickLeaf();
    }
    turnsOf(s, z) {
      const key = z === undefined ? zobrist(s) : z;
      let hit = this.tcache.get(key);
      if (hit === undefined) {
        hit = turns(s, this.p.beam, null, n => this.quick(n), this.deadline, 3, 1);
        this.tcache.set(key, hit);
      }
      return hit;
    }
    killer(depth, t) {
      let ks = this.killers.get(depth); if (!ks) { ks = []; this.killers.set(depth, ks); }
      const k = turnKey(t);
      if (!ks.some(x => turnKey(x) === k)) { ks.unshift(t); ks.length = Math.min(ks.length, 2); }
    }
    order(ts, depth, z, s) {
      const ks = (this.killers.get(depth) || []).map(turnKey);
      // step 13: this position's best turn from the look-ahead one shorter is tried first (ordering only)
      const prev = z !== undefined && SPEED.tt_order ? this.tt.get(ttKey(z, depth - 1)) : undefined;
      const first = prev !== undefined && prev[2] ? turnKey(prev[2]) : null;
      // step 16: a turn that works on a top goal is searched first (ordering only)
      const goals = this.goals && s !== undefined && depth >= 2 ? this.touch(s, z) : [];
      const offGoal = t => {
        for (const a of t) for (const [i, sq] of goals) {
          if ((a.side === 'O' && a.piece === i) || a.dest === sq || (a.side === 'X' && a.dest >= 0 && adjacent(a.dest, sq))) return 0;
        }
        return 1;
      };
      const keyed = ts.map(r => { const k = turnKey(r[1]); return [k === first ? -1 : ks.includes(k) ? 0 : 1, -(r[0] + 0.01 * (this.history.get(r[1][0].id) || 0)), r, goals.length ? offGoal(r[1]) : 0]; });
      keyed.sort((a, b) => (a[0] - b[0]) || (a[3] - b[3]) || (a[1] - b[1]));
      return keyed.map(k => k[2]);
    }
    root(s, maxDepth) {
      const side = actor(s);
      const budget = this.deadline - now();
      const rootRead = new Read(s, { exact: budget >= 0.8 });
      const ts = turns(s, this.p.beam, rootRead, n => this.quick(n), null, budget >= 0.8 ? null : 2, budget >= 0.8 ? 2 : 1);
      const deadline = this.deadline; this.deadline = Infinity;
      let results = [];
      const sign = side === 'O' ? 1 : -1;
      ts.forEach(([q, t], k) => {
        if (k >= 3 && now() > deadline) { results.push([sign * q, t]); return; }
        const n = playTurn(s, t);
        if (this.quiet || this.playOn) results.push([this.value(n, this.childDepth(s, n, 1), VMIN, VMAX), t]);
        else results.push([!isChance(n) ? this.leaf(n) : this.value(n, 0, VMIN, VMAX), t]);
      });
      this.deadline = deadline;
      let reached = 1;
      this.partial = 0;
      const byBest = (x, y) => (side === 'O' ? y[0] - x[0] : x[0] - y[0]);
      const byDepth = new Map([[1, results.slice()]]);
      this.note(1, results, side);                       // the root choice at each completed depth (a record only)
      for (let depth = 2; depth <= maxDepth; depth++) {
        const out = [];
        try {
          for (const [, t] of results.slice().sort(byBest)) {
            const n = playTurn(s, t);
            out.push([this.value(n, this.childDepth(s, n, depth), VMIN, VMAX), t]);
          }
          results = out; reached = depth;
          byDepth.set(depth, out.slice());
          this.note(depth, out, side);
        } catch (e) {
          if (e !== TIMEOUT) throw e;
          if (this.like || this.clear) break;
          this.partial = out.length;
          if (out.length) {
            const pv = out[0][0];
            let best = out[0];
            for (const r of out) if (side === 'O' ? r[0] > best[0] : r[0] < best[0]) best = r;
            if ((side === 'O' ? best[0] > pv : best[0] < pv) || out.length === 1) {
              const done = new Set(out.map(r => turnKey(r[1])));
              results = out.concat(results.filter(r => !done.has(turnKey(r[1]))));
            }
          }
          break;
        }
      }
      if (this.like || this.clear) [results, reached] = this.settle(s, byDepth, side);
      if (this.goals) {                                  // the root's own potential comes off
        const p0 = this.phi(s);
        results = results.map(r => [r[0] - p0, r[1]]);
        this.trace = this.trace.map(r => [r[0], r[1], r[2] - p0]);
      }
      results.sort(byBest);
      return [results, reached];
    }
    childDepth(s, child, depth) {
      if (this.quiet && !isChance(child) && child.stage !== 'over' && actor(child) === actor(s) && midTurn(child)) return depth;
      return depth - 1;
    }
    note(depth, res, side) {
      let best = res[0];
      for (const r of res) if (side === 'O' ? r[0] > best[0] : r[0] < best[0]) best = r;
      this.trace.push([depth, best[1], best[0]]);
      this.depthSeconds.push([depth, now() - this.t0]);
    }
    settle(s, byDepth, side) {
      const done = [...byDepth.keys()].sort((a, b) => a - b);
      const even = this.like ? done.filter(d => d % 2 === 0) : [];
      const d = even.length ? even[even.length - 1] : done[done.length - 1];
      let res = byDepth.get(d).slice();
      const sign = side === 'O' ? 1 : -1;
      const pick = rs => { let b = rs[0]; for (const r of rs) if (sign * r[0] > sign * b[0]) b = r; return b; };
      const best = pick(res);
      const prev = this.clear ? byDepth.get(d - 2) : undefined;
      if (prev) {
        const pTurn = pick(prev)[1], pk = turnKey(pTurn);
        const pNow = res.find(r => turnKey(r[1]) === pk);
        const margin = this.margin[phaseOf(s)] || 0.0;
        if (pNow && turnKey(best[1]) !== pk && sign * (best[0] - pNow[0]) <= margin) {
          this.kept++;
          res = res.map(r => (turnKey(r[1]) === pk ? [best[0], r[1]] : r));
          res.sort((x, y) => (sign * (y[0] - x[0])) || ((turnKey(x[1]) === pk ? 0 : 1) - (turnKey(y[1]) === pk ? 0 : 1)));
          return [res, d];
        }
      }
      return [res, d];
    }
  }
  const FORCING = new Set(['shot', 'contest', 'steal', 'end_turn', 'intercept', 'pause', 'hesitate']);
  const SHOT_ONLY = new Set(['shot']);
  const phaseOf = s => String(Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1)));
  const midTurn = s => s.stage === 'play' && s.turn_n > 0 && !s.pending;

  // ---- the agent's evaluation (agent.Agent._evaluate) --------------------------------------------------------------
  function attentionSets(s, n) {
    if (n >= 5) return null;
    const bp = s.o[s.ball];
    let o = [0, 1, 2, 3, 4].sort((a, b) => (cheb(s.o[a], bp) - cheb(s.o[b], bp)) || (a - b)).slice(0, n);
    if (!o.includes(s.ball)) o = [s.ball].concat(o.slice(0, n - 1));
    const x = [0, 1, 2, 3, 4].sort((a, b) => (cheb(s.x[a], bp) - cheb(s.x[b], bp)) || (a - b)).slice(0, n);
    return [o, x];
  }
  function withStale(s, side, stale) {
    if (side === 'O') {
      const [xs, arrows] = stale;
      if (xs.some(q => s.o.includes(q))) return s;
      return W_(s, { x: xs, arrows });
    }
    const [os] = stale;
    if (os.some(q => s.x.includes(q))) return s;
    return W_(s, { o: os });
  }
  function makeEvaluate(profile, side, stale) {
    const attN = profile.attention, delay = profile.reaction_delay;
    const ev = node => {
      if (isChance(node)) { let t = 0; for (const o of node.outcomes) t += o[0] * ev(o[2]); return t; }
      if (node.stage === 'over') return terminalValue(node);
      let s = node;
      if (delay === 'previous_board' && stale) s = withStale(s, side, stale);
      const att = attentionSets(s, attN);
      if (!att && s === node) return readOf(s).leaf();         // the default read: shared with the ordering
      return new Read(s, { attention: att, k: attN < 5 ? 2 : null }).leaf();
    };
    return ev;
  }
  // One decision's search: what agent.Agent.choose asks of search.Searcher. req: {state, ctx, level profile, side,
  // budget (seconds; null = no limit), depth [lo, hi], stale, habit, habit_weight}.
  function search(req) {
    const ctx = req.ctxObj || makeCtx(req.ctx);
    const s = req.stateObj || stateFrom(req.state, ctx);      // stateObj (step 17): a state already built
    const prof = req.profile, me = actor(s);
    let stale = null;
    if (req.stale) stale = me === 'O' ? [req.stale[0].map(parseSq), req.stale[1].slice()] : [req.stale[0].map(parseSq)];
    const t0 = now();
    const deadline = req.budget == null ? Infinity : t0 + req.budget;
    READS = new Map(); READS_OLD = new Map();
    const srch = new Searcher(me, prof, makeEvaluate(prof, me, stale), deadline);
    if (req.habit) { srch.habit = req.habit; srch.habit_weight = req.habit_weight == null ? 0.3 : req.habit_weight; }
    const maxDepth = req.max_depth != null ? req.max_depth : prof.depth[1];
    const [results, reached] = srch.root(s, maxDepth);
    // the principal line: the best turn, then each reply the transposition table holds for the likeliest outcome
    const pv = [];
    if (results.length) {
      let t = results[0][1], node = s;
      for (let d = reached; d >= 1 && t; d--) {
        pv.push(t.map(actionStr));
        node = playTurn(node, t);
        while (isChance(node)) { let b = node.outcomes[0]; for (const o of node.outcomes) if (o[0] > b[0]) b = o; node = b[2]; }
        if (node.stage === 'over' || d - 1 < 1) break;
        const hit = srch.tt.get(ttKey(zobrist(node), d - 1));
        t = hit ? hit[2] : null;
      }
    }
    return { results: results.map(([v, t]) => [v, t.map(actionJSON)]), reached, leaves: srch.leaves, nodes: srch.nodes,
      partial: srch.partial, seconds: now() - t0, pv,
      stable: srch.stable, extensions: srch.extensions, cap_hits: srch.capHits, kept: srch.kept, depth_seconds: srch.depthSeconds,
      trace: srch.trace.map(([d, t, v]) => [d, t.map(actionJSON), v]) };
  }

  // ---- goals (goals.goals_in) and overloads (decide.Read.overloads), for the agent's goal commitment ------------------
  function overloads(r) {
    const cv = r.cover(), R = cv.R, out = [];
    const base = new Float64Array(5); for (const i of r.att_o) base[i] = r.threat[i].value;
    const threats = r.att_o.filter(i => base[i] > 0);
    const reducers = new Map();
    for (const i of threats) reducers.set(i, r.att_x.filter(j => R[j].slice(1).some(([, left]) => left[i] < base[i] - 1e-9)));
    for (const j of r.att_x) {
      const only = threats.filter(i => { const rd = reducers.get(i); return rd.length === 1 && rd[0] === j; });
      for (let x = 0; x < only.length; x++) for (let y = x + 1; y < only.length; y++) {
        const a = only[x], b = only[y];
        const both = R[j].slice(1).some(([, left]) => left[a] < base[a] - 1e-9 && left[b] < base[b] - 1e-9);
        if (!both) out.push({ defender: j, a, b, value: Math.min(base[a], base[b]) });
      }
    }
    out.sort((p, q) => q.value - p.value);
    return out;
  }
  function matchups(r) {
    const out = new Map();
    for (const i of r.att_o) {
      const lks = r.looks[i];
      if (!lks.length) continue;
      const lk = lks[0];
      let best = null, who = -1;
      for (const d of r.att_x) {
        const vals = lk.vals[d]; if (!vals) continue;
        let v = Infinity; for (const x of vals) if (x < v) v = x;
        if (best === null || v < best) { best = v; who = d; }
      }
      out.set(i, who);
    }
    return out;
  }
  function lanesOf(s) {
    const a = s.o[s.ball], out = new Map();
    for (let i = 0; i < 5; i++) if (i !== s.ball && ONB[s.o[i]]) out.set(i, laneSquares(a, s.o[i]));
    return out;
  }
  function helpersOn(s, lane) {
    const out = [];
    for (let d = 0; d < 5; d++) {
      const [cm, ql] = caps(s, 'X', d);
      const one = oneAction(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, cm, ql);
      for (const b of lane.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { out.push(d); break; }
    }
    return out;
  }
  const ZNAME = z => ZCH[z];
  function goalsIn(before, after, side, rb, ra, turn) {
    const out = [];
    if (side === 'O') {
      for (const ov of overloads(ra).slice(0, 3)) out.push([['Overload', ov.defender, ov.a, ov.b], `make X${ov.defender + 1} the only answer to O${ov.a + 1} and O${ov.b + 1}`]);
      const lb = lanesOf(before), la = lanesOf(after);
      for (const [i, lane] of lb) {
        if (!la.has(i)) continue;
        const was = helpersOn(before, lane), now = new Set(helpersOn(after, la.get(i)));
        for (const d of was) if (!now.has(d)) out.push([['Displace', d, i], `move X${d + 1} out of the lane to O${i + 1}`]);
      }
      for (let i = 0; i < 5; i++) {
        const has = after.ball === i || (after.pending && after.pending[1] === i);
        if (!has || !ONB[after.o[i]]) continue;
        const sq = after.o[i];
        let k = 9;
        for (let d = 0; d < 5; d++) {
          const cm = ra._cm[d]; let m = 9;
          if (cm) { let mm = INF; for (let t = 0; t < 6; t++) mm = Math.min(mm, cm[BI[sq] * 6 + t]); if (mm < INF) m = mm; }
          k = Math.min(k, m);
        }
        if (k >= 1) out.push([['CatchOpen', i, 1], `get O${i + 1} the ball with every cover at least a step away`]);
      }
      const mb = matchups(rb), ma = matchups(ra);
      let changed = 0;
      for (const [i, w] of mb) if (ma.has(i) && w !== ma.get(i) && ma.get(i) >= 0) changed++;
      if (changed >= 2) out.push([['ForceRotation', changed], `force the defence to change ${changed} matchups`]);
      for (const a of turn) if (a.kind === 'shot') { const z = ZNAME(ZN[before.o[a.piece]]); out.push([['Shot', a.piece, z], `O${a.piece + 1} shoots from the ${z} zone`]); }
    } else {
      for (let i = 0; i < 5; i++) {
        const tb = rb.threat[i] ? rb.threat[i].value : 0, ta = ra.threat[i] ? ra.threat[i].value : 0;
        if (tb > 0 && ta <= 0.5 * tb) out.push([['Wall', i], `wall off O${i + 1}`]);
      }
      for (let i = 0; i < 5; i++) {
        if (i === after.ball || !ONB[after.o[i]]) continue;
        const pb = before.ball !== i ? laneP(before, i, before.o[i]) : 1;
        const pa = after.ball !== i ? laneP(after, i, after.o[i]) : 1;
        if (pa <= 0.5 && 0.5 < pb) out.push([['Deny', i], `deny the lane to O${i + 1}`]);
      }
      const ob = overloads(rb), oa = overloads(ra);
      if (ob.length && (!oa.length || oa[0].value < ob[0].value - 1e-9)) out.push([['Shrink', ob[0].defender], `free X${ob[0].defender + 1} from having to choose`]);
      if (ra.cover().value < rb.cover().value - 1e-9 && after.clock <= 6) out.push([['Pressure'], 'make the clock work: no open look as it runs down']);
    }
    return out;
  }
  function likeliest(node) {
    while (isChance(node)) { let best = node.outcomes[0]; for (const o of node.outcomes) if (o[0] > best[0]) best = o; node = best[2]; }
    return node;
  }
  function actionFrom(t) { return A(t[0], t[1], t[2], t[3] ? parseSq(t[3]) : -1, t[4], t[5], t[6] || ''); }
  // agent.Agent.choose after its search: the base leaf and the goals of each turn it weighs. req: {state, ctx, side, turns}
  function goalsJSON(text) {
    const req = JSON.parse(text);
    const key = JSON.stringify(req.ctx);
    let ctx = CTXS.get(key);
    if (!ctx) { if (CTXS.size >= 4) CTXS.clear(); ctx = makeCtx(req.ctx); CTXS.set(key, ctx); }
    const s = stateFrom(req.state, ctx), rb = new Read(s);
    const out = { base: rb.leaf(), goals: [] };
    for (const tj of req.turns) {
      const t = tj.map(actionFrom);
      const after = likeliest(playTurn(s, t, false));
      out.goals.push(after.stage === 'over' ? [] : goalsIn(s, after, req.side, rb, new Read(after), t));
    }
    return JSON.stringify(out);
  }

  // The browser worker's entry: Python (agent.Agent.choose, in Pyodide) passes the request as JSON text. The context is
  // kept between decisions of the same possession (its caches with it).
  const CTXS = new Map();
  function searchJSON(text) {
    const req = JSON.parse(text);
    const key = JSON.stringify(req.ctx);
    let ctx = CTXS.get(key);
    if (!ctx) { if (CTXS.size >= 4) CTXS.clear(); ctx = makeCtx(req.ctx); CTXS.set(key, ctx); }
    req.ctxObj = ctx;
    return JSON.stringify(search(req));
  }

  // ---- the equivalence probe: every measured quantity of one state --------------------------------------------------
  function probe(js, ctxJs, opts = {}) {
    const ctx = makeCtx(ctxJs), s = stateFrom(js, ctx);
    const mapOut = m => { const o = {}; for (const [q, n] of m) o[sqName(q)] = n; return o; };
    const fixedOut = m => { const o = {}; for (const [q, arrs] of m) { const r = {}; for (const [a, n] of arrs) r[a] = n; o[sqName(q)] = r; } return o; };
    const out = { legal: legalActions(s).map(actionStr) };
    if (s.stage === 'over') return out;
    out.attacker_reach = [0, 1, 2, 3, 4].map(i => mapOut(attackerReach(s, i)));
    out.defender_reach = [0, 1, 2, 3, 4].map(d => { const [f, x] = defenderMap(s, d, false); return [mapOut(f), fixedOut(x)]; });
    out.defender_exact = [0, 1, 2, 3, 4].map(d => { const [f, x] = defenderMap(s, d, true); return [mapOut(f), fixedOut(x)]; });
    if (s.stage === 'play' || s.stage === 'reaction') {
      for (const exact of [false, true]) {
        const r = new Read(s, { exact });
        const cv = r.cover();
        const tag = exact ? 'exact' : 'geo';
        out['threat_' + tag] = [0, 1, 2, 3, 4].map(i => [r.threat[i].value, r.threat[i].sq >= 0 ? sqName(r.threat[i].sq) : null, r.threat[i].route]);
        out['cover_' + tag] = [cv.value, [...cv.choice].map(([j, resp]) => [j, sqName(resp[0]), resp[1], resp[2]]).sort((a, b) => a[0] - b[0]),
          [0, 1, 2, 3, 4].map(i => cv.residual[i])];
        out['leaf_' + tag] = r.leaf();
        if (!s.pending && s.stage === 'play') out['features_' + tag] = r.features();     // step 17: the named readings
        if (D.config.eval.advantages === true) {         // step 16: the advantage list, each worth, and the potential
          out['adv_' + tag] = [r.advantages().map(a => [a.kind, a.i, a.j, a.sq >= 0 ? sqName(a.sq) : null, a.stage, a.value, a.chance, a.worth, a.gap]), r.phi()];
        }
        if (r.budgetOn() && !s.pending) {                // step 13 B: the allocation itself, and every look's two parts
          const bd = r.budget();
          out['budget_' + tag] = [bd.value, [0, 1, 2, 3, 4].map(i => (bd.left[i] === undefined ? null : bd.left[i])), bd.shares];
          out['split_' + tag] = [0, 1, 2, 3, 4].map(i => (r.looks[i] || []).map(lk => lookSplit(lk)));
        }
      }
      out.quick = new Read(s, { k: 0, looks_per: 3 }).leaf();
    }
    return out;
  }

  const featuresOf = s => (s.stage === 'play' && !s.pending ? readOf(s).features() : null);    // step 17
  const bankedOf = s => 5 * s.bonus5 + (s.ctx.digital ? 0 : -5 * s.tos) + foulExternality(s);   // what the possession has already earned
  const handLeaf = s => readOf(s)._handLeaf();                                                       // today's hand-combined reading
  return { setCalibrated, setTabletopMap, setSettle, setHelp, ceilingOf, setLearned, FEATURE_NAMES, featuresOf, bankedOf, handLeaf, stateJSON, actionJSON, isChance, scoreTotal, init, setLeafMode, setStable, setSearch, stableParts, setReach, setSpeed, setBudget, setAdvantages, setGoals, REACH_STATS, reachMap, searchJSON, goalsJSON, makeCtx, stateFrom, legalActions, apply, Read, search, probe, zobrist, actor, terminalValue, sqName, parseSq,
    actionStr, actionJSON, isChance, attackerReach, defenderMap, contestMap, candidateActions, turns, playTurn, Searcher,
    makeEvaluate, scoreTotal, vcoarse, laneP, _caches: () => [_GR.size, _CM.size, _LS.size, _OA.size] };
})();
if (typeof module !== 'undefined') module.exports = PMEngine;
if (typeof self !== 'undefined') self.PMEngine = PMEngine;
