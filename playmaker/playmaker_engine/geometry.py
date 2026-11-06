"""Arrow lines and contest position (step 3h): one helper for every rule that reads a defender's arrow.

Two settings (rules_config): arrow_mode 'single' | 'wedge', contest_geometry 'current' | 'wedge_mirror'
| 'rim_distance'. With the defaults ('single', 'current') every function here answers exactly as the
engine did before, and the engine's callers keep their original code paths for that case.

A wedge with arrow index a has two lines, directions a and a+1 (clockwise, 45 degrees apart), so there
are 8 orientations, as with a single arrow.
"""
import math

from . import board as B
from . import rules_config as RC

FRONT, SIDE, BEHIND = 'front', 'side', 'behind'


def lines(rules, a):
    """The arrow-line directions for arrow index a."""
    if rules.arrow_mode == 'wedge':
        return (a, (a + 1) % 8)
    return (a,)


def faces(rules, a, frm, to):
    """Does the defender at frm (arrow a) have the adjacent square `to` on one of his lines?"""
    if not B.adjacent(frm, to):
        return False
    return B.dir_between(frm, to) in lines(rules, a)


def crosses(rules, pos, a, p, q):
    """Does either arrow line strictly cross segment pq (a pass line)?"""
    return any(B.arrow_crosses(pos, d, p, q) for d in lines(rules, a))


def path_crosses(rules, pts, pos, a, strict):
    """Does a movement path cross either arrow line (a drive past an adjacent defender)?"""
    return any(B.path_crosses_ray(pts, pos, d, strict=strict) for d in lines(rules, a))


def sprint_arrows(rules, run_dir):
    """Arrow indices a Sprint in direction run_dir can end with: one edge is the run direction; with a
    wedge the defender chooses the side of the other (a = run_dir, lines run_dir and run_dir+1, or
    a = run_dir-1, lines run_dir-1 and run_dir)."""
    if rules.arrow_mode == 'wedge':
        return (run_dir, (run_dir - 1) % 8)
    return (run_dir,)


def _compass(v):
    """Compass angle in degrees, clockwise from north (y up), of vector v."""
    return math.degrees(math.atan2(v[0], v[1])) % 360.0


def _in_sector(theta, start_dir, eps=1e-9):
    """Is compass angle theta within the 45-degree sector from direction start_dir clockwise to
    start_dir+1, edges included?"""
    lo = start_dir * 45.0
    d = (theta - lo) % 360.0
    return d <= 45.0 + eps or d >= 360.0 - eps


def category(rules, dpos, a, spos):
    """Front, Side or Behind for a contest from dpos (arrow a) on a shooter at spos, by the active
    geometry. Under 'current' this is descriptive only (by rim distance, as the -3 rule measures it)."""
    g = rules.contest_geometry
    if g == 'wedge_mirror':
        v = (RC.RIM[0] - dpos[0], RC.RIM[1] - dpos[1])
        if v == (0, 0):
            return FRONT                  # standing on the rim square: between shooter and basket
        th = _compass(v)
        if _in_sector(th, (a + 4) % 8):    # the wedge mirrored backwards holds the rim
            return FRONT
        if _in_sector(th, a):              # the forward wedge holds the rim
            return BEHIND
        return SIDE
    dd, ds = B.dist_rim(dpos), B.dist_rim(spos)
    return FRONT if dd < ds else SIDE if dd == ds else BEHIND


def terms(rules, dpos, a, spos):
    """How a defender at dpos with arrow a contests a shooter at spos (adjacent):
    (eligible, foul_roll, penalty, category). Under 'current' every adjacent defender is eligible, a
    foul roll means the arrow is off the shooter, and the -3 is for being further from the rim. Under
    the new geometries facing gates the contest, Side and Behind roll for a foul, Behind takes the -3."""
    on = faces(rules, a, dpos, spos)
    cat = category(rules, dpos, a, spos)
    if rules.contest_geometry == 'current':
        return True, not on, B.dist_rim(dpos) > B.dist_rim(spos), cat
    if not on:
        return False, False, False, cat
    return True, cat != FRONT, cat == BEHIND, cat


def best_terms(rules, dpos, arrows, spos):
    """The defence's best way to contest from dpos when the defender may end with any of `arrows`
    (None = any arrow, a Move was used). Returns (eligible, foul_roll, penalty, category, arrow) or None.
    Best = eligible first, then no foul roll, then no penalty."""
    cands = range(8) if arrows is None else arrows
    best = None
    for a in cands:
        t = terms(rules, dpos, a, spos)
        if not t[0]:
            continue
        key = (t[1], t[2])
        if best is None or key < best[0]:
            best = (key, t + (a,))
    return best[1] if best else None


def new_geometry(rules):
    return rules.contest_geometry != 'current'


def check(rules):
    if rules.contest_geometry == 'wedge_mirror' and rules.arrow_mode != 'wedge':
        raise ValueError("contest_geometry 'wedge_mirror' needs arrow_mode 'wedge'")


LATE_RIM = ('layup', 'dunk', 'post', 'floater')


def late(rules, moved, shot_type, t):
    """Step 3i rule test (late_closeout): a contester who moved square in the reaction is late. At the rim,
    post or floater he contests with a foul roll; on a mid-range, long two or three with the -3 and no
    foul roll. One who was already adjacent (and only turns) is set, and contests as before. t is
    (eligible, foul_roll, penalty, category); returns it adjusted. The -3 is applied once."""
    if not rules.late_closeout or not moved or not t[0]:
        return t
    if shot_type in LATE_RIM:
        return (t[0], True, t[2], t[3])
    return (t[0], False, True, t[3])
