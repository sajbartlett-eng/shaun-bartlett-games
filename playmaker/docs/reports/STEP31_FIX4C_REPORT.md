# Step 31, fix 4c: a failed Dribble costs what the rules say. Report

**Built in both engines, on branch `step-31`. Not merged. The exam was not run.**

- **The jumps from 4b come back down:**
  - R5a: 37.96 to 36.
  - R5c: 29.98 to 29.
  - The R5 control: 29.98 to 29.
- **Two jumps don't come down:** R4 and E1's setup. In both, a speed race holds the number up, not the Dribble (section 3).
- **R4 is rewritten** with the quickest real card for X1, but it isn't a control yet: it still reads 38.
- **Both engines read the same** on R1 to R5, P1 to P5 and 40 random positions.

## 1. Changes to the printed game

None.

## 2. What was built (both engines, D-314)

1. **A created Dribble that fails, by RULES_CURRENT.md:**
   - **That phase:** he's locked (no Move, Sprint, Dribble or arrow turn) and rushed for the rest of it. He may still Quick Step, as you said.
   - **His options then:** shoot or pass, rushed (2 lower).
   - **The defence that phase:** it acts freely, so any defender who can get in front of where he shoots by its end contests.
   - **The next phase** clears the lock and the rush. He may try again from where he stands, or after a Move next to his man, at the fresh chance.
   - **The retry** faces the defence as it has set itself, its help counted from the failure, as the clock allows.
2. **How the number takes it.** The attempt is worth its chance times the race of the win, plus the rest times that failure line. The route reads it at chance 1, so no retry comes free any more.
3. **Inside the race:** the chaser's arrival counts from the phase he's beaten in, and the help's from the failure.
4. **R4 rewritten:** X1 is Defensive Point Guard A.
   - Like O1, he has 2 Quick Steps, and his Agility 10 is the highest on any card.
   - That still leaves O1's Dribble 19 at 45 in 100. No real card makes it lower.
   - Fix 3c's R4 is kept as R4old.

## 3. The proof, before (4b) and after (4c)

**R1 to R5** (`docs/runs/step31/fix4c_races.txt`):

| Board | 4b | 4c | The created Dribble (its worth, after 4c) |
|---|---|---|---|
| R1 | 30 | 30 | (a Dribble won already) |
| R2 | 29 | 29 | 28 |
| R3 | 36 | 36 | 29.93 |
| **R4 (new, quick X1)** | 38 | **38** | 28.19 at 45 in 100 |
| R4old | 38 | 38 | 28.29 |
| **R5a** | 37.96 | **36** | 34.54 (was 38) |
| R5b | 30 | 30 | 27.55 |
| **R5c** | 29.98 | **29** | 27.98 (was 30) |
| **R5 control** | 29.98 | **29** | 27.58 (was 30) |

**R4 is not a control yet.** Its Dribble now reads 28.19, below the set defence's 29, as you expected. But speed next phase reads 38:
- O1 Quick Steps, then Moves on at once, to G4: five squares.
- The only square in front of G4 nearer the rim is H3. X1, even with 2 Quick Steps, can't reach it in one phase: a Move, then a Quick Step, gets him to G3 or H4, not H3.
- The race doesn't let X1 drop back this phase to keep a cushion, because the defence's answer only proposes movements that lower the map's looks. A step back only to stop next phase's race is never offered.
- The fix: let the answer offer a movement for each race it would stop.

**E1's setup** stays at 21, in the same shape. It's held by the partial-lane and speed races (21 each), not the Dribble.

**P1 to P5.** The held searches, with every arrow chosen by the number (`docs/runs/step31/fix4c_onball.txt`):

| Board | 4b pressed | 4b two off | 4c pressed | 4c two off |
|---|---|---|---|---|
| P1, top | 30 | 26.48 | 30 | 26.25 |
| P2, short range | 29.91 | 27 | **29** | **29** |
| P3, corner | 26.75 | 27 | 27 | 27 |
| P4, control | 27 | 26.72 | **24** | **24** |

P5 is unchanged:

| X1's arrows on P5 | 4b | 4c |
|---|---|---|
| NW+N (open side toward the help) | 36 | 36 |
| N+NE (open side with no help) | 38 | 38 |
| every other pair | 38 | 38 |
| two off | 38 | 38 |
| the control, pressed / two off | 36 / 35.94 | 36 / 35.5 |

- **The P4 control** now reads level, at 24 both ways, and lower than 4b on both sides.
- **P2** is now level.
- **P1:** pressing still reads worse. O1's speed to E6 (30) beats the presser.

**One failed Dribble, phase by phase** (the R5 control, O1 on I10 against X1 in front):

| Phase | What happens | Worth |
|---|---|---|
| 0 | O1 Dribbles at X1, 55 in 100. Won: the race goes on to E6, 30 | |
| 0, lost | Locked on I10, rushed: his shot 9, his pass to O2 at E6 22. Or wait | 24.61 |
| 1 | Lock and rush cleared. He tries again from I10 at 55 in 100. The help has had phase 0 to set, so the win is worth 26.75 | 24.61 |
| 1, lost | Locked again: shot 3, pass 22 | 22 |
| 2 and 3 | Further tries: the win is now worth only 22, and the help is fully set | 22 |
| **The attempt** | 0.55 × 30 + 0.45 × 24.61 | **27.58** |

The set defence reads 29, so the Dribble no longer lifts the number.

## 4. Cost, and the checks

One at a time, the engine held to 256 MB:

| Reading | 4b | 4c |
|---|---|---|
| A turn on E13 | 15.1 s | 16.4 s |
| Defence setup (E1) | 91 s | 87 s (same shape, 21) |
| Offence setup (E15b) | 256 s | 188 s (same value, 29.375) |

The offence setup got faster: smaller Dribble readings mean fewer answer movements are tried.

| Check | Result | Time |
|---|---|---|
| Both engines on R1 to R5 (with R4old) and P1 to P5 | the same on all | about 2 min |
| The failed Dribble (`tests/test_fix4c_dribble.py`): the worth is chance × win + the rest × the failure line; the retry is at the fresh chance; both engines | passed | in lane 3 |
| Engine equality (40 random positions) | 0 mismatches | in lane 3 |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed | 167 s (lane 3) |
| The rules, memory and golden game | 33 passed | 140 s |
| The value's guards | 13 passed, 1 failed (G5, as in 4b) | 224 s |
| The P1 to P5 proof (20 searches, 4 at a time) | section 3 | 297 s |

- The tests ran three lanes side by side in 3 min 44 s. With the proof, tests and proofs took about 9 minutes.
- The timings took about 5 minutes more.
- **Not run, because it can't fit:** `tests/test_fix1_difference.py`. **Not run, as asked:** the exam.
- R4's exam check is rewritten to your expectation: the number within 1 of the set defence's best look with no race. On these numbers it would fail (38 against 29).

## 5. Still not built as written

- **The defence's answer can't step back just to stop next phase's race.** That's why R4 reads 38 (section 3).
- **The rushed shot after a lost Dribble** is read from the cards as the chaser's Contest is: the shooter 2 lower, without the foul rolls.
- **The retry** reads the defence by when it can arrive, not by a new search of its shape.
- **From the earlier fixes:** the fake mix's own race is read before the answer, and the Steal as the answer to a shot isn't built.

## 6. For Shaun to decide

1. **R4's speed.** Should the defence's answer offer a step back for each race it would stop, so a defender as quick as the guard can keep his cushion? That's the fix that would make R4 a control.
2. **R4's Dribble chance.** No real card gets O1's Dribble below 45 in 100. Is that low enough, or should R4 use a weaker dribbler for O1?

## 7. Model for the next step

Claude Opus 5.5, effort high. The answer's step back (if you agree), then fix 5.
