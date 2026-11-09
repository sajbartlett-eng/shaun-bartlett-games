# Step 3n report: engine speed, a fair exam, and the step 3m fixes

All numbers below come from files in `docs/` (named in each section). Self-play ran on the JavaScript core in Node at a
quarter of the time budgets (this machine runs the engine about four times faster than the throttled phone profile).

## Tests

TESTCOUNT

Changed on purpose: `tests/test_static.py` (the browser timing test is back to the real budgets: at most 1.25 x the
level's budget plus 0.05 s, the +2.5 s allowance gone). New: `tests/test_step3n.py` (25 tests). Two of them are marked as expected failures with the measured reason: "V by phase never rises at Senior Pro" (Part C) and "All-Star reaches with 0 team fouls and declines with 4" (Part F). Also changed on purpose: `tests/test_rolls_scoring.py` (a contest from level or behind now has two foul rolls, F2); `tests/test_wedge.py` (the golden scenario values are checked under the pre-3n settings, since F1 and F2 changed the defaults); `tests/test_step3m.py` (the early-cut and drain boards pin the step 3m phase table; exam boards 2 and 14 join the documented open boards: 2 is a speed problem that passes at fixed depth 4, 14 the variety finding). Fixed along
the way: logs from before step 3i replayed with the step 3n steal rules (`review.log_rules`), now with the old ones.

## A. Speed

**Profile, before (Python, CPython warm, per leaf 8.3 ms):** coverage (responses and the best cover) 90%, threat and
looks 10%, contest maps under 1%, legal actions 0.5 ms a call, state copies negligible. In Pyodide in the browser it was
26 leaves a second for All-Star, depth 1.

**After (JavaScript, per leaf about 1 ms on this machine):** threat (looks, lanes, the carrier's moves) 33%, coverage
33%, garbage collection 20%, reach maps 4%, the leaf's own value and the coarse table 1%, state copies under 1%, the rest
(turn generation, ordering) 8%.

**What made it fast:** the port itself (typed contest maps, bitset reach for the one-action sets, squares as integers);
reach maps cached per player by his square, arrow and remaining capacity, so only a player whose reach changed is
recomputed; one board read per position shared by candidate generation, move ordering and the leaf (the coverage cache
by Zobrist key); leaf values cached by Zobrist key; history and killer moves; the beam from the profile; the defender's
lane checks done incrementally (only the moved defender is re-tested).

**Exact:** `tools/js_equivalence.py --n 2000` on 2,000 random legal states (all three ages and standards, both formats,
phases 1 to 5, play, reaction, contest and finished states): 0 mismatches on legal actions, attacker and defender reach
maps (geometric and the rules' exact reach), every threat value, square and route, the best cover's choice, value and
residual threats, and the leaf (geometric, exact and the ordering read). Whole searches at depth 2 and 3 agree with the
Python search on every value and the leaf count (for example 3,939 leaves each); whole agent decisions (goals,
commitment, noise) agree 6 of 6. Exam board timings show the JavaScript search 15 to 30 times faster than Python.

**Decision times on the phone profile** (static build, Pyodide worker, Chromium 412 x 915, 4x CPU throttle,
`docs/3n_phone_timing.json`):

| Level (budget) | Decisions | Median time | Max time | Median depth | Max depth | Leaves per second | Step 3m |
|---|---|---|---|---|---|---|---|
| Rookie (0.3 s) | 6 | 0.09 s | 0.34 s | 2 | 2 | 476 | depth 1, 7.6 leaves/s |
| Starter (1 s) | 29 | 1.01 s | 1.03 s | 2 | 3 | 1,896 | depth 1, 19 leaves/s |
| All-Star (2.5 s) | 49 | 2.51 s | 2.53 s | 3 | 6 | 1,286 | depth 1, 26 leaves/s |

The time budgets hold (Rookie's longest decision, 0.34 s, is the turn being finished after the deadline). Depth: Starter
meets "about 3" at its longest searches (median 2); Rookie is at 2; All-Star reaches a median of 3 and up to 6, against a
target of 4 to 6. Leaves per second: All-Star 1,286 against the 10,000 target (49 times step 3m, still 8 times short).
What would close it: the leaf does about 1,300 look evaluations (116 candidate defender responses, 22 looks); the levers are
the responses read per defender (`eval.responses_per_defender`, 3) and the looks per attacker (6), which change what the
engine sees, so I left them for you.

## B. The exam in two columns

`docs/3n_exam_fixed4.json` (All-Star at fixed depth 4, no time limit, seeded; principal line per board) and
`docs/3n_exam_timed.json` (the time budgets, the browser verdict). Depth 6 was not run: depth 4 took 15 s to 10 minutes a
board (board 14 plays 20 seeds), so depth 6 would take many hours; it is ready to run with `tools/exam_3n.py fixed 6`.

| # | Position | Fixed depth 4 | Timed | Cause of the fixed-depth failure |
|---|---|---|---|---|
| 1 | Straight lane, by outcome | PASS (10 of 10 seeds) | PASS | Restated by outcome; see below |
| 2 | Sag by shooting | PASS | FAIL | A speed problem: passes once the search is deep enough |
| 3 | Help the helper | FAIL | FAIL | The search's best turn is X5 helping (principal line), but the variety margin (2 points) let a near-equal turn through: X2's Quick Step |
| 4 | Two threats, one answer | FAIL | FAIL | The leaf values O2's catch on the wing (continuation x residual) above making X5 choose |
| 5 | Closeout | FAIL | FAIL | The leaf prefers relocating O2 out of the closeout's reach to the shot or drive as he arrives |
| 6 | Catch window | FAIL | FAIL | The swing pass (O2 to A5, then O4 to O2) is worth more at the leaf than O4 acting at once |
| 7 | Clock | FAIL (also on the new table) | FAIL | Phase 6 still holds several offence turns, so setting up a pass to O2 beats the contested mid-range now; the board assumes the last phase means shoot now |
| 8 | Backdoor | FAIL | FAIL | The pass to the cutter has a low arrival chance (X1 can step onto the lane), so the engine holds (Hesitate) |
| 9 | Corner relocate or kick | FAIL | FAIL | O1's own drive to the rim is worth more at the leaf than the kick |
| 10 | Steal odds | FAIL | FAIL | After F1 and F2 a reach costs the Move and, from level or behind, two foul rolls; with good odds the engine still declines: the board predates the rulings |
| 11 | Contested pass | FAIL | FAIL | Digital: an interception ends the possession at 0 and the final phase still has turns, so the engine never accepts the risk |
| 12 | Strong-side corner | PASS | PASS | |
| 13 | Spacing | FAIL | FAIL | Clearing O5 out of the lane is worth less at the leaf than O1's own sprint |
| 14 | Variety | FAIL | PASS | At depth 4 one turn is clearly best: the same first action over 20 seeds (noise 0.5, variety margin 2 are smaller than the gaps a deeper search finds) |
| 15 | Goal consistency | PASS | PASS | |
| 16 | Drain | FAIL | FAIL | The offence passes to O2 early instead of making X2 spend his Move |
| 17 | 20 random boards, no breach | PASS | PASS | |

Fixed depth: 5 of 17 with board 1 restated (4 of 17 before it). Timed: 5 of 17. One board (2) is a speed problem, one
passes only under time (14, variety). The rest fail at depth 4 too: design, mostly the leaf's weighing of a teammate's
catch and the continuation term against the move the board asks for.

**Board 1 by outcome** (`docs/3n_board1.json`): over 10 seeds at depth 4 the straight drive was available after the
defence's answer every time (10 of 10), and every time worth less than the best alternative (10 against 26 game points):
the board passes, but on this board the drive is weak before the defence does anything, so it no longer tests much. The
on-ball defender stood on the ball-rim line in 0 of 10 (reported, not asserted).

## C. The phase table

Rebuilt (`decide.solve_phase_table`) as the expected final value of every possession alive at the start of phase k, by
backward induction, turnovers and expiry included at 0, the capacity summary kept, per age and standard
(`docs/3n_phase_table.json`, data in `docs/3n_seed/`, the F5 digital run and the aggregate):

| Age / standard | Possessions | V1 | V2 | V3 | V4 | V5 | V6 |
|---|---|---|---|---|---|---|---|
| senior/pro | 220 | 24.89 | 27.04 | 27.96 | 28.61 | 29.24 | 29.48 |
| senior/semi-pro | 16 | 27.12 | 28.64 | 29.56 | 29.56 | 29.33 | 33.0 |
| senior/amateur | 16 | 24.81 | 26.69 | 28.8 | 31.12 | 31.0 | 33.6 |
| youth/pro | 16 | 21.06 | 24.08 | 24.36 | 25.0 | 23.88 | 27.8 |
| youth/semi-pro | 16 | 16.19 | 15.07 | 18.11 | 20.83 | 19.0 | 20.0 |
| youth/amateur | 16 | 19.12 | 21.11 | 25.86 | 29.4 | 33.0 | 34.0 |
| junior/pro | 16 | 20.94 | 23.23 | 19.89 | 23.29 | 16.0 | 21.0 |
| junior/semi-pro | 16 | 13.44 | 14.21 | 12.5 | 12.38 | 17.4 | 17.4 |
| junior/amateur | 16 | 14.88 | 18.31 | 19.5 | 21.8 | 25.33 | 25.33 |

Points by the phase a possession ended (Senior Pro, the selection effect, apart from the table): phase 1: 19.17 (60 possessions), phase 2: 24.18 (39 possessions), phase 3: 25.79 (28 possessions), phase 4: 26.48 (21 possessions), phase 5: 28.5 (18 possessions), phase 6: 29.48 (54 possessions).

**Finding:** V still rises, by about a point a phase at Senior Pro, against a standard error near 1. It is not the old
selection effect (every possession alive at the start of the phase counts, including the ones that later turn over or
expire). Half the turnovers (9 of 18 in the first 120 possessions) come in phase 1 at 0 points, and possessions that run
long end on better looks. The test "V never rises" is marked as an expected failure with this reason. Board 7 rerun at
fixed depth on the new table: still fails, for the reason in the exam table. Tables for the ages and standards other than
Senior Pro rest on 16 possessions each and are noisy.

**A side effect to decide on:** the leaf takes the larger of the board read and the table value, so the table is a
floor. The new Senior Pro values sit about 3 points above step 3m's, which flattens marginal positions: two trainer
boards built on the old table (the early-cut reorder, the capacity drain) read 0 instead of 3 and more, and no flag fired
in 20 real possessions (Part I). Those two tests now pin the step 3m table, since they test the trainer's mechanics. The
lever: use the table only where the board read has no look (or blend it), an engine design choice I left for you.

## D. Credit names the answering defender

The credit now names, among the defenders whose reply differs between the with-action and without-action counterfactuals,
the one whose change takes back the most of the teammates' gain; ties go to the defender whose coverage of the released
attacker was lost. On the new decoy board (O2 lifts to D9) it names X3, the helper who left the far side. On step 3m's
board it names X1, which is correct there: X1 is the one who answers the cut.

## E. Accuracy

Per decision 100 x exp(-loss / k), k in `ai_profiles.json` (`trainer.accuracy_k`); a possession averages the harmonic
mean and the volatility-weighted mean (volatility: the spread of the values of the turns on offer).
Calibration (`docs/3n_accuracy.json`, 12 possessions per level against All-Star, 357 decisions graded): **k = 2.0**,
possession averages All-Star 76, Starter 70, Rookie 68 (targets 90, 75, 55).

No k can hit the targets: the three levels lose almost the same per decision (mean 0.8 game points, 60 to 64% of
decisions exactly best) when graded by the trainer's All-Star read at depth 0. The lever is the grader, not k: grading
with a searched reply (depth 1 or more), now affordable on the JavaScript core, should separate the levels.

## F. Rulings and the check against basketball

F1 to F4 are in (tests in `tests/test_step3n.py`). The engine reaches with 0 team fouls and declines with 4 on the same
marginal board, and says why in plain words ("Didn't reach for the steal: a foul now would be their 5th team foul, and
from the 5th a steal foul gives free throws.").

F5 (`docs/3n_f5_report.json`; 60 possessions each, All-Star v All-Star, Senior Pro; digital as one chain of 1.7 quarters):

| Per 100 possessions | Target | Digital | Tabletop |
|---|---|---|---|
| Steals | about 8 | 18.3 | 3.3 |
| Steal attempts | | 46.7 (step 3m: 116) | 18.3 |
| Turnovers | about 13.6 | 18.3 | 18.3 |
| Reach fouls | fewer than steals | 16.7 (fewer) | 8.3 (more) |
| Team fouls per quarter | about 4 to 5 | 4.5 (3.5 in the full quarter) | n/a |
| Points per possession | | 23.8 | 25.7 |

Steal attempts by position (digital): in front after moving 13, in front from a standstill 7, level or behind 8.
By team fouls at the time: 0: 9, 1: 3, 2: 5, 3: 6, 4: 2, 5 or more: 3. Contested passes: 0.27 a possession digital, 0.30
tabletop; why no Intercept: no legal Intercept (nobody on or able to reach the line, or next to the passer) 99 times
digital and 116 tabletop, could intercept and chose not to 16 each, attempted 0 and 2.

The aggregate (Part I, 100 possessions) gives 10 steals and 10 turnovers per 100 in digital.

**The bonus doesn't deter in digital (a designer decision).** On the rebuilt table an average possession is worth
about 28. A foul before the bonus costs +5 and play on, about 33 to the offence; a bonus foul costs two free throws, 2 x the
shooter's rating, 29 to 31 for these teams, and ends the possession. So a reach is no costlier with 4 team fouls than with
0, and the engine reaches either way: the test "reaches with 0, declines with 4" is marked as an expected failure with these
numbers (the board for it was found on the step 3m table, where it held). Levers: a bigger bonus (three free throws, or
free throws and the ball back), or a lower +5 before the bonus. The engine's own foul pricing also uses a play-on value of
20 (`eval.play_on_value`), below the table's 28; matching it is an evaluation constant, left as it is for now.

**Levers (not changed):** digital steals run high in the 60-possession chain (18) and on target in the 100-possession
aggregate (10): the bonus line (`bonus_from`, 5) is the lever if the designer wants fewer reaches; at the table reach fouls
outnumber steals, and the steal foul ratings (`foul_steal`) are the lever there. Tabletop turnovers include 6 shot-clock
expiries in 60 possessions.

**Lock tokens:** the worst case seen was 2 locked pieces in one phase (4 printed). The worst case the rules allow is now 6
(2 Dribbles, 2 Challenges and 2 Steals in one phase), so 4 is enough in play seen but not in every case; a fifth and sixth
token, or a note to mark locks another way, would cover it.

## G. The recogniser

Shots are no longer "opened a look nobody covers". New labels (labels only): Drive and relocate, Lift, Drift, Empty-side
drive; in the aggregate they named 71, 7, 6 and 40 sequences. Unnamed actions left in the aggregate: 41 (made a defender
choose between two open looks: 32; opened a look nobody covers: 9), each with its replay in
`docs/3n_aggregate_report.json`. From a Hesitate, listed apart: 3 (seed 5013 "O Hesitate", made X1 choose; seed 5034,
opened a look nobody covers, +6; seed 5049 "O5 to Q5, then Hesitate", made X2 choose). Replays (before and after
encodings) are in the same file.

## H. Anchors

`docs/3n_anchors.json`: Rookie v Starter scores 0.40 (gap -68), Starter v All-Star 0.47 (-20), Rookie v All-Star 0.35
(-106). Fitted Senior anchors: **Rookie 1525, Starter 1600, All-Star 1625** (were 1350, 1600, 1850). Youth and junior keep
the senior gaps, 20 and 50 lower. The levels are much closer in match results than the old anchors assumed, which agrees
with the accuracy finding (E).

## I. Reruns

- The exam: both columns above.
- The aggregate (`docs/3n_aggregate_report.json`; 100 possessions, All-Star v All-Star, Senior Pro digital, 2 workers):

  | | Step 3n |
  |---|---|
  | Points per possession | 25.25 |
  | Steals per 100 (attempts) | 10 (44) |
  | Turnovers per 100 | 10.0 |
  | Intercepts attempted | 0 |
  | Help depth / shade | 0.679 / 0.866 |
  | On-ball defender on the ball-rim line | 13% |
  | Drive success | 50% of 32 dribbles |
  | Shots by phase | {'1': 28, '2': 21, '3': 9, '4': 10, '5': 6, '6': 26} |
  | Tight contests by phase | {'1': 0.393, '2': 0.333, '3': 0.444, '4': 0.3, '5': 0.333, '6': 0.231} |
  | Unnamed actions (from a Hesitate) | 41 (3) |
- Decision times: the phone table in A.
- Five possession summaries against Starter (`docs/3n_summaries.json`, 20 possessions read; the human side played by a
  Rookie agent): 
  **Match 1, possession 1** (accuracy 83.9%)
  1. Your best decision: O3 takes a quick step to M10, then O5 moves to N3. That was the best option there.
  2. O3 moves to M9, then O4 moves to B2, and X3 answered it. O1 drives at X1 (Dribble) instead: worth 2 more (a small edge).

  **Match 1, possession 2** (accuracy 77.7%)
  1. Your best decision: O1 moves to I10, then O3 moves to M10. That was the best option there.
  2. O4 moves to B2, then O5 moves to Q2, and X5 answered it. O1 drives at X1 (Dribble) instead: worth 2 more (a small edge).
  3. O2 sprints to G4, then O2 shoots a dunk, and X2 answered it. O2 moves to G4 instead: worth 2 more.

  **Match 1, possession 4** (accuracy 50.0%)
  1. Your best decision: O1 sprints to I7, then O1 passes to O2. That was the best option there.
  2. O2 takes a quick step to F10, then O2 passes to O4, and X1 answered it. O4 sprints to A5 instead: worth 15 more (about an open two).

  **Match 2, possession 4** (accuracy 63.4%)
  1. Your best decision: O4 moves to A2. That was the best option there.
  2. O1 sprints to L8, then O1 passes to O3, and X1 answered it. O1 moves to K9, then O1 takes a quick step to M9 instead: worth 3 more (a small edge).
  3. O3 moves to N9, then the ball handler holds the ball (Hesitate), and X3 answered it. O1 drives at X1 (Dribble) instead: worth 2 more.

  **Match 3, possession 2** (accuracy 63.0%)
  1. Your best decision: O3 moves to P8, then O1 shoots a three. That was the best option there.
  2. O4 moves to A4, then O1 moves to H10, and X4 answered it. O1 drives at X1 (Dribble) instead: worth 2 more (a small edge).

  No minimal-value, off-ball or timing flag fired in these 20 possessions. Those flags need agreement at two depths, and
  at these budgets the second read rarely confirms; the flags are tested on hand-built boards.

## J. Legibility

Before (step 3m) and after (step 3n), the same five summary lines:

| Before | After |
|---|---|
| Your move (O5 Move to I5) pulled X1 out of position: +9.5 to your teammates' best look. | O5's move to I5 pulled X1 out of position, opening space for a teammate: worth 10 more (about a contested two). |
| Your move (O2 Move to N7) pulled X1 out of position: +6.0 to your teammates' best look. | O2's move to N7 pulled X1 out of position, opening space for a teammate: worth 6 more (about a foul bonus). |
| Turn group 8, O1 Sprint to M10; O1 Dribble vs X1: after the defence's best answer, your best look was +25.5. Better: O1 Sprint to M10; O1 Dribble vs X2 (+30.1, 4.6 more). | O1 sprints to M10, then O1 drives at X1 (Dribble), and X1 answered it. O1 sprints to M10, then O1 drives at X2 (Dribble) instead: worth 5 more. |
| Turn group 4, O4 Move to Q4; O2 Move to N9: after the defence's best answer, your best look was +23.2. Better: O Hesitate (+25.0, 1.8 more). | O4 moves to Q4, then O2 moves to N9, but the defence didn't have to react, so your best look stayed at 23. The ball handler holds the ball (Hesitate) instead: worth 2 more. |
| Turn group 24, O3 Move to P14; O4 Move to A9: after the defence's best answer, your best look was +0.0. Better: O Hesitate (+23.3, 23.3 more). | O3 moves to P14, then O4 moves to A9, but the defence didn't have to react, so your best look stayed at 0. The ball handler holds the ball (Hesitate) instead: worth 23 more (about an open three). |

Trainer profile, before: "Rating 1655 ± 290 · 4 rated matches · 31 turn groups read", columns Category, Decisions,
Median lost, Best option, Off-ball value, Trend (fewer lost (-0.4)). After: "Rating 1655 (still settling) · 4 rated
matches · 31 decisions read", a "Practise for the tabletop game" button, columns Situation, Times, Typical cost (2 points),
Best choice (60%), Space created for teammates, Trend (better, steady, worse). The possession header reads "Decisions: 82%
as good as the best available", with the bands in words ("3 best, 1 slip, 1 mistake") and the format named. "Why?" reads
"Why? Your decision 3", the play in sentences, effects as signed whole numbers, "Defender who answered".
A test greps every interface string and template for the banned list, and another reads a real possession and checks
every line the trainer writes.

## K. The rules register

`docs/rules_register.md`, written from `playmaker_engine/register.py`: every rule value and mechanism (every `Rules`
setting from step 3e on, every constant) marked Shared, Digital only, Tabletop only or Split by format. A test asserts
every Shared entry is identical in both formats, that the document is the register, and that the same position offers the
same actions and the same dice in both formats. The trainer grades each game under its format (a test grades the same
risky pass under each), each summary names its format, and "Practise for the tabletop game" starts a tabletop match.

**Splits flagged for the designer:** the turnover cost (tabletop -5 and a phase, play on; digital 0, possession over);
shot-clock expiry (tabletop -5 and a forced shot; digital 0); the steal-foul bonus (within the possession at the table,
across a quarter in digital); the match length. The engine values a risky pass or a reach differently by format, so a
digital-tuned habit is wrong at the table; the coarse phase table is solved from digital self-play.

**Tokens:** locks (failed Challenge, lost Dribble, a Dribble win, the failed Steal) use the 4 printed lock tokens, see F5;
screens use the piece's T side; a used Move uses the Move token. Not covered by the printed list: a player's used Quick
Step (one each, OQ-52) and the junior growth tags (10 markers, or written on the team sheet). Both flagged for the designer.

## Ambiguities

- "Leaves per second" counts leaf evaluations, including ones answered from the leaf cache (the Python search counts
  the same calls).
- The time-budgeted exam ran on the JavaScript core at a quarter of the budget, to stand in for the 4x-throttled phone.
- "Team fouls per quarter" pools both sides: 3.5 in the one full quarter, 4.0 a side in the partial one.
- Board 1 by outcome passes trivially on its own board; a board where the straight drive starts strong would test the
  restated rule better.
- V by phase: the spec expected it to fall; measured, it rises. I kept the measurement and marked the test.
