"""Step 17: learned judgement. The driver for stage 0 (measure properly), stage 1 (learn the weights) and stage 2
(learn which moves to consider). The possessions are played by tools/playout.js (the app's own engine), split over
the cores; this file makes the jobs, gathers the results and does the statistics.

  python3 tools/learn_17.py starts                      the stored possession starts and positions -> runs/step17/pool.json
  python3 tools/learn_17.py throughput                  this machine's possessions per core-hour, by rollout policy
"""
import json
import math
import os
import random
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
RUN = os.path.join(ROOT, 'docs', 'runs', 'step17')
WORK = os.environ.get('LEARN17_WORK', os.path.join(RUN, 'work'))       # big intermediate files (not committed)
CORES = int(os.environ.get('LEARN17_CORES', 4))


def profiles():
    cfg = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))
    return {lv: dict(cfg['profiles'][lv], name=lv) for lv in ('rookie', 'starter', 'allstar')}


def policy(level='allstar', depth=2, noise=0.0, **switches):
    """An engine as the playout tool reads it: a level's settings, the look-ahead, exploration noise, the switches."""
    return dict(profile=profiles()[level], depth=depth, noise=noise, set=switches)


def run_jobs(kind, positions, contexts, chunks=None, **job):
    """Split the positions over the cores, run tools/playout.js on each part, and gather the rows in order."""
    os.makedirs(WORK, exist_ok=True)
    n = chunks or CORES
    # every position gets its own dice and noise (its place in the list), so positions are independent of each other;
    # the same position always gets the same, so engines and candidate turns are compared on common dice
    positions = [dict(p, seed=p.get('seed', 104729 * (i + 1))) for i, p in enumerate(positions)]
    parts = [positions[k::n] for k in range(n)]
    procs, tag = [], f'{kind}_{os.getpid()}_{int(time.time() * 1000) % 100000}'
    for k, part in enumerate(parts):
        if not part:
            continue
        jf, of = os.path.join(WORK, f'{tag}_{k}.job.json'), os.path.join(WORK, f'{tag}_{k}.out.json')
        json.dump(dict(kind=kind, positions=part, contexts=contexts, **job), open(jf, 'w'))
        procs.append((subprocess.Popen(['node', '--max-old-space-size=2048', os.path.join(HERE, 'playout.js'), jf, of]), jf, of))
    rows, seconds = [], 0.0
    for p, jf, of in procs:
        if p.wait() != 0:
            raise RuntimeError(f'playout failed: {jf}')
        o = json.load(open(of))
        rows += o['rows']
        seconds += o['seconds']
        os.remove(jf)
        os.remove(of)
    return rows, seconds


def load_pool():
    return json.load(open(os.path.join(RUN, 'pool.json')))


def cmd_starts():
    """The stored Senior Pro possessions (step 3n seeds): each possession's start, and every play position in it."""
    import relative_average as RA
    from playmaker_engine import jsbridge, rules_config as RC
    contexts, seen, starts, positions = [], {}, [], []
    for age, std, r in RA.rows():
        if (age, std) != ('senior', 'pro') or r.get('format', 'digital') != 'digital':
            continue
        rules = RC.with_rules(digital=True)
        off, dfn = RA.team_of(r['off'], age, std), RA.team_of(r['dfn'], age, std)
        first = True
        for enc in r['snapshots']:
            if not enc.startswith('play:'):
                continue
            s = RA.decode(enc, off, dfn, rules)
            s.ctx.levels_key = (age, std)
            ctx = json.dumps(jsbridge.ctx_json(s.ctx), sort_keys=True)
            if ctx not in seen:
                seen[ctx] = len(contexts)
                contexts.append(json.loads(ctx))
            row = dict(id=f'seed{len(positions)}', state=jsbridge.state_json(s), ctx=seen[ctx])
            positions.append(row)
            if first and enc.startswith('play:O') and s.clock == RC.START_CLOCK:
                starts.append(dict(row, id=f'start{len(starts)}'))
            first = False
    os.makedirs(RUN, exist_ok=True)
    json.dump(dict(contexts=contexts, starts=starts, positions=positions), open(os.path.join(RUN, 'pool.json'), 'w'))
    print(len(contexts), 'team pairings,', len(starts), 'possession starts,', len(positions), 'positions')


def cmd_throughput():
    """Possessions per core-hour for a few rollout policies, from 12 starts each played 4 times on one core."""
    pool = load_pool()
    res = {}
    for name, pol in (('rookie, 1 team turn', policy('rookie', 1, 1.0)), ('starter, 1 team turn', policy('starter', 1, 1.0)),
                      ('all-star, 1 team turn', policy('allstar', 1, 1.0)), ('all-star, 1 pair', policy('allstar', 2, 1.0))):
        rows, secs = run_jobs('selfplay', pool['starts'][:12], pool['contexts'], chunks=1, n=4, seed=1, policies=dict(O=pol, X=pol))
        n = len(rows)
        res[name] = dict(possessions=n, seconds=round(secs, 1), per_possession=round(secs / n, 3),
                         per_core_hour=round(3600 * n / secs), mean_points=round(sum(r['points'] for r in rows) / n, 2),
                         positions_per_possession=round(sum(len(r['states']) for r in rows) / n, 1))
        print(name, res[name], flush=True)
    json.dump(res, open(os.path.join(RUN, 'throughput.json'), 'w'), indent=1)


def mean_ci(v):
    n = len(v)
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1)) if n > 1 else 0.0
    return m, sd, 1.96 * sd / math.sqrt(n)


def wilson(k, n):
    if n == 0:
        return 0.0, 0.0, 0.0
    p, z = k / n, 1.96
    c, h = (p + z * z / (2 * n)) / (1 + z * z / n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return p, c - h, c + h


def h2h_stats(rows, delta=1.0):
    """Paired possessions: d = engine A's points on offence less engine B's, same start and dice. Per possession pair:
    the mean with its 95% interval, the win rate with a Wilson interval, how many pairs a gain of `delta` points needs,
    and where a sequential test (no difference against a gain of delta, 5% each way) would have stopped."""
    d = [r['a_offence'] - r['b_offence'] for r in rows]
    m, sd, ci = mean_ci(d)
    wins, losses = sum(x > 0 for x in d), sum(x < 0 for x in d)
    p, lo, hi = wilson(wins, wins + losses)
    llr, stop, bound = 0.0, None, math.log(0.95 / 0.05)
    for k, x in enumerate(d):
        llr += (delta / (sd * sd)) * (x - delta / 2) if sd else 0.0
        if stop is None and abs(llr) >= bound:
            stop = dict(pairs=k + 1, verdict='a gain' if llr > 0 else 'no gain')
    return dict(pairs=len(d), mean_difference=round(m, 3), interval=[round(m - ci, 3), round(m + ci, 3)], sd=round(sd, 2),
                wins=wins, losses=losses, ties=len(d) - wins - losses, win_rate=round(p, 3), win_interval=[round(lo, 3), round(hi, 3)],
                pairs_needed={str(g): round((1.96 * sd / g) ** 2) for g in (0.5, 1.0, 2.0)}, sequential_stop=stop,
                a_points=round(sum(r['a_offence'] for r in rows) / len(rows), 2),
                b_points=round(sum(r['b_offence'] for r in rows) / len(rows), 2),
                decisions_per_possession=round(sum(r['decisions'] for r in rows) / len(rows) / 2, 1))


ENGINES = {         # the engines the harness knows, by name
    'default': lambda: policy('allstar', 2, 0.5),
    'default_b': lambda: policy('allstar', 2, 0.5),
    'learned': lambda: policy('allstar', 2, 0.5, learned=True),
    'learned_prior': lambda: policy('allstar', 2, 0.5, learned=True, prior=True),
    'goals': lambda: policy('allstar', 2, 0.5, goals=True),
    'data': lambda: policy('rookie', 2, 1.0),            # the cheap policy that plays the labelling possessions
}


def cmd_h2h(a, b, starts='40', n='1', seed='1', out=None):
    """Head to head: engine a against engine b, from the stored possession starts, the sides swapped."""
    pool = load_pool()
    t0 = time.time()
    rows, secs = run_jobs('h2h', pool['starts'][:int(starts)], pool['contexts'], n=int(n), seed=int(seed), a=ENGINES[a](), b=ENGINES[b]())
    rep = dict(a=a, b=b, stats=h2h_stats(rows), core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1), rows=rows)
    json.dump(rep, open(out or os.path.join(RUN, f'h2h_{a}_vs_{b}.json'), 'w'))
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


def cmd_selfplay(name, engine='data', starts='160', n='4', seed='1'):
    """Possessions played by one engine against itself, every play position kept as a training row."""
    pool = load_pool()
    t0 = time.time()
    pol = ENGINES[engine]()
    rows, secs = run_jobs('selfplay', pool['starts'][:int(starts)], pool['contexts'], n=int(n), seed=int(seed), features=True,
                          policies=dict(O=pol, X=pol))
    pts = [r['points'] for r in rows]
    m, sd, ci = mean_ci(pts)
    os.makedirs(WORK, exist_ok=True)
    json.dump(dict(engine=engine, rows=rows), open(os.path.join(WORK, f'selfplay_{name}.json'), 'w'))
    rep = dict(engine=engine, possessions=len(rows), positions=sum(len(r['states']) for r in rows), mean_points=round(m, 2),
               interval=[round(m - ci, 2), round(m + ci, 2)], sd=round(sd, 2), no_score=sum(p == 0 for p in pts),
               decisions_per_possession=round(sum(r['decisions'] for r in rows) / len(rows), 1),
               core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1),
               per_core_hour=round(3600 * len(rows) / secs))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_{name}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


# ---- stage 1: learn the weights -----------------------------------------------------------------------------------------

WEIGHTS = os.path.join(ROOT, 'playmaker_engine', 'data', 'learned_weights.json')


def training_rows(names):
    """(possession key, phase 1..6, what is left to earn, today's reading of it, the readings) for every kept position.
    What is left to earn = the possession's end value less what was already earned at the position."""
    import numpy as np
    rows = []
    for name in names:
        d = json.load(open(os.path.join(WORK, f'selfplay_{name}.json')))
        for g, r in enumerate(d['rows']):
            for st in r['states']:
                clock, banked, hand = st[0], st[1], st[2]
                rows.append((f'{name}/{g}', min(6, max(1, (12 - clock) // 2 + 1)), r['value'] - banked, hand - banked, st[3:]))
    keys = sorted({r[0] for r in rows})
    kid = {k: i for i, k in enumerate(keys)}
    return (np.array([kid[r[0]] for r in rows]), np.array([r[1] for r in rows]), np.array([r[2] for r in rows], float),
            np.array([r[3] for r in rows], float), np.array([r[4] for r in rows], float), len(keys))


def ridge_fit(X, y, lam):
    """Per phase: standardise, then ridge with an intercept. Returns (mean, sd, intercept, weights)."""
    import numpy as np
    mu, sd = X.mean(0), X.std(0)
    sd = np.where(sd < 1e-9, 1.0, sd)
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * len(y) * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return mu, sd, float(y.mean()), w


def predict(model, ph, X):
    import numpy as np
    out = np.zeros(len(ph))
    for p, (mu, sd, b, w) in model.items():
        m = ph == p
        out[m] = b + ((X[m] - mu) / sd) @ w
    return out


def fit_model(g, ph, y, X, lam, groups=None):
    import numpy as np
    keep = np.ones(len(g), bool) if groups is None else np.isin(g, groups)
    return {p: ridge_fit(X[keep & (ph == p)], y[keep & (ph == p)], lam) for p in range(1, 7) if (keep & (ph == p)).sum() > 20}


def cmd_fit(names='pilot', write='no', lam=None):
    """Fit the per-phase weights to what possessions went on to earn. Held out by possession (5 folds): the fit's error
    against today's reading's error (as it stands, and straightened per phase), the learning curve, and, with
    write=yes, the weights file with a 20-model bootstrap spread on every weight."""
    import numpy as np
    from playmaker_engine.decide import FEATURES
    g, ph, y, hand, X, n_poss = training_rows(names.split(','))
    rng = np.random.default_rng(17)
    fold = rng.permutation(n_poss) % 5

    def cv(lam_, sub=None):
        pred = np.zeros(len(y))
        for k in range(5):
            train = np.where(fold != k)[0] if sub is None else np.intersect1d(np.where(fold != k)[0], sub)
            model = fit_model(g, ph, y, X, lam_, train)
            m = fold[g] == k
            pred[m] = predict(model, ph[m], X[m])
        return pred
    lams = [0.001, 0.01, 0.1, 1.0]
    errs = {lm: float(np.sqrt(np.mean((cv(lm) - y) ** 2))) for lm in lams}
    best = float(lam) if lam else min(errs, key=errs.get)
    pred = cv(best)
    straight = np.zeros(len(y))                    # today's reading, straightened per phase on the training folds
    for k in range(5):
        for p in range(1, 7):
            tr, te = (fold[g] != k) & (ph == p), (fold[g] == k) & (ph == p)
            if tr.sum() > 20 and te.sum():
                A = np.vstack([np.ones(tr.sum()), hand[tr]]).T
                c = np.linalg.lstsq(A, y[tr], rcond=None)[0]
                straight[te] = c[0] + c[1] * hand[te]
    rmse = lambda a: float(np.sqrt(np.mean((a - y) ** 2)))
    base = rmse(np.full(len(y), 0.0) + np.array([y[ph == p].mean() for p in ph]))

    def boot(a, b):                                # the gain of a over b in squared error, resampled by possession
        e = (b - y) ** 2 - (a - y) ** 2
        per = np.array([e[g == k].sum() for k in range(n_poss)])
        cnt = np.array([(g == k).sum() for k in range(n_poss)])
        r = np.random.default_rng(3)
        d = [per[i].sum() / cnt[i].sum() for i in (r.integers(0, n_poss, n_poss) for _ in range(400))]
        return [round(float(np.percentile(d, 2.5)), 2), round(float(np.percentile(d, 97.5)), 2)]
    curve = {}
    for frac in (0.1, 0.25, 0.5, 1.0):
        sub = np.where(rng.permutation(n_poss) < frac * n_poss)[0]
        curve[str(int(frac * n_poss))] = round(rmse(cv(best, sub)), 3)
    rep = dict(possessions=n_poss, positions=len(y), by_phase={str(p): int((ph == p).sum()) for p in range(1, 7)},
               ridge_by_strength={str(k): round(v, 3) for k, v in errs.items()}, strength=best,
               held_out_error=dict(learned=round(rmse(pred), 3), todays_reading=round(rmse(hand), 3),
                                   todays_reading_straightened=round(rmse(straight), 3), phase_average_only=round(base, 3)),
               learned_gain_over_straightened_reading=boot(pred, straight), learned_gain_over_phase_average=boot(pred, np.array([y[ph == p].mean() for p in ph])),
               learning_curve=curve)
    model = fit_model(g, ph, y, X, best)
    boots = []
    r = np.random.default_rng(5)
    for _ in range(20):
        pick = r.integers(0, n_poss, n_poss)
        idx = np.concatenate([np.where(g == k)[0] for k in pick])
        boots.append({p: ridge_fit(X[idx][ph[idx] == p], y[idx][ph[idx] == p], best) for p in model})
    names_ = [f[0] for f in FEATURES]
    phases = {}
    for p, (mu, sd, b, w) in model.items():
        spread = np.std([bt[p][3] * sd / bt[p][1] for bt in boots], 0)      # each resample's weights, in this model's units
        phases[str(p)] = dict(intercept=b, mean=[float(v) for v in mu], sd=[float(v) for v in sd], weights=[float(v) for v in w],
                              weights_spread=[float(v) for v in spread], positions=int((ph == p).sum()))
    rep['weights'] = {p: {names_[i]: [round(v['weights'][i], 3), round(v['weights_spread'][i], 3)] for i in range(len(names_))}
                      for p, v in phases.items()}
    rep['near_zero'] = sorted({names_[i] for i in range(len(names_))
                               if all(abs(v['weights'][i]) < 1.96 * v['weights_spread'][i] for v in phases.values())})
    json.dump(rep, open(os.path.join(RUN, f'fit_{names.replace(",", "_")}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'weights'}, indent=1))
    if write == 'yes':
        import hashlib
        body = dict(version=1, features=names_, form='per phase: intercept + sum of weight x (reading - mean) / sd, in the order given',
                    target='what the possession went on to earn beyond what was already earned', trained_on=dict(
                        runs=names.split(','), possessions=n_poss, positions=len(y), ridge_strength=best), phases=phases)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(WEIGHTS, 'w'), indent=1)
        print('wrote', WEIGHTS, body['hash'])


def hand_boards():
    """The 19 hand boards' decisions (boards 1 to 16, every copy, and C2) as playout positions."""
    from playmaker_engine import exam as EX, jsbridge
    contexts, seen, positions = [], {}, []
    jobs = [(n, EX.POSITIONS[n - 1]()[1]) for n in range(1, 17)] + [('C2', EX.c2()[1])]
    for n, b in jobs:
        for k, s in (b.items() if isinstance(b, dict) else [('', b)]):
            ctx = json.dumps(jsbridge.ctx_json(s.ctx), sort_keys=True)
            if ctx not in seen:
                seen[ctx] = len(contexts)
                contexts.append(json.loads(ctx))
            positions.append(dict(id=f'board {n}{(" " + str(k)) if k else ""}', state=jsbridge.state_json(s), ctx=seen[ctx]))
    return positions, contexts


def cmd_measure_boards(n='16', top='3'):
    """The hand boards measured by playing them out: today's computer's best turns (1 pair ahead), each played out n
    times by the cheap policy with the same dice; each turn's mean and standard error, and the gap to the best."""
    positions, contexts = hand_boards()
    t0 = time.time()
    found, s1 = run_jobs('search', positions, contexts, policies=dict(default=policy('allstar', 2)))
    by = {r['id']: r for r in found}
    for p in positions:
        r = by[p['id']]
        sign = 1 if r['side'] == 'O' else -1
        ranked = sorted(r['by']['default']['results'], key=lambda x: -sign * x[0])
        p['turns'] = [t for _, t in ranked[:int(top)]]
        p['search'] = [round(v, 2) for v, _ in ranked[:int(top)]]
        p['side'] = r['side']
    pol = ENGINES['data']()
    rows, s2 = run_jobs('rollout', positions, contexts, n=int(n), seed=7, keep=True, policies=dict(O=pol, X=pol))
    by = {r['id']: r for r in rows}
    out = []
    for p in positions:
        sign = 1 if p['side'] == 'O' else -1
        ts = by[p['id']]['turns']
        best = max(range(len(ts)), key=lambda k: sign * ts[k]['mean'])
        row = dict(board=p['id'], side=p['side'], turns=[])
        for k, t in enumerate(ts):
            d = [sign * (x - y) for x, y in zip(ts[best]['values'], t['values'])]          # paired: the same dice
            m, sd, ci = mean_ci(d) if len(d) > 1 else (0.0, 0.0, 0.0)
            row['turns'].append(dict(turn=t['turn'], search_value=p['search'][k], measured=round(t['mean'], 2), se=round(t['se'], 2),
                                     behind_best=round(m, 2), behind_interval=round(ci, 2), computer_pick=k == 0, measured_best=k == best))
        row['pick_is_measured_best'] = best == 0
        row['pick_clearly_worse'] = row['turns'][0]['behind_best'] - row['turns'][0]['behind_interval'] > 0
        out.append(row)
    rep = dict(rollouts_per_turn=int(n), policy='data', core_hours=round((s1 + s2) / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1),
               pick_is_measured_best=sum(r['pick_is_measured_best'] for r in out), pick_clearly_worse=sum(r['pick_clearly_worse'] for r in out),
               boards=len(out), median_se=sorted(t['se'] for r in out for t in r['turns'])[len(out) * int(top) // 2], rows=out)
    json.dump(rep, open(os.path.join(RUN, 'hand_boards_measured.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


def exam_positions(extra=130):
    """The outcome exam's positions: the hand boards' 22 decisions, and stored self-play positions spread evenly over
    the phases (a fixed draw). Each is tagged with its source, phase and the side to act."""
    hb, hctx = hand_boards()
    pool = load_pool()
    rnd = random.Random(1717)
    by_phase = {}
    for p in pool['positions']:
        by_phase.setdefault(min(6, (12 - p['state']['clock']) // 2 + 1), []).append(p)
    picked = []
    for ph in sorted(by_phase):
        picked += rnd.sample(by_phase[ph], min(len(by_phase[ph]), extra // 6 + 1))
    contexts = hctx + pool['contexts']
    out = [dict(p, source='hand board') for p in hb] + [dict(p, ctx=p['ctx'] + len(hctx), source='self-play') for p in picked[:extra]]
    for p in out:
        s = p['state']
        p['side'] = 'X' if s['stage'] in ('reaction', 'contest') else 'O' if s['stage'] in ('target', 'pick', 'forced') else s['side']
        p['phase'] = min(6, (12 - s['clock']) // 2 + 1)
    return out, contexts


def cmd_exam(engines='default,learned', n='4', extra='130'):
    """The outcome exam. From each position the engine under test plays the side to act to the end of the possession,
    against today's computer, n times with the same dice for every engine. An engine's mark on a position is the
    points it gains for its side (the offence's points, or their negative for the defence). Engines are compared
    position by position; the intervals come from resampling positions."""
    positions, contexts = exam_positions(int(extra))
    t0, secs, marks = time.time(), 0.0, {}
    for e in engines.split(','):
        marks[e] = {}
        for side in 'OX':
            part = [p for p in positions if p['side'] == side]
            pols = dict(O=ENGINES[e](), X=ENGINES['default']()) if side == 'O' else dict(O=ENGINES['default'](), X=ENGINES[e]())
            rows, s = run_jobs('rollout', part, contexts, n=int(n), seed=11, keep=True, policies=pols)
            secs += s
            for r in rows:
                v = r['turns'][0]['values']
                marks[e][r['id']] = [(x if side == 'O' else -x) for x in v]
    rnd = random.Random(5)
    ids = [p['id'] for p in positions]
    tag = {p['id']: p for p in positions}

    def boot(vals):
        m = sum(vals) / len(vals)
        bs = sorted(sum(rnd.choice(vals) for _ in vals) / len(vals) for _ in range(1000))
        return [round(m, 2), round(bs[25], 2), round(bs[975], 2)]
    rep = dict(positions=len(ids), seeds=int(n), opponent='default', core_hours=round(secs / 3600, 2),
               wall_minutes=round((time.time() - t0) / 60, 1), engines={}, against_default={})
    mean = lambda e, i: sum(marks[e][i]) / len(marks[e][i])
    for e in marks:
        rep['engines'][e] = dict(mark=boot([mean(e, i) for i in ids]))
        if e != 'default' and 'default' in marks:
            d = {i: mean(e, i) - mean('default', i) for i in ids}
            groups = dict(all=ids, hand_boards=[i for i in ids if tag[i]['source'] == 'hand board'],
                          self_play=[i for i in ids if tag[i]['source'] == 'self-play'],
                          offence_to_act=[i for i in ids if tag[i]['side'] == 'O'], defence_to_act=[i for i in ids if tag[i]['side'] == 'X'],
                          **{f'phase_{k}': [i for i in ids if tag[i]['phase'] == k] for k in range(1, 7)})
            rep['against_default'][e] = {g: dict(positions=len(v), gain=boot([d[i] for i in v]),
                                                 better=sum(d[i] > 0 for i in v), worse=sum(d[i] < 0 for i in v))
                                         for g, v in groups.items() if v}
    rep['rows'] = {i: dict(source=tag[i]['source'], phase=tag[i]['phase'], side=tag[i]['side'],
                           **{e: round(mean(e, i), 2) for e in marks}) for i in ids}
    json.dump(rep, open(os.path.join(RUN, f'exam_{engines.replace(",", "_")}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


def cmd_speed(engines='default,learned'):
    """The time to finish 1 pair at each level on the hand boards' 22 decisions (one warm engine), by engine: the
    median, 9 in 10 and the slowest, against docs/SPEED_BUDGET.md (the phone is the assumed quarter speed)."""
    positions, contexts = hand_boards()
    target = dict(rookie=(0.3, 1.0), starter=(1.0, 2.0), allstar=(2.5, 3.0))
    rep = {}
    for e in engines.split(','):
        pols = {lv: dict(ENGINES[e](), profile=profiles()[lv], noise=0.0) for lv in target}
        run_jobs('search', positions[:6], contexts, chunks=1, policies=pols)
        rows, _ = run_jobs('search', positions + positions, contexts, chunks=1, policies=pols)
        rows = rows[len(positions):]                      # the second pass: the engine is warm
        rep[e] = {}
        for lv in target:
            v = sorted(r['by'][lv]['seconds'] for r in rows)
            p90 = v[int(0.9 * (len(v) - 1) + 0.5)]
            rep[e][lv] = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(p90, 3), slowest=round(v[-1], 3),
                              desktop_target=target[lv][0], fits_desktop=p90 <= target[lv][0],
                              phone=round(4 * p90, 2), phone_target=target[lv][1], fits_phone=4 * p90 <= target[lv][1])
    json.dump(rep, open(os.path.join(RUN, f'speed_{engines.replace(",", "_")}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
