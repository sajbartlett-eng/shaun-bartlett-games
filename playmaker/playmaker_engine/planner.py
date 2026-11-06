"""The goal-directed offence and the defence's objectives (step 3i, C2a).

Real offences pick a goal, work out what has to be true for it to work, and make those things true.

  goals(view, comp)             every goal in the level's library instantiated on the board: the entry,
                                who it is for, its edge (the finish's value), and its chain of steps
  defence_objectives(view, ...) the defence's ranked objectives: what the offence could be building
                                toward, weighted by its value and by how close the board is to it

A goal's chain is built backwards from its conditions, fresh from the board at every decision, so steps
already gained are kept and a step the defence undoes comes back. A step is one condition met (the
post player on the block, a lane opened by a receiver's move, a swing pass, a seal, a screen); the
level's chain depth decides how far back it reasons (Rookie 0: try the finish directly; Starter 1;
All-Star the full chain). The computer picks the current step's play by create, reply, exploit; the
plan changes goal only on a lost roll, a thwarted condition, or a better goal now cheaper.

The library is data (goal_library.json): words, levels and answers can be edited without code. Each
entry names a pattern below, which reads the board for it.
"""
import json
import os

from . import board as B
from . import rules_config as RC
from .actions import Action, can_move_kind, movement_dests

with open(os.path.join(os.path.dirname(__file__), 'goal_library.json')) as _f:
    LIB = json.load(_f)
ENTRIES = {e['id']: e for e in LIB['offence']}
OBJECTIVES = {o['id']: o for o in LIB['defence']}
SHOTS = ('layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three')


def level_goals(level):
    ids = LIB['levels'][level]['offence']
    if ids == 'all':
        ids = [e['id'] for e in LIB['offence']]
    return [ENTRIES[i] for i in ids if ENTRIES[i]['built'] and ENTRIES[i]['pattern'] != 'modifier']


def chain_depth(level):
    return LIB['levels'][level]['chain_depth']


def level_objectives(level):
    ids = LIB['levels'][level]['defence']
    return [o['id'] for o in LIB['defence']] if ids == 'all' else list(ids)


# ---- board helpers -------------------------------------------------------------------------------------

def _nearest_x(s, sq, exclude=()):
    c = [j for j in range(5) if j not in exclude]
    return min(c, key=lambda j: (B.cheb(s.x[j], sq), j)) if c else None


def _hyp(s, holder):
    """The board with `holder` holding the ball at the start of an offence turn (to ask about his lanes)."""
    return s.with_(ball=holder, side='O', stage='play', turn_n=0, pending=None, approach=-1, tok_o=max(1, s.tok_o))


def lane(s, a, b):
    """pass_risk for a -> b. With the phase's passes used up (two a phase), the lane as it stands for the
    next phase's pass: the plan waits for it rather than reading the limit as a turnover."""
    from .computer import pass_risk
    from .state import CI
    if not (B.on_board(s.o[a]) and B.on_board(s.o[b])) or a == b:
        return None
    live = s.ball == a and s.stage == 'play' and s.side == 'O'
    info = pass_risk(s if live else _hyp(s, a), a, b)
    if info is None and s.count('O', 'pass') >= RC.LIMITS['O']['pass']:
        cnt = list(s.cnt)
        cnt[CI['pass']] = 0
        info = pass_risk(_hyp(s.with_(cnt=tuple(cnt)), a), a, b)
    return info


def lane_clean(s, a, b):
    info = lane(s, a, b)
    return bool(info and info['clean'])


def _o_moves(s, i, kinds=('move', 'qs')):
    """Movement actions offence piece i could make on an offence turn now."""
    st = s if (s.side == 'O' and s.stage == 'play') else s.with_(side='O', stage='play')
    out = []
    for kind in kinds:
        if can_move_kind(st, 'O', i, kind):
            for q in movement_dests(st, 'O', i, kind, s.ctx.rules):
                if B.on_board(q) and q not in s.x and q not in s.o:
                    out.append(Action(kind, 'O', i, q))
    return out


def _moved(s, a):
    return s.with_(o=s.o[:a.piece] + (a.dest,) + s.o[a.piece + 1:])


def _shot_value(card, sq, types=None):
    z = B.zone(sq)
    ts = [t for t in RC.ZONE_SHOTS.get(z, ()) if types is None or t in types]
    return max((RC.ZONE_POINTS[z] * card.shot(t) for t in ts), default=0)


def _screener(s, d, exclude):
    """Who screens X{d}: a teammate whose T is already on him (the step is done), else the nearest free one."""
    on_d = [j for j in range(5) if j not in exclude and _screen_t(s, j) == s.x[d]]
    if on_d:
        return on_d[0]
    scs = [j for j in range(5) if j not in exclude and B.on_board(s.o[j]) and not s.is_screening(j)]
    return min(scs, key=lambda j: (B.cheb(s.o[j], s.x[d]), j)) if scs else None


def _screen_t(s, i):
    sc = s.screen_of(i)
    return B.add(s.o[i], B.DIRS[sc[1]]) if sc else None


def _ws(text, **kw):
    for k, v in kw.items():
        text = text.replace('{' + k + '}', str(v + 1) if isinstance(v, int) else str(v))
    return text


def _step(sid, words, done, plays, finish=False, risk=0.0):
    return dict(id=sid, words=words, done=done, plays=plays, finish=finish, risk=risk)


def _play(concept, *actions):
    from .solver import Play
    return Play(concept, tuple(actions))


# ---- the chain pieces shared by the patterns -------------------------------------------------------------

_OPEN = {}
_GOALS = {}


def _cached(store, key, fn):
    hit = store.get(key)
    if hit is not None and hit[0] is key[1]:
        return hit[1]
    v = fn()
    if len(store) > 4000:
        store.clear()
    store[key] = (key[1], v)
    return v


def open_lane_moves(s, a, b, limit=3):
    """Moves by receiver b that make the lane a -> b clean (a V-cut, a lift, a flash), best look first."""
    return _cached(_OPEN, (s, s.ctx, a, b, limit), lambda: _open_lane_moves(s, a, b, limit))


def _open_lane_moves(s, a, b, limit):
    out = []
    card = s.ctx.off[b]
    for mv in _o_moves(s, b):
        t = _moved(s, mv)
        if lane_clean(t, a, b):
            out.append((_shot_value(card, mv.dest), mv))
    out.sort(key=lambda x: (-x[0], x[1].dest))
    return [m for _, m in out[:limit]]


def swing_path(s, holders, max_open=2, avoid=()):
    """Clean passes from the carrier to any of `holders`: [(from, to, clean, opening moves)], or None.
    At most three passes, and at most max_open lanes that a receiver's move must open first. Fewest
    opened lanes first, then fewest passes."""
    c = s.ball
    if c in holders:
        return []
    best = None
    frontier = [(c, [], 0, {c} | set(avoid))]
    for _ in range(3):
        nxt = []
        for h, path, opened, seen in frontier:
            for r in range(5):
                if r in seen or not B.on_board(s.o[r]):
                    continue
                if lane_clean(s, h, r):
                    np, no = path + [(h, r, True, [])], opened
                elif opened < max_open:
                    mv = open_lane_moves(s, h, r)
                    if not mv:
                        continue
                    np, no = path + [(h, r, False, mv)], opened + 1
                else:
                    continue
                if r in holders:
                    if best is None or (no, len(np)) < (best[0], len(best[1])):
                        best = (no, np)
                    continue
                nxt.append((r, np, no, seen | {r}))
        frontier = nxt
    return best[1] if best else None


def swing_steps(s, path):
    """Opening moves first (the receivers move before the ball goes), then the passes in order."""
    steps = []
    for h, r, clean, moves in path:
        if not clean:
            steps.append(_step(f'open{r}', f'O{r + 1} moved to open the lane', False,
                               lambda moves=moves: [_play('open the lane', m) for m in moves]))
    for k, (h, r, clean, moves) in enumerate(path):
        steps.append(_step(f'swing{r}', f'swung the ball to O{r + 1}', False,
                           lambda h=h, r=r: [_play('swing', Action('pass', 'O', h, target=r))]))
    return steps


def seal_plays(s, p, d):
    """O{p} seals X{d}: a Screen with the T on him, after a Move next to him if needed (rim side first)."""
    out = []
    xd = s.x[d]
    st = s if (s.side == 'O' and s.stage == 'play') else s.with_(side='O', stage='play')
    from .actions import legal_actions
    from .resolve import apply, ChanceNode
    if B.adjacent(s.o[p], xd):
        a = Action('screen', 'O', p, target=B.dir_between(s.o[p], xd))
        if a in legal_actions(st):
            out.append(_play('seal', a))
    if not out and st.tok_o >= 2:
        for mv in sorted(_o_moves(s, p, ('move',)), key=lambda m: (B.dist_rim(m.dest), m.dest)):
            if not B.adjacent(mv.dest, xd):
                continue
            n = apply(st, mv)
            if isinstance(n, ChanceNode) or n.side != 'O':
                continue
            a = Action('screen', 'O', p, target=B.dir_between(mv.dest, xd))
            if a in legal_actions(n):
                out.append(_play('seal', mv, a))
                break
    return out


def screen_plays(s, sc, d):
    """O{sc} screens X{d}: the T on him, after a Move next to him if needed."""
    return [_play('screen', *p.actions) for p in seal_plays(s, sc, d)]


def passes_to(s, r):
    return [_play('pass', Action('pass', 'O', s.ball, target=r))] if s.ball != r else []


def holder_chain(s, target, depth_ok=True, prefer=None, avoid=()):
    """Steps for 'a passer with a clean lane to target has the ball'. Returns (steps, risk). avoid: players
    the ball shouldn't go through (a screener, whose screen ends when he catches it)."""
    holders = [h for h in range(5) if h != target and h not in avoid and B.on_board(s.o[h]) and lane_clean(s, h, target)]
    if prefer is not None:
        holders = [h for h in holders if prefer(h)] or holders
    if s.ball in holders:
        return [], 0.0
    if not holders:
        mv = open_lane_moves(s, s.ball, target)
        if mv:
            return [_step(f'open{target}', f'O{target + 1} moved to open the lane', False,
                          lambda mv=mv: [_play('open the lane', m) for m in mv])], 0.0
        info = lane(s, s.ball, target)
        return [], (info['risk'] if info else 1.0)
    path = swing_path(s, set(holders), avoid=(target,) + tuple(avoid))
    if path is None:
        info = lane(s, s.ball, target)
        return [], (info['risk'] if info else 1.0)
    return swing_steps(s, path), 0.0


# ---- patterns: each reads the board for one kind of goal -------------------------------------------------

def _post_entry(s, e, mem):
    off, dfn = s.ctx.off, s.ctx.dfn
    out = []
    for p in range(5):
        if not B.on_board(s.o[p]) or off[p].bands['shot_post'] != 'H':
            continue
        d = _nearest_x(s, s.o[p])
        diff = 2 * (off[p].shot('post') - dfn[d].con('post'))
        if dfn[d].bands['con_post'] != 'L' and diff < 16:
            continue
        # the seal locks X{d}: he can't turn, so unless he already faces the post player the post-up is open
        faces = B.adjacent(s.o[p], s.x[d]) and s.arrows[d] == B.dir_between(s.x[d], s.o[p])
        edge = diff if faces else _shot_value(off[p], s.o[p] if B.zone(s.o[p]) == 'K' else (RC.RIM[0], RC.RIM[1] + 1), ('post',))
        steps = []
        on_block = B.zone(s.o[p]) == 'K' and B.adjacent(s.o[p], s.x[d])
        steps.append(_step('block', f'O{p + 1} went to the block', on_block,
                           lambda p=p, d=d: [_play('to the block', m) for m in sorted(
                               (m for m in _o_moves(s, p, ('move', 'qs')) if B.zone(m.dest) == 'K' and B.adjacent(m.dest, s.x[d])),
                               key=lambda m: (B.dist_rim(m.dest), m.dest))[:2]]))
        far = (lambda h: (s.o[h][0] - s.x[d][0]) * (s.o[s.ball][0] - s.x[d][0]) < 0) if e.get('variant') == 'far_side' else None
        hold, risk = holder_chain(s, p, prefer=far)
        steps += hold
        t = _screen_t(s, p)
        sealed = t is not None and t == s.x[d]
        steps.append(_step('seal', f'O{p + 1} sealed X{d + 1}', sealed, lambda p=p, d=d: seal_plays(s, p, d)))
        steps.append(_step('entry', f'entry to O{p + 1}', False, lambda p=p: passes_to(s, p), finish=True, risk=risk))
        out.append(dict(bind=dict(p=p, d=d), att=p, edge=float(edge), steps=steps, shot='post',
                        words=_ws(e['words'], p=p, d=d)))
    return out


def _high_low(s, e, mem):
    off, dfn = s.ctx.off, s.ctx.dfn
    out = []
    for p in range(5):
        if not B.on_board(s.o[p]) or off[p].bands['shot_post'] != 'H':
            continue
        d = _nearest_x(s, s.o[p])
        edge = 2 * (off[p].shot('post') - dfn[d].con('post'))
        if edge < 12:
            continue
        for h in range(5):
            if h == p or not B.on_board(s.o[h]) or B.zone(s.o[h]) != 'M' or B.dist_rim(s.o[h]) > 4:
                continue
            steps = []
            hold, risk = holder_chain(s, h)
            if s.ball != h:
                steps += hold + [_step('high', f'entry to O{h + 1} at the high post', False, lambda h=h: passes_to(s, h))]
            t = _screen_t(s, p)
            steps.append(_step('seal', f'O{p + 1} sealed low', t is not None and t == s.x[d], lambda p=p, d=d: seal_plays(s, p, d)))
            steps.append(_step('down', f'O{h + 1} passed down to O{p + 1}', False, lambda p=p: passes_to(s, p), finish=True))
            out.append(dict(bind=dict(p=p, h=h, d=d), att=p, edge=float(edge), steps=steps, shot='post',
                            words=_ws(e['words'], p=p, h=h)))
            break
    return out


def _isolation(s, e, mem):
    from .scoring import p_success
    off, dfn = s.ctx.off, s.ctx.dfn
    c = s.ball
    if not B.on_board(s.o[c]):
        return []
    d = _nearest_x(s, s.o[c])
    pw = float(p_success(off[c].r['dribble'] - dfn[d].r['agility'], s.ctx.rules))
    best = max((_shot_value(off[c], q) for q in _reach_squares(s, c)), default=0)
    edge = pw * best
    if edge <= 0:
        return []
    steps = []
    adj = B.adjacent(s.o[c], s.x[d])
    steps.append(_step('adj', f'O{c + 1} squared up to X{d + 1}', adj,
                       lambda c=c, d=d: [_play('square up', m) for m in _o_moves(s, c, ('move',)) if B.adjacent(m.dest, s.x[d])][:2]))
    steps.append(_step('dribble', f'O{c + 1} attacked X{d + 1} off the dribble', False,
                       lambda c=c, d=d: [_play('dribble attack', Action('dribble', 'O', c, target=d))], finish=True, risk=1 - pw))
    return [dict(bind=dict(c=c, d=d), att=c, edge=float(edge), steps=steps, shot='any', words=_ws(e['words'], c=c, d=d))]


def _reach_squares(s, i):
    return [m.dest for m in _o_moves(s, i, ('move', 'qs', 'sprint'))] + [s.o[i]]


def _closeout_empty(s, sh):
    from .advantage import looks, reach_maps
    lk = looks(s, sh, reach_maps(s))
    return bool(lk) and not any(c['clean'] for c in lk[0][2])


def _spot_up(s, e, mem):
    off = s.ctx.off
    out = []
    for sh in range(5):
        if sh == s.ball or not B.on_board(s.o[sh]) or off[sh].bands['shot_three'] != 'H':
            continue
        d = _nearest_x(s, s.o[sh])
        edge = 3 * off[sh].shot('three')
        steps = []
        on3 = B.zone(s.o[sh]) == '3'
        steps.append(_step('arc', f'O{sh + 1} got to the arc', on3,
                           lambda sh=sh: [_play('to the arc', m) for m in _o_moves(s, sh) if B.zone(m.dest) == '3'][:2]))
        empty = on3 and _closeout_empty(s, sh)
        variant = e.get('variant')

        def empty_plays(sh=sh, d=d):
            xd = s.x[d]
            mv = [m for m in _o_moves(s, sh) if B.zone(m.dest) == '3' and B.cheb(m.dest, xd) > B.cheb(s.o[sh], xd)]
            mv.sort(key=lambda m: (-B.cheb(m.dest, xd), m.dest))
            out_ = [_play('shift away', m) for m in mv[:2]]
            for sc in range(5):
                if sc not in (sh, s.ball) and B.on_board(s.o[sc]) and not s.is_screening(sc):
                    out_ += screen_plays(s, sc, d)[:1]
            return out_
        words = 'X{d}\'s closeout was drained' if variant == 'drain' else 'O{s} got clear of X{d}'
        steps.append(_step('empty', _ws(words, d=d, s=sh), empty, empty_plays))
        hold, risk = holder_chain(s, sh)
        steps += hold
        steps.append(_step('catch', ('skip pass to O{s}' if variant == 'skip' else 'pass to O{s}').replace('{s}', str(sh + 1)),
                           False, lambda sh=sh: passes_to(s, sh), finish=True, risk=risk))
        out.append(dict(bind=dict(s=sh, d=d), att=sh, edge=float(edge), steps=steps, shot='three',
                        words=_ws(e['words'], s=sh, d=d)))
    return out


def _get_open(s, e, mem):
    """V-cut (and the L-cut, veer, shallow and gap cuts): in this phase, out the next (or a Quick Step out
    now), then the catch. The memory records the cut in, and the phase it happened."""
    off = s.ctx.off
    out = []
    for r in range(5):
        if r == s.ball or not B.on_board(s.o[r]) or s.is_screening(r):
            continue
        d = _nearest_x(s, s.o[r])
        best_out = max((_shot_value(off[r], m.dest) for m in _o_moves(s, r)), default=0)
        if best_out <= 0:
            continue
        key = f'in{r}'
        cut_in = mem.get(key)
        steps = []
        if e.get('variant') == 'gap':
            steps.append(_step('gap', f'O{r + 1} cut into the gap', bool(cut_in),
                               lambda r=r: [_play('cut into the gap', m) for m in sorted(
                                   (m for m in _o_moves(s, r) if B.zone(m.dest) in ('K', 'M')), key=lambda m: B.dist_rim(m.dest))[:2]],
                               ))
        else:
            steps.append(_step('in', f'O{r + 1} cut in', bool(cut_in),
                               lambda r=r, d=d: [_play('V-cut in', m) for m in sorted(
                                   (m for m in _o_moves(s, r, ('move',)) if B.dist_rim(m.dest) < B.dist_rim(s.o[r])
                                    or B.cheb(m.dest, s.x[d]) < B.cheb(s.o[r], s.x[d])),
                                   key=lambda m: (B.dist_rim(m.dest), m.dest))[:2]]))
            stepped = mem.get(f'out{r}')
            steps.append(_step('out', f'O{r + 1} stepped out', bool(stepped),
                               lambda r=r, d=d: [_play('V-cut out', m) for m in sorted(
                                   (m for m in _o_moves(s, r) if B.cheb(m.dest, s.x[d]) > B.cheb(s.o[r], s.x[d])
                                    and _shot_value(off[r], m.dest) > 0),
                                   key=lambda m: (-_shot_value(off[r], m.dest), m.dest))[:2]]))
        hold, risk = holder_chain(s, r)
        steps += hold
        steps.append(_step('catch', f'the catch by O{r + 1}', False, lambda r=r: passes_to(s, r), finish=True, risk=risk))
        out.append(dict(bind=dict(r=r, d=d), att=r, edge=float(best_out) * 0.8, steps=steps, shot='any',
                        words=_ws(e['words'], r=r, d=d)))
    return out


def _backdoor(s, e, mem):
    out = []
    c = s.ball
    ball = s.o[c]
    for r in range(5):
        if r == c or not B.on_board(s.o[r]):
            continue
        d = _nearest_x(s, s.o[r])
        xd = s.x[d]
        if ball == xd:
            continue
        toward = B.dir_between(xd, (xd[0] + (ball[0] > xd[0]) - (ball[0] < xd[0]), xd[1] + (ball[1] > xd[1]) - (ball[1] < xd[1])))
        if (s.arrows[d] - toward) % 8 not in (0, 1, 7):
            continue
        edge = _shot_value(s.ctx.off[r], RC.RIM, ('layup', 'dunk')) * 0.85     # help can still meet him at the rim
        cut = mem.get(f'back{r}')
        steps = [_step('cut', f'O{r + 1} cut behind X{d + 1}', bool(cut) or B.zone(s.o[r]) == 'K',
                       lambda r=r, xd=xd: [_play('back cut', m) for m in sorted(
                           (m for m in _o_moves(s, r, ('move', 'qs', 'sprint')) if B.zone(m.dest) == 'K'
                            and B.cheb(m.dest, ball) >= B.cheb(xd, ball)), key=lambda m: (B.dist_rim(m.dest), m.dest))[:2]])]
        steps.append(_step('catch', f'the pass to O{r + 1} at the rim', False, lambda r=r: passes_to(s, r), finish=True))
        out.append(dict(bind=dict(r=r, d=d), att=r, edge=float(edge), steps=steps, shot='layup', words=_ws(e['words'], r=r, d=d)))
    return out


def _shift_away(s, e, mem):
    off = s.ctx.off
    c = s.ball
    out = []
    for sh in range(5):
        if sh == c or not B.on_board(s.o[sh]) or off[sh].bands['shot_three'] != 'H':
            continue
        d = _nearest_x(s, s.o[sh])
        others = [j for j in range(5) if j != d]
        if B.cheb(s.x[d], s.o[c]) > min(B.cheb(s.x[j], s.o[c]) for j in others) + 1:
            continue                      # he isn't the nearest help on the ball
        shifted = mem.get(f'shift{sh}')
        steps = [_step('shift', f'O{sh + 1} shifted away from X{d + 1}', bool(shifted),
                       lambda sh=sh, d=d: [_play('shift away', m) for m in sorted(
                           (m for m in _o_moves(s, sh) if B.zone(m.dest) == '3' and B.cheb(m.dest, s.x[d]) > B.cheb(s.o[sh], s.x[d])),
                           key=lambda m: (-B.cheb(m.dest, s.x[d]), m.dest))[:2]])]

        def attack(sh=sh, d=d):
            followed = B.cheb(s.x[d], s.o[c]) >= 3
            if followed:                                 # he followed: drive at the help that isn't there
                return [_play('drive', *p) for p in _drive_plays(s, c)]
            return passes_to(s, sh)
        steps.append(_step('attack', f'attacked the job X{d + 1} gave up', False, attack, finish=True))
        out.append(dict(bind=dict(s=sh, d=d), att=sh, edge=float(3 * off[sh].shot('three')) * 0.9, steps=steps, shot='three',
                        words=_ws(e['words'], s=sh, d=d)))
    return out


def _drive_plays(s, c):
    from .actions import legal_actions
    acts = legal_actions(s) if (s.side == 'O' and s.stage == 'play') else []
    out = [(a,) for a in acts if a.kind == 'dribble']
    mv = [a for a in acts if a.kind in ('move', 'qs', 'sprint') and a.piece == c and B.on_board(a.dest)]
    mv.sort(key=lambda a: (-_shot_value(s.ctx.off[c], a.dest), a.dest))
    out += [(a,) for a in mv[:2]]
    return out


def _baseline_cut(s, e, mem):
    out = []
    for r in range(5):
        if r == s.ball or not B.on_board(s.o[r]) or s.o[r][1] > 3:
            continue
        side = s.o[r][0] - RC.RIM[0]
        if side == 0:
            continue
        d = _nearest_x(s, s.o[r])
        went = mem.get(f'base{r}')
        steps = [_step('under', f'O{r + 1} cut along the baseline', bool(went) or (s.o[r][0] - RC.RIM[0]) * side < 0,
                       lambda r=r: [_play('baseline cut', m) for m in sorted(
                           (m for m in _o_moves(s, r) if m.dest[1] <= 2 and abs(m.dest[0] - RC.RIM[0]) < abs(s.o[r][0] - RC.RIM[0])
                            or (m.dest[1] <= 3 and (m.dest[0] - RC.RIM[0]) * side < 0)),
                           key=lambda m: ((m.dest[0] - RC.RIM[0]) * side >= 0, abs(m.dest[0] - RC.RIM[0]), m.dest))[:2]])]
        steps.append(_step('corner', f'O{r + 1} came out on the far side', (s.o[r][0] - RC.RIM[0]) * side < 0 and B.zone(s.o[r]) == '3',
                           lambda r=r: [_play('to the far corner', m) for m in sorted(
                               (m for m in _o_moves(s, r) if (m.dest[0] - RC.RIM[0]) * side < 0 and B.zone(m.dest) in ('3', 'K')),
                               key=lambda m: (-_shot_value(s.ctx.off[r], m.dest), m.dest))[:2]]))
        hold, risk = holder_chain(s, r)
        steps += hold
        steps.append(_step('catch', f'the catch by O{r + 1}', False, lambda r=r: passes_to(s, r), finish=True, risk=risk))
        out.append(dict(bind=dict(r=r, d=d), att=r, edge=float(3 * s.ctx.off[r].shot('three')) * 0.8, steps=steps, shot='three',
                        words=_ws(e['words'], r=r, d=d)))
    return out


def _give_go(s, e, mem):
    c = s.ball
    out = []
    for r in range(5):
        if r == c or not B.on_board(s.o[r]) or not lane_clean(s, c, r):
            continue
        gone = mem.get(f'give{r}')
        steps = [_step('give', f'O{c + 1} passed to O{r + 1}', bool(gone), lambda r=r: passes_to(s, r))]
        steps.append(_step('go', f'O{c + 1} cut to the rim', bool(mem.get(f'go{c}')),
                           lambda c=c: [_play('cut to the rim', m) for m in sorted(
                               (m for m in _o_moves(s, c) if B.zone(m.dest) == 'K'), key=lambda m: (B.dist_rim(m.dest), m.dest))[:2]]))
        steps.append(_step('return', f'the return pass to O{c + 1}', False, lambda c=c: passes_to(s, c), finish=True))
        out.append(dict(bind=dict(c=c, r=r), att=c, edge=float(_shot_value(s.ctx.off[c], RC.RIM, ('layup', 'dunk'))) * 0.7,
                        steps=steps, shot='layup', words=_ws(e['words'], c=c, r=r)))
        break
    return out


def _drive_kick(s, e, mem):
    c = s.ball
    if not B.on_board(s.o[c]):
        return []
    off = s.ctx.off
    shooters = [i for i in range(5) if i != c and B.on_board(s.o[i]) and off[i].bands['shot_three'] == 'H']
    if not shooters:
        return []
    sh = max(shooters, key=lambda i: off[i].shot('three'))
    steps = [_step('drive', f'O{c + 1} drove', bool(mem.get(f'drive{c}')), lambda c=c: [_play('drive', *p) for p in _drive_plays(s, c)])]
    steps.append(_step('kick', f'the kick to O{sh + 1}', False, lambda sh=sh: passes_to(s, sh), finish=True))
    return [dict(bind=dict(c=c, s=sh), att=sh, edge=float(3 * off[sh].shot('three')) * 0.75, steps=steps, shot='three',
                 words=_ws(e['words'], c=c, s=sh))]


def _ball_screen(s, e, mem):
    c = s.ball
    if not B.on_board(s.o[c]):
        return []
    off = s.ctx.off
    d = _nearest_x(s, s.o[c])
    v = e.get('variant')
    out = []
    for sc in range(5):
        if sc == c or not B.on_board(s.o[sc]) or s.is_screening(sc):
            continue
        if v == 'roll' and off[sc].bands['shot_layup'] != 'H' and off[sc].bands['shot_dunk'] != 'H':
            continue
        if v in ('pop', 'ghost') and off[sc].bands['shot_three'] != 'H' and off[sc].bands['shot_long'] != 'H':
            continue
        if v == 'gap' and off[c].bands['shot_mid'] != 'H' and off[c].bands['shot_floater'] != 'H':
            continue
        steps = []
        if v in ('slip', 'ghost'):
            near = B.cheb(s.o[sc], s.x[d]) <= 1
            steps.append(_step('approach', f'O{sc + 1} came to screen X{d + 1}', near,
                               lambda sc=sc, d=d: [_play('approach', m) for m in _o_moves(s, sc, ('move',)) if B.adjacent(m.dest, s.x[d])][:2]))
            zone = 'K' if v == 'slip' else '3'
            steps.append(_step('away', f'O{sc + 1} {"slipped to the rim" if v == "slip" else "ghosted to the arc"}', B.zone(s.o[sc]) == zone and near is False,
                               lambda sc=sc, zone=zone: [_play('slip' if zone == 'K' else 'ghost', m) for m in sorted(
                                   (m for m in _o_moves(s, sc) if B.zone(m.dest) == zone), key=lambda m: (B.dist_rim(m.dest), m.dest))[:2]]))
            steps.append(_step('catch', f'the pass to O{sc + 1}', False, lambda sc=sc: passes_to(s, sc), finish=True))
            edge = _shot_value(off[sc], RC.RIM if v == 'slip' else (2, 9)) * 0.85
        else:
            t = _screen_t(s, sc)
            screened = t is not None and t == s.x[d]
            if v == 'rescreen' and not mem.get(f'screened{sc}'):
                continue
            steps.append(_step('screen', f'O{sc + 1} screened X{d + 1}', screened or s.locked('X', d), lambda sc=sc, d=d: screen_plays(s, sc, d)))
            if v == 'spain':
                back = [j for j in range(5) if j not in (c, sc) and B.on_board(s.o[j]) and not s.is_screening(j)]
                d2 = _nearest_x(s, s.o[sc], exclude=(d,))
                if back and d2 is not None:
                    b2 = min(back, key=lambda j: B.cheb(s.o[j], s.x[d2]))
                    steps.append(_step('back', f'O{b2 + 1} back-screened X{d2 + 1}', False, lambda b2=b2, d2=d2: screen_plays(s, b2, d2)))

            def finish(c=c, sc=sc, v=v):
                out_ = [_play('use the screen', *p) for p in _drive_plays(s, c)]
                if v in ('roll', 'pop', 'spain', 'rescreen'):
                    out_ += passes_to(s, sc)
                return out_
            steps.append(_step('use', f'O{c + 1} came off the screen', False, finish, finish=True))
            edge = max(max((_shot_value(off[c], q) for q in _reach_squares(s, c)), default=0),
                       _shot_value(off[sc], RC.RIM) if v in ('roll', 'spain') else _shot_value(off[sc], (2, 9)) if v == 'pop' else 0) * 0.85
        out.append(dict(bind=dict(c=c, sc=sc, d=d), att=c, edge=float(edge), steps=steps, shot='any',
                        words=_ws(e['words'], c=c, sc=sc, d=d)))
    out.sort(key=lambda g: -g['edge'])
    return out[:1]


def _handoff(s, e, mem):
    c = s.ball
    out = []
    for r in range(5):
        if r == c or not B.on_board(s.o[r]):
            continue
        adj = B.adjacent(s.o[c], s.o[r])
        steps = [_step('next', f'O{c + 1} came next to O{r + 1}', adj,
                       lambda c=c, r=r: [_play('to the handoff', m) for m in _o_moves(s, c, ('move',)) if B.adjacent(m.dest, s.o[r])][:2])]
        steps.append(_step('hand', f'O{c + 1} handed off to O{r + 1}', False, lambda r=r: passes_to(s, r)))
        steps.append(_step('go', f'O{r + 1} came off the handoff', False, lambda r=r: [], finish=True))
        out.append(dict(bind=dict(c=c, r=r), att=r, edge=float(max((_shot_value(s.ctx.off[r], q) for q in _reach_squares(s, r)), default=0)) * 0.7,
                        steps=steps, shot='any', words=_ws(e['words'], c=c, r=r)))
    out.sort(key=lambda g: -g['edge'])
    return out[:1]


def _screen_switch(s, e, mem):
    off, dfn = s.ctx.off, s.ctx.dfn
    out = []
    for a in range(5):
        if not B.on_board(s.o[a]):
            continue
        n1 = _nearest_x(s, s.o[a])
        n2 = _nearest_x(s, s.o[a], exclude=(n1,))
        screened = lambda j: s.locked('X', j) or any(_screen_t(s, i) == s.x[j] for i in range(5) if i != a)
        found = None
        # (d, d2): the guard to screen off and the weak defender to pick him up; once the switch is made the
        # weak one is the nearest and the screened one second, which is the same goal half done
        for d, d2 in ((n1, n2), (n2, n1)):
            if d2 is None or (d == n2 and not screened(d)):
                continue
            for t in ('post', 'three', 'layup'):
                if off[a].bands['shot_' + t] == 'H' and dfn[d2].bands['con_' + t] == 'L' and dfn[d].bands['con_' + t] != 'L':
                    found = (d, d2, t)
                    break
            if found:
                break
        if not found:
            continue
        d, d2, t = found
        sc = _screener(s, d, (a, s.ball))
        if sc is None:
            continue
        held = s.locked('X', d)
        steps = [_step('screen', f'O{sc + 1} screened X{d + 1}', held or (_screen_t(s, sc) == s.x[d]), lambda sc=sc, d=d: screen_plays(s, sc, d))]
        zone = {'post': 'K', 'three': '3', 'layup': 'K'}[t]
        steps.append(_step('repos', f'O{a + 1} went at X{d2 + 1}', B.zone(s.o[a]) == zone and B.cheb(s.o[a], s.x[d2]) <= 1,
                           lambda a=a, d2=d2, zone=zone: [_play('reposition', m) for m in sorted(
                               (m for m in _o_moves(s, a) if B.zone(m.dest) == zone), key=lambda m: (B.cheb(m.dest, s.x[d2]), m.dest))[:2]]))
        hold, risk = holder_chain(s, a, avoid=(sc,)) if a != s.ball else ([], 0.0)
        steps += hold
        if a == s.ball:
            steps.append(_step('exploit', f'O{a + 1} attacked X{d2 + 1}', False, lambda a=a: [_play('attack', *p) for p in _drive_plays(s, a)], finish=True))
        else:
            steps.append(_step('exploit', f'the pass to O{a + 1} on X{d2 + 1}', False, lambda a=a: passes_to(s, a), finish=True, risk=risk))
        pts = 3 if t == 'three' else 2
        out.append(dict(bind=dict(a=a, d=d, d2=d2, sc=sc), att=a, edge=float(pts * (off[a].shot(t) - dfn[d2].con(t))), steps=steps,
                        shot=t, words=_ws(e['words'], a=a, d=d, d2=d2)))
    return out


def _offball_screen(s, e, mem):
    off = s.ctx.off
    out = []
    for r in range(5):
        if r == s.ball or not B.on_board(s.o[r]) or s.is_screening(r):
            continue
        if off[r].bands['shot_three'] != 'H' and off[r].bands['shot_layup'] != 'H':
            continue
        d = _nearest_x(s, s.o[r])
        sc = _screener(s, d, (r, s.ball))
        if sc is None:
            continue
        screened = _screen_t(s, sc) == s.x[d] or s.locked('X', d)
        steps = [_step('screen', f'O{sc + 1} screened X{d + 1}', screened, lambda sc=sc, d=d: screen_plays(s, sc, d))]
        steps.append(_step('off', f'O{r + 1} came off the screen', bool(mem.get(f'off{r}')),
                           lambda r=r, d=d: [_play('off the screen', m) for m in sorted(
                               (m for m in _o_moves(s, r) if B.cheb(m.dest, s.x[d]) > B.cheb(s.o[r], s.x[d]) and _shot_value(off[r], m.dest) > 0),
                               key=lambda m: (-_shot_value(off[r], m.dest), m.dest))[:2]]))
        hold, risk = holder_chain(s, r, avoid=(sc,))
        steps += hold
        steps.append(_step('catch', f'the catch by O{r + 1}', False, lambda r=r: passes_to(s, r), finish=True, risk=risk))
        out.append(dict(bind=dict(r=r, sc=sc, d=d), att=r, edge=float(max(3 * off[r].shot('three'), 2 * off[r].shot('layup'))) * 0.8,
                        steps=steps, shot='any', words=_ws(e['words'], r=r, sc=sc, d=d)))
    out.sort(key=lambda g: -g['edge'])
    return out[:2]


def _speed(s, e, mem):
    out = []
    for a in range(5):
        if not B.on_board(s.o[a]) or s.ctx.off[a].qs < 2:
            continue
        d = _nearest_x(s, s.o[a])
        if s.ctx.dfn[d].qs > 0:
            continue
        steps = [_step('burst', f'O{a + 1} burst away from X{d + 1}', False,
                       lambda a=a, d=d: [_play('speed burst', m) for m in sorted(
                           (m for m in _o_moves(s, a, ('qs', 'sprint')) if B.cheb(m.dest, s.x[d]) >= 2),
                           key=lambda m: (-_shot_value(s.ctx.off[a], m.dest), m.dest))[:2]])]
        if a != s.ball:
            hold, risk = holder_chain(s, a)
            steps += hold
            steps.append(_step('catch', f'the catch by O{a + 1}', False, lambda a=a: passes_to(s, a), finish=True, risk=risk))
        else:
            steps[-1]['finish'] = True
        out.append(dict(bind=dict(a=a, d=d), att=a, edge=float(max((_shot_value(s.ctx.off[a], q) for q in _reach_squares(s, a)), default=0)) * 0.8,
                        steps=steps, shot='any', words=_ws(e['words'], a=a, d=d)))
    return out


def _overload(s, e, mem):
    c = s.ball
    if not B.on_board(s.o[c]):
        return []
    side = 1 if s.o[c][0] > RC.RIM[0] else -1
    on = [i for i in range(5) if B.on_board(s.o[i]) and (s.o[i][0] - RC.RIM[0]) * side > 0]
    steps = []
    if len(on) < 3:
        cand = [i for i in range(5) if i not in on and B.on_board(s.o[i])]
        steps.append(_step('load', 'moved a third attacker to the ball side', False,
                           lambda cand=cand: [_play('overload', m) for i in cand for m in _o_moves(s, i)
                                              if (m.dest[0] - RC.RIM[0]) * side > 0][:3]))
    steps.append(_step('find', 'found the open player', False, lambda: [], finish=True))
    # the edge: the best look on that side if the help can't cover everyone, discounted like the other kick-outs
    side_players = [i for i in range(5) if B.on_board(s.o[i]) and (s.o[i][0] - RC.RIM[0]) * side > 0] or [c]
    edge = 0.7 * max(_shot_value(s.ctx.off[i], s.o[i]) for i in side_players)
    return [dict(bind=dict(side=side), att=c, edge=float(edge), steps=steps, shot='any', words=_ws(e['words'], side='right' if side > 0 else 'left'))]


PATTERNS = dict(post_entry=_post_entry, high_low=_high_low, isolation=_isolation, spot_up=_spot_up, get_open=_get_open,
                backdoor=_backdoor, shift_away=_shift_away, baseline_cut=_baseline_cut, give_go=_give_go, drive_kick=_drive_kick,
                ball_screen=_ball_screen, handoff=_handoff, screen_switch=_screen_switch, offball_screen=_offball_screen,
                speed=_speed, overload=_overload)


# ---- goals: instantiate, rank, cut to the level's chain depth --------------------------------------------

ROLL_STEPS = ('seal', 'screen', 'back', 'dribble')       # steps that need a roll to go the offence's way
STEP_KEEP = dict(roll=0.9, plain=0.97)                  # how much of the edge survives each step still to take


def _keep(todo):
    k = 1.0
    for st in todo:
        k *= STEP_KEEP['roll' if st['id'] in ROLL_STEPS else 'plain']
    return k


def _first_playable(todo):
    """The chain's next step can be taken now (a finish with no plays hands over to the advantage attack)."""
    if not todo or todo[0]['finish']:
        return True
    return bool(todo[0]['plays']())


def actions_left(s):
    """Offence actions left in the possession: this phase's tokens plus six a phase to come."""
    phases_after = max(0, s.clock // RC.PHASE_SECONDS - 1)
    return s.tok_o + phases_after * RC.TOKENS_PER_PHASE


def goals(s, level, mems=None, target=None):
    """Every goal of the level's library on this board, ranked. Each: entry, key, bind, att, edge,
    steps (cut to the level's chain depth), remaining (steps not yet done), score. Cached per board."""
    key = (s, s.ctx, level, json.dumps(mems or {}, sort_keys=True), target)
    return _cached(_GOALS, key, lambda: _goals(s, level, mems, target))


def _goals(s, level, mems=None, target=None):
    mems = mems or {}
    depth = chain_depth(level)
    out = []
    left = actions_left(s)
    inbound = bool(s.inbound) and s.ball == s.ctx.inbounder
    for e in level_goals(level):
        if inbound and e['id'] not in ('B1', 'B2', 'B3', 'E2'):
            continue                                   # F4: the first pass into a clean lane
        for g in PATTERNS[e['pattern']](s, e, mems.get(e['id'], {})):
            if s.ctx.three_only and g['shot'] not in ('three', 'any'):
                continue                               # F2: only goals that finish in a three
            steps = g['steps']
            todo = [st for st in steps if not st['done']]
            if depth == 0:
                todo = [st for st in todo if st['finish']] or todo[-1:]
            elif depth == 1:
                todo = todo[-2:]
            g.update(entry=e, key=(e['id'],) + tuple(sorted(g['bind'].items())), todo=todo, remaining=len(todo))
            if g['remaining'] > left:
                continue                               # the chain doesn't fit the clock
            if s.clock <= RC.PHASE_SECONDS and (g['remaining'] > s.tok_o or (todo and not todo[0]['finish'])):
                continue                               # F1: late clock, only a goal that finishes now
            if s.side == 'O' and s.stage == 'play' and not _first_playable(todo):
                continue                               # its next step can't be taken on this board
            risk = sum(st['risk'] for st in todo)
            if todo and todo[0]['finish'] and g['att'] != s.ball and not any(st['risk'] for st in todo):
                info = lane(s, s.ball, g['att'])          # a finish pass straight from the carrier: its own risk
                risk += (info['risk'] if info else 1.0)
            bonus = 0.0
            if s.ctx.coach_call and target is not None and g['att'] == target:
                bonus = 8.0                            # F3: the target's goals carry the card's bonus
            risk = min(1.0, risk)
            g['score'] = (1.0 - risk) * g['edge'] * _keep(todo) + risk * RC.TURNOVER_POINTS + bonus
            out.append(g)
    out.sort(key=lambda g: (-g['score'], g['key']))
    return out


# ---- the defence's objectives -----------------------------------------------------------------------------

_COUNTER = {'post_entry': 'DO-front', 'high_low': 'DO-front', 'screen_switch': 'DO-noswitch', 'spot_up': 'DO-closeout',
            'shift_away': 'DO-closeout', 'get_open': 'DO-deny', 'offball_screen': 'DO-deny', 'backdoor': 'DO-rim',
            'baseline_cut': 'DO-rim', 'give_go': 'DO-rim', 'isolation': 'DO-contain', 'ball_screen': 'DO-contain',
            'drive_kick': 'DO-rotate', 'handoff': 'DO-contain', 'speed': 'DO-contain', 'overload': 'DO-rotate'}


def defence_objectives(s, level, k=4):
    """What the offence could be building toward, read from the board and the cards only (the defence
    doesn't know the plan), as the defence's ranked objectives: value to the offence x closeness."""
    allowed = set(level_objectives(level))
    seen = {}
    for g in goals(s, 'allstar'):
        oid = _COUNTER.get(g['entry']['pattern'])
        if oid not in allowed:
            continue
        b = g['bind']
        who = dict(p=b.get('p', b.get('a', g['att'])), s=b.get('s', g['att']), r=b.get('r', g['att']),
                   c=b.get('c', s.ball), a=b.get('a', g['att']), d2=b.get('d2', 0))
        words = _ws(OBJECTIVES[oid]['words'], **who)
        weight = g['edge'] / (1.0 + g['remaining'])
        key = (oid, words)
        if key not in seen or weight > seen[key]['weight']:
            seen[key] = dict(id=oid, words=words, weight=round(weight, 2), att=g['att'], goal=g['entry']['id'], bind=b)
    out = sorted(seen.values(), key=lambda o: (-o['weight'], o['words']))
    if 'DO-reserve' in allowed and s.tok_x <= 2:
        out.insert(0, dict(id='DO-reserve', words=OBJECTIVES['DO-reserve']['words'], weight=99.0, att=None, goal=None, bind={}))
    return out[:k]


def objective_plays(s, obj, acts):
    """Defence plays that serve an objective (candidates; the evaluation still decides)."""
    from .solver import Play
    out = []
    att = obj.get('att')
    if att is None or not B.on_board(s.o[att]):
        return out
    ball = s.o[s.ball]
    me = s.o[att]
    d = _nearest_x(s, me)
    face = lambda q, to: B.nearest_dir(q, to)
    mv = [a for a in acts if a.kind == 'move' and a.side == 'X']
    if obj['id'] == 'DO-front':
        cand = [a for a in mv if a.piece == d and B.adjacent(a.dest, me) and B.cheb(a.dest, ball) < B.cheb(me, ball)
                and a.arrow == face(a.dest, ball)]
        cand.sort(key=lambda a: (B.cheb(a.dest, ball), a.dest))
        out += [Play('front the post', (a,)) for a in cand[:1]]
    elif obj['id'] in ('DO-closeout', 'DO-deny'):
        cand = [a for a in mv if a.piece == d and B.adjacent(a.dest, me) and a.arrow == B.dir_between(a.dest, me)]
        cand.sort(key=lambda a: (-B.dist_rim(me) + B.dist_rim(a.dest), a.dest))
        out += [Play('close out' if obj['id'] == 'DO-closeout' else 'deny', (a,)) for a in cand[:1]]
    elif obj['id'] == 'DO-rim':
        rim = RC.RIM
        cand = [a for a in mv if B.cheb(a.dest, rim) <= 1 and a.arrow == face(a.dest, ball)]
        cand.sort(key=lambda a: (B.cheb(s.x[a.piece], rim), a.dest))
        out += [Play('protect the rim', (a,)) for a in cand[:1]]
    return out
