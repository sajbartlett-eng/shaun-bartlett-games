"""Step 31 (D-284, Shaun, 25 Nov 2026): the possession's value. The Python engine's copy of engine.js possRead and
possParts; the two must agree on every board (tests/test_exam.py, check B2).

"Take every look the offence can get, best first. Each has a chance of being open in time. The offence takes the best
one that opens. Take off the risks, add the fouls drawn, and read ahead over the phases left." One number, both sides:
the offence acts to raise it, the defence to lower it. On the game's own scale (rating less contest, times points; a
turnover -5, a foul +5).

The looks are the map's (decide.Read.map_options). Looks that share a cause are one route (D-294): one attacker's
squares are one route, the looks behind a pass are that pass, the looks behind a Dribble are that Dribble. A route that
needs a roll ends the turn, so falling back is limited by the actions: a lost pass is -5 and the phase; a lost Dribble
costs nothing and he may still pass from where he stands, off balance. An open look is taken when it beats playing on.
Playing on is the shot bar, counted from the same looks: U(0) = -5 (the shot clock runs out); U(n) = the best route when
playing on is worth U(n - 1); with k phases after this one the possession is worth U(k + 1). A blocked shot is -5 and
the phase, then worth what that later phase is (carry-over 1: the block read past the -5, the same way everywhere).
The defence's answer is inside the number: with the actions it has left this phase it closes what it can, one
defender's movement at a time, each the one that leaves the least, until none lowers it."""
from . import board as B, rules_config as RC

OUT = -5.0                                   # D-198: the shot clock runs out: -5, nothing left to play
NEG = float('-inf')
BOUND_LOOKS = 2
BRUTE = [False]                              # a test's switch: every movement read in full, no cut
CHECK = [False, 0, 0]                        # a test's switch (step 31, fix 1): every candidate read both ways; [on, read, different]


def three_seconds_leave(s):
    """engine.js threeSecondsLeave: the attackers standing in the key without the ball (each must spend an action to
    leave before the second phase end finds him there) -> (already counted once, all of them, their bitmask)."""
    now = nxt = mask = 0
    if RC.app_rule(s.ctx.rules, 'three_seconds'):
        for i in range(5):
            if i == s.ball or not B.in_key(s.o[i]):
                continue
            nxt += 1
            mask |= 1 << i
            if (s.key_o >> i) & 1:
                now += 1
    return now, nxt, mask


def three_seconds_stuck(s):
    """engine.js threeSecondsStuck: the attackers decide.three_seconds_owed counts, as a bitmask."""
    from .actions import can_move_kind
    if not RC.app_rule(s.ctx.rules, 'three_seconds') or not s.key_o:
        return 0
    m = 0
    for i in range(5):
        if not (s.key_o >> i) & 1 or not B.in_key(s.o[i]):
            continue
        if not (s.tok_o > 0 and any(can_move_kind(s, 'O', i, k) for k in ('move', 'qs', 'sprint'))):
            m |= 1 << i
    return m


def _route_t(L, V, b, Bv, left, key_mask, cut, vec=None, act=None, it=0):
    """engine.js routeT: the best route's worth when playing on is worth Bv."""
    best, fall, fi = Bv, Bv, -1
    if vec is not None:
        for k in range(6):
            vec[k] = NEG
    for i, o in enumerate(L):                    # the passes first: a lost Dribble may fall back on one
        v = V[i]
        if o['a'] == b or v == NEG or o['n0'] > left + ((key_mask >> o['a']) & 1):
            continue
        r = o['r']
        e = r * (v if v > Bv else Bv) + (1 - r) * (Bv - o['lc'])
        if e > best:
            best = e
        if vec is not None and e > vec[o['a']]:
            vec[o['a']] = e
        if o['p0'] > 0 and o['n0'] + 1 <= left + ((key_mask >> o['a']) & 1):
            p = 1 if o['p0'] >= 1 else max(0, o['p0'] - cut)
            f = p * (v if v > Bv else Bv) + (1 - p) * (Bv - o['lc'])
            if f > fall:
                fall, fi = f, i
    for i, o in enumerate(L):
        v = V[i]
        if o['a'] != b or v == NEG or o['n0'] > left:
            continue
        e = (o['r'] * (v if v > Bv else Bv) + (1 - o['r']) * fall) if o['dr'] else (v if v > Bv else Bv)
        if e > best:
            best = e
        if vec is not None:
            k = 5 if o['dr'] else b
            if e > vec[k]:
                vec[k] = e
    if act is not None and best > Bv + 1e-9:
        via = False
        for i, o in enumerate(L):
            v = V[i]
            if v == NEG:
                continue
            if o['a'] != b:
                if o['n0'] > left + ((key_mask >> o['a']) & 1):
                    continue
                e = o['r'] * (v if v > Bv else Bv) + (1 - o['r']) * (Bv - o['lc'])
            else:
                if o['n0'] > left:
                    continue
                e = (o['r'] * (v if v > Bv else Bv) + (1 - o['r']) * fall) if o['dr'] else (v if v > Bv else Bv)
                if o['dr'] and e >= best - 1e-9:
                    via = True
            if e >= best - 1e-9:
                act.append((i, it))
        if via and fi >= 0:
            act.append((fi, it))
    return best


def _top_count(vec, U):
    return sum(1 for v in vec if v >= U - 1e-9)


_SVMAP = {}
_MISS = object()


_STEP_G = {}
_SU = {}


def _step_union(p, qs, move_ok, qs_ok, rules):
    """engine.js stepUnion: every square any path of one phase's movement from p can cross."""
    key = (p, qs, move_ok, qs_ok, rules)
    if key not in _SU:
        u, M = set(), []
        if move_ok:
            for pa in B.move_paths(p, rules):
                u.update(pa)
                M.append(pa[-1])
        if qs_ok and qs > 0:
            Q = []
            for pa in B.qs_paths(p, qs, rules):
                u.update(pa)
                Q.append(pa[-1])
            for m1 in M:
                for pa in B.qs_paths(m1, qs, rules):
                    u.update(pa)
            if move_ok:
                for q1 in Q:
                    for pa in B.move_paths(q1, rules):
                        u.update(pa)
                for _d, pa in B.sprint_paths(p, qs, rules):
                    u.update(pa)
        _SU[key] = tuple(sorted(u))
    return _SU[key]


class _RaceLook:
    """(a drive's race look: no Contest of its own; its worth is the race's)"""
    types = ('race',)
    rushed = True


def race_kit(r, Lmap, sr, T):
    """Step 31, fix 3c (engine.js raceKit): the drive's race, read from an advantage. See engine.js for the rules it
    reads; this is the same reading, step for step."""
    from itertools import permutations
    from .decide import Look, cov_pass, SHOOT, INF
    from .scoring import shot_zone, card_shot
    s, rules = r.s, r.rules
    ctx, b = s.ctx, s.ball
    h0 = s.o[b]
    no_rim = RC.rim_shot_barred(rules)
    occ = set(q for q in s.o if B.on_board(q)) | set(q for q in s.x if B.on_board(q))
    qo0 = max(0, RC.LIMITS['O']['qs'] - sr.count('O', 'qs'))
    qd0 = max(0, RC.LIMITS['X']['qs'] - sr.count('X', 'qs'))
    mode = 0 if rules.zone == 'off' else 1

    def clear(pa, me):
        return all(B.on_board(q) and (q == me or q not in occ) for q in pa)

    step_memo = {}

    def step(p, qs, me, move_ok, qs_ok):
        sk = (p, qs, me, move_ok, qs_ok)
        if sk not in step_memo:
            # fix 3d (engine.js step): kept across boards under the taken squares its paths can cross
            gk = (p, qs, move_ok, qs_ok, tuple(q for q in _step_union(p, qs, move_ok, qs_ok, rules) if q != me and q in occ))
            hit = _STEP_G.get(gk)
            if hit is None:
                if len(_STEP_G) > 120000:
                    _STEP_G.clear()
                hit = _STEP_G[gk] = step_calc(p, qs, me, move_ok, qs_ok)
            step_memo[sk] = hit
        return step_memo[sk]

    def step_calc(p, qs, me, move_ok, qs_ok):
        M = []
        seen = set()
        if move_ok:
            for pa in B.move_paths(p, rules):
                if clear(pa, me):
                    d = pa[-1]
                    if d not in seen:
                        seen.add(d)
                        M.append(d)
        if qs_ok and qs > 0:
            Q = []
            for pa in B.qs_paths(p, qs, rules):
                if clear(pa, me):
                    seen.add(pa[-1])
                    Q.append(pa[-1])
            for m1 in M:
                for pa in B.qs_paths(m1, qs, rules):
                    if clear(pa, me):
                        seen.add(pa[-1])
            if move_ok:
                for q1 in Q:
                    for pa in B.move_paths(q1, rules):
                        if clear(pa, me):
                            seen.add(pa[-1])
                for _d, pa in B.sprint_paths(p, qs, rules):
                    if clear(pa, me):
                        seen.add(pa[-1])
        seen.discard(p)
        return seen

    def bfs(start, qs, me, move0, qs0, qs_later):
        dist = {start: 0}
        front = [start]
        t = 1
        while t <= T and front:
            nx = []
            for p in front:
                for q in step(p, qs, me, move0 if t == 1 else True, qs0 if t == 1 else qs_later):
                    if q not in dist:
                        dist[q] = t
                        nx.append(q)
            front = nx
            t += 1
        return dist
    man, best = list(range(5)), None
    for pr in permutations(range(5)):
        sm = sum(B.cheb(s.x[d], s.o[pr[d]]) if (B.on_board(s.x[d]) and B.on_board(s.o[pr[d]])) else 0 for d in range(5))
        if best is None or sm < best:
            best, man = sm, list(pr)
    guard = [-1] * 5
    for d in range(5):
        guard[man[d]] = d
    DQ = [(bfs(s.x[e], ctx.dfn[e].qs, s.x[e], True, qd0 > 0, True) if B.on_board(s.x[e]) else None) for e in range(5)]
    DM = [(bfs(s.x[e], ctx.dfn[e].qs, s.x[e], True, False, False) if B.on_board(s.x[e]) else None) for e in range(5)]
    shots = {}

    def shot(sq):
        if sq not in shots:
            z = shot_zone(ctx, sq)
            if z not in SHOOT or (no_rim and sq == RC.RIM):        # (no shot from a square nobody may shoot from)
                shots[sq] = (None, 0, [])
                return shots[sq]
            lk = Look(b, sq, 'later', 1.0, False)
            lk.types = RC.ZONE_SHOTS[z]
            lk.rushed = False
            pts = RC.worth_now(ctx, z)
            shots[sq] = (lk, pts, [pts * card_shot(ctx, ctx.off[b], ty, sq) for ty in lk.types])
        return shots[sq]
    ROW0 = (0,) + (INF,) * 5
    NOSET = (INF,) * 6

    def vs(sq, e, setc):
        lk, _p, opn = shot(sq)
        if lk is None:
            return NEG
        cv = r._vals_map(lk, e, (ROW0, ROW0 if setc else NOSET, 1, 1 if setc else 0))
        hi = NEG
        for t, ty in enumerate(lk.types):
            v = cv[ty] if (cv and ty in cv and cv[ty] < opn[t]) else opn[t]
            if v > hi:
                hi = v
        return hi

    def chase_v(sq, j, pen, rushed):
        lk, pts, opn = shot(sq)
        dc = ctx.dfn[j]
        hi = NEG
        if lk is None:
            return hi
        for t, ty in enumerate(lk.types):
            rr = card_shot(ctx, ctx.off[b], ty, sq)
            con = dc.con(ty) - pen - (2 if rushed else 0)
            if con < 1:
                con = 1
            v = max(0, pts * (rr - con))
            u = v if v < opn[t] else opn[t]
            if u > hi:
                hi = u
        return hi

    def open_v(sq):
        return max(shot(sq)[2], default=NEG)

    def legal(q):
        return B.on_board(q) and shot_zone(ctx, q) in SHOOT and not (no_rim and q == RC.RIM)
    pc, kc, sorted_w = {}, {}, {}

    def worth_of(o, e):
        w = NEG
        for t, ty in enumerate(o['lk'].types):
            v = o['open'][t]
            for d in range(5):
                x = o['vals'][d]
                if d != e and x and ty in x and x[ty] < v:
                    v = x[ty]
            if v > w:
                w = v
        return w + o['adj']
    by_a = [[] for _ in range(5)]
    for o in Lmap:
        by_a[o['a']].append(o)

    def kick(sq, left):
        key = (sq, left)
        if key in kc:
            return kc[key]
        hit = [NEG, -1, None]
        sb = s.with_(o=tuple(sq if i == b else s.o[i] for i in range(5)))
        for a in range(5):
            if a == b or not B.on_board(s.o[a]):
                continue
            without = left if guard[a] == left else -1
            ws = sorted_w.get((a, without))              # (fix 3d: each man's looks sorted once a board)
            if ws is None:
                ws = sorted_w[(a, without)] = sorted(((worth_of(o, without), o) for o in by_a[a]), key=lambda x: (-x[0], x[1]['c'], x[1]['q0']))
            for w, o in ws:
                if w <= hit[0]:
                    break
                if o['c'] == sq or o['q0'] == sq:
                    continue
                k2 = (sq, o['q0'], a)
                if k2 not in pc:
                    pc[k2] = cov_pass(sb, a, o['q0'])
                pp = pc[k2]
                ev = pp * w - (1 - pp) * 5
                if ev > hit[0]:
                    hit = [ev, a, o['c']]
        kc[key] = hit
        return hit

    def front(c):
        out = []
        for d in range(8):
            f = B.add(c, B.DIRS[d])
            if B.on_board(f) and B.dist_rim(f) < B.dist_rim(c) and not (f in occ and f not in s.x):
                out.append(f)
        return out

    shared = {}

    def race(c0, j, dj, dmj, qo_first, first_ok, w0, move_first=True):
        shr = shared.setdefault(id(dj), ({}, dj))  # (fix 3d: states after phase 0 shared by races with the same chaser)
        memo0 = {}

        def V(t, c, spent, w):
            key = (t, c, spent, w)
            memo = shr[0] if t >= 1 else memo0   # (fix 3d, memory: worths only; engine.js rebuilds its report's line)
            if key in memo:
                return memo[key]
            memo[key] = NEG
            opts = []
            chase, how = float('inf'), None
            for d in range(8):
                a = B.add(c, B.DIRS[d])
                if not B.on_board(a):
                    continue
                k = dj.get(a)
                if k is None or k > t:
                    continue
                pen = 3 if (t > 0 and B.dist_rim(a) <= B.dist_rim(c)) else 6
                km = dmj.get(a)
                rushed = not (km is not None and km <= t)
                v = chase_v(c, j, pen, rushed)
                if v < chase:
                    chase, how = v, (a, pen, rushed)
            alone = min(chase, open_v(c))
            nxt = []
            if t < T and t == 0 and not move_first:      # (no movement left: phase 0 ends with him here)
                nxt.append(c)
            elif t < T:
                for q in step(c, ctx.off[b].qs, s.o[b], True, (qo_first > 0) if t == 0 else True):
                    if legal(q) and B.dist_rim(q) < B.dist_rim(c) and (t > 0 or first_ok(q)):
                        nxt.append(q)
            nxt.sort()
            carry, carry_to = NEG, None
            for q in nxt:
                v = V(t + 1, q, spent, 0)
                if v > carry:
                    carry, carry_to = v, q
            hes = V(t + 1, c, spent, 0) if (t < T and not w) else NEG
            home = kick(c, -1)
            opts.append(dict(by=-1, how='stay home', shoot=alone, kick=home, carry=carry, carry_to=carry_to, hes=hes, worth=max(alone, home[0], carry, hes)))
            for e in range(5):
                if e == j or (spent >> e) & 1 or DQ[e] is None:
                    continue
                kc2 = km2 = float('inf')
                for f in front(c):
                    k = DQ[e].get(f)
                    if k is not None and k < kc2:
                        kc2 = k
                    k2 = DM[e].get(f)
                    if k2 is not None and k2 < km2:
                        km2 = k2
                if kc2 <= t:
                    setc = km2 <= t
                    sh = min(vs(c, e, setc), chase)
                    kk = kick(c, e)
                    fk = V(t, c, spent | (1 << e), 1) if (kc2 >= 1 and kc2 == t and not w) else NEG
                    opts.append(dict(by=e, how='contain' if setc else 'contain, rushed', shoot=sh, kick=kk, fake=fk, worth=max(sh, kk[0], fk)))
                    continue
                ka = float('inf')
                for d in range(8):
                    a = B.add(c, B.DIRS[d])
                    if not B.on_board(a):
                        continue
                    k = DQ[e].get(a)
                    if k is not None and k < ka:
                        ka = k
                if ka <= t:
                    sh = min(vs(c, e, False), chase)
                    kk = kick(c, e)
                    opts.append(dict(by=e, how='help late', shoot=sh, kick=kk, carry=carry, worth=max(sh, kk[0], carry)))
            pick = opts[0]
            for o in opts:
                if o['worth'] < pick['worth'] - 1e-12:
                    pick = o
            memo[key] = pick['worth']
            return pick['worth']
        v0 = V(0, c0, 0, 1 if w0 else 0)
        return dict(v=v0, qo0=qo0, qd0=qd0)
    w0 = sr.count('O', 'hesitate') >= RC.LIMITS['O']['hesitate']
    return dict(man=man, guard=guard, bfs=bfs, step=step, race=race, qo0=qo0, qd0=qd0, occ=occ, legal=legal, w0=w0)


def drive_races(r, Lmap, T, sr):
    """Step 31, fix 3c (engine.js driveRaces): a drive's race from each advantage the board holds: a Dribble won, an
    open or partial lane, speed. (The shot fake beating a closeout is read inside the fake mix.)"""
    from .actions import can_move_kind
    from .decide import lane_squares
    s = r.s
    ctx, b = s.ctx, s.ball
    h0 = s.o[b]
    out = []
    if not B.on_board(h0) or s.pending or sr.pending or sr.stage != 'play':
        return out
    K = race_kit(r, Lmap, sr, T)
    jm = K['guard'][b]
    allq = lambda q: True
    for a, j in sr.beaten:
        if a != b or not B.on_board(s.x[j]):
            continue
        q = ctx.dfn[j].qs
        dj = K['bfs'](s.x[j], q, s.x[j], False, K['qd0'] > 0, True)
        dmj = K['bfs'](s.x[j], q, s.x[j], False, False, False)
        out.append(dict(kind='Dribble won', beaten=j, start=h0, p=1.0, **K['race'](h0, j, dj, dmj, K['qo0'], allq, K['w0'])))
    if out or jm < 0 or not B.on_board(s.x[jm]):
        return [_finish_race(x, b, h0) for x in out]
    qj = ctx.dfn[jm].qs
    dj_full = K['bfs'](s.x[jm], qj, s.x[jm], True, K['qd0'] > 0, True)
    dm_full = K['bfs'](s.x[jm], qj, s.x[jm], True, False, False)
    cov = {s.x[jm]}
    dc = ctx.dfn[jm]
    arrs = [s.arrows[jm], (s.arrows[jm] + 1) % 8] if ctx.rules.zone != 'off' else [s.arrows[jm]]
    for d in arrs:
        diag = d & 1
        R = max(2 if diag else 3, dc.qs, ((2 if diag else 3) + dc.qs) if dc.qs > 0 else 0)
        q = s.x[jm]
        for _n in range(R):
            q = B.add(q, B.DIRS[d])
            if not B.on_board(q) or (q != s.x[jm] and q in K['occ']):
                break
            cov.add(q)
    lane = sorted(lane_squares(h0, RC.RIM, 0.5), key=lambda q: (-B.dist_rim(q), q))
    if lane and lane[0] not in cov:
        full = all(q not in cov for q in lane)

        def ok(q):
            return q not in cov and all(x not in cov for x in lane_squares(h0, q, 0.5))
        out.append(dict(kind='open lane' if full else 'partial lane', beaten=jm, start=h0, p=1.0, **K['race'](h0, jm, dj_full, dm_full, K['qo0'], allq if full else ok, K['w0'])))
    if K['qo0'] > 0 and ctx.off[b].qs > 0 and not sr.quick_stepped('O', b):
        # fix 3d (engine.js, the rules): a Quick Step leaves him his Move; he may Move on at once (then nothing is left
        # this phase); a Sprint is both
        qs = ctx.off[b].qs
        starts, qs_dest = {}, []
        can_move_o = can_move_kind(sr, 'O', b, 'move')
        for pa in B.qs_paths(h0, qs, ctx.rules):
            if all(B.on_board(q) and q not in K['occ'] for q in pa) and pa[-1] not in starts:
                starts[pa[-1]] = can_move_o
                qs_dest.append(pa[-1])
        if can_move_o:
            for s1 in sorted(qs_dest):
                for pa in B.move_paths(s1, ctx.rules):
                    if all(B.on_board(q) and (q == h0 or q not in K['occ']) for q in pa) and pa[-1] != h0 and pa[-1] not in starts:
                        starts[pa[-1]] = False
        if can_move_kind(sr, 'O', b, 'sprint'):
            for _d, pa in B.sprint_paths(h0, qs, ctx.rules):
                if all(B.on_board(q) and q not in K['occ'] for q in pa) and pa[-1] not in starts:
                    starts[pa[-1]] = False
        best = None
        for s1 in sorted(starts):
            if not K['legal'](s1) or B.dist_rim(s1) >= B.dist_rim(h0):
                continue
            reach = False
            for d in range(8):
                f = B.add(s1, B.DIRS[d])
                if B.on_board(f) and B.dist_rim(f) < B.dist_rim(s1) and dj_full.get(f) is not None and dj_full[f] <= 1:
                    reach = True
            if reach:
                continue
            rc = K['race'](s1, jm, dj_full, dm_full, 0, allq, K['w0'], starts[s1])
            if best is None or rc['v'] > best['v']:
                best = dict(kind='speed', beaten=jm, start=s1, p=1.0, keeps_move=starts[s1], **rc)
        if best:
            out.append(best)
    res = _Races(_finish_race(x, b, h0) for x in out)
    res.kit = K                                       # (fix 3d, engine.js: the fake mix reads its races with the same kit)
    return res


class _Races(list):
    kit = None


def _finish_race(x, b, h0):
    x['look'] = dict(a=b, c=h0, rushed=True, r=x['p'], lk=_RaceLook(), open=[x['v']], q0=h0, n0=2, lc=0, adj=0.0, dr=True, p0=0, w=x['v'], race=True, vals=[None] * 5)
    return x


def poss_read(r, opts, s0=None, last_phase=False):
    """engine.js possRead: the looks of the map `opts` (read r), the defence's answer, the value."""
    from .decide import _caps, defender_map, _cmap2, _any_arrow_cmap2, _cmap2_after, fixed_kind, INF, _NOSET, geo_reach
    s, rules = r.s, r.rules
    b, k = s.ball, s.clock // RC.PHASE_SECONDS - 1
    cut = RC.off_balance_cut(rules) / 20.0
    _now, owed, key_mask = three_seconds_leave(s0 or s)
    # the actions a route may use: the phase's six less those spent getting men out of the key; in the last phase what
    # the offence really has left, less the shot's own action
    left = 6 - owed
    if last_phase:
        left, key_mask = (s0 or s).tok_o - 1, 0
    # (the three seconds are counted once: a man who can't get out is charged his -5 by poss_parts, so his own look in
    # the key doesn't carry it again. Scale audit, row 11.)
    stuck = three_seconds_stuck(s0) if s0 is not None else 0
    L = []
    for (a, c, rushed), o in opts.items():
        if o[0] > 0:
            fix = 5.0 if ((stuck >> a) & 1 and B.in_key(o[6])) else 0.0
            L.append(dict(a=a, c=c, rushed=rushed, r=o[0], lk=o[3], open=o[4], q0=o[6], n0=o[7], lc=o[8], adj=o[9] + fix, dr=o[8] == 0, p0=o[10], w=o[1], vals=o[5]))
    mapL, srR = list(L), (s0 if s0 is not None else s)
    races = drive_races(r, mapL, min(3, k + 1), srR)   # fix 3c (engine.js driveRaces): each drive from an advantage, read by its race
    for rc in races:
        L.append(rc['look'])
    n, K = len(L), k + 1
    cms = r._mcms
    memo = {}

    # step 31, fix 1 (engine.js sv2): a look's contest a phase away turns only on the cards, the look and the kinds the
    # defender reaches it with (decide.Read._vals_map keeps the same reading a context at a time), so it is kept across
    # boards: a board that differs from the last by one player finds every other pair already read
    gmemo = _SVMAP.get(s.ctx)
    if gmemo is None:
        if len(_SVMAP) > 8:
            _SVMAP.clear()
        gmemo = _SVMAP[s.ctx] = {}
    if len(gmemo) > 200000:
        gmemo.clear()

    def sval(i, d, pair):
        if pair is None or not pair[2] or L[i].get('race'):
            return None
        km, ksm = (pair[4], pair[5]) if len(pair) > 4 else (0, 0)
        key = (i, d, pair[2], pair[3], km, ksm)
        if key not in memo:
            lk = L[i]['lk']
            gk = (lk.i, lk.c, lk.rushed, d, pair[2], pair[3], km, ksm)
            hit = gmemo.get(gk, _MISS)
            if hit is _MISS:
                lines = []
                cv = r._vals2(lk, d, pair[0], pair[1], split=lines)
                # fix 3 (engine.js sval): his Contest where he stands, with no movement
                st = None
                if km:
                    rs = tuple(0 if (km >> k) & 1 else INF for k in range(6))
                    ls = []
                    cs = r._vals2(lk, d, rs, rs if ksm else _NOSET, split=ls)
                    st = (cs or {}, ls) if (cs or ls) else None
                hit = gmemo[gk] = (cv or {}, lines, st) if (cv or lines) else None
            memo[key] = hit
        return memo[key]
    SV = [[(sval(i, d, cms[d].get(L[i]['c'])) if (cms[d] is not None and not L[i].get('race')) else None) for d in range(5)] for i in range(n)]
    gone = [False] * n
    # Step 31, Part C (Shaun, 25 Nov 2026: "later answers cost actions too"; engine.js possRead). In this phase a look
    # faces only the movements the defence can make before its shot goes up: what is left of the defence's turn if it is
    # the one to act, then two for each turn the offence must hand over on the way. lim[j]: how many of the answer's
    # movements look j faces in this phase (the phases after: lim_l, below). SVK, gone_k: each look's contests as this
    # phase's shot will find them.
    sr = s0 if s0 is not None else s
    base_act = max(0, 2 - sr.turn_n) if (sr.side == 'X' and sr.stage == 'play' and not sr.pending) else 0
    lim = []
    for o in L:
        if o['a'] == b:
            turns = (1 + (o['n0'] - 1) // 2) if o['dr'] else o['n0'] // 2
        else:
            turns = 1 + (o['n0'] - 1) // 2
        lim.append(base_act + 2 * turns)
    SVK = [list(row) for row in SV]
    gone_k = [False] * n
    # Step 31, fix 2 (the step 31C audit: "later answers cost actions in every phase, not just the current one"). The
    # phases after this one are read on this board too, so each starts the same way: the offence acts first, and a look
    # faces only the movements the defence makes before its shot, two for each turn the offence hands over on the way.
    # lim_l[j]: that count for the later phases; SVL, gone_l: each look's contests as a later phase's shot finds them.
    # With no defence turn under way now the count is this phase's, and the two are one.
    lim_l = [0 if x == 0 else x - base_act for x in lim]
    if base_act:
        SVL, gone_l = [list(row) for row in SV], [False] * n
    else:
        SVL, gone_l = SVK, gone_k
    nm = [0]

    def trk(i):                                      # step i's limit, contests and squares taken: this phase's, or a later one's
        return (lim, SVK, gone_k) if i == K else (lim_l, SVL, gone_l)
    sr = s0 if s0 is not None else s
    mode = 0 if rules.zone == 'off' else 1

    # Step 31, fix 3 (engine.js possRead: "two-step routes are looks"; shot fakes read inside the number). The shooter
    # in control mixes real and fake; the defence contests from where it stands or closes out. Against a fake the
    # closeout's movement stands, so that defender has spent his Move, and the offence takes its best look with him so
    # placed: one route, one look, read by the two-by-two mix (shoot / fake against contest standing / close out):
    # wc + (ws - wc)(F - wc) / ((ws - wc) + (F - wc)) where it gains, else wc.
    fakes_on = all(RC.app_rule(rules, k) for k in ('fakes', 'block', 'contest_costs', 'position_contest', 'soft_contest'))
    fk_k = fakes_on and sr.count('O', 'hesitate') < RC.LIMITS['O']['hesitate']
    fk_l = fakes_on
    mix_ok = [fakes_on and not o['rushed'] for o in L]
    cur = [0]

    def core(i, Bv, d, nv, row):
        o = L[i]
        types, tmp = o['lk'].types, list(o['open'])
        arg = [-1] * len(types)
        for e in range(5):
            x = nv if e == d else row[e]
            if not x:
                continue
            cv, bl = x[0], x[1]
            for t, ty in enumerate(types):
                if ty in cv and cv[ty] < tmp[t]:
                    tmp[t] = cv[ty]
                    arg[t] = e
            for (t, c0, c1) in bl:
                v = c0 + c1 * Bv
                if v < tmp[t]:
                    tmp[t] = v
                    arg[t] = -2
        tp, tb = tmp[0], 0
        for t in range(1, len(tmp)):
            if tmp[t] > tp:
                tp, tb = tmp[t], t
        cur[0] = arg[tb]
        return tp + o['adj']
    SV0 = [list(row) for row in SV]
    Fm, Gm, UB0 = {}, {}, {}
    moved_at = [None] * 5                           # (fix 3b: where each defender's answer movement took him, and how)
    RK = [races.kit] if getattr(races, 'kit', None) else []   # (fix 3c: built when a fake's race first needs it; fix 3d: the drives' own)
    fake_kept = {}
    sN = r._msN

    def ok_look(j):
        o = L[j]
        return o['n0'] <= left if o['a'] == b else o['n0'] <= left + ((key_mask >> o['a']) & 1)

    def ub0(e):
        u, order = [0.0] * n, []
        for j in range(n):
            o = L[j]
            types, row, hi = o['lk'].types, SV0[j], NEG
            for t, ty in enumerate(types):
                v = o['open'][t]
                for e2 in range(5):
                    x = row[e2]
                    if e2 != e and x and ty in x[0] and x[0][ty] < v:
                        v = x[0][ty]
                if v > hi:
                    hi = v
            u[j] = o['r'] * (hi + o['adj']) - (1 - o['r']) * o['lc']
            if ok_look(j):
                order.append(j)
        order.sort(key=lambda j: (-u[j], j))
        UB0[e] = (u, order)

    def follow2(e, q, a, kind):
        key = (e, q, a, kind)
        g = Gm.get(key)
        if g is not None:
            return g
        if e not in UB0:
            ub0(e)
        u, order = UB0[e]
        cm = _cmap2_after(rules, q, a, s.ctx.dfn[e].qs, mode, kind, 1)
        hi, hj = NEG, -1
        for j in order:
            if u[j] + 1e-9 <= hi:
                break
            o = L[j]
            if o['c'] == q:
                continue
            ev = o['r'] * core(j, 0.0, e, sval(j, e, cm.get(o['c'])), SV0[j]) - (1 - o['r']) * o['lc']
            if ev > hi:
                hi, hj = ev, j
        g = Gm[key] = (hi, hj)
        return g

    def follow(i, e):
        key = (i, e)
        f = Fm.get(key)
        if f is not None:
            return f
        c = L[i]['c']
        lo, frm, then = float('inf'), None, -1
        mv0 = moved_at[e]
        if mv0 is None:
            free, fixed = defender_map(sN, e, exact=True)

            def fake_race(q):                      # (engine.js: the fake beats the closeout; the drive's race from there)
                if L[i]['a'] != b or L[i]['c'] != s.o[b] or L[i].get('race'):
                    return NEG
                if not RK:
                    RK.append(race_kit(r, mapL, srR, min(3, k + 1)))
                kit = RK[0]
                if (e, q) in fake_kept:                    # (fix 3d: one race a closer and square)
                    return fake_kept[(e, q)]
                qe = s.ctx.dfn[e].qs
                dj = kit['bfs'](q, qe, s.x[e], False, kit['qd0'] > 0, True)
                dmj = kit['bfs'](q, qe, s.x[e], False, False, False)
                fake_kept[(e, q)] = kit['race'](s.o[b], e, dj, dmj, kit['qo0'], lambda _q: True, True)['v']
                return fake_kept[(e, q)]
            for q, na in free.items():
                if na == 1 and B.cheb(q, c) == 1:
                    g = follow2(e, q, B.dir_between(q, c), 'move')
                    fr2 = fake_race(q)
                    v = max(g[0], fr2)
                    if v < lo:
                        lo, frm, then = v, q, (-2 if fr2 > g[0] else g[1])
            for q, arrs in fixed.items():
                if B.cheb(q, c) == 1:
                    for a, na in arrs.items():
                        if na == 1:
                            g = follow2(e, q, a, fixed_kind(sN, e, q, a))
                            fr2 = fake_race(q)
                            v = max(g[0], fr2)
                            if v < lo:
                                lo, frm, then = v, q, (-2 if fr2 > g[0] else g[1])
        elif mv0[2] != 'sprint':                       # (engine.js: he moved in the answer; he closes out with what he has left)
            mq, ma, mk = mv0
            qsd = s.ctx.dfn[e].qs
            if mk == 'qs':
                free = geo_reach(mq, ma, qsd, True, 0, rules)[0]
                for q, na in free.items():
                    if na == 1 and q != mq and B.cheb(q, c) == 1:
                        g = follow2(e, q, B.dir_between(q, c), 'sprint')
                        if g[0] < lo:
                            lo, frm, then = g[0], q, g[1]
            else:
                fixed = geo_reach(mq, ma, qsd, False, 1, rules)[1]
                for q, arrs in fixed.items():
                    if q != mq and B.cheb(q, c) == 1:
                        for a, na in arrs.items():
                            if na == 1:
                                g = follow2(e, q, a, 'sprint')
                                if g[0] < lo:
                                    lo, frm, then = g[0], q, g[1]
        f = Fm[key] = (NEG if lo == float('inf') else lo, frm, then)
        return f

    def worth(i, Bv, d, nv, row_k=None, tk=0):
        row = row_k if row_k is not None else SV[i]
        wc = core(i, Bv, d, nv, row)
        if not mix_ok[i] or not (fk_l if tk == 1 else fk_k):
            return wc
        e0 = cur[0]
        if e0 < 0:
            return wc
        o = L[i]
        types, tmp = o['lk'].types, list(o['open'])
        for e in range(5):
            x0 = nv if e == d else row[e]
            x = x0[2] if x0 else None
            if not x:
                continue
            cv, bl = x[0], x[1]
            for t, ty in enumerate(types):
                if ty in cv and cv[ty] < tmp[t]:
                    tmp[t] = cv[ty]
            for (t, c0, c1) in bl:
                v = c0 + c1 * Bv
                if v < tmp[t]:
                    tmp[t] = v
        ws = max(tmp) + o['adj']
        if not (ws > wc + 1e-9):
            return wc
        F = follow(i, e0)[0]
        if not (F > wc + 1e-9):
            return wc
        da, df = ws - wc, F - wc
        return wc + da * df / (da + df)
    hist, vec = [0.0] * (K + 1), [NEG] * 6
    rows = [None] * (K + 1)
    state = dict(act=[], JA=[])

    def run_cur(bars=None):
        U = OUT
        hist[0] = U
        act = []
        if bars is not None:
            bars.append(U)
        for i in range(1, K + 1):
            Bv = hist[i - 2] if i >= 3 else 0.0
            _l, SVt, gt = trk(i)
            tk = 0 if i == K else 1
            rows[i] = [NEG if gt[j] else worth(j, Bv, -1, None, SVt[j], tk) for j in range(n)]
            U = _route_t(L, rows[i], b, U, left, key_mask, cut, vec if i == K else None, act, i)
            hist[i] = U
            if bars is not None:
                bars.append(U)
        seen, JA = set(), []
        for j, _i in act:
            if j not in seen:
                seen.add(j)
                JA.append(j)
        for i in range(1, K + 1):
            row, Bk, tops = rows[i], hist[i - 1], [[] for _ in range(6)]
            for j in range(n):
                v = row[j]
                if v == NEG:
                    continue
                o = L[j]
                e = o['r'] * (v if v > Bk else Bk) + (1 - o['r']) * (Bk - o['lc'])
                tp = tops[5 if (o['a'] == b and o['dr']) else o['a']]
                if len(tp) < BOUND_LOOKS:
                    tp.append([e, j])
                    continue
                lo = min(range(len(tp)), key=lambda x: (tp[x][0], x))
                if e > tp[lo][0]:
                    tp[lo] = [e, j]
            for tp in tops:
                for _e, j in tp:
                    if j not in seen:
                        seen.add(j)
                        JA.append(j)
        JA.sort()
        state['act'], state['JA'] = act, JA
        build_orders()
        return U

    def run_on(idx, d, q, cm):
        """The same sum over the looks idx, defender d on q (contests cm) -> (U, the routes' values)."""
        LA = [L[j] for j in idx]
        nv = [sval(j, d, cm.get(L[j]['c'])) for j in idx]
        h, v3 = [OUT] * (K + 1), [NEG] * 6
        U = OUT
        for i in range(1, K + 1):
            Bv = h[i - 2] if i >= 3 else 0.0
            lt, SVt, gt = trk(i)
            tk = 0 if i == K else 1
            WA = [((NEG if (gone[j] or L[j]['c'] == q) else worth(j, Bv, d, nv[x], None, tk)) if lt[j] > nm[0]
                   else (NEG if gt[j] else worth(j, Bv, -1, None, SVt[j], tk))) for x, j in enumerate(idx)]
            U = _route_t(LA, WA, b, U, left, key_mask, cut, v3 if i == K else None, None, i)
            h[i] = U
        return U, v3
    # Step 31, fix 1 (engine.js possRead runCand): a candidate movement re-reads only the looks it touches, and the
    # looks a block bears on where what the block leads to changes; every other look keeps its worth as the defence
    # stands, and the route sum takes them best first, stopping where none left can beat what is found.
    vNH, vP0, vH, slot = [False] * n, [False] * n, [False] * n, [0] * n
    for j, o in enumerate(L):
        kb = (key_mask >> o['a']) & 1
        if o['a'] != b:
            vNH[j] = not (o['n0'] > left + kb)
            vP0[j] = vNH[j] and o['p0'] > 0 and o['n0'] + 1 <= left + kb
            slot[j] = o['a']
        else:
            vH[j] = not (o['n0'] > left)
            slot[j] = 5 if o['dr'] else b
    ords = {}

    def has_block(row, j):
        return any(x and (x[1] or (mix_ok[j] and x[2] and x[2][1])) for x in row)

    def build_orders():
        for i in range(1, K + 1):
            row = rows[i]
            nh = [j for j in range(n) if row[j] != NEG and vNH[j]]
            nh.sort(key=lambda j: (-row[j], j))
            ords[i] = (nh, [j for j in nh if vP0[j]], sorted((j for j in range(n) if row[j] != NEG and vH[j]), key=lambda j: (-row[j], j)))
        rk = rows[K]
        ords['slots'] = [sorted((j for j in range(n) if rk[j] != NEG and (vNH[j] or vH[j]) and slot[j] == k), key=lambda j: (-rk[j], j)) for k in range(6)]
        ords['blkL'] = [j for j in range(n) if has_block(SVL[j], j)]
        ords['blkK'] = [j for j in range(n) if has_block(SVK[j], j)]

    EPS_B = 1e-9                                     # (engine.js EPS_B: a weighted average can round a hair above both its ends)

    def route_diff(i, bar, ov):
        # _route_t(L, W, b, bar, ...) at step i, W being rows[i] with the overrides ov put in
        row = rows[i]
        nh, p0, hb = ords[i]
        best = fall = bar
        for j, v in ov.items():
            if v == NEG or not vNH[j]:
                continue
            o = L[j]
            e = o['r'] * (v if v > bar else bar) + (1 - o['r']) * (bar - o['lc'])
            if e > best:
                best = e
            if vP0[j]:
                p = 1 if o['p0'] >= 1 else max(0, o['p0'] - cut)
                f = p * (v if v > bar else bar) + (1 - p) * (bar - o['lc'])
                if f > fall:
                    fall = f
        for j in nh:
            if j in ov:
                continue
            v = row[j]
            if v + EPS_B <= best:
                break
            o = L[j]
            e = o['r'] * (v if v > bar else bar) + (1 - o['r']) * (bar - o['lc'])
            if e > best:
                best = e
        for j in p0:
            if j in ov:
                continue
            v = row[j]
            if v + EPS_B <= fall:
                break
            o = L[j]
            p = 1 if o['p0'] >= 1 else max(0, o['p0'] - cut)
            f = p * (v if v > bar else bar) + (1 - p) * (bar - o['lc'])
            if f > fall:
                fall = f
        for j, v in ov.items():
            if v == NEG or not vH[j]:
                continue
            o = L[j]
            e = (o['r'] * (v if v > bar else bar) + (1 - o['r']) * fall) if o['dr'] else (v if v > bar else bar)
            if e > best:
                best = e
        for j in hb:                                   # a set look: max(v, bar), exact; a Dribble route always read
            if j in ov:
                continue
            o = L[j]
            v = row[j]
            if not o['dr']:
                if v + EPS_B <= best:
                    continue
                e = v if v > bar else bar
            else:
                e = o['r'] * (v if v > bar else bar) + (1 - o['r']) * fall
            if e > best:
                best = e
        return best, fall

    def run_cand(d, q, cm):
        aff = []
        for j in range(n):
            if gone[j]:
                continue
            c = L[j]['c']
            pair = cm.get(c)
            if SV[j][d] is None and (pair is None or not pair[2]) and c != q:
                continue
            aff.append((j, sval(j, d, pair)))
        h = [OUT] * (K + 1)
        U = OUT
        last = None
        for i in range(1, K + 1):
            Bv = h[i - 2] if i >= 3 else 0.0
            ov = {}
            lt, SVt, gt = trk(i)
            tk = 0 if i == K else 1
            if i >= 3 and h[i - 2] != hist[i - 2]:      # a block now leads somewhere else: the looks it bears on move
                for j in ords['blkK' if i == K else 'blkL']:
                    if not gt[j]:
                        ov[j] = worth(j, Bv, -1, None, SVt[j], tk)
            for j, nv in aff:
                if lt[j] <= nm[0]:                     # this step's shot is up before the move
                    continue
                ov[j] = NEG if L[j]['c'] == q else worth(j, Bv, d, nv, None, tk)
            U, fall = route_diff(i, U, ov)           # (the bar: what playing on is worth after the step before)
            h[i] = U
            if i == K:
                last = (h[K - 1], fall, ov)
        return U, last

    def cand_top(u, last):
        Bv, fall, ov = last
        thr, rk, cnt = u - 1e-9, rows[K], 0

        def e_of(j, v):
            o = L[j]
            if o['a'] != b:
                return o['r'] * (v if v > Bv else Bv) + (1 - o['r']) * (Bv - o['lc'])
            return (o['r'] * (v if v > Bv else Bv) + (1 - o['r']) * fall) if o['dr'] else (v if v > Bv else Bv)
        for k in range(6):
            hit = any(slot[j] == k and v != NEG and (vNH[j] or vH[j]) and e_of(j, v) >= thr for j, v in ov.items())
            if not hit:
                for j in ords['slots'][k]:
                    if j in ov:
                        continue
                    v = rk[j]
                    if k != 5 and max(v, Bv) + EPS_B < thr:
                        break
                    if e_of(j, v) >= thr:
                        hit = True
                        break
            cnt += 1 if hit else 0
        return cnt
    bars = []
    U = run_cur(bars)
    U0, worth0 = U, list(rows[K])
    moves, moved, taken = [], [False] * 5, set(s.o) | set(s.x)
    tok = s.tok_x
    mode = 0 if rules.zone == 'off' else 1
    everything = list(range(n))
    while tok > 0 and state['act']:
        act, JA = state['act'], state['JA']
        cands, bm0 = [], _top_count(vec, U)

        def offer(d, q, a, cm):
            if BRUTE[0]:
                cands.append(dict(d=d, q=q, a=a, cm=cm, u=NEG, m=0))
                return
            lowers = False
            for j, i in act:
                if gone[j]:
                    continue
                if trk(i)[0][j] <= nm[0]:              # that step's shot is up before this movement
                    continue
                c = L[j]['c']
                if c == q:
                    lowers = True
                    break
                pair = cm.get(c)
                if (pair is None or not pair[2]) and SV[j][d] is None:
                    continue
                if worth(j, hist[i - 2] if i >= 3 else 0.0, d, sval(j, d, pair), None, 0 if i == K else 1) < rows[i][j] - 1e-9:
                    lowers = True
                    break
            if not lowers:
                return
            ua, v3 = run_on(JA, d, q, cm)
            ma = _top_count(v3, ua)
            if ua > U + 1e-9 or (ua >= U - 1e-9 and ma >= bm0):
                return
            cands.append(dict(d=d, q=q, a=a, cm=cm, u=ua, m=ma))
        for d in range(5):
            if moved[d] or not B.on_board(s.x[d]):
                continue
            can_move, qs_left = _caps(s, 'X', d)
            if not can_move and qs_left <= 0:
                continue
            qs = s.ctx.dfn[d].qs
            free, fixed = defender_map(s, d, exact=True)
            if can_move:                           # a Move on the spot: a new pair of arrows
                for a in range(8):
                    if a != s.arrows[d]:
                        offer(d, s.x[d], a, _cmap2_after(rules, s.x[d], a, qs, mode, 'move', qs_left))
            had = any(SV[j][d] is not None for j, _i in act)

            def bears(q):
                if had or BRUTE[0]:
                    return True
                anyc = _any_arrow_cmap2(rules, q, qs, mode)
                return any(L[j]['c'] == q or ((anyc.get(L[j]['c']) or (0, 0, 0))[2]) for j, _i in act)
            for q, na in free.items():
                if na == 1 and q not in taken and bears(q):
                    for a in range(8):                 # (fix 3: his reply from there is what the movement leaves him)
                        offer(d, q, a, _cmap2_after(rules, q, a, qs, mode, 'move', qs_left))
            for q, arrs in fixed.items():
                if q in taken:
                    continue
                for a, na in arrs.items():
                    if na == 1:
                        offer(d, q, a, _cmap2_after(rules, q, a, qs, mode, fixed_kind(s, d, q, a), qs_left))

        def order(x):                              # the value; level, the fewer routes that reach it; then square, arrow, where he starts
            return (x['m'], x['q'], x['a'], s.x[x['d']])

        def before(x, y):
            if abs(x['u'] - y['u']) > 1e-9:
                return -1 if x['u'] < y['u'] else 1
            kx, ky = order(x), order(y)
            return -1 if kx < ky else 1 if kx > ky else 0
        import functools
        cands.sort(key=functools.cmp_to_key(before))
        best = None
        for c in cands:
            if best is not None and before(best, c) <= 0:
                break
            u, last = run_cand(c['d'], c['q'], c['cm'])
            mm = 0 if u > U + 1e-9 else cand_top(u, last)      # (wanted only when the value doesn't rise)
            if CHECK[0]:                           # the reference: the same sum read over every look, as before fix 1
                uf, vf = run_on(everything, c['d'], c['q'], c['cm'])
                CHECK[1] += 1
                if uf != u or (u <= U + 1e-9 and _top_count(vf, uf) != mm):
                    CHECK[2] += 1
            if u > U + 1e-9 or (u >= U - 1e-9 and mm >= bm0):
                continue
            full = dict(d=c['d'], q=c['q'], a=c['a'], cm=c['cm'], u=u, m=mm)
            if best is None or before(full, best) < 0:
                best = full
        if best is None:
            break
        d, q, cm = best['d'], best['q'], best['cm']
        for i in range(n):
            nv = sval(i, d, cm.get(L[i]['c']))
            if L[i]['c'] == q:
                gone[i] = True
            SV[i][d] = nv
            if lim[i] > nm[0]:
                if L[i]['c'] == q:
                    gone_k[i] = True
                SVK[i][d] = nv
            if base_act and lim_l[i] > nm[0]:
                if L[i]['c'] == q:
                    gone_l[i] = True
                SVL[i][d] = nv
        nm[0] += 1
        # fix 3b (engine.js): the fake's follow-up is read on the board the answer leaves, with its rotations
        kind = 'move' if cm is _cmap2_after(rules, q, best['a'], s.ctx.dfn[d].qs, mode, 'move', _caps(s, 'X', d)[1]) else fixed_kind(s, d, q, best['a'])
        moved_at[d] = (q, best['a'], kind)
        for i in range(n):
            SV0[i] = list(SV[i])
        Fm.clear()
        Gm.clear()
        UB0.clear()
        moves.append((d, q, best['a']))
        moved[d] = True
        taken.add(q)
        tok -= 1
        U = run_cur()
    return dict(U=U, U0=U0, worth0=worth0, r=r, k=k, bars=list(hist), before=bars, moves=moves, L=L, worth=list(rows[K]) if K >= 1 else [], routes=list(vec), races=races)


def poss_parts(s, cfg=None):
    """engine.js possParts: the value of playing on from s (what is banked not counted), with its parts."""
    from . import memo
    from .decide import map_read, cov_off_fresh, cov_fresh, cov_pass, three_seconds_owed
    if s.stage != 'play':
        return dict(V=OUT, k=0, bars=[OUT], moves=[])

    def calc():
        if s.pending:
            recv = s.pending[1]
            base = s.with_(pending=None, approach=-1)
            p = cov_pass(base, recv, base.o[recv])
            pc = poss_parts(base.with_(ball=recv), cfg)
            lost = poss_parts(cov_fresh(base).with_(clock=s.clock - RC.PHASE_SECONDS), cfg)['V'] \
                if s.clock - RC.PHASE_SECONDS > RC.PHASE_SECONDS else OUT
            return dict(pc, V=p * pc['V'] + (1 - p) * (lost - 5), catch=p)
        if s.clock <= RC.PHASE_SECONDS:            # the last phase: its own looks, with what the offence really has left
            f = s.with_(turn_n=0, side='O', approach=-1, prev_wait='', final=False, turn_lead=-1, turn_x=(), turn_moved=0, react_moved=0)
            r, opts = map_read(f, cfg, True)
            rd = poss_read(r, opts, s, True)
        else:
            r, opts = map_read(cov_off_fresh(s), cfg)
            rd = poss_read(r, opts, s)
        rd['V'] = rd['U'] - 5 * three_seconds_owed(s)
        return rd
    return memo.get('map', ('PV', id(s.ctx), s, id(cfg)), calc)


def poss_value(s, cfg=None):
    return poss_parts(s, cfg)['V']
