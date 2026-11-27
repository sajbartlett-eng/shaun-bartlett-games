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
  const ZN = new Uint8Array(NSQ);
  const DEEP = new Uint8Array(NSQ);           // D-274: squares past the three-point band (board.deep)            // 0 '.', 1 K, 2 M, 3 L, 4 '3'
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
  const INKEY = new Uint8Array(NSQ);                      // D-172: the key as drawn: columns G to K, rows 1 to 6
  for (let c = 0; c < NSQ; c++) INKEY[c] = SX[c] >= 6 && SX[c] <= 10 && SY[c] >= 1 && SY[c] <= 6 ? 1 : 0;
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
  // Step 31, Part C: a store in two generations (see MAP_MEMO): full, the newer becomes the older and the oldest is dropped.
  class Memo2 {
    constructor(max) { this.max = max; this.cur = new Map(); this.old = new Map(); }
    get(k) {
      let v = this.cur.get(k);
      if (v !== undefined) return v;
      v = this.old.get(k);
      if (v !== undefined) this.set(k, v);
      return v;
    }
    set(k, v) {
      if (this.cur.size >= this.max) { this.old = this.cur; this.cur = new Map(); }
      this.cur.set(k, v);
    }
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
    // board.deep (D-274): squares past the three-point band in each column, rows up to 12
    const top = {};
    for (let c = 0; c < NSQ; c++) if (ONB[c] && ZN[c] === 4) top[SX[c]] = Math.max(top[SX[c]] || 0, SY[c]);
    for (let c = 0; c < NSQ; c++) { DEEP[c] = 0; if (ONB[c] && ZN[c] === 0 && top[SX[c]] && SY[c] > top[SX[c]] && SY[c] <= 12) DEEP[c] = SY[c] - top[SX[c]]; }
    D.config = data.config; D.vcoarse = data.vcoarse || {}; D.ready = true;
    D.segments = data.segments || null;                  // step 31 (D-287): the court's segments, one data table for both engines
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
  // step 18i (rules_config.app_rule): 'app' is on in the app's format and off at the table; 'on'; 'off'
  const APP_RULES = { three_seconds: 'app', closely_guarded: 'app', fiba_fouled_shot: 'app', soft_contest: 'app', fiba_steal_foul: 'app', off_balance: 'app', position_contest: 'app', points_play_on: 'app', no_rim_shot: 'app', contest_costs: 'app', block: 'app', fakes: 'app', pivot: 'app', deep_range: 'app' };     // the defaults: on in the app
  const appRule = (r, name) => { const v = r && r[name] !== undefined ? r[name] : APP_RULES[name]; return v === 'app' ? !!(r && r.digital) : v === 'on'; };
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
  // rules_config.deep_rows_for (D-274): Senior Pro 5, Semi-pro 2, Amateur 1, Youth 1, Junior 0; no level: Senior Pro
  const deepRowsFor = table => {
    const [age, std] = String(table || 'senior/pro').split('/');
    if (age === 'youth') return 1;
    if (age === 'junior') return 0;
    return ({ pro: 5, semi_pro: 2, amateur: 1 })[std] !== undefined ? ({ pro: 5, semi_pro: 2, amateur: 1 })[std] : 5;
  };
  // scoring.shot_zone, deep_cut, card_shot (D-274): a deep square this offence may shoot from is a three, 1 off a square
  const szone = (ctx, c) => (ZN[c] === 0 && DEEP[c] && DEEP[c] <= ctx.deep ? 4 : ZN[c]);
  const deepCut = (ctx, c) => (ZN[c] === 0 && DEEP[c] && DEEP[c] <= ctx.deep ? DEEP[c] : 0);
  const cardShot = (ctx, card, t, c) => { const r = card.sh[t]; if (t !== 'three') return r; const k = deepCut(ctx, c); return k ? Math.max(1, r - k) : r; };
  let _CTXN = 0;
  function makeCtx(c) {
    checkRules(c.rules || {});
    return { id: ++_CTXN, off: c.off.map(makeCard), dfn: c.dfn.map(makeCard), digital: !!(c.rules && c.rules.digital),
      bonus_from: (c.rules && c.rules.bonus_from) || 5, quarter_possessions: (c.rules && c.rules.quarter_possessions) || 18,
      card_clock: c.card_clock, inbounder: c.inbounder, coach_call: !!c.coach_call, three_only: !!c.three_only,
      // Step 31 (D-289): what a shot is worth right now, by zone, for every reading. Normally 2 and 3. A scenario may set it
      // (worth: [a two, a three]); on the Need a Three card only a three scores, so a two is worth 0. No control for the player.
      worth: c.worth ? [0, c.worth[0], c.worth[0], c.worth[0], c.worth[1]] : (c.three_only ? [0, 0, 0, 0, 3] : [0, 2, 2, 2, 3]),
      two_or_three: !!c.two_or_three, hold_for_one: !!c.hold_for_one, team_fouls: c.team_fouls || 0,
      quarter_left: c.quarter_left || 0, table: c.table || 'senior/pro',
      soft: appRule(c.rules, 'soft_contest'), fibaSteal: appRule(c.rules, 'fiba_steal_foul'),      // step 18j (D-177, D-179)
      pos: appRule(c.rules, 'position_contest') && appRule(c.rules, 'soft_contest'),
      cc: appRule(c.rules, 'contest_costs') && appRule(c.rules, 'position_contest') && appRule(c.rules, 'soft_contest'),    // D-261: the contest is one of the reply's two actions                // step 18n (D-191, D-193): jump shots are contested by position only
      deep: appRule(c.rules, 'deep_range') ? (c.deep_rows !== undefined && c.deep_rows !== null ? c.deep_rows : deepRowsFor(c.table)) : 0,   // D-274: the deep rows open to this offence
      fakes: appRule(c.rules, 'fakes') && appRule(c.rules, 'block') && appRule(c.rules, 'contest_costs') && appRule(c.rules, 'position_contest') && appRule(c.rules, 'soft_contest'),   // D-272
      pivot: appRule(c.rules, 'pivot') && appRule(c.rules, 'closely_guarded'),     // D-273: the pivot Quick Step after a pick-up
      block: appRule(c.rules, 'block') && appRule(c.rules, 'contest_costs') && appRule(c.rules, 'position_contest') && appRule(c.rules, 'soft_contest'),   // D-271: the block replaces the hard Contest
      offCut: appRule(c.rules, 'off_balance') ? controlSize(c.rules) : 0,                          // step 18l (D-185): off balance, the reduction on every rolled rating
      three: appRule(c.rules, 'three_seconds'), guarded: appRule(c.rules, 'closely_guarded'), fiba: appRule(c.rules, 'fiba_fouled_shot'),   // step 18i (D-172 to D-174)
      ppoRule: appRule(c.rules, 'points_play_on'), ppo: appRule(c.rules, 'points_play_on') && !c.hold_for_one, noRim: appRule(c.rules, 'no_rim_shot'),                   // D-198: fouls and turnovers in points, play on; no shot from the rim's own square
      tosOn: !(c.rules && c.rules.digital) || appRule(c.rules, 'points_play_on'),                    // a turnover's -5 stays in what is banked
      control: controlSize(c.rules), zone: !!(c.rules && c.rules.zone === 'on') };      // zone (step 18g, D-167): the zone of influence                    // D-151, D-153: the size, in rating steps (0: the rule is off)
  }
  // D-151, D-153 (rules.control): the reduction a rushed shot, or a rushed Contest of it, takes
  const controlOn = ctx => ctx.control > 0;
  const controlCut = (ctx, t) => ctx.control;            // one size, for every shot type and for the Contest alike
  // two bits a player in rush_o / rush_x: 1 his last movement this phase was a Quick Step, 2 a Sprint, 0 set
  // D-185 (rules.off_balance): a locked player is rushed too (he can't Move, so it lasts the phase)
  const rushedO = (s, i) => ((s.rush_o >> (2 * i)) & 3) !== 0 || (s.ctx.offCut > 0 && ((s.lock_o >> i) & 1) === 1);
  const rushedX = (s, j) => ((s.rush_x >> (2 * j)) & 3) !== 0 || (s.ctx.offCut > 0 && ((s.lock_x >> j) & 1) === 1);
  // D-185: the rating a player rolls with: his card's, less the off-balance reduction when he is rushed (not fouls)
  const rolled = (s, side, i, name) => {
    const v = (side === 'O' ? s.ctx.off : s.ctx.dfn)[i].r[name];
    return s.ctx.offCut > 0 && (side === 'O' ? rushedO(s, i) : rushedX(s, i)) ? v - s.ctx.offCut : v;
  };
 const shotRating = (s, shooter, t) => cardShot(s.ctx, s.ctx.off[shooter], t, s.o[shooter]) - (controlOn(s.ctx) && rushedO(s, shooter) ? controlCut(s.ctx, t) : 0);

  // ---- state --------------------------------------------------------------------------------------------------------
  // cnt indices: o_qs pass screen dribble hesitate shot x_qs intercept challenge steal pause
  const CI = { o_qs: 0, pass: 1, screen: 2, dribble: 3, hesitate: 4, shot: 5, x_qs: 6, intercept: 7, challenge: 8, steal: 9, pause: 10 };
  const cidx = (side, kind) => (kind === 'qs' ? (side === 'O' ? 0 : 6) : CI[kind]);
  const LIMITS = { O: { qs: 2, pass: 2, screen: 2, dribble: 2, hesitate: 1, shot: 1 }, X: { qs: 2, intercept: 2, challenge: 2, steal: 2, pause: 1, contest: 1 } };
  const TURN_ENDERS = new Set(['pass', 'screen', 'dribble', 'hesitate', 'shot', 'intercept', 'challenge', 'steal', 'pause', 'contest']);
  const MOVEMENT = new Set(['move', 'qs', 'sprint']);
  const TOKEN_FREE = new Set(['target', 'pick', 'end_turn', 'forfeit', 'contest', 'forced_shot', 'reset']);
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
      this.phase_x = s.phase_x || null;                 // D-198: the defence's squares and arrows when the phase began
      this.rush_o = s.rush_o || 0;                       // D-151: last movement this phase was a Quick Step or Sprint
      this.rush_x = s.rush_x || 0;
      this.key_o = s.key_o || 0;                         // D-172: attackers in the key at the last phase end
      this.grd = s.grd || 0;                             // D-173: the ball handler's count, packed as GameState.grd
      this.decl = s.decl || 0;                           // D-272: public: the declaration could have been a fake
      this.fake = s.fake || 0;                           // D-272: hidden from the defence: 1 shot fake, 2 pass fake
      this.reset = s.reset === undefined ? -1 : s.reset; // D-276: the blocker who resets after a block
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
      key_o: js.key_o || 0, grd: js.grd || 0, decl: js.decl || 0, fake: js.fake || 0, reset: js.reset === undefined ? -1 : js.reset,
      turn_x: js.turn_x && js.turn_x.length ? [js.turn_x[0].map(sq), js.turn_x[1].slice()] : null,
      phase_x: js.phase_x && js.phase_x.length ? [js.phase_x[0].map(sq), js.phase_x[1].slice()] : null };
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
      rush_o: s.rush_o, rush_x: s.rush_x, key_o: s.key_o, grd: s.grd, decl: s.decl, fake: s.fake, reset: s.reset, turn_x: s.turn_x ? [s.turn_x[0].map(sq), s.turn_x[1].slice()] : null,
      phase_x: s.phase_x ? [s.phase_x[0].map(sq), s.phase_x[1].slice()] : null };
  }

  // ---- actions --------------------------------------------------------------------------------------------------------
  const ORDER = ['target', 'pick', 'forced_shot', 'contest', 'end_turn', 'forfeit', 'shot', 'pass', 'dribble', 'screen', 'hesitate',
    'intercept', 'steal', 'challenge', 'pause', 'move', 'qs', 'sprint', 'reset'];
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
    if (k === 'sprint') return `${who} Sprint to ${sqName(a.dest)}` + (a.arrow >= 0 ? ` facing ${DIR_NAMES[a.arrow]}` : '');
    if (k === 'pass') return a.arrow === 1 ? `${who} Pass fake to O${a.target + 1}` : `${who} Pass to O${a.target + 1}`;
    if (k === 'screen') return `${who} Screen, T ${DIR_NAMES[a.target]}`;
    if (k === 'dribble') return `${who} Dribble vs X${a.target + 1}`;
    if (k === 'shot') return a.arrow === 1 ? `${who} Shot fake (${a.shot})` : `${who} Shot (${a.shot})`;
    if (k === 'intercept') return `${who} Intercept`;
    if (k === 'challenge') return `${who} Challenge screen of O${a.target + 1}`;
    if (k === 'steal') return `${who} Steal`;
    if (k === 'target') return `Coach's Call target O${a.target + 1}`;
    if (k === 'contest') return a.piece >= 0 ? (a.shot === 'hard' ? `${who} goes for the block` : `${who} contests`) : "X: don't contest";
    if (k === 'forced_shot') return `${who} forced shot (${a.shot})`;
    if (k === 'reset') return `${who} resets to ${sqName(a.dest)} facing ${DIR_NAMES[a.arrow]}`;
    if (k === 'pick') return `Failed inbound: ball to O${a.target + 1}`;
    if (k === 'end_turn') return `${who} End turn`;
    if (k === 'forfeit') return `${who} Forfeit tokens (no legal action)`;
    return `${who} ${k[0].toUpperCase()}${k.slice(1)}`;
  }
  const tSquare = (s, scr) => s.o[scr[0]] + DSTEP[scr[1]];

  // rules_config.pivot_open (D-273): picked up, and no pivot Quick Step since
  const pivotOpen = (s, i) => s.ctx.pivot && i === s.ball && (s.grd & 3) === 2 && ((s.grd >> 7) & 1) === 0;
  function canMoveKind(s, side, i, kind) {
    if (tokens(s, side) <= 0) return false;
    if (side === 'O' && i === s.ctx.inbounder && s.inbound) return false;
    if (side === 'O' && s.ctx.guarded && i === s.ball && (s.grd & 3) === 2 && !(kind === 'qs' && pivotOpen(s, i))) return false;     // D-173: picked up: pass or shoot only; D-273: but for his pivot
    if (kind === 'move' || kind === 'sprint') { if (hasMoved(s, side, i) || isLocked(s, side, i)) return false; }
    if (kind === 'qs' || kind === 'sprint') {
      if (count(s, side, 'qs') >= LIMITS[side].qs) return false;
      if (quickStepped(s, side, i)) return false;
    }
    return true;
  }
  // ---- step 18g (rules.zone, D-167): the zone of influence -----------------------------------------------------------
  // A defender's stance as the arrow rules read it (actions.stance, geometry.lines): without the rule, his arrow index
  // (one line); with it, 8 + the index (two lines, a and a + 1), or 16 when a Dribble won against him this phase has
  // broken his zone (no line at all).
  // Step 22b (D-217, Shaun, 18 Nov 2026): while defender j stands on a screen's T square (a screen he hasn't beaten
  // with a Challenge), the screen stops him stepping diagonally from it, and an arrow pointing that way projects
  // nothing: it walls no drive and jumps no passing lane. His contest is unchanged (actions.screen_blocked).
  function screenBlocked(s, j, p) {
    if (!s.screens.length) return false;
    const q = p === undefined ? s.x[j] : p;
    for (const sc of s.screens) if (!((sc[3] >> j) & 1) && tSquare(s, sc) === q) return true;
    return false;
  }
  function stanceOf(s, j, arrow) {
    const a = arrow === undefined ? s.arrows[j] : arrow;
    if (!s.ctx.zone) return a;
    for (const b of s.beaten) if (b[1] === j) return 16;
    return 8 + a;
  }
  const onLine = (st, d) => (st < 8 ? d === st : st < 16 ? (d === st - 8 || d === (st - 7) % 8) : false);
  const stanceMode = (s, j) => { if (!s.ctx.zone) return 0; for (const b of s.beaten) if (b[1] === j) return 2; return 1; };
  function inWedge(st, vx, vy) {                       // strictly between the two lines of a zone stance (geometry.in_wedge)
    const a = st - 8, b = (st - 7) % 8;
    const c0 = DX[a] * DY[b] - DY[a] * DX[b], c1 = DX[a] * vy - DY[a] * vx, c2 = vx * DY[b] - vy * DX[b];
    return (c1 > 0) === (c0 > 0) && (c2 > 0) === (c0 > 0) && c1 !== 0 && c2 !== 0;
  }
  function zoneOf(s, j, vacated, taken) {            // vacated, taken (step 13C): one attacker's square moved
    const st = stanceOf(s, j);
    if (st < 8) return zoneRay(s, j, st, vacated, taken);
    if (st >= 16) return [];
    const out = zoneRay(s, j, st - 8, vacated, taken);
    for (const q of zoneRay(s, j, (st - 7) % 8, vacated, taken)) out.push(q);
    // the zone is the wedge, not only its two edges: every square between the lines that a Move or a Quick Step still
    // left to him reaches (with the attacker's square moved, on that board)
    const t = vacated === undefined ? s : W_(s, { o: s.o.map(q => (q === vacated ? taken : q)) });
    const start = s.x[j], card = s.ctx.dfn[j];
    for (const kind of ['move', 'qs']) {
      if (!canMoveKind(t, 'X', j, kind) || (kind === 'qs' && !(card.qs > 0))) continue;
      for (const q of movementDests(t, 'X', j, kind).keys()) if (!out.includes(q) && inWedge(st, SX[q] - SX[start], SY[q] - SY[start])) out.push(q);
    }
    return out;
  }
  // Measuring only (step 18g): how much zone is on the court, and what the stance of each defender next to the ball
  // handler does: [squares in all five zones; defenders next to him whose arrow is on him (a Steal or a clean Contest)
  // and whose zone denies him a step closer to the rim; arrow on him only; step denied only; neither; of those that
  // deny a step, how many take the middle away (the denied squares lie nearer the centre line than he does) and how
  // many take the outside away].
  function stanceFacts(s, ex) {
    const bh = s.o[s.ball];
    let strength = 0, both = 0, cover = 0, block = 0, neither = 0, mid = 0, out = 0, beside = 0, bmid = 0, bout = 0;
    for (let j = 0; j < 5; j++) {
      const z = zoneOf(s, j);
      strength += z.length;
      if (!ONB[bh] || !adjacent(s.x[j], bh)) continue;
      const covers = onLine(stanceOf(s, j), dirBetween(s.x[j], bh));
      let nb = 0, off = 0;
      for (const q of z) if (adjacent(q, bh) && DR[q] < DR[bh]) { nb++; off += Math.abs(SX[q] - RIMX) - Math.abs(SX[bh] - RIMX); }
      if (covers && nb) both++; else if (covers) cover++; else if (nb) block++; else neither++;
      // his arrow on the ball handler and, at the same time, a square next to the ball handler barred by his zone
      // (any side); which side it bars: the middle (nearer the centre line than the ball handler) or the outside
      if (covers) {
        let k = 0, side = 0;
        for (const q of z) if (adjacent(q, bh)) { k++; side += Math.abs(SX[q] - RIMX) - Math.abs(SX[bh] - RIMX); }
        if (k) { beside++; if (side < 0) bmid++; else if (side > 0) bout++; }
        if (ex && k) ex.push([j, sqName(s.x[j]), s.arrows[j], sqName(bh), z.filter(q => adjacent(q, bh)).map(sqName), side < 0 ? 'mid' : side > 0 ? 'out' : 'level']);
      }
      if (nb) { if (off < 0) mid++; else if (off > 0) out++; }
    }
    return [strength, both, cover, block, neither, mid, out, beside, bmid, bout];
  }
  function zoneRay(s, j, d, vacated, taken) {
    // actions.zone: the squares along his arrow he reaches with one movement left to him (only membership is used).
    // Only the straight path reaches a square on the arrow ray, so the walk checks that path directly.
    const start = s.x[j], card = s.ctx.dfn[j], diag = d & 1, step = DSTEP[d];
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
  // rules.zone (D-170, Shaun, 13 Nov 2026): what can catch ball handler i. For each defender whose zone stands: his
  // square, his two arrow directions, and how far each arrow's line bars (the squares along it his movement left
  // still reaches, the ball handler's own square not stopping it; always the arrow's own square).
  function captureLines(s, i) {
    const out = [], bh = s.o[i];
    for (let j = 0; j < 5; j++) {
      const st = stanceOf(s, j);
      if (st < 8 || st >= 16) continue;
      if (s.beaten.some(b => b[0] === i && b[1] === j)) continue;
      if (screenBlocked(s, j)) continue;              // step 22b: one arrow blocked, nothing to catch him and bar the other
      const d0 = st - 8, d1 = (st - 7) % 8;
      out.push([s.x[j], d0, d1, Math.max(1, zoneRay(s, j, d0, bh, -1).length), Math.max(1, zoneRay(s, j, d1, bh, -1).length)]);
    }
    return out;
  }
  // does the step p -> q cross the barred line (from D along direction b, n squares) to the side away from arrow a?
  function crossesLine(D, b, a, n, p, q) {
    const bx = DX[b], by = DY[b], s0 = bx * DY[a] - by * DX[a];
    const sq = bx * (SY[q] - SY[D]) - by * (SX[q] - SX[D]);
    if (sq * s0 >= 0) return false;
    const sp = bx * (SY[p] - SY[D]) - by * (SX[p] - SX[D]);
    if (sp * s0 < 0) return false;
    const bb = bx * bx + by * by;
    if (sp === 0) { const dot = (SX[p] - SX[D]) * bx + (SY[p] - SY[D]) * by; return bb <= dot && dot <= n * bb; }
    const dot2 = (SX[p] + SX[q] - 2 * SX[D]) * bx + (SY[p] + SY[q] - 2 * SY[D]) * by;
    return 0 < dot2 && dot2 <= 2 * n * bb;
  }
  function captureOk(start, path, caps) {
    for (const c of caps) {
      const D = c[0], dir = [c[1], c[2]], ext = [c[3], c[4]], sq0 = D + DSTEP[c[1]], sq1 = D + DSTEP[c[2]];
      let c0 = start === sq0, c1 = start === sq1, p = start;
      for (const q of path) {
        if (c0 && crossesLine(D, dir[1], dir[0], ext[1], p, q)) return false;
        if (c1 && crossesLine(D, dir[0], dir[1], ext[0], p, q)) return false;
        if (q === sq0) c0 = true;
        if (q === sq1) c1 = true;
        p = q;
      }
    }
    return true;
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
      if (s.ctx.zone) return captureOk(start, path, zones == null ? captureLines(s, i) : zones);
      if (zones == null) zones = carrierZones(s, i);
      for (let n = 0; n < path.length - 1; n++) if (zones.has(path[n])) return false;
    }
    return true;
  }
  // actions.pivot_len (D-273): the pivot after a pick-up is a one-square Quick Step
  const pivotLen = (s, side, i, qs) => (side === 'O' && i === s.ball && s.ctx.guarded && (s.grd & 3) === 2 ? Math.min(qs, 1) : qs);
  function movementDests(s, side, i, kind) {
    const card = (side === 'O' ? s.ctx.off : s.ctx.dfn)[i];
    const start = side === 'O' ? s.o[i] : s.x[i];
    let paths;
    if (kind === 'move') paths = movePaths(start).map(p => [-1, p]);
    else if (kind === 'qs') paths = qsPaths(start, pivotLen(s, side, i, card.qs)).map(p => [-1, p]);
    else paths = sprintPaths(start, card.qs);
    const out = new Map();
    const zs = side === 'O' && i === s.ball ? (s.ctx.zone ? captureLines(s, i) : carrierZones(s, i)) : null;
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
          // the zone (as the old wedge): the run direction is one line; the other may fall either side of it
          if (side === 'X' && kind === 'sprint' && s.ctx.zone) for (const [dest, r] of dests) acts.push(A(kind, side, i, dest, (r + 7) % 8));
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
    if (!onLine(stanceOf(s, j), d)) return false;
    if ((d & 1) && screenBlocked(s, j)) return false;   // step 22b: a screen-blocked arrow jumps no lane
    if (laneMeet(p, d, s.o[s.pending[0]], s.o[s.pending[1]]) !== n) return false;
    if (a.kind === 'sprint') { const keep = (s.ctx.zone && a.arrow === (d + 7) % 8) ? a.arrow : d; if (keep !== s.arrows[j]) return false; }
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
      const z0 = szone(ctx, cpos);
      if (!inbounderHasIt && ONB[cpos] && z0 !== 0 && count(s, 'O', 'shot') < LIMITS.O.shot && !(ctx.hold_for_one && s.clock > 2)) {
        for (const t of ZONE_SHOTS[z0]) acts.push(A('shot', 'O', carrier, -1, -1, -1, t));
      }
      return acts;
    }
    if (count(s, 'O', 'pass') < LIMITS.O.pass) {
      for (let r = 0; r < 5; r++) if (r !== carrier && denier(s, carrier, r) < 0) acts.push(A('pass', 'O', carrier, -1, -1, r));
    }
    const passOnly = !!inbounderHasIt;
    const z = szone(ctx, cpos);                          // D-274: a deep square his team's level opens is a three
    if (!passOnly && ONB[cpos] && z !== 0 && count(s, 'O', 'shot') < LIMITS.O.shot && !(ctx.hold_for_one && s.clock > 2) && !(cpos === RIM && ctx.noRim)) {      // D-198: no shot from the rim's own square
      for (const t of ZONE_SHOTS[z]) acts.push(A('shot', 'O', carrier, -1, -1, -1, t));
    }
    if (!passOnly && count(s, 'O', 'dribble') < LIMITS.O.dribble && !isLocked(s, 'O', carrier) && !(s.ctx.guarded && (s.grd & 3) === 2)) {
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
    if (fakeOpen(s)) {                                  // actions.fake_open (D-272): each shot and pass, faked (arrow 1)
      const tw = acts.filter(a => (a.kind === 'shot' || a.kind === 'pass') && a.piece === carrier).map(a => A(a.kind, 'O', a.piece, a.dest, 1, a.target, a.shot));
      for (const a of tw) acts.push(a);
    }
    for (const a of movementActions(s, 'O')) acts.push(a);
    return acts;
  }
  // actions.fake_open (D-272): the phase's Hesitate or fake unused, in control, the ball in, the offence on the move
  const fakeOpen = s => s.ctx.fakes && s.stage === 'play' && s.side === 'O' && !s.pending && !s.inbound && s.tok_o > 0 &&
    count(s, 'O', 'hesitate') < LIMITS.O.hesitate && !rushedO(s, s.ball);
  function defenceActions(s, kinds) {
    const acts = [];
    if (s.tok_x <= 0) return acts;
    const cpos = s.o[s.ball];
    const ok = k => !kinds || kinds.has(k);
    if (ok('steal') && count(s, 'X', 'steal') < LIMITS.X.steal) {
      for (let j = 0; j < 5; j++) if (adjacent(s.x[j], cpos) && onLine(stanceOf(s, j), dirBetween(s.x[j], cpos))) acts.push(A('steal', 'X', j));
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
  // actions.reset_actions (D-276): the blocker's reset, any open square within 3 (his own included), any arrow
  function resetActions(s) {
    const j = s.reset, xp = s.x[j], out = [];
    for (let dx = -3; dx <= 3; dx++) for (let dy = -3; dy <= 3; dy++) {
      const x = SX[xp] + dx, y = SY[xp] + dy;
      if (x < 0 || x >= W || y < 1 || y > H) continue;
      const q = C(x, y);
      if (s.o.includes(q) || s.x.some((p, k) => k !== j && p === q)) continue;
      for (let a = 0; a < 8; a++) out.push(A('reset', 'X', j, q, a));
    }
    return out;
  }
  // board.push_dir, pushed (D-276): 3 squares straight away from the basket, stopped by a player or the court's edge
  function pushDir(c) {
    const vx = SX[c] - RIMX, vy = SY[c] - RIMY;
    if (vx === 0 && vy === 0) return -1;
    let best = -1, key = null;
    for (let i = 0; i < 8; i++) {
      const k = (DX[i] * vx + DY[i] * vy) / (DX[i] && DY[i] ? Math.SQRT2 : 1.0);
      if (key === null || k > key + 1e-12 || (Math.abs(k - key) <= 1e-12 && DX[i] && DY[i])) { best = i; key = k; }
    }
    return best;
  }
  function pushed(s, shooter) {
    const c = s.o[shooter], d = pushDir(c);
    if (d < 0) return c;
    let q = c;
    for (let n = 0; n < 3; n++) {
      const nxt = q + DSTEP[d];
      if (!ONB[nxt] || s.o.some((p, k) => k !== shooter && p === nxt) || s.x.includes(nxt)) break;
      q = nxt;
    }
    return q;
  }
  // resolve.block_reset (D-276): -5, a new phase, the shooter pushed and as if he had just caught it, the blocker to reset
  function blockReset(s, shooter, blocker) {
    s = W_(s, { pending: null, shot: null });
    if (!s.ctx.ppo) return pickoff(s);
    s = W_(s, { tos: s.tos + 1, approach: -1, stage: 'play' });
    const clock = s.clock - 2;
    if (clock <= 0) return terminal(W_(s, { clock: 0 }), Result('turnover_end'));
    s = newPhase(W_(s, { o: setAt(s.o, shooter, pushed(s, shooter)), key_o: 0, grd: 0 }), clock);
    return W_(s, { stage: 'reset', side: 'X', reset: blocker });
  }
  function legalActions(s) {
    if (s.stage === 'over') return [];
    if (s.stage === 'reset') return resetActions(s);
    if (s.stage === 'target') return [0, 1, 2, 3, 4].map(i => A('target', 'O', -1, -1, -1, i));
    if (s.stage === 'contest') return contestOptions(s, s.ball, s.shot, s.forced).map(o => A('contest', 'X', o.defender, -1, -1, -1, o.hard ? 'hard' : ''));
    if (s.stage === 'forced') return ZONE_SHOTS[szone(s.ctx, s.o[s.ball])].map(t => A('forced_shot', 'O', s.ball, -1, -1, -1, t));
    if (s.stage === 'pick') return inboundTieCandidates(s).map(i => A('pick', 'O', -1, -1, -1, i));
    const side = s.side;
    let acts = [];
    if (s.stage === 'reaction') {
      acts = defenceActions(s, REACTION);
      if (s.tok_x > 0) {                                  // D-18: a Contest by a defender next to the shooter, the last action
        for (const o of contestOptions(s, s.ball, s.shot, false)) if (o.defender >= 0) acts.push(A('contest', 'X', o.defender, -1, -1, -1, o.hard ? 'hard' : ''));
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
      if (s.tok_x > 0) for (const o of contestOptions(s, s.ball, s.shot, false)) if (o.defender >= 0) acts.push(A('contest', 'X', o.defender, -1, -1, -1, o.hard ? 'hard' : ''));
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
  const shotPoints = (pos, ctx) => ZONE_POINTS[ctx ? szone(ctx, pos) : ZN[pos]];
  const freeThrows = (card, points) => (points === 3 ? 3 : 2) * card.r.free_throw;
  // scoring.foul_on_shot_points: [points, and_one]; rating: reduced (D-151). Under rules.fiba_fouled_shot (fiba, D-174)
  // the shot's value as contested (shotValue; left: the rating the Contest leaves it) plus the free throws the rules
  // give, each at his free-throw rating: 1 if it went in, its points if it missed.
  function footPoints(card, t, pts, rating, fiba, shotValue, left) {
    if (fiba && t) {
      const r = rating === undefined ? card.sh[t] : rating;
      if (left === undefined) left = r;
      if (shotValue === undefined) shotValue = Math.max(0, pts * left);
      // the chance it goes in is left in 20; the whole is kept a whole number, as every score is (half a point rounds up)
      left = Math.max(0, Math.min(20, left));
      return [Math.floor((20 * shotValue + card.r.free_throw * (left + (20 - left) * pts) + 10) / 20), false];
    }
    const ft = freeThrows(card, pts);
    if (t) { const open = pts * (rating === undefined ? card.sh[t] : rating); if (open > ft) return [open, true]; }
    return [ft, false];
  }
  // scoring.soft_contest (D-177): the defence's best soft contest: [defender, contest] or [-1, 0]. Every defender next
  // to the shooter gives one with no action: his contest rating less 3, 3 less again from behind, 2 less if rushed.
  // D-191 (rules.position_contest, scoring.auto_contest): a jump shot is contested by position only. D-194: one
  // table for every shot: square (in front, his arrow on the shooter) the full rating; in front with the arrow off,
  // or beside, 3 less; behind 6 less; rushed 2 more off. D-193: a contesting defender always takes at least 1 off.
  const JUMP = { mid: true, long: true, three: true };
  function softContest(s, shooter, t) {
    const ctx = s.ctx, spos = s.o[shooter], cut = controlOn(ctx) ? controlCut(ctx, t) : 0, pos = ctx.pos;
    let bj = -1, bc = 0;
    for (let j = 0; j < 5; j++) {
      const xp = s.x[j];
      if (!adjacent(xp, spos)) continue;
      let c = ctx.dfn[j].cn[t];
      if (!(pos && DR[xp] < DR[spos] && onLine(stanceOf(s, j), dirBetween(xp, spos)))) c -= 3;      // D-194: square or 3 less, every shot
      if (DR[xp] > DR[spos]) c -= 3;
      if (cut && rushedX(s, j)) c -= cut;
      if (pos && c < 1) c = 1;
      if (c > bc) { bc = c; bj = j; }
    }
    return [bj, bc];
  }
  function softOption(s, shooter, t) {
    const opts = contestOptions(s, shooter, t, false), [j, c] = softContest(s, shooter, t);
    if (c <= 0) return opts[0];
    return { defender: j, contest: c, clean: true, k: 0, rolls: 0, value: Math.max(0, shotPoints(s.o[shooter], s.ctx) * (shotRating(s, shooter, t) - c)), ft: opts[0].ft, soft: true };
  }
  // scoring._contest_actions (D-261): one normal Contest per defender next to the shooter (the position table, never a
  // foul) and, on an inside shot from one who isn't square, the hard Contest (the block, with its foul rolls)
  function contestActions(s, shooter, t, val, ft, rating, pts, card) {
    const ctx = s.ctx, spos = s.o[shooter], cut = controlOn(ctx) ? controlCut(ctx, t) : 0, jump = JUMP[t] === true, out = [];
    for (let j = 0; j < 5; j++) {
      const xp = s.x[j];
      if (!adjacent(xp, spos)) continue;
      const square = DR[xp] < DR[spos] && onLine(stanceOf(s, j), dirBetween(xp, spos)), rushed = cut && rushedX(s, j);
      let c = ctx.dfn[j].cn[t] - (square ? 0 : 3) - (DR[xp] > DR[spos] ? 3 : 0);
      if (rushed) c -= cut;
      if (c < 1) c = 1;
      out.push({ defender: j, contest: c, clean: true, k: 0, rolls: 0, value: val(c), ft, hard: false });
      if (ctx.block) { out.push(blockOption(s, j, shooter, t, val, ft, rating, pts, card, rushed, square, cut)); continue; }
      if (jump || square) continue;
      let h = ctx.dfn[j].cn[t] - (DR[xp] > DR[spos] ? 3 : 0);
      h = Math.max(0, h);
      if (rushed) h = Math.max(0, h - cut);
      if (h < 1) h = 1;
      out.push({ defender: j, contest: h, clean: false, k: clampT(ctx.dfn[j].r.foul_contest), rolls: foulRolls(xp, spos), value: val(h),
        ft: ctx.fiba ? footPoints(card, t, pts, rating, true, val(h), rating - h)[0] : ft, hard: true });
    }
    return out;
  }
  // decide.Read._block_value (D-271), as the map reads it: fouls first on Foul (Block), then the Block at -5, else the shot
  function blockValue(ctx, card, dc, ty, k, pts, r, dcut, shooterCut) {
    const pen = KPEN[k], foul = KFOUL[k] || pen, two = KTWO[k] || pen;
    let con = dc.cn[ty] - (pen ? 3 : 0) - dcut; if (con < 1) con = 1;
    let b = dc.r.block - (pen ? 6 : foul ? 3 : 0) - dcut; if (b < 1) b = 1;
    const vs = Math.max(0, pts * (r - con)), pb = pS(b);
    let v = pb * -5 + (1 - pb) * vs;
    if (foul) {
      const ft = ctx.fiba ? footPoints(card, ty, pts, r, true, vs, r - con)[0] : footPoints(card, ty, pts, shooterCut ? r : undefined)[0];
      const pf = pFouls(dc.r.foul_block, two ? 2 : 1);
      v = pf * (ft + (ctx.ppo ? 5 : 0)) + (1 - pf) * v;
    }
    return v;                                          // decide._block_value: no floor (Shaun, 20 Nov): a likely block is worth less than nothing
  }
  // Step 31 (D-284, carry-over 1): the block read past the -5, the same way everywhere. A block is -5 and the phase;
  // the possession goes on, worth what the next phase is worth (B). So the block's value is a line in B:
  // [c0, c1] with value c0 + c1 * B (c0 is blockValue's own number, c1 the chance the block lands and no foul came first).
  function blockLine(ctx, card, dc, ty, k, pts, r, dcut, shooterCut) {
    const pen = KPEN[k], foul = KFOUL[k] || pen, two = KTWO[k] || pen;
    let b = dc.r.block - (pen ? 6 : foul ? 3 : 0) - dcut; if (b < 1) b = 1;
    const pb = pS(b), pf = foul ? pFouls(dc.r.foul_block, two ? 2 : 1) : 0;
    return [blockValue(ctx, card, dc, ty, k, pts, r, dcut, shooterCut), (1 - pf) * pb];
  }
  // scoring.block_option (D-271): fouls first on his Foul (Block) (square none, in front arrow off one, beside two, behind
  // two); then his Block, less 3 (beside or arrow off) or 6 (behind), less the rushed cut, at least 1: a turnover; a miss
  // leaves the shot against his full contest (3 less from behind, the rushed cut, at least 1)
  function blockOption(s, j, shooter, t, val, ft, rating, pts, card, rushed, square, cut) {
    const ctx = s.ctx, xp = s.x[j], spos = s.o[shooter], behind = DR[xp] > DR[spos], dc = ctx.dfn[j];
    const rolls = square ? 0 : behind ? 2 : foulRolls(xp, spos), step = square ? 0 : behind ? 6 : 3;
    let b = dc.r.block - step - (rushed ? cut : 0); if (b < 1) b = 1;
    let h = dc.cn[t] - (behind ? 3 : 0) - (rushed ? cut : 0); if (h < 1) h = 1;
    return { defender: j, contest: h, clean: rolls === 0, k: rolls ? clampT(dc.r.foul_block) : 0, rolls, value: val(h),
      ft: ctx.fiba ? footPoints(card, t, pts, rating, true, val(h), rating - h)[0] : ft, hard: true, block: b, cat: square ? 'square' : behind ? 'behind' : 'side' };
  }
  function contestOptions(s, shooter, t, forced) {
    const ctx = s.ctx, spos = s.o[shooter], card = ctx.off[shooter], pts = shotPoints(spos, ctx), rating = shotRating(s, shooter, t);
    const ft = footPoints(card, t, pts, rating, ctx.fiba)[0];
    const cut = controlOn(ctx) ? controlCut(ctx, t) : 0;
    const val = c => Math.max(0, pts * (rating - c));
    const opts = [{ defender: -1, contest: 0, clean: true, k: 0, rolls: 0, value: val(0), ft }];
    if (ctx.cc && !forced) return opts.concat(contestActions(s, shooter, t, val, ft, rating, pts, card));     // D-261
    const pos = ctx.pos && !forced;
    if (pos && JUMP[t] === true) return opts;             // D-191: a jump shot is contested by position only: no Contest action
    for (let j = 0; j < 5; j++) {
      const xp = s.x[j];
      if (!adjacent(xp, spos)) continue;
      let c = ctx.dfn[j].cn[t];
      if (DR[xp] > DR[spos]) c -= 3;
      c = Math.max(0, c);
      let clean = onLine(stanceOf(s, j), dirBetween(xp, spos));
      if (pos && clean && DR[xp] < DR[spos]) continue;      // D-191: from in front with the arrow on him the full contest is automatic (softContest)
      if (ctx.soft && !forced && DR[xp] >= DR[spos]) clean = false;      // D-177: a hard contest from the side or behind rolls for a foul
      if (cut && rushedX(s, j)) c = Math.max(0, c - cut);       // D-151, D-154: a rushed Contest, no extra foul roll
      if (pos && c < 1) c = 1;                                  // D-193: a contesting defender always takes at least 1 off
      const rolls = foulRolls(xp, spos);
      opts.push({ defender: j, contest: c, clean, k: clean ? 0 : clampT(ctx.dfn[j].r.foul_contest), rolls: clean ? 0 : rolls, value: val(c),
        ft: ctx.fiba ? footPoints(card, t, pts, rating, true, val(c), rating - c)[0] : ft });
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
  const Result = (kind, shooter = -1, shot_type = '', points = 0, rating = 0, contest = 0, contester = -1, shot_value = 0, free_throws = 0, and_one = false, floor = 0, violation = '', violator = -1, soft = false) =>
    ({ kind, shooter, shot_type, points, rating, contest, contester, shot_value, free_throws, and_one, floor, violation, violator, soft });

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
  // D-198 (resolve.play_on): after a turnover the phase ends there and the next begins, the ball where it was; with no
  // phase left the possession is over on what it has banked
  function playOn(s) {
    s = W_(s, { pending: null, approach: -1, shot: null, stage: 'play' });
    if (s.inbound) return endPhase(s);
    const clock = s.clock - 2;
    if (clock <= 0) return terminal(W_(s, { clock: 0 }), Result('turnover_end'));
    return newPhase(W_(s, { key_o: 0, grd: 0 }), clock);
  }
  function pickoff(s) {
    s = W_(s, { tos: s.tos + 1 });
    if (s.ctx.ppo) return playOn(s);
    if (s.ctx.hold_for_one || s.ctx.digital) return terminal(s, Result('turnover_end'), true);
    if (s.clock <= 2) return terminal(s, Result('turnover_end'), true);
    return W_(s, { clock: s.clock - 2 });
  }
  // resolve.unmask, reveal, fake_block (D-272)
  function unmask(s) {
    const cnt = Array.from(s.cnt), kind = s.fake === 1 ? 5 : 1;
    cnt[kind] = Math.max(0, cnt[kind] - 1); cnt[4] += 1;            // the shot or pass never happened; the Hesitate or fake is used
    let g = s.grd;
    if (s.ctx.guarded && (g & 3) === 1) g = (g & ~3) | 2;            // a fake after movement picks the ball up
    return W_(s, { cnt, grd: g, fake: 0, decl: 0, stage: 'play', shot: null, pending: null, approach: -1, react_moved: 0, final: s.final || s.tok_o <= 0 });
  }
  function reveal(s) {
    s = W_(unmask(s), { prev_wait: '', approach: -1 });
    if (s.final || s.tok_o <= 0) return endPhase(s);
    return W_(s, { side: 'O', turn_n: 0, turn_lead: -1, turn_x: null });
  }
  function fakeBlock(s, j, opt) {
    const locked = lock(s, 'X', j);
    if (!opt.rolls) return reveal(locked);
    const k = clampT(s.ctx.dfn[j].r.foul_block), one = k / 20, no = (20 - k) / 20;
    const fouled = W_(locked, { fouls: locked.fouls + 1, bonus5: locked.bonus5 + (s.ctx.ppo ? 1 : 0) });
    if (opt.rolls === 2) {
      const second = chance([[one, 'foul', reveal(fouled)], [no, 'no foul', reveal(locked)]]);
      return chance([[one, 'foul', reveal(fouled)], [no, 'no foul', second]]);
    }
    return chance([[one, 'foul', reveal(fouled)], [no, 'no foul', reveal(locked)]]);
  }
  function newPhase(s, clock) {
    if (s.ctx.ppoRule) s = W_(s, { phase_x: [s.x, s.arrows] });      // D-198: where an interceptor goes back to
    return W_(s, { screens: [], clock, turn_lead: -1, turn_x: null, tok_o: 6, tok_x: 6, moved_o: 0, moved_x: 0, cnt: ZERO, turn_n: 0,
      final: false, lock_o: 0, lock_x: 0, approach: -1, prev_wait: '', beaten: [], side: 'O', phase: s.phase + 1, pending: null,
      turn_moved: 0, qs_o: 0, qs_x: 0, react_moved: 0, rush_o: 0, rush_x: 0 });
  }
  function completePass(s) {
    const passer = s.pending[0], recv = s.pending[1];
    s = W_(s, { ball: recv, pending: null, approach: -1, grd: 0 });      // D-173: a catch starts the new holder's count
    if (s.inbound && passer === s.ctx.inbounder) s = newPhase(W_(s, { inbound: 0 }), s.ctx.card_clock);
    return s;
  }
  function resolveShot(s, forced = false) {
    if (s.fake === 1 && !forced) return reveal(s);       // D-272: the reply is done: it was a fake
    const spos = s.o[s.ball];
    if (forced) {
      if (!ONB[spos] || szone(s.ctx, spos) === 0) return terminal(s, Result('forced', s.ball, '', 0));
      const types = ZONE_SHOTS[szone(s.ctx, spos)];
      if (types.length > 1) return W_(s, { stage: 'forced', side: 'O', shot: null, forced: true, turn_n: 0, pending: null });
      s = W_(s, { shot: types[0], forced: true });
    }
    if (!forced) return contestOutcome(W_(s, { forced: false, pending: null }), s.ctx.soft && !s.ctx.cc ? softOption(s, s.ball, s.shot) : contestOptions(s, s.ball, s.shot, false)[0], false);   // D-261: no Contest, no contest   // D-18; D-177: no Contest action, the best soft contest counts
    return W_(s, { stage: 'contest', side: 'X', turn_n: 0, forced, pending: null });
  }
  function contestOutcome(s, opt, forced) {
    const shooter = s.ball, spos = s.o[shooter], card = s.ctx.off[shooter], t = s.shot, pts = shotPoints(spos, s.ctx);
    const rating = shotRating(s, shooter, t);            // D-151: reduced when the shooter is rushed
    let made = terminal(s, Result(forced ? 'forced' : 'shot', shooter, t, pts, rating, opt.contest, opt.defender, opt.value, 0, false, 0, '', -1, !!opt.soft));
    if (opt.defender >= 0 && !opt.soft && !forced && s.ctx.soft && !s.ctx.cc) {      // (D-261: only the Contest taken counts)
      // D-177: only one contest counts, the defence's best: a teammate's soft contest may beat this hard one
      const [j2, c2] = softContest(s, shooter, t);
      if (c2 > opt.contest) made = terminal(s, Result('shot', shooter, t, pts, rating, c2, j2, Math.max(0, pts * (rating - c2)), 0, false, 0, '', -1, true));
    }
    if (opt.block) {
      // resolve.contest_outcome (D-271): with no foul the Block roll: a block is a turnover (resolve._turnover); a miss, the shot
      const b = blockReset(s, shooter, opt.defender);
      made = chance([[pS(opt.block), 'blocked', b], [pNot(opt.block), 'not blocked', made]]);
    }
    if (opt.clean || opt.k === 0) return made;
    const and1 = footPoints(card, t, pts, rating, s.ctx.fiba, opt.value, rating - opt.contest)[1];
    const fouled = terminal(W_(s, { fouls: s.fouls + 1, bonus5: s.bonus5 + (s.ctx.ppo ? 1 : 0) }),      // D-198: a shooting foul is +5 and its free throws
      Result('free_throws', shooter, t, pts, rating, opt.contest, opt.defender, 0, opt.ft, and1));
    const one = opt.k / 20, no = (20 - opt.k) / 20;
    if (opt.rolls === 2) {
      const second = chance([[one, 'foul', fouled], [no, 'no foul', made]]);
      return chance([[one, 'foul', fouled], [no, 'no foul', second]]);
    }
    return chance([[one, 'foul', fouled], [no, 'no foul', made]]);
  }
  // D-173 (FIBA Article 27): a defender next to the ball handler with an arrow on him
  function closelyGuarded(s) {
    const bh = s.o[s.ball];
    for (let j = 0; j < 5; j++) if (adjacent(s.x[j], bh) && onLine(stanceOf(s, j), dirBetween(s.x[j], bh))) return true;
    return false;
  }
  const violation = (s, what, i) => terminal(W_(s, { tos: s.tos + 1 }), Result('turnover_end', -1, '', 0, 0, 0, -1, 0, 0, false, 0, what, i), s.ctx.hold_for_one || s.ctx.digital);
  // resolve.phase_counts (step 18i, D-171 to D-173): the counts taken at a phase end
  function phaseCounts(s) {
    const ctx = s.ctx;
    if (ctx.three) {
      let k = 0;
      for (let i = 0; i < 5; i++) {
        if (!INKEY[s.o[i]]) continue;
        if ((s.key_o >> i) & 1) {
          if (!ctx.ppo) return violation(s, 'three_seconds', i);
          s = W_(s, { tos: s.tos + 1 });                 // D-198: -5 and play goes on; D-254 (app only): the count doesn't start again
        }
        k |= 1 << i;
      }
      if (k !== s.key_o) s = W_(s, { key_o: k });
    }
    if (ctx.guarded) {
      let ball = s.grd & 3, held = (s.grd >> 2) & 3, idle = (s.grd >> 4) & 3;
      const acted = (s.grd >> 6) & 1;
      if (ball === 1) {
        idle = acted ? 0 : idle + 1;
        held = 0;
        if (idle >= 2) { ball = 2; idle = 0; }
      } else if (closelyGuarded(s)) {
        held += 1;
        if (held >= 3) {
          if (!ctx.ppo) return violation(s, 'closely_guarded', s.ball);
          s = W_(s, { tos: s.tos + 1 }); held = 0;       // D-198: -5 and play goes on; the count starts again
        }
      } else held = 0;
      const g = ball | (held << 2) | (idle << 4) | (ball === 2 ? (s.grd & 128) : 0);     // D-273: one pivot a pick-up
      if (g !== s.grd) s = W_(s, { grd: g });
    }
    return s;
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
      return W_(s, { ball: tied[0], grd: 0 });
    }
    s = phaseCounts(s);                                  // step 18i: three seconds and closely guarded, counted at a phase end
    if (s.stage === 'over') return s;
    const clock = s.clock - 2;
    if (clock <= 0) {
      s = W_(s, { clock: 0, tos: s.tos + 1 });
      if (s.ctx.ppo) return terminal(s, Result('turnover_end', -1, '', 0, 0, 0, -1, 0, 0, false, 0, 'shot_clock', -1));      // D-198: -5, nothing left to play
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
    if (s.pending && s.fake === 2) s = unmask(s);        // D-272: it was a pass fake: the ball never left him
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
    if (k === 'pick') return W_(s, { ball: a.target, stage: 'play', grd: 0 });
    if (k === 'forced_shot') return W_(s, { shot: a.shot, stage: 'contest', side: 'X', forced: true });
    if (k === 'reset') {                                 // resolve.apply 'reset' (D-276): then the new phase begins
      s = W_(s, { x: setAt(s.x, a.piece, a.dest), arrows: setAt(s.arrows, a.piece, a.arrow), stage: 'play', side: 'O', reset: -1 });
      if (s.ctx.ppoRule) s = W_(s, { phase_x: [s.x, s.arrows] });
      return s;
    }
    if (k === 'contest') {
      const hard = a.shot === 'hard';                    // D-261: an inside shot's hard Contest (the block)
      const opt = contestOptions(s, s.ball, s.shot, s.forced).find(o => o.defender === a.piece && !!o.hard === hard);
      if (!opt) throw new Error(`X${a.piece + 1} cannot contest this shot`);
      if (s.stage === 'reaction') s = W_(spend(s, side), { turn_n: s.turn_n + 1 });   // D-18: the reaction's last action, a token
      if (s.fake === 1) return hard ? fakeBlock(s, a.piece, opt) : reveal(s);       // D-272: a fake: the block locks; the honest Contest does nothing
      return contestOutcome(s, opt, s.forced);
    }
    if (!TOKEN_FREE.has(k)) s = spend(s, side);
    if (k === 'forfeit') s = side === 'O' ? W_(s, { tok_o: 0 }) : W_(s, { tok_x: 0 });
    if (k === 'end_turn' || k === 'forfeit') return after(state, s, side, k);
    if (side === 'X' && s.pending && s.fake === 2) {
      // resolve.apply (D-272): a pass fake: an Intercept or a Steal locks him and the reply is over; a movement keeps it
      // in the air; any other action shows it first
      if (k === 'intercept' || k === 'steal') return reveal(lock(inc(s, 'X', k), 'X', a.piece));
      if (!(MOVEMENT.has(k) && mtiApproach(state, a))) s = W_(unmask(s), { side: 'X' });
    }
    if (side === 'X' && s.pending && !isInboundPass(state)) {
      const answering = k === 'intercept' || (MOVEMENT.has(k) && mtiApproach(state, a));
      if (!answering) { const ph = s.phase; s = completePass(s); if (s.phase !== ph) return s; }
    }
    if (MOVEMENT.has(k)) {
      if (side === 'O') {
        s = W_(s, { o: setAt(s.o, a.piece, a.dest) });
        if (s.ctx.guarded && a.piece === s.ball) s = W_(s, { grd: (state.grd & 3) === 2 ? (s.grd | 128) : 65 });     // D-173: a live dribble (ball 1, acted); D-273: his pivot keeps the ball picked up
        if (screenOf(s, a.piece)) s = W_(s, { screens: s.screens.filter(x => x[0] !== a.piece) });
        if (k === 'move' && state.turn_n === 0 && state.side === 'O' && state.stage === 'play') s = W_(s, { turn_lead: a.piece });
      } else {
        const arr = s.arrows.slice();
        if (k === 'move') arr[a.piece] = a.arrow;
        else if (k === 'sprint') {
          const st = state.x[a.piece], dx = SX[a.dest] - SX[st], dy = SY[a.dest] - SY[st], n = Math.max(Math.abs(dx), Math.abs(dy));
          const run = STEPDIR.get((dx / n) * WID + dy / n);
          arr[a.piece] = (s.ctx.zone && a.arrow === (run + 7) % 8) ? a.arrow : run;
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
    if (k === 'pass') return after(state, W_(s, { pending: [a.piece, a.target], approach: -1 },
      s.ctx.fakes ? { decl: fakeOpen(state) ? 1 : 0, fake: a.arrow === 1 ? 2 : 0 } : {}), side, k);
    if (k === 'screen') {
      const scr = s.screens.concat([[a.piece, a.target, true, 0]]);
      scr.sort((p, q) => p[0] - q[0] || p[1] - q[1] || (p[2] === q[2] ? 0 : p[2] ? 1 : -1) || p[3] - q[3]);
      return after(state, W_(s, { screens: scr }), side, k);
    }
    if (k === 'hesitate' || k === 'pause') return after(state, s, side, k);
    if (k === 'shot') {
      s = W_(s, { stage: 'reaction', shot: a.shot, side: 'X', turn_n: 0 });
      if (s.ctx.fakes) s = W_(s, { decl: fakeOpen(state) ? 1 : 0, fake: a.arrow === 1 ? 1 : 0 });      // D-272
      if (s.tok_x <= 0) return resolveShot(s);
      return s;
    }
    if (k === 'dribble') {
      if (s.ctx.guarded) s = W_(s, { grd: 65 });         // D-173: a Dribble keeps him active
      const t = rolled(s, 'O', s.ball, 'dribble') - rolled(s, 'X', a.target, 'agility');
      const nb = s.beaten.filter(b => !(b[0] === s.ball && b[1] === a.target)).concat([[s.ball, a.target]]);
      nb.sort((p, q) => p[0] - q[0] || p[1] - q[1]);
      const win = W_(lock(s, 'X', a.target), { beaten: nb });
      const lose = lock(s, 'O', s.ball);
      return chance([[pS(t), 'success', after(state, win, side, k)], [pNot(t), 'failure', after(state, lose, side, k)]]);
    }
    if (k === 'intercept') {
      const passer = s.pending[0], j = a.piece;
      const t = rolled(s, 'O', passer, 'pass') - rolled(s, 'X', j, 'intercept');
      const ok = completePass(W_(s, { moved_x: s.moved_x | (1 << j) }));
      const okNode = ok.phase !== s.phase ? ok : after(state, ok, side, k);
      let back = s;
      const from = s.ctx.ppo ? (state.phase_x || state.turn_x) : state.turn_x;      // D-198: where he began the phase
      if (from) {
        const sx = from[0], sa = from[1];
        back = W_(s, { x: setAt(s.x, j, sx[j]), arrows: setAt(s.arrows, j, sa[j]) });
      }
      const lost = pickoff(W_(back, { pending: null, approach: -1, moved_x: back.moved_x | (1 << j) }));
      const lostNode = lost.stage === 'over' ? lost : after(state, lost, side, k);
      return chance([[pS(t), 'success', okNode], [pNot(t), 'failure', lostNode]]);
    }
    if (k === 'challenge') {
      const t = rolled(s, 'O', a.target, 'screen') - rolled(s, 'X', a.piece, 'challenge');
      const holds = lock(s, 'X', a.piece);
      const fails = W_(s, { screens: s.screens.filter(x => x[0] !== a.target) });
      return chance([[pS(t), 'success', after(state, holds, side, k)], [pNot(t), 'failure', after(state, fails, side, k)]]);
    }
    if (k === 'steal' && s.stage === 'reaction' && s.fake === 1) { s = unmask(s); state = W_(state, { stage: 'play' }); }   // D-272: no shot went up: a Steal on a ball handler
    if (k === 'steal') {
      const carrier = s.ball, fk = X[a.piece].r.foul_steal, tk = rolled(s, 'O', carrier, 'dribble') - rolled(s, 'X', a.piece, 'steal');
      // D-89: every steal foul is +5; on a shooter it is a shooting foul, free throws only (step 7)
      const fibaSf = s.ctx.fibaSteal;                    // D-179: no +5 outside the penalty
      const d198 = s.ctx.ppo;                            // D-198: every foul is +5, a foul on a shooter included; no penalty
      let fs = W_(s, { fouls: s.fouls + 1, bonus5: s.bonus5 + (d198 ? 1 : (s.stage === 'reaction' || fibaSf) ? 0 : 1) });
      let foulNode, stolenNode;
      if (s.stage === 'reaction') {
        const pts = shotPoints(s.o[carrier], s.ctx), card = O[carrier];
        const rating = shotRating(s, carrier, s.shot);   // D-151
        const [fpts, and1] = footPoints(card, s.shot, pts, rating, s.ctx.fiba);
        foulNode = terminal(fs, Result('free_throws', carrier, s.shot, pts, rating, 0, a.piece, 0, fpts, and1));
        if (s.ctx.digital && !d198) {
          stolenNode = terminal(W_(s, { tos: s.tos + 1 }), Result('steal', carrier, s.shot, pts), true);
        } else {
          const cnt = s.cnt.slice(); cnt[5] = Math.max(0, cnt[5] - 1);
          const st = pickoff(W_(s, { stage: 'play', shot: null, cnt }));
          stolenNode = st.stage === 'over' ? st : after(W_(state, { stage: 'play' }), st, side, k);
        }
      } else {
        const inBonus = s.ctx.digital ? (s.ctx.team_fouls + fs.fouls >= s.ctx.bonus_from) : fs.fouls >= 2;
        if (d198) foulNode = after(state, lock(fs, 'X', a.piece), side, k);      // +5 (banked above), the defender locked, play on
        else if (inBonus) {
          foulNode = terminal(fs, Result('free_throws', carrier, '', 2, 0, 0, a.piece, 0, freeThrows(O[carrier], 2)));
        } else foulNode = after(state, fibaSf ? lock(fs, 'X', a.piece) : fs, side, k);      // D-179: a team foul, the defender locked, play on
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
  const _GR = new Memo2(1200);                         // (was unbounded: a reach for every square, arrow and state of his legs a search ever met)
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
    if (side === 'O' && i === s.ball && s.ctx.guarded && (s.grd & 3) === 2) return [false, pivotOpen(s, i) ? Math.min(qsLeft, 1) : 0];   // D-173, D-273
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
  const SPEED = { reach_cache: true, forcing: true, quiet_read: true, tt_order: true, two_direct: true, two_bound: true, path_block: true, open_facts: true, lane_p: true, look_lazy: true };
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
      if (REACH.size >= REACH_MAX) { REACH_OLD = REACH; REACH = new Map(); }
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
    const [free, fixed] = geoReach(s.o[i], 0, pivotLen(s, 'O', i, s.ctx.off[i].qs), canMove, qsLeft);
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
    if (s.tok_o >= 2 && pivotLen(s, 'O', i, 2) !== 1) {          // D-273: after his pivot he only passes or shoots
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
    // (under rules.zone the capture rule, D-170, reads the whole path: the plain way)
    const plain = !SPEED.two_direct || s.ctx.zone || s.screens.some(sc => sc[0] === i);
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
  let SOFTK = 0;                                         // D-177 (rules.soft_contest), set by each Read from its position's rules
  function kindOf(q, c, pen, foul) {
    if (!foul && (SOFTK & 1) && DR[q] >= DR[c]) foul = true;   // a hard contest from the side or behind rolls for a foul
    if (pen) return foul ? 4 : 3;
    if (!foul) return 0;
    return DR[q] >= DR[c] ? 2 : 1;
  }
  function contestMap(free, fixed, mode = 0) {          // Int8Array(board index * 6 + kind): fewest actions
    // mode (step 18g, rules.zone): 0 one arrow line; 1 the zone's two (a and a + 1); 2 a broken zone (no line)
    const out = new Int8Array(NB * 6).fill(INF);
    const put = (q, a, n, anyArrow) => {
      for (let d = 0; d < 8; d++) {
        const c = q + DSTEP[d];
        if (!ONB[c]) continue;
        const foul = mode === 2 ? true : anyArrow ? false : mode === 1 ? (d !== a && d !== (a + 1) % 8) : d !== a;
        const k = BI[c] * 6 + kindOf(q, c, DR[q] > DR[c], foul);
        if (out[k] > n) out[k] = n;
      }
    };
    for (const [q, n] of free) put(q, -1, n, true);
    for (const [q, arrs] of fixed) for (const [a, n] of arrs) put(q, a, n, false);
    // the kinds he reaches within 0, 1 or 2 reaction actions, per square (bit k = KINDS[k]). D-261: the reply turn's
    // reach before the contest (masks[2]) is one movement when the Contest is itself one of its two actions
    out.masks = [0, 1, (SOFTK & 2) ? 1 : 2].map(react => {
      const m = new Uint8Array(NB);
      for (let b = 0; b < NB; b++) { let v = 0; for (let k = 0; k < 6; k++) if (out[b * 6 + k] <= react) v |= 1 << k; m[b] = v; }
      return m;
    });
    return out;
  }
  const _CM = new Memo2(1200);
  function cmapCached(frm, arrow, qs, canMove, qsLeft, mode = 0) {
    const key = ((((((frm * 8 + arrow) * 8 + qs) * 2 + (canMove ? 1 : 0)) * 3) + qsLeft) * 3 + mode) * 4 + SOFTK;
    let hit = _CM.get(key); if (hit) return hit;
    const [free, fixed] = geoReach(frm, arrow, qs, canMove, qsLeft);
    hit = contestMap(free, fixed, mode); _CM.set(key, hit); return hit;
  }
  // ---- step 18q: the race to the rim (eval.lane; decide._any_arrow_cmap, ahead_row, _lane_paths) ---------------------
  // What the ball handler's way to the rim is worth one phase on. Both halves of the race come from the movement rules:
  // he gets what he has left this phase and one movement the next; each defender gets what he has left this phase
  // (within the defence's tokens) and then the reaction's two actions, fresh. No square or kind of move is named.
  const INF_V = Infinity;
  const _AAM = new Map();
  function anyArrowMask(q, qs, mode) {                 // a defender on q at a phase's start, whichever way he faces
    const key = ((q * 8 + qs) * 3 + mode) * 4 + SOFTK;
    let hit = _AAM.get(key); if (hit) return hit;
    hit = new Uint8Array(NB);
    for (let a = 0; a < 8; a++) { const m = cmapCached(q, a, qs, true, 1, mode).masks[2]; for (let b = 0; b < NB; b++) hit[b] |= m[b]; }
    _AAM.set(key, hit); return hit;
  }
  function aheadMask(c, frm, arrow, qs, canMove, qsLeft, budget, mode) {   // bit k: KINDS[k] within the reaction's two actions
    const b = BI[c];
    let m = cmapCached(frm, arrow, qs, true, 1, mode).masks[2][b];
    if (budget > 0) {
      const fr = geoReach(frm, arrow, qs, canMove, qsLeft);
      for (const [q, n] of fr[0]) if (n <= budget) m |= anyArrowMask(q, qs, mode)[b];
      for (const [q, arrs] of fr[1]) for (const [a, n] of arrs) if (n > 0 && n <= budget) m |= cmapCached(q, a, qs, true, 1, mode).masks[2][b];
    }
    return m;
  }
  const _LNP = new Map();
  function lanePaths(start, qs) {                      // every movement path from start that ends on a paint square
    const key = start * 8 + qs; let hit = _LNP.get(key); if (hit) return hit;
    hit = [];
    const ok = p => p.every(q => ONB[q]) && ZN[p[p.length - 1]] === PAINT;
    // [path, rushed]: rushed for a Quick Step or a Sprint (the shot after it is off balance), not for a Move
    for (const p of movePaths(start)) if (ok(p)) hit.push([p, false]);
    for (const p of qsPaths(start, qs)) if (ok(p)) hit.push([p, true]);
    for (const [, p] of sprintPaths(start, qs)) if (ok(p)) hit.push([p, true]);
    _LNP.set(key, hit); return hit;
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
  // step 18s, stop two (decide.pass_by_rules, decide.icpt_pi): the reading's pass chance is the rules' own. The best
  // chance defender j, on p with this arrow and with canMove / qsLeft left to him, takes a pass from pa to pc: through
  // his square (not next to the passer), or one straight Move, Quick Step or Sprint along one of his arrow lines to the
  // square where it meets the pass (not next to the passer, the way clear), then the Intercept, rolled as he then
  // stands. 0: by the rules he can't.
  const passRulesOn = () => D.config.eval.pass_rules !== false;
  // step 18s, stop two (eval.map): the search reads the coverage map at the end of every line (Read._mapLeaf)
  // true: both sides; 'offence': only where the decision being searched is the offence's (MAP_ME, set by search())
  let MAP_ME = null;
  const mapOn = () => D.config.eval.map === true || (D.config.eval.map === 'offence' && MAP_ME === 'O');
  // step 22b (D-219): what leads the map's reading at the end of a line: 'list' (the largest item on the list of things
  // to cover as the defence stands, before it answers) or 'gap' (step 20's lasting gap, after its answer)
  // step 31 (D-284): 'value': the possession's value (possValue) leads; the list and the lasting gap are displays
  const mapLead = () => D.config.eval.map_lead === 'list';
  const valueLead = () => D.config.eval.map_lead === 'value';
  function setMapLead(v) { D.config.eval.map_lead = v === 'value' ? 'value' : v === 'list' ? 'list' : 'gap'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.map_lead; }
  function setMap(v) { D.config.eval.map = v === 'offence' ? 'offence' : (v === true || v === 'true'); READS = new Map(); READS_OLD = new Map(); return D.config.eval.map; }
  function mapParts(s) { const r = readOf(s); return [r.mapShot()].concat(r.mapTwo(false)).concat(r.mapTwo(true)).concat([s.tok_o, s.tok_x]); }
  function setPassRules(v) { D.config.eval.pass_rules = !(v === false || v === 'false'); READS = new Map(); READS_OLD = new Map(); return D.config.eval.pass_rules; }
  // occ: a Set of the squares taken, or null with (oi, oc, oj, oq): receiver oi on oc, defender oj on oq (passTaken)
  function passTaken(s, z, oi, oc, oj, oq) {
    if (z === oc) return true;
    const x = s.x, o = s.o;
    for (let d = 0; d < 5; d++) if ((d === oj ? oq : x[d]) === z) return true;
    for (let k = 0; k < 5; k++) if (k !== oi && o[k] === z) return true;
    return false;
  }
  function icptPi(s, pa, pc, j, p, arrow, canMove, qsLeft, occ, passer, oi, oc, oj, oq) {
    if (s.tok_x <= 0 || count(s, 'X', 'intercept') >= LIMITS.X.intercept) return 0;
    const base = s.ctx.dfn[j].r.intercept, cut = s.ctx.offCut > 0 ? s.ctx.offCut : 0;
    let best = -Infinity;
    if (cheb(p, pa) !== 1 && onSegment(p, pa, pc, 0)) best = (cut && rushedX(s, j)) ? base - cut : base;
    if (s.tok_x >= 2 && (canMove || qsLeft > 0) && best < base) {
      const st = stanceOf(s, j, arrow), qs = s.ctx.dfn[j].qs;
      for (let k = 0; k < 2; k++) {
        let d;
        if (st < 8) { if (k) break; d = st; } else if (st < 16) d = k ? (st - 7) % 8 : st - 8; else break;
        const n = laneMeet(p, d, pa, pc);
        if (!n) continue;
        const q = p + DSTEP[d] * n;
        let ok = ONB[q] && cheb(q, pa) !== 1;
        for (let m = 1; ok && m <= n; m++) { const z = p + DSTEP[d] * m; if (!ONB[z] || (occ ? occ.has(z) : passTaken(s, z, oi, oc, oj, oq))) ok = false; }
        if (!ok) continue;
        for (const scr of s.screens) {
          if (scr[0] === oi && oc !== s.o[oi]) continue;        // the receiver has moved to catch it: his screen is gone
          const tsq = tSquare(s, scr);
          if ((scr[3] >> j) & 1) { if (q === tsq) { ok = false; break; } continue; }
          let prev = p;
          for (let m = 1; m <= n; m++) { const z = p + DSTEP[d] * m; if (diagStepBanned(prev, z, tsq)) { ok = false; break; } prev = z; }
          if (!ok) break;
        }
        if (!ok) continue;
        const orth = (d & 1) === 0;
        let roll;
        if (canMove && n <= (orth ? 3 : 2)) roll = base;                       // a Move: he is set when he gets there
        else if (qsLeft > 0 && qs > 0 && n <= qs) roll = base - cut;           // a Quick Step or a Sprint: off balance (D-185)
        else if (canMove && qsLeft > 0 && qs > 0 && n <= (orth ? 3 : 2) + qs) roll = base - cut;
        else continue;
        if (roll > best) best = roll;
      }
    }
    return best === -Infinity ? 0 : 1 - pS(passer - best);
  }
  function passOcc(s, i, c, j, q) {                    // the squares taken with receiver i on c (and defender j on q)
    const occ = new Set();
    for (let d = 0; d < 5; d++) occ.add(d === j ? q : s.x[d]);
    for (let k = 0; k < 5; k++) if (k !== i) occ.add(s.o[k]);
    occ.add(c);
    return occ;
  }
  function lanePRules(s, i, c, j, q, a, cm, ql) {      // the chance by the rules; j >= 0: defender j on q facing a with cm / ql left
    if (s.tok_x <= 0 || count(s, 'X', 'intercept') >= LIMITS.X.intercept) return 1;
    const pa = s.o[s.ball], passer = rolled(s, 'O', s.ball, 'pass');
    let worst = 0;
    for (let d = 0; d < 5; d++) {
      let pi;
      if (d === j) pi = icptPi(s, pa, c, d, q, a, cm, ql, null, passer, i, c, j, q);
      else { const cp = caps(s, 'X', d); pi = icptPi(s, pa, c, d, s.x[d], s.arrows[d], cp[0], cp[1], null, passer, i, c, j, q); }
      if (pi > worst) worst = pi;
    }
    return 1 - worst;
  }
  function laneP(s, i, c, reach) {
    const a = s.o[s.ball];
    if (!(ONB[a] && ONB[c])) return 0;
    const den = laneSquares(a, c);
    for (const xp of s.x) if (den.has(xp) && adjacent(xp, c)) return 0;
    if (passRulesOn()) return lanePRules(s, i, c, -1, -1, 0, false, 0);
    const lane = den;
    if (!lane.size) return 1;
    const passer = rolled(s, 'O', s.ball, 'pass');
    let worst = 0;
    const exact = reach === undefined ? reachOn() : reach;
    for (let d = 0; d < 5; d++) {
      const [canMove, qsLeft] = caps(s, 'X', d);
      const one = exact ? exactOne(s, d) : oneAction(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, canMove, qsLeft);
      let hit = false; for (const b of lane.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { hit = true; break; }
      if (!hit) continue;
      const pi = 1 - pS(passer - rolled(s, 'X', d, 'intercept'));
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
        const jump = passRulesOn();                      // step 18s, stop two: one movement and then the Intercept counts too
        for (const b of legalActions(nxt)) {
          if (b.kind === 'intercept') worst = Math.max(worst, 1 - pS(rolled(nxt, 'O', s.ball, 'pass') - rolled(nxt, 'X', b.piece, 'intercept')));
          else if (jump && MOVEMENT.has(b.kind) && mtiApproach(nxt, b)) {
            const af = apply(nxt, b);
            if (!isChance(af) && af.pending) worst = Math.max(worst, 1 - pS(rolled(af, 'O', s.ball, 'pass') - rolled(af, 'X', b.piece, 'intercept')));
          }
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
    const extra = ft2 + (ctx.fibaSteal ? 0 : 5) - ((ctx.fibaSteal ? 0 : 5) + cont);     // D-89: +5 on every steal foul; in the app (D-179, D-181) on none
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
    if (!ctx.digital || !s.fouls || !ctx.quarter_left || ctx.ppoRule) return 0.0;      // D-198: a foul is +5 and nothing else
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
  // decide.leaf_mode: eval.leaf_mode ('floor', 'relative'), or 'looks' (step 18f): the looks alone, without the phase
  // table's floor. 'looks' is in play only under the app's rules with the calibrated reading on and a map fitted to it
  // (calibration_looks); anywhere else it reads as 'floor'.
  let FORCE_LOOKS = false;                               // the fitting tool reads positions in the looks mode whatever the config says
  function leafMode(s) {
    if (FORCE_LOOKS) return 'looks';
    const m = D.config.eval.leaf_mode || 'floor';
    if (m !== 'looks') return m;
    if (!(s.ctx.digital && calibratedOn() && D.learned.calibration_looks)) return 'floor';
    // only where the looks map has a line for this phase and side to act (too few positions to fit one: the floor)
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    return D.learned.calibration_looks.maps[String(phase) + (s.side === 'O' && s.stage === 'play' ? 'O' : 'X')] ? 'looks' : 'floor';
  }
  function leafOf(s, banked, sn, now, cont, coarse, budget) {
    const mode = leafMode(s);
    if (mode === 'relative') return banked + Math.max(sn || 0.0, now, coarse + cont - relativeAverage(s, budget));
    if (mode === 'looks') return banked + Math.max(sn || 0.0, now, cont);     // step 18f: the floor hides what is below the average
    return banked + Math.max(sn || 0.0, now, cont, coarse);
  }
  function setLeafMode(mode) { D.config.eval.leaf_mode = mode; READS = new Map(); READS_OLD = new Map(); return mode; }
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
        const pts = ctx.worth[z];
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
  function calibrate(s, oToAct, r, own) {              // own (step 18h): a map given, in place of the one the position would take
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    // D-141: under the table's rules, the table's own map (fitted on tabletop-rules play) when the file has one
    // step 18f: the looks reading goes through its own map
    const cal = own || (leafMode(s) === 'looks' && D.learned.calibration_looks) || (!s.ctx.digital && TABLETOP_MAP && D.learned.calibration_tabletop) ||
      (s.ctx.digital && D.level && D.config.eval.lane === true && D.learned.calibration_lane && D.learned.calibration_lane[D.level]) ||      // step 18q: the map fitted with the lane reading on
      (s.ctx.digital && D.level && D.config.eval.level_maps !== false && D.learned.calibration_levels && D.learned.calibration_levels[D.level]) || D.learned.calibration;      // D-163: the level's own map
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
  // ---- step 18h (eval.no_floor; decide.parts_map, decide.parts_value) --------------------------------------------------
  // Today's reading takes the largest of the shot that can go up now and "play on", and of the looks the cover leaves
  // only the best counts; what is not the largest is thrown away. With the switch on the parts are kept: what is left
  // to earn is a line fitted to what positions went on to earn (the weights file's calibration_parts block), per level,
  // phase and side to act: a + b1 x the best shot now + b2 x the best look the cover leaves + b3 x the second best.
  // step 18h (eval.exact_shot, off; decide.play_on_map): a shot that can go up now keeps its exact value; only "play on"
  // goes through a map of its own (calibration_play_on, per level), and the reading is the larger of the two
  function setLevelMaps(v) { D.config.eval.level_maps = !(v === false || v === 'false'); READS = new Map(); READS_OLD = new Map(); return D.config.eval.level_maps; }
  // step 18q (eval.lane, off until its checks pass): the reading counts the ball handler's way to the rim next phase
  const laneOn = () => D.config.eval.lane === true;
  function setLane(v) { D.config.eval.lane = v === true || v === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.lane; }
  function setExactShot(v) { D.config.eval.exact_shot = v === true || v === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.exact_shot; }
  function playOnMap(s) {
    if (D.config.eval.exact_shot !== true || !s.ctx.digital || !D.learned.calibration_play_on || leafMode(s) !== 'relative') return null;
    const lv = D.learned.calibration_play_on.levels;
    return (D.level && lv[D.level]) || lv.all || null;
  }
  const noFloorOn = () => D.config.eval.no_floor === true;
  function setNoFloor(v) { D.config.eval.no_floor = v === true || v === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.no_floor; }
  function setLevel(lv) { const v = lv || null; if (D.level !== v) { D.level = v; READS = new Map(); READS_OLD = new Map(); } return D.level; }
  function partsMap(s) {
    if (!noFloorOn() || !s.ctx.digital || !D.learned.calibration_parts) return null;
    return D.learned.calibration_parts.levels;
  }
  function partsValue(levels, s, oToAct, shot, look, second) {      // null where no line was fitted: the map then
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    const key = String(phase) + (oToAct ? 'O' : 'X');
    const own = D.level ? levels[D.level] : null;
    const row = (own && own.maps[key]) || (levels.all && levels.all.maps[key]) || null;
    if (!row) return null;
    const w = row.w, q = calibrationScale(s, phase);
    if (q === 1.0) return w[0] + (w[1] * shot + w[2] * look + w[3] * second);
    return q * (w[0] + (w[1] * shot + w[2] * look + w[3] * second) / q);
  }
  function topTwo(att, of) {                              // the best and the second best of an attacker's value
    let a = 0.0, b = 0.0, n = 0;
    for (const i of att) { const t = of(i); if (n === 0) a = t; else if (t > a) { b = a; a = t; } else if (n === 1 || t > b) b = t; n++; }
    return [n ? a : 0.0, n > 1 ? b : 0.0];
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
    if (s.ctx.ppo) {                                     // D-198: -5, then the next phase with the ball where it was
      const banked = 5 * s.bonus5 - 5 * (s.tos + 1);
      return s.clock <= 2 ? banked : banked + vcoarse(W_(s, { clock: s.clock - 2 }));
    }
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
      SOFTK = (s.ctx.soft ? 1 : 0) | (s.ctx.cc ? 2 : 0);      // bit 1: D-261, the reply's reach before the contest is one movement
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
      this._ahead = undefined;                       // step 18q: laneAhead(), once
      this._lane18q = undefined;                     // step 18q: _laneData(), once
      this._drib = undefined;                        // step 18q: _dribbleOk(), once
    }
    _contest(d, at = -1, arrow = -1, used = null) {
      const s = this.s;
      if (!ONB[s.x[d]]) return null;
      if (at < 0 && (this.exact || reachOn())) {
        const r = defenderMap(s, d, true), mode = stanceMode(s, d);
        if (r.cm && r.cm[mode]) return r.cm[mode];
        const cm = contestMap(r[0], r[1], mode);
        if (SPEED.reach_cache) { if (!r.cm) r.cm = [null, null, null]; r.cm[mode] = cm; }
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
        return contestMap(new Map(), new Map([[frm, new Map([[a, 0]])]]), stanceMode(s, d));
      }
      return cmapCached(frm, a, s.ctx.dfn[d].qs, canMove, qsLeft, stanceMode(s, d));
    }
    _vals(lk, d, cm, moves, dflags) {           // moves (step 13C): at most that many reaction movements; 0 = where he stands
      // dflags (step 18e, the open list's re-read): the defender's control state after his action, in place of now
      const ctx = this.s.ctx;
      if (ctx.soft) {
        // D-177: a soft contest needs no action, so every action of the reaction may be a movement (decide.Read._vals)
        if (!cm) return null;
        const b = BI[lk.c], s = this.s, control = controlOn(ctx);
        const hard = this.react_moves < 0 ? 0 : cm.masks[moves === undefined ? this.react_moves : Math.min(moves, this.react_moves)][b];
        const sl = ctx.cc ? Math.max(this.react_moves, 0) : Math.min(2, Math.max(this.react, this.react_moves, 0));      // D-261: the normal Contest is an action too
        const smask = cm.masks[moves === undefined ? sl : Math.min(moves, sl)][b];
        if (!hard && !smask) return null;
        const st0 = cm.masks[0][b];
        const flags = control ? ((lk.rushed ? 1 : 0) | (dflags === undefined ? ((rushedX(s, d) ? 2 : 0) | (hasMoved(s, 'X', d) ? 4 : 0)) : dflags)) : 0;
        const vc3 = ctx._vc3 || (ctx._vc3 = new Map());
        const key3 = ((((((lk.i * NB + b) * 5 + d) * 64 + hard) * 64 + smask) * 64 + st0) * 8 + flags) * 2 + (control ? 1 : 0);
        let hit3 = vc3.get(key3);
        if (hit3 === undefined) { hit3 = this._valsCalc(lk, d, hard, st0 & hard, control ? flags : undefined, smask, st0); vc3.set(key3, hit3); }
        return hit3;
      }
      if (!cm || this.react_moves < 0) return null;
      const mask = cm.masks[moves === undefined ? this.react_moves : Math.min(moves, this.react_moves)][BI[lk.c]];
      if (!mask) return null;
      if (controlOn(ctx)) {
        // D-151 (rules.control), as the reading takes it (decide.Read._vals): the kinds he reaches standing are rushed
        // if his last movement was a Quick Step or Sprint; the kinds he must move for are rushed if his Move is used
        const s = this.s, m0 = cm.masks[0][BI[lk.c]] & mask;
        const flags = (lk.rushed ? 1 : 0) | (dflags === undefined ? ((rushedX(s, d) ? 2 : 0) | (hasMoved(s, 'X', d) ? 4 : 0)) : dflags);
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
    _valsCalc(lk, d, mask, m0, flags, smask, st0, split) {  // m0, flags: only under rules.control (D-151); smask, st0: the soft contest (D-177)
      // split (step 31): an array; the blocks are not folded in at -5 but pushed as lines (type index, c0, c1: blockLine)
      const ctx = this.s.ctx, card = ctx.off[lk.i], pts = ctx.worth[szone(ctx, lk.c)], dc = this.dcards[d];
      const out = new Float64Array(lk.types.length);
      const control = flags !== undefined;
      let any = false;
      for (let t = 0; t < lk.types.length; t++) {
        const ty = lk.types[t];
        let r = cardShot(ctx, card, ty, lk.c);           // D-274: a deep three is 1 off a square past the band
        const cut = control ? controlCut(ctx, ty) : 0, shooterCut = cut > 0 && (flags & 1) === 1;
        if (shooterCut) r -= cut;
        let best = null;
        const pos = ctx.pos, jump = pos && JUMP[ty] === true;    // D-191: a jump shot has no Contest action: position only (below)
        for (let k = 0; k < 6; k++) {
          if (ctx.block && ((mask >> k) & 1)) {
            // decide.Read._block_value (D-271): the block, from every kind he reaches, on every shot
            const rk = cut > 0 && (((m0 >> k) & 1) ? (flags & 2) : (flags & 4));
            if (split) {                                 // step 31: the block as a line; the plain Contest stays his other answer (below)
              const ln = blockLine(ctx, card, dc, ty, k, pts, r, rk ? cut : 0, shooterCut); split.push(t, ln[0], ln[1]); any = true;
            } else {
              const v = blockValue(ctx, card, dc, ty, k, pts, r, rk ? cut : 0, shooterCut);
              if (best === null || v < best) best = v;
              continue;
            }
          }
          if (jump || !((mask >> k) & 1)) continue;
          const foul = KFOUL[k], two = KTWO[k];
          if (pos && !foul) continue;                            // D-191: in front with the arrow on him: automatic (below)
          let con = dc.cn[ty] - (KPEN[k] ? 3 : 0);
          con = Math.max(0, con);
          if (cut > 0 && (((m0 >> k) & 1) ? (flags & 2) : (flags & 4))) {       // a rushed Contest
            con = Math.max(0, con - cut);                                        // no extra foul roll (D-154)
          }
          if (pos && con < 1) con = 1;                           // D-193
          let v = Math.max(0, pts * (r - con));
          if (foul) {
            const ft = ctx.fiba ? footPoints(card, ty, pts, r, true, v, r - con)[0] : footPoints(card, ty, pts, shooterCut ? r : undefined)[0];
            const pf = pFouls(dc.r.foul_contest, two ? 2 : 1);
            v = pf * (ft + (ctx.ppo ? 5 : 0)) + (1 - pf) * v;      // D-198: a shooting foul is +5 and its free throws (step 18s)
          }
          if (best === null || v < best) best = v;
        }
        if (smask) {
          for (let k = 0; k < 6; k++) {
            if (!((smask >> k) & 1)) continue;
            // D-194: the full rating from in front with the arrow on him, on every shot; else 3 less
            let con = dc.cn[ty] - ((pos && !KFOUL[k]) ? 0 : 3) - (KPEN[k] ? 3 : 0);
            if (cut > 0 && (((st0 >> k) & 1) ? (flags & 2) : (flags & 4))) con -= cut;
            if (pos && con < 1) con = 1;                         // D-193
            if (con <= 0) continue;
            const v = Math.max(0, pts * (r - con));
            if (best === null || v < best) best = v;
          }
        }
        if (best !== null) { out[t] = best; any = true; }
        else out[t] = Math.max(0, pts * r);              // D-177: a soft contest worth nothing on this shot: it stays open to him
      }
      return any ? out : null;
    }
    passP(i, c) {
      const s = this.s;
      if (i === s.ball) return 1.0;
      if (count(s, 'O', 'pass') >= 2) return 0.0;
      if (this.exact && c === s.o[i]) return passProb(s, i);
      if (passRulesOn()) {                         // step 18s, stop two: by the rules, kept for this reading
        const m = this._lpr || (this._lpr = new Map());
        let p = m.get(c * 8 + i);
        if (p === undefined) { p = laneP(s, i, c); m.set(c * 8 + i, p); }
        return p;
      }
      if (!SPEED.lane_p) return this._lane(c).p;
      // step 18f (a speed-up that changes no result, SPEED.lane_p): the chance alone, as _lane works it out, without
      // building the parts per defender that only the moved re-reads of the few looks kept ever use
      const m = this._lpp || (this._lpp = new Map());
      let p = m.get(c);
      if (p !== undefined) return p;
      const a = s.o[s.ball];
      if (!(ONB[a] && ONB[c])) p = 0;
      else {
        const den = laneSquares(a, c);
        let denied = false;
        if (den.size) for (let d = 0; d < 5; d++) { const xp = s.x[d]; if (den.has(xp) && adjacent(xp, c)) { denied = true; break; } }
        if (denied) p = 0;
        else if (!den.size) p = 1;
        else {
          const passer = rolled(s, 'O', s.ball, 'pass'), exact = reachOn(), bi = den.bi;
          let worst = 0;
          for (let d = 0; d < 5; d++) {
            let one;
            if (exact) one = exactOne(s, d);
            else { const cp = caps(s, 'X', d); one = oneAction(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, cp[0], cp[1]); }
            let hit = false;
            for (let k = 0; k < bi.length; k++) { const b = bi[k]; if ((one[b >> 5] >>> (b & 31)) & 1) { hit = true; break; } }
            if (hit) { const pi = 1 - pS(passer - rolled(s, 'X', d, 'intercept')); if (pi > worst) worst = pi; }
          }
          p = 1 - worst;
        }
      }
      m.set(c, p); return p;
    }
    _lane(c) {                                   // laneP(s, ., c) and its parts per defender, for the moved re-reads
      const lp = this._lp || (this._lp = new Map());
      let r = lp.get(c);
      if (r) return r;
      const s = this.s, a = s.o[s.ball];
      r = { off: !(ONB[a] && ONB[c]), den: null, denies: [false, false, false, false, false], hit: [false, false, false, false, false], pi: [0, 0, 0, 0, 0], p: 0 };
      if (!r.off) {
        const den = laneSquares(a, c); r.den = den;
        const passer = rolled(s, 'O', s.ball, 'pass');
        for (let d = 0; d < 5; d++) {
          const xp = s.x[d];
          r.denies[d] = den.has(xp) && adjacent(xp, c);
          if (den.size) {
            const [canMove, qsLeft] = caps(s, 'X', d);
            const one = oneAction(xp, s.arrows[d], s.ctx.dfn[d].qs, canMove, qsLeft);
            let hit = false; for (const b of den.bi) if ((one[b >> 5] >>> (b & 31)) & 1) { hit = true; break; }
            r.hit[d] = hit;
            r.pi[d] = 1 - pS(passer - rolled(s, 'X', d, 'intercept'));
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
    _laneMoved(c, j, q, oneJ, a, cm, ql, i) {    // laneP with defender j at q (decide.responses' moved state)
      if (passRulesOn()) {                         // step 18s, stop two: by the rules, with him there
        const s = this.s, pa = s.o[s.ball];
        if (!(ONB[pa] && ONB[c])) return 0;
        const den = laneSquares(pa, c);
        for (let d = 0; d < 5; d++) { const at = d === j ? q : s.x[d]; if (den.has(at) && adjacent(at, c)) return 0; }
        return lanePRules(s, i, c, j, q, a, cm, ql);
      }
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
    _looks(i, s = this.s, cm = this._cm, dj = -1, dfl = undefined) {      // dj, dfl (step 18f): defender dj's control state, given
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
          const lst = reachList(s.o[i], pivotLen(s, 'O', i, s.ctx.off[i].qs), canMove, qsLeft);
          for (let n = 0; n < lst.length; n += 2) { const q = lst[n]; if (lst[n + 1] === 0 || !occAt(s, q)) reach.set(q, lst[n + 1]); }
        } else reach.set(s.o[i], 0);
      }
      const build = (c, n) => {
        const z = szone(s.ctx, c);
        if (!SHOOT(z) || (c === RIM && this.s.ctx.noRim)) return null;
        let lk;
        if (i === s.ball) {
          if (n === 0 && shotOk && leftNow >= 1) lk = makeLook(i, c, 'shoot', 1.0, this.o_to_act);
          else if (n === 1 && shotOk && leftNow >= 2 && s.tok_o >= 2) lk = makeLook(i, c, 'drive', 1.0, this.o_to_act);
          else lk = makeLook(i, c, 'later', this.cfg.later_p, false, this.o_to_act ? 1 : 2);
        } else {
          const p = this.passP(i, c);
          if (p <= 0) return null;
          if (n === 0) lk = makeLook(i, c, 'catch', p, false, 1);
          else if (leftNow >= 2 && s.tok_o >= 2 && this.o_to_act) lk = makeLook(i, c, 'cut', p, false, 1);
          else lk = makeLook(i, c, 'cut', p * this.cfg.later_p, false, 2);
        }
        lk.types = ZONE_SHOTS[z];
        const pts = this.s.ctx.worth[z];
        if (controlOn(s.ctx)) lk.rushed = n === 0 ? rushedO(s, i) : hasMoved(s, 'O', i);      // D-151 (decide.Read._looks)
        lk.open = lk.rushed ? lk.types.map(t => pts * (cardShot(s.ctx, card, t, c) - controlCut(s.ctx, t))) : lk.types.map(t => pts * cardShot(s.ctx, card, t, c));
        lk.vals = [null, null, null, null, null];
        for (const d of this.att_x) { const v = this._vals(lk, d, cm[d], undefined, d === dj ? dfl : undefined); if (v) lk.vals[d] = v; }
        finishLook(lk);
        return lk;
      };
      if (SPEED.look_lazy) {
        // step 18f (a speed-up that changes no result, SPEED.look_lazy): only the best L looks are kept, earlier ones
        // first when level. So each square's value is worked out first, the same sum in the same order and with
        // nothing built; then only the L kept are built.
        const ctl = controlOn(s.ctx), laterP = this.cfg.later_p, onBall = i === s.ball, L = this.L;
        const scratch = { i, c: 0, rushed: false, types: null };
        const cs = [], ns = [], bs = [];
        const pre = (c, n) => {
          const z = szone(s.ctx, c);
          if (!SHOOT(z) || (c === RIM && this.s.ctx.noRim)) return;
          let p;
          if (onBall) p = (n === 0 && shotOk && leftNow >= 1) || (n === 1 && shotOk && leftNow >= 2 && s.tok_o >= 2) ? 1.0 : laterP;
          else {
            p = this.passP(i, c);
            if (p <= 0) return;
            if (!(n === 0 || (leftNow >= 2 && s.tok_o >= 2 && this.o_to_act))) p = p * laterP;
          }
          const types = ZONE_SHOTS[z], pts = this.s.ctx.worth[z], nt = types.length;
          const rushed = ctl ? (n === 0 ? rushedO(s, i) : hasMoved(s, 'O', i)) : false;
          scratch.c = c; scratch.rushed = rushed; scratch.types = types;
          let best = 0.0, first = true, v0 = 0, v1 = 0, v2 = 0;
          for (let t = 0; t < nt; t++) { const v = rushed ? pts * (cardShot(s.ctx, card, types[t], c) - controlCut(s.ctx, types[t])) : pts * cardShot(s.ctx, card, types[t], c); if (t === 0) v0 = v; else if (t === 1) v1 = v; else v2 = v; }
          for (const d of this.att_x) {
            const vals = this._vals(scratch, d, cm[d], undefined, d === dj ? dfl : undefined);
            if (!vals) continue;
            if (vals[0] < v0) v0 = vals[0];
            if (nt > 1 && vals[1] < v1) v1 = vals[1];
            if (nt > 2 && vals[2] < v2) v2 = vals[2];
          }
          best = Math.max(best, v0); if (nt > 1) best = Math.max(best, v1); if (nt > 2) best = Math.max(best, v2);
          cs.push(c); ns.push(n); bs.push(p * best);
        };
        for (const [c, n] of reach) pre(c, n);
        if (onBall && budgetCfg()) {
          let floor = -Infinity;
          if (SPEED.two_bound && bs.length >= L) floor = bs.slice().sort((a, b) => b - a)[L - 1];
          const most = new Map();
          const keep = c => {
            const z = szone(s.ctx, c);
            if (!SHOOT(z) || (c === RIM && this.s.ctx.noRim)) return false;
            let m = most.get(z);
            if (m === undefined) { m = 0.0; const pts = this.s.ctx.worth[z]; for (const t of ZONE_SHOTS[z]) { const v = pts * card.sh[t]; if (v > m) m = v; } m = this.cfg.later_p * m; most.set(z, m); }
            return m > floor;
          };
          for (const q of twoActions(s, i, reach, keep)) pre(q, 2);
        }
        const idx = bs.map((_, k) => k).sort((x, y) => (bs[y] - bs[x]) || (x - y));
        const kept = [];
        for (let k = 0; k < idx.length && k < L; k++) kept.push(build(cs[idx[k]], ns[idx[k]]));
        return kept;
      }
      const add = (c, n) => { const lk = build(c, n); if (lk) out.push(lk); };
      for (const [c, n] of reach) add(c, n);
      if (i === s.ball && budgetCfg()) {
        // step 13 B2 (D-115): the squares two actions away. Step 13C (a speed-up that changes no result): such a look is
        // worth at most later_p times his best shot from its zone, and the list keeps the best L looks, earlier ones
        // first when level. So a square whose most can't beat the L-th look already found is never built or searched.
        let floor = -Infinity;
        if (SPEED.two_bound && out.length >= this.L) { const bs = out.map(l => l.base).sort((a, b) => b - a); floor = bs[this.L - 1]; }
        const most = new Map();
        const keep = c => {
          const z = szone(s.ctx, c);
          if (!SHOOT(z) || (c === RIM && this.s.ctx.noRim)) return false;
          let m = most.get(z);
          if (m === undefined) { m = 0.0; const pts = this.s.ctx.worth[z]; for (const t of ZONE_SHOTS[z]) { const v = pts * card.sh[t]; if (v > m) m = v; } m = this.cfg.later_p * m; most.set(z, m); }
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
      const kept = keptOn() && controlOn(s.ctx), movedJ = hasMoved(s, 'X', j);
      for (const [q, a, used] of cands) {
        const cm = this._contest(j, q, a, used);
        // step 18f: his control after the answer (2: rushed where he stands, 4: his Move is used)
        const dfl = !kept ? undefined : used === 'move' ? 4 : (2 | (movedJ ? 4 : 0));
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
            const lks = this._looks(carrier, moved, cm2, j, dfl);
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
                pNew = this._laneMoved(lk.c, j, q, oneJ, a, used === 'move' ? false : capsJ[0], capsJ[1], i);
              }
              v = swapped(lk, j, this._vals(lk, j, cm, undefined, dfl), pNew);
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
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
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
        if (here.has(c) || blocked(c) || (c === RIM && s.ctx.noRim)) continue;      // D-198
        let ok = false;
        for (const q0 of stops) {
          for (const p of pathsTo(q0, c, qs)) { let free = true; for (const q of p) if (blocked(q)) { free = false; break; } if (free) { ok = true; break; } }
          if (ok) break;
        }
        if (!ok) continue;
        const lk = makeLook(i, c, 'later', 1.0, false);
        lk.types = ZONE_SHOTS[PAINT];
        const vals = [null, null, null, null, null];
        for (const d of this.att_x) { const cm = this._cm[d]; if (cm) { const mask = cm.masks[2][BI[c]]; if (mask) vals[d] = this._valsCalc(lk, d, mask, 0, undefined, s.ctx.soft ? mask : 0, 0); } }      // D-177: hard or soft, whichever is better for the defence
        let top = 0.0;
        for (let t = 0; t < lk.types.length; t++) {
          let v = this.s.ctx.worth[PAINT] * card.sh[lk.types[t]];
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
                p = this._laneMoved(lk.c, j, q, oneJ, a, used === 'move' ? false : capsJ[0], capsJ[1], i);
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
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
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
      const mode = leafMode(s);
      if (mode === 'relative') return banked + Math.max(now, coarse + cont - relativeAverage(s, bud));
      if (mode === 'looks') return banked + Math.max(now, cont);
      return banked + Math.max(now, cont, coarse);
    }
    quickLeaf() {
      // Read(s, k=0, looks_per=3).leaf() from this read (attention all, looks_per 6): the first three looks of each
      // attacker are that read's looks, its threats are these, and with k = 0 the cover leaves every threat.
      if (this._quick !== undefined) return this._quick;
      const s = this.s;
      if (valueLead()) { const ml = this._mapLeaf(); if (ml !== null) return (this._quick = ml); }   // step 31: the lists are ordered and cut by the value itself
      if (!s.pending) return (this._quick = this._quickCont(this._contOf(null)));
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
      banked += foulExternality(s);
      const passer = s.pending[0], recv = s.pending[1];
      const p = laneP(W_(s, { ball: passer }), recv, s.o[recv]);
      let v = p * readOf(W_(s, { ball: recv, pending: null })).quickLeaf() + (1 - p) * turnoverValue(s);
      if (settleOn()) { const top = ceilingOf(s); if (v - banked > top) v = banked + top; }   // step 18b: no reading above the ceiling
      this._quick = v;
      return v;
    }
    // The quick reading's two halves (no pass in the air). _contOf: what the attackers' best looks leave to play for
    // (tv: each attacker's best look; null: this read's own). _quickCont: the reading from that. Step 18e: the open
    // list's cheap read gives _contOf the looks re-read with one defender moved.
    _contOf(tv) {
      let top = 0.0, first = true;
      for (const i of this.att_o) { const t = tv === null ? this.threat[i].value : tv[i]; if (first || t > top) top = t; first = false; }
      let sum = 0.0, nt = 0;
      for (const i of this.att_o) { const t = tv === null ? this.threat[i].value : tv[i]; if (t >= top - 1e-9) { sum += t; nt++; } }
      return (nt ? sum / nt : 0.0) * this.cfg.continuation;
    }
    _quickCont(cont, nowv, snv, tv) {             // nowv, snv (step 18e): the shots that can go up now, re-read (snv < 0: none); tv (step 18h): each attacker's best look, re-read
      const s = this.s;
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
      banked += foulExternality(s);
      let sn = null, now = 0.0;
      if (nowv !== undefined) { now = nowv; sn = snv < 0 ? null : snv; }
      else {
        if (this.o_to_act) { const ls = this.looks[s.ball] || []; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].route === 'shoot') { sn = ls[n].base; break; } }
        for (const i of this.att_o) { const ls = this.looks[i]; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].now && ls[n].base > now) now = ls[n].base; }
      }
      let v;
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) v = banked + Math.max(sn || 0.0, now);
      else if (laneOn() && leafMode(s) === 'relative') {   // step 18q: the lane, re-read (tv[7]) or this read's own
        let rel = vcoarse(s) + cont - relativeAverage(s, false);
        if (tv !== undefined && tv !== null && tv.length > 7) rel = this.laneRel(rel, tv[7], tv[8], tv[9], false);
        else rel = this.laneOwn(rel, false);
        v = banked + Math.max(sn || 0.0, now, rel);
      } else v = leafOf(s, banked, sn, now, cont, vcoarse(s));
      if (settleOn()) {
        // step 18b: the ordering reading on the leaf's own scale (the ceiling, the calibrated map, the ceiling), so a
        // settled shot and a position that plays on are ranked together (decide.Read.leaf with k = 0)
        const top = ceilingOf(s);
        if (v - banked > top) v = banked + top;
        if (calibratedOn() && s.stage === 'play' && !(!this.o_to_act && s.tok_o <= 0 && s.clock <= 2)) {
          let pm = partsMap(s);
          let r = null;
          const po = playOnMap(s);
          if (po) {                                  // step 18h (eval.exact_shot)
            let rel = vcoarse(s) + cont - relativeAverage(s, false);
            if (rel > top) rel = top;
            r = Math.max(sn || 0.0, now, calibrate(s, this.o_to_act, rel, po));
            pm = null;
          }
          if (pm) {                                  // step 18h (eval.no_floor): with no cover read, every look is left
            const t2 = topTwo(this.att_o, tv ? (i => tv[i]) : (i => this.threat[i].value));
            r = partsValue(pm, s, this.o_to_act, Math.max(sn || 0.0, now), t2[0], t2[1]);
          }
          if (r === null) r = calibrate(s, this.o_to_act, v - banked);
          if (r > top) r = top;
          v = banked + r;
        }
      }
      return v;
    }
    // ---- step 18e (search.open_list, D-156): the cheap read of a defender's action -------------------------------
    // Every attacker's best look with defender j standing at q facing a, with canMove / qsLeft left to him and his
    // control state dflags (2: rushed where he stands, 4: his Move is used): this read's own looks, each re-read with
    // that one defender moved (the re-read decide.responses makes for its hand-picked squares, here for any square,
    // for every attacker, and for the looks that can go up now as well). Written into out: one value an attacker, then
    // out[5] the best shot that can go up now and out[6] the ball handler's shot from where he stands (-1: none), each
    // among an attacker's first three looks as the quick reading takes them.
    _contestAt(j, q, a, canMove, qsLeft) {
      const s = this.s;                               // as _contest reads a defender where he stands (this read's position
      if (s.tok_x <= 0) return contestMap(new Map(), new Map([[q, new Map([[a, 0]])]]), stanceMode(s, j));   // is the turn already advanced)
      return cmapCached(q, a, s.ctx.dfn[j].qs, canMove, qsLeft, stanceMode(s, j));
    }
    reread(j, q, a, canMove, qsLeft, dflags, out) {
      const s = this.s, carrier = s.ball, reach = reachOn();
      const leave = this._leave || (this._leave = new Map());
      const cm = this._contestAt(j, q, a, canMove, qsLeft);
      // (a speed-up that changes no result: the squares in the ball handler's way, worked out once for this read)
      let fr = this._front;
      if (fr === undefined) {
        fr = this._front = new Uint8Array(NSQ);
        if (this.att_o.includes(carrier)) { const cs = s.o[carrier]; for (let p = 0; p < NSQ; p++) if (cheb(p, cs) <= 2 && DR[p] < DR[cs]) fr[p] = 1; }
      }
      const moved = q !== s.x[j];
      const into = moved && fr[q] === 1, outOf = moved && fr[s.x[j]] === 1 && fr[q] !== 1;
      const blocks = into || outOf;
      for (let i = 0; i < 5; i++) out[i] = 0.0;
      out[7] = -1.0; out[8] = -1.0; out[9] = 0.0;
      if (laneOn()) {                                 // step 18q: the lane, and the lane with the man his Dribble would beat out of it
        out[7] = this.laneReread(j, q, a, canMove, qsLeft);
        const dr = this.laneDribble(out[7], [0, 0], j, q, a, canMove, qsLeft, (dflags & 2) !== 0);
        out[8] = dr[0]; out[9] = dr[1];
      }
      let nowv = 0.0, snv = -1;
      if (blocks) {
        let lv = outOf ? leave.get(j) : undefined;
        if (lv === undefined) {
          const at = into ? q : AWAY;
          const mv = W_(s, { x: setAt(s.x, j, at), arrows: setAt(s.arrows, j, a) });
          const cm2 = this._cm.slice(); cm2[j] = into ? cm : null;
          const lks = keptOn() ? this._looks(carrier, mv, cm2, j, dflags) : this._looks(carrier, mv, cm2);
          lv = [0.0, 0.0, -1];
          for (const l of lks) if (l.base > lv[0]) lv[0] = l.base;
          for (let n = 0; n < Math.min(3, lks.length); n++) {
            if (lks[n].now && lks[n].base > lv[1]) lv[1] = lks[n].base;
            if (lv[2] < 0 && this.o_to_act && lks[n].route === 'shoot') lv[2] = lks[n].base;
          }
          if (outOf) leave.set(j, lv);
        }
        out[carrier] = lv[0]; nowv = lv[1]; snv = lv[2];
      }
      let oneJ = null;
      const rm = this.react_moves;
      for (const i of this.att_o) {
        if (i === carrier && blocks) continue;
        let best = 0.0;
        const ls = this.looks[i];
        for (let n = 0; n < ls.length; n++) {
          const lk = ls[n];
          let v;
          if (reach && moved && !lk.now && PATH_ROUTES.has(lk.route) && blocksPath(q, s.o[i], lk.c, s.ctx.off[i].qs)) v = 0.0;
          else {
            let pNew = null;
            if ((lk.route === 'catch' || lk.route === 'cut') && moved) {
              if (!oneJ) oneJ = oneAction(q, a, s.ctx.dfn[j].qs, canMove, qsLeft);
              pNew = this._laneMoved(lk.c, j, q, oneJ, a, canMove, qsLeft, i);
            }
            // (a speed-up that changes no result: where he can't contest the look, swapped() is the look's best
            // without him, kept on the look)
            if (s.ctx.soft && !s.ctx.cc ? !cm.masks[Math.min(2, Math.max(this.react, rm, 0))][BI[lk.c]] : (rm < 0 || !cm.masks[rm][BI[lk.c]])) {      // D-177: a soft contest reaches a movement further
              let bx = lk.bx;
              if (bx === undefined) {
                bx = lk.bx = new Float64Array(5);
                const mx = lk.minex, nt = lk.types.length;
                for (let d = 0; d < 5; d++) { let b = 0.0; for (let t = 0; t < nt; t++) if (mx[d * nt + t] > b) b = mx[d * nt + t]; bx[d] = b; }
              }
              v = (pNew === null ? lk.p : pNew) * bx[j];
            } else v = swapped(lk, j, this._vals(lk, j, cm, undefined, dflags), pNew);
          }
          if (v > best) best = v;
          if (n < 3) {
            if (lk.now && v > nowv) nowv = v;
            if (snv < 0 && i === carrier && this.o_to_act && lk.route === 'shoot') snv = v;
          }
        }
        out[i] = best;
      }
      out[5] = nowv; out[6] = snv;
      return out;
    }
    // Step 13 (a speed-up that changes no result): Read(s, k=0, looks_per=3): is the ball handler's shot now worth more
    // than the possession without it? From this read, as quickLeaf is (the offence to act, no pass in the air).
    quickShotFirst() {
      if (this._qshot !== undefined) return this._qshot;
      const s = this.s;
      let sn = null;
      if (this.o_to_act) { const ls = this.looks[s.ball] || []; for (let n = 0; n < Math.min(3, ls.length); n++) if (ls[n].route === 'shoot') { sn = ls[n].base; break; } }
      if (sn === null) return (this._qshot = false);
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
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
        const mode = leafMode(s);
        if (mode === 'relative') poss = banked + Math.max(now, coarse + cont - relativeAverage(s));
        else if (mode === 'looks') poss = banked + Math.max(now, cont);
        else poss = banked + Math.max(now, cont, coarse);
      }
      return (this._qshot = sn > poss + 1e-9);
    }
    leaf() {
      if (this._leaf !== undefined) return this._leaf;
      return (this._leaf = this._leafCalc());
    }
    // step 18s, stop two (eval.map, off until its checks pass): the coverage map's two numbers for the search. The
    // best any attacker can have at the start of the next phase (the map's strength as the board stands), and the best
    // a second, separate attacker can have (a second way: what makes a defence fragile).
    mapTwo(answered) {                             // [best way, second way]: as the board stands, or after the defence's answers
      // (only the numbers are kept with the reading: the map itself is let go, or a long search holds thousands of them)
      const c = this._map2 || (this._map2 = { raw: null, ans: null });
      if (answered ? c.ans !== null : c.raw !== null) return answered ? c.ans : c.raw;
      const m = covBuild(this.s, true, this);
      const two = () => {
        const mine = [0, 0, 0, 0, 0];
        for (const o of m.options) if (o.r > 0 && o.e > mine[o.a]) mine[o.a] = o.e;
        let a = 0, b = 0;
        for (let i = 0; i < 5; i++) { const v = mine[i]; if (v > a) { b = a; a = v; } else if (v > b) b = v; }
        return [a, b];
      };
      c.raw = two();
      if (answered) { covLeanAnswers(m); c.ans = two(); }
      return answered ? c.ans : c.raw;
    }
    mapValue() {                                   // step 31: the possession's value of playing on (possValue), kept with the reading
      if (this._pv === undefined) this._pv = possValue(this.s);
      return this._pv;
    }
    mapShotOrNone() {                              // the best shot that can go up now; null when none can (the clock then costs -5)
      const sn = this.shotNow();
      let now = sn;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && (now === null || lk.base > now)) now = lk.base;
      return now;
    }
    mapShot() {                                    // the best shot that can go up now, as the reading has it
      const sn = this.shotNow();
      let now = 0.0;
      for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && lk.base > now) now = lk.base;
      return Math.max(sn || 0.0, now);
    }
    // step 20 (Shaun, 17 Nov 2026): the lasting gap, read like for like (lastingOf); only the number is kept with the
    // reading, or a long search holds thousands of maps
    mapLasting() {
      if (this._lg === undefined) {
        const g = lastingOf(this.s, this);
        this._lg = g ? g.L : null; this._lgMoves = g && g.best ? g.best.moves : null; this._lgThreats = lgThreats(g);
      }
      return this._lg;
    }
    mapThreats() { this.mapLasting(); return this._lgThreats || []; }
    mapTop() {                                     // step 22b: the largest item on the list as the defence stands (topOf)
      if (this._top === undefined) this._top = topOf(this.s);
      return this._top;
    }
    mapAnswer() {                                  // step 21: the moves of the defence's best answer (the search tries them)
      this.mapLasting();
      if (this._lgAll === undefined) {               // step 22b (D-219): and the settlement's own one or two movements
        const mv = (this._lgMoves || []).slice();
        for (const z of this.mapSettle()) if (!mv.some(y => y[0] === z[0] && y[1] === z[1] && y[2] === z[2])) mv.push(z);
        this._lgAll = mv;
      }
      return this._lgAll;
    }
    mapSettle() {
      if (this._lgSettle === undefined) {
        const s = this.s;
        if (s.stage !== 'play' || s.clock <= 2 || s.pending) this._lgSettle = [];
        else {
          // step 31, fix 1: the same position settles the same way, so within a think it is read once (the reset choice
          // reads it for every line that reaches a block)
          const key = MAP_MEMO !== null ? 'MS|' + RD.lead + '|' + (MAP_ME || '') + '|' + (D.config.eval.answer_lead || '') + '|' + stateKey(s) : null;
          let hit = key !== null ? MAP_MEMO.get(key) : undefined;
          if (hit === undefined) { hit = settleMoves(covBuild(covOffFresh(s), true, null)); if (key !== null) MAP_MEMO.set(key, hit); }
          this._lgSettle = hit;
        }
      }
      return this._lgSettle;
    }
    // The reading from the map, both sides (step 20): what is banked, plus the larger of the best shot that can go up
    // now and the lasting gap: what the offence can still force after the defence's best answer. Used directly: it is
    // already in points, as a shot's value is. The offence plays to make it larger, the defence to keep it small.
    _mapLeaf() {
      const s = this.s;
      if (!mapOn() || this.k <= 0 || !s.ctx.digital || s.stage !== 'play') return null;
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
      banked += foulExternality(s);
      if (valueLead()) {                           // step 31 (D-284): the possession's value: the shot now, or playing on
        if (s.pending) return banked + this.mapValue();
        const sh = this.mapShotOrNone();
        return banked + Math.max(sh === null ? SHOT_CLOCK_OUT : sh, this.mapValue());
      }
      if (s.pending) {                             // step 21: a pass in the air, by the rules' chance of the catch
        const L = mapLead() ? this.mapTop() : this.mapLasting();
        return L === null ? null : banked + L;
      }
      const shot = this.mapShot();
      if (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2) return banked + shot;
      const L = mapLead() ? this.mapTop() : this.mapLasting();
      return banked + Math.max(shot, L === null ? 0 : L);
    }
    _leafCalc() {
      const ml = this._mapLeaf();
      if (ml !== null) return ml;
      let v = this._handLeaf();
      const s = this.s;
      let top = null;
      if (settleOn()) {                              // step 18b (D-145): the ceiling, before the map
        let b0 = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
        b0 += foulExternality(s);
        top = ceilingOf(s);
        if (v - b0 > top) v = b0 + top;
      }
      if (!calibratedOn() || (this.k <= 0 && top === null) || s.stage !== 'play' || s.pending || (!this.o_to_act && s.tok_o <= 0 && s.clock <= 2)) return v;
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
      banked += foulExternality(s);
      const po = playOnMap(s);
      if (po) {                                      // step 18h (eval.exact_shot): the shot exact, "play on" mapped
        const sn = this.shotNow();
        let now = 0.0;
        for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && lk.base > now) now = lk.base;
        const res = this.cover().residual;
        let tp = 0.0, first = true;
        for (const i of this.att_o) { if (first || res[i] > tp) tp = res[i]; first = false; }
        let sum = 0.0, nt = 0;
        for (const i of this.att_o) if (res[i] >= tp - 1e-9) { sum += res[i]; nt++; }
        const bud = this.budgetOn();
        const cont = (bud ? this.budget().value : (nt ? sum / nt : 0.0)) * this.cfg.continuation;
        let rel = vcoarse(s) + cont - relativeAverage(s, bud);
        if (top !== null && rel > top) rel = top;
        let rx = Math.max(sn || 0.0, now, calibrate(s, this.o_to_act, rel, po));
        if (top !== null && rx > top) rx = top;
        return banked + rx;
      }
      const pm = partsMap(s);
      if (pm) {                                      // step 18h (eval.no_floor): the reading's parts, each kept
        const sn = this.shotNow();
        let now = 0.0;
        for (const i of this.att_o) for (const lk of this.looks[i]) if (lk.now && lk.base > now) now = lk.base;
        const res = this.cover().residual, t2 = topTwo(this.att_o, i => res[i]);
        let rp = partsValue(pm, s, this.o_to_act, Math.max(sn || 0.0, now), t2[0], t2[1]);
        if (rp !== null) { if (top !== null && rp > top) rp = top; return banked + rp; }
      }
      let r = calibrate(s, this.o_to_act, v - banked);                // step 17D: the same reading, calibrated
      if (top !== null && r > top) r = top;                           // and after it
      return banked + r;
    }
    _handLeaf() {                                 // today's hand-combined reading
      const s = this.s;
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
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
      if (laneOn() && leafMode(s) === 'relative') {
        // step 18q (decide.Read._hand_leaf, eval.lane): the ball handler's way to the rim next phase, read as this
        // turn's looks are, one phase on
        const rel = this.laneOwn(vcoarse(s) + cont - relativeAverage(s, bud), bud);
        return banked + Math.max(sn || 0.0, now, rel);
      }
      return leafOf(s, banked, sn, now, cont, vcoarse(s), bud);
    }
    aheadOf(value, budget) {                      // decide.Read.ahead_of
      const nxt = W_(this.s, { clock: this.s.clock - 2 });
      return vcoarse(nxt) + this.cfg.continuation * value - relativeAverage(nxt, budget);
    }
    _laneData() {                                 // decide.Read._lane_data
      if (this._lane18q !== undefined) return this._lane18q;
      this._lane18q = null;
      const s = this.s, i = s.ball;
      if (s.clock <= 2 || !this.att_o.includes(i) || !ONB[s.o[i]] || s.tok_o <= 0) return null;
      const one = new Map([[s.o[i], 0]]);
      for (const kind of ['move', 'qs', 'sprint']) {
        if (canMoveKind(s, 'O', i, kind)) for (const q of movementDests(s, 'O', i, kind).keys()) if (!one.has(q)) one.set(q, 1);
      }
      const stops = [...one.keys()].concat(twoActions(s, i, one));
      const here = new Set(stops), old = s.o[i], card = s.ctx.off[i], qs = card.qs;
      const mates = new Set(); for (let k = 0; k < 5; k++) if (k !== i) mates.add(s.o[k]);
      const xat = new Map(); for (let j = 0; j < 5; j++) if (ONB[s.x[j]]) xat.set(s.x[j], j);
      const lines = [];
      if (s.ctx.zone) {
        for (let j = 0; j < 5; j++) {                 // actions.capture_lines, a defender at a time
          const st = stanceOf(s, j);
          if (st < 8 || st >= 16 || !ONB[s.x[j]]) continue;
          if (s.beaten.some(b => b[0] === i && b[1] === j)) continue;
          if (screenBlocked(s, j)) continue;          // step 22b (D-217)
          const d0 = st - 8, d1 = (st - 7) % 8;
          lines.push([j, [[s.x[j], d0, d1, Math.max(1, zoneRay(s, j, d0, old, -1).length), Math.max(1, zoneRay(s, j, d1, old, -1).length)]]]);
        }
      }
      const paths = new Map();
      for (const q0 of stops) {
        for (const [p, rushed] of lanePaths(q0, qs)) {
          const c = p[p.length - 1];
          if (here.has(c) || (c === RIM && s.ctx.noRim)) continue;      // D-198
          let dm = 0, bad = false;
          for (const q of p) { if (mates.has(q)) { bad = true; break; } const j = xat.get(q); if (j !== undefined) dm |= 1 << j; }
          if (bad) continue;
          let zm = 0;
          for (const ln of lines) if (!captureOk(q0, p, ln[1])) zm |= 1 << ln[0];
          const pk = c * 2 + (rushed ? 1 : 0);
          let list = paths.get(pk);
          if (!list) { list = []; paths.set(pk, list); }
          list.push({ q0, p, dm, zm, stop: q0 !== old ? q0 : -1 });
        }
      }
      const budget = Math.max(0, Math.min(2, s.tok_x));
      const cands = [];
      const off = s.ctx.control > 0 ? s.ctx.control : 0;
      for (const c of paintSquares()) {
        let masks = null;
        for (let rushed = 0; rushed < 2; rushed++) {  // reached by a Move (a set shot), or by a Quick Step or Sprint (rushed)
          const list = paths.get(c * 2 + rushed);
          if (!list) continue;
          if (masks === null) {
            masks = [0, 0, 0, 0, 0];
            for (const d of this.att_x) {
              if (!ONB[s.x[d]]) continue;
              const cp = caps(s, 'X', d);
              masks[d] = aheadMask(c, s.x[d], s.arrows[d], s.ctx.dfn[d].qs, cp[0], cp[1], budget, stanceMode(s, d));
            }
          }
          const lk = makeLook(i, c, 'later', 1.0, false);
          lk.types = ZONE_SHOTS[PAINT];
          lk.rushed = rushed === 1;
          const fl = (rushed === 1 && off > 0) ? 1 : undefined;      // the shooter rushed by his own movement; no defender's state carries over
          const vals = [null, null, null, null, null];
          for (const d of this.att_x) if (masks[d]) vals[d] = this._valsCalc(lk, d, masks[d], 0, fl, s.ctx.soft ? masks[d] : 0, 0);
          const open = [];
          for (let t = 0; t < lk.types.length; t++) open.push(this.s.ctx.worth[PAINT] * (card.sh[lk.types[t]] - (rushed === 1 ? off : 0)));
          cands.push({ c, lk, paths: list, open, vals, fl });
        }
      }
      this._lane18q = cands.length ? { cands, budget, by: [], stat: [null, null, null, null, null, null], onWay: null } : null;
      return this._lane18q;
    }
    _laneValue(e, skip, extra, t) {               // decide.Read._lane_value (t: a defender a Dribble has beaten)
      let top = 0.0;
      for (let n = 0; n < e.open.length; n++) {
        let v = e.open[n];
        for (let d = 0; d < 5; d++) {
          if (d === skip || !e.vals[d]) continue;
          if (d === t) { const vb = this._laneBeatenVals(e, d); if (vb && vb[n] < v) v = vb[n]; continue; }
          if (e.vals[d][n] < v) v = e.vals[d][n];
        }
        if (extra && extra[n] < v) v = extra[n];
        if (v > top) top = v;
      }
      return top;
    }
    _laneBeatenVals(e, d, frm, arrow, qsLeft) {   // decide.Read._lane_beaten_vals: locked, his zone broken
      const s = this.s, mode = s.ctx.zone ? 2 : 0, budget = this._lane18q.budget;
      if (frm !== undefined) {
        const mask = aheadMask(e.c, frm, arrow, s.ctx.dfn[d].qs, false, qsLeft, budget, mode);
        return mask ? this._valsCalc(e.lk, d, mask, 0, e.fl, s.ctx.soft ? mask : 0, 0) : null;
      }
      if (!e.vb) e.vb = [undefined, undefined, undefined, undefined, undefined];
      if (e.vb[d] === undefined) {
        const mask = aheadMask(e.c, s.x[d], s.arrows[d], s.ctx.dfn[d].qs, false, caps(s, 'X', d)[1], budget, mode);
        e.vb[d] = mask ? this._valsCalc(e.lk, d, mask, 0, e.fl, s.ctx.soft ? mask : 0, 0) : null;
      }
      return e.vb[d];
    }
    _laneNext(t = -1) {                           // decide.Read._lane_next
      const data = this._laneData();
      if (!data) return null;
      const bt = t >= 0 ? (1 << t) : 0;
      let best = null;
      for (const e of data.cands) {
        let clear = false;
        for (const pt of e.paths) if (pt.dm === 0 && !(pt.zm & ~bt)) { clear = true; break; }
        if (!clear) continue;
        const top = this._laneValue(e, -1, null, t);
        if (best === null || top > best[1] + 1e-9) best = [e.c, top];
      }
      return best;
    }
    _laneStatic(t = -1) {                         // decide.Read._lane_static: [value, the lowest another defender's step leaves]
      const data = this._laneData();
      if (!data) return [-1.0, [INF_V, INF_V, INF_V, INF_V, INF_V]];
      const hit = data.stat[t + 1];
      if (hit) return hit;
      const s = this.s, bt = t >= 0 ? (1 << t) : 0, tgt = this._laneNext(t), base = tgt !== null ? tgt[1] : -1.0;
      const resp = [INF_V, INF_V, INF_V, INF_V, INF_V];
      if (data.budget > 0) {
        const cands = data.cands;
        const order = cands.map((e, n) => [this._laneValue(e, -1, null, t), n]);
        order.sort((x, y) => (y[0] - x[0]) || (x[1] - y[1]));
        let onWay = data.onWay;
        if (!onWay) {
          onWay = data.onWay = new Set();
          for (const e of cands) for (const pt of e.paths) { for (const q of pt.p) onWay.add(q); if (pt.stop >= 0) onWay.add(pt.stop); }
        }
        for (const j of this.att_x) {
          if (j === t || !ONB[s.x[j]]) continue;
          const r = defenderMap(s, j, true), reach = new Set(), bj = 1 << j;
          for (const [q, n] of r[0]) if (n > 0 && n <= data.budget) reach.add(q);
          for (const [q, arrs] of r[1]) for (const n of arrs.values()) if (n > 0 && n <= data.budget) { reach.add(q); break; }
          for (const q of reach) {
            if (!onWay.has(q) || occAt(s, q)) continue;
            let left = -1.0;
            for (const [v, n] of order) {
              const e = cands[n];
              if (e.c === q) continue;
              let open = false;
              for (const pt of e.paths) if (!(pt.dm & ~bj) && !(pt.zm & ~bj & ~bt) && pt.stop !== q && !pt.p.includes(q)) { open = true; break; }
              if (open) { left = v; break; }
            }
            if (left < resp[j]) resp[j] = left;
          }
        }
      }
      const low = Math.min(resp[0], resp[1], resp[2], resp[3], resp[4]);
      const excl = [0, 1, 2, 3, 4].map(j => { let m = INF_V; for (let k = 0; k < 5; k++) if (k !== j && resp[k] < m) m = resp[k]; return m; });
      data.stat[t + 1] = [Math.min(base, low), excl];
      return data.stat[t + 1];
    }
    laneReread(j, q, a, canMove, qsLeft, t = -1) {   // decide.Read.lane_reread
      const data = this._laneData();
      if (!data) return -1.0;
      const s = this.s, bj = 1 << j, bt = t >= 0 ? (1 << t) : 0, same = q === s.x[j] && a === s.arrows[j], mode = stanceMode(s, j);
      const line = (!same && mode === 1 && t !== j) ? [[q, a, (a + 1) % 8, 1, 1]] : null;
      const ok_ = (t + 1) * 5 + j;
      let order = data.by[ok_];
      if (!order) {
        order = data.by[ok_] = data.cands.map((e, n) => [this._laneValue(e, j, null, t), n]);
        order.sort((x, y) => (y[0] - x[0]) || (x[1] - y[1]));
      }
      let best = -1.0;
      for (const [bw, n] of order) {
        if (bw <= best + 1e-9) break;
        const e = data.cands[n];
        if (e.c === q) continue;
        let ok = false;
        for (const pt of e.paths) {
          if ((pt.dm & ~bj) || (same ? (pt.zm & ~bt) : (pt.zm & ~bj & ~bt)) || pt.stop === q || pt.p.includes(q)) continue;
          if (line !== null && !captureOk(pt.q0, pt.p, line)) continue;
          ok = true; break;
        }
        if (!ok) continue;
        let mine;
        if (t === j) mine = this._laneBeatenVals(e, j, q, a, qsLeft);
        else {
          const mask = aheadMask(e.c, q, a, s.ctx.dfn[j].qs, canMove, qsLeft, data.budget, mode);
          mine = mask ? this._valsCalc(e.lk, j, mask, 0, e.fl, s.ctx.soft ? mask : 0, 0) : null;
        }
        const v = this._laneValue(e, j, mine, t);
        if (v > best) best = v;
      }
      const other = this._laneStatic(t)[1][j];      // and after another defender's best step into it
      return other < best ? other : best;
    }
    // the Dribble in the race: a defender next to the ball handler only stays in it if he wins the roll
    _dribbleOk() {                                // decide.Read._dribble_ok
      if (this._drib === undefined) {
        const s = this.s, i = s.ball;
        const ok = s.tok_o > 0 && this.att_o.includes(i) && ONB[s.o[i]] && count(s, 'O', 'dribble') < LIMITS.O.dribble &&
          !(s.inbound && i === s.ctx.inbounder) && !isLocked(s, 'O', i) && !(s.ctx.guarded && (s.grd & 3) === 2);
        this._drib = [ok, ok ? rolled(s, 'O', i, 'dribble') : 0];
      }
      return this._drib;
    }
    _beatChance(t, rushed) {                      // decide.Read._beat_chance
      const s = this.s;
      const ag = rushed === undefined ? rolled(s, 'X', t, 'agility') : s.ctx.dfn[t].r.agility - (s.ctx.offCut > 0 && rushed ? s.ctx.offCut : 0);
      return pS(this._dribbleOk()[1] - ag);
    }
    laneDribble(lane, into, j = -1, q = -1, a = -1, canMove = false, qsLeft = 0, rushed = false) {   // decide.Read.lane_dribble -> into[0], into[1]
      into[0] = -1.0; into[1] = 0.0;
      if (!this._dribbleOk()[0] || !this._laneData()) return into;
      const s = this.s, bq = s.o[s.ball], floor = lane > 0 ? lane : 0.0;
      let gain = 0.0;
      for (let t = 0; t < 5; t++) {
        const at = t === j ? q : s.x[t];
        if (!ONB[at] || !adjacent(at, bq)) continue;
        const p = this._beatChance(t, t === j ? rushed : undefined);
        if (p <= 0) continue;
        const v = j < 0 ? this._laneStatic(t)[0] : this.laneReread(j, q, a, canMove, qsLeft, t);
        const g = p * (v - floor);
        if (g > gain + 1e-9) { into[0] = v; into[1] = p; gain = g; }
      }
      return into;
    }
    laneRel(rel, lane, beaten, p, budget) {       // decide.Read.lane_rel
      if (lane >= 0) { const ahead = this.aheadOf(lane, budget); if (ahead > rel) rel = ahead; }
      if (p > 0 && beaten >= 0) { const ahead = this.aheadOf(beaten, budget); if (ahead > rel) rel += p * (ahead - rel); }
      return rel;
    }
    laneOwn(rel, budget) {                        // decide.Read.lane_own
      const lane = this._laneStatic()[0], d = this.laneDribble(lane, [0, 0]);
      return this.laneRel(rel, lane, d[0], d[1], budget);
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
      if (READS.size >= READS_MAX) { READS_OLD = READS; READS = new Map(); }
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
  // Step 31 (step 30b's finding, Shaun, 25 Nov 2026): the board's hash is built from the state itself, every field,
  // and from the game it belongs to (the context's id: its cards and rules), never from a hand-picked list. The old
  // list had left out two fields (turn_moved, zeroed), and a reading kept under it could in principle pass from one
  // game to another. The fields are read off the state (the engine's own scratch, underscore names, left out).
  let ZKEYS = null;
  function zobrist(s) {
    let a = 0x811C9DC5 | 0, b = 0x2545F491 | 0;
    const mix = v => { a = Math.imul(a ^ v, 0x01000193); b = Math.imul((b ^ v) + 0x7F4A7C15, 0x85EBCA6B); b ^= b >>> 13; };
    const put = v => {
      if (v === null || v === undefined) mix(-1);
      else if (typeof v === 'number') { mix(v | 0); if (v !== (v | 0)) mix(Math.round(v * 65536) | 0); }
      else if (typeof v === 'boolean') mix(v ? 3 : 5);
      else if (typeof v === 'string') { mix(1000 + v.length); for (let i = 0; i < v.length; i++) mix(v.charCodeAt(i)); }
      else if (Array.isArray(v) || ArrayBuffer.isView(v)) { mix(2000 + v.length); for (let i = 0; i < v.length; i++) put(v[i]); }
      else { const ks = Object.keys(v); mix(3000 + ks.length); for (const k of ks) { put(k); put(v[k]); } }
    };
    if (ZKEYS === null) ZKEYS = Object.keys(s).filter(k => k !== 'ctx' && k.charCodeAt(0) !== 95);
    mix(s.ctx ? s.ctx.id | 0 : 0);
    for (let i = 0; i < ZKEYS.length; i++) put(s[ZKEYS[i]]);
    return (a >>> 0) * 65536 + ((b >>> 0) & 0xFFFF);          // 48 bits: ttKey stays an exact integer
  }
  const ttKey = (z, depth) => z * 16 + depth;          // a Map key: equal keys mean equal (state, depth)
  const actor = s => (s.stage === 'target' || s.stage === 'pick' || s.stage === 'forced') ? 'O' : (s.stage === 'reaction' || s.stage === 'contest' || s.stage === 'reset') ? 'X' : s.side;
  const terminalValue = s => scoreTotal(s) + foulExternality(s);
  const TIMEOUT = { timeout: true };
  const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now()) / 1000;
  const turnKey = t => t.map(a => a.id).join(',');

  function waitOf(acts) {
    for (const k of ['hesitate', 'pause', 'end_turn', 'forfeit']) for (const a of acts) if (a.kind === k) return a;
    return null;
  }
  const FIRSTS = new Set(['shot', 'pass', 'dribble', 'steal', 'intercept', 'challenge', 'forced_shot', 'contest']);
  // search.is_fake, fake_world, worlds, mix_game (D-272)
  const isFake = a => (a.kind === 'shot' || a.kind === 'pass') && a.arrow === 1 && a.side === 'O';
  const fakeWorld = s => !!s.decl && actor(s) === 'X' && (s.stage === 'reaction' || !!s.pending);
  const worlds = s => [W_(s, { fake: 0 }), W_(s, { fake: s.stage === 'reaction' ? 1 : 2 })];
  function mixGame(cols) {
    const n = cols.length, cands = [0.0, 1.0];
    for (let i = 0; i < n; i++) {
      const ai = cols[i][0], bi = cols[i][1];
      for (let j = i + 1; j < n; j++) {
        const aj = cols[j][0], bj = cols[j][1], den = (bi - ai) - (bj - aj);
        if (den !== 0) { const p = (aj - ai) / den; if (p > 0 && p < 1) cands.push(p); }
      }
    }
    cands.sort((x, y) => x - y);
    const g = p => { let m = Infinity; for (const [a, b] of cols) { const v = (1.0 - p) * a + p * b; if (v < m) m = v; } return m; };
    let bestP = 0.0, bestV = g(0.0);
    for (const p of cands) { const v = g(p); if (v > bestV + 1e-12) { bestP = p; bestV = v; } }
    const act = []; cols.forEach(([a, b], k) => { if ((1.0 - bestP) * a + bestP * b <= bestV + 1e-9) act.push(k); });
    const neg = act.filter(k => cols[k][1] - cols[k][0] <= 0), pos = act.filter(k => cols[k][1] - cols[k][0] >= 0);
    let q;
    // step 31 (D-298): a level reply that the offence's choice can't make worse (it reads the same real or fake:
    // holding by position) is taken outright. Step 29 took the first on the list, which could be the gamble.
    const flat = act.filter(k => Math.abs(cols[k][1] - cols[k][0]) <= 1e-9);
    if (flat.length) q = [[flat[0], 1.0]];
    else if (bestP <= 0) q = [[(neg.length ? neg : act)[0], 1.0]];
    else if (bestP >= 1) q = [[(pos.length ? pos : act)[0], 1.0]];
    else {
      const j1 = neg.find(k => cols[k][1] - cols[k][0] < 0), j2 = pos.find(k => cols[k][1] - cols[k][0] > 0);
      if (j1 === undefined || j2 === undefined) q = [[act[0], 1.0]];
      else { const s1 = cols[j1][1] - cols[j1][0], s2 = cols[j2][1] - cols[j2][0], w = s2 / (s2 - s1); q = [[j1, w], [j2, 1.0 - w]]; }
    }
    return [bestV, bestP, q];
  }
  // search.reset_candidates, reset_choice (D-276): each open square within 3, arrow toward the shooter, or staying as he is
  function resetCandidates(s) {       // staying, and where the map's settlement sends him (or the open square within 3 nearest it)
    const j = s.reset, acts = resetActions(s);
    const stay = acts.find(a => a.dest === s.x[j] && a.arrow === s.arrows[j]);
    const out = [stay];
    const mv = new Read(W_(s, { stage: 'play', side: 'X', reset: -1 })).mapSettle().filter(z => z[0] === j).slice(0, 1);
    for (const [, q, a0] of mv) {
      const ar = (a0 === null || a0 === undefined || a0 < 0) ? s.arrows[j] : a0;
      let to = null, tk = null;
      for (const a of acts) {
        if (a.arrow !== ar) continue;
        const d = a.dest, k = [cheb(d, q), Math.abs(SX[d] - SX[q]) + Math.abs(SY[d] - SY[q]), SX[d], SY[d]];
        if (tk === null || k[0] < tk[0] || (k[0] === tk[0] && (k[1] < tk[1] || (k[1] === tk[1] && (k[2] < tk[2] || (k[2] === tk[2] && k[3] < tk[3])))))) { to = d; tk = k; }
      }
      if (to === null) continue;
      const a = acts.find(x => x.dest === to && x.arrow === ar);
      if (a !== stay) out.push(a);
    }
    return out;
  }
  function resetChoice(s, value) {
    let best = null;
    for (const a of resetCandidates(s)) { const v = value(apply(s, a)); if (best === null || v < best[0] - 1e-12) best = [v, a]; }
    return best[1];
  }
  function candidateActions(s, read, perPlayer = 3) {
    if (s.stage === 'reset') return resetCandidates(s);                       // D-276: to the squares that matter (step 30)
    const acts = legalActions(s).filter(a => !isFake(a)), side = actor(s);      // D-272: a fake is read as the mix at the declaration
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
      // step 22 (D-212): the moves that start the map's own threats are always tried, so the search sees what the
      // map reads (step 21 saw the computer pick moves its own map read as worse: the offence's reply it was judged
      // against missed the map's threat)
      if (mapOn() && s.ctx.digital && s.stage === 'play' && !s.pending) {
        for (const t of read.mapThreats()) {
          if (t.q0 === undefined) continue;
          for (const a of acts) {
            if (t.a === s.ball ? (MOVEMENT.has(a.kind) && a.piece === t.a && a.dest === t.q0)
              : t.q0 === s.o[t.a] ? (a.kind === 'pass' && a.target === t.a) : (MOVEMENT.has(a.kind) && a.piece === t.a && a.dest === t.q0)) add(a);
          }
        }
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
      // step 21 (D-207): the map's own best answer is always among the moves tried: each of its movements as the rules
      // allow it (a Move to its square, every arrow; a Quick Step or Sprint to its square with its arrow). The answer
      // matches all five defenders against every look on the board, so no defender is tied to a man and a switch is
      // simply the answer that leaves the least
      if (mapOn() && s.ctx.digital && s.stage === 'play' && !s.pending) {
        // (a Quick Step or Sprint is matched by the arrow it really leaves him, as the rules apply it)
        for (const [d, q, ar] of read.mapAnswer()) for (const a of moves) {
          if (a.piece !== d || a.dest !== q) continue;
          if (ar < 0 ? a.kind === 'move' : a.kind !== 'move' && apply(s, a).arrows[d] === ar) add(a);
        }
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
  // ---- step 18f (search.whole_turns; search.ended_turn in search.py) -------------------------------------------------
  // A one-action turn is valued as the turn ended there: the side's own End turn is played, so the other side has the
  // reply the rules give it before the position is judged. (The computer plays one action and then decides again, so
  // "this action, then stop" is what the turn is worth at least.) n: the node a turn from s leads to.
  // step 18f (eval.kept_actions; decide.kept_on): a defender's answer is read by what he has left. The cover's
  // re-read of a defender moved to a square took his control as it stands now; with the switch on, an answer by a
  // Quick Step or a Sprint is rushed and one by a Move is set, as the control rule says (and the open list's re-read
  // of a defender stepping into the ball handler's way reads the handler's looks the same way).
  const keptOn = () => D.config.eval.kept_actions === true;
  function setKeptActions(v) { D.config.eval.kept_actions = v === true || v === 'true'; READS = new Map(); READS_OLD = new Map(); return D.config.eval.kept_actions; }
  // step 18f (search.split_ties; Searcher.split_ties in search.py): turns that read exactly the same are separated
  // by evidence the search already has: after the other side's best reply, how good its next-best replies are. The
  // turn that leaves it the fewest good replies comes first. (Chance, the pick noise, then doesn't choose between
  // them: the tools and the agent give turns that read the same one draw.)
  const splitOn = () => (D.config.search || {}).split_ties === true;
  function setSplitTies(v) { D.config.search = D.config.search || {}; D.config.search.split_ties = v === true || v === 'true'; return D.config.search.split_ties; }
  const wholeOn = () => (D.config.search || {}).whole_turns === true;
  // step 18f (search.rank_in_hand, off): with whole turns, a turn's first actions are ranked, and the ones to follow
  // with a second action chosen, by the reading with the second action still in hand (as before whole turns). The
  // search still values a one-action turn as the turn ended. Ranked as ended turns, a first action that only pays
  // with its second (move, then shoot) was not followed, and the other side's search never saw it.
  const inHandOn = () => (D.config.search || {}).rank_in_hand === true;
  // ---- step 18j (search.dice_in_hand, eval.ball_loss; search.py): seeing a Steal that a movement sets up ---------------
  const DICE = new Set(['steal', 'challenge', 'intercept']);
  const diceInHandOn = () => (D.config.search || {}).dice_in_hand === true;
  const ballLossOn = me => { const v = D.config.eval.ball_loss; return v === true || (v === 'offence' && me === 'O'); };   // 'offence': only when the offence is the one choosing
  const keepSettledOn = () => (D.config.search || {}).keep_settled === true;
  // step 18k (search.keep_in_hand): in the defence's list two turns are not copies when they leave a defender
  // different things he can still do this phase
  const keepInHandOn = () => { const v = (D.config.search || {}).keep_in_hand; return v === true || v === 'moves'; };   // 'moves': without the Steal in hand
  function setKeepInHand(v) { D.config.search = D.config.search || {}; D.config.search.keep_in_hand = v === 'moves' ? 'moves' : (v === true || v === 'true'); return D.config.search.keep_in_hand; }
  function setKeepSettled(v) { D.config.search = D.config.search || {}; D.config.search.keep_settled = v === true || v === 'true'; return D.config.search.keep_settled; }
  function setDiceInHand(v) { D.config.search = D.config.search || {}; D.config.search.dice_in_hand = v === true || v === 'true'; return D.config.search.dice_in_hand; }
  function setBallLoss(v) { D.config.eval.ball_loss = v === 'offence' ? 'offence' : (v === true || v === 'true'); return D.config.eval.ball_loss; }
  // search.faces_attacker: a defender standing on q with arrow a (as defender j's stance reads it), next to an attacker with an arrow on him
  function facesAttacker(s, j, q, a) {
    const st = stanceOf(s, j, a);
    for (let i = 0; i < 5; i++) { const op = s.o[i]; if (ONB[op] && adjacent(q, op) && onLine(st, dirBetween(q, op))) return true; }
    return false;
  }
  // search.steal_spot: where defender j can try a Steal from within one turn, and his arrow there: [square, arrow] or null
  function stealSpot(s, j) {
    const xp = s.x[j], bh = s.o[s.ball], st = stanceOf(s, j);
    if (st >= 16) return null;
    if (adjacent(xp, bh) && onLine(st, dirBetween(xp, bh))) return [xp, s.arrows[j]];
    if (s.tok_x < 2) return null;
    if (canMoveKind(s, 'X', j, 'move')) {
      const dests = movementDests(s, 'X', j, 'move');
      let bk = -1, bq = -1, bd = -1;
      for (let d = 0; d < 8; d++) {
        const q = bh - DSTEP[d];
        if (!ONB[q]) continue;
        if (q === xp || dests.has(q)) { const k = (DR[q] >= DR[bh] ? 8 : 0) + d; if (bk < 0 || k < bk) { bk = k; bq = q; bd = d; } }
      }
      if (bk >= 0) return [bq, bd];
    }
    if (canMoveKind(s, 'X', j, 'qs') && s.ctx.dfn[j].qs > 0) {
      let dests = null;
      const ls = st >= 8 ? [st - 8, (st - 7) % 8] : [st];
      for (const d of ls) {
        const q = bh - DSTEP[d];
        if (!ONB[q]) continue;
        if (dests === null) dests = movementDests(s, 'X', j, 'qs');
        if (dests.has(q)) return [q, s.arrows[j]];
      }
    }
    return null;
  }
  function setRankInHand(v) { D.config.search = D.config.search || {}; D.config.search.rank_in_hand = v === true || v === 'true'; return D.config.search.rank_in_hand; }
  function setWholeTurns(v) { D.config.search = D.config.search || {}; D.config.search.whole_turns = v === true || v === 'true'; return D.config.search.whole_turns; }
  function endedTurn(s, n) {
    if (isChance(n) || s.stage !== 'play' || n.stage !== 'play' || n.pending || n.turn_n === 0) return n;
    const side = actor(s);
    if (actor(n) !== side) return n;
    return apply(n, A('end_turn', side));
  }
  // ---- step 18e (search.open_list, D-156; search.open_turns in search.py) ------------------------------------------
  // The list of turns without the hand-written choice of which actions to consider (candidateActions): every legal
  // action is read, and only the reading decides what goes forward. No kind of action is named, kept or preferred.
  // The defence in open play: reading every legal action in full costs too much (about 1,000 actions a position), so
  //   1. every legal first action gets a cheap read: the looks of the position the turn leaves when it ends, with
  //      every piece where it stands (nullStep, twice when the turn has two actions), re-read with that one defender
  //      where the action leaves him (Read.reread), and the quick reading taken from them. An action that leaves
  //      every piece where it stands, goes to the dice or keeps a pass in the air has no such re-read and is read in
  //      full at once;
  //   2. every pair of those actions by two defenders is read the same way, each attacker's best look being the
  //      lower of the two re-reads (the rule the reading's own cover uses). A second action is only read as part of
  //      a turn if the reading says it changes something;
  //   3. after each of the best `follow` first actions, every other legal second action is read: the same defender
  //      moving again by a re-read where it leaves him; anything that goes to the dice by its chances, a possession
  //      that ends at its own value and one that plays on at the first action's reading;
  //   4. actions the cheap read can't tell apart are one candidate (the first in the rules' order);
  //   5. the best `full` candidates by the cheap read are read in full (the ordering reading every turn gets today),
  //      and the best `beam` of those are the list.
  // Elsewhere (a declared shot's reaction, and the offence under 'both'): every legal action is read in full.
  // The switch: search.open_list (false, 'defence' or 'both') when it is set; when it is null, the level's own setting
  // (profiles.<level>.open_list). The All-Star plays 'defence' by default (step 18e); the Rookie and Starter don't.
  function openMode(profile) { const g = (D.config.search || {}).open_list; return g === null || g === undefined ? ((profile && profile.open_list) || false) : g; }
  // search.open_width: how many turns a level reads in full, and how many first actions it follows (step 18f, D-157:
  // the levels think the same way and differ in how well they choose): the level's own, or the config's
  function openWidth(profile) {
    const cfg = D.config.search || {}, p = profile || {};
    const full = p.open_full != null ? p.open_full : cfg.open_full, follow = p.open_follow != null ? p.open_follow : cfg.open_follow;
    return [full == null ? 8 : full, follow == null ? 4 : follow];
  }
  function openOn(side, mode) { const v = mode === undefined ? openMode(null) : mode; return v === true || v === 'both' || (v === 'defence' && side === 'X'); }
  function setOpenList(v) { D.config.search = D.config.search || {}; D.config.search.open_list = v === 'true' ? true : v === 'false' ? false : (v === 'null' || v === undefined) ? null : v; return D.config.search.open_list; }
  const OPEN_STATS = { calls: 0, legal: 0, unique: 0, pairs: 0, followed: 0, full: 0 };
  // The turn as one action of the defence leaves it (the token spent, a pass in the air landed, whose action it is,
  // the phase), with every piece where it stands: the position the cheap re-reads are made from (apply's own steps
  // for a movement, without the movement).
  function nullStep(state) {
    let s = spend(state, 'X');
    if (s.pending && !isInboundPass(state)) { const ph = s.phase; s = completePass(s); if (s.phase !== ph) return s; }
    return after(state, s, 'X', 'move');
  }
  function openTurnsX(s, beam, read, evaluate, deadline, expand, whole, width) {
    const acts = legalActions(s);
    if (acts.length <= 12) return null;
    const ref1 = nullStep(s);
    if (isChance(ref1) || ref1.stage !== 'play') return null;
    const two = !endsTurn(s, ref1, 'X');
    const ref2 = two ? nullStep(ref1) : null;
    if (two && (isChance(ref2) || ref2.stage !== 'play')) return null;
    const cfg = D.config.search || {};
    const nexp = expand != null ? expand : Math.max(3, Math.floor(beam / 3));
    const wd = width || openWidth(null), K = beam + nexp * wd[0], F = nexp * wd[1];
    // one read to re-read from: the position the turn leaves when it ends (two actions on, or one if that ends it)
    const ref = two ? ref2 : ref1, R = readOf(ref);
    const att = R.att_o, b2 = bankedOf(ref);
    const qm = new Map(), parts = !!partsMap(ref), lane = laneOn();
    const Qof = vec => {                                 // the quick reading from a re-read (the same arithmetic, kept by its inputs)
      const cont = R._contOf(vec);
      let k = cont + '|' + vec[5] + '|' + vec[6];
      if (lane) k += '|' + vec[7] + '|' + vec[8] + '|' + vec[9];      // step 18q: the lane's values, re-read
      if (parts) { const t2 = topTwo(att, i => vec[i]); k += '|' + t2[0] + '|' + t2[1]; }      // step 18h: the parts the reading keeps
      let v = qm.get(k);
      if (v === undefined) { v = R._quickCont(cont, vec[5], vec[6], vec); qm.set(k, v); }
      return v;
    };
    // what the quick reading is taken from, before the phase table's floor and the map flatten it: the best shot that
    // can go up now, or what the best looks leave. The cheap rank's second key (the reading at a finer grain).
    const rawOf = vec => (lane && vec[7] > 0) ? round6(Math.max(vec[5], vec[6], R._contOf(vec), R.cfg.continuation * vec[7])) : round6(Math.max(vec[5], vec[6], R._contOf(vec)));
    // the cheap read of defender j where the state n leaves him; what he has left and his control are read from
    // `left` (n itself, or the position two actions leave when the turn's end resets them)
    const facts = (n, j, vec, left) => {
      const q = n.x[j], a = n.arrows[j], cp = caps(left, 'X', j);
      R.reread(j, q, a, cp[0], cp[1], (rushedX(left, j) ? 2 : 0) | (hasMoved(left, 'X', j) ? 4 : 0), vec);
    };
    const fresh = ref.phase !== s.phase;                  // the turn's end ends the phase: every defender starts the next anew
    const tieOf = vec => { let t = 0.0; for (const i of att) t += vec[i]; if (lane && vec[7] > 0) t += vec[7]; return round6(t); };
    const keyOf = (c, vec) => { let k = c + '|' + round6(vec[5]) + '|' + round6(vec[6]); for (const i of att) k += '|' + round6(vec[i]); if (lane) k += '|' + round6(vec[7]) + '|' + round6(vec[8]) + '|' + round6(vec[9]); return k; };
    const full = [], U = [], seen = new Set();
    // (a speed-up that changes no result: most actions re-read bit for bit like one before them; those are dropped
    // before anything is built for them. tmp: the re-read in hand; bits: its bits, for a number to find its like by)
    const tmp = new Float64Array(10), bits = new Uint32Array(tmp.buffer), same = new Map();
    tmp[7] = -1.0; tmp[8] = -1.0;
    OPEN_STATS.calls++; OPEN_STATS.legal += acts.length;
    // 1. every legal first action
    // (a speed-up that changes no result, SPEED.open_facts: with no pass in the air, where a movement leaves a
    // defender and what he has left follow from the action itself, as apply() and caps() give them, so the action
    // needn't be played to be re-read)
    const direct = SPEED.open_facts && !s.pending;
    const hand = diceInHandOn() && two;                   // step 18j (search.dice_in_hand)
    const inHandV = (nd, q2) => {
      if (isChance(nd)) { let v = 0.0; for (const o of nd.outcomes) v += o[0] * inHandV(o[2], q2); return v; }
      if (nd.stage === 'over') return terminalValue(nd);
      return q2 + bankedOf(nd) - b2;
    };
    const cap0 = [0, 1, 2, 3, 4].map(j => [hasMoved(s, 'X', j), isLocked(s, 'X', j), quickStepped(s, 'X', j)]);
    const qsCount = count(s, 'X', 'qs'), ctl = controlOn(s.ctx);
    // step 18k (search.keep_in_hand): what a first action leaves its mover able to do this phase: whether he can still
    // Move, still Quick Step, is set or rushed, and a Steal: 1 if he can roll one from where he stands (next to the
    // ball handler with an arrow on him), 2 if a movement he has left gets him there by its shape (onto a free square
    // next to the ball handler, facing him: a Move turns him as he likes, a Quick Step keeps his arrow), 0 if not
    const kih = keepInHandOn() && two;
    let bhq = -1, mvr = null, qsr = null, code0 = null;
    const stealCode = (j, q, ar, canMove, qsLeft) => {
      if (bhq < 0) return 0;
      const st = stanceOf(s, j, ar);
      if (st >= 16) return 0;
      if (adjacent(q, bhq) && onLine(st, dirBetween(q, bhq))) return 1;
      if (canMove && mvr.has(q)) return 2;
      if (qsLeft > 0 && qsr[j]) { const ls = st >= 8 ? [st - 8, (st - 7) % 8] : [st]; for (const d of ls) if (qsr[j][d] && qsr[j][d].has(q)) return 2; }
      return 0;
    };
    const sigOf = (canMove, qsLeft, rushed, code) => (canMove ? 1 : 0) | (qsLeft > 0 ? 2 : 0) | (rushed ? 4 : 0) | (code << 3);
    if (kih && (D.config.search || {}).keep_in_hand === true && ONB[s.o[s.ball]]) {
      bhq = s.o[s.ball];
      const occ = new Set(); for (let i = 0; i < 5; i++) { occ.add(s.o[i]); occ.add(s.x[i]); }
      const ends = (paths, into) => { for (const path of paths) { let ok = true; for (const sq of path) if (!ONB[sq]) { ok = false; break; } if (ok) into.add(path[path.length - 1]); } };
      mvr = new Set(); qsr = [0, 1, 2, 3, 4].map(j => (s.ctx.dfn[j].qs > 0 ? [] : null));
      for (let d = 0; d < 8; d++) {
        const q = bhq - DSTEP[d];
        if (!ONB[q] || occ.has(q)) continue;
        ends(movePaths(q), mvr);                        // (a movement's shape is the same both ways)
        for (let j = 0; j < 5; j++) if (qsr[j]) { qsr[j][d] = new Set(); ends(qsPaths(q, s.ctx.dfn[j].qs), qsr[j][d]); }
      }
      code0 = [0, 1, 2, 3, 4].map(j => { const cp = caps(s, 'X', j); return stealCode(j, s.x[j], s.arrows[j], cp[0], cp[1]); });
    }
    const refCaps = fresh ? [0, 1, 2, 3, 4].map(j => [caps(ref, 'X', j), (rushedX(ref, j) ? 2 : 0) | (hasMoved(ref, 'X', j) ? 4 : 0)]) : null;
    for (const a of acts) {
      if (deadline && now() > deadline) throw TIMEOUT;
      let sg = 0, scode = 0;                             // step 18k: what the action leaves its mover in hand
      if (direct && a.dest >= 0) {
        const j = a.piece, k = a.kind;
        let ar = s.arrows[j];
        if (k === 'move') ar = a.arrow;
        else if (k === 'sprint') { if (a.arrow >= 0) ar = a.arrow; else { const st = s.x[j], dx = SX[a.dest] - SX[st], dy = SY[a.dest] - SY[st], n = Math.max(Math.abs(dx), Math.abs(dy)); ar = STEPDIR.get((dx / n) * WID + dy / n); } }
        if (fresh) {
          R.reread(j, a.dest, ar, refCaps[j][0][0], refCaps[j][0][1], refCaps[j][1], tmp);
          if (kih) { scode = stealCode(j, a.dest, ar, refCaps[j][0][0], refCaps[j][0][1]); sg = sigOf(refCaps[j][0][0], refCaps[j][0][1], refCaps[j][1] & 2, scode); }
        } else {
          const mv = cap0[j][0] || k !== 'qs', qd = cap0[j][2] || k !== 'move';
          const left = LIMITS.X.qs - qsCount - (k === 'move' ? 0 : 1);
          const cm = !mv && !cap0[j][1], ql = qd ? 0 : Math.min(left, 1), fl = (ctl ? (k === 'move' ? 0 : 2) : 0) | (mv ? 4 : 0);
          R.reread(j, a.dest, ar, cm, ql, fl, tmp);
          if (kih) { scode = stealCode(j, a.dest, ar, cm, ql); sg = sigOf(cm, ql, fl & 2, scode); }
        }
      } else {
      const nxt = apply(s, a);
      if (isChance(nxt) || nxt.stage !== 'play' || nxt.pending || !(a.dest >= 0)) { full.push([-evaluate(whole ? endedTurn(s, nxt) : nxt), [a]]); continue; }
      facts(nxt, a.piece, tmp, fresh ? ref : nxt);
      if (kih) { const lf = fresh ? ref : nxt, cp = caps(lf, 'X', a.piece); scode = stealCode(a.piece, nxt.x[a.piece], nxt.arrows[a.piece], cp[0], cp[1]); sg = sigOf(cp[0], cp[1], rushedX(lf, a.piece), scode); }
      }
      // step 18j: a first action that leaves its mover next to an attacker with an arrow on him is never dropped as a
      // copy of another, and is ranked with whatever he can then send to the dice
      let har = -1, hnx = null, hdice = null;
      if (hand) {
        const j = a.piece, k = a.kind;
        let ar = s.arrows[j];
        if (k === 'move') ar = a.arrow;
        else if (k === 'sprint') { if (a.arrow >= 0) ar = a.arrow; else { const st = s.x[j], dx = SX[a.dest] - SX[st], dy = SY[a.dest] - SY[st], n = Math.max(Math.abs(dx), Math.abs(dy)); ar = STEPDIR.get((dx / n) * WID + dy / n); } }
        if (facesAttacker(s, j, a.dest, ar)) {
          hnx = apply(s, a); hdice = defenceActions(hnx, DICE).filter(b => b.piece === j);
          if (hdice.length) har = ar;                     // (if he can send nothing to the dice, it is read like any other action)
        }
      }
      let h = a.piece;
      for (let w = 0; w < 20; w++) h = (Math.imul(h, 16777619) ^ bits[w]) | 0;
      let bucket = same.get(h), dup = false;
      if (bucket === undefined) { bucket = []; same.set(h, bucket); }
      else if (har < 0) for (const o of bucket) { if (o.j === a.piece && o.sg === sg && o[0] === tmp[0] && o[1] === tmp[1] && o[2] === tmp[2] && o[3] === tmp[3] && o[4] === tmp[4] && o[5] === tmp[5] && o[6] === tmp[6] && o[7] === tmp[7] && o[8] === tmp[8] && o[9] === tmp[9]) { dup = true; break; } }
      if (dup) continue;
      const v2 = Float64Array.from(tmp);
      v2.j = a.piece; v2.sg = sg; if (har < 0) bucket.push(v2);       // (a dice-in-hand action never stands in for a later copy)
      const q2 = Qof(v2);
      let c = round6(q2), ukey = keyOf(c, v2);
      if (har >= 0) {
        for (const b of hdice) c = Math.min(c, round6(inHandV(apply(hnx, b), q2)));
        ukey += '|h|' + a.dest + '|' + har;
      }
      if (kih) ukey += '|g' + sg;                        // step 18k: not a copy of an action that leaves him something else in hand
      const u = { turn: [a], j: a.piece, c, raw: rawOf(v2), tie: tieOf(v2), key: ukey, v2, q2, sg, adds: kih && code0 !== null && scode > code0[a.piece] };
      if (seen.has(u.key)) continue;                     // the same by this read as an action before it
      seen.add(u.key);
      U.push(u);
    }
    const byCheap = (x, y) => (x.c - y.c) || (x.raw - y.raw) || (x.tie - y.tie) || (x.turn.length - y.turn.length) || (x.n - y.n);
    U.forEach((u, n) => { u.n = n; });
    U.sort(byCheap);
    OPEN_STATS.unique += U.length;
    const C = U.slice();
    let n = U.length;
    if (two) {
      // 2. every pair of them by two defenders
      const m = new Float64Array(10);
      m[7] = -1.0; m[8] = -1.0;
      for (let x = 0; x < U.length; x++) {
        const ua = U[x];
        if (deadline && now() > deadline) throw TIMEOUT;
        for (let y = x + 1; y < U.length; y++) {
          const ub = U[y];
          if (ub.j === ua.j) continue;
          let lt = false, gt = false;
          for (const i of att) { const va = ua.v2[i], vb = ub.v2[i]; if (vb < va) { lt = true; m[i] = vb; } else { if (va < vb) gt = true; m[i] = va; } }
          for (let i = 5; i < (lane ? 10 : 7); i++) { const va = ua.v2[i], vb = ub.v2[i]; if (vb < va) { lt = true; m[i] = vb; } else { if (va < vb) gt = true; m[i] = va; } }
          // one of the two changes nothing the other doesn't: not read as a pair (step 18k: putting a Steal in hand
          // that the defender didn't have is a change)
          if (!((lt || ub.adds) && (gt || ua.adds))) continue;
          const c = round6(Qof(m));
          const pk = kih ? (ua.j < ub.j ? '|' + ua.j + ':' + ua.sg + ',' + ub.j + ':' + ub.sg : '|' + ub.j + ':' + ub.sg + ',' + ua.j + ':' + ua.sg) : '';
          C.push({ turn: [ua.turn[0], ub.turn[0]], j: -1, c, raw: rawOf(m), tie: tieOf(m), key: keyOf(c, m) + '|p' + pk, pair: true, n: n++ });
        }
      }
      OPEN_STATS.pairs += C.length - U.length;
      // 3. after the best first actions: the same defender again, and whatever goes to the dice
      const cheapNode = (nd, u) => {
        if (isChance(nd)) { let v = 0.0; for (const o of nd.outcomes) v += o[0] * cheapNode(o[2], u); return v; }
        if (nd.stage === 'over') return terminalValue(nd);
        return u.q2 + bankedOf(nd) - b2;
      };
      let followed = 0;
      for (const ua of U) {
        if (followed >= F) break;
        if (deadline && now() > deadline) throw TIMEOUT;
        followed++;
        const a = ua.turn[0], nxt = apply(s, a);
        for (const b of legalActions(nxt)) {
          if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;     // ending here is the one-action turn
          if (b.dest >= 0 && b.piece !== ua.j) continue;  // two defenders moving: read with the pairs above
          const n2 = apply(nxt, b);
          if (!isChance(n2) && n2.stage === 'play' && !n2.pending && b.dest >= 0) {
            const v = new Float64Array(10);
            facts(n2, ua.j, v, n2);
            const c = round6(Qof(v));
            let gk = '';
            if (kih) { const cp = caps(n2, 'X', ua.j); gk = '|g' + sigOf(cp[0], cp[1], rushedX(n2, ua.j), stealCode(ua.j, n2.x[ua.j], n2.arrows[ua.j], cp[0], cp[1])); }
            C.push({ turn: [a, b], j: ua.j, c, raw: rawOf(v), tie: tieOf(v), key: keyOf(c, v) + '|s' + ua.j + gk, n: n++ });
          } else {
            const c = round6(cheapNode(n2, ua));
            C.push({ turn: [a, b], j: ua.j, c, raw: rawOf(ua.v2), tie: tieOf(ua.v2), key: keyOf(c, ua.v2) + '|d' + b.id, n: n++ });
          }
        }
      }
      OPEN_STATS.followed += followed;
    }
    // 4, 5. one candidate for each distinct read; the best by the cheap read are read in full
    C.sort(byCheap);
    if (OPEN_STATS.debug) OPEN_STATS.debug({ C, U, R, ref, full: full.slice() });
    const legalAfter = new Map(), seenC = new Set();
    const idsAfter = a => { let r = legalAfter.get(a.id); if (!r) { const nx = apply(s, a); r = new Set(isChance(nx) ? [] : legalActions(nx).map(b => b.id)); legalAfter.set(a.id, r); } return r; };
    let done = 0;
    for (const u of C) {
      if (done >= K) break;
      if (deadline && now() > deadline) throw TIMEOUT;
      let turn = u.turn;
      if (turn.length === 2) {
        if (seenC.has(u.key)) continue;
        if (u.pair && !idsAfter(turn[0]).has(turn[1].id)) {     // two defenders: the rules say which order is legal
          if (!idsAfter(turn[1]).has(turn[0].id)) continue;
          turn = [turn[1], turn[0]];
        }
        seenC.add(u.key);
      }
      { const nd = playTurn(s, turn); full.push([-evaluate(whole ? endedTurn(s, nd) : nd), turn]); }
      done++;
    }
    OPEN_STATS.full += full.length;
    full.sort((x, y) => y[0] - x[0]);
    const seenT = new Set(), fin = [];
    for (const [v, tn] of full) {
      const key = tn.length === 2 && MOVEMENT.has(tn[0].kind) && MOVEMENT.has(tn[1].kind) ? 'S' + [tn[0].id, tn[1].id].sort((p, q) => p - q).join(',') : 'T' + turnKey(tn);
      if (seenT.has(key)) continue;
      seenT.add(key); fin.push([v, tn]);
      if (fin.length >= beam) break;
    }
    return fin;
  }
  function turns(s, beam, read, evaluate, deadline, expand, second, mode, whole, width) {      // mode: the level's open list (openMode); whole: search.whole_turns
    const side = actor(s), sign = side === 'O' ? 1 : -1;
    const open = openOn(side, mode) && !!evaluate;
    if (open && side === 'X' && s.stage === 'play') { const r = openTurnsX(s, beam, read, evaluate, deadline, expand, whole, width); if (r) return r; }
    const first = open ? legalActions(s) : candidateActions(s, read);
    const scored = [], inHand = inHandOn();
    // step 18j (search.keep_settled): a turn the rules settle outright is never cut for turns that only read higher
    const keep = keepSettledOn() && s.stage === 'play' && !!evaluate, exact = new Set();
    for (const a of first) {
      if (deadline && now() > deadline) throw TIMEOUT;
      const nxt = apply(s, a);
      scored.push([sign * (evaluate ? evaluate(whole && !inHand ? endedTurn(s, nxt) : nxt) : 0.0), [a]]);
      if (keep && !isChance(nxt) && nxt.stage !== 'play') exact.add(turnKey([a]));
    }
    scored.sort((x, y) => y[0] - x[0]);
    const out = scored.slice(0, beam);
    if (exact.size) for (const r of scored.slice(beam)) if (exact.has(turnKey(r[1]))) out.push(r);
    const nexp = expand != null ? expand : Math.max(3, Math.floor(beam / 3));
    for (const [, t] of scored.slice(0, nexp)) {
      const a = t[0], nxt = apply(s, a);
      if (endsTurn(s, nxt, side)) continue;
      for (const b of (open ? legalActions(nxt) : candidateActions(nxt, null, second))) {
        if (deadline && now() > deadline) throw TIMEOUT;
        if (b.kind === 'end_turn' || b.kind === 'forfeit') continue;
        const n2 = apply(nxt, b);
        out.push([sign * (evaluate ? evaluate(n2) : 0.0), [a, b]]);
        if (keep && !isChance(n2) && n2.stage !== 'play') exact.add(turnKey([a, b]));
      }
    }
    out.sort((x, y) => y[0] - x[0]);
    const seen = new Set(), fin = [];
    for (const [v, t] of out) {
      const key = t.length === 2 && MOVEMENT.has(t[0].kind) && MOVEMENT.has(t[1].kind) ? 'S' + [t[0].id, t[1].id].sort((p, q) => p - q).join(',') : 'T' + turnKey(t);
      if (seen.has(key)) continue;
      if (fin.length >= beam) {
        if (!exact.size) break;
        if (!exact.has(turnKey(t))) continue;
        // the best settled turn takes the place of the lowest-reading turn, unless a settled turn is already on the list
        if (!fin.some(x => exact.has(turnKey(x[1])))) fin[fin.length - 1] = [v, t];
        break;
      }
      seen.add(key); fin.push([v, t]);
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
      this.ballLoss = ballLossOn(me); this.xcache = new Map();    // step 18j (eval.ball_loss)
      this.open = openMode(profile);                            // step 18e (search.open_list, or the level's own)
      this.twice = !!(profile && profile.closeout_twice);       // step 18n: a second closeout movement in a settled reaction
      this.whole = wholeOn();                                   // step 18f (search.whole_turns)
      this.split = splitOn(); this.spread = new Map();          // step 18f (search.split_ties): a reply node's values, best first
      this.width = openWidth(profile);                          // step 18f: how many turns this level reads in full
    }
    check() { if (now() > this.deadline) throw TIMEOUT; }
    playT(s, t) { const n = playTurn(s, t); return this.whole ? endedTurn(s, n) : n; }   // a turn played, ended if it is one action (step 18f)
    leaf(s, z) {
      this.leaves++;
      if (this.settleShots && !isChance(s) && s.stage !== 'play' && s.stage !== 'over') return this.settled(s, z);
      const key = z === undefined ? zobrist(s) : z;
      let v = this.lcache.get(key);
      if (v === undefined) { v = this.evaluate(s); this.lcache.set(key, v); }
      if (this.help && !isChance(s) && s.stage === 'play' && !s.pending && actor(s) === 'O') v = this.floor(s, v, key);   // step 18c
      if (this.ballLoss && !isChance(s) && s.stage === 'play' && !s.pending && actor(s) === 'X' && s.turn_n === 0 && !s.inbound) v = this.loss(s, v, key);   // step 18j
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
    // search.Searcher.loss (step 18j, eval.ball_loss): the defence to act with a whole turn in hand: the position is worth no
    // more than what its best Steal leaves, counting a defender who can still get next to the ball handler with an arrow
    // on him, the Steal settled by the rules' own chances
    loss(s, v, key) {
      const hit = this.xcache.get(key);
      if (hit !== undefined) return hit;
      let best = v;
      if (s.tok_x > 0 && count(s, 'X', 'steal') < LIMITS.X.steal && ONB[s.o[s.ball]]) {
        const b0 = bankedOf(s);
        const worth = nd => {
          if (isChance(nd)) { let t = 0.0; for (const o of nd.outcomes) t += o[0] * worth(o[2]); return t; }
          if (nd.stage === 'over') return terminalValue(nd);
          return v + bankedOf(nd) - b0;
        };
        for (let j = 0; j < 5; j++) {
          const spot = stealSpot(s, j);
          if (spot === null) continue;
          const st = (spot[0] === s.x[j] && spot[1] === s.arrows[j]) ? s : W_(s, { x: setAt(s.x, j, spot[0]), arrows: setAt(s.arrows, j, spot[1]) });
          const w = worth(apply(st, A('steal', 'X', j)));
          if (w < best) best = w;
        }
      }
      this.xcache.set(key, best);
      return best;
    }
    floor(s, v, z) {
      const key = z === undefined ? zobrist(s) : z;
      const hit = this.fcache.get(key);
      if (hit !== undefined) return hit[0];
      let banked = 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0);
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
        const sp = s.o[s.ball];
        // D-191 (search.Searcher.settled): position decides the contest, so both of the reaction's actions may be
        // movements; only one that ends next to the shooter is played, a Move only with its arrow on him
        // a level with closeout_twice (the All-Star) plays a second such movement; the others stop at one, as before
        if (s.ctx.pos && !s.ctx.cc && (s.turn_n === 0 || this.twice)) acts = legalActions(s).filter(a => !MOVEMENT.has(a.kind) || (adjacent(a.dest, sp) && (a.kind !== 'move' || a.arrow === dirBetween(a.dest, sp))));
        else if (s.turn_n >= 1) acts = forcingActions(s, 'stage');
        else acts = legalActions(s).filter(a => !MOVEMENT.has(a.kind) || adjacent(a.dest, sp));
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
      if (n.stage === 'reset') return this.leaf(apply(n, resetChoice(n, m => this.quick(m))));   // D-276: as at the horizon
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
      if (depth >= 1 && fakeWorld(s)) return this.mixed(s, depth);           // D-272: the hidden choice, read as the mixed game
      if (depth <= 0 && s.stage === 'reset') return this.leaf(apply(s, resetChoice(s, n => this.quick(n))));   // D-276
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
      const rec = this.split && depth === 1 && a0 === VMIN && b0 === VMAX ? [] : null;      // step 18f: its replies' values
      const opponent = side !== this.me;
      const mix = opponent && (this.lam < 1.0 || !!this.habit);
      let passive = null;
      if (mix) {
        const w = ts.filter(r => PASSIVE.has(r[1][0].kind)).map(r => r[1]);
        passive = w.length ? this.value(this.playT(s, w[0]), depth - 1, VMIN, VMAX) : null;
      }
      for (const [, t] of ts) {
        const child = this.playT(s, t);
        const d = (this.quiet && !isChance(child) && child.stage !== 'over' && actor(child) === side && midTurn(child)) ? depth : depth - 1;
        const v = this.value(child, d, mix ? VMIN : alpha, mix ? VMAX : beta);
        if (rec) rec.push(v);
        if (side === 'O') { if (best === null || v > best[0]) best = [v, t]; if (!mix) alpha = Math.max(alpha, v); }
        else { if (best === null || v < best[0]) best = [v, t]; if (!mix) beta = Math.min(beta, v); }
        if (!mix && alpha >= beta) {
          this.killer(depth, t);
          this.history.set(t[0].id, (this.history.get(t[0].id) || 0) + depth * depth);
          break;
        }
      }
      if (rec && rec.length === ts.length) { rec.sort((x, y) => (side === 'O' ? y - x : x - y)); this.spread.set(z, rec); }
      let v = best[0];
      if (mix && passive !== null) v = this.lam * v + (1 - this.lam) * passive;
      if (mix && this.habit) {
        const kind = this.habit[s.stage + '/' + side];
        let hv = null;
        for (const [, t] of ts) if (t[0].kind === kind) { hv = this.value(this.playT(s, t), depth - 1, VMIN, VMAX); break; }
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
        const v = this.value(this.playT(sub, first), depth - 1, VMIN, VMAX);
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
    mixed(s, depth) {                            // search.Searcher.mixed (D-272): never read from the hidden choice
      const [sr, sf] = worlds(s);
      const key = ttKey(zobrist(sr), depth) + ':mix';
      const hit = this.tt.get(key);
      if (hit !== undefined) return hit[0];
      const ts = this.turnsOf(sr);
      if (!ts.length) return this.leaf(sr);
      this.nodes++;
      const cols = this.replyCols(sr, sf, ts, depth).map(c => c[0]);
      const v = mixGame(cols)[0];
      this.tt.set(key, [v, 0, ts[0][1]]);
      return v;
    }
    replyCols(sr, sf, ts, depth) {               // search.Searcher.reply_cols (D-272): whole replies, one real-or-fake choice
      const out = [];
      for (const [, t] of ts) {
        const a = this.playT(sr, t), b = this.playT(sf, t);
        if (!isChance(a) && fakeWorld(a)) {
          const more = this.turnsOf(a);
          if (more.length) {
            for (const [, t2] of more) {
              const a2 = this.playT(a, t2), b2 = this.playT(b, t2);
              out.push([[this.value(a2, this.childDepth(a, a2, depth), VMIN, VMAX), this.value(b2, this.childDepth(b, b2, depth), VMIN, VMAX)], t.concat(t2)]);
            }
            continue;
          }
        }
        out.push([[this.value(a, this.childDepth(sr, a, depth), VMIN, VMAX), this.value(b, this.childDepth(sf, b, depth), VMIN, VMAX)], t]);
      }
      return out;
    }
    _rootMix(s, maxDepth) {                      // search.Searcher._root_mix (D-272)
      const [sr, sf] = worlds(s);
      const budget = this.deadline - now();
      const rootRead = new Read(sr, { exact: budget >= 0.8 });
      const ts = turns(sr, this.p.beam, rootRead, n => this.quick(n), null, budget >= 0.8 ? null : 2, budget >= 0.8 ? 2 : 1, this.open, this.whole, this.width);
      let done = null, reached = 0;
      for (let depth = 1; depth <= Math.max(1, maxDepth); depth++) {
        let cols;
        try { cols = this.replyCols(sr, sf, ts, depth); } catch (e) {
          if (e !== TIMEOUT) throw e;
          if (done === null) done = ts.map(([q, t]) => [[-q, -q], t]);
          break;
        }
        done = cols; reached = depth;
      }
      const p = mixGame(done.map(c => c[0]))[1];
      this.mixCols = done.map(c => c[0].slice());
      return [done.map(([[a, b], t]) => [(1.0 - p) * a + p * b, t]), reached];
    }
    turnsOf(s, z) {
      const key = z === undefined ? zobrist(s) : z;
      let hit = this.tcache.get(key);
      if (hit === undefined) {
        hit = turns(s, this.p.beam, null, n => this.quick(n), this.deadline, 3, 1, this.open, this.whole, this.width);
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
      // step 18h: the level's own map is in force for the length of its search and no longer (search.Searcher.root)
      const prev = D.level === undefined ? null : D.level;
      setLevel(this.p.level);
      MAP_ME = this.me;                              // step 18s, stop two: eval.map 'offence', likewise for the search's length
      try { return this._root(s, maxDepth); } finally { setLevel(prev); MAP_ME = null; if (D.config.eval.map === 'offence') { READS = new Map(); READS_OLD = new Map(); } }
    }
    _root(s, maxDepth) {
      if (fakeWorld(s)) return this._rootMix(s, maxDepth);
      const side = actor(s);
      const budget = this.deadline - now();
      const rootRead = new Read(s, { exact: budget >= 0.8 });
      const ts = turns(s, this.p.beam, rootRead, n => this.quick(n), null, budget >= 0.8 ? null : 2, budget >= 0.8 ? 2 : 1, this.open, this.whole, this.width);
      const deadline = this.deadline; this.deadline = Infinity;
      let results = [];
      const sign = side === 'O' ? 1 : -1;
      ts.forEach(([q, t], k) => {
        if (k >= 3 && now() > deadline) { results.push([sign * q, t]); return; }
        const n = this.playT(s, t);
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
            const n = this.playT(s, t);
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
      results.sort((x, y) => (Math.abs(x[0] - y[0]) > 1e-9 ? byBest(x, y) : tieCmp(x[1], y[1])));   // step 31: level turns in one order, both engines
      // Step 31, Part C: of the turns level with the best, the list breaks the tie before "standing still" does (the
      // design: the list stays as a tie-break). Each such turn's board is read for every look this phase at its chance,
      // best first: the defence takes the turn that leaves the smaller list, the offence the larger. So a defender turns
      // an arrow or steps across when that takes something off a look below the best one, and stands still only when
      // it takes off nothing at all. (A turn that ends in a roll has no one board to read: it keeps its place.)
      if (valueLead() && results.length > 1 && MAP_MEMO !== null) {
        let g = 1; while (g < results.length && Math.abs(results[g][0] - results[0][0]) <= 1e-9) g++;
        if (g > 1) {
          const lists = results.slice(0, g).map(r => { const node = playTurn(s, r[1]); return (!isChance(node) && node.stage === 'play' && !node.pending) ? stanceRead(node).list : null; });
          const sgn = side === 'X' ? 1 : -1, idx = results.slice(0, g).map((_, i) => i);
          const lcmp = (i, j) => {
            const a = lists[i], b = lists[j];
            if (!a || !b) return 0;
            const n = Math.max(a.length, b.length);
            for (let k = 0; k < n; k++) { const x = k < a.length ? a[k] : 0, y = k < b.length ? b[k] : 0; if (Math.abs(x - y) > 1e-9) return sgn * (x - y); }
            return 0;
          };
          idx.sort((i, j) => lcmp(i, j) || (i - j));
          const head = idx.map(i => results[i]);
          for (let i = 0; i < g; i++) results[i] = head[i];
        }
      }
      if (this.split) results = this.splitTies(s, results, side);
      return [results, reached];
    }
    // step 18f: within each run of turns that read the same (results best first), those whose reply node was wholly
    // searched are put in order of the other side's next-best replies, the worst for it first; the rest keep their places
    splitTies(s, results, side) {
      const keyOf = t => {
        const n = this.playT(s, t);
        if (isChance(n) || n.stage === 'over' || actor(n) === side) return null;
        const sp = this.spread.get(zobrist(n));
        return sp ? sp.slice(1).map(v => round6(side === 'O' ? -v : v)) : null;
      };
      const less = (a, b) => { const n = Math.min(a.length, b.length); for (let k = 0; k < n; k++) if (a[k] !== b[k]) return a[k] - b[k]; return a.length - b.length; };
      const out = results.slice();
      let i = 0;
      while (i < out.length) {
        let j = i + 1;
        while (j < out.length && Math.abs(out[j][0] - out[i][0]) < 1e-9) j++;
        if (j - i > 1) {
          const slots = [], items = [];
          for (let k = i; k < j; k++) { const key = keyOf(out[k][1]); if (key) { slots.push(k); items.push([key, items.length, out[k]]); } }
          items.sort((x, y) => less(x[0], y[0]) || (x[1] - y[1]));
          slots.forEach((k, m) => { out[k] = items[m][2]; });
          if (i === 0) {                                 // a measure only: how many turns still read the same as the first
            const k0 = slots.length && slots[0] === 0 ? items[0][0] : null;
            this.sameTop = k0 ? items.filter(x => less(x[0], k0) === 0).length : j - i;
          }
        }
        i = j;
      }
      return out;
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
  // Step 31 (D-299): the two engines break exact ties the same way. Turns that read the same come out in one order in
  // both: the fewer working actions first (no action without a purpose: a turn that only waits, a Pause or an end of
  // turn, counts none, so standing still wins a level tie), then the fewer actions, then by the action itself (the shot before the pass,
  // the pass before a movement; then the player, the square by column and row, the arrow, the target, the shot).
  const TIE_KINDS = ['shot', 'forced_shot', 'pass', 'dribble', 'screen', 'move', 'qs', 'sprint', 'hesitate', 'contest', 'steal', 'intercept', 'challenge', 'pause', 'target', 'pick', 'reset', 'end_turn', 'forfeit'];
  const TIE_RANK = Object.fromEntries(TIE_KINDS.map((k, i) => [k, i]));
  const TIE_IDLE = new Set(['pause', 'end_turn']);
  const tieWork = t => { let n = 0; for (const a of t) if (!TIE_IDLE.has(a.kind)) n++; return n; };
  function tieCmp(t, u) {
    const w = tieWork(t) - tieWork(u);
    if (w) return w;
    if (t.length !== u.length) return t.length - u.length;
    for (let i = 0; i < t.length; i++) {
      const a = t[i], b = u[i];
      const d = ((TIE_RANK[a.kind] === undefined ? 99 : TIE_RANK[a.kind]) - (TIE_RANK[b.kind] === undefined ? 99 : TIE_RANK[b.kind])) || (a.piece - b.piece) || (a.dest - b.dest) || (a.arrow - b.arrow) || (a.target - b.target) || (SHOT_TYPES.indexOf(a.shot || '') - SHOT_TYPES.indexOf(b.shot || ''));
      if (d) return d;
    }
    return 0;
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
    const deadline = Infinity;                           // step 31 (D-293): no clock. A level is how far ahead it looks (max_depth)
    READS = new Map(); READS_OLD = new Map();
    MAP_ME = me;                                         // step 18s, stop two: eval.map 'offence' reads the map for the offence's decisions only
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
      partial: srch.partial, seconds: now() - t0, pv, same_top: srch.sameTop == null ? null : srch.sameTop,
      stable: srch.stable, extensions: srch.extensions, cap_hits: srch.capHits, kept: srch.kept, depth_seconds: srch.depthSeconds,
      mix: srch.mixCols || null,                         // D-272: at a declaration, each reply's (real, fake) values, in the results' order
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
  function goalsJSON(text) { return withMemo(() => goalsJSONCalc(text)); }
  function goalsJSONCalc(text) {
    const req = JSON.parse(text);
    if (req.lane !== undefined && (req.lane === true) !== laneOn()) setLane(req.lane === true);      // step 18q: eval.lane follows the request
    if (req.map !== undefined && req.map !== D.config.eval.map) setMap(req.map);                    // step 18s, stop two: eval.map follows the request
    if (req.map_me) MAP_ME = req.map_me;                 // (a setup's readings: the side placing)
    if (req.pass_rules !== undefined && (req.pass_rules !== false) !== passRulesOn()) setPassRules(req.pass_rules !== false);
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
  function searchJSON(text) { return withMemo(() => searchJSONCalc(text)); }
  function searchJSONCalc(text) {
    const req = JSON.parse(text);
    if (req.lane !== undefined && (req.lane === true) !== laneOn()) setLane(req.lane === true);      // step 18q: eval.lane follows the request
    if (req.map !== undefined && req.map !== D.config.eval.map) setMap(req.map);                    // step 18s, stop two: eval.map follows the request
    if (req.map_me) MAP_ME = req.map_me;                 // (a setup's readings: the side placing)
    if (req.pass_rules !== undefined && (req.pass_rules !== false) !== passRulesOn()) setPassRules(req.pass_rules !== false);
    const key = JSON.stringify(req.ctx);
    let ctx = CTXS.get(key);
    if (!ctx) { if (CTXS.size >= 4) CTXS.clear(); ctx = makeCtx(req.ctx); CTXS.set(key, ctx); }
    req.ctxObj = ctx;
    return JSON.stringify(search(req));
  }

  // Step 18o (D-195, agent._reads): the quick reading's own parts for a list of setup placements of one matchup: the
  // position's value (the offence's view), then each attacker's best look after the defence's best cover, largest first.
  function readsJSON(text) { return withMemo(() => readsJSONCalc(text)); }
  function readsJSONCalc(text) {
    const req = JSON.parse(text);
    if (req.lane !== undefined && (req.lane === true) !== laneOn()) setLane(req.lane === true);      // step 18q: eval.lane follows the request
    if (req.map !== undefined && req.map !== D.config.eval.map) setMap(req.map);                    // step 18s, stop two: eval.map follows the request
    if (req.map_me) MAP_ME = req.map_me;                 // (a setup's readings: the side placing)
    if (req.pass_rules !== undefined && (req.pass_rules !== false) !== passRulesOn()) setPassRules(req.pass_rules !== false);
    const key = JSON.stringify(req.ctx);
    let ctx = CTXS.get(key);
    if (!ctx) { if (CTXS.size >= 4) CTXS.clear(); ctx = makeCtx(req.ctx); CTXS.set(key, ctx); }
    const out = [];
    for (const it of req.items) {
      const js = Object.assign({}, req.state, { o: it.o, ball: it.ball, x: it.x, arrows: it.arrows });
      const s = stateFrom(js, ctx), r = new Read(s), cv = r.cover();
      const res = [0, 1, 2, 3, 4].map(i => (cv.residual[i] === undefined ? 0 : cv.residual[i])).sort((a, b) => b - a);
      out.push([r.leaf()].concat(res));
    }
    return JSON.stringify(out);
  }

  // ---- the equivalence probe: every measured quantity of one state --------------------------------------------------
  function probe(js, ctxJs, opts = {}) {
    MAP_ME = null;                                       // no decision is being searched
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
  const bankedOf = s => 5 * s.bonus5 + (s.ctx.tosOn ? -5 * s.tos : 0) + foulExternality(s);   // what the possession has already earned
  const handLeaf = s => readOf(s)._handLeaf();                                                       // today's hand-combined reading
  const looksLeaf = s => { FORCE_LOOKS = true; try { return readOf(s)._handLeaf(); } finally { FORCE_LOOKS = false; } };   // step 18f: the same in the looks mode, for fitting its map
  // ---- step 18s (D-199): the coverage map -------------------------------------------------------------------------
  // Shaun's design (docs/reference/COVERAGE_MAP_BLUEPRINT.md). For every attacker and every square a shot may go up
  // from: value (his best open shot there, from his card), reach (the chance he can be shooting there with the ball
  // when the next phase starts, by the movement and pass rules), influence (what the best defender who can get there
  // takes off it, by the contest rules) and weakness (what the offence can get there). Then who covers each square,
  // and what is left after the defence spends the tokens it has: "a defence can't cover two at once" is worked out by
  // the rules, never fitted. Nothing here is read by the search yet (stop one): it is shown to the coach and checked.
  // Approximated, and why: (1) an attacker without the ball is given one movement before his catch, as the reading's
  // looks are; (2) the bars of the defence's arrows are taken at the length they have now, and a defender who steps
  // bars his new arrow's foot only: next phase's exact bars need next phase's board; (3) the defence's answers are
  // chosen one action at a time, each the one that leaves the least, not by trying every set of actions.
  const _SHP = new Map();
  function shotPaths(start, qs, noRim, deep = 0) {     // every movement path from start that ends where a shot may go up: [path, rushed]
    const key = ((start * 8 + qs) * 2 + (noRim ? 1 : 0)) * 8 + deep; let hit = _SHP.get(key); if (hit) return hit;
    hit = [];
    const ok = p => { const c = p[p.length - 1]; return p.every(q => ONB[q]) && SHOOT(ZN[c] === 0 && DEEP[c] && DEEP[c] <= deep ? 4 : ZN[c]) && !(noRim && c === RIM); };
    for (const p of movePaths(start)) if (ok(p)) hit.push([p, false]);
    for (const p of qsPaths(start, qs)) if (ok(p)) hit.push([p, true]);
    for (const [, p] of sprintPaths(start, qs)) if (ok(p)) hit.push([p, true]);
    _SHP.set(key, hit); return hit;
  }
  // The chance a pass from the ball handler to attacker i arrives, by the rules' own options once it is in the air: an
  // Intercept through a defender's square, or one straight movement along his arrow onto the pass line and then the
  // Intercept (never from a square next to the passer; rushed if he got there by a Quick Step or Sprint). 0: no pass.
  const COV_STEP = new Set(['move', 'qs', 'sprint']);
  const COV_SLOW = { on: false };
  function passChanceExact(s, i) {
    const st = W_(s, { side: 'O', stage: 'play', turn_n: 0, tok_o: Math.max(1, s.tok_o), pending: null });
    const a = A('pass', 'O', s.ball, -1, -1, i);
    try {
      if (!isLegal(st, a)) return 0;
      // stop two: the same chance worked out directly (icptPi), equal to the actions below on every random position
      // tried (tools/step_18s.py passproof); COV_SLOW keeps the actions' own way for that check
      if (!COV_SLOW.on) return lanePRules(s, i, s.o[i], -1, -1, 0, false, 0);
      const nxt = apply(st, a);
      if (isChance(nxt) || nxt.stage !== 'play' || nxt.side !== 'X' || !nxt.pending) return 1;
      let worst = 0;
      for (const b of legalActions(nxt)) {
        if (b.kind === 'intercept') worst = Math.max(worst, 1 - pS(rolled(nxt, 'O', s.ball, 'pass') - rolled(nxt, 'X', b.piece, 'intercept')));
        else if (COV_STEP.has(b.kind) && mtiApproach(nxt, b)) {
          const af = apply(nxt, b);
          if (!isChance(af) && af.pending) worst = Math.max(worst, 1 - pS(rolled(af, 'O', s.ball, 'pass') - rolled(af, 'X', b.piece, 'intercept')));
        }
      }
      return 1 - worst;
    } catch (e) { return 0; }
  }
  const COV_NONE = [];
  // Step 22b (D-222, Shaun, 18 Nov 2026): the reaction's own off balance, as the rules have it (D-185). A Contest a
  // defender reaches standing or by one Move finds him set; one he needs a Quick Step or a Sprint for finds him off
  // balance: every roll 2 lower. The map used to read both the same, so a defender six squares off covered a shot as
  // well as one beside the shooter. Per board square: the contest kinds within the reaction's two actions (bits 0 to
  // 5), and those of them he is set for (bits 6 to 11).
  const _CM2 = new Map(), _AAM2 = new Map();
  function cm2Cached(q, a, qs, mode) {
    const key = (((q * 8 + a) * 8 + qs) * 3 + mode) * 4 + SOFTK;
    let hit = _CM2.get(key); if (hit) return hit;
    const cf = cmapCached(q, a, qs, true, 1, mode), full = cf.masks[2], set = cmapCached(q, a, qs, true, 0, mode).masks[1], st = cf.masks[0];
    hit = new Uint32Array(NB);           // (fix 3: bits 12 to 17 the kinds he reaches where he stands, 18 to 23 those he is set for there)
    for (let b = 0; b < NB; b++) hit[b] = full[b] | ((set[b] & full[b]) << 6) | (st[b] << 12) | (st[b] << 18);
    _CM2.set(key, hit); return hit;
  }
  // Step 31, fix 3 (the rules' one Move a phase; Shaun, 26 Nov 2026): a defender's reply after a movement of the
  // defence's answer. After a Move (a Move on the spot too) he has no Move left: a Quick Step, off balance, if he has
  // one, or the Contest where he stands, in control. After a Quick Step he still has his Move (a Move puts him back in
  // control). After a Sprint (his Move and his Quick Step together) only where he stands, off balance.
  const _CMA = new Map();
  function cmAfter(q, a, qs, mode, kind, qsL) {
    const kk = kind === 'move' ? 0 : kind === 'qs' ? 1 : 2, ql = kind === 'move' && qsL > 0 ? 1 : 0;
    const key = ((((((q * 8 + a) * 8 + qs) * 3 + mode) * 3 + kk) * 2 + ql) * 4) + SOFTK;
    let hit = _CMA.get(key); if (hit) return hit;
    let full, set, st;
    if (kk === 0) { const c = cmapCached(q, a, qs, false, ql, mode); full = c.masks[2]; st = c.masks[0]; set = cmapCached(q, a, qs, false, 0, mode).masks[1]; }
    else if (kk === 1) { const c = cmapCached(q, a, qs, true, 0, mode); full = c.masks[2]; set = c.masks[1]; st = c.masks[0]; }
    else { const c = cmapCached(q, a, qs, false, 0, mode); full = c.masks[2]; set = null; st = c.masks[0]; }
    hit = new Uint32Array(NB);           // (standing after a Quick Step or a Sprint he is off balance: not set there)
    for (let b = 0; b < NB; b++) hit[b] = full[b] | (set ? ((set[b] & full[b]) << 6) : 0) | (st[b] << 12) | (kk === 0 ? st[b] << 18 : 0);
    _CMA.set(key, hit); return hit;
  }
  // which of a defender's one-action movements reaches q facing a: a Quick Step keeps his arrow and its square is one a
  // Quick Step reaches; any other fixed-arrow square is a Sprint's
  const fixedKind = (s, d, q, a) => (a === s.arrows[d] && geoReach(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, false, 1)[1].has(q)) ? 'qs' : 'sprint';
  // Step 26 (D-249, Shaun, 19 Nov 2026): "in time" uses the real paths. A defender's contest a phase on from where he
  // stands, by the movement he really has: his paths go around attackers' bodies and his teammates (a bunch can wall
  // off a contest square simply by standing on it), through the diagonals the rules leave open, blocked only by a
  // screen's T square. The same masks as cm2Cached (the kinds within the reaction, and those he is set for).
  function bodyCm2(sN, d, mode) {
    const fr = defenderReachExact(sN, d), key = mode * 4 + SOFTK;
    if (fr._cm2 && fr._cm2k === key) return fr._cm2;
    const cf = contestMap(fr[0], fr[1], mode), full = cf.masks[2], st = cf.masks[0];
    const free1 = new Map(); for (const [q, n] of fr[0]) if (n <= 1) free1.set(q, n);
    const set = contestMap(free1, new Map([[sN.x[d], new Map([[sN.arrows[d], 0]])]]), mode).masks[1];
    const hit = new Uint32Array(NB);
    for (let b = 0; b < NB; b++) hit[b] = full[b] | ((set[b] & full[b]) << 6) | (st[b] << 12) | (st[b] << 18);
    fr._cm2 = hit; fr._cm2k = key;
    return hit;
  }
  function anyArrow2(q, qs, mode) {                    // whichever way he faces (he chose his arrow when a Move took him there)
    const key = ((q * 8 + qs) * 3 + mode) * 4 + SOFTK;
    let hit = _AAM2.get(key); if (hit) return hit;
    hit = new Uint32Array(NB);
    for (let a = 0; a < 8; a++) { const m = cm2Cached(q, a, qs, mode); for (let b = 0; b < NB; b++) hit[b] |= m[b]; }
    _AAM2.set(key, hit); return hit;
  }
  function mapVals(r, lk, d, mk, fl) {                 // the look with defender d's Contest (mk: cm2Cached's value for its square)
    const full = mk & 63, set = (mk >> 6) & 63, soft = r.s.ctx.soft;
    return r._valsCalc(lk, d, full, set, (fl || 0) | 4, soft ? full : 0, soft ? set : 0);
  }
  const TURNOVER_COST = 5;                             // D-198: a lost ball is -5
  const GUARDED_ENDS = 3;                              // D-171: three phase ends closely guarded is the violation (rules_config.GUARDED_ENDS)
  function covValue(o, skip, extra) {                 // [weakness, best shot type's index, the defender who covers, the next best]
    let top = -1, tt = 0, cov = -1, nxt = -1, ob = -1, cb = -1, nb = -1;      // ob, cb, nb: his best shot open, and who takes it away
    for (let t = 0; t < o.open.length; t++) {
      let v = o.open[t], d1 = -1, v2 = o.open[t], d2 = -1;
      for (let d = 0; d < 5; d++) {
        const vals = d === skip ? extra : o.vals[d];
        if (!vals || !(vals[t] < o.open[t])) continue;
        if (vals[t] < v) { v2 = v; d2 = d1; v = vals[t]; d1 = d; } else if (vals[t] < v2) { v2 = vals[t]; d2 = d; }
      }
      if (v > top) { top = v; tt = t; cov = d1; nxt = d2; }
      if (o.open[t] > ob) { ob = o.open[t]; cb = d1; nb = d2; }
    }
    if (cov < 0 && top < ob) { cov = cb; nxt = nb; }   // he is left a lesser shot nobody contests: the cover is whoever took the better one
    return [top, tt, cov, nxt];
  }
  function covPass(s, i, q) {                          // the chance a pass to attacker i on q arrives, by the rules (0: denied)
    if (COV_SLOW.on) return passChanceExact(q === s.o[i] ? s : W_(s, { o: setAt(s.o, i, q) }), i);
    const a = s.o[s.ball];
    for (let j = 0; j < 5; j++) { const xp = s.x[j]; if (adjacent(xp, q) && onSegment(xp, a, q, 0.5)) return 0; }
    return lanePRules(s, i, q, -1, -1, 0, false, 0);
  }
  // lean (stop two, for the search): only each square's best open way is kept, not every way to it. The same options,
  // values and worths; no paths, so nothing can be re-read with a defender moved (covWith, the answers).
  // The board as the next phase finds it if nobody moves again (resolve.new_phase): the defence's movement fresh, no
  // zone broken (a won Dribble lasts the phase), no screen standing (a screen ends with the phase).
  const covNext = s => W_(s, { screens: [], tok_x: 6, moved_x: 0, qs_x: 0, lock_x: 0, rush_x: 0, beaten: [], cnt: ZERO });
  // Step 30b: a memory that lasts one request. The lean map of a board is read once per request and shared by every
  // reading that asks for that same board (the lasting gap, the top of the list, the settlement). The key is the whole
  // state, every field, built from the state itself (the context by its id; the state's own scratch caches, the fields
  // starting with an underscore, left out), with the reading settings that can differ inside one request. It holds
  // readings, never choices, and is thrown away when the request ends. Where no request has opened it (a direct call),
  // nothing is remembered.
  let MAP_MEMO = null;
  // Step 31, Part C: the memory is held to a size a phone's browser can give. It was 2,000 readings with no thought for
  // their size, and one All-Star think held 2 GB. Now two generations: when the newer one is full it becomes the older
  // and the oldest is dropped; a reading found in the older one is moved up. What is dropped is read again when it is
  // next needed, so the memory can change how long a think takes and never what it decides. Small things (a stance's
  // reading: two numbers) have their own, larger store, so they are never pushed out by the big ones.
  let MAP_MEMO_MAX = 30, SMALL_MEMO_MAX = 20000, READS_MAX = 40, REACH_MAX = 80, SV_MEMO_MAX = 30000;   // measured: at these sizes a think is under 10 in 100 slower and fits in 256 MB; ten times larger gave nothing back
  let SMALL_MEMO = null;
  const stateKey = s => JSON.stringify(s, (k, v) => (k === 'ctx' ? (v ? v.id : null) : (k.length && k.charCodeAt(0) === 95) ? undefined : v));
  function withMemo(f) {                               // a request's own memory, opened and thrown away around it
    const keep = MAP_MEMO, keepS = SMALL_MEMO;
    MAP_MEMO = new Memo2(MAP_MEMO_MAX); SMALL_MEMO = new Memo2(SMALL_MEMO_MAX);
    try { return f(); } finally { MAP_MEMO = keep; SMALL_MEMO = keepS; }
  }
  function covBuild(s, lean, r0, lastToo) {
    if (MAP_MEMO === null || r0 || lean !== true) return covBuildCalc(s, lean, r0, lastToo);
    const key = RD.lead + '|' + (MAP_ME || '') + '|' + (D.config.eval.answer_lead || '') + '|' + (lastToo ? 'L' : '') + '|' + stateKey(s);
    let m = MAP_MEMO.get(key);
    if (m === undefined) {
      m = covBuildCalc(s, true, null, lastToo);
      MAP_MEMO.set(key, m);
    }
    return m;
  }
  function covBuildCalc(s, lean, r0, lastToo) {
    const r = r0 || new Read(s), ctx = s.ctx, noRim = ctx.noRim, off = ctx.control > 0 ? ctx.control : 0;
    const sN = covNext(s);
    const xat = new Map(); for (let j = 0; j < 5; j++) if (ONB[s.x[j]]) xat.set(s.x[j], j);
    // each defender's Contest a phase on from where he stands: the reaction's two actions, his movement fresh
    // step 26 (D-249): along the real paths: around attackers' bodies and his teammates, blocked only by screens
    const cms = [0, 1, 2, 3, 4].map(d => (ONB[s.x[d]] ? bodyCm2(sN, d, stanceMode(sN, d)) : null));
    const options = [], byKey = new Map();
    // ---- step 22c (D-224, Shaun, 18 Nov 2026): stagnation, in points by the rules -------------------------------------
    // The Steal, as the defence stands: whoever holds the ball on a square can be reached by a defender next to it
    // with an arrow on him, or by one who gets next to it with a Move (facing as he likes, set when he arrives). By
    // the rules' own chances (D-198): the ball kept on Dribble less Steal or under, else -5; a foul (one roll from in
    // front, two from level or behind) is +5. The defence only tries where that favours it, so it never counts above 0.
    const stealOn = ctx.ppo && s.tok_x >= 1 && count(s, 'X', 'steal') < LIMITS.X.steal;
    const mv1 = [null, null, null, null, null], sev = new Map(), sat = new Map();
    if (stealOn && s.tok_x >= 2) for (let j = 0; j < 5; j++) if (ONB[s.x[j]] && caps(s, 'X', j)[0]) mv1[j] = defenderReachExact(s, j)[0];
    const stealEV = (a, j, rolls, viaMove) => {
      const key = ((a * 5 + j) * 2 + (rolls - 1)) * 2 + (viaMove ? 1 : 0);
      let v = sev.get(key);
      if (v === undefined) {
        const pf = clampT(ctx.dfn[j].r.foul_steal) / 20, foul = rolls === 2 ? 1 - (1 - pf) * (1 - pf) : pf;
        const tk = rolled(s, 'O', a, 'dribble') - (viaMove ? ctx.dfn[j].r.steal : rolled(s, 'X', j, 'steal'));
        v = TURNOVER_COST * foul - TURNOVER_COST * (1 - foul) * pNot(tk);
        sev.set(key, v);
      }
      return v;
    };
    const stealAt = (a, q) => {
      if (!stealOn) return 0;
      const key = a * 4096 + q;
      let best = sat.get(key);
      if (best !== undefined) return best;
      best = 0;
      for (let j = 0; j < 5; j++) {
        const xp = s.x[j];
        if (!ONB[xp]) continue;
        if (adjacent(xp, q) && onLine(stanceOf(s, j), dirBetween(xp, q))) { const v = stealEV(a, j, foulRolls(xp, q), false); if (v < best) best = v; }
        const fr = mv1[j];
        if (fr) for (let d = 0; d < 8; d++) { const p2 = q + DSTEP[d]; if (ONB[p2] && fr.get(p2) === 1) { const v = stealEV(a, j, foulRolls(p2, q), true); if (v < best) best = v; } }
      }
      sat.set(key, best);
      return best;
    };
    // The closely guarded count (D-173): a ball handler who holds where he stands, closely guarded when the phase
    // ends, is one phase end nearer the -5 violation: counted at how far along the count's three that puts him. A
    // live dribble isn't counted (the rule), and moving or passing starts it again.
    // Step 27 (D-256): counted by the rule, not in thirds. He shoots, passes or gets free at the next phase's start, so
    // the count costs nothing unless it falls at this phase end (held already at its last but one): then the full -5.
    const guardAt = (a, q0, n0) => (ctx.guarded && a === s.ball && ((q0 === s.o[a] && n0 === 0) || ((s.grd & 3) === 2 && n0 === 1)) && (s.grd & 3) !== 1 && closelyGuarded(s)     // D-273: the count runs on after his pivot
      && ((s.grd >> 2) & 3) + 1 >= GUARDED_ENDS ? -TURNOVER_COST : 0);
    // Step 26 (D-251): the three seconds, counted as the closely guarded count is. An attacker who has the ball in the
    // key when the next phase starts is one phase end nearer the -5 (he must be out before the second): counted at
    // how far along that puts him (half, or all of it if he was already in the key at the last phase end).
    // Step 27 (D-255): by the rule, no halves. A shot that goes up at the next phase's start beats the violation, so
    // having the ball in the key then costs nothing, unless he was already in the key at the last phase end: then he
    // can't avoid it at this one (the full -5). Leaving costs the movement his look already spends.
    const keyAt = (a, q0) => (ctx.three && INKEY[q0] && ((s.key_o >> a) & 1) ? -TURNOVER_COST : 0);
    // no phase after this one: nothing can be shot at the next phase's start. lastToo (step 31): the possession's value
    // reads the last phase's own looks (the ball there with an action left for the shot, inside the phase)
    const last = s.clock <= 2 && !lastToo;
    let passerSq = null;
    const passerSquares = () => {                      // step 26: the squares the ball handler's one movement reaches this turn
      if (passerSq) return passerSq;
      passerSq = [];
      const b = s.ball, seen = new Set([s.o[b]]);
      if (ONB[s.o[b]] && s.tok_o >= 2 && count(s, 'O', 'pass') < LIMITS.O.pass) for (const kind of ['move', 'qs', 'sprint']) if (canMoveKind(s, 'O', b, kind)) for (const q of movementDests(s, 'O', b, kind).keys()) if (!seen.has(q)) { seen.add(q); passerSq.push(q); }
      passerSq.sort((u, v) => u - v);
      return passerSq;
    };
    const pfMemo = new Map();
    const passFrom = (pq, a, q) => {
      const key = (pq * 4096 + q) * 5 + a;
      let v = pfMemo.get(key);
      if (v === undefined) { v = covPass(W_(s, { o: setAt(s.o, s.ball, pq) }), a, q); pfMemo.set(key, v); }
      return v;
    };
    for (let a = 0; a < 5 && !last; a++) {
      if (!ONB[s.o[a]]) continue;
      const starts = [];                               // where he can have the ball when the next phase starts, and the chance
      if (a === s.ball) {
        const one = new Map([[s.o[a], 0]]);
        if (s.tok_o > 0) for (const kind of ['move', 'qs', 'sprint']) if (canMoveKind(s, 'O', a, kind)) for (const q of movementDests(s, 'O', a, kind).keys()) if (!one.has(q)) one.set(q, 1);
        for (const q of [...one.keys()].concat(s.tok_o > 0 ? twoActions(s, a, one) : [])) starts.push([q, 1.0, false, one.has(q) ? one.get(q) : 2]);
        // step 22b (D-218): a wall he can only pass by winning a Dribble. The squares his movement reaches with a
        // defender next to him beaten (that defender's zone broken for the phase), at the Dribble's chance by the
        // rules. A lost Dribble locks him: nothing is banked against him, so it costs no 5.
        if (s.tok_o >= 2 && r._dribbleOk()[0]) {
          for (let j = 0; j < 5; j++) {
            if (!ONB[s.x[j]] || !adjacent(s.x[j], s.o[a]) || s.beaten.some(b => b[1] === j)) continue;
            const p = r._beatChance(j);
            if (!(p > 0)) continue;
            const sb = W_(s, { beaten: s.beaten.concat([[a, j]]) });
            for (const kind of ['move', 'qs', 'sprint']) if (canMoveKind(sb, 'O', a, kind)) for (const q of movementDests(sb, 'O', a, kind).keys()) if (!one.has(q)) starts.push([q, p, false, 2, true]);
          }
        }
      } else if (s.tok_o > 0 && count(s, 'O', 'pass') < LIMITS.O.pass) {
        // step 22 (D-210): the map reads the offence's whole first turn of the next phase. A receiver one movement
        // away catches and has his movement to a shot; two movements away (his cut) he catches where he gets to and
        // shoots from there: cut, pass, shot, the defence's reaction counted in the contest of it
        for (const [q, n] of attackerReach(s, a)) {
          if (n > 2 || n + 1 > s.tok_o) continue;
          let p = covPass(s, a, q);                   // the rules' own chance
          const p0 = p;                               // step 31: from where the ball handler stands (the fall-back after a lost Dribble)
          // step 26 (D-250): from every square the ball handler can reach this turn. He may Move, Quick Step or
          // Sprint and then pass in the same turn; the defence doesn't move in between, so a lane counts if the ball
          // can get to a square that opens it. (Only where the lane from where he stands isn't already clean.)
          if (p < 1 && n + 2 <= s.tok_o) for (const pq of passerSquares()) { if (pq === q) continue; const p2 = passFrom(pq, a, q); if (p2 > p) p = p2; if (p >= 1) break; }
          if (p > 0) starts.push([q, p, n === 2, n + 1, false, p0]);       // (n0, step 22b: his movements and the pass)
        }
      }
      const mates = new Set(); for (let k = 0; k < 5; k++) if (k !== a) mates.add(s.o[k]);
      const lines = [];
      if (ctx.zone) {
        for (let j = 0; j < 5; j++) {                 // actions.capture_lines, a defender at a time, for this attacker with the ball, a phase on
          const st = stanceOf(sN, j);
          if (st < 8 || st >= 16 || !ONB[s.x[j]]) continue;
          const d0 = st - 8, d1 = (st - 7) % 8;
          lines.push([j, [[s.x[j], d0, d1, Math.max(1, zoneRay(sN, j, d0, s.o[a], -1).length), Math.max(1, zoneRay(sN, j, d1, s.o[a], -1).length)]]]);
        }
      }
      const qs = ctx.off[a].qs, home = s.o[a];
      const add = (c, rushed, path) => {
        const key = (a * 4096 + c) * 2 + (rushed ? 1 : 0);
        let o = byKey.get(key);
        if (!o) { o = { a, c, rushed, paths: [] }; byKey.set(key, o); options.push(o); }
        o.paths.push(path);
      };
      for (const [q0, pr, setOnly, n0, dr, p0] of starts) {
        if (mates.has(q0) || (q0 !== home && xat.has(q0))) continue;
        const stop = q0 !== home ? q0 : -1;
        const adj = stealAt(a, q0) + guardAt(a, q0, n0) + keyAt(a, q0);    // step 22c, 26: what holding the ball there costs him (0 or less)
        if (lean) {
          const put = (c, rushed) => {                             // (the likeliest way there; of two as likely, the one that costs him less)
            const key = (a * 4096 + c) * 2 + (rushed ? 1 : 0);
            const o = byKey.get(key);
            if (!o) { const n = { a, c, rushed, paths: null, pr, q0, n0, dr: !!dr, adj, p0: p0 || 0 }; byKey.set(key, n); options.push(n); }
            else if (pr > o.pr || (pr === o.pr && adj > o.adj)) { o.pr = pr; o.q0 = q0; o.n0 = n0; o.dr = !!dr; o.adj = adj; o.p0 = p0 || 0; }
          };
          if (SHOOT(szone(ctx, q0)) && !(noRim && q0 === RIM)) put(q0, false);
          if (setOnly) continue;
          for (const [p, rushed] of shotPaths(q0, qs, noRim, ctx.deep)) {
            const c = p[p.length - 1], o = byKey.get((a * 4096 + c) * 2 + (rushed ? 1 : 0));
            if (o && (o.pr > pr || (o.pr === pr && o.adj >= adj))) continue;
            let bad = false;
            for (const q of p) if (mates.has(q) || xat.has(q)) { bad = true; break; }
            if (bad) continue;
            for (const ln of lines) if (!captureOk(q0, p, ln[1])) { bad = true; break; }
            if (!bad) put(c, rushed);
          }
          continue;
        }
        if (SHOOT(szone(ctx, q0)) && !(noRim && q0 === RIM)) add(q0, false, { q0, p: COV_NONE, dm: 0, zm: 0, pr, stop, dr: !!dr, adj });      // a set shot from where the phase finds him
        if (setOnly) continue;
        for (const [p, rushed] of shotPaths(q0, qs, noRim, ctx.deep)) {
          let dm = 0, bad = false;
          for (const q of p) { if (mates.has(q)) { bad = true; break; } const j = xat.get(q); if (j !== undefined) dm |= 1 << j; }
          if (bad) continue;
          let zm = 0;
          for (const ln of lines) if (!captureOk(q0, p, ln[1])) zm |= 1 << ln[0];
          add(p[p.length - 1], rushed, { q0, p, dm, zm, pr, stop, dr: !!dr, adj });
        }
      }
    }
    let oid = 0;
    for (const o of options) {
      o.id = oid++;
      const lk = makeLook(o.a, o.c, 'later', 1.0, false), card = ctx.off[o.a], pts = ctx.worth[szone(ctx, o.c)];
      lk.types = ZONE_SHOTS[szone(ctx, o.c)]; lk.rushed = o.rushed;
      o.lk = lk; o.fl = (o.rushed && off > 0) ? 1 : undefined;
      o.open = lk.types.map(t => pts * (cardShot(ctx, card, t, o.c) - (o.rushed ? off : 0)));
      o.v = Math.max(...o.open);                       // value: his best shot there with nobody on it, as he would take it
      o.vals = [null, null, null, null, null];
      for (let d = 0; d < 5; d++) {
        const mask = cms[d] ? cms[d][BI[o.c]] : 0;
        if (mask) o.vals[d] = mapVals(r, lk, d, mask, o.fl);
      }
      let pr = 0;
      if (lean) pr = o.pr;
      else { o.adj = 0; for (const pt of o.paths) if (pt.dm === 0 && pt.zm === 0 && (pt.pr > pr || (pt.pr === pr && pr > 0 && pt.adj > o.adj))) { pr = pt.pr; o.dr = pt.dr; o.adj = pt.adj; } }
      const cv = covValue(o, -1, null);
      o.lc = o.dr ? 0 : TURNOVER_COST;                 // what not getting there costs: a lost pass -5, a lost Dribble nothing
      o.r = pr; o.w = cv[0]; o.t = cv[1]; o.cover = cv[2]; o.next = cv[3];
      o.e = pr > 0 ? pr * (o.w + o.adj) - (1 - pr) * o.lc : -Infinity;
    }
    const sorted = options.filter(o => o.r > 0).sort((x, y) => (y.e - x.e) || (x.a - y.a) || (x.c - y.c) || ((x.rushed ? 1 : 0) - (y.rushed ? 1 : 0)));
    // the best shot that can go up this phase, as the reading has it
    let now = null;
    for (const i of r.att_o) for (const lk of r.looks[i] || []) if (lk.now && (now === null || lk.base > now.e)) now = { a: i, c: lk.c, e: lk.base, route: lk.route };
    return { s, sN, r, options, sorted, now, cms };
  }
  // one option with defender d standing on p facing `arrow` (his Contest from there `cm`), every other piece as it stands
  function covWith(m, o, d, p, arrow, cm) {
    if (o.c === p) return -Infinity;
    const s = m.s, bd = 1 << d, same = p === s.x[d] && arrow === s.arrows[d];
    const line = (!same && s.ctx.zone) ? [[p, arrow, (arrow + 1) % 8, 1, 1]] : null;
    let pr = 0, lc = TURNOVER_COST, adj = 0;
    for (const pt of o.paths) {
      if (pt.pr <= pr || (pt.dm & ~bd) || (same ? pt.zm : (pt.zm & ~bd)) || pt.stop === p || (pt.p.length && pt.p.includes(p))) continue;
      if (line !== null && pt.p.length && !captureOk(pt.q0, pt.p, line)) continue;
      pr = pt.pr; lc = pt.dr ? 0 : TURNOVER_COST; adj = pt.adj;
    }
    if (pr <= 0) return -Infinity;
    const mask = cm[BI[o.c]];
    const mine = mask ? mapVals(m.r, o.lk, d, mask, o.fl) : null;
    return pr * (covValue(o, d, mine)[0] + adj) - (1 - pr) * lc;
  }
  // stop two, for the search: the defence's answers in a fast form. While it has tokens, one defender makes the one
  // movement this phase that takes something off the offence's best option and leaves its best six the smallest, the
  // largest first (a Move: any arrow; a Quick Step or Sprint: the arrow it leaves him), and then contests everything
  // from where he now stands. Each defender moves once. What
  // is left is what the defence could not take away with the tokens it has. His way there is his exact movement (bodies
  // and screens counted). Approximation: of the board's changes only his new square's body is counted.
  function covLeanAnswers(m) {
    const s = m.s, r = m.r, soft = s.ctx.soft, opts = m.options, K = 6;
    if (s.tok_x <= 0) return 0;
    const taken = new Set(); for (let k = 0; k < 5; k++) { taken.add(s.o[k]); taken.add(s.x[k]); }
    const moved = [false, false, false, false, false];
    const before = (x, y) => y.e - x.e || x.a - y.a || x.c - y.c || (x.rushed ? 1 : 0) - (y.rushed ? 1 : 0);
    let tok = s.tok_x, steps = 0;
    while (tok > 0) {
      const head = [];                                  // the offence's best few options, the largest first
      for (const o of opts) {
        if (!(o.r > 0)) continue;
        let k = head.length;
        while (k > 0 && before(o, head[k - 1]) < 0) k--;
        if (k < K) { head.splice(k, 0, o); if (head.length > K) head.pop(); }
      }
      const top = head[0];
      if (!top || top.e <= 0) break;
      const b = BI[top.c];
      const cur = head.map(o => o.e);
      let best = null;
      const offer = (d, q, a, cm) => {                    // a: the arrow a Quick Step or Sprint leaves him, or -1 after a Move
        if (!cm[b] || taken.has(q)) return;
        const after = [];
        for (let k = 0; k < head.length; k++) {
          const o = head[k];
          let e;
          if (o.c === q) e = -Infinity;
          else {
            const mask = cm[BI[o.c]];
            const vals = mask ? mapVals(r, o.lk, d, mask, o.fl) : null;
            e = o.r * (covValue(o, d, vals)[0] + o.adj) - (1 - o.r) * o.lc;
          }
          if (k === 0 && !(e < top.e - 1e-9)) return;     // an answer takes something off the best option
          after.push(e);
        }
        after.sort((x, y) => y - x);
        if (best === null || covLess(after, best.after) || (!covLess(best.after, after) && (d - best.d || q - best.q || a - best.a) < 0)) best = { d, q, a, after };
      };
      for (let d = 0; d < 5; d++) {
        if (moved[d] || !ONB[s.x[d]]) continue;
        const cp = caps(s, 'X', d);
        if (!cp[0] && cp[1] <= 0) continue;
        const qs = s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d), fr = defenderReachExact(s, d);
        for (const [q, n] of fr[0]) if (n === 1) offer(d, q, -1, anyArrow2(q, qs, mode));
        for (const [q, arrs] of fr[1]) for (const [a, n] of arrs) if (n === 1) offer(d, q, a, cm2Cached(q, a, qs, mode));
      }
      if (best === null || !covLess(best.after, cur)) break;
      const d = best.d, qs = s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d);
      const cm = best.a < 0 ? anyArrow2(best.q, qs, mode) : cm2Cached(best.q, best.a, qs, mode);
      moved[d] = true; tok--; steps++;
      taken.add(best.q);
      if (m.steps) m.steps.push([d, best.q, best.a]);
      for (const o of opts) {
        if (o.c === best.q) { o.r = 0; o.e = -Infinity; continue; }
        const mask = cm[BI[o.c]];
        o.vals[d] = mask ? mapVals(r, o.lk, d, mask, o.fl) : null;
        const cv = covValue(o, -1, null);
        o.w = cv[0]; o.t = cv[1]; o.cover = cv[2]; o.next = cv[3];
        o.e = o.r > 0 ? o.r * (o.w + o.adj) - (1 - o.r) * o.lc : -Infinity;
      }
    }
    return steps;
  }
  // ---- step 20 (Shaun, 17 Nov 2026): the lasting gap -------------------------------------------------------------------
  // "The offence attempts to produce lasting gaps in the defence's coverage such that no defender can cover a valuable
  // scoring square, or one defender has to cover multiple squares accessible to multiple offensive players. Conversely,
  // the defence is trying to limit those scenarios as much as possible, and if it has to allow such squares and scenarios
  // to exist, it will aim to leave the lowest possible value ones."
  //
  // Like for like: the map is always read from the position as a fresh phase would find it (resolve.new_phase, with
  // no clock taken off): the offence's full turn to come and the defence's movement fresh, whatever either has spent.
  // Spending actions can't lower it, and a phase ending can't move it. A pass in the air is read as caught.
  function covFresh(s) {
    const t = s.pending ? W_(s, { ball: s.pending[1], pending: null, approach: -1 }) : s;
    return W_(t, { screens: [], beaten: [], tok_o: 6, tok_x: 6, moved_o: 0, moved_x: 0, qs_o: 0, qs_x: 0, lock_o: 0, lock_x: 0, rush_o: 0, rush_x: 0,
      cnt: ZERO, turn_n: 0, side: 'O', stage: 'play', approach: -1, prev_wait: '', final: false, turn_lead: -1, turn_x: [], turn_moved: 0, react_moved: 0 });
  }
  // Step 21 (D-206): the defence read as it really is, the offence fresh. The defence keeps what it has left this
  // phase (tokens, who has moved, quick-stepped, is locked or rushed, a zone a Dribble broke); the offence gets its
  // full turn to come, whatever it has spent (D-204's like for like, which Shaun's ruling leaves standing for the
  // offence): with its tokens spent it still moves first next phase, before the defence can answer again, so the looks
  // that need a pass next phase stay on the map.
  function covOffFresh(s) {
    const cnt = Array.from(s.cnt); for (let k = 0; k < 6; k++) cnt[k] = 0;
    return W_(s, { tok_o: 6, moved_o: 0, qs_o: 0, lock_o: 0, rush_o: 0, cnt, turn_n: 0, side: 'O', stage: 'play', approach: -1, prev_wait: '',
      final: false, turn_lead: -1, turn_x: [], turn_moved: 0, react_moved: 0 });
  }
  // The defence's best answer, by search over its real options: each defender makes at most one movement (a Move with
  // any arrow, turning on the spot included; a Quick Step or Sprint with the arrow it leaves him), within its tokens. A
  // beam of the best LG_BEAM answers so far is carried one defender deeper at a time; each is widened by the LG_WIDE
  // movements that leave the offence's best LG_HEAD threats the smallest. Answers are ranked by the lasting gap, then
  // by the threats left, the largest first. The best answer seen at any depth (none at all included) is the answer.
  const LG_BEAM = 3, LG_WIDE = 3, LG_HEAD = 6;
  function lgRoot(m) {
    const s = m.s, taken = new Set();
    for (let k = 0; k < 5; k++) { taken.add(s.o[k]); taken.add(s.x[k]); }
    const o = [];
    for (const src of m.options) if (src.r > 0) o.push({ src, r: src.r, vals: src.vals.slice(), e: src.e, w: src.w, t: src.t, cover: src.cover, next: src.next });
    return { m, cms: m.cms.slice(), xs: Array.from(s.x), moves: [], moved: [false, false, false, false, false], taken, tok: s.tok_x, o };
  }
  const lgBefore = (x, y) => y.e - x.e || x.src.a - y.src.a || x.src.c - y.src.c || (x.src.rushed ? 1 : 0) - (y.src.rushed ? 1 : 0);
  function lgHead(st) {
    const head = [];
    for (const x of st.o) {
      if (!(x.r > 0)) continue;
      let k = head.length;
      while (k > 0 && lgBefore(x, head[k - 1]) < 0) k--;
      if (k < LG_HEAD) { head.splice(k, 0, x); if (head.length > LG_HEAD) head.pop(); }
    }
    return head;
  }
  function lgChild(m, st, d, q, a, cm) {
    const r = m.r, soft = m.s.ctx.soft, o = [];
    for (const x of st.o) {
      const y = { src: x.src, r: x.r, vals: x.vals.slice(), e: x.e, w: x.w, t: x.t, cover: x.cover, next: x.next };
      if (x.src.c === q) { y.r = 0; y.e = -Infinity; o.push(y); continue; }
      const mask = cm[BI[x.src.c]];
      y.vals[d] = mask ? mapVals(r, x.src.lk, d, mask, x.src.fl) : null;
      const cv = covValue({ open: x.src.open, vals: y.vals }, -1, null);
      y.w = cv[0]; y.t = cv[1]; y.cover = cv[2]; y.next = cv[3];
      y.e = y.r > 0 ? y.r * (y.w + y.src.adj) - (1 - y.r) * y.src.lc : -Infinity;
      o.push(y);
    }
    const taken = new Set(st.taken); taken.add(q);
    const moved = st.moved.slice(); moved[d] = true;
    const cms = st.cms.slice(); cms[d] = cm;
    const xs = st.xs.slice(); xs[d] = q;
    return { m, cms, xs, moves: st.moves.concat([[d, q, a]]), moved, taken, tok: st.tok - 1, o };
  }
  // Overloads (step 21, Shaun, 17 Nov 2026: count numbers, not just pairs): a group of defenders (one, two or three)
  // who are the only cover for looks from more attackers than there are defenders. Each attacker brings his best
  // look of those only the group covers (worth read without the group). The defence's best assignment gives each
  // defender of the group one attacker he can take, or none; an attacker is left open if no taken attacker stands
  // within two squares of him (a Contest is from next to the shooter, so one defender can't be on both). The group is
  // worth the best look left open by the defence's best assignment, found by trying every assignment. One on two is
  // step 20's overload; two on three and three on four follow from the same rule. A group is named only if no
  // smaller group inside it is already worth as much.
  const LG_GROUP = 3;
  const nearKey = c => SX[c] >= 5 && SX[c] <= 11 && SY[c] >= 1 && SY[c] <= 7;
  function lgCovMask(x) {                              // the defenders who take anything off this look
    let m = 0;
    for (let d = 0; d < 5; d++) {
      const v = x.vals[d]; if (!v) continue;
      for (let t = 0; t < x.src.open.length; t++) if (v[t] < x.src.open[t]) { m |= 1 << d; break; }
    }
    return m;
  }
  // Step 25 (D-241, Shaun, 19 Nov 2026): a defender covers every look he can reach in time to contest, because only one
  // attacker can shoot. The exception is an overload: the offence creates the looks one after another (an action, the
  // defence's reaction, the next action), so covering the first leaves the second open. A look stays covered when the
  // defender who took another can still contest it, with the reaction's two actions, from a square next to the look
  // he took. It replaces "within two squares".
  const _CT = new Map();
  function coversToo(m, d, cv, cu) {
    const qs = m.s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d), key = ((cv * NSQ + cu) * 8 + qs) * 3 + mode;
    let hit = _CT.get(key);
    if (hit === undefined) {
      hit = false;
      for (let dir = 0; dir < 8 && !hit; dir++) { const p = cv + DSTEP[dir]; if (ONB[p] && p !== cu && anyArrow2(p, qs, mode)[BI[cu]]) hit = true; }
      _CT.set(key, hit);
    }
    return hit;
  }
  function lgGroupValue(A, ds, m) {                    // the best look the defence's best assignment leaves open
    let best = Infinity, pick = null;
    const k = ds.length, took = new Array(k).fill(-1);
    const go = i => {
      if (i === k) {
        let left = -Infinity, open = -1;
        for (let u = 0; u < A.length; u++) {
          if (took.includes(u)) continue;
          let far = true;
          for (let i = 0; i < k; i++) { const v = took[i]; if (v >= 0 && coversToo(m, ds[i], A[v].c, A[u].c)) { far = false; break; } }
          if (far && A[u].wd > left) { left = A[u].wd; open = u; }
        }
        if (left < best - 1e-9) { best = left; pick = { took: took.slice(), open }; }
        return;
      }
      took[i] = -1; go(i + 1);
      for (let u = 0; u < A.length; u++) {
        if (took.includes(u) || !(A[u].mask >> ds[i] & 1)) continue;
        took[i] = u; go(i + 1); took[i] = -1;
      }
    };
    go(0);
    return { value: best, pick };
  }
  function lgOverloads(st) {
    const looks = [];
    for (const x of st.o) {
      if (!(x.r > 0) || !(x.e > 0)) continue;
      const mask = lgCovMask(x); if (!mask) continue;
      let top = -Infinity, tt = 0;
      for (let t = 0; t < x.src.open.length; t++) if (x.src.open[t] > top) { top = x.src.open[t]; tt = t; }
      looks.push({ x, mask, wd: x.r * (top + x.src.adj) - (1 - x.r) * x.src.lc, tt });
    }
    const out = [], named = [];
    for (let k = 1; k <= LG_GROUP; k++) {
      const groups = [];
      const pickG = (from, ds) => { if (ds.length === k) { groups.push(ds.slice()); return; } for (let d = from; d < 5; d++) { ds.push(d); pickG(d + 1, ds); ds.pop(); } };
      pickG(0, []);
      for (const ds of groups) {
        let gm = 0; for (const d of ds) gm |= 1 << d;
        const by = new Map();                         // each attacker's best look that only the group covers
        for (const z of looks) {
          if ((z.mask & ~gm) || !(z.mask & gm)) continue;
          const a = z.x.src.a, cur = by.get(a);
          if (!cur || z.wd > cur.wd + 1e-9 || (Math.abs(z.wd - cur.wd) <= 1e-9 && lgBefore(z.x, cur.x) < 0)) by.set(a, z);
        }
        if (by.size <= k) continue;
        const A = [...by.values()].map(z => ({ a: z.x.src.a, c: z.x.src.c, t: z.tt, wd: z.wd, now: z.x.e, mask: z.mask }))
          .sort((u, v) => v.wd - u.wd || u.a - v.a);
        const g = lgGroupValue(A, ds, st.m);
        if (!(g.value > 0) || !isFinite(g.value)) continue;
        if (named.some(h => (h.gm & gm) === h.gm && h.value >= g.value - 1e-9)) continue;   // a smaller group says it already
        named.push({ gm, value: g.value });
        // the looks in the order the words need them: those the best assignment takes, then the one it leaves open
        const order = g.pick.took.filter(u => u >= 0).concat(g.pick.open >= 0 ? [g.pick.open] : []);
        for (let u = 0; u < A.length; u++) if (!order.includes(u)) order.push(u);
        out.push({ d: ds[0], ds, value: g.value, threats: order.map(u => A[u]).map(u => ({ a: u.a, c: u.c, t: u.t, worth: u.wd, now: u.now })),
          near_key: A.every(u => nearKey(u.c)) });
      }
    }
    return out;
  }
  // ---- Step 22b, continued (D-218 to D-221, Shaun, 18 Nov 2026): the defence's two responsibilities ----------------
  // "The defender's primary responsibility is their assigned player ... Your secondary objective is to protect high
  // value zones of the court with poor coverage. Regardless of whether that position can be reached in the next phase
  // or actions. And it is ranked by the average shot quality of all the offensive players compared to the square that
  // would be left with no zone of influence."
  // The zone gaps are a race (step 22c, D-228, Shaun, 18 Nov 2026: "Is one phase enough? A phase is only 2 seconds.").
  // A square is a gap only when an attacker can get there with the ball before any defender can arrive set to contest
  // it. Each side's phases are counted by the rules' movement (a Move and a Quick Step, or a Sprint, a phase), over as
  // many phases as the race takes, up to the shot clock. The attacker shoots at the start of the phase after he
  // arrives; a defender is there in time if by then he stands where the reaction's one Move lets him contest set. If
  // none can, the first who can still get a hand up off balance (the reaction's Quick Step or Sprint) brings that
  // contest. The gap is worth that attacker's shot from the square at his real chance of having the ball there (a
  // pass by the rules' chance as the defence stands), less that contest. A square every attacker loses the race to
  // is not a gap, however valuable. This replaces step 22b's average of all five whatever the reach.
  const DESC = (u, v) => v - u;
  const _PS = new Map(), _PD = new Map(), _AP = new Map();
  function phaseStep(p, qs) {                          // the squares one phase's movement reaches from p (bodies not counted)
    const key = p * 8 + qs;
    let hit = _PS.get(key); if (hit) return hit;
    const fr = geoReach(p, 0, qs, true, 1), set = new Set();
    for (const q of fr[0].keys()) if (ONB[q]) set.add(q);
    for (const q of fr[1].keys()) if (ONB[q]) set.add(q);
    set.delete(p);
    hit = Int16Array.from(set); _PS.set(key, hit); return hit;
  }
  function phaseDist(start, qs) {                      // phases of movement from start to every square
    const key = start * 8 + qs;
    let hit = _PD.get(key); if (hit) return hit;
    hit = new Int8Array(NSQ).fill(INF);
    hit[start] = 0;
    let frontier = [start];
    for (let level = 1; frontier.length; level++) {
      const next = [];
      for (const p of frontier) for (const q of phaseStep(p, qs)) if (hit[q] === INF) { hit[q] = level; next.push(q); }
      frontier = next;
    }
    _PD.set(key, hit); return hit;
  }
  function arrivePhases(start, qs, mode) {             // per board square: the phases before he can contest a shot there set, and at all
    const key = ((start * 8 + qs) * 3 + mode) * 4 + SOFTK;
    let hit = _AP.get(key); if (hit) return hit;
    const pd = phaseDist(start, qs), set = new Int8Array(NB).fill(INF), any = new Int8Array(NB).fill(INF);
    for (let p = 0; p < NSQ; p++) {
      const k = pd[p];
      if (!ONB[p] || k >= INF) continue;
      const cv = anyArrow2(p, qs, mode);
      for (let b = 0; b < NB; b++) { const v = cv[b]; if (!v) continue; if (k < any[b]) any[b] = k; if (((v >> 6) & 63) && k < set[b]) set[b] = k; }
    }
    hit = { set, any }; _AP.set(key, hit); return hit;
  }
  function gapInfo(r) {                                // every square a shot may go up from; each attacker's look there and its open value
    const ctx = r.s.ctx;
    let g = ctx._gap;
    if (!g) {
      const sq = [];
      for (let q = 0; q < ONB.length; q++) if (ONB[q] && SHOOT(szone(ctx, q)) && !(ctx.noRim && q === RIM)) sq.push(q);
      const looks = [], open = [];
      for (let k = 0; k < sq.length; k++) {
        const q = sq[k], pts = ctx.worth[szone(ctx, q)], types = ZONE_SHOTS[szone(ctx, q)], row = [], op = [];
        for (let a = 0; a < 5; a++) {
          const lk = makeLook(a, q, 'later', 1.0, false); lk.types = types; lk.rushed = false; row.push(lk);
          let top = -Infinity; for (const t of types) { const v = pts * cardShot(ctx, ctx.off[a], t, q); if (v > top) top = v; }
          op.push(top);
        }
        looks.push(row); open.push(op);
      }
      g = ctx._gap = { sq, looks, open, late: new Map(), idx: new Map(sq.map((q, k) => [q, k])) };
    }
    return g;
  }
  function gapLate(r, g, k, a, d) {                    // attacker a's shot on square k with defender d's hand up off balance
    const key = (k * 5 + a) * 5 + d;
    let v = g.late.get(key);
    if (v === undefined) {
      const ctx = r.s.ctx, lk = g.looks[k][a], pts = ctx.worth[szone(ctx, g.sq[k])], vals = mapVals(r, lk, d, 1, undefined);
      v = -Infinity;
      for (let t = 0; t < lk.types.length; t++) { const o = pts * cardShot(ctx, ctx.off[a], lk.types[t], g.sq[k]), w = vals && vals[t] < o ? vals[t] : o; if (w > v) v = w; }
      g.late.set(key, v);
    }
    return v;
  }
  function gapRace(m) {                                // the offence's side of the race: each attacker's phases to every square, the phases the clock leaves
    if (m.race) return m.race;
    const s = m.s;
    return m.race = { n: Math.floor(s.clock / 2) - 1, A: [0, 1, 2, 3, 4].map(a => (ONB[s.o[a]] ? phaseDist(s.o[a], s.ctx.off[a].qs) : null)), ch: new Map() };
  }
  function gapVec(st, d2, q2) {                        // every square's gap, the defence as the state has it (d2 on q2 instead, where given)
    const m = st.m, r = m.r, s = m.s, g = gapInfo(r), R = gapRace(m), out = new Float64Array(g.sq.length);
    const ap = [null, null, null, null, null], xs = st.xs;
    for (let d = 0; d < 5; d++) { const x = d === d2 ? q2 : xs[d]; if (ONB[x]) ap[d] = arrivePhases(x, s.ctx.dfn[d].qs, stanceMode(m.sN, d)); }
    for (let k = 0; k < g.sq.length; k++) {
      const q = g.sq[k], b = BI[q];
      let on = false, set = INF;
      for (let d = 0; d < 5; d++) {
        if ((d === d2 ? q2 : xs[d]) === q) { on = true; break; }
        if (ap[d] && ap[d].set[b] < set) set = ap[d].set[b];
      }
      if (on) continue;
      let best = 0;
      for (let a = 0; a < 5; a++) {
        const A = R.A[a];
        if (!A) continue;
        const T = A[q] < 1 ? 1 : A[q];                  // (on it already: he shoots as the next phase starts)
        if (T > R.n || set <= T) continue;             // the clock runs out first, or a defender is set there in time
        let w = g.open[k][a];
        if (!(w > best)) continue;
        for (let d = 0; d < 5; d++) if (ap[d] && ap[d].any[b] <= T) { const u = gapLate(r, g, k, a, d); if (u < w) w = u; }
        let ch = 1;
        if (a !== s.ball) { const key = a * 4096 + q; ch = R.ch.get(key); if (ch === undefined) { ch = covPass(s, a, q); R.ch.set(key, ch); } }
        if (!(ch > 0)) continue;
        const e = ch * w - (1 - ch) * TURNOVER_COST;
        if (e > best) best = e;
      }
      out[k] = best;
    }
    return out;
  }
  // The one list of things to cover (item 3): each attacker's best look as the defence stands, before it answers (his
  // looks by the map: value times reach by the rules' chances, the reaction's contest counted), and every square's
  // gap. Largest first. The defence plays to leave the lowest highest item, then the next highest, and so on (compared
  // best first: no weights, no sums); the offence plays to raise it.
  function lgList(st) {
    if (st.list) return st.list;
    const thr = [0, 0, 0, 0, 0];
    for (const x of st.o) if (x.r > 0 && x.e > thr[x.src.a]) thr[x.src.a] = x.e;
    const gv = gapVec(st), out = new Float64Array(5 + gv.length);
    out.set(thr, 0); out.set(gv, 5); out.sort(); out.reverse();
    st.thr = thr; st.gaps = gv;
    return st.list = out;
  }
  function lgScore(st) {
    const head = lgHead(st), worths = head.map(x => x.e);
    // (a group of two or three is named only when it is worth at least the best open look: it then explains the gap)
    const open0 = worths.length ? worths[0] : 0;
    const ov = lgOverloads(st).filter(v => v.ds.length === 1 || v.value >= open0 - 1e-9);
    let L = worths.length ? worths[0] : 0;
    for (const v of ov) if (v.value > L) L = v.value;
    return { L, worths, ov };
  }
  // Is answer a better for the defence than b? The lasting gap; then the list (what it leaves uncovered as it then
  // stands, largest first); then efficiency: the fewest actions. Then the moves' own order, so a position always reads the same.
  // Step 28 (D-262, Shaun, 19 Nov 2026): the list leads the map's own answer too (it was the last place the lasting gap
  // led); eval.answer_lead 'gap' puts step 20's lasting gap first again. The lasting gap is still read and shown.
  const answerGapFirst = () => D.config.eval.answer_lead === 'gap';
  function lgBetter(a, b) {
    const gf = answerGapFirst();
    if (gf) { if (a.sc.L < b.sc.L - 1e-9) return true; if (a.sc.L > b.sc.L + 1e-9) return false; }
    const la = lgList(a), lb = lgList(b);
    if (covLess(la, lb)) return true;
    if (covLess(lb, la)) return false;
    if (!gf) { if (a.sc.L < b.sc.L - 1e-9) return true; if (a.sc.L > b.sc.L + 1e-9) return false; }
    if (a.moves.length !== b.moves.length) return a.moves.length < b.moves.length;
    const x = a.m.s.x;                                 // (the moves' own order: square, arrow, where he starts; never the defender's number)
    for (let k = 0; k < a.moves.length; k++) {
      const u = a.moves[k], v = b.moves[k];
      if (u[1] !== v[1]) return u[1] < v[1];
      if (u[2] !== v[2]) return u[2] < v[2];
      if (x[u[0]] !== x[v[0]]) return x[u[0]] < x[v[0]];
    }
    return false;
  }
  // The quick re-read of a position with one defender somewhere else (the settlement's way of ranking where to look):
  // each attacker's best look with that defender's Contest from his new square in place of his old one, and every
  // square's gap with his influence moved. Bodies and walls on the way (what they do to the offence's reach) are not
  // in it: the full reading has those.
  function qPrep(st) {
    const m = st.m, g = gapInfo(m.r), byA = [[], [], [], [], []];
    for (const x of st.o) if (x.r > 0) byA[x.src.a].push(x);
    const list = lgList(st);
    return { st, m, g, byA, thr: st.thr, gaps: st.gaps, sorted: list, split: [null, null, null, null, null] };
  }
  function qSplit(Q, d) {
    if (Q.split[d]) return Q.split[d];
    const free = [], held = [];
    for (let a = 0; a < 5; a++) {
      const f = [], h = [];
      for (const x of Q.byA[a]) {
        if (x.vals[d]) h.push({ x, ewo: x.r * (covValue({ open: x.src.open, vals: x.vals }, d, null)[0] + x.src.adj) - (1 - x.r) * x.src.lc });
        else f.push(x);
      }
      f.sort((u, v) => v.e - u.e); h.sort((u, v) => v.ewo - u.ewo);
      free.push(f); held.push(h);
    }
    return Q.split[d] = { free, held };
  }
  function qThreat(Q, a, d, q, cm) {                   // attacker a's best look with defender d on q (his Contest cm)
    const sp = qSplit(Q, d), r = Q.m.r, soft = Q.m.s.ctx.soft;
    const re = x => {
      const mask = cm[BI[x.src.c]];
      const vals = mask ? mapVals(r, x.src.lk, d, mask, x.src.fl) : null;
      return x.r * (covValue({ open: x.src.open, vals: x.vals }, d, vals)[0] + x.src.adj) - (1 - x.r) * x.src.lc;
    };
    let best = 0;
    for (const x of sp.free[a]) {
      if (x.e <= best) break;
      if (x.src.c === q) continue;
      if (!cm[BI[x.src.c]]) { best = x.e; break; }
      const e = re(x); if (e > best) best = e;
    }
    for (const z of sp.held[a]) {
      if (z.ewo <= best) break;
      if (z.x.src.c === q) continue;
      const e = cm[BI[z.x.src.c]] ? re(z.x) : z.ewo; if (e > best) best = e;
    }
    return best;
  }
  function qOwn(Q, d, q, cm) {                         // what each attacker's best look is with only defender d on him, from q (largest first)
    const r = Q.m.r, one = [null, null, null, null, null], out = [];
    if (!Q.byOpen) {
      Q.byOpen = Q.byA.map(l => l.map(x => { let top = -Infinity; for (const v of x.src.open) if (v > top) top = v; return { x, e0: x.r * (top + x.src.adj) - (1 - x.r) * x.src.lc }; }).sort((u, v) => v.e0 - u.e0));
    }
    for (let a = 0; a < 5; a++) {
      let best = 0;
      for (const z of Q.byOpen[a]) {
        if (z.e0 <= best) break;
        const x = z.x;
        if (x.src.c === q) continue;
        const mask = cm[BI[x.src.c]];
        if (!mask) { best = z.e0; break; }
        one[d] = mapVals(r, x.src.lk, d, mask, x.src.fl);
        const e = x.r * (covValue({ open: x.src.open, vals: one }, -1, null)[0] + x.src.adj) - (1 - x.r) * x.src.lc;
        one[d] = null;
        if (e > best) best = e;
      }
      out.push(best);
    }
    return out.sort(DESC);
  }
  function qList(Q, d, q, cm) {                        // the list with defender d on q: the items that change swapped for what they become
    const rem = [], add = [], st = Q.st;
    for (let a = 0; a < 5; a++) { const t = qThreat(Q, a, d, q, cm); if (Math.abs(t - Q.thr[a]) > 1e-9) { rem.push(Q.thr[a]); add.push(t); } }
    const gv = gapVec(st, d, q);                       // the race for every square, run again with him there
    for (let k = 0; k < gv.length; k++) if (Math.abs(gv[k] - Q.gaps[k]) > 1e-9) { rem.push(Q.gaps[k]); add.push(gv[k]); }
    if (!rem.length) return Q.sorted;
    rem.sort(DESC); add.sort(DESC);
    const base = Q.sorted, out = new Float64Array(base.length);
    let i = 0, j = 0, u = 0, n = 0;
    while (n < out.length) {
      while (i < base.length && j < rem.length && base[i] === rem[j]) { i++; j++; }
      if (u < add.length && (i >= base.length || add[u] >= base[i])) out[n++] = add[u++];
      else if (i < base.length) out[n++] = base[i++];
      else break;
    }
    return out;
  }
  // The settlement in play (items 3 and 4): the one or two movements of this defence turn that leave the least on the
  // list, by the quick re-read. The most valuable uncovered item is claimed first, by whoever covers it best; then the
  // next. The costs are real: only the movement each defender has left this phase, one each, within the tokens. A tie
  // goes to the Move before the Quick Step or Sprint, then to the lower square, so the answer never turns on the order
  // the defenders are listed in. -> [[defender, square, arrow or -1 for a Move (any arrow)]]: the search tries them.
  function settleMoves(m) {
    const s = m.s, out = [];
    let st = lgRoot(m);
    for (let round = 0; round < 2 && st.tok > 0; round++) {
      const Q = qPrep(st);
      let best = null;
      for (let d = 0; d < 5; d++) {
        if (st.moved[d] || !ONB[s.x[d]]) continue;
        const cp = caps(s, 'X', d);
        if (!cp[0] && cp[1] <= 0) continue;
        const qs = s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d), fr = defenderReachExact(s, d);
        const offer = (q, a, cm) => {
          const list = qList(Q, d, q, cm);
          if (list === Q.sorted || !covLess(list, Q.sorted)) return;
          if (best !== null) {
            if (covLess(best.list, list)) return;
            if (!covLess(list, best.list)) {             // level: a Move first, then the lower square, arrow, starting square
              const u = [a < 0 ? 0 : 1, q, a, s.x[d]], v = [best.a < 0 ? 0 : 1, best.q, best.a, s.x[best.d]];
              let k = 0; while (k < 4 && u[k] === v[k]) k++;
              if (k === 4 || u[k] > v[k]) return;
            }
          }
          best = { d, q, a, cm, list };
        };
        if (cp[0]) offer(s.x[d], -1, anyArrow2(s.x[d], qs, mode));
        for (const [q, n] of fr[0]) if (n === 1 && !st.taken.has(q)) offer(q, -1, anyArrow2(q, qs, mode));
        for (const [q, arrs] of fr[1]) if (!st.taken.has(q)) for (const [a, n] of arrs) if (n === 1) offer(q, a, cm2Cached(q, a, qs, mode));
      }
      if (best === null) break;
      out.push([best.d, best.q, best.a]);
      st = lgChild(m, st, best.d, best.q, best.a, best.cm);
    }
    return out;
  }
  function lasting(m) {
    const s = m.s, r = m.r, soft = s.ctx.soft;
    const BEAM = LG_BEAM, WIDE = LG_WIDE;
    const root = lgRoot(m); root.sc = lgScore(root);
    let best = root, frontier = [root];
    for (let depth = 0; depth < 5 && frontier.length; depth++) {
      const nexts = [];
      for (const st of frontier) {
        if (st.tok <= 0) continue;
        const head = lgHead(st), cur = head.map(x => x.e);
        if (!head.length || !(head[0].e > 0)) continue;
        const cands = [], seen = new Set();
        const offer = (d, q, a, cm) => {
          const key = (d * 4096 + q) * 9 + (a + 1);
          if (seen.has(key)) return;
          seen.add(key);
          const after = [];
          let touched = false;
          for (const x of head) {
            let e;
            if (x.src.c === q) e = -Infinity;
            else {
              const mask = cm[BI[x.src.c]];
              const vals = mask ? mapVals(r, x.src.lk, d, mask, x.src.fl) : null;
              e = x.r * (covValue({ open: x.src.open, vals: x.vals }, d, vals)[0] + x.src.adj) - (1 - x.r) * x.src.lc;
            }
            if (e < x.e - 1e-9) touched = true;
            after.push(e);
          }
          if (!touched) return;
          after.sort((u, v) => v - u);
          if (covLess(after, cur)) cands.push({ d, q, a, cm, after });
        };
        for (let d = 0; d < 5; d++) {
          if (st.moved[d] || !ONB[s.x[d]]) continue;
          const cp = caps(s, 'X', d);
          if (!cp[0] && cp[1] <= 0) continue;
          const qs = s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d), fr = defenderReachExact(s, d);
          if (cp[0]) offer(d, s.x[d], -1, anyArrow2(s.x[d], qs, mode));       // a Move on the spot: a new arrow
          for (const [q, n] of fr[0]) if (n === 1 && !st.taken.has(q)) offer(d, q, -1, anyArrow2(q, qs, mode));
          for (const [q, arrs] of fr[1]) if (!st.taken.has(q)) for (const [a, n] of arrs) if (n === 1) offer(d, q, a, cm2Cached(q, a, qs, mode));
        }
        // (a tie: the lower square, the arrow, then where he starts: never the order the defenders are listed in, D-219)
        cands.sort((u, v) => (covLess(u.after, v.after) ? -1 : covLess(v.after, u.after) ? 1 : (u.q - v.q || u.a - v.a || s.x[u.d] - s.x[v.d])));
        for (const c of cands.slice(0, WIDE)) {
          const ch = lgChild(m, st, c.d, c.q, c.a, c.cm);
          ch.sc = lgScore(ch);
          nexts.push(ch);
        }
      }
      if (!nexts.length) break;
      nexts.sort((u, v) => (lgBetter(u, v) ? -1 : lgBetter(v, u) ? 1 : 0));
      frontier = nexts.slice(0, BEAM);
      if (lgBetter(frontier[0], best)) best = frontier[0];
    }
    best.root = root;
    return best;
  }
  // The lasting gap of a position -> { L, before, best, ov, moves, m } (numbers only). Step 21 (Shaun, 17 Nov 2026,
  // D-206): read with what each side really has left this phase: its tokens and movement, who is locked or rushed, who
  // has already moved. A spent or beaten defender can't recover inside the phase, and the map says so. fresh: step 20's
  // like-for-like read (covFresh), kept for the reports' phase starts, where both sides really are fresh.
  // A pass in the air (step 21, part 4): the ball where it is; the catch by the rules' own chance (covPass, the
  // defence's interceptions from where it stands now). Caught: the receiver's lasting gap. Intercepted (D-198): -5,
  // the phase ends and the next starts with the ball back with the passer, read fresh.
  function lastingOf(s, r0, fresh) {
    if (s.stage !== 'play' || s.clock <= 2) return null;
    if (fresh) {
      const f = covFresh(s);
      const m = covBuild(f, true, r0 && r0.s === f ? r0 : null);
      const best = lasting(m);
      return { L: best.sc.L, before: m.sorted.length ? m.sorted[0].e : 0, ov: best.sc.ov.length, moves: best.moves.length, m, best };
    }
    if (s.pending) {
      const recv = s.pending[1], base = W_(s, { pending: null, approach: -1 });
      const p = covPass(base, recv, s.o[recv]);
      const gc = lastingOf(W_(base, { ball: recv }), null, false);
      const gl = s.clock - 2 > 2 ? lastingOf(base, null, true) : null;
      const L = p * (gc ? gc.L : 0) + (1 - p) * ((gl ? gl.L : 0) - TURNOVER_COST);
      return { L, before: gc ? gc.before : 0, ov: gc ? gc.ov : 0, moves: gc ? gc.moves : 0, m: gc ? gc.m : null, best: gc ? gc.best : null, catch: p };
    }
    const f = covOffFresh(s);
    const m = covBuild(f, true, null);
    const best = lasting(m);
    // step 22 (D-211): the three-second rule's -5, for each attacker in the key at the last phase end who can't
    // leave it before this phase ends with what the offence really has left
    const three = threeSecondsOwed(s);
    return { L: best.sc.L - TURNOVER_COST * three, before: m.sorted.length ? m.sorted[0].e : 0, ov: best.sc.ov.length, moves: best.moves.length, m, best, three };
  }
  // A position's reading for either side (D-219): the lasting gap; the list as the defence stands (each attacker's
  // best look before it answers, every square's gap), largest first; the defence's actions its answer needs.
  const OFFSQ = C(-1, 1);
  function readingOf(g) {
    if (!g || !g.best) return { L: g ? g.L : 0, list: [], n: 0, m: null };
    return { L: g.L, list: lgList(g.best.root), n: g.best.moves.length, m: g.m };
  }
  // each defender's own cover of his own man, under the assignment the position reads (largest first): what tells two
  // placements apart when the list and the lasting gap can't (step 22c: the first responsibility is the assigned man)
  const rdOwn = k => (k.own !== undefined ? k.own : (k.own = k.m ? assignOf(k.m, null, false).vec : []));
  const drvJSON = k => ({ L: +k.L.toFixed(2), n: k.n, list: Array.from(k.list, v => +v.toFixed(2)), own: rdOwn(k).map(v => +v.toFixed(2)) });
  const RD = { lead: 'gap' };                           // 'gap': the lasting gap, then the list; 'list': the list, then the lasting gap
  function rdLess(a, b) {                              // is a better for the defence than b?
    if (RD.lead === 'list') { if (covLess(a.list, b.list)) return true; if (covLess(b.list, a.list)) return false; }
    if (a.L < b.L - 1e-9) return true; if (a.L > b.L + 1e-9) return false;
    if (RD.lead !== 'list') { if (covLess(a.list, b.list)) return true; if (covLess(b.list, a.list)) return false; }
    const oa = rdOwn(a), ob = rdOwn(b);
    if (covLess(oa, ob)) return true; if (covLess(ob, oa)) return false;
    return a.n < b.n;
  }
  function rdWhy(a, b) {                               // what tells a from b
    const dl = covLess(a.list, b.list) || covLess(b.list, a.list), dg = Math.abs(a.L - b.L) > 1e-9;
    const dn = covLess(rdOwn(a), rdOwn(b)) || covLess(rdOwn(b), rdOwn(a)) ? 'his own man' : a.n !== b.n ? 'efficiency' : 'level';
    if (RD.lead === 'list') return dl ? 'the list' : dg ? 'the lasting gap' : dn;
    return dg ? 'the lasting gap' : dl ? 'the list' : dn;
  }
  function rdBetterO(a, b) {                           // is a better for the offence than b? the mirror: it plays to raise the list
    if (a.L > b.L + 1e-9) return true; if (a.L < b.L - 1e-9) return false;
    return covLess(b.list, a.list);
  }
  const cardKey = (ctx, d) => { const k = ctx._ck || (ctx._ck = ctx.dfn.map(c => JSON.stringify(c))); return k[d]; };
  // The defence's setup (D-213, D-216, D-219): all five placed together, every square and every arrow open to each.
  // Nobody starts anywhere: the defenders are put down one at a time, each time the one defender and square that
  // leave the least on the list (the most valuable uncovered item is claimed first, by whoever covers it best), and
  // then any defender may move again, one at a time, while a change leaves less. Where to look is ranked by the quick
  // re-read (qList); the best few squares are then read in full (the lasting gap, the list with bodies and walls
  // counted, efficiency), and the chosen square in full with each of the eight arrows. Nothing in it turns on the
  // order the defenders are listed in: a tie goes to the lower square, then the arrow, then the card itself.
  const SETUP_K = 10;
  function settleSetup(s0, evals) {
    const ctx = s0.ctx;
    let s = W_(covOffFresh(s0), { x: [OFFSQ, OFFSQ, OFFSQ, OFFSQ, OFFSQ], arrows: [0, 0, 0, 0, 0] });
    let used = 0, cur = null;
    const steps = [], placed = [false, false, false, false, false];
    const put = (d, q, a) => W_(s, { x: setAt(s.x, d, q), arrows: setAt(s.arrows, d, a) });
    const been = new Set(), mark = t => t.x.join(',') + '|' + t.arrows.join(',');       // (the quick re-read can't see bodies and walls: never the same shape twice)
    // (level on the list: the placement from which he alone would contain the attackers best: his first responsibility)
    const before = (u, v) => (covLess(u.list, v.list) ? -1 : covLess(v.list, u.list) ? 1 : covLess(u.own, v.own) ? -1 : covLess(v.own, u.own) ? 1 :
      (u.q - v.q || (cardKey(ctx, u.d) < cardKey(ctx, v.d) ? -1 : cardKey(ctx, u.d) > cardKey(ctx, v.d) ? 1 : u.d - v.d)));
    const step = placing => {
      const m = covBuild(s, true, null), st = lgRoot(m), Q = qPrep(st), cands = [];
      for (let d = 0; d < 5; d++) {
        if (placing ? placed[d] : !placed[d]) continue;
        const qs = ctx.dfn[d].qs, mode = stanceMode(m.sN, d);
        for (let q = 0; q < ONB.length; q++) {
          if (!ONB[q] || (st.taken.has(q) && q !== s.x[d])) continue;
          const cm = anyArrow2(q, qs, mode), list = qList(Q, d, q, cm);
          if (!placing && !(list !== Q.sorted && covLess(list, Q.sorted)) && q !== s.x[d]) continue;   // a move must leave less (his own square stays in, for his arrows)
          cands.push({ d, q, list, own: qOwn(Q, d, q, cm) });
        }
      }
      if (!cands.length) return false;
      cands.sort(before);
      const arrowBy = c => {                           // the arrow the quick re-read likes best there (a tie: the lower arrow)
        const qs = ctx.dfn[c.d].qs, mode = stanceMode(m.sN, c.d);
        let ba = 0, bl = null;
        for (let a = 0; a < 8; a++) { const l = qList(Q, c.d, c.q, cm2Cached(c.q, a, qs, mode)); if (bl === null || covLess(l, bl)) { bl = l; ba = a; } }
        return [ba, bl];
      };
      if (used >= evals) {                             // no full reads left: the quick re-read alone, the arrow he would really have
        let pick = null;
        for (const c of cands.slice(0, SETUP_K)) {
          const ab = arrowBy(c);
          if (c.q === s.x[c.d] && ab[0] === s.arrows[c.d]) continue;
          if (pick === null || covLess(ab[1], pick.l)) pick = { c, a: ab[0], l: ab[1] };
        }
        if (pick === null || (!placing && !(pick.l !== Q.sorted && covLess(pick.l, Q.sorted)))) return false;
        if (been.has(mark(put(pick.c.d, pick.c.q, pick.a)))) return false;
        s = put(pick.c.d, pick.c.q, pick.a); placed[pick.c.d] = true; been.add(mark(s));
        steps.push({ d: pick.c.d, to: sqName(pick.c.q), arrow: pick.a, by: 'the quick re-read' });
        return true;
      }
      let best = null, second = null;
      for (const c of cands.slice(0, SETUP_K)) {
        const a = arrowBy(c)[0];
        if (c.q === s.x[c.d] && a === s.arrows[c.d]) continue;
        const rd = readingOf(lastingOf(put(c.d, c.q, a))); used++;
        const z = { d: c.d, q: c.q, a, rd };
        if (best === null || rdLess(rd, best.rd)) { second = best; best = z; } else if (second === null || rdLess(rd, second.rd)) second = z;
      }
      if (best === null) return false;
      for (let a = 0; a < 8; a++) {                    // the chosen square with every arrow, in full
        if (a === best.a || (best.q === s.x[best.d] && a === s.arrows[best.d])) continue;
        const rd = readingOf(lastingOf(put(best.d, best.q, a))); used++;
        if (rdLess(rd, best.rd)) { second = best; best = { d: best.d, q: best.q, a, rd }; }
      }
      if (!placing && !(cur !== null && rdLess(best.rd, cur))) return false;
      steps.push({ d: best.d, to: sqName(best.q), arrow: best.a, by: placing ? (second ? rdWhy(best.rd, second.rd) : 'level') : rdWhy(best.rd, cur) });
      s = put(best.d, best.q, best.a); placed[best.d] = true; cur = best.rd; been.add(mark(s));
      return true;
    };
    for (let k = 0; k < 5; k++) if (!step(true)) break;
    if (cur === null && used < evals) { cur = readingOf(lastingOf(s)); used++; }
    // (a move the quick re-read alone chose, the full reads spent, is kept only if the full reading is better for it)
    const refine = n => {
      for (let k = 0; k < n; k++) {
        const s1 = s, c1 = cur, n1 = steps.length, quick = used >= evals;
        if (!step(false)) break;
        if (!quick) continue;
        const rd = readingOf(lastingOf(s)); used++;
        if (c1 === null || rdLess(rd, c1)) cur = rd; else { s = s1; cur = c1; steps.length = n1; break; }
      }
    };
    refine(12);
    // Step 22c (D-224): the last pass, read with bodies and walls counted. What a defender next to the ball handler
    // takes (the Steal, the closely guarded count, a wall across the way he would go), and what a body or a wall does
    // anywhere, is nothing the quick re-read can see. So every defender is tried on each square next to the ball
    // handler and on each square next to his own, with each of the eight arrows: the list as the defence would stand
    // is read for each, and those that leave the least are read in full. The best is kept if it leaves less. The
    // others may then move again, and so on while anything changes.
    const listAt = t => lgList(lgRoot(covBuild(t, true, null)));
    for (let round = 0; round < 8 && evals > 0 && cur !== null; round++) {
      const bh = s.o[s.ball], cands = [];
      for (let d = 0; d < 5; d++) {
        const sqs = new Set();
        for (let dir = 0; dir < 8; dir++) sqs.add(bh + DSTEP[dir]);
        for (let q = 0; q < ONB.length; q++) if (ONB[q] && cheb(q, s.x[d]) <= 1) sqs.add(q);
        for (const q of sqs) {
          if (!ONB[q] || (q !== s.x[d] && (s.o.includes(q) || s.x.includes(q)))) continue;
          for (let a = 0; a < 8; a++) {
            if (q === s.x[d] && a === s.arrows[d]) continue;
            const list = listAt(put(d, q, a)); used++;
            if (!covLess(cur.list, list)) cands.push({ d, q, a, list, ck: cardKey(ctx, d) });
          }
        }
      }
      cands.sort((u, v) => (covLess(u.list, v.list) ? -1 : covLess(v.list, u.list) ? 1 : u.q - v.q || u.a - v.a || (u.ck < v.ck ? -1 : u.ck > v.ck ? 1 : 0)));
      let best = null;
      for (const c of cands.slice(0, 16)) {
        if (covLess(cands[0].list, c.list)) break;     // only those level with the least
        const rd = readingOf(lastingOf(put(c.d, c.q, c.a))); used++;
        if (rdLess(rd, cur) && (best === null || rdLess(rd, best.rd))) best = { d: c.d, q: c.q, a: c.a, rd };
      }
      if (best === null || been.has(mark(put(best.d, best.q, best.a)))) break;
      steps.push({ d: best.d, to: sqName(best.q), arrow: best.a, by: rdWhy(best.rd, cur), pressure: adjacent(best.q, bh), last: true });
      s = put(best.d, best.q, best.a); cur = best.rd; been.add(mark(s));
      refine(6);
    }
    const g = lastingOf(s);
    return { s, g, rd: readingOf(g), steps, evals: used };
  }
  // The offence's setup over every square (D-216): attacker i tried on every empty square of the court, the defence
  // as it stands (its answer during the phase counted, as always), ranked by the offence's mirror of the reading.
  // Step 24: squares (the attacker's candidate squares, where given) limits where he is tried; quick reads only the
  // list as the defence stands (no answer searched), for ranking where to look.
  function offSweep(s0, i, keep, squares, quick) {
    const s = covOffFresh(s0), occ = new Set();
    for (let k = 0; k < 5; k++) { occ.add(s.o[k]); occ.add(s.x[k]); }
    const only = squares ? new Set(squares.map(parseSq)) : null;
    const out = [];
    for (let q = 0; q < ONB.length; q++) {
      if (!ONB[q] || (occ.has(q) && q !== s.o[i]) || (only && !only.has(q))) continue;
      const t = W_(s, { o: setAt(s.o, i, q) });
      if (quick) { const list = lgList(lgRoot(covBuild(t, true, null))); out.push({ q, k: { L: list.length ? list[0] : 0, list, n: 0, m: null } }); continue; }
      const g = lastingOf(t);
      if (g) out.push({ q, k: readingOf(g) });
    }
    out.sort((u, v) => (rdBetterO(u.k, v.k) ? -1 : rdBetterO(v.k, u.k) ? 1 : u.q - v.q));
    return out.slice(0, keep || 12);
  }
  // Assignments (item 4): every defender has one assigned attacker. Read from the position by an assignment over all
  // five at once (so it never turns on the order they are listed in): each attacker's best look with only one
  // defender on him, for every pairing; the assignment that leaves the lowest highest of those, then the next (best
  // first). prev: the assignments as they were: they stand unless another leaves strictly less (a switch is called
  // only when it covers more; on a tie everyone keeps his man). -> { perm[defender] = attacker, open[a], alone[a][d] }
  const PERMS = (() => { const out = []; const go = (p, left) => { if (!left.length) { out.push(p); return; } for (let k = 0; k < left.length; k++) go(p.concat([left[k]]), left.slice(0, k).concat(left.slice(k + 1))); }; go([], [0, 1, 2, 3, 4]); return out; })();
  function assignOf(m, prev, fixed) {                  // fixed: the assignments as they are, only read (no switch is called here)
    const s = m.s, open = [0, 0, 0, 0, 0], alone = [0, 1, 2, 3, 4].map(() => [0, 0, 0, 0, 0]), one = [null, null, null, null, null];
    for (const o of m.options) {
      if (!(o.r > 0)) continue;
      let top = -Infinity; for (const v of o.open) if (v > top) top = v;
      const e0 = o.r * (top + o.adj) - (1 - o.r) * o.lc;
      if (e0 > open[o.a]) open[o.a] = e0;
      for (let d = 0; d < 5; d++) {
        let e = e0;
        if (o.vals[d]) { one[d] = o.vals[d]; e = o.r * (covValue({ open: o.open, vals: one }, -1, null)[0] + o.adj) - (1 - o.r) * o.lc; one[d] = null; }
        if (e > alone[o.a][d]) alone[o.a][d] = e;
      }
    }
    // attacker a's best look with some defenders taken out of it (bits), the rest as they stand
    const memo = new Map();
    const without = (a, out) => {
      const key = a * 32 + out;
      let best = memo.get(key);
      if (best !== undefined) return best;
      best = 0;
      const vals = [null, null, null, null, null];
      for (const o of m.options) {
        if (o.a !== a || !(o.r > 0)) continue;
        for (let d = 0; d < 5; d++) vals[d] = (out >> d) & 1 ? null : o.vals[d];
        const e = o.r * (covValue({ open: o.open, vals }, -1, null)[0] + o.adj) - (1 - o.r) * o.lc;
        if (e > best) best = e;
      }
      memo.set(key, best);
      return best;
    };
    // Step 22c (D-226, Shaun, 18 Nov 2026): two defenders helping count as a takeover. A beaten defender's man is
    // taken when his teammates already cover that man between them: they leave him less than the beaten defender
    // alone would. The helpers are the teammates who take something off that man's best look. Beaten: a Dribble won
    // against him this phase, or locked, or his man has the ball nearer the rim than he stands (the ball has gone
    // past him).
    const beaten = (d, a) => s.beaten.some(b => b[1] === d) || isLocked(s, 'X', d) || (a === s.ball && ONB[s.o[a]] && DR[s.o[a]] < DR[s.x[d]]);
    const helpers = (d, a) => {
      if (!beaten(d, a)) return null;
      const wo = without(a, 1 << d);
      if (!(wo < alone[a][d] - 0.5)) return null;
      const H = [];
      for (let e = 0; e < 5; e++) if (e !== d && ONB[s.x[e]] && alone[a][e] < open[a] - 0.5) H.push(e);
      return H.length ? H : null;
    };
    const vec = p => p.map((a, d) => alone[a][d]).sort(DESC);
    const info = { open, alone, without, helpers };
    if (prev && fixed) return { perm: prev.slice(), kept: true, takeover: null, vec: vec(prev), ...info };
    // the takeover first: the man the help has is handed over, and his defender picks up what the helpers left: one
    // of the helpers' own men, whichever leaves every defender covering his own man best (a tie: the man left with
    // the most, then the helper standing on the lower square)
    let tk = null;
    if (prev) {
      const due = [];
      for (let d = 0; d < 5; d++) { if (!ONB[s.x[d]]) continue; const H = helpers(d, prev[d]); if (H) due.push({ d, a: prev[d], H }); }
      if (due.length) {
        due.sort((u, v) => without(v.a, 0) - without(u.a, 0) || s.x[u.d] - s.x[v.d]);
        const t = due[0];
        const swap = h => { const p = prev.slice(); p[t.d] = prev[h]; p[h] = t.a; return p; };
        let e = t.H[0], ve = vec(swap(e));              // (whichever helper's man leaves each defender covering his own best)
        for (const h of t.H.slice(1)) {
          const vh = vec(swap(h));
          if (covLess(vh, ve) || (!covLess(ve, vh) && (alone[prev[h]][h] > alone[prev[e]][e] + 1e-9 || (Math.abs(alone[prev[h]][h] - alone[prev[e]][e]) <= 1e-9 && s.x[h] < s.x[e])))) { e = h; ve = vh; }
        }
        const perm = swap(e), left = prev[e];
        tk = { perm, kept: false, takeover: { x: t.d, man: t.a, helpers: t.H, picks: left }, vec: vec(perm), ...info };
      }
    }
    // Step 22d (D-230, Shaun, 18 Nov 2026): a defender's man is named by who is nearest: the attackers in order of the
    // best look each has open, each takes the nearest free defender who takes something off that look (a tie: the one
    // who leaves him less, then the lower square). An attacker nobody free takes anything off gets the nearest free
    // defender. An assignment the help has already taken over is not gone back to while another is there.
    const named = () => {
      const order = [0, 1, 2, 3, 4].filter(a => ONB[s.o[a]]).sort((u, v) => open[v] - open[u] || s.o[u] - s.o[v]);
      const off = [0, 1, 2, 3, 4].filter(a => !ONB[s.o[a]]);
      const p = [-1, -1, -1, -1, -1], free = d => p[d] < 0;
      const dist = (d, a) => (ONB[s.x[d]] && ONB[s.o[a]] ? cheb(s.x[d], s.o[a]) : 99);
      const pick = (a, ok) => {
        let e = -1;
        for (let d = 0; d < 5; d++) {
          if (!free(d) || !ok(d)) continue;
          if (e < 0 || dist(d, a) < dist(e, a) || (dist(d, a) === dist(e, a) && (alone[a][d] < alone[a][e] - 1e-9 || (Math.abs(alone[a][d] - alone[a][e]) <= 1e-9 && s.x[d] < s.x[e])))) e = d;
        }
        if (e >= 0) p[e] = a;
        return e >= 0;
      };
      const left = [];
      for (const a of order) if (!pick(a, d => ONB[s.x[d]] && alone[a][d] < open[a] - 0.5 && helpers(d, a) === null)) left.push(a);
      for (const a of left.concat(off)) if (!pick(a, d => helpers(d, a) === null)) pick(a, () => true);
      return p;
    };
    const near = named(), vn = vec(near);
    // step 28: a takeover stands unless the named matchups cover more than it does, so a read settles at once (read
    // again with nothing changed, it stands); with the contest now an action (D-261) the takeover's own pick can be beaten
    if (tk) return covLess(vn, tk.vec) ? { perm: near, kept: false, takeover: null, vec: vn, ...info } : tk;
    // with assignments standing, a switch is called only when the named matchups cover more (D-220)
    if (prev && !covLess(vn, vec(prev))) return { perm: prev.slice(), kept: true, takeover: null, vec: vec(prev), ...info };
    return { perm: near, kept: false, takeover: null, vec: vn, ...info };
  }
  // Step 22b (D-219): the largest item on the list of things to cover, the defence as it stands and before it answers
  // (the offence acts first): read as the lasting gap is (lastingOf): each side with what it has left; a pass in the
  // air by the catch's chance; the three-second rule's -5 counted. null in the last phase.
  // Step 25 (D-242, Shaun, 19 Nov 2026): the shot bar is the value of playing on, counted phase by phase. With no phase
  // left any shot beats none (0). With n phases left the offence can take any look the map gives it: reached (its
  // chance by the rules) it is worth its value, or playing on if that is more; missed, playing on from one phase fewer,
  // less what the miss costs (a lost pass -5, a lost Dribble nothing). Fewer phases, fewer chances to improve: the bar
  // barely drops early and faster late. No curve is set by hand. -> [{phase, clock, bar}] from this phase on.
  function barsOf(s) {
    const g = lastingOf(s);
    const out = [];
    const n0 = Math.floor(s.clock / 2) - 1;
    const V = [0];
    if (g && g.best) {
      const opts = [];
      for (const x of g.best.o) if (x.r > 0 && isFinite(x.w)) opts.push([x.r, x.w + x.src.adj, x.src.lc]);
      for (let n = 1; n <= n0; n++) {
        const prev = V[n - 1];
        let v = Math.max(prev, g.L);
        for (const [r, val, lc] of opts) { const e = r * Math.max(val, prev) + (1 - r) * (prev - lc); if (e > v) v = e; }
        V.push(v);
      }
    }
    for (let k = 0, c = s.clock; c > 0; k++, c -= 2) { const n = Math.floor(c / 2) - 1; out.push({ phase: k + 1, clock: c, bar: n > 0 && V[n] !== undefined ? +V[n].toFixed(2) : 0 }); }
    return out;
  }
  function topOf(s) {
    if (s.stage !== 'play' || s.clock <= 2) return null;
    const read = f => lgList(lgRoot(covBuild(f, true, null)))[0];
    if (s.pending) {
      const recv = s.pending[1], base = W_(s, { pending: null, approach: -1 });
      const p = covPass(base, recv, s.o[recv]);
      const tc = topOf(W_(base, { ball: recv }));
      const tl = s.clock - 2 > 2 ? read(covFresh(base)) : 0;
      return p * (tc === null ? 0 : tc) + (1 - p) * (tl - TURNOVER_COST);
    }
    return read(covOffFresh(s)) - TURNOVER_COST * threeSecondsOwed(s);
  }
  function threeSecondsStuck(s) {                       // the attackers threeSecondsOwed counts, as a bitmask
    if (!s.ctx.three || !s.key_o) return 0;
    let m = 0;
    for (let i = 0; i < 5; i++) {
      if (!((s.key_o >> i) & 1) || !INKEY[s.o[i]]) continue;
      const out = s.tok_o > 0 && (canMoveKind(s, 'O', i, 'move') || canMoveKind(s, 'O', i, 'qs') || canMoveKind(s, 'O', i, 'sprint'));
      if (!out) m |= 1 << i;
    }
    return m;
  }
  function threeSecondsOwed(s) { let m = threeSecondsStuck(s), n = 0; while (m) { n += m & 1; m >>= 1; } return n; }
  // ---- Step 31 (D-284, Shaun, 25 Nov 2026): the possession's value ------------------------------------------------------
  // "Take every look the offence can get, best first. Each has a chance of being open in time. The offence takes the
  // best one that opens. Take off the risks, add the fouls drawn, and read ahead over the phases left." One number,
  // both sides: the offence acts to raise it, the defence to lower it. On the game's own scale (rating less contest,
  // times points; a turnover -5, a foul +5).
  // The looks are the map's (covBuild): who, where, the chance he has the ball there (the pass by the rules, the
  // Dribble by the rules), and the shot's worth against the best contest it faces as the defence stands. Looks that
  // share a cause are one route (D-294): the same attacker's squares are one route (he can be in one place), the
  // looks behind one pass are that pass, the looks behind a Dribble are that Dribble. A route that needs a roll ends
  // the turn by the rules, so falling back is limited by the actions: a lost pass is -5 and the phase (no fall-back);
  // a lost Dribble locks him and costs nothing, and he may still pass from where he stands, off balance (the one
  // fall-back the rules leave inside a phase). An open look is taken when it beats playing on.
  // Playing on is the shot bar, counted from the same looks: U(0) = -5 (the shot clock runs out, D-198);
  // U(n) = the best route when playing on is worth U(n - 1). With k phases after this one the possession is worth
  // U(k + 1). No curve is set by hand. The search reads ahead with it at the end of every line.
  // The defence's answer is inside the number (the design: "each has a chance of being open in time ... before that
  // defence closes it"). The game has no dice on movement, so "in time" is the race: with the actions the defence has
  // left this phase it closes what it can, one defender's movement at a time, each the movement that leaves the least
  // (the value first; where two leave the same value, the looks left behind it, largest first: the list, as a
  // tie-break), until none lowers it. What it cannot close is what the possession is worth. Each defender moves once
  // (as the lasting gap read it), a Move with any of the eight arrow pairs, a Quick Step or Sprint with the arrow it
  // leaves him. A movement that touches none of the looks the value turns on can't change it and isn't tried (a cut
  // that can't change the answer: the value is the largest of the routes, each a function of its own look).
  const PV = { cap: 0, V: null, W: null, vec2: new Float64Array(6), tmp: new Float64Array(8) };   // working storage, reused by every reading
  function pvRoom(n) {
    if (n <= PV.cap) return;
    PV.cap = Math.max(256, n * 2);
    PV.V = new Float64Array(PV.cap); PV.W = new Float64Array(PV.cap);
  }
  // T(B): the best route when playing on is worth B. Looks L[i] (the map's options), their worths V[i] (after the
  // contests they face). left: the offence's actions less those spent getting men out of the key. vec (6): each
  // attacker's best route value, the ball handler's free route in his own slot and his Dribble route in slot 5.
  function routeT(L, n, V, b, B, left, keyMask, cut, vec, act, it) {
    let best = B, fall = B, fi = -1;
    if (vec) vec.fill(-Infinity);
    for (let i = 0; i < n; i++) {                      // the passes first: a lost Dribble may fall back on one
      const o = L[i];
      if (o.a === b || V[i] === -Infinity || o.n0 > left + ((keyMask >> o.a) & 1)) continue;
      const v = V[i], e = o.r * (v > B ? v : B) + (1 - o.r) * (B - o.lc);
      if (e > best) best = e;
      if (vec && e > vec[o.a]) vec[o.a] = e;
      if (o.p0 > 0 && o.n0 + 1 <= left + ((keyMask >> o.a) & 1)) {  // (after the Dribble's action) the same pass from where he stands, off balance
        const p = o.p0 >= 1 ? 1 : Math.max(0, o.p0 - cut), f = p * (v > B ? v : B) + (1 - p) * (B - o.lc);
        if (f > fall) { fall = f; fi = i; }
      }
    }
    let viaDribble = false;
    for (let i = 0; i < n; i++) {
      const o = L[i];
      if (o.a !== b || V[i] === -Infinity || o.n0 > left) continue;
      const v = V[i], e = o.dr ? o.r * (v > B ? v : B) + (1 - o.r) * fall : (v > B ? v : B);
      if (e > best) best = e;
      if (vec) { const k = o.dr ? 5 : b; if (e > vec[k]) vec[k] = e; }
    }
    if (act && best > B + 1e-9) {                      // the looks the value turns on at this step (ties included): [look, step] pairs
      for (let i = 0; i < n; i++) {
        const o = L[i];
        if (V[i] === -Infinity) continue;
        const v = V[i];
        let e;
        if (o.a !== b) { if (o.n0 > left + ((keyMask >> o.a) & 1)) continue; e = o.r * (v > B ? v : B) + (1 - o.r) * (B - o.lc); }
        else { if (o.n0 > left) continue; e = o.dr ? o.r * (v > B ? v : B) + (1 - o.r) * fall : (v > B ? v : B); if (o.dr && e >= best - 1e-9) viaDribble = true; }
        if (e >= best - 1e-9) act.push(i, it);
      }
      if (viaDribble && fi >= 0) act.push(fi, it);     // (a Dribble route leans on its fall-back pass)
    }
    return best;
  }
  const SHOT_CLOCK_OUT = -TURNOVER_COST;               // D-198: the shot clock runs out: -5, nothing left to play
  const PVS = { offers: 0, runs: 0, reads: 0, looks: 0, steps: 0 };
  let BOUND_LOOKS = 2;
  let PV_BRUTE = false;
  let PV_CHECK = false;                                // a test's switch: every candidate read both ways, by difference and over every look
  const PVC = { n: 0, bad: 0, ex: [] };                                // a test's switch: every movement read in full, no cut (the answer must be the same)
  const topCount = (vec, U) => { let m = 0; for (let i = 0; i < 6; i++) if (vec[i] >= U - 1e-9) m++; return m; };
  // Step 31, fix 3c (Shaun, 27 Nov 2026; the design: "a drive is read by the same race"). A drive starts only from an
  // advantage: a Dribble won (his man locked), a shot fake beating a closeout (his man's Move spent; read inside the
  // fake mix), speed (a Quick Step or Sprint to a square his man can't get in front of this phase), or an open lane
  // (his man's zone doesn't cover the straight line in; a partial lane gives only the part it doesn't cover). The
  // beaten defender starts in that state and chases: he never contains, and his best is a Contest 3 less from beside or
  // 6 less from behind, 2 more off if he needed a Quick Step, never below 1. Every square the handler's movement reaches
  // nearer the rim is a line; movement goes round bodies (real paths); each side's Quick Steps left count phase by
  // phase (the board's in this phase, two in each phase after). Each phase the defence takes the least of: contain (a
  // helper set, or rushed, in front in time; his man is freed), help late (an off-balance Contest; his man freed), or
  // stay home (the chaser alone); the offence the most of: shoot, kick to anyone (a freed man at his own best look, read
  // without his defender; the pass raced from where the handler is), fake a helper who had to move to contain (he is
  // then spent), hesitate, or carry on. Who guards whom: the pairing that keeps the five closest.
  const STEP_G = new Memo2(60000);                     // fix 3d: phases of movement kept across boards (see raceKit's step)
  const _SU = new Map();
  function stepUnion(p, qs, moveOk, qsOk) {            // every square any path of one phase's movement from p can cross
    const key = (((p * 8 + qs) * 2 + (moveOk ? 1 : 0)) * 2) + (qsOk ? 1 : 0);
    let hit = _SU.get(key); if (hit) return hit;
    const u = new Set(), add = pa => { for (const q of pa) u.add(q); }, M = [];
    if (moveOk) for (const pa of movePaths(p)) { add(pa); M.push(pa[pa.length - 1]); }
    if (qsOk && qs > 0) {
      const Q = [];
      for (const pa of qsPaths(p, qs)) { add(pa); Q.push(pa[pa.length - 1]); }
      for (const m1 of M) for (const pa of qsPaths(m1, qs)) add(pa);
      if (moveOk) { for (const q1 of Q) for (const pa of movePaths(q1)) add(pa); for (const [, pa] of sprintPaths(p, qs)) add(pa); }
    }
    hit = Int16Array.from([...u].sort((x, y) => x - y)); _SU.set(key, hit); return hit;
  }
  function raceKit(m, Lmap, sr, T) {
    const s = m.s, r = m.r, ctx = s.ctx, b = s.ball, h0 = s.o[b];
    const occ = new Set(); for (let i = 0; i < 5; i++) { if (ONB[s.o[i]]) occ.add(s.o[i]); if (ONB[s.x[i]]) occ.add(s.x[i]); }
    const qo0 = Math.max(0, LIMITS.O.qs - count(sr, 'O', 'qs')), qd0 = Math.max(0, LIMITS.X.qs - count(sr, 'X', 'qs'));
    const clear = (p, self) => { for (const q of p) if (!ONB[q] || (q !== self && occ.has(q))) return false; return true; };
    const stepMemo = new Map();
    // fix 3d (speed, no number changed): a phase's movement from p turns only on which of the squares its paths can
    // cross are taken (stepUnion), so it is kept across boards under exactly those, and read again only when one changes
    const step = (p, qs, self, moveOk, qsOk) => {        // one phase's movement from p, round bodies (kept for the race)
      const sk = ((((p * 8 + qs) * NSQ + self) * 2 + (moveOk ? 1 : 0)) * 2) + (qsOk ? 1 : 0);
      let hit = stepMemo.get(sk); if (hit) return hit;
      const U = stepUnion(p, qs, moveOk, qsOk);
      let gk = (((p * 8 + qs) * 2 + (moveOk ? 1 : 0)) * 2 + (qsOk ? 1 : 0)) + ':';
      for (let x = 0; x < U.length; x++) { const q = U[x]; if (q !== self && occ.has(q)) gk += q + ','; }
      hit = STEP_G.get(gk);
      if (hit === undefined) { hit = stepCalc(p, qs, self, moveOk, qsOk); STEP_G.set(gk, hit); }
      stepMemo.set(sk, hit); return hit;
    };
    const stepCalc = (p, qs, self, moveOk, qsOk) => {
      const out = new Set(), M = [];
      if (moveOk) for (const pa of movePaths(p)) if (clear(pa, self)) { const d = pa[pa.length - 1]; if (!out.has(d)) { out.add(d); M.push(d); } }
      if (qsOk && qs > 0) {
        const Q = [];
        for (const pa of qsPaths(p, qs)) if (clear(pa, self)) { const d = pa[pa.length - 1]; if (!out.has(d)) out.add(d); Q.push(d); }
        for (const m1 of M) for (const pa of qsPaths(m1, qs)) if (clear(pa, self)) out.add(pa[pa.length - 1]);
        if (moveOk) { for (const q1 of Q) for (const pa of movePaths(q1)) if (clear(pa, self)) out.add(pa[pa.length - 1]); for (const [, pa] of sprintPaths(p, qs)) if (clear(pa, self)) out.add(pa[pa.length - 1]); }
      }
      out.delete(p);
      return Int16Array.from(out);                      // (compact: kept across boards, so it must fit a phone's memory)
    };
    const bfs = (start, qs, self, move0, qs0, qsLater) => {   // phases to every square (0 where he stands)
      const dist = new Map([[start, 0]]);
      let front = [start];
      for (let t = 1; t <= T && front.length; t++) {
        const nx = [];
        for (const p of front) for (const q of step(p, qs, self, t === 1 ? move0 : true, t === 1 ? qs0 : qsLater)) if (!dist.has(q)) { dist.set(q, t); nx.push(q); }
        front = nx;
      }
      return dist;
    };
    const man = [0, 1, 2, 3, 4];
    { let best = Infinity; const pr = [0, 1, 2, 3, 4], used = [false, false, false, false, false];
      const go = (d, sum) => { if (sum >= best) return; if (d === 5) { best = sum; for (let x = 0; x < 5; x++) man[x] = pr[x]; return; }
        for (let a = 0; a < 5; a++) if (!used[a]) { used[a] = true; pr[d] = a; go(d + 1, sum + (ONB[s.x[d]] && ONB[s.o[a]] ? cheb(s.x[d], s.o[a]) : 0)); used[a] = false; } };
      go(0, 0); }
    const guard = [-1, -1, -1, -1, -1]; for (let d = 0; d < 5; d++) guard[man[d]] = d;
    const DQ = [], DM = [];                               // each defender's phases, with and without Quick Steps
    for (let e = 0; e < 5; e++) { const q = ctx.dfn[e].qs; DQ.push(ONB[s.x[e]] ? bfs(s.x[e], q, s.x[e], true, qd0 > 0, true) : null); DM.push(ONB[s.x[e]] ? bfs(s.x[e], q, s.x[e], true, false, false) : null); }
    const shots = new Map(), shot = sq => { let v = shots.get(sq); if (!v) { const z = szone(ctx, sq); if (!SHOOT(z) || (ctx.noRim && sq === RIM)) v = { lk: null, z, pts: 0, open: [] }; else { const lk = makeLook(b, sq, 'later', 1.0, false); lk.types = ZONE_SHOTS[z]; lk.rushed = false; v = { lk, z, pts: ctx.worth[z], open: lk.types.map(ty => ctx.worth[z] * cardShot(ctx, ctx.off[b], ty, sq)) }; } shots.set(sq, v); } return v; };   // (no shot from a square nobody may shoot from)
    const vs = (sq, e, set) => { const sh = shot(sq); if (!sh.lk) return -Infinity; const cv = mapVals(r, sh.lk, e, set ? (W_K0 | (W_K0 << 6)) : W_K0, undefined); let hi = -Infinity; for (let t = 0; t < sh.open.length; t++) { const v = cv && cv[t] < sh.open[t] ? cv[t] : sh.open[t]; if (v > hi) hi = v; } return hi; };
    const chaseV = (sq, j, pen, rushed) => { const sh = shot(sq), dc = ctx.dfn[j]; let hi = -Infinity; for (let t = 0; t < sh.open.length; t++) { const ty = sh.lk.types[t], rr = cardShot(ctx, ctx.off[b], ty, sq); let con = dc.cn[ty] - pen - (rushed ? 2 : 0); if (con < 1) con = 1; const v = Math.max(0, sh.pts * (rr - con)); const u = v < sh.open[t] ? v : sh.open[t]; if (u > hi) hi = u; } return hi; };
    const openV = sq => { const sh = shot(sq); let hi = -Infinity; for (const v of sh.open) if (v > hi) hi = v; return hi; };
    const legal = q => ONB[q] && SHOOT(szone(ctx, q)) && !(ctx.noRim && q === RIM);
    const pc = new Map(), kc = new Map(), sortedW = new Map();
    const worthOf = (o, e) => { let w = -Infinity; for (let t = 0; t < o.open.length; t++) { let v = o.open[t]; for (let d = 0; d < 5; d++) if (d !== e && o.vals[d] && o.vals[d][t] < v) v = o.vals[d][t]; if (v > w) w = v; } return w + o.adj; };
    const byA = [[], [], [], [], []]; for (const o of Lmap) byA[o.a].push(o);
    const kick = (sq, left) => {                        // the best pass from sq: a man whose defender left (left) is read without him
      const key = sq * 8 + (left + 1);
      let hit = kc.get(key); if (hit) return hit;
      hit = { v: -Infinity, a: -1, at: -1 };
      const sb = W_(s, { o: setAt(s.o, b, sq) });
      for (let a = 0; a < 5; a++) {
        if (a === b || !ONB[s.o[a]]) continue;
        const without = guard[a] === left ? left : -1, wk = a * 8 + without + 1;   // (fix 3d: each man's looks sorted once a board)
        let ws = sortedW.get(wk); if (!ws) { ws = byA[a].map(o => [worthOf(o, without), o]).sort((x, y) => y[0] - x[0] || x[1].c - y[1].c || x[1].q0 - y[1].q0); sortedW.set(wk, ws); }
        for (const [w, o] of ws) {
          if (w <= hit.v) break;
          if (o.c === sq || o.q0 === sq) continue;      // (not on the ball handler's own square)
          const k2 = (sq * 4096 + o.q0) * 5 + a;
          let pp = pc.get(k2); if (pp === undefined) { pp = covPass(sb, a, o.q0); pc.set(k2, pp); }
          const ev = pp * w - (1 - pp) * TURNOVER_COST;
          if (ev > hit.v) hit = { v: ev, a, at: o.c };
        }
      }
      kc.set(key, hit); return hit;
    };
    const front = c => { const out = []; for (let d = 0; d < 8; d++) { const f = c + DSTEP[d]; if (ONB[f] && DR[f] < DR[c] && !(f !== c && occ.has(f) && !s.x.includes(f))) out.push(f); } return out; };
    // one race: the handler on c0 at phase 0, the chaser j (his phases dj, dmj), the first step's limits
    // (the offence's one Hesitate or fake a phase: w = 1 when this phase's is used)
    // fix 3d: a state after phase 0 turns only on the chaser (who he is and his phases), never on how the race began,
    // so races with the same chaser share those states. moveFirst false: no movement left to the handler in phase 0.
    const shared = new Map();
    const race = (c0, j, dj, dmj, qoFirst, firstOk, w0, moveFirst = true) => {
      let sh = shared.get(dj); if (!sh) { sh = { memo: new Map() }; shared.set(dj, sh); }
      const memo0 = new Map();
      const MEM = t => (t >= 1 ? sh.memo : memo0);
      // (fix 3d, memory: each state keeps only its worth; the choice table is built again for the line the report shows.
      // No state leans on itself (carry and hesitate go a phase on, a fake spends a helper), so that rebuild is exact.)
      const V = (t, c, spent, w) => {
        const key = ((t * NSQ + c) * 32 + spent) * 2 + w, memo = MEM(t);
        const hit = memo.get(key); if (hit !== undefined) return hit;
        memo.set(key, -Infinity);                       // (a guard: no state leans on itself)
        const v = node(t, c, spent, w).pick.worth;
        memo.set(key, v); return v;
      };
      const node = (t, c, spent, w) => {
        const opts = [];
        let chase = Infinity, chaseHow = null;
        for (let d = 0; d < 8; d++) { const a = c + DSTEP[d]; if (!ONB[a]) continue; const k = dj.get(a); if (k === undefined || k > t) continue; const pen = t > 0 && DR[a] <= DR[c] ? 3 : 6, rushed = !(dmj.get(a) <= t);   /* (beaten: behind the ball in the phase of the advantage) */ const v = chaseV(c, j, pen, rushed); if (v < chase) { chase = v; chaseHow = { at: a, pen, rushed }; } }
        const shootAlone = Math.min(chase, openV(c));
        const nxt = [];
        if (t < T && t === 0 && !moveFirst) nxt.push(c);    // (no movement left: phase 0 ends with him here)
        else if (t < T) for (const q of step(c, ctx.off[b].qs, s.o[b], true, t === 0 ? qoFirst > 0 : true)) if (legal(q) && DR[q] < DR[c] && (t > 0 || firstOk(q))) nxt.push(q);
        nxt.sort((x, y) => x - y);
        let carry = -Infinity, carryTo = -1;
        for (const q of nxt) { const v = V(t + 1, q, spent, 0); if (v > carry) { carry = v; carryTo = q; } }
        const hes = t < T && !w ? V(t + 1, c, spent, 0) : -Infinity;
        const home = kick(c, -1);
        const none = Math.max(shootAlone, home.v, carry, hes);
        opts.push({ by: -1, how: 'stay home', shoot: shootAlone, kick: home, carry, carryTo, hes, worth: none });
        for (let e = 0; e < 5; e++) {
          if (e === j || ((spent >> e) & 1) || !DQ[e]) continue;
          let kc2 = Infinity, km = Infinity;
          for (const f of front(c)) { const k = DQ[e].get(f); if (k !== undefined && k < kc2) kc2 = k; const k2 = DM[e].get(f); if (k2 !== undefined && k2 < km) km = k2; }
          if (kc2 <= t) {                               // he contains: in front in time
            const set = km <= t, sh = Math.min(vs(c, e, set), chase), kk = kick(c, e);
            const fk = kc2 >= 1 && kc2 === t && !w ? V(t, c, spent | (1 << e), 1) : -Infinity;   // he had to move to get there: the fake beats it
            opts.push({ by: e, how: set ? 'contain' : 'contain, rushed', shoot: sh, kick: kk, fake: fk, worth: Math.max(sh, kk.v, fk) });
            continue;
          }
          let ka = Infinity; for (let d = 0; d < 8; d++) { const a = c + DSTEP[d]; if (!ONB[a]) continue; const k = DQ[e].get(a); if (k !== undefined && k < ka) ka = k; }
          if (ka <= t) { const sh = Math.min(vs(c, e, false), chase), kk = kick(c, e); opts.push({ by: e, how: 'help late', shoot: sh, kick: kk, carry, worth: Math.max(sh, kk.v, carry) }); }
        }
        let best = opts[0];
        for (const o of opts) if (o.worth < best.worth - 1e-12) best = o;
        return { t, c, spent, w, chase: chase === Infinity ? null : chase, chaseHow, opts, pick: best };
      };
      const v0 = V(0, c0, 0, w0 ? 1 : 0);
      const phases = [];                                 // the line the number reads: each side's choice phase by phase
      let t = 0, c = c0, sp = 0, w = w0 ? 1 : 0;
      for (let guardN = 0; guardN < 12; guardN++) {
        if (!MEM(t).has(((t * NSQ + c) * 32 + sp) * 2 + w)) break;
        const tr = node(t, c, sp, w);
        phases.push(tr);
        const p = tr.pick;
        if (p.by >= 0 && p.how !== 'help late') { if (p.fake === p.worth && p.fake > -Infinity) { sp |= 1 << p.by; w = 1; continue; } break; }
        const top = Math.max(p.shoot, p.kick.v, p.carry, p.hes === undefined ? -Infinity : p.hes);
        if (p.carry === top && p.carryTo >= 0 && top > Math.max(p.shoot, p.kick.v)) { t++; c = p.carryTo; w = 0; continue; }
        if (p.hes !== undefined && p.hes === top && top > Math.max(p.shoot, p.kick.v, p.carry)) { t++; w = 0; continue; }
        break;
      }
      return { v: v0, phases, qd0, qo0 };
    };
    const w0 = count(sr, 'O', 'hesitate') >= LIMITS.O.hesitate;
    return { s, b, h0, man, guard, DQ, DM, bfs, step, race, qo0, qd0, occ, legal, w0 };
  }
  function driveRaces(m, Lmap, T, sr) {
    const out = [], s = m.s, ctx = s.ctx, b = s.ball, h0 = s.o[b];
    if (!ONB[h0] || s.pending || sr.pending || sr.stage !== 'play') return out;
    const K = raceKit(m, Lmap, sr, T), jm = K.guard[b];
    const all = () => true;
    // a Dribble won: the beaten defender locked this phase (a Quick Step his only movement)
    for (const [a, j] of sr.beaten || []) {
      if (a !== b || !ONB[s.x[j]]) continue;
      const q = ctx.dfn[j].qs, dj = K.bfs(s.x[j], q, s.x[j], false, K.qd0 > 0, true), dmj = K.bfs(s.x[j], q, s.x[j], false, false, false);
      out.push({ kind: 'Dribble won', beaten: j, start: h0, p: 1, ...K.race(h0, j, dj, dmj, K.qo0, all, K.w0) });
    }
    if (out.length || jm < 0 || !ONB[s.x[jm]]) return out.map(x => finishRace(x, b, h0));
    const qj = ctx.dfn[jm].qs, djFull = K.bfs(s.x[jm], qj, s.x[jm], true, K.qd0 > 0, true), dmFull = K.bfs(s.x[jm], qj, s.x[jm], true, false, false);
    // an open lane: his man's zone doesn't cover the straight line in
    const cov = new Set([s.x[jm]]);
    { const dc = ctx.dfn[jm], arrs = ctx.zone ? [s.arrows[jm], (s.arrows[jm] + 1) % 8] : [s.arrows[jm]];
      for (const d of arrs) { const diag = d & 1, R = Math.max(diag ? 2 : 3, dc.qs, dc.qs > 0 ? (diag ? 2 : 3) + dc.qs : 0); let q = s.x[jm];
        for (let n = 1; n <= R; n++) { q += DSTEP[d]; if (!ONB[q] || (q !== s.x[jm] && K.occ.has(q))) break; cov.add(q); } } }
    const lane = Array.from(laneSquares(h0, RIM)).sort((x, y) => DR[y] - DR[x] || x - y);
    if (lane.length && !cov.has(lane[0])) {
      const full = lane.every(q => !cov.has(q));
      const ok = q => { if (cov.has(q)) return false; for (const x of laneSquares(h0, q)) if (cov.has(x)) return false; return true; };
      out.push({ kind: full ? 'open lane' : 'partial lane', beaten: jm, start: h0, p: 1, ...K.race(h0, jm, djFull, dmFull, K.qo0, full ? all : ok, K.w0) });
    }
    // speed: a Quick Step or Sprint to a square his man can't get in front of this phase
    if (K.qo0 > 0 && ctx.off[b].qs > 0 && !quickStepped(sr, 'O', b)) {
      // fix 3d (the rules): a Quick Step leaves him his Move this phase. He may stop there (his Move to come after the
      // defence's turn) or Move on at once, in the same turn, before the defence moves (then nothing is left to him
      // this phase). A Sprint is his Move and his Quick Step together: nothing is left.
      const qs = ctx.off[b].qs, starts = new Map(), clearO = pa => pa.every(q => ONB[q] && !K.occ.has(q));
      const canMoveO = canMoveKind(sr, 'O', b, 'move'), qsDest = [], how = new Map();
      for (const pa of qsPaths(h0, qs)) if (clearO(pa)) { const d = pa[pa.length - 1]; if (!starts.has(d)) { starts.set(d, canMoveO); how.set(d, 'Quick Step'); qsDest.push(d); } }
      if (canMoveO) for (const s1 of qsDest.slice().sort((x, y) => x - y)) for (const pa of movePaths(s1)) if (pa.every(q => ONB[q] && (q === h0 || !K.occ.has(q)))) { const d = pa[pa.length - 1]; if (d !== h0 && !starts.has(d)) { starts.set(d, false); how.set(d, 'Quick Step, then Move'); } }
      if (canMoveKind(sr, 'O', b, 'sprint')) for (const [, pa] of sprintPaths(h0, qs)) if (clearO(pa)) { const d = pa[pa.length - 1]; if (!starts.has(d)) { starts.set(d, false); how.set(d, 'Sprint'); } }
      let best = null;
      for (const s1 of [...starts.keys()].sort((x, y) => x - y)) {
        if (!K.legal(s1) || DR[s1] >= DR[h0]) continue;
        let reach = false; for (let d = 0; d < 8; d++) { const f = s1 + DSTEP[d]; if (ONB[f] && DR[f] < DR[s1] && djFull.get(f) !== undefined && djFull.get(f) <= 1) reach = true; }
        if (reach) continue;
        const rc = K.race(s1, jm, djFull, dmFull, 0, all, K.w0, starts.get(s1));
        if (!best || rc.v > best.v) best = { kind: 'speed', beaten: jm, start: s1, p: 1, keeps_move: starts.get(s1), start_by: how.get(s1), ...rc };
      }
      if (best) out.push(best);
    }
    const res = out.map(x => finishRace(x, b, h0));
    res.kit = K;                                       // (fix 3d: the fake mix reads its races with the same kit)
    return res;
  }
  const r2 = v => (v === -Infinity || v === Infinity || v === undefined || v === null ? null : +v.toFixed(2));
  function raceJSON(rc) {                              // (the report: each phase as the number reads it, every choice and its worth)
    return { advantage: rc.kind, beaten: 'X' + (rc.beaten + 1), from: sqName(rc.start), worth: r2(rc.v), ...(rc.start_by ? { start_by: rc.start_by, move_left: rc.keeps_move } : {}), quick_steps_left_now: { offence: rc.qo0, defence: rc.qd0 },
      phases: rc.phases.map(ph => ({ phase: ph.t, ball_at: sqName(ph.c), spent: [0, 1, 2, 3, 4].filter(e => (ph.spent >> e) & 1).map(e => 'X' + (e + 1)),
        chaser: ph.chaseHow ? { contest_worth: r2(ph.chase), from: sqName(ph.chaseHow.at), less: ph.chaseHow.pen, rushed: ph.chaseHow.rushed } : null,
        choices: ph.opts.map(o => ({ defence: o.by < 0 ? 'stay home' : 'X' + (o.by + 1) + ' ' + o.how, shoot: r2(o.shoot), kick: o.kick && o.kick.a >= 0 ? { to: 'O' + (o.kick.a + 1), at: sqName(o.kick.at), worth: r2(o.kick.v) } : null,
          fake: r2(o.fake), carry_on: r2(o.carry), carry_to: o.carryTo >= 0 ? sqName(o.carryTo) : null, hesitate: r2(o.hes), worth: r2(o.worth) })),
        defence_picks: ph.pick.by < 0 ? 'stay home' : 'X' + (ph.pick.by + 1) + ' ' + ph.pick.how, worth: r2(ph.pick.worth) })) };
  }
  function finishRace(x, b, h0) {
    x.look = { a: b, c: h0, q0: h0, rushed: true, r: x.p, open: [x.v], v: x.v, w: x.v, adj: 0, lc: 0, dr: true, p0: 0, n0: 2, id: 900000 + out9(x.kind) * 8 + x.beaten + 1, race: true, vals: [null, null, null, null, null] };
    return x;
  }
  const out9 = k => (k === 'Dribble won' ? 0 : k === 'open lane' ? 1 : k === 'partial lane' ? 2 : 3);
  function possRead(m, s0, lastPhase, noAnswer, probe) {       // noAnswer: the value as the defence stands (the stance search's number)                           // the looks of map m, the defence's answer, the value: {U, U0, k, bars, moves, L, worth}
    const s = m.s, b = s.ball, k = Math.floor(s.clock / 2) - 1, cut = s.ctx.offCut > 0 ? s.ctx.offCut / 20 : 0;
    const owed = threeSecondsLeave(s0 || s), r = m.r, soft = s.ctx.soft;
    // the actions a route may use: the phase's six less those spent getting men out of the key; in the last phase what
    // the offence really has left, less the shot's own action
    const left = lastPhase ? (s0 || s).tok_o - 1 : 6 - owed.next, keyMask = lastPhase ? 0 : owed.mask;
    const L = []; for (const o of m.options) if (o.r > 0) L.push(o);
    const mapL = L.slice(), srR = s0 || m.s;
    const races = driveRaces(m, mapL, Math.min(3, k + 1), srR);   // fix 3c: each drive from an advantage, read by its race, is one more look
    for (const rc of races) L.push(rc.look);
    const n = L.length, K = k + 1;
    // (the three seconds are counted once: a man who can't get out is charged his -5 by possParts, so his own look in
    // the key doesn't carry it again. Scale audit, row 11.)
    const stuck = s0 ? threeSecondsStuck(s0) : 0, adjv = new Float64Array(n);
    for (let i = 0; i < n; i++) adjv[i] = L[i].adj + (((stuck >> L[i].a) & 1) && INKEY[L[i].q0] ? TURNOVER_COST : 0);
    pvRoom(n * (K + 1));
    const W = PV.W, tmp = PV.tmp, Vit = PV.V;           // Vit: each step's worths as the defence now stands (rows 1 to K)
    // each look's contests, a defender at a time: {cv: the Contest's value by shot type, bl: the blocks as lines}
    const mv = m._mv || (m._mv = new Map());             // read once per (look, defender, contest kinds), kept with the map
    // Step 31, fix 1: a look's contest by defender d depends only on the cards, the look (who, where, rushed or set) and
    // the contest kinds d reaches it with (mk): nothing else on the board. So it is kept for the game (sv2, two small
    // generations) and read again only when one of those changes: a board that differs from the last by one player
    // finds every other pair already read.
    const sv2 = s.ctx._sv2 || (s.ctx._sv2 = new Memo2(SV_MEMO_MAX));
    const sval = (i, d, mk) => {
      if (!mk || L[i].race) return null;              // (a drive's race look already holds its defence)
      const key = (L[i].id * 5 + d) * 16777216 + mk;
      let v = mv.get(key);
      if (v === undefined) {
        const o = L[i], gk = ((((o.a * NSQ + o.c) * 2 + (o.fl ? 1 : 0)) * 5 + d) * 16777216 + mk);
        v = sv2.get(gk);
        if (v === undefined) {
          const full = mk & 63, set = (mk >> 6) & 63, lines = [];
          const cv = r._valsCalc(o.lk, d, full, set, (o.fl || 0) | 4, soft ? full : 0, soft ? set : 0, lines);
          // fix 3: his Contest where he stands, with no movement (st): a shot fake punishes only a Contest that needs one
          const sk = (mk >> 12) & 63, ss = (mk >> 18) & 63;
          let st = null;
          if (sk) { const ls = [], cs = r._valsCalc(o.lk, d, sk, ss, (o.fl || 0) | 4, soft ? sk : 0, soft ? ss : 0, ls); st = cs ? { cv: cs, bl: ls.length ? Float64Array.from(ls) : null } : null; }
          v = cv ? { cv, bl: lines.length ? Float64Array.from(lines) : null, st } : null;
          sv2.set(gk, v);
        }
        mv.set(key, v);
      }
      return v;
    };
    const SV = new Array(n), lc = new Int16Array(n);
    for (let i = 0; i < n; i++) { const c = BI[L[i].c], row = [null, null, null, null, null]; lc[i] = c; if (!L[i].race) for (let d = 0; d < 5; d++) if (m.cms[d]) row[d] = sval(i, d, m.cms[d][c]); SV[i] = row; }
    const gone = new Uint8Array(n);                     // a defender now stands on the look's square
    // Step 31, Part C (Shaun, 25 Nov 2026: "later answers cost actions too"). Inside the number the defence's answer gets
    // only the actions and time it will really have. In this phase a look faces only the movements the defence can make
    // before its shot goes up: what is left of the defence's turn if it is the one to act, then two for each turn the
    // offence must hand over on the way (a pass, a Dribble or a Screen ends its turn; so does its second action). A shot
    // the ball handler can take this turn faces none. lim[j]: how many of the answer's movements look j faces in this
    // phase (the phases after this one: limL, below). SVK, goneK: each look's
    // contests as this phase's shot will find them (they stop following the answer once the look's limit is reached).
    const sr = s0 || s, baseAct = (sr.side === 'X' && sr.stage === 'play' && !sr.pending) ? Math.max(0, 2 - sr.turn_n) : 0;
    const lim = new Int16Array(n);
    for (let i = 0; i < n; i++) {
      const o = L[i];
      let turns;
      // the ball handler: n0 movements then the shot, two actions a turn; by a Dribble: the Dribble ends his turn, then
      // n0 - 1 movements and the shot. A receiver: his n0 - 1 movements, the pass (which ends the turn), then the shot
      if (o.a === b) turns = o.dr ? 1 + Math.floor((o.n0 - 1) / 2) : Math.floor(o.n0 / 2);
      else turns = 1 + Math.floor((o.n0 - 1) / 2);
      lim[i] = noAnswer ? 0 : baseAct + 2 * turns;
    }
    const SVK = new Array(n), goneK = new Uint8Array(n);
    for (let i = 0; i < n; i++) SVK[i] = SV[i].slice();
    // Step 31, fix 2 (the step 31C audit: "later answers cost actions in every phase, not just the current one"). The
    // phases after this one are read on this board too, so each starts the same way: the offence acts first, and a look
    // faces only the movements the defence makes before its shot, two for each turn the offence hands over on the way.
    // limL[j]: that count for the later phases; SVL, goneL: each look's contests as a later phase's shot finds them.
    // With no defence turn under way now the count is this phase's, and the two are one.
    const split = baseAct > 0, limL = split ? new Int16Array(n) : lim;
    if (split) for (let i = 0; i < n; i++) limL[i] = lim[i] === 0 ? 0 : lim[i] - baseAct;
    const SVL = split ? SV.map(r => r.slice()) : SVK, goneL = split ? new Uint8Array(n) : goneK;
    let nm = 0;                                         // the answer's movements so far
    // Step 31, fix 3 (Shaun, 26 Nov 2026: "two-step routes are looks"; shot fakes read inside the number). The shooter
    // in control mixes real and fake; the defence answers by contesting from where it stands or by closing out (a
    // movement, then the Contest). Against a fake an honest Contest does nothing and the movement stands, so the
    // defender who closed out has spent his Move: the offence then takes its best look with him so placed (the shooter's
    // own drive past him: closeout, fake and drive; a cutter behind him: drive then backdoor cut; a man he left: drive
    // then kick-out). One route, one look, read by the two-by-two mix:
    //                 contest where he stands      close out
    //   shoot               ws                         wc
    //   fake                wc                         F (the follow-up)
    // worth = wc when nothing is gained by it (ws or F no more than wc); otherwise the mixed value
    // wc + (ws - wc)(F - wc) / ((ws - wc) + (F - wc)), always between wc and ws. A defender already where he contests
    // from (ws = wc) can't be faked out of it. F is read on the board as the defence stands before its answer.
    const fakesOn = !!s.ctx.fakes;
    const fkK = fakesOn && count(sr, 'O', 'hesitate') < LIMITS.O.hesitate, fkL = fakesOn;   // this phase's fake (or Hesitate) unused; every later phase has one
    const mixOk = new Uint8Array(n);
    for (let i = 0; i < n; i++) mixOk[i] = fakesOn && !L[i].rushed ? 1 : 0;     // (no fake when rushed)
    const arg = new Int8Array(8), tmpS = new Float64Array(8);
    let cTb = 0;
    const core = (i, B, d, nv, row) => {                // the look's worth against the Contests as the reply gives them (arg: whose each shot's is)
      const open = L[i].open, T = open.length;
      for (let t = 0; t < T; t++) { tmp[t] = open[t]; arg[t] = -1; }
      for (let e = 0; e < 5; e++) {
        const x = e === d ? nv : row[e];
        if (!x) continue;
        const cv = x.cv, bl = x.bl;
        for (let t = 0; t < T; t++) if (cv[t] < tmp[t]) { tmp[t] = cv[t]; arg[t] = e; }
        if (bl) for (let j = 0; j < bl.length; j += 3) { const v = bl[j + 1] + bl[j + 2] * B; if (v < tmp[bl[j]]) { tmp[bl[j]] = v; arg[bl[j]] = -2; } }
      }
      let tp = tmp[0], tb = 0; for (let t = 1; t < T; t++) if (tmp[t] > tp) { tp = tmp[t]; tb = t; }
      cTb = tb;
      return tp + adjv[i];
    };
    // the follow-up after the fake: defender e closed out next to look i's shooter, his Move spent (cmAfter), every
    // other piece as the defence stands before its answer; the offence's best look then (r * worth - (1 - r) * what a
    // miss costs), over the map's own looks. Of the squares he could close out to, the defence takes the one that
    // leaves the least. Kept for the reading.
    const SV0 = SV.map(rw => rw.slice()), Fm = new Map(), Gm = new Map(), UB0 = [null, null, null, null, null], ORD0 = [null, null, null, null, null];
    const movedAt = [null, null, null, null, null];     // (fix 3b: where each defender's answer movement took him, and how)
    let RK = races.kit || null;                          // (fix 3c: the race's kit, built when a fake's race first needs it; fix 3d: the drives' own)
    const fakeRaces = [], fakeKept = new Map();          // (for the report: the races the fake mix read)
    const okLook = j => { const o = L[j]; return o.a === b ? o.n0 <= left : o.n0 <= left + ((keyMask >> o.a) & 1); };
    const ub0 = e => {                                  // (each look's best with e's Contest taken off: a bound, so the best-first scan can stop)
      const u = new Float64Array(n), ord = [];
      for (let j = 0; j < n; j++) {
        const o = L[j], open = o.open, T = open.length, row = SV0[j];
        let hi = -Infinity;
        for (let t = 0; t < T; t++) { let v = open[t]; for (let e2 = 0; e2 < 5; e2++) if (e2 !== e && row[e2] && row[e2].cv[t] < v) v = row[e2].cv[t]; if (v > hi) hi = v; }
        u[j] = o.r * (hi + adjv[j]) - (1 - o.r) * o.lc;
        if (okLook(j)) ord.push(j);
      }
      ord.sort((x, y) => u[y] - u[x] || x - y);
      UB0[e] = u; ORD0[e] = ord;
    };
    const follow2 = (e, q, a, kind) => {
      const key = ((e * NSQ + q) * 8 + a) * 3 + (kind === 'move' ? 0 : kind === 'qs' ? 1 : 2);
      let g = Gm.get(key); if (g !== undefined) return g;
      if (!UB0[e]) ub0(e);
      const u = UB0[e], ord = ORD0[e], cm = cmAfter(q, a, s.ctx.dfn[e].qs, stanceMode(m.sN, e), kind, 1);
      let hi = -Infinity, hj = -1;
      for (let x = 0; x < ord.length; x++) {
        const j = ord[x];
        if (u[j] + 1e-9 <= hi) break;
        if (L[j].c === q) continue;
        const o = L[j], ev = o.r * core(j, 0, e, sval(j, e, cm[lc[j]]), SV0[j]) - (1 - o.r) * o.lc;
        if (ev > hi) { hi = ev; hj = j; }
      }
      g = { v: hi, j: hj }; Gm.set(key, g); return g;
    };
    const follow = (i, e) => {
      const key = i * 5 + e;
      let f = Fm.get(key); if (f !== undefined) return f;
      const c = L[i].c, mv0 = movedAt[e];
      let lo = Infinity, from = -1, then = -1;
      if (!mv0) {
        const fr = defenderReachExact(m.sN, e);
        // fix 3c: the ball handler's own look where he stands: the fake beats the closeout and the drive's race starts
        // there, the closer's Move spent (his only movement this phase a Quick Step)
        const fakeRace = q => {
          if (L[i].a !== b || L[i].c !== m.s.o[b] || L[i].race) return -Infinity;
          if (!RK) RK = raceKit(m, mapL, srR, Math.min(3, k + 1));
          const fkey = e * NSQ + q, kept = fakeKept.get(fkey);    // (fix 3d: one race a closer and square, for every look and answer step)
          if (kept !== undefined) return kept;
          const qe = s.ctx.dfn[e].qs, dj = RK.bfs(q, qe, s.x[e], false, RK.qd0 > 0, true), dmj = RK.bfs(q, qe, s.x[e], false, false, false);
          const rc = RK.race(m.s.o[b], e, dj, dmj, RK.qo0, () => true, true);
          if (fakeRaces.length < 8) fakeRaces.push(Object.assign({ kind: 'shot fake beats the closeout', beaten: e, start: m.s.o[b], p: 1, closes_to: q }, rc));
          fakeKept.set(fkey, rc.v);
          return rc.v;
        };
        for (const [q, na] of fr[0]) if (na === 1 && cheb(q, c) === 1) { const g = follow2(e, q, dirBetween(q, c), 'move'), fr2 = fakeRace(q), v = Math.max(g.v, fr2); if (v < lo) { lo = v; from = q; then = fr2 > g.v ? -2 : g.j; } }
        for (const [q, arrs] of fr[1]) if (cheb(q, c) === 1) for (const [a, na] of arrs) if (na === 1) { const g = follow2(e, q, a, fixedKind(m.sN, e, q, a)), fr2 = fakeRace(q), v = Math.max(g.v, fr2); if (v < lo) { lo = v; from = q; then = fr2 > g.v ? -2 : g.j; } }
      } else if (mv0.kind !== 'sprint') {              // fix 3b: he moved in the answer; he closes out with what he has left, and then has nothing
        const qs = s.ctx.dfn[e].qs, fr = mv0.kind === 'move' ? geoReach(mv0.q, mv0.a, qs, false, 1) : geoReach(mv0.q, mv0.a, qs, true, 0);
        if (mv0.kind === 'qs') { for (const [q, na] of fr[0]) if (na === 1 && q !== mv0.q && cheb(q, c) === 1) { const g = follow2(e, q, dirBetween(q, c), 'sprint'); if (g.v < lo) { lo = g.v; from = q; then = g.j; } } }
        else for (const [q, arrs] of fr[1]) if (q !== mv0.q && cheb(q, c) === 1) for (const [a, na] of arrs) if (na === 1) { const g = follow2(e, q, a, 'sprint'); if (g.v < lo) { lo = g.v; from = q; then = g.j; } }
      }
      f = { F: lo === Infinity ? -Infinity : lo, from, then }; Fm.set(key, f); return f;
    };
    const worth = (i, B, d, nv, rowK, tk) => {          // look i's worth when a block leads to B, defender d's contest replaced by nv (rowK: as this phase's shot finds it; tk 1: a later phase)
      const row = rowK || SV[i], wc = core(i, B, d, nv, row);
      if (!mixOk[i] || !(tk === 1 ? fkL : fkK)) return wc;
      const e0 = arg[cTb];
      if (e0 < 0) return wc;
      const open = L[i].open, T = open.length;
      for (let t = 0; t < T; t++) tmpS[t] = open[t];
      for (let e = 0; e < 5; e++) {
        const x0 = e === d ? nv : row[e], x = x0 && x0.st;
        if (!x) continue;
        const cv = x.cv, bl = x.bl;
        for (let t = 0; t < T; t++) if (cv[t] < tmpS[t]) tmpS[t] = cv[t];
        if (bl) for (let j = 0; j < bl.length; j += 3) { const v = bl[j + 1] + bl[j + 2] * B; if (v < tmpS[bl[j]]) tmpS[bl[j]] = v; }
      }
      let ts = tmpS[0]; for (let t = 1; t < T; t++) if (tmpS[t] > ts) ts = tmpS[t];
      const ws = ts + adjv[i];
      if (!(ws > wc + 1e-9)) return wc;
      const F = follow(i, e0).F;
      if (!(F > wc + 1e-9)) return wc;
      const da = ws - wc, df = F - wc;
      return wc + da * df / (da + df);
    };
    // U(k + 1), the bar worked up from the shot clock running out; at step i a blocked shot leads to U(i - 2) (the
    // phase of the shot is lost; with none after it the possession ends on what it has)
    const hist = new Float64Array(K + 1), histC = new Float64Array(K + 1), vec = new Float64Array(6), v2 = PV.vec2;
    const rows = [null]; for (let i = 1; i <= K; i++) rows.push(Vit.subarray(i * n, (i + 1) * n));
    let act = [], blList = [], LA = [], JA = [], WA = new Float64Array(0);
    const histA = new Float64Array(K + 1), v3 = new Float64Array(6), bmax = new Float64Array(n);
    const slopeB = new Uint8Array(n), sameK = new Uint8Array(n), sameL = new Uint8Array(n), w0 = new Float64Array(n), w0L = new Float64Array(n);
    const runCur = bars => {
      let U = SHOT_CLOCK_OUT; hist[0] = U; act = []; blList = [];
      // bmax[j]: above this, no block bears on look j (a block that leads to a phase worth more than that is no longer
      // the defender's best answer), so its worth no longer moves with what the block leads to
      for (let j = 0; j < n; j++) {
        const row = SV[j], open = L[j].open, T = open.length;
        let bm = -Infinity, any = false;
        for (let e = 0; e < 5; e++) if (row[e] && row[e].bl) { any = true; break; }
        if (mixOk[j]) for (let e = 0; e < 5; e++) if (row[e] && row[e].st && row[e].st.bl) bm = Infinity;   // (fix 3: read in full)
        if (any && !gone[j]) {
          for (let t = 0; t < T; t++) { let v = open[t]; for (let e = 0; e < 5; e++) if (row[e] && row[e].cv[t] < v) v = row[e].cv[t]; tmp[t] = v; }
          for (let e = 0; e < 5; e++) { const bl = row[e] && row[e].bl; if (!bl) continue; for (let x = 0; x < bl.length; x += 3) if (bl[x + 2] > 0) { const thr = (tmp[bl[x]] - bl[x + 1]) / bl[x + 2]; if (thr > bm) bm = thr; } }
        }
        bmax[j] = bm;
        if (bm > -Infinity) blList.push(j);
      }
      blList.sort((x, y) => bmax[y] - bmax[x] || x - y);
      if (bars) bars.push(U);
      // step 31, fix 1: a look whose block lines don't move with what a block leads to (none, or flat) is worth the
      // same at every step, so it is read once here (the same sum, the same numbers)
      for (let j = 0; j < n; j++) {
        const row = SV[j], rk = SVK[j], rl = SVL[j];
        let mv = 0, same = 1, sameL_ = 1;
        for (let e = 0; e < 5; e++) {
          const x = row[e], y = rk[e], w = rl[e];
          if (x !== y) same = 0;
          if (x !== w) sameL_ = 0;
          if (x && x.bl) for (let z = 2; z < x.bl.length; z += 3) if (x.bl[z] !== 0) mv = 1;
          if (y && y.bl) for (let z = 2; z < y.bl.length; z += 3) if (y.bl[z] !== 0) mv = 1;
          if (w && w.bl) for (let z = 2; z < w.bl.length; z += 3) if (w.bl[z] !== 0) mv = 1;
          for (const u of [x, y, w]) if (u && u.st && u.st.bl) for (let z = 2; z < u.st.bl.length; z += 3) if (u.st.bl[z] !== 0) mv = 1;
        }
        slopeB[j] = mv; sameK[j] = same && gone[j] === goneK[j] ? 1 : 0; sameL[j] = sameL_ && gone[j] === goneL[j] ? 1 : 0;
        w0[j] = (!mv && !gone[j]) ? worth(j, 0, -1, null, undefined, 0) : -Infinity;
        w0L[j] = fkK === fkL ? w0[j] : ((!mv && !gone[j]) ? worth(j, 0, -1, null, undefined, 1) : -Infinity);
      }
      for (let i = 1; i <= K; i++) {
        const B = i >= 3 ? hist[i - 2] : 0, row = rows[i];
        if (i === K) for (let j = 0; j < n; j++) row[j] = goneK[j] ? -Infinity : ((!slopeB[j] && sameK[j]) ? w0[j] : worth(j, B, -1, null, SVK[j], 0));
        else for (let j = 0; j < n; j++) row[j] = goneL[j] ? -Infinity : ((!slopeB[j] && sameL[j]) ? w0L[j] : worth(j, B, -1, null, SVL[j], 1));
        U = routeT(L, n, row, b, U, left, keyMask, cut, i === K ? vec : null, act, i);
        hist[i] = U;
        if (bars) bars.push(U);
      }
      buildOrders();
      const seen = new Set(); JA = [];
      for (let x = 0; x < act.length; x += 2) if (!seen.has(act[x])) { seen.add(act[x]); JA.push(act[x]); }
      // (the bound's looks: those the value turns on, and each route's next few, which hold the value up when the first
      // are closed. How many is only how tight the bound is: the answer is the same whatever it is.)
      for (let i = 1; i <= K; i++) {
        const row = rows[i], Bk = hist[i - 1], tops = [[], [], [], [], [], []];
        for (let j = 0; j < n; j++) {
          if (row[j] === -Infinity) continue;
          const o = L[j], v = row[j], e = o.r * (v > Bk ? v : Bk) + (1 - o.r) * (Bk - o.lc), tp = tops[o.a === b && o.dr ? 5 : o.a];
          if (tp.length < 2 * BOUND_LOOKS) { tp.push(e, j); continue; }
          let lo = 0; for (let x = 2; x < tp.length; x += 2) if (tp[x] < tp[lo]) lo = x;
          if (e > tp[lo]) { tp[lo] = e; tp[lo + 1] = j; }
        }
        for (const tp of tops) for (let x = 1; x < tp.length; x += 2) if (!seen.has(tp[x])) { seen.add(tp[x]); JA.push(tp[x]); }
      }
      JA.sort((x, y) => x - y);
      LA = JA.map(j => L[j]);
      if (WA.length < JA.length) WA = new Float64Array(JA.length * 2);
      return U;
    };
    // The same sum over only the looks the value turns on, with defender d on q: never more than the whole sum gives
    // (fewer looks, and every route only rises with what playing on is worth). So a movement whose sum over these alone
    // already beats the best answer found can't be the answer, and isn't read in full (a cut that can't change it).
    const actT = new Uint8Array(n);
    const runAct = (d, q, cm) => {
      const na = JA.length;
      let U = SHOT_CLOCK_OUT; histA[0] = U;
      for (let x = 0; x < na; x++) { const j = JA[x]; actT[x] = (SV[j][d] === null && cm[lc[j]] === 0 && L[j].c !== q) ? 0 : 1; }
      for (let i = 1; i <= K; i++) {
        const B = i >= 3 ? histA[i - 2] : 0, keep = i < 3 || histA[i - 2] === hist[i - 2], row = rows[i];
        // (a look the candidate doesn't touch is worth what it is as the defence stands, where what a block leads to is
        // the same or doesn't move it)
        if (i === K) for (let x = 0; x < na; x++) { const j = JA[x]; WA[x] = lim[j] > nm ? ((gone[j] || L[j].c === q) ? -Infinity : ((!actT[x] && (keep || !slopeB[j])) ? row[j] : worth(j, B, d, sval(j, d, cm[lc[j]]), undefined, 0))) : (goneK[j] ? -Infinity : ((keep || (!slopeB[j] && sameK[j])) ? row[j] : worth(j, B, -1, null, SVK[j], 0))); }
        else for (let x = 0; x < na; x++) { const j = JA[x]; WA[x] = limL[j] > nm ? ((gone[j] || L[j].c === q) ? -Infinity : ((!actT[x] && (keep || !slopeB[j])) ? row[j] : worth(j, B, d, sval(j, d, cm[lc[j]]), undefined, 1))) : (goneL[j] ? -Infinity : ((keep || (!slopeB[j] && sameL[j])) ? row[j] : worth(j, B, -1, null, SVL[j], 1))); }
        U = routeT(LA, na, WA, b, U, left, keyMask, cut, i === K ? v3 : null, null, i);
        histA[i] = U;
      }
      return U;
    };
    const aff = new Int32Array(n), affW = new Float64Array(n), affT = new Float64Array(n), affV = new Array(n);
    const blK = new Uint8Array(n);                      // this phase's copy of look j has a block among its contests
    const blL = split ? new Uint8Array(n) : blK;        // (and the later phases' copy)
    const markBl = (rows_, out) => { for (let j = 0; j < n; j++) { let any = 0; const row = rows_[j]; for (let e = 0; e < 5; e++) if (row[e] && (row[e].bl || (mixOk[j] && row[e].st && row[e].st.bl))) { any = 1; break; } out[j] = any; } };
    const markBlK = () => { markBl(SVK, blK); if (split) markBl(SVL, blL); };
    markBlK();
    // Step 31, fix 1 (Shaun, 26 Nov 2026: "after an action, re-read only what it touched"). A candidate movement of
    // the defence's answer (defender d to square q) changes a look only if d contests it from q, contested it from
    // where he stood, or q is its square; and, where it changes what a block leads to, the looks a block bears on.
    // Every other look keeps its worth as the defence stands (rows[i]). Most of the court is touched by one defender,
    // so the touched looks aren't read up front either. For each defender, runCur keeps a ceiling on every look: what
    // it is worth with that defender's contest taken off (no move of his can make it worth more). The route sum takes
    // the looks highest ceiling first and reads a look again only when its ceiling could still beat what is found; it
    // stops when none can (a look's route is never worth more than the larger of its own worth and the bar). The answer
    // is the largest of the same numbers, worked out the same way, so it is identical to reading every look.
    const vNH = new Uint8Array(n), vP0 = new Uint8Array(n), vH = new Uint8Array(n), slotOf = new Int8Array(n);
    for (let j = 0; j < n; j++) {
      const o = L[j], kb = (keyMask >> o.a) & 1;
      if (o.a !== b) { vNH[j] = o.n0 > left + kb ? 0 : 1; vP0[j] = (vNH[j] && o.p0 > 0 && o.n0 + 1 <= left + kb) ? 1 : 0; slotOf[j] = o.a; }
      else { vH[j] = o.n0 > left ? 0 : 1; slotOf[j] = o.dr ? 5 : b; }
    }
    // the ceilings, and the looks in buckets by them (one unit wide, highest first): UB[d] for the phases before the
    // last and the last phase's looks the move reaches; KB[d] for the last phase (a look its shot beats the move to
    // keeps its worth from the contests it had then)
    const UB = [0, 1, 2, 3, 4].map(() => new Float64Array(n)), KB = [0, 1, 2, 3, 4].map(() => new Float64Array(n));
    const KBL = [0, 1, 2, 3, 4].map(() => new Float64Array(n));   // (fix 2: the later phases' ceilings, as KB with their own limit)
    const mkBuckets = () => ({ idx: new Int32Array(n), start: new Int32Array(n + 2), ceil: new Float64Array(n + 1), nb: 0 });
    const DLs = [0, 1, 2, 3, 4].map(mkBuckets), KLs = [0, 1, 2, 3, 4].map(mkBuckets);
    const m1 = new Float64Array(8), m2 = new Float64Array(8), am = new Int8Array(8), mk1 = new Float64Array(8), ml1 = new Float64Array(8);
    const fl = new Int32Array(n), cntB = new Int32Array(64);
    const drL = new Int32Array(n), drLK = new Int32Array(n);   // the ball handler's Dribble routes: always read in full (see routeLazy)
    let nDr = 0, nDrK = 0;
    const bucket = (lst, bound, keep) => {             // counting sort by floor(bound), highest first; keep(j): the look is in the list
      let hi = -Infinity, lo = Infinity, cnt = 0;
      for (let j = 0; j < n; j++) { if (!keep(j)) { fl[j] = 0x7fffffff; continue; } const f = Math.floor(bound[j]); fl[j] = f; if (f > hi) hi = f; if (f < lo) lo = f; cnt++; }
      if (!cnt) { lst.nb = 0; lst.start[0] = 0; return; }
      const nb = Math.min(hi - lo + 1, 60);              // (values beyond 60 units below the top share the last bucket)
      for (let k = 0; k <= nb; k++) cntB[k] = 0;
      for (let j = 0; j < n; j++) if (fl[j] !== 0x7fffffff) cntB[Math.min(hi - fl[j], nb - 1)]++;
      lst.start[0] = 0;
      for (let k = 0; k < nb; k++) { lst.start[k + 1] = lst.start[k] + cntB[k]; lst.ceil[k] = hi - k + 1; cntB[k] = lst.start[k]; }
      lst.ceil[nb - 1] = hi - (nb - 1) + 1;              // the last bucket: everything at or below it; its ceiling is its top
      for (let j = 0; j < n; j++) if (fl[j] !== 0x7fffffff) { const k = Math.min(hi - fl[j], nb - 1); lst.idx[cntB[k]++] = j; }
      lst.nb = nb;
    };
    // (built only when a candidate of that defender is first read after the board changes: many never are)
    let ordGen = 0, ceilGen = -1;
    const bGen = new Int32Array(5).fill(-1);
    function buildOrders() { ordGen++; }
    const ensureOrders = d => {
      if (ceilGen !== ordGen) { buildCeilings(); ceilGen = ordGen; }
      if (bGen[d] !== ordGen) {
        bucket(DLs[d], KBL[d], j => (limL[j] > nm ? !gone[j] : !goneL[j]) && (vNH[j] || vH[j]));
        bucket(KLs[d], KB[d], j => (lim[j] > nm ? !gone[j] : !goneK[j]) && (vNH[j] || vH[j]));
        bGen[d] = ordGen;
      }
    };
    function buildCeilings() {
      for (let j = 0; j < n; j++) {
        const open = L[j].open, T = open.length, row = SV[j], rk = SVK[j], rl = SVL[j];
        for (let t = 0; t < T; t++) { m1[t] = Infinity; m2[t] = Infinity; am[t] = -1; mk1[t] = open[t]; ml1[t] = open[t]; }
        for (let e = 0; e < 5; e++) {
          const x = row[e];
          if (x) { const cv = x.cv; for (let t = 0; t < T; t++) { const v = cv[t]; if (v < m1[t]) { m2[t] = m1[t]; m1[t] = v; am[t] = e; } else if (v < m2[t]) m2[t] = v; } }
          const y = rk[e];
          if (y) { const cv = y.cv; for (let t = 0; t < T; t++) if (cv[t] < mk1[t]) mk1[t] = cv[t]; }
          const w = rl[e];
          if (w) { const cv = w.cv; for (let t = 0; t < T; t++) if (cv[t] < ml1[t]) ml1[t] = cv[t]; }
        }
        let kb0 = -Infinity, kl0 = -Infinity;
        for (let t = 0; t < T; t++) { if (mk1[t] > kb0) kb0 = mk1[t]; if (ml1[t] > kl0) kl0 = ml1[t]; }
        kb0 += adjv[j]; kl0 += adjv[j];
        for (let d = 0; d < 5; d++) {
          let u = -Infinity;
          for (let t = 0; t < T; t++) { let v = open[t]; const c = am[t] === d ? m2[t] : m1[t]; if (c < v) v = c; if (v > u) u = v; }
          UB[d][j] = u + adjv[j];
          KB[d][j] = lim[j] > nm ? UB[d][j] : kb0;
          KBL[d][j] = limL[j] > nm ? UB[d][j] : kl0;
        }
      }
      // fix 3: a look the fake mix reads is worth no more than it is against the Contests from where each defender
      // stands (the mix lies between the closeout's worth and that), so its ceilings are read from those
      for (let j = 0; j < n; j++) {
        if (!mixOk[j] || !(fkK || fkL)) continue;
        const open = L[j].open, T = open.length, row = SV[j], rk = SVK[j], rl = SVL[j];
        for (let t = 0; t < T; t++) { m1[t] = Infinity; m2[t] = Infinity; am[t] = -1; mk1[t] = open[t]; ml1[t] = open[t]; }
        for (let e = 0; e < 5; e++) {
          const x = row[e] && row[e].st;
          if (x) { const cv = x.cv; for (let t = 0; t < T; t++) { const v = cv[t]; if (v < m1[t]) { m2[t] = m1[t]; m1[t] = v; am[t] = e; } else if (v < m2[t]) m2[t] = v; } }
          const y = rk[e] && rk[e].st;
          if (y) { const cv = y.cv; for (let t = 0; t < T; t++) if (cv[t] < mk1[t]) mk1[t] = cv[t]; }
          const w = rl[e] && rl[e].st;
          if (w) { const cv = w.cv; for (let t = 0; t < T; t++) if (cv[t] < ml1[t]) ml1[t] = cv[t]; }
        }
        let kb0 = -Infinity, kl0 = -Infinity;
        for (let t = 0; t < T; t++) { if (mk1[t] > kb0) kb0 = mk1[t]; if (ml1[t] > kl0) kl0 = ml1[t]; }
        kb0 += adjv[j]; kl0 += adjv[j];
        for (let d = 0; d < 5; d++) {
          let u = -Infinity;
          for (let t = 0; t < T; t++) { let v = open[t]; const c = am[t] === d ? m2[t] : m1[t]; if (c < v) v = c; if (v > u) u = v; }
          UB[d][j] = u + adjv[j];
          KB[d][j] = lim[j] > nm ? UB[d][j] : kb0;
          KBL[d][j] = limL[j] > nm ? UB[d][j] : kl0;
        }
      }
      nDr = 0; nDrK = 0;
      for (let j = 0; j < n; j++) if (vH[j] && L[j].dr) { if (limL[j] > nm ? !gone[j] : !goneL[j]) drL[nDr++] = j; if (lim[j] > nm ? !gone[j] : !goneK[j]) drLK[nDrK++] = j; }
    }
    // the candidate: defender cd on cq with contests ccm; what a block leads to at each step (cB), whether it differs
    // from the defence as it stands (cChg) and how low (cLo)
    let cd = 0, cq = -1, ccm = null, cStamp = 0, cB = 0, cChg = false, cLo = 0;
    const cMark = new Int32Array(n), cTouch = new Uint8Array(n), cW = new Float64Array(n), cT = new Float64Array(n), cV = new Array(n);
    const touch = j => {                               // is look j one the candidate touches? (read once a candidate)
      if (cMark[j] === cStamp) return cTouch[j];
      cMark[j] = cStamp;
      const mk = ccm[lc[j]];
      if (SV[j][cd] === null && mk === 0 && L[j].c !== cq) { cTouch[j] = 0; return 0; }
      cTouch[j] = 1;
      const nv = sval(j, cd, mk), row = SV[j], open = L[j].open, T = open.length;
      if (mixOk[j] && (fkK || fkL)) { cV[j] = nv; if (L[j].c === cq) { cW[j] = -Infinity; cT[j] = -Infinity; } else { cW[j] = 0; cT[j] = Infinity; } return 1; }   // (fix 3: read in full)
      // his worth with no block bearing on him (cW), and what a block must lead to before none does (cT)
      for (let t = 0; t < T; t++) tmp[t] = open[t];
      for (let e = 0; e < 5; e++) { const x = e === cd ? nv : row[e]; if (!x) continue; const cv = x.cv, bl = x.bl; for (let t = 0; t < T; t++) if (cv[t] < tmp[t]) tmp[t] = cv[t]; if (bl) for (let z = 0; z < bl.length; z += 3) if (!(bl[z + 2] > 0) && bl[z + 1] < tmp[bl[z]]) tmp[bl[z]] = bl[z + 1]; }
      let thr = -Infinity;
      for (let e = 0; e < 5; e++) { const x = e === cd ? nv : row[e], bl = x && x.bl; if (!bl) continue; for (let z = 0; z < bl.length; z += 3) if (bl[z + 2] > 0) { const h = (tmp[bl[z]] - bl[z + 1]) / bl[z + 2]; if (h > thr) thr = h; } }
      let tp = tmp[0]; for (let t = 1; t < T; t++) if (tmp[t] > tp) tp = tmp[t];
      cW[j] = L[j].c === cq ? -Infinity : tp + adjv[j]; cT[j] = L[j].c === cq ? -Infinity : thr; cV[j] = nv;
      return 1;
    };
    const valAt = (i, j) => {                          // look j's worth at step i with the candidate in place
      if (i === K ? lim[j] <= nm : limL[j] <= nm) {    // that phase's shot is up before the move
        if (i === K ? goneK[j] : goneL[j]) return -Infinity;
        return (cChg && (i === K ? blK[j] : blL[j])) ? worth(j, cB, -1, null, i === K ? SVK[j] : SVL[j], i === K ? 0 : 1) : rows[i][j];
      }
      if (gone[j]) return -Infinity;
      if (touch(j)) return cB >= cT[j] ? cW[j] : worth(j, cB, cd, cV[j], undefined, i === K ? 0 : 1);
      if (cChg && (i === K ? blK[j] : bmax[j] > cLo)) return i === K ? worth(j, cB, -1, null, SVK[j], 0) : worth(j, cB, -1, null, undefined, 1);
      return rows[i][j];
    };
    let barK = 0;
    // (a route's worth is a weighted average of two numbers, and can round a hair above the larger of them: every
    // "can't beat it" test keeps this margin, far above any rounding and far below any real difference)
    const EPS_B = 1e-9;
    // the fall-back pass after a lost Dribble (routeT's `fall`), at step i, worked out only when a Dribble route needs it
    let fStep = -1, fStamp = -1, fVal = 0;
    const fallAt = (i, bar) => {
      if (fStep === i && fStamp === cStamp) return fVal;
      const lst = i === K ? KLs[cd] : DLs[cd], bd = i === K ? KB[cd] : KBL[cd], idx = lst.idx, st = lst.start, ce = lst.ceil, nb = lst.nb;
      let fall = bar;
      for (let k = 0; k < nb; k++) {
        if (ce[k] + EPS_B <= fall) break;
        for (let x = st[k]; x < st[k + 1]; x++) {
          const j = idx[x];
          if (!vP0[j] || bd[j] + EPS_B <= fall) continue;
          const v = valAt(i, j);
          if (v === -Infinity) continue;
          const o = L[j], p = o.p0 >= 1 ? 1 : Math.max(0, o.p0 - cut), f = p * (v > bar ? v : bar) + (1 - p) * (bar - o.lc);
          if (f > fall) fall = f;
        }
      }
      fStep = i; fStamp = cStamp; fVal = fall;
      return fall;
    };
    const routeLazy = (i, bar) => {                    // T(bar) at step i with the candidate in place: routeT over every look
      const lst = i === K ? KLs[cd] : DLs[cd], bd = i === K ? KB[cd] : KBL[cd], idx = lst.idx, st = lst.start, ce = lst.ceil, nb = lst.nb;
      let best = bar;
      for (let k = 0; k < nb; k++) {                    // the passes
        if (ce[k] + EPS_B <= best) break;
        for (let x = st[k]; x < st[k + 1]; x++) {
          const j = idx[x];
          if (!vNH[j] || bd[j] + EPS_B <= best) continue;
          const v = valAt(i, j);
          if (v === -Infinity) continue;
          const o = L[j], e = o.r * (v > bar ? v : bar) + (1 - o.r) * (bar - o.lc);
          if (e > best) best = e;
        }
      }
      // the ball handler's own routes: a set look is worth max(v, bar), exactly, so one whose ceiling is below best is
      // passed over. A Dribble route is worth r * max(v, bar) + (1 - r) * fall, a weighted average that can round a
      // hair above both when they are level: those few are always read, with fall worked out in full
      for (let k = 0; k < nb; k++) {
        if (ce[k] + EPS_B <= best) break;
        for (let x = st[k]; x < st[k + 1]; x++) {
          const j = idx[x];
          if (!vH[j] || L[j].dr || bd[j] + EPS_B <= best) continue;
          const v = valAt(i, j);
          if (v === -Infinity) continue;
          const e = v > bar ? v : bar;
          if (e > best) best = e;
        }
      }
      const dl = i === K ? drLK : drL, nd = i === K ? nDrK : nDr;
      for (let x = 0; x < nd; x++) {
        const j = dl[x], v = valAt(i, j);
        if (v === -Infinity) continue;
        const o = L[j], e = o.r * (v > bar ? v : bar) + (1 - o.r) * fallAt(i, bar);
        if (e > best) best = e;
      }
      if (i === K) barK = bar;
      return best;
    };
    // how many of the six route slots reach u at the last step (topCount over the routes routeT would give), for the
    // candidate just read
    const candTop = u => {
      const thr = u - 1e-9, bar = barK, lst = KLs[cd], bd = KB[cd], idx = lst.idx, st = lst.start, ce = lst.ceil, nb = lst.nb;
      const hit = [false, false, false, false, false, false];
      let left6 = 6, fall = null;
      for (let k = 0; k < nb && left6 > 0; k++) {
        const top = ce[k];
        if (top + EPS_B < thr && bar + EPS_B < thr) {   // nothing further can reach it, but a Dribble route through its fall-back
          if (hit[5]) break;
          if (fall === null) fall = fallAt(K, bar);
          if (fall + EPS_B < thr) break;
        }
        for (let x = st[k]; x < st[k + 1]; x++) {
          const j = idx[x], sl = slotOf[j];
          if (hit[sl]) continue;
          const o = L[j];
          if (Math.max(bd[j], bar) + EPS_B < thr && !(o.a === b && o.dr)) continue;
          const v = valAt(K, j);
          if (v === -Infinity) continue;
          let e;
          if (o.a !== b) e = o.r * (v > bar ? v : bar) + (1 - o.r) * (bar - o.lc);
          else if (o.dr) { if (fall === null) fall = fallAt(K, bar); e = o.r * (v > bar ? v : bar) + (1 - o.r) * fall; }
          else e = v > bar ? v : bar;
          if (e >= thr) { hit[sl] = true; left6--; }
        }
      }
      return 6 - left6;
    };
    const runCand = (d, q, cm) => {                     // the same sum with defender d on q (contests cm): only what he touches is read again
      ensureOrders(d);
      cd = d; cq = q; ccm = cm; cStamp++;
      let U = SHOT_CLOCK_OUT; histC[0] = U;
      for (let i = 1; i <= K; i++) {
        cB = i >= 3 ? histC[i - 2] : 0;
        cChg = i >= 3 && histC[i - 2] !== hist[i - 2];
        cLo = cChg ? Math.min(histC[i - 2], hist[i - 2]) : 0;
        U = routeLazy(i, U);
        histC[i] = U;
      }
      return U;
    };
    // Step 31, fix 1: the candidate reading as it was, every look read again, kept only as the reference a test holds
    // the reading by difference to (PV_CHECK; tests/test_exam.py). Never run in play.
    const histF = new Float64Array(K + 1);
    const runCandFull = (d, q, cm) => {                     // (the test's reference: the same sum read over every look, as before fix 1)
      let na = 0;
      for (let j = 0; j < n; j++) {
        if (gone[j]) continue;
        const mk = cm[lc[j]];
        if (SV[j][d] === null && mk === 0 && L[j].c !== q) continue;
        const nv = sval(j, d, mk), row = SV[j], open = L[j].open, T = open.length;
        if (mixOk[j] && (fkK || fkL)) { affW[na] = L[j].c === q ? -Infinity : 0; affT[na] = L[j].c === q ? -Infinity : Infinity; affV[na] = nv; aff[na++] = j; continue; }
        // his worth with no block bearing on him (affW), and what a block must lead to before none does (affT)
        for (let t = 0; t < T; t++) tmp[t] = open[t];
        for (let e = 0; e < 5; e++) { const x = e === d ? nv : row[e]; if (!x) continue; const cv = x.cv, bl = x.bl; for (let t = 0; t < T; t++) if (cv[t] < tmp[t]) tmp[t] = cv[t]; if (bl) for (let z = 0; z < bl.length; z += 3) if (!(bl[z + 2] > 0) && bl[z + 1] < tmp[bl[z]]) tmp[bl[z]] = bl[z + 1]; }
        let thr = -Infinity;
        for (let e = 0; e < 5; e++) { const x = e === d ? nv : row[e], bl = x && x.bl; if (!bl) continue; for (let z = 0; z < bl.length; z += 3) if (bl[z + 2] > 0) { const h = (tmp[bl[z]] - bl[z + 1]) / bl[z + 2]; if (h > thr) thr = h; } }
        let tp = tmp[0]; for (let t = 1; t < T; t++) if (tmp[t] > tp) tp = tmp[t];
        affW[na] = L[j].c === q ? -Infinity : tp + adjv[j]; affT[na] = L[j].c === q ? -Infinity : thr; affV[na] = nv; aff[na++] = j;
      }
      let U = SHOT_CLOCK_OUT; histF[0] = U;
      for (let i = 1; i <= K; i++) {
        const B = i >= 3 ? histF[i - 2] : 0;
        W.set(rows[i]);
        if (i >= 3 && histF[i - 2] !== hist[i - 2]) {    // a block now leads somewhere else: only the looks a block still bears on move
          const lo = Math.min(histF[i - 2], hist[i - 2]);
          if (i === K) { for (let j = 0; j < n; j++) if (!goneK[j] && blK[j]) W[j] = worth(j, B, -1, null, SVK[j], 0); }
          else { for (let j = 0; j < n; j++) if (!goneL[j] && blL[j]) W[j] = worth(j, B, -1, null, SVL[j], 1); }
        }
        if (i === K) { for (let x = 0; x < na; x++) if (lim[aff[x]] > nm) W[aff[x]] = B >= affT[x] ? affW[x] : worth(aff[x], B, d, affV[x], undefined, 0); }
        else for (let x = 0; x < na; x++) if (limL[aff[x]] > nm) W[aff[x]] = B >= affT[x] ? affW[x] : worth(aff[x], B, d, affV[x], undefined, 1);
        U = routeT(L, n, W, b, U, left, keyMask, cut, i === K ? v2 : null, null, i);
        histF[i] = U;
      }
      return U;
    };
    const bars = [];
    let U = runCur(bars);
    if (probe) {
      // (the stance search's first look: the number with defender probe.d standing on each [square, arrow], by
      // difference: his contests there, the walls and lanes as they stand. It only chooses which squares are then read
      // in full.)
      lim.fill(32767); if (split) limL.fill(32767);
      buildOrders();                                    // (the ceilings depend on how far each look's limit reaches)
      const qsP = s.ctx.dfn[probe.d].qs, modeP = stanceMode(m.sN, probe.d), est = new Float64Array(probe.cands.length);
      for (let x = 0; x < probe.cands.length; x++) est[x] = runCand(probe.d, probe.cands[x][0], cm2Cached(probe.cands[x][0], probe.cands[x][1], qsP, modeP));
      if (PV_CHECK) for (let x = 0; x < probe.cands.length; x++) { const f = runCandFull(probe.d, probe.cands[x][0], cm2Cached(probe.cands[x][0], probe.cands[x][1], qsP, modeP)); PVC.n++; if (f !== est[x]) { PVC.bad++; if (PVC.ex.length < 5) PVC.ex.push([est[x], f]); } }
      return { est, U };
    }
    const U0 = U, worth0 = rows[K].slice();
    PVS.reads++; PVS.looks += n;
    const moves = [], moved = [false, false, false, false, false], taken = new Set();
    for (let j = 0; j < 5; j++) { taken.add(s.o[j]); taken.add(s.x[j]); }
    let tok = noAnswer ? 0 : s.tok_x;
    while (tok > 0 && act.length) {
      // Each movement first gets a bound (the sum over only the looks the value turns on: runAct), then they are read in
      // full best bound first. The first whose full reading is as good as its bound is the answer: no later one can
      // beat its own bound. (A cut that can't change the answer; it replaces reading every movement in full.)
      const cands = [], bm0 = topCount(vec, U);
      const offer = (d, q, a, cm) => {
        if (PV_BRUTE) { cands.push({ d, q, a, cm, ua: -Infinity, ma: 0 }); return; }
        // A movement can only lower the value by lowering a look the value turns on, at the step it turns on it (every
        // route's worth only rises with what playing on is worth): one that lowers none of them is not read further.
        let lowers = false;
        for (let x = 0; x < act.length; x += 2) {
          const j = act[x], i = act[x + 1];
          if (gone[j]) continue;
          if ((i === K ? lim : limL)[j] <= nm) continue;                    // that phase's shot is up before this movement
          if (L[j].c === q) { lowers = true; break; }
          const mk = cm[lc[j]];
          if (!mk && SV[j][d] === null) continue;
          if (worth(j, i >= 3 ? hist[i - 2] : 0, d, sval(j, d, mk), undefined, i === K ? 0 : 1) < rows[i][j] - 1e-9) { lowers = true; break; }
        }
        PVS.offers++; if (!lowers) return;
        const ua = runAct(d, q, cm), ma = topCount(v3, ua);
        if (ua > U + 1e-9 || (ua >= U - 1e-9 && ma >= bm0)) return;     // it can't lower the value, nor the routes that reach it
        cands.push({ d, q, a, cm, ua, ma });
      };
      for (let d = 0; d < 5; d++) {
        if (moved[d] || !ONB[s.x[d]]) continue;
        const cp = caps(s, 'X', d);
        if (!cp[0] && cp[1] <= 0) continue;
        const qs = s.ctx.dfn[d].qs, mode = stanceMode(m.sN, d), fr = defenderReachExact(s, d);
        if (cp[0]) for (let a = 0; a < 8; a++) if (a !== s.arrows[d]) offer(d, s.x[d], a, cmAfter(s.x[d], a, qs, mode, 'move', cp[1]));   // a Move on the spot: a new pair of arrows
        // (a square from which no pair of arrows contests any look the value turns on is passed over whole: anyArrow2 is
        // every pair's contests together, so none of the eight can lower one)
        let had = false;
        for (let x = 0; x < act.length && !had; x += 2) if (SV[act[x]][d] !== null) had = true;
        const bears = q => {
          if (had || PV_BRUTE) return true;
          const any = anyArrow2(q, qs, mode);
          for (let x = 0; x < act.length; x += 2) { const j = act[x]; if (L[j].c === q || any[lc[j]]) return true; }
          return false;
        };
        // (fix 3: his reply from there is what the movement leaves him: cmAfter)
        for (const [q, na] of fr[0]) if (na === 1 && !taken.has(q) && bears(q)) for (let a = 0; a < 8; a++) offer(d, q, a, cmAfter(q, a, qs, mode, 'move', cp[1]));
        for (const [q, arrs] of fr[1]) if (!taken.has(q)) for (const [a, na] of arrs) if (na === 1) offer(d, q, a, cmAfter(q, a, qs, mode, fixedKind(s, d, q, a), cp[1]));
      }
      // the value first; level, the fewer routes that reach it (covering one of two equal looks is a step toward covering
      // both); still level, the lower square, then the arrow, then where he starts (never the order the defenders are listed in)
      const before = (x, y) => (Math.abs(x.u - y.u) > 1e-9 ? x.u - y.u : (x.m - y.m) || (x.q - y.q) || (x.a - y.a) || (s.x[x.d] - s.x[y.d]));
      for (const c of cands) { c.u = c.ua; c.m = c.ma; }
      cands.sort(before);
      let best = null;
      for (const c of cands) {
        if (best !== null && before(best, c) <= 0) break;                 // its bound is already no better than the best read in full
        PVS.runs++;
        const u = runCand(c.d, c.q, c.cm), mm = u > U + 1e-9 ? 0 : candTop(u);    // (the count is wanted only when the value doesn't rise)
        if (PV_CHECK) {
          const mmN = candTop(u), uF = runCandFull(c.d, c.q, c.cm), mmF = topCount(v2, uF);
          PVC.n++;
          if (uF !== u || mmF !== mmN) { PVC.bad++; if (PVC.ex.length < 5) PVC.ex.push([u, uF, mmN, mmF]); }
        }
        if (u > U + 1e-9 || (u >= U - 1e-9 && mm >= bm0)) continue;
        const full = { d: c.d, q: c.q, a: c.a, cm: c.cm, u, m: mm };
        if (best === null || before(full, best) < 0) best = full;
      }
      if (best === null) break;
      const { d, q, a, cm } = best;
      for (let i = 0; i < n; i++) {
        const nv = sval(i, d, cm[lc[i]]);
        if (L[i].c === q) gone[i] = 1;
        SV[i][d] = nv;
        if (lim[i] > nm) { if (L[i].c === q) goneK[i] = 1; SVK[i][d] = nv; }
        if (split && limL[i] > nm) { if (L[i].c === q) goneL[i] = 1; SVL[i][d] = nv; }
      }
      nm++; markBlK();
      // fix 3b: the fake's follow-up is read on the board the answer leaves, with its rotations
      { const qsd = s.ctx.dfn[d].qs, cp = caps(s, 'X', d);
        movedAt[d] = { q, a, kind: cm === cmAfter(q, a, qsd, stanceMode(m.sN, d), 'move', cp[1]) ? 'move' : fixedKind(s, d, q, a) };
        for (let i = 0; i < n; i++) SV0[i] = SV[i].slice();
        Fm.clear(); Gm.clear(); UB0.fill(null); ORD0.fill(null); }
      moves.push([d, q, a]); moved[d] = true; taken.add(q); tok--; PVS.steps++;
      U = runCur(null);
      if (Math.abs(U - best.u) > 1e-9) PVS.bad = (PVS.bad || 0) + 1;   // (a guard: the reading by difference must equal the full reading of the board after the movement)
    }
    const after = Array.from(hist), last = Vit.slice(K * n, (K + 1) * n);
    let pick = -1, pe = -Infinity; const B = hist[K - 1];
    for (let x = 0; x < act.length; x += 2) if (act[x + 1] === K) { const i = act[x], o = L[i], e = o.r * Math.max(last[i], B) + (1 - o.r) * (B - o.lc); if (e > pe) { pe = e; pick = i; } }
    const mixInfo = j => {                              // (fix 3, for the report: look j's fake line this phase, as the defence finally stands)
      if (goneK[j] || !mixOk[j] || !fkK) return null;
      const Bk = K >= 3 ? hist[K - 2] : 0, wc = core(j, Bk, -1, null, SVK[j]), e0 = arg[cTb];
      if (e0 < 0) return null;
      const v = worth(j, Bk, -1, null, SVK[j], 0);
      if (!(v > wc + 1e-9)) return null;
      const f = follow(j, e0);
      return { closer: e0, from: f.from, then: f.then, faked: f.F, contested: wc, mixed: v };
    };
    return { U, U0, worth0, k, bars: after, before: bars, moves, L, worth: last, pick: pick >= 0 ? L[pick] : null, pickWorth: pick >= 0 ? last[pick] : null, routes: Float64Array.from(vec), mixInfo, races, fakeRaces };
  }
  // step 31, fix 3: look i's two-step route for the report: who closes out, from where, and the look that follows the
  // fake (the shooter's own drive; a cutter at the rim behind the help; or a kick-out to the man he left)
  function twoStep(pp, i) {
    const mx = pp.mixInfo ? pp.mixInfo(i) : null;
    if (!mx || mx.then === -1) return null;
    if (mx.then === -2) return { route: 'shot fake beats the closeout, then the drive (its race)', closer: 'X' + (mx.closer + 1), closes_to: sqName(mx.from), then: 'the drive', contested: +mx.contested.toFixed(2), if_faked: +mx.faked.toFixed(2), worth: +mx.mixed.toFixed(2) };
    // (a cut: the man the ball goes to ends nearer the rim than where he stands now)
    const o = pp.L[i], o2 = pp.L[mx.then], s = pp.m.s, drove = o.a === s.ball && o.c !== s.o[o.a], cut = cheb(o2.c, RIM) < cheb(s.o[o2.a], RIM);
    const kind = o2.a === o.a ? 'closeout, then shot fake and drive' : drove ? (cut ? 'drive, then backdoor cut' : 'drive, then kick-out') : (cut ? 'shot fake, then pass to a cutter' : 'shot fake, then kick-out');
    return { route: kind, closer: 'X' + (mx.closer + 1), closes_to: sqName(mx.from), then: 'O' + (o2.a + 1) + ' ' + sqName(o2.c), contested: +mx.contested.toFixed(2), if_faked: +mx.faked.toFixed(2), worth: +mx.mixed.toFixed(2) };
  }
  function possParts(s) {                              // {V, k, bars, pick, m, ...}: the value of playing on (what is banked not counted)
    if (s.stage !== 'play') return { V: SHOT_CLOCK_OUT, k: 0, bars: [SHOT_CLOCK_OUT], pick: null, m: null, moves: [] };
    const key = MAP_MEMO !== null ? 'PV|' + (MAP_ME || '') + '|' + stateKey(s) : null;
    if (key !== null) { const hit = MAP_MEMO.get(key); if (hit !== undefined) return hit; }
    let out;
    if (s.pending) {                                   // a pass in the air: the catch by the rules' chance; lost, -5 and the next phase
      const recv = s.pending[1], base = W_(s, { pending: null, approach: -1 });
      const p = covPass(base, recv, s.o[recv]);
      const pc = possParts(W_(base, { ball: recv }));
      const lost = s.clock - 2 > 2 ? possParts(W_(covFresh(base), { clock: s.clock - 2 })).V : SHOT_CLOCK_OUT;
      out = Object.assign({}, pc, { V: p * pc.V + (1 - p) * (lost - TURNOVER_COST), catch: p });
    } else {
      // The last phase (step 31): its own looks, with what the offence really has left (the shot needs an action too).
      const lastPhase = s.clock <= 2;
      const m = lastPhase ? covBuild(W_(s, { turn_n: 0, side: 'O', approach: -1, prev_wait: '', final: false, turn_lead: -1, turn_x: [], turn_moved: 0, react_moved: 0 }), true, null, true)
        : covBuild(covOffFresh(s), true, null);
      const rd = possRead(m, s, lastPhase);
      out = Object.assign(rd, { V: rd.U - TURNOVER_COST * threeSecondsOwed(s), m });
    }
    if (key !== null) MAP_MEMO.set(key, out);
    return out;
  }
  // ---- Step 31, stage 2 (Shaun, 25 Nov 2026): the team's weight map and its centre -----------------------------------------
  // "The team's weight is a map of where a defender's presence saves the most points right now." Three layers, on the
  // one scale (docs/reference/GRAVITY_AND_SPACING_DESIGN.md, "The defence, part 1"):
  //   1. the points a contest saves: a look's worth with nobody on it, less its worth against the best answer a defender
  //      can give standing there (set, in front, his arrow on the shooter: the contest by position; the block where it
  //      pays, read as a line in what the phase after it is worth; against a shooter in control the fake is a two-by-two
  //      mix, shoot or fake against close out or hold, D-296, and its value is the hold's, because the shot fake sells the
  //      block: so a block counts only against a rushed shooter, who can't fake). Whose contest (D-288): the best of the
  //      five for the team's map and its centre; each defender's own for his own base position (`own`).
  //   2. occupation: each zone cut into segments (D-287, data/segments.json, provisional); a segment no attacker can
  //      reach this phase carries nothing.
  //   3. the ball's reach: each look at the chance its man has the ball there in time, by the rules (the pass's chance,
  //      the Dribble's). Counted once, here: nothing that reads the map discounts it again.
  // One entry an attacker a segment (his heaviest look in it). The centre of gravity is where the entries balance. It
  // is a summary: `lumps` gives the weight itself, group by group (looks within two squares of each other).
  // `left` is the same weight with the cover it already faces taken off (covered weight pulls less, by as much as the
  // cover takes off): what a further defender would still save there.
  const SEGI = { names: null, of: null };
  function segInit() {
    if (SEGI.names) return SEGI;
    const g = D.segments;
    if (!g) throw new Error('the segments table (data/segments.json) was not loaded');
    const names = g.order, idx = Object.fromEntries(names.map((n, i) => [n, i])), of = new Array(NSQ).fill(null);
    for (let c = 0; c < NSQ; c++) {
      if (!ONB[c]) continue;
      let y = SY[c]; const x = SX[c];
      if (g.behind[String(y)]) y = +g.behind[String(y)];
      const row = g.rows[String(y)];
      if (!row) continue;
      const v = row[x];
      of[c] = (g.both[v] || [v]).map(n => idx[n]);
    }
    SEGI.names = names; SEGI.of = of;
    return SEGI;
  }
  const W_K0 = 1;                                        // the contest kind "in front, his arrow on the shooter" (KPEN, KFOUL, KTWO all false)
  function weightMap(s) {
    if (s.stage !== 'play') return null;
    const base = s.pending ? W_(s, { ball: s.pending[1], pending: null, approach: -1 }) : s;
    const pp = possParts(base);
    if (!pp.m) return null;
    const key = MAP_MEMO !== null ? 'WM|' + stateKey(base) : null;
    if (key !== null) { const hit = MAP_MEMO.get(key); if (hit !== undefined) return hit; }
    const seg = segInit(), m = pp.m, r = m.r, ctx = m.s.ctx, soft = ctx.soft, L = pp.L, n = L.length;
    const B = pp.before.length >= 2 ? pp.before[pp.before.length - 2] : 0;   // what playing on is worth as the board stands (a block leads there)
    const ws = m._ws || (m._ws = new Map());
    const cont = new Float64Array(5);
    const looks = [];
    for (let i = 0; i < n; i++) {
      const o = L[i], open = o.open, T = open.length, fake = !o.rushed;
      if (o.race) continue;                              // (a drive's race look has no Contest of its own to weigh)
      let op = open[0]; for (let t = 1; t < T; t++) if (open[t] > op) op = open[t];
      let best = Infinity, by = -1;
      for (let d = 0; d < 5; d++) {
        if (!ONB[m.s.x[d]]) { cont[d] = op; continue; }
        const kk = o.id * 5 + d;
        let sv = ws.get(kk);
        if (sv === undefined) { const lines = []; const cv = r._valsCalc(o.lk, d, W_K0, W_K0, (o.fl || 0) | 4, soft ? W_K0 : 0, soft ? W_K0 : 0, lines); sv = cv ? { cv, bl: lines.length ? Float64Array.from(lines) : null } : null; ws.set(kk, sv); }
        let v = op;
        if (sv) {
          v = -Infinity;
          for (let t = 0; t < T; t++) {
            let u = Math.min(open[t], sv.cv[t]);
            if (!fake && sv.bl) for (let z = 0; z < sv.bl.length; z += 3) if (sv.bl[z] === t) { const b = sv.bl[z + 1] + sv.bl[z + 2] * B; if (b < u) u = b; }
            if (u > v) v = u;
          }
        }
        cont[d] = v;
        if (v < best - 1e-12) { best = v; by = d; }
      }
      const stands = pp.worth0[i] - o.adj;              // what the look is worth against the cover it already faces
      const own = Array.from(cont, v => +(o.r * Math.max(0, Math.min(op, stands) - v)).toFixed(6));
      looks.push({ i, a: o.a, c: o.c, q0: o.q0, r: o.r, open: op, contested: best, by, saving: op - best, weight: o.r * Math.max(0, op - best),
        left: o.r * Math.max(0, Math.min(op, stands) - best), stands, own });
    }
    // one entry an attacker a segment: his heaviest look there (level: the lower square)
    const pick = (field) => {
      const ent = new Map();
      for (const k of looks) {
        const sg = seg.of[k.c];
        if (!sg || !(k[field] > 1e-9)) continue;
        for (const g of sg) { const key = k.a * 32 + g, cur = ent.get(key); if (!cur || k[field] > cur[field] + 1e-9 || (Math.abs(k[field] - cur[field]) <= 1e-9 && k.c < cur.c)) ent.set(key, k); }
      }
      return ent;
    };
    const balance = (ent, field) => {                   // where the entries balance; a look that leads two segments is counted once
      let sw = 0, sx = 0, sy = 0; const seen = new Set();
      for (const k of ent.values()) { const id = k.a * 4096 + k.c; if (seen.has(id)) continue; seen.add(id); sw += k[field]; sx += k[field] * SX[k.c]; sy += k[field] * SY[k.c]; }
      return sw > 0 ? { total: sw, x: sx / sw, y: sy / sw } : { total: 0, x: SX[RIM], y: SY[RIM] };
    };
    const ent = pick('weight'), entL = pick('left');
    const cen = balance(ent, 'weight'), cenL = balance(entL, 'left');
    // the weight itself, group by group: entries whose squares are within two of each other
    const lumpsOf = (entm, field) => {
      const uniq = new Map(); for (const k of entm.values()) uniq.set(k.a * 4096 + k.c, k);
      const items = [...uniq.values()].sort((u, v) => u.c - v.c || u.a - v.a), gid = items.map((_, i) => i);
      const find = i => { while (gid[i] !== i) i = gid[i]; return i; };
      for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) if (cheb(items[i].c, items[j].c) <= 2) { const a = find(i), b = find(j); if (a !== b) gid[Math.max(a, b)] = Math.min(a, b); }
      const groups = new Map();
      items.forEach((k, i) => { const g = find(i); let o = groups.get(g); if (!o) { o = { weight: 0, x: 0, y: 0, top: k, n: 0 }; groups.set(g, o); } o.weight += k[field]; o.x += k[field] * SX[k.c]; o.y += k[field] * SY[k.c]; o.n++; if (k[field] > o.top[field] + 1e-9) o.top = k; });
      return [...groups.values()].map(o => ({ weight: o.weight, x: o.x / o.weight, y: o.y / o.weight, top: o.top, n: o.n })).sort((u, v) => v.weight - u.weight || u.top.c - v.top.c);
    };
    const out = { looks, entries: ent, left: entL, centre: cen, centreLeft: cenL, lumps: lumpsOf(ent, 'weight'), lumpsLeft: lumpsOf(entL, 'left'), B, seg };
    if (key !== null) MAP_MEMO.set(key, out);
    return out;
  }
  // Layer 1 alone, from the cards and the empty board (worked out once a game): every attacker's saving in every
  // segment whether or not he can get there, and where those balance: the base centre of gravity.
  function weightBase(s) {
    const ctx = s.ctx;
    if (ctx._wbase) return ctx._wbase;
    const seg = segInit(), r = new Read(W_(s, { stage: 'play', pending: null })), soft = ctx.soft, ent = new Map();
    for (let c = 0; c < NSQ; c++) {
      if (!ONB[c] || !SHOOT(szone(ctx, c)) || (ctx.noRim && c === RIM) || !seg.of[c]) continue;
      const z = szone(ctx, c), types = ZONE_SHOTS[z], pts = ctx.worth[z];
      for (let a = 0; a < 5; a++) {
        const lk = makeLook(a, c, 'later', 1.0, false); lk.types = types; lk.rushed = false;
        let op = -Infinity; const open = types.map(t => pts * cardShot(ctx, ctx.off[a], t, c)); for (const v of open) if (v > op) op = v;
        let best = op;
        for (let d = 0; d < 5; d++) {
          const cv = r._valsCalc(lk, d, W_K0, W_K0, 4, soft ? W_K0 : 0, soft ? W_K0 : 0, []);
          if (!cv) continue;
          let v = -Infinity; for (let t = 0; t < types.length; t++) { const u = Math.min(open[t], cv[t]); if (u > v) v = u; }
          if (v < best) best = v;
        }
        const k = { a, c, weight: op - best, open: op, contested: best };
        if (!(k.weight > 1e-9)) continue;
        for (const g of seg.of[c]) { const key = a * 32 + g, cur = ent.get(key); if (!cur || k.weight > cur.weight + 1e-9 || (Math.abs(k.weight - cur.weight) <= 1e-9 && c < cur.c)) ent.set(key, k); }
      }
    }
    let sw = 0, sx = 0, sy = 0; const seen = new Set();
    for (const k of ent.values()) { const id = k.a * 4096 + k.c; if (seen.has(id)) continue; seen.add(id); sw += k.weight; sx += k.weight * SX[k.c]; sy += k.weight * SY[k.c]; }
    return (ctx._wbase = { entries: ent, centre: sw > 0 ? { total: sw, x: sx / sw, y: sy / sw } : { total: 0, x: SX[RIM], y: SY[RIM] } });
  }
  function weightJSON(s) {                             // the map for the view, the tools and the tests
    const w = weightMap(s);
    if (!w) return null;
    const seg = w.seg, r2 = v => +v.toFixed(2), xy = c => ({ x: r2(c.x), y: r2(c.y), sq: sqName(C(Math.round(c.x), Math.round(c.y))), total: r2(c.total) });
    const ents = entm => [...entm.entries()].sort((u, v) => u[0] - v[0]).map(([key, k]) => ({ a: k.a, seg: seg.names[key % 32], c: sqName(k.c), ball_at: sqName(k.q0), reach: +k.r.toFixed(4), open: r2(k.open), contested: r2(k.contested), by: k.by, saving: r2(k.saving), weight: r2(k.weight), left: r2(k.left), own: k.own.map(r2) }));
    const lump = l => ({ weight: r2(l.weight), x: r2(l.x), y: r2(l.y), sq: sqName(C(Math.round(l.x), Math.round(l.y))), top: { a: l.top.a, c: sqName(l.top.c) }, entries: l.n });
    const wb = weightBase(s);
    return { centre: xy(w.centre), centre_left: xy(w.centreLeft), base_centre: xy(wb.centre), entries: ents(w.entries), left: ents(w.left).filter(e => e.left > 0),
      lumps: w.lumps.map(lump), lumps_left: w.lumpsLeft.map(lump), playing_on: r2(w.B),
      base: [...wb.entries.entries()].sort((u, v) => u[0] - v[0]).map(([key, k]) => ({ a: k.a, seg: seg.names[key % 32], c: sqName(k.c), open: r2(k.open), contested: r2(k.contested), weight: r2(k.weight) })) };
  }
  // ---- Step 31, stage 3 (Shaun, 25 Nov 2026): the defence's five stances ------------------------------------------------------
  // "The defence, each time it sets up: build the weight map and its centre; place every defender on his base position
  // (on the line between his man and the part of the weight he would help, at the depth the link rule gives: the
  // goal-side starting shape); improve it (try moving and turning one defender at a time, keeping any change that
  // lowers the number, until none does); check the result against the link rule and the goal-side checks."
  // The number is the possession's value (possParts): what the offence can still get after the defence's own answer
  // with the actions it has this phase. A stance is a square and a pair of arrows, chosen together. A change is kept
  // only when it lowers the number; level on the number, when it needs fewer of the phase's actions to hold it there
  // (a movement costs an action: it is the moves it takes, never a number set by hand). Otherwise he stays where his
  // base position put him. Nothing names a trap, a switch, a front or a denial: each is a stance the search can
  // reach, judged by the value.
  // The improvement, in two parts, repeated until neither changes anything:
  //   1. the movements the value itself asks for: the defence's best answer on this board (possRead: every defender's
  //      every movement, read by difference) is a stance it could have set up in, so its first movement is taken for
  //      nothing and the board read again, until the board needs no answer;
  //   2. each defender in turn, his square and the squares next to it with each of the eight arrow pairs, and two
  //      defenders swapping squares (D-295), each read in full on the board as it would then be (walls, lanes and
  //      steals included, which part 1's contests can't see).
  const EMPTY_LIST = new Float64Array(0);
  function stanceRead(s) {
    const key = MAP_MEMO !== null ? 'SR|' + stateKey(s) : null;
    if (key !== null) { const hit = SMALL_MEMO.get(key); if (hit !== undefined) return hit; }
    const pp = possParts(s);
    const vec = pp.routes ? Float64Array.from(pp.routes).sort().reverse() : new Float64Array(6).fill(-Infinity);
    // the list: every look this phase at its chance, best first (the 64 best are kept: the tie-break below reads no further)
    let list = EMPTY_LIST;
    if (pp.L && pp.worth) {
      const all = [];
      for (let j = 0; j < pp.L.length; j++) { const w = pp.worth[j]; if (w > 0) all.push(w * pp.L[j].r); }
      all.sort((x, y) => y - x);
      list = Float64Array.from(all.slice(0, 64));
    }
    const out = { U: pp.V, n: pp.moves.length, m: pp.routes ? topCount(pp.routes, pp.U) : 0, vec, list, moves: pp.moves };
    STANCE_STATS.reads++;
    if (key !== null) SMALL_MEMO.set(key, out);
    return out;
  }
  const STANCE_STATS = { reads: 0, rounds: 0, probed: 0 };
  function stanceLess(a, b) {                          // is a better for the defence than b?
    if (a.U < b.U - 1e-9) return true;
    if (a.U > b.U + 1e-9) return false;
    // Level on the number: the list breaks the tie (the design: "the list can stay as a display and as a tie-break").
    // Every attacker's best look this phase, best first: the shape that leaves the smaller second look, then the
    // smaller third, and so on. Without it the number is mostly its one best look, and four defenders are free to
    // stand anywhere that doesn't change it.
    for (let i = 0; i < a.vec.length; i++) {
      const x = a.vec[i], y = b.vec[i];
      if (x === y) continue;                            // (both -Infinity too)
      if (x < y - 1e-9) return true;
      if (x > y + 1e-9) return false;
    }
    // ... then every look, best first, each at its chance (the design's sum takes the looks in that order; this is that
    // order with no look ever outweighed by the ones below it)
    const la = a.list, lb = b.list, nl = Math.max(la.length, lb.length);
    for (let i = 0; i < nl; i++) {
      const x = i < la.length ? la[i] : 0, y = i < lb.length ? lb[i] : 0;
      if (x < y - 1e-9) return true;
      if (x > y + 1e-9) return false;
    }
    return a.n < b.n;                                   // level all the way down: the stance that needs fewer of the phase's actions to hold it there
  }
  const lineSquares = (a, b) => {                      // the squares from a toward b, nearest a first (a itself left out)
    const out = [], dx = SX[b] - SX[a], dy = SY[b] - SY[a], n = Math.max(Math.abs(dx), Math.abs(dy));
    for (let i = 1; i <= n; i++) { const q = C(Math.round(SX[a] + dx * i / n), Math.round(SY[a] + dy * i / n)); if (ONB[q] && !out.includes(q)) out.push(q); }
    return out;
  };
  // How far part 2 looks around each defender (squares, as the game counts them). Kept, and on trial (D-299): the exam
  // widens it and compares the stances.
  let STANCE_STEP = 1;
  let STANCE_NEAR = 3;                                 // how far from his man a defender's square is looked at (and on his line, any distance)
  let STANCE_TOP = 5;                                  // how many of those squares are read in full each time, besides his own (kept, on trial)
  function stanceProbe(s, d, cands) {
    const lastPhase = s.clock <= 2;
    const m = lastPhase ? covBuild(W_(s, { turn_n: 0, side: 'O', approach: -1, prev_wait: '', final: false, turn_lead: -1, turn_x: [], turn_moved: 0, react_moved: 0 }), true, null, true)
      : covBuild(covOffFresh(s), true, null);
    return possRead(m, s, lastPhase, false, { d, cands }).est;
  }
  function stanceBase(s, man) {                        // the goal-side starting shape -> the board with the five on their base positions
    const put = (st, d, q, a) => W_(st, { x: setAt(st.x, d, q), arrows: setAt(st.arrows, d, a) });
    const lifted = W_(s, { x: [OFFSQ, OFFSQ, OFFSQ, OFFSQ, OFFSQ], arrows: [0, 0, 0, 0, 0] });
    const wm = weightMap(lifted);
    // each defender's line: from his man to the weight he would help (the heaviest lump his man is not himself the
    // top of; the rim if there is none)
    const lineOf = d => {
      const a = man[d], from = s.o[a];
      let tg = RIM;
      if (wm) for (const l of wm.lumps) { if (!(l.top.a === a && cheb(l.top.c, from) <= 1)) { tg = C(Math.round(l.x), Math.round(l.y)); break; } }
      if (tg === from) tg = RIM;
      return lineSquares(from, tg).filter(q => !s.o.includes(q));
    };
    const lines = [0, 1, 2, 3, 4].map(lineOf), taken = new Set(s.o);
    let st = lifted;
    for (let d = 0; d < 5; d++) {
      let q = lines[d].find(z => !taken.has(z));
      if (q === undefined) for (let z = 0; z < NSQ && q === undefined; z++) if (ONB[z] && !taken.has(z) && cheb(z, s.o[man[d]]) <= 2) q = z;
      taken.add(q);
      st = put(st, d, q, nearestDir(q, s.o[man[d]]));
    }
    // the depth the link rule gives: each in turn takes the square on his line that leaves the offence the least
    // (close to a strong threat, deep toward the weight when his man's threat is small), the others where they are
    for (let pass = 0; pass < 2; pass++) {
      for (const d of [0, 1, 2, 3, 4].sort((u, v) => st.x[u] - st.x[v])) {
        let best = { q: st.x[d], a: st.arrows[d], v: stanceRead(st) };
        for (const q of lines[d]) {
          if (q !== st.x[d] && (st.x.includes(q) || st.o.includes(q))) continue;
          const a = nearestDir(q, s.o[man[d]]), v = stanceRead(put(st, d, q, a));
          if (stanceLess(v, best.v)) best = { q, a, v };
        }
        st = put(st, d, best.q, best.a);
      }
    }
    return { s: st, wm, lines };
  }
  function stanceSearch(s0, opts) {
    opts = opts || {};
    let s = W_(covOffFresh(s0), { side: 'O', stage: 'play', pending: null, tok_x: 6, moved_x: 0, qs_x: 0, lock_x: 0, rush_x: 0, beaten: [] });
    const put = (st, d, q, a) => W_(st, { x: setAt(st.x, d, q), arrows: setAt(st.arrows, d, a) });
    const man = opts.man ? opts.man.slice() : [0, 1, 2, 3, 4];     // who each defender starts on (the search may swap them)
    const steps = [];
    let start = 'given';
    const sb = stanceBase(s, man), lines = sb.lines;      // (each defender's line from his man to the weight he would help)
    if (!opts.from) { start = 'base'; s = sb.s; }
    else s = W_(s, { x: opts.from.x.slice(), arrows: opts.from.arrows.slice() });
    const base = { x: Array.from(s.x), arrows: Array.from(s.arrows) };
    let cur = stanceRead(s), rounds = 0;
    for (;;) {
      rounds++;
      let changed = false;
      // 1. the movements the value asks for
      for (let guard = 0; cur.moves.length; guard++) {
        if (guard > 200) throw new Error('the stance search did not settle (part 1)');
        const [d, q, a] = cur.moves[0];
        const t = put(s, d, q, a), v = stanceRead(t);
        if (!stanceLess(v, cur)) break;
        steps.push({ d, from: sqName(s.x[d]), to: sqName(q), arrow: a, value: +v.U.toFixed(4), by: 'the answer' });
        s = t; cur = v; changed = true;
      }
      // 2. one defender at a time, moved and turned (the design's step 3). Every free square within STANCE_NEAR of his
      // man, on his line to the weight or next to where he stands is looked at first by difference (stanceProbe); his
      // own square and the STANCE_TOP best of the others are then read in full with every pair of arrows, on the board
      // as it would be (walls, lanes and steals included). A change is kept when it lowers the number. (In the order of
      // where they stand, never the order the defenders are listed in.)
      for (const d of [0, 1, 2, 3, 4].sort((u, v) => s.x[u] - s.x[v])) {
        let best = null;
        const here = s.x[d], mq = s.o[man[d]], line = new Set(lines[d]);
        const sqs = [];
        for (let q = 0; q < NSQ; q++) {
          if (!ONB[q] || q === here || s.x.includes(q) || s.o.includes(q)) continue;
          if (cheb(q, mq) <= STANCE_NEAR || cheb(q, here) <= STANCE_STEP || line.has(q)) sqs.push(q);
        }
        const cands = []; for (const q of sqs) for (let a = 0; a < 8; a++) cands.push([q, a]);
        const est = cands.length ? stanceProbe(s, d, cands) : [];
        const rank = sqs.map((q, i) => { let lo = Infinity; for (let a = 0; a < 8; a++) if (est[i * 8 + a] < lo) lo = est[i * 8 + a]; return [lo, q]; }).sort((x, y) => (x[0] - y[0]) || (x[1] - y[1]));
        const full = [here].concat(rank.slice(0, STANCE_TOP).map(z => z[1]));
        STANCE_STATS.probed += cands.length;
        for (const q of full) {
          for (let a = 0; a < 8; a++) {
            if (q === here && a === s.arrows[d]) continue;
            const v = stanceRead(put(s, d, q, a));
            if (stanceLess(v, best ? best.v : cur)) best = { q, a, v };
          }
        }
        if (best) { steps.push({ d, from: sqName(here), to: sqName(best.q), arrow: best.a, value: +best.v.U.toFixed(4), by: 'his own stance' }); s = put(s, d, best.q, best.a); cur = best.v; changed = true; }
      }
      // two together (D-295): a pair swapping squares, each then facing the man nearest him
      if (!changed) {
        const near = q => { let b = 0; for (let a = 1; a < 5; a++) if (cheb(q, s.o[a]) < cheb(q, s.o[b])) b = a; return b; };
        let bv = null, bt = null, bp = null;
        for (let d = 0; d < 5; d++) for (let e = d + 1; e < 5; e++) {
          const t = W_(s, { x: setAt(setAt(s.x, d, s.x[e]), e, s.x[d]), arrows: setAt(setAt(s.arrows, d, nearestDir(s.x[e], s.o[near(s.x[e])])), e, nearestDir(s.x[d], s.o[near(s.x[d])])) });
          const v = stanceRead(t);
          if (stanceLess(v, bv || cur)) { bv = v; bt = t; bp = [d, e]; }
        }
        if (bv) { steps.push({ swap: bp, value: +bv.U.toFixed(4), by: 'two together' }); s = bt; cur = bv; changed = true; const mm = man[bp[0]]; man[bp[0]] = man[bp[1]]; man[bp[1]] = mm; }
      }
      if (!changed) break;
      if (rounds > 200) throw new Error('the stance search did not settle');
    }
    STANCE_STATS.rounds += rounds;
    return { x: Array.from(s.x), arrows: Array.from(s.arrows), value: cur.U, answer: cur.n, top: cur.m, vec: Array.from(cur.vec), base, start, rounds, steps, man };
  }
  // ---- Step 31, stage 4 (Shaun, 25 Nov 2026): the offence's setup, in the design's order ---------------------------------------
  //   1. Scout: each attacker's segments by what a defender must save there (layer 1 of the weight map, from the cards:
  //      weightBase): the places that demand a defender.
  //   2. The ball handler's start: each attacker tried with the ball, on the plain wood behind the top and behind each
  //      wing (where the ball begins fixes access and room for everyone else).
  //   3. Possible positions: every other attacker on the square of his heaviest segment not already taken by a
  //      teammate (segments narrow the search and explain the placement); then each in turn tries his next segments, and
  //      a change is kept when it raises the number. Two in one segment is never forbidden: it is tried like any other
  //      square, and the value counts what it costs (one defender then holds both).
  //   4. to 6. The plan's conditions and the adjustment are that same loop read against the defence's answer: a
  //      placement is worth the possession's value against the defence's goal-side shape and the movements the value
  //      asks of it (stanceQuick); the best few are then read against its full answer (stanceSearch).
  // Every placement's reading is independent of the others: they are listed first, read in the list's order and compared
  // in that order, so they can be handed out side by side and combined the same way on any device.
  let OFF_FINAL = 2;                                   // how many of the best placements are read against the defence's full answer (kept, on trial)
  let OFF_SEGS = 3;                                    // how many of his heaviest segments each attacker tries (kept, on trial)
  function stanceQuick(s) {                            // the goal-side shape, then the movements the value asks for (stanceSearch's part 1)
    const put = (st, d, q, a) => W_(st, { x: setAt(st.x, d, q), arrows: setAt(st.arrows, d, a) });
    let st = stanceBase(W_(covOffFresh(s), { side: 'O', stage: 'play', pending: null, tok_x: 6, moved_x: 0, qs_x: 0, lock_x: 0, rush_x: 0, beaten: [] }), [0, 1, 2, 3, 4]).s;
    let cur = stanceRead(st);
    for (let guard = 0; cur.moves.length && guard < 200; guard++) {
      const [d, q, a] = cur.moves[0], t = put(st, d, q, a), v = stanceRead(t);
      if (!stanceLess(v, cur)) break;
      st = t; cur = v;
    }
    return { s: st, v: cur };
  }
  function offenceSetup(s0, opts) {
    opts = opts || {};
    const ctx = s0.ctx, seg = segInit();
    // 1. the scout: "each attacker's zones where his shot is average or better: these are the places that demand a
    // defender". By the card's own marks (average or high), each segment at his best such shot's worth there, the
    // highest first -> [{g, c, weight (that worth)}]. A card with no such shot anywhere is read on every shot it has.
    const scoutOf = (a, all) => {
      const card = ctx.off[a], best = new Map();
      for (let c = 0; c < NSQ; c++) {
        if (!ONB[c] || !seg.of[c]) continue;
        const z = szone(ctx, c);
        if (!SHOOT(z) || (ctx.noRim && c === RIM)) continue;
        let v = -Infinity;
        for (const ty of ZONE_SHOTS[z]) { const bd = card.b['shot_' + ty]; if (all || bd === 'A' || bd === 'H') { const w = ctx.worth[z] * cardShot(ctx, card, ty, c); if (w > v) v = w; } }
        if (!(v > 0)) continue;
        for (const g of seg.of[c]) { const cur = best.get(g); if (!cur || v > cur.weight + 1e-9 || (Math.abs(v - cur.weight) <= 1e-9 && cheb(c, RIM) < cheb(cur.c, RIM))) best.set(g, { g, c, weight: v, open: v }); }
      }
      return [...best.values()].sort((u, v) => v.weight - u.weight || u.c - v.c);
    };
    const scout = [0, 1, 2, 3, 4].map(a => { const rows = scoutOf(a, false); return rows.length ? rows : scoutOf(a, true); });
    // 2. where the ball may start: the first plain-wood square behind the three-point squares in the middle column and
    // in the column of each wing's middle
    const startCols = [RIMX, 2, W - 3], starts = [];
    for (const x of startCols) for (let y = 1; y <= H; y++) { const q = C(x, y); if (ONB[q] && ZN[q] === 0 && y > 1 && !DEEP[q]) { let behind = false; for (let yy = 1; yy < y; yy++) if (ZN[C(x, yy)] === 4) behind = true; if (behind) { starts.push(q); break; } } }
    const mk = (o, ball) => W_(s0, { o, ball, x: [OFFSQ, OFFSQ, OFFSQ, OFFSQ, OFFSQ], arrows: [0, 0, 0, 0, 0], stage: 'play', side: 'O', pending: null });
    const worth = new Map();
    const read = (o, ball) => {                         // a placement's worth against the defence's quick answer
      const key = o.join(',') + '|' + ball;
      let v = worth.get(key);
      if (v === undefined) { const q = stanceQuick(mk(o, ball)); v = { U: q.v.U, vec: q.v.vec, list: q.v.list, x: Array.from(q.s.x), arrows: Array.from(q.s.arrows) }; worth.set(key, v); }
      return v;
    };
    // 3. the others on their heaviest free segments
    const place = (ball, bq) => {
      const o = [-1, -1, -1, -1, -1], usedSeg = new Set(), usedSq = new Set([bq]);
      o[ball] = bq;
      for (const g of (seg.of[bq] || [])) usedSeg.add(g);
      // (the attacker with the fewest places that demand a defender chooses first, so a man with one good spot gets it;
      // level, the one whose best is worth more, then the lower number)
      const order = [0, 1, 2, 3, 4].filter(a => a !== ball).sort((u, v) => (scout[u].length - scout[v].length) || ((scout[v][0] ? scout[v][0].weight : 0) - (scout[u][0] ? scout[u][0].weight : 0)) || u - v);
      for (const a of order) {
        let pick = scout[a].find(r => !usedSeg.has(r.g) && !usedSq.has(r.c)) || scout[a].find(r => !usedSq.has(r.c));
        let q = pick ? pick.c : -1;
        if (q < 0 && scout[a].length) {                  // his spot is taken: the free square of his best segment nearest it (two then share the segment: the value counts it)
          const g = scout[a][0].g; let bd = Infinity;
          for (let z = 0; z < NSQ; z++) if (ONB[z] && !usedSq.has(z) && seg.of[z] && seg.of[z].includes(g) && cheb(z, scout[a][0].c) < bd) { bd = cheb(z, scout[a][0].c); q = z; }
        }
        if (q < 0) for (let z = 0; z < NSQ && q < 0; z++) if (ONB[z] && !usedSq.has(z)) q = z;
        o[a] = q; usedSq.add(q); if (pick) usedSeg.add(pick.g);
      }
      return o;
    };
    const cands = [];
    // an inbound: the inbounder stands where the ball is put in, with the ball; the other four are placed round him by
    // the same steps (the five situations: where the ball starts fixes access and room for everyone else)
    const inb = (s0.inbound && ctx.inbounder != null && ctx.inbounder >= 0) ? ctx.inbounder : -1;
    if (opts.fixed) cands.push({ ball: opts.fixed.ball, o: opts.fixed.o.slice() });
    else if (inb >= 0) cands.push({ ball: inb, o: place(inb, s0.o[inb]) });
    else for (let ball = 0; ball < 5; ball++) for (const bq of starts) cands.push({ ball, o: place(ball, bq) });
    for (const c of cands) c.v = read(c.o, c.ball);
    // more for the offence: the number; level, the list (each attacker's best look this phase, best first; then every
    // look at its chance, best first): the placement that leaves it more good looks, not one
    const more = (a, b) => {
      if (a.U > b.U + 1e-9) return true;
      if (a.U < b.U - 1e-9) return false;
      for (let i = 0; i < a.vec.length; i++) { const x = a.vec[i], y = b.vec[i]; if (x === y) continue; if (x > y + 1e-9) return true; if (x < y - 1e-9) return false; }
      const n = Math.max(a.list.length, b.list.length);
      for (let i = 0; i < n; i++) { const x = i < a.list.length ? a.list[i] : 0, y = i < b.list.length ? b.list[i] : 0; if (x > y + 1e-9) return true; if (x < y - 1e-9) return false; }
      return false;
    };
    const better = (u, v) => more(u.v, v.v);
    let rank = cands.map((c, i) => ({ c, i })).sort((u, v) => (better(u.c, v.c) ? -1 : better(v.c, u.c) ? 1 : u.i - v.i)).map(z => z.c);
    // each attacker in turn tries the squares of his next segments (the best placement first); kept when it raises the number
    const improve = c => {
      let cur = { ball: c.ball, o: c.o.slice(), v: c.v }, steps = 0;
      for (let changed = true; changed;) {
        changed = false;
        for (let a = 0; a < 5; a++) {
          if (a === cur.ball) continue;
          let best = null;
          for (const r of scout[a].slice(0, OFF_SEGS)) {
            if (cur.o.includes(r.c)) continue;
            const o = cur.o.slice(); o[a] = r.c;
            const v = read(o, cur.ball);
            if (more(v, best ? best.v : cur.v)) best = { ball: cur.ball, o, v };
          }
          if (best) { cur = best; changed = true; steps++; }
        }
      }
      cur.steps = steps;
      return cur;
    };
    const tops = rank.slice(0, OFF_FINAL).map(improve);
    // the best few against the defence's full answer
    for (const c of tops) { const st = stanceSearch(mk(c.o, c.ball), null); c.full = { U: st.value, x: st.x, arrows: st.arrows }; }
    tops.sort((u, v) => (v.full.U - u.full.U) || 0);
    const pick = tops[0];
    return { o: pick.o, ball: pick.ball, value: pick.full.U, quick: pick.v.U, defence: pick.full, ranked: tops.map(c => ({ o: c.o.map(sqName), ball: c.ball, quick: +c.v.U.toFixed(2), full: +c.full.U.toFixed(2) })),
      candidates: cands.length, reads: worth.size, scout: scout.map(rows => rows.slice(0, OFF_SEGS).map(r => ({ seg: seg.names[r.g], c: sqName(r.c), weight: +r.weight.toFixed(2), open: +r.open.toFixed(2) }))) };
  }
  const possValue = s => possParts(s).V;
  // Step 31 (the three seconds, counted from entry): an attacker standing in the key without the ball must spend an
  // action to leave before the second phase end finds him there. `now`: those already counted once (they must leave
  // this phase); `next`: every attacker in the key who is not about to shoot (they must leave by the end of the next).
  function threeSecondsLeave(s) {
    let now = 0, next = 0, mask = 0;
    if (s.ctx.three) for (let i = 0; i < 5; i++) {
      if (i === s.ball || !INKEY[s.o[i]]) continue;
      next++; mask |= 1 << i;
      if ((s.key_o >> i) & 1) now++;
    }
    return { now, next, mask };
  }
  // step 22 (D-212): the map's own threats as the offence's first actions: for each of the best looks the defence's
  // answer leaves, and each overload's looks, the action that starts it (the ball handler's movement to where he needs
  // to be, the pass to a receiver standing where he catches, or the receiver's movement to it). [{a, q0}]
  function lgThreats(g) {
    if (!g || !g.best || !g.m) return [];
    const out = [], opt = (a, c) => g.m.options.find(o => o.a === a && o.c === c && !o.rushed) || g.m.options.find(o => o.a === a && o.c === c);
    for (const x of lgHead(g.best).slice(0, 3)) out.push({ a: x.src.a, q0: x.src.q0 });
    for (const v of g.best.sc.ov) for (const z of v.threats) { const o = opt(z.a, z.c); if (o) out.push({ a: o.a, q0: o.q0 }); }
    return out;
  }
  const COV_MOVES = new Set(['move', 'qs', 'sprint']);
  // the defence's answers: one movement action at a time while it has tokens, each the action that leaves the offence
  // the least (the best few by a quick look are then built in full, and the best of those is taken)
  // is the list of worths a (largest first) smaller than b, comparing the largest first, then the next, and so on?
  function covLess(a, b) {
    for (let k = 0; k < Math.max(a.length, b.length); k++) {
      const x = k < a.length ? a[k] : -Infinity, y = k < b.length ? b[k] : -Infinity;
      if (x < y - 1e-9) return true;
      if (x > y + 1e-9) return false;
    }
    return false;
  }
  function covAnswers(m0, limit) {
    let m = m0;
    const answers = [], N = 14;
    for (let step = 0; step < (limit == null ? 6 : limit); step++) {
      const top = m.sorted[0];
      if (!top || top.e <= 0 || m.s.tok_x <= 0) break;
      const sx = W_(m.s, { side: 'X', turn_n: 0, stage: 'play', prev_wait: '' });
      const seen = new Set(), quick = [];
      const head = m.sorted.slice(0, N), cur = head.map(o => o.e);
      const spare = W_(sx, { tok_x: sx.tok_x + 1 });   // (the defence's last token ends the phase in play; here the answer is read inside this phase)
      for (const act of defenceActions(sx, COV_MOVES)) {
        let nx = apply(spare, act);
        if (isChance(nx) || nx.stage !== 'play' || nx.phase !== sx.phase) continue;
        nx = W_(nx, { tok_x: sx.tok_x - 1 });
        const d = act.piece, p = nx.x[d], arrow = nx.arrows[d], key = (d * 4096 + p) * 8 + arrow;
        if (seen.has(key)) continue;
        seen.add(key);
        const cm = cm2Cached(p, arrow, sx.ctx.dfn[d].qs, stanceMode(m.sN, d));
        // a defence can't cover two at once: an action counts if it makes the offence's best options smaller, the
        // largest first, then the next (so with two equal threats, taking one away is still an answer)
        let touched = false;
        const after = [];
        for (const o of head) { const e = covWith(m, o, d, p, arrow, cm); if (e < o.e - 1e-9) touched = true; after.push(e); }
        if (!touched) continue;
        after.sort((x, y) => y - x);
        if (covLess(after, cur)) quick.push([after, quick.length, act, nx]);
      }
      if (!quick.length) break;
      quick.sort((x, y) => (covLess(x[0], y[0]) ? -1 : covLess(y[0], x[0]) ? 1 : x[1] - y[1]));
      let best = null;
      for (const q of quick.slice(0, 5)) {
        const nm = covBuild(W_(q[3], { side: m.s.side, turn_n: m.s.turn_n, prev_wait: m.s.prev_wait }));
        const es = nm.sorted.slice(0, N).map(o => o.e);
        if (best === null || covLess(es, best[0])) best = [es, q[2], nm];
      }
      if (best === null || !covLess(best[0], cur)) break;
      answers.push({ x: best[1].piece, kind: best[1].kind, to: best[2].s.x[best[1].piece], arrow: best[2].s.arrows[best[1].piece], leaves: best[0].length ? best[0][0] : 0 });
      m = best[2];
    }
    return { m, answers };
  }
  const COV_SHOT = { layup: 'a layup', dunk: 'a dunk', post: 'a post shot', mid: 'a mid-range shot', floater: 'a floater', long: 'a long two', three: 'a three' };
  function covOption(o) {
    return { o: o.a, sq: sqName(o.c), shot: o.lk.types[o.t], value: o.v, reach: +o.r.toFixed(3), weakness: +o.w.toFixed(2), worth: +o.e.toFixed(2),
      cover: o.cover, next: o.next, rushed: !!o.rushed };
  }
  // ---- stop two (the addendum on the defence's strength, D-201) -------------------------------------------------------
  // What playing on is worth from the next phase, as the game already measures it: the phase table's average for that
  // phase. In the last phase there is no next one: the last phase's own average stands in, so "broken" still means a
  // shot better than a possession that got this far usually ends with.
  function carryOn(s) {
    const tab = D.vcoarse[s.ctx.table] || D.vcoarse['senior/pro'] || {};
    const phase = Math.min(6, Math.max(1, Math.floor((12 - s.clock) / 2) + 1));
    const v = tab['_phase' + Math.min(6, phase + 1)];
    return v === undefined ? 0 : v;
  }
  // Broken: the ball handler has a shot now, the defence's reaction counted, worth more than playing on.
  function covBreak(s, r) {
    const so = s.side === 'O' ? s : null;
    let shot = null;
    if (so !== null && s.stage === 'play' && !s.pending) {
      r = r || new Read(s);
      for (const lk of r.looks[s.ball] || []) if (lk.route === 'shoot') {
        let bt = 0;
        for (let k = 1; k < lk.types.length; k++) if (lk.open[k] > lk.open[bt]) bt = k;
        shot = { o: s.ball, sq: sqName(lk.c), worth: +lk.base.toFixed(2), kind: lk.types[bt], open: lk.base >= lk.open[bt] - 1e-9 };
        break;
      }
    }
    const carry = carryOn(s);
    return { shot, carry_on: +carry.toFixed(2), broken: shot !== null && shot.worth > carry + 1e-9 };
  }
  // Step 31, stage 5 ("What the player sees"): the number itself, and the weight map as the Coverage view shows it: the
  // centre of gravity, the heaviest weight, and a line in plain words. Never a throw: the view must not stop a game.
  function covValueOf(s0) {
    try {
      const pp = possParts(s0), sh = (s0.pending || s0.stage !== 'play') ? null : new Read(s0).mapShotOrNone();
      const play = pp.V, v = s0.pending ? play : Math.max(sh === null ? SHOT_CLOCK_OUT : sh, play);
      return { value: +(bankedOf(s0) + v).toFixed(1), shot_now: sh === null ? null : +sh.toFixed(1), play_on: +play.toFixed(1),
        words: sh !== null && sh > play + 1e-9 ? `The possession is worth ${Math.round(bankedOf(s0) + v)} to the offence: the shot that can go up now (${Math.round(sh)}) is worth more than playing on (${Math.round(play)}).`
          : `The possession is worth ${Math.round(bankedOf(s0) + v)} to the offence by playing on` + (sh !== null ? ` (the shot that can go up now: ${Math.round(sh)}).` : '.') };
    } catch (e) { return null; }
  }
  function covWeightOf(s0) {
    try {
      const w = weightJSON(s0);
      if (!w) return null;
      const top = w.lumps[0], inKey = c => { const q = parseSq(c); return INKEY[q] === 1; };
      const where = sq => (inKey(sq) ? 'in the key' : SY[parseSq(sq)] >= 8 ? 'out by the three-point line' : 'between the key and the three-point line');
      const words = top ? `The defence's weight (where a defender's presence saves the most right now) balances on ${w.centre.sq}, ${where(w.centre.sq)}. The heaviest of it is O${top.top.a + 1}'s look on ${top.top.c}`
        + (w.lumps.length > 1 && w.lumps[1].weight > 0.5 * top.weight ? `, with a second lump at O${w.lumps[1].top.a + 1}'s look on ${w.lumps[1].top.c}: the balance point is only a summary.` : '.') : 'No weight right now: the offence has no look a defender could save.';
      return { centre: w.centre, base_centre: w.base_centre, lumps: w.lumps.slice(0, 4), entries: w.entries, words };
    } catch (e) { return null; }
  }
  function coverage(s0, opts) {
    opts = opts || {};
    if (opts.trial) {                                    // step 31 (D-299): a cap on trial: widened for this one reading, then put back
      const keep = [STANCE_STEP, OFF_SEGS, OFF_FINAL, STANCE_NEAR, STANCE_TOP], t = opts.trial;
      if (t.stance_step != null) STANCE_STEP = t.stance_step;
      if (t.stance_near != null) STANCE_NEAR = t.stance_near;
      if (t.stance_top != null) STANCE_TOP = t.stance_top;
      if (t.off_segs != null) OFF_SEGS = t.off_segs;
      if (t.off_final != null) OFF_FINAL = t.off_final;
      try { return coverage(s0, Object.assign({}, opts, { trial: null })); } finally { STANCE_STEP = keep[0]; OFF_SEGS = keep[1]; OFF_FINAL = keep[2]; STANCE_NEAR = keep[3]; STANCE_TOP = keep[4]; }
    }
    if (opts.only === 'parts') return { parts: mapParts(s0) };
    if (opts.only === 'value') {                          // step 31 (D-284): the possession's value, with its parts
      const r = new Read(s0), pp = possParts(s0), sh = (s0.pending || s0.stage !== 'play') ? null : r.mapShotOrNone();
      const banked = bankedOf(s0), play = pp.V, V = s0.pending ? play : Math.max(sh === null ? SHOT_CLOCK_OUT : sh, play);
      const looks = [];
      if (pp.L) {
        const idx = pp.L.map((o, i) => i).filter(i => pp.worth[i] > -Infinity).sort((x, y) => pp.L[y].r * pp.worth[y] - pp.L[x].r * pp.worth[x] || pp.L[x].a - pp.L[y].a || pp.L[x].c - pp.L[y].c);
        const seen = new Set();
        for (const i of idx) { const o = pp.L[i], key = o.a * 2 + (o.dr ? 1 : 0); if (seen.has(key)) continue; seen.add(key);
          looks.push({ a: o.a, c: sqName(o.c), q0: sqName(o.q0), p: +o.r.toFixed(4), open: +o.v.toFixed(2), before: +(o.w + o.adj).toFixed(2), worth: +pp.worth[i].toFixed(2), dribble: !!o.dr, actions: o.n0, rushed: !!o.rushed, fake: twoStep(pp, i) }); }
      }
      // step 31, fix 3: the two-step routes the number reads (a look whose worth the fake mix raises), best first
      const two = [];
      if (pp.L && pp.mixInfo) for (let i = 0; i < pp.L.length; i++) { if (!(pp.worth[i] > -Infinity)) continue; const r2 = twoStep(pp, i); if (r2) two.push(Object.assign({ shooter: pp.L[i].a, at: sqName(pp.L[i].c), p: +pp.L[i].r.toFixed(4) }, r2)); }
      two.sort((x, y) => y.p * y.worth - x.p * x.worth || x.shooter - y.shooter || (x.at < y.at ? -1 : x.at > y.at ? 1 : 0));
      // (opts.look {a, c}: every look of that attacker at that square, with its fake line: a proof reads one look)
      const at = (opts.look && pp.L) ? pp.L.map((o, i) => i).filter(i => pp.L[i].a === opts.look.a && sqName(pp.L[i].c) === opts.look.c).map(i => ({ q0: sqName(pp.L[i].q0), rushed: !!pp.L[i].rushed, p: +pp.L[i].r.toFixed(4), worth: pp.worth[i] > -Infinity ? +pp.worth[i].toFixed(4) : null, fake: twoStep(pp, i) })) : undefined;
      return { value: +(banked + V).toFixed(4), banked, shot_now: sh === null ? null : +sh.toFixed(2), play_on: +play.toFixed(4), before_answer: pp.U0 === undefined ? null : +pp.U0.toFixed(4), phases_after: pp.k, two_step: two.slice(0, 12), look_at: at, drive_race: (pp.races || []).map(raceJSON), fake_race: (pp.fakeRaces || []).map(x => Object.assign(raceJSON(x), { closes_to: sqName(x.closes_to) })), bars: pp.bars.map(v => +v.toFixed(2)),
        answer: (pp.moves || []).map(([d, q, a]) => [d, sqName(q), a]), pick: pp.pick ? { a: pp.pick.a, c: sqName(pp.pick.c), q0: sqName(pp.pick.q0), p: +pp.pick.r.toFixed(4), worth: +pp.pickWorth.toFixed(2), dribble: !!pp.pick.dr } : null, looks, catch: pp.catch === undefined ? null : pp.catch };
    }
    if (opts.only === 'offence_setup') {                  // step 31, stage 4: the offence's setup, in the design's order
      const r = offenceSetup(s0, { fixed: opts.fixed ? { ball: opts.fixed.ball, o: opts.fixed.o.map(parseSq) } : null });
      return { squares: r.o.map(sqName), ball: r.ball, value: +r.value.toFixed(4), quick: +r.quick.toFixed(4), defence: { x: r.defence.x.map(sqName), arrows: r.defence.arrows }, ranked: r.ranked, candidates: r.candidates, reads: r.reads, scout: r.scout };
    }
    if (opts.only === 'stances') {                        // step 31, stage 3: the defence's five stances for this board
      const st = stanceSearch(s0, { from: opts.from ? { x: opts.from.x.map(parseSq), arrows: opts.from.arrows } : null, man: opts.man || null });
      const fin = W_(covOffFresh(s0), { side: 'O', stage: 'play', pending: null, tok_x: 6, moved_x: 0, qs_x: 0, lock_x: 0, rush_x: 0, beaten: [], x: st.x, arrows: st.arrows });
      const lifted = [0, 1, 2, 3, 4].map(d => +(stanceRead(W_(fin, { x: setAt(fin.x, d, OFFSQ) })).U - st.value).toFixed(4));
      return { x: st.x.map(sqName), arrows: st.arrows, value: +st.value.toFixed(4), answer: st.answer, top: st.top, lifted, routes: st.vec.map(v => (isFinite(v) ? +v.toFixed(2) : null)), base: { x: st.base.x.map(sqName), arrows: st.base.arrows },
        start: st.start, rounds: st.rounds, steps: st.steps, man: st.man, reads: STANCE_STATS.reads };
    }
    if (opts.only === 'stance_value') { const v = stanceRead(W_(covOffFresh(s0), { side: 'O', stage: 'play', pending: null })); return { value: +v.U.toFixed(4), answer: v.n, top: v.m, routes: Array.from(v.vec, x => (isFinite(x) ? +x.toFixed(2) : null)) }; }
    if (opts.only === 'weight') return { weight: weightJSON(s0) };            // step 31, stage 2: the team's weight map and its centre
    if (opts.only === 'bars') return { bars: barsOf(s0) };                       // step 25: the shot bar, phase by phase                  // the search's three numbers (Read.mapShot, Read.mapTwo)
    if (opts.only === 'break') return covBreak(s0.pending ? W_(s0, { ball: s0.pending[1], pending: null, approach: -1 }) : s0);
    if (opts.only === 'setup') {                          // the defence's setup: the settlement of all five (D-219)
      RD.lead = opts.lead === 'gap' ? 'gap' : 'list';
      const z = settleSetup(s0, opts.evals === undefined ? 240 : opts.evals), m = z.g ? z.g.m : null;
      RD.lead = 'gap';
      const g0 = lastingOf(covOffFresh(s0));
      const ro = m ? defenderRoles(z.s, null) : { perm: [0, 1, 2, 3, 4], roles: [], lines: [] };
      return { L: +z.rd.L.toFixed(2), start: g0 ? +g0.L.toFixed(2) : 0, x: Array.from(z.s.x).map(q => sqName(q)), arrows: Array.from(z.s.arrows), moves: z.steps.length,
        evals: z.evals, drivers: drvJSON(z.rd), steps: z.steps, perm: ro.perm, lines: ro.roles.map(r => r.line) };
    }
    if (opts.only === 'roles') return defenderRoles(s0, opts.prev || null, opts.fixed);
    if (opts.only === 'without') {                        // the checks: is the list worse with each defender taken off the court? (nobody is spare)
      const f = covOffFresh(s0), base = readingOf(lastingOf(f));
      return [0, 1, 2, 3, 4].map(d => { const rd = readingOf(lastingOf(W_(f, { x: setAt(f.x, d, OFFSQ) }))); return { x: d, worse: covLess(base.list, rd.list), top: Array.from(rd.list.slice(0, 4), v => +v.toFixed(1)) }; });
    }
    if (opts.only === 'probe') {                          // the checks: the position as given, and defender `piece` on each of `squares` with every arrow, read in full
      RD.lead = opts.lead === 'gap' ? 'gap' : 'list';
      const f = covOffFresh(s0), base = readingOf(lastingOf(f)), rows = [];
      for (const name of opts.squares || []) {
        const q = parseSq(name);
        if (!ONB[q] || (q !== f.x[opts.piece] && (f.o.includes(q) || f.x.includes(q)))) continue;
        for (let a = 0; a < 8; a++) {
          const rd = readingOf(lastingOf(W_(f, { x: setAt(f.x, opts.piece, q), arrows: setAt(f.arrows, opts.piece, a) })));
          rows.push({ sq: name, arrow: a, better: rdLess(rd, base), worse: rdLess(base, rd), why: rdWhy(rd, base), L: +rd.L.toFixed(2), top: Array.from(rd.list.slice(0, 6), v => +v.toFixed(1)) });
        }
      }
      RD.lead = 'gap';
      return { base: drvJSON(base), rows };
    }
    if (opts.only === 'offsweep') return offSweep(s0, opts.piece, opts.keep, opts.squares, opts.quick).map(r => ({ sq: sqName(r.q), drivers: drvJSON(r.k) }));
    if (opts.only === 'lasting' && opts.answer_lead) {           // step 28: the report's check of D-262 (the answer led by the gap, as it was)
      const keep = D.config.eval.answer_lead;
      D.config.eval.answer_lead = opts.answer_lead;
      try { return coverage(s0, Object.assign({}, opts, { answer_lead: undefined })); } finally { D.config.eval.answer_lead = keep; }
    }
    if (opts.only === 'lasting') {
      const g = lastingOf(s0, null, !!opts.fresh);
      if (!g) return null;
      const out = { L: +g.L.toFixed(2), before: +g.before.toFixed(2), overloads: g.ov, moves: g.moves, drivers: drvJSON(readingOf(g)) };
      if (g.catch !== undefined) out.catch = +g.catch.toFixed(4);       // step 28 (D-263): a pass in the air: the chance it lands, by the rules
      if (opts.prev && g.m) {                           // who has whom after it, and how well each defender alone contains his own man (largest first)
        const A = assignOf(g.m, opts.prev, false);
        out.perm = A.perm; out.kept = A.perm.every((a, d) => a === opts.prev[d]);
        out.own = A.vec.map(v => +v.toFixed(2));
      }
      out.top = topOf(s0);
      // step 27 (D-258): the moves of the defence's best answer by this same reading (the list), for the reading ahead
      if (opts.answer) out.answer = (g.best && g.best.moves ? g.best.moves : []).map(([d, q, a]) => [d, sqName(q), a]);
      if (opts.settle) out.settle = new Read(s0).mapSettle().map(([d, q, a]) => [d, sqName(q), a]);
      return out;
    }
    // step 21 (D-206): the map is read with what each side has left this phase; opts.fresh: step 20's like-for-like
    // read (covFresh), for the reports' phase starts. A pass in the air is shown caught; its number is by the catch's chance
    const caught = s0.pending ? W_(s0, { ball: s0.pending[1], pending: null, approach: -1 }) : s0;
    const s = opts.fresh ? covFresh(s0) : covOffFresh(caught);
    const m0 = covBuild(s);
    const best = lasting(m0);
    const sq = list => {                               // every square, for each attacker: his best option there
      const out = [0, 1, 2, 3, 4].map(() => ({}));
      for (const x of list) {
        if (!(x.r > 0)) continue;
        const o = x.src || x, k = sqName(o.c), cur = out[o.a][k];
        if (!cur || x.e > cur.worth) out[o.a][k] = { value: o.v, reach: +x.r.toFixed(3), weakness: +x.w.toFixed(2), worth: +x.e.toFixed(2), influence: +(o.v - x.w).toFixed(2),
          cover: x.cover, next: x.next, shot: o.lk.types[x.t], rushed: !!o.rushed, cost: +(o.adj || 0).toFixed(2) };    // cost (step 26): what holding the ball there costs him (the Steal, the counts)
      }
      return out;
    };
    const squares = sq(m0.sorted), squaresAfter = sq(best.o);
    // who covers what, after the answer: one defender covers many squares, and several attackers at once
    const covers = [0, 1, 2, 3, 4].map(() => ({ squares: 0, attackers: [] }));
    for (let a = 0; a < 5; a++) for (const k of Object.keys(squaresAfter[a])) {
      const d = squaresAfter[a][k].cover;
      if (d >= 0) { covers[d].squares++; if (!covers[d].attackers.includes(a)) covers[d].attackers.push(a); }
    }
    const opt = x => { const o = x.src; return { o: o.a, sq: sqName(o.c), shot: o.lk.types[x.t], value: o.v, reach: +x.r.toFixed(3), weakness: +x.w.toFixed(2), worth: +x.e.toFixed(2), cover: x.cover, next: x.next, rushed: !!o.rushed }; };
    const head = lgHead(best), left = head.length ? head[0] : null;
    const top = m0.sorted.length ? m0.sorted[0] : null;
    const name = o => `O${o + 1}`;
    const NUM = ['', 'one', 'two', 'three', 'four'];
    const overloads = best.sc.ov.map(v => {
      const th = v.threats.map(z => ({ o: z.a, sq: sqName(z.c), shot: m0.options.find(o => o.a === z.a && o.c === z.c).lk.types[z.t], worth: +z.worth.toFixed(2) }));
      const and = xs => xs.length <= 2 ? xs.join(' and ') : xs.slice(0, -1).join(', ') + ' and ' + xs[xs.length - 1];
      let line;
      if (v.ds.length === 1) {
        const two = th.slice(0, 2).map(z => `${name(z.o)}'s ${COV_SHOT[z.shot].replace(/^an? /, '')} on ${z.sq}`).join(' and ');
        line = `X${v.d + 1} is the only cover for ${two}: whichever he takes, the other is open (worth ${Math.round(v.value)}).`;
      } else {
        const k = v.ds.length, rest = th.length - k;
        line = `${and(v.ds.map(d => `X${d + 1}`))} are the only cover for ${and(th.map(z => name(z.o)))}${v.near_key ? ' near the key' : ''}: ` +
          `whichever ${NUM[k]} they take, ${rest === 1 ? (th.length === 3 ? 'the third' : 'the other') : 'another'} is open (worth ${Math.round(v.value)}).`;
      }
      return { x: v.d, xs: v.ds, value: +v.value.toFixed(2), threats: th, line };
    });
    const words = [];
    if (!top) words.push(s0.clock <= 2 ? 'The last phase: only a shot now counts.' : 'Nothing can be reached next phase.');
    else {
      if (best.moves.length) words.push(`The defence's best answer: ${best.moves.map(([d, q]) => q === s.x[d] ? `X${d + 1} turns on ${sqName(q)}` : `X${d + 1} to ${sqName(q)}`).join(', ')}.`);
      else words.push(s.tok_x <= 0 ? 'The defence has no token left this phase to answer with.' : 'No movement by the defence makes it smaller.');
      if (left && left.e > 0) words.push(`That leaves ${COV_SHOT[left.src.lk.types[left.t]]} for ${name(left.src.a)} on ${sqName(left.src.c)}, worth ${Math.round(left.e)}: ${left.cover < 0 ? 'nobody covers it' : `X${left.cover + 1} covers it`}.`);
      for (const v of overloads) words.push(v.line);
    }
    const brk = covBreak(s0.pending ? W_(s0, { ball: s0.pending[1], pending: null, approach: -1 }) : s0);
    if (brk.broken) words.push(`The defence is broken now: O${brk.shot.o + 1} has a shot on ${brk.shot.sq} worth ${brk.shot.worth.toFixed(0)}, more than playing on (${brk.carry_on.toFixed(0)}).`);
    const L = s0.pending && !opts.fresh ? (lastingOf(s0) || { L: best.sc.L }).L : best.sc.L - (opts.fresh ? 0 : TURNOVER_COST * threeSecondsOwed(s0));
    // where the defence stands after its best answer
    const px = Array.from(s.x), pa = Array.from(s.arrows);
    for (const [d, q, a] of best.moves) { px[d] = q; if (a >= 0) pa[d] = a; }
    const after = { x: px.map(q => sqName(q)), arrows: pa, tokens_left: s.tok_x - best.moves.length };
    return { phase: s0.phase, clock: s0.clock, fresh: !!opts.fresh, squares, squares_after: squaresAfter, after, covers, top: m0.sorted.slice(0, 8).map(covOption),
      strength: +L.toFixed(2), lasting: +L.toFixed(2), before: top ? +top.e.toFixed(2) : 0, fragility: overloads.length, overloads,
      shot_now: brk.shot, carry_on: brk.carry_on, broken: brk.broken,
      // step 31, stage 5: the possession's value (the phase score) and the team's weight map, with its centre, for the view
      value: valueLead() ? covValueOf(s0) : null, weight: valueLead() ? covWeightOf(s0) : null,
      best: top ? covOption(top) : null, answers: best.moves.map(([d, q, a]) => ({ x: d, to: sqName(q), arrow: a, turn: q === s.x[d] })),
      left: left ? opt(left) : null, left_worth: left ? +left.e.toFixed(2) : 0, dribble: null,
      now: m0.now ? { o: m0.now.a, sq: sqName(m0.now.c), worth: +m0.now.e.toFixed(2), route: m0.now.route } : null,
      // the chance a pass straight to each teammate where he stands arrives, by the rules (null: the ball handler, or no pass)
      passes: [0, 1, 2, 3, 4].map(a => (a === s.ball || !ONB[s.o[a]] || !isLegal(W_(s, { side: 'O', stage: 'play', turn_n: 0, pending: null }), A('pass', 'O', s.ball, -1, -1, a)) ? null : +passChanceExact(s, a).toFixed(3))),
      worth: +L.toFixed(2), words: words.join(' ') };
  }
  // What each defender is playing for (D-214, D-220, D-221), in plain words, from the reading itself: his assigned
  // man (what that man's best look is worth open, and with only this defender on him), the gap his influence holds
  // down (the square that would be worth most with him gone), and whether he is beaten and chasing. prev: the
  // assignments as they were (a switch is named when they change).
  function defenderRoles(s0, prev, fixed) {
    if (s0.stage !== 'play' || s0.clock <= 2) return { roles: [], perm: prev || null, lines: [], switched: null };
    const at = s0.pending ? W_(s0, { ball: s0.pending[1], pending: null, approach: -1 }) : s0;
    const m = covBuild(covOffFresh(at), true, null), A = assignOf(m, prev || null, !!fixed), perm = A.perm;
    const g = gapInfo(m.r), st = lgRoot(m), gaps = gapVec(st);
    lgList(st);
    const name = o => `O${o + 1}`, roles = [];
    const and = xs => (xs.length <= 2 ? xs.join(' and ') : xs.slice(0, -1).join(', ') + ' and ' + xs[xs.length - 1]);
    for (let d = 0; d < 5; d++) {
      if (!ONB[at.x[d]]) continue;
      const a = perm[d], open = A.open[a], withHim = A.alone[a][d], takes = open - withHim;
      let gap = null, held = 0, way = null;
      const gone = gapVec(st, d, OFFSQ);              // the race with him off the court: the gaps only he is closing
      for (let k = 0; k < gone.length; k++) {
        const sq = g.sq[k], without = gone[k];
        if (!(without > gaps[k] + 0.5)) continue;
        held++;
        if (gap === null || without > gap.without + 1e-9 || (Math.abs(without - gap.without) <= 1e-9 && sq < gap.q)) gap = { q: sq, sq: sqName(sq), without: +without.toFixed(2), now: +gaps[k].toFixed(2) };
      }
      const beaten = at.beaten.some(b => b[1] === d) || isLocked(at, 'X', d);
      const on = takes > 0.5, apart = on && gap !== null && ONB[at.o[a]] && cheb(gap.q, at.o[a]) > 3;
      const kind = beaten && (!prev || prev[d] === a) ? 'chase' : on && gap ? 'both' : on ? 'man' : gap ? 'sag' : 'free';
      // (the teammates who cover his man with him: whoever leaving would let that man have more)
      const all = A.without(a, 0), mates = [];
      if (all < withHim - 0.5) for (let e = 0; e < 5; e++) if (e !== d && ONB[at.x[e]] && A.without(a, 1 << e) > all + 1e-9) mates.push(e);
      const manW = `${name(a)} (his best look is worth ${Math.round(open)} open, ${Math.round(withHim)} with X${d + 1} on it` +
        (mates.length ? `, ${Math.round(all)} with ${and(mates.map(e => `X${e + 1}`))} helping` : '') + ')';
      const gapW = gap ? `the squares around ${gap.sq} (worth ${Math.round(gap.without)} if he weren't in reach)` : '';
      let line;
      if (kind === 'chase') line = `X${d + 1} beaten: chasing ${name(a)}.`;
      else if (kind === 'both') line = `X${d + 1}: on ${manW}, and covering ${gapW}.` + (apart ? ' The two lie apart: he can\'t hold both for long.' : '');
      else if (kind === 'man') line = `X${d + 1}: on ${manW}.`;
      else if (kind === 'sag') line = `X${d + 1}: sagging off ${name(a)} (his best look is worth ${Math.round(open)}, and X${d + 1} takes nothing off it from here) to cover ${gapW}.`;
      else {
        // (step 22c: a body or a wall in an attacker's way is a job too: whose best look is worth more with him off the court)
        const off = lgRoot(covBuild(W_(m.s, { x: setAt(m.s.x, d, OFFSQ) }), true, null)); lgList(off);
        // (of those, the one whose look would be worth most: the largest item he is keeping down)
        for (let b = 0; b < 5; b++) if (off.thr[b] > st.thr[b] + 0.5 && (way === null || off.thr[b] > way.without + 1e-9)) way = { o: b, now: +st.thr[b].toFixed(2), without: +off.thr[b].toFixed(2) };
        line = way && way.o === a ? `X${d + 1}: in ${name(a)}'s way (his best look is worth ${Math.round(way.now)}, ${Math.round(way.without)} without X${d + 1} there).`
          : way ? `X${d + 1}: off ${name(a)} (his best look is worth ${Math.round(open)}), and in ${name(way.o)}'s way (his best look is worth ${Math.round(way.now)}, ${Math.round(way.without)} without X${d + 1} there).`
          : `X${d + 1}: off ${name(a)} (his best look is worth ${Math.round(open)}), and covering no square the others don't.`;
      }
      roles.push({ x: d, man: a, kind, open: +open.toFixed(2), with: +withHim.toFixed(2), gap, held, apart, beaten, way, line, value: +Math.max(takes, gap ? gap.without - gap.now : 0).toFixed(2) });
    }
    let switched = null;
    if (A.takeover) {                                  // step 22c (D-226): "X4 and X5 have O1: X1 picks up O5."
      const t = A.takeover;
      switched = `${and(t.helpers.map(e => `X${e + 1}`))} ${t.helpers.length > 1 ? 'have' : 'has'} ${name(t.man)}: X${t.x + 1} picks up ${name(t.picks)}.`;
    } else if (prev && perm.some((a, d) => a !== prev[d])) {
      const ch = [0, 1, 2, 3, 4].filter(d => perm[d] !== prev[d]).sort((u, v) => A.open[perm[v]] - A.open[perm[u]] || u - v);
      switched = 'Switch: ' + ch.map((d, k) => `X${d + 1} ${k === 0 ? 'takes' : 'picks up'} ${name(perm[d])}`).join('; ') + '.';
    }
    const lines = [];
    if (switched) lines.push(switched);
    for (const r of roles) if (r.kind === 'chase') lines.push(r.line);
    for (const r of roles) if (r.kind === 'sag') lines.push(`X${r.x + 1} sags off ${name(r.man)} to cover the squares around ${r.gap.sq}.`);
    return { roles, perm, lines, switched, takeover: A.takeover };
  }
  function coverageJSON(text) { return withMemo(() => coverageJSONCalc(text)); }
  function coverageJSONCalc(text) {
    const req = JSON.parse(text);
    const key = JSON.stringify(req.ctx);
    let ctx = CTXS.get(key);
    if (!ctx) { if (CTXS.size >= 4) CTXS.clear(); ctx = makeCtx(req.ctx); CTXS.set(key, ctx); }
    return JSON.stringify(coverage(stateFrom(req.state, ctx), req.options || null));
  }

  return { setCalibrated, setTabletopMap, setSettle, setHelp, ceilingOf, setLearned, FEATURE_NAMES, featuresOf, bankedOf, handLeaf, looksLeaf, leafMode, stateJSON, actionJSON, isChance, scoreTotal, init, setLeafMode, setStable, setSearch, stableParts, setReach, setSpeed, setBudget, setAdvantages, setGoals, REACH_STATS, reachMap, searchJSON, goalsJSON, readsJSON, makeCtx, stateFrom, legalActions, apply, Read, search, probe, zobrist, actor, terminalValue, sqName, coverage, coverageJSON, parseSq,
    actionStr, actionJSON, isChance, attackerReach, defenderMap, contestMap, candidateActions, turns, playTurn, Searcher, setOpenList, openOn, openMode, OPEN_STATS, setWholeTurns, setRankInHand, setDiceInHand, setBallLoss, setKeepSettled, setKeepInHand, stealSpot, endedTurn, setSplitTies, splitOn, openWidth, setKeptActions, setNoFloor, setExactShot, setLane, setPassRules, setMap, setMapLead, mapParts, icptPi, laneP, COV_SLOW, passChanceExact, covBuild, covAnswers, covLeanAnswers, setLevelMaps, setLevel, zoneOf, stanceOf, stanceFacts, closelyGuarded, phaseCounts,
    _memoSizes: (a, b, c, d) => { if (a != null) MAP_MEMO_MAX = a; if (b != null) READS_MAX = b; if (c != null) REACH_MAX = c; if (d != null) SMALL_MEMO_MAX = d; return [MAP_MEMO_MAX, READS_MAX, REACH_MAX, SMALL_MEMO_MAX]; },
    makeEvaluate, scoreTotal, vcoarse, laneP, _caches: () => [_GR.cur.size + _GR.old.size, _CM.cur.size + _CM.old.size, _LS.size, _OA.size],
    _pvStats: () => PVS, _stanceProbe: (s, d, cands) => stanceProbe(s, d, cands),
    _pvCheck: on => { if (on !== undefined) { PV_CHECK = !!on; PVC.n = 0; PVC.bad = 0; PVC.ex = []; } return { on: PV_CHECK, checked: PVC.n, different: PVC.bad, examples: PVC.ex }; },
    _stateKey: stateKey, _covBuild: covBuild, _withMemo: withMemo, covOffFresh, possValue, possParts, possRead, weightMap, weightBase, weightJSON, offenceSetup, stanceQuick, stanceSearch, stanceRead, stanceBase, STANCE_STATS, _stanceStep: v => { STANCE_STEP = v; }, mixGame, PVS, _boundLooks: v => { BOUND_LOOKS = v; }, _pvBrute: v => { PV_BRUTE = !!v; } };
})();
if (typeof module !== 'undefined') module.exports = PMEngine;
if (typeof self !== 'undefined') self.PMEngine = PMEngine;
