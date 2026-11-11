# Step 18b report: settle the shot at the horizon, cap the reading, and test shot timing

## Board 8's 42.3, taken apart

The position: O2 has stepped to the wing and O1, guarded, has declared a three. The look-ahead ends there.

| Part of the reading | Value |
|---|---|
| The phase table's average for phase 1 | 24.89 |
| Plus the continuation share: 85% of the best look left after the defence's best cover, O2's open three (39) | + 33.15 |
| Less the average continuation at that phase | − 15.70 |
| Already earned | 0 |
| **The reading** | **42.34** |

- **It reads a shot that will never be taken.** The possession ends with O1's three. The reading doesn't know a shot
  is declared, so it values the position as open play and counts O2's open three.
- **The calibrated map is skipped there** because the map was fitted on open-play positions only, and the code
  applies it only to those. In open play the same 42.34 goes through the map and comes out 29.79.
- **What the three is worth:** O1's three is 8, X1 is next to him and his Contest on a three is 5. (8 − 5) × 3 = 9.

## The ceiling, derived (D-145)

- **A shot scores points × (rating − contest).** Open, that is points × rating: 3 × the three, 2 × any other shot.
- **The best on any card:** the three, 13, so 39. The best two-point shots are 19, so 38. Shaun's 39 agrees with
  the cards.
- **The rules can pay more than one shot's value:**
  - a foul on a shot pays the free throws if they are higher: 3 × the free-throw rating on a three, up to 54;
  - each steal foul pays +5, and the +5 stays;
  - Coach's Call adds up to +10 to the target's shot.
- **But a foul needs a Contest or a Steal, and the defence chooses those.** Against its best reply the defence
  never has to give free throws or a +5. So:

  **the ceiling = what the possession has already earned + the best open shot any attacker's card can score**
  (plus the Coach's Call bonus on the target's shot where that card is in play).
- For board 8 that is 39. Nothing is set by hand: it comes from the cards and the rules.

## How often the reading broke the ceiling

Every horizon reading of a 1-pair search from the exam's 218 positions (`ceiling_exam_default.json`,
`ceiling_exam_settle.json`), and the stored strong-play positions (`ceiling_stored.json`).

| Readings | Before the map | After the map, switch off | Switch on |
|---|---|---|---|
| The exam, all 91,286 | 14.2% above, by 2.5 on average, 7.1 at most | 0.17% (152) | **0 of 92,779** |
| of which a shot declared (3,071) | 5.0% above, 5.1 at most | 5.0%: the map isn't applied | 0 |
| of which open play (83,081) | 15.5% above | 0 | 0 |
| Stored strong play, open play (21,829) | 11.1% above, 7.2 at most; 23% in phase 5 | 0 | |

- **In open play the map already holds the reading under the ceiling.** The breach that reaches the search is the
  declared shot.
- **The ceiling is the smaller part of the fault.** All 3,071 declared-shot readings were wrong, not just the 152
  above 39: each was read as open play.

## The fix, and the head-to-heads

`eval.settle_shots` (off), three parts in both engines:

1. **A declared shot is settled by the rules.** The engine's own reaction code plays the defence's best reply: a
   Contest, a step next to the shooter and then a Contest, a Steal, or nothing, with the dice at their chances.
2. **The ceiling,** before and after the map.
3. **The list is ordered on the same scale.** The quicker reading that ranks turns goes through the same ceiling
   and map. Without this, board 6's open three (33) ranked 30th of 31 behind turns read at 37 to 42, and was cut.

| Against the calibrated default, All-Star, 1 pair | Gain a pair | Interval | Result |
|---|---|---|---|
| **`eval.settle_shots`** | **+2.4** | +0.8 to +4.0 | stopped at 160 pairs: a gain. 66 wins, 52 losses, 42 ties |
| `play_on` | −0.4 | −2.1 to +1.3 | stopped at 160 pairs: no gain |

- **Why `play_on` doesn't earn its place.** It settles a shot with only the defenders already next to the shooter.
  On 185 declared shots from the exam positions, the defence's best reply was to step in and then Contest on 119.
  `play_on` reads those shots 9.8 points too high on average.
- "Both on" wasn't run: the prompt asks for it only if each alone gains.
- **The outcome exam:** EXAM_PLACEHOLDER

## Boards 6 and 8, move by move

| Board | Before | With the switch on | The board's move |
|---|---|---|---|
| 6, the open catch | moves O2; the shot isn't on the list | **shoots the open three this turn**, after a move by O2 that reads the same | reads 33, the best turn; first on the list |
| 8, the backdoor cut | shuffles O2 on the wing, reading 42.3 | the same move, now reading 28.9 | the cut and pass reads 28.9: **level**, but its first action still isn't generated |

- **Board 6 still fails its judge** only because the judge wants the shot as O4's first action; the pick took a
  turn that reads the same with a move in front.
- **Board 8 is now a candidates fault,** not a judgement one: the cut is as good as anything, and isn't on the list.
- **The 19 boards:** 10 at 1 pair (9 before; board 7 gained) and 10 on the clock. `play_on`: 9 and 9.

## The shot-timing test

All-Star self-play, 1 pair ahead (`shot_timing.json`). "Lost": a steal, an interception or any other turnover, in a
phase the offence didn't shoot in. Intervals in brackets.

| | App, switch off | App, switch on | Table, switch off | Table, switch on |
|---|---|---|---|---|
| Possessions | 640 | 200 | 200 | 200 |
| **The ball is lost, in 100 phases kept** | **7.4** (5.7 to 9.5) | **6.3** (3.7 to 10.5) | **1.1** (0.5 to 2.5) | **0.5** (0.1 to 1.8) |
| In phase 1 | 8.7 (6.4 to 11.8) | 7.5 (4.0 to 13.6) | 0.6 (0.1 to 3.3) | 0.7 (0.1 to 3.8) |
| In phase 2 | 2.2 (0.9 to 5.6) | 3.7 (1.0 to 12.5) | 0.7 (0.1 to 4.1) | 0 (0 to 3.5) |
| In phase 3 | 8.5 (4.2 to 16.6) | 8.3 (2.3 to 25.8) | 0 (0 to 3.6) | 0 (0 to 5.4) |
| Turnovers in 100 possessions | 8.1 | 6.5 | 3.0 | 1.0 |
| Points of a shot taken in phase 1, 2, 3, 4 | 31.5, 31.6, 31.0, 30.4 | 32.1, 31.7, 30.7, 30.5 | 34.4, 33.8, 34.1, 32.8 | 33.8, 33.3, 33.3, 32.4 |
| Shots in phases 1 and 2 | 72% | 73% | 34% | 48% |
| The clock runs out (the table: a forced shot) | 0 in 640 | 0 in 200 (0 to 1.9) | 3.5 in 100 (1.7 to 7.0) | 1.5 in 100 (0.5 to 4.3) |
| Points a possession | 28.8 (28.0 to 29.5) | 29.7 (28.4 to 31.0) | 32.1 (31.3 to 32.9) | 32.2 (31.5 to 32.9) |
| Decisions a possession | 21 | 19 | 41 | 31 |

- **On the app the risk is nearer the research's 10% than its 3%.** About 7 in 100 a phase, and a turnover there
  ends the possession. The research's NBA-like figure is 2.7 in 100 a look.
- **At the table the risk is about 1 in 100,** and the same computer spreads its shots across the clock. So the
  timing follows the risk, as the research's test says it should.
- **Waiting doesn't buy a better shot, in either format.** A shot is worth about 31 on the app whichever of the
  first four phases it comes in. That could be the game, or it could be this computer not finding the kick-out and
  the backdoor cut (the research's caution). The numbers can't separate the two.
- **Nothing is changed on this.** The table uses the table's own map from 18a, still open.

## Compute against the predictions

COMPUTE_PLACEHOLDER

## 1. Changes to the printed game

None. `eval.settle_shots` is off.

## 2. What changed

- **D-144 and D-145 are recorded.** `docs/reference/RESEARCH_fidelity.md` is in.
- **`eval.settle_shots`** (off) in `decide.py`, `search.py` and `engine.js`: the three parts above.
- **No calibrated map at a declared shot.** Once the reaction is played the possession is over and the value is the
  real score.
- **Tools:** `tools/step_18b.py` (the measures) and `tools/ceiling_18b.js` (every horizon reading against the
  ceiling). `tools/js_equivalence.py` compares the ceiling and the settled shot.

## 3. What it proves

- **The settled shot equals the rules.** Against every legal first reaction action on 160 declared shots (80 under
  each format): 0 differences.
- **The two engines agree,** switch on and off: 1,000 positions and 4 whole searches each way, and 400 shot
  reactions with the switch on: 0 mismatches (`js_equivalence_settle_on.json`, `_off.json`, `_reactions.json`).
- **Looks the horizon counts as released now are already read against the Contest** (part 2 of the fix asked). On
  110 positions the "shot now" reading equals the played-out reaction on 106, and is 0.5 to 4.1 higher on 4. Left
  as they are.
- **Speed, against the budget** (`speed_default_settle_play_on.json`): 1 pair on 9 decisions in 10, in seconds.

| Level | Target: desktop, phone | Default | Switch on | Switch on, phone speed |
|---|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.18 | 0.23 | 0.92 |
| Starter | 1.0, 2.0 | 0.55 | 0.64 | 2.54 |
| All-Star | 2.5, 3.0 | 1.04 | 1.14 | 4.57 |

  9% to 27% slower; inside the desktop budget at every level. At the assumed phone speed the Starter and the
  All-Star are over, as they already were. The look-ahead reached is unchanged.
- **Tests:** TESTS_PLACEHOLDER

**Two worked examples a trainer could say:**

- Board 8: "O1's three reads 9, not 42, because X1 is already next to him and Contests: 8 less 5, times 3. The 42
  was O2's open three, a shot that can't happen once O1 has declared his."
- Board 4: "O1's mid-range reads 8, not 22. Nobody is next to him yet, but X5 can step to him with his Move and
  Contest. Counting only the defenders already there, it reads open."

## 4. For Shaun to decide

DECIDE_PLACEHOLDER

## 5. Noticed, not touched

- **Boards 1 and 3 don't move.** With shots settled, helping on the beaten drive still reads 2.1 worse than doing
  nothing. That is the defence's missing readings: 18c.
- **Board 11's last-phase pass is the same kind of fault for a pass in the air.** One team turn ahead the pass
  reads 11.1; searched, it is worth 21.5. It is still cut from the list. Not a declared shot, so not touched.
- **Under the table's rules the settled reading isn't quite exhaustive.** If a Steal in the reaction succeeds, play
  goes on, and a different defender's free step before that Steal isn't searched. No difference showed on 80
  declared shots.
- **The lower levels model their opponent as part passive.** Inside the settled reaction the reply is always the
  defence's best.
- **The exam book** is untouched. The table's own map, the cost of a turnover at the table and plan step 24 are
  untouched.

## 6. Model for the next step

MODEL_PLACEHOLDER
