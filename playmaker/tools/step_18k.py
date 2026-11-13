"""Step 18k: one consistent foul price (D-181, D-182) and the defence's shortlist.

  python3 tools/step_18k.py trace <tag> <n> [seed] [k=v ...]        All-Star self-play under the app's rules and the
                                                                     default foul situation (2 team fouls, 8 left)
  python3 tools/step_18k.py measures <tag> [<tag> ...]              the measures of each run -> measures.json
  python3 tools/step_18k.py h2h <tag> <pairs> <a k=v,..> <b k=v,..> the backstop head to head
  python3 tools/step_18k.py speed [rounds] [k=v ...]                the time to finish 1 pair: 18j's code and this step's
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18k')
os.environ.setdefault('SENSE_18K', '1')
import step_18j as J                                   # noqa: E402
S, L, G, RUN, WORK, tally = J.S, J.L, J.G, J.RUN, J.WORK, J.tally
RULES = J.rules_of('j')
FOULS = dict(team_fouls=2, quarter_left=8)             # D-182: the default foul situation


def cmd_trace(tag, n='160', seed='1', *switches):
    pl = G.pool()
    sw = S._switches(switches) if switches else {}
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **sw)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), rules=RULES, fouls=FOULS)
    json.dump(dict(size=tag, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)])


def _per100(k, n):
    """A count over n possessions as a rate per 100 possessions, with an interval (the count taken as Poisson)."""
    import math
    half = 1.96 * math.sqrt(max(k, 1)) / n * 100
    return dict(n=k, of=n, per_100=round(100 * k / n, 1), interval=[round(max(0.0, 100 * k / n - half), 1), round(100 * k / n + half, 1)])


def cmd_measures(*tags):
    J.cmd_measures(*tags)
    rep = json.load(open(os.path.join(RUN, 'measures.json')))
    for tag in tags:
        rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
        n = len(rows)
        res = [r.get('result') or {} for r in rows]
        tried = sum(1 for r in rows for e in r['events'] if e[3] == 'steal')
        won = sum(1 for r, x in zip(rows, res) if x.get('kind') in ('turnover_end', 'steal') and not x.get('violation') and r['events'] and r['events'][-1][3] == 'steal')
        fouls = sum(r.get('fouls', 0) - (1 if (x.get('kind') == 'free_throws' and x.get('shot_type')) else 0) for r, x in zip(rows, res))
        pen = sum(1 for x in res if x.get('kind') == 'free_throws' and not x.get('shot_type'))
        rep[tag]['basketball'] = dict(steals_tried=_per100(tried, n), steals_won=_per100(won, n), steal_fouls=_per100(fouls, n),
                                      possessions_ended_by_penalty_free_throws=_per100(pen, n))
        print('==', tag, '| per 100 possessions: Steals tried', rep[tag]['basketball']['steals_tried']['per_100'], rep[tag]['basketball']['steals_tried']['interval'],
              '| won', rep[tag]['basketball']['steals_won']['per_100'], rep[tag]['basketball']['steals_won']['interval'],
              '| steal fouls', rep[tag]['basketball']['steal_fouls']['per_100'], rep[tag]['basketball']['steal_fouls']['interval'], '| ended by penalty free throws', pen)
    json.dump(rep, open(os.path.join(RUN, 'measures.json'), 'w'), indent=1)


def cmd_h2h(tag, pairs='80', a_on='', b_on=''):
    """The backstop: a against b at the All-Star under this step's rules and foul situation, paired possessions."""
    lv = 'allstar'
    a = L.policy(lv, 2, L.profiles()[lv]['noise'], **S._switches([x for x in a_on.split(',') if x]))
    b = L.policy(lv, 2, L.profiles()[lv]['noise'], **S._switches([x for x in b_on.split(',') if x]))
    pl, rows, secs, k = G.pool(), [], 0.0, 0
    starts = pl['starts']
    while len(rows) < int(pairs):
        k += 1
        n = min(40, int(pairs) - len(rows))
        part = [starts[(i + 37 * k) % len(starts)] for i in range(n)]
        part = [dict(q, seed=104729 * (i + 1) + 15485863 * k) for i, q in enumerate(part)]
        r, sec = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=2000 + k, a=a, b=b, rules=RULES, fouls=FOULS)
        rows += r
        secs += sec
        st = L.h2h_stats(rows, delta=1.0)
        tally(f'head to head {tag}, pairs {len(rows) - n + 1} to {len(rows)}', sec)
        print(tag, len(rows), st['mean_difference'], st['interval'], st['wins'], st['losses'], st['ties'], round(secs / 3600, 2), flush=True)
        json.dump(dict(tag=tag, a=a_on or 'the default', b=b_on or 'the default', stats=st, core_hours=round(secs / 3600, 2)),
                  open(os.path.join(RUN, f'h2h_{tag}.json'), 'w'), indent=1)


def _timed(sw):
    positions, contexts = L.hand_boards()
    pols = {lv: L.policy(lv, 2, 0.0, **sw) for lv in ('rookie', 'starter', 'allstar')}
    L.run_jobs('search', positions[:6], contexts, chunks=1, policies=pols, fouls=FOULS)
    rows, _ = L.run_jobs('search', positions + positions, contexts, chunks=1, policies=pols, fouls=FOULS)
    rows = rows[len(positions):]
    out = {}
    for lv in pols:
        v = sorted(r['by'][lv]['seconds'] for r in rows)
        out[lv] = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(v[int(0.9 * (len(v) - 1) + 0.5)], 3), slowest=round(v[-1], 3))
    return out


def cmd_speed(rounds='2', *switches):
    """D-161: step 18j's code and this step's (the config as it stands, with the switches given), timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18g as G; "
            "print('RESULT ' + json.dumps(G._timed({})))")
    sw = S._switches(switches) if switches else {}
    name = 'speed' + ('_' + '_'.join(f'{k}-{v}' for k, v in sorted(sw.items())) if sw else '')
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18j/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18j')).stdout
        one = {'18j': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18k'] = _timed(sw)
        tally(f'speed, round {r + 1} (one core){" " + " ".join(switches) if switches else ""}', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18j's code and this step's", switches=sw, rounds=rep),
                  open(os.path.join(RUN, name + '.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
