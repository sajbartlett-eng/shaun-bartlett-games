"""Step 3m Part D: the trainer. It reads each human decision and guides progress; it says nothing during play (except
Learn mode's "Your goal this turn") and reports facts and replays, never verdicts on the person.

  D1 grade_group     every human turn group, in expectation over the dice before the roll: value lost = the All-Star
                     best turn's value minus the chosen turn's value; bands; the dice outcome reported separately.
  D2 credit          exact two-player Shapley credit for each action, re-solving the defence's best reply in every
                     counterfactual (a decoy is worth something only because the defence answers it), split into
                     direct / indirect (naming the defender who moved) / risk; flags (valuable off-ball move,
                     minimal value), kept only when their sign and band agree at depth d and d+1.
  D3 reveal          the timing check: the best legal reordering of the same actions across this and the next turn
                     group against the actual order.
  D4 goal_read       the human's goal (the predicate whose Q his turn raised most) against the best goal.
  D5 summary         1 to 3 points a possession: the best decision first, then at most two needs with the better
                     option and its value; faded as the rating rises.
  D6 skills, rating  categories, Glicko-2 against fixed computer anchors, advancement and practice suggestions.
All numbers live in ai_profiles.json ('trainer').
"""
import math
import statistics as st
import time

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions
from .agent import Agent, profile, SCALE
from .decide import Read, CONFIG
from .goals import goals_in, _likeliest
from .glicko2 import rate, expected  # noqa: F401  (expected is re-exported for the API)
from .resolve import apply, ChanceNode
from .search import Searcher, play_turn, actor, turns, terminal_value, VMIN, VMAX

TC = CONFIG['trainer']


# ---- values ------------------------------------------------------------------------------------------------------------

def _ev(node, fn):
    if isinstance(node, ChanceNode):
        return sum(float(p) * _ev(sub, fn) for p, _, sub in node.outcomes)
    return fn(node)


def _leaf(s):
    if s.stage == 'over':
        return terminal_value(s)
    return Read(s).leaf()


def reply_value(s, depth=1, budget=0.25):
    """V(s) with the side to act answering at its best (the defence's re-solved reply when it is the defence to act),
    searched `depth` turns; in expectation over the dice."""
    if isinstance(s, ChanceNode):
        return _ev(s, lambda n: reply_value(n, depth, budget))
    if s.stage == 'over':
        return terminal_value(s)
    if depth <= 0:
        return _leaf(s)
    p = dict(profile('allstar'), opponent_model=1.0)
    sr = Searcher(actor(s), p, _leaf_ev, time.time() + budget)
    try:
        return sr.value(s, depth, VMIN, VMAX)
    except Exception:
        return _leaf(s)


def _leaf_ev(node):
    return _ev(node, _leaf)


def turnover_p(node):
    """The probability a turn's rolls end in a turnover (a pick-off, a steal, a lost possession)."""
    if isinstance(node, ChanceNode):
        return sum(float(p) * turnover_p(sub) for p, _, sub in node.outcomes)
    r = node.result
    return 1.0 if (node.stage == 'over' and r is not None and r.kind in ('turnover_end', 'steal')) else 0.0


def _end_turn(s):
    """End the current side's turn (to let the other side reply), if it can."""
    if isinstance(s, ChanceNode) or s.stage == 'over':
        return s
    side = actor(s)
    for a in legal_actions(s):
        if a.kind == 'end_turn' and a.side == side:
            return apply(s, a)
    return s


def group_value(s, t, depth=0, budget=0.25):
    """The value (offence's view) of playing turn t from s, then the other side's best reply, before any roll.
    depth 0: the leaf, whose coverage term is the defence's re-solved best cover; depth >= 1: a search."""
    n = play_turn(s, t)
    if not isinstance(n, ChanceNode) and n.stage != 'over' and actor(n) == actor(s):
        n = _end_turn(n)
    if depth <= 0:
        return _ev(n, _leaf)
    return reply_value(n, depth, budget)


def root_turns(s, beam=12):
    """The All-Star's candidate turns here (geometry-generated, ordered), each valued with group_value."""
    sr = Searcher(actor(s), dict(profile('allstar'), noise=0.0), _leaf_ev, time.time() + 60)
    ts = turns(s, beam, read=Read(s), evaluate=sr.quick)
    return [(group_value(s, t), t) for _, t in ts]


# ---- D1: grade a turn group ---------------------------------------------------------------------------------------------

def band(loss, dto):
    if loss >= TC['blunder'] or dto >= TC['blunder_turnover_pp'] / 100.0:
        return 'blunder'
    if loss >= TC['mistake']:
        return 'mistake'
    if loss >= TC['inaccuracy']:
        return 'inaccuracy'
    return 'best' if loss <= 1e-9 else 'good'


def grade_group(s, chosen, budget=1.0, depth=0, results=None):
    """Grade one human turn group (chosen: its actions) at the state before it, in expectation over the dice: the
    chosen turn's value and the All-Star best's (each with the defence's re-solved best reply), value lost, the band,
    turnover chances, the better turn. results: the All-Star's valued turns (root_turns), if already computed."""
    side = actor(s)
    sign = 1 if side == 'O' else -1
    results = results if results is not None else root_turns(s)
    reached = 1
    v_chosen = group_value(s, chosen, depth)
    cands = [(v, t) for v, t in results]
    cands.append((v_chosen, tuple(chosen)))
    best_v, best_t = max(cands, key=lambda r: sign * r[0])
    loss = max(0.0, sign * (best_v - v_chosen))
    to_c = turnover_p(play_turn(s, chosen))
    to_b = turnover_p(play_turn(s, best_t))
    return dict(side=side, value=round(v_chosen, 2), best=round(best_v, 2), loss=round(loss, 2),
                band=band(loss, to_c - to_b), turnover=round(to_c, 3), best_turnover=round(to_b, 3),
                better=[str(a) for a in best_t] if loss > 1e-9 else None, depth=reached)


def accuracy(losses, k=4.0):
    """Possession accuracy: each turn group's accuracy 100 x exp(-loss / k), combined by a harmonic mean, so one
    blunder shows."""
    if not losses:
        return 100.0
    accs = [max(1.0, 100.0 * math.exp(-l / k)) for l in losses]
    return round(len(accs) / sum(1.0 / a for a in accs), 1)


# ---- D2: credit for each action ------------------------------------------------------------------------------------------

def _apply_seq(s, acts):
    n = s
    for a in acts:
        if isinstance(n, ChanceNode) or n.stage == 'over' or a not in legal_actions(n):
            return None
        n = apply(n, a)
    return n


def _reply(n, depth, budget):
    """The other side's best reply from n (after ending this side's turn): (value, the reply turn, state after).
    depth 0: the best cover solved in the leaf (the reply is the cover's chosen responses); depth >= 1: searched."""
    if n is None:
        return None, None, None
    if depth <= 0:
        if not isinstance(n, ChanceNode) and n.stage != 'over' and actor(n) == 'O':
            n = _end_turn(n)
        if isinstance(n, ChanceNode) or n.stage == 'over':
            return _ev(n, _leaf), (), n
        r = Read(n)
        v = r.leaf()
        after, played = _play_cover(n, r.cover()['choice'])
        return v, tuple(str(a) for a in played), after
    side = actor(n) if not isinstance(n, ChanceNode) else None
    if isinstance(n, ChanceNode) or n.stage == 'over':
        return _ev(n, _leaf), (), n
    if side == 'O':
        n = _end_turn(n)
    if isinstance(n, ChanceNode) or n.stage == 'over':
        return _ev(n, _leaf), (), n
    p = dict(profile('allstar'), noise=0.0, opponent_model=1.0)
    sr = Searcher(actor(n), p, _leaf_ev, time.time() + budget)
    ts = turns(n, 12, evaluate=sr.quick)
    best = None
    for _, t in ts:
        after = play_turn(n, t)
        v = _ev(after, _leaf) if depth <= 1 else reply_value(after, depth - 1, budget / 4)
        if best is None or (v < best[0] if actor(n) == 'X' else v > best[0]):
            best = (v, t, after)
    if best is None:
        return _ev(n, _leaf), (), n
    return best


def phase_value(n, max_turns=3):
    """D2 horizon: the value to the end of the current phase, the defence's capacity carried from turn to turn.
    The defence plays its best cover each turn (as legal actions); the offence plays its best turn by the leaf;
    stops at the phase's end, the possession's end, or after max_turns offence turns (then the leaf, B4)."""
    if n is None:
        return None
    if isinstance(n, ChanceNode):
        return _ev(n, lambda m: phase_value(m, max_turns))
    phase = n.phase
    k = guard = 0
    while not isinstance(n, ChanceNode) and n.stage == 'play' and n.phase == phase and k < max_turns and guard < 3 * max_turns + 3:
        guard += 1
        if actor(n) == 'X':
            before = n
            n, _ = _play_cover(n, Read(n).cover()['choice'])
            if n is before:                          # the defence can't move or end its turn here: stop and read the leaf
                break
            continue
        sr = Searcher('O', dict(profile('allstar'), noise=0.0), _leaf_ev, time.time() + 30)
        ts = turns(n, 6, evaluate=sr.quick, expand=2, second=1)
        if not ts:
            break
        t = max(((group_value(n, t), t) for _, t in ts), key=lambda r: r[0])[1]
        nxt = play_turn(n, t)
        if not isinstance(nxt, ChanceNode) and nxt.stage == 'play' and actor(nxt) == 'O':
            nxt = _end_turn(nxt)
        n = nxt
        k += 1
    return _ev(n, _leaf)


def _play_cover(n, choice):
    """Play the best cover's responses as the defence's legal actions (a Move with its arrow, or a Quick Step), then
    end its turn: the position the offence plays on from."""
    played = []
    for j, (q, a, used) in sorted(choice.items()):
        if isinstance(n, ChanceNode) or n.stage == 'over' or actor(n) != 'X':
            break
        legal = legal_actions(n)
        act = next((x for x in legal if x.piece == j and x.side == 'X' and x.dest == q and
                    (x.kind == 'move' and x.arrow == a or x.kind in ('qs', 'sprint') and used != 'move')), None)
        if act is None:
            act = next((x for x in legal if x.piece == j and x.side == 'X' and x.dest == q and x.kind in ('move', 'qs', 'sprint')), None)
        if act is None:
            continue
        n = apply(n, act)
        played.append(act)
    if not isinstance(n, ChanceNode) and n.stage != 'over' and actor(n) == 'X':
        end = next((x for x in legal_actions(n) if x.kind in ('end_turn', 'pause', 'forfeit') and x.side == 'X'), None)
        if end is not None:
            n = apply(n, end)
    return n, played


def _drain(before, after):
    """The drain channel: the value of capacity the defence spent answering (Moves, Quick Steps, tokens), at the
    leaf of the position after its reply, against the same position with that capacity given back. Returns
    (value, the defender who spent the most, what he spent)."""
    if after is None or isinstance(after, ChanceNode) or after.stage == 'over':
        return 0.0, None, ''
    spent = [(bin((after.moved_x & ~before.moved_x) >> j & 1).count('1') + bin((after.qs_x & ~before.qs_x) >> j & 1).count('1'), j)
             for j in range(5)]
    if not any(c for c, _ in spent):
        return 0.0, None, ''
    cnt = list(after.cnt)
    cnt[6] = before.cnt[6]
    restored = after.with_(moved_x=before.moved_x, qs_x=before.qs_x, cnt=tuple(cnt), tok_x=max(after.tok_x, before.tok_x))
    v = _ev(after, _leaf) - _ev(restored, _leaf)
    c, j = max(spent)
    what = ' and '.join(w for w, bit in (('Move', after.moved_x & ~before.moved_x), ('Quick Step', after.qs_x & ~before.qs_x))
                        if bit >> j & 1)
    return v, j, what


def _cf(s, seq, depth, budget, horizon):
    """A counterfactual: the actions, then the defence's re-solved best reply; valued over one reply or to the end
    of the phase. Returns (value, state after the reply) or (None, None) if the actions aren't legal alone."""
    n = _apply_seq(s, seq)
    if n is None:
        return None, None
    v, _, after = _reply(n, depth, budget)
    if horizon == 'phase':
        v = phase_value(after)
    return v, after


def credit(s, acts, depth=0, budget=0.4, horizon='phase'):
    """Shapley credit for a one- or two-action offence turn group, the defence's reply re-solved in every
    counterfactual, valued over the rest of the phase (D2 horizon; 'reply': over one reply). Channels: direct (the
    actor's own threat), indirect (teammates' uncovered threat, naming the defender who moved), drain (the capacity
    the defence spent answering), risk (turnover chance x the value at stake). If an action isn't legal on its own,
    the pair is credited together. Returns [dict(action, phi, direct, indirect, drain, risk, moved, together)]."""
    acts = list(acts)
    V0 = phase_value(s) if horizon == 'phase' else _ev(s, _leaf)
    r0 = Read(s)
    v12, after12 = _cf(s, acts, depth, budget, horizon)
    if v12 is None:
        return []
    rows = []
    together = False
    if len(acts) == 1:
        phis = [v12 - V0]
    else:
        v1, _ = _cf(s, acts[:1], depth, budget, horizon)
        v2, _ = _cf(s, acts[1:], depth, budget, horizon)
        if v1 is None or v2 is None:
            together = True                          # one isn't legal without the other: credit the pair
            phis = [v12 - V0]
        else:
            phis = [0.5 * ((v1 - V0) + (v12 - v2)), 0.5 * ((v2 - V0) + (v12 - v1))]
    groups = [acts] if together else [[a] for a in acts]
    for k, grp in enumerate(groups):
        a = grp[0]
        direct = indirect = 0.0
        moved = None
        after = after12
        if after is not None and not isinstance(after, ChanceNode) and after.stage != 'over' and a.piece >= 0:
            ra = Read(after)
            me = {x.piece for x in grp}
            direct = sum(ra.threat.get(i, {}).get('value', 0.0) - r0.threat.get(i, {}).get('value', 0.0) for i in me)
            res0, res1 = r0.cover()['residual'], ra.cover()['residual']
            others_b = max((res0[i] for i in res0 if i not in me), default=0.0)
            others_a = max((res1[i] for i in res1 if i not in me), default=0.0)
            indirect = others_a - others_b
            shifts = [(B.cheb(s.x[j], after.x[j]), j) for j in range(5)]
            d, j = max(shifts)
            moved = j if d > 0 else None
        before_reply = _apply_seq(s, grp if not together else acts)
        dv, dj, what = _drain(before_reply if before_reply is not None and not isinstance(before_reply, ChanceNode) else s,
                              after)
        to = turnover_p(play_turn(s, grp))
        risk = -to * max(0.0, V0)
        rows.append(dict(action='; '.join(str(x) for x in grp), piece=a.piece, phi=round(phis[k], 2), direct=round(direct, 2),
                         indirect=round(indirect, 2), drain=round(dv, 2), drained=dj, drained_what=what,
                         risk=round(risk, 2), moved=moved, together=together))
    return rows


def flags(s, acts, credits_d, credits_d1):
    """Credit flags, kept only when they agree at depth d and d+1 (sign and band)."""
    out = []
    for c, c1 in zip(credits_d, credits_d1):
        if c.get('drain', 0) >= TC['inaccuracy'] and c1.get('drain', 0) >= TC['inaccuracy'] and c.get('drained') is not None:
            out.append(dict(kind='drain', action=c['action'], value=c['drain'],
                            text=f"X{c['drained'] + 1} used his {c['drained_what']} answering {c['action']}, so he can't "
                                 f"close out with it later this phase: {c['drain']:+.1f}."))
        if c['indirect'] >= TC['inaccuracy'] and c1['indirect'] >= TC['inaccuracy'] and c['moved'] is not None:
            who = f"X{c['moved'] + 1}"
            out.append(dict(kind='off_ball', action=c['action'], value=c['indirect'],
                            text=f"Your move ({c['action']}) pulled {who} out of position: {c['indirect']:+.1f} to "
                                 f"your teammates' best look."))
        if abs(c['phi']) < TC['minimal_value'] and abs(c1['phi']) < TC['minimal_value'] and c['piece'] >= 0:
            alt = best_alternative(s, c['piece'], acts)
            if alt and alt['gain'] >= TC['minimal_alternative']:
                out.append(dict(kind='minimal', action=c['action'], value=c['phi'], alternative=alt['action'],
                                gain=alt['gain'],
                                text=f"{c['action']} changed the position by {c['phi']:+.1f}. {alt['action']} was "
                                     f"worth {alt['gain']:+.1f} more."))
    return out


def best_alternative(s, piece, acts, budget=0.4):
    """The same player's best legal single action here (with the defence's reply), and how much more it is worth
    than his action in the group."""
    side = actor(s)
    sign = 1 if side == 'O' else -1
    mine = [a for a in acts if a.piece == piece]
    base = group_value(s, mine[:1]) if mine else _ev(s, _leaf)
    best = None
    sr = Searcher(side, dict(profile('allstar'), noise=0.0), _leaf_ev, time.time() + budget)
    for a in legal_actions(s):
        if a.piece != piece or a in mine:
            continue
        v = sr.quick(apply(s, a))
        if best is None or sign * v > sign * best[0]:
            best = (v, a)
    if best is None:
        return None
    v = group_value(s, [best[1]])
    return dict(action=str(best[1]), gain=round(sign * (v - base), 2))


# ---- D3: timing and disguise -------------------------------------------------------------------------------------------

def reveal(s, group1, group2, depth=0, budget=0.4):
    """Reveal = V(the best legal reordering of the actions of two consecutive offence turn groups) - V(the actual
    order), each order played with the defence's re-solved best reply after each group. Reorderings: an action of
    the first group moved into the second, or one of the second moved into the first (the cut with the drive).
    Returns dict(reveal, order, actual) or None."""
    def run(g1, g2):
        """Play the groups, each followed by the defence's re-solved best reply; the value once every action is
        played and the defence has answered (the offence to act), so every order ends at the same point."""
        n = s
        for g in (g1, g2):
            if not g:
                continue
            n = _apply_seq(n, g)
            if n is None:
                return None
            _, _, n = _reply(n, depth, budget)
            if n is None or isinstance(n, ChanceNode) or n.stage == 'over':
                return _ev(n, _leaf) if n is not None else None
            for _ in range(3):                         # the defence still has the turn: let it finish
                if isinstance(n, ChanceNode) or n.stage != 'play' or actor(n) != 'X':
                    break
                n, _ = _play_cover(n, Read(n).cover()['choice'])
        return phase_value(n)
    actual = run(list(group1), list(group2))
    if actual is None:
        return None
    best = (actual, (list(group1), list(group2)))
    orders = []
    if len(group1) == 2:
        orders.append(([group1[0]], [group1[1]] + list(group2)))
        orders.append(([group1[1]], [group1[0]] + list(group2)))
    if group2:
        orders.append((list(group2), list(group1)))      # a plain order swap across the two turns
    if len(group1) == 1 and group2:
        for k in range(len(group2)):
            rest = list(group2[:k]) + list(group2[k + 1:])
            orders.append((list(group1) + [group2[k]], rest))
            orders.append(([group2[k]] + list(group1), rest))
    for g1, g2 in orders:
        if len(g1) > 2 or len(g2) > 2:
            continue
        v = run(g1, g2)
        if v is not None and v > best[0]:
            best = (v, (g1, g2))
    # did the actual order let the defence's reply cover the first threat before the second existed?
    covered = False
    first = _apply_seq(s, list(group1))
    if first is not None and not isinstance(first, ChanceNode) and first.stage != 'over':
        movers = [a.piece for a in group1 if a.side == 'O' and a.piece >= 0]
        pre = Read(_end_turn(first)) if actor(first) == 'O' else Read(first)
        _, _, after = _reply(first, depth, budget)
        if after is not None and not isinstance(after, ChanceNode) and after.stage != 'over':
            post = Read(after)
            covered = any(post.threat.get(i, {}).get('value', 0) < pre.threat.get(i, {}).get('value', 0) - 1e-6
                          or post.cover()['residual'].get(i, 0) < pre.cover()['residual'].get(i, 0) - 1e-6 for i in movers)
    return dict(reveal=round(best[0] - actual, 2), actual=round(actual, 2), covered_first=covered,
                order=[[str(a) for a in best[1][0]], [str(a) for a in best[1][1]]])


# ---- D4: goals in plain words ---------------------------------------------------------------------------------------------

def goal_read(s, chosen, budget=0.8, results=None):
    """The goal the human's turn pursued (the predicate it achieved with the highest Q among the All-Star's scored
    turns) and the best goal at that moment. Returns dict(yours, best, q_yours, q_best) in words."""
    side = actor(s)
    sign = 1 if side == 'O' else -1
    results = results if results is not None else root_turns(s)
    results = sorted(results, key=lambda r: -sign * r[0])
    base = sign * _ev(s, _leaf)
    rb = Read(s)
    Q, words = {}, {}
    for v, t in results[:8]:
        after = _likeliest(play_turn(s, t))
        if after.stage == 'over':
            continue
        for g, w in goals_in(s, after, side, rb, Read(after), t).items():
            if g not in Q or sign * v - base > Q[g]:
                Q[g], words[g] = sign * v - base, w
    mine_after = _likeliest(play_turn(s, chosen))
    mine = goals_in(s, mine_after, side, rb, None if mine_after.stage == 'over' else Read(mine_after), chosen) \
        if mine_after.stage != 'over' else {}
    yours = max(mine, key=lambda g: Q.get(g, -99)) if mine else None
    best = max(Q, key=lambda g: Q[g]) if Q else None
    return dict(yours=mine.get(yours) if yours else None, q_yours=round(Q.get(yours, 0.0), 2) if yours else None,
                best=words.get(best) if best else None, q_best=round(Q[best], 2) if best else None,
                same=yours == best)


# ---- D6: categories ---------------------------------------------------------------------------------------------------------

CATEGORIES = {
    'O': ['shot selection', 'clock use', 'passing risk', 'drives', 'off-ball movement and spacing',
          'timing and disguise', 'screens'],
    'X': ['on-ball containment', 'help and rotation', 'closeouts and contests', 'steal and intercept decisions'],
    'setup': ['offence setup', 'defence setup'],
}


def categories(s, acts):
    """The categories a turn group belongs to."""
    out = set()
    side = actor(s)
    if side == 'O':
        for a in acts:
            if a.kind == 'shot' or a.kind == 'forced_shot':
                out.add('shot selection')
            if a.kind == 'pass':
                out.add('passing risk')
            if a.kind == 'screen':
                out.add('screens')
            if a.kind == 'dribble' or (a.kind in ('move', 'qs', 'sprint') and a.piece == s.ball):
                out.add('drives')
            if a.kind in ('move', 'qs', 'sprint') and a.piece != s.ball:
                out.add('off-ball movement and spacing')
        if s.clock <= 4 or (acts and acts[0].kind in ('hesitate', 'end_turn')):
            out.add('clock use')
    else:
        bd = min(range(5), key=lambda j: B.cheb(s.x[j], s.o[s.ball]))
        for a in acts:
            if a.kind in ('steal', 'intercept', 'challenge'):
                out.add('steal and intercept decisions')
            if a.kind in ('move', 'qs', 'sprint'):
                out.add('on-ball containment' if a.piece == bd else 'help and rotation')
            if a.kind == 'contest' or s.stage in ('reaction', 'contest'):
                out.add('closeouts and contests')
    return sorted(out) or (['clock use'] if side == 'O' else ['help and rotation'])


def skill_table(groups, last=None):
    """groups: graded turn groups across matches [dict(match, categories, loss, best (bool), indirect)]. For each
    category: median value lost, how often the best option was chosen, indirect value created, the trend (the median
    of the later half minus the earlier half; negative = fewer points lost)."""
    rows = {}
    matches = sorted({g['match'] for g in groups})
    if last:
        keep = set(matches[-last:])
        groups = [g for g in groups if g['match'] in keep]
    for g in groups:
        for c in g['categories']:
            rows.setdefault(c, []).append(g)
    out = {}
    for c, gs in rows.items():
        losses = [g['loss'] for g in gs]
        half = len(gs) // 2
        trend = (st.median(losses[half:]) - st.median(losses[:half])) if half >= 1 else 0.0
        out[c] = dict(n=len(gs), median_loss=round(st.median(losses), 2),
                      best_rate=round(sum(1 for g in gs if g['loss'] <= 1e-9) / len(gs), 2),
                      indirect=round(sum(g.get('indirect', 0.0) for g in gs), 2), trend=round(trend, 2))
    return out


# ---- D6: rating and progress --------------------------------------------------------------------------------------------

def match_score(my_total, opp_total, possessions):
    """The per-possession point differential mapped to 0..1 (a logistic on the differential per possession), so every
    possession counts, not only the win."""
    d = (my_total - opp_total) / max(1, possessions)
    return 1.0 / (1.0 + math.exp(-d / TC['match_score_scale'] * 2.0))


def anchor(level, age='senior'):
    return TC['anchors'][f'{level}/{age}']


def update_rating(player, results):
    """player: dict(rating, rd, vol); results: [(opponent rating, opponent rd, score)] -> new dict."""
    r, d, v = rate(player['rating'], player['rd'], player['vol'], results, TC['glicko']['tau'])
    return dict(rating=round(r, 1), rd=round(d, 1), vol=round(v, 6))


NEXT = {'rookie': 'starter', 'starter': 'allstar'}


def suggestions(player, level, age, median_loss, recent_scores, weakest=None):
    """Advancement and practice suggestions, exactly at the configured thresholds.
    Move up: rating within one RD of the next level's anchor, RD below advance_rd, and median value lost at or below
    the current level's. Practice: an expected score below practice_below over the last practice_matches matches."""
    out = []
    nxt = NEXT.get(level)
    level_loss = TC.get('level_median_loss', {}).get(level)
    if nxt:
        a = anchor(nxt, age)
        if player['rating'] >= a - player['rd'] and player['rd'] < TC['advance_rd'] and \
                (level_loss is None or median_loss <= level_loss):
            out.append(dict(kind='move_up', to=nxt,
                            text=f"Your rating {player['rating']:.0f} is within {player['rd']:.0f} of {nxt.title() if nxt != 'allstar' else 'All-Star'}'s "
                                 f"{a}, and you lose a median {median_loss:.1f} a decision. Try {nxt.title() if nxt != 'allstar' else 'All-Star'}."))
    n = TC['practice_matches']
    if len(recent_scores) >= n and sum(recent_scores[-n:]) / n < TC['practice_below']:
        out.append(dict(kind='practice', category=weakest, **practice(weakest)))
    return out


PRACTICE = {
    'shot selection': ('scenario', 'Scenario cards 3 and 9: one possession each, a shot to choose against the clock.'),
    'clock use': ('scenario', 'Scenario 16 (Hold for One) and the late-clock cards.'),
    'passing risk': ('random', 'A random deal against a defence with high Intercept ratings (Iron Wall shape).'),
    'drives': ('random', 'Pure random teams: different driving lanes every possession.'),
    'off-ball movement and spacing': ('junior', 'Junior age: types are closer together, so space and timing decide more.'),
    'timing and disguise': ('junior', 'Junior age, Learn mode: "Your goal this turn" shows during play.'),
    'screens': ('random', 'A coherent random deal with a strong screener.'),
    'on-ball containment': ('random', 'Pure random teams: a different ball handler every possession.'),
    'help and rotation': ('scenario', 'Scenario cards with a drive already started.'),
    'closeouts and contests': ('random', 'A random deal against a team of shooters.'),
    'steal and intercept decisions': ('junior', 'Junior age: weaker ball security, so steals and intercepts are live.'),
    'offence setup': ('random', 'Pure random teams: a new setup problem each possession.'),
    'defence setup': ('random', 'Pure random teams: new matchups each possession.'),
}


def practice(category):
    kind, how = PRACTICE.get(category, ('random', 'Pure random teams.'))
    return dict(tool=kind, how=how,
                why=f"Your last {TC['practice_matches']} matches averaged an expected score below "
                    f"{TC['practice_below']}. {category or 'One area'} is where the most points went: practise it in "
                    f"varied situations, then mix again once its accuracy clears {TC['practice_clear_accuracy']}%.")


def fade_every(rating):
    """Show the possession summary every N possessions, N rising with the rating."""
    for lo, hi, n in TC['fade']:
        if lo <= rating < hi:
            return n
    return 1


# ---- D5: the possession summary -------------------------------------------------------------------------------------------

def summary(graded):
    """1 to 3 points for one possession: the best decision first, then at most two needs (each with the better
    option, its value and a replay reference). graded: [dict(group index, actions, grade, credits, flags, goal,
    reveal)]."""
    if not graded:
        return []
    pts = []
    best = max(graded, key=lambda g: (sum(f['value'] for f in g.get('flags', []) if f['kind'] == 'off_ball'),
                                      -g['grade']['loss']))
    good = [f for f in best.get('flags', []) if f['kind'] == 'off_ball']
    pts.append(dict(kind='best', group=best['group'], text=good[0]['text'] if good else
                    f"Your best decision: {'; '.join(best['actions'])} (value {best['grade']['value']:+.1f}"
                    + (', the best option there).' if best['grade']['loss'] <= 1e-9 else f", {best['grade']['loss']:.1f} from the best).")))
    needs = sorted([g for g in graded if g is not best and g['grade']['band'] in ('mistake', 'blunder', 'inaccuracy')],
                   key=lambda g: -g['grade']['loss'])
    for g in needs[:2]:
        gr = g['grade']
        if gr['side'] == 'O':
            bits = [f"{'; '.join(g['actions'])}: after the defence's best answer, your best look was {gr['value']:+.1f}."]
        else:
            bits = [f"{'; '.join(g['actions'])}: it left the offence a best look of {gr['value']:+.1f}."]
        if gr.get('better'):
            bits.append(f"Better: {'; '.join(gr['better'])} ({gr['best']:+.1f}, {gr['loss']:.1f} "
                        f"{'more' if gr['side'] == 'O' else 'less for the offence'}).")
        rv = g.get('reveal')
        if rv and rv['reveal'] >= TC['reveal']:
            bits.append(f"Order it as {' / '.join('; '.join(x) for x in rv['order'])}: {rv['reveal']:+.1f}.")
        mins = [f for f in g.get('flags', []) if f['kind'] == 'minimal']
        if mins:
            bits.append(mins[0]['text'])
        pts.append(dict(kind='need', group=g['group'], text=' '.join(bits), replay=gr.get('better')))
    if len(pts) == 1 and len(graded) > 1:
        flagged = [g for g in graded if g is not best and g.get('flags')]
        if flagged:
            pts.append(dict(kind='note', group=flagged[0]['group'], text=flagged[0]['flags'][0]['text']))
    return pts[:TC['summary_points']]


# ---- one possession, end to end ------------------------------------------------------------------------------------------

def turn_groups(events, side):
    """Group a possession's decisions into one side's turn groups: [(index, state before, [actions])]."""
    out = []
    k = 0
    while k < len(events):
        s, a, n = events[k]
        if a.side != side or a.kind in ('end_turn', 'forfeit'):
            k += 1
            continue
        acts, m = [a], k
        while m + 1 < len(events) and events[m + 1][1].side == side and events[m + 1][0].turn_n > 0 \
                and events[m + 1][0].stage == s.stage and events[m + 1][1].kind not in ('end_turn', 'forfeit'):
            m += 1
            acts.append(events[m][1])
        out.append((k, s, acts))
        k = m + 1
    return out


def read_possession(events, side, budget=0.6, deep=False):
    """Grade every turn group of one side in a possession, with credits, flags, goals and the timing check.
    Returns dict(groups, summary, accuracy)."""
    groups = turn_groups(events, side)
    graded = []
    for n, (k, s, acts) in enumerate(groups):
        res = root_turns(s)
        g = grade_group(s, acts, results=res)
        entry = dict(group=n, index=k, before=s.encode(), actions=[str(a) for a in acts], grade=g,
                     categories=categories(s, acts), phase=s.phase, clock=s.clock)
        if side == 'O' and s.stage == 'play':
            c0 = credit(s, acts, depth=0)
            entry['credits'] = c0
            fl = flags(s, acts, c0, c0)
            if fl:                                   # stability: confirm at the next depth (a searched reply)
                c1 = credit(s, acts, depth=1, budget=budget)
                fl = flags(s, acts, c0, c1)
            entry['flags'] = fl
            if n + 1 < len(groups) and (fl or g['band'] in ('mistake', 'blunder')):
                rv = reveal(s, acts, groups[n + 1][2])
                if rv and rv['reveal'] >= TC['reveal'] and rv['covered_first']:
                    entry['reveal'] = rv
        entry['goal'] = goal_read(s, acts, results=res)
        graded.append(entry)
    return dict(groups=graded, summary=summary(graded), accuracy=accuracy([g['grade']['loss'] for g in graded]))
