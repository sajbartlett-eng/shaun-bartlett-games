"""Step 3n Part B: the exam in two columns. The design verdict: every level at a fixed depth (All-Star at 4, then 6),
no time limit, seeded. The browser verdict: the B8 time budgets, the search in JavaScript, the budget scaled by 1/4
(this machine runs the engine about four times faster than the throttled phone profile).

  python3 tools/exam_3n.py fixed 4 out.json [boards...]
  python3 tools/exam_3n.py timed 0.25 out.json [boards...]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playmaker_engine import agent as AG, jsbridge, exam as EX   # noqa: E402


def main():
    mode, arg, out = sys.argv[1], float(sys.argv[2]), sys.argv[3]
    only = [int(a) for a in sys.argv[4:]] or list(range(1, len(EX.POSITIONS) + 1))
    eng = jsbridge.NodeEngine().install()
    levels = ('allstar',) if mode == 'fixed' else ('allstar', 'starter', 'rookie')
    if mode == 'fixed':
        AG.FIXED['depth'] = int(arg)
    else:
        AG.SCALE['value'] = arg
    rows = []
    notes = []
    orig = AG.Agent.choose

    def choose(self, s):
        a = orig(self, s)
        if self.last and self.last is not (notes[-1] if notes else None):
            notes.append(self.last)
        return a
    AG.Agent.choose = choose
    for n in only:
        row = dict(n=n)
        for lv in levels:
            del notes[:]
            t0 = time.time()
            desc, ok, what = EX.run_position(n, lv)
            row['desc'] = desc
            first = notes[0] if notes else {}
            row[lv] = dict(ok=ok, what=what, seconds=round(time.time() - t0, 1), depth=first.get('depth'),
                           pv=first.get('pv'), value=first.get('value'),
                           depths=sorted({x.get('depth') for x in notes if x.get('depth') is not None}))
        rows.append(row)
        print(json.dumps(row)[:600], flush=True)
        json.dump(dict(mode=mode, arg=arg, rows=rows), open(out, 'w'), indent=1)
    eng.close()


if __name__ == '__main__':
    main()
