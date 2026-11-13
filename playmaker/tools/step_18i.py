"""Step 18i: FIBA rules for single possessions (three seconds, closely guarded, the fouled shot, the foul situation).

  python3 tools/step_18i.py trace <tag> <n> [off|on] [seed]   All-Star self-play, every action kept; 'off': the three
                                                              rules off (the game before this step), 'on': on
  python3 tools/step_18i.py measures <tag> [<tag> ...]        the measures of each run, side by side -> measures.json
  python3 tools/step_18i.py speed [rounds]                    the time to finish 1 pair: step 18g's code and this step's
  python3 tools/step_18i.py fouls <tag>                       fouls a possession in a kept run, with its uncertainty
"""
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18i')
import sense_18h as S                                  # noqa: E402
import step_18g as G                                   # noqa: E402
L, RUN, WORK, tally = S.L, S.RUN, S.WORK, S.tally
RULES = ('three_seconds', 'closely_guarded', 'fiba_fouled_shot')


def rules_of(setting):
    """'off' / 'on': all three; or 'three_seconds=on,closely_guarded=off'."""
    if setting in ('off', 'on'):
        return {k: setting for k in RULES}
    return dict(kv.split('=') for kv in setting.split(',')) if setting else {}


def cmd_trace(tag, n='160', setting='on', seed='1', fouls=''):
    pl = G.pool()
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'])
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    extra = dict(rules=rules_of(setting))
    if fouls:
        f, left = fouls.split(',')
        extra['fouls'] = dict(team_fouls=int(f), quarter_left=int(left))
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), **extra)
    json.dump(dict(size=tag, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)])


def _per100(k, n):
    p, lo, hi = L.wilson(k, n)
    return dict(n=k, of=n, per_100=round(100 * p, 1), interval=[round(100 * lo, 1), round(100 * hi, 1)])


def cmd_measures(*tags):
    import step_18d as D
    D.RUN, D.WORK, D.L.WORK = RUN, WORK, WORK
    D.cmd_fidelity(*tags)
    fid = json.load(open(os.path.join(RUN, 'fidelity.json')))
    rep = {}
    for tag in tags:
        rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
        n = len(rows)
        viol = [(r.get('result') or {}).get('violation') or '' for r in rows]
        kinds = [(r.get('result') or {}).get('kind') or 'unfinished' for r in rows]
        # the ball handler at each turn of the offence: closely guarded or not, and what he did with that turn
        seen = guarded = 0
        did = {}
        held = {1: 0, 2: 0}
        picked = 0
        for r in rows:
            for g in r.get('guards', []):
                at, phase, ball, cg, grd, key = g
                seen += 1
                if grd & 3 == 2:
                    picked += 1
                h = grd >> 2 & 3
                if h in held:
                    held[h] += 1
                if not cg:
                    continue
                guarded += 1
                what = 'nothing'
                for e in r['events'][at:]:
                    if e[2] != 'O':
                        break
                    if e[3] in ('pass', 'shot', 'dribble'):
                        what = e[3]
                        break
                    if e[3] in ('move', 'qs', 'sprint') and e[4] == ball:
                        what = 'moved with the ball'
                        break
                did[what] = did.get(what, 0) + 1
        fouled = [r for r in rows if (r.get('result') or {}).get('kind') == 'free_throws']
        on_shot = [r for r in fouled if r['result'].get('shot_type')]
        steals = [sum(1 for e in r['events'] if e[3] == 'steal') for r in rows]
        fouls = [r.get('fouls', 0) for r in rows]
        rep[tag] = dict(
            possessions=n,
            points=G._ci([r['points'] for r in rows]),
            violations=dict(three_seconds=_per100(viol.count('three_seconds'), n),
                            closely_guarded=_per100(viol.count('closely_guarded'), n)),
            ended_by={k: kinds.count(k) for k in sorted(set(kinds))},
            ball_handler=dict(turns_of_the_offence=seen, closely_guarded=_per100(guarded, seen),
                              what_he_did_when_closely_guarded={k: _per100(v, guarded) for k, v in sorted(did.items())},
                              turns_with_the_count_at_1=held[1], at_2=held[2], turns_picked_up=picked),
            fouled_shots=dict(shots=_per100(len(on_shot), n), scored=G._ci([r['points'] for r in on_shot]),
                              all_free_throw_endings=len(fouled)),
            steals_tried_a_possession=G._ci(steals),
            defence_fouls_a_possession=G._ci(fouls),
            usual=fid.get(tag))
    json.dump(rep, open(os.path.join(RUN, 'measures.json'), 'w'), indent=1)
    for tag in tags:
        r = rep[tag]
        print('==', tag)
        for k in ('points', 'violations', 'ended_by', 'ball_handler', 'fouled_shots', 'steals_tried_a_possession', 'defence_fouls_a_possession'):
            print('  ', k, json.dumps(r[k]))
        u = r['usual']
        print('   shots by phase', u['usual']['shot_by_phase'], '| contested', u['help']['contested'], '| lost in 100 phases kept', u['usual']['lost_in_100_phases_kept'])


def cmd_speed(rounds='2'):
    """D-161: step 18g's code and this step's code (the rules as they default), timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18g as G; "
            "print('RESULT ' + json.dumps(G._timed({})))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18g/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18g')).stdout
        one = {'18g': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18i, the three rules off'] = G._timed(dict(rules=rules_of('off')))
        one['18i, the three rules on'] = G._timed(dict(rules=rules_of('on')))
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18g's code, this step's with the three rules off, and with them on", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
