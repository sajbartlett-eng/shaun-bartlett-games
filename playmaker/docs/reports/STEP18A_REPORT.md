# Step 18a report: the calibrated default checked, the table's map, and the candidate diagnosis

## The candidate diagnosis

**The answer is mixed: two boards are candidate faults, four are judgement faults, and three are ties.** For each
failing decision I rebuilt the search's own list, read every legal team turn one team turn ahead, and searched the
best 300 (and the best 50 board moves) 1 pair ahead (`diagnosis.json`, no pick noise).

| Board | What the search does | The board's move | Cause |
|---|---|---|---|
| 1, defend the drive | shifts a wing defender one square | none of the 350 turns its reading likes best stops the drive | **judgement** |
| 3, help the helper | does nothing; that reads best of all 272,947 legal turns | none of 15,336 is ever generated; the best reads 1.6 worse | **judgement** |
| 6, the open catch | moves another player, keeping the shot open | the shot is generated, then cut by the list's length; it reads 1.7 less than keeping it open | **judgement** (the horizon fault, below) |
| 8, the backdoor cut | shuffles the wing sideways | the cut is generated, ranked 71st, cut by the list's length; it reads 6.0 less | **judgement** (the horizon fault) |
| 9, the kick-out | moves the ball handler and a wing | wins by 0.7 when searched; its first action is never followed by a second | **candidates** |
| 11, the last-phase pass | dribbles at his man | the pass wins by 11.1 when searched; it is generated, then cut by the list's length | **candidates** |
| 5, 7, 10 | the search's best turn meets the board, or ties with one that does | | a tie, or lost at the pick |

- **How narrow the list is.** On offence it holds 24 of 15,000 to 21,000 legal team turns, built from 31 to 38 of
  about 230 legal actions. On defence: 24 of 270,000 to 530,000, built from 14 to 20 of about 1,000.
- **Yet on positions from play the list is mostly enough** (`regret.json`, 48 offence positions): the search's
  choice is the best turn found on 32 of 48. The average left on the table is 0.75 points a decision (interval 0.3
  to 1.2), by the computer's own reading. When something better existed, 12 times in 16 its first action was never
  generated. The defence wasn't measured this way (8 core-minutes a position; the cap).
- **The horizon fault, a third cause.** When the look-ahead ends just as a shot is declared, the search reads that
  position as it would any other, before the Contest. On board 8 a contested three reads 42.3 there; with the
  Contest played it is worth 9. The calibrated map isn't applied at that point either. So a one-action turn that
  leaves a shot open outranks a real cut.
  - The `play_on` switch (built at step 12, off, 4% slower) settles declared shots. With it board 8's cut is within
    0.2 of the choice and board 6's shot is level (`diagnosis_play_on.json`).
  - It changes the choice on 19 of 48 play positions. It also does more than settle shots, so whether it plays
    better needs a head-to-head. Not run: the cap.

## The level checks (D-138, D-142)

Each level with the calibrated reading against itself without it; 160 pairs, 1 pair ahead, its own pick noise.

| Level | Gain a pair | Interval | Points on offence | Average shot phase | Decisions |
|---|---|---|---|---|---|
| Rookie | **+4.9** | +1.7 to +8.0 | 22.1 against 17.2 | 3.6 against 4.1 | 40 against 51 |
| Starter | **+2.8** | +0.4 to +5.2 | 29.5 against 26.6 | 2.9 against 4.3 | 32 against 49 |
| All-Star (step 17D) | +3.2 | +0.9 to +5.5 | | 2.1 against 3.5 | 21 against 38 |
| All-Star, Junior Amateur | +1.7 | **-0.4 to +3.8: not clear** | 20.0 against 18.3 | 2.2 against 2.9 | 22 against 29 |

- **The levels stay in order** (80 pairs each): All-Star over Starter by 6.8 (interval +3.6 to +9.9); Starter over
  Rookie by 10.0 (interval +6.8 to +13.3).
- **Shot timing (D-139),** calibrated, shots by phase 1 to 6: Rookie 12, 21, 15, 19, 18, 15%; Starter 18, 25, 24,
  17, 10, 5%; All-Star 35, 29, 20, 11, 4, 0%. The clock ran out on 3 in 100 for the Rookie, 0 in 160 for the Starter
  and 0 in 80 for the All-Star.
- **The 19 boards:** 9 at 1 pair and 10 on the clock, the same counts as before. Board 10 gained, board 16 lost.

## The table's rules (D-141)

The All-Star playing itself from the Senior Pro starts under the table's rules, 200 possessions each.

| | Before calibration | Calibrated, the app's map | Calibrated, the table's own map | Basketball |
|---|---|---|---|---|
| Points a possession | 30.2 (29.1 to 31.3) | 30.5 (29.9 to 31.2) | 32.1 (31.3 to 32.9) | |
| The clock runs out (a forced shot) | 9 in 100 (5.8 to 13.8) | 0 in 200 (0 to 1.9) | 3.5 in 100 (1.7 to 7.0) | about 1 |
| Shots by phase, 1 to 6 | 21, 14, 12, 12, 6, 36% | 39, 34, 19, 7, 2, 0% | 16, 18, 16, 15, 19, 16% | |
| Decisions a possession | 46 | 20 | 41 | |

- **The table needs its own map.** Positions there go on to earn 29 to 30 at every phase; the app's map says 25 to
  27. Held-out error: 8.26 with the table's own map against 8.94 with the app's, clear of zero (`tabletop_fit.json`).
- **The table's own map plays better at the table:** +1.7 points a pair against the app's map (interval +0.6 to
  +2.8, 160 pairs). It is built into both engines.
- **Plan step 24 is not closed.** The expiry rate fell from 9 in 100 to 3.5, not to 1.

## Compute against the predictions

Cap: about 9 core-hours. Used: about 9.2. Every prediction is in `docs/runs/step18/PREDICTIONS.md`.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| Rookie and Starter checks | 1.9; +0.5 to +2.5 and +1 to +3 | 1.60 | the Rookie's gain was above the range |
| The order of the levels | 1.1; All-Star's lead probably not clear | 0.79 | **wrong:** both leads are clear and larger |
| Junior Amateur | 1.4; +1 to +3 | 0.88 | in range, not clear of zero |
| The table, before and after calibration | 2.0; expiry 5 to 12, then 0 to 2; no need for its own map | 1.77 | expiry as predicted; **wrong** on points (higher, not lower) and on the map |
| The table's own map: self-play and head to head | 1.4; expiry 0 to 2; early shots | 2.09 | **over on cost; wrong** on expiry (3.5) and on timing (even) |
| The 19 boards | 0.2; 9 to 11 | 0.05 | as predicted |
| The diagnosis, two passes | 1.5; boards 8 and 9 judgement, board 1 candidates | 1.3 | **wrong** on boards 1 and 9 |
| Positions from play, two passes | 1.2; choice best on 30% to 50% | 0.6 | **wrong:** 67%; the defence dropped for the cap |

## 1. Changes to the printed game

None.

## 2. What changed

- **Steps 17 and 17D are merged into `main`.** D-138 to D-143 are recorded.
- **`eval.calibrated` is on by default, every level, both engines** (D-138). The playtest site's computer plays
  with it once this is merged.
- **Other ages and standards** (D-142): the Senior Pro map scaled by each level's phase table against Senior Pro's.
- **The table's own map** (D-141): `calibration_tabletop` in the shared weights file, the same form, fitted on 200
  possessions of tabletop-rules play. Both engines use it under the table's rules.
- **Tools:** `tools/step_18.py` (the level checks, the tabletop runs, the diagnosis driver) and
  `tools/diagnose_18.js` (the search's list rebuilt stage by stage, every legal turn read).

## 3. What it proves

- **The two engines agree on the new default:** 1,000 positions across all nine age and standard tables and both
  formats, 0 mismatches, 4 of 4 whole searches equal, before and after the table's map
  (`js_equivalence_calibrated_default.json`, `js_equivalence_tabletop_map.json`).
- **The diagnosis tool's rebuilt list equals the engine's own** on every decision, and its judges agree with the
  boards' own on every turn reported.
- **Speed, against the budget** (`pairtime_calibrated.json`, `pairtime_uncalibrated.json`): the time to finish 1
  pair on 9 decisions in 10, calibrated against not, in seconds.

| Level | Target: desktop, phone | Not calibrated | Calibrated | Calibrated at phone speed |
|---|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.24 | 0.24 | 0.96 |
| Starter | 1.0, 2.0 | 0.57 | 0.56 | 2.25 |
| All-Star | 2.5, 3.0 | 0.99 | 1.08 | 4.32 |

  Inside the desktop budget at every level. At the assumed phone speed the Starter and the All-Star are over, as
  they were before. The look-ahead each level reaches is unchanged.
- **Tests on the new default** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`): 77 pass, 13
  expected failures, 1 unexpected pass, 1 fail. The fail is a timing test (a decision took 1.70 s against a 1.58 s
  limit, on the Python search's clock). Run alone it passes, twice. The machine restarted during this step and the
  whole run took 17 minutes, where it took 12 before. Board 10's test, which failed in step 17's long run, passes.

## 4. For Shaun to decide

- **18b: which fork?** The diagnosis doesn't pick one cleanly. My recommendation, in order:
  1. **First, a head-to-head of `play_on` on the calibrated computer** (about 1.5 core-hours). It is already built
     in both engines, and the search that would make the labels for either fork has this fault in it.
  2. **Then the prior** (the candidates fork), aimed at the two cuts the diagnosis found: actions never generated,
     and passes and shots cut by the list's length. Its labels can't come from a full-width search: a team turn has
     15,000 or more options. The method used here works instead (every legal turn read one team turn ahead, the
     best 300 searched at 1 pair): 11 core-seconds an offence position, 8 core-minutes a defence one.
  3. **Hold the learned weights.** The judgement faults found are specific (a declared shot at the horizon; doing
     nothing reads best on defence), not a general weakness the weights showed any sign of fixing.
- **The table and plan step 24.** Three options:
  - keep the table's own map: best play (+1.7 a pair), the clock out on 3.5 in 100;
  - use the app's map at the table: the clock out on 0 in 200, but weaker play;
  - treat the rest as a rule question. At the table a forced shot still comes when the clock runs out (D-38), so
    holding the ball costs less than in basketball. I'd keep the table's own map and leave step 24 open on that.
- **Junior Amateur.** The gain isn't clear of zero (+1.7, interval -0.4 to +3.8). There is no sign of harm, so the
  default stands (D-138). Its own map comes when there is enough of its play (D-142).

## 5. Noticed, not touched

- **Board 5 is lost at the pick, not in the search.** The search's best turn meets the board; the All-Star's pick
  then takes a screen that reads 1.7 lower, inside its variety margin of 2.
- **Board 7's final phase can't be met on value:** at 1 pair every turn there reads 0, the shot included.
- **Board 16** is judged over a line of three turns, so the single-turn diagnosis doesn't apply to it.
- **The phase tables for the smaller levels are thin** (16 stored possessions each). Junior Pro's scale is 0.55 in
  phase 5 and 0.84 in phase 1.
- **The tabletop pool is the Senior Pro starts under the table's rules,** not stored tabletop possessions.
- **The exam book** is untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high: 18b is new design in both engines (the prior), and reading the `play_on`
head-to-head against shot timing is a judgement call.
