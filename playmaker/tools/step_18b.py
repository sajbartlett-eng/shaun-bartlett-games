"""Step 18b: settle the shot at the horizon, the ceiling (D-145), and the shot-timing test. The possessions are played
by tools/playout.js; the statistics are tools/learn_17.py's.

  python3 tools/step_18b.py ceiling [name] [settle]      horizon readings above the ceiling, on the exam's 218 positions
  python3 tools/step_18b.py ceiling_stored               the same on the stored strong-play positions (open play only)
  python3 tools/step_18b.py h2h a b [max_pairs]          head to head, sequential (engines: see ENGINES)
  python3 tools/step_18b.py selfplay name engine [n] [fmt]   self-play, every position kept
  python3 tools/step_18b.py timing name...               the shot-timing test from kept self-play runs
  python3 tools/step_18b.py exam engines                 the outcome exam against the calibrated default
"""
import json
import math
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import learn_17 as L                                   # noqa: E402

RUN = os.path.join(ROOT, 'docs', 'runs', 'step18b')
WORK = os.environ.get('STEP18B_WORK', os.path.join(RUN, 'work'))
L.WORK = WORK
PHASE = lambda clock: min(6, max(1, (12 - clock) // 2 + 1))


def card_ceiling(ctxj, target=-1):
    """D-145: the best open shot any attacker's card can score (3 x the three, 2 x any other shot), with the Coach's
    Call bonus on the target's where that card is in play."""
    from playmaker_engine import rules_config as RC
    from playmaker_engine.scoring import band
    best = 0
    for i, c in enumerate(ctxj['off']):
        m = max((3 if k == 'shot_three' else 2) * v for k, v in c['r'].items() if k.startswith('shot_'))
        if ctxj.get('coach_call') and i == target:
            m += RC.COACH_BONUS[band(m)]
        best = max(best, m)
    return best


def tally(rows):
    """rows: (phase, kind, reading before the map, reading used, ceiling, map applied). The share above the ceiling
    before and after, the mean and the largest excess, by kind and by phase."""
    def part(rs):
        n = len(rs)
        if not n:
            return None
        b = [r[2] - r[4] for r in rs if r[2] > r[4] + 1e-9]
        a = [r[3] - r[4] for r in rs if r[3] > r[4] + 1e-9]
        return dict(readings=n, above_before=len(b), share_before=round(len(b) / n, 4), mean_excess_before=round(sum(b) / len(b), 2) if b else 0,
                    max_excess_before=round(max(b), 2) if b else 0, above_after=len(a), share_after=round(len(a) / n, 4),
                    mean_excess_after=round(sum(a) / len(a), 2) if a else 0, max_excess_after=round(max(a), 2) if a else 0)
    kinds = sorted({(r[1], 'the map applied' if r[5] else 'no map') for r in rows})
    return dict(all=part(rows),
                by_kind={f'{k}, {m}': part([r for r in rows if (r[1], 'the map applied' if r[5] else 'no map') == (k, m)]) for k, m in kinds},
                by_phase={str(ph): part([r for r in rows if r[0] == ph]) for ph in range(1, 7)})


def cmd_ceiling(name='default', settle='no', switches=''):
    """Every horizon reading of a 1-pair search from each of the exam's 218 positions, against the ceiling."""
    pos, contexts = L.exam_positions()
    prof = L.profiles()['allstar']
    procs = []
    for k in range(L.CORES):
        jf, of = os.path.join(WORK, f'ceil_{name}_{k}.job.json'), os.path.join(WORK, f'ceil_{name}_{k}.out.json')
        json.dump(dict(positions=pos[k::L.CORES], contexts=contexts, profile=prof,
                       set=dict(settle_shots=settle == 'yes', switches={s: True for s in switches.split(',') if s})), open(jf, 'w'))
        procs.append((subprocess.Popen(['node', '--max-old-space-size=2048', os.path.join(HERE, 'ceiling_18b.js'), jf, of]), of))
    rows, secs, per = [], 0.0, []
    for p, of in procs:
        if p.wait() != 0:
            raise RuntimeError('ceiling failed')
        o = json.load(open(of))
        secs += o['seconds']
        for r in o['rows']:
            rows += [tuple(x) for x in r['readings']]
            per.append(dict(id=r['id'], side=r['side'], value_over_ceiling=round(r['value'] - r['banked'] - r['ceiling'], 2)))
    rep = dict(name=name, settle_shots=settle == 'yes', switches=switches or None, positions=len(per), core_hours=round(secs / 3600, 2),
               root_values_above_ceiling=sum(1 for p in per if p['value_over_ceiling'] > 1e-9), **tally(rows))
    json.dump(rep, open(os.path.join(RUN, f'ceiling_exam_{name}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def cmd_ceiling_stored(names='strong,strong2'):
    """The stored strong-play positions (step 17D: open play only, kept as today's reading and the named readings):
    today's reading and the calibrated reading against the ceiling."""
    from playmaker_engine import decide
    cal = decide.learned_weights()['calibration']
    pool = L.load_pool()
    f_side, f_tok = [f[0] for f in decide.FEATURES].index('offence_to_act'), [f[0] for f in decide.FEATURES].index('offence_tokens')
    rep = {}
    for name in names.split(','):
        d = json.load(open(os.path.join(WORK, f'selfplay_{name}.json')))
        rows = []
        for r in d['rows']:
            ceil = card_ceiling(pool['contexts'][r['ctx']])
            for st in r['states']:
                clock, banked, hand, f = st[0], st[1], st[2], st[3:]
                o_to_act, x = f[f_side] > 0.5, hand - banked
                applied = not (not o_to_act and f[f_tok] <= 0 and clock <= 2)
                y = x
                if applied:
                    m = cal['maps'].get(f"{PHASE(clock)}{'O' if o_to_act else 'X'}")
                    if m:
                        y = m['y'][0] + (m['y'][1] - m['y'][0]) * (x - m['x'][0]) / (m['x'][1] - m['x'][0])
                rows.append((PHASE(clock), 'open play', x, y, ceil, 1 if applied else 0))
        rep[name] = dict(possessions=len(d['rows']), **tally(rows))
    json.dump(rep, open(os.path.join(RUN, 'ceiling_stored.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


# ---- the engines measured, all at All-Star settings, 1 pair ahead, on the calibrated default ---------------------------------

L.ENGINES.update({
    'default': lambda: L.policy('allstar', 2, 0.5),                                   # the calibrated default (D-138)
    'default_b': lambda: L.policy('allstar', 2, 0.5),
    'settle': lambda: L.policy('allstar', 2, 0.5, settle_shots=True),                 # eval.settle_shots on
    'play_on': lambda: L.policy('allstar', 2, 0.5, switches=dict(play_on=True)),      # the rival (step 12)
    'both': lambda: L.policy('allstar', 2, 0.5, settle_shots=True, switches=dict(play_on=True)),
})


def pool(fmt='digital'):
    """Senior Pro possession starts: the app's rules, or the same boards under the table's rules (step 18a's pools)."""
    return json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))[f'senior/pro/{fmt}']


def ends(e):
    rep = L.endings(e)
    forced = sum(x[0] == 'forced' for x in e)
    rep['forced_in_100'] = round(100 * forced / len(e), 1)
    for name, k in (('forced', forced), ('clock_ran_out', round(rep['clock_ran_out'] * len(e)))):
        p, lo, hi = L.wilson(k, len(e))
        rep[name + '_interval_in_100'] = [round(100 * max(0.0, lo), 1), round(100 * hi, 1)]
    return rep


def cmd_h2h(a, b='default', max_pairs='400', batch='80', fmt='digital'):
    """Engine a against engine b, paired possessions in batches of 80 with new dice each batch, stopping when the
    sequential test decides (no difference against a gain of 2 points, 5% each way; never before 160 pairs) or at
    max_pairs."""
    pl = pool(fmt)
    rows, secs, t0, k = [], 0.0, time.time(), 0
    starts = pl['starts']
    while len(rows) < int(max_pairs):
        k += 1
        part = [starts[(i + 37 * k) % len(starts)] for i in range(int(batch))]
        part = [dict(p, seed=104729 * (i + 1) + 15485863 * k) for i, p in enumerate(part)]
        r, s = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=200 + k, a=L.ENGINES[a](), b=L.ENGINES[b]())
        rows += r
        secs += s
        st = L.h2h_stats(rows, delta=2.0)
        print(a, 'against', b, len(rows), st['mean_difference'], st['interval'], st['sequential_stop'], flush=True)
        if st['sequential_stop'] is not None and len(rows) >= 160:
            break
    rep = dict(a=a, b=b, format=fmt, stats=L.h2h_stats(rows, delta=2.0), core_hours=round(secs / 3600, 2),
               wall_minutes=round((time.time() - t0) / 60, 1), a_on_offence=ends([r['a_end'] for r in rows]),
               b_on_offence=ends([r['b_end'] for r in rows]), rows=rows)
    json.dump(rep, open(os.path.join(RUN, f'h2h_{a}_vs_{b}{"" if fmt == "digital" else "_" + fmt}.json'), 'w'))
    print(json.dumps({k_: v for k_, v in rep.items() if k_ != 'rows'}, indent=1), flush=True)


def cmd_selfplay(name, engine='default', n='200', fmt='digital', seed='1'):
    """An engine playing itself, every open-play position kept (the clock, what is earned, the readings)."""
    pl = pool(fmt)
    t0 = time.time()
    pol = L.ENGINES[engine]()
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('selfplay', starts, pl['contexts'], n=1, seed=int(seed), features=True, keepDefence=True,
                            policies=dict(O=pol, X=pol))
    pts = [r['points'] for r in rows]
    m, sd, ci = L.mean_ci(pts)
    json.dump(dict(engine=engine, format=fmt, rows=rows), open(os.path.join(WORK, f'selfplay_{name}.json'), 'w'))
    rep = dict(engine=engine, format=fmt, possessions=len(rows), mean_points=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)],
               decisions_per_possession=round(sum(r['decisions'] for r in rows) / len(rows), 1),
               core_hours=round(secs / 3600, 2), wall_minutes=round((time.time() - t0) / 60, 1),
               endings=ends([r['end'] + [r['decisions']] for r in rows]))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_{name}.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def cmd_timing(*names):
    """The shot-timing test (the research's section 6), from kept self-play runs. For each phase a possession enters:
    how it left the phase (a shot, the ball lost, or play going on), the chance the ball is lost in a phase the
    offence doesn't shoot in (with a Wilson interval), and the average points of the shots taken in that phase.
    Under the app's rules a turnover ends the possession; at the table it costs 5 and a phase and play goes on, so a
    possession can lose the ball more than once."""
    rep = {}
    for name in names:
        d = json.load(open(os.path.join(WORK, f'selfplay_{name}.json')))
        ph = {k: dict(entered=0, shot=0, lost=0, clock=0, points=[]) for k in range(1, 7)}
        total_to = 0
        for r in d['rows']:
            kind, clock, tok = r['end'][0], r['end'][1], r['end'][2]
            last = PHASE(clock)
            seen = sorted({PHASE(st[0]) for st in r['states']} | {last})
            lost_in = []
            prev = None
            for st in r['states']:                         # the table: a turnover shows as what is earned falling by 5
                if prev is not None and st[1] < prev[1] - 4.5:
                    lost_in.append(PHASE(prev[0]))
                prev = st
            ended_lost = kind in ('turnover_end', 'steal')
            ran_out = ended_lost and clock <= 2 and tok <= 0 and kind == 'turnover_end'
            if ended_lost and not ran_out:
                lost_in.append(last)
            total_to += len(lost_in)
            for k in seen:
                ph[k]['entered'] += 1
            if kind in ('shot', 'free_throws', 'forced'):
                ph[last]['shot'] += 1
                ph[last]['points'].append(r['points'])
            if ran_out:
                ph[last]['clock'] += 1
            for k in set(lost_in):
                ph[k]['lost'] += 1
        out = {}
        for k, v in ph.items():
            kept = v['entered'] - v['shot']
            p, lo, hi = L.wilson(v['lost'], kept) if kept else (0, 0, 0)
            pm = L.mean_ci(v['points']) if len(v['points']) > 1 else (v['points'][0] if v['points'] else 0, 0, 0)
            out[str(k)] = dict(entered=v['entered'], shot=v['shot'], kept_the_ball=kept, lost=v['lost'], clock_ran_out=v['clock'],
                               loss_chance_in_100=round(100 * p, 1), interval_in_100=[round(100 * max(0.0, lo), 1), round(100 * hi, 1)],
                               shots_mean_points=round(pm[0], 1), shots_points_interval=[round(pm[0] - pm[2], 1), round(pm[0] + pm[2], 1)])
        kept_all = sum(v['entered'] - v['shot'] for v in ph.values())
        lost_all = sum(v['lost'] for v in ph.values())
        p, lo, hi = L.wilson(lost_all, kept_all)
        n = len(d['rows'])
        e = [r['end'] + [r['decisions']] for r in d['rows']]
        rep[name] = dict(possessions=n, format=d.get('format'), engine=d.get('engine'),
                         loss_chance_a_phase_in_100=round(100 * p, 1), interval_in_100=[round(100 * max(0.0, lo), 1), round(100 * hi, 1)],
                         turnovers_per_100_possessions=round(100 * total_to / n, 1),
                         forced_shot_in_100=round(100 * sum(r['end'][0] == 'forced' for r in d['rows']) / n, 1),
                         mean_points=round(sum(r['points'] for r in d['rows']) / n, 2),
                         shot_by_phase=ends(e)['shot_by_phase'], decisions=ends(e)['decisions'], by_phase=out)
    json.dump(rep, open(os.path.join(RUN, 'shot_timing.json'), 'w'), indent=1)
    for name, v in rep.items():
        print(name, {k: x for k, x in v.items() if k != 'by_phase'})
        for k, x in v['by_phase'].items():
            print('   phase', k, x)


def cmd_exam(engines='default,settle'):
    """The outcome exam (218 positions): each engine plays the side to act to the end, against the calibrated default."""
    keep = L.RUN
    L.cmd_exam(engines)
    src = os.path.join(keep, f'exam_{engines.replace(",", "_")}.json')
    os.replace(src, os.path.join(RUN, f'exam_{engines.replace(",", "_")}.json'))


def cmd_speed(engines='default,settle,play_on'):
    L.cmd_speed(engines)
    src = os.path.join(L.RUN, f'speed_{engines.replace(",", "_")}.json')
    os.replace(src, os.path.join(RUN, f'speed_{engines.replace(",", "_")}.json'))


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
