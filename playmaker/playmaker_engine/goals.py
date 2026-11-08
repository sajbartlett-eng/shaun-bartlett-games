"""Step 3m B5: goals are predicates over THREAT and COVERAGE, never plays.

Offence: Overload(Xj; Oa, Ob), Displace(Xj, lane), CatchOpen(Oi, k), ForceRotation(n), Shot(Oi, zone, contest <= c).
Defence: Wall(Oi), Deny(lane), Shrink(Overload), Pressure(clock).

After each search the agent reads its scored root turns: Q(G) = the best value of a turn that achieves G (on the
position after the turn, the likeliest roll) minus V(s), from its own side's point of view. G* = argmax Q. It holds
a goal with hysteresis: it switches from G to G' only if Q(G') > Q(G) + m(phase), or G is achieved or infeasible, with
m(phase) = m0 x (phases remaining / 6) + the value already gained on G. Every switch is logged with its reason.
The trainer (Part D) reads the human's goals with the same predicates.
"""
from . import board as B
from . import rules_config as RC
from .decide import Read, _lane_p, lane_squares, _one_action, _caps


def _likeliest(node):
    from .resolve import ChanceNode
    while isinstance(node, ChanceNode):
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return node


def _matchups(read):
    """Who answers whom: for each attacker, the defender giving his best look its lowest contest (or -1)."""
    out = {}
    for i, lks in read.looks.items():
        if not lks:
            continue
        lk = lks[0]
        best, who = None, -1
        for d, vals in lk.vals.items():
            v = min(vals.values())
            if best is None or v < best:
                best, who = v, d
        out[i] = who
    return out


def lanes(s):
    """The lanes that matter now: the carrier to each teammate (pass lanes)."""
    a = s.o[s.ball]
    return {i: lane_squares(a, s.o[i], 0.5) for i in range(5) if i != s.ball and B.on_board(s.o[i])}


def helpers_on(s, lane):
    """Defenders who stand on, or can step onto, a lane with one action."""
    out = []
    for d, xp in enumerate(s.x):
        cm, ql = _caps(s, 'X', d)
        if not lane.isdisjoint(_one_action(xp, s.arrows[d], s.ctx.dfn[d].qs, cm, ql, s.ctx.rules)):
            out.append(d)
    return out


def goals_in(before, after, side, read_before=None, read_after=None, turn=()):
    """The goal predicates the position `after` (reached from `before` by `turn`) satisfies. Returns {key: words}."""
    rb = read_before or Read(before)
    ra = read_after or Read(after)
    out = {}
    if side == 'O':
        for ov in ra.overloads()[:3]:
            out[('Overload', ov['defender'], ov['a'], ov['b'])] = \
                f"make X{ov['defender'] + 1} the only answer to O{ov['a'] + 1} and O{ov['b'] + 1}"
        lb, la = lanes(before), lanes(after)
        for i, lane in lb.items():
            if i in la:
                was, now = set(helpers_on(before, lane)), set(helpers_on(after, la[i]))
                for d in was - now:
                    out[('Displace', d, i)] = f'move X{d + 1} out of the lane to O{i + 1}'
        for i in range(5):
            has = after.ball == i or (after.pending and after.pending[1] == i)
            if not has or not B.on_board(after.o[i]):
                continue
            sq = after.o[i]
            k = min((min(ra._cm[d].get(sq, [9])) for d in range(5)), default=9)
            if k >= 1:
                out[('CatchOpen', i, 1)] = f'get O{i + 1} the ball with every cover at least a step away'
        mb, ma = _matchups(rb), _matchups(ra)
        changed = sum(1 for i in mb if i in ma and mb[i] != ma[i] and ma[i] >= 0)
        if changed >= 2:
            out[('ForceRotation', changed)] = f'force the defence to change {changed} matchups'
        for a in turn:
            if a.kind == 'shot':
                z = B.zone(before.o[a.piece])
                lk = next((lk for lk in rb.looks.get(a.piece, []) if lk.route == 'shoot'), None)
                c = min((min(v.values()) for v in lk.vals.values()), default=None) if lk else None
                out[('Shot', a.piece, z)] = f'O{a.piece + 1} shoots from the {z} zone'
    else:
        for i in range(5):
            tb = rb.threat.get(i, {}).get('value', 0)
            ta = ra.threat.get(i, {}).get('value', 0)
            if tb > 0 and ta <= 0.5 * tb:
                out[('Wall', i)] = f'wall off O{i + 1}'
        for i in range(5):
            if i == after.ball or not B.on_board(after.o[i]):
                continue
            pb = _lane_p(before, i, before.o[i]) if before.ball != i else 1
            pa = _lane_p(after, i, after.o[i]) if after.ball != i else 1
            if pa <= 0.5 < pb:
                out[('Deny', i)] = f'deny the lane to O{i + 1}'
        ob, oa = rb.overloads(), ra.overloads()
        if ob and (not oa or oa[0]['value'] < ob[0]['value'] - 1e-9):
            out[('Shrink', ob[0]['defender'])] = f"take X{ob[0]['defender'] + 1} out of the dilemma"
        if ra.cover()['value'] < rb.cover()['value'] - 1e-9 and after.clock <= RC.START_CLOCK // 2:
            out[('Pressure',)] = 'make the clock work: no open look as it runs down'
    return out


def goal_words(key, words):
    return words.get(key, str(key))


class Commitment:
    """A goal held with hysteresis (Kinny and Georgeff's commitment: reconsider every turn group, switch only on a
    margin)."""

    def __init__(self, m0):
        self.m0 = m0
        self.goal = None
        self.words = ''
        self.q = 0.0
        self.gained = 0.0
        self.log = []

    def margin(self, s):
        remaining = max(0, s.clock) / RC.PHASE_SECONDS
        return self.m0 * (remaining / (RC.START_CLOCK / RC.PHASE_SECONDS)) + max(0.0, self.gained)

    def choose(self, s, side, scored, base, describe):
        """scored: [(value (own view), turn, goals {key: words})]; base: V(s) (own view). Returns (turn, value)
        played toward the held goal, after reconsidering it."""
        Q = {}
        words = {}
        for v, t, gs in scored:
            for g, w in gs.items():
                if g not in Q or v - base > Q[g]:
                    Q[g] = v - base
                    words[g] = w
        reason = None
        if self.goal is not None:
            if self.goal not in Q:
                reason = f'{self.words}: no turn reaches it now'
                old = self.goal
                self.goal = None
            else:
                best = max(Q, key=lambda g: Q[g]) if Q else None
                m = self.margin(s)
                if best is not None and best != self.goal and Q[best] > Q[self.goal] + m:
                    reason = (f'switched from {self.words} to {words[best]}: Q {Q[best]:+.1f} against '
                              f'{Q[self.goal]:+.1f} with margin {m:.1f}')
                    self.goal = None
        if self.goal is None and Q:
            g = max(Q, key=lambda g: Q[g])
            if reason or not self.log:
                self.log.append(dict(goal=words[g], q=round(Q[g], 2),
                                     reason=reason or f'first goal: {words[g]} (Q {Q[g]:+.1f})'))
            self.goal, self.words, self.q, self.gained = g, words[g], Q[g], 0.0
        top_v, top_t, _ = max(scored, key=lambda r: r[0])
        if self.goal is not None:
            toward = [(v, t) for v, t, gs in scored if self.goal in gs]
            if toward:
                v, t = max(toward, key=lambda r: r[0])
                if top_v > v + self.margin(s):
                    self.log.append(dict(goal=self.words, q=round(self.q, 2),
                                         reason=f'left {self.words} for one turn: a turn worth {top_v - v:+.1f} more'))
                    return top_t, top_v
                self.gained += max(0.0, v - base)
                self.q = Q.get(self.goal, self.q)
                return t, v
        return top_t, top_v
