"""Rolls, shot values, contests, free throws, bands and the possession score."""
from dataclasses import dataclass
from fractions import Fraction

from . import board as B
from . import geometry as G
from . import rules_config as RC


# ---- rolls ------------------------------------------------------------------

def p_success(target, rules=RC.DEFAULT_RULES):
    """P(d20 <= target). Defaults: >= 20 always succeeds, <= 0 always fails (OQ-4)."""
    if rules.natural_rolls:                     # alternative: natural 1 succeeds, 20 fails
        t = max(1, min(19, target))
        return Fraction(t, RC.DIE)
    t = max(0, min(RC.DIE, target))
    return Fraction(t, RC.DIE)


def foul_rolls(rules, dpos, target):
    """Step 3n F2: one foul roll if the defender is closer to the rim than the ball carrier or shooter, two if
    level or further (either one fouls)."""
    if not rules.reach_angle_fouls:
        return 1
    return 1 if B.dist_rim(dpos) < B.dist_rim(target) else 2


def p_fouls(pf, rolls):
    """P(at least one of `rolls` foul rolls fouls)."""
    return 1 - (1 - pf) ** rolls


def p_foul(foul_rating, rules=RC.DEFAULT_RULES):
    """Straight foul roll: d20 <= foul rating."""
    return p_success(foul_rating, rules)


# ---- shots ------------------------------------------------------------------

def band(score):
    for name, lo in RC.BANDS:
        if lo is None or score >= lo:
            return name
    return 'Poor'


def shot_points(pos):
    return RC.ZONE_POINTS.get(B.zone(pos), 0)


def free_throws(card, points):
    mult = RC.FT_MULT_THREE if points == 3 else RC.FT_MULT_TWO
    return mult * card.r['free_throw']


def shot_rating(state, shooter, shot_type):
    """The shooter's rating for this shot: the card's, less the control rule's reduction when he is rushed (D-151)."""
    r = state.ctx.off[shooter].shot(shot_type)
    rules = state.ctx.rules
    if RC.control_size(rules) and state.rushed('O', shooter):
        r -= RC.control_cut(rules, shot_type)
    return r


def foul_on_shot_points(card, shot_type, pts, rules, rating=None, shot_value=None, left=None):
    """Points for a foul on a declared or forced shot: free throws, or under the and-one
    rule the higher of the free throws and the shot's uncontested value (rating: the shooter's rating for it when
    the control rule has reduced it, D-151).
    Under rules.fiba_fouled_shot (D-174, FIBA Articles 34 and 38) the shot is still a shot: its value as contested
    (shot_value; left: the rating the Contest leaves it, the chance in 20 that it goes in), plus the free throws the
    rules give, each at his free-throw rating: 1 if it went in, 2 or 3 (its points) if it missed. The expected value.
    Returns (points, and_one_applied)."""
    if shot_type and RC.app_rule(rules, 'fiba_fouled_shot'):
        r = card.shot(shot_type) if rating is None else rating
        if left is None:
            left = r
        if shot_value is None:
            shot_value = pts * left
            if rules.floor_declared_shot:
                shot_value = max(0, shot_value)
        # the chance it goes in is left in 20; the whole is kept a whole number, as every score is (half a point rounds up)
        left = max(0, min(RC.DIE, left))
        n = RC.DIE * shot_value + card.r['free_throw'] * (left + (RC.DIE - left) * pts)
        return int((n + RC.DIE // 2) // RC.DIE), False
    ft = free_throws(card, pts)
    if rules.and_one and shot_type:
        open_value = pts * (card.shot(shot_type) if rating is None else rating)
        if open_value > ft:
            return open_value, True
    return ft, False


def contest_rating(dcard, shot_type, dpos, spos, rules):
    c = dcard.con(shot_type)
    if B.dist_rim(dpos) > B.dist_rim(spos):
        c -= RC.FAR_CONTEST_PENALTY
    if rules.floor_contest_zero:
        c = max(0, c)
    return c


@dataclass(frozen=True)
class ContestOption:
    defender: int          # -1 = nobody contests
    contest: int
    clean: bool            # arrow on the shooter (no foul roll)
    p_foul: Fraction
    value: int             # shot value if no foul
    ft: int                # free throws if fouled
    ev: Fraction
    category: str = ''     # step 3h: front / side / behind (descriptive under the current geometry)
    rolls: int = 1         # step 3n F2: foul rolls (two when the contester is level with or further from the rim)


def contest_options(state, shooter, shot_type, forced=False):
    """Every contest choice open to the defence for this shot."""
    ctx, rules = state.ctx, state.ctx.rules
    spos = state.o[shooter]
    card = ctx.off[shooter]
    pts = shot_points(spos)
    rating = shot_rating(state, shooter, shot_type)
    ft, _ = foul_on_shot_points(card, shot_type, pts, rules, rating)
    floor = forced or rules.floor_declared_shot
    cut = RC.control_cut(rules, shot_type)
    fiba = RC.app_rule(rules, 'fiba_fouled_shot')

    def val(c):
        v = pts * (rating - c)
        return max(0, v) if floor else v

    opts = [ContestOption(-1, 0, True, Fraction(0), val(0), ft, Fraction(val(0)))]
    for j, xp in enumerate(state.x):
        if not B.adjacent(xp, spos):
            continue
        eligible, foul_roll, penalty, cat = G.terms(rules, xp, G.stance(rules, state.arrows[j], any(b[1] == j for b in state.beaten)), spos)
        if not eligible:
            continue                    # step 3h geometries: arrow lines off the shooter, no contest
        if rules.late_closeout and state.react_moved >> j & 1:
            eligible, foul_roll, penalty, cat = G.late(rules, True, shot_type, (eligible, foul_roll, penalty, cat))
            c = ctx.dfn[j].con(shot_type) - (RC.FAR_CONTEST_PENALTY if penalty else 0)
            if rules.floor_contest_zero:
                c = max(0, c)
        elif rules.contest_geometry == 'current':
            c = contest_rating(ctx.dfn[j], shot_type, xp, spos, rules)
        else:
            c = ctx.dfn[j].con(shot_type) - (RC.FAR_CONTEST_PENALTY if penalty else 0)
            if rules.floor_contest_zero:
                c = max(0, c)
        if cut and state.rushed('X', j):
            # D-151, D-154: a rushed Contest: the rating reduced; its foul rolls are today's for its position
            c -= cut
            if rules.floor_contest_zero:
                c = max(0, c)
        clean = not foul_roll
        rolls = foul_rolls(rules, xp, spos)
        pf = Fraction(0) if clean else p_fouls(p_foul(ctx.dfn[j].r['foul_contest'], rules), rolls)
        v = val(c)
        ftj = foul_on_shot_points(card, shot_type, pts, rules, rating, v, rating - c)[0] if fiba else ft     # D-174
        ev = pf * ftj + (1 - pf) * v
        opts.append(ContestOption(j, c, clean, pf, v, ftj, ev, cat, rolls if not clean else 0))
    return opts


def choose_contest(state, shooter, shot_type, forced=False):
    opts = contest_options(state, shooter, shot_type, forced)
    rules = state.ctx.rules
    if rules.contest_choice == 'nearest':
        spos = state.o[shooter]
        adj = [o for o in opts if o.defender >= 0]
        if adj:
            d2 = lambda o: (state.x[o.defender][0] - spos[0]) ** 2 + (state.x[o.defender][1] - spos[1]) ** 2
            best = min(d2(o) for o in adj)
            opts = [o for o in adj if d2(o) == best]
    return min(opts, key=lambda o: (o.ev, not o.clean, o.defender))


def shot_ev(state, shooter, shot_type, forced=False):
    """Expected value of a shot taken now against the defence's best contest."""
    return choose_contest(state, shooter, shot_type, forced).ev


# ---- possession score -------------------------------------------------------

@dataclass(frozen=True)
class Score:
    shot_value: int
    free_throws: int
    bonus: int
    turnovers: int
    turnover_points: int
    coach_bonus: int
    total: int
    band: str
    look: int               # shot value, or free throws if fouled (what the goal/bonus judge)
    goal_met: bool          # scenario goal: a look of 30+
    late_clock: str         # 'win' / 'tie' / 'loss' on Two or Three, else ''
    detail: str

    def __str__(self):
        parts = [f'total {self.total} ({self.band})', f'shot value {self.shot_value}']
        if self.free_throws:
            parts.append(f'free throws {self.free_throws}')
        if self.bonus:
            parts.append(f'foul bonus +{self.bonus}')
        if self.turnovers:
            parts.append(f'turnovers {self.turnovers} ({self.turnover_points})')
        if self.coach_bonus:
            parts.append(f"coach's call +{self.coach_bonus}")
        if self.late_clock:
            parts.append(f'late clock: {self.late_clock}')
        parts.append(f'goal {"met" if self.goal_met else "missed"}')
        return ', '.join(parts) + (f'. {self.detail}' if self.detail else '')


def is_terminal(state):
    return state.stage == 'over'


def score(state):
    """Final possession score with a breakdown. Works on terminal states."""
    ctx, rules = state.ctx, state.ctx.rules
    r = state.result
    sv = ft = 0
    detail = ''
    pts = r.points if r else 0
    if r:
        sv, ft = r.shot_value, r.free_throws
        if ctx.three_only and pts != 3:
            if sv or ft:
                detail = 'Need a Three: only a three-point shot scores'
            sv = 0
            if not rules.three_only_ft_on_twos:
                ft = 0
        if r.kind in ('shot', 'forced', 'free_throws'):
            who = f'O{r.shooter + 1} {r.shot_type}'
            if r.kind == 'free_throws':
                how = 'and-one, scores the open shot' if r.and_one else 'free throws'
                if RC.app_rule(rules, 'fiba_fouled_shot') and r.shot_type:
                    how = 'the shot as contested plus the free throws that follow (1 if it went in, its points if it missed), on average'
                detail = (detail + '. ' if detail else '') + f'{who}: fouled, {how} {r.free_throws}'
            else:
                cby = f'X{r.contester + 1}' if r.contester >= 0 else 'nobody'
                detail = (detail + '. ' if detail else '') + f'{who} {r.points} x ({r.rating} - {r.contest}) contested by {cby}'
            if RC.control_size(rules):
                # D-151: name a rushed shot and a late closeout in plain words
                last = lambda side, i: 'Sprint' if state.rush(side, i) == RC.RUSH_SPRINT else 'Quick Step'
                if state.rushed('O', r.shooter):
                    detail += f'. A rushed {r.shot_type} off his {last("O", r.shooter)}: {RC.control_size(rules)} lower'
                if r.contester >= 0 and state.rushed('X', r.contester):
                    detail += (f". A late closeout after X{r.contester + 1}'s {last('X', r.contester)}: his Contest is "
                               f'{RC.control_size(rules)} lower')
        elif r.kind == 'steal':
            detail = 'stolen after the shot was declared'
        elif r.kind == 'turnover_end':
            detail = 'turnover ended the possession'
            if r.violation == 'three_seconds':
                detail = f'three seconds: O{r.violator + 1} was in the key when two phases in a row ended'
            elif r.violation == 'closely_guarded':
                detail = f'closely guarded: O{r.violator + 1} held the ball with a defender on him when three phases in a row ended'
    look = ft if (r and r.kind == 'free_throws') else sv
    bonus = RC.STEAL_FOUL_BONUS * state.bonus5
    tpts = RC.TURNOVER_POINTS * state.tos
    coach = 0
    if ctx.coach_call and r and r.shooter >= 0 and r.shooter == state.target and r.kind in ('shot', 'forced', 'free_throws'):
        if r.kind != 'forced' or rules.coach_bonus_on_forced:
            coach = RC.COACH_BONUS[band(look)]
    total = sv + ft + bonus + tpts + coach
    if state.zeroed:
        total = r.floor if (r is not None and rules.turnover_floor) else 0     # D-82: never better than banked
    late = ''
    if ctx.two_or_three:
        if r and look >= RC.SCENARIO_GOAL and pts == 3:
            late = 'win'
        elif r and look >= RC.SCENARIO_GOAL and pts == 2:
            late = 'tie'
        else:
            late = 'loss'
    goal = bool(r) and look >= RC.SCENARIO_GOAL and not state.zeroed
    return Score(sv, ft, bonus, state.tos, tpts, coach, total, band(total), look, goal, late, detail)


def late_clock_key(sc):
    """Head-to-head ranking for Late Clock cards: result first, then shot value."""
    return ({'win': 2, 'tie': 1, 'loss': 0}.get(sc.late_clock, 0), sc.look)


# ---- match --------------------------------------------------------------------

def tiebreak_probability(rating, contest, rules=RC.DEFAULT_RULES):
    """P(make) for the match tiebreaker roll: d20 <= rating - contest."""
    return p_success(rating - contest, rules)


def match_result(total_a, total_b, final_a=None, final_b=None, rules=RC.DEFAULT_RULES):
    """Winner of a two-possession match. On a tie, final_x = (rating, contest) of each
    player's final shot; returns {'A': p, 'B': p, 'tie': p} (a make beats a miss; both
    make or both miss stays tied)."""
    if total_a != total_b:
        return {'A': Fraction(int(total_a > total_b)), 'B': Fraction(int(total_b > total_a)), 'tie': Fraction(0)}
    pa = tiebreak_probability(*final_a, rules)
    pb = tiebreak_probability(*final_b, rules)
    return {'A': pa * (1 - pb), 'B': pb * (1 - pa), 'tie': pa * pb + (1 - pa) * (1 - pb)}
