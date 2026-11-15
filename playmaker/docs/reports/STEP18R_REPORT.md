# Step 18r: the agreed rules (D-198): fouls and turnovers in points, play on, no shot from the rim square

**In five lines.**

- **Speed first: under the new rules the slow decisions run over their time** (9 decisions in 10: All-Star 2.4 to 3.0 seconds against 2.5, Starter 1.5 to 1.7 against 1.0; the middle decision is 1.5 to 1.7 at All-Star). A steal or an intercepted pass used to end the line the computer was reading; now play goes on and it reads further. It is the first thing to mend next, with the lane's speed.
- **The rules are built, the same in both engines,** and recorded as D-198: a foul +5, every turnover −5, the phase ends and the next begins, a shooting foul +5 and its free throws, no shot from the rim square, 18i's foul pricing retired. The app only.
- **The reach settled itself, as you said it should.** Reaches fall from 0.80 a possession to 0.07, defensive fouls from 0.33 to 0.01. Nothing sets that by hand.
- **Every possession now ends in a shot,** so points a possession rise from 1.09 to 1.34. No possession ended below zero in 410.
- **Under the new rules help defence shows by play:** with the lane open the offence scores 27.3 (25.0 to 29.7), with help in it 19.9 (16.4 to 23.3). Against help, the forced drive and kick-out beats the offence's own choice by 5: that is your item 2, now with a number on it.

## 1. What was built

`rules.points_play_on` and `rules.no_rim_shot`, both on in the app and off at the table.

| Your ruling | As built |
|---|---|
| A foul is +5, play goes on | Every foul banks +5. The defender who fouls on a steal is still locked (D-179). |
| A steal is −5, play goes on | −5, the ball stays with the ball handler, the phase ends there and the next begins. A stolen shot is cancelled. |
| Every other turnover is −5, play goes on | An intercepted pass, three seconds, closely guarded, the shot clock. |
| After any turnover the phase ends and the next begins | Tokens, movement and locks start again; the clock moves on one phase. |
| After an intercepted pass | The passer keeps the ball. The defender goes back to the square and arrow he began the phase on. |
| A shooting foul is +5 plus its free throws | Built for a foul on the contest and for a steal foul on a declared shot. |
| 18i's foul pricing is retired | The computer no longer prices a foul by the penalty. A foul is its +5 and nothing else. |
| No shot from the rim square | No shot action there, and the computer's reading has no look there. |

**How I read four points you didn't spell out. Say if any is wrong.**

1. **There is no penalty for team fouls any more.** With every foul at +5, free throws from the 5th team foul would price a foul a second time, which is what point 4 retires. The count still shows on screen.
2. **A turnover in the last phase ends the possession on what it has banked,** and so does the shot clock. That can be below zero (−5 with nothing banked).
3. **The counts of three seconds and closely guarded start again** after a turnover.
4. **In the possession's first phase,** "where he started the phase" is where the defender stood when the defence's turn began.

**The table is untouched,** as with every ruling since D-190. It keeps its own turnover and foul rules, and its shot from the rim square.

## 2. What the rules do to play

All-Star against itself, the app's rules, the same 200 starts and dice as step 18o's run before the rules.

| A possession | Before (18o) | After |
|---|---|---|
| Points | 1.09 | 1.34 (1.30 to 1.38) |
| Reaches | 0.80 | 0.07 |
| Defence fouls | 0.33 | 0.01 |
| Turnovers | 0.20 | 0.15 |
| Possessions that ended in a turnover | 20 in 100 | 0 |
| Possessions ended below zero | | 0 of 200 |
| Intercepts tried | 0.01 | 0.15 |
| Phases used | | 2.1 |

- **The reach is now rare, and nothing told it to be.** On your board of 15 November a reach by X1 reads 23.5 for the offence; not reaching reads 23.1 to 23.3. Before the rules it read 18.1.
- **The defence now jumps passing lanes instead.** An intercepted pass costs the offence 5 and the defender goes home, so it is a fair gamble; it tries one in 7 possessions.
- **Starter and Rookie the same way:** 0.11 and 0.17 reaches a possession; 1.28 and 1.17 points.
- **Points a possession are up because the offence always gets its shot.** A fifth of possessions used to end at 0.

## 3. The open lane under the new rules (the start of your item 2)

Your board after the point guard beats X1, forced lines, 16 play-outs a line, the lane reading off.

| Line | Before the rules (18p) | After |
|---|---|---|
| Lane open, the offence as it chooses | 25.1 (20.1 to 30.0) | 27.3 (25.0 to 29.7) |
| Lane open, made to sprint into it | 26.9 (21.6 to 32.1) | 27.1 (25.2 to 29.1) |
| Help in the lane, the offence as it chooses | 22.5 (18.0 to 27.0) | 19.9 (16.4 to 23.3) |
| Help in the lane, made to sprint into it | 23.4 (19.9 to 26.9) | 24.8 (22.7 to 26.8) |

- **Help in the lane is worth 7 points against the offence's own choice, and the ranges no longer overlap.** This is design check 1's defence half, shown by play for the first time.
- **With the lane open the offence no longer loses by its own choice:** 27.3 against 27.1 for the forced sprint. Step 18q's gap came from reaches punishing every turn it waited.
- **With help in the lane it does lose:** made to sprint it scores 24.8, by its own choice 19.9. The forced sprint ends in a pass every time and 10 threes in 16; left alone it settles for a three 16 times in 16. So the computer doesn't yet read what a drive opens for the other four. That is your item 2, and this is its baseline.
- The lane reading itself (`eval.lane`) was not replayed: it is over its time and stays off (your item 3).

## 4. What it proves

- **Both engines agree under the new rules:** 300 positions; 80 more with 8 searches; 200 shot reactions; 0 different.
- **No golden value moved.** Eleven older tests described the rules D-198 replaces (a turnover ends the possession; no +5 in the app; free throws from the 5th foul). Those rules stay in the engine behind the switch, and the tests now run with the switch off and say so. One test's wording follows the screen ("every foul is +5" for "bonus from the 5th").
- **Tests:** `tests/test_rules_current.py` and the named test files: 464 passed, 15 expected failures (14 from before and exam position 14, below), and 1 failed, the timing test (3.3 seconds on one decision against a limit of 1.7; it failed before at 1.95 and the new rules make it worse). Not loosened. `tests/test_static.py`, run on its own: 11 passed. `tests/test_computer.py`: the one failure it had before. The new file is `tests/test_points_play_on_18r.py` (14 tests).
- **The maps were refitted on play under the new rules, and the refit was not kept.** With the refitted maps exam position 12 fails (X2 leaves the elite corner shooter and sprints 5 squares away), reaches rise to 0.21 a possession, and points a possession don't change (1.33). With the maps as they were the position passes. The refit flattens the reading further, which is the fault the plan already lists; so the design position wins over the fit (D-196). The refitted file is kept beside the run for the record (`docs/runs/step18r/refit_not_kept/`). Every number in this report is with the maps as they were.
- **Speed (desktop, seconds; two rounds beside step 18q's code, the lane off):**

  | | Rookie | Starter | All-Star |
  |---|---|---|---|
  | Target, 9 decisions in 10 | 0.3 | 1.0 | 2.5 |
  | Step 18q: middle, 9 in 10 | 0.13, 0.19 to 0.20 | 0.45 to 0.48, 0.59 to 0.66 | 1.15 to 1.27, 1.52 to 1.59 |
  | This step: middle, 9 in 10 | 0.18 to 0.19, 0.28 to 0.51 | 0.53 to 0.57, 1.55 to 1.68 | 1.50 to 1.70, 2.39 to 3.02 |

  **The speed budget is broken at Starter and at the edge or over at Rookie and All-Star.** The middle decision is a fifth to a third slower; the slow ones are far slower. Cause: after a steal or an intercepted pass the possession used to be over, so that branch cost nothing to read; now it is a new phase and the computer reads on from it. The likely remedy is to treat the new phase after a turnover as the end of the line being read. It touches the search in both engines and changes what the computer plays, so it needs its own proof. Not done here.
- **One exam position moved.** Position 14 (the offence varies its first action) passed on step 18q's code and is open again under the new rules. It was already on the list of open positions, so the test run shows it as an expected failure; I am naming it here so it isn't hidden. Position 12 passes with the maps as they were.

## 5. Compute

**6.2 core-hours against an estimate of 5.3** (`docs/runs/step18r/PREDICTIONS.md`). The stop was 10.6.

| Stage | Estimate | Used |
|---|---|---|
| 1a The rules in both engines, agreeing; the tests they move | 1.0 | 1.8 |
| 1b Self-play under the new rules, the refit (not kept) and the replay that showed why | 2.5 | 3.0 |
| 1d Speed, twice (with the refit, then without) | 0.3 | 0.3 |
| 2 The open lane under the new rules, twice (the baseline only) | 1.5 | 1.2 |

Stage 1a ran to 1.8 against 1.0, short of twice: the named tests take 25 minutes a run and were run three times (before the old tests were brought in line, after the refit, and after the refit was dropped).

## 6. Decisions for you (three)

1. **Merge.** This branch is built on step 18q's, which is not merged. I recommend merging pull request 78 and then this one, so the app plays the agreed rules. The cost: until the speed is mended the computer's slow decisions run up to half a second over at All-Star and more than that at Starter.
2. **The four readings in section 1.** I recommend all four as built. The one with most weight is the first: no penalty for team fouls.
3. **The next step, in your order with one addition at the front:**
   - **speed under the new rules** (the turnover line), together with **the lane read inside the speed budget** (your item 3), because both are the same kind of work and nothing can be switched on without them;
   - then **the offence takes an open lane, with what a drive opens for the other four** (your item 2), judged on the new baseline above;
   - then **setup judged by the lane** (your item 4), then **passing options** (your item 5).

## 7. Model advice

Claude Fable 5.2, effort high. The next step is search and speed work in two engines that must stay equal.
