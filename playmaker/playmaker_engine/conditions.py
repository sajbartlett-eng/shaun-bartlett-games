"""Step 25 (Shaun, 19 Nov 2026; docs/reference/OFFENCE_CONDITIONS_19NOV.md): the offence's conditions.

Each condition is a way to create an advantage under the rules, read from the coverage map on the board as it stands:
who is involved, whether it is forming, and what it pays at its real chance. They are building blocks the plan combines
and rules in or out (the file's last section). None is a play to run (D-156). The defence reads the same conditions on
the same public board with its own model, and works to deny the ones forming.

Each detector returns a list of dict(id, name, o: [attackers], x: [defenders], worth: value at its real chance, sq,
why: plain words). worth is read from the map (the list's value times reach), never set by hand. A condition is ruled
in when its worth clears the bar for the next phase, and out (with the reason) when it doesn't, when there isn't time,
or when there aren't the tokens.

Conditions the map can't yet measure are listed in UNMEASURED with the reason, so nothing is claimed that isn't read.
"""
from . import board as B
from . import rules_config as RC

NAMES = {
    '1': 'post-up with the defender behind', '4': 'duck-in', '5': 'seal on the switch', '6': 'high-post flash',
    '7': 'dunker spot or short corner', '9': 'drag a defender', '10': 'open the passing angle', '13': 'basket cut',
    '15': 'flash cut', '18': 'space and occupy', '19b': 'isolation by spacing', '20': 'on-ball screen',
    '23': 'off-ball screen', '30': 'beat him off the dribble', '31': 'outrun him', '32': 'attack the closeout',
    '36': 'shoot over a weak contest', '37': 'punish the sag', '45': 'drive and kick', '46': 'drive and dump',
    '47': 'cut behind help', '49': 'overload a side', '49b': 'attack the gap (area-weighted defence)',
    '49d': 'overload an area (area-weighted defence)', '52': 'attack a foul-prone defender',
    '53': 'attack a tired or locked defender', '54': 'the closely guarded count', '55': 'three seconds',
    '57': 'the budget',
    # step 27 (D-258): read from the board read ahead (plan.horizon_read), turn by turn by the rules
    '20b': 'screen, then the dive', '9b': 'the off-ball seal', '11': 'the V-cut', '33': 'hesitate', '39': 'swing', '41': 'extra pass', '22': 're-screen', '17': 'relocate after passing',
    # step 28 (D-267): read from the defender's stance (his square and arrows against his man, the ball and the rim)
    '2': 'post entry against the front', '2b': 'the lob over the front', '3': 'post entry against the three-quarter denial',
    '14': 'backdoor', '19c': 'dribble at to force the backdoor', '21': 'reject the screen', '24': 'curl, fade or straight cut',
    '25': 'stagger', '26': 'screen the screener', '27': 'back screen on the roller\'s defender',
    # step 29 (D-271 to D-274): proposed additions for Shaun, read with the same measure (the map's own looks)
    '58': 'shot fake against a closeout', '59': 'pass fake against a likely Intercept', '60': 'pivot after the fake',
    '61': 'deep three dragging a defender out', '62': 'draw the foul on a fake',
}
PROPOSED = ('58', '59', '60', '61', '62')          # step 29: proposed for Shaun, not yet in his list

UNMEASURED = {
    '8': 'a post-to-post cross screen: off-ball screens are read (23), but not which of two bigs it frees',
    '12': 'the L-cut: as the V-cut',
    '16': 'drift or lift on a drive: the kick-out target is read (45), not the drift that makes it',
    '19': 'clear out: read as isolation by spacing (19b)',
    '28': 'handoff: a short pass with a body in the way is read as a pass and a screen separately',
    '29': 'hold or pin: read inside the screens (20, 23)',
    '34': 'retreat dribble: traps are not recorded',
    '35': 'probe: the next phase',
    '38': 'create separation: read inside "outrun him" (31)',
    '40': 'skip: read inside the pass chances (10)', '42': 'entry angle: read inside the pass chances (10)', '43': 'pocket pass or lob: read inside the screens (20)',
    '44': 'hit ahead: transition is not in the half-court game',
    '46b': 'baseline drive to the weak corner: read inside drive and kick (45)',
    '48': 'beat the double-team: read inside overloads (49)',
    '49c': 'flash where two areas meet: read inside flash cut (15)', '49e': 'skip over the shift: the next phase',
    '49f': 'inbound screen: only on a scenario card', '49g': 'the inbounder as a scorer once he steps in: only on a scenario card',
    '49h': 'the inbound lob: only on a scenario card',
    '50': 'force a switch: read inside the screens (20, 23)', '51': 'attack the helper: read inside drive and kick (45)',
    '56': 'don\'t clog the lanes: the search pays for every body in the way already',
}


def _sq(c):
    return B.parse_sq(c) if isinstance(c, str) else c


def _paint(q):
    return B.zone(q) == 'K'


def _best(sqs):
    if not sqs:
        return None, None
    k, lk = max(sqs.items(), key=lambda kv: (kv[1].get('worth', 0), kv[0]))
    return k, lk


# ---- step 28 (D-267): the defender's stance, from his square and arrows (no new rule, no new token) ----------------

STANCE_WORDS = {'front': 'fronts', 'three-quarter': 'plays three-quarter on', 'deny': 'denies', 'behind': 'plays behind',
                'beside': 'plays beside', 'off': 'sags off', 'over': 'cheats over the screen on', 'under': 'goes under the screen on'}


def _faces(state, d, target):
    from . import geometry as G
    rules = state.ctx.rules
    return G.faces(rules, G.stance(rules, state.arrows[d], any(b[1] == d for b in state.beaten)), state.x[d], target)


def _dir_to(a, b):
    """The one of the eight directions nearest the line from a to b (any distance)."""
    import math
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    return min(range(8), key=lambda k: (abs((math.atan2(B.DIRS[k][1], B.DIRS[k][0]) - ang + math.pi) % (2 * math.pi) - math.pi), k))


def stance(state, d, a):
    """Defender d's stance on attacker a, read from where he stands and where his arrows point, against a, the ball and
    the rim (plain words from the rules):
    - off: not next to him (he sags off);
    - front: next to him, between him and the ball (straight along the line from him to the ball), his arrow on him or
      the ball: a pass straight to him has to go over the defender;
    - three-quarter (a post in the paint) or deny (anyone else): next to him, on the ball's side but off that line by
      one direction, his arrow on him or the ball: the pass from the ball handler's side is cut, the other side is not;
    - behind: next to him, nearer the rim than he is and further from the ball, his arrow on him;
    - beside: next to him, anything else."""
    xd, oa = state.x[d], state.o[a]
    if not (B.on_board(xd) and B.on_board(oa)) or not B.adjacent(xd, oa):
        return 'off'
    bq = state.o[state.ball]
    if a == state.ball:
        return 'behind' if B.dist_rim(xd) < B.dist_rim(oa) else 'beside'
    to_ball, to_d = _dir_to(oa, bq), B.dir_between(oa, xd)
    eyes = _faces(state, d, oa) or _faces(state, d, bq)
    nearer_ball = B.cheb(xd, bq) < B.cheb(oa, bq)
    if nearer_ball and eyes and to_d == to_ball:
        return 'front'
    if nearer_ball and eyes and (to_d - to_ball) % 8 in (1, 7):
        return 'three-quarter' if _paint(oa) else 'deny'
    if B.dist_rim(xd) < B.dist_rim(oa) and not nearer_ball:
        return 'behind'
    return 'beside'


def screen_stance(state, d, i):
    """Defender d against a teammate's screener i next to him (a screen i can set on him): over (cheating over the top:
    he stands on the screener's high side, further from the rim) or under (between the screener and the rim)."""
    xd, oi = state.x[d], state.o[i]
    if not (B.on_board(xd) and B.on_board(oi)) or not B.adjacent(xd, oi) or i == state.ball:
        return None
    if B.dist_rim(xd) > B.dist_rim(oi):
        return 'over'
    if B.dist_rim(xd) < B.dist_rim(oi):
        return 'under'
    return None


def stances(state, perm):
    """Every defender's stance on his man (perm: defender -> attacker), and against any screener next to him whose
    screen his man could use. -> [dict(x, o, stance, text)]."""
    out = []
    for d, a in enumerate(perm or []):
        if a is None or a < 0 or not B.on_board(state.x[d]):
            continue
        st = stance(state, d, a)
        out.append(dict(x=d, o=a, stance=st, text=f"X{d + 1} {STANCE_WORDS[st]} O{a + 1}"))
        for i in range(5):
            if i in (a, state.ball) or not B.on_board(state.o[i]) or B.cheb(state.o[i], state.o[a]) > 3:
                continue
            ss = screen_stance(state, d, i)
            if ss:
                out.append(dict(x=d, o=a, screener=i, stance=ss, text=f"X{d + 1} {STANCE_WORDS[ss]} O{i + 1} (his man O{a + 1})"))
    return out


def read(state, scout, cov=None, roles=None, bar=0.0):
    """Every measured condition forming on this board, each with its worth at its real chance, ruled in or out.
    -> dict(found: [condition], in: [ids ruled in], out: [(id, why)], unmeasured: UNMEASURED)."""
    from . import agent as AG
    if AG.JS.get('coverage') is None or state.stage != 'play':
        return dict(found=[], ruled_in=[], ruled_out=[], unmeasured=dict(UNMEASURED))
    try:
        cov = cov or AG.coverage(state)
        roles = roles or AG.coverage(state, only='roles')
    except ValueError:
        return dict(found=[], ruled_in=[], ruled_out=[], unmeasured=dict(UNMEASURED))
    found = []
    squares = cov.get('squares') or [{}] * 5
    passes = cov.get('passes') or [None] * 5
    perm = (roles or {}).get('perm') or list(range(5))
    man_of = {d: a for d, a in enumerate(perm)}
    on_man = {a: d for d, a in enumerate(perm)}
    bh = state.ball
    ctx = state.ctx

    def add(cid, o, x, worth, sq, why):
        found.append(dict(id=cid, name=NAMES[cid], o=list(o), x=list(x), worth=round(float(worth), 2), sq=sq, why=why))

    for a in range(5):
        if not B.on_board(state.o[a]):
            continue
        sqs = squares[a] or {}
        d = on_man.get(a, -1)
        card = ctx.off[a]
        paint = {k: v for k, v in sqs.items() if _paint(_sq(k))}
        # A. posting: a post shot on or next to his own square, his defender beside or behind him
        here = sqs.get(B.sq(state.o[a]))
        if here and here.get('shot') == 'post' and d >= 0:
            behind = B.dist_rim(state.x[d]) >= B.dist_rim(state.o[a])
            add('1' if behind else '4', [a], [d], here['worth'], B.sq(state.o[a]),
                f"O{a + 1} posts X{d + 1} on {B.sq(state.o[a])}" + (' with him behind' if behind else ''))
            if d >= 0 and ctx.dfn[d].qs < card.qs or (d >= 0 and scout.contested(a, d, 'K')[0] > max(scout.contested(a, e, 'K')[0] for e in range(5) if e != d)):
                add('5', [a], [d], here['worth'], B.sq(state.o[a]), f"O{a + 1} has the smaller X{d + 1} on him in the post")
        # flashes and cuts into the paint or the high post: the map's own reach this phase
        if paint and a != bh:
            k, lk = _best(paint)
            if lk and lk.get('worth', 0) > 0:
                cover = lk.get('cover', -1)
                if cover >= 0 and cover != d and d >= 0:
                    add('47', [a], [d, cover], lk['worth'], k, f"O{a + 1} cuts to {k} behind the help: X{cover + 1} is the only cover, not his own X{d + 1}")
                elif not _paint(state.o[a]):
                    add('13', [a], [d] if d >= 0 else [], lk['worth'], k, f"O{a + 1} cuts to the rim at {k}")
                else:
                    add('7', [a], [d] if d >= 0 else [], lk['worth'], k, f"O{a + 1} sits on {k}, behind the help")
        mid = {k: v for k, v in sqs.items() if B.zone(_sq(k)) == 'M' and _sq(k)[0] in range(6, 11)}
        if mid and a != bh:
            k, lk = _best(mid)
            if lk and lk.get('worth', 0) > 0:
                add('6' if _sq(k)[1] >= 6 else '15', [a], [d] if d >= 0 else [], lk['worth'], k, f"O{a + 1} flashes to {k}")
        # D. shooting over a weak contest, punishing the sag
        k, lk = _best(sqs)
        if lk and lk.get('cover', -1) >= 0 and lk.get('worth', 0) > 0:
            cov_d = lk['cover']
            if lk['worth'] >= 0.6 * lk.get('value', 0):
                add('36', [a], [cov_d], lk['worth'], k, f"O{a + 1}'s {lk['shot']} on {k} over X{cov_d + 1}'s contest")
        if lk and lk.get('cover', -1) < 0 and lk.get('worth', 0) > 0:
            add('31', [a], [], lk['worth'], k, f"O{a + 1} gets to {k} before anyone can contest")
        # 10: the passing angle: the pass to him is not certain now
        ch = passes[a]
        if a != bh and ch is not None and 0 < ch < 1 and lk:
            add('10', [a, bh], [], lk.get('worth', 0) * (1 - ch), k, f"the pass from O{bh + 1} to O{a + 1} arrives {round(100 * ch)} in 100: a better angle is worth up to this")
        # G. hunting matchups: a foul-prone defender, a tired or locked one
        if d >= 0:
            fr = ctx.dfn[d].r.get('foul_contest', 0)
            if fr >= max(ctx.dfn[e].r.get('foul_contest', 0) for e in range(5)) and paint:
                kk, pl = _best(paint)
                add('52', [a], [d], pl.get('worth', 0) if pl else 0, kk, f"X{d + 1} fouls most on a contest: O{a + 1} attacks him inside")
            if state.rushed('X', d) or any(lk_[1] == d for lk_ in state.beaten):
                add('53', [a], [d], lk.get('worth', 0) if lk else 0, k, f"X{d + 1} is rushed or beaten this phase")
    # D. the ball handler: beat him off the dribble, attack the closeout
    d_bh = on_man.get(bh, -1)
    if d_bh >= 0 and B.on_board(state.x[d_bh]) and B.adjacent(state.x[d_bh], state.o[bh]):
        b = scout.beat(state, bh, d_bh, state.o[bh])
        if b:
            add('30', [bh], [d_bh], b['chance'] * max(0.0, b['biggest']), B.sq(state.o[bh]),
                f"O{bh + 1} beats X{d_bh + 1} off the dribble {round(100 * b['chance'])} in 100; it opens {b['squares']} squares")
        if state.rushed('X', d_bh):
            add('32', [bh], [d_bh], b['chance'] * max(0.0, b['biggest']) if b else 0, B.sq(state.o[bh]), f"X{d_bh + 1} is closing out off balance")
    # step 29 (D-272 to D-274, proposed): the fake, the pivot and deep range, from the same looks
    try:
        from .actions import fake_open
        from .scoring import p_fouls, p_foul, foul_rolls
        can_fake = fake_open(state.with_(side='O', turn_n=0)) if state.side == 'O' else False
        mine = squares[bh] or {}
        here = mine.get(B.sq(state.o[bh])) or {}
        if can_fake and d_bh >= 0 and here.get('worth', 0) > 0 and not B.adjacent(state.x[d_bh], state.o[bh]) \
                and B.cheb(state.x[d_bh], state.o[bh]) <= 1 + ctx.dfn[d_bh].qs:
            add('58', [bh], [d_bh], here['worth'], B.sq(state.o[bh]),
                f"O{bh + 1} can fake the shot: X{d_bh + 1} must close out with a Quick Step or Sprint and would arrive off balance")
        if can_fake:
            for a in range(5):
                ch = passes[a]
                if a != bh and ch is not None and 0 < ch < 1:
                    k2, lk2 = _best(squares[a] or {})
                    if lk2:
                        add('59', [bh, a], [], lk2.get('worth', 0) * (1 - ch), k2,
                            f"a pass fake to O{a + 1}: a defender who goes for the ball is locked for the phase")
        if (state.picked_up() or (can_fake and state.guard()[0] == 1)) and RC.pivot_rule(ctx.rules) and ctx.off[bh].qs > 0:
            near = {k: v for k, v in mine.items() if B.cheb(_sq(k), state.o[bh]) == 1}
            k3, lk3 = _best(near)
            if lk3 and lk3.get('worth', 0) > 0:
                add('60', [bh], [d_bh] if d_bh >= 0 else [], lk3['worth'], k3, f"O{bh + 1} pivots to {k3} after the pick-up")
        n_open = RC.deep_open(ctx)
        for a in range(5):
            for k4, v4 in (squares[a] or {}).items():
                dq = B.deep(_sq(k4))
                if dq and dq <= n_open and v4.get('worth', 0) > 0 and v4.get('cover', -1) >= 0:
                    add('61', [a], [v4['cover']], v4['worth'], k4, f"O{a + 1}'s deep three on {k4} ({dq} off) pulls X{v4['cover'] + 1} out to cover it")
        if can_fake and d_bh >= 0 and B.adjacent(state.x[d_bh], state.o[bh]):
            fb = ctx.dfn[d_bh].r.get('foul_block', 0)
            pf = float(p_fouls(p_foul(fb, ctx.rules), foul_rolls(ctx.rules, state.x[d_bh], state.o[bh])))
            add('62', [bh], [d_bh], pf * RC.STEAL_FOUL_BONUS, B.sq(state.o[bh]),
                f"a shot fake: if X{d_bh + 1} goes for the block he fouls {round(100 * pf)} in 100 (+5, play on) and is locked")
    except Exception:
        pass
    # F. the help chain: overloads the offence creates one after another (step 25, D-241)
    for ov in cov.get('overloads') or []:
        th = ov.get('threats') or []
        if len(th) < 2:
            continue
        first, left = th[0], th[-1]
        kind = '46' if _paint(_sq(left['sq'])) and left['shot'] in ('layup', 'dunk', 'post') else '45'
        xs = list(ov.get('xs') or [])
        add(kind, [first['o'], left['o']], xs, ov['value'], left['sq'],
            f"{' and '.join(f'X{z + 1}' for z in xs)} can't cover O{first['o'] + 1} and O{left['o'] + 1} one after the other: the pass to O{left['o'] + 1} on {left['sq']}")
        if len(th) >= 3:
            add('49', [t['o'] for t in th], xs, ov['value'], left['sq'], f"{len(th)} attackers on {len(xs)} defender{'s' if len(xs) > 1 else ''}")
    # B. attention: a defender held by his man, one dragged away, isolation by spacing
    held = []
    for r in (roles or {}).get('roles') or []:
        if r['kind'] in ('man', 'both') and r.get('with', 0) > 0:
            held.append(r)
            add('18', [r['man']], [r['x']], r.get('open', 0) - r.get('with', 0), B.sq(state.o[r['man']]),
                f"O{r['man'] + 1} holds X{r['x'] + 1}: his look is worth {round(r.get('open', 0))} open")
    far = [r for r in held if B.cheb(state.x[r['x']], state.o[bh]) >= 5]
    if d_bh >= 0 and len(far) >= 3:
        k, lk = _best(squares[bh] or {})
        add('19b', [bh], [d_bh], lk.get('worth', 0) if lk else 0, k,
            f"{len(far)} defenders held five or more squares from O{bh + 1}: X{d_bh + 1} has him with the help far away")
    # F2. area-weighted defence: defenders whose pull leans to gaps
    sag = [r for r in (roles or {}).get('roles') or [] if r['kind'] == 'sag' or (r['kind'] == 'free' and not r.get('way'))]
    if len(sag) >= 2:
        area = [(_best(squares[r['man']] or {}), r) for r in sag]
        k, lk = _best(squares[bh] or {})
        add('49b', [bh], [r['x'] for r in sag], lk.get('worth', 0) if lk else 0, k,
            f"{' and '.join(f'X{r['x'] + 1}' for r in sag)} lean to areas, not men: attack the gap between them")
        (k2, lk2), r2 = max(area, key=lambda z: (z[0][1] or {}).get('worth', 0))
        if lk2:
            add('49d', [r2['man']], [r['x'] for r in sag], lk2.get('worth', 0), k2,
                f"O{r2['man'] + 1} is left to the area: an overload there leaves him free on {k2}")
    # S. step 28 (D-267): the stances, and what each one gives the offence, by the same measure (worth at its real chance)
    from . import decide as D
    for z in stances(state, perm):
        d, a, st = z['x'], z['o'], z['stance']
        sqs = squares[a] or {}
        paint = {k: v for k, v in sqs.items() if _paint(_sq(k))}
        pk, pl = _best(paint)
        pw = (pl or {}).get('worth', 0)
        if st in ('front', 'three-quarter') and a != bh and pl:
            # the entry from another angle: each teammate's pass to him, if that teammate had the ball, by the rules
            alts = []
            for k2 in range(5):
                if k2 in (a, bh) or not B.on_board(state.o[k2]):
                    continue
                try:
                    alts.append((D.cov_pass(state.with_(ball=k2), a, state.o[a]), k2))
                except (ValueError, IndexError):
                    continue
            ch, k2 = max(alts, default=(0.0, -1))
            if k2 >= 0 and ch > 0:
                add('2' if st == 'front' else '3', [a, k2], [d], ch * pw, pk,
                    f"X{d + 1} {STANCE_WORDS[st]} O{a + 1}: the entry from O{k2 + 1} lands {round(100 * ch)} in 100, to his {pl['shot']} on {pk}")
            if st == 'front':
                ch0 = passes[a] or 0
                if ch0 > 0:
                    add('2b', [a, bh], [d], ch0 * pw, pk, f"X{d + 1} fronts O{a + 1}: the pass over the top lands {round(100 * ch0)} in 100")
        if st == 'deny' and pl:
            add('14', [a], [d], pw, pk, f"X{d + 1} denies O{a + 1}: the backdoor cut to {pk}")
            if B.cheb(state.o[bh], state.o[a]) <= 3:
                add('19c', [bh, a], [d], pw, pk, f"O{bh + 1} dribbles at O{a + 1} to force X{d + 1}'s denial: the backdoor to {pk}")
        if st in ('over', 'under') and z.get('screener') is not None:
            i = z['screener']
            if a == bh:
                away = {k: v for k, v in (squares[bh] or {}).items() if B.cheb(_sq(k), state.o[i]) > B.cheb(state.o[bh], state.o[i])}
                ak, al = _best(away)
                if st == 'over' and al:
                    add('21', [bh, i], [d], al.get('worth', 0), ak, f"X{d + 1} cheats over O{i + 1}'s screen: O{bh + 1} rejects it, away to {ak}")
            else:
                three = {k: v for k, v in sqs.items() if v.get('shot') == 'three'}
                tk, tl = _best(three)
                if st == 'over' and pl:
                    add('24', [a, i], [d], pw, pk, f"X{d + 1} trails O{a + 1} over O{i + 1}'s screen: he curls to {pk}")
                elif st == 'under' and tl:
                    add('24', [a, i], [d], tl.get('worth', 0), tk, f"X{d + 1} goes under O{i + 1}'s screen: O{a + 1} fades to {tk}")
    # H. what the offence must manage
    held_n = (state.grd >> 2) & 3
    if (state.grd & 3) == 2 or held_n:
        add('54', [bh], [], -5 * min(3, held_n + 1) / 3, B.sq(state.o[bh]), f"O{bh + 1} has picked the ball up: the count is {held_n + 1} of 3")
    key = [a for a in range(5) if B.on_board(state.o[a]) and _paint(state.o[a])]
    if key:
        add('55', key, [], -5, None, f"{' and '.join(f'O{a + 1}' for a in key)} in the key: out before two phase ends")
    left_tok = state.tok_o if state.side == 'O' else RC.TOKENS_PER_PHASE
    add('57', [], [], 0, None, f"{left_tok} actions left this phase; passes {state.count('O', 'pass')} of {RC.LIMITS['O']['pass']}, "
                                f"screens {state.count('O', 'screen')} of {RC.LIMITS['O']['screen']}, dribbles {state.count('O', 'dribble')} of {RC.LIMITS['O']['dribble']}")
    # ruled in or out (the file's last section)
    ruled_in, ruled_out = [], []
    phases_left = state.clock // RC.PHASE_SECONDS - 1
    for c in found:
        if c['id'] in ('54', '55', '57', '18'):
            continue                                     # what the offence must manage, and attention: always read
        if c['worth'] <= bar + 1e-9:
            ruled_out.append((c['id'], f"worth {round(c['worth'])} at its real chance: not above the bar of {round(bar)}"))
        elif phases_left < 1 and c['id'] in ('13', '15', '6', '7', '47', '23', '20'):
            ruled_out.append((c['id'], 'no phase left to get there'))
        else:
            ruled_in.append(c['id'])
            c['ruled_in'] = True
    return dict(found=found, ruled_in=sorted(set(ruled_in)), ruled_out=ruled_out, unmeasured=dict(UNMEASURED))


def screens_as_conditions(screens, state):
    """The plan's screens (plan.screen_roles) as conditions 20 (on the ball handler's defender) and 23 (off the ball)."""
    out = []
    for z in screens or []:
        on_ball = z['x'] in [d for d, q in enumerate(state.x) if B.on_board(q) and B.adjacent(q, state.o[state.ball])]
        cid = '20' if on_ball else '23'
        out.append(dict(id=cid, name=NAMES[cid], o=[z['o']], x=[z['x']], worth=z['value'], sq=z['sq'], ruled_in=True,
                        why=f"O{z['o'] + 1} screens X{z['x'] + 1} from {', '.join(z['squares'])}"))
    return out


def words(cond):
    return f"{cond['name'].capitalize()}: {cond['why']} (worth {round(cond['worth'])})."


def _screened(p):
    """The defender a read-ahead screen is set on (its own words: "O4 screens X5 from I3")."""
    w = p.get('offence') or ''
    if ' screens X' not in w:
        return None
    try:
        return int(w.split(' screens X')[1].split()[0]) - 1
    except ValueError:
        return None


def _guards(state, d):
    """The attacker defender d is nearest to (the board's own reading of who he guards, for the read-ahead's words)."""
    xd = state.x[d]
    return min(range(5), key=lambda a: (B.cheb(xd, state.o[a]), a)) if B.on_board(xd) else -1


def ahead(h, state):
    """Step 27 (D-258): the conditions the board read ahead shows, each from the route itself (plan.horizon_read):
    every turn played by the rules, the defence's answer by its own reading, the list read again. A condition is named
    only where its turn raises what the offence threatens (the list's largest item) above the turn before it.
    -> [dict(id, name, turn, why)]."""
    out = []
    if not h or not h.get('path'):
        return out
    prev = list(h['first'][0][:5]) if isinstance(h.get('first'), tuple) else list(h.get('first') or [0])
    path = h['path']
    for k, p in enumerate(path):
        nxt = path[k + 1] if k + 1 < len(path) else None
        rise = (p['list'] or [0])[0] > (prev or [0])[0] + 1e-9 or (nxt is not None and (nxt['list'] or [0])[0] > (p['list'] or [0])[0] + 1e-9)
        kind, o, dest, tgt = p['act']
        add = lambda cid, why: out.append(dict(id=cid, name=NAMES[cid], turn=p['turn'], o=o, why=why))
        if kind == 'screen':
            prev_s = [q for q in path[:k] if q['act'][0] == 'screen']
            add('22' if any(q['act'][1] == o for q in prev_s) else '20b',
                f"O{o + 1} screens; the next turn reads {(nxt or p)['list'][0]:g} after the defence answers")
            if prev_s and prev_s[-1]['act'][1] != o:
                # step 28 (D-267): two screens in a row by two screeners: a stagger; on the first screener's own defender,
                # screening the screener; and a back screen on the roller's defender when the first screener then rolls
                first = prev_s[-1]
                mine = _screened(p)
                if mine is not None and _guards(state, mine) == first['act'][1]:
                    rolls = any(q['act'][1] == first['act'][1] and q['act'][0] in ('move', 'qs', 'sprint') for q in path[k + 1:])
                    add('27' if rolls else '26', f"O{o + 1} screens X{mine + 1}, the defender of the screener O{first['act'][1] + 1}")
                else:
                    add('25', f"O{first['act'][1] + 1} then O{o + 1}: two screens in a row")
        elif p.get('fake'):
            # step 30: the fake read ahead in the route itself (the defence's reply by its own mix, then the list again)
            add('58' if kind == 'shot' else '59', f"O{o + 1} fakes; the defence replies ({', '.join(p.get('defence') or []) or 'it holds'}) "
                f"and the board then reads {p['list'][0]:g}")
        elif kind == 'pass':
            two = k > 0 and path[k - 1]['act'][0] == 'pass' and not path[k - 1].get('fake')
            add('41' if two else '39', f"O{o + 1} to O{tgt + 1}; the board then reads {p['list'][0]:g}")
            if nxt is not None and nxt['act'][1] == o and nxt['act'][0] in ('move', 'qs', 'sprint'):
                add('17', f"O{o + 1} moves on after his pass")
        elif kind == 'hesitate':
            add('33', f"the defence answers the Hesitate and the board reads {p['list'][0]:g}")
        elif kind in ('move', 'qs', 'sprint') and dest:
            q = B.parse_sq(dest)
            beside = [d for d, x in enumerate(state.x) if B.on_board(x) and B.adjacent(x, q)]
            if nxt is not None and nxt['act'][0] == 'pass' and not nxt.get('fake') and nxt['act'][3] == o and beside:
                add('9b', f"O{o + 1} steps beside X{beside[0] + 1} on {dest}, then the pass comes to him")
            elif p.get('moved'):
                add('11', f"O{o + 1} moves to {dest} and X{p['moved'][0] + 1} answers; the next turn reads {(nxt or p)['list'][0]:g}")
        prev = p['list']
        if not rise:
            out.pop() if out and out[-1]['turn'] == p['turn'] else None
    return out
