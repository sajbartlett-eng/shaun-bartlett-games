# Step 18d report: Shaun's control rule, tested at three sizes

## In plain words: what changes under each size

- **The offence changes a lot.** Today more than half of all shots come straight off a Quick Step or a Sprint.
  Under the rule the computer drives hard and then controls the finish: it Moves the last step, or shoots off the
  catch. Size 1 halves the rushed shots, size 2 leaves under a fifth, size 3 almost none.
- **The defence barely changes.** Nine Contests in ten still arrive late, in the reaction, from about 3 squares
  away. Two in three already arrive by a Move, which stays a full Contest. The rule moves the rest from a Sprint or
  Quick Step to a Move. It doesn't move help from late to early.
- **Scoring doesn't move** at sizes 1 and 2. Size 3 shows the first signs of a cost.
- **The foul roll matters more than the size.** A rushed Contest on a three risks free throws worth up to 54. On
  your closeout board a rushed Contest is worse than no Contest at size 3, and close to it at size 1.
- **Your closeout line is right under the rule, and the computer only half finds it.** It Moves in and Contests in
  the reaction every time. It never Quick Steps closer first: that move isn't on its list.
- **Game EB3F5B isn't replayed.** A game code is random, so the game can't be rebuilt from it. I need the log file.

## The cases the ruling on "following" doesn't settle

Each is read as the same last-movement test, with no exceptions, and built that way. Marked for you.

| Case | My reading |
|---|---|
| A rushed shooter is fouled | The "open shot" he may take instead of free throws uses his reduced rating. The free throws don't change |
| A defender's movement in the reaction | It counts as his last movement. A Move in the reaction restores control: that is your closeout line |
| A jump into the passing lane | It is a Move, Quick Step or Sprint, so it counts |
| A Sprint | It uses the Move, so a player who Sprints can't restore control that phase |
| A Steal | Its odds and its foul roll don't change. The rule names the shot and the Contest only |
| A rushed Contest with the arrow off the shooter as well | One foul roll, as today. The two don't stack |
| How many foul rolls a rushed Contest takes | Today's count: once from closer to the rim than the shooter, twice from level or further |
| A board set up with a player's Move and Quick Step both used (boards 3 and 8) | Read as set: the Move last |

## The fidelity table

All-Star self-play, Senior Pro, the app's rules, 200 possessions a setting (`fidelity.json`). Intervals in brackets.

| | Today's rules | Size 1 | Size 2 | Size 3 | Basketball |
|---|---|---|---|---|---|
| **Shots taken rushed** (after a Quick Step or Sprint) | **54%** (47 to 61) | **26%** (20 to 33) | **18%** (14 to 25) | **6%** (3 to 10) | |
| Points of a set shot | 29.6 | 30.9 | 30.7 | 30.6 | catch-and-shoot 54.1% |
| Points of a rushed shot | 30.7 | 30.7 | 29.5 | 29.4 | pull-up 45.6% |
| Catch-and-shoot, share of shots | 24% | 23% | 27% | 25% | |
| Catch-and-shoot against off the dribble or a movement, points | 30.8, 30.1 | 31.3, 30.7 | 31.3, 30.2 | 31.0, 30.4 | |
| **Shots contested** | 40% (33 to 47) | 26% (20 to 32) | 34% (28 to 41) | 28% (22 to 35) | |
| **Contests that arrive late, in the reaction** | 92% (84 to 96) | 90% (78 to 96) | 94% (85 to 98) | 96% (87 to 99) | |
| Contests already in place before the shot (early) | 6 of 76 | 5 of 49 | 4 of 65 | 2 of 52 | |
| A late Contest comes from, squares | 3.1 | 2.9 | 2.9 | 2.6 | |
| Contests by a helper, not the shooter's own man | 46% | 55% | 58% | 50% | |
| Contests after a Move | 66% | 69% | 69% | 83% | |
| Contests after a Sprint, after a Quick Step | 20%, 11% | 18%, 6% | 23%, 5% | 12%, 2% | |
| Points allowed: open, contested late | 31.5, 28.3 | 31.5, 28.8 | 31.4, 28.4 | 31.6, 27.8 | wide open 1.16, tight 0.88 a shot |
| Contests that draw a foul | 14% (8 to 24) | 20% (11 to 34) | 17% (10 to 28) | 8% (3 to 18) | |
| **The extra pass after a closeout** | 21% (15 to 29) | 16% (10 to 26) | 30% (21 to 40) | 26% (18 to 36) | |
| Points a possession | 29.5 (28.3 to 30.7) | 30.2 (29.2 to 31.2) | 29.5 (28.4 to 30.7) | 28.8 (27.5 to 30.1) | |
| Shots in phases 1 and 2 | 71% | 71% | 72% | 66% | |
| The clock runs out | 1 in 200 | 0 in 200 | 0 in 200 | 0 in 200 | about 1 in 100 |
| The ball lost, in 100 phases kept | 4.7 (2.6 to 8.4) | 4.1 (2.1 to 7.9) | 4.7 (2.6 to 8.4) | 6.9 (4.3 to 11.0) | |
| Decisions a possession | 19.5 | 18.7 | 19.7 | 20.3 | |

- **Today a rushed shot is worth as much as a set one** (30.7 against 29.6). Basketball's pull-up is worth about a
  sixth less than its catch-and-shoot. At sizes 2 and 3 the rushed shot is worth about 1 point less: the right
  direction, a quarter of basketball's gap.
- **A Contest takes about 3 points off** in every setting (31.5 open, 28.3 contested). Basketball's tight contest
  takes about a quarter off. The computer mostly shoots where the Contest is weak.
- **The calibrated map needs no refit.** Its error is 9.1 today and 7.9, 8.0 and 9.1 under the sizes.

## Shaun's closeout line, and the archetypes

**The board** (`closeout_line.json`): O4 (three 11) has the ball in the corner and can't move again this phase. His
defender X3 (Contest on a three 6) is one square too far to step next to him with a Move.

| What X3 does | Today | Size 1 | Size 2 | Size 3 |
|---|---|---|---|---|
| **The line:** Quick Steps closer, then Moves into the Contest when the three goes up | the three is worth 15 | 15 | 15 | 15 |
| Waits, then Sprints into the Contest | 15 | 30.6 | 32.6 | 33 (better not to Contest) |
| Sprints next to him at once, then Contests rushed | 15 | 30.6 | 32.6 | 33 |

- **Why the jump is so large:** the rushed Contest takes 5 off the three instead of 6, which is 3 points. The foul
  roll adds the rest: 7 in 20 to give this shooter free throws worth 54.
- **Does the computer find the line as the defence?**
  - *The Quick Step closer:* no, at any size. It isn't on its list. Forced in, it reads 1.0 behind the move the
    computer picks (it moves a different defender), and 2.4 behind under today's rules.
  - *The Pause:* level with its choice at every size.
  - *The Move into the Contest in the reaction:* yes, at every size.
- **A bigger miss on the same board.** Once X3 is a Move away, stepping next to the shooter at once reads 18.1. The
  computer's choice reads 25.5. That closeout isn't on its list either.

**Archetypes** (shots and Contests by the card's Quick Step rating; 8 of the 75 cards have a rating of 2):

| | Today | Size 1 | Size 2 | Size 3 |
|---|---|---|---|---|
| Quick Step 2: share of their shots that are rushed | 83% | 43% | 30% | 14% |
| Quick Step 2: points a shot | 30.6 (29.4 to 31.7) | 30.2 | 29.7 | 29.3 (28.1 to 30.5) |
| Quick Step 2: shots taken, of all shots | 48 of 190 | 46 of 192 | 43 of 190 | 37 of 184 |
| Quick Step 1: points a shot | 30.3 | 31.0 | 30.7 | 30.9 |
| Quick Step 0: points a shot | 29.1 | 31.5 | 30.7 | 30.7 |
| Quick Step 2 defenders: points allowed when they Contest | 29.4 (20 Contests) | 28.2 (10) | 28.1 (9) | 28.1 (11) |

- **The quickest shooters are the ones the rule touches.** By size 3 they take fewer shots and each is worth about
  1 point less, though the intervals overlap. The other cards don't lose.
- **On defence no card type is weakened.**

## Boards 1, 3, 6, 8 and 9

The search's choice 1 pair ahead, with no pick noise, and what the board's move reads (`boards.json`).

| Board | Today | Size 1 | Size 2 | Size 3 |
|---|---|---|---|---|
| 1: the drive's open layup is worth | 32 | 30 | 28 | 26 |
| 1: does any early help beat doing nothing? | no | no | no | no: the drive now reads below playing on (27.5) |
| 3: O1's layup if the defence does nothing | 22 | 22 | 22 | 22 |
| 3: the board's early help, against doing nothing | 2.1 worse | 1.9 worse | 1.6 worse | 1.4 worse |
| 6: the open three | chosen, 33 | chosen | chosen | chosen |
| 8: the backdoor cut and pass, against the choice | level | level | 0.4 behind | 1.0 behind |
| 9: the kick-out to the corner, against the choice | 1.2 behind | 1.2 behind | 1.2 behind | 1.2 behind |

- **Board 1:** the drive is a Sprint and then a layup, so it is a rushed shot and loses 2 points a size.
- **Board 3 doesn't change.** The low man hasn't moved this phase, so his late step-in is a Move and a set Contest.
  The rule makes late help worse only for a defender who has already spent his Move.
- **Board 9:** the corner man relocating reads 1.2 better than the computer's choice at every size, and still
  isn't on its list.

## The EB3F5B replay

**Not done.** The code is a random label; the game's log is not in the repository or the uploads. With the exported
log I can replay it to O4's shot from A3 under today's rules and each size in a few minutes.

## Speed

SPEED_PLACEHOLDER

## Compute against the estimate

Estimate: about 8 core-hours. Used: about COMPUTE_TOTAL. Predictions: `docs/runs/step18d/PREDICTIONS.md`.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| Self-play, today's rules and three sizes | 3.0; a fifth to a third of shots rushed today | 3.22 | **wrong** on today's share (54%); right on the fall, the Contests, the points and the map |
| The defence's list cost at size 2 | 0.9; about the same as today's | REGRET_USED | REGRET_VERDICT |
| The boards, the closeout line, the agreement checks, speed | 2.3 | about 0.8 | the two defence boards were read from named turns, not a full pass |
| A refit of the map | 2.5, only if its error rose | 0 | not needed |

## 1. Changes to the printed game

None. `rules.control` is off. `RULES_CURRENT.md` is unchanged, and nothing is changed for the table.

## 2. What changed

- **Step 18c is merged.** D-151 (the rule) and D-152 (the rulings on 18c) are recorded.
- **`rules.control`** (off; `'1'`, `'2'` or `'3'`) in both engines: the rushed state (which of a Quick Step or a
  Sprint was his last movement this phase), the reduced shot, the reduced Contest with the wrong-angle foul roll.
- **The computer's reading knows the rule,** in a simpler form: a player who must move first is taken to be set if
  his Move is unused, and rushed if it is used. The search settles every declared shot by the exact rule.
- **In the app:** `?control=1`, `2` or `3` in the address plays the rule in the app's format. A rushed player
  carries a "RUSHED" marker on the court and in his row, cleared when he Moves or the phase ends
  (`docs/runs/step18d/rushed_marker.png`). The result line names "a rushed three off his Sprint" and "a late
  closeout after X4's Quick Step".
- **Tools:** `tools/step_18d.py` (the measures), `tools/line_18d.js` (a line read step by step), a `trace` job in
  `tools/playout.js` (every action of a possession kept).

## 3. What it proves

- **The two engines agree, switch off and at each size:** 600 positions and 4 whole searches each, and 300 shot
  reactions at each size: 0 mismatches (`js_equivalence_control_*.json`).
- **`RULES_CURRENT.md` is unchanged:** RULES_CHECK_PLACEHOLDER
- **Tests:** TESTS_PLACEHOLDER

**Three worked examples a coach could say:**

- "X3 was a Quick Step and a Move from the corner. He Quick Stepped closer while the ball was there, then Moved
  into the Contest when the three went up. Set, a full Contest: 11 less 6, times 3, is 15."
- "X3 waited and Sprinted across. He arrived off balance: his Contest takes 5 off, not 6, and he fouls 7 times in
  20. That three is worth 30.6. Getting a step closer early would have kept him in control."
- "O1 sprints to the rim and lays it in: a rushed layup, 30, 28 or 26 by the size, where it was 32. If he Moves the
  last step instead, it is a set shot and worth the full rating."

## 4. For Shaun to decide

- **Which size, if any?** I'd pick **size 2**.
  - It does the offensive job: rushed shots fall from 54% to 18%, and a rushed shot is worth about 1 point less.
  - It matches the research best: the pull-up against catch-and-shoot gap is about 2 rating steps on a jump shot.
  - Scoring is unchanged (29.5 against 29.5). Size 3 is the first to show a cost (28.8, and the ball lost 6.9 times
    in 100 phases against 4.7), though neither is clear of noise.
  - Size 3 has one thing for it: it is the size of the existing "further from the rim" penalty.
- **The foul roll on a rushed Contest.** It is the larger part of the penalty, and on a good free-throw shooter's
  three it makes a rushed Contest worse than none. Options: keep it as ruled; or keep the reduction and drop the
  roll. As ruled, the practical rule is "don't Contest rushed", which may be what you want.
- **The cases in the table above:** each reads as I've built it unless you say otherwise.
- **The rule doesn't make early help necessary.** A helper with his Move unused still steps in late at full value
  (board 3). If early help should matter, that needs a further rule, such as a Contest only from a defender who was
  next to the shooter when the shot was declared. That is yours.
- **What the defence's list misses, and what widening is worth.**
  - Under today's rules: 1.2 points a decision (step 18c), every loss an action never generated, "step in, then
    Steal" among them.
  - Under the rule: REGRET_PLACEHOLDER
  - On the closeout board the list misses the Quick Step closer and, worth 7.4 points, the Move next to the shooter.
  - I'd widen it by rule next: for each defender, a Move or Quick Step toward the ball handler and toward his own
    man, and a step in followed by a Steal.
- **Rookie and Starter:** not revisited here, as ruled. The rule was measured at All-Star only.

## 5. Noticed, not touched

- **The reading under the rule is simpler than the rule.** It can't tell a square reached by a Move from one that
  needs a Sprint. The search's settled shots are exact, and the map's error didn't rise.
- **"His own man"** in the table means the defender with the shooter's number.
- **The app's rule switch is an address parameter,** not a menu item. The marker was checked in a test page, not in
  a played game in a browser.
- **The table's rules:** nothing built, measured or printed (D-146).
- **The exam book** is untouched.

## 6. Model for the next step

MODEL_PLACEHOLDER
