"""Step 18g: the zone of influence (rules.zone, D-167), measured by how the game plays.

  python3 tools/step_18g.py trace <tag> <n> [zone]      All-Star self-play with every action kept and the stance rows
  python3 tools/step_18g.py measures <tag> [<tag> ...]  the fidelity measures of each run, side by side -> measures.json
  python3 tools/step_18g.py speed [rounds]              the time to finish 1 pair: step 18h's code, this step's, and the zone on
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
os.environ.setdefault('SENSE_RUN', 'step18g')
import sense_18h as S                                  # noqa: E402
L, RUN, WORK, tally = S.L, S.RUN, S.WORK, S.tally


def pool():
    return json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))['senior/pro/digital']


def cmd_trace(tag, n='120', zone='', seed='1'):
    """Self-play at the All-Star on the default as it stands; zone = 'zone' plays under rules.zone."""
    pl, t0 = pool(), time.time()
    pol = L.policy('allstar', 2, L.profiles()['allstar']['noise'])
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), **(dict(zone=True) if zone == 'zone' else {}))
    json.dump(dict(size=tag, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play ({tag}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    print(tag, len(rows), 'possessions', round(m, 2), [round(m - ci, 2), round(m + ci, 2)])


def _ci(v):
    if not v:
        return None
    m, sd, ci = L.mean_ci(v)
    return dict(n=len(v), mean=round(m, 2), interval=[round(m - ci, 2), round(m + ci, 2)])


def _share(k, n):
    if not n:
        return None
    p, lo, hi = L.wilson(k, n)
    return dict(n=k, of=n, pct=round(100 * p, 1), interval=[round(100 * lo, 1), round(100 * hi, 1)])


def _in_phase(rows):
    """Each turn of the offence, from the kept actions: [its number in the phase, the offence's movements and passes so
    far this phase, defenders with their Move still in hand, defenders with any movement still in hand, zone squares on
    the court]. A defender's Move is spent by a Move or a Sprint, his Quick Step by a Quick Step or a Sprint; a Dribble
    won against him takes both. The stance rows are the offence's turns in order."""
    out = []
    for r in rows:
        qs_card = [c['qs'] for c in r['cards_x']] if r.get('cards_x') else None
        drib = iter(r['dribbles'])
        phase, turn, acts, moved, quick, beaten, prev, k = None, 0, 0, set(), set(), set(), None, 0
        for e in r['events']:
            if e[0] != phase:
                phase, turn, acts, moved, quick, beaten, prev = e[0], 0, 0, set(), set(), set(), None
            if e[2] == 'O' and prev != 'O':
                st = r['stances'][k] if k < len(r['stances']) else None
                k += 1
                turn += 1
                if st is not None:
                    out.append([turn, acts, 5 - len(moved | beaten), 5 - len((moved & quick) | beaten), st[4]])
            prev = e[2]
            if e[2] == 'O':
                if e[3] in ('move', 'qs', 'sprint', 'pass'):
                    acts += 1
                if e[3] == 'dribble':
                    d = next(drib, None)
                    if d and d[1] and e[7] is not None and e[7] >= 0:
                        beaten.add(e[7])
            elif e[2] == 'X':
                if e[3] in ('move', 'sprint'):
                    moved.add(e[4])
                if e[3] in ('qs', 'sprint'):
                    quick.add(e[4])
    return out


def _within(rows):
    v = _in_phase(rows)
    by_turn, by_acts = {}, {}
    for t, a, mv, anym, sq in v:
        by_turn.setdefault(min(t, 4), []).append((mv, anym, sq))
        by_acts.setdefault('0' if a == 0 else '1 or 2' if a <= 2 else '3 or 4' if a <= 4 else '5 or more', []).append((mv, anym, sq))
    row = lambda x: dict(turns=len(x), defenders_with_their_move_in_hand=_ci([y[0] for y in x]),
                         defenders_with_any_movement_in_hand=_ci([y[1] for y in x]), zone_squares_shaded=_ci([y[2] for y in x]))
    return dict(by_the_offences_turn_in_the_phase={('4th or later' if k == 4 else f'turn {k}'): row(x) for k, x in sorted(by_turn.items())},
                by_offence_movements_and_passes_so_far_this_phase={k: row(by_acts[k]) for k in ('0', '1 or 2', '3 or 4', '5 or more') if k in by_acts})


def cmd_measures(*tags):
    """Step 18g's own measures from the kept runs (the usual ones come from step 18d's fidelity tool)."""
    import step_18d as D
    D.RUN, D.WORK, D.L.WORK = RUN, WORK, WORK
    D.cmd_fidelity(*tags)
    fid = json.load(open(os.path.join(RUN, 'fidelity.json')))
    rep = {}
    for tag in tags:
        rows = json.load(open(os.path.join(WORK, f'trace_{tag}.json')))['rows']
        n = len(rows)
        st = [x for r in rows for x in r['stances']]
        # [phase, moves, passes, caught, strength, both, cover, block, neither, mid, out]
        caught = [x for x in st if x[3]]
        buckets = {}
        for lo, hi, name in ((0, 2, '0 to 2'), (3, 5, '3 to 5'), (6, 9, '6 to 9'), (10, 99, '10 or more')):
            buckets[name] = _ci([x[4] for x in caught if lo <= x[1] + x[2] <= hi])
        first = _ci([x[4] for x in st if x[1] + x[2] == 0])
        adj = sum(x[5] + x[6] + x[7] + x[8] for x in st)
        drib = [d for r in rows for d in r['dribbles']]
        won = set(i for i, r in enumerate(rows) if any(d[1] for d in r['dribbles']))
        tried = set(i for i, r in enumerate(rows) if r['dribbles'])
        passes = [sum(1 for e in r['events'] if e[3] == 'pass') for r in rows]
        offball = [sum(1 for e in r['events'] if e[2] == 'O' and e[3] in ('move', 'qs', 'sprint') and e[4] != e[8]) for r in rows]
        onball = [sum(1 for e in r['events'] if e[2] == 'O' and e[3] in ('move', 'qs', 'sprint') and e[4] == e[8]) for r in rows]
        steals = [sum(1 for e in r['events'] if e[3] == 'steal') for r in rows]
        rep[tag] = dict(
            possessions=n,
            zone_squares_on_the_court=dict(before_the_offence_has_moved=first, when_the_ball_is_caught_by_offence_movements_and_passes_before=buckets,
                                           at_every_turn_of_the_offence=_ci([x[4] for x in st])),
            defenders_next_to_the_ball_handler=dict(
                seen=adj,
                arrow_on_him_and_a_step_to_the_rim_denied=_share(sum(x[5] for x in st), adj),
                arrow_on_him_only=_share(sum(x[6] for x in st), adj),
                a_step_denied_only=_share(sum(x[7] for x in st), adj),
                neither=_share(sum(x[8] for x in st), adj)),
            where_the_denied_step_lies=dict(the_middle_is_taken_away=_share(sum(x[9] for x in st), sum(x[9] + x[10] for x in st)),
                                            the_outside_is_taken_away=_share(sum(x[10] for x in st), sum(x[9] + x[10] for x in st))),
            dribbles=dict(a_possession=_ci([len(r['dribbles']) for r in rows]), won=_share(sum(d[1] for d in drib), len(drib)),
                          points_when_one_is_won=_ci([rows[i]['points'] for i in won]),
                          points_when_one_is_tried_and_none_won=_ci([rows[i]['points'] for i in tried - won]),
                          points_when_none_is_tried=_ci([r['points'] for i, r in enumerate(rows) if i not in tried])),
            a_possession=dict(passes=_ci(passes), off_ball_movements=_ci(offball), ball_handler_movements=_ci(onball), steals_tried=_ci(steals)),
            within_a_phase=_within(rows),
            usual=fid.get(tag))
    json.dump(rep, open(os.path.join(RUN, 'measures.json'), 'w'), indent=1)
    for tag in tags:
        r = rep[tag]
        print('==', tag)
        for k in ('within_a_phase', 'defenders_next_to_the_ball_handler', 'where_the_denied_step_lies', 'dribbles', 'a_possession'):
            print('  ', k, json.dumps(r[k]))


def _timed(job, runs=1):
    """9 decisions in 10 (and the median) to finish 1 pair on the hand boards' 22 decisions, for each level."""
    positions, contexts = L.hand_boards()
    pols = {lv: L.policy(lv, 2, 0.0) for lv in ('rookie', 'starter', 'allstar')}
    out = {}
    for _ in range(runs):
        L.run_jobs('search', positions[:6], contexts, chunks=1, policies=pols, **job)
        rows, _s = L.run_jobs('search', positions + positions, contexts, chunks=1, policies=pols, **job)
        rows = rows[len(positions):]
        for lv in pols:
            v = sorted(r['by'][lv]['seconds'] for r in rows)
            one = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(v[int(0.9 * (len(v) - 1) + 0.5)], 3), slowest=round(v[-1], 3))
            if lv not in out or one['nine_in_ten'] < out[lv]['nine_in_ten']:
                out[lv] = one
    return out


def cmd_speed(rounds='2'):
    """D-161: step 18h's code, this step's code, and this step's with rules.zone on, timed in turn."""
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18f as F; "
            "print('RESULT ' + json.dumps(F._timed({lv: F._level(lv) for lv in F.TARGET}, runs=1)))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18h/playmaker', capture_output=True, text=True, check=True).stdout
        one = {'18h': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18g'] = _timed({})
        one['18g, the zone on'] = _timed(dict(zone=True))
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair; each round times step 18h's code, this step's, and this step's with the zone on", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
