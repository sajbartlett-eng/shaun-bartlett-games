"""Step 18r (D-198): fouls and turnovers in points, play on; no shot from the rim's own square. The refit and what the
rules do to play.

  python3 tools/step_18r.py trace TAG [n] [level] [seed] [old]   self-play, the app's rules (old: D-198 switched off)
  python3 tools/step_18r.py stats TAG [TAG ...]                  reaches, fouls, turnovers and points a possession
  python3 tools/step_18r.py maps write|no level=TAG ...          the levels' maps refitted (step 18h's fit)
  python3 tools/step_18r.py speed [rounds]                       step 18q's code and this step's, timed in turn
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18r')
os.environ.setdefault('SENSE_18N', '1')
import step_18q as Q                                    # noqa: E402
P, O, T, L, RUN, WORK, tally, RULES = Q.P, Q.O, Q.T, Q.L, Q.RUN, Q.WORK, Q.tally, Q.RULES
OLD = dict(RULES, points_play_on='off', no_rim_shot='off')      # the app's rules before D-198


def cmd_trace(tag, n='200', level='allstar', seed='1', old=''):
    pl = O.G.pool()
    T.pool_is_current(pl)
    pol = L.policy(level, 2, L.profiles()[level]['noise'])
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), rules=OLD if old == 'old' else RULES, fouls=T.FOULS)
    json.dump(dict(size=tag, zone=True, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {level}, {n} possessions{", the rules before D-198" if old == "old" else ""})', secs)
    cmd_stats(tag)


def stats(rows):
    n = len(rows)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    c = dict(reaches=0, dribbles=0, intercepts=0, passes=0, actions=0)
    ends, phases, minus = {}, [], 0
    for r in rows:
        k = (r.get('result') or {}).get('shot_type') or (r.get('result') or {}).get('kind')
        ends[k] = ends.get(k, 0) + 1
        phases.append(max((e[0] for e in r['events']), default=1))
        minus += r['points'] < 0
        for e in r['events']:
            c['actions'] += 1
            if e[3] == 'steal':
                c['reaches'] += 1
            elif e[3] == 'dribble':
                c['dribbles'] += 1
            elif e[3] == 'intercept':
                c['intercepts'] += 1
            elif e[3] == 'pass':
                c['passes'] += 1
    tos = sum(r.get('tos', 0) for r in rows) if any('tos' in r for r in rows) else None
    return dict(possessions=n, points=round(m, 2), low=round(m - ci, 2), high=round(m + ci, 2), a_possession={k: round(v / n, 2) for k, v in c.items()},
                fouls_a_possession=round(sum(r.get('fouls', 0) for r in rows) / n, 2), turnovers_a_possession=None if tos is None else round(tos / n, 2),
                ended_in_a_turnover=round(ends.get('turnover_end', 0) / n, 3), below_zero=minus, phases_a_possession=round(sum(phases) / n, 2), ends=ends)


def cmd_stats(*tags):
    out = {}
    for t in tags:
        path = os.path.join(WORK, f'trace_{t}.json')
        if not os.path.exists(path):
            path = t
        out[os.path.basename(t)] = stats(json.load(open(path))['rows'])
        print(os.path.basename(t), json.dumps(out[os.path.basename(t)]))
    json.dump(out, open(os.path.join(RUN, f'stats_{os.path.basename(tags[0])}.json'), 'w'), indent=1)


def cmd_maps(write='no', *sources):
    import step_18l as S
    S.RUN, S.WORK = RUN, WORK
    S.cmd_maps(write, *sources)


def cmd_speed(rounds='2'):
    """D-161: step 18q's code and this step's, timed in turn, the app's rules as each has them (the lane off)."""
    import subprocess
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18q as Q; "
            "print('RESULT ' + json.dumps(Q.T._timed({}, Q.RULES)))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18q/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18q', SENSE_18N='1')).stdout
        one = {'18q': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18r'] = T._timed({}, RULES)
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair, the app's rules; each round times step 18q's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
