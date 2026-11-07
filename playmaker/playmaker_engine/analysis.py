"""First-turn ceilings: the legacy scenario_tests.py model, and the same question under engine rules.

Legacy model (data/scenario_tests.py), rebuilt from engine primitives:
  * movement = the union of Move, Quick Step and Sprint shapes, straight-then-diagonal only;
  * no arrow-line limit on the ball carrier, no screen geometry;
  * defenders react with ONE movement and are blocked only by other X pieces;
  * the contest is the HIGHEST adjacent contest, ignoring arrows and fouls.

Engine model:
  * the ball carrier's legal movement action (arrow lines, locks, blocking by every piece);
  * the declared shot, then the defence's best single reaction action from the engine's
    legal reaction set (Move with any arrow, Quick Step, Sprint, Steal, or no reaction),
    scored with the engine's contest choice (arrows, fouls, free throws).
  Because the real reaction may use two actions, the engine number is a ceiling.
"""
from fractions import Fraction

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions, movement_dests, can_move_kind, MOVEMENT
from .resolve import apply, ChanceNode, settle
from .scenarios import SCENARIOS, scenario_state
from .scoring import contest_rating, choose_contest

LEGACY_RULES = RC.with_rules(move_either_order=False, sprint_needs_qs=False)


def _legacy_reach(p, qs, occ, locked=False):
    out = {p}
    for kind, paths in (('qs', [(None, x) for x in B.qs_paths(p, qs, LEGACY_RULES)]),
                        ('move', [(None, x) for x in B.move_paths(p, LEGACY_RULES)]),
                        ('sprint', list(B.sprint_paths(p, qs, LEGACY_RULES)))):
        if locked and kind != 'qs':
            continue
        for _, path in paths:
            # legacy lines stop at the first blocked square but keep the clear prefix
            if all(B.on_board(q) and q not in occ for q in path):
                out.add(path[-1])
    return out


def _legacy_best_shot(state, k, sp, three_only):
    z = B.zone(sp)
    if z == '.' or (three_only and z != '3'):
        return -99, None
    pts = RC.ZONE_POINTS[z]
    card = state.ctx.off[k]
    occ_x = set(state.x)
    best = (-99, None)
    for t in RC.ZONE_SHOTS[z]:
        r = card.shot(t)

        def con(j, dp):
            return contest_rating(state.ctx.dfn[j], t, dp, sp, LEGACY_RULES)

        cmax = max([con(j, dp) for j, dp in enumerate(state.x) if B.adjacent(dp, sp)] + [0])
        for j, dp in enumerate(state.x):
            occ = (occ_x - {dp}) | {sp}
            for q in _legacy_reach(dp, state.ctx.dfn[j].qs, occ):
                if B.adjacent(q, sp):
                    cmax = max(cmax, con(j, q))
        v = pts * (r - cmax)
        if v > best[0]:
            best = (v, f'{t} {r}-{cmax}')
    return best


def legacy_ceilings():
    """{n: (gift or None, gift how, top, top how)} exactly as scenario_tests.py computes them."""
    out = {}
    for n, sc in SCENARIOS.items():
        st = scenario_state(n, target=0 if sc.get('target') else None)
        three_only = st.ctx.three_only
        occ_all = set(st.o) | set(st.x)
        gift = how_g = None
        if not (sc.get('inb') or st.ctx.hold_for_one):
            k = st.ball
            sp = st.o[k]
            gift, how_g = -99, ''
            for q in sorted(_legacy_reach(sp, st.ctx.off[k].qs, occ_all - {sp}, locked=sc.get('locked') == k + 1)):
                v, h = _legacy_best_shot(st, k, q, three_only)
                if v > gift:
                    gift, how_g = v, f'O{k + 1} to {B.sq(q)}: {h}'
        top, how_t = -99, ''
        for k, p in enumerate(st.o):
            if not B.on_board(p):
                continue
            for q in sorted(_legacy_reach(p, st.ctx.off[k].qs, occ_all - {p})):
                v, h = _legacy_best_shot(st, k, q, three_only)
                if v > top:
                    top, how_t = v, f'O{k + 1} to {B.sq(q)}: {h}'
        out[n] = (gift, how_g, top, how_t)
    return out


# ---- engine rules ---------------------------------------------------------------

def _value(node, three_only):
    """Expected look of a resolved shot (shot value or free throws, -5 for a steal)."""
    if isinstance(node, ChanceNode):
        return sum(Fraction(p) * _value(s, three_only) for p, _, s in node.outcomes)
    if node.stage in ('contest', 'forced'):
        return _value(settle(node), three_only)
    r = node.result
    if r is None and node.stage == 'play' and node.tos > 0:
        return Fraction(RC.TURNOVER_POINTS)            # a stolen shot (play on since the turnover-cost ruling): the look is lost
    if r is None:
        raise ValueError('unresolved')
    if r.kind == 'steal':
        return Fraction(RC.TURNOVER_POINTS)
    if three_only and r.points != 3:
        return Fraction(0)
    return Fraction(r.shot_value + r.free_throws)


def _face_shooter(R):
    sp = R.o[R.ball]
    return R.with_(arrows=tuple(B.dir_between(p, sp) if B.adjacent(p, sp) else d for p, d in zip(R.x, R.arrows)))


def _reaction_value(R, three_only, ignore_arrows=False):
    """Defence's best single reaction to a declared shot (lower is better for it).
    ignore_arrows: every adjacent defender contests cleanly (the legacy contest)."""
    sp = R.o[R.ball]
    best = None
    if ignore_arrows:
        R = _face_shooter(R)
    for a in legal_actions(R):
        if a.kind in MOVEMENT and not B.adjacent(a.dest, sp):
            continue                                   # can't contest from there
        if ignore_arrows and a.kind == 'steal':
            continue
        nxt = apply(R, a)
        if not isinstance(nxt, ChanceNode) and nxt.stage == 'reaction':
            if ignore_arrows:
                nxt = _face_shooter(nxt)
            nxt = apply(nxt, Action('end_turn', 'X'))
        nxt = settle(nxt)
        v = _value(nxt, three_only)
        if best is None or v < best[0]:
            best = (v, str(a))
    return best


def _reaction_value2(R, three_only):
    """Defence's best reaction with up to two actions by one defender (e.g. Quick Step in, then
    a Move that turns the arrow onto the shooter), or any single action. Still a ceiling: pairs
    of actions by two different defenders are not searched."""
    best = _reaction_value(R, three_only)
    sp = R.o[R.ball]
    if R.tok_x < 2:
        return best
    seen = set()
    for a in legal_actions(R):
        if a.kind not in MOVEMENT:
            continue
        reach = RC.MOVE_STRAIGHT + R.ctx.dfn[a.piece].qs + R.ctx.rules.sprint_orth_base
        if B.cheb(a.dest, sp) > 1 + reach:
            continue
        child = apply(R, a)
        if isinstance(child, ChanceNode) or child.stage != 'reaction':
            continue
        key = (child.x, child.arrows, child.moved_x, child.cnt)
        if key in seen:
            continue
        seen.add(key)
        for b in legal_actions(child):
            if b.piece != a.piece:
                continue
            if b.kind in MOVEMENT and not B.adjacent(b.dest, sp):
                continue
            if b.kind not in MOVEMENT and b.kind != 'steal':
                continue
            v = _value(apply(child, b), three_only)
            if v < best[0]:
                best = (v, f'{a} then {b}')
    return best


def _looks(state, k, three_only):
    """Every look for player k (given the ball) after at most one movement action:
    (single-action value, description, reaction state)."""
    st = state.with_(ball=k, stage='play', side='O', turn_n=0)
    starts = [(st, 'stay')]
    for kind in ('move', 'qs', 'sprint'):
        if can_move_kind(st, 'O', k, kind):
            for dest in movement_dests(st, 'O', k, kind, st.ctx.rules):
                starts.append((apply(st, Action(kind, 'O', k, dest)), f'{kind} {B.sq(dest)}'))
    out = []
    for s0, how in starts:
        if s0.side != 'O':
            continue
        for a in legal_actions(s0):
            if a.kind == 'shot':
                R = apply(s0, a)
                if not isinstance(R, ChanceNode) and R.stage != 'reaction':
                    R = settle(R)
                if isinstance(R, ChanceNode) or R.stage != 'reaction':
                    out.append((_value(R, three_only), f'O{k + 1} {how}, {a.shot}', None))
                else:
                    out.append((_reaction_value(R, three_only)[0], f'O{k + 1} {how}, {a.shot}', R))
    return out


def two_action_ceilings(ns=None, rules=None, parts=('gift', 'top')):
    """Gift and top ceilings with the two-action reaction (branch and bound: the single-action
    value is an upper bound for each look, so looks are checked best first)."""
    out = {}
    for n in ns or SCENARIOS:
        sc = SCENARIOS[n]
        st = scenario_state(n, rules=rules, target=0 if sc.get('target') else None)
        three_only = st.ctx.three_only

        def ceiling(players):
            looks = sorted((l for k in players for l in _looks(st, k, three_only)), key=lambda l: -l[0])
            best = None
            for v1, how, R in looks:
                if best is not None and v1 <= best[0]:
                    break
                v2, react = (v1, 'no tokens') if R is None else _reaction_value2(R, three_only)
                if best is None or v2 > best[0]:
                    best = (v2, f'{how} vs {react}')
            return best

        gift = None if (sc.get('inb') or st.ctx.hold_for_one or 'gift' not in parts) else ceiling([st.ball])
        top = ceiling([k for k, p in enumerate(st.o) if B.on_board(p)]) if 'top' in parts else None
        out[n] = (gift, top)
    return out


def _best_from(state, k, three_only, ignore_arrows=False):
    """Best shot for player k (given the ball) after at most one movement action."""
    st = state.with_(ball=k, stage='play', side='O', turn_n=0)
    starts = [(st, 'stay')]
    for kind in ('move', 'qs', 'sprint'):
        if can_move_kind(st, 'O', k, kind):
            for dest in movement_dests(st, 'O', k, kind, st.ctx.rules):
                nxt = apply(st, Action(kind, 'O', k, dest))
                starts.append((nxt, f'{kind} {B.sq(dest)}'))
    best = None
    for s0, how in starts:
        if s0.side != 'O':
            continue
        for a in legal_actions(s0):
            if a.kind != 'shot':
                continue
            R = apply(s0, a)
            if isinstance(R, ChanceNode) or R.stage != 'reaction':
                v, react = _value(R, three_only), 'no tokens'
            else:
                v, react = _reaction_value(R, three_only, ignore_arrows)
            if best is None or v > best[0]:
                best = (v, f'O{k + 1} {how}, {a.shot} vs {react}')
    return best


def engine_ceilings(ns=None, ignore_arrows=False, rules=None):
    out = {}
    for n in ns or SCENARIOS:
        sc = SCENARIOS[n]
        st = scenario_state(n, rules=rules, target=0 if sc.get('target') else None)
        three_only = st.ctx.three_only
        gift = None
        if not (sc.get('inb') or st.ctx.hold_for_one):
            gift = _best_from(st, st.ball, three_only, ignore_arrows)
        top = None
        for k, p in enumerate(st.o):
            if B.on_board(p):
                b = _best_from(st, k, three_only, ignore_arrows)
                if b and (top is None or b[0] > top[0]):
                    top = b
        out[n] = (gift, top)
    return out


def _fmt(v):
    if v is None:
        return 'n/a'
    f = float(v)
    return str(int(f)) if f == int(f) else f'{f:.1f}'


def _two(n):
    return two_action_ceilings([n])[n]


def ceilings_report(workers=None):
    import os
    from concurrent.futures import ProcessPoolExecutor
    leg = legacy_ceilings()
    eng = engine_ceilings()
    flat = engine_ceilings(ignore_arrows=True)
    with ProcessPoolExecutor(workers or os.cpu_count() or 1) as ex:
        two = dict(zip(SCENARIOS, ex.map(_two, list(SCENARIOS))))
    lines = ['First-turn ceilings: legacy script vs engine rules (expected look: shot value or free throws).',
             '"no arrows" = engine movement rules but every adjacent defender contests cleanly (the legacy contest).',
             '"1 action" = engine rules, defence reacts with one action. "2 actions" = up to two actions by one defender.',
             f'{"#":>2} {"scenario":24} {"gift: legacy":>12} {"no arrows":>9} {"1 action":>8} {"2 actions":>9}   '
             f'{"top: legacy":>11} {"no arrows":>9} {"1 action":>8} {"2 actions":>9}']
    v = lambda x: _fmt(x[0] if x else None)
    for n in SCENARIOS:
        g, _, t, _ = leg[n]
        eg, et = eng[n]
        fg, ft = flat[n]
        tg, tt = two[n]
        lines.append(f'{n:>2} {SCENARIOS[n]["title"]:24} {_fmt(g):>12} {v(fg):>9} {v(eg):>8} {v(tg):>9}   '
                     f'{_fmt(t):>11} {v(ft):>9} {v(et):>8} {v(tt):>9}')
    lines.append('')
    for n in SCENARIOS:
        g, gh, t, th = leg[n]
        eg, et = eng[n]
        lines.append(f'{n:>2} legacy gift: {gh or "n/a"} | top: {th}')
        lines.append(f'   engine gift: {eg[1] if eg else "n/a"} | top: {et[1] if et else "n/a"}')
        tg, tt = two[n]
        lines.append(f'   2-action gift: {tg[1] if tg else "n/a"} | top: {tt[1] if tt else "n/a"}')
    return '\n'.join(lines)
