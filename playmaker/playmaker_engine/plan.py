"""Step 24 (Shaun, 19 Nov 2026; docs/reference/SETUP_PLAN_BLUEPRINT.md): the setup plan.

The order: the scout for both teams; each team's shot tolerance and matchup preferences; the offence's plan; the
offence's placement; then the defence's setup. Each side thinks alone: everything here is built from public
information (the board, the rules, all ten cards) and the side's own predictions. Nothing here reads the other side's
goals or plan.

Stage 1a, the shot review: every attacker, every shot type the rules allow, against every defender, in every case the
contest rules tell apart (D-191, D-193, D-194, D-198): 14 cases for a jump shot, 22 for an inside shot. Each case's
value is the points times the chance, on the game's scale (points times the rating, in twentieths).
"""
from fractions import Fraction

from . import board as B
from . import rules_config as RC
from .scoring import p_foul, p_fouls, foul_on_shot_points

INSIDE = tuple(t for shots in RC.ZONE_SHOTS.values() for t in shots if t not in RC.JUMP_SHOTS)
SHOT_ZONE = {t: z for z, shots in RC.ZONE_SHOTS.items() for t in shots}
ZONE_NAMES = {'K': 'the green zone', 'M': 'mid-range', 'L': 'the long two', '3': 'the three-point line'}
SHOT_WORDS = {'layup': 'layup', 'dunk': 'dunk', 'post': 'post shot', 'floater': 'floater', 'mid': 'mid-range shot',
              'long': 'long two', 'three': 'three'}

# The defender's cases when the shot goes up (the blueprint's table). where: 'square' (in front, his arrow on the
# shooter), 'side' (in front with the arrow off, or beside), 'behind'. how: 'hand' (the automatic contest: no action,
# never a foul) or 'block' (the Contest action on an inside shot: it rolls for a foul).
JUMP_CASES = (('open', None, None), ('square', 'hand', False), ('square', 'hand', True), ('side', 'hand', False),
              ('side', 'hand', True), ('behind', 'hand', False), ('behind', 'hand', True))
INSIDE_CASES = (('open', None, None), ('square', 'hand', False), ('square', 'hand', True),
                ('side', 'hand', False), ('side', 'block', False), ('side', 'hand', True), ('side', 'block', True),
                ('behind', 'hand', False), ('behind', 'block', False), ('behind', 'hand', True), ('behind', 'block', True))


def cases_for(shot_type):
    """The defender cases the rules tell apart for this shot: 7 for a jump shot, 11 for an inside shot. Each is taken
    for both shooter states (set, rushed): 14 and 22."""
    return JUMP_CASES if shot_type in RC.JUMP_SHOTS else INSIDE_CASES


def _plus5(rules, hold_for_one=False):
    return RC.STEAL_FOUL_BONUS if (RC.app_rule(rules, 'points_play_on') and not hold_for_one) else 0


def contest_left(dcard, shot_type, where, how, d_rushed, rules):
    """What the defender's contest takes off the shooter's rating in this case (D-194's one table; D-193's floor)."""
    cut = RC.control_cut(rules, shot_type)
    c = dcard.con(shot_type)
    if how == 'hand':
        if where != 'square':
            c -= RC.SOFT_CONTEST                         # in front with the arrow off, or beside: 3 less
        if where == 'behind':
            c -= RC.FAR_CONTEST_PENALTY                  # behind: 3 less again
    else:                                                # the block: the full rating; from behind 3 less
        if where == 'behind':
            c -= RC.FAR_CONTEST_PENALTY
        if rules.floor_contest_zero:
            c = max(0, c)
    if d_rushed and cut:
        c -= cut                                         # a rushed contest: 2 less (D-151)
        if how == 'block' and rules.floor_contest_zero:
            c = max(0, c)
    return max(RC.CONTEST_FLOOR, c)                      # D-193: every contest takes at least 1


def case_value(ocard, dcard, shot_type, where, how, s_rushed, d_rushed, rules, front=True, hold_for_one=False):
    """One case's value: the points times the chance, on the game's scale. front (the block from 'side' only): the
    defender is nearer the rim than the shooter (one foul roll) or level with him (two). -> dict(value, left, contest,
    foul, rolls)."""
    pts = RC.ZONE_POINTS[SHOT_ZONE[shot_type]]
    rating = ocard.shot(shot_type) - (RC.control_cut(rules, shot_type) if s_rushed else 0)
    floor = rules.floor_declared_shot
    if where == 'open':
        v = pts * rating
        return dict(value=Fraction(max(0, v) if floor else v), left=rating, contest=0, foul=Fraction(0), rolls=0)
    c = contest_left(dcard, shot_type, where, how, d_rushed, rules)
    v = pts * (rating - c)
    if floor:
        v = max(0, v)
    if how == 'hand':
        return dict(value=Fraction(v), left=rating - c, contest=c, foul=Fraction(0), rolls=0)
    rolls = (1 if (where == 'side' and front) else 2) if rules.reach_angle_fouls else 1
    pf = Fraction(p_fouls(p_foul(dcard.r['foul_contest'], rules), rolls))
    if RC.app_rule(rules, 'fiba_fouled_shot'):
        ft = foul_on_shot_points(ocard, shot_type, pts, rules, rating, v, rating - c)[0]
    else:
        ft = foul_on_shot_points(ocard, shot_type, pts, rules, rating if s_rushed else None)[0]
    ft += _plus5(rules, hold_for_one)                    # D-198: a shooting foul is +5 and its free throws
    return dict(value=pf * ft + (1 - pf) * v, left=rating - c, contest=c, foul=pf, rolls=rolls)


def shot_review(ocard, dcard, shot_type, rules, hold_for_one=False):
    """Every case of one attacker's shot against one defender: [dict(shooter: 'set' | 'rushed', where, how,
    defender: 'set' | 'rushed' | None, value, left, contest, foul, rolls, front)]: 14 rows for a jump shot, 22 for an
    inside shot. The block from the side is listed at its better value for the defence of in front (one foul roll)
    and beside (two), with both kept (value_front, value_beside)."""
    rows = []
    for s_rushed in (False, True):
        for where, how, d_rushed in cases_for(shot_type):
            r = case_value(ocard, dcard, shot_type, where, how, s_rushed, bool(d_rushed), rules, True, hold_for_one)
            row = dict(shooter='rushed' if s_rushed else 'set', where=where, how=how,
                       defender=None if where == 'open' else ('rushed' if d_rushed else 'set'), **r)
            if where == 'side' and how == 'block':
                b = case_value(ocard, dcard, shot_type, where, how, s_rushed, bool(d_rushed), rules, False, hold_for_one)
                row.update(value_front=r['value'], value_beside=b['value'], rolls_beside=b['rolls'])
            rows.append(row)
    return rows


def best_contest(rows, shooter='set', where=None, defender='set'):
    """The defence's best contest among the rows of a place (where) and state: the lowest value (only the best contest
    counts)."""
    pick = [r for r in rows if r['shooter'] == shooter and (where is None or r['where'] == where)
            and (r['defender'] in (None, defender))]
    return min(pick, key=lambda r: r['value']) if pick else None
