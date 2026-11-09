"""Step 9: evidence for every failing exam board (measures only: no board, judge or engine value changes).

For each board, under today's rules and the All-Star's settings:
  1. every legal turn for the side to act (one action, or two), judged by the board's own judge function;
  2. the computer's value of its own choice and of the best accepted turn at three look-aheads: the depth it reaches
     on the clock (re-measured: the Python search with the All-Star's 2.5 s, as in the step 6 run), 4, then 5 and 6
     while the board's 10 minutes last. The searches run on engine.js (tools/exam_evidence.js), the app's own search,
     proved equal to the Python search by tools/js_equivalence.py;
  3. the facts a basketball person needs.

  python3 tools/exam_evidence.py out.json [board ...]     (boards: 2 3 4 5 6 7 8 11 13 14 16 T1 T2 C1 C2)
"""
import importlib.util
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from playmaker_engine import board as B                                   # noqa: E402
from playmaker_engine import exam as E                                    # noqa: E402
from playmaker_engine import jsbridge as J                                # noqa: E402
from playmaker_engine import rules_config as RC                           # noqa: E402
from playmaker_engine import agent as AG                                  # noqa: E402
from playmaker_engine.agent import Agent, profile                         # noqa: E402
from playmaker_engine.actions import legal_actions, Action                # noqa: E402
from playmaker_engine.decide import Read, vcoarse, _lane_p, lane_squares, _caps, _one_action  # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode                    # noqa: E402
from playmaker_engine.search import actor, play_turn                      # noqa: E402

CAP_S = float(os.environ.get('EXAM_EVIDENCE_CAP_S', 600))
KEEP = 8
SQ = B.parse_sq


def aj(a):
    return [a.kind, a.side, a.piece, B.sq(a.dest) if a.dest else None, a.arrow, a.target, a.shot]


def words(t):
    return '; '.join(str(a) for a in t)


def likeliest(n):
    while isinstance(n, ChanceNode):
        n = max(n.outcomes, key=lambda o: o[0])[2]
    return n


# ---- every legal turn, and the board's judge on each ------------------------------------------------------------------

def all_turns(s):
    """Every legal turn: one action, or two by the same side in the same stage (the search's own turn shape). Returns
    {turn: state after (the likeliest outcome of a roll, as exam.after takes it)}."""
    side = actor(s)
    out = {}
    for a in legal_actions(s):
        n1 = apply(s, a)
        out[(a,)] = n1
        if a.kind in ('end_turn', 'forfeit'):
            continue
        if isinstance(n1, ChanceNode) or n1.stage == 'over' or actor(n1) != side or n1.stage != s.stage:
            continue
        for b in legal_actions(n1):
            if b.kind in ('end_turn', 'forfeit'):
                continue
            out[(a, b)] = apply(n1, b)
    return out


class judged:
    """exam.after answered from the enumeration (the same state play_turn reaches; the judge itself is untouched)."""

    def __init__(self, s, table):
        self.s, self.table, self.orig = s, table, E.after

    def __enter__(self):
        def fast(s0, t):
            if s0 is self.s:
                n = self.table.get(tuple(t))
                if n is not None:
                    return likeliest(n)
            return self.orig(s0, t)
        E.after = fast
        return self

    def __exit__(self, *a):
        E.after = self.orig


# ---- the clock choice (Python, the All-Star's own time budget) ---------------------------------------------------------

def clock_choice(s, side=None):
    AG.SCALE['value'] = 1.0
    ag = Agent(side or actor(s), 'allstar', seed=1)
    a = ag.choose(s)
    t = [a] + list(ag.plan)
    return t, ag.last or {}


# ---- the JavaScript searches ----------------------------------------------------------------------------------------------

class Node:
    def __init__(self):
        self.p = subprocess.Popen(['node', os.path.join(ROOT, 'tools', 'exam_evidence.js')], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True, bufsize=1)

    def call(self, req):
        self.p.stdin.write(json.dumps(req) + '\n')
        self.p.stdin.flush()
        out = json.loads(self.p.stdout.readline())
        if 'error' in out:
            raise RuntimeError(out['error'])
        return out['ok']

    def close(self):
        self.p.stdin.close()
        self.p.wait(10)


def search(node, s, accepted, extra, depths, cap_s, mode='floor'):
    req = dict(state=J.state_json(s), ctx=J.ctx_json(s.ctx), profile=profile('allstar'), depths=depths, cap_s=cap_s,
               leaf_mode=mode,
               first_cap_s=cap_s / 3, accepted=[[aj(a) for a in t] for t in accepted],
               keep=KEEP, extra=[[aj(a) for a in t] for t in extra])
    return node.call(req)


def turn_of_json(s, tj):
    """The turn (Action objects) from its JSON form."""
    out, n = [], s
    for j in tj:
        a = next(x for x in legal_actions(n) if aj(x) == j)
        out.append(a)
        n = apply(n, a)
        if isinstance(n, ChanceNode):
            break
    return tuple(out)


def measure(node, s, accept, cap_s, extra=(), label=''):
    """The values for one board: returns the evidence dict."""
    t0 = time.time()
    side = actor(s)
    sign = 1 if side == 'O' else -1
    table = all_turns(s)
    with judged(s, table):
        acc = [t for t in table if accept(list(t))]
    t_enum = time.time() - t0
    chosen, note = clock_choice(s)
    dclock = note.get('depth') or 1
    depths = sorted({max(1, dclock), 4, 5, 6})
    extra = [tuple(chosen)] + [tuple(x) for x in extra]
    left = max(30.0, cap_s - (time.time() - t0))
    r = search(node, s, acc, extra, depths, left)
    acc_set = set(acc)
    rows = []
    for d in r['depths']:
        top = [(v, turn_of_json(s, tj)) for v, tj in d['top']]
        choice_v, choice_t = top[0]
        kept = [(v, acc[i]) for v, i in d['kept']]
        kept += [(v, t) for v, t in top if t in acc_set]
        best_acc = max(kept, key=lambda r_: sign * r_[0]) if kept else None
        xv = {words(extra[i]): v for v, i in d['extra']}
        rows.append(dict(depth=d['depth'], seconds=round(d['seconds'], 1),
                         choice=words(choice_t), choice_value=round(choice_v, 2), choice_accepted=choice_t in acc_set,
                         best_accepted=words(best_acc[1]) if best_acc else None,
                         best_accepted_value=round(best_acc[0], 2) if best_acc else None,
                         gap=round(sign * (choice_v - best_acc[0]), 2) if best_acc else None,
                         top=[dict(turn=words(t), value=round(v, 2), accepted=t in acc_set) for v, t in top[:6]],
                         extra={k: round(v, 2) for k, v in xv.items()}))
    clock_row = next((x for x in rows if x['depth'] == dclock), None)
    return dict(label=label, side=side, n_turns=len(table), n_accepted=len(acc), n_valued_first=r.get('n_first'),
                accepted_examples=[words(t) for t in acc[:5]],
                clock=dict(depth=dclock, partial=note.get('partial'), seconds=note.get('seconds'), choice=words(chosen),
                           accepted=tuple(chosen) in acc_set),
                rows=rows, capped=r['capped'], reached_in_cap=r['reached_in_cap'],
                seconds=round(time.time() - t0, 1), enum_seconds=round(t_enum, 1),
                result=classify(rows, acc, clock_row, tuple(chosen) in acc_set))


def classify(rows, acc, clock_row, chosen_ok):
    """met: the choice on the clock meets the board. Otherwise by the deepest look measured: speed if an accepted
    move is level or ahead there; valuation or board if the computer's own choice is still ahead."""
    if not acc:
        return 'no accepted move'
    if chosen_ok:
        return 'met'
    deep = [r for r in rows if r['gap'] is not None]
    if not deep:
        return 'not measured'
    return 'speed' if deep[-1]['gap'] <= 0 else 'valuation or board'


# ---- small readers for the facts ------------------------------------------------------------------------------------------

def look_values(s, i):
    """Attacker i's looks: [(route, square, chance it arrives, value)]."""
    r = Read(s, exact=True)
    return [(lk.route, B.sq(lk.c), round(lk.p, 2), round(lk.base, 2)) for lk in r.looks.get(i, [])]


def threat(s, i):
    return round(Read(s, exact=True).threat[i]['value'], 2)


def leaf(s):
    return round(Read(s, exact=True).leaf(), 2)


def can_contest(s, d, i):
    """Actions defender d needs to Contest attacker i where he stands (None: he can't in the reaction)."""
    cm = Read(s, exact=True)._cm[d].get(s.o[i])
    if not cm:
        return None
    return min(cm.values()) if isinstance(cm, dict) else min(cm)


def end_turn(s):
    n = s
    for _ in range(3):
        if isinstance(n, ChanceNode) or n.stage != 'play':
            return n
        e = next((x for x in legal_actions(n) if x.kind in ('end_turn', 'pause')), None)
        if e is None or actor(n) != n.side:
            return n
        if actor(n) == s.side:
            n = apply(n, e)
        else:
            return n
    return n


# ---- the boards -----------------------------------------------------------------------------------------------------------

# the halves of the two-copy judges, word for word from exam.py (p5, p7, p11): each copy is judged on its own
HALVES = {
    5: {'close': lambda t: any(x.piece == 1 and x.kind in ('move', 'qs', 'sprint', 'dribble') for x in t) and t[0].kind != 'shot',
        'short': lambda t: t[0].kind == 'shot'},
    7: {'phase 2': lambda t: t[0].kind != 'shot', 'phase 6': lambda t: t[0].kind == 'shot'},
    11: {'early': lambda t: not any(a.kind == 'pass' and a.target == 1 for a in t),
         'final phase': lambda t: any(a.kind == 'pass' for a in t)},
}


def sag_half(boards, k, other, other_turn):
    """Board 2's judge (exam.p2), split by copy: d4 < d12 and X2 can still contest on the rating-12 copy. The other
    copy's part is computed once, from the computer's own choice there; this copy's part, per turn, word for word."""
    n_other = E.after(boards[other], other_turn)
    d_other = B.dist_rim(n_other.x[1])
    if k == 4:                                   # the poor shooter: X2 must end closer to the rim than on the other copy
        cm = Read(n_other)._cm[1].get(n_other.o[1])
        reach12 = cm is not None and min(cm) <= 2

        def accept(t):
            return reach12 and B.dist_rim(E.after(boards[k], t).x[1]) < d_other
        return accept

    seen = {}

    def accept(t):                               # the good shooter: further from the rim than on the other copy, and in reach
        n = E.after(boards[k], t)
        if not d_other < B.dist_rim(n.x[1]):
            return False
        # Read(n)._cm[1] (decide.Read._contest, not exact) depends only on X2's square, facing, Move and Quick Step left
        # and whether the defence has tokens: read once per case, the same answer
        key = (n.x[1], n.arrows[1], _caps(n, 'X', 1), n.tok_x <= 0, n.o[1])
        if key not in seen:
            cm = Read(n)._cm[1].get(n.o[1])
            seen[key] = cm is not None and min(cm) <= 2
        return seen[key]
    return accept


def board_pair(n, node, cap):
    """Boards with two copies. Boards 5, 7 and 11 judge each copy on its own (the judge's two halves, copied). Board 2
    compares the copies, so each copy is judged by the board's own judge together with the computer's choice on the
    other copy."""
    _, boards, check = E.POSITIONS[n - 1]()
    keys = list(boards)
    choices = {k: clock_choice(boards[k])[0] for k in keys}
    out = {}
    for k in keys:
        other = [x for x in keys if x != k][0]
        if n in HALVES:
            accept = HALVES[n][k]
        elif n == 2:
            accept = sag_half(boards, k, other, choices[other])
        else:
            def accept(t, k=k, other=other):
                return check({k: t, other: choices[other]})[0]
        out[str(k)] = measure(node, boards[k], accept, cap / 2, label=str(k))
    return out, boards


def single(n, node, cap, extra=()):
    _, s, check = E.POSITIONS[n - 1]()
    accept = lambda t: check(t)[0]
    if n == 4:
        # the first half can't be met by any move (it reads the board, not the move): the values table measures the
        # second half (the offence attacks), and the facts say so
        accept = overload_half(s, attack_only=True)
        legal = legal_actions(s)
        shot = [(a,) for a in legal if a.kind == 'shot' and a.piece == 0]
        to5 = [(a,) for a in legal if a.kind == 'pass' and a.target == 4]
        d9 = next(a for a in legal if str(a) == 'O2 Move to D9')
        p2 = next(b_ for b_ in legal_actions(apply(s, d9)) if b_.kind == 'pass' and b_.target == 1)
        extra = shot + to5 + [(d9, p2)]
    return measure(node, s, accept, cap, extra=extra), s


def overload_half(s, attack_only=False):
    """Board 4's judge (exam.p4), split: its first part (the computer's reading sees X5 overloaded) doesn't depend on
    the move, so it is computed once; its second part (the offence attacks), per turn, word for word."""
    ov = [o for o in Read(s).overloads() if o['defender'] == 4]

    def accept(t):
        attack = any((a.kind == 'shot') or (a.kind == 'pass' and a.target == 4) or
                     (a.kind in ('move', 'qs', 'sprint', 'dribble') and a.piece == 0) for a in t)
        return (attack_only or bool(ov)) and attack
    accept.overloaded = bool(ov)
    return accept


def facts_2(ev, boards):
    f = {}
    for k, s in boards.items():
        o2, x2 = s.o[1], s.x[1]
        f[f'three_{k}'] = s.ctx.off[1].r['shot_three']
        f[f'clock_end_{k}'] = ev[str(k)]['clock']['choice']
        # how far off O2 can X2 sag and still Contest (D-18: the reaction's actions, the Contest last)
        best = None
        for x in range(17):
            for y in range(1, 15):
                q = (x, y)
                if q in s.o or q in s.x[:1] + s.x[2:] or q == RC.RIM:
                    continue
                t = s.with_(x=s.x[:1] + (q,) + s.x[2:])
                need = can_contest(t, 1, 1)
                if need is not None and need <= 2:
                    dr = B.dist_rim(q)
                    if best is None or dr < best[0]:
                        best = (dr, B.sq(q), B.cheb(q, o2), need)
        f[f'deepest_contest_{k}'] = dict(rim_distance=best[0], square=best[1], squares_from_O2=best[2], actions=best[3]) if best else None
        f[f'x2_contest_three'] = s.ctx.dfn[1].r['con_three']
        f[f'start_{k}'] = dict(square=B.sq(x2), rim_distance=B.dist_rim(x2))
    return f


def facts_3(s):
    f = dict(o1_threat_now=threat(s, 0), position_now=leaf(s), o1_looks=look_values(s, 0)[:4])
    steps = {}
    for j in range(5):
        best = None
        for a in legal_actions(s):
            if a.side != 'X' or a.piece != j or a.kind not in ('move', 'qs', 'sprint'):
                continue
            n = apply(s, a)
            if isinstance(n, ChanceNode) or not B.adjacent(n.x[j], n.o[0]):
                continue
            v = threat(end_turn(n), 0)
            if best is None or v < best[0]:
                best = (v, str(a))
        steps[f'X{j + 1}'] = dict(o1_after=best[0], step=best[1]) if best else None
    f['step_up'] = steps
    return f


def facts_4(s):
    r = Read(s, exact=True)
    return dict(pull_up_now=round(r.shot_now() or 0.0, 2), o1_looks=look_values(s, 0)[:4], o5_looks=look_values(s, 4)[:4],
                overloads=[dict(defender=f"X{o['defender'] + 1}", a=f"O{o['a'] + 1}", b=f"O{o['b'] + 1}") for o in r.overloads()],
                hinges=[dict(defender=f"X{o['defender'] + 1}", a=f"O{o['a'] + 1}", b=f"O{o['b'] + 1}") for o in r.hinges()],
                position_now=leaf(s))


def facts_5(boards):
    a, b = boards['close'], boards['short']
    rb = Read(b, exact=True)
    return dict(three=b.ctx.off[1].r['shot_three'], x2_contest_three=b.ctx.dfn[1].r['con_three'],
                x2_contest_actions_A=can_contest(a, 1, 1), x2_contest_actions_B=can_contest(b, 1, 1),
                shot_now_A=round(Read(a, exact=True).shot_now() or 0.0, 2), shot_now_B=round(rb.shot_now() or 0.0, 2),
                o2_looks_A=look_values(a, 1)[:4], o2_looks_B=look_values(b, 1)[:4])


def facts_6(s):
    r = Read(s, exact=True)
    return dict(corner_three=s.ctx.off[3].r['shot_three'], shot_now=round(r.shot_now() or 0.0, 2),
                phase_table=round(vcoarse(s), 2), position_now=leaf(s), o4_looks=look_values(s, 3)[:4],
                contest_actions={f'X{d + 1}': can_contest(s, d, 3) for d in range(5)})


def facts_clock(boards, key):
    s = boards[key]
    r = Read(s, exact=True)
    return dict(clock=s.clock, phase=s.phase, tokens_o=s.tok_o, tokens_x=s.tok_x,
                offence_turns_left=f'up to {s.tok_o // 2} turns of two actions ({s.tok_o} actions)',
                shot_now=round(r.shot_now() or 0.0, 2), phase_table=round(vcoarse(s), 2), position_now=leaf(s))


def facts_8(s, ev):
    f = dict(o2_looks=look_values(s, 1)[:4], position_now=leaf(s))
    cuts = {}
    for a in legal_actions(s):
        if a.side == 'O' and a.piece == 1 and a.kind in ('move', 'qs', 'sprint') and B.dist_rim(a.dest) <= B.dist_rim(s.o[1]) - 2:
            n = apply(s, a)
            if isinstance(n, ChanceNode):
                continue
            p = _lane_p(n, 1, n.o[1])
            lane = lane_squares(n.o[n.ball], n.o[1], 0.5)
            step_in = []
            for d in range(5):
                cm, ql = _caps(n, 'X', d)
                if not lane.isdisjoint(_one_action(n.x[d], n.arrows[d], n.ctx.dfn[d].qs, cm, ql, n.ctx.rules)):
                    step_in.append(f'X{d + 1}')
            cuts[str(a)] = dict(arrives=round(p, 2), can_step_in=step_in, square=B.sq(a.dest))
    f['cuts'] = cuts
    return f


def facts_13(s):
    f = dict(o1_looks_with_o5=look_values(s, 0)[:4], o1_threat_with_o5=threat(s, 0))
    best = None
    lane = lane_squares(s.o[0], RC.RIM, 0.5)
    for a in legal_actions(s):
        if a.side == 'O' and a.piece == 4 and a.kind in ('move', 'qs', 'sprint') and a.dest not in lane:
            n = apply(s, a)
            if isinstance(n, ChanceNode):
                continue
            v = threat(n, 0)
            if best is None or v > best[0]:
                best = (v, str(a), look_values(n, 0)[:3])
    f['o1_threat_o5_cleared'] = dict(value=best[0], by=best[1], looks=best[2]) if best else None
    return f


def run_14(node, cap):
    _, s, _ = E.POSITIONS[13]()
    chosen, note = clock_choice(s)
    depths = sorted({max(1, note.get('depth') or 1), 4, 5, 6})
    r = search(node, s, [], [tuple(chosen)], depths, cap)
    rows = []
    for d in r['depths']:
        top = [dict(turn=words(turn_of_json(s, tj)), value=round(v, 2)) for v, tj in d['top']]
        firsts = {}
        for t in top:
            k = t['turn'].split('; ')[0]
            firsts.setdefault(k, t['value'])
        fl = sorted(firsts.items(), key=lambda kv: -kv[1])
        rows.append(dict(depth=d['depth'], seconds=round(d['seconds'], 1), top=top, first_moves=fl,
                         gap=round(fl[0][1] - fl[1][1], 2) if len(fl) > 1 else None))
    return dict(clock=dict(depth=note.get('depth'), choice=words(chosen)), rows=rows, capped=r['capped'],
                reached_in_cap=r['reached_in_cap'], variety_margin=profile('allstar')['variety_margin'],
                noise=profile('allstar')['noise'])


def run_16(node, cap):
    """Board 16: the judge reads a line. Its own method (exam.drain_line), instrumented turn by turn, then the values of
    the first turns that hold an off-ball move, by the trainer's phase reading (the judge's per-move part)."""
    from playmaker_engine.trainer import _play_cover, phase_value, _end_turn, credit
    t0 = time.time()
    _, s, check = E.POSITIONS[15]()
    ag = Agent('O', 'allstar', seed=1)
    steps = [dict(turn=None, value=round(phase_value(s, max_turns=2), 2),
                  x2_move_left=not (s.moved_x >> 1 & 1), x2_qs_left=not (s.qs_x >> 1 & 1))]
    n = s
    for _ in range(3):
        if n.stage != 'play' or actor(n) != 'O' or n.phase != s.phase:
            break
        a = ag.choose(n)
        t = [a] + list(ag.plan)
        ag.plan = []
        stop = any(x.kind in ('shot', 'pass') for x in t)
        n = E.after(n, t)
        if not stop:
            if not isinstance(n, ChanceNode) and n.stage == 'play' and actor(n) == 'O':
                n = _end_turn(n)
            if not isinstance(n, ChanceNode) and n.stage == 'play' and actor(n) == 'X':
                n, _ = _play_cover(n, Read(n).cover()['choice'])
        live = not isinstance(n, ChanceNode) and n.stage != 'over'
        steps.append(dict(turn=words(t), value=round(phase_value(n, max_turns=1), 2) if live else None,
                          x2_move_left=(not (n.moved_x >> 1 & 1)) if live else None,
                          x2_qs_left=(not (n.qs_x >> 1 & 1)) if live else None,
                          o2_threat=threat(n, 1) if live and n.stage == 'play' else None))
        if stop or not live:
            break
    # O2's shot once X2 is spent: X2's Move and Quick Step used, the rest of the board as it starts
    spent = s.with_(moved_x=s.moved_x | 2, qs_x=s.qs_x | 2)
    o2_spent = dict(o2_threat_x2_spent=threat(spent, 1), o2_threat_start=threat(s, 1), o2_looks_spent=look_values(spent, 1)[:3])
    # the first turns holding an off-ball move: one action each, by the trainer's phase reading
    offball = []
    for a in legal_actions(s):
        if a.side == 'O' and a.piece != s.ball and a.kind in ('move', 'qs', 'sprint'):
            if time.time() - t0 > cap / 2:
                break
            c = credit(s, [a], horizon='phase')
            if c:
                offball.append(dict(move=str(a), phase=c[0]['phi'], drain=c[0]['drain'], drained=c[0]['drained']))
    offball.sort(key=lambda r: -r['drain'])
    accepted = [r_ for r_ in offball if r_['drain'] > 0]
    extra = [(next(x for x in legal_actions(s) if str(x) == r_['move']),) for r_ in accepted[:KEEP]]
    left = max(30.0, cap - (time.time() - t0))
    ev = measure(node, s, lambda t: any(str(x) in {r_['move'] for r_ in accepted} for x in t[:1]), left,
                 extra=[], label='first turn')
    return dict(line=steps, o2=o2_spent, offball_first_moves=offball[:12], n_offball=len(offball),
                n_offball_drain=len(accepted), evidence=ev, seconds=round(time.time() - t0, 1))


def run_t1():
    from playmaker_engine import trainer as TR
    s = E.board(['H9', 'C8', 'O8', 'B3', 'P3'], ['H8', 'D8', 'N8', 'C3', 'O3'], ['N', 'W', 'E', 'W', 'E'])
    cut = Action('move', 'O', 4, dest=SQ('N5'))
    drive = Action('move', 'O', 0, dest=SQ('J7'))
    out = {}
    from playmaker_engine import decide as DC
    for name in ('today', 'step 3m table (as the test runs)'):
        saved = dict(DC._TABLES)
        if name != 'today':
            tab = json.load(open(os.path.join(ROOT, 'tests', 'data', 'vcoarse_3m.json')))['senior/pro']
            DC._TABLES.clear()
            DC._TABLES[('senior', 'pro')] = tab
        try:
            rv = TR.reveal(s, [cut], [drive])
            orders = {'cut, then drive (as played)': ([cut], [drive]), 'drive, then cut': ([drive], [cut]),
                      'cut and drive together': ([cut, drive], []), 'drive and cut together': ([drive, cut], [])}
            vals = {k: (lambda v: None if v is None else round(v, 2))(_reveal_run(TR, s, g1, g2))
                    for k, (g1, g2) in orders.items()}
            out[name] = dict(reveal=rv, orders=vals)
        finally:
            DC._TABLES.clear()
            DC._TABLES.update(saved)
    return dict(tables=out, bar=TR.TC['reveal'])


def _reveal_run(TR, s, g1, g2, depth=0, budget=0.4):
    """trainer.reveal's own run(), copied: each group then the defence's re-solved best reply; the phase value."""
    n = s
    for g in (g1, g2):
        if not g:
            continue
        n = TR._apply_seq(n, g)
        if n is None:
            return None
        _, _, n = TR._reply(n, depth, budget)
        if n is None or isinstance(n, ChanceNode) or n.stage == 'over':
            return TR._ev(n, TR._leaf) if n is not None else None
        for _ in range(3):
            if isinstance(n, ChanceNode) or n.stage != 'play' or actor(n) != 'X':
                break
            n, _ = TR._play_cover(n, Read(n).cover()['choice'])
    return TR.phase_value(n)


def run_t2():
    from playmaker_engine import trainer as TR
    s = E.board(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'D4', 'N4'], ['N', 'W', 'E', 'E', 'W'])
    a = Action('move', 'O', 1, dest=SQ('D9'))
    c = TR.credit(s, [a])[0]
    v_with, with_ = TR._cf(s, [a], 0, 0.4, 'phase')
    v_without, without = TR._cf(s, [], 0, 0.4, 'phase')
    changes = {}
    for j in range(5):
        changes[f'X{j + 1}'] = dict(with_lift=B.sq(with_.x[j]), without_lift=B.sq(without.x[j]),
                                    facing_with=B.DIR_NAMES[with_.arrows[j]], facing_without=B.DIR_NAMES[without.arrows[j]],
                                    differs=(with_.x[j], with_.arrows[j]) != (without.x[j], without.arrows[j]))
    # trainer._answering_defender's own rule, copied: put each changed defender back where the without-lift reply had
    # him; the one who takes back most of the teammates' gain is named (ties: the matchup rule)
    me = {1}
    others = lambda res: max((res[i] for i in res if i not in me), default=0.0)
    r0, ra = Read(s), Read(with_)
    gain_with = others(ra.cover()['residual'])
    contrib = {}
    for j in range(5):
        if not changes[f'X{j + 1}']['differs']:
            continue
        q = without.x[j]
        if q in set(with_.o) | {p for k, p in enumerate(with_.x) if k != j}:
            contrib[j] = 0.0
            changes[f'X{j + 1}']['takes_back'] = 0.0
            changes[f'X{j + 1}']['square_taken'] = True
            continue
        back = with_.with_(x=with_.x[:j] + (q,) + with_.x[j + 1:],
                           arrows=with_.arrows[:j] + (without.arrows[j],) + with_.arrows[j + 1:])
        contrib[j] = gain_with - others(Read(back).cover()['residual'])
        changes[f'X{j + 1}']['takes_back'] = round(contrib[j], 2)
    tie = None
    if contrib:
        top = max(contrib.values())
        tied = [j for j in contrib if contrib[j] >= top - 1e-6]
        if len(tied) > 1:
            from playmaker_engine.goals import _matchups
            res0, res1 = r0.cover()['residual'], ra.cover()['residual']
            released = max((i for i in res1 if i not in me and i in res0), key=lambda i: (res1[i] - res0[i], -i), default=None)
            lost = _matchups(r0).get(released) if released is not None else None
            tie = dict(tied=[f'X{j + 1}' for j in tied], released=None if released is None else f'O{released + 1}',
                       his_defender_before=None if lost is None else f'X{lost + 1}')
        changes['_tie'] = tie
        changes['_gain_with'] = round(gain_with, 2)
    return dict(named=None if c['moved'] is None else f"X{c['moved'] + 1}", indirect=c['indirect'],
                bar=TR.TC['inaccuracy'], phi=c['phi'], v_with=round(v_with, 2), v_without=round(v_without, 2),
                changes=changes)


def _archived(name):
    spec = importlib.util.spec_from_file_location(f'playmaker_engine.{name}_archived',
                                                  os.path.join(ROOT, 'archive', 'engine', f'{name}.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def c1_state():
    from playmaker_engine.scenarios import game_state
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                   ['N', 'NE', 'NW', 'N', 'N'])
    a = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == SQ('I12'))
    t = apply(s, a)
    return apply(t, next(x for x in legal_actions(t) if x.kind == 'end_turn'))


def run_c1(node, cap):
    """D-108: the archived test's judge: after the defence's turn the carrier's lane to O2 is answered (denied or
    interceptable) and at least two lanes to O2 are. Its lane check (capacity.lane_answered) is read from the archive
    unchanged."""
    cap_m = _archived('capacity')
    s = c1_state()
    O2 = 1

    def lanes_to(n, att):
        out = {}
        for p in range(5):
            if p == att or not B.on_board(n.o[p]):
                continue
            h = n.with_(ball=p, side='O', stage='play', turn_n=0, pending=None, approach=-1, tok_o=max(1, n.tok_o))
            out[p] = cap_m.lane_answered(h, p, att)
        return out

    def accept(t):
        n = E.after(s, t)
        if isinstance(n, ChanceNode) or n.stage == 'over':
            return False
        n2 = end_turn(n) if n.stage == 'play' and actor(n) == 'X' else n
        ln = lanes_to(n2, O2)
        return bool(ln.get(n2.ball)) and sum(ln.values()) >= 2
    ev = measure(node, s, accept, cap)
    chosen = ev['clock']['choice']
    return dict(evidence=ev, o2_three=s.ctx.off[1].r['shot_three'], x2_contest_three=s.ctx.dfn[1].r['con_three'],
                o2_looks=look_values(s, 1)[:3], position_now=leaf(s), chosen=chosen)


def c2_state():
    from playmaker_engine.scenarios import scenario_state
    d = json.load(open(os.path.join(ROOT, 'tests', 'data', 'pass_positions.json')))['prefer_clean']
    fl = dict(d['fields'])
    fl.update(o=tuple(map(tuple, fl['o'])), x=tuple(map(tuple, fl['x'])), arrows=tuple(fl['arrows']),
              cnt=tuple(fl['cnt']), screens=tuple(fl['screens']), beaten=tuple(fl['beaten']))
    return scenario_state(d['spec'][1]).with_(**fl), d


def run_c2(node, cap):
    """D-109: the archived test's judge, its choice half: the All-Star doesn't throw the contested pass (to O4). The
    value half (the clean pass rated above the contested one) is reported from the same searches."""
    s, d = c2_state()
    clean = next(a for a in legal_actions(s) if a.kind == 'pass' and a.target == d['clean'])
    cont = next(a for a in legal_actions(s) if a.kind == 'pass' and a.target == d['contested'])
    ev = measure(node, s, lambda t: not (t[0].kind == 'pass' and t[0].target == d['contested']), cap,
                 extra=[(clean,), (cont,)])
    return dict(evidence=ev, arrives_clean=round(_lane_p(s, d['clean'], s.o[d['clean']]), 2),
                arrives_contested=round(_lane_p(s, d['contested'], s.o[d['contested']]), 2),
                o2_looks=look_values(s.with_(ball=d['clean']), d['clean'])[:3],
                o4_looks=look_values(s.with_(ball=d['contested']), d['contested'])[:3])


def run(board, node):
    t0 = time.time()
    if board in ('2', '5', '7', '11'):
        n = int(board)
        ev, boards = board_pair(n, node, CAP_S)
        out = dict(subs=ev)
        if n == 2:
            out['facts'] = facts_2(ev, boards)
        elif n == 5:
            out['facts'] = facts_5(boards)
        else:
            key = [k for k in boards][1]
            out['facts'] = dict(B=facts_clock(boards, key), A=facts_clock(boards, list(boards)[0]))
    elif board in ('3', '4', '6', '8', '13'):
        n = int(board)
        ev, s = single(n, node, CAP_S)
        out = dict(subs={'': ev})
        out['facts'] = {'3': facts_3, '4': facts_4, '6': facts_6, '13': facts_13}[board](s) if board != '8' \
            else facts_8(s, ev)
    elif board == '14':
        out = run_14(node, CAP_S)
    elif board == '16':
        out = run_16(node, CAP_S)
    elif board == 'T1':
        out = run_t1()
    elif board == 'T2':
        out = run_t2()
    elif board == 'C1':
        out = run_c1(node, CAP_S)
    elif board == 'C2':
        out = run_c2(node, CAP_S)
    out['seconds'] = round(time.time() - t0, 1)
    return out


def main():
    path = sys.argv[1]
    boards = sys.argv[2:]
    node = Node()
    res = {}
    for b in boards:
        print('board', b, flush=True)
        res[b] = run(b, node)
        json.dump(res, open(path, 'w'), indent=1, default=str)
        print('done', b, res[b]['seconds'], 's', flush=True)
    node.close()


if __name__ == '__main__' and sys.argv[1:2] not in (['--facts'], ['--merge']):
    main()


# ---- step 9 supplement: a few more facts, cheap reads only (python3 tools/exam_evidence.py --facts out.json) -----------

def shoot_contests(s, i):
    """Attacker i's shot where he stands: its value, the open value, and who can contest it (with the value left)."""
    r = Read(s, exact=True)
    for lk in r.looks.get(i, []):
        if lk.route == 'shoot':
            return dict(value=round(lk.base, 2), open={t: round(v, 2) for t, v in lk.open.items()},
                        contested_by={f'X{d + 1}': {t: round(v, 2) for t, v in vals.items()} for d, vals in lk.vals.items()})
    return None


def one_ahead(s, t):
    """The All-Star's value of a turn one move ahead (its leaf; a roll weighed by its chances)."""
    ag = Agent(actor(s), 'allstar', seed=1)
    return round(ag._evaluate(s)(play_turn(s, t)), 2)


def supplement():
    f = {}
    _, b5, _ = E.POSITIONS[4]()
    f['5'] = {k: dict(shot_here=shoot_contests(s, 1),
                      step_up_B8=shoot_contests(s.with_(o=s.o[:1] + (SQ('B8'),) + s.o[2:]), 1)) for k, s in b5.items()}
    _, s6, _ = E.POSITIONS[5]()
    f['6'] = dict(shot_here=shoot_contests(s6, 3))
    _, b7, _ = E.POSITIONS[6]()
    f['7'] = {k: dict(shot_here=shoot_contests(s, 2), phase_table=round(vcoarse(s), 2)) for k, s in b7.items()}
    _, b11, _ = E.POSITIONS[10]()
    out = {}
    for k, s in b11.items():
        from playmaker_engine.actions import denier
        p2 = next((a for a in legal_actions(s) if a.kind == 'pass' and a.target == 1), None)
        den = {f'O{i + 1}': (lambda j: None if j is None else f'X{j + 1}')(denier(s, s.ball, i)) for i in range(5) if i != s.ball}
        out[k] = dict(pass_to_O2_legal=p2 is not None, denied_by=den,
                      pass_to_O2_lane_arrives=round(_lane_p(s, 1, s.o[1]), 2),
                      pass_to_O2_one_ahead=one_ahead(s, (p2,)) if p2 else None,
                      phase_table=round(vcoarse(s), 2),
                      other_passes={str(a): dict(arrives=round(_lane_p(s, a.target, s.o[a.target]), 2),
                                                 one_ahead=one_ahead(s, (a,)))
                                    for a in legal_actions(s) if a.kind == 'pass'})
    f['11'] = out
    _, s13, _ = E.POSITIONS[12]()
    avail, drive, alt = E.straight_drive(s13)
    cleared = []
    lane = lane_squares(s13.o[0], RC.RIM, 0.5)
    for a in legal_actions(s13):
        if a.side == 'O' and a.piece == 4 and a.kind in ('move', 'qs', 'sprint') and a.dest not in lane:
            n = apply(s13, a)
            if isinstance(n, ChanceNode):
                continue
            av, dv, al = E.straight_drive(n)
            cleared.append(dict(move=str(a), available=av, drive=round(dv, 2), best_other=round(al, 2)))
    cleared.sort(key=lambda r: -r['drive'])
    o3 = next(a for a in legal_actions(s13) if str(a) == 'O3 Move to N5')
    f['13'] = dict(straight_drive_with_o5=dict(available=avail, drive=round(drive, 2), best_other=round(alt, 2)),
                   straight_drive_o5_cleared=cleared[:3], n_clearing_moves=len(cleared),
                   o3_move_effect=dict(one_ahead=one_ahead(s13, (o3,)), before=leaf(s13)))
    _, s8, _ = E.POSITIONS[7]()
    cut = next(a for a in legal_actions(s8) if str(a) == 'O2 Move to D7')
    n = apply(s8, cut)
    pas = next(a for a in legal_actions(n) if a.kind == 'pass' and a.target == 1)
    f['8'] = dict(cut_alone=one_ahead(s8, (cut,)), cut_and_pass=one_ahead(s8, (cut, pas)), position_now=leaf(s8))
    return f


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[1] == '--facts':
    json.dump(supplement(), open(sys.argv[2], 'w'), indent=1, default=str)


def merge(folder):
    """docs/runs/step9/part_*.json and supplement.json -> exam_evidence.json, with the times."""
    import glob
    out = {}
    for f in sorted(glob.glob(os.path.join(folder, 'part_*.json'))):
        out.update(json.load(open(f)))
    sup = json.load(open(os.path.join(folder, 'supplement.json')))
    for k, v in sup.items():
        if k in out:
            out[k]['supplement'] = v
    secs = {k: v.get('seconds') for k, v in out.items()}
    out['_meta'] = dict(seconds=secs, total_minutes=round(sum(x or 0 for x in secs.values()) / 60, 1),
                        engine='engine.js (tools/exam_evidence.js), All-Star settings, rules through step 7',
                        cap_seconds=CAP_S)
    json.dump(out, open(os.path.join(folder, 'exam_evidence.json'), 'w'), indent=1, default=str)
    return out


if __name__ == '__main__' and sys.argv[1:2] == ['--merge']:
    merge(sys.argv[2])
