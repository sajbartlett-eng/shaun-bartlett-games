"""Step 31: the fundamentals exam's boards (docs/reports/STEP31_PLAN.md, section 6, as Shaun approved them, D-292).
One place for every board: the exam (tests/test_exam.py), the tools and the report all read these. A board is a
GameState; a board the defence or the offence sets up itself is a GameState too (the other side placed, the side that
sets up on stand-in squares) with `.setup` naming who sets up."""
import math

from playmaker_engine import board as B, levels as L, rules_config as RC
from playmaker_engine.scenarios import TEAMS
from playmaker_engine.state import Context, GameState

FOULS = dict(team_fouls=0, quarter_left=0)

# built teams (each one card a position, so a legal roster); printed teams come from TEAMS by name
BUILT = {
    'Poor five': ['apgC', 'pmsC', 'dfsfC', 'dpfC', 'rpcC'],
    'One shooter': ['apgC', 'shsA', 'dfsfC', 'dpfC', 'rpcC'],
    'Five Out, big centre': ['ppgC', 'shsA', 'twsfB', 'stpfA', 'rpcC'],
    'Speed': ['cgA', 'bgsA', 'slsfA', 'stpfA', 'stcC'],
    'Speed, wings swapped': ['cgA', 'slsfA', 'bgsA', 'stpfA', 'stcC'],
    'Two equal': ['ppgC', 'tndA', 'stsfA', 'dpfC', 'rpcC'],
    'Best in corner': ['ppgC', 'stsfA', 'shsA', 'dpfC', 'rpcC'],
    'Five Out, weak two': ['ppgC', 'pmsC', 'twsfB', 'stpfA', 'stcC'],
}
SPREAD = ['I11', 'C9', 'O9', 'A3', 'Q3']
SPREAD_X = ['I10', 'D8', 'N8', 'B4', 'P4']


def cards(name):
    if name in TEAMS:
        return TEAMS[name]
    keys = BUILT[name]
    return L.team([(k, i + 1) for i, k in enumerate(keys)], 'senior')


def facing(xq, oq):
    """The arrow pair whose first arrow points most nearly from xq at oq."""
    dx, dy = oq[0] - xq[0], oq[1] - xq[1]
    if dx == 0 and dy == 0:
        return 4
    ang = math.atan2(dx, dy)                       # 0 is north (up the court), clockwise
    return int(round(ang / (math.pi / 4))) % 8


def board(off, dfn, o, x=None, ball=0, clock=12, arrows=None, level=('senior', 'pro'), rules=None, ctx_kw=None, **kw):
    x = x or SPREAD_X
    rules = rules or RC.with_rules(digital=True, zone='on')
    ctx = Context(cards(off), cards(dfn), rules, title=f'{off} v {dfn}', kind='GAME', off_team=off, def_team=dfn,
                  **dict(FOULS, **(ctx_kw or {})))
    ctx.levels_key = level
    os_, xs = tuple(B.parse_sq(q) for q in o), tuple(B.parse_sq(q) for q in x)
    if arrows is None:
        arr = tuple(facing(xs[i], os_[i]) for i in range(5))
    else:
        arr = tuple(B.DIR_NAMES.index(a) if isinstance(a, str) else a for a in arrows)
    s = GameState(ctx=ctx, o=os_, x=xs, arrows=arr, ball=ball, clock=clock)
    return s.with_(**kw) if kw else s


def _e25():
    """A screened defender: O5 screens X1 from J8 (the board is made by playing that Screen)."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    s = board('High-Low', 'Iron Wall', ['I10', 'C9', 'O9', 'A3', 'J8'], ['I9', 'D8', 'N8', 'B4', 'J7'], clock=10)
    scr = [a for a in legal_actions(s) if a.kind == 'screen' and a.piece == 4]
    return s, scr



P_O = SPREAD


# the stance search's base positions (x, arrows) for each P offence (only='stance_base'); the ball's defender is replaced
P_BASE = {
    'P1': (['I6', 'D8', 'K4', 'D3', 'J2'], [0, 7, 1, 6, 2]),
    'P2': (['I4', 'D8', 'M7', 'B3', 'J2'], [0, 7, 1, 6, 2]),
    'P3': (['I6', 'E7', 'I2', 'D3', 'O3'], [0, 7, 1, 6, 2]),
    'P4': (['I9', 'E7', 'L6', 'E3', 'J2'], [0, 7, 1, 6, 2]),
}


def _p(ball_sq, ball, x_sq, arrow, base):
    """A P board: the ball handler (piece `ball`) on ball_sq, his defender on x_sq with his first arrow `arrow`, the
    other four on the base positions."""
    o = list(P_O)
    o[ball] = ball_sq
    xs, arr = list(base[0]), list(base[1])
    xs[ball] = x_sq
    arr[ball] = B.DIR_NAMES.index(arrow)
    return board('Race five', 'Iron Wall', o, xs, ball=ball, arrows=arr)

BOARDS = {
    # ---- the defence -------------------------------------------------------------------------------------------------
    'E1': lambda: board('Poor five', 'Iron Wall', SPREAD),
    'E2': lambda: board('One shooter', 'Iron Wall', SPREAD),
    'E3': lambda: board('Five Out', 'Iron Wall', SPREAD),
    'E3b': lambda: board('Five Out, weak two', 'Iron Wall', SPREAD),                 # G2: O2 a non-shooter
    'E4': lambda: board('Five Out', 'Iron Wall', ['I11', 'L6', 'C9', 'A3', 'Q3'], ['I10', 'I4', 'D8', 'B4', 'P4'], ball=1, clock=10, side='X'),
    'E5': lambda: board('Five Out, big centre', 'Iron Wall', ['C9', 'A3', 'I11', 'O9', 'Q3'], ['D8', 'B4', 'I10', 'N8', 'P4']),
    'E5b': lambda: board('Five Out', 'Iron Wall', ['C9', 'Q3', 'I11', 'O9', 'A3'], ['D8', 'P4', 'I10', 'N8', 'B4']),   # the Sharpshooter in that corner
    'E6': lambda: board('Five Out', 'Iron Wall', SPREAD, ['I10', 'G5', 'N8', 'B4', 'P4'], ball=1, clock=10, side='X'),
    'E7': lambda: board('Five Out', 'Iron Wall', ['I11', 'C11', 'O9', 'A3', 'Q3']),
    'E7j': lambda: board('Five Out', 'Iron Wall', ['I11', 'C11', 'O9', 'A3', 'Q3'], level=('junior', 'pro')),
    'E8': lambda: board('Five Out', 'Iron Wall', SPREAD, clock=2, ctx_kw=dict(three_only=True)),
    'E9': lambda: board('Poor five', 'Iron Wall', ['M6', 'Q8', 'Q2', 'C9', 'K2'], ['N5', 'Q7', 'P3', 'E8', 'L2'], ball=2, clock=8, side='X',
                        grd=2),                                                       # his dribble dead (he has picked the ball up)
    'E10': lambda: board('Ball Movement', 'Iron Wall', SPREAD, clock=10, side='X'),
    'E11': lambda: board('Speed', 'Iron Wall', ['J5', 'Q4', 'O9', 'C9', 'G3'], ['J8', 'M4', 'N7', 'D8', 'H3'], clock=10, side='X',
                         beaten=((0, 0),)),
    'E12': lambda: board('Twin Towers', 'Iron Wall', ['I11', 'C9', 'O9', 'G3', 'K3'], ['I10', 'D8', 'N8', 'G4', 'K4']),
    # ---- the offence -------------------------------------------------------------------------------------------------
    'E13': lambda: board('High-Low', 'Iron Wall', ['I11', 'C9', 'O9', 'J3', 'A3'], ['I10', 'D8', 'N8', 'L5', 'B4'], ball=3, clock=8,
                         cnt=_used('hesitate')),
    'E14': lambda: board('Twin Towers', 'Iron Wall', ['I11', 'C9', 'O9', 'G3', 'K4'], ['I10', 'D8', 'N8', 'H2', 'J3'], clock=8, key_o=(1 << 3) | (1 << 4)),
    'E14out': lambda: board('Twin Towers', 'Iron Wall', ['I11', 'C9', 'O9', 'F3', 'L4'], ['I10', 'D8', 'N8', 'H2', 'J3'], clock=8),
    'E15': lambda: board('Five Out', 'Iron Wall', SPREAD),
    'E15b': lambda: board('Shoot and Protect', 'Iron Wall', SPREAD),
    'E16': lambda: board('High-Low', 'Iron Wall', ['I9', 'C9', 'O9', 'A3', 'I6'], ['H9', 'D8', 'N8', 'B4', 'J5'], clock=10, lock_x=1, beaten=((0, 0),)),
    'E17': lambda: board('Five Out', 'Iron Wall', ['I11', 'C9', 'K0', 'A3', 'Q3'], ball=2, clock=8, inbound=1, ctx_kw=dict(inbounder=2, card_clock=8)),
    'E18': lambda: board('Five Out', 'Iron Wall', ['I11', 'C9', 'B0', 'A3', 'Q3'], ball=2, clock=8, inbound=1, ctx_kw=dict(inbounder=2, card_clock=8)),
    'E19': lambda: board('Five Out', 'Iron Wall', ['I11', 'C9', 'R12', 'A3', 'Q3'], ball=2, clock=8, inbound=1, ctx_kw=dict(inbounder=2, card_clock=8)),
    'E20': lambda: board('Five Out', 'Iron Wall', SPREAD, clock=2),
    'E21': lambda: board('Five Out', 'Iron Wall', ['I11', 'E7', 'M7', 'A3', 'Q3'], ['I10', 'F8', 'L8', 'B4', 'P4']),
    'E22': lambda: board('Five Out', 'Iron Wall', ['I13', 'C9', 'O9', 'A3', 'Q3']),
    # ---- both sides, the centre, the arrows -------------------------------------------------------------------------------
    'E23a': lambda: board('Two equal', 'Iron Wall', ['I11', 'C9', 'O9', 'G13', 'K13'], ['I10', 'F6', 'L6', 'G12', 'K12']),
    'E23b': lambda: board('Two equal', 'Iron Wall', ['I11', 'C9', 'O9', 'G13', 'K13'], ['I10', 'D8', 'L6', 'G12', 'K12']),
    'E23c': lambda: board('Two equal', 'Iron Wall', ['I11', 'C9', 'O9', 'G13', 'K13'], ['I10', 'D8', 'N8', 'G12', 'K12']),
    'E24': lambda: board('Five Out, big centre', 'Iron Wall', ['K9', 'C9', 'I12', 'A3', 'Q3'], ['K8', 'D8', 'P4', 'B4', 'N4'], clock=10, side='X'),
    'E26': lambda: board('Speed', 'Iron Wall', SPREAD),
    'E26b': lambda: board('Speed, wings swapped', 'Iron Wall', SPREAD),
    'E27': lambda: board('Two equal', 'Iron Wall', ['L10', 'E9', 'Q3', 'G13', 'K13'], ['L9', 'F8', 'P4', 'G12', 'K12']),
    'E27b': lambda: board('Best in corner', 'Iron Wall', ['L10', 'E9', 'Q3', 'G13', 'K13'], ['L9', 'F8', 'P4', 'G12', 'K12']),
    'E28': lambda: board('Five Out', 'Iron Wall', ['I11', 'C9', 'O9', 'A3', 'L7'], ['I10', 'G5', 'K5', 'B4', 'I9'], clock=10, side='X'),
    'E28b': lambda: board('One shooter', 'Iron Wall', ['I11', 'C9', 'P10', 'A3', 'L7'], ['I10', 'G5', 'K5', 'B4', 'I9'], clock=10, side='X'),
    'E29': lambda: board('High-Low', 'Iron Wall', ['N8', 'C9', 'I11', 'A3', 'F3'], ['M7', 'D8', 'I9', 'B4', 'J4'], clock=10, side='X'),
    'E30': lambda: board('Five Out', 'Iron Wall', ['C9', 'A3', 'O9', 'I11', 'G3'], ['D8', 'B4', 'J4', 'I9', 'H3'], clock=10),
    'E30b': lambda: board('Five Out', 'Iron Wall', ['C9', 'A3', 'O9', 'I11', 'G3'], ['D8', 'B4', 'M7', 'I9', 'H3'], clock=10),
    'E31': lambda: board('High-Low', 'Run and Gun', ['C9', 'I11', 'O9', 'A3', 'Q3'], ['A6', 'F7', 'P6', 'J4', 'L10'], ball=1),
    'E32': lambda: board('Speed', 'Iron Wall', ['I11', 'C9', 'O9', 'A3', 'K3'], ['I10', 'D8', 'N8', 'B4', 'K4']),
    'E33': lambda: board('Speed', 'Iron Wall', SPREAD),
    # ---- the block (D-291): step 29's board, and a second with a good shot -------------------------------------------------
    'BLK1': lambda: board('Five Out', 'Iron Wall', ['H4', 'C9', 'O9', 'A3', 'Q9'], ['D8', 'B8', 'N8', 'B3', 'H3'], arrows=[0] * 5),
    'BLK2': lambda: board('Twin Towers', 'Run and Gun', ['I11', 'C9', 'O9', 'A3', 'H4'], ['I10', 'D8', 'N8', 'B4', 'H3'], ball=4, clock=10, arrows=[0, 0, 0, 0, 0]),
    # ---- the 20 November possession, from its setup (D-292: the cards are the best reading of the record) -------------------
    'B4': lambda: board('B4 offence', 'B4 defence', ['K4', 'I2', 'N6', 'I11', 'Q3'], ['K3', 'N7', 'I10', 'J4', 'H4'], ball=3),
}
# who sets up on a board (the other side stands as given); boards not named here are read as they stand
SETUP = {k: 'defence' for k in ('E1', 'E2', 'E3', 'E3b', 'E5', 'E5b', 'E7', 'E7j', 'E8', 'E12', 'E26', 'E26b', 'E27', 'E27b', 'E32', 'E33')}
SETUP.update({k: 'offence' for k in ('E15', 'E15b', 'E17', 'E18', 'E19', 'E20')})
# the 20 November cards, read from the record's values (D-292): said plainly in the report
BUILT['B4 offence'] = ['spgB', 'cgC', 'scsfB', 'arpfB', 'pscB']
BUILT['B4 defence'] = ['dpgB', 'twB', 'dfsfB', 'dpfB', 'rpcB']


def _used(*kinds):
    from playmaker_engine.state import ZERO_COUNTS, CI
    cnt = list(ZERO_COUNTS)
    for k in kinds:
        cnt[CI[k]] = 1
    return tuple(cnt)


def get(name):
    return BOARDS[name]()


def as_json(name):
    """The board for the JavaScript engine: {state, ctx, setup}."""
    from playmaker_engine import jsbridge
    s = get(name)
    return dict(name=name, state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), setup=SETUP.get(name))


# ---- step 31, fix 3c: the drive's race (R1 to R5) ---------------------------------------------------------------------
# Real cards, the ratings each board names: O1 Attacking Point Guard A (Dribble 19); O1 on R3 Defensive Point Guard A
# (Agility 10, Quick Step 2); O2 Sharpshooter A (three 11); O3 Rim Runner C (three 5); O4 Stretch Power Forward A
# (three 9); O5 Post Scoring Centre A (layup 19). X1 Defensive Point Guard C (Agility 8, Quick Step 2); on R3 Post
# Scoring Centre C (Agility 3, no Quick Step); X2 Two-way Defender B; X3 Two-way Wing B; X4 Defensive Small Forward B;
# X5 Rim Protector A (layup contest 12, Block 10).
BUILT['Race five'] = ['apgA', 'shsA', 'rrcC', 'stpfA', 'pscA']
BUILT['Race five, quick guard'] = ['dpgA', 'shsA', 'rrcC', 'stpfA', 'pscA']
BUILT['Race defence'] = ['dpgC', 'tndB', 'twB', 'dfsfB', 'rpcA']
BUILT['Race defence, slow guard'] = ['pscC', 'tndB', 'twB', 'dfsfB', 'rpcA']
RACE_O = ['I9', 'C9', 'O9', 'A3', 'K3']           # O1 top, O2 left wing, O3 right wing, O4 left corner, O5 right block (K3: L3 is mid-range, K3 the nearest paint square)
RACE_X = ['I8', 'D8', 'N8', 'B4', 'J3']           # X1 in front of O1, X2 to X4 on their men, X5 beside O5


def quick_steps_left(s, offence, defence):
    """The board's Quick Steps left this phase (Sprints count): each side's count set to 2 less what is left."""
    from playmaker_engine.state import CI, count_key
    c = list(s.cnt)
    c[CI[count_key('O', 'qs')]] = RC.LIMITS['O']['qs'] - offence
    c[CI[count_key('X', 'qs')]] = RC.LIMITS['X']['qs'] - defence
    return s.with_(cnt=tuple(c))


def _r1():
    """R1: O1 wins a Dribble on X1 from the top (the board is made by playing the Dribble and taking the win)."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    s = board('Race five', 'Race defence', RACE_O, RACE_X)
    for a in legal_actions(s):
        if a.kind != 'dribble' or a.piece != 0:
            continue
        nx = apply(s, a)
        nodes = [nx]
        while nodes:
            n = nodes.pop()
            if isinstance(n, ChanceNode):
                nodes.extend(o[2] for o in n.outcomes)
            elif any(bt == (0, 0) for bt in n.beaten):
                return n
    raise RuntimeError('R1: no Dribble win on X1')


def _r5(x1, arrow1, off_qs, def_qs):
    o = ['I10', 'C9', 'O9', 'A3', 'K3']
    x = [x1, 'D8', 'N8', 'B4', 'I4']
    arr = [arrow1] + [facing(B.parse_sq(x[i]), B.parse_sq(o[i])) for i in range(1, 5)]
    return quick_steps_left(board('Race five', 'Race defence', o, x, arrows=arr), off_qs, def_qs)


BOARDS.update({
    'R1': _r1,
    # R2: O2 has just caught on the left wing; X2 a Move away (E7: one Move to D8, in front of him)
    'R2': lambda: board('Race five', 'Race defence', ['I11', 'C9', 'O9', 'A3', 'K3'], ['I10', 'E7', 'N8', 'B4', 'J3'], ball=1),
    # R3: O1 quick (Quick Step 2), X1 slow (no Quick Step) one square off (I7, a square between them)
    'R3': lambda: board('Race five, quick guard', 'Race defence, slow guard', RACE_O, ['I7', 'D8', 'N8', 'B4', 'J3']),
    # R4: the control: X1 set in front, arrow on O1; no Dribble won; no Quick Step left to the offence (no speed edge)
    'R4': lambda: quick_steps_left(board('Race five', 'Race defence', RACE_O, RACE_X), 0, 2),
    # R5: O1 at the top (I10), X1 off to his side (K10, facing him: his zone doesn't cover the line in), X5 at I4
    'R5a': lambda: _r5('K10', 6, 2, 0),
    'R5b': lambda: _r5('K10', 6, 2, 1),
    'R5c': lambda: _r5('J9', 4, 2, 1),             # X1 diagonal in front, arrow S: his zone (S, SW) covers I8 on the line, not I9
    'R5ctl': lambda: _r5('I9', 0, 2, 2),           # X1 set in front, arrow on O1
    # ---- fix 4 (Shaun, 27 Nov 2026): what on-ball position is worth. Each board twice: pressed (his defender next to
    # him) and two off (the same defender two squares off on the same line, facing him). Race five against Iron Wall.
    # The other four stand on the stance search's own starting shape for that offence (its goal-side base positions,
    # read with only='stance_base' on fix 4's engine and written down here), so only the one defender changes.
    'P1': lambda: _p('I10', 0, 'I9', 'N', P_BASE['P1']),    # the top of the key, pressed in front, arrows on the drive lanes
    'P1off': lambda: _p('I10', 0, 'I8', 'N', P_BASE['P1']),
    'P2': lambda: _p('I6', 0, 'I5', 'N', P_BASE['P2']),     # short range, inside the mid-range
    'P2off': lambda: _p('I6', 0, 'I4', 'N', P_BASE['P2']),
    'P3': lambda: _p('A3', 3, 'B4', 'SE', P_BASE['P3']),    # the corner, arrows SE and S: the middle walled, the baseline left
    'P3off': lambda: _p('A3', 3, 'C5', 'SW', P_BASE['P3']),
    'P4': lambda: _p('I13', 0, 'I12', 'N', P_BASE['P4']),   # the control: deep, on plain wood (no shot from there)
    'P4off': lambda: _p('I13', 0, 'I11', 'N', P_BASE['P4']),
})
