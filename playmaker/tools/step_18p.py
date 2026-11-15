"""Step 18p (D-196): fix what the computer can't do, in the plan's order (docs/plans/COMPUTER_FIX_PLAN.md).

  python3 tools/step_18p.py explore <tag> <n> [seed] [rate] [learned]   play for the fit: at most one turn a possession is
                                                                        drawn from all the turns the search weighed
  python3 tools/step_18p.py fit <write|no> <tag>[,<tag>...]             the reading's parts, each given its worth by what
                                                                        positions went on to earn (held out by possession)
  python3 tools/step_18p.py checks [learned]                            the design checks on Shaun's board: the reading of
                                                                        each named position, and what the search chooses
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18p')
os.environ.setdefault('SENSE_18N', '1')
import step_18o as O                                    # noqa: E402
T, L, G, RUN, WORK, tally = O.T, O.L, O.G, O.RUN, O.WORK, O.tally
ROOT = os.path.dirname(HERE)
RULES = dict(T.RULES, zone='on')                         # the app's rules since this step: the zone on (D-196)


def cmd_explore(tag, n='160', seed='1', rate='0.125', learned='no'):
    """All-Star against All-Star from the stored starts under the app's rules, every open-play position kept with the
    reading's parts. At most once a possession a decision takes a turn drawn at random from all the turns the search
    weighed (rate: the chance at each open-play decision until it has happened)."""
    pl = G.pool()
    T.pool_is_current(pl)
    sw = dict(learned=True) if learned == 'learned' else {}
    pol = dict(L.policy('allstar', 2, L.profiles()['allstar']['noise'], **sw), explore=float(rate))
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), features=True, stances=True, boards=True,
                            policies=dict(O=pol, X=pol), rules=RULES, fouls=T.FOULS)
    json.dump(dict(size=tag, rows=rows, zone=True, explore=float(rate), learned=learned == 'learned'), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'play for the fit ({tag}, {n} possessions, a drawn turn at rate {rate}{", the fitted reading" if sw else ""})', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    drawn = sum(1 for r in rows if r.get('drawn'))
    clean = sum(len(r['reads']) - r['clean_from'] for r in rows)
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)], '| a turn was drawn in', drawn, '| positions', sum(len(r['reads']) for r in rows), 'usable', clean)


def training_rows(tags):
    """(possession, phase, what was left to earn, the hand reading of it, the parts) for every usable position: one with
    no drawn turn after it, so that what it went on to earn is the computer's own play from there."""
    import numpy as np
    g, ph, y, hand, X = [], [], [], [], []
    k = 0
    for tag in tags:
        for r in json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']:
            k += 1
            for st in r['reads'][r.get('clean_from', 0):]:
                clock, banked, h = st[0], st[1], st[2]
                g.append(k)
                ph.append(min(6, max(1, (12 - clock) // 2 + 1)))
                y.append(r['value'] - banked)
                hand.append(h - banked)
                X.append(st[4:])
    return np.array(g), np.array(ph), np.array(y, float), np.array(hand, float), np.array(X, float), k


def cmd_fit(write='no', tags=''):
    """Ridge per phase on the reading's parts, held out by possession (5 folds). Reports the held-out error against
    the hand reading straightened per phase and against the phase average alone, and each part's weight with its
    spread over 20 resamples. write: the weights go into learned_weights.json (the 'phases' block; the maps stay)."""
    import hashlib
    import numpy as np
    from playmaker_engine.decide import FEATURES
    tags = tags.split(',')
    g, ph, y, hand, X, n_poss = training_rows(tags)
    assert X.shape[1] == len(FEATURES), X.shape
    ids = np.unique(g)
    rng = np.random.default_rng(18)
    fold_of = dict(zip(ids, rng.permutation(len(ids)) % 5))
    fold = np.array([fold_of[i] for i in g])

    def fit(mask, lam):
        return {p: L.ridge_fit(X[mask & (ph == p)], y[mask & (ph == p)], lam) for p in range(1, 7) if (mask & (ph == p)).sum() > 40}

    def predict(model, m):
        out = np.array([y[ph == p].mean() if (ph == p).any() else 0.0 for p in ph[m]])
        for p, (mu, sd, b, w) in model.items():
            mm = ph[m] == p
            out[mm] = b + ((X[m][mm] - mu) / sd) @ w
        return out

    def cv(lam):
        pred = np.zeros(len(y))
        for k in range(5):
            pred[fold == k] = predict(fit(fold != k, lam), fold == k)
        return pred
    rmse = lambda a: float(np.sqrt(np.mean((a - y) ** 2)))
    errs = {lam: rmse(cv(lam)) for lam in (0.001, 0.01, 0.1, 1.0)}
    best = min(errs, key=errs.get)
    pred = cv(best)
    straight = np.zeros(len(y))
    for k in range(5):
        for p in range(1, 7):
            tr, te = (fold != k) & (ph == p), (fold == k) & (ph == p)
            if te.sum():
                if tr.sum() > 40:
                    c = np.linalg.lstsq(np.vstack([np.ones(tr.sum()), hand[tr]]).T, y[tr], rcond=None)[0]
                    straight[te] = c[0] + c[1] * hand[te]
                else:
                    straight[te] = y[tr].mean() if tr.sum() else 0.0
    avg = np.array([y[ph == p].mean() for p in ph])
    model = fit(np.ones(len(y), bool), best)
    boots = []
    for b in range(20):
        pick = rng.choice(ids, len(ids))
        idx = np.concatenate([np.where(g == i)[0] for i in pick])
        boots.append({p: L.ridge_fit(X[idx][ph[idx] == p], y[idx][ph[idx] == p], best) for p in model if (ph[idx] == p).sum() > 40})
    names = [f[0] for f in FEATURES]
    phases = {}
    for p, (mu, sd, b, w) in model.items():
        spread = np.std([bt[p][3] * sd / bt[p][1] for bt in boots if p in bt], 0)
        phases[str(p)] = dict(intercept=b, mean=[float(v) for v in mu], sd=[float(v) for v in sd], weights=[float(v) for v in w],
                              weights_spread=[float(v) for v in spread], positions=int((ph == p).sum()))
    rep = dict(runs=tags, possessions=n_poss, positions=len(y), by_phase={str(p): int((ph == p).sum()) for p in range(1, 7)}, ridge_strength=best,
               held_out_error=dict(fitted_parts=round(rmse(pred), 3), hand_reading_straightened=round(rmse(straight), 3), phase_average_only=round(rmse(avg), 3)),
               worth_per_point={p: {names[i]: [round(v['weights'][i] / v['sd'][i], 3), round(v['weights_spread'][i] / v['sd'][i], 3)] for i in range(len(names))}
                                for p, v in phases.items()})
    json.dump(rep, open(os.path.join(RUN, f'fit_{"_".join(tags)}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'worth_per_point'}))
    for p, d in rep['worth_per_point'].items():
        print(' phase', p, ' '.join(f'{k}={v[0]:+.2f}({v[1]:.2f})' for k, v in d.items()))
    if write == 'write':
        body = json.load(open(L.WEIGHTS))
        for p in range(1, 7):                       # a phase with too few positions borrows the nearest fitted phase
            if str(p) not in phases:
                near = min(phases, key=lambda q: abs(int(q) - p))
                phases[str(p)] = dict(phases[near], borrowed_from=near)
        body.update(features=names, phases=phases, trained_on=dict(runs=tags, possessions=n_poss, positions=len(y), ridge_strength=best,
                                                                   how='play with at most one drawn turn a possession; positions after it only (step 18p, D-196)'))
        body.pop('hash', None)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote', body['hash'])


# ---- the design checks on Shaun's board, by the reading and the search (stage 1) --------------------------------------

def _after_beat(x4='B4', a4='SW', x5='P2', a5='NE', zone=True):
    """Shaun's board after the point guard has beaten X1 and X1's reach has missed: the offence to act."""
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    st = O._beaten(O.shaun_state(O.HIS[0][:3] + [x4, x5], O.HIS[1][:3] + [a4, a5], zone=zone))
    reach = next((z for z in legal_actions(st) if z.kind == 'steal' and z.piece == 0), None)
    if reach is not None:                               # under the zone the beaten defender has no reach here: the defence just waits
        n = apply(st, reach)
        fouls = st.fouls
        while isinstance(n, ChanceNode):
            n = next(sub for p_, lab, sub in n.outcomes if isinstance(sub, ChanceNode) or (sub.stage != 'over' and sub.fouls == fouls))
        st = n
    while st.side == 'X' and st.stage == 'play':
        st = apply(st, next(z for z in legal_actions(st) if z.kind in ('pause', 'end_turn')))
    return st


def _act(s, kind, piece=None, dest=None, side=None):
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    from playmaker_engine import board as B
    a = next(a for a in legal_actions(s) if a.kind == kind and (piece is None or a.piece == piece) and (dest is None or B.sq(a.dest) == dest))
    return apply(s, a)


class Eng:
    """The JavaScript engine, asked directly (the search and the reading as the app runs them)."""

    def __init__(self, learned):
        from playmaker_engine.jsbridge import NodeEngine
        self.e = NodeEngine().install()
        self.e.call('setLearned', 'true' if learned else 'false')
        self.learned = learned

    def search(self, s, depth=2, budget=120):
        from playmaker_engine import agent as AG, jsbridge
        p = dict(AG.profile('allstar'), noise=0.0, depth=[depth, depth])
        out = json.loads(AG.JS['search'](json.dumps(dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=p, budget=budget, max_depth=depth, stale=None))))
        sign = 1 if s.side == 'O' else -1
        return sorted(((v, [str(jsbridge.action_from(a)) for a in t]) for v, t in out['results']), key=lambda r: -sign * r[0])

    def reading(self, s):
        """The reading of a position as the search's horizon sees it: a search with no look-ahead is not offered, so
        the Python reading is used; it is the same reading (the two engines are checked equal)."""
        from playmaker_engine.decide import Read, CONFIG
        CONFIG['eval']['learned'] = self.learned
        import playmaker_engine.decide as D
        D._LEARNED.clear()
        try:
            return Read(s).leaf()
        finally:
            CONFIG['eval']['learned'] = False


def cmd_checks(which='hand'):
    """The design checks that the reading and the search can answer without a play-out. which: 'hand' (the reading as
    it was: the best look this turn, through the fitted map) or 'learned' (each part with its fitted worth)."""
    from playmaker_engine import board as B
    eng = Eng(which == 'learned')
    out = {}
    rd = lambda s: round(eng.reading(s), 1)
    top = lambda s, depth=2: eng.search(s, depth)

    # check 1 and 4: the open lane after the beat
    for label, kw in (('lane open (X4, X5 next to their men)', {}), ('help in the lane (X4, X5 on H5, J5)', dict(x4='H5', a4='N', x5='J5', a5='N'))):
        a = _after_beat(**kw)
        spr = _act(a, 'sprint', 0, 'I6')
        res = top(a)
        drive = [r for r in res if r[1] and r[1][0].startswith('O1 Sprint')]
        ent = dict(reading_before=rd(a), reading_after_the_sprint_into_the_lane=rd(spr), search_choice=res[0][1], search_value=round(res[0][0], 1),
                   best_sprint_turn=drive[0][1] if drive else None, best_sprint_value=round(drive[0][0], 1) if drive else None,
                   offence_takes_the_lane=bool(res[0][1] and res[0][1][0].startswith('O1 Sprint')))
        # the defence to act with the ball handler in the lane (the offence's turn ended after the Sprint)
        d = spr
        while d.side == 'O' and d.stage == 'play':
            d = _act(d, 'end_turn')
        dres = top(d)
        ent['defence_answer_to_the_sprint'] = dres[0][1]
        ent['defence_answer_value'] = round(dres[0][0], 1)
        ent['defence_pause_value'] = next((round(v, 1) for v, t in dres if t and t[0] in ('X Pause', 'X End turn')), None)
        out[f'check 1 and 4, {label}'] = ent
    # check 2: square in front, beside, behind (the start of the possession, the offence to act, and the defence to act after a wait)
    sq = {}
    for name, (q, d) in (('square in front (I10, arrow on him)', ('I10', 'N')), ('in front, arrow off him (I10 facing E)', ('I10', 'E')),
                         ('diagonal, arrow on him (J10, his game)', ('J10', 'NW')), ('beside (J11 facing W, on him)', ('J11', 'W')), ('behind (I12 facing S, on him)', ('I12', 'S'))):
        s0 = O.shaun_state([q] + O.HIS[0][1:], [d] + O.HIS[1][1:], zone=True)
        res = top(s0)
        sq[name] = dict(reading=rd(s0), search_value=round(res[0][0], 1), offence_choice=res[0][1])
    out['check 2, where X1 stands'] = sq
    # check 3: an arrow that walls the drive against one that covers nothing (X1 on J10)
    ar = {}
    for name, d in (('arrow across the lane (facing W)', 'W'), ('arrow on him (NW)', 'NW'), ('arrow away from everything (facing E)', 'E')):
        s0 = O.shaun_state(['J10'] + O.HIS[0][1:], [d] + O.HIS[1][1:], zone=True)
        res = top(s0)
        ar[name] = dict(reading=rd(s0), search_value=round(res[0][0], 1), offence_choice=res[0][1])
    out['check 3, X1\'s arrow'] = ar
    # check 3 again: an off-ball arrow on a passing lane the offence wants against one on his man (X3, whose man is the best shooter)
    pa = {}
    for name, d in (('X3 arrow on his man (N)', 'N'), ('X3 arrow on the pass to his man (NW)', 'NW'), ('X3 arrow away (SE)', 'SE')):
        s0 = O.shaun_state(O.HIS[0], O.HIS[1][:2] + [d] + O.HIS[1][3:], zone=True)
        res = top(s0)
        pa[name] = dict(reading=rd(s0), search_value=round(res[0][0], 1))
    out['check 3, an off-ball arrow'] = pa
    json.dump(out, open(os.path.join(RUN, f'checks_{which}.json'), 'w'), indent=1)
    print(json.dumps(out, indent=1))


def play(named, copies=16, learned=False, seed=1, what='play-outs'):
    """Play each named position out `copies` times, All-Star against All-Star, the app's rules (the zone on), the same
    dice copy by copy; learned: both sides play with the fitted reading. Rows are filed by the name they carry."""
    from playmaker_engine import jsbridge
    ctx = jsbridge.ctx_json(named[0][1].ctx)
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **(dict(learned=True) if learned else {}))
    positions = [dict(id=name, state=jsbridge.state_json(s), ctx=0, seed=104729 * (k + 1) + 7919 * seed) for name, s in named for k in range(copies)]
    rows, secs = L.run_jobs('trace', positions, [ctx], n=1, seed=seed, stances=True, policies=dict(O=pol, X=pol), rules=RULES, fouls=T.FOULS)
    tally(f'{what} ({len(named)} positions, {copies} each{", the fitted reading" if learned else ""})', secs)
    out = {name: [] for name, _ in named}
    for r in rows:
        out[r['id']].append(r)
    assert all(len(v) == copies for v in out.values())
    return out


def _summary(rows):
    import collections
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    ends = collections.Counter(((r.get('result') or {}).get('shot_type') or (r.get('result') or {}).get('kind')) for r in rows)
    first = collections.Counter((e[2] + (str(e[4] + 1) if e[4] >= 0 else ''), e[3], e[6]) for r in rows for e in r['events'][:1])
    return dict(mean=round(m, 1), low=round(m - ci, 1), high=round(m + ci, 1), ends=dict(ends), first_action=[[' '.join(str(x) for x in k if x), v] for k, v in first.most_common(3)],
                points=[r['points'] for r in rows])


def cmd_played(tag, learned='no', copies='16'):
    """Check 1 played, by forced lines: Shaun's board after the beat, with the lane open and with help in it. The
    offence by its own choice; the offence made to Sprint into the lane; and then the defence's own answer."""
    named = []
    for label, kw in (('lane open', {}), ('help in the lane', dict(x4='H5', a4='N', x5='J5', a5='N'))):
        a = _after_beat(**kw)
        named.append((f'{label}: the offence as it chooses', a))
        named.append((f'{label}: O1 Sprints into the lane', _act(a, 'sprint', 0, 'I6')))
    out = play(named, int(copies), learned == 'learned', what=f'check 1 played ({tag})')
    rep = {k: _summary(v) for k, v in out.items()}
    json.dump(rep, open(os.path.join(RUN, f'played_{tag}.json'), 'w'), indent=1)
    json.dump(out, open(os.path.join(WORK, f'played_{tag}_rows.json'), 'w'))
    for k, v in rep.items():
        print(f"{k:45} {v['mean']} ({v['low']} to {v['high']}) {v['ends']} first: {v['first_action']}")


def cmd_speed(rounds='2'):
    """D-161: step 18o's code and this step's, timed in turn, both under the app's rules as they now are (the zone on)."""
    import subprocess
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18o as O; "
            "print('RESULT ' + json.dumps(O.T._timed({}, dict(O.T.RULES, zone='on'))))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18o/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18o', SENSE_18N='1')).stdout
        one = {'18o, zone on': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18p (the zone on by default)'] = T._timed({}, RULES)
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair, the zone on; each round times step 18o's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
