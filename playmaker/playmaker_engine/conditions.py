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
}

UNMEASURED = {
    '2': 'fronting needs the defender in front and a swing to change the angle: two phases the one-phase map does not hold',
    '3': 'three-quarter denial is a stance the board does not record',
    '8': 'a post-to-post cross screen: off-ball screens are read (23), but not which of two bigs it frees',
    '9b': 'the off-ball seal: the screen rule blocks the arrow, but the map does not yet test a seal on a passing lane',
    '11': 'the V-cut is two movements read as one: the map reads where he ends, not the defender worn out on the way',
    '12': 'the L-cut: as the V-cut',
    '14': 'backdoor: a denial stance is not recorded',
    '16': 'drift or lift on a drive: the kick-out target is read (45), not the drift that makes it',
    '17': 'relocate after passing: the next phase, beyond the one-phase reading',
    '19': 'clear out: read as isolation by spacing (19b)',
    '19c': 'dribble at to force the backdoor: as backdoor',
    '21': 'reject the screen: the defender cheating over is not recorded',
    '22': 're-screen: the next phase',
    '24': 'curl, fade or straight cut: the defender\'s chase is not recorded',
    '25': 'stagger: two screens in a row, beyond one screen read at a time',
    '26': 'screen the screener: as stagger',
    '27': 'back screen on the roller\'s defender: as stagger',
    '28': 'handoff: a short pass with a body in the way is read as a pass and a screen separately',
    '29': 'hold or pin: read inside the screens (20, 23)',
    '33': 'hesitate: freezing the defence is not in the map',
    '34': 'retreat dribble: traps are not recorded',
    '35': 'probe: the next phase',
    '38': 'create separation: read inside "outrun him" (31)',
    '39': 'swing: the next phase', '40': 'skip: read inside the pass chances (10)', '41': 'extra pass: the next phase',
    '42': 'entry angle: read inside the pass chances (10)', '43': 'pocket pass or lob: read inside the screens (20)',
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
