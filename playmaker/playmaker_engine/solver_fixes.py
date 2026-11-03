"""Suggested card fixes: setup changes only (squares, arrows, clock, teams). Never a rule change.

Each fix is a function from the card's starting GameState to a new starting state; the solver
re-solves the card with it to check the verdict becomes Puzzle.
"""
from . import board as B
from .cards import TEAMS
from .state import Context


def _face(st, d, man):
    arr = list(st.arrows)
    arr[d] = B.nearest_dir(st.x[d], st.o[man])
    return arr


def swap_x(a, b):
    """Swap defenders a and b (1-based) on the card, each facing its new man."""
    def fix(st):
        x = list(st.x)
        x[a - 1], x[b - 1] = x[b - 1], x[a - 1]
        st = st.with_(x=tuple(x))
        arr = list(st.arrows)
        for d in (a - 1, b - 1):
            man = min(range(5), key=lambda o: B.cheb(st.o[o], st.x[d]))
            arr[d] = B.nearest_dir(st.x[d], st.o[man])
        return st.with_(arrows=tuple(arr))
    return fix


def move_x(d, square, face):
    """Defender d (1-based) starts on `square`, arrow on O`face`."""
    def fix(st):
        x = list(st.x)
        x[d - 1] = B.parse_sq(square)
        st = st.with_(x=tuple(x))
        arr = list(st.arrows)
        arr[d - 1] = B.nearest_dir(st.x[d - 1], st.o[face - 1])
        return st.with_(arrows=tuple(arr))
    return fix


def move_o(i, square):
    def fix(st):
        o = list(st.o)
        o[i - 1] = B.parse_sq(square)
        return st.with_(o=tuple(o))
    return fix


def clock(c):
    def fix(st):
        ctx = st.ctx
        new = Context(ctx.off, ctx.dfn, ctx.rules, ctx.title, ctx.kind, ctx.scenario, c, ctx.inbounder, ctx.coach_call,
                      ctx.three_only, ctx.two_or_three, ctx.hold_for_one, ctx.off_team, ctx.def_team)
        return st.with_(ctx=new, clock=st.clock if st.inbound else c)
    return fix


def defence_team(name):
    def fix(st):
        ctx = st.ctx
        new = Context(ctx.off, TEAMS[name], ctx.rules, ctx.title, ctx.kind, ctx.scenario, ctx.card_clock, ctx.inbounder,
                      ctx.coach_call, ctx.three_only, ctx.two_or_three, ctx.hold_for_one, ctx.off_team, name)
        return st.with_(ctx=new)
    return fix


def teams(off, dfn):
    """Play the card with another prescribed matchup (same squares and clock)."""
    def fix(st):
        ctx = st.ctx
        new = Context(TEAMS[off], TEAMS[dfn], ctx.rules, ctx.title, ctx.kind, ctx.scenario, ctx.card_clock,
                      ctx.inbounder, ctx.coach_call, ctx.three_only, ctx.two_or_three, ctx.hold_for_one, off, dfn)
        return st.with_(ctx=new)
    return fix


def both(*fixes):
    def fix(st):
        for f in fixes:
            st = f(st)
        return st
    return fix


# Candidates tried per card (filled in from the solver runs); FIXES holds the chosen one.
CANDIDATES = {
    6: [('Swap X2 and X3: the Defensive SF (contest 6 on threes) takes O2, the sharpshooter; X2 (contest 3) takes O3.',
         swap_x(2, 3)),
        ('Swap X1 and X2: the Defensive PG (contest 5 on threes) starts on O2 at D9; X2 takes the ball at I10.',
         swap_x(1, 2))],
    7: [('Swap X3 and X4: the Post Scorer PF (contest 5 on threes) starts on O3 at P8, X3 (contest 2) on O4 at F9.',
         swap_x(3, 4))],
    15: [('Swap X4 and X5: the Post Scorer PF (contest 6 on posts) starts on O5 at H3, X5 on O4.',
          swap_x(4, 5)),
         ('X5 fronts the post: starts on G4 (between O5 and the ball) instead of H3.', move_x(5, 'G4', 5))],
    8: [('X4 starts behind O4, on G2 instead of G3: a seal for the post looks, contested from the far side.',
         move_x(4, 'G2', 4)),
        ('Swap X1 and X5: the switch leaves a guard (Combo Guard B, post contest 3) on O5 and the Rim Runner on O1.',
         swap_x(1, 5)),
        ('Defence team Pace and Space -> Bucket Brigade (weaker interior defence).', defence_team('Bucket Brigade'))],
    1: [('X1 starts on F6, outside O1 (G6), instead of H5 in the lane: the perimeter cut is taken away.',
         move_x(1, 'F6', 1)),
        ('X1 starts on F5 (below and outside O1) instead of H5.', move_x(1, 'F5', 1)),
        ('X1 starts on F6 and X2 on L7: both wing defenders outside their men, cutting the path to the arc.',
         both(move_x(1, 'F6', 1), move_x(2, 'L7', 2)))],
    16: [('Clock 6 -> 8: one more phase gives the locked star a second way in.', clock(8)),
         ('X2 plays O2 straight up on D9 (arrow on him) instead of denying from D8.', move_x(2, 'D9', 2))],
}
FIXES = {}
