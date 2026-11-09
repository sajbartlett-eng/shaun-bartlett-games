"""Step 3k: the computer's setup (rulebook setup steps 4 and 5), offence and defence. No rule changes: the offence
places five pieces first with the ball on a player on plain wood beyond the three-point tiles; the defence then places
on empty squares and sets every arrow. Only where the computer places its own side (full games, custom teams, quick
games); scenario cards keep their fixed setups and a human always places their own side.

The computer uses only what a human sees at that moment: the offence sets up from the cards alone (it places first and
never sees the defence's placement, so it anticipates the defence's best response); the defence sees the offence's
placement.

Levels (computer_levels.json names):
  offence  rookie: the fixed formation, the ball on the best creator; starter: the formation from the top goal, the ball
           chosen by that goal; allstar: every goal's formations scored against the defence's best response, chosen
           among those within a small margin of the best (variety).
  defence  rookie: man-to-man by number, arrows on the man; starter: the matchup search (all 120) plus the basic jobs
           (contain, help, sag); allstar: every job (deny, contain, wall, help, sag, front), the coherence checks and a
           short evaluation of the on-ball wall.
"""
import random
import time
from itertools import permutations, product

from . import board as B
from . import rules_config as RC

SHOT_PTS = {'layup': 2, 'dunk': 2, 'post': 2, 'floater': 2, 'mid': 2, 'long': 2, 'three': 3}
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
SQ = B.parse_sq

# court spots, as squares (built from the zone map: the rules' own tiles)
BALL_SPOTS = [SQ(q) for q in ('I11', 'H11', 'J11', 'G11', 'K11', 'I12', 'D10', 'N10', 'C10', 'O10')]
CORNERS = {'L': [SQ(q) for q in ('A2', 'A3', 'A4')], 'R': [SQ(q) for q in ('Q2', 'Q3', 'Q4')]}
WINGS = {'L': [SQ(q) for q in ('B7', 'B8', 'C8', 'C9')], 'R': [SQ(q) for q in ('P7', 'P8', 'O8', 'O9')]}
SLOTS = {'L': [SQ(q) for q in ('E10', 'F10', 'D9')], 'R': [SQ(q) for q in ('M10', 'L10', 'N9')]}
BLOCKS = {'L': [SQ(q) for q in ('G3', 'G4')], 'R': [SQ(q) for q in ('K3', 'K4')]}
ELBOWS = {'L': [SQ(q) for q in ('G7', 'G6')], 'R': [SQ(q) for q in ('K7', 'K6')]}
HIGH_POST = [SQ(q) for q in ('I7', 'I6', 'H7', 'J7')]
SIDES = ('L', 'R')


def ball_legal(q):
    """The rulebook's ball square: plain wood beyond the three-point tiles."""
    return B.on_board(q) and B.zone(q) == '.' and q[1] > 1


def legal_offence(squares, ball):
    return (len(squares) == 5 and len(set(squares)) == 5 and all(B.on_board(q) for q in squares)
            and ball_legal(squares[ball]))


# ---- cards ---------------------------------------------------------------------------------------------------------

def creator(off):
    return max(range(5), key=lambda i: (off[i].qs, off[i].r['dribble'], -i))


def passer(off, exclude=()):
    c = [i for i in range(5) if i not in exclude]
    return max(c, key=lambda i: (off[i].r['pass'], off[i].r['dribble'], -i))


def threat(o, d):
    """Attacker card o against defender card d, from the cards alone: the best shot edge (points x (rating - that
    defender's contest)) and the creation edge (Dribble against Agility, with the Quick Step), as one number."""
    shots = max(SHOT_PTS[t] * (o.shot(t) - d.con(t)) for t in SHOT_PTS)
    drive = 0.5 * (o.r['dribble'] - d.r['agility']) + 1.5 * o.qs
    return max(shots, 2 * (o.shot('layup') - d.con('layup')) + drive)


def best_matchups(off, dfn):
    """Every one of the 120 assignments; the one leaving the offence the lowest best threat (then the lowest total, then
    the fewest changes from man-to-man by number). perm[j] = the attacker defender j guards."""
    cost = [[threat(off[i], dfn[j]) for j in range(5)] for i in range(5)]
    best = None
    for perm in permutations(range(5)):
        vals = [cost[perm[j]][j] for j in range(5)]
        k = (round(max(vals), 6), round(sum(vals), 6), sum(perm[j] != j for j in range(5)), perm)
        if best is None or k < best:
            best = k
    return tuple(best[3]), cost


def goals(off, dfn, perm=None):
    """The offence's goals from the cards alone, against the defenders it expects (the defence's best assignment),
    best first: [{kind, att, value, words, ...}]."""
    perm = perm or best_matchups(off, dfn)[0]
    guard = {perm[j]: j for j in range(5)}
    cr, out = creator(off), []
    for i in range(5):
        d = dfn[guard[i]]
        c = off[i]
        three = 3 * (c.shot('three') - d.con('three'))
        post = 2 * (c.shot('post') - d.con('post'))
        drive = 2 * (c.shot('layup') - d.con('layup')) + 0.5 * (c.r['dribble'] - d.r['agility']) + 1.5 * c.qs
        if c.bands['shot_three'] == 'H' or three >= 24:
            out.append(dict(kind='three', att=i, value=three, shot='three'))
        if c.bands['shot_post'] == 'H':
            out.append(dict(kind='post', att=i, value=post + 1.0, shot='post'))
            hp = max((k for k in range(5) if k != i), key=lambda k: (off[k].r['screen'] + off[k].r['pass'], -k))
            out.append(dict(kind='highlow', att=i, value=post + 0.5, shot='post', high=hp))
        if i == cr or c.bands['dribble'] == 'H':
            out.append(dict(kind='iso', att=i, value=drive, shot='layup'))
            scr = max((k for k in range(5) if k != i), key=lambda k: (off[k].r['screen'], -k))
            pr = drive + 0.4 * (off[scr].r['screen'] - 10)
            out.append(dict(kind='pnr', att=i, value=pr, shot='layup', screener=scr))
        if c.bands['shot_three'] == 'H':
            big = max((k for k in range(5) if k != i), key=lambda k: (off[k].r['screen'], -k))
            out.append(dict(kind='handoff', att=i, value=three - 1.0, shot='three', screener=big))
    return sorted(out, key=lambda g: (-g['value'], g['kind'], g['att']))


GOAL_WORDS = {'three': 'a three for O{a}', 'post': 'a post entry to O{a}', 'highlow': 'a high-low to O{a}',
              'iso': 'an isolation for O{a}', 'pnr': 'a pick and roll for O{a}', 'handoff': 'a dribble handoff for O{a}'}


# ---- offence formations from principles ----------------------------------------------------------------------------

def _spaced(squares, pairs_ok=()):
    """No two attackers within 2 squares, unless a goal needs them close (pairs_ok: index pairs)."""
    ok = {frozenset(p) for p in pairs_ok}
    for a in range(5):
        for b in range(a + 1, 5):
            if B.cheb(squares[a], squares[b]) <= 2 and frozenset((a, b)) not in ok:
                return False
    return True


def _in_lane(q):
    return B.zone(q) in ('K', 'M') and 6 <= q[0] <= 10


def _fill(squares, rest, off, side_pref, kick):
    """Place the remaining players on spacing spots: shooters on their best three squares (corners first when a drive or
    kick is the goal), everyone else spaced on the perimeter, the lane kept clear."""
    taken = [q for q in squares if q is not None]
    order = sorted(rest, key=lambda i: (-off[i].r['shot_three'], i))
    spots = []
    for s in (side_pref, 'R' if side_pref == 'L' else 'L'):
        spots += (CORNERS[s] + WINGS[s] + SLOTS[s]) if kick else (WINGS[s] + CORNERS[s] + SLOTS[s])
    for i in order:
        best = None
        for q in spots:
            if q in taken or any(B.cheb(q, t) <= 2 for t in taken):
                continue
            score = (0 if off[i].bands['shot_three'] != 'L' or B.zone(q) != '3' else 1, spots.index(q))
            if best is None or score < best[0]:
                best = (score, q)
        if best is None:
            return None
        squares[i] = best[1]
        taken.append(best[1])
    return squares


def formations(off, gl, kinds=None, limit=80):
    """Candidate offence setups built from the goals: {squares, ball, goal, shape}. kinds: restrict to these goal
    kinds (Starter: the top goal's)."""
    out, seen = [], set()
    for g in gl:
        if kinds and g['kind'] not in kinds:
            continue
        for side, bspot in product(SIDES, BALL_SPOTS[:6]):
            sq = [None] * 5
            pairs = ()
            k, a = g['kind'], g['att']
            if k in ('pnr', 'iso'):
                ball = a
                sq[a] = bspot
                if k == 'pnr':
                    s = g['screener']
                    dx = -1 if side == 'L' else 1
                    near = [(bspot[0] + dx, bspot[1] - 1), (bspot[0] + dx, bspot[1] - 2), (bspot[0], bspot[1] - 2)]
                    near = [q for q in near if B.on_board(q) and q != bspot]
                    if not near:
                        continue
                    sq[s] = near[0]
                    pairs = ((a, s),)
                rest = [i for i in range(5) if sq[i] is None]
                kick = True
            elif k in ('post', 'highlow'):
                ball = passer(off, exclude=(a,))
                sq[a] = BLOCKS[side][0 if bspot[1] >= 11 else 1]
                wing_ball = [q for q in BALL_SPOTS if q[1] == 10 and ((q[0] < 8) == (side == 'L'))]
                sq[ball] = wing_ball[0] if (k == 'post' and bspot in BALL_SPOTS[:2] and wing_ball) else bspot
                if k == 'highlow':
                    h = g['high'] if g['high'] != ball else next(i for i in range(5) if i not in (a, ball))
                    sq[h] = HIGH_POST[(BALL_SPOTS.index(bspot)) % len(HIGH_POST)]
                    pairs = ((a, h),)
                rest = [i for i in range(5) if sq[i] is None]
                kick = False
            elif k == 'handoff':
                ball = a
                sq[a] = bspot
                s = g['screener']
                dx = -1 if side == 'L' else 1
                sq[s] = (bspot[0] + dx, bspot[1] - 1)
                pairs = ((a, s),)
                rest = [i for i in range(5) if sq[i] is None]
                kick = True
            else:                                          # 'three': a creator or passer to find the shooter
                ball = creator(off) if creator(off) != a else passer(off, exclude=(a,))
                sq[ball] = bspot
                spots = (CORNERS[side] + WINGS[side]) if off[ball].bands['dribble'] == 'H' else (WINGS[side] + CORNERS[side])
                sq[a] = next((q for q in spots if B.cheb(q, bspot) > 2), spots[0])
                rest = [i for i in range(5) if sq[i] is None]
                kick = off[ball].bands['dribble'] == 'H'
            if any(q is not None and not B.on_board(q) for q in sq):
                continue
            filled = _fill(sq, rest, off, 'R' if side == 'L' else 'L', kick)
            if filled is None or not legal_offence(filled, ball) or not _spaced(filled, pairs):
                continue
            if k in ('pnr', 'iso') and any(_in_lane(filled[i]) for i in range(5) if i != ball and (k != 'pnr' or i != g.get('screener'))):
                continue                                   # the lane kept open for the drive
            key = (tuple(filled), ball)
            if key in seen:
                continue
            seen.add(key)
            out.append(dict(squares=filled, ball=ball, goal=g, shape=shape_name(filled, ball, g)))
            if len(out) >= limit:
                return out
    return out


def shape_name(squares, ball, goal=None):
    """The recognisable shape, when one fits."""
    inside = [i for i, q in enumerate(squares) if B.zone(q) in ('K', 'M')]
    elbows = [i for i, q in enumerate(squares) if q in ELBOWS['L'] + ELBOWS['R']]
    blocks = [i for i, q in enumerate(squares) if q in BLOCKS['L'] + BLOCKS['R'] or B.zone(q) == 'K']
    left = sum(1 for q in squares if q[0] < 8)
    right = sum(1 for q in squares if q[0] > 8)
    bq = squares[ball]
    screener_near = any(i != ball and B.cheb(squares[i], bq) <= 2 for i in range(5))
    if len(elbows) == 2:
        return 'horns'
    if blocks and any(squares[i] in HIGH_POST + ELBOWS['L'] + ELBOWS['R'] for i in range(5) if i not in blocks):
        return 'high-low'
    if screener_near and not inside and goal and goal['kind'] in ('pnr', 'handoff'):
        return 'spread pick and roll'
    if max(left, right) >= 4:
        return 'overload'
    if not inside:
        return 'five out'
    if len(inside) == 1:
        return 'four out, one in'
    return None


# ---- the defence's jobs --------------------------------------------------------------------------------------------

JOB_WORDS = {'contain': 'contained O{a} between the ball and the basket', 'wall': 'walled O{a}\'s drive',
             'deny': 'denied O{a} the catch', 'front': 'fronted O{a} in the post', 'help': 'helped off O{a}',
             'sag': 'sagged off O{a}', 'man': 'guarded O{a}'}


def _adjacent_free(q, taken):
    return [(q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)
            if (dx or dy) and B.on_board((q[0] + dx, q[1] + dy)) and (q[0] + dx, q[1] + dy) not in taken]


def _best_look_open(c, q):
    z = B.zone(q)
    if not RC.ZONE_SHOTS.get(z):
        return 0
    return max(RC.ZONE_POINTS[z] * c.shot(t) for t in RC.ZONE_SHOTS[z])


def _best_look_v(c, d, q):
    z = B.zone(q)
    if not RC.ZONE_SHOTS.get(z):
        return 0
    return max(RC.ZONE_POINTS[z] * (c.shot(t) - d.con(t)) for t in RC.ZONE_SHOTS[z])


def choose_jobs(off, dfn, o_sq, ball, perm, level, comfort):
    """A job for each defender: what is most worth protecting against the attacker it guards."""
    jobs = {}
    for j in range(5):
        a = perm[j]
        c, d, q = off[a], dfn[j], o_sq[a]
        if a == ball:
            jobs[j] = 'contain'
        elif level == 'allstar' and c.bands['shot_three'] == 'H' and (B.zone(q) == '3' or min(B.cheb(q, t) for t in sum(CORNERS.values(), []) + sum(WINGS.values(), []) + sum(SLOTS.values(), [])) <= 1):
            jobs[j] = 'deny'
        elif level == 'allstar' and c.bands['shot_post'] == 'H' and (B.zone(q) == 'K' or q in BLOCKS['L'] + BLOCKS['R']):
            jobs[j] = 'front'
        elif comfort is not None and (_best_look_open(c, q) <= comfort or
                                      (c.bands['shot_three'] == 'L' and _best_look_v(c, d, q) <= comfort)):
            jobs[j] = 'sag'
        else:
            jobs[j] = 'help'
    return jobs


def place_jobs(state_of, o_sq, ball, perm, jobs):
    """Squares and arrows for the jobs, the most demanding first. state_of(xs, arrows) builds a board for checks."""
    from .actions import denier
    rim = RC.RIM
    bq = o_sq[ball]
    taken = set(o_sq)
    xs, arrows = [None] * 5, [None] * 5
    order = sorted(range(5), key=lambda j: ['contain', 'wall', 'deny', 'front', 'help', 'sag', 'man'].index(jobs[j]))
    for j in order:
        a = perm[j]
        man = o_sq[a]
        job = jobs[j]
        best = None
        if job in ('contain', 'wall', 'man'):
            for q in _adjacent_free(man, taken):
                k = (B.dist_rim(q) - B.dist_rim(man), abs((man[0] - rim[0]) * (q[1] - man[1]) - (man[1] - rim[1]) * (q[0] - man[0])), q)
                if best is None or k < best[0]:
                    best = (k, q, B.dir_between(q, man))
        elif job in ('deny', 'front'):
            for q in _adjacent_free(man, taken):
                if job == 'front' and B.cheb(q, bq) >= B.cheb(man, bq):
                    continue
                trial = list(xs)
                trial[j] = q
                full = [t if t is not None else (-9, -9) for t in trial]
                st = _Probe(o_sq, full, ball)
                dn = denier(st, ball, a) == j
                k = (0 if dn else 1, B.cheb(q, bq), q)
                if best is None or k < best[0]:
                    best = (k, q, B.dir_between(q, man))
        else:                                              # help / sag: off the man, recoverable in one movement
            want = 2 if job == 'sag' else None
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    q = (man[0] + dx, man[1] + dy)
                    c = B.cheb(q, man)
                    if not B.on_board(q) or q in taken or c == 0 or (want and c != want) or (not want and c > 2):
                        continue
                    if B.dist_rim(q) > B.dist_rim(man) + (0 if job == 'sag' else 1):
                        continue
                    lane = B.on_segment(q, bq, man, 0.5) if a != ball else False
                    drive = _near_path(q, bq, rim)
                    k = (-(2.0 * lane + 1.5 * drive) + 0.15 * B.dist_rim(q) + 0.3 * c, q)
                    if best is None or k < best[0]:
                        best = (k, q, B.nearest_dir(q, bq))
        if best is None:                                   # fall back to the nearest free square next to him
            q = min(_adjacent_free(man, taken) or [s for s in ((x, y) for x in range(17) for y in range(1, 15)) if s not in taken],
                    key=lambda s: (B.cheb(s, man), s))
            best = (None, q, B.dir_between(q, man) if B.adjacent(q, man) else B.nearest_dir(q, man))
            jobs[j] = 'man'
        xs[j], arrows[j] = best[1], best[2]
        taken.add(best[1])
    return xs, arrows


def _near_path(q, a, b):
    """Within a square of the straight path a -> b (the drive)."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy or 1
    t = max(0.0, min(1.0, ((q[0] - a[0]) * vx + (q[1] - a[1]) * vy) / L2))
    px, py = a[0] + t * vx, a[1] + t * vy
    return max(abs(q[0] - px), abs(q[1] - py)) <= 1.0


class _Probe:
    """The minimum a geometry check needs (o, x, ball, ctx.rules) without building a full game state."""
    def __init__(self, o, x, ball):
        self.o, self.x, self.ball = tuple(o), tuple(x), ball

        class _C:
            rules = RC.DEFAULT_RULES
        self.ctx = _C()


def coherence(state, perm, jobs, off):
    """The whole defence: the rim, the drives, overloaded defenders, the reserve. Returns (problems, notes)."""
    from .actions import movement_dests
    rules = state.ctx.rules
    rim = RC.RIM
    reach = {j: set(movement_dests(state, 'X', j, 'move', rules)) | {state.x[j]} for j in range(5)}
    notes, problems = [], []
    if not any(B.cheb(q, rim) <= 1 for j in range(5) for q in reach[j]):
        problems.append('rim')
    else:
        j = min(range(5), key=lambda j: (min(B.cheb(q, rim) for q in reach[j]), j))
        notes.append(f'X{j + 1} can reach the rim in one movement.')
    drivers = [i for i in range(5) if i == state.ball or off[i].bands['dribble'] == 'H' or off[i].bands['shot_layup'] == 'H']
    for i in drivers:
        g = next(j for j in range(5) if perm[j] == i)
        walled = B.adjacent(state.x[g], state.o[i]) and B.dist_rim(state.x[g]) < B.dist_rim(state.o[i])
        helped = any(_near_path(state.x[j], state.o[i], rim) for j in range(5) if j != g)
        if not (walled or helped):
            problems.append(f'drive O{i + 1}')
    threats = [i for i in range(5) if i == state.ball or off[i].bands['shot_three'] == 'H' or off[i].bands['shot_post'] == 'H']
    answers = {i: {j for j in range(5) if any(B.adjacent(q, state.o[i]) for q in reach[j])} for i in threats}
    for j in range(5):
        only = [i for i in threats if answers[i] == {j}]
        if len(only) >= 2:
            notes.append(f'X{j + 1} is the only answer to ' + ' and '.join(f'O{i + 1}' for i in only)
                         + ': accepted, no other defender is within one movement of both.')
    notes.append('The reaction reserve is intact: six tokens at tip-off.')
    return problems, notes


def defence_setup(comp, o_sq, ball, build, level=None, budget_s=1.5, refine=True):
    """The computer defence's setup against the offence's placement. build(xs, arrows) -> the starting GameState.
    Returns dict(xs, arrows, perm, jobs, notes, reasons)."""
    t0 = time.time()
    level = level or comp.level
    o_sq = [tuple(q) for q in o_sq]
    probe = build(*_man(o_sq, list(range(5))))
    comp._context(probe)
    off, dfn = comp.seen.off, comp.seen.dfn
    if level == 'rookie':
        xs, arrows = _man(o_sq, list(range(5)))
        return dict(xs=xs, arrows=arrows, perm=tuple(range(5)), jobs={j: 'man' for j in range(5)},
                    notes=[], reasons=['Man-to-man by number, every arrow on its man.'], seconds=round(time.time() - t0, 2))
    perm, cost = best_matchups(off, dfn)
    jobs = choose_jobs(off, dfn, o_sq, ball, perm, level, comp.comfort)
    xs, arrows = place_jobs(None, o_sq, ball, perm, jobs)
    state = build(xs, arrows)
    problems, notes = coherence(state, perm, jobs, off)
    if 'rim' in problems:
        # the least needed off-ball defender goes to the rim (between the ball and the basket)
        cands = [j for j in range(5) if jobs[j] in ('sag', 'help') and perm[j] != ball] or [j for j in range(5) if perm[j] != ball]
        j = min(cands, key=lambda j: (jobs[j] != 'help', max(cost[perm[j]][j], 0), j))   # a helper first, then a sagger
        taken = set(o_sq) | {xs[k] for k in range(5) if k != j}
        q = min((s for s in ((x, y) for x in range(5, 12) for y in range(2, 7)) if s not in taken),
                key=lambda s: (B.cheb(s, RC.RIM) != 1, B.cheb(s, o_sq[ball]), s))   # next to the rim, ball side
        xs[j], arrows[j] = q, B.nearest_dir(q, o_sq[ball])
        jobs[j] = 'rim'
        state = build(xs, arrows)
        problems, notes = coherence(state, perm, jobs, off)
        notes = [n for n in notes if 'can reach the rim' not in n]
        notes.insert(0, f'X{j + 1} left O{perm[j] + 1} to protect the rim: no other defender could reach it in one movement.')
    if refine and level == 'allstar':
        # the on-ball wall: the arrow along the drive, if the evaluation prefers it to the contain
        jb = next(j for j in range(5) if perm[j] == ball)
        stop = t0 + budget_s

        def value(ar):
            s = build(xs, ar)
            comp._context(s)
            return comp.ev(s.with_(ctx=comp.seen))[0].ev
        best_v = value(arrows)
        for d in range(8):
            if time.time() > stop or d == arrows[jb]:
                continue
            a2 = arrows[:jb] + [d] + arrows[jb + 1:]
            v = value(a2)
            if v < best_v - 0.25:
                best_v, arrows = v, a2
                jobs[jb] = 'wall'
    reasons = _defence_reasons(off, dfn, perm, jobs, cost)
    for p in problems:
        if p.startswith('drive'):
            notes.append(f'No wall or help on {p[6:]}\'s drive: accepted, every defender is needed elsewhere.')
    return dict(xs=xs, arrows=arrows, perm=perm, jobs=jobs, notes=notes, reasons=reasons, seconds=round(time.time() - t0, 2))


def _man(o_sq, perm):
    from .computer import _assign
    return _assign(o_sq, perm)


def _defence_reasons(off, dfn, perm, jobs, cost):
    out = []
    for j in range(5):
        a = perm[j]
        if a != j:
            why = _why_switch(off[a], dfn[a], dfn[j], a)
            out.append(f'Put X{j + 1} on O{a + 1}: {why}.')
    for j in range(5):
        if jobs[j] in JOB_WORDS:                           # the rim protector has its own note
            out.append(f'X{j + 1} ' + JOB_WORDS[jobs[j]].format(a=perm[j] + 1) + '.')
    return out


def _why_switch(o, d_default, d_new, a):
    """The plain reason a defender other than the same number guards this attacker."""
    if o.bands['shot_three'] == 'H' and d_new.con('three') > d_default.con('three'):
        return f"X{a + 1} couldn't close out on him (three contest {d_default.con('three')} against {d_new.con('three')})"
    if o.bands['shot_post'] == 'H' and d_new.con('post') > d_default.con('post'):
        return f"a better post defender (post contest {d_new.con('post')} against {d_default.con('post')})"
    if o.bands['dribble'] == 'H' and d_new.r['agility'] > d_default.r['agility']:
        return f"a quicker defender on the creator (Agility {d_new.r['agility']} against {d_default.r['agility']})"
    return 'the assignment that leaves the offence the lowest best edge'


# ---- the offence's setup -------------------------------------------------------------------------------------------

def offence_setup(comp, make, seed=0, budget_s=2.5, anticipate=None):
    """The computer offence's setup from the cards alone. make(o_sq, ball, xs, arrows) -> a GameState (used only for
    boards the offence builds itself: its own candidates against the defence it anticipates; it is never given the
    defence's real placement, which doesn't exist yet). Returns dict(squares, ball, goal, shape, reasons, value,
    candidates, within)."""
    t0 = time.time()
    level = comp.level
    o_tab = [SQ(q) for q in TABLE_O]
    probe = make(o_tab, 0, *_man(o_tab, list(range(5))))
    comp._context(probe)
    off, dfn = comp.seen.off, comp.seen.dfn
    cr = creator(off)
    if level == 'rookie':
        sq = list(o_tab)
        sq[0], sq[cr] = sq[cr], sq[0]                     # the fixed formation, the ball on the best creator
        return dict(squares=sq, ball=cr, goal=None, shape='five out', value=None, candidates=1, within=1,
                    reasons=[f'Started the ball with O{cr + 1} (best creator) in the fixed formation.'], seconds=round(time.time() - t0, 2))
    perm, _ = best_matchups(off, dfn)
    gl = goals(off, dfn, perm)
    kinds = None
    if level == 'starter':
        kinds = {gl[0]['kind']}
    cands = formations(off, gl[:6] if level == 'allstar' else gl[:1], kinds)
    if not cands:
        sq = list(o_tab)
        sq[0], sq[cr] = sq[cr], sq[0]
        cands = [dict(squares=sq, ball=cr, goal=gl[0] if gl else None, shape='five out')]
    anticipate = level == 'allstar' if anticipate is None else anticipate
    from .advantage import reach_maps, looks
    from .capacity import lane_answered
    stop = t0 + budget_s
    scored = []
    for c in cands:
        if scored and time.time() > stop:
            break
        o_sq, ball = c['squares'], c['ball']
        if anticipate:
            # the defence's best response: its matchups and jobs against this placement (section 2's logic)
            build = lambda xs, ar: make(o_sq, ball, xs, ar)
            r = defence_setup(comp_as_defence(comp), o_sq, ball, build, level='allstar', refine=False)
            xs, ar = r['xs'], r['arrows']
        else:
            xs, ar = _man(o_sq, list(range(5)))          # a passive defence: man-to-man by number
        s = make(o_sq, ball, xs, ar)
        maps = reach_maps(s)
        vals = []
        for i in range(5):
            L = looks(s, i, maps)
            if not L:
                continue
            v = L[0][0]
            if i != ball and lane_answered(s, ball, i):
                v *= 0.35                                  # the catch is answered: denied, or a lane a defender reaches
            vals.append(v)
        vals.sort(reverse=True)
        goal_bonus = 0.15 * max(0.0, c['goal']['value']) if c.get('goal') else 0.0
        value = (vals[0] if vals else 0) + 0.3 * (vals[1] if len(vals) > 1 else 0) + goal_bonus
        scored.append((round(value, 3), c))
    scored.sort(key=lambda vc: -vc[0])
    best_v = scored[0][0]
    margin = {'allstar': 1.5, 'starter': 0.0}.get(level, 0.0)
    within = [vc for vc in scored if vc[0] >= best_v - margin]
    rng = random.Random(seed * 7919 + 13)
    v, c = within[rng.randrange(len(within))] if len(within) > 1 else within[0]
    g = c.get('goal')
    why = _offence_reason(off, c, cr)
    reasons = [why]
    if len(within) > 1:
        reasons.append(f'Chosen among {len(within)} setups within {margin} of the best ({best_v:.1f}), for variety.')
    return dict(squares=list(c['squares']), ball=c['ball'], goal=g, shape=c.get('shape'), value=v,
                candidates=len(scored), within=len(within), reasons=reasons, seconds=round(time.time() - t0, 2))


def comp_as_defence(comp):
    """The offence's model of the defence's response: an All-Star defence reading the same cards."""
    from .computer import Computer
    cache = comp.__dict__.setdefault('_defence_model', {})
    m = cache.get('x')
    if m is None:
        m = Computer('X', 'allstar', seed=0, habits=[], budget_s=None)
        cache['x'] = m
    return m


def _offence_reason(off, c, cr):
    g = c.get('goal')
    ball = c['ball']
    shape = c.get('shape')
    if not g:
        return f'Started the ball with O{ball + 1}.'
    role = ('best creator' if ball == cr else 'creator') if g['kind'] in ('pnr', 'iso') else \
           'best passer' if g['kind'] in ('post', 'highlow') else \
           'shooter' if g['kind'] == 'handoff' else ('best creator' if ball == cr else 'best passer')
    words = GOAL_WORDS[g['kind']].format(a=g['att'] + 1)
    return f'Started the ball with O{ball + 1} ({role}) for {words}' + (f'; {shape}.' if shape else '.')
