# Step 18c report: the defence's missing readings

## First: the step's premise didn't hold, and the Rookie has caught the Starter

- **Boards 1 and 3 aren't evidence of a missing reading.** On both, doing nothing is right by the rules (below).
- **The reading I built, `eval.help_readings`, shows no gain** head to head. I'd leave it off.
- **`eval.settle_shots` is now on by default,** as ruled. It lifts the Rookie by 11.4 points a pair, so the Starter
  no longer clearly beats the Rookie. That is yours to judge.
- **Speed:** on today's slower machine the Rookie on the new default sits at its desktop target (0.29 s against
  0.30). Section 3 has the table.

## `eval.settle_shots` at Rookie and Starter (D-148)

Each level with the switch against itself without it; 160 pairs, 1 pair ahead, its own pick noise.

| Level | Gain a pair | Interval | Wins, losses, ties | Points on offence | Shots in phases 1 and 2 |
|---|---|---|---|---|---|
| Rookie | **+11.4** | +8.8 to +13.9 | 120, 27, 13 | 29.9 against 18.5 | 49% against 25% |
| Starter | **+2.4** | +0.3 to +4.5 | 87, 55, 18 | 29.5 against 27.1 | 66% against 46% |

- **Neither loses, so the switch is on by default for every level, in both engines.**
- **The order of the levels on the new default** (80 pairs each):
  - All-Star over Starter: +5.4 a pair (interval +2.6 to +8.1). Still clear.
  - Starter over Rookie: +2.6 (interval -0.8 to +5.9). **No longer clear.** It was +10.0 at step 18a.

## Boards 1 and 3, taken apart

**Board 1 (defend the drive): no defence turn stops it.**

- O1 can sprint to the rim and lay it in before anyone is next to him: 32.
- I played every complete defence turn there is: 457,510 positions. After every one of them the offence still has
  that open 32 (`board_1_replies.json`).
- The board's judge asks for the straight lane to be walled. That can be done, but the layup one square to the side
  is still open, so walling it gains nothing.
- With the switch on the search reads every turn as 32 and picks any. Before, it read 27.6.

**Board 3 (help the helper): doing nothing is right.**

- If O1 goes to the rim after the defence does nothing, the low man (X4) steps next to him in the reaction and
  Contests. The layup is worth 22, less than the 26.7 the possession is worth anyway.
- If the low man steps up early, as the board asks, O1 moves a square and lays it in for 29.5.
- So the board's move is 2.4 worse when searched, and doing nothing is the best of all 272,947 legal turns.

**Why.** The rules give the defence a reaction to every shot: up to two actions, the Contest last. A defender one
Move away can still Contest. On 185 declared shots (step 18b), the defence's best reply was to step in and then
Contest on 119. Early help buys little when late help still arrives.

## The head-to-head, and what was built

**`eval.help_readings` (off): the floor.** With the offence to act, a position is worth at least the best shot the
ball handler can release this turn (from where he stands, or after one movement), settled by the rules.

- **The fault it fixes is real.** With the offence to act, half of all horizon readings (51%) sat below that shot,
  by 4.4 points on average; 67% in the defence's own searches. The calibrated map pulls a shot that can be taken
  now down toward the average.
- **But it doesn't change the play.**

| Against the default, All-Star, 1 pair | Gain a pair | Interval | Result |
|---|---|---|---|
| `eval.help_readings` | +0.4 | -1.1 to +1.9 | stopped at 240 pairs: no gain. 97 wins, 80 losses, 63 ties |

- **The second reading (the look one pass after the help commits) wasn't built as a new reading.** The engine
  already reads it: the best look left after the defence's best cover. Rebuilding it had nothing to aim at once
  boards 1 and 3 fell away and the first reading showed no gain.
- **The `eval.coverage_budget` route wasn't run.** I'd said only if the readings gained alone.
- **The outcome exam wasn't run** for the same reason. The 19 boards: 10 at 1 pair and 10 on the clock, the same
  boards with the switch on as off.

## What the defence's narrow list costs

`tools/diagnose_18.js`'s method on 11 defence positions from play, spread over the phases (`regret.json`,
`regret_help.json`). Each has about 200,000 to 500,000 legal team turns; the search's list is built from about 60.

| | Switch off | Switch on |
|---|---|---|
| The search's choice is the best turn found | 4 of 11 | 8 of 11 |
| Left on the table, points a decision | 1.2 (interval 0.4 to 2.1) | 0.9 (interval -0.3 to +2.0) |
| Where the better turns were lost | all 7: the first action was never generated | all 3: never generated |

- **It costs more than the offence's list** (0.75 at step 18a), on a small sample.
- **Two of the largest losses are the same move: step next to the ball handler, then Steal** (3.8 and 2.9 points).
  The list never offers a step followed by a Steal.

## Shot timing (D-139)

From the head-to-heads, the engine on offence (`shot_timing.json`). The app's rules only.

| | Default (`eval.settle_shots` on) | With `eval.help_readings` | Rookie, default | Starter, default |
|---|---|---|---|---|
| Shots in phases 1 and 2 | 69% | 75% | 49% | 66% |
| Shots by phase, 1 to 6 | 36, 33, 23, 6, 2, 0% | 37, 38, 15, 8, 1, 1% | 12, 37, 20, 14, 7, 10% | 24, 42, 20, 9, 4, 1% |
| Decisions a possession | 20 | 19 | 31 | 23 |
| The clock runs out | 0 in 240 | 0 in 240 | 0 in 160 | 0 in 160 |
| The ball lost, in 100 phases kept | 5.5 (3.3 to 9.0) | 6.1 (3.7 to 9.8) | 4.2 (2.5 to 6.9) | 4.9 (2.8 to 8.5) |

## Compute against the estimate

Estimate: about 14 core-hours. Used: about 8. Predictions: `docs/runs/step18c/PREDICTIONS.md`.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| `eval.settle_shots` at Rookie and Starter | 1.5; no clear difference at Rookie, 0 to +3 at Starter | 1.59 | **wrong** at Rookie: +11.4 |
| Head to head, `eval.help_readings` | 1.0 to 2.5; +1 to +3, clear | 1.97 | **wrong:** no gain |
| The defence's list cost, two passes | 3.5; best on half or more, under 1 point | 1.86 | **wrong:** best on 4 of 11, 1.2 points |
| The order of the levels | 0.8; Starter over Rookie by 3 to 8 | 0.94 | below the range, and not clear |
| Boards 1 and 3 taken apart, the diagnosis, the boards, speed, agreement checks | 1.5 | about 1.6 | |
| The outcome exam, self-play, `eval.coverage_budget` | 5.1 | 0 | not run: the reading showed no gain |

## 1. Changes to the printed game

None. The playtest site's computer now settles shots at every level, once this is merged.

## 2. What changed

- **Steps 18a and 18b are merged.** D-146 to D-150 are recorded.
- **`eval.settle_shots` is on by default,** every level, both engines. It applies under the table's rules too; I
  didn't measure it there (D-146).
- **`play_on` is retired** (D-149): off, marked retired in `ai_profiles.json`, not offered by this step's tools.
  The code stays, because the engines' agreement tests switch all five search parts on together.
- **`eval.help_readings`** (off) in `search.py` and `engine.js`: the floor. The reading names the candidate shots;
  the rules value them. Each floor keeps its reason: the square, the shot and its value.
- **Tools:** `tools/step_18c.py` (the measures), `tools/replies_18c.js` (a defence turn's best legal reply against
  the best reply the search looks at).

## 3. What it proves

- **The two engines agree,** on the new default and with `eval.help_readings` on: 600 positions and 4 whole
  searches each, 0 mismatches (`js_equivalence_default.json`, `js_equivalence_help_on.json`).
- **The candidate shots the floor uses are valued by the rules, not the reading.** The reading's own
  move-then-shoot looks match the rules on 555 of 574, and are too high on 18 (by 7.3 on average), so the floor
  doesn't trust them.
- **A move-then-shoot is worth the same whichever movement or facing gets there:** 0 differences on 1,624 squares.
- **Speed, against the budget** (`speed_plain_default_help_1.json`, `_2.json`): 1 pair on 9 decisions in 10, in
  seconds, two runs each, all three engines in the same run.

| Level | Target: desktop, phone | Before (shots not settled) | The new default | With `eval.help_readings` |
|---|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.27, 0.24 | **0.29, 0.29** | 0.25, 0.29 |
| Starter | 1.0, 2.0 | 0.72, 0.69 | 0.79, 0.80 | 0.81, 0.76 |
| All-Star | 2.5, 3.0 | 1.42, 1.21 | 1.55, 1.40 | 1.47, 1.50 |

  - The machine ran about a third slower today than at step 18b (the All-Star without the switch took 1.04 then).
  - **The Rookie on the new default is at its desktop target** (0.29 against 0.30; one earlier run read 0.32). At
    18b's machine speed it was 0.23.
  - At the assumed phone speed every level is over on the new default (1.15, 3.2, 5.6 to 6.2).
  - `eval.help_readings` costs nothing that shows.
- **Tests on the new default** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`): 77 pass, 14
  expected failures, 1 fail.
  - The one unexpected pass of earlier steps (an early cut flagged with a legal reorder) is now an expected failure,
    as its mark says.
  - The fail is the timing test that sits at its limit: 2.44 s against 1.70 s. On today's machine it goes over
    with shots settled and without (the same game, run alone: over on 2 and 1 decisions with, 5 and 4 without). Not
    loosened.

**Three worked examples a trainer could say:**

- Board 1: "It's 32 whatever we do. O1 sprints to the rim and lays it in, and nobody can get next to him in time.
  Wall the straight lane and he goes one square to the side."
- Board 3: "Stay home. If O1 goes up, the low man steps to him and Contests: 22. Step up early and he slides past
  for 29.5."
- A defence position from play, phase 2: "X2 could step next to the ball handler and go for the Steal. By our own
  reading that is 3.8 points better than what we played, and it was never on our list."

## 4. For Shaun to decide

- **The Rookie and the Starter.** With shots settled the Starter leads the Rookie by 2.6 (interval -0.8 to +5.9),
  where it led by 10.0. Options:
  - accept closer levels for now, and widen them when the levels are set (D-98 is still open);
  - widen the Rookie's settings now (its pick noise, its list length): a design choice, so I haven't touched it.
- **Switch `eval.help_readings` on?** I'd leave it off: no gain (+0.4, interval -1.1 to +1.9). Keep the code: the
  fault is real, and 18e's refit of the map should remove it at the source.
- **`eval.coverage_budget`?** Not run. Nothing here gives it a reason.
- **Boards 1 and 3.** Both ask for something the rules make unnecessary. Options: retire them as board 13 was
  (D-134), or rebuild them so the board's move is really better.
- **A rules question behind both boards: should late help work this well?** A defender one Move away Contests any
  shot. If help defence should matter as it does in basketball, the reaction's reach is the lever. That is a rule,
  and yours.
- **18d.** The defence's list is the clearer target: 1.2 points a decision, every loss at "never generated", and
  "step in, then Steal" missing outright. I'd start there, by rule, as planned.

## 5. Noticed, not touched

- **Speed moved by a third between runs on this machine today,** so the speed table gives each engine beside the
  default measured in the same run.
- **The defence's list cost is from 11 positions,** not 12: one phase had only one usable position.
- **Board 11's pass in the air** is still waiting for 18d, as ruled.
- **The table's rules:** nothing measured (D-146).
- **The exam book** is untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high: 18d changes how the list of turns is built in both engines, where a wrong rule costs
speed at once, and its measures need the same care in reading.
