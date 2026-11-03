"""Solve scenario cards and write SOLVER_REPORT.md."""
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor

from . import board as B
from . import rules_config as RC
from .resolve import ChanceNode
from .scenarios import SCENARIOS, scenario_state
from .scoring import score
from .solver import Searcher, apply_play, expected, Val
from .solver_config import DEFAULT, with_config

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, 'solver_results')
SOLVE_ORDER = [13, 7, 10, 6, 5, 3, 4, 1, 2, 8, 9, 11, 12, 14, 15, 16]


def sig(play):
    return tuple((a.kind, a.side + str(a.piece + 1)) for a in play.actions if a.kind != 'end_turn')


def roll_text(what, label, p):
    pct = f'{p:.0%}'
    if what.startswith('Pass'):
        need = round(p * 20) if label == 'success' else round((1 - p) * 20)
        return f'{what}: pass {"completes" if label == "success" else "intercepted"} (offence needs {need} or less; {pct})'
    if what.startswith('Dribble'):
        return f'{what}: dribble {"wins" if label == "success" else "loses"} ({pct})'
    if what.startswith('Screen'):
        return f'{what}: screen {"holds" if label == "success" else "beaten"} ({pct})'
    return f'{what}: {label} ({pct})'


def _follow(searcher, s, depth, target_index=0):
    """Principal line with readable rolls, plus the node it stops at."""
    lines, end = searcher.principal_line(s, depth, target_index)
    out = []
    for ln in lines:
        rolls = []
        for what, lab, p in ln['rolls']:
            rolls.append(roll_text(what, lab, p))
        out.append(dict(side=ln['side'], concept=ln['concept'], text=ln['text'], rolls=rolls, clock=ln['clock'],
                        phase=ln['phase'], kinds=[a.kind for a in ln['play'].actions if a.kind != 'end_turn'],
                        actors=[a.side + str(a.piece + 1) for a in ln['play'].actions if a.kind != 'end_turn']))
    finish = ''
    if not isinstance(end, ChanceNode) and end.stage == 'over':
        finish = str(score(end))
    elif not isinstance(end, ChanceNode):
        v = searcher.ev(end)[target_index]
        finish = f'search horizon reached; evaluation {v.ev:.1f} (look {v.look:.1f})'
    return out, finish


def _most_likely(node):
    while isinstance(node, ChanceNode):
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return node


def plans(searcher, s, depth, cfg, target_index=0):
    """Offence opening plans (first two offence turns, by action type and player) and their values."""
    root = searcher.tt.get((s, depth))
    if root is None or not root.children:
        return [], 0.0
    out = {}
    best = root.vals[target_index].ev
    for p1, v1 in root.children:
        node = _most_likely(apply_play(s, p1))
        val = v1[target_index]
        plan_sig = (sig(p1),)
        got_second = False
        if depth >= 3 and not isinstance(node, ChanceNode) and node.stage != 'over':
            e = searcher.tt.get((node, depth - 1))
            if e and e.best is not None:
                node2 = _most_likely(apply_play(node, e.best))
                if not isinstance(node2, ChanceNode) and node2.stage != 'over' and node2.side == 'O':
                    e2 = searcher.tt.get((node2, depth - 2))
                    if e2 and e2.children:
                        for p2, v2 in e2.children:
                            k = (sig(p1), sig(p2))
                            vv = v2[target_index]
                            if k not in out or vv.ev > out[k][0].ev:
                                out[k] = (vv, p1, p2)
                        got_second = True
        if not got_second:
            if plan_sig not in out or val.ev > out[plan_sig][0].ev:
                out[plan_sig] = (val, p1, None)
    thr = best - (1 - cfg.plan_share) * abs(best)
    good = [(k, v) for k, v in out.items() if v[0].ev >= thr - 1e-9]
    return good, best


def gift_two_turns(searcher, s, depth, target_index=0):
    """A 30+ look in the offence's first two turns against best defence?"""
    root = searcher.tt.get((s, depth))
    if root is None:
        return False
    for p1, v1 in root.children:
        if any(a.kind == 'shot' for a in p1.actions) and v1[target_index].look >= RC.SCENARIO_GOAL:
            return True
    good, _ = plans(searcher, s, depth, DEFAULT, target_index)
    for k, (v, p1, p2) in good:
        if p2 is not None and any(a.kind == 'shot' for a in p2.actions) and v.look >= RC.SCENARIO_GOAL:
            return True
    return False


def verdict(v, n_plans, gift2, cfg):
    if v.p30 > cfg.gift_p30 or gift2:
        return 'Gift'
    if v.p30 < cfg.wall_p30 and v.look < cfg.wall_look:
        return 'Wall'
    if n_plans <= 1:
        return 'Single trick'
    return 'Puzzle'


def solve_state(s, cfg=DEFAULT, budget_s=60, seed=0, max_depth=None, targets=(None,), target_index=0):
    se = Searcher(cfg, targets=targets, seed=seed)
    res = se.search(s, budget_s=budget_s, max_depth=max_depth)
    d = res['depth']
    v = res['vals'][target_index]
    line, finish = _follow(se, s, d, target_index)
    good, _ = plans(se, s, d, cfg, target_index)
    gift2 = gift_two_turns(se, s, d, target_index)
    plan_list = [dict(sig=[list(x) for x in k], value=round(val[0].ev, 2),
                      text=val[1].text() + (f' / {val[2].text()}' if val[2] else '')) for k, val in good]
    return dict(value=v.ev, look=v.look, p30=v.p30, pexp=v.pexp, fs=v.fs, depth=d, seconds=round(res['seconds'], 1),
                nodes=res['nodes'], evals=res['evals'], exact_hits=res['exact_hits'], exact_tries=res['exact_tries'],
                line=line, finish=finish, plans=plan_list, n_plans=len(plan_list), gift2=gift2,
                verdict=verdict(v, len(plan_list), gift2, cfg), all_vals=[x.ev for x in res['vals']])


def _start(n, rules=None, setup=None):
    sc = SCENARIOS[n]
    st = scenario_state(n, rules=rules, target=0 if sc.get('target') else None)
    if setup:
        st = setup(st)
    return st


def solve_card(n, budget_s=60, seed=0, cfg=DEFAULT, rules=None, setup=None, max_depth=None):
    """One run on one card. Coach's Call cards: known-target value for each target, best taken."""
    sc = SCENARIOS[n]
    if sc.get('target'):
        best = None
        per = {}
        for t in range(5):
            st = _start(n, rules, setup).with_(target=t)
            r = solve_state(st, cfg, budget_s / 5, seed, max_depth)
            per[t] = r['value']
            if best is None or r['value'] > best['value']:
                best = dict(r, target=t)
        best['known_per_target'] = per
        return best
    return solve_state(_start(n, rules, setup), cfg, budget_s, seed, max_depth)


def coach_bounds(n, budget_s=60, cfg=DEFAULT):
    """Known target (defence plays against it) and guessing defence (one strategy for all targets)."""
    known = solve_card(n, budget_s, 0, cfg)
    st = _start(n)
    se = Searcher(cfg, targets=(0, 1, 2, 3, 4))
    res = se.search(st, budget_s=budget_s)
    vals = res['vals']
    t_best = max(range(5), key=lambda t: vals[t].ev)
    return dict(known=known['value'], known_target=known['target'], known_per_target=known['known_per_target'],
                guessing=vals[t_best].ev, guessing_target=t_best, guessing_per_target=[v.ev for v in vals],
                gap=vals[t_best].ev - known['value'], depth=res['depth'])


# ---- jobs (run in parallel) ----------------------------------------------------------------

def _job(args):
    kind, n, budget, seed, extra = args
    t0 = time.time()
    if kind == 'solve':
        r = solve_card(n, budget, seed)
    elif kind == 'rule7':
        r = solve_card(n, budget, seed, rules=RC.with_rules(defence_empty_ends_phase=False))
    elif kind == 'coach':
        r = coach_bounds(n, budget)
    elif kind == 'fix':
        from .solver_fixes import FIXES
        r = solve_card(n, budget, seed, setup=FIXES[n]['setup'])
    else:
        raise ValueError(kind)
    r['wall'] = round(time.time() - t0, 1)
    return (kind, n, budget, seed), r


def run_jobs(jobs, workers=None):
    out = {}
    with ProcessPoolExecutor(workers or os.cpu_count() or 1) as ex:
        for key, r in ex.map(_job, jobs):
            out[key] = r
    return out


def save(name, data):
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), 'w') as f:
        json.dump(data, f, indent=1, default=str)
