"""Step 3n Part I: possession summaries from real play against Starter. Five digital matches, 4 possessions a side;
the human side is played by a Rookie agent and read by the trainer on offence. Reports the summaries and whether the
minimal-value and timing flags fire in real play.

  python3 tools/summaries_3n.py out.json [--scale 0.25]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    from playmaker_engine import jsbridge, selfplay, trainer as TR
    out = sys.argv[1]
    scale = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 0.25
    eng = jsbridge.NodeEngine().install()
    rows = json.load(open(out))['rows'] if os.path.exists(out) else []
    t0 = time.time()
    teams = selfplay.TEAMS6
    for m in range(5):
        for k in range(4):
            if any(r['match'] == m and r['k'] == k for r in rows):
                continue
            r = selfplay.possession(teams[m], teams[(m + 2) % len(teams)], ('rookie', 'starter'), 7000 + 10 * m + k, scale,
                                    keep=True)
            rd = TR.read_possession(r['triples'], 'O', budget=0.6)
            flags = [f['kind'] for g in rd['groups'] for f in g.get('flags', [])]
            rows.append(dict(match=m, k=k, score=r['score'], summary=[p['text'] for p in rd['summary']],
                             accuracy=rd['accuracy'], flags=flags, reveal=sum(1 for g in rd['groups'] if g.get('reveal'))))
            json.dump(dict(rows=rows), open(out, 'w'), indent=1)
            print(m, k, r['score'], rd['accuracy'], flags, round(time.time() - t0), flush=True)
    eng.close()
    from collections import Counter
    rep = dict(possessions=len(rows), flags=dict(Counter(f for r in rows for f in r['flags'])),
               timing=sum(r['reveal'] for r in rows))
    print(json.dumps(rep, indent=1))
    json.dump(dict(rows=rows, report=rep), open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
