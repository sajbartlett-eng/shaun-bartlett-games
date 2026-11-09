"""Step 3n F5: All-Star v All-Star at Senior Pro in both formats, against the real-basketball targets.
Digital: one chain of possessions with the quarter carried (team fouls by side, reset after 18 possessions a side).
Tabletop: independent possessions (one possession is the whole game).

  python3 tools/f5_3n.py digital 60 out.json [--scale 0.25]
  python3 tools/f5_3n.py tabletop 60 out.json
  python3 tools/f5_3n.py report digital.json tabletop.json
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run(fmt, n, out, scale=0.25):
    from playmaker_engine import jsbridge, selfplay
    eng = jsbridge.NodeEngine().install()
    rows = json.load(open(out))['rows'] if os.path.exists(out) else []
    teams = ('Ball Movement', 'Iron Wall')
    q = dict(fouls=dict(A=0, B=0), poss=dict(A=0, B=0), number=1)
    for r in rows:                                   # resume: replay the quarter state
        q = r['quarter_after']
    t0 = time.time()
    for k in range(len(rows), n):
        att = 'A' if k % 2 == 0 else 'B'
        dfn = 'B' if att == 'A' else 'A'
        off_t, def_t = (teams if att == 'A' else teams[::-1])
        tf, left = (q['fouls'][dfn], max(1, 18 - q['poss'][att])) if fmt == 'digital' else (0, 0)
        r = selfplay.possession(off_t, def_t, ('allstar', 'allstar'), 900 + k, scale, digital=(fmt == 'digital'),
                                team_fouls=tf, quarter_left=left)
        if fmt == 'digital':
            q = json.loads(json.dumps(q))
            q['fouls'][dfn] += r['fouls']
            q['poss'][att] += 1
            if q['poss']['A'] >= 18 and q['poss']['B'] >= 18:
                r['quarter_end'] = dict(fouls=q['fouls'], number=q['number'])
                q = dict(fouls=dict(A=0, B=0), poss=dict(A=0, B=0), number=q['number'] + 1)
        r.update(attacker=att, quarter_after=q, format=fmt)
        r.pop('snapshots', None)
        rows.append(r)
        json.dump(dict(rows=rows), open(out, 'w'))
        print(k + 1, r['score'], r['result'], r['fouls'], q if fmt == 'digital' else '', round(time.time() - t0), flush=True)
    eng.close()


def report(paths):
    from collections import Counter
    out = {}
    for p in paths:
        rows = json.load(open(p))['rows']
        fmt = rows[0]['format']
        ev = [e for r in rows for e in r['events']]
        steals = [e for e in ev if e['kind'] == 'steal']
        won = [e for e in steals if (e.get('roll') or '').endswith('stolen')]
        fouled = [e for e in steals if (e.get('roll') or '').startswith('foul') or '/foul' in (e.get('roll') or '')]
        tos = sum(r.get('tos', 0) for r in rows)
        answers = [e for e in ev if e.get('pass_answer')]
        passes = [e for e in ev if e['kind'] == 'pass']
        why = Counter()
        for e in answers:
            if e['kind'] == 'intercept':
                why['intercepted (attempted)'] += 1
            elif e.get('intercepts', 0) or e.get('jumps', 0):
                why['could intercept, chose not to'] += 1
            else:
                why['no legal Intercept (nobody on or able to reach the line, or next to the passer)'] += 1
        n = len(rows)
        per100 = lambda x: round(100.0 * x / n, 1)
        quarters = [r['quarter_end'] for r in rows if r.get('quarter_end')]
        fouls_by_side = None
        if fmt == 'digital':
            done = [(q['fouls']['A'] + q['fouls']['B']) / 2 for q in quarters]
            last = rows[-1]['quarter_after']
            played = (last['poss']['A'] + last['poss']['B']) / 2
            part = (last['fouls']['A'] + last['fouls']['B']) / 2
            fouls_by_side = dict(full_quarters=done, partial=dict(possessions_each=played, fouls_each=part),
                                 per_quarter_rate=round((sum(q['fouls']['A'] + q['fouls']['B'] for q in quarters) / 2 +
                                                         part) / max(1e-9, len(quarters) * 18 + played) * 18, 2))
        out[fmt] = dict(
            possessions=n, points_per_possession=round(sum(r['score'] for r in rows) / n, 2),
            steals_per_100=per100(len(won)), steal_attempts_per_100=per100(len(steals)),
            turnovers_per_100=per100(tos), reach_fouls_per_100=per100(len(fouled)),
            team_fouls_per_quarter=fouls_by_side,
            steal_attempts_by_position=dict(Counter(e.get('reach', '?') for e in steals)),
            steal_attempts_by_team_fouls=dict(sorted(Counter(e.get('team_fouls', 0) for e in steals).items())),
            contested_passes_per_possession=round(len([e for e in answers if e.get('intercepts', 0) or e.get('jumps', 0)]) / n, 2),
            passes_per_possession=round(len(passes) / n, 2), why_no_intercept=dict(why),
            worst_locks_in_a_phase=max(r.get('locks_max', 0) for r in rows),
            results=dict(Counter(r['result'] for r in rows)))
    print(json.dumps(out, indent=1))
    return out


if __name__ == '__main__':
    if sys.argv[1] == 'report':
        rep = report(sys.argv[2:4])
        if len(sys.argv) > 4:
            json.dump(rep, open(sys.argv[4], 'w'), indent=1)
    else:
        sc = float(sys.argv[sys.argv.index('--scale') + 1]) if '--scale' in sys.argv else 0.25
        run(sys.argv[1], int(sys.argv[2]), sys.argv[3], sc)
