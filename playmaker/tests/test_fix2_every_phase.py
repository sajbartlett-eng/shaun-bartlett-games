"""Step 31, fix 2 (the step 31C audit: "later answers cost actions in every phase, not just the current one").

The proof board is D2's (E2): the defence's setup with X3 moved off the Sharpshooter (O2) to C10, so the defence's answer
has to close him out to B8. Closing out costs a movement in every phase now: a look faces only the movements the defence
makes before its shot, phase after phase. Before the fix the later phases faced the whole answer, so on top of the
closeout X2 got a free rotation to M7 in each of them (later phases 15, this phase 16). Now every phase reads 16 and
the answer is the closeout and X1's step, nothing more. Both engines, the same numbers."""
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

SHAPE = ['F10', 'M8', 'C10', 'D4', 'I5']      # the setup's shape on E2 (docs/runs/step31/same_after.json), X3 on C10
ARROWS = (0, 4, 0, 0, 1)
CLOSED = [[2, 'B8', 0], [0, 'F11', 0]]        # the answer: X3 closes out to B8, X1 steps to F11


def board():
    s = X.get('E2')
    return dataclasses.replace(s, x=tuple(B.parse_sq(q) for q in SHAPE), arrows=ARROWS)


def test_E2_a_closeout_costs_a_movement_in_every_phase_in_both_engines():
    s = board()
    js = T.js([T.req('E2', dict(only='value'), state=s)])[0]['res']
    assert js['answer'] == CLOSED, js['answer']
    assert js['bars'][1:] == [16] * (len(js['bars']) - 1), js['bars']      # no later phase reads lower than this one
    pp = V.poss_parts(s)
    assert [[d, B.sq(q), a] for d, q, a in pp['moves']] == CLOSED
    assert [round(b, 6) for b in pp['bars'][1:]] == [16.0] * (len(pp['bars']) - 1), pp['bars']
    assert round(pp['V'], 4) == js['value'] == 16
