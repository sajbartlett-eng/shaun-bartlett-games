# Step 31, fix 4g: each race names its own answers. Report

**On branch `step-31`. Not merged. The exam was not run.**

- **Built, in both engines, in play.** Each race on the board names the movements that would stop it, and those are read in full beside the map's own best. Both engines read the same on all 21 R and P boards.
- **Against the exact answer: the same number on 16 of 21 boards.** The five misses are 0.25 to 1.9 points, and every one is explained below. They fall into two kinds:
  - a defender who gets to the race in time from off its named squares: two helpers, and one drop to the rim (three boards);
  - a two-step route, the closeout then the fake and drive, which no race names (three boards).
- **The test had a fault of its own, now fixed.** A movement tried and taken back could leave stale readings of the fake's follow-up. It touched the full reading and the exact answer too. With it fixed, they still agree on all nine R boards. The exact number moved on P2 (31.84 to 31.5), and R4's exact answer is now one movement (same number, 29).
- **Not playable yet.** On four cores within 256 MB, a turn takes 30 to 36 s (target about 20) and the setups 8 and 15 minutes (target about a minute). Section 5 says where the time goes.
- **The per-square race saving is not folded in.** Here it would save at most a sixth of the race reads (section 5).
- **Design version 7 is on the branch,** with its two new sections, the levels table and the floor.

## 1. Changes to the printed game

None.

## 2. What was built (D-318)

1. **Each race names its answers.** For every race the number turns on:
   - **in front of its line:** each phase's ball square, and its neighbours nearer the rim;
   - **a helper arriving in time:** any defender who reaches one of those squares;
   - **a step into its passing lane:** the squares between the ball and the teammate it kicks to, both staying home and as the defence picks;
   - **a drop to where it finishes:** the squares round the line's last ball square.
2. **Who is read.** Every defender who reaches a named square with one movement.
   - A Move there faces the ball's square on the line.
   - A Quick Step or Sprint keeps the arrows it leaves him.
3. **How it's read.** Each named movement is played, its races read again on the board it leaves, and taken back. That's exactly how the full reading reads it.
   - The map's own best is read the same way and kept if the races don't raise the number.
   - The best of them is the answer, taken in the same order as before, so ties fall the same way.
4. **The fault in the test, fixed (both engines).**
   - The answer keeps the board after each of its movements, so a look whose shot goes up earlier reads its fake's follow-up there (D-316).
   - Those kept boards saved their follow-up readings, but read the races live. So a movement tried and taken back could leave readings made with its own races, and the same board could read differently depending on what had been tried before. On P2 it read 31.84, then 31.5 once a later movement was tried and taken back. With the fix it reads 31.5 every time.
   - Now each kept board keeps the races as they read on it, so a movement tried since can't change it. That is Shaun's ruling, applied to the races too.
   - The board being read keeps no follow-up across a fresh reading of its races.
   - The full reading and the exact answer share this code, so the fix applies to the test as well.

## 3. The proof: the new answer against the exact one

All read live (`docs/runs/step31/fix4g_proof.txt`, `.json`). On R1 to R5 the full reading was read too, and it equals the exact answer on all nine boards, number and movements.

| Board | Exact | New | Gap | The exact answer | The new answer |
|---|---|---|---|---|---|
| R1 | 29.42 | 29.42 | 0 | X3 to J8 | the same |
| R2 | 29 | 29 | 0 | none | none |
| R3 | 36 | 36 | 0 | none | none |
| R4 | 29 | 29 | 0 | X1 to H8 | X4 to F4, X2 to C7 |
| R4c | 29.67 | 29.67 | 0 | X1 to H8 | X4 to F4, X2 to C7 |
| R5a | 36 | 36 | 0 | none | none |
| **R5b** | **29** | **30** | **+1** | X3 to J8 (Sprint) | none |
| R5c | 29 | 29 | 0 | none | none |
| R5 control | 29 | 29 | 0 | none | none |
| P1 | 30 | 30 | 0 | none | none |
| **P1 two off** | **28.5** | **28.75** | **+0.25** | X3 to I6 | none |
| P2 | 31.5 | 31.5 | 0 | X1 to I2, facing N | X1 to I2, facing S |
| **P2 two off** | **30** | **31.5** | **+1.5** | X1 to K2, X2 to D9 | X5 to I3 |
| P3 | 27 | 27 | 0 | X2 to E8 | the same |
| P3 two off | 27 | 27 | 0 | X2 to E8 | the same |
| **P4** | **30** | **31.5** | **+1.5** | X2 to D6 | X2 to B7 |
| **P4 two off** | **29.63** | **31.5** | **+1.88** | X2 to D7 | X2 to B7 |
| P5 | 38 | 38 | 0 | none | none |
| P5 two off | 38 | 38 | 0 | none | none |
| P5 control | 36 | 36 | 0 | none | none |
| P5 control, two off | 36 | 36 | 0 | X1 to E11 (the number the same) | none |

- **On these boards the new answer is never lower than the exact one.** It reads a part of what the exact one reads.
- On R4, R4c and P2 it finds the same number by other movements.

## 4. Each miss: the movement, and why no race named it

| Board | Missed movement | What it stops | Why no race named it |
|---|---|---|---|
| R5b (+1) | X3 Sprints N8 to J8 | O1's open lane from I10 and both speed races to E6: all three gone | **A helper arriving from off the line.** J8 is two squares from the line (I10, E6). From there X3 gets in front in time; he's never on a line square now |
| P1 two off (+0.25) | X3 K4 to I6 | O1's Dribble race (its line J8, L6): 28.75 to 28.5 | **The same kind.** I6 is two squares from J8. X3 arrives as the help, from beside the line |
| P2 two off (+1.5), step 1 | X1 I4 to K2 | O1's Dribble race from H4: gone | **The drop to the rim.** The race's line stops at H4, its only phase read, so "where it finishes" was named round H4. The drive finishes at the rim, and K2 is beside it |
| P2 two off, step 2 | X2 D8 to D9 | O2's closeout, then fake and drive, from H10: 31.5 to 16.75 | **A two-step route, not a race.** No race is on the board by then |
| P4 (+1.5) | X2 E7 to D6 | O2's closeout, then fake and drive, at A5: 31.5 to 16.75 | **A two-step route, not a race.** No race on the board at all |
| P4 two off (+1.88) | X2 E7 to D7 | the same look: 31.5 to 16.75 | **The same** |

**Why the map's own candidates miss the two-step routes.** The map puts forward a movement only if it lowers a look as the look reads now. It reads the fake's follow-up without the movement played. X2's step to D6 matters only after the fake, where he's in place to stop O2's drive. So the map never offers it. Fix 4e found the same thing.

**Where a race named the square but the arrow differed** (no number lost):
- R4 and R4c: X1 to H8. The exact answer faces him NE; the new one would face him toward G4, the ball's square on the line. It reached 29 and 29.67 by other movements.
- P2: X1 to I2. The exact answer faces him N; the new one S, toward H2. The same 31.5.

**What this says to name next:**
1. **Helpers arriving in time:** a square from which a defender reaches the line by the phase the ball gets there, not only the line's own squares.
2. **Where a drive finishes:** round the rim, when the line stops short of it.
3. **The two-step routes:** each names its answers as a race does: the closeout square, and where the drive after the fake goes.
4. **A Move's arrows:** read each of a named square's arrow pairs, not only the one facing the line.

The first three cover all five misses on these boards. Each adds movements to read, so each costs time (section 5).

## 5. Times, memory and the per-square saving

Four cores, the engine and each worker held to 256 MB, one reading at a time (`docs/runs/step31/fix4g_times.txt`):

| Reading | Fix 4f (answer in play then) | Fix 4g | Target |
|---|---|---|---|
| A turn on E13 | 12.7 s (7.4 s warm) | **35.5 s (29.6 s warm)** | about 20 s: **not met** |
| Defence setup (E1) | 49 s | **461 s** | about a minute: **not met** |
| Offence setup (E15b) | 114 s | **927 s** | about a minute: **not met** |
| One R or P board | about 0.5 s | 0.7 to 3.4 s | |
| The exact answer, one board | | 25 to 121 s | |

- **Memory held:** every worker ran under its 256 MB cap and none failed.
- **Where the time goes.** Each reading where a race is on the board now reads 20 to 29 named movements in full. Each one re-reads every race three phases ahead, from scratch. A turn reads a few hundred boards; a setup reads thousands, so it grows most.
- **The exact saving I'd build next:** read each named movement's races by difference, with fix 4e's machinery. It's exact, and fix 4e proved it against reading afresh. In fix 4e it kept too much in memory because it ran for every legal movement; here it would run for about 25.

**The per-square saving is not folded in.** Over the 16 steps where races named answers, 389 movements came from 322 named squares: 1.2 a square. A Move faces the line, and a Quick Step or Sprint has its fixed arrows, so a square rarely has more than one movement to share a race reading. At best it would save about a sixth of the race reads. It also needs every race's trace kept on every board, and that is what ran out of memory in fix 4e.

## 6. The checks

| Check | Result | Time |
|---|---|---|
| The proof: the full reading, the exact answer and the new one, R1 to R5 and P1 to P5 | section 3; the full reading equals the exact answer on all nine R boards | 8.5 min, four at a time |
| Both engines with the new answer, all 21 R and P boards | the same number and answer on all 21 | about 6 min |
| Engine equality (40 random positions) | 0 mismatches | in lane C |
| Fix 4g's tests: both engines take the same race-named answer (R4, P2, P3); a movement taken back leaves the number as it was (P2) | 2 passed | in lane D |
| Fix 4e's and 4f's tests | 4 passed | in lane D (307 s) |
| Fix 2's, 3's, 4's and 4c's tests | 7 passed, after the two changes below | lane C (716 s) |
| The rules, memory and golden game | 33 passed | lane A (159 s) |
| The value's guards | 12 passed; G5 failed, as in 4b to 4f; the memory check stopped at its 10-minute limit (below) | lane B (17 min) |

**Two tests changed, and why:**
- **E2 re-recorded** (fix 2's test), as at fixes 3, 3c and 3d. The speed race now names X2's Sprint from M8 to I8, beside where it finishes, and the number falls from 26 to 24.48. The exact answer takes the same movement at the same number, and so does Python.
- **The engines compared at the number's own precision** (fix 4's and 4f's tests). The JavaScript engine reports the number to 4 decimals. These tests held it to Python's full number within 0.000001, which passed only while the numbers were round. R4c now reads 29.67 in play. Python's number, rounded the same way, must now equal it exactly.

**The memory check** reads every third legal action on five exam boards, each a full reading, and compares it with a fresh one. Each reading is slower now, so it passed its 10-minute limit. Run from a copy without the limit, one board per core, it passes: 1,024 boards, every one the same as read fresh (E13 82, E16 79, E24 373, E29 406, E30 84). E29 alone took 9 minutes. The test's limit is unchanged.

- **Tests and proofs took over the 10 minutes:** the four lanes about 17 minutes side by side (lane B the longest), the proof 8.5.
- **Not run, as asked:** the exam.

## 7. For Shaun to decide

1. **Name more answers, in the order of section 4:** helpers arriving in time, the drive's finish at the rim, and the two-step routes. Together they cover all five misses here. Each costs time, and I'd measure each against the exact answer as it's added.
2. **The arrows of a named Move:** read every arrow pair there, or only the one facing the line? Facing the line lost nothing on these boards.

## 8. Model for the next step

Claude Opus 5.5, effort high. Your answers to section 7, then the levels.
