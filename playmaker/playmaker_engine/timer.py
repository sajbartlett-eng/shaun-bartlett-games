"""The decision timer's one engine event (step 3d part C), off by default.

timer_forfeit(state) is an ordinary state change, logged and replayed like any other. It is never in
the legal action set and never offered to the solver.

- In play or a reaction, with tokens left: the acting side loses 1 token from its pool; the turn goes on
  (if that was its last token, the turn ends, as it does when the last token is spent on an action).
- In play or a reaction, with the pool empty: the acting side's turn ends.
- A token-free decision (the contest choice, the forced shot type, the failed-inbound pick): the default
  applies (don't contest; the first legal shot type the zone allows; the first legal pick). No token is lost.
"""
from .actions import Action, legal_actions
from .resolve import apply, end_turn, end_phase, resolve_shot

TIMED_STAGES = ('play', 'reaction', 'contest', 'forced', 'pick')
TOKEN_FREE_STAGES = ('contest', 'forced', 'pick')


def token_free(state):
    return state.stage in TOKEN_FREE_STAGES


def timer_forfeit(state):
    """Returns (node, effect): node is a GameState or a ChanceNode. effect: 'token' (1 token lost, the turn goes
    on), 'token_end' (the last token lost, so the turn ends, exactly as spending it on an action would),
    'end_turn' (the pool was already empty) or 'default' (a token-free decision's default applied)."""
    s = state
    if s.stage not in TIMED_STAGES:
        raise ValueError(f'no timer in stage {s.stage}')
    if s.stage == 'contest':
        return apply(s, Action('contest', 'X', -1)), 'default'
    if s.stage in ('forced', 'pick'):
        kind = 'forced_shot' if s.stage == 'forced' else 'pick'
        first = next(a for a in legal_actions(s) if a.kind == kind)
        return apply(s, first), 'default'
    side = s.side
    if s.tokens(side) > 0:
        s = s.with_(tok_o=s.tok_o - 1) if side == 'O' else s.with_(tok_x=s.tok_x - 1)
        if s.tokens(side) > 0:
            return s, 'token'
        return _out_of_tokens(s, side), 'token_end'        # the last token: as after spending it on an action
    return _out_of_tokens(s, side), 'end_turn'


def _out_of_tokens(s, side):
    """The same ending the engine applies when a side's last token goes (resolve._after), without counting
    the forfeit as one of the turn's actions."""
    if s.stage == 'reaction':
        return resolve_shot(s)
    if side == 'X' and s.ctx.rules.defence_empty_ends_phase:
        return end_phase(s)
    return end_turn(s, side, 'timer')


def default_action(state):
    """The action a token-free default stands for (for the log and the feed)."""
    if state.stage == 'contest':
        return Action('contest', 'X', -1)
    kind = 'forced_shot' if state.stage == 'forced' else 'pick'
    return next(a for a in legal_actions(state) if a.kind == kind)


# Timer settings (step 3d C1/C3). The web session reads these; the engine itself never runs a clock.
TIMER_CONFIG = dict(
    settings=[None, 60, 45, 30],   # seconds per decision; None = off (the default)
    grace=15,                      # admin grace after selecting an action, to pick its square / target / direction
    regrace_after=5,               # a fresh grace needs this many seconds of main timer since the last selection
    warn_at=10,                    # the ring changes pattern (and the phone may vibrate) at this many seconds
)
