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
from .resolve import apply, ChanceNode
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
    r = node.result
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
        v = _value(nxt, three_only)
        if best is None or v < best[0]:
            best = (v, str(a))
    return best


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


def ceilings_report():
    leg = legacy_ceilings()
    eng = engine_ceilings()
    flat = engine_ceilings(ignore_arrows=True)
    lines = ['First-turn ceilings: legacy script vs engine rules (expected look: shot value or free throws).',
             '"no arrows" = engine movement rules but every adjacent defender contests cleanly (the legacy contest).',
             f'{"#":>2} {"scenario":24} {"gift: legacy":>12} {"no arrows":>9} {"engine":>7}   {"top: legacy":>11} {"no arrows":>9} {"engine":>7}']
    v = lambda x: _fmt(x[0] if x else None)
    for n in SCENARIOS:
        g, _, t, _ = leg[n]
        eg, et = eng[n]
        fg, ft = flat[n]
        lines.append(f'{n:>2} {SCENARIOS[n]["title"]:24} {_fmt(g):>12} {v(fg):>9} {v(eg):>7}   {_fmt(t):>11} {v(ft):>9} {v(et):>7}')
    lines.append('')
    for n in SCENARIOS:
        g, gh, t, th = leg[n]
        eg, et = eng[n]
        lines.append(f'{n:>2} legacy gift: {gh or "n/a"} | top: {th}')
        lines.append(f'   engine gift: {eg[1] if eg else "n/a"} | top: {et[1] if et else "n/a"}')
    return '\n'.join(lines)
