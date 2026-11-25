"""Step 3m Part B1-B4: the decision engine's two measurements and its position value.

Basketball is meant to emerge from value and search, not from scripted plays: nothing here names a play, a position or
a distance. Every number is in the game's units (shot value = points x (rating - contest); x20 = expected points).

  Reach (B1)     reach(s, side, i): where a player can stand after 0, 1 or 2 of his side's actions (Move, Quick Step,
                 Sprint, within his remaining capacity). Exact (the rules' own movement and blocking: actions.
                 movement_dests, solver.defender_reach) at the root; at the search's leaves a cached geometric reach
                 that ignores blocking by other pieces (it never decides legality: the search only plays legal actions).
                 contest_map(d): for every square c, the fewest defender actions to reach a legal contest of a shot
                 from c, per contest kind (with or without the -3 for standing further from the rim; clean, or a foul
                 roll when the arrow is off the shooter).
  THREAT (B2)    the best delivered shot each attacker can get: max over squares c and delivery routes r (shoot now,
                 drive and shoot, catch here, cut and catch) of P_deliver x the shot value against the best contest
                 that arrives in time (the defence's actions before the release: the reaction to a declared shot, plus a
                 full defence turn when the shot needs a pass or another turn). The arg-max square and route are kept.
  COVERAGE (B3)  each defender's candidate responses (a square and an arrow within his next turn), the cover matrix
                 R[j][resp][i] = THREAT(i) left if j makes that response, and the best cover: one response per
                 defender, at most the defence's actions in its next turn moving, minimising the best uncovered
                 threat. Overloads and dilemmas, and each attacker's gravity, come from the same matrix.
  Value (B4)     V_leaf = max(ShotNow, sum_i w_i x residual_i, Vcoarse[ball zone, defended, phase, tokens]); w is the
                 offence's best-response distribution over the residual threats (all weight on the best, ties split).
"""
import json
import os
from functools import lru_cache

from . import board as B
from . import geometry as G
from . import rules_config as RC
from .scoring import p_success, rolled, p_foul, p_fouls, foul_on_shot_points, shot_zone, card_shot, zone_at
from .actions import lane_meet

HERE = os.path.dirname(os.path.abspath(__file__))
INF = 99
SHOOT = {'K', 'M', 'L', '3'}
NEAR = [d for d in B.DIRS]


# ---- reach (B1) ------------------------------------------------------------------------------------------------------

@lru_cache(maxsize=None)
def _geo_paths(kind, frm, qs, rules):
    """Movement destinations from frm ignoring other pieces: {dest: run direction or None}."""
    if kind == 'move':
        raw = [(None, p) for p in B.move_paths(frm, rules)]
    elif kind == 'qs':
        raw = [(None, p) for p in B.qs_paths(frm, qs, rules)]
    else:
        raw = list(B.sprint_paths(frm, qs, rules))
    out = {}
    for dr, p in raw:
        if all(B.on_board(q) for q in p) and p[-1] not in out:
            out[p[-1]] = dr
    return out


@lru_cache(maxsize=200000)
def geo_reach(frm, arrow, qs, can_move, qs_left, rules):
    """(free, fixed) like solver.defender_reach, from geometry alone: free[sq] = actions (a Move was used: any arrow);
    fixed[sq] = {arrow: actions}. Up to two actions."""
    free, fixed = {}, {frm: {arrow: 0}}

    def add_free(q, n):
        if free.get(q, INF) > n:
            free[q] = n

    def add_fixed(q, a, n):
        cur = fixed.setdefault(q, {})
        if cur.get(a, INF) > n:
            cur[a] = n
    moves = _geo_paths('move', frm, qs, rules) if can_move else {}
    qss = _geo_paths('qs', frm, qs, rules) if qs_left >= 1 and qs > 0 else {}
    sprints = _geo_paths('sprint', frm, qs, rules) if can_move and qs_left >= 1 and qs > 0 else {}
    if can_move:
        add_free(frm, 1)
        for q in moves:
            add_free(q, 1)
            if qs_left >= 1 and qs > 0:
                for q2 in _geo_paths('qs', q, qs, rules):
                    add_free(q2, 2)
    for q in qss:
        add_fixed(q, arrow, 1)
        if can_move:
            for q2 in _geo_paths('move', q, qs, rules):
                add_free(q2, 2)
    for q, dr in sprints.items():
        add_fixed(q, dr, 1)
    return free, fixed


def _caps(s, side, i):
    """(can_move, quick steps left) for a player now, by the rules' limits."""
    rules = s.ctx.rules
    if s.tokens(side) <= 0:
        return False, 0
    can_move = not s.moved(side, i) and not s.locked(side, i)
    if side == 'O' and i == s.ctx.inbounder and s.inbound:
        return False, 0
    qs_left = RC.LIMITS[side]['qs'] - s.count(side, 'qs')
    if rules.qs_once_per_player:
        qs_left = 0 if s.quick_stepped(side, i) else min(qs_left, 1)
    if side == 'O' and i == s.ball and s.picked_up() and RC.app_rule(rules, 'closely_guarded'):
        # D-173: picked up, he only passes or shoots; D-273: but for his one pivot Quick Step
        return False, (min(qs_left, 1) if RC.pivot_open(s, i) else 0)
    return can_move, qs_left


_EXACT = {}


def defender_map(s, d, exact=False):
    """(free, fixed) reach for defender d with action counts (0 = where he stands, with his arrow)."""
    if exact:
        # step 13 (a speed-up that changes no result): kept for the position; the answer depends only on the pieces'
        # squares, his arrow and what he has left, the screens and the rules. Callers only read it.
        key = (s.o, s.x, d, s.arrows[d], min(s.tok_x, 2), s.moved('X', d), s.locked('X', d), s.quick_stepped('X', d),
               s.count('X', 'qs'), s.screens, s.ctx.dfn[d].qs, s.ctx.rules)
        hit = _EXACT.get(key)
        if hit is None:
            from .solver import defender_reach
            free, fixed = defender_reach(s, d, 2)
            hit = ({q: len(seq) for q, seq in free.items()},
                   {q: {a: len(seq) for a, seq in arrs.items()} for q, arrs in fixed.items()})
            if len(_EXACT) >= 20000:
                _EXACT.clear()
            _EXACT[key] = hit
        return hit
    can_move, qs_left = _caps(s, 'X', d)
    if s.tok_x <= 0:
        return {}, {s.x[d]: {s.arrows[d]: 0}}
    return geo_reach(s.x[d], s.arrows[d], s.ctx.dfn[d].qs, can_move, qs_left, s.ctx.rules)


def two_actions(s, i, one):
    """Step 13 B2 (D-115): the squares attacker i reaches with exactly two movement actions (a Move then a Quick Step,
    or a Quick Step then a Move), each by the rules' own movement from where the first leaves him: blocking pieces,
    teammates included, screens and the ball handler's zones all apply. `one`: his squares within one action. Sorted."""
    from .actions import movement_dests, can_move_kind
    if s.tok_o < 2 or not B.on_board(s.o[i]):
        return []
    rules, bit, out = s.ctx.rules, 1 << i, set()
    for first, second in (('move', 'qs'), ('qs', 'move')):
        if not can_move_kind(s, 'O', i, first):
            continue
        for q1 in movement_dests(s, 'O', i, first, rules):
            s2 = s.with_(o=s.o[:i] + (q1,) + s.o[i + 1:], **({'moved_o': s.moved_o | bit} if first == 'move' else
                                                             {'qs_o': s.qs_o | bit}))
            if can_move_kind(s2, 'O', i, second):
                for q2 in movement_dests(s2, 'O', i, second, rules):
                    if q2 not in one:
                        out.add(q2)
    return sorted(out)


def attacker_reach(s, i, exact=False):
    """{square: actions} for attacker i (0 = where he stands), up to two of the offence's actions. Exact: the rules'
    movement (blocking, screens, the ball carrier's zones); else cached geometry."""
    out = {s.o[i]: 0}
    can_move, qs_left = _caps(s, 'O', i)
    if not B.on_board(s.o[i]) or s.tok_o <= 0:
        return out
    card = s.ctx.off[i]
    from .actions import pivot_len
    pick = pivot_len(s, 'O', i, 2) == 1          # D-173, D-273: picked up: his one pivot step, then pass or shoot
    if exact:
        from .actions import movement_dests, can_move_kind
        rules = s.ctx.rules
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(s, 'O', i, kind):
                for q in movement_dests(s, 'O', i, kind, rules):
                    out.setdefault(q, 1)
        if s.tok_o >= 2 and not pick:
            for q in [q for q, n in out.items() if n == 1]:
                for q2 in _geo_paths('qs' if can_move else 'move', q, card.qs, rules):
                    if q2 not in out and q2 not in s.x and q2 not in s.o:
                        out[q2] = 2
        return out
    free, fixed = geo_reach(s.o[i], 0, pivot_len(s, 'O', i, card.qs), can_move, qs_left, s.ctx.rules)
    for q, n in free.items():
        out.setdefault(q, n)
    for q, arrs in fixed.items():
        n = min(arrs.values())
        if out.get(q, INF) > n:
            out[q] = n
    occ = set(s.o) | set(s.x)
    return {q: n for q, n in out.items() if n == 0 or q not in occ}


# Contest kinds, best first for the defence: (penalty, foul roll). Each map: square c -> [actions for each kind].
# Contest kinds (penalty, foul roll, two foul rolls): the -3 for standing further from the rim than the shooter; a
# foul roll when the arrow is off him; two foul rolls (step 3n F2) when level with him or further from the rim.
KINDS = ((False, False, False), (False, True, False), (False, True, True), (True, False, False), (True, True, True),
         (True, True, False))
NK = len(KINDS)


def _kind(rules, q, c, pen, foul):
    if not foul and RC.app_rule(rules, 'soft_contest') and B.dist_rim(q) >= B.dist_rim(c):
        foul = True                  # D-177: a hard contest from the side or behind rolls for a foul, arrow on him or not
    two = foul and rules.reach_angle_fouls and B.dist_rim(q) >= B.dist_rim(c)
    if pen and foul:
        two = rules.reach_angle_fouls
    return KINDS.index((pen, foul, bool(two)))


@lru_cache(maxsize=400000)
def _terms(rules, q, a, c):
    e, foul, pen, _ = G.terms(rules, q, a, c)
    return e, foul, pen


def stance_mode(s, d):
    """Step 18g (rules.zone): how defender d's arrow reads in a Contest: 0 one line; 1 the zone's two (a and a + 1);
    2 a zone broken by a Dribble (no line: every Contest takes the wrong-angle foul roll)."""
    if s.ctx.rules.zone == 'off':
        return 0
    return 2 if any(b[1] == d for b in s.beaten) else 1


def contest_map(rules, free, fixed, mode=0):
    """c -> [fewest actions for each contest kind (KINDS order)], from a defender's reach maps. mode: stance_mode."""
    out = {}
    code = (lambda a: a) if mode == 0 else (lambda a: 8 + a) if mode == 1 else (lambda a: 16)
    for q, n in free.items():                 # after a Move: any arrow; face the shooter
        for dx, dy in NEAR:
            c = (q[0] + dx, q[1] + dy)
            if not B.on_board(c):
                continue
            e, foul, pen = _terms(rules, q, 16 if mode == 2 else B.dir_between(q, c), c)
            if not e:
                continue
            k = _kind(rules, q, c, pen, foul)
            row = out.get(c)
            if row is None:
                row = out[c] = [INF] * NK
            if row[k] > n:
                row[k] = n
    for q, arrs in fixed.items():
        for a, n in arrs.items():
            for dx, dy in NEAR:
                c = (q[0] + dx, q[1] + dy)
                if not B.on_board(c):
                    continue
                e, foul, pen = _terms(rules, q, code(a), c)
                if not e:
                    continue
                k = _kind(rules, q, c, pen, foul)
                row = out.get(c)
                if row is None:
                    row = out[c] = [INF] * NK
                if row[k] > n:
                    row[k] = n
    return out


@lru_cache(maxsize=200000)
def _cmap_cached(rules, frm, arrow, qs, can_move, qs_left, mode=0):
    free, fixed = geo_reach(frm, arrow, qs, can_move, qs_left, rules)
    return contest_map(rules, free, fixed, mode)


# ---- step 18q: the race to the rim (eval.lane) -------------------------------------------------------------------------
# What the ball handler's way to the rim is worth one phase on. Both halves of the race come from the movement rules:
# he gets what he has left this phase and one movement the next; each defender gets what he has left this phase (within
# the defence's tokens) and then the reaction's two actions, fresh. Bodies and arrows that bar his way count as they
# stand. No square, distance or kind of move is named.

_NOSET = (INF,) * 6


@lru_cache(maxsize=200000)
def _cmap2(rules, q, a, qs, mode):
    """Step 22b (engine.js cm2Cached, D-222): the reaction's own off balance. c -> (the contest row within the reaction,
    the row he is set for (standing, or one Move), the kinds within the reaction's two actions as bits, those of them
    he is set for as bits). A Contest reached by a Quick Step or a Sprint finds him off balance, by the rules (D-185)."""
    full = _cmap_cached(rules, q, a, qs, True, 1, mode)
    setr = _cmap_cached(rules, q, a, qs, True, 0, mode)
    RN = RC.reply_moves(rules)            # D-261: the movements before the Contest in the reply turn
    out = {}
    for c, row in full.items():
        st = setr.get(c) or _NOSET
        fm = sum(1 << k for k, n in enumerate(row) if n <= RN)
        sm = sum(1 << k for k, n in enumerate(st) if n <= 1 and row[k] <= RN)
        out[c] = (tuple(row), tuple(st), fm, sm)
    return out


_BODY = {}


def _body_cmap2(s_next, d, mode):
    """Step 26 (engine.js bodyCm2, D-249): a defender's contest a phase on along the real paths: around attackers'
    bodies and his teammates, through the diagonals the rules leave open, blocked only by screens. The same rows as
    _cmap2."""
    rules = s_next.ctx.rules
    free, fixed = defender_map(s_next, d, exact=True)
    key = (s_next.o, s_next.x, d, s_next.arrows[d], s_next.ctx.dfn[d].qs, rules, mode, s_next.screens)
    hit = _BODY.get(key)
    if hit is None:
        RN = RC.reply_moves(rules)        # D-261
        full = contest_map(rules, free, fixed, mode)
        setr = contest_map(rules, {q: n for q, n in free.items() if n <= 1}, {s_next.x[d]: {s_next.arrows[d]: 0}}, mode)
        hit = {}
        for c, row in full.items():
            st = setr.get(c) or _NOSET
            fm = sum(1 << k for k, n in enumerate(row) if n <= RN)
            sm = sum(1 << k for k, n in enumerate(st) if n <= 1 and row[k] <= RN)
            hit[c] = (tuple(row), tuple(st), fm, sm)
        if len(_BODY) > 20000:
            _BODY.clear()
        _BODY[key] = hit
    return hit


@lru_cache(maxsize=None)
def _any_arrow_cmap2(rules, q, qs, mode):
    """engine.js anyArrow2: a defender on q whichever way he faces (he chose his arrow when a Move took him there)."""
    acc = {}
    for a in range(8):
        for c, (row, st, _fm, _sm) in _cmap2(rules, q, a, qs, mode).items():
            cur = acc.get(c)
            if cur is None:
                acc[c] = [list(row), list(st)]
            else:
                for k in range(6):
                    if row[k] < cur[0][k]:
                        cur[0][k] = row[k]
                    if st[k] < cur[1][k]:
                        cur[1][k] = st[k]
    out = {}
    RN = RC.reply_moves(rules)            # D-261
    for c, (row, st) in acc.items():
        fm = sum(1 << k for k, n in enumerate(row) if n <= RN)
        sm = sum(1 << k for k, n in enumerate(st) if n <= 1 and row[k] <= RN)
        out[c] = (tuple(row), tuple(st), fm, sm)
    return out


_GAP = {}                  # step 22b: the zone gaps' table, a context at a time (engine.js gapInfo)
_LATE_ROW = (1,) + (INF,) * 5      # step 22c: the first defender to arrive, a hand up off balance (engine.js gapLate; one movement: inside the reply under D-261 too)


@lru_cache(maxsize=None)
def _phase_step(rules, p, qs):
    """engine.js phaseStep (step 22c, D-228): the squares one phase's movement reaches from p (bodies not counted)."""
    free, fixed = geo_reach(p, 0, qs, True, 1, rules)
    return tuple(sorted(q for q in set(free) | set(fixed) if q != p and B.on_board(q)))


@lru_cache(maxsize=None)
def _phase_dist(rules, start, qs):
    """engine.js phaseDist: phases of movement from start to every square it can get to."""
    out = {start: 0}
    frontier, level = [start], 1
    while frontier:
        nxt = []
        for p in frontier:
            for q in _phase_step(rules, p, qs):
                if q not in out:
                    out[q] = level
                    nxt.append(q)
        frontier = nxt
        level += 1
    return out


@lru_cache(maxsize=None)
def _arrive(rules, start, qs, mode):
    """engine.js arrivePhases: per square, the phases before a defender starting on `start` can contest a shot there
    set (standing, or one Move), and at all (off balance: the reaction's Quick Step or Sprint). -> (set, any)."""
    setd, anyd = {}, {}
    for p, k in _phase_dist(rules, start, qs).items():
        if not B.on_board(p):
            continue
        for c, pair in _any_arrow_cmap2(rules, p, qs, mode).items():
            if not pair[2]:
                continue
            if k < anyd.get(c, INF):
                anyd[c] = k
            if pair[3] and k < setd.get(c, INF):
                setd[c] = k
    return setd, anyd
_VMAP = {}                 # step 22b: the map's Contest values, a context at a time


@lru_cache(maxsize=None)
def _any_arrow_cmap(rules, q, qs, mode):
    """A defender standing on q at the start of a phase, whichever way he faces: c -> [fewest reaction actions for each
    contest kind] (he chose his arrow when a Move took him there)."""
    out = {}
    for a in range(8):
        for c, row in _cmap_cached(rules, q, a, qs, True, 1, mode).items():
            cur = out.get(c)
            if cur is None:
                out[c] = list(row)
            else:
                for k, n in enumerate(row):
                    if n < cur[k]:
                        cur[k] = n
    return out


def ahead_row(rules, c, frm, arrow, qs, can_move, qs_left, budget, mode=0):
    """A defender's Contest of square c a phase on: from where he stands, or from any square the movement he has left
    this phase gets him to (`budget` actions: the defence's tokens left, at most two; any arrow after a Move, his own
    after a Quick Step or Sprint), with the next phase's movement fresh for the reaction. [fewest reaction actions for
    each contest kind], or None if he can't contest it at all."""
    out = None

    def merge(row):
        nonlocal out
        if row is None:
            return
        if out is None:
            out = list(row)
        else:
            for k, n in enumerate(row):
                if n < out[k]:
                    out[k] = n
    merge(_cmap_cached(rules, frm, arrow, qs, True, 1, mode).get(c))
    if budget > 0:
        free, fixed = geo_reach(frm, arrow, qs, can_move, qs_left, rules)
        for q, n in free.items():
            if n <= budget:
                merge(_any_arrow_cmap(rules, q, qs, mode).get(c))
        for q, arrs in fixed.items():
            for a, n in arrs.items():
                if 0 < n <= budget:
                    merge(_cmap_cached(rules, q, a, qs, True, 1, mode).get(c))
    return out


@lru_cache(maxsize=None)
def _shot_paths(start, qs, rules, no_rim, deep=0):
    """Step 18s (the coverage map): every movement path from start that ends where a shot may go up, all on the board:
    (path, rushed), rushed for a Quick Step or a Sprint, not for a Move."""
    out = []

    def ok(p):
        c = p[-1]
        return all(B.on_board(q) for q in p) and zone_at(c, deep) in RC.ZONE_POINTS and not (no_rim and c == RC.RIM)
    for p in B.move_paths(start, rules):
        if ok(p):
            out.append((tuple(p), False))
    for p in B.qs_paths(start, qs, rules):
        if ok(p):
            out.append((tuple(p), True))
    for _, p in B.sprint_paths(start, qs, rules):
        if ok(p):
            out.append((tuple(p), True))
    return tuple(out)


def cov_pass(s, i, q):
    """Step 18s (engine.js covPass): the chance a pass to attacker i on q arrives, by the rules (0: denied)."""
    rules = s.ctx.rules
    a = s.o[s.ball]
    for xp in s.x:
        if B.adjacent(xp, q) and B.on_segment(xp, a, q, 0.5):
            return 0.0
    if s.tok_x <= 0 or s.count('X', 'intercept') >= RC.LIMITS['X']['intercept']:
        return 1.0
    passer = rolled(s, 'O', s.ball, 'pass')
    occ = set(s.x)
    occ.update(z for k, z in enumerate(s.o) if k != i)
    occ.add(q)
    worst = 0.0
    for d, xp in enumerate(s.x):
        can_move, qs_left = _caps(s, 'X', d)
        pi = icpt_pi(s, a, q, d, xp, s.arrows[d], can_move, qs_left, occ, passer, i)
        if pi > worst:
            worst = pi
    return 1.0 - worst


@lru_cache(maxsize=None)
def _lane_paths(start, qs, rules):
    """Every movement path from start that ends on a paint square, all on the board: (path, rushed), rushed for a
    Quick Step or a Sprint (the shot after it is off balance, D-151 and D-185), not for a Move."""
    paint = set(PAINT_SQUARES)
    out = []
    for p in B.move_paths(start, rules):
        if p[-1] in paint and all(B.on_board(q) for q in p):
            out.append((tuple(p), False))
    for p in B.qs_paths(start, qs, rules):
        if p[-1] in paint and all(B.on_board(q) for q in p):
            out.append((tuple(p), True))
    for _, p in B.sprint_paths(start, qs, rules):
        if p[-1] in paint and all(B.on_board(q) for q in p):
            out.append((tuple(p), True))
    return tuple(out)


# ---- shot values -------------------------------------------------------------------------------------------------------

def shot_value(card, dcards, t, c, contests, window, rules):
    """Expected shot value of `card` shooting type t from c, the defence choosing its best contest among defenders
    that can reach a contest within `window` actions. contests: {d: row}. Returns (value, best defender or -1)."""
    pts = RC.ZONE_POINTS[B.zone(c)]
    r = card.shot(t)
    best, who = pts * r, -1
    ft = None
    fiba = RC.app_rule(rules, 'fiba_fouled_shot')
    for d, row in contests.items():
        if row is None:
            continue
        for k, n in enumerate(row):
            if n > window:
                continue
            pen, foul, two = KINDS[k]
            con = dcards[d].con(t) - (RC.FAR_CONTEST_PENALTY if pen else 0)
            if rules.floor_contest_zero:
                con = max(0, con)
            v = pts * (r - con)
            if rules.floor_declared_shot:
                v = max(0, v)
            if foul:
                if fiba:
                    ft = foul_on_shot_points(card, t, pts, rules, r, v, r - con)[0]     # D-174: by this Contest
                elif ft is None:
                    ft = foul_on_shot_points(card, t, pts, rules)[0]
                pf = float(p_fouls(p_foul(dcards[d].r['foul_contest'], rules), 2 if two else 1))
                v = pf * ft + (1 - pf) * v
            if v < best:
                best, who = v, d
    return best, who


def best_shot(card, dcards, c, contests, window, rules):
    """(value, type, contester) for the best shot type from c."""
    z = B.zone(c)
    if z not in SHOOT:
        return 0.0, None, -1
    best = (-1.0, None, -1)
    for t in RC.ZONE_SHOTS[z]:
        v, who = shot_value(card, dcards, t, c, contests, window, rules)
        if v > best[0]:
            best = (v, t, who)
    return best


# ---- the board read: THREAT and COVERAGE -----------------------------------------------------------------------------

class Look:
    """One way attacker i can shoot: from square c by route r, delivered with probability p. now=True: the shot is
    released before the defence has a turn (shoot or drive this turn), so no response can cover it. vals[t][d]:
    the expected shot value of type t if defender d contests (the best contest he reaches in time), open[t] if
    nobody does."""
    __slots__ = ('i', 'c', 'route', 'p', 'now', 'open', 'vals', 'types', 'minex', 'base', 'replies', 'rushed')

    def finish(self):
        """Precompute, per shot type, the best contest without each defender (minex[j][t]) and the look's value."""
        self.minex = {}
        best = 0.0
        for j in range(5):
            row = {}
            for t in self.types:
                v = self.open[t]
                for d, vals in self.vals.items():
                    if d != j and t in vals and vals[t] < v:
                        v = vals[t]
                row[t] = v
            self.minex[j] = row
        for t in self.types:
            v = self.open[t]
            for vals in self.vals.values():
                if t in vals and vals[t] < v:
                    v = vals[t]
            best = max(best, v)
        self.base = self.p * best

    def swapped(self, j, vals, p=None):
        """The look's value with defender j's contest replaced by vals (None: he can't contest it), and the delivery
        chance replaced by p (his response changed the lane)."""
        mx = self.minex[j]
        best = 0.0
        for t in self.types:
            v = mx[t]
            if vals and t in vals and vals[t] < v:
                v = vals[t]
            if v > best:
                best = v
        return (self.p if p is None else p) * best

    def __init__(self, i, c, route, p, now, replies=None):
        self.i, self.c, self.route, self.p, self.now = i, c, route, p, now
        self.rushed = False          # D-151 (rules.control): the shooter would be rushed for this look
        # B0/B2: the defence replies (turns of at most 2 actions) before this look can be released
        self.replies = (0 if now else 1) if replies is None else replies


PATH_ROUTES = ('drive', 'later', 'cut')
FEATURES = (            # step 17: name, and meaning in words (the order is the weights file's order)
    ('shot_now', "the ball handler's shot from where he stands, against the reaction"),
    ('look_now', 'the best look the offence can release this turn'),
    ('best_look_after_cover', "the best look left after the defence's best cover"),
    ('second_look_after_cover', "the second attacker's best look after that cover"),
    ('best_look_before_cover', 'the best look before the defence replies'),
    ('best_look_after_shares', 'the best look when each defender can attend only one attacker'),
    ('paint_next_phase', "the ball handler's best paint look next phase"),
    ('free_looks', 'attackers whose best look no defender can Contest in time'),
    ('mismatches_two_bands', 'attackers whose best look is contested by a defender two bands below'),
    ('mismatches_one_band', 'attackers whose best look is contested by a defender one band below'),
    ('offence_tokens', "the offence's tokens left this phase"),
    ('defence_tokens', "the defence's tokens left this phase"),
    ('offence_to_act', 'the offence is to act'),
    ('defenders_moved', 'defenders who have used their Move this phase'),
    ('attackers_moved', 'attackers who have used their Move this phase'),
)
BAND = {'L': 0, 'A': 1, 'H': 2}                       # step 16: the cards' bands as tiers
PAINT = next(z for z, shots in RC.ZONE_SHOTS.items() if 'layup' in shots)      # the zone of layups, dunks and post shots
PAINT_SQUARES = sorted((x, y) for x in range(B.W) for y in range(1, B.H + 1) if B.on_board((x, y)) and B.zone((x, y)) == PAINT)


def _blocks(q, start, c, qs, rules):
    from .reach import blocks_path
    return blocks_path(q, start, c, qs, rules)


class Read:
    """One position's THREAT, COVERAGE, overloads and the leaf value, from the offence's point of view.
    exact: the rules' own reach and pass outcomes (the root, the trainer); else cached geometry (the leaves).
    attention: (attackers, defenders) to evaluate (None = all): Rookie and Starter read only those nearest the ball."""

    def __init__(self, s, exact=False, attention=None, k=None, cfg=None, looks_per=None):
        self.s = s
        self.exact = exact
        self.rules = s.ctx.rules
        self.cfg = cfg or CONFIG['eval']
        self.k = k if k is not None else self.cfg['responses_per_defender']
        self.L = looks_per or self.cfg.get('looks_per_attacker', 6)
        att = attention or (range(5), range(5))
        self.att_o, self.att_x = list(att[0]), list(att[1])
        self.dcards = s.ctx.dfn
        self.o_to_act = s.side == 'O' and s.stage == 'play'
        self.react = min(2, s.tok_x) if s.tok_x > 0 else 0
        if self.rules.contest_action:
            # D-18: the Contest is itself one of the reaction's actions (and a token), so the closeout before it has one
            # fewer; inside the reaction, the actions already taken count
            if s.stage == 'reaction':
                self.react = max(0, min(RC.MAX_ACTIONS_PER_TURN - s.turn_n, s.tok_x))
            self.react_moves = self.react - 1
        else:
            self.react_moves = self.react
        self._cm = {d: self._contest(d) for d in range(5)}
        self.looks = {i: self._looks(i) for i in self.att_o}
        self.threat = {i: self._best(self.looks[i]) for i in self.att_o}
        self._cover = None
        self._budget = None
        self._adv = None
        self._ahead = False                # step 18q: lane_ahead(), once
        self._lane = False                 # step 18q: _lane_data(), once
        self._map2 = None                # step 18s, stop two: map_two(), once
        self._lg = None                  # step 20: map_lasting(), once
        self._drib = None                  # step 18q: _dribble_ok(), once

    # -- contest maps
    def _contest(self, d, at=None, arrow=None, used=None):
        s = self.s
        if not B.on_board(s.x[d]):
            return {}
        if at is None and (self.exact or self.cfg.get('reach')):
            # step 12 (eval.reach): the reach map's exact movement (blocking, screens, locks) for every reading
            free, fixed = defender_map(s, d, exact=True)
            return contest_map(self.rules, free, fixed, stance_mode(s, d))
        can_move, qs_left = _caps(s, 'X', d)
        frm, a = s.x[d], s.arrows[d]
        if at is not None:                    # after a response: what is left of his capacity for the reaction
            frm, a = at, arrow
            if used == 'move':
                can_move = False
            elif used in ('qs', 'sprint'):
                qs_left = 0
                can_move = can_move and used == 'qs'
            if s.tok_x <= 2:
                can_move, qs_left = False, 0
        elif s.tok_x <= 0:
            return contest_map(self.rules, {}, {frm: {a: 0}}, stance_mode(s, d))
        return _cmap_cached(self.rules, frm, a, s.ctx.dfn[d].qs, can_move, qs_left, stance_mode(s, d))

    def _vals2(self, look, d, row, setrow=None, split=None):
        """Step 16: the same, for a look a phase away: any Contest he reaches with two movement actions. setrow (step
        22b, D-222): the contest row he is set for; a kind outside it is contested off balance."""
        keep, self.react_moves = self.react_moves, RC.reply_moves(self.rules)     # D-261: one movement before the Contest
        self._phase_away = True                    # D-151: the rushed state doesn't carry over the phase's end
        try:
            return self._vals(look, d, row, setrow=setrow, split=split)
        finally:
            self.react_moves = keep
            self._phase_away = False

    def _vals_map(self, look, d, pair):
        """The map's Contest of a look by defender d (pair: _cmap2's value for the look's square)."""
        if pair is None or not pair[2]:
            return None
        # (a phase away the Contest turns only on the cards, the square and the kinds he reaches: kept a context at a time)
        ctx = self.s.ctx
        memo = _VMAP.get(ctx)
        if memo is None:
            if len(_VMAP) > 8:
                _VMAP.clear()
            memo = _VMAP[ctx] = {}
        key = (look.i, look.c, look.rushed, d, pair[2], pair[3])
        if key not in memo:
            memo[key] = self._vals2(look, d, pair[0], pair[1]) or None
        return memo[key]

    def _vals(self, look, d, row, moves=None, dflags=None, setrow=None, split=None):
        """Expected value per shot type if defender d (contest row `row`) contests look within the reaction (moves: with
        at most that many of the reaction's movements; 0 = from where he stands). dflags (step 18e, the open list's
        re-read): the defender's control state after his action (rushed where he stands, his Move used), in place of
        the state's."""
        out = {}
        if row is None:
            return None
        limit = self.react_moves if moves is None else min(moves, self.react_moves)
        soft = RC.app_rule(self.rules, 'soft_contest')
        soft_limit = max(self.react, self.react_moves, 0)
        if RC.contest_costs(self.rules):
            soft_limit = limit                   # D-261: the normal Contest is an action too: one movement before it
        if moves is not None:
            soft_limit = min(moves, soft_limit)
        card = self.s.ctx.off[look.i]
        pts = RC.ZONE_POINTS[shot_zone(self.s.ctx, look.c)]
        rules = self.rules
        away = getattr(self, '_phase_away', False)
        control = RC.control_size(rules) > 0 and not away
        # D-151 (rules.control), as the reading takes it: a defender contesting from where he stands is rushed if his
        # last movement was a Quick Step or Sprint; one who must move to contest is rushed if his Move is already used
        # (only a Quick Step or Sprint is left), and is taken to Move there otherwise. The rules themselves are exact
        # (scoring.contest_options); the search settles every declared shot by them.
        d_stand = control and (self.s.rushed('X', d) if dflags is None else dflags[0])
        d_moved = control and (self.s.moved('X', d) if dflags is None else dflags[1])
        position = RC.position_contest(rules)
        plus5 = RC.app_rule(rules, 'points_play_on') and not self.s.ctx.hold_for_one
        block = RC.block_rule(rules)
        for ti, t in enumerate(look.types):
            r = card_shot(self.s.ctx, card, t, look.c)     # D-274: a deep three is 1 off a square past the band
            # (step 18q: a look a phase away whose shooter gets there by a Quick Step or Sprint is rushed by that
            # movement itself; the defenders' own rushed states still don't carry over)
            cut = RC.control_cut(rules, t) if (control or (away and look.rushed) or setrow is not None) else 0
            if cut and look.rushed:
                r -= cut
            best = None
            jump = position and t in RC.JUMP_SHOTS      # D-191: a jump shot has no Contest action: position only (below)
            for k, n in enumerate(row):
                if n > limit:
                    continue
                if block:
                    # D-271: the block, from every kind he reaches, on every shot (scoring.block_option, as the reading takes it)
                    rushed_k = bool(cut) and ((d_stand if n == 0 else d_moved) if setrow is None else setrow[k] > 1)
                    v = self._block_value(card, d, t, k, pts, r, cut if rushed_k else 0, plus5, (cut and look.rushed))
                    if split is not None:
                        # step 31 (engine.js blockLine): the block as a line in what the next phase is worth; the plain
                        # Contest stays his other answer (below)
                        split.append((ti, v, self._block_c1(d, k, cut if rushed_k else 0)))
                    else:
                        if best is None or v < best:
                            best = v
                        continue
                if jump:
                    continue
                pen, foul, two = KINDS[k]
                if position and not foul:
                    continue                             # D-191: in front with the arrow on him: automatic (below)
                con = self.dcards[d].con(t) - (RC.FAR_CONTEST_PENALTY if pen else 0)
                if rules.floor_contest_zero:
                    con = max(0, con)
                if cut and ((d_stand if n == 0 else d_moved) if setrow is None else setrow[k] > 1):
                    con = max(0, con - cut)              # a rushed Contest: reduced; no extra foul roll (D-154)
                if position:
                    con = max(RC.CONTEST_FLOOR, con)     # D-193
                v = pts * (r - con)
                if rules.floor_declared_shot:
                    v = max(0, v)
                if foul:
                    if RC.app_rule(rules, 'fiba_fouled_shot'):
                        ft = foul_on_shot_points(card, t, pts, rules, r, v, r - con)[0]   # D-174
                    else:
                        ft = foul_on_shot_points(card, t, pts, rules, r if (cut and look.rushed) else None)[0]
                    if plus5:
                        ft += RC.STEAL_FOUL_BONUS          # D-198: a shooting foul is +5 and its free throws (step 18s)
                    pf = float(p_fouls(p_foul(self.dcards[d].r['foul_contest'], rules), 2 if two else 1))
                    v = pf * ft + (1 - pf) * v
                if best is None or v < best:
                    best = v
            if soft:
                # D-177: a soft contest needs no action, so every action of the reaction may be a movement
                for k, n in enumerate(row):
                    if n > soft_limit:
                        continue
                    # D-194: the full rating from in front with the arrow on him, on every shot; else 3 less
                    full = position and not KINDS[k][1]
                    con = self.dcards[d].con(t) - (0 if full else RC.SOFT_CONTEST) - (RC.FAR_CONTEST_PENALTY if KINDS[k][0] else 0)
                    if cut and ((d_stand if n == 0 else d_moved) if setrow is None else setrow[k] > 1):
                        con -= cut
                    if position:
                        con = max(RC.CONTEST_FLOOR, con)  # D-193
                    if con <= 0:
                        continue
                    v = max(0, pts * (r - con))
                    if best is None or v < best:
                        best = v
            if best is not None:
                out[t] = best
        return out or None

    def _block_value(self, card, d, t, k, pts, r, dcut, plus5, shooter_cut):
        """D-271, as the map reads it: defender d's block of this shot from contest kind k (KINDS: behind, foul, two):
        fouls first on his Foul (Block) (square none, in front with the arrow off one, beside or behind two), then his
        Block (less 3, or 6 from behind, less the rushed cut dcut, at least 1) is a turnover at -5 (the lost pass's price
        in a look), else the shot against his full contest (3 less from behind, dcut, at least 1)."""
        rules = self.rules
        pen, foul, two = KINDS[k]
        foul = foul or pen                               # from behind always two foul rolls
        dc = self.dcards[d]
        con = max(RC.CONTEST_FLOOR, dc.con(t) - (RC.FAR_CONTEST_PENALTY if pen else 0) - dcut)
        b = max(RC.CONTEST_FLOOR, dc.r['block'] - (RC.BLOCK_BEHIND if pen else (RC.BLOCK_SIDE if foul else 0)) - dcut)
        v = pts * (r - con)
        if rules.floor_declared_shot:
            v = max(0, v)
        pb = float(p_success(b, rules))
        vs, v = v, pb * RC.TURNOVER_POINTS + (1 - pb) * v
        if foul:
            if RC.app_rule(rules, 'fiba_fouled_shot'):
                ft = foul_on_shot_points(card, t, pts, rules, r, vs, r - con)[0]
            else:
                ft = foul_on_shot_points(card, t, pts, rules, r if shooter_cut else None)[0]
            if plus5:
                ft += RC.STEAL_FOUL_BONUS
            pf = float(p_fouls(p_foul(dc.r['foul_block'], rules), 2 if (two or pen) else 1))
            v = pf * ft + (1 - pf) * v
        # Shaun (20 Nov): no floor. A block is a turnover (-5), so a shot into a likely block is worth less than nothing,
        # and the reading must see it to avoid it (the shot's own floor, OQ-5, still applies to the shot itself above)
        return v

    def _block_c1(self, d, k, dcut):
        """Step 31 (engine.js blockLine): the chance the block lands and no foul came first: what multiplies the worth
        of the phase after it."""
        rules = self.rules
        pen, foul, two = KINDS[k]
        foul = foul or pen
        dc = self.dcards[d]
        b = max(RC.CONTEST_FLOOR, dc.r['block'] - (RC.BLOCK_BEHIND if pen else (RC.BLOCK_SIDE if foul else 0)) - dcut)
        pb = float(p_success(b, rules))
        pf = float(p_fouls(p_foul(dc.r['foul_block'], rules), 2 if (two or pen) else 1)) if foul else 0.0
        return (1 - pf) * pb

    def _value(self, look, swap=None):
        """The look's value, the defence contesting with its best defender (swap: {d: replacement vals})."""
        best = 0.0
        for t in look.types:
            v = look.open[t]
            for d, vals in look.vals.items():
                if swap and d in swap:
                    vals = swap[d]
                if vals and t in vals and vals[t] < v:
                    v = vals[t]
            if swap:
                for d, vals in swap.items():
                    if d not in look.vals and vals and t in vals and vals[t] < v:
                        v = vals[t]
            if v > best:
                best = v
        return look.p * best

    # -- the looks (B2)
    def pass_p(self, i, c):
        s = self.s
        if i == s.ball:
            return 1.0
        if s.count('O', 'pass') >= RC.LIMITS['O']['pass']:
            return 0.0
        if self.exact and c == s.o[i]:
            return _pass_prob(s, i)
        return _lane_p(s, i, c)

    def _looks(self, i):
        s, rules = self.s, self.rules
        if not B.on_board(s.o[i]):
            return []
        card = s.ctx.off[i]
        left_now = (2 - s.turn_n) if self.o_to_act else 2
        shot_ok = s.count('O', 'shot') < RC.LIMITS['O']['shot']
        out = []
        if i == s.ball:
            reach = {s.o[i]: 0}
            from .actions import movement_dests, can_move_kind
            for kind in ('move', 'qs', 'sprint'):
                if can_move_kind(s, 'O', i, kind):
                    for q in movement_dests(s, 'O', i, kind, rules):
                        reach.setdefault(q, 1)
            if self.cfg.get('coverage_budget'):
                for q in two_actions(s, i, reach):        # step 13 B2 (D-115): where he can get to in two actions
                    reach[q] = 2
        else:
            reach = {q: n for q, n in attacker_reach(s, i).items() if n <= 1}
        no_rim = RC.rim_shot_barred(rules)
        for c, n in reach.items():
            z = shot_zone(s.ctx, c)                              # D-274: a deep square his team's level opens is a three
            if z not in SHOOT or (no_rim and c == RC.RIM):       # D-198: no shot from the rim's own square
                continue
            # B0/B2: count the offence's actions. The ball handler can move then shoot in one turn; a receiver catches
            # and shoots where he stands after the pass (one defence reply between); a receiver who must move first
            # and can't fit the move and the pass into this turn needs a later turn (another reply)
            if i == s.ball:
                if n == 0 and shot_ok and (left_now >= 1):
                    lk = Look(i, c, 'shoot', 1.0, self.o_to_act)
                elif n == 1 and shot_ok and left_now >= 2 and s.tok_o >= 2:
                    lk = Look(i, c, 'drive', 1.0, self.o_to_act)
                else:
                    lk = Look(i, c, 'later', self.cfg['later_p'], False, replies=1 if self.o_to_act else 2)
            else:
                p = self.pass_p(i, c)
                if p <= 0:
                    continue
                if n == 0:
                    lk = Look(i, c, 'catch', p, False, replies=1)
                elif left_now >= 2 and s.tok_o >= 2 and self.o_to_act:
                    lk = Look(i, c, 'cut', p, False, replies=1)
                else:
                    lk = Look(i, c, 'cut', p * self.cfg['later_p'], False, replies=2)
            lk.types = RC.ZONE_SHOTS[z]
            pts = RC.ZONE_POINTS[z]
            if RC.control_size(rules):
                # D-151, as the reading takes it: shooting from where he stands he is rushed if his last movement was
                # a Quick Step or Sprint; if he must move first he is rushed when his Move is already used
                lk.rushed = s.rushed('O', i) if n == 0 else s.moved('O', i)
            if lk.rushed:
                lk.open = {t: pts * (card_shot(s.ctx, card, t, c) - RC.control_cut(rules, t)) for t in lk.types}
            else:
                lk.open = {t: pts * card_shot(s.ctx, card, t, c) for t in lk.types}
            lk.vals = {}
            for d in self.att_x:
                dj = getattr(self, '_dj', None)             # step 18f: a moved defender's control state, given
                v = self._vals(lk, d, self._cm[d].get(c), dflags=dj[1] if dj and dj[0] == d else None)
                if v:
                    lk.vals[d] = v
            lk.finish()
            out.append((lk.base, lk))
        out.sort(key=lambda r: -r[0])
        return [lk for _, lk in out[:self.L]]

    def _best(self, looks, swap=None, now_only=False):
        best, arg = 0.0, None
        for lk in looks:
            if now_only and not lk.now:
                continue
            v = lk.base if (not swap or lk.now) else self._value(lk, swap)
            if v > best + 1e-9:
                best, arg = v, lk
        if arg is None:
            return dict(value=0.0, sq=None, route='none', p=0.0, now=False)
        return dict(value=best, sq=arg.c, route=arg.route, p=arg.p, now=arg.now, type=max(arg.types, key=lambda t: arg.open[t]))

    # -- step 18e (search.open_list, D-156): the cheap read of a defender's action
    def _cont_of(self, tv):
        """What the attackers' best looks leave to play for, as the quick reading takes it (tv: each attacker's best
        look, re-read; None: this read's own)."""
        vals = [self.threat[i]['value'] if tv is None else tv[i] for i in self.att_o]
        top = 0.0
        for n, t in enumerate(vals):
            if n == 0 or t > top:
                top = t
        ties = [t for t in vals if t >= top - 1e-9]
        return (sum(ties) / len(ties) if ties else 0.0) * self.cfg['continuation']

    def _quick_cont(self, cont, nowv, snv, tv=None):
        """The quick reading (Read(s, k=0, looks_per=3).leaf(), no pass in the air) from what is left to play for and
        the shots that can go up now, re-read (snv < 0: none). tv (step 18h): each attacker's best look, re-read."""
        s = self.s
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        sn = None if snv < 0 else snv
        last = not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS
        if last:
            v = banked + max(sn or 0.0, nowv)
        elif leaf_mode(s, self.cfg) == 'relative':
            rel = vcoarse(s) + cont - relative_average(s, self.cfg, False)
            if self.cfg.get('lane') is True:             # step 18q: the lane, re-read (tv[7]) or this read's own
                if tv is not None and len(tv) > 7:
                    rel = self.lane_rel(rel, tv[7], tv[8], tv[9], False)
                else:
                    rel = self.lane_own(rel, False)
            v = banked + max(sn or 0.0, nowv, rel)
        elif leaf_mode(s, self.cfg) == 'looks':
            v = banked + max(sn or 0.0, nowv, cont)
        else:
            v = banked + max(sn or 0.0, nowv, cont, vcoarse(s))
        if self.cfg.get('settle_shots') is True:
            top = ceiling(s)
            if v - banked > top:
                v = banked + top
            w = learned_weights() if self.cfg.get('calibrated') is True and self.cfg.get('learned') is not True else None
            if w is not None and w.get('calibration') and s.stage == 'play' and not last:
                pm = parts_map(s, self.cfg, w)
                r = None
                po = play_on_map(s, self.cfg, w)
                if po is not None:                    # step 18h (eval.exact_shot)
                    rel = vcoarse(s) + cont - relative_average(s, self.cfg, False)
                    if rel > top:
                        rel = top
                    r = max(sn or 0.0, nowv, calibrate(po, s, self.o_to_act, rel))
                    pm = None
                if pm is not None:                    # step 18h (eval.no_floor): with no cover read, every look is left
                    res = sorted((self.threat[i]['value'] if tv is None else tv[i] for i in self.att_o), reverse=True)
                    r = parts_value(pm, s, self.o_to_act, max(sn or 0.0, nowv), res[0] if res else 0.0, res[1] if len(res) > 1 else 0.0)
                if r is None:
                    cal = calibration_for(s, self.cfg, w)
                    r = calibrate(cal, s, self.o_to_act, v - banked)
                if r > top:
                    r = top
                v = banked + r
        return v

    def _contest_at(self, j, q, a, can_move, qs_left):
        s = self.s
        if s.tok_x <= 0:
            return contest_map(self.rules, {}, {q: {a: 0}}, stance_mode(s, j))
        return _cmap_cached(self.rules, q, a, s.ctx.dfn[j].qs, can_move, qs_left, stance_mode(s, j))

    def reread(self, j, q, a, can_move, qs_left, dflags):
        """Every attacker's best look with defender j standing at q facing a, with can_move / qs_left left to him and
        his control state dflags (rushed where he stands, his Move used): this read's own looks, each re-read with that
        one defender moved (the re-read responses() makes for its hand-picked squares, here for any square, for every
        attacker, and for the looks that can go up now as well). Returns eight values: one an attacker, then the best
        shot that can go up now and the ball handler's shot from where he stands (-1: none), each among an attacker's
        first three looks as the quick reading takes them; and (step 18q, eval.lane) the lane's value (-1: none), its
        value with the defender a Dribble would beat out of the race (-1: none), and the chance of that."""
        s = self.s
        carrier = s.ball
        reach = bool(self.cfg.get('reach'))
        leave = self.__dict__.setdefault('_leave', {})
        cm = self._contest_at(j, q, a, can_move, qs_left)
        front = lambda p_: (carrier in self.att_o and B.cheb(p_, s.o[carrier]) <= 2 and
                            B.dist_rim(p_) < B.dist_rim(s.o[carrier]))
        moved = q != s.x[j]
        into = moved and front(q)
        out_of = moved and front(s.x[j]) and not front(q)
        blocks = into or out_of
        out = [0.0] * 10
        out[7], out[8] = -1.0, -1.0
        if self.cfg.get('lane') is True:             # step 18q: the lane, and the lane with the man his Dribble would beat out of it
            out[7] = self.lane_reread(j, q, a, can_move, qs_left)
            out[8], out[9] = self.lane_dribble(out[7], j, q, a, can_move, qs_left, bool(dflags[0]))
        nowv, snv = 0.0, -1
        if blocks:
            lv = leave.get(j) if out_of else None
            if lv is None:
                at = q if into else (-9, -9)
                mv = s.with_(x=s.x[:j] + (at,) + s.x[j + 1:], arrows=s.arrows[:j] + (a,) + s.arrows[j + 1:])
                sub = Read.__new__(Read)
                sub.__dict__.update(self.__dict__)
                sub.s = mv
                sub._cm = dict(self._cm)
                sub._cm[j] = cm if into else {}
                sub._dj = (j, dflags) if kept_on(self.cfg) else None
                lks = sub._looks(carrier)
                lv = [0.0, 0.0, -1]
                for lk in lks:
                    if lk.base > lv[0]:
                        lv[0] = lk.base
                for lk in lks[:3]:
                    if lk.now and lk.base > lv[1]:
                        lv[1] = lk.base
                    if lv[2] < 0 and self.o_to_act and lk.route == 'shoot':
                        lv[2] = lk.base
                if out_of:
                    leave[j] = lv
            out[carrier], nowv, snv = lv[0], lv[1], lv[2]
        for i in self.att_o:
            if i == carrier and blocks:
                continue
            best = 0.0
            for n, lk in enumerate(self.looks[i]):
                if reach and moved and not lk.now and lk.route in PATH_ROUTES and _blocks(q, s.o[i], lk.c, s.ctx.off[i].qs,
                                                                                         self.rules):
                    v = 0.0
                else:
                    p_new = None
                    if lk.route in ('catch', 'cut') and moved:
                        p_new = _lane_p_moved(s, lk.c, j, q, a, can_move, qs_left, i)
                    row = cm.get(lk.c)
                    v = lk.swapped(j, self._vals(lk, j, row, dflags=dflags) if row is not None else None, p_new)
                if v > best:
                    best = v
                if n < 3:
                    if lk.now and v > nowv:
                        nowv = v
                    if snv < 0 and i == carrier and self.o_to_act and lk.route == 'shoot':
                        snv = v
            out[i] = best
        out[5], out[6] = nowv, snv
        return out

    # -- COVERAGE (B3)
    def responses(self, j):
        """Defender j's top-k responses in his next turn (a square and an arrow, by Move or Quick Step), each with
        the threat left on every attacker; standing still first."""
        s = self.s
        base = {i: self.threat[i]['value'] for i in self.att_o}
        still = ((s.x[j], s.arrows[j], None), base)
        if self.k <= 0 or s.tok_x <= 0 or not B.on_board(s.x[j]) or not any(not lk.now for i in self.att_o for lk in self.looks[i]):
            return [still]
        can_move, qs_left = _caps(s, 'X', j)
        free, fixed = geo_reach(s.x[j], s.arrows[j], s.ctx.dfn[j].qs, can_move, qs_left, self.rules)
        occ = set(s.o) | set(s.x)
        spots = [lk.c for i in self.att_o for lk in self.looks[i][:3] if not lk.now]
        bp = s.o[s.ball]
        lanes = set()
        for i in self.att_o:
            for lk in self.looks[i][:2]:
                if lk.route in ('catch', 'cut') and B.on_board(bp):
                    lanes |= lane_squares(bp, lk.c, 0.5)
        if B.on_board(bp):                             # and the ball handler's way to the rim
            lanes |= lane_squares(bp, RC.RIM, 0.5)
        reach = bool(self.cfg.get('reach'))
        paths = {}
        if reach:                                      # step 12: every attacker's way to his later looks
            from .reach import path_squares
            for i in self.att_o:
                for lk in self.looks[i]:
                    if not lk.now and lk.route in PATH_ROUTES:
                        sq = path_squares(s.o[i], lk.c, s.ctx.off[i].qs, self.rules)
                        paths.setdefault(i, set()).update(sq)
                        lanes |= sq
        cands = []
        for q, n in free.items():
            if n > 1 or (q in occ and q != s.x[j]):
                continue
            near = [c for c in spots if B.cheb(q, c) <= 2 and c != q]
            if not near and q in lanes:
                near = [bp] if q != bp else []
            if not near:
                continue
            c0 = min(near, key=lambda c: (B.cheb(q, c), c))      # face the nearest look: the arrow that answers it
            cands.append((q, B.nearest_dir(q, c0), 'move'))
        for q, arrs in fixed.items():
            if q in occ and q != s.x[j]:
                continue
            for a, n in arrs.items():
                if n == 1 and any(B.cheb(q, c) <= 2 for c in spots):
                    cands.append((q, a, 'qs'))
        out = []
        near = {}
        for i in self.att_o:
            sq = set()
            for lk in self.looks[i]:
                if not lk.now:
                    cx, cy = lk.c
                    sq.update((x, y) for x in range(cx - 3, cx + 4) for y in range(cy - 3, cy + 4))
            near[i] = sq | paths.get(i, set())
        carrier = s.ball
        leave_cache = {}
        front = lambda p_: (carrier in self.att_o and B.cheb(p_, s.o[carrier]) <= 2 and
                            B.dist_rim(p_) < B.dist_rim(s.o[carrier]))
        kept = kept_on(self.cfg) and RC.control_size(self.rules) > 0
        moved_j = s.moved('X', j)
        for q, a, used in cands:
            cm = self._contest(j, q, a, used)
            # step 18f (eval.kept_actions): his control after the answer (rushed where he stands, his Move used)
            dfl = None if not kept else ((False, True) if used == 'move' else (True, moved_j))
            left = dict(base)
            gain = 0.0
            moved_state = None
            into, out_of = q != s.x[j] and front(q), q != s.x[j] and front(s.x[j]) and not front(q)
            blocks = into or out_of                     # steps into, or out of, the ball handler's way
            if blocks:
                # standing in the ball handler's way blocks squares and adds a zone; leaving it opens them: re-read his
                # looks (once per defender for leaving, wherever he goes)
                if out_of and j in leave_cache:
                    left[carrier] = leave_cache[j]
                else:
                    at = q if into else (-9, -9)
                    moved = s.with_(x=s.x[:j] + (at,) + s.x[j + 1:], arrows=s.arrows[:j] + (a,) + s.arrows[j + 1:])
                    sub = Read.__new__(Read)
                    sub.__dict__.update(self.__dict__)
                    sub.s = moved
                    sub._cm = dict(self._cm)
                    sub._cm[j] = cm if into else {}
                    sub._dj = (j, dfl) if dfl is not None else None
                    left[carrier] = max((lk.base for lk in sub._looks(carrier)), default=0.0)
                    if out_of:
                        leave_cache[j] = left[carrier]
                gain += max(0.0, base[carrier] - left[carrier])
            for i in self.att_o:
                if i == carrier and blocks:
                    continue
                if q not in near[i]:
                    continue                     # out of his reach after this response: unchanged
                best = 0.0
                for lk in self.looks[i]:
                    if lk.now:
                        v = lk.base
                    elif reach and q != s.x[j] and lk.route in PATH_ROUTES and _blocks(q, s.o[i], lk.c, s.ctx.off[i].qs,
                                                                                        self.rules):
                        v = 0.0                  # step 12: he reaches the attacker's way first: the look is gone
                    else:
                        row = cm.get(lk.c)
                        p_new = None
                        if lk.route in ('catch', 'cut') and q != s.x[j]:
                            if moved_state is None:
                                moved_state = s.with_(x=s.x[:j] + (q,) + s.x[j + 1:],
                                                      arrows=s.arrows[:j] + (a,) + s.arrows[j + 1:],
                                                      moved_x=s.moved_x | (1 << j) if used == 'move' else s.moved_x)
                            p_new = _lane_p(moved_state, i, lk.c, reach=False)   # his response changes the lane
                        v = lk.swapped(j, self._vals(lk, j, row, dflags=dfl) if row is not None else None, p_new)
                    if v > best:
                        best = v
                left[i] = best
                gain += max(0.0, base[i] - best)
            if gain > 1e-9:
                out.append((gain, (q, a, used), left))
        out.sort(key=lambda r: -r[0])
        return [still] + [(r[1], r[2]) for r in out[:self.k]]

    def cover(self):
        """The best cover: one response per defender, at most the defence's actions in its next turn moving
        (a Move or Quick Step each), minimising the best uncovered threat (residual(i) = the least threat any chosen
        response leaves on i). Returns dict(value, choice {j: response}, residual {i: value}, R)."""
        if self._cover is not None:
            return self._cover
        s = self.s
        movers = min(2, s.tok_x) if not self.o_to_act or True else 0
        R = {j: self.responses(j) for j in self.att_x}
        threats = list(self.att_o)
        base = {i: self.threat[i]['value'] for i in threats}
        # minimise the best uncovered threat (the offence needs only one open look); among equal covers, the one that
        # leaves the least threat in total (so a defender still answers the lesser threats)
        key0 = (round(max(base.values(), default=0.0), 6), round(sum(base.values()), 6))
        best = [key0, {}, dict(base)]
        opts = [(j, idx) for j in self.att_x for idx in range(1, len(R[j]))]

        def score(chosen):
            res = {}
            for i in threats:
                v = base[i]
                for j, idx in chosen:
                    lv = R[j][idx][1][i]
                    if lv < v:
                        v = lv
                res[i] = v
            return (round(max(res.values(), default=0.0), 6), round(sum(res.values()), 6)), res
        for a in range(len(opts)):
            ch = [opts[a]]
            k, res = score(ch)
            if k < best[0]:
                best = [k, {j: R[j][idx][0] for j, idx in ch}, res]
            if movers >= 2:
                for b in range(a + 1, len(opts)):
                    if opts[b][0] == opts[a][0]:
                        continue
                    ch2 = ch + [opts[b]]
                    k, res = score(ch2)
                    if k < best[0]:
                        best = [k, {j: R[j][idx][0] for j, idx in ch2}, res]
        self._cover = dict(value=best[0][0], choice=best[1], residual=best[2], R=R)
        return self._cover

    def overloads(self):
        """Overloaded defenders: Xj is the only defender whose responses reduce each of two threats, and none of his
        responses reduces both. Dilemma(j; a, b) = min(residual without j (a), (b)): the threat he must concede."""
        cv = self.cover()
        R = cv['R']
        out = []
        base = {i: self.threat[i]['value'] for i in self.att_o}
        threats = [i for i in self.att_o if base[i] > 0]
        reducers = {i: [j for j in self.att_x if any(left[i] < base[i] - 1e-9 for _, left in R[j][1:])] for i in threats}
        for j in self.att_x:
            only = [i for i in threats if reducers[i] == [j]]
            for x in range(len(only)):
                for y in range(x + 1, len(only)):
                    a, b = only[x], only[y]
                    both = any(left[a] < base[a] - 1e-9 and left[b] < base[b] - 1e-9 for _, left in R[j][1:])
                    if not both:
                        out.append(dict(defender=j, a=a, b=b, value=min(base[a], base[b])))
        out.sort(key=lambda o: -o['value'])
        return out

    def hinges(self):
        """Hinge defenders (addendum B3): the only defender who reduces two threats, and one of his responses
        reduces both. Not a dilemma: the defence's key piece, and a target for the offence."""
        cv = self.cover()
        R = cv['R']
        base = {i: self.threat[i]['value'] for i in self.att_o}
        threats = [i for i in self.att_o if base[i] > 0]
        reducers = {i: [j for j in self.att_x if any(left[i] < base[i] - 1e-9 for _, left in R[j][1:])] for i in threats}
        out = []
        for j in self.att_x:
            only = [i for i in threats if reducers[i] == [j]]
            for x in range(len(only)):
                for y in range(x + 1, len(only)):
                    a, b = only[x], only[y]
                    if any(left[a] < base[a] - 1e-9 and left[b] < base[b] - 1e-9 for _, left in R[j][1:]):
                        out.append(dict(defender=j, a=a, b=b, value=min(base[a], base[b])))
        return out

    def gravity(self, i):
        """Attacker i's gravity: the change in the best uncovered threat among the other attackers when i is
        replaced by an inert body on his square (his looks removed; the cover re-solved)."""
        cv = self.cover()
        others = [k for k in self.att_o if k != i]
        with_i = max((cv['residual'][k] for k in others), default=0.0)
        inert = Read.__new__(Read)
        inert.__dict__.update(self.__dict__)
        inert.att_o = others
        inert.looks = {k: self.looks[k] for k in others}
        inert.threat = {k: self.threat[k] for k in others}
        inert._cover = None
        without = inert.cover()['value']
        return without - with_i

    # -- value (B4)
    def shot_now(self):
        """The carrier's shot declared now, against the reaction, or None if he can't shoot now."""
        if not self.o_to_act:
            return None
        for lk in self.looks.get(self.s.ball, []):
            if lk.route == 'shoot':
                return lk.base
        return None

    # ---- step 18s, stop two (eval.map, off until its checks pass): the search reads the coverage map ----
    def map_options(self):
        """The coverage map in its lean form (engine.js covBuild, lean): for every attacker and every square he could
        shoot from next phase, the chance he has the ball where he needs it when the phase starts (reach) and what the
        defence leaves of the shot, each defender given the reaction's two actions from where he stands (weakness).
        {(attacker, square, rushed): [reach, weakness, worth, the look, each type's open value, each defender's
        contest of it]}; empty in the last phase."""
        s, rules = self.s, self.rules
        out = {}
        if s.clock <= RC.PHASE_SECONDS:
            return out
        from .actions import movement_dests, can_move_kind, capture_lines, capture_ok
        no_rim = RC.rim_shot_barred(rules)
        xat = {s.x[j]: j for j in range(5) if B.on_board(s.x[j])}
        # the board as the next phase finds it if nobody moves again (resolve.new_phase): the defence's movement fresh,
        # no zone broken, no screen standing
        from .state import ZERO_COUNTS
        s_next = s.with_(screens=(), tok_x=RC.TOKENS_PER_PHASE, moved_x=0, qs_x=0, lock_x=0, rush_x=0, beaten=(), cnt=ZERO_COUNTS)
        mode = 0 if rules.zone == 'off' else 1
        cms = [(_body_cmap2(s_next, d, mode) if B.on_board(s.x[d]) else None) for d in range(5)]      # step 26 (D-249): the real paths
        self._mcms = cms
        off = RC.control_cut(rules) if RC.control_size(rules) > 0 else 0
        # ---- step 22c (engine.js covBuild, D-224): stagnation, in points by the rules ----
        # The Steal as the defence stands (a defender next to the square with an arrow on it, or one a Move takes next
        # to it): kept on Dribble less Steal or under, else -5; a foul is +5 (D-198). Never counted above 0.
        from .resolve import ppo
        from .scoring import foul_rolls
        from .actions import stance as _stance, closely_guarded
        steal_on = ppo(s) and s.tok_x >= 1 and s.count('X', 'steal') < RC.LIMITS['X']['steal']
        mv1 = [None] * 5
        if steal_on and s.tok_x >= 2:
            for j in range(5):
                if B.on_board(s.x[j]) and _caps(s, 'X', j)[0]:
                    mv1[j] = defender_map(s, j, exact=True)[0]
        sev, sat = {}, {}

        def steal_ev(a, j, rolls, via_move):
            key = (a, j, rolls, via_move)
            if key not in sev:
                pf = float(p_foul(s.ctx.dfn[j].r['foul_steal'], rules))
                foul = 1 - (1 - pf) * (1 - pf) if rolls == 2 else pf
                tk = rolled(s, 'O', a, 'dribble') - (s.ctx.dfn[j].r['steal'] if via_move else rolled(s, 'X', j, 'steal'))
                sev[key] = 5 * foul - 5 * (1 - foul) * (1 - float(p_success(tk, rules)))
            return sev[key]

        def steal_at(a, q):
            if not steal_on:
                return 0.0
            if (a, q) not in sat:
                best_ = 0.0
                for j in range(5):
                    xp = s.x[j]
                    if not B.on_board(xp):
                        continue
                    if B.adjacent(xp, q) and B.dir_between(xp, q) in G.lines(rules, _stance(s, j)):
                        v = steal_ev(a, j, foul_rolls(rules, xp, q), False)
                        if v < best_:
                            best_ = v
                    fr = mv1[j]
                    if fr:
                        for dx, dy in B.DIRS:
                            p2 = (q[0] + dx, q[1] + dy)
                            if fr.get(p2) == 1:
                                v = steal_ev(a, j, foul_rolls(rules, p2, q), True)
                                if v < best_:
                                    best_ = v
                sat[a, q] = best_
            return sat[a, q]
        # the closely guarded count (D-173): holding where he stands, closely guarded at the phase end, is one phase
        # end nearer the -5: counted at how far along the count's three that puts him
        guard_now = (RC.app_rule(rules, 'closely_guarded') and (s.grd & 3) != 1 and B.on_board(s.o[s.ball]) and closely_guarded(s))
        # step 27 (engine.js guardAt, D-256): the full -5 only when the count falls at this phase end, else nothing
        guard_cost = -5.0 if guard_now and ((s.grd >> 2) & 3) + 1 >= RC.GUARDED_ENDS else 0.0
        three_on = RC.app_rule(rules, 'three_seconds')
        psq, pf_memo = [], {}
        bq = s.o[s.ball]
        if B.on_board(bq) and s.tok_o >= 2 and s.count('O', 'pass') < RC.LIMITS['O']['pass']:
            seen = {bq}
            for kind in ('move', 'qs', 'sprint'):
                if can_move_kind(s, 'O', s.ball, kind):
                    for q in movement_dests(s, 'O', s.ball, kind, rules):
                        if q not in seen:
                            seen.add(q)
                            psq.append(q)
        psq.sort(key=lambda q: (q[0] + 2) * 64 + (q[1] + 2))        # engine.js C(x, y) order

        def passer_squares():
            return psq

        def pass_from(pq, a, q):
            k = (pq, a, q)
            if k not in pf_memo:
                pf_memo[k] = cov_pass(s.with_(o=tuple(pq if i == s.ball else z for i, z in enumerate(s.o))), a, q)
            return pf_memo[k]
        for a in range(5):
            home = s.o[a]
            if not B.on_board(home):
                continue
            starts = []                            # where he can have the ball when the next phase starts, and the chance
            if a == s.ball:
                one = {home: 0}
                if s.tok_o > 0:
                    for kind in ('move', 'qs', 'sprint'):
                        if can_move_kind(s, 'O', a, kind):
                            for q in movement_dests(s, 'O', a, kind, rules):
                                one.setdefault(q, 1)
                for q in list(one) + (two_actions(s, a, one) if s.tok_o > 0 else []):
                    starts.append((q, 1.0, False, one.get(q, 2), False))
                # step 22b (engine.js covBuild, D-218): a wall he can only pass by winning a Dribble, at its chance
                if s.tok_o >= 2 and self._dribble_ok()[0]:
                    for j in range(5):
                        if not B.on_board(s.x[j]) or not B.adjacent(s.x[j], home) or any(b[1] == j for b in s.beaten):
                            continue
                        p = self._beat_chance(j)
                        if not p > 0:
                            continue
                        sb = s.with_(beaten=tuple(s.beaten) + ((a, j),))
                        for kind in ('move', 'qs', 'sprint'):
                            if can_move_kind(sb, 'O', a, kind):
                                for q in movement_dests(sb, 'O', a, kind, rules):
                                    if q not in one:
                                        starts.append((q, p, False, 2, True))
            elif s.tok_o > 0 and s.count('O', 'pass') < RC.LIMITS['O']['pass']:
                # step 22 (engine.js covBuild, D-210): a receiver two movements away (his cut) catches and shoots there
                for q, n in attacker_reach(s, a).items():
                    if n > 2 or n + 1 > s.tok_o:
                        continue
                    p = cov_pass(s, a, q)
                    p0 = p                                  # step 31: from where he stands (the fall-back after a lost Dribble)
                    # step 26 (engine.js covBuild, D-250): from every square the ball handler can reach this turn
                    if p < 1 and n + 2 <= s.tok_o:
                        for pq in passer_squares():
                            if pq == q:
                                continue
                            p2 = pass_from(pq, a, q)
                            if p2 > p:
                                p = p2
                            if p >= 1:
                                break
                    if p > 0:
                        starts.append((q, p, n == 2, n + 1, False, p0))      # (n0, step 22b: his movements and the pass)
            mates = {s.o[k] for k in range(5) if k != a}
            lines = capture_lines(s_next, a) if rules.zone != 'off' else []
            card, qs = s.ctx.off[a], s.ctx.off[a].qs
            best, start, acts, drb, p0s = {}, {}, {}, {}, {}
            for st_ in starts:
                q0, pr, set_only, n0, dr = st_[:5]
                p0 = st_[5] if len(st_) > 5 else 0
                if q0 in mates or (q0 != home and q0 in xat):
                    continue
                # step 22c: what holding the ball there costs him (0 or less); of two ways as likely, the one that costs less
                # D-273: a pivot after the pick-up doesn't stop the closely guarded count: it runs on at his pivot square
                adj = steal_at(a, q0) + (guard_cost if (a == s.ball and ((q0 == home and n0 == 0) or (s.picked_up() and n0 == 1)))
                                         else 0.0)
                if three_on and B.in_key(q0) and (s.key_o >> a) & 1:     # step 27 (engine.js keyAt, D-255): by the rule
                    adj += -5.0
                if shot_zone(s.ctx, q0) in RC.ZONE_POINTS and not (no_rim and q0 == RC.RIM):
                    b = best.get((q0, False))
                    if b is None or pr > b[0] or (pr == b[0] and adj > b[1]):
                        best[q0, False] = (pr, adj)    # a set shot from where the phase finds him
                        start[q0, False] = q0
                        acts[q0, False] = n0
                        drb[q0, False] = dr
                        p0s[q0, False] = p0
                if set_only:
                    continue
                for p, rushed in _shot_paths(q0, qs, rules, no_rim, RC.deep_open(s.ctx)):
                    c = p[-1]
                    b = best.get((c, rushed))
                    if b is not None and (b[0] > pr or (b[0] == pr and b[1] >= adj)):
                        continue
                    if any(q in mates or q in xat for q in p):
                        continue
                    if lines and not capture_ok(q0, p, lines):
                        continue
                    best[c, rushed] = (pr, adj)
                    start[c, rushed] = q0
                    acts[c, rushed] = n0
                    drb[c, rushed] = dr
                    p0s[c, rushed] = p0
            for (c, rushed), (pr, adj) in best.items():
                z = shot_zone(s.ctx, c)
                lk = Look(a, c, 'later', 1.0, False)
                lk.types = RC.ZONE_SHOTS[z]
                lk.rushed = rushed
                pts = RC.ZONE_POINTS[z]
                vals = [None] * 5
                for d in range(5):
                    vals[d] = self._vals_map(lk, d, cms[d].get(c)) if cms[d] is not None else None
                opens = [pts * (card_shot(s.ctx, card, ty, c) - (off if rushed else 0)) for ty in lk.types]
                top = self._map_weak(lk, opens, vals)
                lc = 0 if drb[c, rushed] else 5     # what not getting there costs: a lost pass -5, a lost Dribble nothing
                out[a, c, rushed] = [pr, top, pr * (top + adj) - (1 - pr) * lc, lk, opens, vals, start[c, rushed], acts[c, rushed], lc, adj, p0s[c, rushed]]
        return out

    @staticmethod
    def _map_weak(lk, opens, vals, d=-1, mine=None):
        """What the defence leaves of a look: its best type, each against the best Contest of every defender (defender
        d's taken from `mine`)."""
        top = -1.0
        for n, ty in enumerate(lk.types):
            v = opens[n]
            for j in range(5):
                vd = mine if j == d else vals[j]
                if vd and ty in vd and vd[ty] < opens[n] and vd[ty] < v:
                    v = vd[ty]
            if v > top:
                top = v
        return top

    def map_answers(self, opts):
        """engine.js covLeanAnswers: the defence's answers in a fast form. While it has tokens, one defender makes the
        one movement this phase that takes something off the offence's best option and leaves its best six the
        smallest, the largest first; he then contests everything from where he now stands. Each defender moves once.
        Changes opts in place; -> the number of answers."""
        s, rules = self.s, self.rules
        if s.tok_x <= 0:
            return 0
        K = 6
        taken = set(s.o) | set(s.x)
        moved = [False] * 5
        tok, steps = s.tok_x, 0
        mode = 0 if rules.zone == 'off' else 1

        def less(x, y):
            for u, v in zip(x, y):
                if u < v - 1e-9:
                    return True
                if u > v + 1e-9:
                    return False
            return False
        while tok > 0:
            head = sorted((key for key, o in opts.items() if o[0] > 0), key=lambda key: (-opts[key][2], key))[:K]
            if not head or opts[head[0]][2] <= 0:
                break
            cur = [opts[key][2] for key in head]
            c0 = head[0][1]
            best = None
            for d in range(5):
                if moved[d] or not B.on_board(s.x[d]):
                    continue
                can_move, qs_left = _caps(s, 'X', d)
                if not can_move and qs_left <= 0:
                    continue
                qs = s.ctx.dfn[d].qs
                free, fixed = defender_map(s, d, exact=True)
                cands = [(q, -1) for q, n in free.items() if n == 1]
                cands += [(q, a) for q, arrs in fixed.items() for a, n in arrs.items() if n == 1]
                for q, a in cands:
                    if q in taken:
                        continue
                    cm = _any_arrow_cmap2(rules, q, qs, mode) if a < 0 else _cmap2(rules, q, a, qs, mode)
                    if cm.get(c0) is None or not cm[c0][2]:
                        continue
                    after = []
                    for n, key in enumerate(head):
                        pr, _, e0, lk, opens, vals = opts[key][:6]
                        if key[1] == q:
                            e = float('-inf')
                        else:
                            mine = self._vals_map(lk, d, cm.get(key[1]))
                            e = pr * (self._map_weak(lk, opens, vals, d, mine) + opts[key][9]) - (1 - pr) * opts[key][8]
                        if n == 0 and not e < e0 - 1e-9:
                            after = None
                            break
                        after.append(e)
                    if after is None:
                        continue
                    after.sort(reverse=True)
                    if best is None or less(after, best[0]) or (not less(best[0], after) and (d, q, a) < best[1:]):
                        best = (after, d, q, a)
            if best is None or not less(best[0], cur):
                break
            _, d, q, a = best
            qs = s.ctx.dfn[d].qs
            cm = _any_arrow_cmap2(rules, q, qs, mode) if a < 0 else _cmap2(rules, q, a, qs, mode)
            moved[d] = True
            tok -= 1
            steps += 1
            taken.add(q)
            for key, o in opts.items():
                if key[1] == q:
                    o[0], o[2] = 0.0, float('-inf')
                    continue
                o[5][d] = self._vals_map(o[3], d, cm.get(key[1]))
                o[1] = self._map_weak(o[3], o[4], o[5])
                o[2] = o[0] * (o[1] + o[9]) - (1 - o[0]) * o[8] if o[0] > 0 else float('-inf')
        return steps

    # ---- step 20 (Shaun, 17 Nov 2026): the lasting gap (engine.js lasting, lastingOf) ----
    @staticmethod
    def _map_cov(lk, opens, vals, d=-1, mine=None):
        """engine.js covValue: (what the defence leaves of a look, its best type's index, the defender who takes most off
        it, the next one), defender d's contest taken from `mine` (None: read without him)."""
        top, tt, cov, nxt, ob, cb, nb = -1.0, 0, -1, -1, -1.0, -1, -1
        for n, ty in enumerate(lk.types):
            v, d1, v2, d2 = opens[n], -1, opens[n], -1
            for j in range(5):
                vd = mine if j == d else vals[j]
                if not vd or ty not in vd or not vd[ty] < opens[n]:
                    continue
                x = vd[ty]
                if x < v:
                    v2, d2, v, d1 = v, d1, x, j
                elif x < v2:
                    v2, d2 = x, j
            if v > top:
                top, tt, cov, nxt = v, n, d1, d2
            if opens[n] > ob:
                ob, cb, nb = opens[n], d1, d2
        if cov < 0 and top < ob:
            cov, nxt = cb, nb
        return top, tt, cov, nxt

    def lasting(self, opts):
        """engine.js lasting: the defence's best answer by a beam search over its real options (each defender at most one
        movement: a Move with any arrow, turning on the spot included; a Quick Step or Sprint with the arrow it leaves
        him), ranked by the lasting gap and then the threats left, the largest first. -> the best answer's state:
        {moves, L, worths, ov, o}."""
        import functools
        s, rules = self.s, self.rules
        BEAM, WIDE, HEAD = 3, 3, 6
        mode = 0 if rules.zone == 'off' else 1
        inf = float('-inf')

        def less(x, y):
            for k in range(max(len(x), len(y))):
                u = x[k] if k < len(x) else inf
                v = y[k] if k < len(y) else inf
                if u < v - 1e-9:
                    return True
                if u > v + 1e-9:
                    return False
            return False
        root = self._lg_root(opts)

        def head_of(st):
            return sorted((x for x in st['o'] if x['r'] > 0), key=lambda x: (-x['e'], x['key']))[:HEAD]

        def overloads(st):
            """engine.js lgOverloads (step 21): groups of one, two or three defenders who are the only cover for looks
            from more attackers than there are defenders; worth the best look the defence's best assignment leaves."""
            looks = []
            for x in st['o']:
                if not x['r'] > 0 or not x['e'] > 0:
                    continue
                lk, opens = x['src'][3], x['src'][4]
                mask = 0
                for d in range(5):
                    vd = x['vals'][d]
                    if vd and any(ty in vd and vd[ty] < opens[n] for n, ty in enumerate(lk.types)):
                        mask |= 1 << d
                if not mask:
                    continue
                top, tt = float('-inf'), 0
                for n, o in enumerate(opens):
                    if o > top:
                        top, tt = o, n
                looks.append(dict(x=x, mask=mask, wd=x['r'] * (top + x['src'][9]) - (1 - x['r']) * x['src'][8], tt=tt))

            return cover_groups(covers_too_of(s), [dict(a=z['x']['key'][0], c=z['x']['key'][1], t=z['tt'], wd=z['wd'], now=z['x']['e'], mask=z['mask'],
                                      order=(-z['x']['e'], z['x']['key'])) for z in looks])

        def score(st):
            head = head_of(st)
            worths = [x['e'] for x in head]
            open0 = worths[0] if worths else 0.0
            ov = [v for v in overloads(st) if len(v['ds']) == 1 or v['value'] >= open0 - 1e-9]
            L = worths[0] if worths else 0.0
            for v in ov:
                if v['value'] > L:
                    L = v['value']
            st['L'], st['worths'], st['ov'] = L, worths, ov

        def better(a, b):
            """engine.js lgBetter (step 22b, D-219): the list (what it leaves uncovered as it then stands, largest
            first); then the lasting gap; then efficiency, the fewest actions; then the moves' own order. Step 28 (D-262,
            Shaun, 19 Nov 2026): the list leads here too, as everywhere; eval.answer_lead 'gap' puts the lasting gap first."""
            la, lb = self._lg_list(a), self._lg_list(b)
            if gap_first:
                if a['L'] < b['L'] - 1e-9:
                    return True
                if a['L'] > b['L'] + 1e-9:
                    return False
            if less(la, lb):
                return True
            if less(lb, la):
                return False
            if a['L'] < b['L'] - 1e-9:
                return True
            if a['L'] > b['L'] + 1e-9:
                return False
            if len(a['moves']) != len(b['moves']):
                return len(a['moves']) < len(b['moves'])
            for ma, mb in zip(a['moves'], b['moves']):
                ka, kb = (ma[1], ma[2], s.x[ma[0]]), (mb[1], mb[2], s.x[mb[0]])
                if ka != kb:
                    return ka < kb
            return False
        gap_first = (self.cfg or {}).get('answer_lead') == 'gap'
        cmp = lambda u, v: -1 if better(u, v) else 1 if better(v, u) else 0
        score(root)
        best, frontier = root, [root]
        for _depth in range(5):
            if not frontier:
                break
            nexts = []
            for st in frontier:
                if st['tok'] <= 0:
                    continue
                head = head_of(st)
                cur = [x['e'] for x in head]
                if not head or not head[0]['e'] > 0:
                    continue
                cands, seen = [], set()

                def offer(d, q, a, cm):
                    if (d, q, a) in seen:
                        return
                    seen.add((d, q, a))
                    after, touched = [], False
                    for x in head:
                        if x['key'][1] == q:
                            e = inf
                        else:
                            mine = self._vals_map(x['src'][3], d, cm.get(x['key'][1]))
                            e = x['r'] * (self._map_cov(x['src'][3], x['src'][4], x['vals'], d, mine)[0] + x['src'][9]) - (1 - x['r']) * x['src'][8]
                        if e < x['e'] - 1e-9:
                            touched = True
                        after.append(e)
                    if not touched:
                        return
                    after.sort(reverse=True)
                    if less(after, cur):
                        cands.append(dict(d=d, q=q, a=a, cm=cm, after=after))
                for d in range(5):
                    if st['moved'][d] or not B.on_board(s.x[d]):
                        continue
                    can_move, qs_left = _caps(s, 'X', d)
                    if not can_move and qs_left <= 0:
                        continue
                    qs = s.ctx.dfn[d].qs
                    free, fixed = defender_map(s, d, exact=True)
                    if can_move:                       # a Move on the spot: a new arrow
                        offer(d, s.x[d], -1, _any_arrow_cmap2(rules, s.x[d], qs, mode))
                    for q, n in free.items():
                        if n == 1 and q not in st['taken']:
                            offer(d, q, -1, _any_arrow_cmap2(rules, q, qs, mode))
                    for q, arrs in fixed.items():
                        if q in st['taken']:
                            continue
                        for a, n in arrs.items():
                            if n == 1:
                                offer(d, q, a, _cmap2(rules, q, a, qs, mode))

                def ccmp(u, v):
                    if less(u['after'], v['after']):
                        return -1
                    if less(v['after'], u['after']):
                        return 1
                    ku, kv = (u['q'], u['a'], s.x[u['d']]), (v['q'], v['a'], s.x[v['d']])    # (never the defender's number, D-219)
                    return -1 if ku < kv else 1 if ku > kv else 0
                cands.sort(key=functools.cmp_to_key(ccmp))
                for c in cands[:WIDE]:
                    ch = self._lg_child(st, c['d'], c['q'], c['a'], c['cm'])
                    score(ch)
                    nexts.append(ch)
            if not nexts:
                break
            nexts.sort(key=functools.cmp_to_key(cmp))
            frontier = nexts[:BEAM]
            if better(frontier[0], best):
                best = frontier[0]
        best['root'] = root
        return best

    # ---- step 22b, continued (D-218 to D-222, Shaun, 18 Nov 2026): the defence's two responsibilities (engine.js) ----
    def _lg_root(self, opts):
        """engine.js lgRoot: the map as it stands, as a state the answers and the settlement work on."""
        s = self.s
        o = []
        for key in sorted(opts):
            src = opts[key]
            if not src[0] > 0:
                continue
            top, tt, cov, nxt = self._map_cov(src[3], src[4], src[5])
            o.append(dict(key=key, src=src, r=src[0], vals=list(src[5]), e=src[2], w=top, t=tt, cover=cov, next=nxt))
        return dict(moves=[], moved=[False] * 5, taken=set(s.o) | set(s.x), tok=s.tok_x, o=o, cms=list(self._mcms), xs=list(s.x))

    def _lg_child(self, st, d, q, a, cm):
        """engine.js lgChild: the state with defender d on q (his Contest from there cm)."""
        inf = float('-inf')
        o2 = []
        for x in st['o']:
            y = dict(x)
            y['vals'] = list(x['vals'])
            if x['key'][1] == q:
                y['r'], y['e'] = 0.0, inf
                o2.append(y)
                continue
            y['vals'][d] = self._vals_map(x['src'][3], d, cm.get(x['key'][1]))
            y['w'], y['t'], y['cover'], y['next'] = self._map_cov(x['src'][3], x['src'][4], y['vals'])
            y['e'] = y['r'] * (y['w'] + x['src'][9]) - (1 - y['r']) * x['src'][8] if y['r'] > 0 else inf
            o2.append(y)
        moved = list(st['moved'])
        moved[d] = True
        cms = list(st['cms'])
        cms[d] = cm
        xs = list(st['xs'])
        xs[d] = q
        return dict(moves=st['moves'] + [(d, q, a)], moved=moved, taken=st['taken'] | {q}, tok=st['tok'] - 1, o=o2, cms=cms, xs=xs)

    # Step 22c (D-228, Shaun, 18 Nov 2026): zone gaps are a race (engine.js gapInfo, gapLate, gapRace, gapVec). A
    # square is a gap only when an attacker can get there with the ball before any defender can arrive to contest it
    # set. The phases each side needs are counted by the rules' movement, over as many phases as the race takes, up
    # to the shot clock. Its value is that attacker's shot there at his real chance of having the ball (a pass by the
    # rules' chance as the defence stands), less the contest of any defender who arrives in time off balance. A square
    # every attacker loses the race to is not a gap, however valuable.
    def _gap_info(self):
        """engine.js gapInfo: every square a shot may go up from; each attacker's look there and its open value."""
        ctx = self.s.ctx
        g = _GAP.get(ctx)
        if g is None:
            no_rim = RC.rim_shot_barred(self.rules)
            sq = [q for q in ((x, y) for x in range(B.W) for y in range(1, B.H + 1))
                  if shot_zone(ctx, q) in RC.ZONE_POINTS and not (no_rim and q == RC.RIM)]
            looks, opens = [], []
            for q in sq:
                z = shot_zone(ctx, q)
                pts, types = RC.ZONE_POINTS[z], RC.ZONE_SHOTS[z]
                row, op = [], []
                for a in range(5):
                    lk = Look(a, q, 'later', 1.0, False)
                    lk.types = types
                    lk.rushed = False
                    row.append(lk)
                    op.append(max(pts * card_shot(ctx, ctx.off[a], ty, q) for ty in types))
                looks.append(row)
                opens.append(op)
            if len(_GAP) > 8:
                _GAP.clear()
            g = _GAP[ctx] = dict(sq=sq, looks=looks, open=opens, late={}, idx={q: k for k, q in enumerate(sq)})
        return g

    def _gap_late(self, g, k, a, d):
        """engine.js gapLate: attacker a's shot on square k with defender d's hand up off balance."""
        key = (k, a, d)
        v = g['late'].get(key)
        if v is None:
            lk = g['looks'][k][a]
            pts = RC.ZONE_POINTS[shot_zone(self.s.ctx, g['sq'][k])]
            vals = self._vals2(lk, d, _LATE_ROW, _NOSET) or {}
            card = self.s.ctx.off[a]
            v = None
            for ty in lk.types:
                o = pts * card_shot(self.s.ctx, card, ty, g['sq'][k])
                w = vals[ty] if ty in vals and vals[ty] < o else o
                if v is None or w > v:
                    v = w
            g['late'][key] = v
        return v

    def _gap_race(self):
        """engine.js gapRace: the offence's side of the race: each attacker's phases to every square, the phases the
        shot clock leaves, the chance a pass finds him there (as the defence stands)."""
        r = getattr(self, '_race', None)
        if r is None:
            s = self.s
            r = self._race = dict(n=s.clock // RC.PHASE_SECONDS - 1, ch={},
                                  A=[(_phase_dist(self.rules, s.o[a], s.ctx.off[a].qs) if B.on_board(s.o[a]) else None) for a in range(5)])
        return r

    def _gap_vec(self, st, d2=None, q2=None):
        """engine.js gapVec: every square's gap, the defence as the state has it (d2 on q2 instead, where given)."""
        s, rules = self.s, self.rules
        g, R = self._gap_info(), self._gap_race()
        mode = 0 if rules.zone == 'off' else 1
        xs = [q2 if d == d2 else st['xs'][d] for d in range(5)]
        ap = [(_arrive(rules, xs[d], s.ctx.dfn[d].qs, mode) if B.on_board(xs[d]) else None) for d in range(5)]
        on = set(xs)
        n, A, chs, opens = R['n'], R['A'], R['ch'], g['open']
        out = []
        for k, q in enumerate(g['sq']):
            if q in on:
                out.append(0.0)
                continue
            setp = INF
            for z in ap:
                if z is not None:
                    v = z[0].get(q, INF)
                    if v < setp:
                        setp = v
            best = 0.0
            for a in range(5):
                if A[a] is None:
                    continue
                t = A[a].get(q, INF)
                if t < 1:
                    t = 1                               # (on it already: he shoots as the next phase starts)
                if t > n or setp <= t:
                    continue                            # the clock runs out first, or a defender is set there in time
                w = opens[k][a]
                if not w > best:
                    continue
                for d in range(5):
                    if ap[d] is not None and ap[d][1].get(q, INF) <= t:
                        u = self._gap_late(g, k, a, d)
                        if u < w:
                            w = u
                ch = 1.0
                if a != s.ball:
                    ch = chs.get((a, q))
                    if ch is None:
                        ch = chs[(a, q)] = cov_pass(s, a, q)
                if not ch > 0:
                    continue
                e = ch * w - (1 - ch) * 5.0
                if e > best:
                    best = e
            out.append(best)
        return out

    def _lg_list(self, st):
        """engine.js lgList: the one list of things to cover: each attacker's best look as the defence stands and
        every square's gap, largest first."""
        if 'list' not in st:
            thr = [0.0] * 5
            for x in st['o']:
                if x['r'] > 0 and x['e'] > thr[x['key'][0]]:
                    thr[x['key'][0]] = x['e']
            gv = self._gap_vec(st)
            st['thr'], st['gaps'] = thr, gv
            st['list'] = sorted(thr + gv, reverse=True)
        return st['list']

    def settle_moves(self, opts):
        """engine.js settleMoves (items 3 and 4): the one or two movements of this defence turn that leave the least
        on the list, by the quick re-read: the most valuable uncovered item is claimed first, by whoever covers it
        best; then the next. Only the movement each defender has left, one each, within the tokens. -> [(d, q, arrow or
        -1 for a Move)]."""
        s, rules = self.s, self.rules
        mode = 0 if rules.zone == 'off' else 1
        inf = float('-inf')

        def less(x, y):
            for k in range(max(len(x), len(y))):
                u = x[k] if k < len(x) else inf
                v = y[k] if k < len(y) else inf
                if u < v - 1e-9:
                    return True
                if u > v + 1e-9:
                    return False
            return False
        out = []
        st = self._lg_root(opts)
        for _round in range(2):
            if st['tok'] <= 0:
                break
            base = self._lg_list(st)
            thr, gaps = st['thr'], st['gaps']
            by_a = [[] for _ in range(5)]
            for x in st['o']:
                if x['r'] > 0:
                    by_a[x['key'][0]].append(x)
            split = {}

            def split_of(d):
                if d not in split:
                    free, held = [], []
                    for a in range(5):
                        f, h = [], []
                        for x in by_a[a]:
                            if x['vals'][d]:
                                ewo = x['r'] * (self._map_cov(x['src'][3], x['src'][4], x['vals'], d, None)[0] + x['src'][9]) - (1 - x['r']) * x['src'][8]
                                h.append((ewo, x))
                            else:
                                f.append(x)
                        f.sort(key=lambda x: -x['e'])
                        h.sort(key=lambda z: -z[0])
                        free.append(f)
                        held.append(h)
                    split[d] = (free, held)
                return split[d]

            def threat(a, d, q, cm):
                free, held = split_of(d)

                def re(x):
                    mine = self._vals_map(x['src'][3], d, cm.get(x['key'][1]))
                    return x['r'] * (self._map_cov(x['src'][3], x['src'][4], x['vals'], d, mine)[0] + x['src'][9]) - (1 - x['r']) * x['src'][8]
                best = 0.0
                for x in free[a]:
                    if x['e'] <= best:
                        break
                    c = x['key'][1]
                    if c == q:
                        continue
                    pair = cm.get(c)
                    if pair is None or not pair[2]:
                        best = x['e']
                        break
                    e = re(x)
                    if e > best:
                        best = e
                for ewo, x in held[a]:
                    if ewo <= best:
                        break
                    c = x['key'][1]
                    if c == q:
                        continue
                    pair = cm.get(c)
                    e = re(x) if (pair is not None and pair[2]) else ewo
                    if e > best:
                        best = e
                return best

            def qlist(d, q, cm):
                rem, add = [], []
                for a in range(5):
                    t = threat(a, d, q, cm)
                    if abs(t - thr[a]) > 1e-9:
                        rem.append(thr[a])
                        add.append(t)
                gv = self._gap_vec(st, d, q)             # the race for every square, run again with him there
                for k, v in enumerate(gv):
                    if abs(v - gaps[k]) > 1e-9:
                        rem.append(gaps[k])
                        add.append(v)
                if not rem:
                    return base
                lst = list(base)
                for v in rem:
                    lst.remove(v)
                lst.extend(add)
                lst.sort(reverse=True)
                return lst
            best = None
            for d in range(5):
                if st['moved'][d] or not B.on_board(s.x[d]):
                    continue
                can_move, qs_left = _caps(s, 'X', d)
                if not can_move and qs_left <= 0:
                    continue
                qs = s.ctx.dfn[d].qs
                free, fixed = defender_map(s, d, exact=True)
                cands = []
                if can_move:
                    cands.append((s.x[d], -1, _any_arrow_cmap2(rules, s.x[d], qs, mode)))
                for q, n in free.items():
                    if n == 1 and q not in st['taken']:
                        cands.append((q, -1, _any_arrow_cmap2(rules, q, qs, mode)))
                for q, arrs in fixed.items():
                    if q in st['taken']:
                        continue
                    for a, n in arrs.items():
                        if n == 1:
                            cands.append((q, a, _cmap2(rules, q, a, qs, mode)))
                for q, a, cm in cands:
                    lst = qlist(d, q, cm)
                    if lst is base or not less(lst, base):
                        continue
                    if best is not None:
                        if less(best[4], lst):
                            continue
                        if not less(lst, best[4]):       # level: a Move first, then the lower square, arrow, starting square
                            if not (0 if a < 0 else 1, q, a, s.x[d]) < (0 if best[2] < 0 else 1, best[1], best[2], s.x[best[0]]):
                                continue
                    best = (d, q, a, cm, lst)
            if best is None:
                break
            out.append((best[0], best[1], best[2]))
            st = self._lg_child(st, best[0], best[1], best[2], best[3])
        return out

    def map_lasting(self):
        """The lasting gap of this reading's position, read with what each side has left this phase (lasting_of, step 21);
        only the number and the answer's moves are kept."""
        if self._lg is None:
            g = lasting_of(self.s, self.cfg, r0=self)
            self._lg = (g['L'] if g else None, list(g['best']['moves']) if g and g.get('best') else [], map_threats(g))
        return self._lg[0]

    def map_top(self):
        """Step 22b (engine.js Read.mapTop): the largest item on the list as the defence stands (top_of)."""
        if getattr(self, '_top', False) is False:
            self._top = top_of(self.s, self.cfg)
        return self._top

    def map_threats(self):
        """Step 22: the map's threats as [(attacker, start square)] (the search's offence tries the moves that start them)."""
        self.map_lasting()
        return self._lg[2]

    def map_answer(self):
        """Step 21: the moves of the defence's best answer, [(defender, square, arrow or -1)] (the search tries them).
        Step 22b (D-219): and the settlement's own one or two movements."""
        self.map_lasting()
        if getattr(self, '_lg_all', None) is None:
            mv = list(self._lg[1])
            for z in self.map_settle():
                if z not in mv:
                    mv.append(z)
            self._lg_all = mv
        return self._lg_all

    def map_settle(self):
        """engine.js Read.mapSettle: the settlement's movements for this defence turn (settle_moves)."""
        if getattr(self, '_lg_settle', None) is None:
            s = self.s
            if s.stage != 'play' or s.clock <= RC.PHASE_SECONDS or s.pending:
                self._lg_settle = []
            else:
                r, opts = map_read(cov_off_fresh(s), self.cfg)
                self._lg_settle = r.settle_moves(opts)
        return self._lg_settle

    def map_two(self, answered=False):
        """The map's two numbers for the search: the best any attacker can have at the start of the next phase and the
        best a second, separate attacker can have; as the board stands, or after the defence's answers (map_answers)."""
        if self._map2 is None:
            self._map2 = dict(opts=self.map_options(), raw=None, ans=None)
        c = self._map2

        def two():
            mine = [0.0] * 5
            for (a, sq_, rushed), o in c['opts'].items():
                if o[0] > 0 and o[2] > mine[a]:
                    mine[a] = o[2]
            first = second = 0.0
            for v in mine:
                if v > first:
                    first, second = v, first
                elif v > second:
                    second = v
            return (first, second)
        if c['raw'] is None:
            c['raw'] = two()
        if not answered:
            return c['raw']
        if c['ans'] is None:
            self.map_answers(c['opts'])
            c['ans'] = two()
        return c['ans']

    def map_shot_or_none(self):
        """Step 31 (engine.js mapShotOrNone): the best shot that can go up now; None when none can."""
        now = self.shot_now()
        for i in self.att_o:
            for lk in self.looks[i]:
                if lk.now and (now is None or lk.base > now):
                    now = lk.base
        return now

    def map_shot(self):
        """The best shot that can go up now, as the reading has it."""
        now = 0.0
        for i in self.att_o:
            for lk in self.looks[i]:
                if lk.now and lk.base > now:
                    now = lk.base
        return max(self.shot_now() or 0.0, now)

    def _map_leaf(self):
        """Step 20 (Shaun, 17 Nov 2026), both sides: the reading from the map is what is banked, plus the larger of the best
        shot that can go up now and the lasting gap: what the offence can still force after the defence's best answer,
        read like for like. Used directly: it is in points, as a shot's value is. None: the map is off."""
        s = self.s
        # (the quick look that orders the list, k = 0, keeps its own reading: engine.js quickLeaf)
        on = self.cfg.get('map')                   # True: both sides; 'offence': only where the decision searched is the offence's
        if not (on is True or (on == 'offence' and MAP_ME[0] == 'O')) or self.k <= 0 or not s.ctx.rules.digital or s.stage != 'play':
            return None
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        if self.cfg.get('map_lead') == 'value':     # step 31 (D-284): the possession's value: the shot now, or playing on
            from .value import poss_value, OUT
            if s.pending:
                return banked + poss_value(s, self.cfg)
            sh = self.map_shot_or_none()
            return banked + max(OUT if sh is None else sh, poss_value(s, self.cfg))
        lead = self.cfg.get('map_lead') == 'list'   # step 22b (D-219): the list's largest item leads, or step 20's lasting gap
        if s.pending:                              # step 21: a pass in the air, by the rules' chance of the catch
            L = self.map_top() if lead else self.map_lasting()
            return None if L is None else banked + L
        shot = self.map_shot()
        if not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS:
            return banked + shot
        L = self.map_top() if lead else self.map_lasting()
        return banked + max(shot, L if L is not None else 0.0)

    def leaf(self):
        """The position's value at the search's horizon: today's hand-combined reading (_hand_leaf), or, with
        eval.calibrated on (step 17D), that reading passed through the map fitted to what positions went on to earn."""
        ml = self._map_leaf()
        if ml is not None:
            return ml
        v, s = self._hand_leaf(), self.s
        top = None
        if self.cfg.get('settle_shots') is True:
            # step 18b (D-145): no reading is above the most the possession can still earn, before or after the map
            banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
            banked += foul_externality(s)
            top = ceiling(s)
            if v - banked > top:
                v = banked + top
        w = learned_weights() if self.cfg.get('calibrated') is True and self.cfg.get('learned') is not True else None
        # the quicker reading that orders the list (k = 0) is mapped too when shots are settled, so that a settled shot
        # and a position that plays on are ranked on one scale (step 18b)
        if w is None or not w.get('calibration') or (self.k <= 0 and top is None) or s.stage != 'play' or s.pending or \
                (not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS):
            return v
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        po = play_on_map(s, self.cfg, w)
        if po is not None:
            # step 18h (eval.exact_shot): a shot that can go up now keeps its exact value; only "play on" is mapped
            sn = self.shot_now() or 0.0
            now = max((lk.base for i in self.att_o for lk in self.looks[i] if lk.now), default=0.0)
            rel = vcoarse(s) + self.continuation() - relative_average(s, self.cfg, self._budget_on())
            if top is not None and rel > top:
                rel = top
            r = max(sn, now, calibrate(po, s, self.o_to_act, rel))
            if top is not None and r > top:
                r = top
            return banked + r
        pm = parts_map(s, self.cfg, w)
        if pm is not None:
            # step 18h (eval.no_floor): the reading's parts, each kept, in place of the largest of them
            sn = self.shot_now() or 0.0
            now = max((lk.base for i in self.att_o for lk in self.looks[i] if lk.now), default=0.0)
            res = sorted((self.cover()['residual'][i] for i in self.att_o), reverse=True)
            r = parts_value(pm, s, self.o_to_act, max(sn, now), res[0] if res else 0.0, res[1] if len(res) > 1 else 0.0)
            if r is not None:
                if top is not None and r > top:
                    r = top
                return banked + r
        cal = calibration_for(s, self.cfg, w)           # D-141: the table's own map; step 18f: the looks reading's own
        r = calibrate(cal, s, self.o_to_act, v - banked)
        if top is not None and r > top:
            r = top
        return banked + r

    def _hand_leaf(self):
        """V_leaf from the offence's point of view (expected possession value, game units): the best of the shot
        now, the best look the defence can't cover in its next turn (released this turn: uncoverable), and the
        coarse table."""
        s = self.s
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        if s.pending:
            # a pass in the air: the catch (the receiver with the ball, the defence still to answer) weighted by the
            # chance it arrives, and the turnover
            passer, recv = s.pending
            p = _lane_p(s.with_(ball=passer), recv, s.o[recv])
            caught = Read(s.with_(ball=recv, pending=None), attention=None if len(self.att_o) == 5 else
                          (self.att_o, self.att_x), k=self.k, cfg=self.cfg, looks_per=self.L).leaf()
            return p * caught + (1 - p) * turnover_value(s)
        if self.cfg.get('learned') is True and self.k > 0 and s.stage == 'play' and learned_weights() is not None and \
                not (not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS):
            lv = learned_value(s, self.features())       # step 17: the learned judgement in place of the hand-combined one
            if lv is not None:
                return banked + lv
        sn = self.shot_now()
        now = max((lk.base for i in self.att_o for lk in self.looks[i] if lk.now), default=0.0)
        cont = self.continuation()
        coarse = vcoarse(s)
        if not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS:
            return banked + max(sn or 0.0, now)     # no offence turn is left before the clock runs out: only a shot now counts
        mode = leaf_mode(s, self.cfg)
        if mode == 'relative':
            # step 10 (behind the switch): the phase table's average plus how much better or worse this position reads
            # than an average position at that phase, read the same way (eval.relative_average, from the step 3n seeds)
            rel = coarse + cont - relative_average(s, self.cfg, self._budget_on())
            if self.cfg.get('lane') is True:
                # step 18q (D-196, design checks 1 and 4): the reading looked one turn ahead, so a way to the rim that
                # finishes next phase read as nothing. The ball handler's best paint look next phase (step 16's
                # penetration, against every defender who can get to a Contest of it) is read as this turn's looks
                # are, one phase on. The search plays the defence's answer to it; the reading no longer hides it.
                rel = self.lane_own(rel, self._budget_on())
            return banked + max(sn or 0.0, now, rel)
        if mode == 'looks':
            # step 18f (behind the switch): the looks alone. The phase table's floor hides everything below the
            # average (a shot worth 15 and one worth 21 read the same); the map fitted to this reading
            # (calibration_looks) says what such positions went on to earn instead
            return banked + max(sn or 0.0, now, cont)
        return banked + max(sn or 0.0, now, cont, coarse)

    def ahead_of(self, value, budget):
        """A lane worth `value` next phase, on the reading's own scale: the next phase's average, plus the look carried
        forward as a look is this phase, less what an average position reads then."""
        nxt = self.s.with_(clock=self.s.clock - RC.PHASE_SECONDS)
        return vcoarse(nxt) + self.cfg['continuation'] * value - relative_average(nxt, self.cfg, budget)

    def possession(self):
        """Step 12 (stable search, 'play on while pending'): what the position is worth without the ball handler's shot
        now: the leaf with the carrier's shot left out (a look another attacker releases this turn still counts)."""
        s = self.s
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        now = max((lk.base for i in self.att_o for lk in self.looks[i]
                   if lk.now and not (i == s.ball and lk.route == 'shoot')), default=0.0)
        if not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS:
            return banked + now
        cont, coarse = self.continuation(), vcoarse(s)
        mode = leaf_mode(s, self.cfg)
        if mode == 'relative':
            return banked + max(now, coarse + cont - relative_average(s, self.cfg, self._budget_on()))
        if mode == 'looks':
            return banked + max(now, cont)
        return banked + max(now, cont, coarse)

    # -- step 17: the named readings a learned judgement is built from (FEATURES gives each one's meaning)
    def features(self):
        """The position's readings, in FEATURES' order, as plain numbers (game points, counts, or 0 and 1). None is
        new: each is a reading the engine already makes. No hand weight combines them."""
        s = self.s
        sn = self.shot_now() or 0.0
        now = max((lk.base for i in self.att_o for lk in self.looks[i] if lk.now), default=0.0)
        res = sorted((self.cover()['residual'][i] for i in self.att_o), reverse=True)
        opened = max((self.threat[i]['value'] for i in self.att_o), default=0.0)
        tgt = self._paint_next()
        free = two = one = 0
        for i in self.att_o:
            if not self.looks[i]:
                continue
            lk = self.looks[i][0]
            top, shot, who = -1.0, None, -1
            for t in lk.types:
                v, d0 = lk.open[t], -1
                for d in sorted(lk.vals):
                    if t in lk.vals[d] and lk.vals[d][t] < v:
                        v, d0 = lk.vals[d][t], d
                if v > top:
                    top, shot, who = v, t, d0
            if who < 0:
                free += 1
            else:
                gap = BAND[s.ctx.off[i].bands['shot_' + shot]] - BAND[s.ctx.dfn[who].bands['con_' + shot]]
                two += gap >= 2
                one += gap == 1
        return [sn, now, res[0] if res else 0.0, res[1] if len(res) > 1 else 0.0, opened, self.budget()['value'],
                tgt[1] if tgt else 0.0, float(free), float(two), float(one), float(s.tok_o), float(s.tok_x),
                1.0 if self.o_to_act else 0.0, float(bin(s.moved_x).count('1')), float(bin(s.moved_o).count('1'))]

    # -- step 16, stage 3: advantages (eval.advantages). Reading and recording only.
    def advantages(self):
        """The offence's advantages on this board, each computed from the readings (no fixed zones or distances):
          separation: a look no defender can Contest in time;
          mismatch: a contested look where the attacker's band for the shot is above the best contester's band for the
            Contest (the cards' H, A, L: two bands apart is strong, one an advantage);
          numbers (with coverage_budget on): an attacker the defence's best shares leave above its full cover;
          penetration: the ball handler's way into the paint (the zone of layups, dunks and post shots), this phase by
            his looks there, or next phase by the movement rules with the pieces as they stand (two phases ahead).
        Each: dict(kind, i attacker, j defender or -1, sq, stage create | keep | convert, value: the target look after
        the defence's best answer, chance: of it arriving, gap: the band gap (mismatch), worth: what it adds to what
        the possession is worth now, never below 0). One per attacker and kind, his best. A look that only matches
        what the position is already worth has worth 0: it is counted once, in the position's value."""
        if self._adv is not None:
            return self._adv
        s, out = self.s, []
        self._adv = out
        if s.stage != 'play' or s.pending:
            return out
        if not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS:
            return out                   # no offence turn is left before the clock runs out: nothing can be built
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (RC.TURNOVER_POINTS * s.tos if RC.turnover_counts(s.ctx.rules) else 0)
        banked += foul_externality(s)
        now_worth = self.leaf() - banked                      # what the possession is worth now
        best = {}

        def put(kind, i, j, sq, stage, value, chance, worth, gap=0):
            cur = best.get((i, kind))
            if cur is None or worth > cur['worth'] + 1e-9 or \
                    (abs(worth - cur['worth']) <= 1e-9 and value * chance > cur['value'] * cur['chance'] + 1e-9):
                best[i, kind] = dict(kind=kind, i=i, j=j, sq=sq, stage=stage, value=value, chance=chance, worth=worth, gap=gap)
        for i in self.att_o:
            for lk in self.looks[i]:
                top, shot, who = -1.0, None, -1
                for t in lk.types:
                    v, d0 = lk.open[t], -1
                    for d in sorted(lk.vals):
                        if t in lk.vals[d] and lk.vals[d][t] < v:
                            v, d0 = lk.vals[d][t], d
                    if v > top:
                        top, shot, who = v, t, d0
                if shot is None or lk.p <= 0:
                    continue
                stage = 'convert' if lk.now else 'keep'
                worth = max(0.0, lk.base - now_worth)
                if who < 0:
                    put('separation', i, -1, lk.c, stage, top, lk.p, worth)
                else:
                    gap = BAND[s.ctx.off[i].bands['shot_' + shot]] - BAND[s.ctx.dfn[who].bands['con_' + shot]]
                    if gap >= 1:
                        put('mismatch', i, who, lk.c, stage, top, lk.p, worth, gap)
                if i == s.ball and B.zone(lk.c) == PAINT:
                    put('penetration', i, who, lk.c, stage, top, lk.p, worth)
        if self._budget_on():
            bd, full = self.budget(), max(self.cover()['residual'].values(), default=0.0)
            if bd['value'] > full + 1e-9:
                for i in self.att_o:
                    if bd['left'].get(i, 0.0) >= bd['value'] - 1e-9:
                        put('numbers', i, -1, self.threat[i]['sq'], 'keep', bd['left'][i], 1.0, max(0.0, bd['left'][i] - now_worth))
        tgt = self._paint_next()
        if tgt is not None:
            c, v = tgt
            nxt = s.with_(clock=s.clock - RC.PHASE_SECONDS)
            ahead = vcoarse(nxt) + self.cfg['continuation'] * v - relative_average(nxt, self.cfg, self._budget_on())
            put('penetration', s.ball, -1, c, 'create', v, 1.0, max(0.0, ahead - now_worth))
        order = ('separation', 'mismatch', 'numbers', 'penetration')
        out.extend(best[k] for k in sorted(best, key=lambda k: (k[0], order.index(k[1]))))
        return out

    def _paint_next(self):
        """Two phases ahead: the best paint square the ball handler can't reach this phase but can next phase: from any
        square he reaches this phase (one or two actions, by the movement rules) with one more movement, the pieces as
        they stand (a teammate in the way blocks it). (square, the look's value there against every defender who can
        get to a Contest with two movement actions), or None. Needs a phase after this one."""
        s, i = self.s, self.s.ball
        if s.clock <= RC.PHASE_SECONDS or i not in self.att_o or not B.on_board(s.o[i]) or s.tok_o <= 0:
            return None
        from .actions import movement_dests, can_move_kind
        from .reach import paths_to
        one = {s.o[i]: 0}
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(s, 'O', i, kind):
                for q in movement_dests(s, 'O', i, kind, self.rules):
                    one.setdefault(q, 1)
        stops = list(one) + two_actions(s, i, one)
        here = set(stops)
        occ = (set(s.o) | set(s.x)) - {s.o[i]}
        card, qs = s.ctx.off[i], s.ctx.off[i].qs
        best = None
        for c in PAINT_SQUARES:
            if c in here or c in occ or (c == RC.RIM and RC.rim_shot_barred(self.rules)):   # D-198
                continue
            if not any(all(q not in occ for q in p) for q0 in stops for p in paths_to(q0, c, qs, self.rules)):
                continue
            lk = Look(i, c, 'later', 1.0, False)
            lk.types = RC.ZONE_SHOTS[PAINT]
            pts = RC.ZONE_POINTS[PAINT]
            top = 0.0
            for t in lk.types:
                v = pts * card.shot(t)
                for d in self.att_x:
                    vals = self._vals2(lk, d, self._cm[d].get(c))
                    if vals and t in vals and vals[t] < v:
                        v = vals[t]
                if v > top:
                    top = v
            if best is None or top > best[1] + 1e-9:
                best = (c, top)
        return best

    def _lane_data(self):
        """Step 18q (eval.lane): the race to the rim, worked out once for this read. None when the ball handler has no
        way to the paint next phase. Else the paint squares he can't reach this phase but could next (in PAINT_SQUARES'
        order), each with its paths from every square he reaches this phase, and for each path the defenders whose
        bodies stand on it and the defenders whose arrows bar it (the rules' own crossing test, D-170), and the shot's
        value there against each defender's Contest a phase on (ahead_row)."""
        if self._lane is not False:
            return self._lane
        self._lane = None
        s, i = self.s, self.s.ball
        if s.clock <= RC.PHASE_SECONDS or i not in self.att_o or not B.on_board(s.o[i]) or s.tok_o <= 0:
            return None
        from .actions import movement_dests, can_move_kind, capture_lines, capture_ok
        one = {s.o[i]: 0}
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(s, 'O', i, kind):
                for q in movement_dests(s, 'O', i, kind, self.rules):
                    one.setdefault(q, 1)
        stops = list(one) + two_actions(s, i, one)
        here = set(stops)
        mates = set(s.o) - {s.o[i]}
        no_rim = RC.rim_shot_barred(self.rules)      # D-198: no shot from the rim's own square
        xat = {s.x[j]: j for j in range(5) if B.on_board(s.x[j])}
        lines = []
        if self.rules.zone != 'off':
            for ln in capture_lines(s, i):
                lines.append((xat[ln[0]], (ln,)))
        card, qs = s.ctx.off[i], s.ctx.off[i].qs
        paths = {}
        for q0 in stops:
            for p, rushed in _lane_paths(q0, qs, self.rules):
                c = p[-1]
                if c in here or any(q in mates for q in p) or (no_rim and c == RC.RIM):
                    continue
                dm = zm = 0
                for q in p:
                    j = xat.get(q)
                    if j is not None:
                        dm |= 1 << j
                for j, ln in lines:
                    if not capture_ok(q0, p, ln):
                        zm |= 1 << j
                paths.setdefault((c, rushed), []).append((q0, p, frozenset(p) | ({q0} if q0 != s.o[i] else frozenset()), dm, zm))
        budget = max(0, min(2, s.tok_x))
        pts = RC.ZONE_POINTS[PAINT]
        cands = []
        off = RC.control_cut(self.rules) if RC.control_size(self.rules) > 0 else 0
        for c in PAINT_SQUARES:
            rows = None
            for rushed in (False, True):           # reached by a Move (a set shot), or by a Quick Step or Sprint (rushed)
                if (c, rushed) not in paths:
                    continue
                if rows is None:
                    rows = {}
                    for d in self.att_x:
                        if B.on_board(s.x[d]):
                            can_move, qs_left = _caps(s, 'X', d)
                            rows[d] = ahead_row(self.rules, c, s.x[d], s.arrows[d], s.ctx.dfn[d].qs, can_move, qs_left, budget, stance_mode(s, d))
                lk = Look(i, c, 'later', 1.0, False)
                lk.types = RC.ZONE_SHOTS[PAINT]
                lk.rushed = rushed
                vals = {}
                for d, row in rows.items():
                    v = self._vals2(lk, d, row) if row is not None else None
                    if v:
                        vals[d] = v
                cands.append(dict(c=c, lk=lk, paths=paths[c, rushed], open=[pts * (card.shot(t) - (off if rushed else 0)) for t in lk.types], vals=vals))
        self._lane = dict(cands=cands, budget=budget, by={}, static={}) if cands else None
        return self._lane

    def _lane_value(self, e, skip=-1, extra=None, t=-1):
        """The shot's value on a lane square: its best type, each against the best Contest of every defender but `skip`,
        and `extra` (one defender's values, re-read). t: a defender a Dribble has beaten, contesting as he then can."""
        top = 0.0
        for n, ty in enumerate(e['lk'].types):
            v = e['open'][n]
            for d, vals in e['vals'].items():
                if d == skip:
                    continue
                if d == t:
                    vals = self._lane_beaten_vals(e, d)
                if ty in vals and vals[ty] < v:
                    v = vals[ty]
            if extra and ty in extra and extra[ty] < v:
                v = extra[ty]
            if v > top:
                top = v
        return top

    def _lane_beaten_vals(self, e, d, frm=None, arrow=None, qs_left=None):
        """Defender d's Contest of a lane square once a Dribble has beaten him: locked (no Move left this phase), his
        zone broken. frm, arrow, qs_left: the open list's re-read of him moved (not kept)."""
        s = self.s
        mode = 2 if self.rules.zone != 'off' else 0
        if frm is not None:
            row = ahead_row(self.rules, e['c'], frm, arrow, s.ctx.dfn[d].qs, False, qs_left, self._lane['budget'], mode)
            return (self._vals2(e['lk'], d, row) if row is not None else None) or {}
        vb = e.setdefault('vb', {})
        if d not in vb:
            row = ahead_row(self.rules, e['c'], s.x[d], s.arrows[d], s.ctx.dfn[d].qs, False, _caps(s, 'X', d)[1], self._lane['budget'], mode)
            vb[d] = (self._vals2(e['lk'], d, row) if row is not None else None) or {}
        return vb[d]

    def _lane_next(self, t=-1):
        """(square, value): the best lane square with a way to it clear as the pieces stand; None if there is none.
        t: with defender t beaten by a Dribble (his arrow bars nothing)."""
        data = self._lane_data()
        if not data:
            return None
        bt = (1 << t) if t >= 0 else 0
        best = None
        for e in data['cands']:
            if not any(dm == 0 and not (zm & ~bt) for _, _, _, dm, zm in e['paths']):
                continue
            top = self._lane_value(e, -1, None, t)
            if best is None or top > best[1] + 1e-9:
                best = (e['c'], top)
        return best

    def _lane_static(self, t=-1):
        """Step 18q: the lane after the defence's best single answer with a body ("no defender able to get between").
        (value, [for each defender: the lowest value any other defender's step leaves]); value -1: no lane. A defender
        answers by stepping, with the movement he has left this phase (his exact reach: other pieces and screens stop
        him), onto a square of a way to the rim; the lane is then worth its best square still open. With no defence
        token left nobody can answer, and the lane is worth what it reads as it stands. t: the same with defender t
        beaten by a Dribble: his arrow bars nothing, he is locked and makes no answer, and he contests as he then can."""
        data = self._lane_data()
        if not data:
            return -1.0, [INF] * 5
        hit = data['static'].get(t)
        if hit is not None:
            return hit
        s = self.s
        bt = (1 << t) if t >= 0 else 0
        tgt = self._lane_next(t)
        base = tgt[1] if tgt is not None else -1.0
        resp = [INF] * 5
        if data['budget'] > 0:
            cands = data['cands']
            order = sorted(((self._lane_value(e, -1, None, t), n) for n, e in enumerate(cands)), key=lambda r: (-r[0], r[1]))
            on_way = data.get('on_way')
            if on_way is None:
                on_way = data['on_way'] = set()
                for e in cands:
                    for _, _, pset, _, _ in e['paths']:
                        on_way |= pset
            occ = set(s.o) | set(s.x)
            for j in self.att_x:
                if j == t or not B.on_board(s.x[j]):
                    continue
                free, fixed = defender_map(s, j, exact=True)
                reach = {q for q, n in free.items() if 0 < n <= data['budget']}
                reach |= {q for q, arrs in fixed.items() if any(0 < n <= data['budget'] for n in arrs.values())}
                bj = 1 << j
                for q in reach:
                    if q not in on_way or q in occ:
                        continue
                    left = -1.0
                    for v, n in order:
                        e = cands[n]
                        if e['c'] != q and any(not (dm & ~bj) and not (zm & ~bj & ~bt) and q not in pset for _, _, pset, dm, zm in e['paths']):
                            left = v
                            break
                    if left < resp[j]:
                        resp[j] = left
        low = min(resp)
        excl = [min((resp[k] for k in range(5) if k != j), default=INF) for j in range(5)]
        data['static'][t] = (min(base, low), excl)
        return data['static'][t]

    def lane_reread(self, j, q, a, can_move, qs_left, t=-1):
        """The lane's value with defender j standing on q facing a, with can_move / qs_left left to him (the open list's
        cheap read): his body where it now stands, his old arrow's bar lifted and his new arrow's foot barred, his
        Contest a phase on from there; every other piece as it stands. -1: no lane. t: with defender t beaten by a
        Dribble (t may be j himself, where the action leaves him)."""
        data = self._lane_data()
        if not data:
            return -1.0
        from .actions import capture_ok
        s = self.s
        bj = 1 << j
        bt = (1 << t) if t >= 0 else 0
        same = q == s.x[j] and a == s.arrows[j]
        mode = stance_mode(s, j)
        line = None
        if not same and mode == 1 and t != j:
            line = ((q, (a, (a + 1) % 8), (1, 1)),)
        order = data['by'].get((t, j))
        if order is None:
            order = data['by'][t, j] = sorted(((self._lane_value(e, j, None, t), n) for n, e in enumerate(data['cands'])), key=lambda r: (-r[0], r[1]))
        best = -1.0
        for bw, n in order:
            if bw <= best + 1e-9:
                break
            e = data['cands'][n]
            if e['c'] == q:
                continue
            ok = False
            for q0, p, pset, dm, zm in e['paths']:
                if dm & ~bj or ((zm & ~bt) if same else (zm & ~bj & ~bt)) or q in pset:
                    continue
                if line is not None and not capture_ok(q0, p, line):
                    continue
                ok = True
                break
            if not ok:
                continue
            if t == j:
                mine = self._lane_beaten_vals(e, j, q, a, qs_left)
            else:
                row = ahead_row(self.rules, e['c'], q, a, s.ctx.dfn[j].qs, can_move, qs_left, data['budget'], mode)
                mine = self._vals2(e['lk'], j, row) if row is not None else None
            v = self._lane_value(e, j, mine, t)
            if v > best:
                best = v
        other = self._lane_static(t)[1][j]           # and after another defender's best step into it
        return other if other < best else best

    # -- the Dribble in the race: a defender next to the ball handler only stays in it if he wins the roll
    def _dribble_ok(self):
        """Can the ball handler Dribble at a defender next to him this phase, by the rules? (and his rating for it)"""
        if self._drib is None:
            s, i = self.s, self.s.ball
            ok = (s.tok_o > 0 and i in self.att_o and B.on_board(s.o[i]) and s.count('O', 'dribble') < RC.LIMITS['O']['dribble']
                  and not (s.inbound and i == s.ctx.inbounder and self.rules.inbounder_pass_only)
                  and (self.rules.locked_can_dribble or not s.locked('O', i))
                  and not (s.picked_up() and RC.app_rule(self.rules, 'closely_guarded')))
            self._drib = (ok, rolled(s, 'O', i, 'dribble') if ok else 0)
        return self._drib

    def _beat_chance(self, t, rushed=None):
        """The chance his Dribble beats defender t (rushed: t's state where the open list's re-read leaves him)."""
        s = self.s
        if rushed is None:
            ag = rolled(s, 'X', t, 'agility')
        else:
            cut = RC.off_balance_cut(self.rules)
            ag = s.ctx.dfn[t].r['agility'] - (cut if cut and rushed else 0)
        return float(p_success(self._dribble_ok()[1] - ag, self.rules))

    def lane_dribble(self, lane, j=-1, q=None, a=None, can_move=False, qs_left=0, rushed=False):
        """(the lane's value with the defender his Dribble would beat out of the race, the chance he beats him): the
        defender next to him whose beating gains most (the chance times what the lane gains). (-1, 0): no Dribble, or
        none that gains. lane: the lane's value as it stands. j, q, ...: the open list's re-read of defender j moved."""
        if not self._dribble_ok()[0] or not self._lane_data():
            return -1.0, 0.0
        s = self.s
        bq = s.o[s.ball]
        floor = lane if lane > 0 else 0.0
        best, gain = (-1.0, 0.0), 0.0
        for t in range(5):
            at = q if t == j else s.x[t]
            if not B.on_board(at) or not B.adjacent(at, bq):
                continue
            p = self._beat_chance(t, rushed if t == j else None)
            if p <= 0:
                continue
            v = self._lane_static(t)[0] if j < 0 else self.lane_reread(j, q, a, can_move, qs_left, t)
            g = p * (v - floor)
            if g > gain + 1e-9:
                best, gain = (v, p), g
        return best

    def lane_rel(self, rel, lane, beaten, p, budget):
        """The play-on reading with the lane in it: the larger of the reading and the lane a phase on; and, where a
        Dribble would take a defender out of the race, the chance of it times what that adds."""
        if lane >= 0:
            ahead = self.ahead_of(lane, budget)
            if ahead > rel:
                rel = ahead
        if p > 0 and beaten >= 0:
            ahead = self.ahead_of(beaten, budget)
            if ahead > rel:
                rel += p * (ahead - rel)
        return rel

    def lane_own(self, rel, budget):
        """lane_rel for this read's own position."""
        lane = self._lane_static()[0]
        beaten, p = self.lane_dribble(lane)
        return self.lane_rel(rel, lane, beaten, p, budget)

    def phi(self):
        """Step 16, stage 4: the goal potential: each attacker's best advantage, summed (0 when the possession ends)."""
        top = {}
        for a in self.advantages():
            if a['worth'] > top.get(a['i'], 0.0):
                top[a['i']] = a['worth']
        return sum(top[i] for i in sorted(top))

    # -- step 13 B3: the look-value split (reporting only; no value changes)
    @staticmethod
    def look_split(lk):
        """A look's value in two parts: the finisher (the card: the value of his best shot type there with nobody near)
        and the quality (the position: the chance it arrives and what the best Contest leaves of it), between 0 and 1.
        finisher x quality is the look's value, so the trainer can say 'good look, poor shooter'."""
        fin = max(lk.open.values(), default=0.0)
        return fin, (lk.base / fin if fin > 0 else 0.0)

    # -- step 13 B1: coverage as a budget (eval.coverage_budget)
    def _budget_on(self):
        """The switch; the ordering's quick reading (k = 0: no cover is searched) stays as it was."""
        return bool(self.cfg.get('coverage_budget')) and self.k > 0

    def budget_tables(self):
        """What the allocation is solved from, every number an existing one. D-125: a Contest from where a defender
        stands is free, in full, on every look he is next to; only an answer that needs a movement shares his budget.
        looks: every look of every attacker, in order, as (attacker, look, its value after the free Contests); a look
        released this turn keeps its value. cols: the answers that need a movement, as (defender, attacker or -1,
        'react' or 'move', {look index: how far that look falls}):
          'react': he reaches attacker i's shot with a movement in the reaction;
          'move': one of his movement replies in the defence's turn (the replies the reading already finds). From his
          new square his Contest is free on every look next to it, the pass's chance and the attacker's way change for
          everyone, and his free Contests from the old square are lost (a look can rise: a negative fall). With an
          attacker named, he also reaches that attacker's shot with a movement in the reaction."""
        s = self.s
        reach = bool(self.cfg.get('reach'))

        def best(lk, p, rows):
            top = 0.0
            for t in lk.types:
                v = lk.open[t]
                for vals in rows:
                    if vals and t in vals and vals[t] < v:
                        v = vals[t]
                if v > top:
                    top = v
            return p * top
        looks, first, free = [], {}, []
        for i in self.att_o:
            first[i] = len(looks)
            for lk in self.looks[i]:
                f0 = {}
                if not lk.now:
                    for j in self.att_x:
                        v0 = self._vals(lk, j, self._cm[j].get(lk.c), 0)
                        if v0:
                            f0[j] = v0
                free.append(f0)
                looks.append((i, lk, lk.base if lk.now else best(lk, lk.p, list(f0.values()))))
        R = self.cover()['R']
        cols = []
        for j in self.att_x:
            for i in self.att_o:
                falls = {}
                for n, lk in enumerate(self.looks[i]):
                    l = first[i] + n
                    if not lk.now and j in lk.vals:
                        f = looks[l][2] - best(lk, lk.p, list(free[l].values()) + [lk.vals[j]])
                        if f > 1e-9:
                            falls[l] = f
                if falls:
                    cols.append((j, i, 'react', falls))
            for (q, a, used), _ in R[j][1:]:
                cm = self._contest(j, q, a, used)
                moved = None
                stand, extra = {}, {}                  # from his new square: for everyone; and more for one attacker
                for l, (i, lk, o) in enumerate(looks):
                    if lk.now:
                        continue
                    if reach and q != s.x[j] and lk.route in PATH_ROUTES and _blocks(q, s.o[i], lk.c, s.ctx.off[i].qs,
                                                                                     self.rules):
                        w0 = w1 = 0.0
                    else:
                        p = lk.p
                        if lk.route in ('catch', 'cut') and q != s.x[j]:
                            if moved is None:
                                moved = s.with_(x=s.x[:j] + (q,) + s.x[j + 1:], arrows=s.arrows[:j] + (a,) + s.arrows[j + 1:],
                                                moved_x=s.moved_x | (1 << j) if used == 'move' else s.moved_x)
                            p = _lane_p(moved, i, lk.c, reach=False)
                        row = cm.get(lk.c)
                        others = [v for d, v in free[l].items() if d != j]
                        w0 = best(lk, p, others + [self._vals(lk, j, row, 0) if row is not None else None])
                        w1 = best(lk, p, others + [self._vals(lk, j, row) if row is not None else None])
                    if abs(o - w0) > 1e-9:
                        stand[l] = o - w0
                    if w1 < w0 - 1e-9:
                        extra.setdefault(i, {})[l] = o - w1
                if any(f > 1e-9 for f in stand.values()):
                    cols.append((j, -1, 'move', stand))
                for i in self.att_o:
                    if i in extra:
                        falls = dict(stand)
                        falls.update(extra[i])
                        cols.append((j, i, 'move', falls))
        return looks, cols

    def budget(self):
        """Step 13 B1: coverage as a budget. In one team turn a defender attends one attacker: he ends on one square
        and makes one Contest. The defence splits each defender across the attackers he can answer (shares adding to
        at most 1); a share is the chance he is the one there. On any one look at most one answer counts, and the
        answers that need a movement share the defence's movement actions next turn. The defence chooses the shares
        that hold the offence's best look lowest: an exact small linear program (lp_max). Returns dict(value, left
        {attacker: his best look after it}, open {attacker: with no answer}, shares [(defender, attacker, kind, share)])."""
        if self._budget is not None:
            return self._budget
        looks, cols = self.budget_tables()
        top = max((o for _, _, o in looks), default=0.0)
        n = len(cols)
        covered = sorted({l for c in cols for l in c[3]})
        up = lambda c, l: c[3].get(l, 0.0) > 0.0       # an answer that lowers look l
        A, b = [], []
        free = max((o for l, (_, _, o) in enumerate(looks) if l not in set(covered)), default=0.0)
        A.append([0.0] * n + [1.0])                 # the looks no answer reaches stay as they are
        b.append(top - free)
        for l in covered:                           # look l is held to top - z
            A.append([-c[3].get(l, 0.0) for c in cols] + [1.0])
            b.append(top - looks[l][2])
        for l in covered:                           # on one look, one answer counts
            if sum(1 for c in cols if up(c, l)) > 1:
                A.append([1.0 if up(c, l) else 0.0 for c in cols] + [0.0])
                b.append(1.0)
        for j in self.att_x:                        # one defender, one attacker
            if any(c[0] == j for c in cols):
                A.append([1.0 if c[0] == j else 0.0 for c in cols] + [0.0])
                b.append(1.0)
        if any(c[2] == 'move' for c in cols):       # the defence's movement actions next turn
            A.append([1.0 if c[2] == 'move' else 0.0 for c in cols] + [0.0])
            b.append(float(min(2, self.s.tok_x)))
        z, x = lp_max([0.0] * n + [1.0], A, b)
        left, opened = {}, {}
        for l, (i, _, o) in enumerate(looks):
            v = o - sum(x[k] * c[3].get(l, 0.0) for k, c in enumerate(cols))
            left[i] = max(left.get(i, 0.0), v)
            opened[i] = max(opened.get(i, 0.0), o)
        self._budget = dict(value=top - z, left=left, open=opened,
                            shares=[(c[0], c[1], c[2], x[k]) for k, c in enumerate(cols) if x[k] > 1e-9])
        return self._budget

    def continuation(self):
        """The best look the defence's best cover leaves (the mean of the tied top residuals) times the continuation:
        what the board read says the position is worth beyond a shot now."""
        if self._budget_on():
            return self.budget()['value'] * self.cfg['continuation']       # step 13 B1: after the defence's best shares
        res = self.cover()['residual']
        top = max(res.values(), default=0.0)
        ties = [i for i in res if res[i] >= top - 1e-9]
        return (sum(res[i] for i in ties) / len(ties) if ties else 0.0) * self.cfg['continuation']


_LEARNED = {}


def learned_weights():
    """Step 17: the shared weights file (data/learned_weights.json), or None if there is none. A file that names
    other readings than FEATURES is refused."""
    if 'w' not in _LEARNED:
        p = os.path.join(HERE, 'data', 'learned_weights.json')
        _LEARNED['w'] = json.load(open(p)) if os.path.exists(p) else None
        if _LEARNED['w'] is not None and _LEARNED['w']['features'] != [f[0] for f in FEATURES]:
            raise ValueError('learned_weights.json names other readings than this engine makes')
    return _LEARNED['w']


def learned_value(s, f):
    """What is left to earn, by the learned weights: per phase, intercept + sum of weight x (reading - mean) / sd, in
    the file's order (float64, the same order as the JavaScript)."""
    m = learned_weights()['phases'].get(str(min(6, max(1, (RC.START_CLOCK - s.clock) // RC.PHASE_SECONDS + 1))))
    if m is None:
        return None
    v = m['intercept']
    for i in range(len(f)):
        v += m['weights'][i] * (f[i] - m['mean'][i]) / m['sd'][i]
    return v


_CEILING = {}


def ceiling(s):
    """Step 18b (D-145): the most the possession can still earn beyond what it has already earned, against the
    defence's best reply. A possession ends in one shot, and the defence can always decline to Contest or to Steal (so
    it never has to give free throws or the +5): no position is worth more than the best open shot any attacker's
    card can score: points x rating, 3 x the three or 2 x any other shot. With Coach's Call in play the target's shot
    also earns the bonus for its look. From the rules and the cards; no number is set by hand."""
    ctx = s.ctx
    key = (id(ctx), s.target if ctx.coach_call else -1)
    hit = _CEILING.get(key)
    if hit is not None and hit[0] is ctx:
        return hit[1]
    from .scoring import band
    best = 0.0
    for i, card in enumerate(ctx.off):
        m = 0.0
        for z, types in RC.ZONE_SHOTS.items():
            pts = RC.ZONE_POINTS.get(z, 0)
            for ty in types:
                v = pts * card.shot(ty)
                if v > m:
                    m = v
        if ctx.coach_call and i == s.target:
            m = m + RC.COACH_BONUS[band(m)]
        if m > best:
            best = m
    if len(_CEILING) > 4096:
        _CEILING.clear()
    _CEILING[key] = (ctx, best)
    return best


def calibration_scale(s, phase):
    """Step 18a (Shaun, 11 Nov 2026): the map was fitted on Senior Pro play. For any other age and standard it is
    scaled by that level's phase table value over Senior Pro's at the same phase, as D-114 does for the averages.
    Senior Pro is exactly 1."""
    lv = tuple(getattr(s.ctx, 'levels_key', None) or ('senior', 'pro'))
    if lv == ('senior', 'pro'):
        return 1.0
    own = _TABLES.get(lv)
    if own is None:
        own = _load_table(lv)
    base = _TABLES.get(('senior', 'pro'))
    if base is None:
        base = _load_table(('senior', 'pro'))
    a, b = own.get('_phase' + str(phase)), base.get('_phase' + str(phase))
    if not a or not b or a <= 0 or b <= 0:
        return 1.0
    return a / b


def kept_on(cfg):
    """Step 18f (eval.kept_actions): a defender's answer is read by what he has left. The cover's re-read of a defender
    moved to a square took his control as it stands now; with the switch on, an answer by a Quick Step or a Sprint is
    rushed and one by a Move is set, as the control rule says (and the open list's re-read of a defender stepping into
    the ball handler's way reads the handler's looks the same way)."""
    return cfg.get('kept_actions') is True


_FORCE_LOOKS = [False]              # the fitting tool reads positions in the looks mode whatever the config says


def leaf_mode(s, cfg):
    """The reading's mode at a position: eval.leaf_mode ('floor', 'relative'), or 'looks' (step 18f): the looks
    alone, without the phase table's floor. 'looks' is in play only under the app's rules with the calibrated reading
    on and a map fitted to it (calibration_looks); anywhere else it reads as 'floor'."""
    if _FORCE_LOOKS[0]:
        return 'looks'
    m = cfg.get('leaf_mode', 'floor')
    if m != 'looks':
        return m
    w = learned_weights() if cfg.get('calibrated') is True and cfg.get('learned') is not True else None
    if not (s.ctx.rules.digital and w is not None and w.get('calibration_looks')):
        return 'floor'
    # only where the looks map has a line for this phase and side to act (too few positions to fit one: the floor)
    phase = min(6, max(1, (RC.START_CLOCK - s.clock) // RC.PHASE_SECONDS + 1))
    key = str(phase) + ('O' if s.side == 'O' and s.stage == 'play' else 'X')
    return 'looks' if key in w['calibration_looks']['maps'] else 'floor'


# ---- step 18h (eval.no_floor) ------------------------------------------------------------------------------------------
# Today's reading takes the largest of three things: the shot the ball handler can release now, the best look another
# attacker can release this turn, and "play on" (the phase table plus the best look the cover leaves, less the phase's
# average). Whatever is not the largest is thrown away, and of the looks the cover leaves only the best one counts. So
# positions that differ in the shot they leave, or in the second look they leave, read the same. With the switch on
# the parts are kept: what is left to earn is a line fitted to what positions went on to earn (the weights file's
# calibration_parts block), per level, phase and side to act:
#   a + b1 x (the best shot that can go up now) + b2 x (the best look the cover leaves) + b3 x (the second best)
# with b1, b2, b3 never below 0 (a better shot, or a better look left, is never worth less to the offence: it can
# decline it). Every number is from the fit. Under the app's rules, with the calibrated reading on.
LEVEL = [None]                                          # the level whose search is running (its own lines, if it has them)


def play_on_map(s, cfg, w):
    """Step 18h (eval.exact_shot, off): today's reading takes the largest of the shot that can go up now and "play
    on", and then passes it through the map. So a shot's exact value (points x rating less the Contest, from the
    rules) is bent by a map fitted to what positions went on to earn, and a position whose worth is that very shot
    reads above the shot itself. With the switch on the shot keeps its exact value and only "play on" (the phase table
    plus the best look the cover leaves, less the phase's average) goes through a map of its own (the weights file's
    calibration_play_on block, per level): the reading is the larger of the two. The map, or None."""
    if cfg.get('exact_shot') is not True or w is None or not w.get('calibration_play_on') or not s.ctx.rules.digital:
        return None
    if leaf_mode(s, cfg) != 'relative':
        return None
    lv = w['calibration_play_on']['levels']
    return lv.get(LEVEL[0]) or lv.get('all')


def parts_map(s, cfg, w):
    if cfg.get('no_floor') is not True or w is None or not w.get('calibration_parts') or not s.ctx.rules.digital:
        return None
    return w['calibration_parts']['levels']


def parts_value(levels, s, o_to_act, shot, look, second):
    """What is left to earn, from the reading's parts; None where no line was fitted (too few positions): the map then."""
    phase = min(6, max(1, (RC.START_CLOCK - s.clock) // RC.PHASE_SECONDS + 1))
    key = str(phase) + ('O' if o_to_act else 'X')
    row = (levels.get(LEVEL[0]) or {}).get('maps', {}).get(key) or (levels.get('all') or {}).get('maps', {}).get(key)
    if row is None:
        return None
    a, b1, b2, b3 = row['w']
    q = calibration_scale(s, phase)
    if q == 1.0:
        return a + (b1 * shot + b2 * look + b3 * second)
    return q * (a + (b1 * shot + b2 * look + b3 * second) / q)


def calibration_for(s, cfg, w):
    """The map a position's reading goes through: the looks reading's own (step 18f), the table's own under the
    table's rules (D-141), or the app's."""
    if leaf_mode(s, cfg) == 'looks' and w.get('calibration_looks'):
        return w['calibration_looks']
    if not s.ctx.rules.digital and cfg.get('tabletop_map', True) and w.get('calibration_tabletop'):
        return w['calibration_tabletop']
    if s.ctx.rules.digital and cfg.get('lane') is True and w.get('calibration_lane') and LEVEL[0] in w['calibration_lane']:
        return w['calibration_lane'][LEVEL[0]]         # step 18q: the map fitted on play with the lane reading on
    if s.ctx.rules.digital and cfg.get('level_maps', True) and w.get('calibration_levels') and LEVEL[0] in w['calibration_levels']:
        return w['calibration_levels'][LEVEL[0]]       # D-163: the level's own map, fitted on its own play
    return w['calibration']


def calibrate(cal, s, o_to_act, r):
    """Step 17D: the map for this phase and side to act (knots x -> y, straight lines between and beyond them).
    Step 18a: for another age and standard, the reading and the result are both in that level's own scale
    (calibration_scale): earned = scale x map(reading / scale)."""
    phase = min(6, max(1, (RC.START_CLOCK - s.clock) // RC.PHASE_SECONDS + 1))
    m = cal['maps'].get(str(phase) + ('O' if o_to_act else 'X'))
    if m is None:
        return r
    q = calibration_scale(s, phase)
    if q != 1.0:
        r = r / q
    x, y = m['x'], m['y']
    n = len(x)
    if n == 1:
        v = y[0]
    else:
        k = 0
        while k < n - 2 and r > x[k + 1]:
            k += 1
        v = y[k] + (y[k + 1] - y[k]) * (r - x[k]) / (x[k + 1] - x[k])
    return v if q == 1.0 else q * v


def lp_max(c, A, b):
    """Maximise c.x subject to A.x <= b, x >= 0, with every b >= 0 (so the slack start is feasible): the simplex
    method on a dense table, Bland's rule (the lowest index enters, ties leave by the lowest basis index), so it ends
    and both engines take the same steps. Returns (the maximum, x)."""
    m, n = len(A), len(c)
    T = [list(A[r]) + [1.0 if k == r else 0.0 for k in range(m)] + [b[r]] for r in range(m)]
    obj = [-v for v in c] + [0.0] * (m + 1)
    basis = [n + r for r in range(m)]
    for _ in range(500):
        col = -1
        for k in range(n + m):
            if obj[k] < -1e-12:
                col = k
                break
        if col < 0:
            break
        row, best = -1, 0.0
        for r in range(m):
            if T[r][col] > 1e-12:
                ratio = T[r][-1] / T[r][col]
                if row < 0 or ratio < best - 1e-12 or (ratio <= best + 1e-12 and basis[r] < basis[row]):
                    row, best = r, ratio
        if row < 0:
            break
        pv = T[row][col]
        T[row] = [v / pv for v in T[row]]
        for r in range(m):
            if r != row and T[r][col] != 0.0:
                f = T[r][col]
                T[r] = [v - f * w for v, w in zip(T[r], T[row])]
        f = obj[col]
        obj = [v - f * w for v, w in zip(obj, T[row])]
        basis[row] = col
    x = [0.0] * n
    for r in range(m):
        if basis[r] < n:
            x[basis[r]] = T[r][-1]
    return obj[-1], x


@lru_cache(maxsize=100000)
def lane_squares(a, c, tol):
    """Squares strictly between a and c whose centre lies within tol of the pass segment (board.on_segment, in
    floats)."""
    out = []
    vx, vy = c[0] - a[0], c[1] - a[1]
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return frozenset()
    for x in range(min(a[0], c[0]), max(a[0], c[0]) + 1):
        for y in range(min(a[1], c[1]), max(a[1], c[1]) + 1):
            p = (x, y)
            if p == a or p == c:
                continue
            wx, wy = x - a[0], y - a[1]
            dot = wx * vx + wy * vy
            if dot <= 0 or dot >= L2:
                continue
            cross = vx * wy - vy * wx
            if (cross == 0) if tol == 0 else (cross * cross < tol * tol * L2):
                out.append(p)
    return frozenset(out)


@lru_cache(maxsize=200000)
def _one_action(frm, arrow, qs, can_move, qs_left, rules):
    """The squares a defender stands on now or after one Move or Quick Step (geometry)."""
    free, fixed = geo_reach(frm, arrow, qs, can_move, qs_left, rules)
    return frozenset([frm] + [q for q, n in free.items() if n <= 1] + [q for q, arr in fixed.items() if min(arr.values()) <= 1])


_LP = {}


def _off_balance_key(s):
    """D-185 (rules.off_balance): what a pass's chance now also turns on, for the keys of the two caches below: whether
    the passer is rushed, and which defenders are (a rushed Pass and a rushed Intercept are rolled lower). Without
    it a chance worked out with a player set was handed back for the same board with him rushed or locked."""
    if not RC.off_balance_cut(s.ctx.rules):
        return 0
    return (1 if s.rushed('O', s.ball) else 0) | sum(2 << d for d in range(5) if s.rushed('X', d))


def turnover_value(s):
    """What a pick-off leaves the offence: 0 in the digital format or the final phase; else -5 and the clock cost,
    then the coarse value of playing on."""
    if RC.app_rule(s.ctx.rules, 'points_play_on') and not s.ctx.hold_for_one:
        # D-198: -5, then the next phase with the ball where it was; with no phase left, what is banked
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * (s.tos + 1)
        if s.clock <= RC.PHASE_SECONDS:
            return float(banked)
        return banked + vcoarse(s.with_(clock=s.clock - RC.PHASE_SECONDS))
    if s.ctx.rules.digital or s.ctx.hold_for_one or s.clock <= RC.PHASE_SECONDS:
        if s.ctx.rules.turnover_floor:                  # D-82: 0, or what is banked if that is lower
            return float(min(0, RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * s.tos))
        return 0.0
    banked = RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * (s.tos + 1)
    return banked + vcoarse(s.with_(clock=s.clock - RC.PHASE_SECONDS))


def _lane_p(s, i, c, reach=None):
    """P(a pass to attacker i at c arrives), from geometry: 0 if a defender next to c stands on the lane (receiver
    denial); else 1 - the best Intercept chance of a defender who stands on the lane or can step onto it with a
    Move or Quick Step. reach (step 12, eval.reach): who can step onto it from the reach map's exact movement."""
    if reach is None:
        reach = bool(CONFIG['eval'].get('reach'))
    rl = pass_by_rules(s.ctx.rules)                      # by the rules the chance also turns on bodies, screens, broken zones
    # step 21: keyed on the context itself (kept alive while cached), not its id: a freed context's id can come back
    # for a new one, and the new board then read the old board's chance (seen in step 21's tests)
    key = (s.ctx, s.o[s.ball], s.ball, c, s.x, s.arrows, s.moved_x, s.qs_x, s.lock_x, s.tok_x, s.cnt[6], reach,
           s.o if reach or rl else None, s.screens if reach or rl else None, _off_balance_key(s),
           (i, s.cnt, s.beaten) if rl else None)
    hit = _LP.get(key)
    if hit is None:
        if len(_LP) > 300000:
            _LP.clear()
        hit = _LP[key] = _lane_p_calc(s, i, c, reach)
    return hit


def _exact_one(s, d):
    """The squares defender d stands on now or after one of his movement actions, by the rules' exact movement."""
    free, fixed = defender_map(s, d, exact=True)
    return frozenset([s.x[d]] + [q for q, n in free.items() if n <= 1] +
                     [q for q, arr in fixed.items() if min(arr.values()) <= 1])


def cov_fresh(s):
    """Step 20 (engine.js covFresh): the position as a fresh phase would find it (resolve.new_phase, no clock taken off):
    the offence's full turn to come and the defence's movement fresh. A pass in the air is read as caught."""
    from .state import ZERO_COUNTS
    if s.pending:
        s = s.with_(ball=s.pending[1], pending=None, approach=-1)
    return s.with_(screens=(), beaten=(), tok_o=RC.TOKENS_PER_PHASE, tok_x=RC.TOKENS_PER_PHASE, moved_o=0, moved_x=0, qs_o=0, qs_x=0,
                   lock_o=0, lock_x=0, rush_o=0, rush_x=0, cnt=ZERO_COUNTS, turn_n=0, side='O', stage='play', approach=-1, prev_wait='',
                   final=False, turn_lead=-1, turn_x=(), turn_moved=0, react_moved=0)


def covers_too_of(s):
    """Step 25 (engine.js coversToo, D-241): does defender d, having taken the look on cv, still contest the look on cu
    with the reaction's two actions from a square next to cv? Only one attacker can shoot: he covers every look he can
    reach in time, unless the offence creates them one after another and he can't."""
    rules = s.ctx.rules
    from_next = stance_mode(s.with_(beaten=()), 0)
    memo = {}

    def covers(d, cv, cu):
        qs, mode = s.ctx.dfn[d].qs, from_next
        key = (d, cv, cu)
        if key not in memo:
            hit = False
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    p = (cv[0] + dx, cv[1] + dy)
                    if (dx, dy) == (0, 0) or p == cu or not B.on_board(p):
                        continue
                    pair = _any_arrow_cmap2(rules, p, qs, mode).get(cu)
                    if pair is not None and pair[2]:
                        hit = True
                        break
                if hit:
                    break
            memo[key] = hit
        return memo[key]
    return covers


def cover_groups(covers, looks, most=3):
    """Step 21 (engine.js lgOverloads, D-206: count numbers, not just pairs). looks: [dict(a, c, t, wd, now, mask, order)]
    (the attacker, his square, the shot, its worth read without the defenders in mask, its worth now, the defenders who
    take anything off it, a tie order). A group of one, two or three defenders is the only cover for the looks whose mask
    lies inside it; each attacker brings his best such look. With more attackers than defenders, the defence's best
    assignment gives each defender one attacker he can take (or none); an attacker is open if no defender who took a
    look can still contest his from beside the look he took (step 25, covers). The group is worth the best look the best assignment leaves open. A group is named only
    if no smaller group inside it is already worth as much. -> [dict(d, ds, value, threats, near_key)]"""
    import itertools

    def value_of(A, ds):
        best = float('inf')
        pick = [None]
        k = len(ds)
        took = [-1] * k

        def go(i):
            nonlocal best
            if i == k:
                left, open_ = float('-inf'), -1
                for u in range(len(A)):
                    if u in took:
                        continue
                    if all(v < 0 or not covers(ds[i], A[v]['c'], A[u]['c']) for i, v in enumerate(took)) and A[u]['wd'] > left:
                        left, open_ = A[u]['wd'], u
                if left < best - 1e-9:
                    best = left
                    pick[0] = (list(took), open_)
                return
            took[i] = -1
            go(i + 1)
            for u in range(len(A)):
                if u in took or not (A[u]['mask'] >> ds[i] & 1):
                    continue
                took[i] = u
                go(i + 1)
                took[i] = -1
        go(0)
        return best, pick[0]
    out, named = [], []
    for k in range(1, most + 1):
        for ds in itertools.combinations(range(5), k):
            gm = sum(1 << d for d in ds)
            by = {}
            for z in looks:
                if (z['mask'] & ~gm) or not (z['mask'] & gm):
                    continue
                cur = by.get(z['a'])
                if cur is None or z['wd'] > cur['wd'] + 1e-9 or (abs(z['wd'] - cur['wd']) <= 1e-9 and z['order'] < cur['order']):
                    by[z['a']] = z
            if len(by) <= k:
                continue
            A = sorted(by.values(), key=lambda u: (-u['wd'], u['a']))
            val, pick = value_of(A, list(ds))
            if not val > 0 or val == float('inf'):
                continue
            if any((h[0] & gm) == h[0] and h[1] >= val - 1e-9 for h in named):
                continue
            named.append((gm, val))
            # the looks in the order the words need them: those the best assignment takes, then the one it leaves open
            order = [u for u in pick[0] if u >= 0] + ([pick[1]] if pick[1] >= 0 else [])
            order += [u for u in range(len(A)) if u not in order]
            out.append(dict(d=ds[0], ds=list(ds), value=val, threats=[dict(a=A[u]['a'], c=A[u]['c'], t=A[u]['t'], worth=A[u]['wd'], now=A[u]['now']) for u in order],
                            near_key=all(5 <= u['c'][0] <= 11 and 1 <= u['c'][1] <= 7 for u in A)))
    return out


def cov_off_fresh(s):
    """Step 21 (engine.js covOffFresh, D-206): the defence as it really is this phase, the offence fresh (its full turn
    to come, whatever it has spent): spent, it still moves first next phase, before the defence can answer again."""
    return s.with_(tok_o=RC.TOKENS_PER_PHASE, moved_o=0, qs_o=0, lock_o=0, rush_o=0, cnt=(0,) * 6 + tuple(s.cnt[6:]), turn_n=0, side='O',
                   stage='play', approach=-1, prev_wait='', final=False, turn_lead=-1, turn_x=(), turn_moved=0, react_moved=0)


def map_read(f, cfg=None):
    """Step 30b (engine.js covBuild's memory): the board's reading and its map, worked out once per think. The key is
    the state itself (every field) with its context and the reading's settings."""
    from . import memo
    return memo.get('map', (id(f.ctx), f, id(cfg)), lambda: _map_read_calc(f, cfg))


def _map_read_calc(f, cfg):
    r = Read(f, cfg=cfg)
    return r, r.map_options()


def lasting_of(s, cfg=None, fresh=False, r0=None):
    """engine.js lastingOf (step 21, D-206): the lasting gap of a position, read with what each side really has left
    this phase (its tokens and movement, who is locked or rushed, who has moved); fresh: step 20's like-for-like read
    (cov_fresh), for the reports' phase starts. A pass in the air: the catch by the rules' own chance (cov_pass);
    caught, the receiver's lasting gap; intercepted (D-198), -5 and the next phase read fresh with the ball back with
    the passer. None in the last phase. -> {L, before, ov, moves, best}."""
    if s.stage != 'play' or s.clock <= RC.PHASE_SECONDS:
        return None
    if fresh:
        f = cov_fresh(s)
        r = Read(f, cfg=cfg)
        opts = r.map_options()
    elif s.pending:
        recv = s.pending[1]
        base = s.with_(pending=None, approach=-1)
        p = cov_pass(base, recv, base.o[recv])
        gc = lasting_of(base.with_(ball=recv), cfg)
        gl = lasting_of(base, cfg, fresh=True) if s.clock - RC.PHASE_SECONDS > RC.PHASE_SECONDS else None
        L = p * (gc['L'] if gc else 0.0) + (1 - p) * ((gl['L'] if gl else 0.0) - 5)
        return dict(L=L, before=gc['before'] if gc else 0.0, ov=gc['ov'] if gc else 0, moves=gc['moves'] if gc else 0,
                    best=gc['best'] if gc else None, opts=gc.get('opts') if gc else None, catch=p, list=gc.get('list') if gc else None)
    else:
        r, opts = map_read(cov_off_fresh(s), cfg)
    best = r.lasting(opts)
    before = max((o[2] for o in opts.values() if o[0] > 0), default=0.0)
    three = three_seconds_owed(s) if not fresh else 0
    return dict(L=best['L'] - 5 * three, before=before, ov=len(best['ov']), moves=len(best['moves']), best=best, opts=opts, three=three,
                list=r._lg_list(best['root']))


def bars_of(s, cfg=None):
    """Step 25 (engine.js barsOf, D-242): the shot bar phase by phase, the value of playing on. V(0) = 0; with n phases
    left, V(n) = the best of playing on (V(n-1)), the lasting gap, and each look at its chance: reached, its value or
    V(n-1) if more; missed, V(n-1) less what the miss costs. -> [{phase, clock, bar}]."""
    g = lasting_of(s, cfg)
    n0 = s.clock // RC.PHASE_SECONDS - 1
    V = [0.0]
    if g and g.get('best'):
        opts = [(x['r'], x['w'] + x['src'][9], x['src'][8]) for x in g['best']['o'] if x['r'] > 0 and x['w'] not in (float('inf'), float('-inf'))]
        for n in range(1, n0 + 1):
            prev = V[n - 1]
            v = max(prev, g['L'])
            for r, val, lc in opts:
                e = r * max(val, prev) + (1 - r) * (prev - lc)
                if e > v:
                    v = e
            V.append(v)
    out, c, k = [], s.clock, 1
    while c > 0:
        n = c // RC.PHASE_SECONDS - 1
        out.append(dict(phase=k, clock=c, bar=round(V[n], 2) if 0 < n < len(V) else 0.0))
        c -= RC.PHASE_SECONDS
        k += 1
    return out


def top_of(s, cfg=None):
    """engine.js topOf (step 22b, D-219): the largest item on the list of things to cover, the defence as it stands and
    before it answers; read as the lasting gap is (each side with what it has left; a pass in the air by the catch's
    chance; the three-second rule's -5 counted). None in the last phase."""
    if s.stage != 'play' or s.clock <= RC.PHASE_SECONDS:
        return None

    def read(f):
        r, opts = map_read(f, cfg)
        return r._lg_list(r._lg_root(opts))[0]
    if s.pending:
        recv = s.pending[1]
        base = s.with_(pending=None, approach=-1)
        p = cov_pass(base, recv, base.o[recv])
        tc = top_of(base.with_(ball=recv), cfg)
        tl = read(cov_fresh(base)) if s.clock - RC.PHASE_SECONDS > RC.PHASE_SECONDS else 0.0
        return p * (tc if tc is not None else 0.0) + (1 - p) * (tl - 5)
    return read(cov_off_fresh(s)) - 5 * three_seconds_owed(s)


def three_seconds_owed(s):
    """Step 22 (engine.js threeSecondsOwed, D-211): the attackers in the key at the last phase end who can't leave it
    before this phase ends with what the offence really has left: each is -5 at the phase end."""
    from .actions import can_move_kind
    if not RC.app_rule(s.ctx.rules, 'three_seconds') or not s.key_o:
        return 0
    n = 0
    for i in range(5):
        if not (s.key_o >> i) & 1 or not B.in_key(s.o[i]):
            continue
        if not (s.tok_o > 0 and any(can_move_kind(s, 'O', i, k) for k in ('move', 'qs', 'sprint'))):
            n += 1
    return n


def map_threats(g):
    """Step 22 (engine.js lgThreats, D-212): the map's own threats as the offence's first actions: [(attacker, the
    square he must have the ball on when the next phase starts)] for the best three looks the answer leaves and each
    overload's looks."""
    if not g or not g.get('best') or g.get('opts') is None:
        return []
    best, opts = g['best'], g['opts']
    head = sorted((x for x in best['o'] if x['r'] > 0), key=lambda x: (-x['e'], x['key']))[:3]
    out = [(x['key'][0], x['src'][6]) for x in head]
    for v in best['ov']:
        for z in v['threats']:
            o = opts.get((z['a'], z['c'], False)) or opts.get((z['a'], z['c'], True))
            if o is not None:
                out.append((z['a'], o[6]))
    return out


MAP_ME = [None]            # step 18s, stop two: the side whose decision the search in hand is (search.Searcher sets it)


def pass_by_rules(rules):
    """Step 18s, stop two (D-199): is the reading's pass chance the rules' own? It is wherever the Intercept is the
    current rule ('move_then_intercept') and eval.pass_rules is not switched off."""
    return rules.intercept_rule == 'move_then_intercept' and CONFIG['eval'].get('pass_rules', True) is not False


def icpt_pi(s, pa, pc, j, p, arrow, can_move, qs_left, occ, passer, recv=-1):
    """Step 18s, stop two: the best chance defender j, on p with this arrow and with can_move / qs_left left to him,
    takes a pass from pa to pc, by the rules' own Intercept: through his square (not next to the passer), or one
    straight Move, Quick Step or Sprint along one of his arrow lines to the square where it meets the pass (not next
    to the passer, the way clear), and then the Intercept, rolled as he then stands. 0.0: by the rules he can't."""
    rules = s.ctx.rules
    if s.tok_x <= 0 or s.count('X', 'intercept') >= RC.LIMITS['X']['intercept']:
        return 0.0
    base = s.ctx.dfn[j].r['intercept']
    cut = RC.off_balance_cut(rules)
    best = None
    if B.cheb(p, pa) != 1 and B.on_segment(p, pa, pc, rules.on_line_tolerance):
        best = base - cut if cut and s.rushed('X', j) else base
    if s.tok_x >= 2 and (can_move or qs_left > 0) and (best is None or best < base):
        broken = rules.zone != 'off' and any(b[1] == j for b in s.beaten)
        qs = s.ctx.dfn[j].qs
        for d in G.lines(rules, G.stance(rules, arrow, broken)):   # (a screen's T: the screens below stop a diagonal, step 22b)
            n = lane_meet(p, d, pa, pc)
            if not n:
                continue
            step = B.DIRS[d]
            path = [(p[0] + step[0] * k, p[1] + step[1] * k) for k in range(1, n + 1)]
            q = path[-1]
            if B.cheb(q, pa) == 1 or any(not B.on_board(z) or z in occ for z in path):
                continue
            ok = True
            for scr in s.screens:
                if scr[0] == recv and pc != s.o[recv]:
                    continue                                 # the receiver has moved to catch it: his screen is gone
                tsq = B.add(s.o[scr[0]], B.DIRS[scr[1]])
                if scr[3] >> j & 1:
                    if q == tsq:
                        ok = False
                        break
                    continue
                prev = p
                for z in path:
                    if B.diag_step_banned(prev, z, tsq, rules):
                        ok = False
                        break
                    prev = z
                if not ok:
                    break
            if not ok:
                continue
            orth = d % 2 == 0
            if can_move and n <= (RC.MOVE_STRAIGHT if orth else RC.MOVE_DIAGONAL):
                roll = base                                  # a Move: he is set when he gets there
            elif qs_left > 0 and qs > 0 and (n <= qs if rules.qs_up_to else n == qs):
                roll = base - cut                            # a Quick Step or a Sprint: off balance (D-185)
            elif (can_move and qs_left > 0 and (qs > 0 or not rules.sprint_needs_qs)
                  and n <= (rules.sprint_orth_base if orth else rules.sprint_diag_base) + qs):
                roll = base - cut
            else:
                continue
            if best is None or roll > best:
                best = roll
    if best is None:
        return 0.0
    return 1 - float(p_success(passer - best, rules))


def _lane_p_calc(s, i, c, reach=False):
    rules = s.ctx.rules
    a = s.o[s.ball]
    if not (B.on_board(a) and B.on_board(c)):
        return 0.0
    if rules.receiver_denial:
        den = lane_squares(a, c, float(rules.receiver_denial_tol))
        if any(xp in den and B.adjacent(xp, c) for xp in s.x):
            return 0.0
    if pass_by_rules(rules):                             # step 18s, stop two: who can take it is the rules' own answer
        passer = rolled(s, 'O', s.ball, 'pass')
        occ = set(s.x)
        occ.update(q for k, q in enumerate(s.o) if k != i)
        occ.add(c)
        worst = 0.0
        for d, xp in enumerate(s.x):
            can_move, qs_left = _caps(s, 'X', d)
            pi = icpt_pi(s, a, c, d, xp, s.arrows[d], can_move, qs_left, occ, passer, i)
            if pi > worst:
                worst = pi
        return 1.0 - worst
    lane = lane_squares(a, c, 0.5)
    if not lane:
        return 1.0
    passer = rolled(s, 'O', s.ball, 'pass')              # D-185: off balance, each player as he stands now
    worst = 0.0
    for d, xp in enumerate(s.x):
        can_move, qs_left = _caps(s, 'X', d)
        one = _exact_one(s, d) if reach else _one_action(xp, s.arrows[d], s.ctx.dfn[d].qs, can_move, qs_left, rules)
        if lane.isdisjoint(one):
            continue
        pi = 1 - float(p_success(passer - rolled(s, 'X', d, 'intercept'), rules))
        if pi > worst:
            worst = pi
    return 1.0 - worst


def _lane_p_moved(s, c, j, q, a, can_move, qs_left, i=None):
    """Step 18e: _lane_p's geometry with defender j at q facing a, with can_move / qs_left left to him (the open
    list's re-read of a moved defender)."""
    rules = s.ctx.rules
    pa = s.o[s.ball]
    if not (B.on_board(pa) and B.on_board(c)):
        return 0.0
    lane = lane_squares(pa, c, 0.5)
    for d, xp in enumerate(s.x):
        at = q if d == j else xp
        if at in lane and B.adjacent(at, c):
            return 0.0
    if pass_by_rules(rules):                             # step 18s, stop two
        passer = rolled(s, 'O', s.ball, 'pass')
        occ = set(s.x[:j] + (q,) + s.x[j + 1:])
        occ.update(z for k, z in enumerate(s.o) if k != i)
        occ.add(c)
        worst = 0.0
        for d, xp in enumerate(s.x):
            if d == j:
                pi = icpt_pi(s, pa, c, d, q, a, can_move, qs_left, occ, passer, -1 if i is None else i)
            else:
                cm, ql = _caps(s, 'X', d)
                pi = icpt_pi(s, pa, c, d, xp, s.arrows[d], cm, ql, occ, passer, -1 if i is None else i)
            if pi > worst:
                worst = pi
        return 1.0 - worst
    if not lane:
        return 1.0
    passer = rolled(s, 'O', s.ball, 'pass')              # D-185: off balance, each player as he stands now
    worst = 0.0
    for d, xp in enumerate(s.x):
        if d == j:
            one = _one_action(q, a, s.ctx.dfn[d].qs, can_move, qs_left, rules)
        else:
            cm, ql = _caps(s, 'X', d)
            one = _one_action(xp, s.arrows[d], s.ctx.dfn[d].qs, cm, ql, rules)
        if lane.isdisjoint(one):
            continue
        pi = 1 - float(p_success(passer - rolled(s, 'X', d, 'intercept'), rules))
        if pi > worst:
            worst = pi
    return 1.0 - worst


def _pass_prob(s, i):
    """P(a pass from the carrier to attacker i now arrives): 0 if not legal; else 1 - the best Intercept chance
    over the defence's legal intercepts once it is in the air (the rules' own options)."""
    key = (s.ctx, s.o, s.x, s.arrows, s.ball, i, s.cnt, s.tok_x, s.moved_x, s.qs_x, s.lock_x, s.screens, _off_balance_key(s),   # (step 21: the context, not its id)
           s.beaten if pass_by_rules(s.ctx.rules) else None)
    if key in _PP:
        return _PP[key]
    from .actions import Action, legal_actions, mti_approach
    from .resolve import apply, ChanceNode
    st = s.with_(side='O', stage='play', turn_n=0, tok_o=max(1, s.tok_o), pending=None)
    a = Action('pass', 'O', s.ball, target=i)
    try:
        if a not in legal_actions(st):
            p = 0.0
        else:
            nxt = apply(st, a)
            worst = 0.0
            if not isinstance(nxt, ChanceNode) and nxt.stage == 'play' and nxt.side == 'X' and nxt.pending:
                jump = pass_by_rules(s.ctx.rules)        # step 18s, stop two: one movement and then the Intercept counts too
                for b in legal_actions(nxt):
                    if b.kind == 'intercept':
                        worst = max(worst, 1 - float(p_success(rolled(nxt, 'O', s.ball, 'pass') - rolled(nxt, 'X', b.piece, 'intercept'),
                                                               s.ctx.rules)))
                    elif jump and b.kind in ('move', 'qs', 'sprint') and mti_approach(nxt, b):
                        af = apply(nxt, b)
                        if not isinstance(af, ChanceNode) and af.pending:
                            worst = max(worst, 1 - float(p_success(rolled(af, 'O', s.ball, 'pass') - rolled(af, 'X', b.piece, 'intercept'),
                                                                   s.ctx.rules)))
            p = 1.0 - worst
    except Exception:
        p = 0.0
    if len(_PP) > 200000:
        _PP.clear()
    _PP[key] = p
    return p


_PP = {}


# ---- team fouls across the quarter (step 3n F4) ----------------------------------------------------------------------

_FOUL = {}


def foul_table(ctx):
    """The future cost of the defence's team fouls over the rest of the quarter, by backward induction over (team
    fouls, possessions left). C(f, n): the offence's expected extra points in the defence's n remaining possessions with
    f team fouls. In a possession the defence fouls with the engine's estimated rate; from the bonus (the bonus_from-th
    team foul on) a steal foul is two free throws for the pairing's cards (and, D-89, the +5) and ends the possession,
    instead of +5 and play on."""
    rules = ctx.rules
    fiba_sf = RC.app_rule(rules, 'fiba_steal_foul')
    key = (id(ctx.off), id(ctx.dfn), rules.bonus_from, rules.quarter_possessions, rules.steal_foul_always_plus5, fiba_sf)
    if key in _FOUL:
        return _FOUL[key]
    q = CONFIG['eval'].get('fouls_per_possession', 0.25)
    ft2 = sum(RC.FT_MULT_TWO * c.r['free_throw'] for c in ctx.off) / len(ctx.off)
    cont = CONFIG['eval'].get('play_on_value', 20.0)
    plus5 = RC.STEAL_FOUL_BONUS if rules.steal_foul_always_plus5 and not fiba_sf else 0     # D-89: the bonus foul is +5 as well
    # a bonus foul against an ordinary one: +5 and play on; in the app (D-179, D-181) no foul carries +5: two free
    # throws against play on
    extra = ft2 + plus5 - ((0 if fiba_sf else RC.STEAL_FOUL_BONUS) + cont)
    N, F = rules.quarter_possessions + 1, rules.bonus_from + 12
    C = [[0.0] * (N + 1) for _ in range(F + 2)]
    for n in range(1, N + 1):
        for f in range(F, -1, -1):
            x = extra if f + 1 >= rules.bonus_from else 0.0
            C[f][n] = (1 - q) * C[f][n - 1] + q * (x + C[min(F, f + 1)][n - 1])
    _FOUL[key] = (C, F)
    return C, F


def foul_marginal(ctx, f, n):
    """What one more defensive foul now (team fouls f, n possessions left including this one) costs the defence over
    the rest of the quarter, in the offence's points: C(f + 1, n - 1) - C(f, n - 1)."""
    if not ctx.rules.digital or n <= 0:
        return 0.0
    C, F = foul_table(ctx)
    n1 = max(0, n - 1)
    return C[min(F, f + 1)][n1] - C[min(F, f)][n1]


def foul_externality(s):
    """The quarter's price of the fouls the defence has committed this possession (added to the offence's value)."""
    ctx = s.ctx
    if not ctx.rules.digital or not s.fouls or not ctx.quarter_left or RC.app_rule(ctx.rules, 'points_play_on'):
        return 0.0                                   # D-198: a foul is +5 and nothing else; 18i's price is retired
    return sum(foul_marginal(ctx, ctx.team_fouls + i, ctx.quarter_left) for i in range(s.fouls))


# ---- the coarse value table (B4) -------------------------------------------------------------------------------------

def capacity(s):
    """The defence's spent capacity, summarised (addendum B4): how many defenders can still close out (a Move or a
    Quick Step left, and tokens) from the perimeter (long-two, three and beyond) and from the paint (the rim and
    mid-range zones)."""
    return _capacity(s.x, s.moved_x, s.qs_x, s.lock_x, s.tok_x, s.cnt[6], s.ctx.rules.qs_once_per_player)


def _capacity(xs, moved_x, qs_x, lock_x, tok_x, x_qs_used, once=True):
    per = paint = 0
    if tok_x <= 0:
        return 0, 0
    for j, q in enumerate(xs):
        can_move = not (moved_x >> j & 1) and not (lock_x >> j & 1)
        can_qs = x_qs_used < RC.LIMITS['X']['qs'] and not (once and qs_x >> j & 1)
        if not (can_move or can_qs) or not B.on_board(q):
            continue
        if B.zone(q) in ('K', 'M'):
            paint += 1
        else:
            per += 1
    return min(per, 3), min(paint, 2)


def coarse_key(s):
    """(ball zone, defended?, phase, offence tokens bucket, capacity): the coarsened state."""
    return _key(s.o[s.ball], any(B.adjacent(xp, s.o[s.ball]) for xp in s.x), s.clock, s.tok_o, capacity(s))


def _key(bp, defended, clock, tok_o, cap):
    z = B.zone(bp) if B.on_board(bp) else '.'
    tok = 0 if tok_o <= 0 else 1 if tok_o <= 2 else 2 if tok_o <= 4 else 3
    phase = min(6, max(1, (RC.START_CLOCK - clock) // RC.PHASE_SECONDS + 1))
    return f'{z}|{int(defended)}|{phase}|{tok}|{cap[0]}{cap[1]}'


def key_from_encode(enc):
    """The coarse key of a state from its one-line encoding (state.encode), so stored snapshots can be re-solved."""
    f = {}
    for part in enc.split('|'):
        if part.startswith('c') and part[1:].isdigit():
            f['clock'] = int(part[1:])
        elif part.startswith('t') and '/' in part:
            a, b = part[1:].split('/')
            f['tok_o'], f['tok_x'] = int(a), int(b)
        elif part.startswith('O') and ',' in part:
            f['o'] = [B.parse_sq(q) for q in part[1:].split(',')]
        elif part.startswith('X') and ',' in part:
            f['x'] = [B.parse_sq(q.rstrip('NESW')) for q in part[1:].split(',')]
        elif part.startswith('b') and part[1:].isdigit():
            f['ball'] = int(part[1:]) - 1
        elif part.startswith('m') and len(part) == 5:
            f['moved_x'] = int(part[3:5], 16)
        elif part.startswith('n') and part[1:].isdigit():
            f['x_qs'] = int(part[1:][6])
        elif part.startswith('L') and len(part) == 5:
            f['lock_x'] = int(part[3:5], 16)
        elif part.startswith('q') and len(part) == 5:
            f['qs_x'] = int(part[3:5], 16)
    bp = f['o'][f['ball']]
    cap = _capacity(f['x'], f.get('moved_x', 0), f.get('qs_x', 0), f.get('lock_x', 0), f['tok_x'], f.get('x_qs', 0))
    return _key(bp, any(B.adjacent(xp, bp) for xp in f['x']), f['clock'], f['tok_o'], cap)


_TABLES = {}


def relative_average(s, cfg=None, budget=False):
    """Step 10: the average continuation read of the positions the phase table was built from, at this position's
    phase (eval.relative_average[age/standard][phase]); 0 if there is none."""
    cfg = cfg or CONFIG['eval']
    lv = getattr(s.ctx, 'levels_key', None) or ('senior', 'pro')
    tab = cfg.get('relative_average_budget' if budget else 'relative_average') or cfg.get('relative_average', {})
    row = tab.get(f'{lv[0]}/{lv[1]}') or tab.get('senior/pro') or {}
    phase = coarse_key(s).split('|')[2]
    return float(row.get(phase, 0.0))


def vcoarse(s, age='senior', standard='pro'):
    """The coarse value of a state, from vcoarse.json (solved by backward induction over the phases from stored
    possessions: engine self-play to seed, refined from stored games), by age and standard."""
    lv = getattr(s.ctx, 'levels_key', None) or (age, standard)
    tab = _TABLES.get(lv)
    if tab is None:
        tab = _load_table(lv)
    k = coarse_key(s)
    if k in tab:
        return tab[k]
    short = '|'.join(k.split('|')[:4])                # the key without the capacity summary
    return tab.get(short, tab.get('_phase' + k.split('|')[2], 0.0))


def _load_table(lv):
    path = os.path.join(HERE, 'data', 'vcoarse.json')
    tab = {}
    try:
        allt = json.load(open(path))
        tab = allt.get(f'{lv[0]}/{lv[1]}') or allt.get('senior/pro') or {}
    except (OSError, ValueError):
        tab = {}
    _TABLES[lv] = tab
    return tab


def solve_coarse(records):
    """Backward induction over the 6 phases. records: possessions as [(coarse key at each turn group start), ...,
    final score]. V(k at phase p) = mean over transitions from k of V(next key) (or the final score at the end),
    solved from the last phase back, shrunk toward the phase mean for rare keys."""
    by_phase = {p: {} for p in range(1, 7)}
    for keys, final in records:
        for n, k in enumerate(keys):
            nxt = keys[n + 1] if n + 1 < len(keys) else None
            p = int(k.split('|')[2])
            by_phase[p].setdefault(k, []).append((nxt, final))
    V = {}
    prior = 8
    if records and records[0][0] and records[0][0][0].count('|') >= 4:
        # solve the table without the capacity summary first: the fallback for capacity keys never seen
        V.update({k: v for k, v in solve_coarse([(['|'.join(k.split('|')[:4]) for k in keys], f)
                                                 for keys, f in records]).items() if not k.startswith('_')})
    for p in range(6, 0, -1):
        rows = by_phase[p]
        tot = []
        for k, trs in rows.items():
            vals = [V.get(nk, final) if nk else final for nk, final in trs]
            tot += vals
        pm = sum(tot) / len(tot) if tot else 0.0
        V[f'_phase{p}'] = round(pm, 2)
        for k, trs in rows.items():
            vals = [V.get(nk, final) if nk else final for nk, final in trs]
            V[k] = round((sum(vals) + prior * pm) / (len(vals) + prior), 2)
    return V


def solve_phase_table(records, prior=8):
    """Step 3n Part C: the coarse table as the expected final value of every possession alive at the start of phase k.
    records: possessions as [(phase, coarse key) at each offence turn-group start, ...] and the final score (turnovers
    and expiry included, at their 0). One key per possession per phase: the key at the phase's first turn group. Backward
    induction from phase 6: a key's value is the mean, over the possessions that start the phase with it, of the next
    phase's key value (if the possession lives to the next phase) or the final score, shrunk toward the phase value V_k
    (the mean over every possession alive at the start of phase k) for rare keys. The table without the capacity summary
    is solved the same way, as the fallback for capacity keys never seen. Returns the table; '_phase{k}' holds V_k."""
    starts = []
    for keys, final in records:
        by = {}
        for item in keys:
            ph, k = item if isinstance(item, (tuple, list)) else (int(item.split('|')[2]), item)
            by.setdefault(ph, k)
        starts.append((by, final))

    def solve(trim):
        V = {}
        for ph in range(6, 0, -1):
            rows = {}
            alive = []
            for by, final in starts:
                if ph not in by:
                    continue
                k = by[ph] if not trim else '|'.join(by[ph].split('|')[:4])
                nxt = by.get(ph + 1)
                if nxt is not None:
                    nk = nxt if not trim else '|'.join(nxt.split('|')[:4])
                    tgt = V.get(nk, final)
                else:
                    tgt = final
                rows.setdefault(k, []).append(tgt)
                alive.append(final)
            vk = sum(alive) / len(alive) if alive else 0.0
            V[f'_phase{ph}'] = round(vk, 2)
            V[f'_alive{ph}'] = len(alive)
            for k, vals in rows.items():
                V[k] = round((sum(vals) + prior * vk) / (len(vals) + prior), 2)
        return V
    V = {k: v for k, v in solve(True).items() if not k.startswith('_')}
    V.update(solve(False))
    return V


def points_by_end_phase(records_with_end):
    """The selection effect, reported apart from the table: the mean final score by the phase a possession ended in."""
    by = {}
    for ph, final in records_with_end:
        by.setdefault(ph, []).append(final)
    return {ph: dict(possessions=len(v), points=round(sum(v) / len(v), 2)) for ph, v in sorted(by.items())}


# ---- config ----------------------------------------------------------------------------------------------------------

def load_config():
    return json.load(open(os.path.join(HERE, 'data', 'ai_profiles.json')))


CONFIG = load_config()
