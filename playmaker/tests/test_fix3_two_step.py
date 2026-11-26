"""Step 31, fix 3 (the step 31C audit): two-step routes are looks, shot fakes are read inside the number, and the
rules' one Move a phase holds in the defence's answer.

D1's board (E1), the setup's shape as Shaun saw it: O1's drive is now one route with the cut behind it. X5 has to close
out on the drive; against the fake his movement stands, his Move is spent, and O5 cuts from the corner behind him. The
number was 14 with no such route; now the route is a look and the number is well above 14.

D2's board (E2): the Sharpshooter's (O2's) three from where he stands. With X3 a Move away (B7) the fake beats his
closeout; standing in front of O2 (C8) he contests from where he is and the fake gains nothing, so off now costs more
than tight on that look. (Before fix 3 it was the other way: 12.75 off, 13.13 in front.)

Both engines read the same numbers."""
import dataclasses
import os
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'tests'))
sys.path.insert(0, os.path.join(ROOT, 'tools'))

import exam_boards as X                       # noqa: E402
import step_31 as T                           # noqa: E402
from playmaker_engine import board as B, value as V   # noqa: E402
from playmaker_engine.decide import _cmap2_after      # noqa: E402

E1_SHAPE, E1_ARROWS = ['M8', 'E8', 'G10', 'D5', 'I5'], (4, 2, 2, 5, 6)
E2_SHAPE, E2_ARROWS = ['F10', 'M8', 'B7', 'D4', 'I5'], (0, 4, 2, 0, 1)


def shaped(name, shape, arrows):
    return dataclasses.replace(X.get(name), x=tuple(B.parse_sq(q) for q in shape), arrows=tuple(arrows))


def test_E1_the_drive_and_backdoor_cut_is_a_look_and_lifts_the_number_in_both_engines():
    s = shaped('E1', E1_SHAPE, E1_ARROWS)
    js = T.js([T.req('E1', dict(only='value'), state=s)])[0]['res']
    cuts = [z for z in js['two_step'] if z['route'] == 'drive, then backdoor cut' and z['shooter'] == 0 and z['closer'] == 'X5' and z['then'].startswith('O5')]
    assert cuts, js['two_step']
    assert cuts[0]['worth'] > cuts[0]['contested'] + 5, cuts[0]           # the drive alone, contested by X5, was the 14
    assert js['value'] > 14 + 5, js['value']
    assert round(V.poss_parts(s)['V'], 4) == js['value']


def test_E2_off_the_sharpshooter_now_costs_more_than_in_front_of_him_on_his_three():
    reqs, states = [], []
    for q, a in (('B7', 2), ('C8', 0)):
        sh = list(E2_SHAPE); sh[2] = q
        ar = list(E2_ARROWS); ar[2] = a
        s = shaped('E2', sh, ar)
        states.append(s)
        reqs.append(T.req('E2', dict(only='value', look=dict(a=1, c='C9')), state=s))
    off, front = [max(z['worth'] for z in r['res']['look_at'] if z['worth'] is not None) for r in T.js(reqs)]
    assert off > front + 0.5, (off, front)
    vals = [r['res']['value'] for r in T.js([T.req('E2', dict(only='value'), state=s) for s in states])]
    assert [round(V.poss_parts(s)['V'], 4) for s in states] == vals


def test_a_defender_who_moved_in_the_answer_has_no_move_in_his_reply():
    s = X.get('E2')
    rules, qs = s.ctx.rules, s.ctx.dfn[2].qs
    after = _cmap2_after(rules, B.parse_sq('C8'), 0, qs, 0, 'move', 0)
    assert after and all(t[2] == t[4] for t in after.values())                    # every Contest he has left is from where he stands
