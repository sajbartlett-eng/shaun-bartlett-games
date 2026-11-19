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
        base = float(AG.coverage(s0, only='lasting')['L'])
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
                    gain = float(r['L']) - base
                    if gain > 0.5:
                        row = found.setdefault((k, d), dict(o=k, x=d, sq=B.sq(q), value=float(r['L']), gain=round(gain, 2), squares=[], state=after))
                        row['squares'].append(B.sq(q))
                        if float(r['L']) > row['value'] + 1e-9:
                            row.update(sq=B.sq(q), value=float(r['L']), gain=round(gain, 2), state=after)
    out = sorted(found.values(), key=lambda z: (-z['value'], z['o'], z['x']))
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
    """A placement's one measure (blueprint, stage 4): the value of its best plan at its real chance against the
    defence it predicts (the lasting gap), then the rest of what it leaves to cover, then efficiency (the fewest
    actions the defence's answer needs: the offence's gain comes soonest)."""
    drv = m[3] or {}
    return (round(float(m[2]), 6), tuple(drv.get('list') or ()), -int(drv.get('n') or 0))


def place_offence(make, seed=0, level='allstar', budget=None, nth=0, scout=None):
    """The offence sets up first (blueprint, stages 3, 3b and 4). Candidate squares for each attacker from the scout;
    each placement is measured against the defence the offence predicts for it (the defence's own setup logic, run on
    public information); the best is locked in and its plan read. make(o squares, ball, x squares, arrows) builds the
    state. nth: 0 the best placement found, 1 the next best, and so on. -> dict(squares, ball, value, plan, words,
    text, candidates, ranked, checks)."""
    import random
    import time
    from . import agent as AG
    from playmaker_web.game import TABLE_O, man_to_man
    t0 = time.time()
    budget = 12.0 if budget is None else max(2.0, budget)      # the level's own setup time (D-213); the button's: 12 seconds
    t_end = t0 + budget
    rng = random.Random(seed)
    base = [B.parse_sq(q) for q in TABLE_O]
    s0 = make(base, 0, *man_to_man(base, 0))
    scout = scout or scout_for(s0.ctx, 'O')
    cands = [set(scout.candidates(a)) for a in range(5)]
    wood = {(x, y) for x in range(B.W) for y in range(2, B.H + 1) if B.on_board((x, y)) and B.zone((x, y)) == '.'}
    seen = {}

    def read(sq, ball, evals=0):
        key = (tuple(sq), ball)
        if key not in seen or (evals and not seen[key][2]):
            m = AG._map_setup(make, list(sq), ball, evals=evals)
            if m is None:
                return None
            seen[key] = (_okey(m), m, bool(evals))
        return seen[key]

    def ok(sq, ball):
        return AG._legal_o(sq, ball) and all(sq[i] in cands[i] or i == ball for i in range(5))

    # the start: the table's own squares, each attacker in turn tried with the ball
    best = None
    for b in range(5):
        sq = list(base)
        sq[0], sq[b] = sq[b], sq[0]
        r = read(sq, b)
        if r and (best is None or r[0] > best[0]):
            best = (r[0], sq, b)
    if best is None:
        return None
    key, sq, ball = best
    steps, changed, rounds = [], True, 0
    while changed and rounds < 3 and time.time() < t_end:
        changed, rounds = False, rounds + 1
        for i in range(5):
            if time.time() >= t_end:
                break
            m = read(sq, ball)[1]
            allowed = sorted(B.sq(q) for q in (wood if i == ball else cands[i]))
            try:
                rows = AG.coverage(make(sq, ball, m[0], m[1]), only='offsweep', piece=i, keep=4, squares=allowed, quick=True) or []
            except ValueError:
                rows = []
            must = i != ball and sq[i] not in cands[i]      # ruled out as a starting square: he moves to a candidate
            for row in rows:
                q = B.parse_sq(row['sq'])
                trial = sq[:i] + [q] + sq[i + 1:]
                if q == sq[i] or not AG._legal_o(trial, ball):
                    continue
                r = read(trial, ball)
                if r and (must or r[0] > key):
                    steps.append(dict(o=i, to=row['sq'], why='a candidate square' if must and not r[0] > key else 'the plan is worth more'))
                    key, sq, changed, must = r[0], trial, True, False
    ranked = sorted(((k, list(p[0]), p[1]) for p, (k, m, full) in seen.items() if ok(list(p[0]), p[1])), key=lambda r: r[0], reverse=True)
    if not ranked:
        ranked = [(key, sq, ball)]
    # the level's variety (D-208): among the placements within its margin of the best, by the seed
    margin = AG.profile(level).get('variety_margin', 0)
    near = [r for r in ranked if r[0][0] >= ranked[0][0][0] - margin - 1e-9]
    pick = ranked[min(nth, len(ranked) - 1)] if nth else (rng.choice(near) if margin > 0 and len(near) > 1 else ranked[0])
    key, sq, ball = pick
    # the predicted defence for the placement locked in: its full setup where the time allows, else its quick one
    full = read(sq, ball, evals=240 if budget >= 8 else 0) or read(sq, ball)
    m = full[1]
    xs, arrows, perm = list(m[0]), list(m[1]), list(m[4] or range(5))
    state = make(sq, ball, xs, arrows)
    plan = read_plan(state, scout, perm, deep=True)
    checks = placement_checks(state, scout, plan)
    words = plan_words(plan)
    text = ' '.join(words) if words else 'Placed on its candidate squares against the defence it predicts.'
    return dict(squares=sq, ball=ball, value=round(float(full[0][0]), 2), plan=plan, words=words, text=text, steps=steps,
                candidates=len(seen), within=len(near), ranked=[dict(squares=[B.sq(q) for q in r[1]], ball=r[2], value=r[0][0]) for r in ranked[:6]],
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
    text = 'Matchups: ' + '; '.join(z['text'] for z in read) + '.' + (' Avoided: ' + '; '.join(z['text'] for z in avoided) + '.' if avoided else '')
    if watching:
        text += ' Watching: ' + '; '.join(z['text'] for z in watching) + '.'
    return dict(squares=pick['x'], arrows=pick['arrows'], perm=pm, value=round(pick['L'], 2), read=read, avoided=avoided, text=text, watching=watching,
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
    now = read_plan(state, scout, deep=bool(plan.get('screens')) and not state.screens)
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
        return dict(kind='chasing', line=f"Chasing: {new}{how}.", plan=dict(now, first=plan.get('first', plan)), worth=now['worth'])
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
