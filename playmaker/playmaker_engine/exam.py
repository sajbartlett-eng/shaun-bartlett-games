"""Step 3m B9: the exam (validation, not rules). Hand-built positions: the All-Star result is asserted; what Starter
and Rookie do is recorded. Tune only ai_profiles.json and the evaluation constants against these; never ratings or
rules, and never hard-code an answer.

  python3 -m playmaker_engine.exam            the table (markdown) for the report
"""
import random
import sys
import time

from . import board as B
from . import rules_config as RC
from .agent import Agent, SCALE
from .cards import TEAMS, CARDS, Card, register_cards
from .decide import Read, lane_squares
from .resolve import apply, ChanceNode
from .scenarios import game_state
from .search import play_turn, actor

OFF, DFN = 'Five Out', 'Iron Wall'
SQ = B.parse_sq
DIGITAL = RC.with_rules(digital=True)


def card_with(key, **ratings):
    """A copy of a card with some ratings changed (an exam board only: the real cards are never edited)."""
    base = CARDS[key]
    c = Card.__new__(Card)
    for k in Card.__slots__:
        setattr(c, k, getattr(base, k))
    c.r = dict(base.r)
    c.r.update(ratings)
    return c


def team(name, cards):
    return register_cards(name, cards)


def board(o, x, arrows, ball=0, off=OFF, dfn=DFN, side='O', clock=12, rules=DIGITAL, **kw):
    s = game_state(off, dfn, o, x, arrows, ball=ball, rules=rules, clock=clock, check=False)
    phase = (RC.START_CLOCK - clock) // RC.PHASE_SECONDS + 1
    s = s.with_(side=side, phase=phase, **kw)
    return s


LAST = {'agent': None}          # step 10: the agent of the last turn_of (judges that weigh the evidence read its look)


def turn_of(level, s, seed=1):
    """The level's whole turn from s: its first action and the planned rest."""
    ag = Agent(actor(s), level, seed=seed)
    a = ag.choose(s)
    t = [a] + list(ag.plan)
    LAST['agent'] = ag
    return t, ag


def search_values(s, depth):
    """Step 10: the All-Star's own search values of its candidate turns at a fixed look (no time limit, no noise):
    [(value from the side to act's view, turn)], best first. The JavaScript search when it is installed (proved equal),
    else the Python one. The evidence for judges that accept 'something the evidence shows is worth more'."""
    import json as _json
    from . import agent as _AG, jsbridge as _J
    from .agent import profile as _profile
    from .search import Searcher
    side = actor(s)
    sign = 1 if side == 'O' else -1
    p = _profile('allstar')
    if _AG.JS['search'] is not None and _J.ported(s.ctx.rules):
        req = dict(state=_J.state_json(s), ctx=_J.ctx_json(s.ctx), profile=p, budget=None, max_depth=depth, stale=None)
        out = _json.loads(_AG.JS['search'](_json.dumps(req)))
        res = [(v, tuple(_J.action_from(a) for a in t)) for v, t in out['results']]
    else:
        ag = Agent(side, 'allstar', seed=1)
        res, _ = Searcher(side, p, ag._evaluate(s), float('inf')).root(s, depth, depth)
    return sorted(((sign * v, tuple(t)) for v, t in res), key=lambda r: -r[0])


def look_depth(default=3):
    """How far the last agent looked (its fixed depth, or the depth it reached on the clock)."""
    ag = LAST['agent']
    return (ag.last or {}).get('depth') or default if ag is not None else default


def after(s, t):
    n = play_turn(s, t)
    while isinstance(n, ChanceNode):
        n = max(n.outcomes, key=lambda o: o[0])[2]
    return n


def words(t):
    return '; '.join(str(a) for a in t)


# ---- the positions ----------------------------------------------------------------------------------------------------
# Each returns (description, board or boards, check(level -> turn) -> (ok, what happened)).

WINGS = dict(o=['I9', 'B7', 'P7', 'A3', 'Q3'], x=['K9', 'C6', 'O6', 'B3', 'P3'], arrows=['W', 'NW', 'NE', 'W', 'E'])


def straight_drive(n):
    """Step 3n B4: after the defence's answer, the ball handler's straight drive: his legal movements onto the ball-rim
    line, closer to the rim, and the best look one gives him, against his team's best other look. Returns (available,
    drive value, best alternative)."""
    from .actions import movement_dests, can_move_kind
    o = n.with_(side='O', stage='play', turn_n=0) if n.stage == 'play' else n
    c = o.ball
    lane = lane_squares(o.o[c], RC.RIM, 0.5)
    dests = set()
    for kind in ('move', 'qs', 'sprint'):
        if can_move_kind(o, 'O', c, kind):
            dests |= {q for q in movement_dests(o, 'O', c, kind, o.ctx.rules) if q in lane and B.dist_rim(q) < B.dist_rim(o.o[c])}
    r = Read(o)
    drive = max((lk.base for lk in r.looks.get(c, []) if lk.c in dests), default=0.0)
    alt = max((lk.base for i, lks in r.looks.items() for lk in lks if not (i == c and lk.c in dests)), default=0.0)
    return bool(dests), drive, alt


STRONG_LANE = dict(o=['I8', 'B7', 'P7', 'A3', 'Q3'], x=['K11', 'C6', 'O6', 'B3', 'P3'], arrows=['SW', 'NW', 'NE', 'W', 'E'])


def p1():
    # step 10 (Shaun, 9 Nov 2026): the drive starts strong, worth more than the offence's best other option, before the
    # defence acts: X1 trails behind O1 at the top of the key
    s = board(STRONG_LANE['o'], STRONG_LANE['x'], STRONG_LANE['arrows'], side='X')
    lane = lane_squares(s.o[0], RC.RIM, 0.5)

    def check(t, s=s):
        n = after(s, t)
        avail, drive, alt = straight_drive(n)
        on = [j for j, q in enumerate(n.x) if q in lane and B.cheb(q, n.o[0]) <= 3]
        ok = (not avail) or drive < alt
        return ok, (f"{words(t)} (straight drive {'available' if avail else 'walled or contained'}"
                    + (f", worth {drive:.1f} against the best other look {alt:.1f}" if avail else '')
                    + f"; on the ball-rim line, reported only: {', '.join(f'X{j + 1}' for j in on) or 'nobody'})")
    return ('Straight lane: after the defence\'s answer the straight drive is walled, contained or worth less than the '
            'best alternative'), s, check


def p2():
    out = {}
    for r in (4, 12):
        cards = list(TEAMS[OFF])
        cards[1] = card_with(cards[1].key, shot_three=r)
        name = team(f'Exam sag three {r}', cards)
        out[r] = board(['I11', 'B7', 'P7', 'G3', 'Q3'], ['I10', 'C7', 'O7', 'H3', 'P3'], ['N', 'W', 'E', 'W', 'E'],
                       off=name, side='X')

    def check(levels_turns):
        n4 = after(out[4], levels_turns[4])
        n12 = after(out[12], levels_turns[12])
        d4, d12 = B.dist_rim(n4.x[1]), B.dist_rim(n12.x[1])
        cm = Read(n12)._cm[1].get(n12.o[1])
        reach12 = cm is not None and min(cm) <= 2
        return d4 < d12 and reach12, (f'three 4: X2 to {B.sq(n4.x[1])} (rim distance {d4}); three 12: X2 to '
                                      f'{B.sq(n12.x[1])} (rim distance {d12}, {"can" if reach12 else "can not"} contest)')
    return 'Sag by shooting: the same board with O2\'s three rated 4, then 12', out, check


def p3():
    # step 10: X1 has used his Move and his Quick Step, so he can't get back beside O1: help must come
    s = board(['I5', 'B7', 'P7', 'D3', 'Q3'], ['I7', 'C7', 'O7', 'G3', 'P3'], ['S', 'W', 'E', 'W', 'E'], side='X',
              beaten=((0, 0),), moved_x=1, qs_x=1)

    def check(t, s=s):
        n = after(s, t)
        movers = {a.piece for a in t if a.kind in ('move', 'qs', 'sprint')}
        helper = [j for j in movers if B.cheb(n.x[j], n.o[0]) <= 1 and B.cheb(s.x[j], s.o[0]) > 1]
        rot = [j for j in movers if j not in helper]
        ok = bool(helper) and bool(rot)
        return ok, f"{words(t)} (help: {', '.join(f'X{j + 1}' for j in helper) or 'none'}; " \
                   f"rotation: {', '.join(f'X{j + 1}' for j in rot) or 'none'})"
    return 'Help the helper: O1 has beaten X1, who has no movement left; the low man helps and another covers', s, check


def p4():
    # step 10: X5 sits between O1 and O5 off the passing line, so the pass to O5 is legal. The judge reads only what the
    # offence does: it attacks X5 (O1 shoots or drives, or the pass to O5), or picks a turn the All-Star's own search
    # rates above every attacking turn it weighs (the evidence, at the look the computer used)
    s = board(['I7', 'B7', 'P7', 'A3', 'K3'], ['I9', 'C6', 'O6', 'B3', 'J5'], ['S', 'NW', 'NE', 'W', 'NE'],
              moved_x=1)

    def attack(t):
        return any((a.kind == 'shot') or (a.kind == 'pass' and a.target == 4) or
                   (a.kind in ('move', 'qs', 'sprint', 'dribble') and a.piece == 0) for a in t)

    def check(t, s=s):
        if attack(t):
            return True, f"{words(t)} (attacks X5)"
        vals = search_values(s, look_depth())
        best_attack = max((v for v, tt in vals if attack(tt)), default=None)
        mine = next((v for v, tt in vals if list(tt) == list(t)), None)
        ok = best_attack is not None and mine is not None and mine > best_attack
        return ok, (f"{words(t)} (doesn't attack X5; its value {mine if mine is None else round(mine, 1)} against the best "
                    f"attack {best_attack if best_attack is None else round(best_attack, 1)})")
    return 'Two threats, one answer: X5 is the only answer to O1\'s pull-up and O5 at the rim', s, check


def p5():
    a = board(['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'C7', 'O6', 'B3', 'P3'], ['N', 'W', 'NE', 'W', 'E'],
              ball=1, moved_x=2, qs_x=2, cnt=(0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0))
    b = board(['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'D7', 'O6', 'B3', 'P3'], ['N', 'W', 'NE', 'W', 'E'],
              ball=1, moved_x=2, qs_x=2, cnt=(0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0))

    def check(lt):
        # step 10 (Shaun, 9 Nov 2026): A, the drive must end closer to the rim; B, a shot now, or a move to a spot where
        # no defender can Contest him (stepping up for an open three is right)
        ta, tb = lt['close'], lt['short']
        na = after(a, ta)
        drive = ta[0].kind != 'shot' and any(x.piece == 1 and x.kind in ('move', 'qs', 'sprint', 'dribble') for x in ta) \
            and B.dist_rim(na.o[1]) < B.dist_rim(a.o[1])
        shoot = tb[0].kind == 'shot' or open_spot(b, tb)
        return drive and shoot, f'closed to C7: {words(ta)}; stopped 2 short at D7: {words(tb)}'
    return 'Closeout: X2 closed from 3 squares with his Move; drive when he arrives, shoot when he stops 2 short', \
        dict(close=a, short=b), check


def open_spot(s, t):
    """Board 5 B: O2 moves (no shot) to a square where no defender can Contest him after the turn."""
    if any(x.kind == 'shot' for x in t) or not any(x.piece == 1 and x.kind in ('move', 'qs', 'sprint', 'dribble') for x in t):
        return False
    n = after(s, t)
    if n.stage == 'over' or n.o[1] == s.o[1]:
        return False
    r = Read(n.with_(ball=1, side='O', stage='play'))
    return all((r._cm[d].get(n.o[1]) is None) or min(r._cm[d].get(n.o[1])) > r.react_moves for d in range(5))


def p6():
    s = board(['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'D9', 'O7', 'H6', 'P3'], ['N', 'W', 'E', 'N', 'E'], ball=3)

    def check(t, s=s):
        # step 10 (D-94): O4 must act at once when his open look beats what the possession is worth now (the phase table)
        from .decide import vcoarse
        look = Read(s, exact=True).shot_now() or 0.0
        if look <= vcoarse(s):
            return True, f'{words(t)} (the open look {look:.1f} does not beat the possession, {vcoarse(s):.1f})'
        ok = t[0].piece == 3 and t[0].kind in ('shot', 'move', 'qs', 'sprint', 'dribble')
        return ok, words(t) + f' (open look {look:.1f} against the possession {vcoarse(s):.1f})'
    return 'Catch window: O4 caught in the corner with every cover far; he acts on his next action', s, check


def p7():
    o, x, ar = ['I11', 'B7', 'H6', 'A3', 'Q3'], ['I10', 'C7', 'H5', 'G4', 'J4'], ['N', 'W', 'N', 'NW', 'NE']
    early = board(o, x, ar, ball=2, clock=10)
    late = board(o, x, ar, ball=2, clock=2, tok_o=2)        # step 10: the offence's final turn of the possession

    def check(lt):
        te, tl = lt['phase 2'], lt['phase 6']
        ok = te[0].kind != 'shot' and tl[0].kind == 'shot'
        return ok, f'phase 2: {words(te)}; phase 6: {words(tl)}'
    return 'Clock: the same contested mid-range by O3; pass in phase 2, shoot in phase 6', \
        {'phase 2': early, 'phase 6': late}, check


def p8():
    # step 10: X1 and X2 have used their Move and Quick Step, so no defender can step into the backdoor pass
    s = board(['H10', 'D9', 'P7', 'A3', 'Q3'], ['H9', 'E9', 'O7', 'B4', 'P3'], ['N', 'W', 'E', 'W', 'E'], moved_x=3, qs_x=3)

    def check(t, s=s):
        cut = any(a.piece == 1 and a.kind in ('move', 'qs', 'sprint') and B.dist_rim(a.dest) <= B.dist_rim(s.o[1]) - 2
                  for a in t)
        return cut, words(t)
    return 'Backdoor: X2 denies O2 on the wing; the lane to the rim is open', s, check


def p9():
    s = board(['L4', 'B7', 'H11', 'D3', 'Q3'], ['L5', 'C7', 'H10', 'E4', 'K3'], ['S', 'W', 'N', 'W', 'E'],
              moved_x=16)

    def check(t, s=s):
        ok = any((a.kind == 'pass' and a.target == 4) or (a.piece == 4 and a.kind in ('move', 'qs', 'sprint'))
                 for a in t)
        return ok, words(t)
    return 'Corner: O1\'s wing drive pulled X5 off the corner; O5 relocates or gets the kick', s, check


def p10():
    o = ['I11', 'B7', 'P7', 'I9', 'Q3']
    weak = board(o, ['I12', 'C7', 'O7', 'I8', 'P3'], ['S', 'W', 'E', 'N', 'E'], off='Twin Towers', dfn='Run and Gun',
                 ball=3, side='X')
    strong = board(['I9', 'B7', 'P7', 'A3', 'Q3'], ['I8', 'C7', 'O7', 'B3', 'P3'], ['N', 'W', 'E', 'W', 'E'],
                   off='Ball Movement', dfn='Twin Towers', ball=0, side='X', clock=12)

    def check(lt):
        tw, ts = lt['good odds'], lt['bad odds']
        ok = any(a.kind == 'steal' for a in tw) and not any(a.kind == 'steal' for a in ts)
        return ok, f'good odds: {words(tw)}; bad odds, early: {words(ts)}'
    return 'Steal: tried with good odds (a weak dribbler, a teammate near); declined early on a strong dribbler', \
        {'good odds': weak, 'bad odds': strong}, check


def p11():
    o = ['I11', 'B7', 'P7', 'A3', 'Q3']
    x = ['I10', 'C6', 'O7', 'B3', 'E9']          # step 10: X2 off the passing line, so the pass to O2 is legal
    early = board(o, x, ['N', 'W', 'E', 'W', 'SW'], clock=12)
    late = board(o, x, ['N', 'W', 'E', 'W', 'SW'], clock=2, tok_o=2)      # the offence's final turn

    def check(lt):
        te, tl = lt['early'], lt['final phase']
        bad_early = any(a.kind == 'pass' and a.target == 1 for a in te)
        late_pass = any(a.kind == 'pass' for a in tl)
        return (not bad_early) and late_pass, f'early: {words(te)}; final phase: {words(tl)}'
    return 'Contested pass: the pass to O2 crosses X5\'s lane; declined early, accepted in the final phase ' \
           '(O1 has no forced shot from plain wood)', dict(early=early, **{'final phase': late}), check


def p12():
    s = board(['D5', 'A3', 'P7', 'K9', 'Q3'], ['D4', 'B3', 'O7', 'K8', 'P3'], ['N', 'W', 'E', 'N', 'E'], side='X')

    def check(t, s=s):
        n = after(s, t)
        ok = B.cheb(n.x[1], n.o[1]) <= 1
        return ok, f'{words(t)} (X2 ends {B.cheb(n.x[1], n.o[1])} square(s) from O2)'
    return 'Strong-side corner: X2 on the elite shooter O2 in the corner; O1\'s drive is contained by X1', s, check


def p13():
    s = board(['I9', 'B7', 'P7', 'A3', 'I6'], ['G9', 'C7', 'O7', 'B3', 'H5'], ['E', 'W', 'E', 'W', 'N'])
    lane = lane_squares(s.o[0], RC.RIM, 0.5)

    def check(t, s=s):
        n = after(s, t)
        still = n.o[4] in lane and not any(a.kind in ('shot', 'pass') for a in t)
        return not still, words(t)
    return 'Spacing: O5 stands in O1\'s driving lane', s, check


def p14():
    off = team('Exam mirror O', [CARDS['ppgC'], CARDS['shsA'], CARDS['shsA'], CARDS['stpfA'], CARDS['stpfA']])
    dfn = team('Exam mirror X', [CARDS['dpgB'], CARDS['bgsB'], CARDS['bgsB'], CARDS['rpcB'], CARDS['rpcB']])
    s = board(['I11', 'B7', 'P7', 'D3', 'N3'], ['I10', 'C7', 'O7', 'E3', 'M3'], ['N', 'W', 'E', 'W', 'E'],
              off=off, dfn=dfn)

    def check(firsts, lead=None):
        # step 10 (D-97, Shaun, 9 Nov 2026): predictable is fine when one move is clearly best. Met when the top first
        # move leads the next by more than the variety margin (the All-Star's own search, at the look it used);
        # otherwise no first move above 70% over the 20 seeds
        from collections import Counter
        from .agent import profile as _profile
        margin = _profile('allstar')['variety_margin']
        c = Counter(firsts)
        top = c.most_common(1)[0][1] / len(firsts)
        if lead is not None and lead > margin:
            return True, (f'the top first move leads by {lead:.1f}, more than the variety margin {margin} '
                          f'({len(c)} different first actions over {len(firsts)} seeds; the most common {round(100 * top)}%)')
        return top <= 0.7, (f'{len(c)} different first actions over {len(firsts)} seeds; the most common {round(100 * top)}%'
                            + (f' (the top first move leads by {lead:.1f})' if lead is not None else ''))
    return 'Variety: a mirror-image board; clearly best, or no option above 70% over 20 seeds', s, check


def p15():
    s = board(['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'C7', 'O7', 'B3', 'P3'], ['N', 'W', 'E', 'W', 'E'])

    def check(goals):
        seq = [g for g in goals if g]
        flips = sum(1 for k in range(2, len(seq)) if seq[k] == seq[k - 2] and seq[k] != seq[k - 1])
        return flips == 0, f"goals over the line: {' > '.join(dict.fromkeys(seq)) or 'none'}; flip-flops {flips}"
    return 'Goal consistency: six turn groups on a fixed board; one goal unless a logged reason', s, check


def p16():
    """Capacity drain (addendum): no single off-ball move gains after one reply, but a sequence over the phase drains
    a defender's capacity and opens a shot. The board: O2 an elite shooter on the wing; X2 sags to the elbow and is
    the only defender who can answer cuts into his side, so every answer spends his Move or Quick Step."""
    s = board(['I11', 'B7', 'H9', 'D3', 'Q3'], ['I10', 'F7', 'H8', 'E3', 'P3'], ['N', 'W', 'N', 'W', 'E'])

    def check(lt):
        from .trainer import credit
        t, line = lt['turn'], lt['line']
        offball = [a for a in t if a.side == 'O' and a.piece != s.ball and a.kind in ('move', 'qs', 'sprint')]
        reply = credit(s, offball[:1], horizon='reply')[0]['phi'] if offball else None
        phase = credit(s, offball[:1], horizon='phase')[0] if offball else None
        drained = lt['drained']
        ok = bool(offball) and drained and lt['gain'] >= 3.0 and phase is not None and phase['drain'] > 0
        return ok, (f"line: {' / '.join(line) or 'none'}; X2 capacity spent: {'yes' if drained else 'no'}; "
                    f"value {lt['start']:+.1f} to {lt['end']:+.1f}; first off-ball move credit "
                    + (f"{reply:+.1f} over one reply, {phase['phi']:+.1f} over the phase (drain {phase['drain']:+.1f})"
                       if phase else 'none: no off-ball move in its first turn'))
    return 'Capacity drain: off-ball moves over the phase drain X2 and open O2', s, check


def p17():
    """Turn economy (addendum B0): over every exam board, no cover uses more than 2 responses, no threat is realised
    with more actions than the turn allows, and the defence never answers with more than 2 actions in a turn."""
    boards = []
    for f in POSITIONS[:15]:
        _, b, _ = f()
        boards += list(b.values()) if isinstance(b, dict) else [b]

    def check(_):
        bad = []
        for b in boards:
            r = Read(b)
            if len(r.cover()['choice']) > 2:
                bad.append(f'cover of {len(r.cover()["choice"])}')
            o_to_act = b.side == 'O' and b.stage == 'play'
            for i, lks in r.looks.items():
                for lk in lks:
                    if lk.route == 'shoot' and lk.c != b.o[i]:
                        bad.append('a shot from a square he is not on')
                    if lk.route == 'drive' and lk.now and not (o_to_act and b.turn_n == 0):
                        bad.append('a drive and shot that needs three actions')
                    if lk.route in ('drive', 'shoot') and not lk.now and lk.replies < 1:
                        bad.append('a later drive with no defence reply before it')
                    if i != b.ball and lk.replies < 1:
                        bad.append('a receiver shooting without a defence reply')
                    if lk.route == 'cut' and not (o_to_act and b.turn_n == 0) and lk.replies < 2:
                        bad.append('a cut, catch and shot in one go')
        return not bad, f'{len(boards)} boards; ' + ('no breach' if not bad else '; '.join(sorted(set(bad))))
    return 'Turn economy: at most 2 defensive actions a turn; no threat realised with more actions than the turn allows', \
        None, check


POSITIONS = [p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17]


def c2():
    """Step 10 (D-109, rebuilt): the clean pass against the contested one. Two equal shooters on the wings (the mirror
    teams). X1 has used his Move and Quick Step; X2 sags low below O2, out of reach of the pass to O2 but in reach of
    a closeout; X3 stays up the line, where he can step into the pass to O3. Met when the All-Star doesn't throw the
    contested pass and its own search rates the clean pass above it."""
    off = team('Exam mirror O', [CARDS['ppgC'], CARDS['shsA'], CARDS['shsA'], CARDS['stpfA'], CARDS['stpfA']])
    dfn = team('Exam mirror X', [CARDS['dpgB'], CARDS['bgsB'], CARDS['bgsB'], CARDS['rpcB'], CARDS['rpcB']])
    s = board(['I11', 'B7', 'P7', 'D3', 'N3'], ['I10', 'B4', 'O6', 'E3', 'M3'], ['N', 'N', 'N', 'W', 'E'],
              off=off, dfn=dfn, moved_x=1, qs_x=1)
    CLEAN, CONTESTED = 1, 2

    def check(t, s=s):
        if any(a.kind == 'pass' and a.target == CONTESTED for a in t):
            return False, f'{words(t)} (the contested pass)'
        vals = {}
        for v, tt in search_values(s, look_depth()):
            if len(tt) == 1 and tt[0].kind == 'pass':
                vals[tt[0].target] = v
        vc, vx = vals.get(CLEAN), vals.get(CONTESTED)
        ok = vc is not None and (vx is None or vc > vx)
        return ok, (f"{words(t)} (the clean pass {'not weighed' if vc is None else round(vc, 1)}, the contested pass "
                    f"{'not weighed' if vx is None else round(vx, 1)})")
    return 'Clean pass: two equal shooters; the pass to O2 is clean, the pass to O3 contested', s, check


CANDIDATES = {'C2': c2}


def drain_line(level, s, turns_=3):
    """Play the offence (the level) and the defence's best cover for up to `turns_` offence turns within the phase.
    Returns (offence moves played, whether X2 spent capacity, start value, end value)."""
    from .trainer import _play_cover, phase_value, _end_turn
    ag = Agent('O', level, seed=1)
    start = phase_value(s, max_turns=2)
    line = []
    n = s
    for _ in range(turns_):
        if n.stage != 'play' or actor(n) != 'O' or n.phase != s.phase:
            break
        a = ag.choose(n)
        t = [a] + list(ag.plan)
        ag.plan = []
        line.append(words(t))
        if any(x.kind in ('shot', 'pass') for x in t):
            n = after(n, t)
            break
        n = after(n, t)
        if not isinstance(n, ChanceNode) and n.stage == 'play' and actor(n) == 'O':
            n = _end_turn(n)
        if not isinstance(n, ChanceNode) and n.stage == 'play' and actor(n) == 'X':
            n, _ = _play_cover(n, Read(n).cover()['choice'])
    drained = bool((n.moved_x | n.qs_x) >> 1 & 1) if not isinstance(n, ChanceNode) and n.stage != 'over' else True
    end = phase_value(n, max_turns=1) if not isinstance(n, ChanceNode) and n.stage != 'over' else \
        (n.result.shot_value if n.result else 0)
    return line, drained, start, end


def run_position(n, level):
    """(ok, what the level did) for position n (1-based) at a level."""
    desc, boards, check = POSITIONS[n - 1]()
    if n == 14:
        firsts = []
        for seed in range(20):
            t, _ = turn_of(level, boards, seed=seed)
            firsts.append(str(t[0]))
        best = {}
        for v, tt in search_values(boards, look_depth()):
            best.setdefault(str(tt[0]), v)
        top2 = sorted(best.values(), reverse=True)[:2]
        lead = top2[0] - top2[1] if len(top2) == 2 else None
        ok, what = check(firsts, lead)
        return desc, ok, what
    if n == 16:
        t, _ = turn_of(level, boards)
        line, drained, start, end = drain_line(level, boards)
        ok, what = check(dict(turn=t, line=line, drained=drained, start=start, end=end, gain=end - start))
        return desc, ok, what
    if n == 17:
        ok, what = check(None)
        return desc, ok, what
    if n == 15:
        ag = Agent('O', level, seed=3)
        s = boards
        goals = []
        for _ in range(6):
            if s.stage == 'over' or actor(s) != 'O':
                break
            a = ag.choose(s)
            goals.append(ag.commit.words)
            n_ = apply(s, a)
            while isinstance(n_, ChanceNode):
                n_ = max(n_.outcomes, key=lambda o: o[0])[2]
            s = n_
            while s.stage != 'over' and actor(s) == 'X':          # a passive defence: it ends its turns
                from .actions import legal_actions
                acts = legal_actions(s)
                w = next((x for x in acts if x.kind in ('end_turn', 'pause', 'forfeit')), acts[0])
                s = apply(s, w)
                while isinstance(s, ChanceNode):
                    s = max(s.outcomes, key=lambda o: o[0])[2]
        ok, what = check(goals)
        reasons = [g['reason'] for g in ag.commit.log]
        return desc, ok, what + (f" (switches: {'; '.join(reasons[1:])})" if len(reasons) > 1 else '')
    if isinstance(boards, dict):
        turns = {k: turn_of(level, b)[0] for k, b in boards.items()}
        ok, what = check(turns)
        return desc, ok, what
    t, _ = turn_of(level, boards)
    ok, what = check(t)
    return desc, ok, what


def table(levels=('allstar', 'starter', 'rookie'), scale=1.0, only=None):
    SCALE['value'] = scale
    rows = []
    for n in range(1, len(POSITIONS) + 1):
        if only and n not in only:
            continue
        row = dict(n=n)
        for lv in levels:
            t0 = time.time()
            desc, ok, what = run_position(n, lv)
            row['desc'] = desc
            row[lv] = dict(ok=ok, what=what, seconds=round(time.time() - t0, 1))
        rows.append(row)
    return rows


def markdown(rows):
    out = ['| # | Position | All-Star (asserted) | Starter | Rookie |', '|---|---|---|---|---|']
    for r in rows:
        cell = lambda lv: (('PASS: ' if r[lv]['ok'] else 'FAIL: ') if lv == 'allstar' else '') + r[lv]['what'] \
            if lv in r else ''
        out.append(f"| {r['n']} | {r['desc']} | {cell('allstar')} | {cell('starter')} | {cell('rookie')} |")
    return '\n'.join(out)


if __name__ == '__main__':
    only = [int(a) for a in sys.argv[1:]] or None
    rows = table(only=only)
    print(markdown(rows))
