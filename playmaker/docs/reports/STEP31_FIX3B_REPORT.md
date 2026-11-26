# Step 31, fix 3b: the drive's race, and the fake's follow-up after the answer. Report

**Built in both engines, on branch `step-31`. Not merged, as asked. The exam was not run.** Both engines read the same numbers (0 mismatches on 40 random positions, and the exam's both-engines checks). The design file now carries design 5's "Reading ahead is a race, not a tree" and "A drive is read by the same race", and the PDF is filed in `docs/reference/step31/`.

**What moved:**
- **D2:** the Sharpshooter's three with his defender a Move off rose from 15.95 to 20.04, while in front of him it stays 14.93. The setup search now puts a defender next to O2 (X4 at B8).
- **D1:** the drive's race is read and shown phase by phase below. It doesn't move D1's number, because O1's own man recovers in time.

## 1. Changes to the printed game

None.

## 2. What was built

1. **The drive's race (both engines).** From a beaten defender, the ball handler drives at the rim, one phase of movement at a time. If nobody is next to him he needs no Dribble win, and the race starts from where he stands. Each phase he goes to the square nearest the rim that phase reaches, for up to three phases as the clock allows.
   - **Each defender's arrival is raced against him:** the phases before he can contest there set, or at all. The beaten defender can't contain in the phase he was beaten, because he's locked.
   - **The defence's choice each phase:** contain the handler there with a defender set in time, or let him carry on.
   - **The offence's choice each phase:** shoot (against the container's full Contest, or a late defender's off-balance one), kick out to the man the container left, or carry on.
   - **The freed man** takes his own best look by his card: the map's looks of him, read without his defender. The kick-out's pass is raced by the rules from the square where the handler is contained.
   - **Help is taken only when it saves more than the look it leaves,** because the defence takes the least. Each side assumes the other plays well.
   - **One look per drive:** its chance is the Dribble's (1 with nobody next to him), its worth is the race's. The value report shows each race phase by phase (`drive_race`).
2. **The fake's follow-up, on the board the answer leaves (both engines).** After each movement of the defence's answer, the follow-up is read again with that movement in place. A defender who moved closes out only with what his movement left him: after a Move only a Quick Step, after a Quick Step only a Move, after a Sprint nothing.
3. **Your question 2, from the rules.** You were right that RULES_CURRENT.md answers it, and I should have checked before asking. Fix 3's mix already read it that way: an adjacent defender's Contest from where he stands (3 less beside or with his arrow off, 6 less behind) is set against moving in front for the full one. That's why a defender beside O2 can still be faked (section 3).
4. **The record.** D-308 (the drive's race) and D-309 (the follow-up after the answer) added.
5. **Tests.**
   - The fix-1 shortcut-against-full check now reads every 5th board one action on in Python, instead of every 20th. The shorter answers had left it under its bar of 50 candidates; the bar wasn't lowered.
   - Fix 3's proof tests still pass on the new numbers.

## 3. The proofs, before (fix 3) and after (fix 3b)

**D1's board (E1), the setup's shape as Shaun saw it** (X1 M8, X2 E8, X3 G10, X4 D5, X5 I5). The number is 22.9 both before and after. The race exists only after. O1's drive, phase by phase:

| Phase | O1 gets to | If nobody contains him | Who can contain him in time, and what each leaves | The defence's choice | Worth |
|---|---|---|---|---|---|
| 0 (this phase; nobody next to O1, so no Dribble needed) | H7 | a pull-up against X5's late Contest: 9.95 | X3, his own man: shot 7.65, frees nobody. X2: shot 13.75, or the kick to O2 at D4 (8.3). X5: shot 5.45, or the kick to O5 at K3 (8.65) | X3 contains | **7.65** |
| 1 (the next) | H3 | 9.95 | X3: 7.65, frees nobody. **X5: shot 5.45, but frees O5's cut to K3, worth 34.** X1, X4: frees O3 or O4 (16). X2: 16.75 | X3 contains | 7.65 |

O1's own man recovers in time, so the defence needs no help, and taking X5's would hand O5 a 34-point cut. That is "help only when it saves more than the look it leaves" in numbers.

The drive, worth 7.65, sits below the board's best routes, which are the fake-and-cutter routes at the rim (22.9), so it doesn't move D1's number.

The setup search answers differently after: X1 I10, X2 B7, X3 N6, X4 G4, X5 M3, reading 15.7. X1 now stands next to O1 at I11. Before: F8, M8, I5, D4, J2, also 15.7.

**D2's board (E2), the Sharpshooter's three from where he stands (C9),** the setup's shape with X3 moved:

| X3 stands | Before: O2's three | After: O2's three | After: the board |
|---|---|---|---|
| B7, a Move off him | 15.95 (fake, then pass to O5) | **20.04**: X3 closes out to B8, O2 fakes and drives past him to D5 (22 after the fake) | 24.48 |
| B8, beside him | 15.9 | **20.99**: from beside, his standing Contest is 3 less, so he still closes out in front and gets faked | 24.48 |
| C8, in front | 14.93 | **14.93**: no fake can beat him | 24.48 |
| D8, in front, on the diagonal | 15.0 | 15.0 | 24.48 |

On O2's three, standing a Move off now costs 5.1 more than standing in front (it was 1.0 more after fix 3). The follow-up read after the answer finds O2's own drive past the closer, which the board before the answer didn't show.

The board's number still reads the same (24.48) because it's set at the rim, as in fix 3.

**The setup search on E2 changed:** X1 J9, X2 E9, X3 G4, X4 B8, X5 I5, reading 21.65 (before: X1 I7, X2 E9, X3 I2, X4 B6, X5 G3, 21.83). **X4 now stands next to the Sharpshooter (B8)**, which is D2's check. It's beside him, not in front, so the fake still works there. Whether that passes D2 is the exam's call.

## 4. Times, before and after (the cost)

One at a time, nothing else running, the engine held to 256 MB:

| Thinking | Before (fix 3) | After (fix 3b) |
|---|---|---|
| D1's defence setup (E1) | 28.7 s | 18.8 s |
| D2's defence setup (E2) | 20.8 s | 25.0 s |
| A turn with a shot and blocks in it (E13) | 11.3 s | 12.3 s |

The race itself is cheap: one drive line and five defenders' arrivals per board. The cost is the follow-up being read again after each answer movement. E2's setup got about 20 in 100 slower, and the turn about 9 in 100. E1's setup got faster, because its answers stop sooner under the new numbers. These setup times move by several seconds from run to run (E1's "before" read 36.8 s in fix 3's report), so take them as rough.

## 5. What it proves

| Check | Result | Time |
|---|---|---|
| The quick reading against the full one, both engines (`tests/test_fix1_difference.py`) | 2 passed, 0 different | 2 min 33 s (JavaScript) and 38 s (Python, widened) |
| Engine equality (`tools/js_equivalence.py`, 40 random states) | 0 mismatches | under 1 min |
| The rules, the memory tests and the golden game | 33 passed, no golden value moved | 1 min 54 s |
| The value's own guards (`tests/test_exam.py`: every movement read in full, the memory, the mix in both engines, both engines on five boards) | 10 passed | 61 s |
| Fix 2's and fix 3's proof tests | 4 passed | 25 s |
| The proofs and times above (`docs/runs/step31/fix3b_proofs.json`) | as in sections 3 and 4 | about 2 min 30 s |
| Both engines on D1's and D2's shapes, value, phases and answer | the same, to the last digit | about 3 min |

The tests ran four lanes side by side in 2 min 35 s; the widened Python guard took 38 s more, and the proofs and checks about 5 min 30 s. That's about 9 minutes of tests and proofs. Earlier runs while building, including a first try at widening the guard, took a few more. **Not run:** the exam and the rest of the suite.

## 6. What is still not built as written

- **The race's choices are narrower than the design's.**
  - The offence can shoot, kick out to the freed man, or carry on. It doesn't fake or hesitate inside the race, or pass to anyone but the freed man.
  - The defence can contain or let him carry on, which covers "protecting the rim and giving up the mid-range" only through who arrives late.
  - The fix: add those choices to each phase's table; they're more rows of the same kind.
- **One drive line.** Each phase takes the square nearest the rim. A drive along the baseline, or toward the help, isn't raced. The fix: race every square that phase reaches and let the offence take the best line.
- **Arrivals ignore bodies,** as the zone-gap race does (`arrivePhases`). The fix: the real-paths reach the contest maps already use.
- **Who guards whom** is the pairing that keeps the five closest, not the setup's own matchups, because the board doesn't carry them. On D1 it gives the setup's pairs (X3 on O1, X1 on O3, X5 on O5). The fix: carry the setup's matchups on the board.
- **The race is read on the board as the defence stands before its answer.** It models the defence's movements itself, but the answer's own movements don't change it.
- **The freed man positions when his defender contains,** not one phase earlier as "as soon as his defender is the only one who can contain" might mean.
- **Help defence beyond the drive:** a stunt and recover, or a second rotation behind the help, isn't raced.

## 7. For Shaun to decide

1. Fix 4 next, as planned. Your question 1 (does the defence help at the rim first on E2) waits for it.
2. Is "beside him" tight enough for D2? The rules make a defender beside the Sharpshooter 3 less from where he stands, so the fake still beats his move in front (O2's three 20.99 from beside, 14.93 from in front).

## 8. Noticed, not touched

- The E1 setup now puts X1 next to the ball handler (I10 against O1 at I11): ball pressure, which D1's audit asked about.
- The race shows a drive worth well below the fake routes on both boards. The playtest will say whether drives read too cheap.

## 9. Model for the next step

Claude Opus 5.5, effort high. Fix 4 (what on-ball position is worth) touches the contest reading in both engines.
