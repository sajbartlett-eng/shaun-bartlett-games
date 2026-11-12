"""Step 18h: the floor removed (eval.no_floor), the maps per level, the recheck (D-160 to D-163).

  python3 tools/step_18h.py fit <SC|SC2> <write|no> level=file[,file] ...   the parts' lines per level -> learned_weights.json
  python3 tools/step_18h.py selfplay <level> <n> <seed> [k=v ...]           self-play with every action kept and the readings
  python3 tools/step_18h.py h2h <tag> <pairs> <a switches> <b switches>     the backstop head to head (sequential)
"""
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import sense_18h as S                                  # noqa: E402
L, RUN, WORK, tally = S.L, S.RUN, S.WORK, S.tally
F18 = '/home/user/step18f/playmaker/docs/runs/step18f/work'


def rows(files):
    """(possession, phase, what was left to earn, today's reading, the readings' parts, offence to act) from self-play
    files: a 'selfplay' run with the named readings, or a run with every action kept (its 'reads')."""
    import numpy as np
    g, ph, y, hand, f, side, k = [], [], [], [], [], [], 0
    for name in files:
        path = name if os.path.exists(name) else os.path.join(WORK, name) if os.path.exists(os.path.join(WORK, name)) else os.path.join(F18, name)
        for r in json.load(open(path))['rows']:
            if 'reads' in r:                             # [clock, earned, today's reading, offence to act, (looks,) the named readings]
                sts = [(st[0], st[1], st[2], st[-15:]) for st in r['reads']]
            else:                                        # [clock, earned, today's reading, the named readings, (looks)]
                sts = [(st[0], st[1], st[2], st[3:18]) for st in r['states']]
            for clock, banked, hd, ft in sts:
                g.append(k); ph.append(min(6, max(1, (12 - clock) // 2 + 1))); y.append(r['value'] - banked)
                hand.append(hd - banked); f.append(ft); side.append(int(ft[12]))
            k += 1
    return np.array(g), np.array(ph), np.array(y, float), np.array(hand, float), np.array(f, float), np.array(side), k


def nnls(X, y):
    """Least squares with every column but the first (the level) held at 0 or above: columns that come out below 0
    are dropped and the rest fitted again."""
    import numpy as np
    keep = list(range(X.shape[1]))
    while True:
        w, *_ = np.linalg.lstsq(X[:, keep], y, rcond=None)
        neg = [k for k, v in zip(keep, w) if v < 0 and k != 0]
        if not neg:
            break
        keep = [k for k in keep if k not in neg]
    out = np.zeros(X.shape[1])
    out[keep] = w
    return out


def design(variant, f):
    import numpy as np
    shot = np.maximum(f[:, 0], f[:, 1])
    cols = [np.ones(len(shot)), shot, f[:, 2], f[:, 3] if variant == 'SC2' else np.zeros(len(shot))]
    return np.c_[tuple(cols)]


MIN_POSITIONS = 60                                     # a line is fitted from this many positions or more (else the level falls back to all levels' line, then the map)


def fit_level(variant, files):
    import numpy as np
    g, ph, y, hand, f, side, n = rows(files)
    X = design(variant, f)
    fold = np.random.default_rng(18).permutation(n) % 5
    maps, pred, pmap = {}, np.full(len(y), np.nan), np.full(len(y), np.nan)
    for p in range(1, 7):
        for sd in (0, 1):
            m = (ph == p) & (side == sd)
            if m.sum() < MIN_POSITIONS:
                continue
            w = nnls(X[m], y[m])
            # the spread of each number over possessions drawn again (a bootstrap by possession)
            rs, ws = np.random.default_rng(7), []
            ids = np.unique(g[m])
            for _ in range(60):
                pick = rs.choice(ids, len(ids))
                cnt = np.bincount(pick, minlength=n)[g] * m
                sel = np.repeat(np.arange(len(y)), cnt)
                ws.append(nnls(X[sel], y[sel]))
            ws = np.array(ws)
            maps[f"{p}{'O' if sd else 'X'}"] = dict(w=[round(float(v), 5) for v in w], positions=int(m.sum()),
                                                 spread=[[round(float(np.percentile(ws[:, k], 5)), 3), round(float(np.percentile(ws[:, k], 95)), 3)] for k in range(4)])
            for k in range(5):
                tr, te = m & (fold[g] != k), m & (fold[g] == k)
                if tr.sum() < 20 or not te.any():
                    continue
                pred[te] = X[te] @ nnls(X[tr], y[tr])
                a, b = np.polyfit(hand[tr], y[tr], 1)
                pmap[te] = a * hand[te] + b
    ok = ~np.isnan(pred)
    rmse = lambda v: round(float(np.sqrt(np.mean((v[ok] - y[ok]) ** 2))), 3)
    return maps, dict(possessions=n, positions=int(len(y)), fitted_positions=int(ok.sum()), held_out_error=dict(the_parts=rmse(pred), the_map_refit=rmse(pmap)))


def cmd_fit(variant='SC2', write='no', *sources):
    """The parts' lines, one set for each level named (level=file,file) and one for all of them together."""
    import hashlib
    src = {a.split('=')[0]: a.split('=')[1].split(',') for a in sources}
    levels, rep = {}, {}
    for lv, files in list(src.items()) + [('all', [x for fs in src.values() for x in fs])]:
        maps, r = fit_level(variant, files)
        levels[lv] = dict(maps=maps, fitted_on=dict(files=[os.path.basename(x) for x in files], possessions=r['possessions'], positions=r['positions']))
        rep[lv] = dict(r, lines=sorted(maps), thin=[k for k in ('1X', '1O', '2X', '2O', '3X', '3O', '4X', '4O', '5X', '5O', '6X', '6O') if k not in maps])
        print(lv, json.dumps(rep[lv]))
        for k in sorted(maps):
            print('   ', k, maps[k]['positions'], maps[k]['w'], maps[k]['spread'])
    json.dump(dict(variant=variant, levels=rep, maps={lv: v['maps'] for lv, v in levels.items()}), open(os.path.join(RUN, f'fit_{variant}_{write}.json'), 'w'), indent=1)
    if write != 'no':
        body = json.load(open(L.WEIGHTS))
        body.pop('hash', None)
        body['calibration_parts'] = dict(version=1, form=variant,
                                         inputs=['the best shot that can go up now', 'the best look the cover leaves', 'the second best look the cover leaves'],
                                         meaning="what is left to earn = w[0] + w[1] x input 1 + w[2] x input 2 + w[3] x input 3, per level, phase and side to act "
                                                 "(O: the offence to act); w[1] to w[3] never below 0; a level without a line uses 'all', then the map",
                                         levels=levels)
        body['hash'] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()[:16]
        json.dump(body, open(L.WEIGHTS, 'w'), indent=1)
        print('wrote', body['hash'])


# ---- self-play, the backstop head to head, speed -----------------------------------------------------------------------

def _f18():
    import step_18f as F
    F.RUN, F.WORK = RUN, WORK
    F.E18.RUN, F.E18.WORK, L.WORK = RUN, WORK, WORK
    return F


def cmd_selfplay(level='allstar', n='200', seed='1', tag='', *on):
    """Self-play at a level on the config as it stands (and the switches named), every action kept, with the readings
    the lines are fitted on -> work/trace_<tag or level>.json; the All-Star's untagged run is work/trace_app.json."""
    F = _f18()
    t0 = time.time()
    F.cmd_trace(n, seed, level, tag, *on)
    name = f'selfplay_final_{tag or level}.json'
    tally(f'self-play ({tag or level}, {n} possessions)', json.load(open(os.path.join(RUN, name)))['core_hours'] * 3600)


def cmd_fidelity(*tags):
    _f18().cmd_fidelity(*tags)


def cmd_h2h(tag, pairs='200', a_on='', b_on=''):
    """The backstop: a against b at the All-Star, paired possessions, in batches of 40; it stops when the sequential
    test for a gain of 1 point a pair against none gives its verdict (after 80 pairs), or at `pairs`."""
    F = _f18()
    lv = 'allstar'
    a = L.policy(lv, 2, L.profiles()[lv]['noise'], **F._switches([x for x in a_on.split(',') if x]))
    b = L.policy(lv, 2, L.profiles()[lv]['noise'], **F._switches([x for x in b_on.split(',') if x]))
    pl, rows, secs, k = F.pool(), [], 0.0, 0
    starts = pl['starts']
    while len(rows) < int(pairs):
        k += 1
        n = min(40, int(pairs) - len(rows))
        part = [starts[(i + 37 * k) % len(starts)] for i in range(n)]
        part = [dict(p, seed=104729 * (i + 1) + 15485863 * k) for i, p in enumerate(part)]
        r, s = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=1800 + k, a=a, b=b)
        rows += r
        secs += s
        st = L.h2h_stats(rows, delta=1.0)
        tally(f'head to head {tag}, pairs {len(rows) - n + 1} to {len(rows)}', s)
        print(tag, len(rows), st['mean_difference'], st['interval'], st['wins'], st['losses'], st['ties'], st['sequential_stop'], round(secs / 3600, 2), flush=True)
        json.dump(dict(tag=tag, a=a_on or 'the default', b=b_on or 'the default', stats=st, core_hours=round(secs / 3600, 2),
                       a_on_offence=F.E18.shot_timing([x['a_end'] for x in rows]), b_on_offence=F.E18.shot_timing([x['b_end'] for x in rows])),
                  open(os.path.join(RUN, f'h2h_{tag}.json'), 'w'), indent=1)
        if st['sequential_stop'] and len(rows) >= 80:
            break


def cmd_speed(rounds='2'):
    """D-161: the time to finish 1 pair at every level, this step's code and step 18f's timed in turn in the same hour
    (the 22 hand-board decisions, one warm engine, 9 decisions in 10) -> speed.json"""
    import subprocess
    code = ("import json, sys; sys.path.insert(0, 'tools'); import step_18f as S; "
            "print('RESULT ' + json.dumps(S._timed({lv: S._level(lv) for lv in S.TARGET}, runs=1)))")
    rep = []
    for r in range(int(rounds)):
        one = {}
        for name, cwd in (('18f', '/home/user/step18f/playmaker'), ('18h', ROOT)):
            t0 = time.time()
            out = subprocess.run([sys.executable, '-c', code], cwd=cwd, capture_output=True, text=True, check=True).stdout
            one[name] = json.loads([ln for ln in out.splitlines() if ln.startswith('RESULT ')][0][7:])
            tally(f'speed ({name}, round {r + 1})', time.time() - t0)       # one core
            print(r + 1, name, {lv: (v['median'], v['nine_in_ten']) for lv, v in one[name].items()}, flush=True)
        rep.append(one)
        json.dump(dict(note='seconds to finish 1 pair; each round times step 18f\'s code and then this step\'s', rounds=rep), open(os.path.join(RUN, 'speed.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
