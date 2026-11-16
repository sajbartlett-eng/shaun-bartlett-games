"""Step 18q (D-196, stage 1 again): the way to the rim next phase in the reading (eval.lane), tested by the design checks.

  python3 tools/step_18q.py checks on|off     the reading and the search on Shaun's board (checks 1, 2, 3, 4)
  python3 tools/step_18q.py played TAG on|off check 1 by forced lines, 16 play-outs a line
  python3 tools/step_18q.py speed [rounds]    step 18p's code and this step's, timed in turn
"""
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ.setdefault('SENSE_RUN', 'step18q')
os.environ.setdefault('SENSE_18N', '1')
import step_18p as P                                    # noqa: E402
O, T, L, RUN, WORK, tally, RULES = P.O, P.T, P.L, P.RUN, P.WORK, P.tally, P.RULES


class Eng(P.Eng):
    """The JavaScript engine with the lane reading on or off (the Python reading follows the same switch)."""

    def __init__(self, lane):
        super().__init__(False)
        self.lane = lane
        self.e.call('setLane', 'true' if lane else 'false')

    def reading(self, s):
        from playmaker_engine.decide import Read, CONFIG
        keep = CONFIG['eval'].get('lane')
        CONFIG['eval']['lane'] = self.lane
        try:
            return Read(s).leaf()
        finally:
            CONFIG['eval']['lane'] = keep


def after_beat(xs, arrows):
    """Shaun's board with the defence on xs facing arrows, after the point guard has beaten X1 and X1's reach (if he
    has one) has missed: the offence to act. (step_18p._after_beat for any defence.)"""
    keep = O.HIS
    O.HIS = (list(xs), list(arrows))
    try:
        return P._after_beat(x4=xs[3], a4=arrows[3], x5=xs[4], a5=arrows[4])
    finally:
        O.HIS = keep


def cmd_probe(lane='on', *variants):
    """A quick look by the search: variants as X2,X3 squares and arrows, e.g. D8:NW,Q8:W"""
    eng = Eng(lane == 'on')
    for v in variants:
        (x2, a2), (x3, a3) = [t.split(':') for t in v.split(',')]
        a = after_beat(['J10', x2, x3, 'B4', 'P2'], ['NW', a2, a3, 'SW', 'NE'])
        res = eng.search(a)
        drive = [r for r in res if r[1] and r[1][0].startswith('O1 Sprint')]
        spr = P._act(a, 'sprint', 0, 'I6')
        d = spr
        while d.side == 'O' and d.stage == 'play':
            d = P._act(d, 'end_turn')
        dres = eng.search(d)
        print(v, 'reading', round(eng.reading(a), 1), 'choice', res[0][1], round(res[0][0], 1), 'best sprint', drive[0][1] if drive else None, round(drive[0][0], 1) if drive else None,
              'defence answer to the Sprint to I6', dres[0][1], round(dres[0][0], 1), flush=True)


def cmd_checks(lane='on'):
    P.Eng = lambda learned: Eng(lane == 'on')
    P.RUN = RUN
    P.cmd_checks('lane_on' if lane == 'on' else 'lane_off')


def play(named, copies=16, lane=True, seed=1, what='play-outs', sides=None):
    """Each named position played out `copies` times, All-Star against All-Star, the app's rules, the same dice copy by
    copy. lane: the lane reading for both sides, or sides=dict(O=bool, X=bool). Rows are filed by the name they carry."""
    from playmaker_engine import jsbridge
    ctx = jsbridge.ctx_json(named[0][1].ctx)
    sides = sides or dict(O=lane, X=lane)
    pol = {k: L.policy('allstar', 2, L.profiles()['allstar']['noise'], lane=bool(v)) for k, v in sides.items()}
    positions = [dict(id=name, state=jsbridge.state_json(s), ctx=0, seed=104729 * (k + 1) + 7919 * seed) for name, s in named for k in range(copies)]
    rows, secs = L.run_jobs('trace', positions, [ctx], n=1, seed=seed, stances=True, policies=pol, rules=RULES, fouls=T.FOULS)
    tally(f'{what} ({len(named)} positions, {copies} each, the lane reading {sides})', secs)
    out = {name: [] for name, _ in named}
    for r in rows:
        out[r['id']].append(r)
    assert all(len(v) == copies for v in out.values())
    return out


def cmd_played(tag, lane='on', copies='16', lines='four'):
    """Check 1 played, by forced lines: Shaun's board after the beat, the lane open and with help in it."""
    named = []
    for label, kw in (('lane open', {}), ('help in the lane', dict(x4='H5', a4='N', x5='J5', a5='N'))):
        a = P._after_beat(**kw)
        named.append((f'{label}: the offence as it chooses', a))
        named.append((f'{label}: O1 Sprints into the lane', P._act(a, 'sprint', 0, 'I6')))
    if lines == 'six':
        # the same board with X3 beside his man (P9, facing him) and not between him and the lane: nobody can get between
        a = after_beat(['J10', 'D8', 'P9', 'B4', 'P2'], ['NW', 'NW', 'W', 'SW', 'NE'])
        named.append(('nobody able to get between: the offence as it chooses', a))
        named.append(('nobody able to get between: O1 Sprints into the lane', P._act(a, 'sprint', 0, 'I6')))
    out = play(named, int(copies), lane == 'on', what=f'check 1 played ({tag})')
    rep = {k: P._summary(v) for k, v in out.items()}
    json.dump(rep, open(os.path.join(RUN, f'played_{tag}.json'), 'w'), indent=1)
    json.dump(out, open(os.path.join(WORK, f'played_{tag}_rows.json'), 'w'))
    for k, v in rep.items():
        print(f"{k:45} {v['mean']} ({v['low']} to {v['high']}) {v['ends']} first: {v['first_action']}")


def cmd_trace(tag, n='160', level='allstar', seed='1'):
    """Self-play with the lane reading on, the app's rules, every action kept with its reading -> work/trace_<tag>.json"""
    pl = O.G.pool()
    T.pool_is_current(pl)
    pol = L.policy(level, 2, L.profiles()[level]['noise'], lane=True)
    starts = [pl['starts'][i % len(pl['starts'])] for i in range(int(n))]
    starts = [dict(p, seed=104729 * (i + 1) + 7919 * int(seed)) for i, p in enumerate(starts)]
    rows, secs = L.run_jobs('trace', starts, pl['contexts'], n=1, seed=int(seed), looks=True, features=True, stances=True,
                            policies=dict(O=pol, X=pol), rules=RULES, fouls=T.FOULS)
    json.dump(dict(size=tag, zone=True, rows=rows), open(os.path.join(WORK, f'trace_{tag}.json'), 'w'))
    tally(f'self-play, the lane reading on ({tag}, {level}, {n} possessions)', secs)
    m, sd, ci = L.mean_ci([r['points'] for r in rows])
    ends = {}
    for r in rows:
        k = (r.get('result') or {}).get('shot_type') or (r.get('result') or {}).get('kind')
        ends[k] = ends.get(k, 0) + 1
    rep = dict(tag=tag, level=level, possessions=len(rows), mean=round(m, 2), low=round(m - ci, 2), high=round(m + ci, 2), ends=ends,
               positions=sum(len(r['reads']) for r in rows))
    json.dump(rep, open(os.path.join(RUN, f'selfplay_{tag}.json'), 'w'), indent=1)
    print(json.dumps(rep))


def cmd_fitlane(write='no', *sources):
    """The map for play with the lane reading on, one for each level named (level=tag[,tag]), fitted as step 18h's maps
    are (a straight line per phase and side to act) -> learned_weights.json, calibration_lane."""
    import hashlib
    import numpy as np
    import step_18h as H
    H.RUN, H.WORK = RUN, WORK
    body = json.load(open(L.WEIGHTS))
    levels, rep = dict(body.get('calibration_lane') or {}), {}
    for a in sources:
        lv, tags = a.split('=')
        files = [f'trace_{t}.json' for t in tags.split(',')]
        g, ph, y, hand, side, n = H.map_rows(files)
        maps, _ = L.fit_maps('linear', ph, side, hand, y, np.ones(len(y), bool))
        maps = {k: m for k, m in maps.items() if m.get('positions', 0) >= H.MIN_POSITIONS}
        own = sorted(maps)
        base = (body.get('calibration_levels') or {}).get(lv) or body['calibration']
        thin = [k for k in base['maps'] if k not in maps]
        for k in thin:                                  # too few positions for a line of its own: the level's line as it was
            maps[k] = dict(base['maps'][k], from_the_map_without_the_lane=True)
        before = np.array(hand, float)
        for key, m in base['maps'].items():
            sel = (ph == int(key[0])) & (side == (1 if key[1] == 'O' else 0))
            before[sel] = L.knot_map(hand[sel], m['x'], m['y'])
        after = np.array(hand, float)
        for key, m in maps.items():
            sel = (ph == int(key[0])) & (side == (1 if key[1] == 'O' else 0))
            after[sel] = L.knot_map(hand[sel], m['x'], m['y'])
        rmse = lambda v: round(float(np.sqrt(np.mean((v - y) ** 2))), 3)
        levels[lv] = dict(version=1, form='linear', fitted_on=dict(files=files, possessions=n, positions=int(len(y))), maps=maps)
        rep[lv] = dict(possessions=n, positions=int(len(y)), lines_of_its_own=own, lines_kept=thin,
                       error=dict(the_map_without_the_lane=rmse(before), this_map_on_its_own_positions=rmse(after)),
                       mean_reading=round(float(np.mean(hand)), 2), mean_earned=round(float(np.mean(y)), 2))
        print(lv, json.dumps(rep[lv]))
    json.dump(rep, open(os.path.join(RUN, f'fitlane_{write}.json'), 'w'), indent=1)
    if write != 'no':
        body.pop('hash', None)
        body['calibration_lane'] = levels
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote', body['hash'])


def cmd_speed(rounds='2'):
    """D-161: step 18p's code and this step's (the lane off, then on), timed in turn, the app's rules."""
    import subprocess
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18p as P; "
            "print('RESULT ' + json.dumps(P.T._timed({}, P.RULES)))")
    rep = []
    for r in range(int(rounds)):
        t0 = time.time()
        out = subprocess.run([sys.executable, '-c', code], cwd='/home/user/step18p/playmaker', capture_output=True, text=True, check=True,
                             env=dict(os.environ, SENSE_RUN='step18p', SENSE_18N='1')).stdout
        one = {'18p': json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])}
        one['18q, the lane reading off'] = T._timed(dict(lane=False), RULES)
        one['18q, the lane reading on'] = T._timed(dict(lane=True), RULES)
        tally(f'speed, round {r + 1} (one core)', time.time() - t0)
        for k, v in one.items():
            print(r + 1, k, {lv: (x['median'], x['nine_in_ten']) for lv, x in v.items()}, flush=True)
        rep.append(one)
        json.dump(dict(note="seconds to finish 1 pair, the app's rules; each round times step 18p's code and this step's", rounds=rep),
                  open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
