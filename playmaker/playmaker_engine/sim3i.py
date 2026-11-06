"""Step 3i: the one combined simulation, after every change (research tool, not part of the game).

Five pairings (All-Star v All-Star; Rookie and Starter offence v All-Star defence; All-Star offence v Rookie
and Starter defence), the 16 scenario cards plus 4 random prescribed-team possessions, 2 seeds each, plus a
late_closeout=True rule-test variant (All-Star v All-Star only). Each possession records:

  offence tokens spent off the ball (by a player without the ball) and on it
  passes clean when thrown (pass_risk at the throw), and how the contested ones ended
  interceptions and steals won
  shots, split twos and threes; shooting fouls; shots with no eligible contester at the contest
  the possession's points; the goals the offence set (step 3i notes)

Resumable: results are stored by key after every possession, and a rerun skips the keys already there.
The harness uses only the engine's public calls, so it also runs against the pre-3i code (the before
figures): PYTHONPATH=<old checkout> python3 -m playmaker_engine.sim3i --store before.json --no-variant

  python3 -m playmaker_engine.sim3i [--workers 3] [--store sim3i.json] [--estimate] [--random 4] [--seeds 1 2]
"""
import argparse
import json
import os
import random
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed

RESULTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'solver_results')
PAIRS = [('allstar', 'allstar'), ('rookie', 'allstar'), ('starter', 'allstar'), ('allstar', 'rookie'), ('allstar', 'starter')]


def starts(random_n=4):
    from .headtohead import starts as h2h_starts
    return h2h_starts(random_n)


def start_state(spec, rules=None):
    from .scenarios import scenario_state, game_state
    from .headtohead import TABLE_O, TABLE_X, TABLE_ARROWS
    kind, v = spec
    if kind == 'card':
        return scenario_state(v, rules=rules) if rules is not None else scenario_state(v)
    if rules is None:
        return game_state(v[0], v[1], TABLE_O, TABLE_X, TABLE_ARROWS)
    return game_state(v[0], v[1], TABLE_O, TABLE_X, TABLE_ARROWS, rules=rules)


def key(o, x, spec, seed, variant):
    return json.dumps([o, x, spec, seed, variant])


def play(o_level, x_level, spec, seed, variant='default', budget_s=2.0):
    from . import board as B
    from . import rules_config as RC
    from .computer import Computer, BUDGET, pass_risk
    from .resolve import apply, ChanceNode, sample
    from .scoring import score, contest_options, shot_points
    BUDGET['active'] = budget_s
    rules = RC.with_rules(late_closeout=True) if variant == 'late_closeout' else None
    s = start_state(spec, rules)
    pols = {'O': Computer('O', o_level, seed=seed), 'X': Computer('X', x_level, seed=seed)}
    rng = random.Random(seed * 1009 + 7)
    st = Counter()
    pend = None                                   # the pass in the air: clean when thrown?
    think = {'O': [], 'X': []}
    t0 = time.time()
    for _ in range(400):
        if s.stage == 'over':
            break
        side = 'O' if (s.stage in ('target', 'pick', 'forced') or (s.side == 'O' and s.stage == 'play')) else 'X'
        t1 = time.time()
        a = pols[side].choose(s)
        think[side].append(time.time() - t1)
        if s.stage == 'contest':
            two_three = 'three' if shot_points(s.o[s.ball]) == 3 else 'two'
            st['shots'] += 1
            st['shots_' + two_three] += 1
            if not [o for o in contest_options(s, s.ball, s.shot, s.forced) if o.defender >= 0]:
                st['no_contester'] += 1
                st['no_contester_' + two_three] += 1
        if a.side == 'O' and s.stage == 'play' and a.kind == 'pass':
            info = pass_risk(s, a.piece, a.target)
            clean = bool(info and info['clean'])
            st['passes'] += 1
            st['passes_clean'] += clean
            pend = dict(clean=clean)
        node = apply(s, a)
        while isinstance(node, ChanceNode):
            nxt, lab = sample(node, rng)
            what = node.what or ''
            if what.startswith('Pass '):
                st['icpt_tried'] += 1
                if lab == 'failure':
                    st['icpt_won'] += 1
                if pend is not None and not pend['clean']:
                    st['contested_resolved'] += 1
                    st['contested_completed'] += lab == 'success'
                pend = None
            elif what.startswith('Contest foul'):
                st['foul_rolls'] += 1
                if lab == 'foul':
                    st['fouls'] += 1
                    st['fouls_' + ('three' if shot_points(s.o[s.ball]) == 3 else 'two')] += 1
            elif what.startswith('Dribble') and 'Steal' in what:
                st['steal_tried'] += 1
                st['steal_won'] += lab == 'stolen'
            node = nxt
        if a.side == 'O' and node.stage != 'over' and node.phase == s.phase:
            spent = s.tok_o - node.tok_o
            if spent > 0:
                off = a.piece is not None and a.piece >= 0 and a.piece != s.ball
                st['tok_off_ball' if off else 'tok_on_ball'] += spent
        if pend is not None and not node.pending and node.stage != 'over' and a.kind != 'pass':
            if not pend['clean']:                   # a contested pass no one tried to intercept: completed
                st['contested_resolved'] += 1
                st['contested_completed'] += 1
            pend = None
        s = node
    sc = score(s) if s.stage == 'over' else None
    goals = [n['id'] for n in pols['O'].notes if n.get('event') == 'goal']
    return dict(o=o_level, x=x_level, spec=spec, seed=seed, variant=variant, counts=dict(st),
                points=float(sc.total) if sc else None, goals=goals,
                think_max={k: round(max(v or [0]), 2) for k, v in think.items()},
                think_mean={k: round(sum(v) / len(v), 3) if v else 0 for k, v in think.items()},
                wall=round(time.time() - t0, 1))


def _job(args):
    return args, play(*args)


def jobs(random_n=4, seeds=(1, 2), variant=True):
    out = []
    for sp in starts(random_n):
        for sd in seeds:
            for o, x in PAIRS:
                out.append((o, x, sp, sd, 'default'))
    if variant:
        for sp in starts(random_n):
            for sd in seeds:
                out.append(('allstar', 'allstar', sp, sd, 'late_closeout'))
    return out


def run(store='sim3i.json', workers=3, random_n=4, seeds=(1, 2), variant=True, limit=None):
    path = os.path.join(RESULTS, store)
    done = json.load(open(path)) if os.path.exists(path) else {}
    todo = [j for j in jobs(random_n, seeds, variant) if key(*j) not in done]
    if limit:
        todo = todo[:limit]
    t0 = time.time()
    print(f'{len(done)} done, {len(todo)} to run', flush=True)
    with ProcessPoolExecutor(workers) as ex:
        futs = [ex.submit(_job, j) for j in todo]
        for k, f in enumerate(as_completed(futs), 1):
            args, r = f.result()
            done[key(*args)] = r
            with open(path + '.tmp', 'w') as fh:
                json.dump(done, fh)
            os.replace(path + '.tmp', path)
            el = time.time() - t0
            print(f'{k}/{len(todo)} {args[0]} v {args[1]} {args[2]} s{args[3]} {args[4]}: {r["points"]} '
                  f'({r["wall"]}s; {el / k * (len(todo) - k) / 60:.0f} min left)', flush=True)
    return done


def summary(rows):
    """The comparison table: per pairing (and variant), the step 3i figures."""
    groups = {}
    for r in rows:
        groups.setdefault((r['variant'], r['o'], r['x']), []).append(r)
    out = {}
    for g, rs in sorted(groups.items()):
        c = Counter()
        for r in rs:
            c.update(r['counts'])
        n = len(rs)
        pts = [r['points'] for r in rs if r['points'] is not None]
        tok = c['tok_off_ball'] + c['tok_on_ball']
        div = lambda a, b: round(a / b, 3) if b else None
        gm = Counter(x for r in rs for x in r.get('goals', []))
        out['|'.join(g)] = dict(
            n=n, mean_points=round(sum(pts) / len(pts), 2) if pts else None,
            off_ball_token_share=div(c['tok_off_ball'], tok),
            clean_pass_share=div(c['passes_clean'], c['passes']), passes_per_poss=div(c['passes'], n),
            contested_completion=div(c['contested_completed'], c['contested_resolved']),
            contested_passes=c['contested_resolved'],
            interceptions_per_100=div(100 * c['icpt_won'], n), steals_per_100=div(100 * c['steal_won'], n),
            foul_share=div(c['fouls'], c['shots']), foul_share_two=div(c['fouls_two'], c['shots_two']),
            foul_share_three=div(c['fouls_three'], c['shots_three']),
            no_contester_share=div(c['no_contester'], c['shots']),
            no_contester_three=div(c['no_contester_three'], c['shots_three']), shots=c['shots'],
            goal_mix=dict(gm.most_common(8)),
            think_max={k: max(r['think_max'][k] for r in rs) for k in ('O', 'X')})
    return out


def estimate(n=3, workers=3):
    """Time a few possessions and project the whole run."""
    js = jobs()
    sample_jobs = [js[i] for i in range(0, len(js), max(1, len(js) // n))][:n]
    t0 = time.time()
    with ProcessPoolExecutor(workers) as ex:
        walls = [r['wall'] for _, r in ex.map(_job, sample_jobs)]
    per = sum(walls) / len(walls)
    return dict(sample=walls, per_possession=round(per, 1), possessions=len(js),
                hours=round(per * len(js) / workers / 3600, 2), took=round(time.time() - t0, 1))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--store', default='sim3i.json')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--random', type=int, default=4)
    ap.add_argument('--seeds', type=int, nargs='+', default=[1, 2])
    ap.add_argument('--no-variant', action='store_true')
    ap.add_argument('--estimate', action='store_true')
    ap.add_argument('--limit', type=int)
    a = ap.parse_args()
    if a.estimate:
        print(estimate(workers=a.workers))
    else:
        run(a.store, a.workers, a.random, tuple(a.seeds), not a.no_variant, a.limit)
