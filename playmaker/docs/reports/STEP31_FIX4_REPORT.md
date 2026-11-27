# Step 31, fix 4 of 7: what on-ball position is worth. Report

**Built in both engines, on branch `step-31`. Not merged. The exam was not run.**

- **The reading is built.** What each defender's stance removes from the ball handler's real options is read by the number itself. Both engines read the same on all eight P boards.
- **A rules gap is fixed.** Inside the drive's race, the ball handler's movement now obeys the arrows' walls, as it does everywhere else. Nothing on R1 to R5 changed.
- **P1 to P4 mostly disagree with your expectations.** P2 passes. On P1 and P4 pressing reads worse, and on P3 it reads level.
  - **The cause is one thing: speed.** O1 has 2 Quick Steps and X1 has 1. Pressed, X1 is beaten by O1's speed. Two off, he can still get in front.
  - **The proof:** give X1 a card with 2 Quick Steps and pressing reads better on P1, and level on P4, the control.
- **Not built:** the Steal as the answer to a shot (section 7).

## 1. Changes to the printed game

None.

## 2. The two small things first

**(a) The start-skipping cut (exact).**
- A race's worth from any point is at most what staying home gives the offence there: the open shot, the kick (no more than the look it reaches), or a point a phase on.
- So no race from a start reads more than the best open shot the handler can reach nearer the rim, or the board's best kick.
- A start whose ceiling can't beat the best start already found is skipped.
- On R1 to R5 and the E13 turn, every number is the same. E13 went from 15.5 s to 14.9 s.

**(b) G5 in numbers: why E23a reads 30 and E23b 32.** Nothing changed for it.

| Board | X2 (O2's defender) | X3 (O3's defender) | The best looks | Number |
|---|---|---|---|---|
| E23a | F6, sagging | L6, sagging | O2's three from A3, 30; O3's from P8, 30 | **30** |
| E23b | D8, tight on O2 | L6, sagging | **O2's cut behind X2 to G4: open 36.** X3 closes out to H5 (30 contested), fake 34, mixed 32 | **32** |
| E23c | D8, tight | N8, tight | O2's cut to G4 and O3's to J4, 34 each | **34** |

- Sagging at F6, X2 stood in O2's cutting lane. Tight at D8, he opens the backdoor cut behind him, which beats O2's three.
- So covering the shooter tight raises the number here. The check assumed the two threes were the looks that mattered; on this board the cuts are.

**E13's guards, rewritten as you asked.** "He takes the shot unless playing on reads higher, and the report says what beats it."
- Since fix 3c, O5's cut from the corner to G3 reads 38 against O4's shot at 36, and the turn passes to O5.
- The value report now has `beats_shot`: O5 at G3 from D3, worth 38, by a pass then the shot.
- Both guards pass. Nothing else was loosened.

## 3. What was built (both engines, D-312)

1. **The reading: what each stance removes.**
   - For each defender, the number is read again with him lifted off the court.
   - The difference is split by the handler's options as the number reads them:
     - **Shot:** his shot now.
     - **Drives:** every look that moves him, including the drive's races.
     - **Passes:** each teammate's look, at its pass chance.
     - **Holding:** what holding the ball where he stands costs him (the Steal and the closely guarded count).
   - Each is at its real cost in actions, because the answer, the fake on a closeout, the opened lanes and the races are all inside the number.
   - There's no weight anywhere: how much is contest and how much is denial is whatever the number reads.
   - It's in the value report as `onball` when asked for (`onball: true`).
2. **The on-ball defender** is the one whose lifting raises the handler's own shot and drives the most. Of two level, the nearer one.
3. **The walls inside the race (a rules gap, now closed).** The map always obeyed the rules' walls, but the race checked only bodies.
   - Now, in the phase of the advantage, the handler's movement can't cross a line a defender's arrows bar him (D-170). That includes the speed start's own path.
   - A defender beaten by a Dribble, or by the fake in the fake mix, has his zone broken.
4. **A man nobody guards.** A defender off the court now guards nobody. A handler nobody guards gets the open lane's race with no chaser.
   - Before, lifting his defender left no race at all, so an unguarded handler could read lower than one his defender was chasing.
   - This only happens in the reading, never on a real board.
5. **The P boards' defence.** The other four come from the stance search's own starting shape (the goal-side base positions), written into the boards. Only the one defender changes.

## 4. The boards (`tests/exam_boards.py`; the exam's P checks in `tools/step_31_exam.py`)

**Cards:**
- **Offence: Race five.** O1 is Attacking Point Guard A: Dribble 19, 2 Quick Steps, three 9, layup 19.
- **Defence: Iron Wall.** X1 is Defensive Point Guard B: 1 Quick Step, Agility 9, Steal 5, mid-range contest 6. X4 is Defensive Small Forward B.

**Squares:**

| Board | Ball handler | Pressed | Two off | The other four |
|---|---|---|---|---|
| P1 | O1, I10 (top of the key) | X1 I9, arrows N and NE | X1 I8, facing him | D8, K4, D3, J2 |
| P2 | O1, I6 (mid-range) | X1 I5, arrows N and NE | X1 I4, facing him | D8, M7, B3, J2 |
| P3 | O4, A3 (corner) | X4 B4, arrows SE and S | X4 C5, facing him | I6, E7, I2, O3 |
| P4 | O1, I13 (deep, no shot) | X1 I12, arrows N and NE | X1 I11, facing him | E7, L6, E3, J2 |

**How I chose the arrows: by the rules' own movement test, not the number.**
- **In front (P1, P2, P4):** any pair leaves O1 12 squares nearer the rim, except N and NE (and its mirror), which leave 6. A defender in front can wall only one side; that is the most he can wall.
- **In the corner (P3):** SE and S close the middle (C4, D3, E3) and leave the baseline open (C1, C2). That is "force baseline".

## 5. The proof, side by side

What the ball's defender removes, pressed and two off (points, the number with him lifted minus with him there):

| Board | Number pressed | Number two off | Pressed removes: shot, drives, passes | Two off removes: shot, drives, passes | Exam check |
|---|---|---|---|---|---|
| P1 | **30** | 27 | 15, 0, 1.5 | 6.82, 3, 3 | fail |
| P2 | 28 | 28 | 4.5, 2, 3 | 0, 2, 3 | **pass**: the difference is all contest |
| P3 | 27 | 27 | 3.96, 3, 3 | 2.63, 3, 3 | fail |
| P4 | **31.5** | 24 | none, 0, −1.5 | none, 6, 6 | fail |

Holding the ball costs O1 nothing on any of these boards. The full readings, all five defenders each, are in `docs/runs/step31/fix4_onball.txt`.

**Why the number disagrees with you on P1, P3 and P4: speed.**
- **Pressed at I9,** X1 walls the east side, but O1 Quick Steps, then Moves on at once, west to E6. That beats X1: from I9 he can't get in front of E6 this phase.
  - In front of E6 means F5. That is 3 across and 4 down from I9, and his one phase is a Move (2 diagonal) and a Quick Step (1).
  - So O1's drive reads 30 with X1 pressing, and 30 with X1 lifted off the court. Pressing removes 0 from his drives.
- **Two off at I8,** X1 reaches F5 in one phase (3 diagonal), so no speed race starts. He removes 3 from the drives and 3 from the passes.
- **P4** is the same thing in the backcourt. Pressed at I12, X1 is beaten by speed to D11. Two off at I11 he isn't.
  - The race isn't changed by the defence's answer (not built yet), so it holds the pressed number at 30 or more, while two off the answer brings it to 24.
- **P3:** pressing in the corner takes more off his shot (3.96 against 2.63). But the baseline left open gives him a speed drive (27). The number stays 27 either way, set by drives and kicks at 27 that neither stance removes.
  - The defender who removes most from O4's own options is X3 at the rim (7). On these boards the rim help, not the corner defender, does most of the work.

**The same boards with a quicker X1** (Defensive Point Guard C, 2 Quick Steps; a probe, not an exam board, `docs/runs/step31/fix4_quick_x1_probe.txt`):

| Board | Pressed | Two off | What pressed X1 removes: shot, drives, passes |
|---|---|---|---|
| P1 | **25.99** | 27 | 12, 4.01, 6.38 |
| P4 (the control) | **24** | **24** | none, 6, 6.38 |

- A presser who can keep up reads better at the top, and level in the control.
- The number can read what you described. On these cards, the rules say a defender with 1 Quick Step shouldn't press a guard with 2.

**What standing two off costs is inside these numbers:**
- **The closeout:** on P1 two off, O1's three reads 20.18 against 12 pressed, because X1 has to close out with his Move and can be faked.
- **The lanes it opens:** none open on these boards. Two off on the same line still stands on the lane, so the open-lane race doesn't start.

**The on-ball defender, by the reading:**
- **P2 and P4 two off:** X1.
- **P1 pressed:** X2. X1, beaten by speed, removes nothing from O1's drives, while X2 on the west side removes 3.
- **P1 two off:** X5.
- **P3:** X3, at the rim.

## 6. Cost, and the checks

One at a time, the engine held to 256 MB:

| Reading | Fix 3d | Fix 4 |
|---|---|---|
| A turn on E13 | 15.5 s | **14.1 s** (same choice as fix 3c) |
| Defence setup (E1) | 135 s | **134 s** (same shape, 14.2) |
| Offence setup (E15b) | 129 s | **113 s** (same value, 24) |

| Check | Result | Time |
|---|---|---|
| Both engines on P1 to P4, the on-ball reading (`tests/test_fix4_onball.py`) | the same on all eight | 38 s (with the walls test) |
| The walls inside the race: arrows walling the east send O1's speed start west; the mirror sends it east | passed | in the above |
| Both engines on R1 to R5 | the same on all eight, every number as fix 3d | about 15 s |
| Engine equality (40 random positions) | 0 mismatches | 45 s |
| The rules, memory and golden game | 33 passed | 126 s |
| The value's guards, with E13's two rewritten | 13 passed, 1 failed (G5, as before and explained above) | 162 s |
| Fix 2's and fix 3's proofs | passed | in lane 3 |

- The tests ran three lanes side by side in 2 min 42 s. The proofs took about 2 minutes more, so tests and proofs fit inside 10 minutes.
- The timings took about 5 minutes on top.
- **Not run, because it can't fit:** the quick reading against the full one (`tests/test_fix1_difference.py`). **Not run, as asked:** the exam.

## 7. Still not built as written

- **The Steal as the answer to a shot.** The rules allow it from next to the shooter with an arrow on him. It isn't in the number.
  - On P1 it wouldn't change the answer. O1 (Dribble 19) keeps the ball 70 in 100 against X1's Steal 5, and X1 fouls 1 in 4.
  - So a Steal on O1's three (27 open) is worth about 21.3 to the offence, against the contest's 12. The contest stays the answer.
  - It would matter against weaker dribblers. Building it reaches into every look's contest and the defence's answer in both engines, which is why it isn't in this fix.
- **The race isn't changed by the defence's answer.** That's why P4's pressed number holds at 30 or more.
- **Who guards whom inside the race** is still the closest pairing of the defenders on the court. The on-ball reading names the defender who removes most, but the race doesn't use it.
- **The fake mix's race** treats the closer the fake beat as having his zone broken (as after a won Dribble). Every other defender's walls hold.
- **The walls are read in the phase of the advantage.** After it, the race reads defenders by when they arrive, as before.

## 8. For Shaun to decide

1. **Speed against pressure.** By the rules, a defender with 1 Quick Step who presses a guard with 2 gets beaten on his open side. Is that the basketball you want, or should a pressing defender get something more (both sides walled, or a reaction step)?
2. **G5.** On E23 tight coverage opens the backdoor cut. Should the check use a board where the cut is covered, or measure the threes only?
3. **The on-ball defender.** I named the one who removes most from the handler's own shot and drives. That's sometimes the rim help (X3 on P3). Is that what you meant, or only defenders next to the ball?

## 9. Model for the next step

Claude Opus 5.5, effort high. Fix 5 (ties broken by the next-best line), or the speed question first if you rule on it.
