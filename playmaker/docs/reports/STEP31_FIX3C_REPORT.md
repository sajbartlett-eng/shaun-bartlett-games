# Step 31, fix 3c: the drive's race, rebuilt from an advantage. Report

**Built in both engines, on branch `step-31`. Not merged. The full exam was not run.**

- **What holds:** both engines read the same numbers on all eight R boards and on 40 random positions. A drive starts only from an advantage. The beaten defender never contains; he chases for a reduced Contest at best.
- **What fails:**
  1. **The cost.** A turn on E13 went from 11.2 s to 41.0 s.
  2. **The 10-minute budget.** The shortcut-against-full check couldn't finish inside 15 minutes. A smaller version (571 boards) is exact.
  3. **R5's spread.** R5a and R5b read the same, and R5c reads level with the control. The numbers are in section 4.

## 1. Changes to the printed game

None.

## 2. What was built (both engines, D-310)

1. **A drive starts only from an advantage.**
   - **A Dribble won:** the beaten defender is locked, and a Quick Step is his only movement that phase.
   - **A shot fake beating a closeout:** the closer's Move is spent. This is read inside the fake mix, as the fake's follow-up.
   - **Speed:** a Quick Step or Sprint to a square his man can't get in front of this phase.
   - **An open lane:** his man's zone (both arrows' rays, as far as his movement reaches) doesn't cover the straight line to the rim. With a partial lane, his first movement may only use the part the zone doesn't cover.
   - With no advantage, no race starts. R4 and the R5 control start none.
2. **The beaten defender chases and never contains.** His best is a Contest 3 less from beside, or 6 less from behind, and 2 more off if he needed a Quick Step, never below 1. In the phase of the advantage he counts as behind the ball.
3. **Every line.** Every square the handler's movement reaches nearer the rim is raced, on real paths round bodies (his and every defender's).
4. **Quick Steps left.** Each side's Quick Steps (Sprints count) are read phase by phase: the board's own in this phase, two in each phase after.
5. **Every choice, each phase.**
   - **Defence:** contain (a helper in front in time, set or rushed, which frees his man); help late (an off-balance Contest, which also frees his man); or stay home (the chaser alone). Protecting the rim and giving up the mid-range is staying home, then containing at the rim later.
   - **Offence:** shoot, kick to anyone, fake a helper who had to move to contain (he is then spent), hesitate, or carry on. A freed man takes his own best look by his card, read without his defender, with the pass raced from the handler's square. The offence gets one Hesitate or fake per phase, by the rules.
6. **Who guards whom:** the pairing that keeps the five closest. On every R board this is the setup's own matchups (X1 on O1 through X5 on O5).
7. **Two exact speed-ups.** Each movement step's result is kept for the race. The one-wait-a-phase rule cuts the branching. Together they took Python from up to 33 s a board to under 8 s.

## 3. The boards (`tests/exam_boards.py`; exam checks R1 to R5 in `tools/step_31_exam.py`)

**Cards** (real cards, the ratings named):

| Piece | Card | The rating that matters |
|---|---|---|
| O1 | Attacking Point Guard A | Dribble 19 |
| O1 on R3 | Defensive Point Guard A | Agility 10, Quick Step 2 |
| O2 | Sharpshooter A | three 11 |
| O3 | Rim Runner C | three 5 |
| O4 | Stretch Power Forward A | three 9 |
| O5 | Post Scoring Centre A | layup 19 |
| X1 | Defensive Point Guard C | Agility 8, Quick Step 2 |
| X1 on R3 | Post Scoring Centre C | Agility 3, Quick Step 0 |
| X2, X3, X4 | Two-way Defender B, Two-way Wing B, Defensive Small Forward B | |
| X5 | Rim Protector A | layup contest 12, Block 10 |

**One square moved:** the right block, L3, is a mid-range square, so O5 is on K3 (the nearest paint square) and X5 beside him on J3.

**The boards:**
- **R1:** made by playing O1's Dribble on X1 and taking the win.
- **R2:** O2 with the ball on C9, X2 a Move away on E7.
- **R3:** X1 two squares in front of O1 (I7, one square between them).
- **R4:** the control, X1 in front, offence with no Quick Steps.
- **R5:** O1 on I10, X5 on I4. X1 on K10 for R5a and R5b, on J9 facing south for R5c (his zone covers I8 on the line, not I9), on I9 for the control.

| Board | Quick Steps left (offence, defence) |
|---|---|
| R5a | 2, 0 |
| R5b | 2, 1 |
| R5c | 2, 1 |
| R5 control | 2, 2 |

## 4. Phase by phase (`docs/runs/step31/fix3c_races.txt` has every choice)

**R1, the Dribble won** (worth 30; both sides have 2 Quick Steps):
- **Phase 0, ball on I9.** X1 is locked behind him: his Contest from I8 is 6 less (16). Nobody can contain yet. O1 carries on.
- **Phase 1, ball on E5.**
  - Staying home leaves the pull-up at 30.
  - X2 can contain rushed, but that frees the Sharpshooter for his three from C9 (30).
  - X4 can contain rushed, but the fake beats him (30).
  - X5 can't reach E5's front in time. Every choice reads 30, and the defence stays home.
- **O3 never moves:** on the line the number picks, his defender X3 is never the one who must contain.
- **Why the worth dropped:** it was 36 before the one-fake-a-phase rule. Then the offence could fake X2 and X4 in the same phase; now one fake leaves X4 to contain, with only the kick to O2 left (27).

**R2, the fake beats X2's closeout** (worth 30; read inside the fake mix):
- **Phase 0, ball on C9.** X2 closed out to D8 with his Move. He's behind the ball, his Contest 6 less (30). The best is to shoot now (30); carrying on to C5 reads 28.
- **The fake's branch of the mix** for O2's three is now this race, where before it was a single follow-up look.

**R3, speed** (worth 29.9):
- O1's Sprint takes him to E5. Slow X1 (no Quick Step) can't get in front of E5 this phase.
- **Phase 0, ball on E5.** Nobody contains in time. The best of shoot (18), the kick to O2 (29.9) and carrying on (29.9) is 29.9.

**R4:** no race. **R5 control:** no race.

**R5, side by side:**

| Board | The number | The race | How the race plays |
|---|---|---|---|
| R5a: full lane; offence 2, defence 0 | **38** | open lane 36; speed 38 | Speed: E6, then G4; an open layup unless X5 steps up, which frees O5 at G2 (38) |
| R5b: full lane; offence 2, defence 1 | **38** | open lane 30; speed 38 | Speed: I5, then H3; X5's step-up frees O5 (38) |
| R5c: partial lane; offence 2, defence 1 | **29** | partial lane 28 | X1, diagonal in front, chases from next to him: 24 in phase 0, 28 in phase 1 |
| R5 control: 2 against 2 | **29** | none | |

**X5's dilemma** is in R5a's lane race. In phase 1 on G5, X5 can contain (O1's shot drops to 5.5), but that frees O5 at G2 (38). So the defence stays home and gives up 36.

**Where the numbers differ from what you expected:**
- **R5a doesn't beat R5b.** Both reach an open layup worth 38 (O1's layup 19, times 2) by speed. In R5b, X1's one Quick Step closes the speed line to E6 but not the one to I5, and the lane race does drop from 36 to 30. The best route ties at 38 because both reach the card's top value.
- **R5c reads 29, the same as the control.** With X1 next to him on J9, the chase is never far: his Contest holds the partial-lane drive to 28. That is below the board's best other look (29), so the race doesn't lift the number.

## 5. Cost, and what was proved

**Timed one at a time:**

| Reading | Fix 3b | Fix 3c |
|---|---|---|
| R1, one reading | 0.18 s | 0.66 s |
| R5a, one reading | | 0.37 s |
| A turn on E13 | 11.2 s | **41.0 s** |

The setups weren't timed. At this rate they'd take several minutes each.

**Where the time goes:** each board runs up to about 20 races (the lane, one per speed square, one per closeout square in the fake mix), and each reads every line through up to four phases.

**The fix:** share one race's states across starts with the same chaser (all the speed squares share them). That changes no number, but I haven't built it.

| Check | Result | Time |
|---|---|---|
| Both engines on R1 to R5 (value, races, worths) | the same on all eight | about 30 s |
| Engine equality (40 random positions) | 0 mismatches | 103 s |
| The rules, memory and golden game | 33 passed | 150 s |
| The value's guards, plus fix 2's and fix 3's proofs | 14 passed (fix 2's board re-recorded with a note) | 305 s |
| The quick reading against the full one, the whole check | **didn't finish in 15 minutes** (the JavaScript half alone ran past 10) | |
| The same, on the R boards, E1, E2 and E13 and their boards one action on | 1,425 candidates on 571 boards, **0 different** | 138 s |

All told, the runs took well over the 10 minutes asked for, about 40 minutes.

## 6. Still not built as written

- **Speed.** The handler's leftover Move after a Quick Step in the phase of the advantage isn't used.
- **The chaser's arrival** uses the best square he can reach beside or behind. His Contest from there uses his card's rating less 3 or 6 (and 2 if rushed), without the foul rolls.
- **The fake inside the race** only beats a helper who had to move to contain, and the race doesn't re-run the fake mix there.
- **Who guards whom** is the closest pairing, not a matchup carried on the board.
- **Screens' corner rules** aren't in the race's paths.
- **The race is read on the board as it stands.** The defence's answer inside the number doesn't change it.
- **The speed** (section 5).

## 7. For Shaun to decide

1. **R5a and R5b tie at 38.** Both reach the card's best shot. Do you want the speed race to count the defence's Quick Steps beyond whether X1 gets in front?
2. **R5c reads the same as the control.** By the rules the chase from next to him holds the drive to 28. Is that the partial lane you meant, or should the partial lane give more than one movement's worth?

## 8. Model for the next step

Claude Opus 5.5, effort high. First the speed (sharing race states), then fix 4.
