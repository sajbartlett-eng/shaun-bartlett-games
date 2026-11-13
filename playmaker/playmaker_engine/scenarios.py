"""Scenario cards and normal-game setup."""
from . import board as B
from . import rules_config as RC
from .cards import SCENARIO_CARDS, TEAMS, FIRST_GAME
from .state import Context, GameState, CI, ZERO_COUNTS

SCENARIOS = {s['n']: s for s in SCENARIO_CARDS}

# Constraints the scenario rules describe in words (Scenario_rules.pdf, CONSTRAINTS; card text).
CONSTRAINTS = {
    10: dict(tok_o=4, tok_x=4, screens_used=2),     # Late Clock Reset: both Screens spent, 4 tokens each
    15: dict(fouls=1, bonus5=1),                     # In the Bonus: one steal foul already, +5
}


def resolve_arrow(pos, intent, O, ball_pos):
    """Arrow intent ('man', 'ball', 'deny', 'help') to a direction (ported from check_scenarios.py).
    Returns (direction, error or None)."""
    mode, tgt = intent
    man = O[tgt]
    if mode in ('man', 'ball'):
        return B.nearest_dir(pos, man), None
    if mode == 'help':
        return B.nearest_dir(pos, ball_pos), None
    (ax, ay), (bx, by) = ball_pos, man
    online = ((bx - ax) * (pos[1] - ay) - (by - ay) * (pos[0] - ax) == 0
              and min(ax, bx) <= pos[0] <= max(ax, bx) and min(ay, by) <= pos[1] <= max(ay, by))
    far = lambda d: (pos[0] + B.DIRS[d][0] * 30, pos[1] + B.DIRS[d][1] * 30)
    opts = list(range(8)) if online else [d for d in range(8) if B.seg_cross(pos, far(d), ball_pos, man)]
    want = B.nearest_dir(pos, man)
    if not opts:
        return want, 'deny arrow cannot cross the lane'
    return min(opts, key=lambda d: min(abs(d - want), 8 - abs(d - want))), None


def scenario_layout(n):
    """Squares, arrows and errors for scenario n, in the same terms as check_scenarios.py."""
    sc = SCENARIOS[n]
    errs = []
    O = {k: B.parse_sq(v) for k, v in sc['O'].items()}
    occ = {}
    for k, p in O.items():
        on = B.on_board(p)
        if k == sc.get('inb'):
            if on:
                errs.append('inbounder on court')
            beside = (p[1] == 0 and 0 <= p[0] < B.W) or (p[0] in (-1, B.W) and 1 <= p[1] <= B.H)
            if not beside:
                errs.append('inbounder not beside an edge square')
        elif not on:
            errs.append(f'O{k} off board')
        occ.setdefault(p, []).append(f'O{k}')
    ball_pos = O[sc['ball']]
    X, arrows = {}, {}
    for k, (s, intent) in sc['X'].items():
        p = B.parse_sq(s)
        X[k] = p
        occ.setdefault(p, []).append(f'X{k}')
        if not B.on_board(p):
            errs.append(f'X{k} off board')
        d, e = resolve_arrow(p, intent, O, ball_pos)
        if e:
            errs.append(f'X{k} {e}')
        if intent[0] == 'ball' and B.cheb(p, O[intent[1]]) != 1:
            errs.append(f'X{k} on the ball but not adjacent')
        arrows[k] = d
    for p, who in occ.items():
        if len(who) > 1:
            errs.append('shared square ' + '+'.join(who))
    return O, X, arrows, errs


def situation_context(sc):
    """Step 18i (D-175): the foul situation a scenario card sets, as the engine reads it: the defence's team fouls this
    quarter and the possessions it has left. A card that sets none: no fouls, and a foul costs only what it costs now."""
    sit = sc.get('situation')
    if not sit:
        return {}
    return dict(team_fouls=int(sit.get('team_fouls', {}).get('dfn', 0)), quarter_left=int(sit.get('possessions_left', 0)))


def situation_words(sc):
    """The card's foul situation in plain words, or None."""
    sit = sc.get('situation')
    if not sit:
        return None
    tf, left = sit.get('team_fouls', {}), int(sit.get('possessions_left', 0))
    d, o = int(tf.get('dfn', 0)), int(tf.get('off', 0))
    return (f"The defence has {d} team foul{'s' if d != 1 else ''}; the offence has {o}. "
            f"{left} possession{'s' if left != 1 else ''} left in the quarter.")


def scenario_state(n, rules=None, target=None):
    """The starting GameState for scenario card n. With a Coach's Call card and no target,
    the first decision is the offence's secret target."""
    sc = SCENARIOS[n]
    O, X, arrows, errs = scenario_layout(n)
    if errs:
        raise ValueError(f'scenario {n}: ' + '; '.join(errs))
    title = sc['title']
    inb = sc.get('inb')
    ctx = Context(TEAMS[sc['off']], TEAMS[sc['dfn']], rules, title=f"{n}. {title}", kind=sc['kind'], scenario=n,
                  card_clock=sc['clock'], inbounder=(inb - 1) if inb else -1, coach_call=bool(sc.get('target')),
                  three_only=title == 'Need a Three', two_or_three=title == 'Two or Three',
                  hold_for_one=title == 'Hold for One', off_team=sc['off'], def_team=sc['dfn'],
                  **situation_context(sc))
    kw = dict(o=tuple(O[k] for k in range(1, 6)), x=tuple(X[k] for k in range(1, 6)),
              arrows=tuple(arrows[k] for k in range(1, 6)), ball=sc['ball'] - 1, clock=sc['clock'],
              inbound=1 if inb else 0)
    if sc.get('screen'):
        kw['screens'] = tuple(sorted((k - 1, B.angle_to_dir(a), False, 0) for k, a in sc['screen'].items()))
    if sc.get('locked'):
        kw['lock_o'] = 1 << (sc['locked'] - 1)
    con = CONSTRAINTS.get(n, {})
    cnt = list(ZERO_COUNTS)
    if 'screens_used' in con:
        cnt[CI['screen']] = con['screens_used']
    kw['cnt'] = tuple(cnt)
    for key in ('tok_o', 'tok_x', 'fouls', 'bonus5'):
        if key in con:
            kw[key] = con[key]
    if ctx.coach_call:
        if target is None:
            kw['stage'] = 'target'
        else:
            kw['target'] = target
    return GameState(ctx=ctx, **kw)


def game_state(off_team=FIRST_GAME[0], def_team=FIRST_GAME[1], o_squares=None, x_squares=None, arrows=None,
               ball=0, rules=None, clock=RC.START_CLOCK, check=True, team_fouls=0, quarter_left=0):
    """A normal-game start. Squares are names ('I11'); arrows are compass names or indices. team_fouls /
    quarter_left (digital, step 3n F3): the defence's team fouls before this possession and its possessions left in
    the quarter."""
    ctx = Context(TEAMS[off_team], TEAMS[def_team], rules, title=f'{off_team} v {def_team}', kind='GAME',
                  off_team=off_team, def_team=def_team, team_fouls=team_fouls, quarter_left=quarter_left)
    o = tuple(B.parse_sq(s) for s in o_squares)
    x = tuple(B.parse_sq(s) for s in x_squares)
    arr = tuple(B.DIR_NAMES.index(a) if isinstance(a, str) else a for a in arrows)
    if check:
        errs = setup_errors(o, x, ball)
        if errs:
            raise ValueError('; '.join(errs))
    return GameState(ctx=ctx, o=o, x=x, arrows=arr, ball=ball, clock=clock)


def setup_errors(o, x, ball):
    errs = []
    allp = list(o) + list(x)
    if len(set(allp)) != len(allp):
        errs.append('two pieces share a square')
    if not all(B.on_board(p) for p in allp):
        errs.append('a piece is off the board')
    bp = o[ball]
    if not (B.zone(bp) == '.' and bp[1] > 1):
        errs.append('the ball must start on plain wood beyond the three-point tiles')
    return errs
