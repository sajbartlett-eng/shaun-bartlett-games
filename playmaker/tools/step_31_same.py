"""Step 31, fix 1 (re-read only what an action touched): the before-and-after comparison.

  python3 tools/step_31_same.py record <tag>        every exam board read by both engines; the outputs and their times
                                                    kept in docs/runs/step31/same_<tag>.json
  python3 tools/step_31_same.py compare <a> <b>     the two records, field by field: any choice, value or line that
                                                    differs is listed (counters of work done and times are left out)
  python3 tools/step_31_same.py time <tag>          six readings one at a time, nothing else running: their times

Every JavaScript reading runs with the engine's heap held to 256 MB (node --max-old-space-size=256): a phone's browser
gives a page about that much, so a reading that needs more fails here instead of passing."""
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RUN = os.path.join(ROOT, 'docs', 'runs', 'step31')

import step_31 as T                      # noqa: E402
import step_31_exam as XM                # noqa: E402
import exam_boards as X                  # noqa: E402

HEAP_MB = 256
# counters of work done (how many readings, offers, ...): they may change when work is saved, and decide nothing
COUNTERS = {'reads', 'probed', 'nodes', 'leaves', 'ms', 'seconds', 'depth_seconds', 'stats', 'pvs'}


def js(reqs, timeout=3000):
    env = dict(os.environ, NODE_OPTIONS=f'--max-old-space-size={HEAP_MB}')
    p = subprocess.run(['node', '-e', T.NODE, os.path.abspath(ROOT)], input=json.dumps(reqs), capture_output=True, text=True, timeout=timeout, env=env)
    if p.returncode != 0:
        return [dict(name=r['name'], ms=None, res=dict(error='the engine stopped: ' + p.stderr[-600:])) for r in reqs]
    return json.loads(p.stdout)


def jobs():
    out = []
    for n in X.BOARDS:
        out.append(('value', n, T.req(n, dict(only='value'))))
        out.append(('weight', n, T.req(n, dict(only='weight'))))
        out.append(('coverage', n, T.req(n, None)))                      # the app's own request: the Coverage view and its words
    for n in XM.TURNS:
        out.append(('turn', n, T.req(n, None, fn='searchJSON', profile=XM.PROFILE, max_depth=1)))
    for n in XM.DEF_SETUPS:
        out.append(('stances', n, T.req(n, dict(only='stances'))))
    out.append(('stances_bad_start', 'E3', T.req('E3', dict(only='stances', **{'from': XM._above('E3')}))))
    for n in XM.OFF_SETUPS:
        out.append(('offence', n, T.req(n, dict(only='offence_setup'))))
    return out


COST = dict(value=1, weight=1, coverage=2, turn=15, stances=60, stances_bad_start=60, offence=120)


def python_side():
    """The Python engine on every board: the value's parts and the weight map (B2's readings)."""
    from playmaker_engine import board as B, value as V, weight as W
    out = {}
    for n in X.BOARDS:
        s = X.get(n)
        t0 = time.time()
        try:
            pp = V.poss_parts(s)
            row = dict(V=pp['V'], bars=[round(b, 9) for b in pp['bars']], moves=[[d, B.sq(q), a] for d, q, a in pp['moves']], weight=W.weight_json(s))
        except Exception as e:                             # reported, never hidden
            row = dict(error=repr(e))
        out['python:' + n] = dict(ms=round(1000 * (time.time() - t0)), res=row)
    return out


def lines_of(R):
    """The coach's lines each defence setup gives (setup31.defender_lines on its own result)."""
    from playmaker_engine import board as B, setup31
    out = {}
    for k, v in R.items():
        if not k.startswith('stances:') or 'error' in v['res']:
            continue
        n, r = k.split(':')[1], v['res']
        s = X.get(n)
        ls = setup31.defender_lines(s, [B.parse_sq(q) for q in r['x']], r['arrows'], r['man'], r['lifted'], r['value'])
        out['lines:' + n] = dict(ms=0, res=[z['text'] for z in ls])
    return out


def cmd_record(tag):
    js_jobs = sorted(jobs(), key=lambda j: -COST[j[0]])
    lanes, load = [[], [], []], [0, 0, 0]
    for j in js_jobs:
        i = load.index(min(load))
        lanes[i].append(j)
        load[i] += COST[j[0]]

    def run(lane):
        got = {}
        for kind, name, rq in lane:
            r = js([rq])[0]
            got[kind + ':' + name] = dict(ms=r['ms'], res=r['res'])
            if kind in ('turn', 'stances', 'stances_bad_start', 'offence'):
                print(kind, name, r['ms'], 'ms', ('ERROR ' + r['res']['error'][:200]) if 'error' in r['res'] else '', flush=True)
        return got
    t0 = time.time()
    R = {}
    with ThreadPoolExecutor(4) as ex:
        futs = [ex.submit(run, lane) for lane in lanes] + [ex.submit(python_side)]
        for f in futs:
            R.update(f.result())
    R.update(lines_of(R))
    json.dump(dict(tag=tag, seconds=round(time.time() - t0), heap_mb=HEAP_MB, R=R), open(os.path.join(RUN, f'same_{tag}.json'), 'w'))
    print(len(R), 'readings in', round(time.time() - t0), 's')


def _strip(x):
    if isinstance(x, dict):
        return {k: _strip(v) for k, v in x.items() if k not in COUNTERS}
    if isinstance(x, list):
        return [_strip(v) for v in x]
    return x


def _diff(a, b, path='', out=None):
    out = [] if out is None else out
    if type(a) is not type(b) and not (isinstance(a, (int, float)) and isinstance(b, (int, float))):
        out.append((path, a, b))
    elif isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                out.append((path + '.' + k, a.get(k, '(none)'), b.get(k, '(none)')))
            else:
                _diff(a[k], b[k], path + '.' + k, out)
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append((path + '[len]', len(a), len(b)))
        for i, (x, y) in enumerate(zip(a, b)):
            _diff(x, y, f'{path}[{i}]', out)
    elif a != b:
        out.append((path, a, b))
    return out


def cmd_compare(a, b):
    A, Bm = json.load(open(os.path.join(RUN, f'same_{a}.json'))), json.load(open(os.path.join(RUN, f'same_{b}.json')))
    keys = sorted(set(A['R']) | set(Bm['R']))
    bad, rows, errors = [], 0, []
    for k in keys:
        x, y = A['R'].get(k), Bm['R'].get(k)
        if x is None or y is None:
            bad.append(dict(reading=k, differs=['only in ' + (b if x is None else a)]))
            continue
        rows += 1
        for side, v in ((a, x), (b, y)):
            if isinstance(v['res'], dict) and 'error' in v['res']:
                errors.append(dict(reading=k, run=side, error=v['res']['error'][:300]))
        d = _diff(_strip(x['res']), _strip(y['res']))
        if d:
            bad.append(dict(reading=k, differs=[f'{p}: {json.dumps(u)[:120]} -> {json.dumps(w)[:120]}' for p, u, w in d[:6]], fields=len(d)))
    by_kind = {}
    for k in keys:
        kind = k.split(':')[0]
        ta, tb = (A['R'].get(k) or {}).get('ms'), (Bm['R'].get(k) or {}).get('ms')
        z = by_kind.setdefault(kind, [0, 0, 0])
        if ta is not None and tb is not None:
            z[0] += ta; z[1] += tb; z[2] += 1
    out = dict(a=a, b=b, readings=rows, different=len(bad), errors=errors, differences=bad,
               time_by_kind={k: dict(readings=v[2], before_s=round(v[0] / 1000, 1), after_s=round(v[1] / 1000, 1), times_faster=round(v[0] / v[1], 2) if v[1] else None) for k, v in by_kind.items()},
               wall_s=[A.get('seconds'), Bm.get('seconds')])
    json.dump(out, open(os.path.join(RUN, f'same_{a}_vs_{b}.json'), 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k not in ('differences',)}, indent=1)[:3000])
    for z in bad[:12]:
        print(z['reading'], z['differs'][:3])


TIMED = [('stances', 'E1'), ('stances', 'E3'), ('offence', 'E15b'), ('turn', 'E13'), ('turn', 'E21'), ('turn', 'BLK1')]


def cmd_time(tag):
    """One at a time, nothing else running."""
    allj = {(k, n): rq for k, n, rq in jobs()}
    out = {}
    for k, n in TIMED:
        r = js([allj[(k, n)]])[0]
        out[k + ':' + n] = r['ms']
        print(k, n, r['ms'], 'ms', flush=True)
    json.dump(out, open(os.path.join(RUN, f'same_time_{tag}.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
