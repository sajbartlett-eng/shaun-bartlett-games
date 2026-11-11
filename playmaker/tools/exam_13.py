"""Step 13, part A: the stable search's five switches, measured apart. Settings: off; cheap (quiet_points,
like_with_like and tempo); cheap with play_on; cheap with the reach map; stable (all five); both (all five and the
reach map). On the JavaScript search (the app's own, proved equal). Every run has a total time cap.

  python3 tools/exam_13.py stability <setting> out.json     the root choice and the time at each depth, boards 2, 7,
                                                            9, 10 and 16 (EXAM13_CAP: seconds per decision)
  python3 tools/exam_13.py exam <setting> <fixed|clock> out.json   the exam (EXAM12_DEPTH=2: 1 team-turn pair;
                                                            EXAM12_CAP per board; EXAM12_TOTAL for the run)
  python3 tools/exam_13.py levels <setting> out.json        each level's time and look-ahead on the clock, here and at
                                                            phone speed
  python3 tools/exam_13.py pairtime <setting> out.json      the time each level needs to finish 1 team-turn pair
  python3 tools/exam_13.py record <setting> <depth> out.json    whole searches, no time limit, on the step 12 boards:
                                                            every root value and turn, the choice at each depth, counts
  python3 tools/exam_13.py dump <depth> requests.json       the boards' search requests, for tools/profile_13.js
  python3 tools/exam_13.py same a.json b.json               two records give the same choices and values; the times
"""
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import agent as AG, jsbridge, exam as EX          # noqa: E402
from playmaker_engine.decide import CONFIG                               # noqa: E402
from playmaker_engine.search import actor, PARTS                         # noqa: E402
import exam_12 as X12                                                    # noqa: E402

CHEAP = ('quiet_points', 'like_with_like', 'tempo')
SPEEDUPS = ('reach_cache', 'forcing', 'quiet_read', 'tt_order', 'two_direct', 'two_bound', 'path_block')
SETTINGS = {'off': ((), False), 'cheap': (CHEAP, False), 'cheap_play_on': (CHEAP + ('play_on',), False),
            'cheap_reach': (CHEAP, True), 'stable': (PARTS, False), 'both': (PARTS, True),
            'play_on': (('play_on',), False), 'reach': ((), True),
            # without quiet_points: 'light' (like_with_like and tempo), and 'rest' (light, play_on and the reach map)
            'light': (('like_with_like', 'tempo'), False), 'rest': (('like_with_like', 'tempo', 'play_on'), True),
            # each part alone, and pairs, to see which part moves a board
            'tempo': (('tempo',), False), 'like_with_like': (('like_with_like',), False),
            'quiet_points': (('quiet_points',), False), 'light_play_on': (('like_with_like', 'tempo', 'play_on'), False),
            'light_reach': (('like_with_like', 'tempo'), True), 'play_on_reach': (('play_on',), True),
            # part B: the default game (like_with_like and the reach map, D-121), and with coverage as a budget
            'base': (('like_with_like',), True), 'budget': (('like_with_like',), True, True),
            # step 16: advantages only (must equal base), and with goals steering the search; the same with the budget
            'adv': (('like_with_like',), True, False, 'adv'), 'goals': (('like_with_like',), True, False, 'goals'),
            'budget_adv': (('like_with_like',), True, True, 'adv'), 'budget_goals': (('like_with_like',), True, True, 'goals'),
            # step 18b: the default game with play_on (the rival to eval.settle_shots, which EXAM13_SETTLE=1 turns on)
            'base_play_on': (('like_with_like', 'play_on'), True)}


def set_switches(eng, setting):
    on, reach = SETTINGS[setting][:2]
    budget = len(SETTINGS[setting]) > 2 and SETTINGS[setting][2] is True
    CONFIG['eval']['coverage_budget'] = budget
    g = SETTINGS[setting][3] if len(SETTINGS[setting]) > 3 else None
    CONFIG['eval']['advantages'] = g is not None
    CONFIG['search']['goals'] = g == 'goals'
    srch = CONFIG.setdefault('search', {})
    srch['stable'] = False
    for k in PARTS:
        srch[k] = k in on
    CONFIG['eval']['reach'] = reach
    if eng is not None:
        off = [x for x in os.environ.get('EXAM13_WITHOUT', '').split(',') if x]      # speed-ups turned off, to time them
        eng.call('setSpeed', json.dumps({k: k not in off and 'all' not in off for k in SPEEDUPS}))
        eng.call('setSearch', json.dumps(dict(stable=False, **{k: k in on for k in PARTS})))
        eng.call('setReach', 'true' if reach else 'false')
        eng.call('setBudget', 'true' if budget else 'false')
        eng.call('setAdvantages', 'true' if g is not None else 'false')
        eng.call('setGoals', 'true' if g == 'goals' else 'false')
    settle = os.environ.get('EXAM13_SETTLE', '1') != '0'    # step 18b: eval.settle_shots (on by default since D-148; 0 turns it off)
    CONFIG['eval']['settle_shots'] = settle
    helpr = os.environ.get('EXAM13_HELP') == '1'             # step 18c: eval.help_readings
    CONFIG['eval']['help_readings'] = helpr
    if eng is not None:
        eng.call('setSettle', 'true' if settle else 'false')
        eng.call('setHelp', 'true' if helpr else 'false')
    openv = os.environ.get('EXAM13_OPEN')               # step 18e: search.open_list ('defence', 'both'; unset: the config's)
    if openv is not None:
        CONFIG.setdefault('search', {})['open_list'] = False if openv in ('', '0', 'false') else openv
        if eng is not None:
            eng.call('setOpenList', 'false' if openv in ('', '0', 'false') else openv)
    cal = os.environ.get('EXAM13_CALIBRATED')          # step 18a: 0 measures the computer before D-138 (the default is on)
    if cal is not None:
        CONFIG['eval']['calibrated'] = cal != '0'
        if eng is not None:
            eng.call('setCalibrated', 'true' if cal != '0' else 'false')


X12.SETTINGS = SETTINGS
X12.set_switches = set_switches          # the step 12 exam runner, with this step's settings


def boards(which=X12.STABILITY_BOARDS):
    """(name, state): each copy of each board, the computer's first decision there."""
    out = []
    for n in which:
        _, b, _ = EX.POSITIONS[n - 1]()
        for k, s in (b.items() if isinstance(b, dict) else [('', b)]):
            out.append((f'{n}{(" " + str(k)) if k else ""}', s))
    return out


def run_stability(setting, out, depth=4):
    """The root choice and the time at each completed depth (1 to 4), each decision capped."""
    cap = float(os.environ.get('EXAM13_CAP', 200))
    res = {}
    for name, s in boards():
        eng = jsbridge.NodeEngine().install()             # a fresh engine per decision
        set_switches(eng, setting)
        AG.FIXED['depth'] = depth
        AG.FIXED['deadline'] = time.time() + cap
        ag = AG.Agent(actor(s), 'allstar', seed=1)
        t0 = time.time()
        ag.choose(s)
        note = ag.last or {}
        res[name] = dict(depth_used=note.get('depth'), trace=note.get('trace'), depth_seconds=note.get('depth_seconds'),
                         stable=note.get('stable'), leaves=note.get('leaves'), seconds=round(time.time() - t0, 1))
        print(setting, name, note.get('depth'), note.get('depth_seconds'),
              [(d, ' ; '.join(t)) for d, t, _ in (note.get('trace') or [])], flush=True)
        json.dump(dict(setting=setting, depth=depth, cap_per_decision=cap, boards=res), open(out, 'w'), indent=1)
        eng.close()
    AG.FIXED['deadline'] = None
    AG.FIXED['depth'] = None


def run_levels(setting, out):
    """Each level's decision time and look-ahead on the clock, here and at phone speed (the budget quartered), on the
    exam's boards (every copy) and C2."""
    eng = jsbridge.NodeEngine().install()
    set_switches(eng, setting)
    AG.FIXED['depth'] = None
    AG.FIXED['deadline'] = None
    positions = boards(range(1, 17)) + [('C2', EX.c2()[1])]
    res = {}
    for scale, label in ((1.0, 'here'), (0.25, 'phone speed')):
        AG.SCALE['value'] = scale
        for level in ('rookie', 'starter', 'allstar'):
            rows = []
            for name, s in positions:
                ag = AG.Agent(actor(s), level, seed=1)
                ag.choose(s)
                n = ag.last or {}
                rows.append(dict(board=name, depth=n.get('depth'), seconds=n.get('seconds'),
                                 depth_seconds=n.get('depth_seconds')))
            ds = [r['depth'] for r in rows]
            secs = sorted(r['seconds'] for r in rows)
            first = [r['depth_seconds'][0][1] for r in rows if r['depth_seconds']]
            res[f'{label}/{level}'] = dict(depth_median=statistics.median(ds), depth_min=min(ds), depth_max=max(ds),
                                           depth_counts={str(d): ds.count(d) for d in sorted(set(ds))},
                                           seconds_median=round(statistics.median(secs), 3), seconds_max=round(secs[-1], 3),
                                           first_depth_median=round(statistics.median(first), 3) if first else None,
                                           first_depth_max=round(max(first), 3) if first else None, rows=rows)
            print(setting, label, level, {k: v for k, v in res[f'{label}/{level}'].items() if k != 'rows'}, flush=True)
    AG.SCALE['value'] = 1.0
    json.dump(dict(setting=setting, results=res), open(out, 'w'), indent=1)
    eng.close()


def run_pair_time(setting, out):
    """The time each level needs to finish 1 team-turn pair (and its first team turn), with no time limit, on the exam's
    boards and C2, one warm engine (as in a game): what a setting needs to fit a budget."""
    eng = jsbridge.NodeEngine().install()
    set_switches(eng, setting)
    positions = boards(range(1, 17)) + [('C2', EX.c2()[1])]

    def one(s, level):
        ag = AG.Agent(actor(s), level, seed=1)
        req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=ag.p, budget=None, max_depth=2,
                   stale=None)
        o = json.loads(AG.JS['search'](json.dumps(req)))
        ds = dict((d, x) for d, x in o.get('depth_seconds', []))
        return dict(one_turn=round(ds.get(1, 0), 3), one_pair=round(ds.get(2, o['seconds']), 3), leaves=o['leaves'])
    for _, s in positions[:6]:
        one(s, 'allstar')                                   # warm the engine
    res = {}
    for level in ('rookie', 'starter', 'allstar'):
        rows = [dict(board=name, **one(s, level)) for name, s in positions]
        for f in ('one_turn', 'one_pair'):
            v = sorted(r[f] for r in rows)
            res.setdefault(level, {})[f] = dict(median=round(statistics.median(v), 3), p90=v[int(0.9 * (len(v) - 1) + 0.5)],
                                                worst=v[-1])
        res[level]['rows'] = rows
        print(setting, level, {f: res[level][f] for f in ('one_turn', 'one_pair')}, flush=True)
    json.dump(dict(setting=setting, results=res), open(out, 'w'), indent=1)
    eng.close()


def run_record(setting, depth, out):
    """Whole searches with no time limit on the step 12 boards (EXAM13_BOARDS to choose): what a speed-up must not
    change (every root value and its turn, the choice and value at each depth, the extensions, cap hits and kept
    choices) and what it should (the seconds)."""
    which = os.environ.get('EXAM13_BOARDS')
    todo = boards([int(x) for x in which.split(',')] if which else X12.STABILITY_BOARDS)
    res = {}
    for name, s in todo:
        eng = jsbridge.NodeEngine().install()
        set_switches(eng, setting)
        ag = AG.Agent(actor(s), 'allstar', seed=1)
        req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=ag.p, budget=None,
                   max_depth=depth, stale=None)
        t0 = time.time()
        o = json.loads(AG.JS['search'](json.dumps(req)))
        res[name] = dict(results=o['results'], trace=o['trace'], reached=o['reached'], extensions=o.get('extensions'),
                         cap_hits=o.get('cap_hits'), kept=o.get('kept'), leaves=o['leaves'], nodes=o['nodes'],
                         seconds=round(o['seconds'], 3), depth_seconds=o.get('depth_seconds'))
        print(setting, name, res[name]['seconds'], o['leaves'], o['nodes'], flush=True)
        json.dump(dict(setting=setting, depth=depth, boards=res), open(out, 'w'), indent=1)
        eng.close()


def run_dump(depth, out):
    """The search requests for the step 12 boards (for tools/profile_13.js)."""
    reqs = {}
    for name, s in boards():
        ag = AG.Agent(actor(s), 'allstar', seed=1)
        reqs[name] = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=ag.p, budget=None,
                          max_depth=depth, stale=None)
    json.dump(reqs, open(out, 'w'))


def run_same(a, b):
    """Two records: the same choices and values (to 1e-9); the seconds of each."""
    A, Bb = json.load(open(a)), json.load(open(b))
    bad = []
    ta = tb = 0.0
    for name, x in A['boards'].items():
        y = Bb['boards'].get(name)
        if y is None:
            continue
        same = (len(x['results']) == len(y['results'])
                and all(abs(p[0] - q[0]) <= 1e-9 * max(1.0, abs(p[0])) and p[1] == q[1] for p, q in zip(x['results'], y['results']))
                and len(x['trace']) == len(y['trace'])
                and all(p[0] == q[0] and p[1] == q[1] and abs(p[2] - q[2]) <= 1e-9 * max(1.0, abs(p[2]))
                        for p, q in zip(x['trace'], y['trace']))
                and all(x[f] == y[f] for f in ('reached', 'kept')))
        if not same:
            bad.append(name)
        ta += x['seconds']
        tb += y['seconds']
        print(f"{name:16} {'same' if same else 'DIFFERENT':9} {x['seconds']:8.2f} s -> {y['seconds']:8.2f} s   "
              f"leaves {x['leaves']} -> {y['leaves']}")
    print(f"total {ta:.2f} s -> {tb:.2f} s ({ta / tb if tb else 0:.2f} times); different: {bad or 'none'}")
    return dict(different=bad, seconds_before=round(ta, 2), seconds_after=round(tb, 2))


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'stability':
        run_stability(sys.argv[2], sys.argv[3])
    elif what == 'exam':
        X12.run_exam(sys.argv[2], sys.argv[3], sys.argv[4])
    elif what == 'levels':
        run_levels(sys.argv[2], sys.argv[3])
    elif what == 'pairtime':
        run_pair_time(sys.argv[2], sys.argv[3])
    elif what == 'record':
        run_record(sys.argv[2], int(sys.argv[3]), sys.argv[4])
    elif what == 'sensitivity':                  # the three pairs: the default game, and with coverage as a budget
        X12.run_sensitivity(sys.argv[2], sys.argv[3].split(',') if len(sys.argv) > 3 else ['base', 'budget'])
    elif what == 'dump':
        run_dump(int(sys.argv[2]), sys.argv[3])
    elif what == 'same':
        r = run_same(sys.argv[2], sys.argv[3])
        if len(sys.argv) > 4:
            json.dump(r, open(sys.argv[4], 'w'), indent=1)
