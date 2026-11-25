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
