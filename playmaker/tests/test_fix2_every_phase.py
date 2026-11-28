"""Step 31, fix 2 (the step 31C audit: "later answers cost actions in every phase, not just the current one").

The proof board is D2's (E2): the defence's setup with X3 moved off the Sharpshooter (O2) to C10, so the defence's answer
has to close him out to B8. Closing out costs a movement in every phase now: a look faces only the movements the defence
makes before its shot, phase after phase. Before the fix the later phases faced the whole answer, so on top of the
closeout X2 got a free rotation to M7 in each of them (later phases 15, this phase 16). Now every phase reads 16 and
the answer is the closeout and X1's step, nothing more. Both engines, the same numbers.

Re-recorded in fix 3 (D-306). The one Move a phase and the fake mix changed this board's reading: the number is now set at
the rim (O2 cutting to G4 draws X5's closeout; a fake there leaves O5 open at K3), 24.48 this phase, and no movement of the
answer lowers it, so the answer is empty. Fix 2's limit itself is unchanged and still held by the every-look reference in
tests/test_fix1_difference.py, which reads every candidate under the same limits.

Re-recorded in fix 3c (D-310): the drive's race now reads this board (an open lane for O2's drive, his man X3 off at C10),
and the race reads 30 in every phase; still no answer movement lowers it.

Re-recorded in fix 3d (D-311): O1's speed start to I7 is a Sprint, or a Quick Step then a Move at once; either way it leaves
him no movement that phase. Fix 3c let a Move follow the Sprint, to H5, which the rules don't allow. Now the race shoots
from I7 (26) in every phase; still no answer movement lowers it.

Re-recorded in fix 4g (D-318): the speed race names its own answers, and one is X2's Sprint from M8 to I8, next to I7
where the race finishes. Both speed races fall from 26 to 24, and the number to 24.48 from the phase after. The exact
answer (_pvAnswers) takes the same movement at the same number, and so does Python."""
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
CLOSED = [[1, 'I8', 6]]                       # fix 4g: X2 Sprints to I8 (fix 3 to 4f: none; before: X3 closed out to B8, X1 stepped to F11)
BARS = [24, 24, 24.4762, 24.4762, 24.4762, 24.4762]   # fix 4g (fix 3d: 26; fix 3c: 30; fix 3: 24 to 24.48; fix 2: 16 in every phase)


def board():
    s = X.get('E2')
    return dataclasses.replace(s, x=tuple(B.parse_sq(q) for q in SHAPE), arrows=ARROWS)


def test_E2_a_closeout_costs_a_movement_in_every_phase_in_both_engines():
    s = board()
    js = T.js([T.req('E2', dict(only='value'), state=s)])[0]['res']
    assert js['answer'] == CLOSED, js['answer']
    assert [round(v, 4) for v in js['bars'][1:]] == [round(v, 2) for v in BARS] or [round(v, 2) for v in js['bars'][1:]] == [round(v, 2) for v in BARS], js['bars']
    pp = V.poss_parts(s)
    assert [[d, B.sq(q), a] for d, q, a in pp['moves']] == CLOSED
    assert [round(b, 4) for b in pp['bars'][1:]] == BARS, pp['bars']
    assert round(pp['V'], 4) == js['value'] == 24.4762
