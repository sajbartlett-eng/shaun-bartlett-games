"""Step 3n B4: board 1 by outcome over seeds at fixed depth 4: how often the straight drive is available after the
defence's answer, and whether it is worth less than the best alternative."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from playmaker_engine import agent as AG, jsbridge, exam as EX
eng = jsbridge.NodeEngine().install()
AG.FIXED['depth'] = int(sys.argv[2]) if len(sys.argv) > 2 else 4
desc, s, check = EX.POSITIONS[0]()
rows = []
for seed in range(1, 11):
    t, _ = EX.turn_of('allstar', s, seed=seed)
    n = EX.after(s, t)
    avail, drive, alt = EX.straight_drive(n)
    ok, what = check(t)
    rows.append(dict(seed=seed, ok=ok, available=avail, drive=round(drive, 1), alt=round(alt, 1), what=what))
    print(json.dumps(rows[-1]), flush=True)
eng.close()
rep = dict(passes=sum(r['ok'] for r in rows), seeds=len(rows), drive_available=sum(r['available'] for r in rows), rows=rows)
json.dump(rep, open(sys.argv[1], 'w'), indent=1)
print(json.dumps({k: v for k, v in rep.items() if k != 'rows'}))
