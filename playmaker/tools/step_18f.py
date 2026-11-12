"""Step 18f: the computer's judgement, now that it sees every move (D-157 to D-159).

  python3 tools/step_18f.py also                 the default's choices on 18e's pilot positions, for the regret tool to value
  python3 tools/step_18f.py lines [switches]     the closeout board (both forms) and the EB3F5B position under a setting
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import step_18e as E18                                 # noqa: E402
L = E18.L

RUN = os.path.join(ROOT, 'docs', 'runs', 'step18f')
WORK = os.environ.get('STEP18F_WORK', os.path.join(RUN, 'work'))
E18.RUN, E18.WORK, L.WORK = RUN, WORK, WORK
SWITCHES = ('whole_turns', 'split_ties', 'kept_actions', 'rank_in_hand')   # this step's switches, as the tools name them


def setting(*on, open_list=None):
    """A setting for the line tool: the default rules, the level's own open list unless given, and this step's switches."""
    st = dict(control=None, open_list=open_list, **{k: (k in on) for k in SWITCHES})
    st.update({k.split('=')[0]: k.split('=')[1] for k in on if '=' in k})      # e.g. leaf_mode=looks
    return st


def run_line(state_json, ctx_json, st, turns, top=6):
    jf, of = os.path.join(WORK, f'line_{os.getpid()}.job.json'), os.path.join(WORK, f'line_{os.getpid()}.out.json')
    job = dict(state=state_json, ctx=ctx_json, profile=L.profiles()['allstar'], turns=turns, top=top, replies=int(os.environ.get('LINE_REPLIES', '0')))
    for k, v in st.items():
        if v is not None:
            job[k] = v
    json.dump(job, open(jf, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'line_18d.js'), jf, of], check=True)
    return json.load(open(of))


E18.run_line = run_line


def cmd_also(src='/home/user/step18e/playmaker/docs/runs/step18e/work'):
    """The default's choice on each of 18e's pilot positions (12 defence, 24 offence), as action JSON, so that another
    setting's run can value it whatever its rank -> work/also.json"""
    out = {}
    for f in sorted(os.listdir(src)):
        if f.startswith('regret_open_defence_') and f.endswith('.out.json'):
            o = json.load(open(os.path.join(src, f)))
            sign = 1 if o['side'] == 'O' else -1
            on = [r for r in o['rows'] if r['stage'] == 4]
            ch = max(on, key=lambda r: sign * r['pair'])
            out[f[len('regret_open_defence_'):-len('.out.json')]] = [ch['turn']]
    json.dump(out, open(os.path.join(WORK, 'also.json'), 'w'))
    print(len(out), 'positions')


def cmd_lines(*on):
    """The tests of part 3, under a setting: the closeout board's step 1 with the shooter unable to move, the same
    with him able to move, and the EB3F5B position. What the computer chooses and what each expected move reads."""
    from playmaker_engine import jsbridge as J
    from playmaker_engine import rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    st = setting(*on)
    rep = {}
    s0 = E18.closeout_board()
    free = s0.with_(moved_o=0, qs_o=0, cnt=(0,) * len(s0.cnt))        # the same board, the shooter able to move
    before, _ = E18._replay(RC.with_rules(digital=True), ['N'] * 5)
    lines = [ln.split('] ', 1)[1] for ln in E18.LOG.splitlines()]
    sb = before[lines.index('O1 Pass to O4')]
    sp = apply(sb, next(a for a in legal_actions(sb) if str(a) == 'O1 Pass to O4'))
    for name, s, who in (('closeout, the shooter cannot move', s0, 'X3'), ('closeout, the shooter can move', free, 'X3'), ('EB3F5B, the pass in the air', sp, 'X4')):
        turns = [dict(name=f'{who} Quick Steps closer (E4)', turn=E18._named(s, (f'{who} Quick Step to E4',), soft=True)),
                 dict(name=f'{who} Moves closer (C4), facing him', turn=E18._named(s, (f'{who} Move to C4 facing SW',), soft=True)),
                 dict(name='the defence Pauses', turn=E18._named(s, ('X Pause',), soft=True))]
        turns = [t for t in turns if t['turn'] is not None]
        r = run_line(J.state_json(s), J.ctx_json(s.ctx), st, turns, top=5)
        rep[name] = dict(chose=r['rows'][0]['words'], reads=round(r['rows'][0]['value'], 3), top=[(x['words'], round(x['value'], 3)) for x in r['rows']],
                         named=[dict(name=x['name'], reads=round(x['value'], 3), behind=round(x['behind_the_choice'], 3), on_the_list=x['list_rank'],
                                     **({'replies': [(round(v, 2), w) for v, w in x['replies']]} if x.get('replies') else {})) for x in r['named'] if x['legal']])
        print(name, '| chose', rep[name]['chose'], rep[name]['reads'])
        for x in rep[name]['named']:
            print('     ', x)
    json.dump(rep, open(os.path.join(RUN, 'lines_' + ('_'.join(on).replace('=', '_') or 'default') + '.json'), 'w'), indent=1)


# ---- self-play for fitting, and the maps ------------------------------------------------------------------------------

def pool():
    return json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))['senior/pro/digital']


def cmd_selfplay(name, level='allstar', n='240', seed='1', *on):
    """Possessions played by one level against itself on the default with the named switches on (its own pick noise),
    every open-play position kept as a row: the clock, what is already earned, today's reading, the named readings,
    and the looks reading last -> work/selfplay_<name>.json"""
    import time
    pl = pool()
    sw = {k: True for k in on if k in SWITCHES}
    sw.update({k.split('=')[0]: k.split('=')[1] for k in on if '=' in k})
    pol = L.policy(level, 2, L.profiles()[level]['noise'], **sw)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    t0 = time.time()
    rows, secs = L.run_jobs('selfplay', starts, pl['contexts'], n=1, seed=int(seed), features=True, looks=True, policies=dict(O=pol, X=pol))
    json.dump(dict(level=level, switches=sw, rows=rows), open(os.path.join(WORK, f'selfplay_{name}.json'), 'w'))
    pts = [r['points'] for r in rows]
    m, sd, ci = L.mean_ci(pts)
    rep = dict(name=name, level=level, switches=sw, possessions=len(rows), positions=sum(len(r['states']) for r in rows),
               mean_points=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)], shot_timing=E18.shot_timing([r['end'] + [r['decisions']] for r in rows]),
               core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_{name}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1), flush=True)


def _rows(names):
    """(possession number, phase, what was left to earn, today's reading of it, the looks reading of it, offence to act)"""
    import numpy as np
    g, ph, y, hand, looks, side = [], [], [], [], [], []
    k = 0
    for name in names:
        if name.startswith('trace_'):                # a run with every action kept (cmd_trace): [clock, earned, today's reading, offence to act, the looks reading]
            for r in json.load(open(os.path.join(WORK, f'{name}.json')))['rows']:
                for clock, banked, hd, o_to_act, lk in r['reads']:
                    g.append(k); ph.append(min(6, max(1, (12 - clock) // 2 + 1))); y.append(r['value'] - banked)
                    hand.append(hd - banked); looks.append(lk - banked); side.append(int(o_to_act))
                k += 1
            continue
        d = json.load(open(os.path.join(WORK, f'selfplay_{name}.json')))
        for r in d['rows']:
            for st in r['states']:
                clock, banked = st[0], st[1]
                g.append(k); ph.append(min(6, max(1, (12 - clock) // 2 + 1))); y.append(r['value'] - banked)
                hand.append(st[2] - banked); looks.append(st[-1] - banked); side.append(int(st[3 + 12]))
            k += 1
    return np.array(g), np.array(ph), np.array(y, float), np.array(hand, float), np.array(looks, float), np.array(side), k


def cmd_fit(names, write='no'):
    """The maps, the same form as step 17D's (a straight line per phase and side to act): from today's reading
    (the block 'calibration'), and from the looks reading (the block 'calibration_looks'). The held-out error of each
    (5 folds, by possession), beside the map in the weights file now. write: 'looks', 'calibration', 'both' or 'no'."""
    import numpy as np
    g, ph, y, hand, looks, side, n_poss = _rows(names.split(','))
    fold = np.random.default_rng(18).permutation(n_poss) % 5
    rmse = lambda a, m=None: float(np.sqrt(np.mean(((a - y) if m is None else (a - y)[m]) ** 2)))
    body = json.load(open(L.WEIGHTS))

    def held(r):
        pred = np.array(r, float)
        for k in range(5):
            tr, te = fold[g] != k, fold[g] == k
            maps, _ = L.fit_maps('linear', ph, side, r, y, tr)
            for key, m in maps.items():
                sel = te & (ph == int(key[0])) & (side == (1 if key[1] == 'O' else 0))
                pred[sel] = L.knot_map(r[sel], m['x'], m['y'])
        return pred

    def boot(pa, pb):                                  # the gain of a over b in squared error, resampled by possession
        rs = np.random.default_rng(5)
        d = np.bincount(g, (pb - y) ** 2 - (pa - y) ** 2, n_poss)
        cnt = np.bincount(g, minlength=n_poss)
        out = []
        for _ in range(400):
            pick = rs.integers(0, n_poss, n_poss)
            out.append(d[pick].sum() / cnt[pick].sum())
        return [round(float(np.percentile(out, 2.5)), 2), round(float(np.percentile(out, 97.5)), 2)]

    now = np.array(hand, float)
    for key, m in body['calibration']['maps'].items():
        sel = (ph == int(key[0])) & (side == (1 if key[1] == 'O' else 0))
        now[sel] = L.knot_map(hand[sel], m['x'], m['y'])
    p_hand, p_looks = held(hand), held(looks)
    slopes = {}
    for p in range(1, 7):
        for sd in (1, 0):
            m = (ph == p) & (side == sd)
            if m.sum() > 20:
                slopes[f"{p}{'O' if sd else 'X'}"] = dict(positions=int(m.sum()), earned=round(float(y[m].mean()), 1),
                                                         todays_reading=round(float(hand[m].mean()), 1), looks_reading=round(float(looks[m].mean()), 1),
                                                         slope_today=round(float(np.polyfit(hand[m], y[m], 1)[0]), 3),
                                                         slope_looks=round(float(np.polyfit(looks[m], y[m], 1)[0]), 3),
                                                         below_the_floor=round(float((looks[m] < hand[m] - 1e-9).mean()), 2))
    rep = dict(runs=names.split(','), possessions=n_poss, positions=len(y),
               held_out_error=dict(the_map_in_the_file=round(rmse(now), 3), todays_reading_refit=round(rmse(p_hand), 3), looks_reading=round(rmse(p_looks), 3)),
               squared_error_gain=dict(refit_over_the_file=boot(p_hand, now), looks_over_refit=boot(p_looks, p_hand), looks_over_the_file=boot(p_looks, now)),
               by_phase_and_side=slopes)
    json.dump(rep, open(os.path.join(RUN, f'fit_{names.replace(",", "_")}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))
    if write != 'no':
        import hashlib
        ones = np.ones(len(y), bool)
        body.pop('hash', None)
        fitted = dict(runs=names.split(','), possessions=n_poss, positions=len(y))
        if write in ('looks', 'both'):
            maps, _ = L.fit_maps('linear', ph, side, looks, y, ones)
            body['calibration_looks'] = dict(version=1, form='linear', fitted_on=fitted, maps=maps,
                                             meaning="what is left to earn, from the looks reading of it (eval.leaf_mode 'looks': the best look, "
                                                     "without the phase table's floor): per phase and side to act, knots x -> y")
        if write in ('calibration', 'both'):
            maps, _ = L.fit_maps('linear', ph, side, hand, y, ones)
            body['calibration'] = dict(body['calibration'], fitted_on=fitted, maps=maps)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote', write, body['hash'])


# ---- part 2: how often the top of the list is a tie ----------------------------------------------------------------

def cmd_ties(tag='default', *on):
    """On the outcome exam's stored positions (the hand boards, and positions from play for both sides): how many of
    the computer's turns read exactly the same as its best, 1 pair ahead with no pick noise, and how many are within
    its pick noise (0.5)."""
    pos, contexts = L.exam_positions()
    pos = [p for p in pos if p['state']['stage'] == 'play']
    sw = {k: True for k in on if k in SWITCHES}
    sw.update({k.split('=')[0]: k.split('=')[1] for k in on if '=' in k})
    rows, secs = L.run_jobs('search', pos, contexts, policies=dict(a=L.policy('allstar', 2, 0.0, **sw)))
    rep = {}
    for side in ('O', 'X', 'both'):
        tied, near, n, firsts, changed = [], [], 0, 0, []
        for p, r in zip(pos, rows):
            if side != 'both' and r['side'] != side:
                continue
            sign = 1 if r['side'] == 'O' else -1
            vals = sorted((sign * v for v, _ in r['by']['a']['results']), reverse=True)
            if len(vals) < 2:
                continue
            n += 1
            same = r['by']['a'].get('same_top')
            tied.append(same if sw.get('split_ties') and same is not None else sum(1 for v in vals if v > vals[0] - 1e-6))
            near.append(sum(1 for v in vals if v > vals[0] - 0.5))
            # the same position decided twice with the level's pick noise (0.5): how often the two choices differ.
            # Without split_ties every turn has its own draw; with it, turns that read the same share one and the
            # first of them is taken
            import random
            rn, first, diff = random.Random(7919 * (n + 1)), [], 0
            res = [(sign * v, json.dumps(t[0])) for v, t in r['by']['a']['results']]
            for _ in range(400):
                pick = []
                for _k in range(2):
                    best, bv, prev, nz = None, -1e9, None, 0.0
                    for v, a0 in res:
                        if not sw.get('split_ties') or prev is None or abs(v - prev) >= 1e-9:
                            nz = rn.gauss(0, 0.5)
                        prev = v
                        if v + nz > bv:
                            bv, best = v + nz, a0
                    pick.append(best)
                diff += pick[0] != pick[1]
            changed.append(diff / 400)
        k = sum(1 for x in tied if x > 1)
        pr, lo, hi = L.wilson(k, n)
        rep[side] = dict(decisions=n, top_is_a_tie=k, share=round(pr, 3), interval=[round(lo, 3), round(hi, 3)],
                         turns_tied_at_the_top_mean=round(sum(tied) / max(1, n), 1), turns_within_pick_noise_mean=round(sum(near) / max(1, n), 1),
                         first_action_differs_between_two_runs=[round(x, 3) for x in L.mean_ci(changed)])
    rep['core_hours'] = round(secs / 3600, 2)
    rep['switches'] = sw
    json.dump(rep, open(os.path.join(RUN, f'ties_{tag}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


# ---- head to head --------------------------------------------------------------------------------------------------

def _switches(on):
    if 'start' in on:                                  # the default as it stood at the start of the step (18e's): the old map, this step's switches off
        return dict(whole_turns=False, split_ties=False, kept_actions=False, rank_in_hand=False, map='start')
    sw = {k: True for k in on if k in SWITCHES}
    sw.update({k.split('=')[0]: k.split('=')[1] for k in on if '=' in k})
    return sw


def cmd_h2h(tag, pairs, a_on, b_on='', level='allstar', level_b=None):
    """Paired possessions (the same start and dice, sides swapped), in batches of 80, each side its own pick noise, 1
    pair ahead: a (the level with the switches a_on, comma-separated) against b (the level with b_on). Sequential: it
    stops when the test for a gain of 1 point a pair against none gives its verdict (after 160 pairs), or at `pairs`."""
    import time
    lb = level_b or level
    a = L.policy(level, 2, L.profiles()[level]['noise'], **_switches([x for x in a_on.split(',') if x]))
    b = L.policy(lb, 2, L.profiles()[lb]['noise'], **_switches([x for x in b_on.split(',') if x]))
    pl, rows, secs, k, t0 = pool(), [], 0.0, 0, time.time()
    starts = pl['starts']
    while len(rows) < int(pairs):
        k += 1
        n = min(80, int(pairs) - len(rows))
        part = [starts[(i + 37 * k) % len(starts)] for i in range(n)]
        part = [dict(p, seed=104729 * (i + 1) + 15485863 * k) for i, p in enumerate(part)]
        r, s = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=400 + k, a=a, b=b)
        rows += r
        secs += s
        st = L.h2h_stats(rows, delta=1.0)
        print(tag, len(rows), st['mean_difference'], st['interval'], st['wins'], st['losses'], st['ties'], st['sequential_stop'], round(secs / 3600, 2), flush=True)
        if st['sequential_stop'] and len(rows) >= 160:
            break
    st = L.h2h_stats(rows, delta=1.0)
    rep = dict(tag=tag, a=f'{level}: {a_on or "the default"}', b=f'{lb}: {b_on or "the default"}', stats=st, core_hours=round(secs / 3600, 2),
               wall_minutes=round((time.time() - t0) / 60, 1), a_on_offence=E18.shot_timing([r['a_end'] for r in rows]),
               b_on_offence=E18.shot_timing([r['b_end'] for r in rows]), rows=rows)
    json.dump(rep, open(os.path.join(RUN, f'h2h_{tag}.json'), 'w'))
    print(json.dumps({k_: v for k_, v in rep.items() if k_ != 'rows'}, indent=1), flush=True)


# ---- part 5: the open list for the Rookie and the Starter ---------------------------------------------------------------

TARGET = dict(rookie=(0.3, 1.0), starter=(1.0, 2.0), allstar=(2.5, 3.0))


def _level(lv, open_list=None, full=None, follow=None, **sw):
    """A level's policy for timing: no pick noise, 1 pair; open_list None = the level's own; full, follow = its list widths."""
    pol = L.policy(lv, 2, 0.0, **({} if open_list is None else dict(open_list=open_list)), **sw)
    if full is not None:
        pol['profile'] = dict(pol['profile'], open_full=int(full), open_follow=int(follow))
    return pol


def _timed(pols, runs=2):
    """The time to finish 1 pair on the hand boards' 22 decisions for each policy (one warm engine), the best of `runs`."""
    positions, contexts = L.hand_boards()
    best = {}
    for _ in range(runs):
        L.run_jobs('search', positions[:6], contexts, chunks=1, policies=pols)
        rows, _s = L.run_jobs('search', positions + positions, contexts, chunks=1, policies=pols)
        rows = rows[len(positions):]
        for name in pols:
            v = sorted(r['by'][name]['seconds'] for r in rows)
            x = sorted(r['by'][name]['seconds'] for r in rows if r.get('side') == 'X')
            one = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(v[int(0.9 * (len(v) - 1) + 0.5)], 3), slowest=round(v[-1], 3),
                       defence_nine_in_ten=round(x[int(0.9 * (len(x) - 1) + 0.5)], 3) if x else None)
            if name not in best or one['nine_in_ten'] < best[name]['nine_in_ten']:
                best[name] = one
    return best


def cmd_widths(level='rookie', widths='8:4,4:2,2:1,1:1', *on):
    """Part 5: a level's time to finish 1 pair with the open list at each pair of widths (turns read in full : first
    actions followed), beside its list today."""
    pols = {'today': _level(level, **_switches(on))}
    for w in widths.split(','):
        f, fo = w.split(':')
        pols[w] = _level(level, 'defence', f, fo, **_switches(on))
    rep = _timed(pols)
    for k, v in rep.items():
        v['desktop_target'] = TARGET[level][0]
        v['fits'] = v['nine_in_ten'] <= TARGET[level][0]
        print(level, k, v, flush=True)
    json.dump(rep, open(os.path.join(RUN, f'widths_{level}.json'), 'w'), indent=1)


def cmd_speed(tag='final', *on):
    """The time to finish 1 pair at every level under the config as it stands (and switches `on`), against the budget."""
    rep = _timed({lv: _level(lv, **_switches(on)) for lv in TARGET}, runs=3)
    for lv, v in rep.items():
        v.update(desktop_target=TARGET[lv][0], fits_desktop=v['nine_in_ten'] <= TARGET[lv][0], phone=round(4 * v['nine_in_ten'], 2), phone_target=TARGET[lv][1])
        print(lv, v, flush=True)
    json.dump(rep, open(os.path.join(RUN, f'speed_{tag}.json'), 'w'), indent=1)


# ---- the end: self-play with every action kept, the levels' order, the last head to head -----------------------------------

def cmd_trace(n='200', seed='1', level='allstar', tag='', *on):
    """Self-play at a level on the config as it stands, every action kept (step 18d's measures), with the readings the
    map is fitted on -> work/trace_app.json (the All-Star's) or work/trace_<level>.json; `fidelity` reads the first."""
    import time
    import step_18d as D
    D.RUN, D.WORK, D.L.WORK = RUN, WORK, WORK
    pl, t0 = pool(), time.time()
    pol = L.policy(level, 2, L.profiles()[level]['noise'], **_switches(on))
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, policies=dict(O=pol, X=pol))
    name = ('trace_app' if level == 'allstar' else f'trace_{level}') if not tag else f'trace_{tag}'
    level = level if not tag else tag
    json.dump(dict(size='app', rows=rows), open(os.path.join(WORK, f'{name}.json'), 'w'))
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    rep = dict(level=level, possessions=len(rows), mean_points=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)],
               positions=sum(len(r['reads']) for r in rows), core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_final_{level}.json'), 'w'), indent=1)
    print(json.dumps(rep))


def cmd_fidelity(*tags):
    """Step 18d's measures on the All-Star's self-play (cmd_trace; a tag names another run) -> fidelity.json"""
    import step_18d as D
    D.RUN, D.WORK, D.L.WORK = RUN, WORK, WORK
    D.cmd_fidelity(*(tags or ('app',)))


def cmd_boards(names='1,3,8,9'):
    """Boards move by move on the default as the config has it: the computer's choice 1 pair ahead (no pick noise),
    and what each board move reads when it is searched -> boards.json"""
    from playmaker_engine import exam as EX, jsbridge as J
    rep = {}
    for n in names.split(','):
        _, s, _ = EX.POSITIONS[int(n) - 1]()
        turns = [dict(name=nm, turn=tj) for nm, tj in ((nm, E18._named(s, acts, soft=True)) for nm, acts in E18.BOARD_TURNS[n]) if tj is not None]
        r = run_line(J.state_json(s), J.ctx_json(s.ctx), setting(*default_on()), turns, top=4)
        rep[n] = dict(side=r['side'], choice=dict(words=r['rows'][0]['words'], value=round(r['rows'][0]['value'], 3)),
                      top=[(x['words'], round(x['value'], 3)) for x in r['rows']],
                      named=[dict(name=x['name'], reads=round(x['value'], 3), behind=round(x['behind_the_choice'], 3), on_the_list=x['list_rank']) for x in r['named'] if x['legal']])
        print('board', n, '| choice:', rep[n]['choice'])
        for x in rep[n]['named']:
            print('      ', x)
    json.dump(rep, open(os.path.join(RUN, 'boards.json'), 'w'), indent=1)


def default_on():
    """This step's switches as the config has them."""
    cfg = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))
    return [k for k in SWITCHES if cfg['search'].get(k) is True or cfg['eval'].get(k) is True]


def cmd_sense(which='fixed,free,eb3f5b', n='160'):
    """The sense checks on the default as the config has it: on part 3's three positions, the computer's own choice
    and each expected move played out by the rules with common dice (the All-Star on both sides) -> sense_checks.json"""
    from playmaker_engine import jsbridge as J
    from playmaker_engine import rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    path = os.path.join(RUN, 'sense_checks.json')
    rep = json.load(open(path)) if os.path.exists(path) else {}
    s0 = E18.closeout_board()
    free = s0.with_(moved_o=0, qs_o=0, cnt=(0,) * len(s0.cnt))
    before, _ = E18._replay(RC.with_rules(digital=True), ['N'] * 5)
    lines = [ln.split('] ', 1)[1] for ln in E18.LOG.splitlines()]
    sb = before[lines.index('O1 Pass to O4')]
    sp = apply(sb, next(a for a in legal_actions(sb) if str(a) == 'O1 Pass to O4'))
    for name in which.split(','):
        s, who = dict(fixed=(s0, 'X3'), free=(free, 'X3'), eb3f5b=(sp, 'X4'))[name]
        sj, cj = J.state_json(s), J.ctx_json(s.ctx)
        own = run_line(sj, cj, setting(*default_on()), [], top=1)['rows'][0]
        named = [(f'{who} Quick Steps closer (E4)', E18._named(s, (f'{who} Quick Step to E4',), soft=True)),
                 (f'{who} Moves closer (C4), facing him', E18._named(s, (f'{who} Move to C4 facing SW',), soft=True)),
                 ('the defence Pauses', E18._named(s, ('X Pause',), soft=True))]
        turns = [("the computer's: " + own['words'], own['turn'])] + [(nm, t) for nm, t in named if t is not None and t != own['turn']]
        r = E18.sense(name, sj, cj, turns, n=int(n), setting=dict(open_list=None, control=None))
        r['the_computer_reads_its_choice'] = round(own['value'], 2)
        rep[name] = r
        print(name, json.dumps(r, indent=1), flush=True)
        json.dump(rep, open(path, 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
