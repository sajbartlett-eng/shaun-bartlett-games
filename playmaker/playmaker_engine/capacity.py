"""Defender capacity (step 3i, C1): what a defender can still do this phase, from the engine's own
limits, and the three reaches that follow from it.

The fact the computer has to use: a defender who has spent his Move can only Quick Step, and a Quick
Step can't turn the arrow. A defender who followed a cut in is left facing the wrong way to answer the
pass back out.

  capacity(state, j)                 Move / Quick Step / Sprint left, locked, the pool's tokens, the side's
                                     Intercepts and Steals left, and whether the arrow can still turn
  lane_reach(state, j, passer, r)    can j answer a pass passer -> r: 'direct' (on the line), 'approach'
                                     (arrow across it, then one legal movement onto it), or None
  help_reach(state, j)               contest squares around the ball and the rim j can reach in a reaction
  closeout_reach(state, j, a=None, matchups=None)
                                     can j reach a clean contest on attacker a (default: the attacker he is
                                     guarding, from the matchup record when given, guarding.py, OQ-67a)
"""
from . import board as B
from . import rules_config as RC
from .actions import Action, can_move_kind, intercept_status, is_approach, movement_dests, zone


def reaction_budget(state):
    return min(2, state.tok_x) if state.tok_x > 0 else 0


def guarded(state, j, matchups=None):
    """The attacker defender j is guarding: from the matchup record (guarding.py) when there is one, else
    the nearest on the board (lower number on a tie)."""
    if matchups is not None:
        return matchups[j]
    on = [i for i in range(5) if B.on_board(state.o[i])]
    return min(on, key=lambda i: (B.cheb(state.x[j], state.o[i]), i)) if on else None


def capacity(state, j):
    rules = state.ctx.rules
    card = state.ctx.dfn[j]
    lim = RC.LIMITS['X']
    can_move = can_move_kind(state, 'X', j, 'move')
    can_qs = can_move_kind(state, 'X', j, 'qs') and card.qs > 0
    can_sprint = can_move_kind(state, 'X', j, 'sprint') and (card.qs > 0 or not rules.sprint_needs_qs)
    kinds = [k for k, ok in (('move', can_move), ('qs', can_qs), ('sprint', can_sprint)) if ok]
    return dict(defender=j, move_left=not state.moved('X', j), quick_step_left=not state.quick_stepped('X', j),
                side_qs_left=max(0, lim['qs'] - state.count('X', 'qs')), sprint=can_sprint,
                locked=state.locked('X', j), tokens=state.tok_x,
                intercepts_left=max(0, lim['intercept'] - state.count('X', 'intercept')),
                steals_left=max(0, lim['steal'] - state.count('X', 'steal')),
                can_turn=can_move,              # only a Move sets the arrow; a Quick Step keeps it
                movements=kinds,                # what he can still use to move at all
                reaction=reaction_budget(state),
                zone=zone(state, j))             # his zone of influence (actions.zone, the ruled definition)


def _pending(state, passer, receiver):
    return state.with_(ball=passer, pending=(passer, receiver), approach=-1, side='X', turn_n=0, stage='play')


def lane_reach(state, j, passer, receiver):
    """Can defender j answer a pass passer -> receiver in the defence's next turn (the pass ends the
    offence's turn and the defence answers before it lands)? 'direct', 'approach' or None."""
    p = _pending(state, passer, receiver)
    if p.tok_x <= 0 or p.count('X', 'intercept') >= RC.LIMITS['X']['intercept']:
        return None
    if p.ctx.rules.intercept_rule == 'move_then_intercept':
        # the refined ruling: 'direct' through his square, 'approach' one straight movement along his arrow
        # onto the line (then Intercept)
        from .actions import through_you, approach_moves
        if through_you(p, j):
            return 'direct'
        return 'approach' if p.tok_x >= 2 and approach_moves(p, j) else None
    if p.ctx.rules.intercept_rule == 'ring_jump':
        # OQ-72 ruling: 'direct' through his square, 'approach' a lane jump (now, or after a movement)
        from .actions import through_you, lane_jumps, follow_jumps
        if through_you(p, j):
            return 'direct'
        if lane_jumps(p, j) or any(m.piece == j for m, _ in follow_jumps(p)):
            return 'approach'
        return None
    st = intercept_status(p, j)
    if st == 'direct':
        return 'direct'
    if st != 'approach' or p.tok_x < 2:
        return None                            # an approach needs a token for the movement and one to intercept
    a, b = p.o[passer], p.o[receiver]
    tol = p.ctx.rules.on_line_tolerance
    for kind in ('move', 'qs', 'sprint'):
        if not can_move_kind(p, 'X', j, kind):
            continue
        for q in movement_dests(p, 'X', j, kind, p.ctx.rules):
            if not B.on_segment(q, a, b, tol):
                continue
            act = Action(kind, 'X', j, q, p.arrows[j]) if kind == 'move' else Action(kind, 'X', j, q)
            if is_approach(p, act):
                return 'approach'
    return None


def lane_answered(state, passer, receiver):
    """Is the lane passer -> receiver answered by the defence: denied outright (a defender next to the receiver on the
    line: receiver denial) or interceptable by some defender (lane_reach)?"""
    from .actions import denier
    if denier(state, passer, receiver) is not None:
        return True
    return any(lane_reach(state, j, passer, receiver) for j in range(5))


def lane_held(state, passer, receiver):
    """Is the lane passer -> receiver held against the offence's turn: answered now (lane_answered) and still answered
    after any one movement by the passer or the receiver (the offence moves before it passes: a new angle, or the
    receiver off the line)? state: the offence to act."""
    from .actions import legal_actions, MOVEMENT
    from .resolve import apply, ChanceNode
    if not lane_answered(state, passer, receiver):
        return False
    if state.stage != 'play' or state.side != 'O' or state.ball != passer:
        return True
    for a in legal_actions(state):
        if a.kind in MOVEMENT and a.piece in (passer, receiver):
            t = apply(state, a)
            if not isinstance(t, ChanceNode) and t.stage == 'play' and not lane_answered(t, t.ball, receiver):
                return False
    return True


def lanes(state, j):
    """The passes from the ball carrier that defender j can still answer: {receiver: 'direct'|'approach'}."""
    out = {}
    if not B.on_board(state.o[state.ball]):
        return out
    for r in range(5):
        if r != state.ball and B.on_board(state.o[r]):
            how = lane_reach(state, j, state.ball, r)
            if how:
                out[r] = how
    return out


def _reach(state, j):
    from .solver import defender_reach
    return defender_reach(state, j, reaction_budget(state))


def help_reach(state, j):
    """Contest squares around the ball carrier and around the rim that j can reach in a reaction, each
    with whether he arrives able to face the carrier (a Move sets the arrow; a Quick Step keeps it)."""
    free, fixed = _reach(state, j)
    cp = state.o[state.ball]
    rim = RC.RIM
    targets = set()
    for c in (cp, rim):
        if not B.on_board(c):
            continue
        for dx, dy in B.DIRS:
            q = (c[0] + dx, c[1] + dy)
            if B.on_board(q) and q not in state.o:
                targets.add(q)
    out = {}
    for q in targets:
        if q in free:
            out[q] = True
        elif q in fixed:
            out[q] = any(B.adjacent(q, cp) and B.dir_between(q, cp) == a for a in fixed[q])
    return out


def closeout_reach(state, j, attacker=None, matchups=None):
    """Can j reach a clean contest (adjacent and facing) on the attacker's best shot in a reaction?"""
    from .advantage import contests, looks
    a = guarded(state, j, matchups) if attacker is None else attacker
    if a is None or not B.on_board(state.o[a]):
        return False
    from .advantage import reach_maps
    maps = reach_maps(state)
    lk = looks(state, a, maps)
    if not lk:
        return False
    return any(c['defender'] == j and c['clean'] for c in lk[0][2])


def summary(state, j, matchups=None):
    """capacity plus the three reaches, for logging and tests."""
    c = capacity(state, j)
    c['lanes'] = lanes(state, j)
    c['help'] = sorted(B.sq(q) for q, facing in help_reach(state, j).items())
    c['closeout'] = closeout_reach(state, j, matchups=matchups)
    c['guarding'] = guarded(state, j, matchups)
    return c
