"""Step 18a: the calibrated default (D-138), checked level by level, under the table's rules (D-141), and the candidate
diagnosis on the exam's persistent boards. The possessions are played by tools/playout.js; the statistics are
tools/learn_17.py's.

  python3 tools/step_18.py pools                         the possession starts -> runs/step18/pools.json
  python3 tools/step_18.py level rookie [pairs] [pool]   a level, calibrated, against its uncalibrated self
  python3 tools/step_18.py order [pairs]                 All-Star against Starter, Starter against Rookie (calibrated)
  python3 tools/step_18.py tabletop uncal|cal|tab [n]    self-play under the table's rules, every position kept
  python3 tools/step_18.py tabletop_fit                  does the table need its own map? (D-141)
  python3 tools/step_18.py diagnose [boards] [keep]      the candidate diagnosis (tools/diagnose_18.js)
  python3 tools/step_18.py regret [offence] [defence]    the same reading on positions from play: what the list leaves out
"""
import json
import math
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import learn_17 as L                                   # noqa: E402

RUN = os.environ.get('STEP18_RUN', os.path.join(ROOT, 'docs', 'runs', 'step18'))      # step 18b writes to its own folder
WORK = os.environ.get('STEP18_WORK', os.path.join(RUN, 'work'))
L.WORK = WORK
POOLS = (('senior', 'pro', True), ('senior', 'pro', False), ('junior', 'amateur', True))
NOISE = {lv: p['noise'] for lv, p in L.profiles().items()}             # each level's own pick noise


def pool_name(age, std, digital):
    return f'{age}/{std}/{"digital" if digital else "tabletop"}'


def cmd_pools():
    """The stored possession starts (step 3n seeds) for the pools this step plays from. The table's pool is the Senior
    Pro starts under the table's rules: the same boards, so the two formats are compared from the same places."""
    import relative_average as RA
    from playmaker_engine import jsbridge, rules_config as RC
    out = {}
    for age, std, digital in POOLS:
        contexts, seen, starts = [], {}, []
        for a, sd, r in RA.rows():
            if (a, sd) != (age, std):
                continue
            rules = RC.with_rules(digital=digital)
            off, dfn = RA.team_of(r['off'], age, std), RA.team_of(r['dfn'], age, std)
            enc = next((e for e in r['snapshots'] if e.startswith('play:')), None)
            if enc is None or not enc.startswith('play:O'):
                continue
            s = RA.decode(enc, off, dfn, rules)
            if s.clock != RC.START_CLOCK:
                continue
            s.ctx.levels_key = (age, std)
            ctx = json.dumps(jsbridge.ctx_json(s.ctx), sort_keys=True)
            if ctx not in seen:
                seen[ctx] = len(contexts)
                contexts.append(json.loads(ctx))
            starts.append(dict(id=f'start{len(starts)}', state=jsbridge.state_json(s), ctx=seen[ctx]))
        out[pool_name(age, std, digital)] = dict(contexts=contexts, starts=starts)
        print(pool_name(age, std, digital), len(contexts), 'team pairings,', len(starts), 'starts')
    os.makedirs(RUN, exist_ok=True)
    json.dump(out, open(os.path.join(RUN, 'pools.json'), 'w'))


def pool(name):
    return json.load(open(os.path.join(RUN, 'pools.json')))[name]


def engine(level, calibrated=True):
    """A level as it plays: its own settings and pick noise, 1 pair ahead (D-118: the fixed look-ahead)."""
    return L.policy(level, 2, NOISE[level], calibrated=calibrated)


def ends(rows, key):
    """endings() for the digital game; the table's shot-clock expiry is the forced shot (D-38)."""
    e = [r[key] for r in rows]
    rep = L.endings(e)
    forced = sum(x[0] == 'forced' for x in e)
    rep['forced_shot'] = forced
    rep['forced_in_100'] = round(100 * forced / len(e), 1)
    p, lo, hi = L.wilson(forced, len(e))
    rep['forced_interval_in_100'] = [round(100 * lo, 1), round(100 * hi, 1)]
    k = round(rep['clock_ran_out'] * len(e))
    p, lo, hi = L.wilson(k, len(e))
    rep['clock_ran_out_interval_in_100'] = [round(100 * lo, 1), round(100 * hi, 1)]
    return rep


def h2h(a, b, pairs, pl, tag, batch=80):
    """Paired possessions in batches of 80 (new dice each batch), a fixed number of pairs. The sequential test's
    verdict is recorded but doesn't stop the run."""
    rows, secs, t0, k = [], 0.0, time.time(), 0
    starts = pl['starts']
    while len(rows) < pairs:
        k += 1
        n = min(batch, pairs - len(rows))
        part = [starts[(i + 37 * k) % len(starts)] for i in range(n)]
        part = [dict(p, seed=104729 * (i + 1) + 15485863 * k) for i, p in enumerate(part)]
        r, s = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=100 + k, a=a, b=b)
        rows += r
        secs += s
        st = L.h2h_stats(rows, delta=2.0)
        print(tag, len(rows), st['mean_difference'], st['interval'], st['sequential_stop'], flush=True)
    rep = dict(tag=tag, stats=L.h2h_stats(rows, delta=2.0), core_hours=round(secs / 3600, 2),
               wall_minutes=round((time.time() - t0) / 60, 1), a_on_offence=ends(rows, 'a_end'), b_on_offence=ends(rows, 'b_end'),
               rows=rows)
    json.dump(rep, open(os.path.join(RUN, f'h2h_{tag}.json'), 'w'))
    print(json.dumps({k_: v for k_, v in rep.items() if k_ != 'rows'}, indent=1), flush=True)
    return rep


def cmd_level(level, pairs='160', pl='senior/pro/digital'):
    """A level with the calibrated reading (a) against the same level without it (b)."""
    h2h(engine(level, True), engine(level, False), int(pairs), pool(pl), f'{level}_cal_vs_uncal_{pl.replace("/", "_")}')


def cmd_order(pairs='80'):
    """Do the levels still stand in order with the calibrated reading on? Each stronger level (a) against the next (b)."""
    pl = pool('senior/pro/digital')
    for a, b in (('allstar', 'starter'), ('starter', 'rookie')):
        h2h(engine(a), engine(b), int(pairs), pl, f'order_{a}_vs_{b}')


TABLE_ENGINES = {
    'uncal': lambda: engine('allstar', False),        # today's computer before D-138
    'cal': lambda: engine('allstar', True),           # the calibrated default (under the table's rules: the app's map
                                                      # before the table's own was fitted, the table's own after)
    'cal_app_map': lambda: L.policy('allstar', 2, NOISE['allstar'], calibrated=True, tabletop_map=False),
}


def cmd_tabletop_h2h(pairs='160'):
    """Under the table's rules: the calibrated All-Star with the table's own map (a) against the same with the app's
    map (b)."""
    h2h(TABLE_ENGINES['cal'](), TABLE_ENGINES['cal_app_map'](), int(pairs), pool('senior/pro/tabletop'), 'tabletop_own_map_vs_app_map')


def cmd_tabletop(name, n='200', fmt='tabletop', seed='1', tag=None):
    """Self-play under the table's rules (or the app's, fmt digital), every play position kept as a training row."""
    pl = pool(f'senior/pro/{fmt}')
    t0 = time.time()
    pol = TABLE_ENGINES[name]()
    n = int(n)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(n)]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('selfplay', starts, pl['contexts'], n=1, seed=int(seed), features=True, keepDefence=True,
                            policies=dict(O=pol, X=pol))
    pts = [r['points'] for r in rows]
    m, sd, ci = L.mean_ci(pts)
    tag = tag or f'{fmt}_{name}'
    os.makedirs(WORK, exist_ok=True)
    json.dump(dict(engine=name, rows=rows), open(os.path.join(WORK, f'selfplay_{tag}.json'), 'w'))
    rep = dict(engine=name, format=fmt, possessions=len(rows), positions=sum(len(r['states']) for r in rows),
               mean_points=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)], sd=round(sd, 2),
               decisions_per_possession=round(sum(r['decisions'] for r in rows) / len(rows), 1),
               core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1),
               per_core_hour=round(3600 * len(rows) / secs),
               endings=ends([dict(end=r['end'] + [r['decisions']]) for r in rows], 'end'))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_{tag}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def rows_of(tag):
    """Training rows from a kept self-play run: per position, the phase, the side to act, the hand reading of what is
    left to earn and what the possession went on to earn beyond what was already earned; grouped by possession."""
    d = json.load(open(os.path.join(WORK, f'selfplay_{tag}.json')))
    out = []
    for g, r in enumerate(d['rows']):
        for st in r['states']:
            clock, banked, reading = st[0], st[1], st[2]
            side = 'O' if st[3 + L_FEATURE('offence_to_act')] > 0.5 else 'X'
            out.append((g, min(6, max(1, (12 - clock) // 2 + 1)), side, reading - banked, r['value'] - banked))
    return out


def L_FEATURE(name):
    from playmaker_engine import decide
    return [f[0] for f in decide.FEATURES].index(name)


def cmd_tabletop_fit():
    """D-141: does the table need its own map? On the uncalibrated computer's tabletop play (the same kind of play the
    digital map was fitted on), by possessions held out in 5 folds: the error of (1) the reading as it stands, (2) the
    digital map applied to it, (3) a straight line per phase and side fitted on tabletop play. The paired difference
    between (2) and (3), with its interval over possessions, is the answer."""
    from playmaker_engine import decide
    cal = decide.learned_weights()['calibration']
    rows = rows_of('tabletop_uncal')
    groups = sorted({r[0] for r in rows})

    def digital(ph, side, x):
        m = cal['maps'].get(f'{ph}{side}')
        if m is None:
            return x
        a, b = m['x'], m['y']
        return b[0] + (b[1] - b[0]) * (x - a[0]) / (a[1] - a[0]) if len(a) > 1 else b[0]

    def line(train):
        fit = {}
        for key in {(r[1], r[2]) for r in train}:
            pts = [(r[3], r[4]) for r in train if (r[1], r[2]) == key]
            n = len(pts)
            mx, my = sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n
            sxx = sum((p[0] - mx) ** 2 for p in pts)
            b = sum((p[0] - mx) * (p[1] - my) for p in pts) / sxx if sxx > 1e-9 and n >= 30 else 0.0
            fit[key] = (my - b * mx, b, n)
        return fit
    err = {g: [0.0, 0.0, 0.0, 0.0, 0] for g in groups}       # per possession: squared errors of raw, digital, own, level; n
    for f in range(5):
        test = {g for i, g in enumerate(groups) if i % 5 == f}
        fit = line([r for r in rows if r[0] not in test])
        for g, ph, side, x, y in (r for r in rows if r[0] in test):
            a, b, _ = fit.get((ph, side), (y, 0.0, 0))
            e = err[g]
            e[0] += (x - y) ** 2
            e[1] += (digital(ph, side, x) - y) ** 2
            e[2] += (a + b * x - y) ** 2
            e[4] += 1
    n = sum(e[4] for e in err.values())
    rmse = [math.sqrt(sum(e[k] for e in err.values()) / n) for k in range(3)]
    # the paired gain of the table's own map over the digital map, a possession at a time (mean squared error per position)
    d = [(e[1] - e[2]) / e[4] for e in err.values() if e[4]]
    m, sd, ci = L.mean_ci(d)
    full = line(rows)
    maps, bias = {}, {}
    for (ph, side), (a, b, k) in sorted(full.items()):
        xs = sorted(r[3] for r in rows if (r[1], r[2]) == (ph, side))
        lo, hi = xs[len(xs) // 10], xs[-1 - len(xs) // 10]
        if hi - lo < 1e-6:
            hi = lo + 1.0
        maps[f'{ph}{side}'] = dict(x=[round(lo, 4), round(hi, 4)], y=[round(a + b * lo, 4), round(a + b * hi, 4)], n=k, slope=round(b, 3))
        ys = [r for r in rows if (r[1], r[2]) == (ph, side)]
        bias[f'{ph}{side}'] = dict(n=k, reading=round(sum(r[3] for r in ys) / k, 2), earned=round(sum(r[4] for r in ys) / k, 2),
                                   digital_map_says=round(sum(digital(ph, side, r[3]) for r in ys) / k, 2))
    rep = dict(possessions=len(groups), positions=n,
               held_out_error=dict(reading_as_it_stands=round(rmse[0], 2), digital_map=round(rmse[1], 2), tabletop_map=round(rmse[2], 2)),
               gain_of_tabletop_map_over_digital=dict(mean_squared_error_per_position=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)]),
               by_phase_and_side=bias, tabletop_maps=maps)
    json.dump(rep, open(os.path.join(RUN, 'tabletop_fit.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


# ---- the candidate diagnosis ----------------------------------------------------------------------------------------

def decisions(names):
    """The exam decisions to diagnose: (name, state, the board's own judge of a turn, the judge's form for
    tools/diagnose_18.js)."""
    from playmaker_engine import exam as EX, board as B, rules_config as RC
    from playmaker_engine.decide import lane_squares
    rim = {B.sq((x, y)): B.dist_rim((x, y)) for x in range(B.W) for y in range(1, B.H + 1)}
    steal = lambda t: any(a.kind == 'steal' for a in t)
    out = []
    for n in names:
        if n == 'C2':
            desc, s, check = EX.c2()
            out.append(('C2', s, lambda t, c=check: c(t)[0], {}))
            continue
        desc, b, check = EX.POSITIONS[int(n) - 1]()
        one = lambda t, c=check: c(t)[0]
        if n == '1':
            out.append(('1', b, one, dict(name='on_lane', stand_in=True, lane=[B.sq(q) for q in lane_squares(b.o[0], RC.RIM, 0.5)])))
        elif n == '3':
            out.append(('3', b, one, dict(name='help_and_rotate')))
        elif n == '5':
            a, c = b['close'], b['short']
            drive = lambda t, a=a: t[0].kind != 'shot' and any(x.piece == 1 and x.kind in ('move', 'qs', 'sprint', 'dribble') for x in t) \
                and B.dist_rim(EX.after(a, t).o[1]) < B.dist_rim(a.o[1])
            out.append(('5 closed out', a, drive, dict(name='drive_closer', piece=1, rim=rim)))
            out.append(('5 stopped short', c, lambda t, c=c: t[0].kind == 'shot' or EX.open_spot(c, t), dict(name='shot_or_move', piece=1, stand_in=True)))
        elif n == '7':
            out.append(('7 phase 2', b['phase 2'], lambda t: t[0].kind != 'shot', dict(name='first_not_shot')))
            out.append(('7 phase 6', b['phase 6'], lambda t: t[0].kind == 'shot', dict(name='first_shot')))
        elif n == '6':
            out.append(('6', b, one, dict(name='acts_at_once', piece=3)))
        elif n == '8':
            out.append(('8', b, one, dict(name='cut', piece=1, rim=rim)))
        elif n == '9':
            out.append(('9', b, one, dict(name='kick_or_relocate', piece=4)))
        elif n == '10':
            out.append(('10 good odds', b['good odds'], steal, dict(name='steal')))
            out.append(('10 bad odds', b['bad odds'], lambda t: not steal(t), dict(name='no_steal')))
        elif n == '11':
            out.append(('11 early', b['early'], lambda t: not any(a.kind == 'pass' and a.target == 1 for a in t), dict(name='no_pass_to', piece=1)))
            out.append(('11 final phase', b['final phase'], lambda t: any(a.kind == 'pass' for a in t), dict(name='pass')))
        elif isinstance(b, dict):
            for k, s in b.items():
                out.append((f'{n} {k}', s, None, {}))
        else:
            out.append((n, b, one, {}))
    return out


def cmd_diagnose(names='1,3,6,8,9,10,11', keep='300', cap='1500', switches=''):
    """For each decision: is the board's move on the search's list, where was it cut if not, and does it win when it
    is searched 1 pair ahead? And the same for the best turn found when every legal turn is read."""
    import subprocess
    from playmaker_engine import jsbridge as J
    import exam_evidence as EV
    os.makedirs(WORK, exist_ok=True)
    todo = decisions(names.split(','))
    todo.sort(key=lambda d: 0 if d[1].side == 'X' else 1)             # the defence's boards are the long ones: first
    running, done = [], {}
    prof = L.profiles()['allstar']

    def start(d):
        name, s, judge, form = d
        tag = name.replace(' ', '_') + ('_' + switches.replace(',', '_') if switches else '')
        jf, of = os.path.join(WORK, f'diag_{tag}.job.json'), os.path.join(WORK, f'diag_{tag}.out.json')
        json.dump(dict(state=J.state_json(s), ctx=J.ctx_json(s.ctx), profile=prof, judge=form, keep=int(keep), keep_accepted=50,
                       cap_s=float(cap), switches={k: True for k in switches.split(',') if k and k not in ('settle', 'nosettle', 'help')} or None,
                           settle_shots=True if 'settle' in switches.split(',') else False if 'nosettle' in switches.split(',') else None,
                           help_readings=True if 'help' in switches.split(',') else None), open(jf, 'w'))
        return subprocess.Popen(['node', '--max-old-space-size=3072', os.path.join(HERE, 'diagnose_18.js'), jf, of]), d, of
    queue = list(todo)
    while queue or running:
        while queue and len(running) < L.CORES:
            running.append(start(queue.pop(0)))
        for r in list(running):
            if r[0].poll() is not None:
                running.remove(r)
                if r[0].returncode != 0:
                    raise RuntimeError(f'diagnose failed: {r[1][0]}')
                done[r[1][0]] = (r[1], json.load(open(r[2])))
                print('done', r[1][0], round(done[r[1][0]][1]['seconds']), 's', flush=True)
        time.sleep(1)
    rep = {}
    for name, ((_, s, judge, form), o) in done.items():
        sign = 1 if o['side'] == 'O' else -1
        rows, differ = o['rows'], 0
        for r in rows:                                    # the board's own judge, on every reported turn
            t = EV.turn_of_json(s, r['turn'])
            ok = bool(judge(list(t))) if judge else None
            if form.get('name') and not form.get('stand_in') and r['accepted'] is not None and ok != r['accepted']:
                differ += 1
            r['accepted'] = ok
        on = [r for r in rows if r['stage'] == 4]
        choice = max(on, key=lambda r: sign * r['pair'])
        acc = [r for r in rows if r['accepted']]
        best_acc = max(acc, key=lambda r: sign * r['pair']) if acc else None
        best = max(rows, key=lambda r: sign * r['pair'])
        gap = sign * (best_acc['pair'] - choice['pair']) if best_acc else None
        if choice['accepted']:
            verdict = 'met: the search\'s choice at 1 pair is a board move'
        elif best_acc is None:
            verdict = 'no board move among the turns read'
        elif abs(gap) <= 0.005:
            where = 'on the list' if any(r['accepted'] for r in on) else f'off the list ({best_acc["where"]})'
            verdict = f'level: the best board move reads the same as the choice when searched; a board move is {where}'
        elif gap > 0.005:
            verdict = f'candidates: a board move wins when searched (by {gap:.1f}) but is off the list ({best_acc["where"]})'
        else:
            where = 'on the list' if any(r['accepted'] for r in on) else f'off the list ({best_acc["where"]})'
            verdict = f'judgement: the best board move is worth {-gap:.1f} less when searched; a board move is {where}'
        slim = lambda r: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items() if k != 'turn'}
        rep[name] = dict(
            side=o['side'], judge=form.get('name'), judge_differences=differ, rebuilt_equal=o['rebuilt_equal'], capped=o['capped'],
            legal_first_actions=o['legal_first_actions'], generated_first_actions=o['generated_first_actions'],
            followed_first_actions=o['followed_first_actions'], all_turns=o['all_turns'], generated_turns=o['generated_turns'],
            list_length=o['list_length'], turns_by_stage=o['turns_by_stage'],
            accepted_turns=o['accepted_turns'] if not form.get('stand_in') else None,
            accepted_by_stage=o['accepted_by_stage'] if not form.get('stand_in') else None,
            accepted_among_read=len(acc), read_at_1_pair=len(rows),
            choice=slim(choice), best_board_move=slim(best_acc) if best_acc else None, board_move_gap=None if gap is None else round(gap, 2),
            best_turn_found=slim(best), regret=round(sign * (best['pair'] - choice['pair']), 2),
            better_than_choice=sum(1 for r in rows if sign * (r['pair'] - choice['pair']) > 0.005),
            better_by_stage={w: sum(1 for r in rows if sign * (r['pair'] - choice['pair']) > 0.005 and r['where'] == w)
                             for w in sorted({r['where'] for r in rows})},
            verdict=verdict, seconds=round(o['seconds'], 1),
            top=[slim(r) for r in sorted(rows, key=lambda r: -sign * r['pair'])[:8]],
            the_list=[slim(r) for r in sorted(on, key=lambda r: r['list_rank'])])
        print(name, '|', verdict, '| regret', rep[name]['regret'], '| turns', o['all_turns'], flush=True)
    path = os.path.join(RUN, 'diagnosis' + ('_' + switches.replace(',', '_') if switches else '') + '.json')
    old = json.load(open(path)) if os.path.exists(path) else {}
    old.update(rep)
    json.dump(old, open(path, 'w'), indent=1)
    print('core-hours', round(sum(v[1]['seconds'] for v in done.values()) / 3600, 2))


def cmd_regret(n_off='48', n_def='12', keep='200', cap='900', switches=''):
    """On positions from play (the outcome exam's stored positions, spread over the phases): the best turn found when
    every legal turn is read one team turn ahead and the best `keep` of them 1 pair ahead, against the search's own
    choice at 1 pair. Regret: how much the search's list leaves on the table, by the computer's own reading."""
    import subprocess
    pos, contexts = L.exam_positions()
    pick = []
    for src, per in (('self-play', int(n_off) // 6), ('defence, self-play', int(n_def) // 6)):
        for ph in range(1, 7):
            pick += [p for p in pos if p['source'] == src and p['phase'] == ph and p['state']['stage'] == 'play'
                     and not p['state'].get('pending')][:per]
    pick.sort(key=lambda p: 0 if p['side'] == 'X' else 1)
    prof = L.profiles()['allstar']
    tag = 'regret' + ('_' + switches.replace(',', '_') if switches else '')
    queue, running, rows = list(pick), [], []
    while queue or running:
        while queue and len(running) < L.CORES:
            p = queue.pop(0)
            jf, of = os.path.join(WORK, f'{tag}_{p["id"]}.job.json'), os.path.join(WORK, f'{tag}_{p["id"]}.out.json')
            json.dump(dict(state=p['state'], ctx=contexts[p['ctx']], profile=prof, judge={}, keep=int(keep), cap_s=float(cap),
                           switches={k: True for k in switches.split(',') if k and k not in ('settle', 'nosettle', 'help')} or None,
                           settle_shots=True if 'settle' in switches.split(',') else False if 'nosettle' in switches.split(',') else None,
                           help_readings=True if 'help' in switches.split(',') else None), open(jf, 'w'))
            running.append((subprocess.Popen(['node', '--max-old-space-size=3072', os.path.join(HERE, 'diagnose_18.js'), jf, of]), p, of))
        for r in list(running):
            if r[0].poll() is not None:
                running.remove(r)
                if r[0].returncode != 0:
                    print('failed', r[1]['id'], flush=True)
                    continue
                o, p = json.load(open(r[2])), r[1]
                sign = 1 if o['side'] == 'O' else -1
                on = [x for x in o['rows'] if x['stage'] == 4]
                choice = max(on, key=lambda x: sign * x['pair'])
                best = max(o['rows'], key=lambda x: sign * x['pair'])
                rows.append(dict(id=p['id'], side=o['side'], phase=p['phase'], all_turns=o['all_turns'], capped=o['capped'],
                                 legal_first_actions=o['legal_first_actions'], generated_first_actions=o['generated_first_actions'],
                                 generated_turns=o['generated_turns'], rebuilt_equal=o['rebuilt_equal'],
                                 choice=choice['words'], choice_value=round(choice['pair'], 2), best=best['words'],
                                 best_value=round(best['pair'], 2), best_where=best['where'],
                                 best_one_turn_rank=best['one_turn_rank'], regret=round(sign * (best['pair'] - choice['pair']), 2),
                                 better=sum(1 for x in o['rows'] if sign * (x['pair'] - choice['pair']) > 0.005),
                                 seconds=round(o['seconds'], 1)))
                print(rows[-1]['id'], rows[-1]['side'], rows[-1]['phase'], rows[-1]['regret'], rows[-1]['best_where'], rows[-1]['seconds'], flush=True)
        time.sleep(0.5)
    rep = dict(switches=switches or None, keep=int(keep))
    for side in ('O', 'X', 'both'):
        rs = [r for r in rows if side == 'both' or r['side'] == side]
        if not rs:
            continue
        m, sd, ci = L.mean_ci([r['regret'] for r in rs])
        none = sum(r['regret'] <= 0.005 for r in rs)
        rep[side] = dict(positions=len(rs), mean_regret=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)],
                         choice_is_best=none, share_choice_is_best=round(none / len(rs), 2),
                         regret_over_2=sum(r['regret'] > 2 for r in rs),
                         median_all_turns=sorted(r['all_turns'] for r in rs)[len(rs) // 2],
                         median_generated_turns=sorted(r['generated_turns'] for r in rs)[len(rs) // 2],
                         best_was={w: sum(1 for r in rs if r['regret'] > 0.005 and r['best_where'] == w) for w in sorted({r['best_where'] for r in rs})},
                         by_phase={str(ph): round(sum(r['regret'] for r in rs if r['phase'] == ph) / max(1, sum(r['phase'] == ph for r in rs)), 2) for ph in range(1, 7)})
    rep['core_hours'] = round(sum(r['seconds'] for r in rows) / 3600, 2)
    rep['rows'] = sorted(rows, key=lambda r: (r['side'], r['phase'], r['id']))
    json.dump(rep, open(os.path.join(RUN, tag + '.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}, indent=1))


def cmd_tabletop_map(write='no'):
    """D-141: the table's own map, the same form as the app's (a straight line per phase and side to act), fitted on
    the uncalibrated computer's play under the table's rules. write=yes puts it in the shared weights file."""
    import hashlib
    import numpy as np
    g, ph, y, hand, X, n_poss = L.training_rows(['tabletop_uncal'])
    side = X[:, L_FEATURE('offence_to_act')].astype(int)
    maps, _ = L.fit_maps('linear', ph, side, hand, y, np.ones(len(y), bool))
    for k, m in sorted(maps.items()):
        print(k, m['positions'], [round(v, 1) for v in m['x']], '->', [round(v, 1) for v in m['y']],
              'slope', round((m['y'][1] - m['y'][0]) / (m['x'][1] - m['x'][0]), 2))
    if write == 'yes':
        body = json.load(open(L.WEIGHTS))
        body.pop('hash', None)
        body['calibration_tabletop'] = dict(
            version=1, form='linear', fitted_on=dict(runs=['tabletop_uncal'], possessions=n_poss, positions=len(y)),
            meaning='the same as calibration, for play under the table\'s rules (D-141): a turnover costs 5 and play goes on, '
                    'so a position has more left to earn than under the app\'s rules', maps=maps)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote calibration_tabletop', body['hash'])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
