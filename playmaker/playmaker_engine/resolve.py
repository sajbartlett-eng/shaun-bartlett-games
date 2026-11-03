"""apply(): the rules in motion. Randomness is never hidden: rolls come back as ChanceNodes."""
from dataclasses import dataclass
from fractions import Fraction

from . import board as B
from . import rules_config as RC
from .actions import Action, intercept_status, is_approach, MOVEMENT, TOKEN_FREE
from .scoring import p_success, p_foul, choose_contest, shot_points, free_throws, contest_options, foul_on_shot_points
from .state import CI, ZERO_COUNTS, Result, count_key


@dataclass(frozen=True)
class ChanceNode:
    """outcomes: tuple of (probability, label, GameState or ChanceNode). Probabilities sum to 1."""
    outcomes: tuple
    what: str = ''

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


def chance(what, outcomes):
    """Build a node, dropping impossible branches; a sure thing collapses to its state."""
    outs = tuple((Fraction(p), l, s) for p, l, s in outcomes if p > 0)
    if len(outs) == 1:
        return outs[0][2]
    return ChanceNode(outs, what)


def cmap(node, fn):
    """Apply fn to every state leaf of a node (fn may itself return a ChanceNode)."""
    if isinstance(node, ChanceNode):
        return ChanceNode(tuple((p, l, cmap(s, fn)) for p, l, s in node.outcomes), node.what)
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


def _terminal(s, result, zeroed=False):
    return s.with_(stage='over', side='-', result=result, zeroed=s.zeroed or zeroed, pending=None, shot=None)


def _turnover(s):
    """A turnover that plays on (OQ-1), or ends the possession."""
    s = s.with_(tos=s.tos + 1)
    if s.ctx.hold_for_one:
        return _terminal(s, Result('turnover_end'), zeroed=True)
    if s.ctx.rules.turnover_play_on == 'end':
        return _terminal(s, Result('turnover_end'))
    return s


def new_phase(s, clock):
    return s.with_(clock=clock, tok_o=RC.TOKENS_PER_PHASE, tok_x=RC.TOKENS_PER_PHASE, moved_o=0, moved_x=0,
                   cnt=ZERO_COUNTS, turn_n=0, final=False, lock_o=0, lock_x=0, approach=-1, prev_wait='',
                   beaten=(), side='O', phase=s.phase + 1, pending=None)


def complete_pass(s):
    passer, recv = s.pending
    s = s.with_(ball=recv, pending=None, approach=-1)
    if s.inbound and passer == s.ctx.inbounder:
        # The ball is in: reset to a new phase with the card's clock.
        s = new_phase(s.with_(inbound=0), s.ctx.card_clock)
    return s


def resolve_shot(s, forced=False):
    """Automatic contest for the declared (or forced) shot. Returns a terminal state or ChanceNode."""
    shooter = s.ball
    spos = s.o[shooter]
    card = s.ctx.off[shooter]
    if forced:
        if not B.on_board(spos) or B.zone(spos) == '.':
            return _terminal(s, Result('forced', shooter, '', 0))
        types = RC.ZONE_SHOTS[B.zone(spos)]
        t = max(types, key=lambda t: (choose_contest(s, shooter, t, True).ev, -types.index(t)))
    else:
        t = s.shot
    opt = choose_contest(s, shooter, t, forced)
    pts = shot_points(spos)
    kind = 'forced' if forced else 'shot'
    made = _terminal(s, Result(kind, shooter, t, pts, card.shot(t), opt.contest, opt.defender, opt.value, 0))
    if opt.clean or opt.p_foul == 0:
        return made
    _, and1 = foul_on_shot_points(card, t, pts, s.ctx.rules)
    fouled = _terminal(s, Result('free_throws', shooter, t, pts, card.shot(t), opt.contest, opt.defender, 0, opt.ft, and1))
    return chance(f'contest foul roll X{opt.defender + 1}', [(opt.p_foul, 'foul', fouled), (1 - opt.p_foul, 'no foul', made)])


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
        if s.ctx.hold_for_one:
            return _terminal(s, Result('turnover_end'), zeroed=True)
        return resolve_shot(s, forced=True)
    return new_phase(s, clock)


def _age_screens(s):
    keep = tuple((i, d, False, m) for i, d, f, m in s.screens if f)
    return s.with_(screens=keep)


def end_turn(s, side, kind=''):
    if s.stage == 'over':
        return s
    if s.stage == 'reaction':
        return resolve_shot(s)
    if side == 'O':
        s = _age_screens(s)
        s = s.with_(side='X', turn_n=0, prev_wait='H' if kind == 'hesitate' else '', final=s.tok_o == 0)
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
    return s.with_(side='O', turn_n=0)


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
            raise ValueError(f'illegal action {action} in {state.encode()}')
    s = state
    a = action
    side = a.side
    k = a.kind

    if k == 'target':
        return s.with_(target=a.target, stage='play')
    if k == 'pick':
        return s.with_(ball=a.target, stage='play')

    if k not in TOKEN_FREE:
        s = _spend(s, side)
    if k == 'forfeit':
        s = s.with_(tok_o=0) if side == 'O' else s.with_(tok_x=0)
    if k == 'end_turn' or k == 'forfeit':
        return _after(state, s, side, k)

    # A pending pass lands at the start of the defence's turn unless this action answers it.
    if side == 'X' and s.pending:
        answering = k == 'intercept' or (k in MOVEMENT and is_approach(state, a))
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
                arr[a.piece] = B.DIRS.index((dx // n, dy // n))
            s = s.with_(x=tuple(x), arrows=tuple(arr))
            if k in MOVEMENT and is_approach(state, a):
                s = s.with_(approach=a.piece)
        if k in ('move', 'sprint'):
            s = s.with_(moved_o=s.moved_o | 1 << a.piece) if side == 'O' else s.with_(moved_x=s.moved_x | 1 << a.piece)
        if k in ('qs', 'sprint'):
            s = _inc(s, side, 'qs')
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
        return chance(f'Dribble O{s.ball + 1} vs X{a.target + 1}', [
            (p, 'success', _after(state, win, side, k)),
            (1 - p, 'failure', _after(state, lose, side, k))])

    if k == 'intercept':
        passer, recv = s.pending
        p = p_success(O[passer].r['pass'] - X[a.piece].r['intercept'], rules)
        ok = complete_pass(s)
        if ok.phase != s.phase:
            ok_node = ok                                   # inbound pass landed: new phase
        else:
            ok_node = _after(state, ok, side, k)
        lost = _turnover(s.with_(pending=None, approach=-1))   # ball stays with the passer
        lost_node = lost if lost.stage == 'over' else _after(state, lost, side, k)
        return chance(f'Pass O{passer + 1}->O{recv + 1} vs Intercept X{a.piece + 1}', [
            (p, 'success', ok_node), (1 - p, 'failure', lost_node)])

    if k == 'challenge':
        scr = s.screen_of(a.target)
        p = p_success(O[a.target].r['screen'] - X[a.piece].r['challenge'], rules)
        holds = _lock(s, 'X', a.piece)
        fails = s.with_(screens=tuple((i, d, f, m | (1 << a.piece) if i == a.target else m) for i, d, f, m in s.screens))
        return chance(f'Screen O{a.target + 1} vs Challenge X{a.piece + 1}', [
            (p, 'success', _after(state, holds, side, k)),
            (1 - p, 'failure', _after(state, fails, side, k))])

    if k == 'steal':
        carrier = s.ball
        pf = p_foul(X[a.piece].r['foul_steal'], rules)
        pk = p_success(O[carrier].r['dribble'] - X[a.piece].r['steal'], rules)
        fs = s.with_(fouls=s.fouls + 1)
        if s.stage == 'reaction':
            pts = shot_points(s.o[carrier])
            card = O[carrier]
            fpts, and1 = foul_on_shot_points(card, s.shot, pts, rules)
            foul_node = _terminal(fs, Result('free_throws', carrier, s.shot, pts, card.shot(s.shot), 0, a.piece, 0,
                                              fpts, and1))
            stolen_node = _terminal(s.with_(tos=s.tos + 1), Result('steal', carrier, s.shot, pts),
                                    zeroed=s.ctx.hold_for_one)
        else:
            if fs.fouls >= 2:
                foul_node = _terminal(fs, Result('free_throws', carrier, '', 2, 0, 0, a.piece, 0,
                                                 free_throws(O[carrier], 2)))
            else:
                foul_node = _after(state, fs.with_(bonus5=fs.bonus5 + 1), side, k)
            st = _turnover(s)
            stolen_node = st if st.stage == 'over' else _after(state, st, side, k)
        kept_node = _after(state, s, side, k)
        inner = chance(f'Steal: Dribble O{carrier + 1} vs Steal X{a.piece + 1}',
                       [(pk, 'kept', kept_node), (1 - pk, 'stolen', stolen_node)])
        return chance(f'Steal foul roll X{a.piece + 1}', [(pf, 'foul', foul_node), (1 - pf, 'no foul', inner)])

    raise ValueError(f'unknown action {a}')
