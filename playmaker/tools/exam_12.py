"""Step 12: the exam in four settings (search.stable and eval.reach, off and on), on the JavaScript search (the app's
own, proved equal): the fixed look-ahead of 2 team-turn pairs (4 team turns; a board's decisions share 10 minutes, and
a decision that can't finish 4 keeps the deepest it finished) and the clock (the All-Star's time). Boards 1 to 17 with
their own judges, C1 (the archived lane judge, read unchanged) and C2. Each decision records the root choice at every
completed depth, for depth stability. Then the sensitivity pairs and the depth on the clock per level.

  python3 tools/exam_12.py exam <off|stable|reach|both> <fixed|clock> out.json
  python3 tools/exam_12.py sensitivity out.json
  python3 tools/exam_12.py depth <off|stable|reach|both> out.json
"""
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import agent as AG, jsbridge, exam as EX, board as B          # noqa: E402
from playmaker_engine.decide import CONFIG, Read                                   # noqa: E402
from playmaker_engine.search import actor                                          # noqa: E402
import exam_10 as X10                                                               # noqa: E402

SETTINGS = {'off': (False, False), 'stable': (True, False), 'reach': (False, True), 'both': (True, True)}
BOARD_CAP_S = float(os.environ.get('EXAM12_CAP', 600))
PAIRS = int(os.environ.get('EXAM12_DEPTH', 4))   # 4 = 2 team-turn pairs; the cut-down run uses 2 (1 pair)


def set_switches(eng, setting):
    stable, reach = SETTINGS[setting]
    CONFIG.setdefault('search', {})['stable'] = stable
    CONFIG['eval']['reach'] = reach
    if eng is not None:
        eng.call('setStable', 'true' if stable else 'false')
        eng.call('setReach', 'true' if reach else 'false')


def memo_search():
    """The same search asked again (board 14 asks 20 times, the seed only changes the pick after it) is answered from
    the first: the search is deterministic. Only complete answers are kept."""
    orig = AG.JS['search']
    cache = {}

    def call(text):
        req = json.loads(text)
        key = json.dumps({k: v for k, v in req.items() if k != 'budget'}, sort_keys=True)
        if key in cache:
            return cache[key]
        out = orig(text)
        if json.loads(out)['reached'] >= (req.get('max_depth') or 0):
            cache[key] = out
        return out
    AG.JS['search'] = call


def run_exam(setting, cond, out):
    eng = None
    AG.SCALE['value'] = 1.0
    AG.FIXED['depth'] = PAIRS if cond == 'fixed' else None
    notes = X10.capture()
    rows = []
    jobs = [(str(n), n) for n in range(1, 18)] + [('C1', None), ('C2', None)]
    only = os.environ.get('EXAM12_ONLY')
    if only:
        jobs = [j for j in jobs if j[0] in only.split(',')]
    total = float(os.environ.get('EXAM12_TOTAL', 0)) or None      # step 13: a total time cap for the whole run
    start = time.time()
    for name, n in jobs:
        if total and time.time() - start > total:
            rows.append(dict(board=name, not_run='the total time cap was reached'))
            json.dump(dict(setting=setting, condition=cond, pairs=PAIRS, rows=rows), open(out, 'w'), indent=1)
            continue
        # a fresh engine per board: the search's caches stay within one board's memory
        if eng is not None:
            eng.close()
        eng = jsbridge.NodeEngine().install()
        set_switches(eng, setting)
        memo_search()
        del notes[:]
        t0 = time.time()
        cap = min(BOARD_CAP_S, start + total - t0) if total else BOARD_CAP_S
        AG.FIXED['deadline'] = t0 + cap if cond == 'fixed' else None
        if n is not None:
            desc, ok, what = EX.run_position(n, 'allstar')
        elif name == 'C1':
            s = X10.c1_state()
            t, _ = EX.turn_of('allstar', s)
            desc = 'Deny the shooter\'s catch (D-108)'
            ok, what = X10.c1_check(s, t)
        else:
            desc, s, check = EX.c2()
            t, _ = EX.turn_of('allstar', s)
            ok, what = check(t)
        decisions = [dict(depth=x.get('depth'), turn=x.get('turn'), value=x.get('value'), trace=x.get('trace'),
                          stable=x.get('stable'), seconds=x.get('seconds'), depth_seconds=x.get('depth_seconds'))
                     for x in notes]
        row = dict(board=name, desc=desc, ok=ok, what=what, seconds=round(time.time() - t0, 1),
                   choice=decisions[0]['turn'] if decisions else None,
                   depth_min=min((d['depth'] for d in decisions if d['depth']), default=None),
                   decisions=decisions)
        rows.append(row)
        print(json.dumps({k: row[k] for k in ('board', 'ok', 'choice', 'depth_min', 'seconds')}), flush=True)
        json.dump(dict(setting=setting, condition=cond, pairs=PAIRS, rows=rows), open(out, 'w'), indent=1)
    AG.FIXED['deadline'] = None
    eng.close()


# ---- sensitivity: the reading's difference on pairs of positions, against the margin of error -------------------------

def pairs():
    out = {}
    _, s13, _ = EX.POSITIONS[12]()
    cleared = s13.with_(o=s13.o[:4] + (B.parse_sq('J6'),))
    out['13: O5 in the lane, and cleared to J6'] = (s13, cleared)
    _, s16, _ = EX.POSITIONS[15]()
    spent = s16.with_(moved_x=s16.moved_x | 2, qs_x=s16.qs_x | 2)
    out['16: X2 fresh, and spent (Move and Quick Step used)'] = (s16, spent)
    _, s12, _ = EX.POSITIONS[11]()
    # the mismatch: O2, an elite shooter (three 13), in the corner against X2 (contest on a three 3); the help, X1, near
    # him at D4, and drawn away to the top of the key (I8)
    _, s12x, _ = EX.POSITIONS[11]()
    drawn = s12.with_(x=(B.parse_sq('I8'),) + s12.x[1:], side='O')
    out['12: help (X1) near the mismatch at D4, and drawn away to I8'] = (s12.with_(side='O'), drawn)
    return out


def run_sensitivity(out):
    margin = CONFIG['search']['stable_margin']
    res = {}
    for setting in SETTINGS:
        set_switches(None, setting)
        for name, (a, b) in pairs().items():
            va, vb = Read(a).leaf(), Read(b).leaf()
            ph = str(a.phase)
            res.setdefault(name, {})[setting] = dict(first=round(va, 2), second=round(vb, 2), difference=round(vb - va, 2),
                                                     margin=margin.get(ph), beyond_margin=abs(vb - va) > margin.get(ph, 0))
    set_switches(None, 'off')
    json.dump(res, open(out, 'w'), indent=1)
    print(json.dumps(res, indent=1))


def run_depth(setting, out):
    eng = jsbridge.NodeEngine().install()
    set_switches(eng, setting)
    AG.FIXED['depth'] = None
    AG.FIXED['deadline'] = None
    positions = []
    for n in range(1, 17):
        _, b, _ = EX.POSITIONS[n - 1]()
        for k, s in (b.items() if isinstance(b, dict) else [('', b)]):
            positions.append((f'{n}{(" " + str(k)) if k else ""}', s))
    positions.append(('C2', EX.c2()[1]))
    res = {}
    for scale, label in ((1.0, 'here'), (0.25, 'phone speed')):
        AG.SCALE['value'] = scale
        for level in ('rookie', 'starter', 'allstar'):
            rows = []
            for name, s in positions:
                ag = AG.Agent(actor(s), level, seed=1)
                ag.choose(s)
                rows.append(dict(board=name, depth=ag.last.get('depth'), seconds=ag.last.get('seconds')))
            ds = [r['depth'] for r in rows]
            res[f'{label}/{level}'] = dict(median=statistics.median(ds), min=min(ds), max=max(ds),
                                           slowest=min(rows, key=lambda r: (r['depth'], -(r['seconds'] or 0))), rows=rows)
            print(setting, label, level, res[f'{label}/{level}']['median'], min(ds), flush=True)
    json.dump(dict(setting=setting, results=res), open(out, 'w'), indent=1)
    eng.close()


STABILITY_BOARDS = (2, 7, 9, 10, 16)       # the boards whose choice flipped with depth (steps 9 to 11)


def run_stability(setting, out, depth=4, cap=120.0):
    """The root choice at each completed depth (up to 2 team-turn pairs, each board capped) on the boards that
    flipped, for each copy of a board: the computer's first decision there."""
    eng = None
    res = {}
    for n in STABILITY_BOARDS:
        _, b, _ = EX.POSITIONS[n - 1]()
        copies = list(b.items()) if isinstance(b, dict) else [('', b)]
        for k, s in copies:
            if eng is not None:
                eng.close()
            eng = jsbridge.NodeEngine().install()
            set_switches(eng, setting)
            AG.FIXED['depth'] = depth
            AG.FIXED['deadline'] = time.time() + cap / len(copies)
            ag = AG.Agent(actor(s), 'allstar', seed=1)
            t0 = time.time()
            ag.choose(s)
            note = ag.last or {}
            name = f'{n}{(" " + str(k)) if k else ""}'
            res[name] = dict(depth_used=note.get('depth'), trace=note.get('trace'), stable=note.get('stable'),
                             seconds=round(time.time() - t0, 1))
            print(setting, name, note.get('depth'), [(d, ' ; '.join(t)) for d, t, _ in (note.get('trace') or [])], flush=True)
            json.dump(dict(setting=setting, depth=depth, cap_per_board=cap, boards=res), open(out, 'w'), indent=1)
    AG.FIXED['deadline'] = None
    if eng is not None:
        eng.close()


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'exam':
        run_exam(sys.argv[2], sys.argv[3], sys.argv[4])
    elif what == 'sensitivity':
        run_sensitivity(sys.argv[2])
    elif what == 'depth':
        run_depth(sys.argv[2], sys.argv[3])
    elif what == 'stability':
        run_stability(sys.argv[2], sys.argv[3], cap=float(os.environ.get('EXAM12_CAP', 120)))
