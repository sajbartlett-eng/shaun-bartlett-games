"""Step 18d: Shaun's control rule (D-151, rules.control) measured for fidelity. The possessions are played by
tools/playout.js (job kind 'trace': every action kept). The app's rules only (D-146).

  python3 tools/step_18d.py trace off|1|2|3 [n]        All-Star self-play under today's rules or a size, every action kept
  python3 tools/step_18d.py fidelity off 1 2 3         the fidelity measures from the kept runs -> runs/step18d/fidelity.json
  python3 tools/step_18d.py speed                      the time to finish 1 pair at each level, today's rules and each size
"""
import json
import math
import os
import random
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import learn_17 as L                                   # noqa: E402

RUN = os.path.join(ROOT, 'docs', 'runs', 'step18d')
WORK = os.environ.get('STEP18D_WORK', os.path.join(RUN, 'work'))
L.WORK = WORK
MOVES = ('move', 'qs', 'sprint')
PHASE = lambda clock: min(6, max(1, (12 - clock) // 2 + 1))


def pool():
    return json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))['senior/pro/digital']


def engine(level='allstar'):
    p = L.profiles()[level]
    return L.policy(level, 2, p['noise'])


def cmd_trace(size='off', n='200', seed='1'):
    """All-Star self-play from the Senior Pro starts under rules.control at `size` ('off': today's rules)."""
    pl = pool()
    t0 = time.time()
    pol = engine()
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), control=size, policies=dict(O=pol, X=pol))
    os.makedirs(WORK, exist_ok=True)
    json.dump(dict(size=size, rows=rows), open(os.path.join(WORK, f'trace_{size}.json'), 'w'))
    pts = [r['points'] for r in rows]
    m, sd, ci = L.mean_ci(pts)
    print(json.dumps(dict(size=size, possessions=len(rows), mean_points=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)],
                          decisions=round(sum(r['decisions'] for r in rows) / len(rows), 1), core_hours=round(secs / 3600, 2),
                          wall_minutes=round((time.time() - t0) / 60, 1))))


# ---- the fidelity measures ------------------------------------------------------------------------------------------

def xy(sq):
    return ord(sq[0]) - 65, int(sq[1:])


def cheb(a, b):
    p, q = xy(a), xy(b)
    return max(abs(p[0] - q[0]), abs(p[1] - q[1]))


def share(k, n):
    """A share with its Wilson interval, in percent."""
    if not n:
        return dict(n=0, of=0, pct=None, interval=None)
    p, lo, hi = L.wilson(k, n)
    return dict(n=k, of=n, pct=round(100 * p, 1), interval=[round(100 * max(0.0, lo), 1), round(100 * hi, 1)])


def mean(v):
    """A mean with its 95% interval."""
    if not v:
        return dict(n=0, mean=None, interval=None)
    if len(v) == 1:
        return dict(n=1, mean=round(v[0], 1), interval=None)
    m, sd, ci = L.mean_ci(v)
    return dict(n=len(v), mean=round(m, 1), interval=[round(m - ci, 1), round(m + ci, 1)])


def shots_of(row, contexts):
    """Each shot of a possession, read from its actions: what the shooter and the contester last did this phase, how
    the shooter got the ball, where the contester came from, and what the shot earned."""
    ev, out = row['events'], []
    ctx = contexts[row['ctx']]
    for sh in row['shots']:
        k, shooter, ph = sh['at'], sh['ball'], sh['phase']
        last = {('O', i): 'none' for i in range(5)}
        last.update({('X', j): 'none' for j in range(5)})
        for e in ev[:k]:
            if e[0] == ph and e[3] in MOVES:
                last[(e[2], e[4])] = e[3]
        # how he got the ball: the last action before the shot taken while someone else held it
        got = max((j for j, e in enumerate(ev[:k]) if e[8] != shooter), default=-1)
        since = [e for e in ev[got + 1:k] if e[2] == 'O' and e[4] == shooter and e[3] in MOVES + ('dribble',)]
        how = ('catch and shoot' if got >= 0 else 'from a standstill') if not since else 'off the dribble or a movement'
        res = row['result'] if sh is row['shots'][-1] else None
        d = dict(phase=ph, type=sh['type'], forced=sh['forced'], shooter=shooter, shooter_last=last[('O', shooter)],
                 shooter_rushed=last[('O', shooter)] in ('qs', 'sprint'), how=how, shooter_qs=ctx['off'][shooter]['qs'])
        if res and res['kind'] in ('shot', 'forced', 'free_throws'):
            c = res['contester']
            d['earned'] = res['shot_value'] + res['free_throws']
            d['fouled'] = res['kind'] == 'free_throws'
            d['contester'] = c
            if c >= 0:
                react = [e for e in ev[k + 1:] if e[2] == 'X' and e[4] == c and e[3] in MOVES]
                clast = react[-1][3] if react else last[('X', c)]
                d.update(contest_last=clast, contest_rushed=clast in ('qs', 'sprint'), late=bool(react),
                         from_far=cheb(sh['x'][c], sh['o'][shooter]), helper=c != shooter, contester_qs=ctx['dfn'][c]['qs'],
                         contest=res['contest'])
            out.append(d)
        elif res and res['kind'] == 'steal':
            d.update(earned=0, stolen=True, contester=-2)
            out.append(d)
    return out


def extra_pass(row):
    """Closeouts in open play (a defender ends a movement next to the ball handler, having not been next to him) and
    what the offence did with its next turn."""
    ev, out = row['events'], []
    for k, e in enumerate(ev):
        if e[1] != 'play' or e[2] != 'X' or e[3] not in MOVES or e[6] is None or e[9] is None:
            continue
        if cheb(e[6], e[9]) != 1 or cheb(e[5], e[9]) == 1:
            continue
        nxt = []
        for f in ev[k + 1:]:
            if f[2] == 'O':
                nxt.append(f[3])
                if f[3] in ('pass', 'shot', 'dribble', 'screen', 'hesitate'):
                    break
            elif nxt:
                break
        if not nxt:
            continue
        out.append('pass' if 'pass' in nxt else 'shot' if 'shot' in nxt else 'dribble' if 'dribble' in nxt else 'other')
    return out


def map_error(rows, cal):
    """The calibrated map's error on a run: the root mean square of (the map's reading less what the possession went on
    to earn), over open-play positions, with a bootstrap interval over possessions."""
    per = []
    for r in rows:
        se = n = 0
        for clock, banked, hand, o_to_act in r['reads']:
            m = cal['maps'].get(f"{PHASE(clock)}{'O' if o_to_act else 'X'}")
            x = hand - banked
            y = (m['y'][0] + (m['y'][1] - m['y'][0]) * (x - m['x'][0]) / (m['x'][1] - m['x'][0])) if m else x
            se += (y - (r['value'] - banked)) ** 2
            n += 1
        per.append((se, n))
    rm = lambda v: math.sqrt(sum(a for a, _ in v) / max(1, sum(b for _, b in v)))
    rnd = random.Random(18)
    bs = sorted(rm([rnd.choice(per) for _ in per]) for _ in range(400))
    return dict(positions=sum(b for _, b in per), error=round(rm(per), 2), interval=[round(bs[10], 2), round(bs[389], 2)])


def cmd_fidelity(*sizes):
    from playmaker_engine import decide
    cal = decide.learned_weights()['calibration']
    contexts = pool()['contexts']
    rep = {}
    for size in sizes or ('off', '1', '2', '3'):
        rows = json.load(open(os.path.join(WORK, f'trace_{size}.json')))['rows']
        n = len(rows)
        shots = [s for r in rows for s in shots_of(r, contexts)]
        taken = [s for s in shots if not s.get('stolen')]
        cont = [s for s in taken if s['contester'] >= 0]
        open_ = [s for s in taken if s['contester'] == -1]
        late, early = [s for s in cont if s['late']], [s for s in cont if not s['late']]
        ep = [(x, r['points']) for r in rows for x in extra_pass(r)]
        ends = [r['end'] + [r['decisions']] for r in rows]
        e = L.endings(ends)
        shot_ph = lambda x: x[0] in ('shot', 'free_throws')
        kept = sum(sum(1 for x in ends if PHASE(x[1]) >= k) - sum(1 for x in ends if PHASE(x[1]) == k and shot_ph(x)) for k in range(1, 7))
        ran = lambda x: x[0] == 'turnover_end' and x[1] <= 2 and x[2] <= 0
        lost = sum(1 for x in ends if not shot_ph(x) and not ran(x))
        pts = mean([r['points'] for r in rows])
        by_last = lambda group, key, kinds: {k: dict(share=share(sum(1 for s in group if s[key] == k), len(group)),
                                                     points=mean([s['earned'] for s in group if s[key] == k])) for k in kinds}
        rep[size] = dict(
            possessions=n, shots=len(taken),
            usual=dict(points=pts, shots_in_phases_1_and_2=round(e['shot_by_phase']['1'] + e['shot_by_phase']['2'], 3),
                       shot_by_phase=e['shot_by_phase'], decisions=e['decisions'],
                       clock_ran_out=share(round(e['clock_ran_out'] * n), n), lost_in_100_phases_kept=share(lost, kept)),
            help=dict(contested=share(len(cont), len(taken)), open=share(len(open_), len(taken)),
                      early=share(len(early), len(cont)), late=share(len(late), len(cont)),
                      by_a_helper=share(sum(1 for s in cont if s['helper']), len(cont)),
                      late_from_how_far=mean([s['from_far'] for s in late]),
                      late_from_3_or_more=share(sum(1 for s in late if s['from_far'] >= 3), len(late)),
                      points_allowed=dict(open=mean([s['earned'] for s in open_]), early=mean([s['earned'] for s in early]),
                                          late=mean([s['earned'] for s in late]))),
            closeouts=by_last(cont, 'contest_last', ('none', 'move', 'qs', 'sprint')),
            rushed_contests=share(sum(1 for s in cont if s['contest_rushed']), len(cont)),
            contest_fouls=share(sum(1 for s in cont if s['fouled']), len(cont)),
            shots_set_and_rushed=dict(set=dict(share=share(sum(1 for s in taken if not s['shooter_rushed']), len(taken)),
                                               points=mean([s['earned'] for s in taken if not s['shooter_rushed']])),
                                      rushed=dict(share=share(sum(1 for s in taken if s['shooter_rushed']), len(taken)),
                                                  points=mean([s['earned'] for s in taken if s['shooter_rushed']]))),
            shots_by_last_movement=by_last(taken, 'shooter_last', ('none', 'move', 'qs', 'sprint')),
            shots_by_how=by_last(taken, 'how', ('catch and shoot', 'off the dribble or a movement', 'from a standstill')),
            extra_pass=dict(closeouts=len(ep), **{k: dict(share=share(sum(1 for x, _ in ep if x == k), len(ep)),
                                                          possession_points=mean([p for x, p in ep if x == k]))
                                                  for k in ('pass', 'shot', 'dribble', 'other')}),
            archetypes=dict(
                shooters_by_quick_step={str(q): dict(shots=sum(1 for s in taken if s['shooter_qs'] == q),
                                                     rushed=share(sum(1 for s in taken if s['shooter_qs'] == q and s['shooter_rushed']),
                                                                  sum(1 for s in taken if s['shooter_qs'] == q)),
                                                     points=mean([s['earned'] for s in taken if s['shooter_qs'] == q])) for q in (0, 1, 2)},
                contesters_by_quick_step={str(q): dict(contests=sum(1 for s in cont if s['contester_qs'] == q),
                                                       rushed=share(sum(1 for s in cont if s['contester_qs'] == q and s['contest_rushed']),
                                                                    sum(1 for s in cont if s['contester_qs'] == q)),
                                                       points_allowed=mean([s['earned'] for s in cont if s['contester_qs'] == q]))
                                          for q in (0, 1, 2)}),
            map_error=map_error(rows, cal))
    json.dump(rep, open(os.path.join(RUN, 'fidelity.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def cmd_speed():
    """The time to finish 1 pair at each level on the hand boards' 22 decisions, under today's rules and each size
    (one warm engine each), against docs/SPEED_BUDGET.md."""
    positions, contexts = L.hand_boards()
    target = dict(rookie=(0.3, 1.0), starter=(1.0, 2.0), allstar=(2.5, 3.0))
    rep = {}
    for size in ('off', '1', '2', '3'):
        pols = {lv: dict(engine(lv), noise=0.0) for lv in target}
        L.run_jobs('search', positions[:6], contexts, chunks=1, control=size, policies=pols)
        rows, _ = L.run_jobs('search', positions + positions, contexts, chunks=1, control=size, policies=pols)
        rows = rows[len(positions):]
        rep[size] = {}
        for lv in target:
            v = sorted(r['by'][lv]['seconds'] for r in rows)
            p90 = v[int(0.9 * (len(v) - 1) + 0.5)]
            rep[size][lv] = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(p90, 3), desktop_target=target[lv][0],
                                 fits_desktop=p90 <= target[lv][0], phone=round(4 * p90, 2), phone_target=target[lv][1])
        print(size, {lv: (x['median'], x['nine_in_ten']) for lv, x in rep[size].items()}, flush=True)
    json.dump(rep, open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
