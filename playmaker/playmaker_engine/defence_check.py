"""How close the computer defence plays to the exact solver (step 3e).

The 50-position agreement set (agreement.py) holds small endgames with the offence to act. From each, the
offence makes its exact-best first action and its greedy first action; every resulting position where
the defence must decide (a turn or a reaction to a declared shot) is a defence test position. Each is
solved exactly (expectimax over the engine, transposition table, provably exact pruning), giving the best
value the defence can hold and the exact value of any first action.

A defence agrees with the solver when its first action is within 0.5 points of the exact best.
"""
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

from .actions import legal_actions, Action
from .agreement import load as load_agreement, state_of
from .policies import GreedyPolicy
from .resolve import apply, ChanceNode

PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'data', 'defence_set.json')


def _aj(a):
    return dict(kind=a.kind, side=a.side, piece=a.piece, dest=list(a.dest) if a.dest is not None else None,
                arrow=a.arrow, target=a.target, shot=a.shot)


def _ja(d):
    return Action(d['kind'], d['side'], d['piece'], tuple(d['dest']) if d['dest'] is not None else None,
                  d['arrow'], d['target'], d['shot'])


def _settle(node):
    """Follow a chance node to its most likely outcome (a pass, a dribble...)."""
    while isinstance(node, ChanceNode):
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return node


def _defending(st):
    return st.stage in ('reaction', 'contest') or (st.stage == 'play' and st.side == 'X')


def defence_positions(spec):
    """Follow the offence's exact-best line, and its greedy line, until the defence must decide."""
    from .solver import exact_solve
    s0 = state_of(spec)
    out = []
    for how in ('exact', 'greedy'):
        st, line = s0, []
        for _ in range(6):
            if st.stage == 'over' or _defending(st):
                break
            if how == 'exact':
                _, per = exact_solve(st)
                a = max(per, key=lambda x: per[x].ev)
            else:
                a = GreedyPolicy().choose(st)
            line.append(a)
            st = _settle(apply(st, a))
        if _defending(st) and all(st != o[2] for o in out):
            out.append((how, line, st))
    return out


def exact_value(state, a, tt):
    from .solver import exact_solve, mix
    node = apply(state, a)

    def val(n):
        if isinstance(n, ChanceNode):
            return sum(float(p) * val(sub) for p, _, sub in n.outcomes)
        if n.stage == 'over':
            from .solver import terminal_vals
            return terminal_vals(n, (None,))[0].ev
        return exact_solve(n, tt=tt)[0].ev
    return val(node)


def _row(spec):
    from .solver import exact_solve
    from .defence import ReadingDefence
    rows = []
    for how, oa, st in defence_positions(spec):
        t = time.time()
        tt = {}
        v, per = exact_solve(st, tt=tt)
        values = {json.dumps(_aj(a)): p.ev for a, p in per.items()}
        for pol in (GreedyPolicy(), ReadingDefence()):
            a = pol.choose(st)
            k = json.dumps(_aj(a))
            if k not in values:
                values[k] = exact_value(st, a, tt)
        rows.append(dict(spec=spec, offence=[_aj(a) for a in oa], via=how, best=v.ev, values=values,
                         seconds=round(time.time() - t, 1)))
    return rows


def build(workers=2):
    specs = [r['spec'] for r in load_agreement()]
    with ProcessPoolExecutor(workers) as ex:
        rows = [r for rs in ex.map(_row, specs) for r in rs]
    os.makedirs(os.path.dirname(PATH), exist_ok=True)
    with open(PATH, 'w') as f:
        json.dump(rows, f, indent=1)
    return rows


def load():
    with open(PATH) as f:
        return json.load(f)


def position(row):
    st = state_of(row['spec'])
    for d in row['offence']:
        st = _settle(apply(st, _ja(d)))
    return st


def grade(policy, rows=None, tol=0.5):
    """Share of defence positions where the policy's first action is within tol of the exact best, and
    the mean gap in points (defence: higher value = worse)."""
    rows = rows or load()
    agree, gaps, missing = 0, [], 0
    for r in rows:
        st = position(r)
        a = policy.choose(st)
        v = r['values'].get(json.dumps(_aj(a)))
        if v is None:
            missing += 1
            continue
        gap = v - r['best']
        gaps.append(gap)
        agree += gap <= tol
    n = len(gaps)
    return dict(n=n, agree=agree / n if n else 0.0, mean_gap=sum(gaps) / n if n else 0.0, missing=missing)


# ---- the mid-phase set: defence decisions from the 16 scenario cards in play ------------------------

PLAY_PATH = os.path.join(os.path.dirname(PATH), 'defence_play_set.json')


def play_positions(n=50, seeds=range(1, 9)):
    """Defence decision states (the start of a defence turn) from greedy-v-greedy games on every scenario
    card, several seeds each, taken round-robin across the cards so every card is represented. Deterministic."""
    import random
    from .scenarios import SCENARIOS, scenario_state
    from .resolve import sample
    g = GreedyPolicy()
    per_card = {}
    for c in sorted(SCENARIOS):
        seen, found = set(), []
        for sd in seeds:
            rng = random.Random(sd)
            s = scenario_state(c)
            if s.ctx.coach_call:
                s = apply(s, next(a for a in legal_actions(s) if a.kind == 'target'))
            for _ in range(80):
                if s.stage == 'over':
                    break
                if s.stage == 'play' and s.side == 'X' and s.turn_n == 0 and s not in seen:
                    seen.add(s)
                    found.append(s)
                node = apply(s, g.choose(s))
                s = sample(node, rng)[0] if isinstance(node, ChanceNode) else node
        per_card[c] = found
    out = []
    k = 0
    while len(out) < n and any(len(v) > k for v in per_card.values()):
        for c in sorted(per_card):
            if len(per_card[c]) > k and len(out) < n:
                out.append((c, per_card[c][k]))
        k += 1
    return out


def _turn(policy, s):
    """Let a defence play its whole turn (a chance node ends it there)."""
    node = s
    for _ in range(4):
        if isinstance(node, ChanceNode) or node.stage == 'over' or not _defending(node):
            break
        node = apply(node, policy.choose(node))
    return node


def _play_row(item):
    from .solver import Searcher
    from .solver_config import with_config
    from .defence import ReadingDefence
    card, s = item
    t = time.time()
    se = Searcher(with_config(eval_turns=1))
    ref = se.value(s, 2)[0].ev
    vals = {}
    for name, pol in (('greedy', GreedyPolicy()), ('reader', ReadingDefence(budget_s=None))):
        vals[name] = se.expect(_turn(pol, s), 1)
        vals[name] = vals[name][0].ev
    return dict(card=card, state=s.encode(), ref=ref, values=vals, seconds=round(time.time() - t, 1))


def build_play(workers=2, n=50):
    with ProcessPoolExecutor(workers) as ex:
        rows = list(ex.map(_play_row, play_positions(n)))
    with open(PLAY_PATH, 'w') as f:
        json.dump(rows, f, indent=1)
    return rows


def summary_play(rows, tol=0.5):
    out = {}
    for name in ('greedy', 'reader'):
        gaps = [r['values'][name] - r['ref'] for r in rows]
        out[name] = dict(n=len(gaps), agree=sum(g <= tol for g in gaps) / len(gaps), mean_gap=sum(gaps) / len(gaps))
    return out


# ---- what the arrows do: each moved defender's job at the end of the defence's turn ---------------

TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']


def profile_starts():
    from .cards import PRESCRIBED
    from .scenarios import game_state, scenario_state, SCENARIOS
    starts = [game_state(PRESCRIBED[i], PRESCRIBED[(i + k) % 10], TABLE_O, TABLE_X, TABLE_ARROWS)
              for i in range(10) for k in (1, 3, 7)]
    return starts + [scenario_state(n) for n in sorted(SCENARIOS)]


def job_profile(defence, starts=None, offence=None):
    """`offence` (greedy by default) v `defence` over the starts. Returns ({'play': Counter, 'reaction': Counter}, mean
    offence score). A defender's job is read when the defence's turn (or reaction) ends, so a closeout
    that turns first and then steps in counts as one arrow on the shooter."""
    import collections
    from . import board as B
    from .defence import arrow_job
    from .policies import play
    from .actions import MOVEMENT
    jobs = {'play': collections.Counter(), 'reaction': collections.Counter()}
    totals = []
    for st in starts or profile_starts():
        moved = {}

        def check(b, act, s):
            if isinstance(s, ChanceNode):
                moved.clear()
                return
            if act.side == 'X' and act.kind in MOVEMENT:
                moved[act.piece] = b.stage
            ended = s.stage != b.stage or (b.side == 'X' and s.side != 'X') or s.stage == 'over'
            if moved and ended and act.side == 'X':
                ref = b if s.stage == 'over' else s
                for j, stg in moved.items():
                    if stg == 'reaction' or B.on_board(ref.o[ref.ball]):
                        jobs[stg][arrow_job(ref, j)] += 1
                moved.clear()
        totals.append(float(play(st, offence or GreedyPolicy(), defence, seed=1, check=check)['score'].total))
    return jobs, sum(totals) / len(totals)
