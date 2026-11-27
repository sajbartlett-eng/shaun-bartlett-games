# Step 31, fix 3d: the speed start by the rules, and a faster race. Report

**Built in both engines, on branch `step-31`. Not merged. The exam was not run as asked (one slip, in section 5).**

- **The speed start now follows the rules.** A Quick Step leaves him his Move. He can stop and keep it, or Move on at once before the defence moves. A Sprint uses both.
- **Fix 3c had a rules bug that this fixes.** It let a Move follow a Sprint in the same phase. Every speed number that moved on R1 to R5 moved for one of these two reasons. Nothing else moved.
- **Both engines read the same** on all eight R boards and on 40 random positions.
- **The cost:**
  - A turn on E13 went from 39.0 s to 15.5 s. That's still short of 11 s (section 4).
  - The setups went from about 8 minutes each to just over 2.
  - Fix 3d first ran out of a phone's memory on the defence setup. I found the cause and fixed it; it now fits.

## 1. Changes to the printed game

None.

## 2. What was built (both engines, D-311)

1. **The speed start, by the rules.**
   - **A Quick Step alone:** he keeps his Move. The race reads that Move after the defence's turn, as in fix 3c.
   - **A Quick Step, then a Move at once:** he moves before the defence does, and nothing is left to him that phase. This is new.
   - **A Sprint:** his Move and his Quick Step together. Nothing is left to him that phase. Fix 3c wrongly let him Move again.
   - Each end square is a speed start if his man can't get in front of it this phase. The race report now says how he got there (`start_by`) and whether he has a Move left (`move_left`).
2. **Exact speed-ups (no number changed):**
   - **Shared states:** races with the same chaser share their states from phase 1 on.
   - **Movement kept across boards:** each movement's result is reused while the bodies near it stay put.
   - **Fewer repeats:**
     - one fake race per helper and square;
     - each man's looks sorted once per board;
     - one race kit per board, shared by the drives and the fake mix.
3. **Memory.** States are shared now, so each board's race kept about 237,000 full choice tables alive. That pushed the defence setup past 256 MB. Now each state keeps only its worth. The choice table is rebuilt only for the line the report shows. That rebuild is exact: no state leans on itself, because carrying on and hesitating go a phase on, and a fake spends a helper. Movement results are also stored compactly.

## 3. The boards: every number the same as fix 3c, except these

| Board | Fix 3c | Fix 3d | Why |
|---|---|---|---|
| R1 | 30 | 30 | |
| R2 | 29 | 29 | |
| **R3** | 29.93 | **36** | the leftover Move |
| R4 | 29.42 | 29.42 | |
| **R5a** | 38 | **36** | the Sprint correction |
| **R5b** | 38 | **30** | the Sprint correction |
| R5c | 29 | 29 | |
| R5 control | 29 | 29 | |

Every other race, phase and choice on these boards is the same, to the digit (`docs/runs/step31/fix3d_races.txt` has them all).

**R3: speed, worth 29.93 before, 36 now**
- **Fix 3c:** O1 Sprinted from I9 to E5, then Moved again in the same phase toward F3, which the rules don't allow.
  - Phase 0 on E5: the shot 18, the kick to O2 at I11 29.93, carrying on 29.93. **Worth 29.93.**
- **Fix 3d:** O1 Quick Steps, then Moves on at once to G4, before the defence moves. Nothing is left to him that phase.
  - Phase 0 on G4: nobody can contain in time. The shot 36, the kick to O2 29.93, waiting for the next phase 29.93. **Worth 36: he shoots.**
- Fix 3c could reach G4 only by keeping the Move until after the defence's turn. By then X1 had time to recover. Using the Move at once beats him there.

**R5a: offence 2 Quick Steps, defence 0, worth 38 before, 36 now**
- **Fix 3c:** a Sprint to E6, then a Move to G4 in the same phase (not allowed). Phase 1 on G4: an open layup, 38.
- **Fix 3d:** the best legal start is a Quick Step, then a Move to G5. Nothing is left.
  - Phase 0 on G5: the shot 30, waiting 36.
  - Phase 1 on G5: X5 can contain (the shot drops to 5.5), but that frees O5 at G2 (38). So the defence stays home. Carry on to K2.
  - Phase 2 on K2: the shot 36. X5 containing again frees O5 (38), so the defence stays home.
  - **Worth 36,** the same as the open-lane race.

**R5b: offence 2, defence 1, worth 38 before, 30 now**
- **Fix 3c:** a Sprint to I5, then a Move to H3 in the same phase (not allowed). An open layup, 38.
- **Fix 3d:** the best legal start is a Quick Step, then a Move to E6. Nothing is left.
  - Phase 0 on E6: the shot 30, the kick to O2 20.93, waiting 30. **Worth 30,** the same as the open-lane race.

**R5 side by side now:**

| Board | Fix 3c | Fix 3d |
|---|---|---|
| R5a | 38 | 36 |
| R5b | 38 | 30 |
| R5c | 29 | 29 |
| R5 control | 29 | 29 |

With the Sprint read by the rules, R5a now beats R5b. X1's one Quick Step in R5b costs the offence 6. The R5a and R5b tie you accepted in fix 3c came from the bug. R5c stays level with the control, as you ruled.

**Fix 2's proof board (E2, X3 on C10), 30 before, 26 now: the Sprint correction**
- **Fix 3c:** O1 Sprinted from I11 to I7, then Moved on to H5 in the same phase. That line was worth 30.
- **Fix 3d:** I7 leaves him nothing that phase. He shoots from I7: **26.**
- Still no answer movement lowers it. The test is re-recorded with a note.

**Readings with the setups and the turn:**
- **E1 defence setup:** the same shape and value as fix 3c (X1 H9, X2 B8, X3 I5, X4 N9, X5 N4; 14.2).
- **E13 turn:** the same choice and line as fix 3c.
- **E15b offence setup:** it changed. Fix 3c's pick (O2 with the ball at I13, O3 on C8, O4 on D7) still reads 21.5. The runner-up (O2 on C8, O3 with the ball at I13, O4 on D6) rose from 20.12 to 24, so the setup now picks it. That's the speed start reading more for that shape.

## 4. Cost

One at a time, the engine held to 256 MB:

| Reading | Fix 3c | Fix 3d |
|---|---|---|
| A turn on E13 | 39.0 s | **15.5 s** |
| Defence setup (E1) | 512 s | **135 s** |
| Offence setup (E15b) | 473 s | **129 s** |
| R1, one reading | 0.65 s | 0.48 s |

The fix 3c setups ran alongside one other job, so they may read a little slow.

**Why E13 isn't near 11 s yet:**
- The exact speed-ups alone brought it to 13.8 s.
- The new speed starts (Quick Step, then Move) add races, which took it back to 15.5 s.
- The race and its kit are now about a quarter of the turn. The rest is reading the board, about as it was before fix 3c.

**The next exact saving:** skip a speed start whose ceiling can't beat the best start already found. Its ceiling is its open shot or the best kick, read before the race. Like the other cuts, this changes no number.

## 5. What was proved, and the time it took

| Check | Result | Time |
|---|---|---|
| R1 to R5, fix 3d against fix 3c (every race, phase and choice) | the same, except R3, R5a and R5b (section 3) | about 1 min, several runs |
| Both engines on R1 to R5 (value, races, worths) | the same on all eight | about 15 s a run |
| Engine equality (40 random positions) | 0 mismatches | 45 s |
| The rules, memory and golden game | 33 passed | 116 s |
| Fix 2's and fix 3's proofs | 4 passed (fix 2's board re-recorded with a note) | 16 s |
| The value's guards | 11 passed, 3 failed (below) | 117 s |
| The E13 turn against fix 3c | the same result | |

**The 3 failed guards fail on the fix 3c commit too, with the same numbers.** I checked by running the guards on that commit (347 s). So fix 3d didn't cause them. Fix 3c's report listed 14 passing; that run was before the end of fix 3c. The numbers:
- **E13, "take the good shot":** the shot reads 36, but playing on reads 38. A shot fake on X4's closeout at J3 is worth 38. Two guards hold that playing on is never worth more than the shot.
- **G5:** E23a and E23b should read the same, since covering one of two equal looks leaves the other. They read 30 and 32.
- I didn't loosen or re-record these. They need your call, or a later fix.

**A slip:** once I ran `tests/test_exam.py` without filtering it to the guards (118 s). That also ran the exam's checks. Another short run caught three more checks (6 s). I haven't read or used their results.

**Time:**
- The fast tests and the proofs took about 6 minutes, inside the 10 asked for.
- The setup timings took about 25 minutes more, most of it fix 3c's own setups.
- So did finding the memory fault, and checking the 3 guards on fix 3c.

**Not run, because it can't fit in 10 minutes:** the quick reading against the full one (`tests/test_fix1_difference.py`). It ran past 15 minutes after fix 3c. **Not run, as asked:** the exam.

## 6. Still not built as written

- **The chaser's arrival** uses the best square he can reach beside or behind. His Contest there is his card's rating less 3 or 6 (and 2 more if rushed), without the foul rolls.
- **The fake inside the race** only beats a helper who had to move to contain. The race doesn't re-run the fake mix there.
- **Who guards whom** is the closest pairing, not a matchup carried on the board.
- **Screens' corner rules** aren't in the race's paths.
- **The race is read on the board as it stands.** The defence's answer inside the number doesn't change it.
- **The speed** (section 4).

## 7. For Shaun to decide

1. **The 3 failing guards** (section 5). On E13, should a shot fake beating the closeout be allowed to read above the shot? Or should the guard hold and the number change?
2. **R5 now reads 36, 30, 29, 29.** Does that spread match what you meant?

## 8. Model for the next step

Claude Opus 5.5, effort high. First the start-skipping cut (section 4), then fix 4.
