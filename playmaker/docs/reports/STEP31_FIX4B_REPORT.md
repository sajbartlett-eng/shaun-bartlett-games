# Step 31, fix 4b: pressure controls direction. Report

**Built in both engines, on branch `step-31`. Not merged. The exam was not run.**

- **P5 reads the way you expected:**
  - Pressing with the open side toward the help: **36**.
  - Standing two off: 38.
  - Giving up the side with no help: 38.
- **The P5 control reads level** (36 against 35.94), and so does P4 now (27 against 26.72), with the race read after the answer.
- **On P1, pressing still reads worse** (30 against 26.48). Section 3 says why.
- **The cost:** the offence setup more than doubled (113 s to 256 s). Section 5 has the times.

## 1. Changes to the printed game

None.

## 2. What was built (both engines, D-313, except where it says JavaScript)

1. **Arrows chosen by the number, with the square, all five together.** Each defender takes the arrow pair that leaves the offence's whole number lowest (drives, passes, the shot and his contest together).
   - The setup search reads every square and every arrow pair for each defender, round after round, with the others as they stand, until none lowers the number.
   - **Fixed:** when two defenders swap squares, each now reads every arrow pair. Before, each faced the man nearest him: a rule of thumb.
   - **New options:** hold one defender's square (and his arrows if given), or read arrows only. That's how a board's question (pressed, or two off) is read with everything else chosen around it. JavaScript only: the setup search lives there.
   - The defence's answer inside the number already read all eight pairs for every movement.
2. **The race reads advantages the offence can create, not only those that exist now:**
   - **A Dribble on his man,** from next to him (where he stands, or one Move on), at the rules' chance (Dribble less Agility). Won, his man is locked and his zone broken. It's raced this phase if the offence has the actions, else the next.
   - **Speed in the next phase,** with the help as it stands then. Every arrival counts from the phase the advantage comes in.
3. **The race is read after the defence's answer,** on the board the answer leaves. Each answering defender has his Move spent.
   - An answer movement is kept only if, with the races read again, the number still doesn't rise.
   - It also mustn't open an advantage the board didn't have, worth more than the number.
4. **One Move a phase in the race.** A defender who has already moved this phase has no Move left in it.
5. **The on-ball defender** is the one guarding the ball. "Removes the most" is reported as `removes_most`; it decides who should guard the ball when matchups are set.
6. **G5** now reads boards where the backdoor cuts are covered (E23d to E23f). O4 and O5 stand deep with no shot, so their defenders help on the low blocks.

## 3. The proof

**P1 to P4.** The ball's defender is held on his square. The search chose his arrows and everyone else's squares and arrows together. (`docs/runs/step31/fix4b_onball.txt`)

| Board | Pressed | Two off | Pressed: his arrows; the shape | Two off: his arrows |
|---|---|---|---|---|
| P1, top | **30** | 26.48 | N+NE; I9, D8, A7, K4, H4 | NW+N |
| P2, short range | 29.91 | 27 | N+NE | NE+E |
| P3, corner | **26.75** | 27 | S+SW; G3, H6, E8, B4, K3 | N+NE |
| P4, control | 27 | 26.72 | N+NE | N+NE |

- **P3:** pressing now reads better, by 0.25. Pressed, the corner leaves O4 4 squares nearer the rim; two off, 11.
- **P4:** the control reads level, as you expected. It no longer reads 31.5 against 24, now that the race comes after the answer.
- **P1 and P2:** pressing still reads worse.
  - On P1 the search found no arrow pair whose open side runs into help in time. O1's speed to E6 reads 30 pressed, with no helper able to contain in that phase.
  - Two off, X1's cushion stops the blow-by. The best race left is a Move next to him, then the Dribble, at 24.75.

**P5.** Help on the right only: X3 sags off O3 (Rim Runner C, three 5). On the left, X2 stays on the Sharpshooter (three 11).
- Every square is as the board has it.
- X1 is held on I9 with each pair in turn, and every other defender's arrows are chosen by the number.

| X1's arrows | Number | Drive squares left him this turn | His shot now | Best drive | Best pass |
|---|---|---|---|---|---|
| **NW+N** (walls the west, gives up the east, toward X3) | **36** | 6, all east | 12 | 36 | 35 |
| N+NE (walls the east, gives up the west: no help) | 38 | 6, all west | 12 | 38 | 35.33 |
| any other pair (walls neither side) | 38 | 12 | 18.69 | 38 | 36 |
| two off (I8, arrows by the number) | 38 | 11 | 21.51 | 38 | 35.33 |
| the control (I13): pressed 36, two off 35.94 | | | | | |

**Where the difference comes from, with no weights.** These are your four expected effects:
- **Best help coverage: shows.**
  - Giving up the west, O1's drive finishes at G2 untouched: 38.
  - There, only X2 can help, rushed and only in phase 1, and that leaves the Sharpshooter (the kick to O2 at G4, 34 to 36).
  - Giving up the east, X3 helps in phase 0 (O1's shot drops to 15.15), and the drive reads 36.
- **A specific denial target: shows on the west, not on the east.**
  - On the west the help would leave the Sharpshooter.
  - On the east the 36 isn't the help leaving O3: it's O4's baseline cut to G2 (36), open whichever way X1 faces.
- **Least passing lanes: barely shows** (35 against 35.33 and 36). The passes that matter are to cutters at the rim (O4 to G2, O2 to G4), and they're the same from either side.
- **Least area: doesn't arise at the top,** where there's no baseline. In the corner (P3) it does: pressing leaves O4 4 squares, two off 11.

## 4. Other numbers that moved

**The created advantages raise many readings:**

| Board | Fix 4 | Fix 4b | Why |
|---|---|---|---|
| R4 | 29.42 | **38** | Next phase the Quick Steps are back and speed beats X1 |
| R5a | 36 | 37.96 | The created Dribble |
| R5c | 29 | 29.98 | The created Dribble |
| R5 control | 29 | 29.98 | The created Dribble |

- R1, R2, R3 and R5b are unchanged.
- **R4's check** ("no advantage, no race may start") no longer holds.
- **E1's defence setup** now reads 21 (was 14.2), in a new shape.

**G5 on the covered boards:** both sag 30, one covered 30, both covered 30.
- Covering one of two equal threes leaves the number unchanged.
- Covering both doesn't lower it, because O1's created Dribble race (30) and O2's move to the corner for a three (A3, 30) hold it there. The test fails on that; I didn't force it.

## 5. Cost, and the checks

One at a time, the engine held to 256 MB:

| Reading | Fix 4 | Fix 4b | Added |
|---|---|---|---|
| A turn on E13 | 14.1 s | 15.1 s | +1.0 s |
| Defence setup (E1) | 134 s | 91 s | −43 s (a new shape, found in fewer rounds) |
| Offence setup (E15b) | 113 s | **256 s** | +143 s |

**What added it:**
- The races read again after each answer movement.
- More races a board (the created advantages).
- Swaps reading every arrow pair.

Nothing was narrowed. The only savings are exact ones (the start-skipping cut covers the new speed starts too).

| Check | Result | Time |
|---|---|---|
| Both engines, R1 to R5 and P1 to P4 (the on-ball reading) | the same on all | about 1 min |
| Engine equality (40 random positions) | 0 mismatches | in lane 3 |
| Fix 2's, fix 3's and fix 4's tests | 6 passed | in lane 3 |
| The rules, memory and golden game | 33 passed | 138 s |
| The value's guards | 13 passed, 1 failed (G5, section 4) | 199 s |
| The P1 to P5 proof (20 searches, 4 at a time) | section 3 | 266 s |

- The tests ran three lanes side by side in 3 min 20 s. With the proof, tests and proofs took about 8 minutes.
- The timings took about 6 minutes more.
- **Not run, because it can't fit:** `tests/test_fix1_difference.py`. **Not run, as asked:** the exam.
  - It now records P1 to P5 from the held searches.
  - P2's "mostly the contest" check still reads the boards as written.

## 6. Still not built as written

- **The fake mix's own race** is still read on the board before the answer.
- **A Quick Step spent in the answer** isn't taken off that defender in the race; only his Move is.
- **A created Dribble that fails** goes to the route's next phase, where it can be tried again. So a 50-in-100 Dribble each phase reads close to a sure blow-by over a possession.
- **The on-ball reading** counts a look with a chance below 1 at its chance times its worth, so it shows such drives lower than the number does.
- **The Steal as the answer to a shot** (as in fix 4).

## 7. For Shaun to decide

1. **The created Dribble.** By the rules, a Dribble can be tried every phase. With O1's 50 in 100 against X1, the number reads the blow-by as nearly certain over a possession. Is that right, or should a failed Dribble cost something more than the phase?
2. **R4.** It now has an advantage next phase (speed). Rewrite R4 so the offence has no Quick Steps next phase either, or keep it as a speed board?
3. **The offence setup's time** (256 s). Look for exact savings next, or accept it?

## 8. Model for the next step

Claude Opus 5.5, effort high. Fix 5 (ties broken by the next-best line), after your answers to section 7.
