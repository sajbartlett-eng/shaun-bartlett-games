"""Step 31, fix 4b: the proof on P1 to P5 (docs/reports/STEP31_FIX4B_REPORT.md).

P1 to P4: the ball's defender held on his square (pressed, or two off); the stance search chooses everything else
together, his arrows and the other four's squares and arrows included. P5: every square as the board has it (help on one
side only); the ball's defender held on his square with each of the eight arrow pairs in turn, every other defender's
arrows chosen by the number; and two off, and the control, with all arrows chosen by the number.

For every shape the search returns, the number is read with what the ball's defender removes (the on-ball reading),
the drive's races, the squares nearer the rim the handler's movement still reaches this turn (the lines the arrows
leave him), and, in each race's first phase, which helper can contain in time and whom he would leave.

    python3 tools/step_31_onball_proof.py [out.json]
"""
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import exam_boards as X                                  # noqa: E402
import step_31 as T                                      # noqa: E402
from playmaker_engine import board as B                  # noqa: E402
from playmaker_engine.actions import movement_dests      # noqa: E402

HELD = {'P1': ('I9', 0), 'P1off': ('I8', 0), 'P2': ('I5', 0), 'P2off': ('I4', 0), 'P3': ('B4', 3), 'P3off': ('C5', 3),
        'P4': ('I12', 0), 'P4off': ('I11', 0)}


def jobs():
    out = []
    for n, (q, d) in HELD.items():
        out.append((n, None, T.req(n, dict(only='stances', hold=dict(d=d, q=q)))))
    for n in ('P5', 'P5off', 'P5ctl', 'P5ctloff'):
        s = X.get(n)
        frm = {'x': [B.sq(q) for q in s.x], 'arrows': list(s.arrows)}
        arrows = range(8) if n == 'P5' else [None]
        for a in arrows:
            out.append((n, a, T.req(n, {'only': 'stances', 'from': frm, 'fix_squares': True, 'hold': dict(d=0, q=B.sq(s.x[0]), a=a)})))
    return out


def reach(s):
    b, h = s.ball, s.o[s.ball]
    got = set()
    for k in ('move', 'qs', 'sprint'):
        got |= set(movement_dests(s, 'O', b, k, s.ctx.rules).keys())
    return sorted(B.sq(q) for q in got if B.dist_rim(q) < B.dist_rim(h))


def helpers(rc):
    """In the race's first phase: each helper who can contain in time, and whom he would leave (the kick-out)."""
    if not rc['phases']:
        return []
    out = []
    for c in rc['phases'][0]['choices']:
        if 'contain' in c['defence']:
            k = c.get('kick') or {}
            out.append(dict(helper=c['defence'], shot_if_he_contains=c['shoot'], leaves=k.get('to'), the_man_left_worth=k.get('worth'), worth=c['worth']))
    return out


def main(path):
    J = jobs()
    with ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda j: T.js([j[2]], timeout=1800)[0], J))
    shapes = []
    for (n, a, _), r in zip(J, res):
        v = r['res']
        s = X.get(n).with_(x=tuple(B.parse_sq(q) for q in v['x']), arrows=tuple(v['arrows']))
        shapes.append((n, a, r['ms'], v, s))
    reads = T.js([T.req(n, dict(only='value', onball=True), state=s) for n, a, ms, v, s in shapes], timeout=1800)
    rows = []
    for (n, a, ms, v, s), rd in zip(shapes, reads):
        val = rd['res']
        d = HELD.get(n, (None, 0))[1]
        mine = next(x for x in val['onball']['defenders'] if x['defender'] == 'X%d' % (d + 1))
        races = [dict(kind=x['advantage'], start=x['from'], worth=x['worth'], help=helpers(x)) for x in val['drive_race']]
        rows.append(dict(board=n, arrow=None if a is None else B.DIR_NAMES[a] + '+' + B.DIR_NAMES[(a + 1) % 8], search_ms=ms,
                         x=v['x'], arrows=[B.DIR_NAMES[z] + '+' + B.DIR_NAMES[(z + 1) % 8] for z in v['arrows']],
                         value=val['value'], stance_value=v['value'], options=val['onball']['options'], removes=mine['removes'],
                         on_ball=val['onball']['on_ball'], removes_most=val['onball']['removes_most'],
                         reach=reach(s), races=races, answer=val['answer']))
    json.dump(rows, open(path, 'w'), indent=1)
    for r in rows:
        print(f"{r['board']:9} {r['arrow'] or '':6} value {r['value']:6} | X {r['x']} {r['arrows']} | shot {r['options']['shot']} drives {r['options']['drives']} passes {r['options']['passes']} | "
              f"reach {len(r['reach'])} | races {[(z['kind'], z['start'], z['worth']) for z in r['races']]} | {r['search_ms']} ms")
        for z in r['races']:
            for h in z['help']:
                print(f"{'':16} {z['kind']}: {h['helper']} (shot then {h['shot_if_he_contains']}), leaves {h['leaves']} worth {h['the_man_left_worth']}")


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'docs', 'runs', 'step31', 'fix4b_onball.json'))
