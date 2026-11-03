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


# ---- plans by role (the context test) ---------------------------------------------------------

def role(card):
    """A role word from the card's strongest offensive skill."""
    r = card.r
    if r['shot_three'] >= 11:
        return 'shooter'
    if r['shot_post'] >= 15:
        return 'post'
    if r['pass'] >= 17:
        return 'playmaker'
    if r['shot_layup'] >= 19 or r['shot_dunk'] >= 18:
        return 'slasher'
    return {1: 'guard', 2: 'guard', 3: 'wing', 4: 'big', 5: 'big'}[card.num]


def zone_name(p):
    z = B.zone(p)
    if z == '3':
        return 'corner three' if p[1] <= 7 else 'arc three'
    return {'K': 'rim', 'M': 'mid-range', 'L': 'long two', '.': 'plain wood'}[z]


def play_label(s, play):
    """Concept play with player roles, e.g. 'kick to the shooter', 'drive by the slasher to the rim'."""
    acts = [a for a in play.actions if a.kind != 'end_turn']
    if not acts:
        return play.concept
    a = acts[0]
    if a.side == 'O':
        who = role(s.ctx.off[a.piece]) if a.piece >= 0 else ''
        last = acts[-1]
        if last.kind == 'pass':
            r = role(s.ctx.off[last.target])
            if len(acts) > 1:
                return f'relocate the {r} and kick'
            return f'{"kick" if play.concept == "kick" else "swing"} to the {r}'
        if last.kind == 'shot':
            spot = acts[0].dest if acts[0].kind in ('move', 'qs', 'sprint') else s.o[last.piece]
            return f'{"drive and shoot" if len(acts) > 1 else "shoot"}: {who}, {zone_name(spot)}'
        if a.kind in ('move', 'qs', 'sprint'):
            kind = 'drive' if a.piece == s.ball else 'relocate'
            return f'{kind}: {who} to {zone_name(a.dest)}'
        if play.concept == 'seal' or (last.kind == 'screen' and len(acts) > 1):
            return f'seal by the {who}'
        return {'screen': f'screen by the {who}', 'dribble': f'attack the closeout ({who})',
                'hesitate': 'hesitate'}.get(a.kind, f'{a.kind} by the {who}')
    # defence
    c = play.concept
    base = c.split('+')[0]
    if base in ('closeout', 'help', 'deny', 'recover', 'switch'):
        two = B.cheb(s.x[a.piece], s.o[s.ball]) >= 4
        return f'{c}{" from two passes away" if base == "help" and two else ""}'
    return c


def root_labels(se, s, depth):
    root = se.tt.get((s, depth))
    if root is None:
        return []
    return [dict(label=play_label(s, p), concept=p.concept, text=p.text(), value=round(v[0].ev, 3))
            for p, v in root.children]


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
    labels = root_labels(se, s, d)
    best_label = max(labels, key=lambda x: x['value'])['label'] if labels else ''
    # label every turn of the principal line too (for dead-rule counting)
    node, dd, line_labels = s, d, []
    for ln in se.principal_line(s, d, target_index)[0]:
        line_labels.append(dict(side=ln['side'], label=play_label(node, ln['play']), concept=ln['concept']))
        nxt = apply_play(node, ln['play'])
        while isinstance(nxt, ChanceNode):
            nxt = max(nxt.outcomes, key=lambda o: o[0])[2]
        node = nxt
    return dict(value=v.ev, look=v.look, p30=v.p30, pexp=v.pexp, fs=v.fs, depth=d, seconds=round(res['seconds'], 1),
                root=labels, best_label=best_label, line_labels=line_labels,
                teams=[s.ctx.off_team, s.ctx.def_team],
                nodes=res['nodes'], evals=res['evals'], exact_hits=res['exact_hits'], exact_tries=res['exact_tries'],
                line=line, finish=finish, plans=plan_list, n_plans=len(plan_list), gift2=gift2,
                verdict=verdict(v, len(plan_list), gift2, cfg), all_vals=[x.ev for x in res['vals']])


def _start(n, rules=None, setup=None):
    sc = SCENARIOS[n]
    st = scenario_state(n, rules=rules, target=0 if sc.get('target') else None)
    if setup:
        st = setup(st)
    return st


def solve_card(n, budget_s=60, seed=0, cfg=DEFAULT, rules=None, setup=None, max_depth=None, target=None):
    """One run on one card. Coach's Call cards: known-target value for each target, best taken
    (or the given target only)."""
    sc = SCENARIOS[n]
    if sc.get('target') and target is not None:
        r = solve_state(_start(n, rules, setup).with_(target=target), cfg, budget_s, seed, max_depth)
        r['target'] = target
        return r
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


def coach_vector(n, budget_s=60, cfg=DEFAULT):
    """Guessing defence: one strategy against all five possible targets."""
    st = _start(n)
    se = Searcher(cfg, targets=(0, 1, 2, 3, 4))
    res = se.search(st, budget_s=budget_s)
    vals = res['vals']
    t_best = max(range(5), key=lambda t: vals[t].ev)
    return dict(value=vals[t_best].ev, guessing=vals[t_best].ev, guessing_target=t_best,
                guessing_per_target=[v.ev for v in vals], depth=res['depth'])


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
        from .solver_fixes import CANDIDATES
        text, fix = CANDIDATES[n][extra]
        r = solve_card(n, budget, seed, setup=fix, target=_best_target(n))
        r['fix'] = text
    elif kind == 'target':                    # Coach's Call: one target, its own full budget
        r = solve_card(n, budget, seed, target=extra)
    elif kind == 'coachvec':
        r = coach_vector(n, budget)
    elif kind == 'rule7b':
        r = solve_card(n, budget, seed, rules=RC.with_rules(defence_empty_ends_phase=False), target=_best_target(n))
    elif kind == 'context':                   # another prescribed matchup, same squares and clock
        from .solver_fixes import teams
        r = solve_card(n, budget, seed, setup=teams(*extra), target=_best_target(n))
    else:
        raise ValueError(kind)
    r['wall'] = round(time.time() - t0, 1)
    r['job'] = [kind, n, budget, seed, extra]
    return (kind, n, budget, seed), r


BEST_TARGET = {8: 0, 9: 4, 11: 1}         # the known-target winners from round 1, for single-target jobs


def _best_target(n):
    return BEST_TARGET.get(n) if SCENARIOS[n].get('target') else None


def run_jobs(jobs, workers=3, store='runs.json'):
    """Run jobs in parallel, saving every finished result as it lands (resumable)."""
    from concurrent.futures import as_completed
    path = os.path.join(RESULTS, store)
    done = {}
    if os.path.exists(path):
        with open(path) as f:
            done = json.load(f)
    keyf = lambda j: json.dumps(list(j[:4]) + ([j[4]] if j[4] is not None else []))
    todo = [j for j in jobs if keyf(j) not in done]
    with ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(_job, j): j for j in todo}
        for fut in as_completed(futs):
            key, r = fut.result()
            j = futs[fut]
            done[keyf(j)] = r
            os.makedirs(RESULTS, exist_ok=True)
            with open(path, 'w') as f:
                json.dump(done, f, indent=1, default=str)
            print(f'done {key}: value {r.get("value", r.get("known", 0)):.2f} ({r["wall"]}s)', flush=True)
    return done


def main_jobs(short=90, long=240, seeds=2, cards=None):
    cards = cards or SOLVE_ORDER
    jobs = []
    for n in cards:
        for sd in range(seeds):
            jobs.append(('solve', n, short, sd, None))
        jobs.append(('solve', n, long, 0, None))
    for n in cards:
        jobs.append(('rule7', n, short, 0, None))
    for n in cards:
        if SCENARIOS[n].get('target'):
            jobs.append(('coach', n, short, 0, None))
    return jobs


def save(name, data):
    os.makedirs(RESULTS, exist_ok=True)
    with open(os.path.join(RESULTS, name), 'w') as f:
        json.dump(data, f, indent=1, default=str)


# ---- reading results back --------------------------------------------------------------------

def load_runs(store='runs.json'):
    path = os.path.join(RESULTS, store)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {tuple(json.loads(k)): v for k, v in raw.items()}


def _runs_for(runs, kind, n):
    return {(k[2], k[3]): v for k, v in runs.items() if k[0] == kind and k[1] == n}


def card_summary(runs, n, short, long):
    rs = _runs_for(runs, 'solve', n)
    if not rs:
        return None
    main = rs.get((long, 0)) or rs.get((short, 0)) or next(iter(rs.values()))
    vals = [r['value'] for r in rs.values()]
    spread = max(vals) - min(vals)
    first = lambda r: r['line'][0]['text'] if r['line'] else ''
    changed = (long, 0) in rs and (short, 0) in rs and first(rs[(long, 0)]) != first(rs[(short, 0)])
    label = 'unstable' if (spread > DEFAULT.unstable_spread or changed) else 'estimated'
    if main.get('exact_full'):
        label = 'exact'
    return dict(main=main, spread=spread, line_changed=changed, label=label, runs=rs)


def format_line(line, finish):
    out = []
    for i, ln in enumerate(line, 1):
        who = 'Offence' if ln['side'] == 'O' else 'Defence'
        rolls = (' — ' + '; '.join(ln['rolls'])) if ln['rolls'] else ''
        out.append(f'{i}. **{who}** ({ln["concept"]}, clock {ln["clock"]}): {ln["text"]}{rolls}')
    if finish:
        out.append(f'\n*Result:* {finish}')
    return '\n'.join(out)


def format_card(n, r):
    sc = SCENARIOS[n]
    head = (f'{n}. {sc["title"]} ({sc["kind"]}, clock {sc["clock"]}): value {r["value"]:.2f}, look {r["look"]:.2f}, '
            f'P(30+) {r["p30"]:.0%}, plans {r["n_plans"]}, verdict {r["verdict"]}, depth {r["depth"]} '
            f'({r["seconds"]}s)')
    return head + '\n' + format_line(r['line'], r['finish']).replace('**', '')


def rule_health(runs, short=90, long=240):
    rh = {}
    # 1. open question 7
    seven = []
    for n in SOLVE_ORDER:
        base = runs.get(('solve', n, short, 0))
        alt = runs.get(('rule7', n, short, 0))
        if not base or not alt:
            continue
        first = lambda r: [l['text'] for l in r['line'][:2]]
        seven.append(dict(n=n, base=base['value'], alt=alt['value'], diff=alt['value'] - base['value'],
                          line_changed=first(base) != first(alt), base_line=first(base), alt_line=first(alt),
                          base_x_tokens_burn=sum(1 for l in base['line'] if l['side'] == 'X' and l['concept'] == 'pause')))
    rh['seven'] = seven
    # 2. dominant / unused actions in the principal lines
    from collections import Counter
    kinds_o, kinds_x, cards_with = Counter(), Counter(), Counter()
    fouls = []
    for n in SOLVE_ORDER:
        c = card_summary(runs, n, short, long)
        if not c:
            continue
        seen = set()
        for ln in c['main']['line']:
            for k in ln['kinds']:
                (kinds_o if ln['side'] == 'O' else kinds_x)[k] += 1
                seen.add((ln['side'], k))
            for r in ln['rolls']:
                if 'foul' in r and r.split(': ', 1)[1].startswith('foul'):
                    fouls.append((n, r))
        for k in seen:
            cards_with[k] += 1
    rh['kinds_o'], rh['kinds_x'], rh['cards_with'] = dict(kinds_o), dict(kinds_x), {f'{a}:{b}': v for (a, b), v in cards_with.items()}
    rh['fouls'] = fouls
    # 4. clock expiry
    exp = []
    for n in SOLVE_ORDER:
        c = card_summary(runs, n, short, long)
        if c:
            m = c['main']
            exp.append(dict(n=n, pexp=m['pexp'], fs=m['fs'], value=m['value'], alt=m['value'] - m['fs']))
    rh['expiry'] = exp
    rh['forced_ref'] = forced_reference()
    return rh


def forced_reference():
    """Forced-shot value if the clock ran out with the pieces as the card sets them (the carrier
    shoots where it stands; the defence gets its last two actions). As built: forced shot - 5.
    Alternative: the forced shot or -5, whichever is worse for the offence."""
    from .solver import Evaluator
    out = []
    ev = Evaluator()
    for n in SOLVE_ORDER:
        st = _start(n)
        if st.inbound:
            st = st.with_(ball=max((i for i in range(5) if i != st.ctx.inbounder), key=lambda i: B.dist_rim(st.o[i])))
        fs = ev.carrier_look(st, st.ball, 2, False, forced=True)[0]
        out.append(dict(n=n, forced=fs, built=fs + RC.TURNOVER_POINTS, alt=min(fs, RC.TURNOVER_POINTS)))
    return out


def rule_health_text(runs, short=90, long=240):
    rh = rule_health(runs, short, long)
    out = ['Open question 7 (defence playing its last token ends the phase):']
    for r in rh['seven']:
        out.append(f'  {r["n"]:>2}: as built {r["base"]:.2f}, alternative {r["alt"]:.2f} (diff {r["diff"]:+.2f}); '
                   f'opening changed: {r["line_changed"]}')
    out.append(f'Offence action counts in principal lines: {rh["kinds_o"]}')
    out.append(f'Defence action counts in principal lines: {rh["kinds_x"]}')
    out.append(f'Foul outcomes on principal lines: {rh["fouls"] or "none"}')
    for e in rh['expiry']:
        out.append(f'  {e["n"]:>2}: P(clock 0) {e["pexp"]:.0%}, expected forced-shot points {e["fs"]:.2f}')
    return '\n'.join(out)


# ---- SOLVER_REPORT.md --------------------------------------------------------------------------

def _pct(x):
    return f'{x:.0%}'


def write_report(short=90, long=240, path=None, fixes=None, extra=''):
    runs = load_runs()
    path = path or os.path.join(ROOT, 'SOLVER_REPORT.md')
    cfg = DEFAULT
    L = []
    L.append('# Solver Report\n')
    L.append(f'Budgets used in this run: **{short} s and {long} s per card** (defaults in `solver_config.py`: '
             f'{cfg.budgets_min[0]:g} and {cfg.budgets_min[1]:g} minutes), seeds 0 and 1 at the short budget. '
             'Every value is **estimated** (guided search, evaluation at the leaves) unless marked exact. '
             'A card is **unstable** if its values spread by more than 2 points across runs, or its first play changes '
             'between budgets.\n')
    L.append('Value is the expected possession score under best play; look is the expected shot value (or foul points); '
             'P(30+) is the chance of an Excellent look. Coach\'s Call rows use the known-target value.\n')
    L.append('## Summary\n')
    L.append('| # | Card | Value | Look | P(30+) | Plans | Verdict | Label | Depth | Spread |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    summaries = {}
    for n in SOLVE_ORDER:
        c = card_summary(runs, n, short, long)
        if not c:
            continue
        summaries[n] = c
        m = c['main']
        L.append(f'| {n} | {SCENARIOS[n]["title"]} | {m["value"]:.1f} | {m["look"]:.1f} | {_pct(m["p30"])} | '
                 f'{m["n_plans"]} | {m["verdict"]} | {c["label"]} | {m["depth"]} | {c["spread"]:.1f} |')
    L.append('')
    if extra:
        L.append(extra)
    L.append(extra_sections(runs, short, long))
    # coach
    coach = [(n, runs.get(('coach', n, short, 0))) for n in SOLVE_ORDER if SCENARIOS[n].get('target')]
    coach = [(n, r) for n, r in coach if r]
    if coach:
        L.append("## Coach's Call bounds\n")
        L.append('| # | Card | Known target (defence plays against it) | Guessing defence | Secret worth | Best target |')
        L.append('|---|---|---|---|---|---|')
        for n, r in coach:
            L.append(f'| {n} | {SCENARIOS[n]["title"]} | {r["known"]:.1f} (O{r["known_target"] + 1}) | '
                     f'{r["guessing"]:.1f} (O{r["guessing_target"] + 1}) | {r["gap"]:+.1f} | O{r["guessing_target"] + 1} |')
        L.append('')
    # rule health
    rh = rule_health(runs, short, long)
    L.append('## Rule health\n')
    L.append('### 1. Open question 7: the defence playing its last token ends the phase\n')
    L.append('| # | Card | As built | Phase runs on | Difference | Opening changes |')
    L.append('|---|---|---|---|---|---|')
    for r in rh['seven']:
        L.append(f'| {r["n"]} | {SCENARIOS[r["n"]]["title"]} | {r["base"]:.1f} | {r["alt"]:.1f} | {r["diff"]:+.1f} | '
                 f'{"yes" if r["line_changed"] else "no"} |')
    L.append('')
    L.append('### 2. Action use in the principal lines\n')
    L.append('| Side | Action | Times played | Cards using it |')
    L.append('|---|---|---|---|')
    for side, counts in (('O', rh['kinds_o']), ('X', rh['kinds_x'])):
        names = (['move', 'qs', 'sprint', 'pass', 'screen', 'dribble', 'hesitate', 'shot'] if side == 'O'
                 else ['move', 'qs', 'sprint', 'intercept', 'challenge', 'steal', 'pause', 'end_turn'])
        for k in names:
            L.append(f'| {"Offence" if side == "O" else "Defence"} | {k} | {counts.get(k, 0)} | '
                     f'{rh["cards_with"].get(f"{side}:{k}", 0)} of {len(summaries)} |')
    L.append('')
    L.append('### 3. And-one\n')
    L.append(('Foul outcomes on the principal lines: ' + '; '.join(f'card {n}: {t}' for n, t in rh['fouls']))
             if rh['fouls'] else 'No principal line contains a foul outcome.')
    L.append('')
    L.append('### 4. Clock expiry\n')
    L.append('Best play never runs the clock out on any card: every principal line shoots inside the search horizon, '
             'so P(clock 0) is 0% throughout. To give the designer the numbers anyway, this table prices a forced shot '
             'from each card\'s starting position (the carrier shoots where it stands after the defence\'s last two '
             'actions; inbound cards use the player furthest from the rim).\n')
    L.append('| # | Card | Forced shot | As built (forced shot − 5) | Alternative (worse of forced shot or −5) |')
    L.append('|---|---|---|---|---|')
    for e in rh['forced_ref']:
        L.append(f'| {e["n"]} | {SCENARIOS[e["n"]]["title"]} | {e["forced"]:.1f} | {e["built"]:.1f} | {e["alt"]:.1f} |')
    L.append('')
    L.append('Because forced shots are floored at 0, "the worse of the two" is always −5: the alternative simply removes the '
             'forced shot. Per-card values from the solver runs:\n')
    L.append('| # | Card | P(clock 0) | Expected forced-shot points | Value as built | Value with "forced shot or −5, whichever is worse" |')
    L.append('|---|---|---|---|---|---|')
    for e in rh['expiry']:
        L.append(f'| {e["n"]} | {SCENARIOS[e["n"]]["title"]} | {_pct(e["pexp"])} | {e["fs"]:.2f} | {e["value"]:.1f} | {e["alt"]:.1f} |')
    L.append('')
    # per card
    L.append('## Cards\n')
    for n in SOLVE_ORDER:
        c = summaries.get(n)
        if not c:
            continue
        m = c['main']
        sc = SCENARIOS[n]
        L.append(f'<div class="file"></div>\n\n### {n}. {sc["title"]}\n')
        L.append(f'{sc["kind"]}, clock {sc["clock"]}. O: {sc["off"]}. X: {sc["dfn"]}. *{sc["text"]}*\n')
        L.append(f'**Value {m["value"]:.1f}**, look {m["look"]:.1f}, P(30+) {_pct(m["p30"])}, '
                 f'P(clock 0) {_pct(m["pexp"])}. Plans within 90%: {m["n_plans"]}. **Verdict: {m["verdict"]}** '
                 f'({c["label"]}; depth {m["depth"]}; spread {c["spread"]:.1f} across '
                 + ', '.join(f'{v["value"]:.1f}' for v in c['runs'].values()) + ').\n')
        if m.get('known_per_target'):
            L.append('Known-target values: ' + ', '.join(f'O{int(t) + 1} {v:.1f}' for t, v in m['known_per_target'].items()) + '.\n')
        L.append('**Principal line** (best play, following the most likely roll):\n')
        L.append(format_line(m['line'], m['finish']) + '\n')
        if m['plans']:
            top = sorted(m['plans'], key=lambda p: -p['value'])[:5]
            L.append('**Opening plans within 90% of best** (top 5 shown): ' +
                     '; '.join(f'{p["text"]} ({p["value"]:.1f})' for p in top) + '\n')
        if fixes and n in fixes:
            L.append('**Suggested fix:** ' + fixes[n] + '\n')
    with open(path, 'w') as f:
        f.write('\n'.join(L))
    return path


# ---- fixes, settings, limits --------------------------------------------------------------------

def fix_rows(runs, long=240):
    from .solver_fixes import CANDIDATES
    rows = []
    for n, cands in CANDIDATES.items():
        base = runs.get(('solve', n, long, 0))
        for i, (text, _) in enumerate(cands):
            r = runs.get(('fix', n, long, 0, i))
            if r and base:
                rows.append(dict(n=n, i=i, text=text, base=base, fix=r))
    return rows


def concept_share(runs, long=240):
    raw = concept = 0
    for n in SOLVE_ORDER:
        r = runs.get(('solve', n, long, 0))
        if not r:
            continue
        for ln in r['line']:
            if ln['concept'] == 'raw':
                raw += 1
            else:
                concept += 1
    return concept, raw


def extra_sections(runs, short=90, long=240):
    L = []
    rows = fix_rows(runs, long)
    if rows:
        L.append('## Suggested fixes, re-solved\n')
        L.append(f'Each fix changes only the card setup. Both columns are the same budget ({long} s, seed 0).\n')
        L.append('| # | Card | Fix | Before | After |')
        L.append('|---|---|---|---|---|')
        for r in rows:
            b, f = r['base'], r['fix']
            L.append(f'| {r["n"]} | {SCENARIOS[r["n"]]["title"]} | {r["text"]} | {b["verdict"]}: {b["value"]:.1f}, '
                     f'P(30+) {_pct(b["p30"])}, {b["n_plans"]} plans | **{f["verdict"]}**: {f["value"]:.1f}, '
                     f'P(30+) {_pct(f["p30"])}, {f["n_plans"]} plans |')
        L.append('')
    c, raw = concept_share(runs, long)
    L.append('## Search settings and their tested effect\n')
    L.append('All live in `solver_config.py`.\n')
    L.append('| Setting | Value | Tested effect |')
    L.append('|---|---|---|')
    before = {}
    path = os.path.join(RESULTS, 'runs_inbound_before_fix.json')
    if os.path.exists(path):
        with open(path) as f:
            for k, v in json.load(f).items():
                kk = json.loads(k)
                if kk[0] == 'solve' and kk[2] == long and kk[3] == 0:
                    before[kk[1]] = v['value']
    inb = ', '.join(f'{SCENARIOS[n]["title"]} {before[n]:.1f} → {runs[("solve", n, long, 0)]["value"]:.1f}'
                    for n in sorted(before) if ('solve', n, long, 0) in runs)
    L += [
        f'| `top_k_raw` (K) | 8 | Candidate coverage 50/50 on random endgames. In the principal lines, {c} turns used a concept play and {raw} a raw action. |',
        '| `raw_depth` | 1 | Raw actions are added at the root only; deeper nodes use concept plays (cost). |',
        '| `beam` / `root_beam` | 6 / 40 | Not varied in this run (time). Guided search on micro positions with beam 30 matched exact values within 0.5. |',
        '| `endgame_tokens` (N) / `exact_node_cap` | 2 / 4000 | The exact solver never triggered on a full card: no principal line reaches the last phase with 2 or fewer tokens inside the horizon. Exactness is tested on micro positions (matches brute force; pruning changes nothing). |',
        '| `quiescence` | on | Leaves where the defence is to move get one more defence turn. Without it, Need a Three showed P(30+) = 100% on a line with a 45% interception risk. Costs 2 to 4 times the search time. |',
        f'| Inbound evaluation prices interception risk | on | Before → after ({long} s): {inb}. |' if inb else '| Inbound evaluation prices interception risk | on | |',
        '| `kick_weight` | 0 | 0.9 tried on One Phase Left and Need a Three at depth 3: no change in value (21.0, 30.0). Kept at 0. |',
        f'| Budgets | {short} s and {long} s | Defaults are 2 and 10 minutes; see Limits. Values moved by up to the spreads in the summary table between the two budgets. |',
    ]
    L.append('')
    L.append('## Limits of this run\n')
    L.append(f'- **Budgets were scaled down** from 2 and 10 minutes to {short} and {long} seconds, and from 5 seeds to 2, '
             'to fit the session (the full default set is about 30 hours of compute on this machine). '
             '`python -m playmaker_engine solve-all` runs the defaults.')
    L.append('- **Depth is 2 to 4 turns.** Clock-8 cards last 20 or more turns, so the value is "the best look the offence '
             'can force in the next few turns", not the whole possession. The leaf evaluation fills in the rest.')
    L.append('- **Seeds only change tie-breaking.** The search is deterministic, so the spread mostly reflects budget '
             '(depth reached), not randomness.')
    L.append("- **Coach's Call** searches reached depth 2 only (five targets share the budget), so the secret's value "
             'could not be measured at this depth.')
    L.append('- **The evaluation does not score defensive position for later turns.** That is why Pause (doing nothing) '
             'often ties for best: see rule health 2.')
    L.append('')
    return '\n'.join(L)


# ---- round 2 job list -----------------------------------------------------------------------------

TEAM_NAMES = [t[0] for t in __import__('playmaker_engine.cards', fromlist=['TEAMS_MOD']).TEAMS_MOD.TEAMS]
SCREEN_TEAMS = ['Twin Towers', 'High-Low', 'Pace and Space']


def alt_matchups(n, k=2):
    """k other prescribed matchups for card n, chosen by rotation (never the card's own teams)."""
    sc = SCENARIOS[n]
    out, i = [], n
    while len(out) < k:
        off = TEAM_NAMES[(i * 3 + 1) % 10]
        dfn = TEAM_NAMES[(i * 7 + 4) % 10]
        i += 1
        if off == dfn or (off, dfn) == (sc['off'], sc['dfn']) or (off, dfn) in out:
            continue
        out.append((off, dfn))
    return out


SCREEN_CARDS = [10, 12, 15]                # O5's standing screen; post cards where seals matter


def round2_jobs(short=120, long=600, seeds=5):
    jobs = []
    coach = [n for n in SOLVE_ORDER if SCENARIOS[n].get('target')]
    for n in SOLVE_ORDER:
        if n in coach:
            for b in (short, long):
                for t in range(5):
                    jobs.append(('target', n, b, 0, t))
                jobs.append(('coachvec', n, b, 0, None))
        else:
            for sd in range(seeds):
                jobs.append(('solve', n, short, sd, None))
            jobs.append(('solve', n, long, 0, None))
    for n in SOLVE_ORDER:
        for b in (short, long):
            jobs.append(('rule7b', n, b, 0, None))
    for n in SOLVE_ORDER:
        for m in alt_matchups(n):
            jobs.append(('context', n, short, 0, list(m)))
    for n in SCREEN_CARDS:
        for off in SCREEN_TEAMS:
            if off != SCENARIOS[n]['off']:
                jobs.append(('context', n, short, 0, [off, SCENARIOS[n]['dfn']]))
    # cheapest first so partial results are useful early
    return sorted(jobs, key=lambda j: (j[2], j[0] != 'solve'))
