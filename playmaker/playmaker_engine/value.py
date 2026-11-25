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


def poss_read(r, opts, s0=None):
    """engine.js possRead: the looks of the map `opts` (read r), the defence's answer, the value."""
    from .decide import _caps, defender_map, _cmap2, _any_arrow_cmap2
    s, rules = r.s, r.rules
    b, k = s.ball, s.clock // RC.PHASE_SECONDS - 1
    cut = RC.off_balance_cut(rules) / 20.0
    _now, owed, key_mask = three_seconds_leave(s0 or s)
    left = 6 - owed
    # (the three seconds are counted once: a man who can't get out is charged his -5 by poss_parts, so his own look in
    # the key doesn't carry it again. Scale audit, row 11.)
    stuck = three_seconds_stuck(s0) if s0 is not None else 0
    L = []
    for (a, c, rushed), o in opts.items():
        if o[0] > 0:
            fix = 5.0 if ((stuck >> a) & 1 and B.in_key(o[6])) else 0.0
            L.append(dict(a=a, c=c, rushed=rushed, r=o[0], lk=o[3], open=o[4], q0=o[6], n0=o[7], lc=o[8], adj=o[9] + fix, dr=o[8] == 0, p0=o[10], w=o[1]))
    n, K = len(L), k + 1
    cms = r._mcms
    memo = {}

    def sval(i, d, pair):
        if pair is None or not pair[2]:
            return None
        key = (i, d, pair[2], pair[3])
        if key not in memo:
            lines = []
            cv = r._vals2(L[i]['lk'], d, pair[0], pair[1], split=lines)
            memo[key] = (cv or {}, lines) if (cv or lines) else None
        return memo[key]
    SV = [[(sval(i, d, cms[d].get(L[i]['c'])) if cms[d] is not None else None) for d in range(5)] for i in range(n)]
    gone = [False] * n

    def worth(i, Bv, d, nv):
        o = L[i]
        types, tmp, row = o['lk'].types, list(o['open']), SV[i]
        for e in range(5):
            x = nv if e == d else row[e]
            if not x:
                continue
            cv, bl = x
            for t, ty in enumerate(types):
                if ty in cv and cv[ty] < tmp[t]:
                    tmp[t] = cv[ty]
            for (t, c0, c1) in bl:
                v = c0 + c1 * Bv
                if v < tmp[t]:
                    tmp[t] = v
        return max(tmp) + o['adj']
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
            rows[i] = [NEG if gone[j] else worth(j, Bv, -1, None) for j in range(n)]
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
        return U

    def run_on(idx, d, q, cm):
        """The same sum over the looks idx, defender d on q (contests cm) -> (U, the routes' values)."""
        LA = [L[j] for j in idx]
        nv = [sval(j, d, cm.get(L[j]['c'])) for j in idx]
        h, v3 = [OUT] * (K + 1), [NEG] * 6
        U = OUT
        for i in range(1, K + 1):
            Bv = h[i - 2] if i >= 3 else 0.0
            WA = [(NEG if (gone[j] or L[j]['c'] == q) else worth(j, Bv, d, nv[x])) for x, j in enumerate(idx)]
            U = _route_t(LA, WA, b, U, left, key_mask, cut, v3 if i == K else None, None, i)
            h[i] = U
        return U, v3
    bars = []
    U = run_cur(bars)
    U0 = U
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
                c = L[j]['c']
                if c == q:
                    lowers = True
                    break
                pair = cm.get(c)
                if (pair is None or not pair[2]) and SV[j][d] is None:
                    continue
                if worth(j, hist[i - 2] if i >= 3 else 0.0, d, sval(j, d, pair)) < rows[i][j] - 1e-9:
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
                        offer(d, s.x[d], a, _cmap2(rules, s.x[d], a, qs, mode))
            had = any(SV[j][d] is not None for j, _i in act)

            def bears(q):
                if had or BRUTE[0]:
                    return True
                anyc = _any_arrow_cmap2(rules, q, qs, mode)
                return any(L[j]['c'] == q or ((anyc.get(L[j]['c']) or (0, 0, 0))[2]) for j, _i in act)
            for q, na in free.items():
                if na == 1 and q not in taken and bears(q):
                    for a in range(8):
                        offer(d, q, a, _cmap2(rules, q, a, qs, mode))
            for q, arrs in fixed.items():
                if q in taken:
                    continue
                for a, na in arrs.items():
                    if na == 1:
                        offer(d, q, a, _cmap2(rules, q, a, qs, mode))

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
            u, v2 = run_on(everything, c['d'], c['q'], c['cm'])
            mm = _top_count(v2, u)
            if u > U + 1e-9 or (u >= U - 1e-9 and mm >= bm0):
                continue
            full = dict(d=c['d'], q=c['q'], a=c['a'], cm=c['cm'], u=u, m=mm)
            if best is None or before(full, best) < 0:
                best = full
        if best is None:
            break
        d, q, cm = best['d'], best['q'], best['cm']
        for i in range(n):
            if L[i]['c'] == q:
                gone[i] = True
            SV[i][d] = sval(i, d, cm.get(L[i]['c']))
        moves.append((d, q, best['a']))
        moved[d] = True
        taken.add(q)
        tok -= 1
        U = run_cur()
    return dict(U=U, U0=U0, k=k, bars=list(hist), before=bars, moves=moves, L=L, worth=list(rows[K]) if K >= 1 else [], routes=list(vec))


def poss_parts(s, cfg=None):
    """engine.js possParts: the value of playing on from s (what is banked not counted), with its parts."""
    from . import memo
    from .decide import map_read, cov_off_fresh, cov_fresh, cov_pass, three_seconds_owed
    if s.stage != 'play' or s.clock <= RC.PHASE_SECONDS:
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
        r, opts = map_read(cov_off_fresh(s), cfg)
        rd = poss_read(r, opts, s)
        rd['V'] = rd['U'] - 5 * three_seconds_owed(s)
        return rd
    return memo.get('map', ('PV', id(s.ctx), s, id(cfg)), calc)


def poss_value(s, cfg=None):
    return poss_parts(s, cfg)['V']
