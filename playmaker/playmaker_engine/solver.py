"""Step 2: the scenario solver.

Three parts, all on top of the unchanged engine:
  * exact_solve   : expectimax over raw engine actions with a transposition table (exact).
  * evaluate      : fast position value: the best look the offence can get on its next turn
                    against the defence's best two-action reaction (the regression ceiling, generalised).
  * Searcher      : depth-limited expectimax over basketball plays (candidate generator) with the
                    evaluation at the leaves, iterative deepening under a time budget, exact
                    probabilities at chance nodes, and the exact solver for the tail.
Values are per Coach's Call target (a tuple); ordinary cards have one entry.
"""
import random
import time
from dataclasses import dataclass, field

from . import board as B
from . import geometry as G
from . import rules_config as RC
from .actions import Action, legal_actions, movement_dests, can_move_kind, MOVEMENT, intercept_status, t_square
from .resolve import apply, ChanceNode
from .scoring import score, contest_rating, foul_on_shot_points, p_success, band
from .solver_config import DEFAULT
from .state import CI


class Timeout(Exception):
    pass


# =====================================================================================
# values
# =====================================================================================

@dataclass(frozen=True)
class Val:
    """Expected possession score, expected look, P(look >= 30), P(clock reaches 0),
    expected forced-shot points (counted only when the clock expires)."""
    ev: float
    look: float = 0.0
    p30: float = 0.0
    pexp: float = 0.0
    fs: float = 0.0


def mix(pairs):
    """Weighted average of Val tuples: pairs = [(p, (Val, ...)), ...]."""
    n = len(pairs[0][1])
    out = []
    for t in range(n):
        ev = look = p30 = pexp = fs = 0.0
        for p, vs in pairs:
            v = vs[t]
            ev += p * v.ev
            look += p * v.look
            p30 += p * v.p30
            pexp += p * v.pexp
            fs += p * v.fs
        out.append(Val(ev, look, p30, pexp, fs))
    return tuple(out)


def terminal_vals(s, targets):
    out = []
    for t in targets:
        st = s if t is None else s.with_(target=t)
        sc = score(st)
        r = s.result
        shot = r is not None and r.kind in ('shot', 'forced', 'free_throws')
        look = float(sc.look) if shot else 0.0
        expired = s.clock == 0
        out.append(Val(float(sc.total), look, 1.0 if (shot and sc.look >= RC.SCENARIO_GOAL and not s.zeroed) else 0.0,
                       1.0 if expired else 0.0, look if expired else 0.0))
    return tuple(out)


# =====================================================================================
# fast evaluation
# =====================================================================================

def _with_x(s, d, q, arrow=None):
    x = list(s.x)
    x[d] = q
    kw = dict(x=tuple(x))
    if arrow is not None:
        arr = list(s.arrows)
        arr[d] = arrow
        kw['arrows'] = tuple(arr)
    return s.with_(**kw)


from functools import lru_cache


@lru_cache(maxsize=None)
def _paths(kind, frm, qs, rules):
    """On-board movement paths from frm: tuple of (run direction or None, path, path as frozenset, dest)."""
    if kind == 'move':
        raw = [(None, p) for p in B.move_paths(frm, rules)]
    elif kind == 'qs':
        raw = [(None, p) for p in B.qs_paths(frm, qs, rules)]
    else:
        raw = list(B.sprint_paths(frm, qs, rules))
    return tuple((dr, p, frozenset(p), p[-1]) for dr, p in raw if all(B.on_board(q) for q in p))


def defender_reach(s, d, budget):
    """Where defender d can be after up to `budget` (<= 2) actions, and with what arrow.
    Returns (free, fixed): free[sq] = action list arriving with any arrow (a Move was used);
    fixed[sq] = {arrow: action list} for arrivals whose arrow is set (Quick Step / Sprint).
    Uses the engine's movement shapes, blocking and screen geometry directly (no state copies)."""
    rules = s.ctx.rules
    start = s.x[d]
    arrow = s.arrows[d]
    free, fixed = {}, {start: {arrow: []}}
    if budget <= 0 or s.tok_x <= 0:
        return free, fixed
    qs = s.ctx.dfn[d].qs
    occ = (set(s.o) | set(s.x)) - {start}
    scr = []
    for sc in s.screens:
        scr.append((t_square(s, sc), bool(sc[3] >> d & 1)))
    qs_left = RC.LIMITS['X']['qs'] - s.count('X', 'qs')
    once = rules.qs_once_per_player
    if once and s.quick_stepped('X', d):
        qs_left = 0                          # OQ-52: this defender's Quick Step is used (no Quick Step, no Sprint)
    if once:
        qs_left = min(qs_left, 1)            # one Quick Step per player: never two, nor a Quick Step and a Sprint
    can_move = not s.moved('X', d) and not s.locked('X', d)
    two = budget >= 2 and s.tok_x >= 2
    on_board, banned = B.on_board, B.diag_step_banned

    def ok(frm, path):
        if scr:
            prev = frm
            for q in path:
                for tsq, beat in scr:
                    if not beat and banned(prev, q, tsq, rules):
                        return False
                prev = q
            for tsq, beat in scr:
                if beat and path[-1] == tsq:
                    return False
        return True

    def dests(frm, kind):
        out = {}
        disjoint = occ.isdisjoint
        for dr, path, pset, dest in _paths(kind, frm, qs, rules):
            if dest not in out and disjoint(pset) and (not scr or ok(frm, path)):
                out[dest] = dr
        return out

    def add_fixed(q, a, seq):
        cur = fixed.setdefault(q, {})
        if a not in cur or len(seq) < len(cur[a]):
            cur[a] = seq

    def add_free(q, seq):
        if q not in free or len(seq) < len(free[q]):
            free[q] = seq

    moves = dests(start, 'move') if can_move else {}
    qss = dests(start, 'qs') if qs_left >= 1 and qs > 0 else {}
    sprints = dests(start, 'sprint') if can_move and qs_left >= 1 else {}
    if can_move:
        add_free(start, [('move', start)])
    for q in moves:
        add_free(q, [('move', q)])
    for q in qss:
        add_fixed(q, arrow, [('qs', q)])
    wedge = rules.arrow_mode == 'wedge'
    for q, dr in sprints.items():
        add_fixed(q, dr, [('sprint', q)])
        if wedge:                          # step 3h: the other edge on the anticlockwise side
            add_fixed(q, (dr - 1) % 8, [('sprint', q, (dr - 1) % 8)])
    if two:
        if qs_left >= 1 and qs > 0:
            for m in list(moves) + ([start] if can_move else []):
                for q in dests(m, 'qs'):
                    add_free(q, [('move', m), ('qs', q)])
        for q1 in qss:
            if can_move:
                for q in dests(q1, 'move'):
                    add_free(q, [('qs', q1), ('move', q)])
            if qs_left >= 2:
                for q in dests(q1, 'qs'):
                    add_fixed(q, arrow, [('qs', q1), ('qs', q)])
                if can_move:
                    for q, dr in dests(q1, 'sprint').items():
                        add_fixed(q, dr, [('qs', q1), ('sprint', q)])
                        if wedge:
                            add_fixed(q, (dr - 1) % 8, [('qs', q1), ('sprint', q, (dr - 1) % 8)])
        if qs_left >= 2 and qs > 0:
            for q1, dr1 in sprints.items():
                for q in dests(q1, 'qs'):
                    add_fixed(q, dr1, [('sprint', q1), ('qs', q)])
                    if wedge:
                        add_fixed(q, (dr1 - 1) % 8, [('sprint', q1, (dr1 - 1) % 8), ('qs', q)])
    return free, fixed


_DR = {(x, y): B.dist_rim((x, y)) for x in range(-1, B.W + 1) for y in range(0, B.H + 2)}


class ReachMaps(list):
    """Per-defender (free, fixed) maps, plus an index: square -> [(d, free_len, [(arrow, len)])]."""

    def __init__(self, maps):
        super().__init__(maps)
        idx = {}
        for d, (free, fixed) in enumerate(maps):
            squares = set(free) | set(fixed)
            for q in squares:
                fl = len(free[q]) if q in free else None
                fx = [(a, len(seq)) for a, seq in fixed.get(q, {}).items()]
                idx.setdefault(q, []).append((d, fl, fx))
        self.index = idx


class Evaluator:
    """Fast position values, cached per position."""

    def __init__(self, cfg=DEFAULT, targets=(None,)):
        self.cfg = cfg
        self.targets = targets
        self.reach_cache = {}
        self.cache = {}
        self.calls = 0

    # -- reach of every defender, cached on what it depends on
    def reach(self, s, budget):
        key = (s.o, s.x, s.arrows, s.moved_x, s.cnt[6], s.tok_x, s.lock_x, s.screens, budget)
        r = self.reach_cache.get(key)
        if r is None:
            r = ReachMaps([defender_reach(s, d, budget) for d in range(5)])
            if len(self.reach_cache) > 15000:
                self.reach_cache.clear()
            self.reach_cache[key] = r
        return r

    def defended(self, s, maps, shooter, spos, t, budget, forced=False):
        """Defence's best answer to a shot by `shooter` from spos (shot type t).
        Returns (ev, look, p30, kind) where kind names the answer ('open', 'clean', 'side', 'steal')."""
        if s.ctx.rules.contest_geometry != 'current':
            return self._defended_geo(s, maps, shooter, spos, t, budget, forced)
        ctx, rules = s.ctx, s.ctx.rules
        card = ctx.off[shooter]
        pts = RC.ZONE_POINTS[B.zone(spos)]
        rating = card.shot(t)
        if ctx.three_only and pts != 3:
            return 0.0, 0.0, 0.0, None
        floor = forced or rules.floor_declared_shot
        fp = float(foul_on_shot_points(card, t, pts, rules)[0])
        fp30 = fp >= 30
        v0 = pts * rating
        best = (float(v0), float(v0), 1.0 if v0 >= 30 else 0.0, 'open')
        best_ev = best[0]
        steal_ok = s.count('X', 'steal') < RC.LIMITS['X']['steal']
        tok = s.tok_x
        far_pen = RC.FAR_CONTEST_PENALTY
        floor_c = rules.floor_contest_zero
        ds = _DR[spos]
        idx = maps.index
        occ_o = s.o
        sx, sy = spos
        pk_cache = {}
        con_key = 'con_' + t
        for dx, dy in B.DIRS:
            q = (sx + dx, sy + dy)
            ents = idx.get(q)
            if not ents or q in occ_o:
                continue
            on = B.DIRS.index((-dx, -dy))
            far = _DR[q] > ds
            for d, fl, fx in ents:
                dcard = ctx.dfn[d]
                c = dcard.r[con_key] - (far_pen if far else 0)
                if floor_c and c < 0:
                    c = 0
                v = pts * (rating - c)
                if floor and v < 0:
                    v = 0
                v = float(v)
                clean_len = None
                if fl is not None and fl <= budget:
                    clean_len = fl
                for a, ln in fx:
                    if ln <= budget and a == on and (clean_len is None or ln < clean_len):
                        clean_len = ln
                if clean_len is not None:
                    if v < best_ev:
                        best, best_ev = (v, v, 1.0 if v >= 30 else 0.0, 'clean'), v
                else:
                    pf = dcard.r['foul_contest'] / 20.0
                    for a, ln in fx:
                        if ln <= budget and a != on:
                            ev = pf * fp + (1 - pf) * v
                            if ev < best_ev:
                                best, best_ev = (ev, ev, pf * fp30 + (1 - pf) * (v >= 30), 'side'), ev
                            break
                if steal_ok and clean_len is not None and clean_len + 1 <= budget and tok >= clean_len + 1:
                    pf = dcard.r['foul_steal'] / 20.0
                    pk = pk_cache.get(d)
                    if pk is None:
                        pk = pk_cache[d] = float(p_success(card.r['dribble'] - dcard.r['steal'], rules))
                    ev = pf * fp + (1 - pf) * (pk * v + (1 - pk) * RC.TURNOVER_POINTS)
                    if ev < best_ev:
                        best = (ev, pf * fp + (1 - pf) * pk * v, pf * fp30 + (1 - pf) * pk * (v >= 30), 'steal')
                        best_ev = ev
        return best

    def _defended_geo(self, s, maps, shooter, spos, t, budget, forced=False):
        """defended() under the step 3h contest geometries: only a defender who ends with the shooter on
        an arrow line contests; Front is a full contest, Side a foul roll, Behind a foul roll and the -3
        (geometry.terms decides, from the arrows each reach path can end with)."""
        ctx, rules = s.ctx, s.ctx.rules
        card = ctx.off[shooter]
        pts = RC.ZONE_POINTS[B.zone(spos)]
        rating = card.shot(t)
        if ctx.three_only and pts != 3:
            return 0.0, 0.0, 0.0, None
        floor = forced or rules.floor_declared_shot
        fp = float(foul_on_shot_points(card, t, pts, rules)[0])
        fp30 = fp >= 30
        v0 = pts * rating
        best = (float(v0), float(v0), 1.0 if v0 >= 30 else 0.0, 'open')
        best_ev = best[0]
        steal_ok = s.count('X', 'steal') < RC.LIMITS['X']['steal']
        tok = s.tok_x
        idx = maps.index
        occ_o = s.o
        sx, sy = spos
        con_key = 'con_' + t
        pk_cache = {}
        for dx, dy in B.DIRS:
            q = (sx + dx, sy + dy)
            ents = idx.get(q)
            if not ents or q in occ_o:
                continue
            for d, fl, fx in ents:
                dcard = ctx.dfn[d]
                opts = []
                if fl is not None and fl <= budget:
                    opts.append((None, fl))
                opts += [((a,), ln) for a, ln in fx if ln <= budget]
                facing_len = None
                for arrows, ln in opts:
                    bt = G.best_terms(rules, q, arrows, spos)
                    if bt is None:
                        continue                           # lines off the shooter: no contest
                    _, foul_roll, penalty, _, _ = bt
                    facing_len = ln if facing_len is None else min(facing_len, ln)
                    c = dcard.r[con_key] - (RC.FAR_CONTEST_PENALTY if penalty else 0)
                    if rules.floor_contest_zero and c < 0:
                        c = 0
                    v = pts * (rating - c)
                    if floor and v < 0:
                        v = 0
                    v = float(v)
                    if foul_roll:
                        pf = dcard.r['foul_contest'] / 20.0
                        ev = pf * fp + (1 - pf) * v
                        cand = (ev, ev, pf * fp30 + (1 - pf) * (v >= 30), 'side')
                    else:
                        cand = (v, v, 1.0 if v >= 30 else 0.0, 'clean')
                    if cand[0] < best_ev:
                        best, best_ev = cand, cand[0]
                if steal_ok and facing_len is not None and facing_len + 1 <= budget and tok >= facing_len + 1:
                    c = dcard.r[con_key]
                    v = float(max(0, pts * (rating - c)) if floor else pts * (rating - c))
                    pf = dcard.r['foul_steal'] / 20.0
                    pk = pk_cache.get(d)
                    if pk is None:
                        pk = pk_cache[d] = float(p_success(card.r['dribble'] - dcard.r['steal'], rules))
                    ev = pf * fp + (1 - pf) * (pk * v + (1 - pk) * RC.TURNOVER_POINTS)
                    if ev < best_ev:
                        best = (ev, pf * fp + (1 - pf) * pk * v, pf * fp30 + (1 - pf) * pk * (v >= 30), 'steal')
                        best_ev = ev
        return best

    def carrier_look(self, s, shooter, budget_x, can_move, forced=False):
        """Best (ev, look, p30, shot square, type) for `shooter` with the ball."""
        spos = s.o[shooter]
        maps = self.reach(s, budget_x)
        squares = [spos]
        if can_move:
            st = s.with_(ball=shooter)
            for kind in ('move', 'qs', 'sprint'):
                if can_move_kind(st, 'O', shooter, kind):
                    squares += list(movement_dests(st, 'O', shooter, kind, s.ctx.rules))
        best = (0.0, 0.0, 0.0, None, None)
        first = True
        for q in dict.fromkeys(squares):
            if not B.on_board(q):
                continue
            z = B.zone(q)
            for t in RC.ZONE_SHOTS[z]:
                if q != spos:
                    sh = s.with_(o=s.o[:shooter] + (q,) + s.o[shooter + 1:])
                else:
                    sh = s
                ev, look, p30, _ = self.defended(sh, maps, shooter, q, t, budget_x, forced)
                if first or ev > best[0]:
                    best = (ev, look, p30, q, t)
                    first = False
        return best

    def __call__(self, s):
        key = s
        v = self.cache.get(key)
        if v is not None:
            return v
        self.calls += 1
        v = self._eval(s)
        if self.cfg.eval_turns >= 2 and s.stage == 'play' and s.side == 'O' and s.tok_o >= 1 and not s.ctx.coach_call:
            v2 = self._two_turns(s, v)
            if v2 is not None and v2[0].ev > v[0].ev:
                v = v2
        v = self._terms(s, v)
        if len(self.cache) > 60000:
            self.cache.clear()
        self.cache[key] = v
        return v

    def _eval(self, s):
        if s.stage == 'over':
            return terminal_vals(s, self.targets)
        if s.stage in ('pick', 'forced'):
            return max((expected(apply(s, a), self) for a in legal_actions(s)), key=lambda vs: vs[0].ev)
        if s.stage == 'contest':
            return min((expected(apply(s, a), self) for a in legal_actions(s)), key=lambda vs: max(v.ev for v in vs))
        if s.stage == 'target':
            return max((self(apply(s, a)) for a in legal_actions(s)), key=lambda vs: vs[0].ev)
        ctx = s.ctx
        base = RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * s.tos
        if s.pending:
            from .actions import completed_view
            landed = completed_view(s)
            p = 1.0
            for j in range(5):
                if intercept_status(s, j) in ('direct', 'approach'):
                    pj = float(p_success(ctx.off[s.pending[0]].r['pass'] - ctx.dfn[j].r['intercept'], ctx.rules))
                    p = min(p, pj)
            if s.inbound and s.pending[0] == ctx.inbounder:
                from .resolve import complete_pass
                landed = complete_pass(s)
            lost = s.with_(pending=None, approach=-1, tos=s.tos + 1)
            if p >= 1.0:
                return self(landed)
            if ctx.hold_for_one:
                lost_v = tuple(Val(0.0) for _ in self.targets)
            else:
                lost_v = self(lost)
            return mix([(p, self(landed)), (1 - p, lost_v)])
        budget_x = min(2, s.tok_x) if s.tok_x > 0 else 0
        # the shot already declared: the defence's reaction is all that is left
        if s.stage == 'reaction':
            maps = self.reach(s, budget_x)
            ev, look, p30, _ = self.defended(s, maps, s.ball, s.o[s.ball], s.shot, budget_x)
            return self._vals(s, base, ev, look, p30, s.ball, 0.0, 0.0)
        # clock about to run out: forced shot from where the carrier stands
        last_turn = s.inbound == 0 and s.clock <= RC.PHASE_SECONDS and (
            (s.side == 'X' and s.final) or (s.side == 'O' and s.tok_o == 0))
        if last_turn:
            if ctx.hold_for_one:
                return tuple(Val(0.0, 0.0, 0.0, 1.0, 0.0) for _ in self.targets)
            ev, look, p30, _, _ = self.carrier_look(s, s.ball, budget_x, False, forced=True)
            return self._vals(s, base + RC.TURNOVER_POINTS, ev, look, p30, s.ball, 1.0, ev)
        o_tokens = s.tok_o
        can_move = o_tokens >= 2 or s.side == 'X'
        if s.inbound and s.ball == ctx.inbounder:
            w, cands = self.cfg.inbound_kick_weight, [i for i in range(5) if i != s.ball and B.on_board(s.o[i])]
            # the ball still has to come in: weigh each receiver's look by the pass's interception risk
            best = (RC.TURNOVER_POINTS * 1.0, 0.0, 0.0, -1)
            can_pass = s.count('O', 'pass') < RC.LIMITS['O']['pass'] and s.tok_o > 0
            for r in cands if can_pass else []:
                ev, look, p30, _, _ = self.carrier_look(s, r, budget_x, True)
                pend = s.with_(pending=(s.ball, r))
                p = 1.0
                for j in range(5):
                    if intercept_status(pend, j) in ('direct', 'approach'):
                        p = min(p, float(p_success(ctx.off[s.ball].r['pass'] - ctx.dfn[j].r['intercept'], ctx.rules)))
                v = (p * ev + (1 - p) * RC.TURNOVER_POINTS) * w
                if v > best[0]:
                    best = (v, p * look * w, p * p30 * w, r)
            return self._vals(s, base, best[0], best[1], best[2], best[3], 0.0, 0.0)
        ev, look, p30, _, _ = self.carrier_look(s, s.ball, budget_x, can_move)
        shooter = s.ball
        if self.cfg.kick_weight > 0:
            for r in range(5):
                if r != s.ball and B.on_board(s.o[r]):
                    e2, l2, p2, _, _ = self.carrier_look(s, r, budget_x, True)
                    if e2 * self.cfg.kick_weight > ev:
                        ev, look, p30, shooter = e2 * self.cfg.kick_weight, l2 * self.cfg.kick_weight, p2 * self.cfg.kick_weight, r
        return self._vals(s, base, ev, look, p30, shooter, 0.0, 0.0)

    def _one(self, s):
        """One-turn evaluation (no recursion), cached."""
        k = ('one', s)
        v = self.cache.get(k)
        if v is None:
            v = self._eval(s)
            self.cache[k] = v
        return v

    def _two_turns(self, s, v1):
        """Best look over the offence's next two turns: a setup play now (no shot), the defence's
        best reply among its ball-side plays, then the one-turn evaluation."""
        gen = getattr(self, '_gen', None)
        if gen is None:
            gen = self._gen = Generator(self.cfg, self)
        pri = {'kick': 0, 'relocate+kick': 1, 'drive': 2, 'seal': 3, 'relocate': 4, 'screen': 5, 'swing': 6,
               'dribble': 7, 'hesitate': 8}
        setups = [p for p in gen.offence_plays(s) if not any(a.kind == 'shot' for a in p.actions)]
        setups.sort(key=lambda p: pri.get(p.concept, 9))
        best = None
        tried = 0
        for p in setups:
            if tried >= self.cfg.eval_setup_k:
                break
            node = apply_play(s, p)
            if node is None:
                continue
            tried += 1
            val = expected(node, self._reply)
            if best is None or val[0].ev > best[0].ev:
                best = val
        return best

    def _reply(self, s):
        """Defence's best reply (ball-side plays), then the one-turn evaluation."""
        if s.stage != 'play' or s.side != 'X':
            return self._one(s)
        gen = self._gen
        res = []
        for p in gen.plays(s, False, light=True)[:self.cfg.eval_reply_k + 2]:
            node = apply_play(s, p)
            if node is not None:
                res.append(expected(node, self._one))
        if not res:
            return self._one(s)
        res.sort(key=lambda vs: vs[0].ev)
        return res[0]

    def _terms(self, s, v):
        c = self.cfg
        if not (c.term_open_lane or c.term_zone) or s.stage != 'play' or s.side != 'O':
            return v
        extra = 0.0
        if c.term_zone and B.on_board(s.o[s.ball]) and B.zone(s.o[s.ball]) != '.':
            extra += c.term_zone
        if c.term_open_lane:
            mine = v[0].look
            best = mine
            for r in range(5):
                if r == s.ball or not B.on_board(s.o[r]):
                    continue
                pend = s.with_(pending=(s.ball, r))
                if any(intercept_status(pend, j) for j in range(5)):
                    continue
                best = max(best, self.carrier_look(s, r, min(2, s.tok_x), True)[0])
            extra += c.term_open_lane * max(0.0, best - mine)
        return tuple(Val(x.ev + extra, x.look, x.p30, x.pexp, x.fs) for x in v)

    def _vals(self, s, base, ev, look, p30, shooter, pexp, fs):
        out = []
        for t in self.targets:
            coach = 0.0
            tgt = s.target if t is None else t
            if s.ctx.coach_call and tgt == shooter:
                coach = RC.COACH_BONUS[band(int(round(look)))]
            total = 0.0 if (s.zeroed) else base + ev + coach
            out.append(Val(total, look, p30, pexp, fs))
        return tuple(out)


# =====================================================================================
# plays (the candidate generator)
# =====================================================================================

@dataclass(frozen=True)
class Play:
    concept: str
    actions: tuple

    def text(self):
        return ' then '.join(str(a) for a in self.actions if a.kind != 'end_turn') or str(self.actions[0])


def _contest_arrow(rules, q, sp):
    """The arrow a defender arriving on q with a Move sets to contest a shooter on sp: facing him, and
    under the step 3h geometries the wedge with the best contest category."""
    if rules.contest_geometry == 'current' and rules.arrow_mode == 'single':
        return B.dir_between(q, sp)
    bt = G.best_terms(rules, q, None, sp)
    return bt[4] if bt else B.dir_between(q, sp)


def _seq_actions(d, seq, arrow):
    """Turn a reach sequence into engine actions (the Move's arrow set to `arrow`)."""
    out = []
    for item in seq:
        kind, q = item[0], item[1]
        if kind == 'move':
            out.append(Action('move', 'X', d, q, arrow if arrow is not None else 0))
        elif len(item) > 2:                                    # a wedge Sprint's chosen other edge
            out.append(Action(kind, 'X', d, q, item[2]))
        else:
            out.append(Action(kind, 'X', d, q))
    return out


def quick_legal(s, a):
    """Cheap legality check for an action in state s."""
    if a.kind == 'end_turn':
        from .actions import inbound_held
        return s.turn_n >= 1 or s.stage == 'reaction' or (s.pending and s.side == 'X' and not inbound_held(s))
    if a.kind in MOVEMENT:
        if not can_move_kind(s, a.side, a.piece, a.kind):
            return False
        start = (s.o if a.side == 'O' else s.x)[a.piece]
        if a.kind == 'move' and a.dest == start:
            return a.side == 'X' and a.arrow != s.arrows[a.piece]
        return a.dest in movement_dests(s, a.side, a.piece, a.kind, s.ctx.rules)
    if a.kind == 'steal':
        cp = s.o[s.ball]
        return (s.tok_x > 0 and s.count('X', 'steal') < RC.LIMITS['X']['steal']
                and G.faces(s.ctx.rules, s.arrows[a.piece], s.x[a.piece], cp))
    return a in legal_actions(s)


def apply_play(s, play):
    """Apply a play's actions in order; returns a state or ChanceNode, or None if illegal."""
    node = s
    for i, a in enumerate(play.actions):
        if isinstance(node, ChanceNode) or node.stage == 'over':
            return None
        if i > 0 and (node.side != a.side or not quick_legal(node, a)):
            return None                   # the turn passed (e.g. its action limit), or the action is illegal
        node = apply(node, a)
    if not isinstance(node, ChanceNode) and node.stage in ('play', 'reaction') and node.side == s.side \
            and node.turn_n >= 1 and node.stage == s.stage:
        node = apply(node, Action('end_turn', s.side))
    return node


class Generator:
    def __init__(self, cfg, ev):
        self.cfg = cfg
        self.ev = ev

    def plays(self, s, shallow, rng=None, light=False):
        if s.stage == 'target':
            out = [Play('target', (a,)) for a in legal_actions(s)]
        elif s.stage in ('pick', 'contest', 'forced'):
            out = [Play(s.stage, (a,)) for a in legal_actions(s)]
        elif s.stage == 'reaction':
            out = self.reaction_plays(s)
        elif s.side == 'O':
            out = self.offence_plays(s)
        else:
            out = self.defence_plays(s, light)
        if shallow and self.cfg.top_k_raw > 0 and s.stage in ('play', 'reaction'):
            out += self.raw_plays(s, out)
        seen, uniq = set(), []
        for p in out:
            if p.actions not in seen:
                seen.add(p.actions)
                uniq.append(p)
        if rng is not None:
            rng.shuffle(uniq)
        return uniq

    def _value_after(self, s, play):
        node = apply_play(s, play)
        if node is None:
            return None
        return expected(node, self.ev)[0].ev

    def raw_plays(self, s, have):
        firsts = {p.actions[0] for p in have}
        scored = []
        maximise = s.side == 'O' and s.stage != 'reaction'
        for a in legal_actions(s):
            if a in firsts:
                continue
            p = Play('raw', (a,))
            v = self._value_after(s, p)
            if v is not None:
                scored.append((v if maximise else -v, p))
        scored.sort(key=lambda x: -x[0])
        return [p for _, p in scored[:self.cfg.top_k_raw]]

    # ---- offence ----
    def offence_plays(self, s):
        acts = legal_actions(s)
        out = []
        c = s.ball
        two = s.tok_o >= 2
        ev = self.ev
        budget_x = min(2, s.tok_x)
        maps = ev.reach(s, budget_x)
        for a in acts:
            if a.kind == 'shot':
                out.append(Play('shoot', (a,)))
            elif a.kind == 'pass':
                r = a.target
                look = ev.carrier_look(s, r, budget_x, True)[0] if B.on_board(s.o[r]) else -99
                out.append(Play('kick' if look >= 20 else 'swing', (a,)))
            elif a.kind == 'hesitate':
                out.append(Play('hesitate', (a,)))
            elif a.kind == 'dribble':
                out.append(Play('dribble', (a,)))
            elif a.kind == 'screen':
                tq = B.add(s.o[a.piece], B.DIRS[a.target])
                if tq in s.x:
                    out.append(Play('screen', (a,)))
        # drives: carrier movement, ranked by the look from the new square
        drives = []
        for a in acts:
            if a.kind in MOVEMENT and a.piece == c and B.on_board(a.dest):
                sh = s.with_(o=s.o[:c] + (a.dest,) + s.o[c + 1:])
                best = None
                for t in RC.ZONE_SHOTS[B.zone(a.dest)]:
                    v = ev.defended(sh, maps, c, a.dest, t, budget_x)[0]
                    if best is None or v > best[0]:
                        best = (v, t)
                drives.append((best[0] if best else -50, a, best[1] if best else None))
        drives.sort(key=lambda x: -x[0])
        for v, a, t in drives[:self.cfg.drive_k]:
            out.append(Play('drive', (a,)))
            if two and t is not None and not (s.ctx.hold_for_one and s.clock > RC.PHASE_SECONDS):
                out.append(Play('drive+shoot', (a, Action('shot', 'O', c, shot=t))))
        # relocations: off-ball movement to the best open shot squares
        rel = []
        for a in acts:
            if a.kind in MOVEMENT and a.piece != c and B.on_board(a.dest) and B.zone(a.dest) != '.':
                sh = s.with_(o=s.o[:a.piece] + (a.dest,) + s.o[a.piece + 1:])
                best = max((ev.defended(sh, maps, a.piece, a.dest, t, budget_x)[0] for t in RC.ZONE_SHOTS[B.zone(a.dest)]),
                           default=-50)
                rel.append((best, a))
        rel.sort(key=lambda x: -x[0])
        can_pass = s.count('O', 'pass') < RC.LIMITS['O']['pass']
        for v, a in rel[:self.cfg.relocate_k]:
            out.append(Play('relocate', (a,)))
            if two and can_pass:
                out.append(Play('relocate+kick', (a, Action('pass', 'O', c, target=a.piece))))
        # seal: move round your defender, then Screen with the T on it
        if two and s.count('O', 'screen') < RC.LIMITS['O']['screen']:
            for p in range(5):
                if p == c or s.is_screening(p) or not B.on_board(s.o[p]):
                    continue
                for j, xp in enumerate(s.x):
                    if not B.adjacent(xp, s.o[p]):
                        continue
                    for a in acts:
                        if a.kind == 'move' and a.piece == p and B.adjacent(a.dest, xp) and B.dist_rim(a.dest) < B.dist_rim(xp):
                            d = B.dir_between(a.dest, xp)
                            out.append(Play('seal', (a, Action('screen', 'O', p, target=d))))
                            break
        return out

    # ---- defence ----
    def defence_plays(self, s, light=False):
        out = []
        rules = s.ctx.rules
        view = s
        if s.pending:
            from .actions import completed_view, is_approach
            acts = legal_actions(s)
            for a in acts:
                if a.kind == 'intercept':
                    out.append(Play('intercept', (a,)))
                elif a.kind in MOVEMENT and is_approach(s, a):
                    out.append(Play('approach+intercept', (a, Action('intercept', 'X', a.piece))))
            from .actions import inbound_held
            if s.inbound and s.pending[0] == s.ctx.inbounder:
                if not inbound_held(s):
                    out.append(Play('allow', (Action('end_turn', 'X'),)))
                    return out
                # OQ-35: the defence plays a normal turn while the inbound is in the air
                for a in acts:
                    if a.kind in MOVEMENT and is_approach(s, a):
                        for b in (Action('intercept', 'X', a.piece),):
                            out.append(Play('approach+intercept', (a, b)))
                view = s
            else:
                view = completed_view(s)
        acts = legal_actions(view)
        c = view.ball
        cp = view.o[c]
        budget = min(2, view.tok_x)
        maps = self.ev.reach(view, budget)
        singles = []
        for a in acts:
            if a.kind == 'steal':
                out.append(Play('steal', (a,)))
            elif a.kind == 'challenge':
                out.append(Play('challenge', (a,)))
            elif a.kind == 'pause':
                out.append(Play('pause', (a,)))
        # closeouts on the carrier (Move facing, then Quick Step in), strongest contest first
        cl = []
        for d in range(5):
            free, fixed = maps[d]
            for dr in B.DIRS:
                q = (cp[0] + dr[0], cp[1] + dr[1])
                seq = free.get(q)
                if seq is None or not B.on_board(q):
                    continue
                on = _contest_arrow(s.ctx.rules, q, cp)
                acts_seq = _seq_actions(d, seq, on)
                score_c = max((s.ctx.dfn[d].con(t) for t in RC.ZONE_SHOTS.get(B.zone(cp), ()) ), default=0)
                cl.append((score_c, -len(seq), d, acts_seq))
        cl.sort(key=lambda x: (-x[0], -x[1]))
        for _, _, d, seq in cl[:self.cfg.closeout_k]:
            out.append(Play('closeout', tuple(seq)))
            if len(seq) == 1:
                singles.append(('closeout', seq[0]))
        # help: step into the drive lane between the carrier and the rim
        for d in range(5):
            free, _ = maps[d]
            best = None
            for q, seq in free.items():
                if len(seq) != 1 or q == view.x[d]:
                    continue
                if 1 <= B.cheb(q, cp) <= 2 and B.dist_rim(q) < B.dist_rim(cp):
                    k = (B.dist_rim(q), B.cheb(q, cp))
                    if best is None or k < best[0]:
                        best = (k, q)
            if best:
                a = Action('move', 'X', d, best[1], B.nearest_dir(best[1], cp))
                out.append(Play('help', (a,)))
                singles.append(('help', a))
        # deny: put an arrow across a passing lane (turn in place, or step onto the lane)
        for r in range(5):
            if r == c or not B.on_board(view.o[r]):
                continue
            a_, b_ = cp, view.o[r]
            found = None
            for d in range(5):
                if not can_move_kind(view, 'X', d, 'move'):
                    continue
                xp = view.x[d]
                for arr in range(8):
                    if arr != view.arrows[d] and G.crosses(rules, xp, arr, a_, b_):
                        found = Action('move', 'X', d, xp, arr)
                        break
                if found:
                    break
            if found:
                out.append(Play('deny', (found,)))
                singles.append(('deny', found))
        # contain: the carrier's best looks after a step (Move, Quick Step or Sprint, then shoot) are one
        # offence turn away; stand next to those squares, facing them, before the turn passes
        if s.side == 'X' and B.on_board(cp) and not view.pending:
            for q in self.step_shots(view, c, budget, self.cfg.contain_k):
                cl = []
                for d in range(5):
                    free, fixed = maps[d]
                    for dr in B.DIRS:
                        r = (q[0] + dr[0], q[1] + dr[1])
                        if not B.on_board(r) or r in view.o:
                            continue
                        on = _contest_arrow(s.ctx.rules, r, q)
                        seq, clean = free.get(r), True
                        if seq is None and r in fixed:            # a step that keeps the arrow: facing q, or a foul roll
                            arrows = fixed[r]
                            fa = [k for k in arrows if G.faces(s.ctx.rules, k, r, q)]
                            if fa:
                                a = min(fa, key=lambda k: len(arrows[k]))
                            elif s.ctx.rules.contest_geometry != 'current':
                                continue                          # step 3h: no contest with the lines off him
                            else:
                                a = min(arrows, key=lambda k: len(arrows[k]))
                            seq, clean = arrows[a], a in fa
                        if not seq or len(seq) > view.tok_x:     # none, or already there
                            continue
                        con = max((s.ctx.dfn[d].con(t) for t in RC.ZONE_SHOTS.get(B.zone(q), ())), default=0)
                        cl.append((not clean, -con, len(seq), B.dist_rim(r), d, tuple(_seq_actions(d, seq, on))))
                cl.sort(key=lambda x: x[:5])
                used = set()
                for _, _, _, _, d, seq in cl:
                    if d in used:
                        continue
                    used.add(d)
                    out.append(Play('contain', seq))
                    if len(seq) == 1:
                        singles.append(('contain', seq[0]))
                    if len(used) >= 2:
                        break
        if light:                       # quiescence: plays around the ball only
            return out
        # recover / switch: back to a man, rim side, arrow on him
        for d in range(5):
            free, _ = maps[d]
            for kind, man in (('recover', d), ('switch', None)):
                if man is None:
                    others = [o for o in range(5) if o != d and B.on_board(view.o[o])]
                    if not others:
                        continue
                    man = min(others, key=lambda o: B.cheb(view.o[o], view.x[d]))
                    if man == d:
                        continue
                mp = view.o[man]
                if not B.on_board(mp) or B.adjacent(view.x[d], mp):
                    continue
                cands = [(B.dist_rim(q), q) for q, seq in free.items() if len(seq) == 1 and B.adjacent(q, mp)]
                if cands:
                    q = min(cands)[1]
                    a = Action('move', 'X', d, q, B.dir_between(q, mp))
                    out.append(Play(kind, (a,)))
                    singles.append((kind, a))
        # two-action combos from the best singles (different defenders)
        if view.tok_x >= 2:
            seen = 0
            for i, (k1, a1) in enumerate(singles):
                for k2, a2 in singles[i + 1:]:
                    if a1.piece != a2.piece and seen < self.cfg.combo_k * 3:
                        out.append(Play(f'{k1}+{k2}', (a1, a2)))
                        seen += 1
        return out

    def step_shots(self, s, shooter, budget_x, k):
        """The k best squares (other than where the carrier stands) the carrier can step to with one
        movement action and shoot from, by the value of the shot against the defence as it stands."""
        if k <= 0:
            return []
        spos = s.o[shooter]
        maps = self.ev.reach(s, budget_x)
        squares = set()
        st = s.with_(side='O', ball=shooter)
        for kind in ('move', 'qs', 'sprint'):
            if can_move_kind(st, 'O', shooter, kind):
                squares |= set(movement_dests(st, 'O', shooter, kind, s.ctx.rules))
        scored = []
        for q in squares:
            if q == spos or not B.on_board(q):
                continue
            sh = s.with_(o=s.o[:shooter] + (q,) + s.o[shooter + 1:])
            best = max((self.ev.defended(sh, maps, shooter, q, t, budget_x)[0] for t in RC.ZONE_SHOTS[B.zone(q)]),
                       default=None)
            if best is not None:
                scored.append((best, q))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return [q for _, q in scored[:k]]

    def reaction_plays(self, s):
        out = [Play('no reaction', (Action('end_turn', 'X'),))]
        sp = s.o[s.ball]
        budget = min(2, s.tok_x)
        maps = self.ev.reach(s, budget)
        for a in legal_actions(s):
            if a.kind == 'steal':
                out.append(Play('steal gamble', (a,)))
        for d in range(5):
            free, fixed = maps[d]
            for dr in B.DIRS:
                q = (sp[0] + dr[0], sp[1] + dr[1])
                if not B.on_board(q):
                    continue
                on = _contest_arrow(s.ctx.rules, q, sp)
                seq = free.get(q)
                if seq is not None and len(seq) <= budget:
                    acts_seq = _seq_actions(d, seq, on)
                    out.append(Play('closeout', tuple(acts_seq)))
                    if len(acts_seq) == 1 and budget >= 2:
                        out.append(Play('closeout+steal', (acts_seq[0], Action('steal', 'X', d))))
                for arr, fseq in fixed.get(q, {}).items():
                    if fseq and len(fseq) <= budget:
                        facing = G.faces(s.ctx.rules, arr, q, sp)
                        if not facing and s.ctx.rules.contest_geometry != 'current':
                            continue                       # step 3h: lines off the shooter can't contest
                        out.append(Play('closeout (side-on)' if not facing else 'closeout', tuple(_seq_actions(d, fseq, None))))
        return out


def expected(node, fn):
    """Expected Val tuple of a node under fn (state -> Val tuple)."""
    if isinstance(node, ChanceNode):
        return mix([(float(p), expected(sub, fn)) for p, _, sub in node.outcomes])
    return fn(node)


# =====================================================================================
# exact solver
# =====================================================================================

class NodeCap(Exception):
    pass


def _terminal_turn(s):
    """Is this the defence's last turn before the possession resolves (contest or forced shot)?"""
    if not (s.side == 'X' and not s.pending and s.inbound == 0 and s.ctx.rules.contest_choice in ('min_value', 'player')):
        return False
    if s.stage == 'reaction':
        return True
    if s.stage != 'play' or s.clock > RC.PHASE_SECONDS:
        return False
    # the final turn, or the defence's last token (which ends the phase at once, then the clock runs out)
    return s.final or (s.tok_x == 1 and s.ctx.rules.defence_empty_ends_phase)


REACH_BOUND = 1 + RC.MOVE_STRAIGHT + 2 + 2   # adjacent square + longest Sprint (3 + QS 2) + margin = 8 (>= 6 needed)


def pruned_actions(s):
    """Legal actions, with provably irrelevant defence actions removed on its last turn.
    On that turn only the defenders next to the shooter, their arrows and Steals matter:
      * second actions that don't end a defender next to the shooter (or turn an adjacent
        defender's arrow, or Steal) can only remove contest options, never add one;
      * first actions by defenders that start and end far from the shooter can't affect it
        (they can't reach it, and can't unblock anyone who can); one is kept as a no-op."""
    acts = legal_actions(s)
    if not _terminal_turn(s):
        return acts
    sp = s.o[s.ball]
    keep, noop = [], None
    for a in acts:
        if a.kind in ('steal', 'end_turn', 'forfeit'):
            keep.append(a)
        elif a.kind in MOVEMENT:
            start = s.x[a.piece]
            if s.turn_n >= 1 or s.tok_x <= 1:          # this is the defence's last action
                if B.adjacent(a.dest, sp):
                    keep.append(a)
                elif noop is None and s.turn_n == 0 and not B.adjacent(start, sp):
                    noop = a                            # a true no-op: nobody near the shooter moves
            elif B.cheb(a.dest, sp) <= REACH_BOUND or B.cheb(start, sp) <= REACH_BOUND:
                keep.append(a)
            elif noop is None:
                noop = a
        elif s.turn_n == 0 and noop is None:
            noop = a
    if noop is not None and not any(a.kind == 'end_turn' for a in keep):
        keep.append(noop)
    return keep


def exact_solve(s, cap=10 ** 6, prune=True, tt=None, stats=None):
    """Exact best play from s (target as set in s): expectimax over raw engine actions with a
    transposition table. Returns (Val, {action: Val}) for the root. Raises NodeCap past `cap` applies."""
    tt = {} if tt is None else tt
    count = [0]

    def node_value(node):
        if isinstance(node, ChanceNode):
            return mix([(float(p), (node_value(sub),)) for p, _, sub in node.outcomes])[0]
        return rec(node)

    def rec(st):
        if st.stage == 'over':
            return terminal_vals(st, (None,))[0]
        v = tt.get(st)
        if v is not None:
            return v
        acts = pruned_actions(st) if prune else legal_actions(st)
        vals = []
        for a in acts:
            count[0] += 1
            if count[0] > cap:
                raise NodeCap()
            vals.append(node_value(apply(st, a)))
        maximise = st.side == 'O' or st.stage in ('target', 'pick')
        v = max(vals, key=lambda x: x.ev) if maximise else min(vals, key=lambda x: x.ev)
        tt[st] = v
        return v

    if s.stage == 'over':
        return terminal_vals(s, (None,))[0], {}
    acts = pruned_actions(s) if prune else legal_actions(s)
    per = {}
    for a in acts:
        count[0] += 1
        if count[0] > cap:
            raise NodeCap()
        per[a] = node_value(apply(s, a))
    maximise = s.side == 'O' or s.stage in ('target', 'pick')
    v = max(per.values(), key=lambda x: x.ev) if maximise else min(per.values(), key=lambda x: x.ev)
    if stats is not None:
        stats['applies'] = count[0]
    return v, per


# =====================================================================================
# guided search
# =====================================================================================

@dataclass
class Entry:
    vals: tuple
    best: Play = None
    children: list = field(default_factory=list)     # [(Play, vals)]


class Searcher:
    def __init__(self, cfg=DEFAULT, targets=(None,), seed=0, deadline=None):
        self.cfg = cfg
        self.targets = targets
        self.ev = Evaluator(cfg, targets)
        self.gen = Generator(cfg, self.ev)
        self.rng = random.Random(seed) if seed else None
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0
        self.exact_hits = 0
        self.exact_tries = 0
        self.exact_tt = {}
        self.root_depth = 0
        self.concept_counts = {}

    def choose(self, children, maximise):
        """Offence: best per target (it knows its own target). Defence: the play that
        minimises the offence's best value across targets."""
        if maximise:
            if len(self.targets) == 1:
                p, v = max(children, key=lambda pv: pv[1][0].ev)
                return v, p
            out = []
            for t in range(len(self.targets)):
                out.append(max(children, key=lambda pv: pv[1][t].ev)[1][t])
            p = max(children, key=lambda pv: max(x.ev for x in pv[1]))[0]
            return tuple(out), p
        p, v = min(children, key=lambda pv: max(x.ev for x in pv[1]))
        return v, p

    def in_exact_range(self, s):
        n = self.cfg.endgame_tokens
        return (len(self.targets) == 1 and s.stage == 'play' and s.inbound == 0 and s.clock <= RC.PHASE_SECONDS
                and s.tok_o <= n and s.tok_x <= n and not s.ctx.coach_call)

    def value(self, s, depth):
        if s.stage == 'over':
            return terminal_vals(s, self.targets)
        if self.deadline and time.time() > self.deadline:
            raise Timeout()
        k = (s, depth)
        e = self.tt.get(k)
        if e is not None:
            return e.vals
        self.nodes += 1
        if self.in_exact_range(s):
            self.exact_tries += 1
            try:
                v, _ = exact_solve(s, cap=self.cfg.exact_node_cap, tt=self.exact_tt)
                self.exact_hits += 1
                vals = (v,)
                self.tt[k] = Entry(vals)
                return vals
            except NodeCap:
                pass
        if depth <= 0:
            if self.cfg.quiescence and s.side == 'X' and s.stage == 'play':
                return self.quiesce(s)
            return self.ev(s)
        shallow = (self.root_depth - depth) < self.cfg.raw_depth
        plays = self.gen.plays(s, shallow, self.rng)
        maximise = (s.side == 'O' and s.stage != 'reaction') or s.stage in ('target', 'pick', 'forced')
        children = []
        for p in plays:
            node = apply_play(s, p)
            if node is None:
                continue
            children.append((p, node))
        if not children:
            return self.ev(s)
        width = self.cfg.root_beam if depth == self.root_depth else self.cfg.beam
        if len(children) > width and depth >= 2:
            scored = [(expected(n, self.ev), p, n) for p, n in children]
            scored.sort(key=lambda x: (-x[0][0].ev if maximise else max(v.ev for v in x[0])))
            children = [(p, n) for _, p, n in scored[:width]]
        results = []
        for p, node in children:
            v = self.expect(node, depth - 1)
            results.append((p, v))
        vals, best = self.choose(results, maximise)
        self.tt[k] = Entry(vals, best, results)
        return vals

    def quiesce(self, s):
        """Leaf with the defence to move: let it take its turn (best of its concept plays), then evaluate."""
        k = (s, -1)
        e = self.tt.get(k)
        if e is not None:
            return e.vals
        plays = self.gen.plays(s, False, light=True)
        results = []
        for p in plays:
            node = apply_play(s, p)
            if node is None:
                continue
            results.append((p, expected(node, self.ev)))
        if not results:
            vals = self.ev(s)
        else:
            results.sort(key=lambda pv: max(v.ev for v in pv[1]))
            vals, best = self.choose(results[:self.cfg.quiescence_beam], False)
        self.tt[k] = Entry(vals)
        return vals

    def expect(self, node, depth):
        if isinstance(node, ChanceNode):
            return mix([(float(p), self.expect(sub, depth)) for p, _, sub in node.outcomes])
        return self.value(node, depth)

    def search(self, s, budget_s=None, max_depth=None, min_depth=1):
        """Iterative deepening. Returns dict with vals, depth reached, best play, timings."""
        max_depth = max_depth or self.cfg.max_depth
        t0 = time.time()
        self.deadline = (t0 + budget_s) if budget_s else None
        done = None
        for d in range(1, max_depth + 1):
            self.root_depth = d
            try:
                vals = self.value(s, d)
            except Timeout:
                break
            done = (d, vals, self.tt.get((s, d)))
            if self.deadline is None and d >= max_depth:
                break
            if s.stage == 'over':
                break
        if done is None:                         # nothing finished: fall back to depth 1 without a deadline
            self.deadline = None
            self.root_depth = min_depth
            vals = self.value(s, min_depth)
            done = (min_depth, vals, self.tt.get((s, min_depth)))
        d, vals, entry = done
        return dict(depth=d, vals=vals, entry=entry, seconds=time.time() - t0, nodes=self.nodes,
                    evals=self.ev.calls, exact_hits=self.exact_hits, exact_tries=self.exact_tries)

    # ---- reading the result ----
    def principal_line(self, s, depth, target_index=0, max_turns=20):
        """Best plays from s, following the most likely outcome of each roll."""
        lines = []
        node = s
        d = depth
        while d > 0 and len(lines) < max_turns:
            if isinstance(node, ChanceNode):
                break
            if node.stage == 'over':
                break
            e = self.tt.get((node, d))
            if e is None or e.best is None:
                break
            p = e.best
            if len(self.targets) > 1 and (node.side == 'O' and node.stage == 'play'):
                p = max(e.children, key=lambda pv: pv[1][target_index].ev)[0]
            side = node.side
            nxt = apply_play(node, p)
            rolls = []
            while isinstance(nxt, ChanceNode):
                po, lab, sub = max(nxt.outcomes, key=lambda o: o[0])
                rolls.append((nxt.what, lab, float(po)))
                nxt = sub
            lines.append(dict(side=side, concept=p.concept, text=p.text(), rolls=rolls, play=p,
                              clock=node.clock, phase=node.phase))
            node = nxt
            d -= 1
        return lines, node


def describe_terminal(node):
    if not isinstance(node, ChanceNode) and node.stage == 'over':
        return str(score(node))
    return ''
