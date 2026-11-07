"""Actions and legal move generation."""
from typing import NamedTuple

from . import board as B
from . import geometry as G
from . import rules_config as RC

ORDER = ['target', 'pick', 'forced_shot', 'contest', 'end_turn', 'forfeit', 'shot', 'pass', 'dribble', 'screen', 'hesitate',
         'intercept', 'steal', 'challenge', 'pause', 'move', 'qs', 'sprint']
TOKEN_FREE = {'target', 'pick', 'end_turn', 'forfeit', 'contest', 'forced_shot'}
MOVEMENT = {'move', 'qs', 'sprint'}


class Action(NamedTuple):
    """An action. A NamedTuple: hashable, ordered, cheap to build."""
    kind: str
    side: str
    piece: int = -1          # acting player (index 0..4)
    dest: tuple = None       # movement destination
    arrow: int = -1          # defender arrow after a Move
    target: int = -1         # pass receiver / dribble defender / screen T direction / challenged screener
    shot: str = ''           # shot type

    def sort_key(self):
        return (ORDER.index(self.kind), self.piece, self.dest or (-9, -9), self.arrow, self.target, self.shot)

    def __str__(self):
        who = f'{self.side}{self.piece + 1}' if self.piece >= 0 else self.side
        k = self.kind
        if k == 'move':
            s = f'{who} Move to {B.sq(self.dest)}'
            return s + (f' facing {B.DIR_NAMES[self.arrow]}' if self.arrow >= 0 else '')
        if k == 'qs':
            return f'{who} Quick Step to {B.sq(self.dest)}'
        if k == 'sprint':
            return f'{who} Sprint to {B.sq(self.dest)}'
        if k == 'pass':
            return f'{who} Pass to O{self.target + 1}'
        if k == 'screen':
            return f'{who} Screen, T {B.DIR_NAMES[self.target]}'
        if k == 'dribble':
            return f'{who} Dribble vs X{self.target + 1}'
        if k == 'shot':
            return f'{who} Shot ({self.shot})'
        if k == 'intercept':
            if self.dest is not None:
                return f"{who} Intercept, jumping the lane to {B.sq(self.dest)} ({'Move' if self.target == 0 else 'Quick Step'})"
            return f'{who} Intercept'
        if k == 'challenge':
            return f'{who} Challenge screen of O{self.target + 1}'
        if k == 'steal':
            return f'{who} Steal'
        if k == 'target':
            return f"Coach's Call target O{self.target + 1}"
        if k == 'contest':
            return f'{who} contests' if self.piece >= 0 else "X: don't contest"
        if k == 'forced_shot':
            return f'{who} forced shot ({self.shot})'
        if k == 'pick':
            return f'Failed inbound: ball to O{self.target + 1}'
        if k == 'end_turn':
            return f'{who} End turn'
        if k == 'forfeit':
            return f'{who} Forfeit tokens (no legal action)'
        return f'{who} {k.capitalize()}'

    __repr__ = __str__


_new = tuple.__new__      # fast Action construction for the big movement lists


# ---- geometry helpers that need the state -----------------------------------------

def t_square(state, screen):
    i, d = screen[0], screen[1]
    return B.add(state.o[i], B.DIRS[d])


def zone(state, j):
    """Defender j's zone of influence (ruled, step 3i follow-up): the squares along each of his arrow
    directions that he could reach with one movement in that direction, with his remaining capacity: a Move
    if unused; a Sprint if his Move and Quick Step are both available; a Quick Step only once his Move is
    used; a locked defender keeps only his Quick Step reach (and can't turn). It stops at the first square
    another player stands on. {square: 'move' | 'qs' | 'sprint'}, the movement that reaches it (solid for a
    Move or Quick Step, the lighter extension for a Sprint)."""
    rules = state.ctx.rules
    start = state.x[j]
    dests = {}
    for kind in ('move', 'qs', 'sprint'):
        if can_move_kind(state, 'X', j, kind) and (kind != 'qs' or state.ctx.dfn[j].qs > 0):
            dests[kind] = movement_dests(state, 'X', j, kind, rules)
    occ = state.occupied()
    out = {}
    for d in G.lines(rules, state.arrows[j]):
        step = B.DIRS[d]
        q = start
        while True:
            q = B.add(q, step)
            if not B.on_board(q) or q in occ:
                break
            kind = next((k for k in ('move', 'qs', 'sprint') if k in dests and q in dests[k]), None)
            if kind is None:
                break
            out[q] = kind
    return out


def path_ok(state, side, i, path, rules, occ=None, zones=None):
    """Is this movement path legal for player i of side?"""
    start = state.o[i] if side == 'O' else state.x[i]
    if occ is None:
        occ = state.occupied()
    for q in path:
        if not B.on_board(q) or q in occ:
            return False
    if side == 'X':
        if not state.screens:
            return True
        pts = (start,) + tuple(path)
        for scr in state.screens:
            tsq = t_square(state, scr)
            if scr[3] >> i & 1:              # beat this screen: may cross T, not stop on it
                if path[-1] == tsq:
                    return False
                continue
            for a, b in zip(pts, pts[1:]):
                if B.diag_step_banned(a, b, tsq, rules):
                    return False
    elif i == state.ball:
        if rules.drive_rule == 'zone':       # ruled: may end in an adjacent defender's zone, not pass through it
            if zones is None:
                zones = carrier_zones(state, i)
            for q in path[:-1]:
                if any(q in z for z in zones.values()):
                    return False
            return True
        pts = (start,) + tuple(path)
        for j, xp in enumerate(state.x):
            if B.adjacent(xp, start) and (i, j) not in state.beaten:
                if G.path_crosses(rules, pts, xp, state.arrows[j], rules.arrow_line_strict):
                    return False
    return True


def carrier_zones(state, i):
    """The zones that restrict ball carrier i: those of the defenders adjacent to him, unless beaten."""
    start = state.o[i]
    return {j: set(zone(state, j)) for j, xp in enumerate(state.x)
            if B.adjacent(xp, start) and (i, j) not in state.beaten}


def movement_dests(state, side, i, kind, rules):
    """dest -> run direction (Sprint) or None, for one movement kind."""
    card = (state.ctx.off if side == 'O' else state.ctx.dfn)[i]
    start = state.o[i] if side == 'O' else state.x[i]
    if kind == 'move':
        paths = [(None, p) for p in B.move_paths(start, rules)]
    elif kind == 'qs':
        paths = [(None, p) for p in B.qs_paths(start, card.qs, rules)]
    else:
        paths = B.sprint_paths(start, card.qs, rules)
    out = {}
    occ = state.occupied()
    zs = carrier_zones(state, i) if side == 'O' and i == state.ball and rules.drive_rule == 'zone' else None
    for d, path in paths:
        dest = path[-1]
        if dest in out:
            continue
        if path_ok(state, side, i, path, rules, occ, zs):
            out[dest] = d
    return out


def can_move_kind(state, side, i, kind):
    """Limits and status for a movement kind (ignores geometry)."""
    rules = state.ctx.rules
    if state.tokens(side) <= 0:
        return False
    if side == 'O':
        if state.is_screening(i) and rules.screen_rule == 'two_turns':
            return False                    # the old rule: the screener can't move while his screen stands
        if i == state.ctx.inbounder and state.inbound:      # inbounder can't move until the ball is in
            return False
    if kind in ('move', 'sprint'):
        if state.moved(side, i) or state.locked(side, i):
            return False
    if kind in ('qs', 'sprint'):
        if state.count(side, 'qs') >= RC.LIMITS[side]['qs']:
            return False
        if rules.qs_once_per_player and state.quick_stepped(side, i):
            return False                    # OQ-52: that player's Quick Step is used (a Sprint uses it too)
    return True


def movement_actions(state, side, rules):
    """Movement actions grouped by kind (move, qs, sprint), each in piece order."""
    acts = []
    pieces = state.o if side == 'O' else state.x
    for kind in ('move', 'qs', 'sprint'):
        for i in range(5):
            if not can_move_kind(state, side, i, kind):
                continue
            dests = movement_dests(state, side, i, kind, rules)
            if side == 'X' and kind == 'move':
                start = pieces[i]
                cur = state.arrows[i]
                acts += [_new(Action, ('move', 'X', i, start, d, -1, '')) for d in range(8) if d != cur]   # arrow turn
                acts += [_new(Action, ('move', 'X', i, dest, d, -1, '')) for dest in dests for d in range(8)]
            else:
                acts += [_new(Action, (kind, side, i, dest, -1, -1, '')) for dest in dests]
                if side == 'X' and kind == 'sprint' and rules.arrow_mode == 'wedge':
                    # wedge: the run direction is one edge; the other may go either side (-1 = clockwise)
                    start = pieces[i]
                    for dest in dests:
                        r = sprint_dir(start, dest)
                        acts.append(_new(Action, (kind, side, i, dest, (r - 1) % 8, -1, '')))
    return acts


def sprint_dir(start, dest):
    dx, dy = dest[0] - start[0], dest[1] - start[1]
    n = max(abs(dx), abs(dy))
    return B.DIRS.index((dx // n, dy // n))


# ---- intercept geometry ---------------------------------------------------------

# ---- interception (OQ-72 ruling, intercept_rule='ring_jump') --------------------------------

def passer_ring(state):
    """The squares next to the passer of the pending pass: no Intercept happens on any of them."""
    a = state.o[state.pending[0]]
    return {B.add(a, d) for d in B.DIRS}


def lane_crossing(p, d, a, b):
    """Where the arrow ray from p in direction d meets the pass segment a-b: the number of ray squares to the
    crossing square (the first ray square at or past the geometric intersection), or None. A diagonal pass
    can't slip between two corner-touching ray squares: the next square along the ray catches it."""
    import math
    dx, dy = B.DIRS[d]
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = dx * ey - dy * ex
    if den == 0:
        return None                                   # the ray runs parallel to the pass
    wx, wy = a[0] - p[0], a[1] - p[1]
    t = (wx * ey - wy * ex) / den
    u = (wx * dy - wy * dx) / den
    if t <= 1e-9 or u <= 1e-9 or u >= 1 - 1e-9:
        return None
    return max(1, math.ceil(t - 1e-9))


def lane_meet(p, d, a, b):
    """Where a straight path from p in direction d meets the pass segment a-b: the number of squares to the
    square that contains the intersection (squares are unit cells round their centres), or None. At a corner
    between two diagonal squares (a diagonal pass slipping between corner-touching squares) it is the next
    square along the path: the corner-slip fix."""
    import math
    dx, dy = B.DIRS[d]
    ex, ey = b[0] - a[0], b[1] - a[1]
    den = dx * ey - dy * ex
    if den == 0:
        return None
    wx, wy = a[0] - p[0], a[1] - p[1]
    t = (wx * ey - wy * ex) / den
    u = (wx * dy - wy * dx) / den
    if u <= 1e-9 or u >= 1 - 1e-9:
        return None
    n = math.floor(t + 0.5 + 1e-9)
    return n if n >= 1 else None


def through_you(state, j):
    """Defender j may Intercept the pending pass where he stands: the line passes through his square, he isn't
    in the passer's ring, and he hasn't moved this defence turn (a movement is only a movement)."""
    rules = state.ctx.rules
    passer, recv = state.pending
    p = state.x[j]
    if p in passer_ring(state) or state.turn_moved >> j & 1:
        return False
    return B.on_segment(p, state.o[passer], state.o[recv], rules.on_line_tolerance)


def lane_jumps(state, j):
    """Defender j's lane jumps against the pending pass: [(crossing square, 'move' | 'qs')], each one straight
    Move or Quick Step along one of his arrow lines to the crossing square, with that movement unused."""
    rules = state.ctx.rules
    p = state.x[j]
    ring = passer_ring(state)
    if p in ring:
        return []                                     # a defender next to the passer can't Intercept
    passer, recv = state.pending
    a, b = state.o[passer], state.o[recv]
    occ = state.occupied()
    out = []
    for d in G.lines(rules, state.arrows[j]):
        k = lane_crossing(p, d, a, b)
        if k is None:
            continue
        path = tuple(B.add(p, (B.DIRS[d][0] * n, B.DIRS[d][1] * n)) for n in range(1, k + 1))
        q = path[-1]
        if not B.on_board(q) or q in ring or q in occ:
            continue
        for kind in ('move', 'qs'):
            if not can_move_kind(state, 'X', j, kind):
                continue
            if kind == 'qs' and state.ctx.dfn[j].qs <= 0:
                continue
            shapes = B.move_paths(p, rules) if kind == 'move' else B.qs_paths(p, state.ctx.dfn[j].qs, rules)
            if not any(tuple(sh) == path for sh in shapes):
                continue                              # beyond his straight reach of that kind
            if path_ok(state, 'X', j, list(path), rules, occ):
                out.append((q, kind))
    return out


def intercept_actions(state):
    """Every Intercept open to the defence against the pending pass: through a defender's square
    (Action('intercept', 'X', j)) or a lane jump (dest = the crossing square, target 0 a Move, 1 a Quick Step).
    Ruled: after a movement (the turn's first action) only the defender who moved may jump; one defender's
    movement never opens a jump for a teammate. A defender the line passes through, unmoved, still may."""
    out = []
    for j in range(5):
        if through_you(state, j):
            out.append(Action('intercept', 'X', j))
        if state.turn_n >= 1 and not state.turn_moved >> j & 1:
            continue                    # ruled: as the turn's second action, a jump follows the jumper's own movement
        for q, kind in lane_jumps(state, j):
            out.append(Action('intercept', 'X', j, dest=q, target=0 if kind == 'move' else 1))
    return out


def follow_jumps(state):
    """The defence's two-action answers: a movement by a defender (the pass still in the air), then a lane
    jump from his new square with the straight reach he has left. [(movement, intercept)]."""
    from .resolve import apply, ChanceNode
    if state.tok_x < 2 or state.turn_n != 0 or state.ctx.rules.intercept_rule != 'ring_jump':
        return []
    rules = state.ctx.rules
    passer, recv = state.pending
    a, b = state.o[passer], state.o[recv]
    ring = passer_ring(state)
    out = []
    for m in movement_actions(state, 'X', rules):
        if m.kind == 'sprint' or m.dest in ring:
            continue                                  # a Sprint leaves no straight reach to jump with
        j = m.piece
        # what straight reach he has left after this movement: a Quick Step after a Move, a Move after a Quick Step
        if m.kind == 'move':
            arrow, left = m.arrow, state.ctx.dfn[j].qs
            if left <= 0 or state.quick_stepped('X', j) or state.count('X', 'qs') >= RC.LIMITS['X']['qs']:
                continue
        else:
            arrow, left = state.arrows[j], None   # a Move: 3 straight or 2 diagonal
            if state.moved('X', j) or state.locked('X', j):
                continue
        hit = False
        for d in G.lines(rules, arrow):
            k = lane_crossing(m.dest, d, a, b)
            if k is None:
                continue
            reach = left if left is not None else (RC.MOVE_STRAIGHT if d % 2 == 0 else RC.MOVE_DIAGONAL)
            if k <= reach:
                hit = True
                break
        if not hit:
            continue
        nxt = apply(state, m)
        if isinstance(nxt, ChanceNode) or nxt.side != 'X' or not nxt.pending:
            continue
        for q, kind in lane_jumps(nxt, j):
            out.append((m, Action('intercept', 'X', j, dest=q, target=0 if kind == 'move' else 1)))
    return out


# ---- interception (the OQ-72 refinement, intercept_rule='move_then_intercept') --------------------------

def mti_approach(state, a):
    """Is defence movement a the first half of 'one movement, then Intercept'? One Move, Quick Step or Sprint
    as the defence's first action, from his starting square straight along one of his arrow lines, whose path
    crosses or ends on the pass line, ending on the square where it meets it (lane_meet: the square holding
    the intersection, or the next one at a diagonal corner: the corner-slip fix), not next to the passer, a Sprint keeping his
    facing, a Move too (the rulebook: "keeping your facing"), with a token left for the Intercept."""
    if not (state.pending and a.side == 'X' and a.kind in MOVEMENT and state.turn_n == 0 and state.stage == 'play'):
        return False
    if state.count('X', 'intercept') >= RC.LIMITS['X']['intercept'] or state.tok_x < 2:
        return False
    rules = state.ctx.rules
    j = a.piece
    p, q = state.x[j], a.dest
    if q in passer_ring(state):
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    n = max(abs(dx), abs(dy))
    if n == 0 or dx not in (-n, 0, n) or dy not in (-n, 0, n):
        return False                                  # not a straight line
    d = B.DIRS.index((dx // n, dy // n))
    if d not in G.lines(rules, state.arrows[j]):
        return False                                  # off the arrow
    passer, recv = state.pending
    pa, pb = state.o[passer], state.o[recv]
    if lane_meet(p, d, pa, pb) != n:
        return False                                  # doesn't end where his path meets the pass line
    if a.kind == 'sprint':
        keep = a.arrow if (rules.arrow_mode == 'wedge' and a.arrow == (d - 1) % 8) else d
        if keep != state.arrows[j]:
            return False                              # a Sprint along the arrow keeps his facing
    elif a.kind == 'move' and rules.lane_jump_keeps_facing and a.arrow != state.arrows[j]:
        return False                                  # rulebook: a lane jump keeps your facing (a Move may not turn)
    path = [B.add(p, (B.DIRS[d][0] * k, B.DIRS[d][1] * k)) for k in range(1, n + 1)]
    return path_ok(state, 'X', j, path, rules, state.occupied())


def approach_moves(state, j=None):
    """The movements that open 'move, then Intercept' against the pending pass (all defenders, or j): built from
    the geometry (the square where each arrow line meets the pass) rather than every movement on the board."""
    if not state.pending or state.turn_n != 0 or state.stage != 'play':
        return []
    rules = state.ctx.rules
    passer, recv = state.pending
    pa, pb = state.o[passer], state.o[recv]
    ring = passer_ring(state)
    occ = state.occupied()
    out = []
    for jj in (range(5) if j is None else (j,)):
        p = state.x[jj]
        qs = state.ctx.dfn[jj].qs
        for d in G.lines(rules, state.arrows[jj]):
            n = lane_meet(p, d, pa, pb)
            if not n:
                continue
            path = tuple(B.add(p, (B.DIRS[d][0] * k, B.DIRS[d][1] * k)) for k in range(1, n + 1))
            q = path[-1]
            if not B.on_board(q) or q in ring or q in occ:
                continue
            for kind in ('move', 'qs', 'sprint'):
                if not can_move_kind(state, 'X', jj, kind):
                    continue
                if kind == 'move':
                    shapes = B.move_paths(p, rules)
                elif kind == 'qs':
                    shapes = B.qs_paths(p, qs, rules) if qs > 0 else []
                else:
                    shapes = [sp for _, sp in B.sprint_paths(p, qs, rules)] if (qs > 0 or not rules.sprint_needs_qs) else []
                if not any(tuple(sh) == path for sh in shapes):
                    continue
                if kind == 'move':
                    cands = ([_new(Action, ('move', 'X', jj, q, state.arrows[jj], -1, ''))] if rules.lane_jump_keeps_facing
                             else [_new(Action, ('move', 'X', jj, q, a, -1, '')) for a in range(8)])   # facing kept
                elif kind == 'qs':
                    cands = [_new(Action, ('qs', 'X', jj, q, -1, -1, ''))]
                else:
                    cands = [_new(Action, ('sprint', 'X', jj, q, -1, -1, ''))]
                    if rules.arrow_mode == 'wedge':
                        cands.append(_new(Action, ('sprint', 'X', jj, q, (d - 1) % 8, -1, '')))
                out += [c for c in cands if mti_approach(state, c)]
    return out


def lane_marks(pend):
    """For the interface: every way the defence can Intercept the pending pass, exactly as the legal actions
    allow it. [{defender, how: 'through' | 'jump' | 'follow', sq: where the Intercept happens, by: 'Move' |
    'Quick Step' | None, via: the follow movement's square}], and the passer's ring (no Intercept there)."""
    if pend.count('X', 'intercept') >= RC.LIMITS['X']['intercept'] or pend.tok_x <= 0:
        return [], sorted(passer_ring(pend))
    out = []
    if pend.ctx.rules.intercept_rule == 'move_then_intercept':
        if pend.turn_n == 0:
            for j in range(5):
                if through_you(pend, j):
                    out.append(dict(defender=j, how='through', sq=pend.x[j], by=None, via=None))
        seen = set()
        for m in approach_moves(pend):
            k = (m.piece, m.dest)
            if k in seen:
                continue
            seen.add(k)
            out.append(dict(defender=m.piece, how='jump', sq=m.dest, via=None,
                            by={'move': 'Move', 'qs': 'Quick Step', 'sprint': 'Sprint'}[m.kind]))
        return out, sorted(passer_ring(pend))
    for a in intercept_actions(pend):
        out.append(dict(defender=a.piece, how='through' if a.dest is None else 'jump',
                        sq=pend.x[a.piece] if a.dest is None else a.dest,
                        by=None if a.dest is None else ('Move' if a.target == 0 else 'Quick Step'), via=None))
    seen = set()
    for m, a in follow_jumps(pend):
        k = (a.piece, a.dest)
        if k in seen:
            continue
        seen.add(k)
        out.append(dict(defender=a.piece, how='follow', sq=a.dest, by='Move' if a.target == 0 else 'Quick Step', via=m.dest))
    return out, sorted(passer_ring(pend))


def _seg_dist(q, a, b):
    """Chebyshev distance from square q to the nearest point of the segment a-b (sampled)."""
    n = max(abs(b[0] - a[0]), abs(b[1] - a[1]), 1) * 2
    return min(max(abs(q[0] - (a[0] + (b[0] - a[0]) * i / n)), abs(q[1] - (a[1] + (b[1] - a[1]) * i / n))) for i in range(n + 1))


def intercept_status(state, j):
    """'direct', 'approach' or None for defender j against the pending pass. Under the OQ-72 ruling:
    'direct' = through his square, 'approach' = a lane jump open to him now."""
    rules = state.ctx.rules
    if rules.intercept_rule == 'move_then_intercept':
        if through_you(state, j):
            return 'direct'
        return 'approach' if approach_moves(state, j) else None
    if rules.intercept_rule == 'ring_jump':
        if through_you(state, j):
            return 'direct'
        return 'approach' if lane_jumps(state, j) else None
    passer, recv = state.pending
    a, b = state.o[passer], state.o[recv]
    p = state.x[j]
    on = B.on_segment(p, a, b, rules.on_line_tolerance)
    if B.adjacent(p, a):
        if G.faces(rules, state.arrows[j], p, a):
            return 'direct' if on else None
        return 'approach' if G.crosses(rules, p, state.arrows[j], a, b) else None
    if on:
        return 'direct'
    if G.crosses(rules, p, state.arrows[j], a, b):
        return 'approach'
    return None


def is_inbound_pass(state):
    return bool(state.pending) and state.inbound and state.pending[0] == state.ctx.inbounder


def inbound_held(state):
    """An inbound pass in the air that resolves only after the defence's whole turn (OQ-35)."""
    return is_inbound_pass(state) and state.ctx.rules.inbound_resolves == 'after_defence_turn'


def completed_view(state):
    """The state as if the pending pass had landed (used for legality only)."""
    return state.with_(ball=state.pending[1], pending=None, approach=-1)


# ---- legal actions --------------------------------------------------------------

def _offence_actions(s, rules):
    acts = []
    ctx = s.ctx
    tok = s.tok_o
    if tok <= 0:
        return acts
    carrier = s.ball
    cpos = s.o[carrier]
    inbounder_has_it = s.inbound and carrier == ctx.inbounder
    # Pass
    if s.count('O', 'pass') < RC.LIMITS['O']['pass']:
        for r in range(5):
            if r != carrier:
                acts.append(Action('pass', 'O', carrier, target=r))
    pass_only = inbounder_has_it and rules.inbounder_pass_only
    # Shot
    z = B.zone(cpos)
    if (not pass_only and B.on_board(cpos) and z != '.' and s.count('O', 'shot') < RC.LIMITS['O']['shot']
            and not (ctx.hold_for_one and s.clock > RC.PHASE_SECONDS)):
        for t in RC.ZONE_SHOTS[z]:
            acts.append(Action('shot', 'O', carrier, shot=t))
    # Dribble
    if (not pass_only and s.count('O', 'dribble') < RC.LIMITS['O']['dribble']
            and (rules.locked_can_dribble or not s.locked('O', carrier))):
        for j, xp in enumerate(s.x):
            if B.adjacent(xp, cpos):
                acts.append(Action('dribble', 'O', carrier, target=j))
    # Screen
    if s.count('O', 'screen') < RC.LIMITS['O']['screen']:
        for i, p in enumerate(s.o):
            if not B.on_board(p) or s.is_screening(i):
                continue
            if rules.screen_rule == 'hold_until_move' and not (s.turn_n == 0 or (s.turn_n == 1 and s.turn_lead == i)):
                continue                     # OQ-29: first action, or second straight after his own Move
            if i == ctx.inbounder and s.inbound:
                continue
            if i == carrier and not rules.carrier_can_screen:
                continue                     # ruled (step 3i): the ball carrier can't Screen
            for d in range(8):
                if B.on_board(B.add(p, B.DIRS[d])):
                    acts.append(Action('screen', 'O', i, target=d))
    # Hesitate
    if s.count('O', 'hesitate') < RC.LIMITS['O']['hesitate'] and not (rules.wait_chain_block and s.prev_wait == 'P'):
        acts.append(Action('hesitate', 'O'))
    acts += movement_actions(s, 'O', rules)
    return acts


def _defence_actions(s, rules, kinds=None):
    acts = []
    if s.tok_x <= 0:
        return acts
    cpos = s.o[s.ball]
    ok = (lambda k: True) if kinds is None else (lambda k: k in kinds)
    if ok('steal') and s.count('X', 'steal') < RC.LIMITS['X']['steal']:
        for j, xp in enumerate(s.x):
            if G.faces(rules, s.arrows[j], xp, cpos):
                acts.append(Action('steal', 'X', j))
    if ok('challenge') and s.count('X', 'challenge') < RC.LIMITS['X']['challenge']:
        for scr in s.screens:
            for j, xp in enumerate(s.x):
                if scr[3] >> j & 1:
                    continue
                if rules.challenge_who == 'adjacent' and not B.adjacent(xp, s.o[scr[0]]):
                    continue
                if rules.challenge_who == 'on_t' and xp != t_square(s, scr):
                    continue
                acts.append(Action('challenge', 'X', j, target=scr[0]))
    if ok('pause') and s.count('X', 'pause') < RC.LIMITS['X']['pause'] and not (rules.wait_chain_block and s.prev_wait == 'H'):
        acts.append(Action('pause', 'X'))
    mv = movement_actions(s, 'X', rules)
    if kinds is not None:
        mv = [a for a in mv if a.kind in kinds]
    return acts + mv


def legal_actions(state):
    """Every legal action for the side to act, in a deterministic order."""
    s = state
    rules = s.ctx.rules
    if s.stage == 'over':
        return []
    if s.stage == 'target':
        return [Action('target', 'O', target=i) for i in range(5)]
    if s.stage == 'contest':
        from .scoring import contest_options
        return [Action('contest', 'X', o.defender) for o in contest_options(s, s.ball, s.shot, s.forced)]
    if s.stage == 'forced':
        return [Action('forced_shot', 'O', s.ball, shot=t) for t in RC.ZONE_SHOTS[B.zone(s.o[s.ball])]]
    if s.stage == 'pick':
        return [Action('pick', 'O', target=i) for i in inbound_tie_candidates(s)]
    side = s.side
    acts = []
    if s.stage == 'reaction':
        acts = _defence_actions(s, rules, kinds=set(rules.reaction_kinds))
        if s.turn_n >= 1 or rules.reaction_may_decline or not acts:
            acts.append(Action('end_turn', 'X'))
    elif side == 'O':
        acts = _offence_actions(s, rules)
        if s.turn_n >= 1:
            acts.append(Action('end_turn', 'O'))
    else:
        if s.pending and rules.intercept_rule == 'ring_jump':
            # OQ-72 ruling: an Intercept through a defender's square or by a lane jump; any movement keeps the
            # pass in the air (a defender may follow, then jump); any other action lands the pass first
            can_icpt = s.count('X', 'intercept') < RC.LIMITS['X']['intercept'] and s.tok_x > 0
            if can_icpt:
                acts += intercept_actions(s)
            if is_inbound_pass(s) and not inbound_held(s):
                if s.turn_n == 0:
                    acts += movement_actions(s, 'X', rules)      # follow, then jump
                acts.append(Action('end_turn', 'X'))             # let the inbound pass in
            else:
                acts += movement_actions(s, 'X', rules)          # the pass stays in the air
                view = s if inbound_held(s) else completed_view(s)
                others = [a for a in _defence_actions(view, rules) if a.kind not in MOVEMENT]
                if inbound_held(s):
                    others = [a for a in others if a.kind != 'steal']
                acts += others                                   # these land the pass first
                if s.turn_n >= 1:
                    acts.append(Action('end_turn', 'X'))
        elif s.pending:
            can_icpt = s.count('X', 'intercept') < RC.LIMITS['X']['intercept'] and s.tok_x > 0
            if s.turn_n == 0 and can_icpt:
                for j in range(5):
                    if intercept_status(s, j) == 'direct':
                        acts.append(Action('intercept', 'X', j))
            if s.turn_n == 1 and s.approach >= 0 and can_icpt:
                acts.append(Action('intercept', 'X', s.approach))
            if inbound_held(s):
                # the defence plays a normal turn while the ball is in the air; a defender already
                # on the line (and still there, unmoved) may intercept with either action
                if s.turn_n == 1 and can_icpt and rules.intercept_rule != 'move_then_intercept':
                    for j in range(5):
                        if intercept_status(s, j) == 'direct' and not (s.turn_moved >> j & 1):
                            acts.append(Action('intercept', 'X', j))
                acts += [a for a in _defence_actions(s, rules) if a.kind != 'steal']
                if s.turn_n >= 1:
                    acts.append(Action('end_turn', 'X'))
            elif is_inbound_pass(s):
                if s.turn_n == 0 and can_icpt:
                    for a in movement_actions(s, 'X', rules):
                        if is_approach(s, a):
                            acts.append(a)
                acts.append(Action('end_turn', 'X'))       # let the inbound pass in
            else:
                acts += _defence_actions(completed_view(s), rules)
                if s.turn_n >= 1:
                    acts.append(Action('end_turn', 'X'))
        else:
            acts = _defence_actions(s, rules)
            if s.turn_n >= 1:
                acts.append(Action('end_turn', 'X'))
    if not acts and rules.forfeit_when_stuck and s.tokens(side) > 0:
        acts = [Action('forfeit', side)]
    return _ordered(acts)


def _ordered(acts):
    """Group by kind in ORDER (stable within a kind: generation order is deterministic).
    Movement actions already come grouped and last, so only the rest needs sorting."""
    rest = [a for a in acts if a.kind not in MOVEMENT]
    if len(rest) == len(acts):
        return sorted(rest, key=lambda a: ORDER.index(a.kind))
    mv = [a for a in acts if a.kind in MOVEMENT]          # generated grouped by kind already
    rest.sort(key=lambda a: ORDER.index(a.kind))          # stable sort keeps generation order
    return rest + mv


def inbound_tie_candidates(state):
    """On-court players (not the inbounder) tied for furthest from the rim."""
    ib = state.ctx.inbounder
    cands = [i for i in range(5) if i != ib and B.on_board(state.o[i])]
    far = max(B.dist_rim(state.o[i]) for i in cands)
    return [i for i in cands if B.dist_rim(state.o[i]) == far]


def is_approach(state, a):
    """Is this defender movement an approach onto the pending pass line? (The old rule only: under the OQ-72
    ruling the lane jump is the Intercept itself, and any other movement is only a movement.)"""
    if state.ctx.rules.intercept_rule == 'ring_jump':
        return False
    if state.ctx.rules.intercept_rule == 'move_then_intercept':
        return mti_approach(state, a)
    if not (state.pending and a.side == 'X' and a.kind in MOVEMENT and state.turn_n == 0):
        return False
    if state.count('X', 'intercept') >= RC.LIMITS['X']['intercept']:
        return False
    if intercept_status(state, a.piece) != 'approach':
        return False
    passer, recv = state.pending
    return B.on_segment(a.dest, state.o[passer], state.o[recv], state.ctx.rules.on_line_tolerance)
