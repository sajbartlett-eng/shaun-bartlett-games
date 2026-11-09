"""Step 3m B6: search. Whole turns (one or two actions) are the units; the two sides alternate (alpha-beta, the offence
maximising the possession's expected value, the defence minimising it), rolls are chance nodes (Star2: Star1 bounds
with a probing pass), iterative deepening under a deadline, a Zobrist-keyed transposition table (chance nodes
included), killer and history heuristics, no random rollouts. Leaves are scored by decide.Read.leaf().

Turns are generated from geometry: every legal action is a candidate; the ones worth searching are kept by the change
they make to THREAT and COVERAGE (the leaf value after the action) and the dilemmas they create, a beam of 8 to 24
turns. Labels (B7) never change a candidate's value.
"""
import random
import time

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions
from .resolve import apply, ChanceNode
from .scoring import score
from .decide import Read, CONFIG

VMIN, VMAX = CONFIG['eval']['value_bounds']


class Timeout(Exception):
    pass


# ---- Zobrist keys -----------------------------------------------------------------------------------------------------
_ZR = random.Random(20261108)
_ZPIECE = {(side, i, x, y): _ZR.getrandbits(64) for side in 'OX' for i in range(5)
           for x in range(-1, B.W + 1) for y in range(0, B.H + 2)}
_ZARROW = {(i, a): _ZR.getrandbits(64) for i in range(5) for a in range(8)}
_ZBALL = [_ZR.getrandbits(64) for _ in range(5)]


def zobrist(s):
    """The position's Zobrist key: XOR of a random word per (piece, square), per (defender, arrow) and for the ball,
    combined with the rest of the state (clock, counters, stage) so equal keys mean equal states."""
    h = _ZBALL[s.ball]
    for i, p in enumerate(s.o):
        h ^= _ZPIECE[('O', i, p[0], p[1])]
    for i, p in enumerate(s.x):
        h ^= _ZPIECE[('X', i, p[0], p[1])] ^ _ZARROW[(i, s.arrows[i])]
    rest = (s.stage, s.side, s.clock, s.tok_o, s.tok_x, s.moved_o, s.moved_x, s.cnt, s.turn_n, s.final, s.lock_o,
            s.lock_x, s.screens, s.pending, s.shot, s.prev_wait, s.beaten, s.fouls, s.bonus5, s.tos, s.qs_o, s.qs_x,
            s.phase, s.inbound, s.target, s.approach, s.turn_lead, s.turn_x, s.react_moved, s.forced, s.result)
    return h ^ (hash(rest) & 0xFFFFFFFFFFFFFFFF)


# ---- who acts --------------------------------------------------------------------------------------------------------

def actor(s):
    """'O' or 'X': the side making the next decision."""
    if s.stage in ('target', 'pick', 'forced'):
        return 'O'
    if s.stage in ('reaction', 'contest'):
        return 'X'
    return s.side


def terminal_value(s):
    from .decide import foul_externality
    return float(score(s).total) + foul_externality(s)      # step 3n F4: the quarter's price of the fouls


# ---- turn generation (B6) --------------------------------------------------------------------------------------------

def _wait(acts):
    for k in ('hesitate', 'pause', 'end_turn', 'forfeit'):
        for a in acts:
            if a.kind == k:
                return a
    return None


def candidate_actions(s, read=None, per_player=3):
    """The legal actions worth trying as the next action, from geometry: every shot, pass, dribble, steal, intercept
    and challenge; movement to the squares that matter (each attacker's best looks, the carrier's drives, each
    defender's top responses and the best cover); a few screens; one wait. Every one is legal (taken from
    legal_actions)."""
    acts = legal_actions(s)
    side = actor(s)
    if s.stage in ('contest', 'forced', 'target', 'pick') or len(acts) <= 12:
        return acts
    keep, seen = [], set()

    def add(a):
        if a not in seen:
            seen.add(a)
            keep.append(a)
    for a in acts:
        if a.kind in ('shot', 'pass', 'dribble', 'steal', 'intercept', 'challenge', 'forced_shot', 'contest'):
            add(a)
    w = _wait(acts)
    if w:
        add(w)
    read = read or Read(s)
    moves = [a for a in acts if a.kind in ('move', 'qs', 'sprint')]
    if side == 'O':
        want = {}
        for i, lks in read.looks.items():
            want[i] = [lk.c for lk in lks[:per_player]]
        for a in moves:
            if a.dest in want.get(a.piece, ()):
                add(a)
        # each attacker's move that most raises the best look of a teammate (spacing, dragging a defender) is found
        # by the ordering pass; here a few of his moves that change who blocks whom: away from the carrier's lane
        bp = s.o[s.ball]
        for i in range(5):
            if i == s.ball:
                continue
            mine = [a for a in moves if a.piece == i and a.kind == 'move']
            mine.sort(key=lambda a: (-B.cheb(a.dest, bp), a.dest))
            for a in mine[:1]:
                add(a)
        scr = [a for a in acts if a.kind == 'screen']
        scr.sort(key=lambda a: min(B.cheb(B.add(s.o[a.piece], B.DIRS[a.target]), xp) for xp in s.x))
        for a in scr[:4]:
            add(a)
    else:
        if s.stage == 'reaction' and s.ctx.rules.contest_action:
            # D-18: the closeouts: every movement that ends next to the shooter (a Move facing him), so a Contest can follow
            sp = s.o[s.ball]
            for a in moves:
                if B.adjacent(a.dest, sp) and (a.kind != 'move' or a.arrow == B.dir_between(a.dest, sp)):
                    add(a)
        cv = read.cover()
        targets = {}
        for j, resp in cv['choice'].items():
            targets.setdefault(j, []).append(resp)
        for j, rs in cv['R'].items():
            for resp, _ in rs[1:per_player + 1]:
                targets.setdefault(j, []).append(resp)
        for a in moves:
            for (q, arrow, used) in targets.get(a.piece, []):
                if a.dest == q and (a.kind != 'move' or a.arrow == arrow):
                    add(a)
        # every defender keeps at least one movement: the one nearest the offence's best look (ordering only)
        spots = [lk.c for lks in read.looks.values() for lk in lks[:1]] or [s.o[s.ball]]
        for j in range(5):
            mine = [a for a in moves if a.piece == j]
            if mine and not any(a.piece == j for a in keep if a.kind in ('move', 'qs', 'sprint')):
                mine.sort(key=lambda a: (min(B.cheb(a.dest, c) for c in spots), a.kind != 'move', a.dest, a.arrow))
                add(mine[0])
    if not keep:
        return acts
    return keep


def _step(s, a):
    """Apply one action; returns the state or ChanceNode."""
    return apply(s, a)


def turns(s, beam, read=None, evaluate=None, deadline=None, expand=None, second=2):
    """The candidate whole turns from s (lists of 1 or 2 actions), ordered by the value after the turn's
    deterministic part (the side's own point of view), at most `beam`. A turn ends at a turn-ender, a roll, the
    side's second action or a change of side."""
    side = actor(s)
    sign = 1 if side == 'O' else -1
    first = candidate_actions(s, read)
    scored = []
    for a in first:
        if deadline and time.time() > deadline:
            raise Timeout
        nxt = _step(s, a)
        if isinstance(nxt, ChanceNode) or nxt.stage == 'over' or actor(nxt) != side or nxt.stage != s.stage:
            v = evaluate(nxt) if evaluate else 0.0
            scored.append((sign * v, (a,)))
            continue
        v = evaluate(nxt) if evaluate else 0.0
        scored.append((sign * v, (a,)))
        if len(scored) > 4 * beam:
            continue
    scored.sort(key=lambda r: -r[0])
    out = list(scored[:beam])
    # second actions after the best non-ending first actions
    for _, t in scored[:(expand if expand is not None else max(3, beam // 3))]:
        a = t[0]
        nxt = _step(s, a)
        if isinstance(nxt, ChanceNode) or nxt.stage == 'over' or actor(nxt) != side or nxt.stage != s.stage:
            continue
        for b in candidate_actions(nxt, None, per_player=second):
            if deadline and time.time() > deadline:
                raise Timeout
            if b.kind in ('end_turn', 'forfeit'):
                continue
            n2 = _step(nxt, b)
            v = evaluate(n2) if evaluate else 0.0
            out.append((sign * v, (a, b)))
    out.sort(key=lambda r: -r[0])
    seen, final = set(), []
    for v, t in out:
        key = frozenset(t) if len(t) == 2 and all(x.kind in ('move', 'qs', 'sprint') for x in t) else t
        if key in seen:
            continue
        seen.add(key)
        final.append((v, t))
        if len(final) >= beam:
            break
    return final


def play_turn(s, t):
    """Apply a turn's actions; a roll mid-turn stops it (the rest of the turn is decided after the roll)."""
    node = s
    for a in t:
        if isinstance(node, ChanceNode) or node.stage == 'over':
            break
        if a not in legal_actions(node):
            break
        node = _step(node, a)
    return node


# ---- the searcher ------------------------------------------------------------------------------------------------------

class Searcher:
    """Expectimax alpha-beta over whole turns with Star2 at chance nodes. me: the side whose decision this is;
    opp_weight: the opponent model (1.0 = the opponent's best reply; 0 = a passive opponent; between: the mix).
    evaluate(s): the leaf value (offence's view)."""

    def __init__(self, me, profile, evaluate, deadline, rng=None):
        self.me = me
        self.p = profile
        self.evaluate = evaluate
        self.deadline = deadline
        self.tt = {}
        self.tcache = {}
        self.killers = {}
        self.history = {}
        self.nodes = 0
        self.leaves = 0
        self.rng = rng or random.Random(0)
        self.lam = profile['opponent_model']
        self.habit = None                # All-Star scouting: the human's most frequent first action by stage
        self.habit_weight = 0.0

    def check(self):
        if time.time() > self.deadline:
            raise Timeout

    def leaf(self, s):
        self.leaves += 1
        return self.evaluate(s)

    def value(self, node, depth, alpha, beta):
        """The value of a state or ChanceNode with `depth` turn plies to go (offence's view)."""
        self.check()
        if isinstance(node, ChanceNode):
            return self.chance(node, depth, alpha, beta)
        s = node
        if s.stage == 'over':
            return terminal_value(s)
        if depth <= 0:
            return self.leaf(s)
        key = (zobrist(s), depth)
        hit = self.tt.get(key)
        if hit is not None:
            v, flag = hit[0], hit[1]
            if flag == 0 or (flag == 1 and v >= beta) or (flag == -1 and v <= alpha):
                return v
        side = actor(s)
        ts = self.turns_of(s)
        if not ts:
            return self.leaf(s)
        ts = self.order(ts, depth)
        self.nodes += 1
        a0, b0 = alpha, beta
        best = None
        opponent = side != self.me
        mix = opponent and (self.lam < 1.0 or bool(self.habit))
        passive = None
        if mix:
            w = [t for _, t in ts if t[0].kind in ('end_turn', 'pause', 'hesitate', 'forfeit')]
            passive = self.value(play_turn(s, w[0]), depth - 1, VMIN, VMAX) if w else None
        for _, t in ts:
            v = self.value(play_turn(s, t), depth - 1, VMIN if mix else alpha, VMAX if mix else beta)
            if side == 'O':
                if best is None or v > best[0]:
                    best = (v, t)
                if not mix:
                    alpha = max(alpha, v)
            else:
                if best is None or v < best[0]:
                    best = (v, t)
                if not mix:
                    beta = min(beta, v)
            if not mix and alpha >= beta:
                self.killer(depth, t)
                self.history[t[0]] = self.history.get(t[0], 0) + depth * depth
                break
        v = best[0]
        if mix and passive is not None:
            v = self.lam * v + (1 - self.lam) * passive
        if mix and self.habit:
            kind = self.habit.get(s.stage + '/' + side)
            hv = next((self.value(play_turn(s, t), depth - 1, VMIN, VMAX) for _, t in ts if t[0].kind == kind), None)
            if hv is not None:
                v = (1 - self.habit_weight) * v + self.habit_weight * hv
        flag = 0
        if not mix:
            flag = 1 if v >= b0 else -1 if v <= a0 else 0
        self.tt[key] = (v, flag, best[1])
        return v

    def chance(self, node, depth, alpha, beta):
        """Star2 (Ballard): bounds from the values already searched and [VMIN, VMAX] for the rest; a probing pass
        searches each outcome's first turn only, which bounds it from one side; then the full search, cutting off as
        soon as the bounds fall outside the window."""
        outs = node.outcomes
        key = None
        probs = [float(p) for p, _, _ in outs]
        lo_b = [VMIN] * len(outs)
        hi_b = [VMAX] * len(outs)
        # Star2 probing: one turn of each outcome bounds it from one side (a max node is at least the value of its
        # first-ordered turn, a min node at most); a terminal outcome is exact; a transposition hit may be exact
        for k, (p, _, sub) in enumerate(outs):
            if probs[k] == 0 or isinstance(sub, ChanceNode):
                continue
            if sub.stage == 'over':
                lo_b[k] = hi_b[k] = terminal_value(sub)
                continue
            hit = self.tt.get((zobrist(sub), depth))
            if hit is not None and hit[1] == 0:
                lo_b[k] = hi_b[k] = hit[0]
                continue
            if depth <= 0:
                continue
            ts = self.turns_of(sub)
            if not ts:
                continue
            first = self.order(ts, depth)[0][1]
            v = self.value(play_turn(sub, first), depth - 1, VMIN, VMAX)
            if actor(sub) == 'O':
                lo_b[k] = max(lo_b[k], v)
            else:
                hi_b[k] = min(hi_b[k], v)
        lo = sum(p * l for p, l in zip(probs, lo_b))
        hi = sum(p * h for p, h in zip(probs, hi_b))
        if hi <= alpha:
            return hi
        if lo >= beta:
            return lo
        total = 0.0
        for k, (p, _, sub) in enumerate(outs):
            pf = probs[k]
            if pf == 0:
                continue
            if lo_b[k] == hi_b[k]:
                v = lo_b[k]
            else:
                rest_lo = sum(probs[m] * lo_b[m] for m in range(k + 1, len(outs)))
                rest_hi = sum(probs[m] * hi_b[m] for m in range(k + 1, len(outs)))
                a = (alpha - total - rest_hi) / pf
                b = (beta - total - rest_lo) / pf
                v = self.value(sub, depth, max(VMIN, a), min(VMAX, b))
            total += pf * v
            lo_b[k] = hi_b[k] = v
            done_lo = total + sum(probs[m] * VMIN for m in range(k + 1, len(outs)))
            done_hi = total + sum(probs[m] * VMAX for m in range(k + 1, len(outs)))
            if done_hi <= alpha:
                return done_hi
            if done_lo >= beta:
                return done_lo
        return total

    def quick(self, node):
        """Move ordering only: THREAT without the coverage search (a cheaper read than the leaf)."""
        if isinstance(node, ChanceNode):
            return sum(float(p) * self.quick(sub) for p, _, sub in node.outcomes)
        if node.stage == 'over':
            return terminal_value(node)
        return Read(node, k=0, looks_per=3).leaf()

    def turns_of(self, s):
        key = zobrist(s)
        hit = self.tcache.get(key)
        if hit is None:
            hit = turns(s, self.p['beam'], evaluate=self.quick, deadline=self.deadline, expand=3, second=1)
            self.tcache[key] = hit
        return hit

    def killer(self, depth, t):
        ks = self.killers.setdefault(depth, [])
        if t not in ks:
            ks.insert(0, t)
            del ks[2:]

    def order(self, ts, depth):
        ks = self.killers.get(depth, [])
        return sorted(ts, key=lambda r: (0 if r[1] in ks else 1, -(r[0] + 0.01 * self.history.get(r[1][0], 0))))

    def root(self, s, max_depth, min_depth=1):
        """Iterative deepening. Returns (scored turns [(value, turn)], depth reached, the principal turn)."""
        side = actor(s)
        budget = self.deadline - time.time()
        root_read = Read(s, exact=budget >= 0.8)            # the rules' exact reach when the budget allows
        ts = turns(s, self.p['beam'], read=root_read, evaluate=self.quick, deadline=None,
                   expand=None if budget >= 0.8 else 2, second=2 if budget >= 0.8 else 1)
        deadline, self.deadline = self.deadline, float('inf')
        results = []
        sign = 1 if side == 'O' else -1
        for k, (q, t) in enumerate(ts):
            # the first ply: each turn's leaf; once the deadline passes (and the first three have their leaf), the
            # rest keep their ordering value
            if k >= 3 and time.time() > deadline:
                results.append((sign * q, t))
                continue
            n = play_turn(s, t)
            results.append((self.leaf(n) if not isinstance(n, ChanceNode) else self.value(n, 0, VMIN, VMAX), t))
        self.deadline = deadline
        reached = 1
        self.partial = 0
        for depth in range(2, max_depth + 1):
            out = []
            try:
                for _, t in sorted(results, key=lambda r: -r[0] if side == 'O' else r[0]):
                    v = self.value(play_turn(s, t), depth - 1, VMIN, VMAX)
                    out.append((v, t))
                results = out
                reached = depth
            except Timeout:
                # a partial iteration: the principal turn was re-searched first; a turn searched deeper replaces it
                # only if it is better at that depth
                self.partial = len(out)
                if out:
                    pv_v = out[0][0]
                    best = max(out, key=lambda r: r[0]) if side == 'O' else min(out, key=lambda r: r[0])
                    if (best[0] > pv_v if side == 'O' else best[0] < pv_v) or len(out) == 1:
                        done = {r[1] for r in out}
                        results = out + [r for r in results if r[1] not in done]
                break
        results.sort(key=lambda r: -r[0] if side == 'O' else r[0])
        return results, reached
