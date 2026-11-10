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
from .scoring import p_success, p_foul, p_fouls, foul_on_shot_points

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
    if exact:
        from .actions import movement_dests, can_move_kind
        rules = s.ctx.rules
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(s, 'O', i, kind):
                for q in movement_dests(s, 'O', i, kind, rules):
                    out.setdefault(q, 1)
        if s.tok_o >= 2:
            for q in [q for q, n in out.items() if n == 1]:
                for q2 in _geo_paths('qs' if can_move else 'move', q, card.qs, rules):
                    if q2 not in out and q2 not in s.x and q2 not in s.o:
                        out[q2] = 2
        return out
    free, fixed = geo_reach(s.o[i], 0, card.qs, can_move, qs_left, s.ctx.rules)
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
    two = foul and rules.reach_angle_fouls and B.dist_rim(q) >= B.dist_rim(c)
    if pen and foul:
        two = rules.reach_angle_fouls
    return KINDS.index((pen, foul, bool(two)))


@lru_cache(maxsize=400000)
def _terms(rules, q, a, c):
    e, foul, pen, _ = G.terms(rules, q, a, c)
    return e, foul, pen


def contest_map(rules, free, fixed):
    """c -> [fewest actions for each contest kind (KINDS order)], from a defender's reach maps."""
    out = {}
    for q, n in free.items():                 # after a Move: any arrow; face the shooter
        for dx, dy in NEAR:
            c = (q[0] + dx, q[1] + dy)
            if not B.on_board(c):
                continue
            e, foul, pen = _terms(rules, q, B.dir_between(q, c), c)
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
                e, foul, pen = _terms(rules, q, a, c)
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
def _cmap_cached(rules, frm, arrow, qs, can_move, qs_left):
    free, fixed = geo_reach(frm, arrow, qs, can_move, qs_left, rules)
    return contest_map(rules, free, fixed)


# ---- shot values -------------------------------------------------------------------------------------------------------

def shot_value(card, dcards, t, c, contests, window, rules):
    """Expected shot value of `card` shooting type t from c, the defence choosing its best contest among defenders
    that can reach a contest within `window` actions. contests: {d: row}. Returns (value, best defender or -1)."""
    pts = RC.ZONE_POINTS[B.zone(c)]
    r = card.shot(t)
    best, who = pts * r, -1
    ft = None
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
                if ft is None:
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
    __slots__ = ('i', 'c', 'route', 'p', 'now', 'open', 'vals', 'types', 'minex', 'base', 'replies')

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

    # -- contest maps
    def _contest(self, d, at=None, arrow=None, used=None):
        s = self.s
        if not B.on_board(s.x[d]):
            return {}
        if at is None and (self.exact or self.cfg.get('reach')):
            # step 12 (eval.reach): the reach map's exact movement (blocking, screens, locks) for every reading
            free, fixed = defender_map(s, d, exact=True)
            return contest_map(self.rules, free, fixed)
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
            return contest_map(self.rules, {}, {frm: {a: 0}})
        return _cmap_cached(self.rules, frm, a, s.ctx.dfn[d].qs, can_move, qs_left)

    def _vals2(self, look, d, row):
        """Step 16: the same, for a look a phase away: any Contest he reaches with two movement actions."""
        keep, self.react_moves = self.react_moves, 2
        try:
            return self._vals(look, d, row)
        finally:
            self.react_moves = keep

    def _vals(self, look, d, row, moves=None):
        """Expected value per shot type if defender d (contest row `row`) contests look within the reaction (moves: with
        at most that many of the reaction's movements; 0 = from where he stands)."""
        out = {}
        if row is None:
            return None
        limit = self.react_moves if moves is None else min(moves, self.react_moves)
        card = self.s.ctx.off[look.i]
        pts = RC.ZONE_POINTS[B.zone(look.c)]
        rules = self.rules
        for t in look.types:
            r = card.shot(t)
            best = None
            for k, n in enumerate(row):
                if n > limit:
                    continue
                pen, foul, two = KINDS[k]
                con = self.dcards[d].con(t) - (RC.FAR_CONTEST_PENALTY if pen else 0)
                if rules.floor_contest_zero:
                    con = max(0, con)
                v = pts * (r - con)
                if rules.floor_declared_shot:
                    v = max(0, v)
                if foul:
                    ft = foul_on_shot_points(card, t, pts, rules)[0]
                    pf = float(p_fouls(p_foul(self.dcards[d].r['foul_contest'], rules), 2 if two else 1))
                    v = pf * ft + (1 - pf) * v
                if best is None or v < best:
                    best = v
            if best is not None:
                out[t] = best
        return out or None

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
        for c, n in reach.items():
            z = B.zone(c)
            if z not in SHOOT:
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
            lk.open = {t: pts * card.shot(t) for t in lk.types}
            lk.vals = {}
            for d in self.att_x:
                v = self._vals(lk, d, self._cm[d].get(c))
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
        for q, a, used in cands:
            cm = self._contest(j, q, a, used)
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
                        v = lk.swapped(j, self._vals(lk, j, row) if row is not None else None, p_new)
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

    def leaf(self):
        """V_leaf from the offence's point of view (expected possession value, game units): the best of the shot
        now, the best look the defence can't cover in its next turn (released this turn: uncoverable), and the
        coarse table."""
        s = self.s
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (0 if s.ctx.rules.digital else RC.TURNOVER_POINTS * s.tos)
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
        if self.cfg.get('leaf_mode', 'floor') == 'relative':
            # step 10 (behind the switch): the phase table's average plus how much better or worse this position reads
            # than an average position at that phase, read the same way (eval.relative_average, from the step 3n seeds)
            return banked + max(sn or 0.0, now, coarse + cont - relative_average(s, self.cfg, self._budget_on()))
        return banked + max(sn or 0.0, now, cont, coarse)

    def possession(self):
        """Step 12 (stable search, 'play on while pending'): what the position is worth without the ball handler's shot
        now: the leaf with the carrier's shot left out (a look another attacker releases this turn still counts)."""
        s = self.s
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (0 if s.ctx.rules.digital else RC.TURNOVER_POINTS * s.tos)
        banked += foul_externality(s)
        now = max((lk.base for i in self.att_o for lk in self.looks[i]
                   if lk.now and not (i == s.ball and lk.route == 'shoot')), default=0.0)
        if not self.o_to_act and s.tok_o <= 0 and s.clock <= RC.PHASE_SECONDS:
            return banked + now
        cont, coarse = self.continuation(), vcoarse(s)
        if self.cfg.get('leaf_mode', 'floor') == 'relative':
            return banked + max(now, coarse + cont - relative_average(s, self.cfg, self._budget_on()))
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
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (0 if s.ctx.rules.digital else RC.TURNOVER_POINTS * s.tos)
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
            if c in here or c in occ:
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


def turnover_value(s):
    """What a pick-off leaves the offence: 0 in the digital format or the final phase; else -5 and the clock cost,
    then the coarse value of playing on."""
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
    key = (id(s.ctx), s.o[s.ball], s.ball, c, s.x, s.arrows, s.moved_x, s.qs_x, s.lock_x, s.tok_x, s.cnt[6], reach,
           s.o if reach else None, s.screens if reach else None)
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


def _lane_p_calc(s, i, c, reach=False):
    rules = s.ctx.rules
    a = s.o[s.ball]
    if not (B.on_board(a) and B.on_board(c)):
        return 0.0
    if rules.receiver_denial:
        den = lane_squares(a, c, float(rules.receiver_denial_tol))
        if any(xp in den and B.adjacent(xp, c) for xp in s.x):
            return 0.0
    lane = lane_squares(a, c, 0.5)
    if not lane:
        return 1.0
    passer = s.ctx.off[s.ball].r['pass']
    worst = 0.0
    for d, xp in enumerate(s.x):
        can_move, qs_left = _caps(s, 'X', d)
        one = _exact_one(s, d) if reach else _one_action(xp, s.arrows[d], s.ctx.dfn[d].qs, can_move, qs_left, rules)
        if lane.isdisjoint(one):
            continue
        pi = 1 - float(p_success(passer - s.ctx.dfn[d].r['intercept'], rules))
        if pi > worst:
            worst = pi
    return 1.0 - worst


def _pass_prob(s, i):
    """P(a pass from the carrier to attacker i now arrives): 0 if not legal; else 1 - the best Intercept chance
    over the defence's legal intercepts once it is in the air (the rules' own options)."""
    key = (id(s.ctx), s.o, s.x, s.arrows, s.ball, i, s.cnt, s.tok_x, s.moved_x, s.qs_x, s.lock_x, s.screens)
    if key in _PP:
        return _PP[key]
    from .actions import Action, legal_actions
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
                for b in legal_actions(nxt):
                    if b.kind == 'intercept':
                        worst = max(worst, 1 - float(p_success(s.ctx.off[s.ball].r['pass'] - s.ctx.dfn[b.piece].r['intercept'],
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
    key = (id(ctx.off), id(ctx.dfn), rules.bonus_from, rules.quarter_possessions, rules.steal_foul_always_plus5)
    if key in _FOUL:
        return _FOUL[key]
    q = CONFIG['eval'].get('fouls_per_possession', 0.25)
    ft2 = sum(RC.FT_MULT_TWO * c.r['free_throw'] for c in ctx.off) / len(ctx.off)
    cont = CONFIG['eval'].get('play_on_value', 20.0)
    plus5 = RC.STEAL_FOUL_BONUS if rules.steal_foul_always_plus5 else 0     # D-89: the bonus foul is +5 as well
    extra = ft2 + plus5 - (RC.STEAL_FOUL_BONUS + cont)  # a bonus foul against +5 and play on
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
    if not ctx.rules.digital or not s.fouls or not ctx.quarter_left:
        return 0.0
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
