"""Step 10: the exam both ways (leaf_mode floor and relative), on the JavaScript search (the app's own, proved equal):
on the clock (the All-Star's time) and at a fixed 3 moves ahead. Boards 1 to 17 with their own judges (exam.py), C1
(the archived lane judge, read unchanged from the archive) and C2 (rebuilt, exam.c2). Then, on the real-gap boards,
the values of the computer's choice and of the moves the board expects, 3 moves ahead, in each mode. Then how far the
app's search looks on the clock, per level, here and at phone speed.

  python3 tools/exam_10.py exam <floor|relative> <clock|fixed3> out.json
  python3 tools/exam_10.py gaps <floor|relative> out.json
  python3 tools/exam_10.py depth out.json
"""
import importlib.util
import json
import os
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import agent as AG, jsbridge, exam as EX, board as B          # noqa: E402
from playmaker_engine.decide import CONFIG                                          # noqa: E402
from playmaker_engine.actions import legal_actions                                  # noqa: E402
from playmaker_engine.resolve import apply, ChanceNode                              # noqa: E402
from playmaker_engine.search import actor                                           # noqa: E402


def set_mode(eng, mode):
    CONFIG['eval']['leaf_mode'] = mode
    eng.call('setLeafMode', mode)


def capture():
    notes = []
    orig = AG.Agent.choose

    def choose(self, s):
        a = orig(self, s)
        if self.last and (not notes or self.last is not notes[-1]):
            notes.append(self.last)
        return a
    AG.Agent.choose = choose
    return notes


def c1_state():
    from playmaker_engine.scenarios import game_state
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                   ['N', 'NE', 'NW', 'N', 'N'])
    a = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == B.parse_sq('I12'))
    t = apply(s, a)
    return apply(t, next(x for x in legal_actions(t) if x.kind == 'end_turn'))


def c1_check(s, t):
    """D-108's archived judge: after the defence's turn the carrier's lane to O2 is answered and at least two are."""
    spec = importlib.util.spec_from_file_location('playmaker_engine.capacity_archived',
                                                  os.path.join(ROOT, 'archive', 'engine', 'capacity.py'))
    cap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cap)
    n = EX.after(s, t)
    if isinstance(n, ChanceNode) or n.stage == 'over':
        return False, EX.words(t)
    lanes = {}
    for p in range(5):
        if p == 1 or not B.on_board(n.o[p]):
            continue
        h = n.with_(ball=p, side='O', stage='play', turn_n=0, pending=None, approach=-1, tok_o=max(1, n.tok_o))
        lanes[p] = cap.lane_answered(h, p, 1)
    ok = bool(lanes.get(n.ball)) and sum(lanes.values()) >= 2
    return ok, f'{EX.words(t)} (lanes to O2 answered: {sum(lanes.values())}, the ball\'s: {bool(lanes.get(n.ball))})'


def run_exam(mode, cond, out):
    eng = jsbridge.NodeEngine().install()
    set_mode(eng, mode)
    AG.FIXED['depth'] = 3 if cond == 'fixed3' else None
    AG.SCALE['value'] = 1.0
    notes = capture()
    rows = []
    jobs = [(str(n), n) for n in range(1, 18)] + [('C1', None), ('C2', None)]
    for name, n in jobs:
        del notes[:]
        t0 = time.time()
        if n is not None:
            desc, ok, what = EX.run_position(n, 'allstar')
        elif name == 'C1':
            s = c1_state()
            t, _ = EX.turn_of('allstar', s)
            desc = 'Deny the shooter\'s catch (D-108)'
            ok, what = c1_check(s, t)
        else:
            desc, s, check = EX.c2()
            t, _ = EX.turn_of('allstar', s)
            ok, what = check(t)
        first = notes[0] if notes else {}
        row = dict(board=name, desc=desc, ok=ok, what=what, seconds=round(time.time() - t0, 1),
                   choice=first.get('turn'), value=first.get('value'), depth=first.get('depth'),
                   depths=sorted({x.get('depth') for x in notes if x.get('depth') is not None}))
        rows.append(row)
        print(json.dumps(row)[:300], flush=True)
        json.dump(dict(mode=mode, condition=cond, rows=rows), open(out, 'w'), indent=1)
    eng.close()


# ---- the real-gap boards: the choice against the moves the board expects, 3 moves ahead --------------------------------

def run_gaps(mode, out):
    import exam_evidence as X
    eng = jsbridge.NodeEngine().install()
    set_mode(eng, mode)
    AG.FIXED['depth'] = 3
    node = X.Node()
    node.call_mode = mode
    res = {}

    def expected_turns(s, first_piece, side, accept):
        """The board's accepted turns among those whose first action is the key defender's or attacker's (the full
        list of a defence turn runs to a million; the expected move starts with him)."""
        out = []
        for a in legal_actions(s):
            if a.side != side or a.piece != first_piece:
                continue
            n1 = apply(s, a)
            cands = [(a,)]
            if not isinstance(n1, ChanceNode) and n1.stage == s.stage and actor(n1) == side:
                cands += [(a, b) for b in legal_actions(n1) if b.kind not in ('end_turn', 'forfeit')]
            out += [t for t in cands if accept(list(t))]
        return out

    def measure(s, accepted, label):
        t, _ = EX.turn_of('allstar', s)
        r = X.search(node, s, accepted, [tuple(t)], [3], 240.0, mode=mode)
        sign = 1 if actor(s) == 'O' else -1
        d = r['depths'][0] if r['depths'] else None
        if d is None:
            return dict(label=label, capped=True)
        top_v, top_t = d['top'][0]
        kept = [(v, accepted[i]) for v, i in d['kept']]
        best = max(kept, key=lambda r_: sign * r_[0]) if kept else None
        return dict(label=label, n_accepted=len(accepted), computer_choice=EX.words(t),
                    computer_choice_value=round(d['extra'][0][0], 2),
                    search_top=' ; '.join(' '.join(map(str, a)) for a in top_t), search_top_value=round(top_v, 2),
                    expected=EX.words(best[1]) if best else None, expected_value=round(best[0], 2) if best else None,
                    gap=round(sign * (d['extra'][0][0] - best[0]), 2) if best else None)

    # board 2: X2's own turns, each copy judged with the computer's choice on the other copy (step 9's split)
    _, b2, _ = EX.POSITIONS[1]()
    choices = {k: EX.turn_of('allstar', v)[0] for k, v in b2.items()}
    out2 = {}
    for k, other in ((4, 12), (12, 4)):
        acc = X.sag_half(b2, k, other, choices[other])
        out2[str(k)] = measure(b2[k], expected_turns(b2[k], 1, 'X', acc), str(k))
    res['2'] = out2
    # board 3: the low man's step (X4) and a second mover
    _, s3, c3 = EX.POSITIONS[2]()
    res['3'] = measure(s3, expected_turns(s3, 3, 'X', lambda t: c3(t)[0]), '')
    # board 6: O4's own first move (D-94: his open look beats the possession)
    _, s6, c6 = EX.POSITIONS[5]()
    res['6'] = measure(s6, expected_turns(s6, 3, 'O', lambda t: c6(t)[0]), '')
    # board 13: O5 out of the lane (or a shot or pass by O1): O5's own moves and O1's shots and passes
    _, s13, c13 = EX.POSITIONS[12]()
    acc13 = expected_turns(s13, 4, 'O', lambda t: c13(t)[0]) + \
        [(a,) for a in legal_actions(s13) if a.piece == 0 and a.kind in ('shot', 'pass')]
    res['13'] = measure(s13, acc13, '')
    # board 16: the first moves away from the ball that step 9 found wear X2 out over the phase
    ev9 = json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step9', 'exam_evidence.json')))['16']
    moves16 = {r['move'] for r in ev9['offball_first_moves'] if r['drain'] > 0}
    _, s16, _ = EX.POSITIONS[15]()
    acc16 = [(a,) for a in legal_actions(s16) if str(a) in moves16]
    res['16'] = measure(s16, acc16, '')
    json.dump(dict(mode=mode, look=3, boards=res), open(out, 'w'), indent=1)
    node.close()
    eng.close()
    print(json.dumps(res, indent=1)[:3000])


# ---- how far the app's search looks on the clock ------------------------------------------------------------------------

def run_depth(out):
    eng = jsbridge.NodeEngine().install()
    set_mode(eng, 'floor')
    AG.FIXED['depth'] = None
    positions = []
    for n in range(1, 17):
        _, b, _ = EX.POSITIONS[n - 1]()
        for k, s in (b.items() if isinstance(b, dict) else [('', b)]):
            positions.append((f'{n}{(" " + str(k)) if k else ""}', s))
    positions.append(('C2', EX.c2()[1]))
    res = {}
    for scale, label in ((1.0, 'here'), (0.25, 'phone speed (a quarter of the time)')):
        AG.SCALE['value'] = scale
        for level in ('rookie', 'starter', 'allstar'):
            rows = []
            for name, s in positions:
                ag = AG.Agent(actor(s), level, seed=1)
                ag.choose(s)
                rows.append(dict(board=name, depth=ag.last.get('depth'), partial=ag.last.get('partial'),
                                 seconds=ag.last.get('seconds')))
            ds = [r['depth'] for r in rows]
            slow = min(rows, key=lambda r: (r['depth'], -(r['seconds'] or 0)))
            res[f'{label}/{level}'] = dict(median=statistics.median(ds), min=min(ds), max=max(ds),
                                           slowest=slow, budget_s=AG.profile(level)['time_budget_s'] * scale, rows=rows)
            print(label, level, res[f'{label}/{level}']['median'], slow, flush=True)
    json.dump(res, open(out, 'w'), indent=1)
    eng.close()


if __name__ == '__main__':
    what = sys.argv[1]
    if what == 'exam':
        run_exam(sys.argv[2], sys.argv[3], sys.argv[4])
    elif what == 'gaps':
        run_gaps(sys.argv[2], sys.argv[3])
    elif what == 'depth':
        run_depth(sys.argv[2])
