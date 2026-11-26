# Step 31, fix 3 of 7: two-step routes are looks, fakes inside the number, one Move a phase. Report

**Built in both engines, on branch `step-31`. Not merged, as asked. The exam was not run.** Both engines read the same numbers on every board tried (0 mismatches on 40 random positions, and the exam's both-engines checks).

**The proofs, in short:**
- **D1 (E1): passes.** On D1's board as Shaun saw it, O1's drive and O5's cut behind X5 now show up as one look, and the number rises from 14 to 22.9.
- **D2 (E2): passes for the Sharpshooter's own shot, not for the whole board.** Standing a Move off O2 now costs more than standing in front of him on his three. The board's number is set at the rim, though, so the setup search still spends its help there rather than on O2. Section 3 has the detail.

## 1. Changes to the printed game

None.

## 2. What was built

1. **One Move a phase, in the defence's answer (both engines).** A defender who Moves in the answer inside the number has no Move in his reply. That leaves a Quick Step (off balance) if he has one, or a Contest from where he stands. After a Quick Step he keeps his Move; after a Sprint (his Move and his Quick Step) he can only contest where he stands, off balance. Before, a defender who closed out in the answer still got a Move then Contest in the reply.
2. **Shot fakes read inside the number (both engines).** At every look where the shooter is in control and still has his fake, the defence has two answers: contest from where it stands, or close out (a movement, then the Contest). The offence has two choices: shoot, or fake. Against a fake an honest Contest does nothing and the closeout's movement stands, so that defender has spent his Move. The look's worth is the mix of the four outcomes:

   |  | Contest from where he stands | Close out |
   |---|---|---|
   | **Shoot** | the look against standing Contests | the look against the closeout |
   | **Fake** | the look against the closeout (nothing gained) | the follow-up, with the closer spent |

   Where faking gains nothing, the look is worth what it was. A defender already where he contests from can't be faked out of it.
3. **Two-step routes are those follow-ups.** After the fake, the offence takes its best look with the closer so placed. That's one of three things:
   - the shooter's own drive past him (**closeout, then shot fake and drive**);
   - a man cutting toward the rim behind him (**drive, then backdoor cut**);
   - the man he left (**drive, then kick-out**).

   Each route is one look in the sum. Its race is the closer's reach (he closes to whichever square next to the shooter leaves the least) and the follow-up look's own race. The value report now lists these routes: who closes out, from where, what follows, and what each is worth.
4. **The fix-1 shortcuts still give the exact numbers.** The quick reading and the full reference reading both read the mix, and the test that holds them equal passes on more than 20,000 candidates.
5. **Tests.**
   - New: `tests/test_fix3_two_step.py` (D1's route, D2's three, the Move rule).
   - Widened: the fix-1 guard now checks every 3rd board one action on, not every 12th, and adds D2's board to the probe. Answers are shorter now, so it needed more boards to keep its "over 20,000 checked" bar; the bar wasn't lowered.
   - Re-recorded, with a note: fix 2's proof board (section 5).
6. **The record.** D-306 (two-step routes and fakes) and D-307 (one Move a phase) added.

## 3. The proofs, before and after

**D1's board (E1), the setup's shape as Shaun saw it** (X1 M8, X2 E8, X3 G10, X4 D5, X5 I5):

| | Before (fix 2) | After (fix 3) |
|---|---|---|
| The number | 14 | 22.9 |
| O1's drive to F5 | 14, X5 contesting; no route behind it | **drive, then backdoor cut:** X5 closes out to G5; on the fake his Move is spent, and O5 cuts from Q3 to K3 behind him. Contested 14, after the fake 34, the route worth 21.5 |
| Two-step routes read | none | 12 listed, led by O5's cut to K3: X5 closes out, the fake frees O4 at G3 (22.9) |

The setup search now answers it differently. Its new shape (X1 F8, X2 M8, X3 I5, X4 D4, X5 J2) reads 15.7 and puts two defenders in the key (X3 and X5), where before it put one.

**D2's board (E2), the Sharpshooter's three from where he stands (C9),** the setup's shape with X3 moved:

| X3 stands | Before: O2's three | After: O2's three |
|---|---|---|
| **B7**, a Move off him | 12.75 | **15.95**: X3 closes out to B8, the fake beats it |
| **C8**, in front of him | 13.13 | **14.93**: he contests from where he stands, no fake line |
| **D8**, in front, on the diagonal | 13.2 | 15.0, no fake line |
| B8, B9, D9, B10, C10, D10 (beside or behind him) | 12.75 to 13.88 | 15.9 to 15.94: from there his best Contest still needs a movement, so the fake still works |

So on his three, standing off now costs more than standing in front. Before, it was the other way round.

**The whole board's number doesn't reward it yet.**

| Shape | Before: as set / best tight / best off | After: as set / best tight / best off |
|---|---|---|
| The fix 2 setup (X3 on O2 at B7) | 15 / 15 / 15 | 23.47 / 23.47 / **22.36** (X3 at F7, helping at the rim) |
| The new setup (X1 I7, X2 E9, X3 I2, X4 B6, X5 G3; X2 on O2, two off) | 21.78 / 21.78 / 21.56 | 21.83 / 22.28 / **21.83** |

Why: the number is the offence's single best route, and on E2 that's at the rim, not O2's three. The one-Move rule and the fake make a lone rim protector easy to beat. A cutter at G4 draws X5's closeout; a fake there leaves O5 open at K3, worth 34. So the best use of the third defender is helping at the rim, and the new setup does exactly that (X3 to I2, X5 to G3).

D2's check (the Sharpshooter gets tighter defence) won't pass from this fix alone. It needs the rim covered first. Fix 4 (what on-ball position is worth) is the next lever on it.

## 4. Times, before and after

One at a time, nothing else running, the engine held to 256 MB:

| Thinking | Before (fix 2) | After (fix 3) |
|---|---|---|
| D2's defence setup (E2) | 25.5 s | 25.9 s |
| D1's defence setup (E1) | 22.9 s | 36.8 s |
| A turn with a shot and blocks in it (E13) | 12.0 s | 12.3 s |

E1's setup got slower. A look the mix reads can only be bounded by what it's worth against standing Contests, which is a looser ceiling, so fewer looks get skipped. The fake's follow-ups themselves are read best first and stop early.

## 5. What it proves

| Check | Result | Time |
|---|---|---|
| `tests/test_fix3_two_step.py`: D1's route, D2's three, the Move rule, both engines | 3 passed | 6 s |
| The quick reading against the full one, every candidate both ways (`tests/test_fix1_difference.py`), both engines | 2 passed, 0 different (JavaScript over 20,000 candidates) | 2 min 30 s |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | under 1 min |
| The rules, the memory tests and the golden game | 33 passed, no golden value moved | 1 min 57 s |
| The value's own guards (`tests/test_exam.py`: every movement read in full, the memory, the mix in both engines, both engines on five boards) | 10 passed | 59 s |
| Fix 2's proof board (`tests/test_fix2_every_phase.py`), re-recorded with a note | passed | 2 s |

Fix 2's proof board was re-recorded because this fix changes its reading. It now reads 24.48, and no answer movement lowers it, because the rim route sets the number. Fix 2's limit itself is unchanged and is still held by the every-look reference.

The tests ran four lanes side by side in 2 min 32 s. The proofs and timings took about 5 minutes more. Calibrating the widened guard while building took about 4 minutes on top, so everything counted comes to about 11 or 12 minutes. **Not run:** the exam (as asked) and the rest of the suite.

## 6. What in the design I couldn't build as written

- **"Read by its own race, with the actions it really has."** The follow-up after the fake is read on the board as the defence stands before its answer. It doesn't see the rotations the answer makes. The fix: read the follow-up again after each answer movement. That makes it depend on the answer, so the fix-1 shortcut would need a new bound for it, which is why it isn't in this fix.
- **The kick-out's pass** comes from where the map's looks already pass from (the ball handler's square, or where his one movement takes him this turn, D-250), not from the drive's finishing square. The fix: a pass chance from the drive's square for the follow-up, read by the rules' own pass race.
- **The backdoor cut** is the cutter's own look from the map, not a separate two-turn race. The cut has to be a look the map already reads.
- **The fake is the shot fake only.** The pass fake isn't in the mix; the design names shot fakes. It applies where the rules allow: the shooter in control, and the phase's fake or Hesitate unused (every later phase has one).

## 7. For Shaun to decide

1. **E2's help.** The number now says a lone rim protector against a cutter loses to the fake and the drop-off, so the defence spends its third man at the rim before it tightens on the Sharpshooter. Is that the basketball you want, or should D2 wait for fix 4?
2. **What counts as tight.** Only in front of the shooter (C8, D8 for O2) kills the fake. Beside or behind him, a defender's best Contest still needs a movement, so the fake still works. Is that the rule you meant?

## 8. Noticed, not touched

- The Coverage view's own answer lines use the older answer code (the coverage map's answers), not the number's answer. The one-Move rule is in the number's answer only.
- The number's value rose on many boards: the fake now prices every closeout. E1's setup value went from 14 to 15.7, and E2's from 15 to 21.8.

## 9. Model for the next step

Claude Opus 5.5, effort high. Fix 4 (what on-ball position is worth) is the next lever on D1 and D2, and it touches both engines' contest reading.
