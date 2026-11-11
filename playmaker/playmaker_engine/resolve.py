"""apply(): the rules in motion. Randomness is never hidden: rolls come back as ChanceNodes."""
from dataclasses import dataclass, replace
from fractions import Fraction

from . import board as B
from . import rules_config as RC
from .actions import Action, intercept_status, is_approach, inbound_held, MOVEMENT, TOKEN_FREE
from .scoring import p_success, p_foul, choose_contest, shot_points, free_throws, contest_options, foul_on_shot_points, shot_rating
from .state import CI, ZERO_COUNTS, Result, count_key


@dataclass(frozen=True)
class ChanceNode:
    """outcomes: tuple of (probability, label, GameState or ChanceNode). Probabilities sum to 1.
    roller: the side rolling the d20 ('O' for opposed rolls, 'X' for the defender's foul rolls)."""
    outcomes: tuple
    what: str = ''
    roller: str = ''

    def flatten(self, prefix=''):
        out = []
        for p, label, node in self.outcomes:
            lab = f'{prefix}{label}'
            if isinstance(node, ChanceNode):
                for q, l2, s in node.flatten(lab + '/'):
                    out.append((p * q, l2, s))
            else:
                out.append((p, lab, node))
        return out

    def total(self):
        return sum(p for p, _, _ in self.flatten())


def chance(what, outcomes, roller=''):
    """Build a node, dropping impossible branches; a sure thing collapses to its state."""
    outs = tuple((Fraction(p), l, s) for p, l, s in outcomes if p > 0)
    if len(outs) == 1:
        return outs[0][2]
    return ChanceNode(outs, what, roller)


def cmap(node, fn):
    """Apply fn to every state leaf of a node (fn may itself return a ChanceNode)."""
    if isinstance(node, ChanceNode):
        return ChanceNode(tuple((p, l, cmap(s, fn)) for p, l, s in node.outcomes), node.what, node.roller)
    return fn(node)


def sample(node, rng):
    """Pick one outcome. Returns (state, label)."""
    labels = []
    while isinstance(node, ChanceNode):
        r = Fraction(rng.random())
        acc = Fraction(0)
        pick = node.outcomes[-1]
        for o in node.outcomes:
            acc += o[0]
            if r < acc:
                pick = o
                break
        labels.append(pick[1])
        node = pick[2]
    return node, '/'.join(labels)


def force(node, *labels):
    """Follow named outcomes (for tests and replays)."""
    for lab in labels:
        if not isinstance(node, ChanceNode):
            break
        for p, l, s in node.outcomes:
            if l == lab:
                node = s
                break
        else:
            raise KeyError(f'no outcome {lab!r} in {[l for _, l, _ in node.outcomes]}')
    return node


# ---- small state edits ---------------------------------------------------------

def _inc(s, side, kind):
    c = list(s.cnt)
    c[CI[count_key(side, kind)]] += 1
    return s.with_(cnt=tuple(c))


def _spend(s, side):
    return s.with_(tok_o=s.tok_o - 1) if side == 'O' else s.with_(tok_x=s.tok_x - 1)


def _lock(s, side, i):
    return s.with_(lock_o=s.lock_o | 1 << i) if side == 'O' else s.with_(lock_x=s.lock_x | 1 << i)


def _terminal(s, result, zeroed=False, units=1):
    """The possession is over. zeroed: a turnover that scores it 0 (units: the -5s that turnover added to s.tos);
    D-82 records what was banked before it, so it scores 0 or that, whichever is lower."""
    if zeroed and not s.zeroed:
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * (s.tos - units)
        result = replace(result, floor=min(0, banked))
    return s.with_(stage='over', side='-', result=result, zeroed=s.zeroed or zeroed, pending=None, shot=None)


def rules_ij(state):
    """The OQ-72 interception ruling is in force (a defence movement keeps the pass in the air)."""
    return state.ctx.rules.intercept_rule == 'ring_jump'


def _turnover(s):
    """A turnover that plays on (OQ-1), or ends the possession."""
    s = s.with_(tos=s.tos + 1)
    if s.ctx.hold_for_one or s.ctx.rules.digital:
        return _terminal(s, Result('turnover_end'), zeroed=True)
    if s.ctx.rules.turnover_play_on == 'end':
        return _terminal(s, Result('turnover_end'))
    return s


LOSE_PHASE = ('minus5_lose_phase', 'lose_phase')
COST_UNITS = {'minus5_lose_phase': 1, 'minus5': 1, 'minus10': 2, 'lose_phase': 0, 'end_possession': 1}


def pickoff(s):
    """What a successful Intercept or Steal costs (turnover_cost). s: the state after it, the ball already
    with the passer or carrier. Returns the state play goes on from, or a terminal state. The -5s are banked
    in s.tos (one per -5)."""
    cost = s.ctx.rules.turnover_cost
    if cost == 'legacy':
        return _turnover(s)
    s = s.with_(tos=s.tos + COST_UNITS[cost])
    units = COST_UNITS[cost]
    if s.ctx.hold_for_one or s.ctx.rules.digital:      # digital format: every turnover ends the possession at 0
        return _terminal(s, Result('turnover_end'), zeroed=True, units=units)
    if cost == 'end_possession':
        return _terminal(s, Result('turnover_end'))
    if cost in LOSE_PHASE:
        if s.clock <= RC.PHASE_SECONDS:             # the final phase: the possession ends and scores 0
            return _terminal(s, Result('turnover_end'), zeroed=True, units=units)
        s = s.with_(clock=s.clock - RC.PHASE_SECONDS)   # the phase goes on, tokens and actions as they were
    return s


def pickoff_value(pre, keep, tol=1.0, relative=False):
    """What a pick-off (a successful Intercept or Steal) is worth to the offence, for the computer's pricing.
    pre: the offence to act, before the pass. keep: what the ball carrier has where he is (his best look,
    relative to what is banked): with play-on, the ball stays with him. Under turnover_cost: -5 (x tol, the
    level's pass_risk_tolerance) and, with the clock cost, two seconds gone; in the final phase the whole
    possession is gone (0). relative: the value less what pre has banked."""
    banked = RC.STEAL_FOUL_BONUS * pre.bonus5 + RC.TURNOVER_POINTS * pre.tos
    rules = pre.ctx.rules
    cost = rules.turnover_cost
    zero = float(min(0, banked)) if rules.turnover_floor else 0.0     # D-82: 0, or what is banked if that is lower
    if pre.ctx.hold_for_one:
        v = zero
    elif rules.intercept_rule == 'ring_jump' or cost in ('legacy', 'end_possession'):
        v = banked + RC.TURNOVER_POINTS * tol           # the possession ends (or, legacy, valued as if it did)
    elif cost in LOSE_PHASE and pre.clock <= RC.PHASE_SECONDS:
        v = zero                                        # the final phase: the possession scores 0 (D-82: or less)
    else:
        v = banked + RC.TURNOVER_POINTS * COST_UNITS[cost] * tol + keep
    return v - banked if relative else v


def new_phase(s, clock):
    if s.ctx.rules.screen_rule == 'hold_until_move':
        s = s.with_(screens=())                  # OQ-29: a screen ends with the phase
    return s.with_(clock=clock, turn_lead=-1, turn_x=(), tok_o=RC.TOKENS_PER_PHASE, tok_x=RC.TOKENS_PER_PHASE, moved_o=0, moved_x=0,
                   cnt=ZERO_COUNTS, turn_n=0, final=False, lock_o=0, lock_x=0, approach=-1, prev_wait='',
                   beaten=(), side='O', phase=s.phase + 1, pending=None, turn_moved=0, qs_o=0, qs_x=0, react_moved=0,
                   rush_o=0, rush_x=0)


def complete_pass(s):
    passer, recv = s.pending
    s = s.with_(ball=recv, pending=None, approach=-1)
    if s.inbound and passer == s.ctx.inbounder:
        # The ball is in: reset to a new phase with the card's clock.
        s = new_phase(s.with_(inbound=0), s.ctx.card_clock)
    return s


def resolve_shot(s, forced=False):
    """The declared (or forced) shot reaches its contest. With contest_choice='player' this returns the
    decision node (the defence chooses who contests); otherwise the automatic contest is resolved."""
    shooter = s.ball
    spos = s.o[shooter]
    rules = s.ctx.rules
    if forced:
        if not B.on_board(spos) or B.zone(spos) == '.':
            return _terminal(s, Result('forced', shooter, '', 0))
        types = RC.ZONE_SHOTS[B.zone(spos)]
        if rules.forced_shot_choice == 'player' and len(types) > 1:
            return s.with_(stage='forced', side='O', shot=None, forced=True, turn_n=0, pending=None)
        if rules.forced_shot_choice == 'player':
            t = types[0]
        else:
            t = max(types, key=lambda t: (choose_contest(s, shooter, t, True).ev, -types.index(t)))
        s = s.with_(shot=t, forced=True)
    if rules.contest_action and not forced:
        # D-18: the reaction ended without a Contest (a Contest resolves the shot itself): a contest of 0
        return contest_outcome(s.with_(forced=False, pending=None), contest_options(s, shooter, s.shot, False)[0], False)
    if rules.contest_choice == 'player':
        return s.with_(stage='contest', side='X', turn_n=0, forced=forced, pending=None)
    return contest_outcome(s, choose_contest(s, shooter, s.shot, forced), forced)


def contest_outcome(s, opt, forced):
    """The result of one contest option: a terminal state, or a foul roll (arrow off the shooter)."""
    shooter = s.ball
    spos = s.o[shooter]
    card = s.ctx.off[shooter]
    t = s.shot
    pts = shot_points(spos)
    kind = 'forced' if forced else 'shot'
    rating = shot_rating(s, shooter, t)              # D-151: reduced when the shooter is rushed
    made = _terminal(s, Result(kind, shooter, t, pts, rating, opt.contest, opt.defender, opt.value, 0))
    if opt.clean or opt.p_foul == 0:
        return made
    _, and1 = foul_on_shot_points(card, t, pts, s.ctx.rules, rating)
    fouled = _terminal(s.with_(fouls=s.fouls + 1),
                       Result('free_throws', shooter, t, pts, rating, opt.contest, opt.defender, 0, opt.ft, and1))
    fr = s.ctx.dfn[opt.defender].r['foul_contest']
    why = 'arrow off the shooter' if s.ctx.rules.contest_geometry == 'current' else f'{opt.category} contest'
    if s.ctx.rules.control != 'off' and s.rushed('X', opt.defender):
        why = 'a late closeout after his Quick Step or Sprint'
    one = p_foul(fr, s.ctx.rules)
    if getattr(opt, 'rolls', 1) == 2:
        # step 3n F2: contesting from the side or behind (level with the shooter or further from the rim): two rolls
        second = chance(f'Contest foul {fr}, second roll (X{opt.defender + 1}, reaching from the side or behind)',
                        [(one, 'foul', fouled), (1 - one, 'no foul', made)], 'X')
        return chance(f'Contest foul {fr} (X{opt.defender + 1}, {why}; reaching from the side or behind: two foul rolls)',
                      [(one, 'foul', fouled), (1 - one, 'no foul', second)], 'X')
    return chance(f'Contest foul {fr} (X{opt.defender + 1}, {why})',
                  [(one, 'foul', fouled), (1 - one, 'no foul', made)], 'X')


def settle(node):
    """Resolve contest and forced-shot decisions the automatic way (defence's minimum, offence's best type).
    For analysis code written before those became player decisions; play itself never needs it."""
    if isinstance(node, ChanceNode):
        return ChanceNode(tuple((p, l, settle(sub)) for p, l, sub in node.outcomes), node.what, node.roller)
    if node.stage == 'contest':
        return settle(contest_outcome(node, choose_contest(node, node.ball, node.shot, node.forced), node.forced))
    if node.stage == 'forced':
        types = RC.ZONE_SHOTS[B.zone(node.o[node.ball])]
        t = max(types, key=lambda t: (choose_contest(node, node.ball, t, True).ev, -types.index(t)))
        return settle(apply(node, Action('forced_shot', 'O', node.ball, shot=t)))
    return node


def end_phase(s):
    if s.stage == 'over':
        return s
    if s.pending:
        phase = s.phase
        s = complete_pass(s)
        if s.phase != phase:              # an inbound pass landed: that already started a new phase
            return s
    if s.inbound:
        if s.inbound < RC.INBOUND_PHASES:
            return new_phase(s, s.clock).with_(inbound=s.inbound + 1)
        # Not in after two phases: turnover, -5, play on; ball to the player furthest from the rim.
        s = s.with_(tos=s.tos + 1)
        if s.ctx.hold_for_one:
            return _terminal(s, Result('turnover_end'), zeroed=True)
        ib = s.ctx.inbounder
        cands = [i for i in range(5) if i != ib and B.on_board(s.o[i])]
        far = max(B.dist_rim(s.o[i]) for i in cands)
        tied = [i for i in cands if B.dist_rim(s.o[i]) == far]
        s = new_phase(s.with_(inbound=0), s.ctx.card_clock)
        if len(tied) > 1 and s.ctx.rules.inbound_tie == 'offence':
            return s.with_(stage='pick')                 # the offence picks who gets the ball
        return s.with_(ball=tied[0])
    clock = s.clock - RC.PHASE_SECONDS
    if clock <= 0:
        s = s.with_(clock=0, tos=s.tos + 1, phase=s.phase)
        if s.ctx.hold_for_one or s.ctx.rules.digital:      # digital: shot-clock expiry is a turnover, scores 0
            return _terminal(s, Result('turnover_end'), zeroed=True)
        return resolve_shot(s, forced=True)
    return new_phase(s, clock)


def _age_screens(s):
    if s.ctx.rules.screen_rule == 'hold_until_move':
        return s                             # OQ-29: a screen holds until the screener moves
    keep = tuple((i, d, False, m) for i, d, f, m in s.screens if f)
    return s.with_(screens=keep)


def end_turn(s, side, kind=''):
    if s.stage == 'over':
        return s
    if s.stage == 'reaction':
        return resolve_shot(s)
    if side == 'O':
        s = _age_screens(s)
        s = s.with_(side='X', turn_n=0, prev_wait='H' if kind == 'hesitate' else '', final=s.tok_o == 0, turn_moved=0,
                    turn_lead=-1, turn_x=(s.x, s.arrows) if s.ctx.rules.intercept_return else ())
        if s.tok_x <= 0:
            return end_phase(s)
        return s
    phase = s.phase
    if s.pending:
        s = complete_pass(s)
        if s.phase != phase:
            return s
    s = s.with_(prev_wait='P' if kind == 'pause' else '', approach=-1)
    if s.final:
        return end_phase(s)
    return s.with_(side='O', turn_n=0, turn_lead=-1, turn_x=())


def _after(prev, s, side, kind):
    """Turn and phase bookkeeping after an action's effect."""
    if s.stage == 'over' or s.phase != prev.phase:
        return s
    if kind == 'end_turn':
        return end_turn(s, side, kind)
    if kind == 'forfeit':
        if side == 'X':
            if s.stage == 'reaction':
                return resolve_shot(s)
            return end_phase(s)
        return end_turn(s, side, kind)
    s = s.with_(turn_n=s.turn_n + 1)
    if s.stage == 'reaction':
        if kind in RC.TURN_ENDERS or s.turn_n >= RC.MAX_ACTIONS_PER_TURN or s.tok_x <= 0:
            return resolve_shot(s)
        return s
    if side == 'X' and s.tok_x <= 0 and s.ctx.rules.defence_empty_ends_phase:
        return end_phase(s)
    if kind in RC.TURN_ENDERS or s.turn_n >= RC.MAX_ACTIONS_PER_TURN or s.tokens(side) <= 0:
        return end_turn(s, side, kind)
    return s


# ---- the main entry point --------------------------------------------------------

def apply(state, action, check=False):
    """Apply an action. Returns a new GameState, or a ChanceNode listing every outcome."""
    if check:
        from .actions import legal_actions
        if action not in legal_actions(state):
            from .actions import why_illegal
            why = why_illegal(state, action)
            raise ValueError(f'illegal action {action}' + (f' ({why})' if why else '') + f' in {state.encode()}')
    s = state
    a = action
    side = a.side
    k = a.kind

    if k == 'target':
        return s.with_(target=a.target, stage='play')
    if k == 'pick':
        return s.with_(ball=a.target, stage='play')
    if k == 'forced_shot':
        s = s.with_(shot=a.shot, stage='play')
        if s.ctx.rules.contest_choice == 'player':
            return s.with_(stage='contest', side='X', forced=True)
        return contest_outcome(s, choose_contest(s, s.ball, a.shot, True), True)
    if k == 'contest':
        opts = {o.defender: o for o in contest_options(s, s.ball, s.shot, s.forced)}
        if a.piece not in opts:
            raise ValueError(f'X{a.piece + 1} cannot contest this shot')
        if s.stage == 'reaction':                 # D-18: a Contest is the reaction's last action and uses a token
            s = _spend(s, side).with_(turn_n=s.turn_n + 1)
        return contest_outcome(s, opts[a.piece], s.forced)

    if k not in TOKEN_FREE:
        s = _spend(s, side)
    if k == 'forfeit':
        s = s.with_(tok_o=0) if side == 'O' else s.with_(tok_x=0)
    if k == 'end_turn' or k == 'forfeit':
        return _after(state, s, side, k)

    # A pending pass lands at the start of the defence's turn unless this action answers it.
    if side == 'X' and s.pending and not inbound_held(state):
        answering = k == 'intercept' or (k in MOVEMENT and (is_approach(state, a) or rules_ij(state)))
        if not answering:
            phase = s.phase
            s = complete_pass(s)
            if s.phase != phase:          # an inbound pass landed: new phase, offence to act
                return s

    if k in MOVEMENT:
        if side == 'O':
            o = list(s.o)
            o[a.piece] = a.dest
            s = s.with_(o=tuple(o))
            if s.is_screening(a.piece):          # OQ-29: the screener's movement ends his screen
                s = s.with_(screens=tuple(x for x in s.screens if x[0] != a.piece))
            if (k == 'move' and state.turn_n == 0 and state.side == 'O' and state.stage == 'play'
                    and s.ctx.rules.screen_rule == 'hold_until_move'):
                s = s.with_(turn_lead=a.piece)   # he may Screen as the turn's second action
        else:
            x = list(s.x)
            x[a.piece] = a.dest
            arr = list(s.arrows)
            if k == 'move':
                arr[a.piece] = a.arrow
            elif k == 'sprint':
                start = state.x[a.piece]
                dx, dy = a.dest[0] - start[0], a.dest[1] - start[1]
                n = max(abs(dx), abs(dy))
                run = B.DIRS.index((dx // n, dy // n))
                # wedge (step 3h): the run direction is one edge; a.arrow = run - 1 puts the other edge
                # anticlockwise, otherwise it goes clockwise (arrow index = run)
                arr[a.piece] = a.arrow if (s.ctx.rules.arrow_mode == 'wedge' and a.arrow == (run - 1) % 8) else run
            s = s.with_(x=tuple(x), arrows=tuple(arr))
            if state.stage == 'reaction' and a.dest != state.x[a.piece]:
                s = s.with_(react_moved=s.react_moved | 1 << a.piece)     # late_closeout test: moved to contest
            if k in MOVEMENT and is_approach(state, a):
                s = s.with_(approach=a.piece)
            if state.pending:
                s = s.with_(turn_moved=s.turn_moved | 1 << a.piece)
        if k in ('move', 'sprint'):
            s = s.with_(moved_o=s.moved_o | 1 << a.piece) if side == 'O' else s.with_(moved_x=s.moved_x | 1 << a.piece)
        if k in ('qs', 'sprint'):
            s = _inc(s, side, 'qs')
            s = s.with_(qs_o=s.qs_o | 1 << a.piece) if side == 'O' else s.with_(qs_x=s.qs_x | 1 << a.piece)
        if s.ctx.rules.control != 'off':
            # D-151: a Quick Step or a Sprint leaves him rushed; a Move restores control
            bit = 1 << a.piece
            if side == 'O':
                s = s.with_(rush_o=(s.rush_o & ~bit) if k == 'move' else (s.rush_o | bit))
            else:
                s = s.with_(rush_x=(s.rush_x & ~bit) if k == 'move' else (s.rush_x | bit))
        return _after(state, s, side, k)

    s = _inc(s, side, k)
    rules = s.ctx.rules
    O, X = s.ctx.off, s.ctx.dfn

    if k == 'pass':
        s = s.with_(pending=(a.piece, a.target), approach=-1)
        if rules.pass_resolution == 'immediate':
            if not any(intercept_status(s, j) == 'direct' for j in range(5)):
                phase = s.phase
                s = complete_pass(s)
                if s.phase != phase:
                    return s
        return _after(state, s, side, k)

    if k == 'screen':
        s = s.with_(screens=tuple(sorted(s.screens + ((a.piece, a.target, True, 0),))))
        return _after(state, s, side, k)

    if k == 'hesitate' or k == 'pause':
        return _after(state, s, side, k)

    if k == 'shot':
        s = s.with_(stage='reaction', shot=a.shot, side='X', turn_n=0)
        if s.tok_x <= 0:
            return resolve_shot(s)
        return s

    if k == 'dribble':
        p = p_success(O[s.ball].r['dribble'] - X[a.target].r['agility'], rules)
        win = _lock(s, 'X', a.target).with_(beaten=tuple(sorted(set(s.beaten) | {(s.ball, a.target)})))
        lose = _lock(s, 'O', s.ball)
        return chance(f'Dribble {O[s.ball].r["dribble"]} v Agility {X[a.target].r["agility"]} (O{s.ball + 1} v X{a.target + 1})', [
            (p, 'success', _after(state, win, side, k)),
            (1 - p, 'failure', _after(state, lose, side, k))], 'O')

    if k == 'intercept' and rules.intercept_rule == 'ring_jump':
        # OQ-72 ruling: a lane jump moves him straight along his arrow to the crossing square (facing kept),
        # spending the Move or Quick Step it uses; through his square, he stays put
        passer, recv = s.pending
        j = a.piece
        if a.dest is not None:
            x = list(s.x)
            x[j] = a.dest
            s = s.with_(x=tuple(x))
            if a.target == 0:
                s = s.with_(moved_x=s.moved_x | 1 << j)
            else:
                cnt = list(s.cnt)
                cnt[CI['x_qs']] += 1
                s = s.with_(qs_x=s.qs_x | 1 << j, cnt=tuple(cnt))
            if rules.control != 'off':                       # D-151: the jump into the lane counts as his movement
                s = s.with_(rush_x=(s.rush_x & ~(1 << j)) if a.target == 0 else (s.rush_x | 1 << j))
        p = p_success(O[passer].r['pass'] - X[j].r['intercept'], rules)
        ok = complete_pass(s.with_(moved_x=s.moved_x | 1 << j))      # missed: out of position, Move used
        ok_node = ok if ok.phase != s.phase else _after(state, ok, side, k)
        won = s.with_(pending=None, approach=-1, tos=s.tos + 1)
        lost_node = (_terminal(won, Result('turnover_end'), zeroed=True) if s.ctx.hold_for_one or rules.digital
                     else _terminal(won, Result('turnover_end')))   # the possession ends at -5
        return chance(f'Pass {O[passer].r["pass"]} v Intercept {X[j].r["intercept"]} (O{passer + 1} to O{recv + 1}, X{j + 1})', [
            (p, 'success', ok_node), (1 - p, 'failure', lost_node)], 'O')

    if k == 'intercept':
        passer, recv = s.pending
        j = a.piece
        mti = rules.intercept_rule == 'move_then_intercept'
        p = p_success(O[passer].r['pass'] - X[j].r['intercept'], rules)
        ok = complete_pass(s.with_(moved_x=s.moved_x | 1 << j) if mti else s)   # missed: on the line, Move used
        if ok.phase != s.phase:
            ok_node = ok                                   # inbound pass landed: new phase
        else:
            ok_node = _after(state, ok, side, k)
        back = s
        if s.ctx.rules.intercept_return and state.turn_x:  # ruled: a successful interceptor goes back to where he
            sx, sa = state.turn_x                          # stood at the start of the defence's turn (Move still used)
            back = s.with_(x=s.x[:j] + (sx[j],) + s.x[j + 1:], arrows=s.arrows[:j] + (sa[j],) + s.arrows[j + 1:])
        if mti:
            lost = pickoff(back.with_(pending=None, approach=-1, moved_x=back.moved_x | 1 << j))   # ball with the passer
        else:
            lost = _turnover(back.with_(pending=None, approach=-1))   # ball stays with the passer
        lost_node = lost if lost.stage == 'over' else _after(state, lost, side, k)
        return chance(f'Pass {O[passer].r["pass"]} v Intercept {X[j].r["intercept"]} (O{passer + 1} to O{recv + 1}, X{j + 1})', [
            (p, 'success', ok_node), (1 - p, 'failure', lost_node)], 'O')

    if k == 'challenge':
        scr = s.screen_of(a.target)
        p = p_success(O[a.target].r['screen'] - X[a.piece].r['challenge'], rules)
        holds = _lock(s, 'X', a.piece)
        if rules.screen_rule == 'hold_until_move':   # OQ-29: a Challenge that wins removes the screen for everyone
            fails = s.with_(screens=tuple(x for x in s.screens if x[0] != a.target))
        else:
            fails = s.with_(screens=tuple((i, d, f, m | (1 << a.piece) if i == a.target else m) for i, d, f, m in s.screens))
        return chance(f'Screen {O[a.target].r["screen"]} v Challenge {X[a.piece].r["challenge"]} (O{a.target + 1}, X{a.piece + 1})', [
            (p, 'success', _after(state, holds, side, k)),
            (1 - p, 'failure', _after(state, fails, side, k))], 'O')

    if k == 'steal':
        carrier = s.ball
        pf = p_foul(X[a.piece].r['foul_steal'], rules)
        pk = p_success(O[carrier].r['dribble'] - X[a.piece].r['steal'], rules)
        fs = s.with_(fouls=s.fouls + 1)                  # a team foul in the app, a shooting foul included
        if rules.steal_foul_always_plus5 and s.stage != 'reaction':
            fs = fs.with_(bonus5=fs.bonus5 + 1)          # D-89: every steal foul is +5, in the bonus too; a steal foul on
        legacy = rules.turnover_cost == 'legacy'         # a shooter is a shooting foul: free throws only (step 7)
        if s.stage == 'reaction':
            pts = shot_points(s.o[carrier])
            card = O[carrier]
            rating = shot_rating(s, carrier, s.shot)     # D-151
            fpts, and1 = foul_on_shot_points(card, s.shot, pts, rules, rating)
            foul_node = _terminal(fs, Result('free_throws', carrier, s.shot, pts, rating, 0, a.piece, 0,
                                              fpts, and1))
            if legacy or rules.digital:
                stolen_node = _terminal(s.with_(tos=s.tos + 1), Result('steal', carrier, s.shot, pts),
                                        zeroed=s.ctx.hold_for_one or rules.digital)
            else:
                # ruled: a stolen shot is cancelled (it doesn't use the phase's shot) and play goes on
                cnt = list(s.cnt)
                cnt[CI['shot']] = max(0, cnt[CI['shot']] - 1)
                st = pickoff(s.with_(stage='play', shot=None, cnt=tuple(cnt)))
                stolen_node = st if st.stage == 'over' else _after(state.with_(stage='play'), st, side, k)
        else:
            # the bonus: tabletop, the second steal foul of the possession; digital (step 3n F3), the bonus_from-th
            # team foul of the quarter (the defence's fouls before this possession travel in the context)
            in_bonus = (s.ctx.team_fouls + fs.fouls >= rules.bonus_from) if rules.digital else fs.fouls >= 2
            if in_bonus:
                foul_node = _terminal(fs, Result('free_throws', carrier, '', 2, 0, 0, a.piece, 0,
                                                 free_throws(O[carrier], 2)))
            else:
                foul_node = _after(state, fs if rules.steal_foul_always_plus5 else fs.with_(bonus5=fs.bonus5 + 1), side, k)
            st = _turnover(s) if legacy else pickoff(s)
            stolen_node = st if st.stage == 'over' else _after(state, st, side, k)
        # step 3n F1: a failed Steal (no foul, the ball kept) locks the defender, as a failed Challenge does
        kept_node = _after(state, _lock(s, 'X', a.piece) if rules.steal_lock else s, side, k)
        inner = chance(f'Dribble {O[carrier].r["dribble"]} v Steal {X[a.piece].r["steal"]} (O{carrier + 1} v X{a.piece + 1})',
                       [(pk, 'kept', kept_node), (1 - pk, 'stolen', stolen_node)], 'O')
        from .scoring import foul_rolls
        if foul_rolls(rules, s.x[a.piece], s.o[carrier]) == 2:
            # step 3n F2: reaching level with the ball carrier or from behind: two foul rolls, either fouls
            second = chance(f'Steal foul {X[a.piece].r["foul_steal"]}, second roll (X{a.piece + 1}, reaching from the side or behind)',
                            [(pf, 'foul', foul_node), (1 - pf, 'no foul', inner)], 'X')
            return chance(f'Steal foul {X[a.piece].r["foul_steal"]} (X{a.piece + 1}; reaching from the side or behind: two foul rolls)',
                          [(pf, 'foul', foul_node), (1 - pf, 'no foul', second)], 'X')
        return chance(f'Steal foul {X[a.piece].r["foul_steal"]} (X{a.piece + 1})',
                      [(pf, 'foul', foul_node), (1 - pf, 'no foul', inner)], 'X')

    raise ValueError(f'unknown action {a}')
