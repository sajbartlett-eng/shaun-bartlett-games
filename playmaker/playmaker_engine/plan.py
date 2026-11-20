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
ZONES = tuple(z for z, shots in RC.ZONE_SHOTS.items() if shots)      # the zones a shot may go up from
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


# D-271 (step 29): the block replaces the hard Contest, on every shot and from every position, the square one too.
BLOCK_CASES = (('open', None, None), ('square', 'hand', False), ('square', 'hand', True), ('square', 'block', False),
               ('square', 'block', True), ('side', 'hand', False), ('side', 'block', False), ('side', 'hand', True),
               ('side', 'block', True), ('behind', 'hand', False), ('behind', 'block', False), ('behind', 'hand', True),
               ('behind', 'block', True))


def cases_for(shot_type, rules=None):
    """The defender cases the rules tell apart for this shot: 7 for a jump shot, 11 for an inside shot. Each is taken
    for both shooter states (set, rushed): 14 and 22. Under the block (D-271): 13 for every shot, 26 with both states."""
    if rules is not None and RC.block_rule(rules):
        return BLOCK_CASES
    return JUMP_CASES if shot_type in RC.JUMP_SHOTS else INSIDE_CASES


def block_left(dcard, where, d_rushed, rules, shot_type):
    """D-271: the Block roll in this case: his Block, less 3 from the side, 6 from behind, the rushed cut, at least 1."""
    b = dcard.r['block'] - {'square': 0, 'side': RC.BLOCK_SIDE, 'behind': RC.BLOCK_BEHIND}[where]
    if d_rushed:
        b -= RC.control_cut(rules, shot_type)
    return max(RC.CONTEST_FLOOR, b)


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
    block = RC.block_rule(rules)
    rolls = (1 if (where == 'side' and front) else 2) if rules.reach_angle_fouls else 1
    if block and where == 'square':
        rolls = 0                                        # D-271: square, his arrow on the shooter: no foul roll
    pf = Fraction(p_fouls(p_foul(dcard.r['foul_block' if block else 'foul_contest'], rules), rolls)) if rolls else Fraction(0)
    if RC.app_rule(rules, 'fiba_fouled_shot'):
        ft = foul_on_shot_points(ocard, shot_type, pts, rules, rating, v, rating - c)[0]
    else:
        ft = foul_on_shot_points(ocard, shot_type, pts, rules, rating if s_rushed else None)[0]
    ft += _plus5(rules, hold_for_one)                    # D-198: a shooting foul is +5 and its free throws
    if block:
        # D-271: with no foul, the Block roll (a turnover at -5), else the shot against the contest
        b = block_left(dcard, where, d_rushed, rules, shot_type)
        pb = Fraction(min(max(b, 0), RC.DIE), RC.DIE)
        return dict(value=pf * ft + (1 - pf) * (pb * RC.TURNOVER_POINTS + (1 - pb) * v), left=rating - c, contest=c,
                    foul=pf, rolls=rolls, block=b, p_block=pb)
    return dict(value=pf * ft + (1 - pf) * v, left=rating - c, contest=c, foul=pf, rolls=rolls)


def shot_review(ocard, dcard, shot_type, rules, hold_for_one=False):
    """Every case of one attacker's shot against one defender: [dict(shooter: 'set' | 'rushed', where, how,
    defender: 'set' | 'rushed' | None, value, left, contest, foul, rolls, front)]: 14 rows for a jump shot, 22 for an
    inside shot. The block from the side is listed at its better value for the defence of in front (one foul roll)
    and beside (two), with both kept (value_front, value_beside)."""
    rows = []
    for s_rushed in (False, True):
        for where, how, d_rushed in cases_for(shot_type, rules):
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


# ---- stage 1: the scout (cached a game at a time: the cards don't change) ------------------------------------------------

OFF_COURT = (-1, 1)


def _leaves(node, pr=1.0):
    from .resolve import ChanceNode
    if isinstance(node, ChanceNode):
        for z in node.outcomes:
            yield from _leaves(z[2], pr * float(z[0]))
    else:
        yield pr, node


class Scout:
    """One team's own scout: its offence's table and its defence's table are the same public facts (the rules and all
    ten cards), held by the side that reads them. Nothing of the other side's is ever in here."""

    def __init__(self, ctx, side):
        self.ctx, self.side, self.rules = ctx, side, ctx.rules
        self.off, self.dfn = ctx.off, ctx.dfn
        self._shots, self._beat, self._base = {}, {}, None
        # Step 25 (D-245, Shaun: "If a computer gets its prediction wrong, its setup still stands. It adapts its strategy
        # on the fly."): no prediction is carried from one possession to the next. Each possession predicts fresh from
        # what it can see; in play the computer re-reads the actual board every phase.

    # -- 1a: the shot review
    def shots(self, a, d, t):
        key = (a, d, t)
        if key not in self._shots:
            self._shots[key] = shot_review(self.off[a], self.dfn[d], t, self.rules, self.ctx.hold_for_one)
        return self._shots[key]

    def open_value(self, a, zone, rushed=False):
        """Attacker a's best open shot in a zone: (value, shot type)."""
        return max((float(self.shots(a, 0, t)[7 if (rushed and t in RC.JUMP_SHOTS) else 11 if rushed else 0]['value']), t)
                   for t in RC.ZONE_SHOTS[zone])

    def contested(self, a, d, zone, where='square', shooter='set', defender='set'):
        """Attacker a's best shot in a zone with defender d there (the defence taking its best contest of each shot,
        the attacker his best shot): (value, shot type)."""
        best = None
        for t in RC.ZONE_SHOTS[zone]:
            r = best_contest(self.shots(a, d, t), shooter, where, defender)
            v = float(r['value'])
            if r.get('value_beside') is not None:
                v = float(min(r['value_front'], r['value_beside']))
            if best is None or v > best[0]:
                best = (v, t)
        return best

    def floor(self):
        """What the offence can always get: its best shot against any one defender square and set on it. A square
        where an attacker's open shot is worth no more than this holds nobody's attention."""
        return max(min(self.contested(a, d, z)[0] for d in range(5)) for a in range(5) for z in ZONES)

    # -- 1b: the movement review
    def beat_chance(self, a, d):
        """The chance attacker a's Dribble beats defender d, by the rules (Dribble against Agility)."""
        from .scoring import p_success
        return float(p_success(self.off[a].r['dribble'] - self.dfn[d].r['agility'], self.rules))

    def beat(self, base, a, d, q):
        """Where a won Dribble is worth something: attacker a with the ball on q, defender d between him and the rim
        with his arrow on him, the two of them alone. The coverage map is read before the Dribble and after a win:
        how many of his squares get better, and by how much in all (how much his options grow); and his best shot
        this phase before and after. base: any state of this game (for its context). None where no defender can
        stand between him and the rim."""
        key = (a, d, q)
        if key in self._beat:
            return self._beat[key]
        from . import agent as AG
        from .actions import legal_actions
        from .resolve import apply
        out = None
        nb = [(q[0] + dx, q[1] + dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if (dx, dy) != (0, 0)]
        nb = sorted((p for p in nb if B.on_board(p) and B.dist_rim(p) < B.dist_rim(q)), key=lambda p: (B.dist_rim(p), abs(p[0] - q[0]), p))
        if nb and AG.JS.get('coverage') is not None:
            dq = nb[0]
            s = base.with_(o=tuple(q if k == a else OFF_COURT for k in range(5)), x=tuple(dq if k == d else OFF_COURT for k in range(5)),
                           arrows=tuple(B.dir_between(dq, q) if k == d else 0 for k in range(5)), ball=a, side='O', turn_n=0)
            try:
                act = next((z for z in legal_actions(s) if z.kind == 'dribble' and z.target == d), None)
                if act is not None:
                    won = [(p, t) for p, t in _leaves(apply(s, act)) if t.stage == 'play' and t.beaten]
                    # step 25 (D-243): everything the offence threatens before the beat and after it, by the coverage
                    # map's own measure (each square's look at its value times its reach), and the difference square
                    # by square: many small gains at the top of the key, one large one in the paint, both counted
                    cb, ca = AG.coverage(s), AG.coverage(won[0][1]) if won else None
                    if cb and ca:
                        sb, sa = cb['squares'][a], ca['squares'][a]
                        w = lambda m, k: (m.get(k) or {}).get('worth', 0)
                        diffs = [w(sa, k) - w(sb, k) for k in set(sb) | set(sa)]
                        out = dict(chance=round(sum(p for p, _ in won), 3), squares=sum(1 for z in diffs if z > 0.5),
                                   grows=round(sum(diffs), 1), biggest=round(max(diffs + [0.0]), 1),
                                   before=round(sum(w(sb, k) for k in sb), 1), after=round(sum(w(sa, k) for k in sa), 1),
                                   shot_before=(cb.get('now') or {}).get('worth', 0), shot_after=(ca.get('now') or {}).get('worth', 0),
                                   defender_on=B.sq(dq))
            except ValueError:
                out = None
        self._beat[key] = out
        return out

    # -- 1c: the matchup table
    def matchup(self, a, d):
        """Attacker a against defender d: in each zone his best open shot and what d's contest leaves of it (square,
        from the side, from behind); and the chance his Dribble beats him."""
        zones = {}
        for z in ZONES:
            o = self.open_value(a, z)
            zones[z] = dict(open=o[0], shot=o[1], square=self.contested(a, d, z, 'square')[0],
                            side=self.contested(a, d, z, 'side')[0], behind=self.contested(a, d, z, 'behind')[0])
        return dict(o=a, x=d, zones=zones, beat=self.beat_chance(a, d))

    def table(self):
        return [[self.matchup(a, d) for d in range(5)] for a in range(5)]

    # -- stage 2: matchups to chase and to avoid, in preference order
    def preferences(self, bar):
        """Every attacker against every defender in every zone, by how far the shot that defender leaves (square and
        set on him) clears or misses the bar: best for the offence first. The offence chases from the top; the defence
        avoids from the top. [dict(o, x, zone, shot, value, over, beat)]."""
        rows = []
        for a in range(5):
            for d in range(5):
                for z in ZONES:
                    v, t = self.contested(a, d, z)
                    rows.append(dict(o=a, x=d, zone=z, shot=t, value=round(v, 2), over=round(v - bar, 2), beat=self.beat_chance(a, d)))
        rows.sort(key=lambda r: (-r['over'], -r['beat'], r['o'], r['x'], r['zone']))
        return rows

    # -- the candidate squares (stage 3b): where his card makes him a real look
    def candidates(self, a):
        """The squares where attacker a's open shot is worth more than the offence can always get (floor): a defender
        has to honour him there. The rest are ruled out as shooting squares."""
        f = self.floor()
        out = []
        for x in range(B.W):
            for y in range(1, B.H + 1):
                q = (x, y)
                z = B.zone(q)
                if not B.on_board(q) or z not in ZONES or q == RC.RIM:
                    continue
                if self.open_value(a, z)[0] > f + 1e-9:
                    out.append(q)
        return out


def scout_for(ctx, side):
    """This side's scout for the game (kept on the context's own cards: the cards don't change)."""
    key = (tuple(id(c) for c in ctx.off), tuple(id(c) for c in ctx.dfn), ctx.rules, side)
    hit = _SCOUTS.get(key)
    if hit is None or hit[0] is not ctx.off:
        if len(_SCOUTS) > 16:
            _SCOUTS.clear()
        hit = _SCOUTS[key] = (ctx.off, Scout(ctx, side))
    return hit[1]


_SCOUTS = {}


# ---- stage 2: shot tolerance, phase by phase ------------------------------------------------------------------------------

def bars(state):
    """The acceptable-shot bar for each phase the clock leaves (step 25, D-242): the value of playing on, counted phase
    by phase by the rules (engine.js barsOf). It barely drops early and falls faster late; in the last phase any shot
    beats none (0). [dict(phase, clock, bar)]."""
    from . import agent as AG
    if AG.JS.get('coverage') is not None:
        try:
            r = AG.coverage(state, only='bars')
            if r and r.get('bars'):
                return r['bars']
        except ValueError:
            pass
    from .decide import bars_of
    return bars_of(state)


# ---- stage 3: the offence's plan ------------------------------------------------------------------------------------------

def _and(xs):
    xs = list(xs)
    return xs[0] if len(xs) == 1 else ', '.join(xs[:-1]) + (' or ' if len(xs) > 1 else '') + xs[-1] if xs else ''


WHERE_WORDS = {'square': 'square in front', 'side': 'from the side', 'behind': 'from behind'}


def acceptance(scout, a, shot_type, bar):
    """The acceptance spec of a shot: which of the scout's cases leave it at or above the bar. Never written by hand.
    -> dict(open, rushed_open, by: {defender: [accepted (where, defender state)]}, refused: [defenders with no accepted
    contest], words)."""
    rows0 = scout.shots(a, 0, shot_type)
    val = lambda rs, sh, wh=None, df=None: min(float(r['value']) for r in rs if r['shooter'] == sh and r['where'] == (wh or 'open') and r['defender'] == df)
    open_ok, rushed_ok = val(rows0, 'set') >= bar, val(rows0, 'rushed') >= bar
    by, refused = {}, []
    for d in range(5):
        rs = scout.shots(a, d, shot_type)
        ok = [(wh, df) for wh in ('square', 'side', 'behind') for df in ('set', 'rushed') if val(rs, 'set', wh, df) >= bar]
        if ok:
            by[d] = ok
        else:
            refused.append(d)
    name = SHOT_WORDS[shot_type]
    art = 'an' if name[0] in 'aeiou' else 'a'
    parts = [f"open {'accepted' if open_ok else 'not accepted'}", f"rushed open {'accepted' if rushed_ok else 'not accepted'}"]
    for d, ok in sorted(by.items()):
        if len(ok) == 6:
            parts.append(f'contested by X{d + 1} accepted')
        else:
            wheres = []
            for wh in ('square', 'side', 'behind'):
                st = [df for w2, df in ok if w2 == wh]
                if st:
                    wheres.append(WHERE_WORDS[wh] + ('' if len(st) == 2 else ' (only if he is rushed)' if st == ['rushed'] else ''))
            parts.append(f"contested by X{d + 1} {' or '.join(wheres)} accepted, otherwise not")
    if refused:
        parts.append(f"contested by {_and(f'X{d + 1}' for d in refused)} not accepted")
    words = f"Create {art} {name} for O{a + 1}: " + '; '.join(parts) + '.'
    return dict(o=a, shot=shot_type, bar=round(bar, 2), open=open_ok, rushed_open=rushed_ok,
                by={d: [list(z) for z in ok] for d, ok in by.items()}, refused=refused, words=words)


def _look_words(lk):
    name = SHOT_WORDS.get(lk['shot'], lk['shot'])
    return f"O{lk['o'] + 1}'s {name} on {lk['sq']}"


def screen_roles(state):
    """Stage 3b: can a screen on the ball handler's defender build something? For each defender next to the ball
    handler, each teammate is tried on each free square next to that defender, setting the Screen the rules allow
    there; the map is read with the screen standing. -> the screens that leave more than the board as it is, best
    first: [dict(o, x, sq, value, gain, squares: every square that screener could set it from, left: the look it
    frees)]. Found by reading the map, never named."""
    from . import agent as AG
    from .actions import legal_actions
    from .resolve import apply, ChanceNode
    if AG.JS.get('coverage') is None or state.stage != 'play':
        return []
    bh = state.o[state.ball]
    walls = [d for d, q in enumerate(state.x) if B.on_board(q) and B.adjacent(q, bh)]
    # step 25: off-ball screens too (condition 23): on any defender within reach of a teammate this phase
    others = [d for d, q in enumerate(state.x) if B.on_board(q) and d not in walls
              and any(k != state.ball and B.cheb(q, p) <= 3 for k, p in enumerate(state.o) if B.on_board(p))]
    s0 = state.with_(side='O', turn_n=0)
    try:
        # step 27 (audit): judged by the one list (D-219), as the search and the setups are, not by the lasting gap
        # alone with a fixed half-point margin: a screen builds more when the list reads better with it standing
        base_k = list_key(AG.coverage(s0, only='lasting'))
        base = float((base_k[0] or (0,))[0])
        cov0 = AG.coverage(s0)
    except (ValueError, TypeError):
        return []
    paint0 = [max((v.get('worth', 0) for k, v in (sq or {}).items() if B.zone(B.parse_sq(k)) == 'K'), default=0)
              for sq in (cov0.get('squares') or [{}] * 5)]
    taken = set(state.o) | set(state.x)
    found = {}
    for d in walls + others:
        xq = state.x[d]
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                q = (xq[0] + dx, xq[1] + dy)
                if (dx, dy) == (0, 0) or not B.on_board(q) or q in taken:
                    continue
                for k in range(5):
                    if k == state.ball:
                        continue
                    st = s0.with_(o=tuple(q if i == k else p for i, p in enumerate(s0.o)))
                    try:
                        act = next((a for a in legal_actions(st) if a.kind == 'screen' and a.piece == k and a.target == B.dir_between(q, xq)), None)
                        if act is None:
                            continue
                        after = apply(st, act)
                        if isinstance(after, ChanceNode) or after.stage != 'play':
                            continue
                        r = AG.coverage(after, only='lasting')
                    except ValueError:
                        continue
                    if not r:
                        continue
                    kr = list_key(r)
                    if kr > base_k:
                        top = float((kr[0] or (0,))[0])
                        row = found.setdefault((k, d), dict(o=k, x=d, sq=B.sq(q), value=top, gain=round(top - base, 2), key=kr, squares=[], state=after))
                        row['squares'].append(B.sq(q))
                        if kr > row['key']:
                            row.update(sq=B.sq(q), value=top, gain=round(top - base, 2), key=kr, state=after)
    out = sorted(found.values(), key=lambda z: (z['key'], -z['o'], -z['x']), reverse=True)
    for z in out:
        z['list'] = list(z.pop('key')[0][:8])        # the list with the screen standing (its first items), best first
    for z in out[:3]:
        try:
            c = AG.coverage(z['state'])
            z['left'] = c.get('left') if c else None
            # who the screen frees to the rim: an attacker other than the screener whose best look in the paint rises
            dive = None
            for k2, sq in enumerate(c.get('squares') or []):
                if k2 in (z['o'], state.ball) or not sq:
                    continue
                pk = [(v.get('worth', 0), q) for q, v in sq.items() if B.zone(B.parse_sq(q)) == 'K']
                if pk:
                    w, q = max(pk)
                    if w > paint0[k2] + 0.5 and (dive is None or w > dive['worth']):
                        dive = dict(o=k2, sq=q, worth=w, before=paint0[k2])
            z['dive'] = dive
            z['on_ball'] = z['x'] in walls
        except ValueError:
            z['left'] = None
    for z in out:
        z.pop('state', None)
        z['squares'] = sorted(set(z['squares']))
    return out


def read_plan(state, scout, perm=None, deep=False):
    """The offence's plan on a board (its own placement against the defence it predicts, or the real board in play):
    read from the coverage map, one phase ahead (the defence's setup and its first answer). The first preference is
    the look left after the defence's best answer, at its real chance; the backups are the next attackers' best
    looks; the conditions are the defenders who could take it away and what holds each; the branch is what opens if
    the condition fails (the map read again with that defender on the target). Nothing names a play."""
    from . import agent as AG
    if AG.JS.get('coverage') is None:
        return None
    try:
        cov = AG.coverage(state)
    except ValueError:
        return None
    if not cov or not cov.get('left'):
        return None
    tol = bars(state)
    bar_next = tol[1]['bar'] if len(tol) > 1 else 0.0
    left = cov['left']
    a = left['o']
    spec = acceptance(scout, a, left['shot'], bar_next)
    # backups: the other attackers' best looks, best first
    backups = []
    for o2 in range(5):
        if o2 == a:
            continue
        sqs = (cov.get('squares') or [{}] * 5)[o2] or {}
        if not sqs:
            continue
        q2, lk = max(sqs.items(), key=lambda kv: (kv[1].get('worth', 0), kv[0]))
        if lk.get('worth', 0) > 0:
            backups.append(dict(o=o2, sq=q2, shot=lk['shot'], open=lk['value'], reach=lk['reach'], worth=lk['worth'], cover=lk.get('cover', -1)))
    backups.sort(key=lambda z: (-z['worth'], z['o']))
    backups = backups[:2]
    for bk in backups:
        bk['spec'] = acceptance(scout, bk['o'], bk['shot'], bar_next)
    # conditions: the defender who covers the target, and what pulls him (an overload: he is the only cover of two looks)
    conds, roles = [], [dict(o=a, role='shooter', sq=left['sq'])]
    cover = left.get('cover', -1)
    pull = None
    for ov in cov.get('overloads') or []:
        th = ov.get('threats') or []
        if any(t['o'] == a and t['sq'] == left['sq'] for t in th) or (cover in (ov.get('xs') or []) and any(t['o'] == a for t in th)):
            others = [t for t in th if t['o'] != a]
            if others:
                pull = (ov, others[0])
                break
    if pull:
        ov, other = pull
        xs = _and(f'X{d + 1}' for d in ov['xs'])
        conds.append(dict(kind='attention', x=list(ov['xs']), o=other['o'], text=f"{xs} drawn to {_look_words(other)}"))
        roles.append(dict(o=other['o'], role='draws ' + xs, sq=other['sq']))
    elif cover >= 0:
        conds.append(dict(kind='attention', x=[cover], o=a, text=f"X{cover + 1} a step late to {left['sq']}"))
    if a != state.ball:
        ch = (cov.get('passes') or [None] * 5)[a]
        conds.append(dict(kind='access', x=[], o=state.ball, chance=ch,
                          text=f"the pass from O{state.ball + 1} to O{a + 1} arrives" + (f' ({round(100 * ch)} in 100)' if ch is not None else '')))
        roles.append(dict(o=state.ball, role='passer', sq=B.sq(state.o[state.ball])))
    elif left.get('reach', 1) < 1:
        conds.append(dict(kind='access', x=[], o=a, chance=left['reach'],
                          text=f"O{a + 1} beats his man off the dribble ({round(100 * left['reach'])} in 100)"))
    # the branch: the condition fails (the covering defender stays home on the target): what does that open?
    branch = None
    if cover >= 0 and B.parse_sq(left['sq']) not in state.x and B.parse_sq(left['sq']) not in state.o:
        try:
            home = state.with_(x=tuple(B.parse_sq(left['sq']) if k == cover else q for k, q in enumerate(state.x)))
            c2 = AG.coverage(home)
            if c2 and c2.get('left'):
                b = c2['left']
                branch = dict(o=b['o'], sq=b['sq'], shot=b['shot'], worth=b['worth'], reach=b['reach'],
                              when=f"X{cover + 1} stays home on {left['sq']}", text=f"If X{cover + 1} stays home: {_look_words(b)}")
        except ValueError:
            branch = None
    # attention, holes, access
    held = []
    try:
        ro = AG.coverage(state, only='roles', **(dict(prev=list(perm), fixed=True) if perm else {}))
    except ValueError:
        ro = None
    idle = []
    for r in (ro or {}).get('roles') or []:
        if r['kind'] in ('man', 'both', 'chase'):
            held.append((r['x'], r['man']))
        elif r['kind'] == 'free' and not r.get('way'):
            idle.append(r['x'])
    att = '; '.join(f"O{o + 1} holds X{x + 1}" for x, o in held[:3]) or 'nobody is held'
    access = (f"the pass to O{a + 1}" if a != state.ball else f"O{a + 1}'s own step with the ball")
    line = f"Attention: {att}. Hole: {left['sq']}, {ZONE_NAMES.get(B.zone(B.parse_sq(left['sq'])), '')}. Access: {access}."
    name = SHOT_WORDS.get(left['shot'], left['shot'])
    art = 'an open' if left.get('cover', -1) < 0 else 'an' if name[0] in 'aeiou' else 'a'
    target = f"Plan: {art} {name} for O{a + 1} on {left['sq']}"
    # a screen on the ball handler's defender, where one builds more than the board as it is (read at setup: deep)
    screens = screen_roles(state) if deep else []
    first = dict(o=a, sq=left['sq'], shot=left['shot'], open=left['value'], reach=left['reach'], worth=left['worth'], cover=cover)
    value = float(cov.get('lasting') or 0)
    if screens and screens[0].get('left'):
        sc0, lk = screens[0], screens[0]['left']
        nm = SHOT_WORDS.get(lk['shot'], lk['shot'])
        base_words = _look_words(left)
        art2 = 'an open' if lk.get('cover', -1) < 0 else 'an' if nm[0] in 'aeiou' else 'a'
        how = (f"after he screens X{sc0['x'] + 1} and rolls" if lk['o'] == sc0['o'] else f"off O{sc0['o'] + 1}'s screen on X{sc0['x'] + 1}")
        target = f"Plan: {art2} {nm} for O{lk['o'] + 1} on {lk['sq']}, {how}"
        conds = [dict(kind='access', x=[sc0['x']], o=sc0['o'], text=f"O{sc0['o'] + 1}'s screen on X{sc0['x'] + 1} is set (from {_and(sc0['squares'])})")]
        if lk.get('cover', -1) >= 0:
            conds.append(dict(kind='attention', x=[lk['cover']], o=lk['o'], text=f"X{lk['cover'] + 1} a step late to {lk['sq']}"))
        if lk['o'] != state.ball:
            conds.append(dict(kind='access', x=[], o=state.ball, text=f"the pass from O{state.ball + 1} to O{lk['o'] + 1} arrives"))
        roles = [dict(o=sc0['o'], role='screener', sq=sc0['sq'], squares=sc0['squares'])]
        roles.append(dict(o=lk['o'], role='shooter', sq=lk['sq']))
        if lk['o'] != state.ball:
            roles.append(dict(o=state.ball, role='passer', sq=B.sq(state.o[state.ball])))
        branch = dict(o=a, sq=left['sq'], shot=left['shot'], worth=left['worth'], reach=left['reach'], when='the screen fails',
                      text=f"If the screen fails: {base_words}")
        first = dict(o=lk['o'], sq=lk['sq'], shot=lk['shot'], open=lk['value'], reach=lk['reach'], worth=lk['worth'], cover=lk.get('cover', -1))
        spec = acceptance(scout, lk['o'], lk['shot'], bar_next)
        value = float(sc0['value'])
        access = f"O{sc0['o'] + 1}'s screen" + (f", then the pass to O{lk['o'] + 1}" if lk['o'] != state.ball else '')
        line = f"Attention: {att}. Hole: {lk['sq']}, {ZONE_NAMES.get(B.zone(B.parse_sq(lk['sq'])), '')}. Access: {access}."
    # step 25 (D-244): the conditions forming on this board (OFFENCE_CONDITIONS_19NOV.md), read from the map, ruled
    # in or out by the bar; the plan names the ones that build its target, and a branch from another attacker's
    from . import conditions as CD
    try:
        cr = CD.read(state, scout, cov=cov, roles=ro, bar=bar_next)
    except ValueError:
        cr = dict(found=[], ruled_in=[], ruled_out=[], unmeasured=dict(CD.UNMEASURED))
    found = cr['found'] + CD.screens_as_conditions(screens, state)
    for z in screens or []:
        if z.get('dive'):
            dv = z['dive']
            found.append(dict(id='47', name=CD.NAMES['47'], o=[dv['o']], x=[z['x']], worth=dv['worth'], sq=dv['sq'], ruled_in=dv['worth'] > bar_next,
                              why=f"O{dv['o'] + 1} dives to {dv['sq']} while the defence turns to O{z['o'] + 1}'s screen on X{z['x'] + 1}; his best look inside was {round(dv['before'])} before the screen"))
    tgt_o, tgt_x = first['o'], first.get('cover', -1)
    used = [c for c in found if c.get('ruled_in') and (tgt_o in c['o'] or (tgt_x >= 0 and tgt_x in c['x']))]
    used.sort(key=lambda c: (tgt_o not in c['o'], -c['worth']))
    seen_u, uniq = set(), []
    for c in used:
        k = (c['id'], tuple(c['o']))
        if k not in seen_u:
            seen_u.add(k)
            uniq.append(c)
    used = uniq
    if not branch or branch.get('o') == tgt_o:
        alt = [c for c in found if c.get('ruled_in') and tgt_o not in c['o'] and c['o']]
        if alt:
            c0 = max(alt, key=lambda c: c['worth'])
            branch = dict(o=c0['o'][0], sq=c0['sq'], shot=None, worth=c0['worth'], reach=None, when='the first preference is shut',
                          text=f"If that is shut: {c0['name']}, {c0['why']}")
    return dict(first, value=value, bar=bar_next, bars=tol, spec=spec, backups=backups, conditions=conds, roles=roles,
                found=found, used=used[:4], ruled_out=cr['ruled_out'], unmeasured=cr['unmeasured'],
                branch=branch, line=line, target=target, idle=idle, answers=cov.get('answers') or [], screens=screens,
                needs='Needs: ' + '; '.join(c['text'] for c in conds) + '.' if conds else '',
                backup_words=('Backups: ' + '; '.join(_look_words(b) for b in backups) + '.') if backups else '')


def plan_words(plan):
    """The plan in plain words, a line each: the target, what it needs, the branch, the backups, and the attention,
    holes and access line."""
    if not plan:
        return []
    out = [plan['target'] + '.']
    if plan['needs']:
        out.append(plan['needs'])
    if plan.get('used'):
        out.append('Built from: ' + '; '.join(f"{c['name']} ({c['why']})" for c in plan['used'][:3]) + '.')
    if plan['branch']:
        out.append(plan['branch']['text'] + '.')
    if plan['backup_words']:
        out.append(plan['backup_words'])
    out.append(plan['line'])
    return out


# ---- stage 4: the offence's placement -------------------------------------------------------------------------------------

def _okey(m):
    """A placement's quick measure (step 27, D-257): the list leads, as in play (D-219): the list of things to cover
    against the defence it predicts, largest first; then the lasting gap; then efficiency (the fewest actions the
    defence's answer needs). The same order as list_key; used to rank which placements get the full reading."""
    drv = m[3] or {}
    return (tuple(drv.get('list') or ()), round(float(m[2]), 6), -int(drv.get('n') or 0))


FULL_CAP_S = 95.0       # step 27: the full reads stop by here, so the whole offence setup stays under about 2 minutes on desktop
HORIZON_TURNS = 4       # step 27 (D-258), step 28 (D-268): every placement compared is read to the same horizon, capped by the clock


def _why_lost(win, lose):
    """What tells the winner from the alternative, by the one list (item by item, best first)."""
    a, b = list(win['key'][0]), list(lose['key'][0])
    for k in range(min(len(a), len(b))):
        if abs(a[k] - b[k]) > 1e-9:
            nth = ('its best look', 'its second look', 'its third look', 'its fourth look', 'its fifth look')[k] if k < 5 else 'a gap further down its list'
            return f"{nth} reads {b[k]:g} against {a[k]:g} once the full defence answers"
    if abs(win['key'][1] - lose['key'][1]) > 1e-9:
        return f"the gap that lasts reads {lose['key'][1]:g} against {win['key'][1]:g}"
    return 'the defence answers it with fewer actions'


JOB_SHOTS = (('post', ('post',)), ('roll', ('layup', 'dunk')), ('spacing', ('three',)))


def _job_variants(make, read, sq, ball, t_end):
    """Step 28 (D-265): from a placement, each attacker but the ball handler on his best square for each job he can do,
    by the map's own looks against the quick defence (his best post shot, his best layup or dunk at the rim, his best
    three) and the best screen he can set (screen_roles). Each is read the quick way. -> [dict(o, job, q, sq, r)]."""
    import time
    from . import agent as AG
    m = read(sq, ball)
    if not m:
        return []
    st = make(sq, ball, m[1][0], m[1][1]).with_(side='O', turn_n=0)
    try:
        cov = AG.coverage(st)
        scr = screen_roles(st)
    except ValueError:
        return []
    taken = set(sq) | set(m[1][0])
    out = []
    allsq = cov.get('squares') or [{}] * 5
    for a in range(5):
        if a == ball:
            continue
        sqs = allsq[a] or {}
        picks = []
        for job, shots in JOB_SHOTS:
            # his own best square for the job, where the map gives him one this phase; else the best square for the job
            # on this board (any attacker's look there), so a player far from it this phase is still tried on it
            best = max(((v.get('worth', 0), q) for q, v in sqs.items() if v.get('shot') in shots), default=None)
            if best is None:
                best = max(((v.get('worth', 0), q) for z in allsq for q, v in (z or {}).items() if v.get('shot') in shots
                            and B.parse_sq(q) not in taken), default=None)
            if best:
                picks.append((job, B.parse_sq(best[1])))
        z = next((z for z in scr if z['o'] == a), None)
        if z:
            picks.append(('screen', B.parse_sq(z['sq'])))
        for job, q in picks:
            if time.time() >= t_end:
                return out
            if q == sq[a] or (q in taken and q != sq[a]):
                continue
            trial = sq[:a] + [q] + sq[a + 1:]
            if not AG._legal_o(trial, ball):
                continue
            out.append(dict(o=a, job=job, q=q, sq=trial, r=read(trial, ball)))
    return out


def place_offence(make, seed=0, level='allstar', budget=None, nth=0, scout=None, pool=None, cap=None, depth=None):
    """The offence sets up first (blueprint, stages 3, 3b and 4), the way it plays (step 27, D-257 to D-259).
    1. Quick search: from the table's squares (each attacker tried with the ball), each attacker in turn swept over
       every legal square (D-240 retired as a restriction: no candidate squares, nothing forced), kept when the list
       reads better against the defence's quick setup.
    2. Full reading: placements in the quick order, and always the table's squares, each against the defence's full
       setup (the setup it really uses), then read ahead to the same horizon (horizon_read). The best by the list wins.
       It reads on while the clock allows (FULL_CAP_S) and stops once the leader has held through two full readings
       after it took the lead, so the choice no longer changes; every pair compared is the same reading.
    pool: placements to read in full instead of searching [(squares, ball)] (for the checks). nth: the next best.
    make(o squares, ball, x squares, arrows) builds the state.
    -> dict(squares, ball, value, plan, words, text, candidates, ranked, full, alternative, checks, seconds)."""
    import random
    import time
    from . import agent as AG
    from playmaker_web.game import TABLE_O, man_to_man
    t0 = time.time()
    cap = FULL_CAP_S if cap is None else cap
    depth = HORIZON_TURNS if depth is None else depth
    quick_s = 12.0 if budget is None else max(2.0, min(budget, 12.0))      # the quick search's own time
    rng = random.Random(seed)
    base = [B.parse_sq(q) for q in TABLE_O]
    s0 = make(base, 0, *man_to_man(base, 0))
    scout = scout or scout_for(s0.ctx, 'O')
    seen = {}
    wood = sorted(B.sq((x, y)) for x in range(B.W) for y in range(2, B.H + 1) if B.on_board((x, y)) and B.zone((x, y)) == '.')

    def read(sq, ball):
        key = (tuple(sq), ball)
        if key not in seen:
            m = AG._map_setup(make, list(sq), ball, evals=0)
            if m is None:
                return None
            seen[key] = (_okey(m), m)
        return seen[key]

    # the table's squares, each attacker in turn tried with the ball (the ball handler must stand on plain wood)
    table = []
    for b in range(5):
        sq = list(base)
        sq[0], sq[b] = sq[b], sq[0]
        if AG._legal_o(sq, b):
            r = read(sq, b)
            if r:
                table.append((r[0], sq, b))
    if not table:
        return None
    table.sort(key=lambda r: r[0], reverse=True)
    steps = []
    if pool is None:
        key, sq, ball = table[0]
        changed, rounds = True, 0
        while changed and rounds < 3 and time.time() < t0 + quick_s:
            changed, rounds = False, rounds + 1
            for i in range(5):
                if time.time() >= t0 + quick_s:
                    break
                m = read(sq, ball)[1]
                try:       # every legal square (the sweep skips only squares taken by another piece, and for the ball
                    # handler squares off plain wood, which the rules don't allow him to start on)
                    rows = AG.coverage(make(sq, ball, m[0], m[1]), only='offsweep', piece=i, keep=4, quick=True,
                                       **(dict(squares=wood) if i == ball else {})) or []
                except ValueError:
                    rows = []
                for row in rows:
                    q = B.parse_sq(row['sq'])
                    trial = sq[:i] + [q] + sq[i + 1:]
                    if q == sq[i] or not AG._legal_o(trial, ball):
                        continue
                    r = read(trial, ball)
                    if r and r[0] > key:
                        steps.append(dict(o=i, to=row['sq'], why='the list reads better', key=r[0]))
                        key, sq, changed = r[0], trial, True
        # step 28 (D-265, Shaun, 19 Nov 2026): a wider search, no rule. From the quick leader, each attacker is also tried
        # on his best square for each job he can do (a post shot, a roll to the rim, spacing for a three, a screen on a
        # defender), read the same quick way; the best of them is read in full beside the leader and the table squares
        jobs = _job_variants(make, read, sq, ball, t0 + quick_s + 25.0)
        quick = sorted(((k, list(p[0]), p[1]) for p, (k, m) in seen.items() if AG._legal_o(list(p[0]), p[1])), key=lambda r: r[0], reverse=True)
        jv = sorted((z for z in jobs if z['r']), key=lambda z: z['r'][0], reverse=True)
        order = [quick[0], table[0]] + [(z['r'][0], z['sq'], ball) for z in jv] + quick[1:]
    else:
        order = []
        for sq, b in pool:
            r = read(list(sq), b)
            if r:
                order.append((r[0], list(sq), b))
        quick = sorted(order, key=lambda r: r[0], reverse=True)
    # the full reading: the defence it really uses, then read ahead; same reading and same horizon for every placement
    if pool is not None:
        jobs = []
    full, done, lead_held, last = [], set(), 0, 0.0
    for k0, sq, ball in order:
        p = (tuple(sq), ball)
        if p in done:
            continue
        if len(done) >= 2 and pool is None and (time.time() - t0) + last > cap:
            break                     # (the quick leader and the table squares are always both read in full: the rival stays)
        if pool is None and lead_held >= 2:
            break
        t1 = time.time()
        m = AG._map_setup(make, list(sq), ball, evals=240)
        if m is None:
            continue
        st = make(list(sq), ball, m[0], m[1])
        h = horizon_read(st, scout, budget=60.0, depth=depth)
        if h is None:
            continue
        done.add(p)
        row = dict(squares=list(sq), ball=ball, m=m, h=h, key=h['key'], quick=k0, seconds=round(time.time() - t1, 1))
        prev = max(full, key=lambda r: r['key']) if full else None
        full.append(row)
        lead_held = 0 if prev is None or row['key'] > prev['key'] else lead_held + 1
        last = time.time() - t1
    if not full:
        return None
    ranked = sorted(full, key=lambda r: r['key'], reverse=True)
    margin = AG.profile(level).get('variety_margin', 0)
    near = [r for r in ranked if (r['key'][0][:1] or (0,))[0] >= (ranked[0]['key'][0][:1] or (0,))[0] - margin - 1e-9]
    pick = ranked[min(nth, len(ranked) - 1)] if nth else (rng.choice(near) if margin > 0 and len(near) > 1 else ranked[0])
    sq, ball, m, h = pick['squares'], pick['ball'], pick['m'], pick['h']
    xs, arrows, perm = list(m[0]), list(m[1]), list(m[4] or range(5))
    state = make(sq, ball, xs, arrows)
    plan = route_plan(state, scout, perm, h, deep=True)
    from . import conditions as CD
    plan['ahead'] = CD.ahead(h, state)
    checks = placement_checks(state, scout, plan)
    words = plan_words(plan)
    if plan['ahead']:          # (the route itself is the Plan line, D-264: one plan on screen)
        words.append('Built on the way: ' + '; '.join(f"{c['name']} ({c['why']})" for c in plan['ahead'][:3]) + '.')
    alt = next((r for r in ranked if r is not pick), None)
    alternative = None
    if alt is not None:
        alternative = dict(squares=[B.sq(q) for q in alt['squares']], ball=alt['ball'], list=alt['h']['list'],
                           text=f"Weighed instead: {', '.join(f'O{i + 1} {B.sq(q)}' for i, q in enumerate(alt['squares']))} "
                                f"(ball O{alt['ball'] + 1}). It lost because {_why_lost(pick, alt)}.")
    if alternative:
        words.append(alternative['text'])
    text = ' '.join(words) if words else 'Placed where the list reads best against the defence it predicts.'
    tab = next((r for r in full if (tuple(r['squares']), r['ball']) == (tuple(table[0][1]), table[0][2])), None)
    top = (pick['h']['list'] or [0])[0]
    return dict(squares=sq, ball=ball, value=round(float(top), 2), plan=plan, words=words, text=text, steps=steps,
                candidates=len(seen), within=len(near), list=pick['h']['list'], horizon=plan['horizon'],
                ranked=[dict(squares=[B.sq(q) for q in r['squares']], ball=r['ball'], value=(r['h']['list'] or [0])[0], list=r['h']['list'],
                             turns=r['h']['turns'], seconds=r['seconds']) for r in ranked[:6]],
                full=len(full), quick_ranked=len(quick), alternative=alternative,
                jobs=[dict(o=z['o'], job=z['job'], to=B.sq(z['q']), quick=list(z['r'][0][0][:5]) if z['r'] else None,
                           full=next((list(r['h']['list']) for r in full if r['squares'] == z['sq']), None)) for z in jobs],
                table=dict(squares=[B.sq(q) for q in table[0][1]], ball=table[0][2], list=tab['h']['list'] if tab else None,
                           turns=tab['h']['turns'] if tab else None),
                predicted=dict(x=[B.sq(q) for q in xs], arrows=list(arrows), perm=list(perm)), checks=checks,
                roles=role_squares(scout, sq, ball, plan), seconds=round(time.time() - t0, 1))


def role_squares(scout, sq, ball, plan):
    """For the board: each attacker's candidate squares, and the squares the plan's roles need (where he stands, and
    for the shooter where the shot goes up)."""
    out = []
    need = {}
    for r in (plan or {}).get('roles') or []:
        need.setdefault(r['o'], []).extend(r.get('squares') or [r['sq']])
    for a in range(5):
        out.append(dict(o=a, candidates=sorted(B.sq(q) for q in scout.candidates(a)), needs=sorted(set(need.get(a, []) + ([B.sq(sq[a])] if a in need else []))),
                        role=', '.join(r['role'] for r in (plan or {}).get('roles') or [] if r['o'] == a)))
    return out


def placement_checks(state, scout, plan):
    """Shaun's two expectations, as checks and never as rules: every defender is pulled to a real job; a
    poor-shooting centre is a post or screening presence, not a body in a corner."""
    from . import scouting as SCT
    out = []
    idle = (plan or {}).get('idle') or []
    # step 27 (item 2): the candidate squares kept as a check, never a rule: an attacker with no job (no
    # look of his own, no screen, no pass, no defender drawn to him) is reported
    try:
        from . import agent as AG
        cov = AG.coverage(state)
    except ValueError:
        cov = None
    if cov:
        roles = {r['o'] for r in (plan or {}).get('roles') or []}
        drawn = {a for c in (cov.get('covers') or []) for a in (c.get('attackers') or c.get('o') or []) if isinstance(a, int)} if isinstance(cov.get('covers'), list) else set()
        nothing = []
        for a in range(5):
            sqs = (cov.get('squares') or [{}] * 5)[a] or {}
            own = max((v.get('worth', 0) for v in sqs.values()), default=0)
            if own <= 0 and a not in roles and a != state.ball and a not in drawn:
                nothing.append(a)
        out.append(dict(check='every attacker has a job', passed=not nothing, idle=nothing,
                        text='Every attacker has a job: a look of his own, a screen, a pass or a defender drawn to him.' if not nothing
                        else f"{_and(f'O{a + 1}' for a in nothing).replace(' or ', ' and ')} has no job from where he stands: no look, screen or pass, and no defender drawn to him."))
    out.append(dict(check='every defender has a real job', passed=not idle,
                    text='Every defender has a real job.' if not idle else f"{_and(f'X{d + 1}' for d in idle).replace(' or ', ' and ')} left with no real job: the defence can use him on the plan's gaps."))
    for a, card in enumerate(state.ctx.off):
        if SCT.position(card) != 'C':
            continue
        q = state.o[a]
        corner = B.zone(q) == '3' and q[1] <= 4
        poor = card.bands.get('shot_three') == 'L'
        if poor:
            out.append(dict(check='a poor-shooting centre is not a corner body', passed=not corner, o=a, sq=B.sq(q),
                            text=f"O{a + 1} ({SCT.short_role(card)}) stands on {B.sq(q)}, {ZONE_NAMES.get(B.zone(q), 'beyond the arc')}."
                                 + (' He is a body in the corner: his three there is the best look the map found for him.' if corner else '')))
    return out


# ---- stage 5: the defence's setup -----------------------------------------------------------------------------------------

POS_ORDER = ('PG', 'SG', 'SF', 'PF', 'C')


def _where_words(q):
    z = B.zone(q)
    return {'.': 'at the arc', '3': 'at the three-point line', 'L': 'at the long two', 'M': 'in mid-range', 'K': 'in the green zone'}.get(z, '')


def place_defence(make, o_sq, ball, seed=0, level='allstar', budget=None, nth=0, scout=None):
    """The defence sets up (blueprint, stage 5): everything that works is kept (the settlement of all five by the
    list), then the matchup rule: among the ways of standing that leave as much (within the level's margin), the
    mismatch priced where it hurts, then like against like, then matching numbers. The defence's own scout names the
    matchups it avoided. -> dict(squares, arrows, perm, value, text, read, avoided)."""
    from . import agent as AG
    from . import scouting as SCT
    o_sq = list(o_sq)
    m = AG._map_setup(make, o_sq, ball)
    if m is None:
        return None
    xs, arrows, L, drv, perm, lines = list(m[0]), list(m[1]), float(m[2]), m[3] or {}, list(m[4] or range(5)), m[5]
    s0 = make(o_sq, ball, xs, arrows)
    scout = scout or scout_for(s0.ctx, 'X')
    margin = AG.profile(level).get('variety_margin', 0)
    pos_o = [POS_ORDER.index(SCT.position(c)) for c in s0.ctx.off]
    pos_x = [POS_ORDER.index(SCT.position(c)) for c in s0.ctx.dfn]

    def price(a, d):
        b = scout.beat(s0, a, d, o_sq[a])
        return (b['chance'] * b['grows']) if b else 0.0

    def measure(xq, ar):
        st = make(o_sq, ball, xq, ar)
        r = AG.coverage(st, only='lasting')
        ro = AG.coverage(st, only='roles')
        pm = list(ro['perm']) if ro and ro.get('perm') else list(range(5))
        top = (r['drivers']['list'] or [0])[0]
        cost = round(sum(price(a, d) for d, a in enumerate(pm)), 3)
        unlike = sum(abs(pos_x[d] - pos_o[a]) for d, a in enumerate(pm))
        same = sum(1 for d, a in enumerate(pm) if d == a)
        return dict(x=list(xq), arrows=list(ar), L=float(r['L']), top=float(top), perm=pm, key=(cost, unlike, -same), cost=cost, unlike=unlike, same=same)
    cur = measure(xs, arrows)
    base, tried, swaps = cur, [cur], []
    for _ in range(4):
        better = None
        for i in range(5):
            for j in range(i + 1, 5):
                xq, ar = list(cur['x']), list(cur['arrows'])
                xq[i], xq[j] = xq[j], xq[i]
                ar[i], ar[j] = ar[j], ar[i]
                try:
                    t = measure(xq, ar)
                except ValueError:
                    continue
                tried.append(t)
                if t['L'] > base['L'] + margin + 1e-9 or t['top'] > base['top'] + margin + 1e-9:
                    continue                             # it leaves more than the margin allows: everything that works is kept
                if t['key'] < (better or cur)['key']:
                    better = dict(t, swap=(i, j))
        if better is None:
            break
        swaps.append(better['swap'])
        cur = better
    pick = cur
    # step 27 (D-258): the same horizon as the offence's (neutrality). The ways of standing still in the running (the
    # settlement, the matchup rule's pick, the next ones the rule allowed) are read ahead to the same depth; the
    # matchup rule's pick stands while it leaves no more by the list read ahead than the level's margin allows
    ahead = []
    if not nth:
        import time as _t
        t_h = _t.time()
        allowed = sorted((t for t in tried if t['L'] <= base['L'] + margin + 1e-9 and t['top'] <= base['top'] + margin + 1e-9), key=lambda t: (t['key'], t['L']))
        pool = []
        for t in [pick, base] + allowed:
            if all(t['x'] != u['x'] or t['arrows'] != u['arrows'] for u in pool):
                pool.append(t)
        for t in pool[:3]:                  # (three ways read ahead keeps the defence's setup inside the time guard at four turns)
            h = horizon_read(make(o_sq, ball, t['x'], t['arrows']), scout, budget=60.0, depth=HORIZON_TURNS)
            if h is not None:
                ahead.append((h['key'], t, h))
        if ahead:
            low = min(ahead, key=lambda z: z[0])
            mine = next((z for z in ahead if z[1] is pick), None)
            top = lambda z: (z[0][0][:1] or (0,))[0]
            if mine is None or (mine[0] > low[0] if margin <= 0 else top(mine) > top(low) + margin + 1e-9):
                pick = low[1]
        ahead_s = round(_t.time() - t_h, 1)
    if nth:                                              # the next-best ways of standing, by the same rule
        allowed = sorted((t for t in tried if t['L'] <= base['L'] + margin + 1e-9 and t['top'] <= base['top'] + margin + 1e-9), key=lambda t: (t['key'], t['L']))
        uniq = []
        for t in allowed:
            if all(t['x'] != u['x'] for u in uniq):
                uniq.append(t)
        pick = uniq[min(nth, len(uniq) - 1)] if uniq else cur
    pm = pick['perm']
    # step 26 (D-252): the read matches the board. "X5 on O5" only when X5 can contest O5's look this turn (his job
    # line says he takes something off it); otherwise it says he sags off him, and why
    try:
        roles = {r['x']: r for r in (AG.coverage(make(o_sq, ball, pick['x'], pick['arrows']), only='roles', prev=list(pm), fixed=True) or {}).get('roles') or []}
    except ValueError:
        roles = {}
    read = []
    for d, a in enumerate(pm):
        co, cx = s0.ctx.off[a], s0.ctx.dfn[d]
        r = roles.get(d) or {}
        if r and r.get('kind') not in ('man', 'both', 'chase'):
            if r.get('way') and r['way']['o'] == a:
                why = f"he sags off him, standing in his way rather than on him (his look is worth {round(r['way']['now'])}, {round(r['way']['without'])} without him there)"
            elif r.get('way'):
                why = f"he sags off him to guard O{r['way']['o'] + 1}'s look (worth {round(r['way']['without'])} without him there)"
            elif r.get('gap'):
                why = f"he sags off him to cover the squares around {r['gap']['sq']}"
            else:
                why = "he sags off him: he can't reach his look this turn"
            read.append(dict(x=d, o=a, why=why, sags=True, text=f'X{d + 1} sags off O{a + 1}{why[len("he sags off him"):]}'))
            continue
        why = ('same position' if pos_o[a] == pos_x[d] else 'same speed' if co.qs == cx.qs else
               'the nearest defender who takes something off his look')
        read.append(dict(x=d, o=a, why=why, text=f'X{d + 1} on O{a + 1}: {why}'))
    # the matchups it avoided, from its own scout: the Dribble mismatch where it hurts, and the shot it most wants to keep its man off
    avoided = []
    costs = sorted(((price(ball, d), d) for d in range(5)), reverse=True)
    if costs and costs[0][0] > 0 and pm[costs[0][1]] != ball and costs[0][0] > price(ball, pm.index(ball)) + 1e-9:
        avoided.append(dict(x=costs[0][1], o=ball, text=f'not X{costs[0][1] + 1} on O{ball + 1} {_where_words(o_sq[ball])}'))
    tol = bars(make(o_sq, ball, pick['x'], pick['arrows']))
    for r in scout.preferences(tol[0]['bar']):
        if pm[r['x']] != r['o'] and r['over'] > 0 and not any(z['x'] == r['x'] and z['o'] == r['o'] for z in avoided):
            avoided.append(dict(x=r['x'], o=r['o'], text=f"not X{r['x'] + 1} on O{r['o'] + 1} {_where_words_zone(r['zone'])}"))
            break
    # step 25 (D-244): the defence reads the offence's conditions forming on the board, with its own model (public
    # information only: it never sees the offence's plan), and names the ones it must deny
    watching = []
    try:
        from . import conditions as CD
        st_d = make(o_sq, ball, pick['x'], pick['arrows'])
        cr = CD.read(st_d, scout, bar=tol[1]['bar'] if len(tol) > 1 else 0.0)
        for c in sorted((c for c in cr['found'] if c.get('ruled_in')), key=lambda c: -c['worth'])[:2]:
            watching.append(dict(id=c['id'], text=f"{c['name']}: {c['why']}"))
    except ValueError:
        watching = []
    # step 28 (D-267): the stances the defence takes, read from its own squares and arrows
    try:
        from . import conditions as CD
        stn = [z for z in CD.stances(make(o_sq, ball, pick['x'], pick['arrows']), pm) if z['stance'] not in ('beside', 'off')]
    except ValueError:
        stn = []
    text = 'Matchups: ' + '; '.join(z['text'] for z in read) + '.' + (' Avoided: ' + '; '.join(z['text'] for z in avoided) + '.' if avoided else '')
    if stn:
        text += ' Stances: ' + '; '.join(z['text'] for z in stn) + '.'
    if watching:
        text += ' Watching: ' + '; '.join(z['text'] for z in watching) + '.'
    hz = next((z[2] for z in ahead if z[1] is pick), None)
    return dict(squares=pick['x'], arrows=pick['arrows'], perm=pm, value=round(pick['L'], 2), read=read, avoided=avoided, text=text, watching=watching,
                stances=stn,
                ahead=[dict(x=[B.sq(q) for q in z[1]['x']], list=z[2]['list'], turns=z[2]['turns'], chosen=z[1] is pick) for z in ahead],
                horizon=dict(turns=hz['turns'], list=hz['list'], words=horizon_words(hz)) if hz else None,
                lines=list(lines or []), swaps=[list(z) for z in swaps], settled=dict(x=[B.sq(q) for q in xs], L=L),
                rule=dict(cost=pick['cost'], unlike=pick['unlike'], same=pick['same'], before=dict(cost=base['cost'], unlike=base['unlike'], same=base['same'])))


def _where_words_zone(z):
    return {'3': 'at the three-point line', 'L': 'at the long two', 'M': 'in mid-range', 'K': 'in the green zone'}.get(z, '')


# ---- stage 6: in play ------------------------------------------------------------------------------------------------------

def plan_status(plan, state, scout):
    """At a phase's start, the plan measured on the board as it really is: is the first preference still the look the
    offence gets, has the defence taken it away, or has something worth as much or more at its real chance opened?
    Opportunities are compared by value at their real chance of happening (the list's value times reach), never by a
    shot's open value. -> dict(kind: 'chasing' | 'denied' | 'better', line, plan: the plan to carry on with)."""
    if not plan:
        return None
    # a plan that needs a screen is measured with the screen still to be set (the same reading that built it)
    # step 27 (D-258): nothing is locked; the route is read ahead again each phase, to the setup's own horizon. Step 28
    # (D-264): the plan is that route's
    try:
        h = horizon_read(state, scout, budget=12.0, depth=HORIZON_TURNS)
    except ValueError:
        h = None
    now = route_plan(state, scout, None, h, deep=bool(plan.get('screens')) and not state.screens)
    if not now:
        return None
    same = now['o'] == plan['o'] and now['shot'] == plan['shot']
    was = f"O{plan['o'] + 1}'s {SHOT_WORDS.get(plan['shot'], plan['shot'])}"
    new = _look_words(now)
    if same:
        how = ''
        if now.get('screens') and not state.screens:
            z = now['screens'][0]
            how = f", off O{z['o'] + 1}'s screen on X{z['x'] + 1} (still to be set)"
        steps = '; then '.join(p['offence'] for p in (now.get('horizon') or {}).get('path') or [])
        return dict(kind='chasing', line=f"Chasing: {steps + '; then ' if steps else ''}{new}{how}.", plan=dict(now, first=plan.get('first', plan)), worth=now['worth'])
    # what the planned look is worth now, at its real chance
    from . import agent as AG
    cov = AG.coverage(state)
    mine = [lk for lk in ((cov.get('squares') or [{}] * 5)[plan['o']] or {}).values() if lk.get('shot') == plan['shot']]
    left = max((lk.get('worth', 0) for lk in mine), default=0)
    if left < now['bar'] - 1e-9 or left <= 0:
        line = f"{was} is taken away: switching to {new}."
        kind = 'denied'
    else:
        line = (f"A better chance: {new}, worth {round(now['worth'])} at its real chance. The planned "
                f"{SHOT_WORDS.get(plan['shot'], plan['shot'])} is worth {round(left)}.")
        kind = 'better'
    return dict(kind=kind, line=line, plan=dict(now, first=plan.get('first', plan)), worth=now['worth'], planned=left)


# ---- step 27 (D-258): reading as far ahead as the plan needs ------------------------------------------------------------

def list_key(r):
    """The one measure play and setup share (D-219, D-257): the list of things to cover, largest first (compared item
    by item, the offence wanting it higher), then the lasting gap, then efficiency (fewer of the defence's actions)."""
    if not r:
        return ((), 0.0, 0)
    d = r.get('drivers') or {}
    return (tuple(d.get('list') or ()), float(r.get('L') or 0), -int(d.get('n') or 0))


def _defence_turn(state):
    """The defence's turn as the in-play computer weighs it (D-219, _driver_order): the turns its search tries from
    the map (the lasting reading's own best answer, each first part of it, the settlement's movements) and holding,
    each played by the rules and ended by them (the phase too, if that was the last token; a pass in the air lands
    the likeliest way). It takes the one that leaves the offence the least by the list, then the lasting gap, then
    the fewest actions. -> (state, [words])."""
    from . import agent as AG
    from .resolve import end_turn
    from .goals import _likeliest
    if state.stage != 'play':
        return state, []
    view = state.with_(ball=state.pending[1], pending=None, approach=-1) if state.pending else state
    try:
        r = AG.coverage(view, only='lasting', answer=True, settle=True)
    except ValueError:
        r = None
    ans = [tuple(z) for z in (r or {}).get('answer') or []]
    cands = [()] + [tuple(ans[:k]) for k in range(1, len(ans) + 1)]
    st_moves = tuple(tuple(z) for z in (r or {}).get('settle') or [])
    if st_moves and st_moves not in cands:
        cands.append(st_moves)
    best = None
    for mv in cands[:6]:
        xs, arrows, done, n = list(state.x), list(state.arrows), [], 0
        for d, q, a in mv:
            if n >= state.tok_x:
                break
            q = B.parse_sq(q)
            if q != xs[d]:
                done.append(f"X{d + 1} to {B.sq(q)}")
            elif a is not None and a >= 0 and a != arrows[d]:
                done.append(f"X{d + 1} turns")
            xs[d] = q
            if a is not None and a >= 0:
                arrows[d] = a
            n += 1
        st = state.with_(x=tuple(xs), arrows=tuple(arrows), side='X', tok_x=max(0, state.tok_x - max(1, n)))
        nxt = _likeliest(end_turn(st, 'X'))
        if nxt.stage != 'play':
            k = ((), 0.0, 0)                              # the possession over (a turnover or the clock): nothing left to the offence
        else:
            try:
                k = list_key(AG.coverage(nxt.with_(turn_n=0), only='lasting'))
            except ValueError:
                continue
        key = (k[0], k[1], n)                               # the defence wants the least: the list, then the gap, then actions
        if best is None or key < best[0]:
            best = (key, nxt, done, k)
    if best is None:
        return _likeliest(end_turn(state.with_(side='X', tok_x=max(0, state.tok_x - 1)), 'X')), []
    return best[1], best[2]


def _both_outcomes(after, caught):
    """Step 28 (D-263, Shaun, 19 Nov 2026): a pass read ahead counts both outcomes, the way the map does (D-250): the
    board if it lands (caught: the list read after the defence's turn), at the chance it lands by the rules (the map's
    own catch chance, the defence's Intercepts counted); and the pass stopped (-5, play on: the phase ends and the next
    begins, the ball back with the passer), at the chance it is stopped. Each item of the list is weighed by the two
    chances, as each look's worth is (its chance of getting there, less the -5 at the chance it doesn't); no new rule."""
    from . import agent as AG
    from .resolve import _turnover
    try:
        p = (AG.coverage(after, only='lasting') or {}).get('catch')
    except ValueError:
        p = None
    if p is None or p >= 1 - 1e-9:
        return caught, p
    stop = _turnover(after.with_(pending=None, approach=-1))
    if stop.stage == 'play':
        try:
            sk = list_key(AG.coverage(stop.with_(side='O', turn_n=0), only='lasting'))
        except ValueError:
            sk = ((), 0.0, 0)
    else:
        sk = ((), 0.0, 0)
    a, b = list(caught[0]), list(sk[0])
    n = max(len(a), len(b))
    a += [0.0] * (n - len(a))
    b += [0.0] * (n - len(b))
    items = sorted((p * u + (1 - p) * (v + RC.TURNOVER_POINTS) for u, v in zip(a, b)), reverse=True)
    return (tuple(round(x, 6) for x in items), p * caught[1] + (1 - p) * (sk[1] + RC.TURNOVER_POINTS), caught[2]), p


def _continuations(state, scout):
    """The offence's turns worth reading a turn further on, each by the rules and ending its turn as the rules say
    (a Screen, a Pass, a Hesitate): every screen that builds more on this board (screen_roles: on or off the ball,
    the screener's own Move first where he needs one); each pass the ball handler can make (the ball swung); the
    ball handler's Hesitate; and each teammate's one Move to where his best look starts, then the ball handler's
    Hesitate (a seal, a V-cut, a cut that needs the defender to answer first). -> [(words, state after its turn)]."""
    from . import agent as AG
    from .actions import legal_actions
    from .resolve import apply
    from .goals import _likeliest
    out = []
    s0 = state.with_(side='O', turn_n=0)

    def run(st, act):
        nxt = _likeliest(apply(st, act))
        return nxt if nxt.stage == 'play' and nxt.side == 'X' else None
    try:
        acts = legal_actions(s0)
        # the best screens by the list that the screener can set this turn: from where he stands, or after his own
        # one Move to a square it can be set from (the rules: a Screen is the turn's first action, or its second
        # straight after that player's own Move)
        done = 0
        for z in screen_roles(s0):
            if done >= 3:
                break
            for name in [z['sq']] + [q for q in z['squares'] if q != z['sq']]:
                q = B.parse_sq(name)
                mv = None if s0.o[z['o']] == q else next((a for a in acts if a.piece == z['o'] and a.kind == 'move' and a.dest == q), None)
                if s0.o[z['o']] != q and mv is None:
                    continue
                st = _likeliest(apply(s0, mv)) if mv is not None else s0
                if st.stage != 'play' or st.o[z['o']] != q:
                    continue
                act = next((a for a in legal_actions(st) if a.kind == 'screen' and a.piece == z['o'] and a.target == B.dir_between(q, st.x[z['x']])), None)
                nxt = run(st, act) if act is not None else None
                if nxt is not None:
                    out.append((f"O{z['o'] + 1} screens X{z['x'] + 1} from {name}", nxt, act))
                    done += 1
                    break
        for a in acts:
            if a.kind == 'pass' and a.piece == s0.ball:
                nxt = run(s0, a)
                if nxt is not None and (nxt.ball != s0.ball or nxt.pending):
                    out.append((f"O{s0.ball + 1} passes to O{a.target + 1}" if isinstance(a.target, int) else f"O{s0.ball + 1} passes", nxt, a))
        hes = next((a for a in acts if a.kind == 'hesitate'), None)
        if hes is not None:
            nxt = run(s0, hes)
            if nxt is not None:
                out.append((f"O{s0.ball + 1} hesitates", nxt, hes))
            cov = AG.coverage(s0)
            for k in range(5):
                if k == s0.ball:
                    continue
                sqs = (cov.get('squares') or [{}] * 5)[k] or {}
                moves = {B.sq(x.dest): x for x in acts if x.piece == k and x.kind == 'move' and x.dest}
                cands = sorted(((v.get('worth', 0), q) for q, v in sqs.items() if q in moves), reverse=True)
                if not cands:
                    continue
                st = _likeliest(apply(s0, moves[cands[0][1]]))
                h2 = next((a for a in legal_actions(st) if a.kind == 'hesitate'), None) if st.stage == 'play' else None
                nxt = run(st, h2) if h2 is not None else None
                if nxt is not None:
                    out.append((f"O{k + 1} moves to {cands[0][1]}, O{s0.ball + 1} hesitates", nxt, moves[cands[0][1]]))
    except ValueError:
        pass
    return out


def horizon_read(state, scout=None, budget=None, depth=None):
    """Step 27 (D-258): the board read as far ahead as its best plan needs, capped by the shot clock. Turn by turn:
    the offence's best turn that ends as the rules say (a screen, a pass, a Hesitate, a move then a Hesitate), the
    defence's best answer by its own map, the turn's end and the phase's end by the rules (their counts included),
    then the board read again by the one list. It reads a turn further only while that reads better for the offence
    than stopping, so a look that pays at once reads in one turn and a screen then a dive in two. Both sides use this
    same reading (the defence's setup compares its candidates with it). -> dict(key, list, L, turns, phases, path,
    first: the one-turn key)."""
    import time
    from . import agent as AG
    t_end = time.time() + (budget if budget is not None else 30.0)
    s0 = state.with_(side='O', turn_n=0)
    try:
        first = list_key(AG.coverage(s0, only='lasting'))
    except ValueError:
        return None
    best = dict(key=first, turns=1, phases=1, path=[])
    cur, turns, path = s0, 1, []
    while time.time() < t_end and (depth is None or turns < depth):
        step = None
        for words, after, act in _continuations(cur, scout):
            if time.time() >= t_end:
                break
            nxt, dn = _defence_turn(after)
            if nxt.stage != 'play' or nxt.side != 'O':
                continue
            try:
                k = list_key(AG.coverage(nxt.with_(turn_n=0), only='lasting'))
            except ValueError:
                continue
            ch = None
            if act.kind == 'pass' and after.pending:
                k, ch = _both_outcomes(after, k)
            if step is None or k > step[0]:
                step = (k, nxt, words, dn, act, ch)
        if step is None or not step[0] > best['key']:
            break
        turns += 1
        a = step[4]
        path = path + [dict(turn=turns - 1, phase=cur.phase, offence=step[2], defence=step[3],
                            act=[a.kind, a.piece, B.sq(a.dest) if a.dest else None, a.target], list=list(step[0][0][:5]), catch=step[5],
                            moved=[int(w.split()[0][1:]) - 1 for w in step[3] if w.startswith('X')])]
        best = dict(key=step[0], turns=turns, phases=step[1].phase - state.phase + 1, path=path, final=step[1])
        cur = step[1]
    return dict(key=best['key'], list=list(best['key'][0][:5]), L=best['key'][1], turns=best['turns'],
                phases=best['phases'], path=best['path'], first=first, final=best.get('final', s0))


def route_plan(state, scout, perm=None, h=None, deep=True):
    """Step 28 (D-264, Shaun, 19 Nov 2026): one plan on screen, the route the computer actually chases, read ahead. With
    a route of one turn it is the board's own plan (read_plan). With more, the plan is read on the board the route leads
    to (after each turn and the defence's answer, by the rules), and the route's turns come first: the target, its needs,
    its branch, and the attention, holes and access line all follow the route."""
    if h is None:
        h = horizon_read(state, scout, budget=12.0, depth=HORIZON_TURNS)
    if not h or h['turns'] <= 1 or h.get('final') is None:
        plan = read_plan(state, scout, perm, deep=deep)
        if plan is not None and h:
            plan['horizon'] = dict(turns=h['turns'], phases=h['phases'], path=h['path'], words=horizon_words(h), list=h['list'], first=list(h['first'][0][:5]))
            plan['route'] = None
        return plan
    fin = h['final'].with_(side='O', turn_n=0)
    plan = read_plan(fin, scout, None, deep=False) or read_plan(state, scout, perm, deep=deep)
    if plan is None:
        return None
    steps = [p['offence'] for p in h['path']]
    head = '; then '.join(steps)
    plan['target'] = f"Plan: {head}; then {plan['target'][len('Plan: '):]}" if plan['target'].startswith('Plan: ') else f"Plan: {head}; then {plan['target']}"
    needs = []
    for p in h['path']:
        kind, o, dest, tgt = p['act']
        if kind == 'screen':
            needs.append(f"O{o + 1}'s screen holds ({p['offence'].split(' from ')[0].split('screens ')[-1]} stays behind it)")
        elif kind == 'pass':
            ch = p.get('catch')
            needs.append(f"the pass from O{o + 1} to O{tgt + 1} arrives" + (f" ({round(100 * ch)} in 100)" if ch is not None else ''))
        elif kind in ('move', 'qs', 'sprint') and dest:
            needs.append(f"O{o + 1} gets to {dest}")
    rest = plan.get('needs') or ''
    rest = rest[len('Needs: '):].rstrip('.') if rest.startswith('Needs: ') else rest.rstrip('.')
    plan['needs'] = 'Needs: ' + '; '.join(needs + ([rest] if rest else [])) + '.'
    roles = list(plan.get('roles') or [])
    for p in h['path']:
        kind, o, dest, tgt = p['act']
        role = {'screen': 'screener', 'pass': 'passer', 'hesitate': 'ball handler'}.get(kind, 'cutter')
        if not any(r['o'] == o and r['role'] == role for r in roles):
            roles.append(dict(o=o, role=role, sq=dest or B.sq(state.o[o])))
    plan['roles'] = roles
    plan['horizon'] = dict(turns=h['turns'], phases=h['phases'], path=h['path'], words=horizon_words(h), list=h['list'], first=list(h['first'][0][:5]))
    plan['route'] = h['path'][0]['act']
    plan['route_board'] = dict(o=[B.sq(q) for q in fin.o], x=[B.sq(q) for q in fin.x], ball=fin.ball)
    return plan


def horizon_words(h):
    if not h or h['turns'] <= 1:
        return 'It pays on this turn.'
    steps = '; then '.join(f"{p['offence']}" + (f" ({', '.join(p['defence'])})" if p['defence'] else '') for p in h['path'])
    ph = f", across {h['phases']} phases" if h['phases'] > 1 else ''
    return f"It needs {h['turns']} turns{ph}: {steps}."
