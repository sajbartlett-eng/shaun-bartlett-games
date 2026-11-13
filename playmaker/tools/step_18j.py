"""Step 18j: the soft and hard contest (D-177), the penalty's bite (D-179), and seeing "step in, then Steal" coming.

  python3 tools/step_18j.py trace <tag> <n> [i|j] [seed] [k=v ...]   All-Star self-play, every action kept. 'i': the
                                                                      rules as step 18i left them; 'j': with the soft
                                                                      and hard contest and the FIBA steal foul on.
                                                                      k=v: engine switches for both sides
  python3 tools/step_18j.py measures <tag> [<tag> ...]               the measures of each run -> measures.json
  python3 tools/step_18j.py speed [rounds]                           the time to finish 1 pair: 18i's code and this step's
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
os.environ.setdefault('SENSE_RUN', 'step18j')
import sense_18h as S                                  # noqa: E402
import step_18g as G                                   # noqa: E402
L, RUN, WORK, tally = S.L, S.RUN, S.WORK, S.tally
FIBA = ('three_seconds', 'closely_guarded', 'fiba_fouled_shot')
NEW = ('soft_contest', 'fiba_steal_foul')


def rules_of(setting):
    r = {k: 'on' for k in FIBA}
    r.update({k: ('on' if setting == 'j' else 'off') for k in NEW})
    return r


def cmd_trace(tag, n='160', setting='j', seed='1', *switches):
    pl = G.pool()
    sw = S._switches(switches) if switches else {}
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'], **sw)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), rules=rules_of(setting))
    json.dump(dict(size=tag, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)])


def _share(k, n):
    if not n:
        return None
    p, lo, hi = L.wilson(k, n)
    return dict(n=k, of=n, pct=round(100 * p, 1), interval=[round(100 * lo, 1), round(100 * hi, 1)])


def _dist(sq):
    x, y = 'ABCDEFGHIJKLMNOPQ'.index(sq[0]), int(sq[1:])
    return max(abs(x - 8), abs(y - 2))


def cmd_measures(*tags):
    import step_18d as D
    D.RUN, D.WORK, D.L.WORK = RUN, WORK, WORK
    D.cmd_fidelity(*tags)
    fid = json.load(open(os.path.join(RUN, 'fidelity.json')))
    rep = {}
    for tag in tags:
        rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
        n = len(rows)
        res = [r.get('result') or {} for r in rows]
        shots = [(r, x) for r, x in zip(rows, res) if x.get('kind') in ('shot', 'free_throws') and x.get('shot_type')]
        threes = [(r, x) for r, x in shots if x.get('points') == 3]
        soft = [(r, x) for r, x in shots if x.get('kind') == 'shot' and x.get('contester', -1) >= 0 and x.get('soft')]
        hard = [(r, x) for r, x in shots if (x.get('kind') == 'shot' and x.get('contester', -1) >= 0 and not x.get('soft')) or x.get('kind') == 'free_throws']
        place = dict(front=0, side=0, behind=0)
        for r, x in hard:
            if not r.get('endX') or not r.get('shots'):
                continue
            d, c = _dist(r['endX'][x['contester']]), _dist(r['shots'][-1]['o'][x['shooter']])
            place['front' if d < c else 'side' if d == c else 'behind'] += 1
        viol = [x.get('violation') or '' for x in res]
        steals = [sum(1 for e in r['events'] if e[3] == 'steal') for r in rows]
        steal_fouls = [r.get('fouls', 0) - (1 if (x.get('kind') == 'free_throws' and x.get('shot_type')) else 0) for r, x in zip(rows, res)]
        rep[tag] = dict(
            possessions=n, points=G._ci([r['points'] for r in rows]),
            shots=len(shots),
            shots_contested=_share(len(soft) + len(hard), len(shots)),
            by_a_soft_contest=_share(len(soft), len(shots)), by_a_hard_contest=_share(len(hard), len(shots)),
            threes_contested=_share(sum(1 for r, x in soft + hard if x.get('points') == 3), len(threes)),
            hard_contests_by_position=place,
            fouled_shots=_share(sum(1 for r, x in shots if x.get('kind') == 'free_throws'), n),
            steals_tried_a_possession=G._ci(steals), steal_fouls_a_possession=G._ci(steal_fouls),
            defence_fouls_a_possession=G._ci([r.get('fouls', 0) for r in rows]),
            violations=dict(three_seconds=viol.count('three_seconds'), closely_guarded=viol.count('closely_guarded')),
            usual=fid.get(tag))
    json.dump(rep, open(os.path.join(RUN, 'measures.json'), 'w'), indent=1)
    for tag in tags:
        r = rep[tag]
        print('==', tag)
        for k in ('points', 'shots', 'shots_contested', 'by_a_soft_contest', 'by_a_hard_contest', 'threes_contested', 'hard_contests_by_position', 'fouled_shots',
                  'steals_tried_a_possession', 'steal_fouls_a_possession', 'defence_fouls_a_possession', 'violations'):
            print('  ', k, json.dumps(r[k]))
        u = r['usual']
        print('   shots by phase', u['usual']['shot_by_phase'], '| lost in 100 phases kept', u['usual']['lost_in_100_phases_kept'], '| rushed shots', u['shots_set_and_rushed']['rushed']['share'])


def cmd_speed(rounds='2'):
    """D-161: step 18i's code and this step's code as it defaults, timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18g as G; "
            "print('RESULT ' + json.dumps(G._timed({})))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18i/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18i')).stdout
        one = {'18i': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18j'] = G._timed({})
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18i's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)




def cmd_fault(pid='closeout, shooter cannot move', name='your order', *switches):
    """Part 1, no code change: after the named candidate, the offence's reading of each of its turns; then, for its
    turn that keeps the ball where it is, what the defence finds when it is the one to act, and what play gives."""
    positions, answers = S.load()
    p = next(q for q in positions if q['id'] == pid)
    c = next(c for c in p['candidates'] if name in c['name'])
    pol = {'p': L.policy('allstar', 2, 0.0, **(S._switches(switches) if switches else {}))}
    rows, _ = L.run_jobs('search', [dict(id='0', state=p['state'], ctx=0, pre=c['turn'])], [p['ctx']], chunks=1, policies=pol, **S.RULE)
    res = rows[0]['by']['p']['results']
    print('after', c['name'][:70], '| the offence reads:')
    for v, t in res[:8]:
        print('   ', round(v, 2), S.words(t))
    ball = p['state']['ball']
    keeps = [(v, t) for v, t in res if all(a[0] in ('move', 'qs', 'sprint', 'hesitate', 'screen') and a[2] != ball for a in t)]
    if not keeps:
        print('no turn keeps the ball where it is')
        return
    v0, hold = keeps[0]
    rows, _ = L.run_jobs('search', [dict(id='0', state=p['state'], ctx=0, pre=c['turn'] + hold)], [p['ctx']], chunks=1, policies=pol, **S.RULE)
    print('the offence holds the ball:', S.words(hold), '| it reads', round(v0, 2), '| then the defence, to act, reads:')
    for v, t in rows[0]['by']['p']['results'][:6]:
        print('   ', round(v, 2), S.words(t))
    rows, secs = L.run_jobs('rollout', [dict(id='0', state=p['state'], ctx=0, seed=S._seed(pid, 0), turns=[c['turn'] + hold])], [p['ctx']], chunks=1,
                            n=16, seed=7, keep=True, ends=True, policies=dict(O=L.policy('allstar', 2, L.profiles()['allstar']['noise'], **S.REF),
                                                                              X=L.policy('allstar', 2, L.profiles()['allstar']['noise'], **S.REF)), **S.RULE)
    t = rows[0]['turns'][0]
    from collections import Counter
    print('by play, the ball held:', round(sum(t['values']) / max(1, len(t['values'])), 2), dict(Counter(t['ends'])))
    tally('the fault shown: one position, 16 play-outs', secs)


def cmd_after(pid, *switches):
    """Each named candidate of a position, and what the other side's best reply to it reads (searches only)."""
    positions, answers = S.load()
    p = next(q for q in positions if q['id'] == pid)
    pol = {'p': L.policy('allstar', 2, 0.0, **(S._switches(switches) if switches else {}))}
    cands = [c for c in p['candidates'] if not c.get('added_by')]
    rows, _ = L.run_jobs('search', [dict(id=str(i), state=p['state'], ctx=0, pre=c['turn']) for i, c in enumerate(cands)], [p['ctx']], chunks=1, policies=pol, **S.RULE)
    for r in sorted(rows, key=lambda r: int(r['id'])):
        res = r['by']['p']['results']
        print(cands[int(r['id'])]['name'][:64].ljust(66), '| reply:', round(res[0][0], 2), S.words(res[0][1])[:60])


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
