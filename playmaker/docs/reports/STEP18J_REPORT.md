# Step 18j report: the soft and hard contest, the penalty's bite, and seeing the Steal coming

## First

- **Speed fits.** @@SPEED@@
- **Compute: @@USED@@ core-hours,** against my estimate of 10.5 and the hard limit of 12.
- **The two rule changes are built in both engines and the app, and on by default in the app.** Each has its own
  switch. Nothing for the table changed.
- **The fix for "step in, then Steal" is built in three parts. One passed the gate and is on. Two are off.** The
  part that makes the offence see the Steal coming works on the position you named, but it broke one board on the
  gate, so by your rule it stays off until you say otherwise. See "For Shaun to decide".
- **Your closeout order is still not found.** I can now say exactly where it is lost. See Part 3.
- **The zone was not retested.** It needed about 4 core-hours that the step did not have, as I said before the first
  run, and part 3 did not pass in full.

## In plain words

**The soft and hard contest.** More shots meet a defender now, and all of the rise is the hand up. About 3 shots in
10 are contested where it was about 1 in 4. Of those, a little over half are soft. The jump to the ball has become
rarer and more careful: the computer now only jumps from in front. It has stopped jumping from the side or from
behind altogether, because those roll for a foul twice and a fouled shot is costly. No shot was fouled in 160
possessions. Threes are contested about as often as before, about 1 in 4 or 5, nowhere near half. Scoring did not
clearly fall. The offence simply shoots from where no defender ends next to it, and a hand up takes only a point or
three off when one does.

**The penalty change.** An ordinary steal foul now costs the defence no points, so the computer Steals in the
position where it used to hold back, and play says it is right to. Over a whole possession it tries fewer Steals,
not more, and fouls less. One traced position shows why: the offence now passes the ball away from a defender who
stands next to it, where it used to hold the ball and lose it. At 4 team fouls with 10 possessions left the computer
still Steals. It does not hold back. In that position the Steal wins by about 8 points even at the penalty's price,
so by play it is right. The penalty does cost more than it did, about twice as much, but not enough to change that
choice.

**Does the computer see the Steal coming?**

- **The offence:** with the part that is off turned on, yes, on the position you named. It reads the held ball at
  19, play gives 20, and it passes. Without it, it still reads the held ball at 27.5 and holds.
- **The offence's list** no longer drops an open three. That part is on.
- **The defence:** with the same part on, it steps in and Steals on board 1, which is 8 points better than what it
  did before. It also does so on board 3, where it is 5.5 points worse than its old choice. That is the board that
  broke.

**Is your closeout order found?** No. The defence's list keeps one turn for each different quick reading, and the
quick reading can't tell your order from other pairs of movements, so your order is dropped before the search ever
compares it. Shown your order, the search does read it as the best turn on the board (with the off part on): 21.0,
against 24.8 for the Move closer and 30 for doing nothing. Play gives 21.5, 24.4 and 30.0. So the judgement is
right and the list is what loses it.

**How the zone plays now.** Not measured in this step.

## Part 0: rulings, and the two rule changes

- **Step 18i is merged** (pull request 70). The rulings are D-177 to D-180 in `DECISIONS.md`.
- **The soft and hard contest (D-177)** is `rules.soft_contest`: on in the app, off at the table, `?softcontest=0`
  turns it off.
- **The steal foul (D-179)** is `rules.fiba_steal_foul`: on in the app, off at the table, `?stealfoul=0` turns it
  off.
- **A scenario card that sets a foul situation (D-180)** now plays under the app's rules.
- **The log and the shot's explanation name the contest:** "X3's soft contest, a hand up from the side: 3 off",
  "X3's hard contest from in front: 5 off". A steal foul outside the penalty reads "Foul on the steal: a team foul.
  X2 is locked. Play on."

**How I read three points of the rule; each is flagged for you:**

1. **In front, side, behind.** In front is nearer the rim than the shooter. Behind is further from the rim. The
   side is level with him. This is the measure the "from behind, 3 less" rule already used.
2. **A hard contest from the side or behind rolls twice even with the arrow on him.** Your rule 4 gives the arrow a
   say only from in front, so I built it that way.
3. **In the penalty the +5 stays with the two free throws.** You wrote "two free throws, as now", and now is +5 and
   two free throws (D-89).

**The two numbers that price a foul over the quarter, remeasured** from 160 possessions under the new rules: the
defence fouls 0.25 times a possession (0.17 to 0.33; it was 0.35), and a possession is worth 26.9 (25.1 to 28.7; it
was 27.5).

## Part 3b: what the two rule changes did on their own

160 possessions of All-Star self-play under each rule set, the same starts and dice. "Rules only" is before any
change to the computer's judgement. "Final" is this step's default.

| | Step 18i | Rules only | Final |
|---|---|---|---|
| Points a possession (out of 20 a point) | 27.5 (25.5 to 29.4) | 26.9 (25.1 to 28.7) | 27.4 (25.7 to 29.1) |
| Shots contested, in 100 | 24 (17 to 32) | 30 (23 to 38) | 29 (22 to 37) |
| ... by a soft contest | 0 | 18 (13 to 26) | 17 (12 to 24) |
| ... by a hard contest | 24 (17 to 32) | 12 (7 to 18) | 12 (8 to 19) |
| Threes contested, in 100 | 20 (14 to 29) | 21 (14 to 30) | 26 (18 to 35) |
| Hard contests from in front, the side, behind | 19, 3, 10 | 16, 0, 0 | 17, 0, 0 |
| Shots fouled, in 160 possessions | 0 | 0 | 0 |
| Steals tried a possession | 0.83 (0.69 to 0.98) | 0.60 (0.49 to 0.71) | 0.66 (0.52 to 0.79) |
| Steal fouls a possession | 0.35 (0.26 to 0.44) | 0.25 (0.17 to 0.33) | 0.26 (0.18 to 0.34) |
| Ball lost, in 100 phases kept | 16 (11 to 23) | 17 (12 to 24) | 15 (10 to 22) |
| Shots rushed, in 100 | 13 (9 to 20) | 15 (10 to 22) | 15 (10 to 22) |
| Shots in phase 1, 2, 3, 4, 5, 6, in 100 | 47, 30, 15, 7, 0, 1 | 49, 33, 15, 3, 1, 0 | 46, 38, 9, 6, 1, 0 |
| Violations (three seconds, closely guarded) | 1, 0 | 0, 0 | 0, 0 |

- **You expected contests to rise toward half of threes and possessions to score less.** Contests rose by about 6
  shots in 100, all soft. Threes contested did not clearly move. Scoring did not clearly fall: every range in the
  points row overlaps.
- **Hard contests from the side or behind are gone:** 13 of 32 before, none of 16 and none of 17 after.
- **No shot was fouled,** before or after.

**The set replayed: which answers moved, and why.** 19 positions near a shot, every candidate played out 32 times
under the new rules. Scores are what the offence went on to score, so the defence wants them low.

| Position | What moved | Why |
|---|---|---|
| Closeout, the shooter cannot move | Your order 25.3 to 21.5. The Move closer 25.8 to 24.4. Doing nothing 33.0 to 30.0. Your order now leads by 3 where the two were level. | The defender beside the shooter now takes a point off with a hand up, and the kept Move's Steal costs no points when it fouls. |
| Closeout, the shooter can move | The Move closer 28.6 to 30.5. Doing nothing is now level with it, 30.0. | The same hand up: the defence gets a soft contest for standing there. |
| Closeout, step 2 | "Moves next to him and stops" 10.0 to 25.8. "Moves next to him, then Steals" 11.4 to 8.5. | When the defender stops, the offence now passes away at once and shoots a three. Before, it held the ball and lost it 8 times in 16. Stealing now is clearly the best turn. |
| The Steal position, clock 2 | Doing nothing 27.0 to 36.0. Step in, then Steal is now best, 28.1. | The offence moves to a spot the defender can only reach from the side, and the defence no longer jumps from the side. The shot goes up open. |
| Shoot now or play on 1 | Playing on fell from 31.2 to 9.8, and from 29.0 to 5.4. Shooting the open three, 30, is now far the best. | When the pass is caught the defence steps in and Steals, since the foul costs it no points. The ball is lost 7 times in 16. |
| Board 3 | The board's help 27.6 to 34.9. The computer's own choice, 26.3, is best. | Not traced. |
| Board 8 | The backdoor cut and the pass 33.0 to 32.0. Level with the cut alone. | A small move, inside chance. |

- **The computer's choices on the 19 under the new rules, before any change to its judgement:** best or level on
  14 of 19, 1.9 points lost a position. Under 18i's rules it was 19 of 19. The new rules made the judgement's gaps
  cost more. The misses: the closeout with the shooter unable to move (8.5 behind your order), board 1 (7.8), board
  8 (6.3), shoot now or play on 1 (5.4), and game EB3F5B (3.0).

**The three foul situations.** The same Steal position at clock 10, each candidate played out 32 times under each
situation, with the foul's later cost counted in the score.

| The situation | The computer's choice | By play: step in, then Steal | By play: no Steal | Right by play? |
|---|---|---|---|---|
| 0 team fouls, 10 possessions left | **Steps in and Steals** (18i: held back) | 28.2 (21.7 to 34.6) | 34.8 (31.6 to 37.9) | Yes |
| 4 team fouls, 10 left | **Steps in and Steals** | 26.7 (20.3 to 33.0) | 34.4 (32.8 to 36.0) | Yes |
| 4 team fouls, 1 left | the same | 26.7 | 34.4 | Yes |

- **Does it now hold back with 4 fouls and many possessions left? No.** By play it is right not to, in this
  position: the Steal is about 8 points better even with the penalty's price in the score.
- **What the penalty costs now.** For these cards, a penalty foul costs the defence 9.3 more than an ordinary steal
  foul. It was 4.3. A foul at 3 team fouls with 10 possessions left costs 8.6 later in the quarter. It was 4.0.
- **Why the bite is still small.** Your reason was that two penalty free throws are worth about 1.6 half-court
  possessions in basketball. In Playmaker a possession scores about 27 and two free throws with the +5 score about
  36: 1.3 possessions. Possessions here score more than in basketball, so free throws weigh less beside them.
- **The last two rows are identical** because at 4 fouls the next foul is the penalty foul whether it comes now or
  later, so a foul now changes nothing later.

## Part 1: the fault, shown

No code changed for this part. Under the new rules, on the closeout board after your order:

- **The offence reads "hold the ball and move another player" at 27.5.**
- **The defence, given that same position to act in, finds "X3 moves to B4 and tries a Steal" at 19.6.**
- **By play the held ball scores 19.9:** 11 shots and 5 turnovers in 16.

So the two halves of the same search disagree by 8 points about one position. The cause is the list of replies.
When the offence weighs a turn, the search gives the defence a reply. That reply list follows a second action after
only the 12 best first actions by a quick reading, and it keeps one first action for each different reading. A
Move that only sets up a Steal reads no better than standing still, so it is dropped as a copy, and the Steal
behind it is never looked at. When the defence is the one to choose, its own list is wider (32) and the Steal is
found.

The same gap shows on "shoot now or play on 1". The computer played on because passing read at 28.3. Play gives
that turn 24.6, and the two reference "play on" turns under 10, because the catch is met by a Steal. The open
three, an exact 30, had been cut from the offence's list before the defence's answer was read.

## Part 2: what was built

Three switches, all in both engines. None names a kind of move.

| Switch | What it does | Default |
|---|---|---|
| `search.keep_settled` | A turn the rules settle outright (a declared shot, or the possession ending) is never cut from a list for turns that only read higher before the other side has answered. | **On** |
| `search.dice_in_hand` | In the defence's list, a first action that leaves its mover able to send something to the dice (a Steal, a Challenge, an Intercept) is ranked by the better of stopping there and that roll, by the rules' chances, and is not dropped as a copy. If he can roll nothing from there, the action is read like any other. | Off |
| `eval.ball_loss` | Where the search stops with the defence to act, the position is worth no more than what its best Steal leaves, counting a defender who can still get next to the ball handler. Settings: either side's search, or only the offence's. | Off |

- **I did not open the offence's list** the way 18e opened the defence's. The two cheaper parts reached the named
  positions first, and an open offence list is the costliest of the three options in speed.

## Part 3: the gate

The 19 positions near a shot, under the new rules. Each setting's choices are scored against the same played-out
answers. A choice is a pass when it is the best candidate or level with it inside chance.

| | Rules only | `keep_settled` (on) | ... and `dice_in_hand` | ... and `ball_loss` |
|---|---|---|---|---|
| Best or level, of 19 | @@G_NONE@@ | @@G_KS@@ | @@G_KSD@@ | @@G_ALL@@ |
| Points lost a position | @@P_NONE@@ | @@P_KS@@ | @@P_KSD@@ | @@P_ALL@@ |

**The four tests you named:**

| Test | Rules only | `keep_settled` (on) | ... and `dice_in_hand` |
|---|---|---|---|
| Closeout, the shooter cannot move: does the defence keep the Move? | No. It does nothing: 30.0 by play, 8.5 behind your order (3.8 to 13.3). | No. The same 8.5 behind. | No. The same. |
| Closeout, the shooter can move: does the Move closer stay best? | By play yes, level with doing nothing (30.5 and 30.0). The computer does nothing. | The same. | The same. |
| "Hold the ball" after your order: does the offence pass? | No. It reads the held ball at 27.5. Play gives 19.9. | No. | **Yes.** It reads the held ball at 19.1 and the pass at 21.0, and passes. |
| Shoot now or play on 1: does the open three stay on the list? | No. It plays on, 5.4 behind (1.6 to 9.1). | **Yes.** It shoots, 30. | Yes. |

**Did any passing position break?**

- **`keep_settled`: none.** One position fixed, none worse. It is on.
- **`dice_in_hand`: one fixed, one broken.**
  - Board 1: the defence now steps in and Steals. 25.2 by play against 33.0 for what it did before: 7.8 better.
  - Board 3: the defence now steps in and Steals. 31.1 by play against 25.6 for its old choice: 5.5 worse (1.5 to
    9.6), on 64 play-outs. The search reads that Steal at 27.6. It is too hopeful about what follows a Steal that
    fails.
  - The gate says "break none". It is off.
- **`eval.ball_loss`: no gain, one loss.** For the offence it adds nothing once `dice_in_hand` is on: the held ball
  already reads 19.1. In the defence's own search it counts the same Steal after every one of its turns, whether it
  steps in now or waits, so the defence puts the Steal off. On the Steal position at clock 10 it did nothing, 5.9
  behind (0.4 better to 12.1 worse). With all three parts on, before I tightened `dice_in_hand`, the gate read 16 of
  19 at 2.3 points lost a position, worse than no fix. It is off.

**Why your closeout order is not found.** On the closeout board the defence has 1,430 candidate turns after its
first cut and keeps 84, one for each different quick reading. Your order is X3's Quick Step to E4 with X2's Move to
B6.

- X3's Quick Step to E4 has the same quick reading as his Quick Step to E5, so only one of them is kept.
- Every pair that sends X2 to B6 has the same quick reading as another pair already kept, so each is dropped as a
  copy.
- The quick reading can't see what makes your order good: the Move X3 still has, and X2's hand up where the pass
  will be caught.

Shown your order, the search reads it right. So the next fix is in the list, not in the judgement: stop treating
two turns as copies when they leave different movement in hand, and rank the kept ones by the search's own reading
of the reply. That costs time, and the time has to be found.

**The backstop head to head,** All-Star, paired possessions under the new rules:

| | Pairs | Points a pair for the first named | |
|---|---|---|---|
| The final default against the rules-only default | @@H2H_FINAL@@ |
| `dice_in_hand` on against the final default | @@H2H_DICE@@ |

@@H2H_WORDS@@

## Part 4: the zone

Not retested. Two reasons. It needs about 4 core-hours (21 positions replayed and 2 runs of 120 possessions), which
did not fit beside the rest; I said so in `docs/runs/step18j/PREDICTIONS.md` before the first run. And the prompt
makes it conditional on part 3 passing, which it did only in part.

## Part 5: the recheck

The final default beside 18i is the "Final" column of the table in Part 3b.

- **Points a possession:** 27.4 against 27.5. No change.
- **Ball lost in 100 phases kept:** 15 against 16. No change.
- **Shots by phase:** more in phase 2 (38 against 30), fewer in phase 3 (9 against 15). The first two phases
  together hold 84 shots in 100 against 78.
- **Shots contested:** 29 in 100 against 24, the rise all soft.
- **Shots rushed:** 15 in 100 against 13. The ranges overlap.
- **Nothing moved the wrong way clear of chance.**

@@DICE_SELF@@

## Speed

@@SPEED_TABLE@@

## Compute

Estimate 10.5. Hard limit 12. **Used: @@USED@@.**

@@COMPUTE_TABLE@@

- **What the rest would cost:** the zone retest, about 4. The other 15 positions of the set under the new rules,
  about 2.5.

**How the predictions came out** (`docs/runs/step18j/PREDICTIONS.md`):

1. Shots contested above 45 in 100, points down by 1 to 3: **wrong.** 30 in 100, and points did not clearly move.
2. Fouled shots return: **wrong.** None. The computer stopped jumping from the side instead.
3. Steals tried rise, and the computer holds back at 4 fouls: **wrong on both.** Steals fell, and it Steals at 4
   fouls.
4. The reply list is too narrow to hold a Move followed by a Steal: **right.** The speed cost I expected did not
   come.
5. One chance in 3 that your order is found: **it was not.**

## 1. Changes to the printed game

None. Both rule changes are for the app only. `RULES_CURRENT.md` lists them under "Split by format": the table
keeps one kind of Contest and its +5 on every steal foul.

## 2. What changed

- **`rules.soft_contest` and `rules.fiba_steal_foul`:** on in the app's format, off at the table, in
  `playmaker_engine` and `playmaker_web/static/engine.js`. `?softcontest=0` and `?stealfoul=0` turn each off.
- **The app:** the log and the shot's explanation say which contest applied and from where; a reminder of each
  rule; the steal foul's new line.
- **A scenario card with a foul situation** (cards 12 and 13) plays under the app's rules.
- **`ai_profiles.json`:** `search.keep_settled` on; `search.dice_in_hand` and `eval.ball_loss` off; the two foul
  numbers remeasured (0.25 and 26.9).
- **`DECISIONS.md`** D-177 to D-180; the rules register and `RULES_CURRENT.md`.
- **Tools:** `tools/step_18j.py`; `tools/sense_18h.py` replays under the new rules (`answers_18j.json`);
  `tools/js_equivalence.py --soft --dice-in-hand --ball-loss --keep-settled`.
- **Tests:** `tests/test_contest_18j.py` (13 tests: each line of the contest rule, the steal foul, the scenario
  card); `tests/test_see_the_steal_18j.py` (4 tests); `tests/test_fiba_18i.py` updated for the steal foul.

## 3. What it proves

@@PROVES@@
- **What it does not prove:** how a person plays under the two rules. And 19 positions is a small gate: one board
  each way decided `dice_in_hand`.

## 4. For Shaun to decide

1. **Adopt the zone, and how.** This step adds no new evidence. 18g's stands: under the zone the offence dribbles
   more and scores about the same, and the computer does not yet find your closeout order under either rule set.
   My advice: decide it after the list fix in Part 3, because that fix is what lets the computer play the zone's
   best defence.
2. **Turn `dice_in_hand` on despite board 3?** It is the part that makes the offence see the Steal coming, and it
   fixes board 1 by 7.8 points. It breaks board 3 by 5.5. Your gate says break none, so it is off. @@DICE_ADVICE@@
3. **The hard contest from the side or behind has vanished from the computer's play.** Two foul rolls and the
   fouled shot's price put it out of reach. If you want to see it sometimes, the lever is rule 4: one roll from the
   side with the arrow on him, two from behind.
4. **Threes are still contested about 1 time in 4, not half.** A soft contest needs a defender next to the shooter.
   If a hand up should reach further, that is a rule: for example a defender two squares away in front with his
   arrow on the shooter. Your call whether to try it.
5. **Does the penalty bite enough?** It costs about twice what it did, and the computer still Steals at 4 fouls
   where the Steal is good. To make it bite harder, the penalty could give the two free throws and the ball back.
6. **The three readings of the contest rule in Part 0.**

## 5. Noticed, not touched

- **The search is too hopeful about a Steal that fails.** On board 3 it reads the Steal at 27.6 and play gives
  31.1. A locked defender costs more over the next turns than the reading sees.
- **The offence's quick list is still hand-written.** `keep_settled` protects shots the rules can value exactly.
  Other turns can still be cut before the defence's answer is read.
- **Board 8 and game EB3F5B still miss,** as they did before the fix: 6.3 and 3.0 behind.
- **The timing test still fails** as it has since 18f (`test_the_agent_only_plays_legal_actions_within_its_budget`).
  Not loosened.
- **Steals tried fell under the new rules.** I traced one position, not the whole run.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next step is the defence's list: what counts as a copy, and what the kept turns
are ranked by. It is search work in both engines under a fixed speed budget, with your closeout order as the test.
