"""Advantage states (step 3g): what an offence has created on the board, and for whom.

advantages(state, prev=None) is a pure function of what both players can see. Each advantage names the
attacker it benefits and is valued at the shot value after the defence's reaction that it opens (from
where the attacker stands, the same contest model as everywhere else). These are labels for the
computer's search and the post-game review, not scoring rules.

The six states:
  beaten       a defender is locked (lost a Dribble, or held by a Screen after a Challenge), and the
               attacker he was guarding has a shot he can't contest
  mismatch     an attacker's ▲ shot type meets a ▼ contest from the only defender who can reach it
  help_pulled  a defender moved toward the ball and away from the attacker he was nearest to, and that
               attacker now has no clean reachable contest (needs prev: the board before the move)
  bad_closeout the only defender who can reach the shot arrives with a foul roll, or with the -3 for
               being further from the rim than the shooter
  spent        the defence has no tokens, or the likely closeout defender (the nearest) has used his Move
  numbers      more attackers with a ▲ shot in their zone than defenders who can reach a clean contest
               on them in one reaction (the advantage goes to the best attacker left over)
"""
from . import board as B
from . import rules_config as RC

KINDS = ('beaten', 'mismatch', 'help_pulled', 'bad_closeout', 'spent', 'numbers', 'overloaded')
WORDS = {'beaten': 'beat his man', 'mismatch': 'a mismatch', 'help_pulled': 'help pulled off him',
         'bad_closeout': 'a bad closeout', 'spent': 'a spent defence', 'numbers': 'numbers',
         'overloaded': 'a defender with two jobs'}


def reaction_budget(state):
    return min(2, state.tok_x) if state.tok_x > 0 else 0


def reach_maps(state, reach=None):
    """Each defender's reach in the reaction (free and fixed-arrow squares), as the solver models it."""
    budget = reaction_budget(state)
    if reach is not None:
        return reach(state, budget)
    from .solver import defender_reach
    return [defender_reach(state, d, budget) for d in range(5)]


def contests(state, i, t, maps):
    """Every defender who can contest attacker i shooting t from his square after the reaction, each at
    his best: clean (facing the shooter), far (the -3), contest rating and the shot's value after it."""
    from .scoring import foul_on_shot_points
    spos = state.o[i]
    pts = RC.ZONE_POINTS[B.zone(spos)]
    card = state.ctx.off[i]
    rules = state.ctx.rules
    if rules.contest_geometry != 'current' or rules.arrow_mode != 'single' or rules.late_closeout:
        return _contests_geo(state, i, t, maps, spos, pts, card)
    out = []
    for d in range(5):
        free, fixed = maps[d]
        best = None
        for q in set(free) | set(fixed):
            if not B.adjacent(q, spos) or q in state.o:
                continue
            on = B.dir_between(q, spos)
            far = B.dist_rim(q) > B.dist_rim(spos)
            c = state.ctx.dfn[d].con(t) - (RC.FAR_CONTEST_PENALTY if far else 0)
            if state.ctx.rules.floor_contest_zero:
                c = max(0, c)
            v = max(0, pts * (card.shot(t) - c))
            clean = q in free or on in fixed.get(q, {})
            if not clean:
                pf = state.ctx.dfn[d].r['foul_contest'] / 20.0
                fp = float(foul_on_shot_points(card, t, pts, state.ctx.rules)[0])
                v = pf * fp + (1 - pf) * v
            cand = dict(defender=d, clean=clean, far=far, contest=c, value=v, square=B.sq(q))
            if best is None or (v, not clean) < (best['value'], not best['clean']):
                best = cand
        if best:
            out.append(best)
    return sorted(out, key=lambda e: e['value'])


def _contests_geo(state, i, t, maps, spos, pts, card):
    """contests() under a step 3h setting, through geometry.best_terms (far = Behind's -3)."""
    from . import geometry as G
    from .scoring import foul_on_shot_points
    rules = state.ctx.rules
    out = []
    for d in range(5):
        free, fixed = maps[d]
        best = None
        for q in set(free) | set(fixed):
            if not B.adjacent(q, spos) or q in state.o:
                continue
            opts = ([None] if q in free else []) + [(a,) for a in fixed.get(q, {})]
            for arrows in opts:
                bt = G.best_terms(rules, q, arrows, spos)
                if bt is None:
                    continue
                moved = q != state.x[d] or (state.stage == 'reaction' and state.react_moved >> d & 1)
                _, foul_roll, penalty, cat = G.late(rules, moved, t, bt[:4])
                c = state.ctx.dfn[d].con(t) - (RC.FAR_CONTEST_PENALTY if penalty else 0)
                if rules.floor_contest_zero:
                    c = max(0, c)
                v = max(0, pts * (card.shot(t) - c))
                if foul_roll:
                    pf = state.ctx.dfn[d].r['foul_contest'] / 20.0
                    fp = float(foul_on_shot_points(card, t, pts, rules)[0])
                    v = pf * fp + (1 - pf) * v
                cand = dict(defender=d, clean=not foul_roll, far=penalty, contest=c, value=v, square=B.sq(q),
                            category=cat)
                if best is None or (v, foul_roll) < (best['value'], not best['clean']):
                    best = cand
        if best:
            out.append(best)
    return sorted(out, key=lambda e: e['value'])


def looks(state, i, maps):
    """Attacker i's shot types from his square: [(value after the reaction, type, contests)], best first."""
    if not B.on_board(state.o[i]):
        return []
    z = B.zone(state.o[i])
    if not RC.ZONE_SHOTS.get(z):
        return []                              # plain wood: no shot from here
    pts = RC.ZONE_POINTS[z]
    out = []
    for t in RC.ZONE_SHOTS[z]:
        if state.ctx.three_only and t != 'three':
            continue
        cs = contests(state, i, t, maps)
        v = cs[0]['value'] if cs else float(pts * state.ctx.off[i].shot(t))
        out.append((v, t, cs))
    return sorted(out, key=lambda x: -x[0])


def _adv(kind, attacker, value, shot, defender=None, **kw):
    return dict(kind=kind, attacker=attacker, value=float(value), shot=shot, defender=defender, **kw)


def advantages(state, prev=None, maps=None, dilemma=False):
    """Every advantage on the board: a list of dicts (kind, attacker, value, shot, defender), best first.
    prev is the board before the defence's last turn (for help_pulled); without it that state is skipped."""
    if state.stage == 'over' or not B.on_board(state.o[state.ball]):
        return []
    maps = maps if maps is not None else reach_maps(state)
    L = {i: looks(state, i, maps) for i in range(5)}
    off, dfn = state.ctx.off, state.ctx.dfn
    out = []
    nearest_x = lambda i: min(range(5), key=lambda j: (B.cheb(state.x[j], state.o[i]), j))
    # beaten: a locked defender, and the attacker he was guarding has a shot he can't contest
    for j in range(5):
        if not state.locked('X', j):
            continue
        beat = [o for o, x in state.beaten if x == j]
        a = beat[0] if beat else min(range(5), key=lambda i: (B.cheb(state.x[j], state.o[i]), i))
        if L[a]:
            v, t, cs = L[a][0]
            if not any(c['defender'] == j for c in cs):
                out.append(_adv('beaten', a, v, t, j))
    for i in range(5):
        if not L[i]:
            continue
        v, t, cs = L[i][0]
        # mismatch: a ▲ shot type against a ▼ contest from the only defender who can reach it
        for vt, tt, ct in L[i]:
            if off[i].bands['shot_' + tt] == 'H' and len(ct) == 1 and dfn[ct[0]['defender']].bands['con_' + tt] == 'L':
                out.append(_adv('mismatch', i, vt, tt, ct[0]['defender']))
                break
        # bad closeout: the only defender who can reach arrives with a foul roll or the -3
        if state.ctx.rules.contest_geometry != 'current':
            if cs and cs[0].get('category') in ('side', 'behind'):     # step 3h: the best contest isn't Front
                out.append(_adv('bad_closeout', i, v, t, cs[0]['defender'], foul_roll=not cs[0]['clean'],
                                far=cs[0]['far'], category=cs[0]['category']))
        elif len(cs) == 1 and (not cs[0]['clean'] or cs[0]['far']):
            out.append(_adv('bad_closeout', i, v, t, cs[0]['defender'], foul_roll=not cs[0]['clean'], far=cs[0]['far']))
        # spent: no tokens, or the likely closeout defender (the nearest) has used his Move
        j = nearest_x(i)
        if state.tok_x <= 0 or state.moved('X', j):
            out.append(_adv('spent', i, v, t, j, no_tokens=state.tok_x <= 0))
    # help pulled: a defender moved toward the ball and away from the attacker he was nearest to
    if prev is not None and prev.o == state.o:
        ball = state.o[state.ball]
        for j in range(5):
            if prev.x[j] == state.x[j]:
                continue
            man = min(range(5), key=lambda i: (B.cheb(prev.x[j], prev.o[i]), i))
            if man == state.ball or not L[man]:
                continue
            toward = B.cheb(state.x[j], ball) < B.cheb(prev.x[j], ball)
            away = B.cheb(state.x[j], state.o[man]) > B.cheb(prev.x[j], prev.o[man])
            v, t, cs = L[man][0]
            if toward and away and not any(c['clean'] for c in cs):
                out.append(_adv('help_pulled', man, v, t, j, helper=j))
    # numbers: more ▲ shooters in their zones than defenders who can reach a clean contest on them
    tri = {}
    for i in range(5):
        hs = [(vt, tt, ct) for vt, tt, ct in L[i] if off[i].bands['shot_' + tt] == 'H']
        if hs:
            tri[i] = (hs[0], {c['defender'] for vt, tt, ct in hs for c in ct if c['clean']})
    if tri:
        att = sorted(tri)
        cover = _max_cover(att, {i: tri[i][1] for i in att})
        if cover < len(att):
            # the attacker left over: the best one no full cover can include
            left = [i for i in att if _max_cover([a for a in att if a != i], {a: tri[a][1] for a in att}) == cover]
            if left:
                i = max(left, key=lambda a: tri[a][0][0])
                out.append(_adv('numbers', i, tri[i][0][0], tri[i][0][1], None, shooters=len(att), cover=cover))
    if dilemma:
        out += _overloaded(state, maps, L)
    return sorted(out, key=lambda a: (-a['value'], KINDS.index(a['kind']), a['attacker']))


def _without(cs, j, open_value):
    rest = [c for c in cs if c['defender'] != j]
    return rest[0]['value'] if rest else open_value


def _overloaded(state, maps, L):
    """Step 3i, C3: one defender is the only answer to two threats this phase (the closeout on a ▲
    shooter, the help on the carrier's best drive, a passing lane). Valued as the threat he leaves
    open after the defence's best single choice: the lesser of the two values with him gone."""
    from .actions import can_move_kind, movement_dests
    from .capacity import lane_reach
    off = state.ctx.off
    c = state.ball
    threats = []                                   # (job, attacker, answering defenders, value without j)
    for i in range(5):
        hs = [(v, t, cs) for v, t, cs in L[i] if off[i].bands['shot_' + t] == 'H']
        if not hs:
            continue
        v, t, cs = hs[0]
        ans = {e['defender'] for e in cs if e['clean']}
        open_v = float(RC.ZONE_POINTS[B.zone(state.o[i])] * off[i].shot(t))
        threats.append((f'closeout on O{i + 1}', i, ans, lambda j, cs=cs, o=open_v: _without(cs, j, o), t))
    st = state.with_(side='O')
    best_q = None
    if B.on_board(state.o[c]) and state.tok_o > 0:
        for kind in ('move', 'qs', 'sprint'):
            if not can_move_kind(st, 'O', c, kind):
                continue
            for q in movement_dests(st, 'O', c, kind, state.ctx.rules):
                z = B.zone(q)
                if not RC.ZONE_SHOTS.get(z) or q in state.x:
                    continue
                t = max(RC.ZONE_SHOTS[z], key=lambda k: off[c].shot(k))
                v = RC.ZONE_POINTS[z] * off[c].shot(t)
                if best_q is None or (v, -B.dist_rim(q)) > (best_q[0], -B.dist_rim(best_q[1])):
                    best_q = (v, q, t)
    if best_q:
        v, q, t = best_q
        sh = state.with_(o=state.o[:c] + (q,) + state.o[c + 1:])
        cs = contests(sh, c, t, maps)
        ans = {e['defender'] for e in cs if e['clean']}
        threats.append((f'help on O{c + 1}\'s drive', c, ans, lambda j, cs=cs, o=float(v): _without(cs, j, o), t))
    for r in range(5):
        if r == c or not L[r]:
            continue
        ans = {j for j in range(5) if lane_reach(state, j, c, r)}
        v = L[r][0][0]
        threats.append((f'the lane to O{r + 1}', r, ans, lambda j, v=v: v, L[r][0][1]))
    out = []
    for j in range(5):
        mine = [th for th in threats if th[2] == {j}]
        best = None
        for a in range(len(mine)):
            for b in range(a + 1, len(mine)):
                A, Bt = mine[a], mine[b]
                if A[1] == Bt[1]:
                    continue                            # two jobs means two different attackers
                va, vb = A[3](j), Bt[3](j)
                left = A if va <= vb else Bt          # the defence covers the bigger one
                val = min(va, vb)
                if best is None or val > best[0]:
                    best = (val, left, (A[0], Bt[0]))
        if best:
            val, left, jobs = best
            out.append(_adv('overloaded', left[1], val, left[4], j, jobs=list(jobs)))
    return out


def _max_cover(att, can):
    """Most attackers that distinct defenders can each cleanly contest (bipartite matching)."""
    match = {}

    def aug(i, seen):
        for d in can.get(i, ()):
            if d in seen:
                continue
            seen.add(d)
            if d not in match or aug(match[d], seen):
                match[d] = i
                return True
        return False
    return sum(aug(i, set()) for i in att)


def describe(adv):
    """Plain words for the review: 'O1 has a mismatch on X4, for a three'."""
    who = f"O{adv['attacker'] + 1}"
    d = f" on X{adv['defender'] + 1}" if adv.get('defender') is not None and adv['kind'] != 'help_pulled' else ''
    if adv['kind'] == 'help_pulled':
        return f"Help came from X{adv['helper'] + 1}; {who} was left for a {adv['shot']}"
    if adv['kind'] == 'overloaded':
        return f"X{adv['defender'] + 1} had two jobs ({' and '.join(adv['jobs'])}); {who} was left for a {adv['shot']}"
    return f"{who} has {WORDS[adv['kind']]}{d}, for a {adv['shot']}"
