# Step 18h report: the floor, tested against played-out answers

## First

- **Removing the floor did not pass the gate, so it is off.** On the sense-check set today's computer picks the
  played-out best, or a turn level with it, on 22 of 24 positions. With the floor removed it does so on 20, and
  breaks three positions that passed. I tried it three ways; none beat today.
- **The step is inside the hard limit: about 11.5 core-hours of 12,** and over my estimate of 9.5. The sense-check set
  cost 6.1 where I allowed 3.5. Part of that was a fault in my own tool (below).
- **Speed fits,** judged the new way (D-161): each level is within 2 to 5% of step 18f's code timed in the same
  hour.

## In plain words

**What the computer now sees that it didn't:**

- **"Move, then shoot" in the other side's reply.** Rank-in-hand is on (your ruling). Both positions in the set
  where 18f missed that reply are now right.
- **Each level is judged by its own play.** Every level has its own map. With it the All-Star gets your game
  EB3F5B right again (it closes with the Move), and 18e's Steal position too.

**What it still can't do:**

- **Find your closeout order.** It still Moves closer where your Quick Step closer is about 4 points better by play.
- **Keep a good shot on its list every time.** In one position an open three worth 30 was dropped from the
  offence's list, because 24 other turns read a shade higher before the defence had answered. By play, shooting was
  6.6 points better. That is the offence's hand-written list, which this step didn't open.
- **Board 9's kick-out to the corner.** It plays something else and loses about 5 points.

**Did the Contest rate and the early shooting come back?**

- **Early shooting: mostly.** First-phase shots fall from 6 in 10 to just under 5 in 10 (4 in 10 at 18e). The cause
  was the shared map, as 18f said. A map for each level undoes most of it.
- **The Contest rate: no, and the set says it is not a judgement fault at the shot.** 23 shots in 100 are
  contested, as at 18f. When a Contest was there the computer took it every time, and was right every time. On 26
  of 35 shots from play nobody could reach the shooter at all. And one turn before such a shot, nothing the defence
  tried changed it either. The shot is lost earlier than the computer looks.

**What I got wrong coming in.** I told you the floor was "behind the Move it can't see and the ties that remain".
The set doesn't bear that out:

- The shot the floor hides is not what separates your closeout order from the computer's. By play the gap is in
  what X3's kept Move does later, not in the shot he leaves now.
- Most of the ties left are real at this look-ahead: the offence has a shot nothing can reach this turn, so every
  defence turn truly reads the same.

## Part 0: rulings

- **Step 18f is merged** (pull request 67). D-160 to D-163 are in `DECISIONS.md`.
- **Rank-in-hand is on by default** in both engines. The tie splitter stays on.
- **How speed is judged** is recorded in `docs/SPEED_BUDGET.md`.
- The prompt numbers the sense-check ruling D-159. Step 18f had used that number, so it is recorded as D-162.

## Part 1: the floor shown, before any change

`floor.json`: the reading's parts in the position each candidate turn leaves.

- **With the offence to act, "play on" is what the reading returns on 36 of 42 candidate positions.** The shot that
  can go up now is the larger part on the other 6.
- **With the defence to act there is no shot term at all.** The reading is "play on" alone: the phase table plus the
  single best look the cover leaves.
- **How much does it hide?** Less than I claimed. Of 15 pairs of candidates whose shot now differs by 5 points or
  more, 12 already read differently today. Three read within half a point, and your closeout pair is one:

| The closeout board, after the defence's turn | Shot now | Best look left, second | Today's reading | By play |
|---|---|---|---|---|
| Your order: X3 Quick Steps to E4, X2 moves to B6 | 15 | 15, 13.6 | 27.5 | **20.5** |
| X3 Moves to C4, X2 moves to B6 | 21 | 15, 11.7 | 27.5 | 24.5 |

- **So the reading is level where play is not.** But un-hiding the shot (15 against 21) would not close it: by play
  neither shot is taken. The offence plays on, and what it earns depends on whether X3 still has his Move.

## Part 2: the sense-check set

**What it is.** 24 positions, each with every candidate that matters played out by the rules with common dice:
81 candidates, 3,360 play-outs kept, 32 to 64 a candidate. Stored in `tools/sense_set/` (`positions.json`,
`answers.json`, and the map the answers were measured with).

- **Every play-out is continued by one fixed engine:** the All-Star as it stood at the start of this step. So the
  answers don't move when the default does.
- **Scoring a setting takes under a minute** when its choices already have answers
  (`python3 tools/sense_18h.py score <name> switch=true`). A choice the set has never seen is added and played out
  once, about 0.05 core-hours each.
- **A choice "matches"** if it is the played-out best or its paired interval against the best includes 0. With 32
  play-outs those intervals are wide (4 to 8 points either way), so I read the points lost first and the matches
  second.

**Where the positions come from:**

| Group | Positions | From |
|---|---|---|
| Closeouts | 4 | the closeout board (both versions and its step 2), game EB3F5B |
| Steals | 2 | step 18e's two positions |
| Contest or not | 4 | the first four shot reactions from play where the defence had a real choice |
| Before an open shot | 3 | the defence's last turn before a shot nobody could reach |
| Shoot now or play on | 4 | first-phase turns from play with a shot the ball handler can release at once |
| Move, then shoot | 2 | the two worst misses of 18f's reply list |
| Boards | 5 | boards 1, 2, 3, 8 and 9 |

**Each position: the played-out best, and the computer's choice** (`sense_today.json`, `sense_no_floor.json`,
`sense_maps.json`). "Behind" is points lost against the best, with its interval.

| Position | Best by play (the offence scored) | Today, at the start of the step | The floor removed | The final default (a map for each level) |
|---|---|---|---|---|
| Closeout, the shooter can't move | **your order:** X3 Quick Steps to E4, X2 moves to B6 (20.5) | level: X3 Moves to C4, X2 to B6; 4.0 behind (-0.8 to 8.8) | the same | the same |
| Closeout, the shooter can move | X3 Quick Steps to E3, then Moves to B3 (28.8) | **best** | level, 0.3 behind | **best** |
| Closeout, step 2 | X3 Moves next to him, then tries a Steal (6.8) | **best** | **best** | **best** |
| Game EB3F5B, the pass in the air | X4 Moves to C4 (30.0) | **worse:** X4 Quick Steps to E4, 3.0 behind | **best** | **best** |
| 18e's Steal position, clock 2 | the defence Pauses (27.0) | **best** | **best** | **best** |
| 18e's Steal position, clock 10 | X3 steps in, then tries a Steal (32.0) | level: 3.8 behind (-4.0 to 11.6) | **worse:** 8.0 behind (1.5 to 14.5) | **best** |
| Contest or not 1 | X2 Quick Steps into the Contest (29.6; no Contest 41.0) | **best** | **best** | **best** |
| Contest or not 2 | X3 Moves into the Contest (30.0; none 36.0) | **best** | **best** | **best** |
| Contest or not 3 | X3 Moves into the Contest (24.0; a Sprint 30.0; none 33.0) | **best** | **best** | **best** |
| Contest or not 4 | X2 Quick Steps into the Contest (24.0; none 27.0) | **best** | **best** | **best** |
| Before an open shot 1 | every candidate gives up the same 30.0 | **best** | level | **best** |
| Before an open shot 2 | every candidate gives up the same 30.0 | **best** | level | **best** |
| Before an open shot 3 | the defence Pauses (33.0) | level: X3 tries a Steal, 1.4 behind (-0.7 to 3.6) | level | level |
| Shoot now or play on 1 | **shoot:** O1's three (30.0; passing on 23.4 and 27.8) | **best** | **best** | **worse:** O1 passes to O2, 6.6 behind (1.1 to 12.0) |
| Shoot now or play on 2 | shoot: O5's layup (38.0; moving first 37.9) | **best** | **best** | **best** |
| Shoot now or play on 3 | shoot or move first: both 30.0 | level | **best** | level |
| Shoot now or play on 4 | **play on:** O2 sets a screen (28.3; shooting now 21.0) | **best** | **best** | **best** |
| Move, then shoot 1 | O4 moves to A2, then shoots (28.3; Hesitating 12.8) | **best** | **best** | **best** |
| Move, then shoot 2 | O4 moves to I2, then shoots (46.0; Hesitating 27.6) | **best** | **best** | **best** |
| Board 1 | the computer's own: X2 Quick Steps to D6 (28.9; doing nothing 31.4; 18a's choice 39.0) | **best** | **best** | **best** |
| Board 2 (three 12) | the defence Pauses (14.6; the board's sag 19.4) | level: X3 steps in, X1 tries a Steal; 2.0 behind (-6.5 to 10.4) | the same | the same |
| Board 3 | doing nothing (28.4; the board's help 32.1 and 37.9) | level: 2.0 behind (-1.1 to 5.0) | **worse:** 4.2 behind (1.3 to 7.2) | level: 2.0 behind |
| Board 8 | the computer's own: O2 cuts to E10, O1 passes (39.0; the board's cut to D7 33.0) | **best** | **worse:** 7.9 behind (5.3 to 10.5) | **best** |
| Board 9 | the board's kick-out to the corner (29.8) | **worse:** 4.7 behind (0.6 to 8.7) | **worse:** 7.9 behind (1.9 to 13.9) | **worse:** 4.7 behind |

**The scores:**

| Setting | Matches | Points lost a position | Gate |
|---|---|---|---|
| Today, at the start of the step | **22 of 24** | **0.87** (0.30 to 1.44) | |
| The floor removed (`eval.no_floor`) | 20 of 24 | 1.5 (0.9 to 2.0) | **fails:** breaks 18e's Steal position and boards 3 and 8 |
| The floor removed, with the control-aware cover | 18 of 24 | 2.4 (1.7 to 3.1) | fails |
| The control-aware cover alone (`eval.kept_actions`) | 20 of 24 | 1.8 (1.2 to 2.5) | fails: on the closeout's step 2 it Pauses, 20.7 behind |
| The shot kept exact (`eval.exact_shot`) | 21 of 24 | 1.2 (0.7 to 1.8) | fails |
| **The final default** (a map for each level) | **22 of 24** | **0.86** (0.34 to 1.38) | level with today: gains two, breaks one |

**What the set says that I didn't expect:**

- **Today's computer is better than its boards suggest.** It is the played-out best, or level, on 22 of 24.
- **Three boards' own answers lose to play.**
  - Board 3: the board's early help gives up 3.8 to 9.4 points more than doing nothing.
  - Board 1: 18a's choice gives up 7.6 more than doing nothing; the computer's Quick Step to D6 is best of all.
  - Board 8: the computer's cut to E10 and pass scores 39; the board's cut to D7 scores 33.
- **A Contest is always worth it here.** Even rushed, it saved 3 to 11 points each time it was on offer.
- **Shooting early is usually right.** A shot worth 30 or more now was the best or level on 3 of 4 positions.

## Part 3: removing the floor: built three ways, none on

Each is behind its own switch, in both engines, off.

- **`eval.no_floor`:** the reading keeps its parts instead of taking the largest. What is left to earn is a line
  fitted to what positions went on to earn: the best shot now, the best look the cover leaves, and the second best,
  none allowed a weight below 0. Fitted on 680 stored possessions.
  - **What the fit itself said:** in the All-Star's own play the shot now carries no weight at all in phase 1. When
    its shot is poor it plays on and earns about 28 anyway.
- **`eval.exact_shot`:** a shot that can go up now keeps its exact value from the rules, and only "play on" goes
  through a map. Today the largest is taken first and then mapped, so an exact shot is bent by a map.
- **`eval.kept_actions`** (18f's) with each of them.
- **The gate:** the table above. None improves on today; each breaks positions that passed.
- **The backstop head to head for the floor was not run.** Nothing passed the gate, so there was nothing to back.

## Part 4: one map for each level (D-163): on

`eval.level_maps`, on. Each level's reading goes through a map fitted on its own play (`maps_write.json`).

| Level | Fitted on | Lines of its own | Held-out error: its own map, the shared one | Marked |
|---|---|---|---|---|
| All-Star | 840 stored possessions (12,782 positions) | phases 1 to 4 | **10.9**, 11.3 | phases 5 and 6 use the shared map: it rarely plays that long |
| Starter | 120 new possessions on today's default (2,459) | phases 1 to 5 | 12.5, 12.6 | **thin:** no clear gain yet |
| Rookie | 160 new possessions on today's default (3,674) | phases 1 to 4 | 11.1, 11.0 | **thin:** no better than the shared map yet |

- **The All-Star's map is fitted on stored play,** from 18f's runs: 200 possessions with today's switches and 640
  from just before them. I had no budget for a fresh 840. A line needs 60 positions or more.
- **On today's default the Starter scores 25.5 points a possession against itself (23.2 to 27.7) and the Rookie
  25.5 (23.5 to 27.5).** The Rookie was at 21.3 at 18f.
- **The lower levels' maps are thin.** 120 and 160 possessions are what the limit left. They do no harm on the
  held-out error and no clear good. More play would settle them: about 0.6 core-hours for 200 possessions each.
- **On the set the maps are level with today** (22 of 24 both; 0.9 points lost both). They gain EB3F5B and 18e's
  Steal position and break "shoot now or play on 1".
- **Why that one breaks.** The All-Star's own play scores more than the shared map assumed, so its "play on"
  readings rise. Then 24 turns read 30.1 to 30.7 before the defence answers, the open three reads its exact 30.0,
  and the list of 24 has no room for it. After the defence answers, the best listed turn is worth 28.0.

**The backstop head to head for the maps** (`h2h_maps.json`, All-Star, 80 pairs; the other side has the shared map):

| | Result |
|---|---|
| Points a pair | -0.4 (-3.2 to 2.4): level |
| Pairs won, lost, tied | 26, 26, 28 |
| Shots in phases 1 and 2, on offence | 57 in 100 with its own map; 99 in 100 with the shared map |
| The ball lost, per 100 phases kept | 7.4 (3.8 to 13.9); 23.5 (12.4 to 40.0) |

- 80 pairs was what the limit left. It can only rule out a large loss, and it does.

## Part 5: the recheck, beside 18e and 18f

All-Star self-play, 200 possessions on the final default (`fidelity.json`).

| | 18e | 18f | **18h** |
|---|---|---|---|
| Points a possession | 26.8 (25.1 to 28.4) | 27.8 (26.1 to 29.6) | **28.4 (26.6 to 30.2)** |
| Shots contested | 40% (33 to 48) | 23% (17 to 30) | **23% (17 to 30)** |
| Contests after a Move | 62% | 62% | 64% (48 to 77) |
| Contests after a Quick Step, after a Sprint | 22%, 14% | 23%, 8% | 28%, 8% |
| Shots by phase, 1 to 6 | 40, 36, 19, 4, 2, 1% | 60, 29, 9, 2, 1, 0% | **48, 26, 11, 9, 5, 2%** |
| Shots in phases 1 and 2 | 76% | 89% | 74% |
| The clock runs out | 0 of 200 | 0 of 200 | 0 of 200 |
| The ball lost, in 100 phases kept | 14.2 (10.1 to 19.7) | 21.5 (15.4 to 29.1) | **12.9 (9.2 to 17.8)** |
| Possessions that end with the ball lost | 29 of 200 | 29 of 200 | 30 of 200 |
| Shots taken rushed | 13% (9 to 19) | 11% (7 to 17) | 13.5% (9 to 20) |
| Contests that draw a foul | 16% | 33% | 15% (7 to 30) |

**The two measures still off 18e's, and what the set says:**

- **Shots contested, 23% against 40%. The set supports the computer where it can see.**
  - At the shot: it took the Contest on all four positions, and each was right by 3 to 11 points.
  - One turn before an open shot: on all three positions no candidate did better than its choice.
  - On 26 of 35 shots from play nobody was in reach, whatever the defence chose.
  - So the shots are lost two turns or more before they go up. The computer looks one pair ahead. I can't yet say
    whether the offence has simply got better at stepping away (it scores 28.4 now, 26.8 at 18e) or the defence
    stands wrong early. The set has no position that far back; adding some is cheap (section 4).
- **First-phase shots, 48% against 40%. Mixed.**
  - Shooting a good shot early is right by play on 3 positions of 4.
  - The fall from 60% is partly a fault: with its own map the All-Star sometimes drops a good shot from its list
    (above). So some of the "patience" it regained is the wrong kind.

## Part 6: speed

The time to finish 1 pair on 9 decisions in 10, in seconds. Two rounds, each timing 18f's code and then this step's
(`speed.json`).

| Level | Target | 18f's code today | This step today | This step against 18f | Scaled to 18f's report |
|---|---|---|---|---|---|
| Rookie | 0.3 | 0.31, 0.28 | 0.30, 0.30 | 2% slower | **about 0.23** |
| Starter | 1.0 | 1.08, 0.93 | 1.08, 1.03 | 5% slower | **about 0.79** |
| All-Star | 2.5 | 2.24, 2.12 | 2.16, 2.27 | 2% slower | **about 1.7** |

- **Every level fits** by D-161. The differences are inside the round-to-round swing.
- Nothing in this step adds work to a decision: rank-in-hand reads no more positions, and a map costs nothing.

## Compute against the estimate and the hard limit

Estimate 9.5. Hard limit 12. **Used: about 11.5.**

| Run | Estimated | Used | |
|---|---|---|---|
| The floor shown, harvest, searches | 0.2 | 0.6 | |
| The sense-check set's play-outs | 3.5 | **6.1** | play-outs from early in a possession take 8 to 10 seconds, not the 3 I took from 18f's closeout check |
| Each setting's own choices played out | 0.5 | 1.0 | five settings, not two |
| The fit | 0.1 | 0 | from stored play |
| The backstop head to head for the floor, 200 pairs | 2.2 | 0 | not run: nothing passed the gate |
| The backstop for the maps, 80 pairs | 0 | 0.9 | not in the estimate |
| Self-play: the All-Star 200, the Starter 120, the Rookie 160 | 2.2 | 1.8 | the lower levels cut to fit the limit |
| Speed, agreement checks, tests | 0.9 | 1.1 | the tests ran twice: before and after a fix (section 3) |

- **A fault of mine cost about 2 core-hours.** The helper that spreads work over four cores returns results core
  by core, and I paired them with positions in the order sent. So the first run of the set filed answers under the
  wrong positions, and the candidates I had attached to the positions from play belonged to other positions. I
  undid the shuffle for the fixed positions (it is a fixed permutation), rebuilt the rest, and filled gaps at 32
  play-outs. Every row now carries its own name and is matched by it. The same trap is in `learn_17.run_jobs` for
  anyone who zips its rows; I left that function alone and noted it.
- **What the rest would cost:** 200 fresh possessions for each lower level's map, 0.6; the set's thin candidates
  brought up to 64 play-outs, about 1.5; ten positions two turns before an open shot, about 1.5.

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 18f is merged.** D-160 to D-163 are recorded. `docs/SPEED_BUDGET.md` says how speed is judged.
- **On by default:** `search.rank_in_hand` (your ruling), and `eval.level_maps` with a map for each level in
  `learned_weights.json` (`calibration_levels`).
- **Built and off, both engines:** `eval.no_floor` (its lines in `calibration_parts`), `eval.exact_shot` (its maps in
  `calibration_play_on`).
- **Each level's profile names its level** (`"level": "rookie"`), so a search knows whose map to use.
- **The sense-check set:** `tools/sense_18h.py` and `tools/sense_set/`. `tools/step_18h.py` holds the fits, the
  self-play, the head to head and the speed run. `tools/floor_18h.js` shows the floor.
- **Small changes to shared tools:** the play-out tool keeps shot-reaction positions and the named readings; the new
  switches are in the line, diagnosis, exam and agreement tools.

## 3. What it proves

- **The two engines agree,** 0 mismatches in every run:
  - the final default: 300 positions and 4 whole searches; 150 shot reactions;
  - `eval.no_floor` on: 150 positions and 2 whole searches (and 120 with 3 earlier);
  - `eval.exact_shot` on: 150 positions and 2 whole searches.
- **The gate works as a gate.** It separated five settings in an afternoon where 18f's head to heads could not
  separate four in a day, and it said no to a change I expected to pass.
- **Nothing names a kind of move.** The new readings are fits to play; the set's candidates are tests only.
- **Tests on the final code** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`,
  `test_course_boards` and the golden tests): 88 pass, 13 expected failures, 1 fail.
  - The fail is the timing test that sits over its limit: 2.28 s against 1.70 s (3.24 s at 18f, 2.16 s at 18e). Not
    loosened.
  - **The first run had a second fail, and it was a fault of this step.** The test that checks the two engines agree
    on random positions failed: a level's map stayed in force after its search ended, so a reading made later took
    that map in one engine and the shared map in the other. Fixed: a level's map is now in force only for the
    length of its own search, in both engines. The computer's choices on the set are unchanged, the agreement runs
    were repeated (0 mismatches), and the whole named set was run again.

**Three things a coach could say, from the measured positions:**

- "He's just caught it in the corner and you're four squares off. Close with the Move, not the Quick Step: after the
  Quick Step he steps away and it's an open three, 33 against 30."
- "If you can reach him when he shoots, Contest, even rushed. Every time it was there it took 3 to 11 points off."
- "An open three now beats a pass that might find a better one. Here shooting was worth 30 and passing on 23 to 28."

## 4. For Shaun to decide

- **Three boards disagree with play.** Board 3's early help, board 1's old answer and board 8's cut to D7 all lose
  to what the computer does. The played-out answer decides (your rule), so I'd change those boards' expected
  answers. They are your boards.
- **The closeout order.** It is the one position where your line still beats the computer's, by about 4 points,
  and nothing I built finds it. The gap is in what a kept Move does one turn later. Two ways on:
  - step 18g's zone of influence, which reads exactly that, with this position as its test (my view);
  - or a second pair of look-ahead on defence turns that end level, which costs speed.
- **The offence's list.** It can drop an exact 30-point shot for turns that only read higher before the defence
  answers. With each level's own map that now happens. It is the hand-written list this step left alone. Do you
  want it opened next, with the set as its gate? My view: yes, straight after 18g.
- **The maps stay on?** They are your ruling and they are on. The evidence is level, not a gain: the set the same,
  the head to head level, the shot timing most of the way back to 18e's. Say if level isn't enough.
- **Grow the set?** It has 24 positions, and its intervals are wide at 32 play-outs. I'd add about ten positions
  two turns before an open shot, to answer the Contest question, and bring every candidate to 64. About 3
  core-hours, once.

## 5. Noticed, not touched

- **`eval.kept_actions` has a fault of its own:** on the closeout's step 2 it Pauses where stepping in and Stealing
  is 20.7 points better. It is off; worth knowing before anyone turns it on.
- **18e's Steal position at clock 2:** by play the Pause is best, and 18e's own choice is 6.8 behind it. The
  computer now Pauses.
- **Game EB3F5B is right by a thread.** All 24 defence turns read 33 there; the Move closer comes first only by the
  tie splitter's order.
- **The timing test** still sits over its limit (below). Not loosened.
- **`learn_17.run_jobs` returns rows core by core.** Safe for every tool before this step, which read each row on
  its own. A trap for the next one.
- **The exam book and the trainer** are untouched.

## 6. Model for the next step

Claude Fable 5.2, effort high.

**Step 18g can go next.** The floor was not what stopped the computer valuing a defender's movement left; the gate
says nothing I could fit to the reading's present parts does. The zone of influence is a new part that reads
exactly that, so it is the right next thing. Gate it on the sense-check set, with the closeout board as its test,
and hold it to the same hard limit: the set now makes that cheap.
