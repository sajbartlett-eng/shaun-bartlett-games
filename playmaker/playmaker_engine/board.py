"""Board geometry: squares, zones, adjacency, arrows, lines and movement shapes.

Coordinates are (x, y): x = 0..16 for columns A..Q, y = 1..14 for rows (row 1 is
the baseline). Off-board inbounder squares: row 0 ('K0'), x = -1 ('@9'), x = 17 ('R9').
"""
import json
import os
from functools import lru_cache
from fractions import Fraction

from . import rules_config as RC

COLS = 'ABCDEFGHIJKLMNOPQ'
W, H = RC.BOARD_COLS, RC.BOARD_ROWS
RIM = RC.RIM

# 8 directions, index 0..7 = 0, 45, ..., 315 degrees clockwise from north (row up).
DIRS = ((0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1), (-1, 0), (-1, 1))
DIR_NAMES = ('N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW')
ORTH = (0, 2, 4, 6)
DIAG = (1, 3, 5, 7)


def angle_to_dir(a):
    return (a % 360) // 45


def dir_to_angle(d):
    return d * 45


def on_board(p):
    return 0 <= p[0] < W and 1 <= p[1] <= H


def in_key(p):
    """D-172: is this square in the key (the lane as drawn: columns G to K, rows 1 to 6)?"""
    return RC.KEY_COLS[0] <= p[0] <= RC.KEY_COLS[1] and RC.KEY_ROWS[0] <= p[1] <= RC.KEY_ROWS[1]


def sq(p):
    """Square name, including off-board inbounder names."""
    x, y = p
    if x == -1:
        c = '@'
    elif x == W:
        c = 'R'
    else:
        c = COLS[x]
    return f'{c}{y}'


def parse_sq(s):
    c, r = s[0], int(s[1:])
    if c == '@':
        x = -1
    elif c == 'R':
        x = W
    else:
        x = COLS.index(c)
    return (x, r)


_ZONES_PATH = os.path.join(os.path.dirname(__file__), 'data', 'court_zones.json')
with open(_ZONES_PATH) as _f:
    _Z = json.load(_f)
ZONE = {parse_sq(k): v for k, v in _Z.items()}


def zone(p):
    return ZONE.get(p, '.')


def cheb(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]))


def dist_rim(p):
    return cheb(p, RIM)


def adjacent(a, b):
    return cheb(a, b) == 1


def add(p, d, n=1):
    return (p[0] + d[0] * n, p[1] + d[1] * n)


def dir_between(a, b):
    """Exact direction index from a to an adjacent square b, else None."""
    d = (b[0] - a[0], b[1] - a[1])
    return DIRS.index(d) if d in DIRS else None


def nearest_dir(frm, to):
    """Direction closest to pointing from frm at to (ported from check_scenarios.py)."""
    import math
    vx, vy = to[0] - frm[0], to[1] - frm[1]
    a = math.degrees(math.atan2(vx, vy)) % 360
    return min(range(8), key=lambda d: min(abs(d * 45 - a), 360 - abs(d * 45 - a)))


# ---- lines -------------------------------------------------------------------

def _orient(p, q, r):
    return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])


def seg_cross(p, q, a, b):
    """Strict crossing of segments pq and ab (ported from check_scenarios.py)."""
    d1, d2, d3, d4 = _orient(a, b, p), _orient(a, b, q), _orient(p, q, a), _orient(p, q, b)
    return d1 * d2 < 0 and d3 * d4 < 0


def ray_end(p, d):
    """Where the arrow ray from p in direction d leaves the board (board edge at half squares)."""
    dx, dy = DIRS[d]
    ts = []
    if dx > 0:
        ts.append(Fraction(2 * (W - 1) + 1, 2) - p[0])
    elif dx < 0:
        ts.append(p[0] + Fraction(1, 2))
    if dy > 0:
        ts.append(Fraction(2 * H + 1, 2) - p[1])
    elif dy < 0:
        ts.append(p[1] - Fraction(1, 2))
    t = min(ts)
    return (p[0] + dx * t, p[1] + dy * t)


def arrow_crosses(def_pos, d, a, b):
    """Does the arrow line (ray to the board edge) strictly cross segment ab?"""
    return seg_cross(def_pos, ray_end(def_pos, d), a, b)


def on_segment(p, a, b, tol):
    """Is square p on the pass segment a->b (centre within tol of it, strictly between ends)?"""
    if p == a or p == b:
        return False
    vx, vy = b[0] - a[0], b[1] - a[1]
    wx, wy = p[0] - a[0], p[1] - a[1]
    L2 = vx * vx + vy * vy
    dot = wx * vx + wy * vy
    if dot <= 0 or dot >= L2:
        return False
    cross = vx * wy - vy * wx
    if tol == 0:
        return cross == 0
    t = Fraction(tol).limit_denominator(1000)
    return Fraction(cross * cross) < t * t * L2


def path_crosses_ray(points, D, d, strict=True):
    """Does the polyline `points` cross the arrow ray from D in direction d?

    Crossing means going from one side of the ray to the other. Touching the ray,
    or stepping onto it and back to the same side, is allowed. With strict=False,
    stepping onto the ray at all counts as crossing.
    """
    dx, dy = DIRS[d]

    def side(p):
        return dx * (p[1] - D[1]) - dy * (p[0] - D[0])

    def fwd(p):
        return dx * (p[0] - D[0]) + dy * (p[1] - D[1])

    last_i, last_s = None, 0
    for i, p in enumerate(points):
        s = side(p)
        if s == 0:
            if not strict and fwd(p) > 0 and i > 0:
                return True
            continue
        if last_s and (s > 0) != (last_s > 0):
            if i - last_i == 1:
                a, b = points[last_i], p
                sa, sb = abs(last_s), abs(s)
                ix = a[0] + Fraction((b[0] - a[0]) * sa, sa + sb)
                iy = a[1] + Fraction((b[1] - a[1]) * sa, sa + sb)
                if dx * (ix - D[0]) + dy * (iy - D[1]) >= 0:
                    return True
            else:
                if all(fwd(points[j]) > 0 for j in range(last_i + 1, i)):
                    return True
        last_i, last_s = i, s
    return False


# ---- movement shapes -----------------------------------------------------------

def straight_paths(p, dirs, max_len, min_len=1):
    """Paths along one straight line: list of (dir, [squares...])."""
    out = []
    for d in dirs:
        path = []
        for n in range(1, max_len + 1):
            path = path + [add(p, DIRS[d], n)]
            if n >= min_len:
                out.append((d, list(path)))
    return out


@lru_cache(maxsize=None)
def move_paths(p, rules):
    """All Move shapes from p: up to 3 straight, up to 2 diagonal, 1 straight + 1 diagonal."""
    out = [path for _, path in straight_paths(p, ORTH, RC.MOVE_STRAIGHT)]
    if rules.diag_move_straight:
        out += [path for _, path in straight_paths(p, DIAG, RC.MOVE_DIAGONAL)]
    else:
        for a in DIAG:
            m = add(p, DIRS[a])
            out.append([m])
            for b in DIAG:
                out.append([m, add(m, DIRS[b])])
    for a in ORTH:
        for b in DIAG:
            m = add(p, DIRS[a])
            out.append([m, add(m, DIRS[b])])
            if rules.move_either_order:
                m2 = add(p, DIRS[b])
                out.append([m2, add(m2, DIRS[a])])
    # drop shapes that end where they started (e.g. N then SW then... never in these shapes)
    return tuple(tuple(path) for path in out if path[-1] != p)


@lru_cache(maxsize=None)
def qs_paths(p, qs, rules):
    if qs <= 0:
        return ()
    lo = 1 if rules.qs_up_to else qs
    return tuple(tuple(path) for _, path in straight_paths(p, range(8), qs, lo))


@lru_cache(maxsize=None)
def sprint_paths(p, qs, rules):
    """(dir, path) pairs for a Sprint."""
    if rules.sprint_needs_qs and qs <= 0:
        return ()
    out = straight_paths(p, ORTH, rules.sprint_orth_base + qs)
    out += straight_paths(p, DIAG, rules.sprint_diag_base + qs)
    return tuple((d, tuple(path)) for d, path in out)


def diag_step_banned(a, b, t_sq, rules):
    """Screen geometry: is the diagonal step a->b banned by a screen whose T marks t_sq?"""
    if a[0] == b[0] or a[1] == b[1]:
        return False
    if a == t_sq:
        return True
    if rules.screen_geometry == 'from_t_or_corner':
        if (a[0], b[1]) == t_sq or (b[0], a[1]) == t_sq:
            return True
    return False
