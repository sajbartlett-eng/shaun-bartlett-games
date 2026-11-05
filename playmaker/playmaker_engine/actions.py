"""Actions and legal move generation."""
from typing import NamedTuple

from . import board as B
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


def path_ok(state, side, i, path, rules, occ=None):
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
        pts = (start,) + tuple(path)
        for j, xp in enumerate(state.x):
            if B.adjacent(xp, start) and (i, j) not in state.beaten:
                if B.path_crosses_ray(pts, xp, state.arrows[j], strict=rules.arrow_line_strict):
                    return False
    return True


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
    for d, path in paths:
        dest = path[-1]
        if dest in out:
            continue
        if path_ok(state, side, i, path, rules, occ):
            out[dest] = d
    return out


def can_move_kind(state, side, i, kind):
    """Limits and status for a movement kind (ignores geometry)."""
    rules = state.ctx.rules
    if state.tokens(side) <= 0:
        return False
    if side == 'O':
        if state.is_screening(i):
            return False
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
    return acts


# ---- intercept geometry ---------------------------------------------------------

def intercept_status(state, j):
    """'direct', 'approach' or None for defender j against the pending pass."""
    rules = state.ctx.rules
    passer, recv = state.pending
    a, b = state.o[passer], state.o[recv]
    p = state.x[j]
    on = B.on_segment(p, a, b, rules.on_line_tolerance)
    if B.adjacent(p, a):
        if state.arrows[j] == B.dir_between(p, a):
            return 'direct' if on else None
        return 'approach' if B.arrow_crosses(p, state.arrows[j], a, b) else None
    if on:
        return 'direct'
    if B.arrow_crosses(p, state.arrows[j], a, b):
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
            if i == ctx.inbounder and s.inbound:
                continue
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
            if B.adjacent(xp, cpos) and s.arrows[j] == B.dir_between(xp, cpos):
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
        if s.pending:
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
                if s.turn_n == 1 and can_icpt:
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
    """Is this defender movement an approach onto the pending pass line?"""
    if not (state.pending and a.side == 'X' and a.kind in MOVEMENT and state.turn_n == 0):
        return False
    if state.count('X', 'intercept') >= RC.LIMITS['X']['intercept']:
        return False
    if intercept_status(state, a.piece) != 'approach':
        return False
    passer, recv = state.pending
    return B.on_segment(a.dest, state.o[passer], state.o[recv], state.ctx.rules.on_line_tolerance)
