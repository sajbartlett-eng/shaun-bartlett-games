# Step 18j report: the soft and hard contest, the penalty's bite, and seeing the Steal coming

## First

- **Speed fits.** With the two rule changes on, no level is slower than step 18i's code timed in the same rounds,
  on 9 decisions in 10. One form of the fix did break it (Starter 13% slower, on its target line); I rebuilt that
  part so it costs nothing. See "Speed".
- **Compute: 10.4 core-hours,** against my estimate of 10.5 and the hard limit of 12.
- **The two rule changes are built in both engines and the app, and on by default in the app.** Each has its own
  switch. Nothing for the table changed.
- **The fix for "step in, then Steal" is built in three parts, and all three are off.** None passed your gate
  cleanly. The two that help each fix a position and each move board 3, and board 3 turns out to be a coin toss
  (Part 3). So the gate can't settle it. That call is yours, and my advice is in "For Shaun to decide".
- **One test fails that passed before, and it is a rules question.** The exam expects the computer to decline an
  early Steal on a strong dribbler. With a steal foul now free of points it Steals, and by play the two are level.
  See "What it proves" and decision 3.
- **Your closeout order is still not found.** I can now say exactly where it is lost. See Part 3.
- **The zone was not retested.** It needed about 4 core-hours that the step did not have, as I said before the first
  run, and part 3 did not pass.

## In plain words

**The soft and hard contest.** More shots meet a defender now, and all of the rise is the hand up. About 3 shots in
10 are contested where it was about 1 in 4. Of those, a little over half are soft. The jump to the ball has become
rarer and more careful: the computer now only jumps from in front. It has stopped jumping from the side or from
behind altogether, because those roll for a foul twice and a fouled shot is costly. No shot was fouled in 160
possessions. Threes are contested about as often as before, about 1 in 5, nowhere near half. Scoring did not clearly
fall. The offence shoots from where no defender ends next to it, and a hand up takes only a point or three off when
one does.

**The penalty change.** An ordinary steal foul now costs the defence no points, so the computer Steals in the
position where it used to hold back, and play says it is right to. Over a whole possession it tries fewer Steals,
not more, and fouls less. One traced position shows why: the offence now passes the ball away from a defender who
stands next to it, where it used to hold the ball and lose it. At 4 team fouls with 10 possessions left the computer
still Steals. It does not hold back. In that position the Steal wins by about 8 points even at the penalty's price,
so by play it is right. The penalty does cost more than it did, about twice as much, but not enough to change that
choice.

**Does the computer see the Steal coming?** By default, no: nothing in its judgement changed. With the part built
for it turned on (`dice_in_hand`):

- **The offence sees it.** On the position you named it reads the held ball at 19, play gives 20, and it passes.
  Without the part it reads the held ball at 27.5 and holds.
- **The defence uses it.** It steps in and Steals on board 1, 8 points better than what it does now.
- **And it changes the game.** In self-play the defence tries half as many Steals again, fouls twice as often, and
  the offence answers by shooting in phase 1 on 63 shots in 100, where it was 49. Head to head it leads by 2.4
  points a pair, not clear of chance.

**The offence's list** drops an open three by default, as it did in 18h. A second part (`keep_settled`) stops that,
at no cost in time.

**Is your closeout order found?** No. The defence's list keeps one turn for each different quick reading, and the
quick reading can't tell your order from other pairs of movements, so your order is dropped before the search ever
compares it. Shown your order, the search does read it as the best turn on the board (with `dice_in_hand` on):
21.0, against 24.8 for the Move closer and 30 for doing nothing. Play gives 21.5, 24.4 and 30.0. So the judgement
is right and the list is what loses it.

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

160 possessions of All-Star self-play, the same starts and dice. "This step's default" is the two rule changes
with no change to the computer's judgement. The last column is beside it for Part 5.

| | Step 18i | This step's default | With `keep_settled`, first form |
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
| Closeout, the shooter cannot move | Your order 25.3 to 21.5. The Move closer 25.8 to 24.4. Doing nothing 33.0 to 30.0. Your order now leads by 3 where the two were level. | Once the shot is declared a defender now Sprints next to the shooter and gets a hand up: a point off, with no Contest action spent. And the kept Move's Steal costs no points when it fouls. |
| Closeout, the shooter can move | The Move closer 28.6 to 30.5. Doing nothing is now level with it, 30.0. | The same hand up, which doing nothing now gets for free in the reaction. |
| Closeout, step 2 | "Moves next to him and stops" 10.0 to 25.8. "Moves next to him, then Steals" 11.4 to 8.5. | When the defender stops, the offence now passes away at once and shoots a three. Before, it held the ball and lost it 8 times in 16. Stealing now is clearly the best turn. |
| The Steal position, clock 2 | Doing nothing 27.0 to 36.0. Step in, then Steal is now best, 28.1. | The offence now shoots from D9 where it shot from E10, and the defence makes no Contest there. Under 18i it moved and jumped. I read that as the two foul rolls pricing the jump out; not checked further. |
| Shoot now or play on 1 | Playing on fell from 31.2 to 9.8, and from 29.0 to 5.4. Shooting the open three, 30, is now far the best. | When the pass is caught the defence steps in and Steals, since the foul costs it no points. The ball is lost 7 times in 16. |
| Board 3 | The board's help 27.6 to 35.1. The computer's own choice, 25.6, is best. | Not traced. |
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

Three switches, all in both engines. None names a kind of move. All three are off.

| Switch | What it does |
|---|---|
| `search.keep_settled` | The best turn the rules settle outright (a declared shot, or the possession ending) is never cut from a list for turns that only read higher before the other side has answered. |
| `search.dice_in_hand` | In the defence's list, a first action that leaves its mover able to send something to the dice (a Steal, a Challenge, an Intercept) is ranked by the better of stopping there and that roll, by the rules' chances, and is not dropped as a copy. If he can roll nothing from there, the action is read like any other. |
| `eval.ball_loss` | Where the search stops with the defence to act, the position is worth no more than what its best Steal leaves, counting a defender who can still get next to the ball handler. Settings: either side's search, or only the offence's. |

- **`keep_settled` has had two forms.** The first added every settled turn to the list. It made the search slower
  (see "Speed"). The final form puts the one best settled turn in the place of the lowest-reading turn, so the list
  is no longer. A settled turn's value is exact, so a second, lower one adds nothing.
- **I did not open the offence's list** the way 18e opened the defence's. The two cheaper parts reached the named
  positions first, and an open offence list is the costliest of the three options in speed.

## Part 3: the gate

The 19 positions near a shot, under the new rules. Every setting's choices are scored against the same played-out
answers. A choice passes when it is the best candidate or level with it inside chance.

| | The default (no fix) | `keep_settled`, first form | `keep_settled`, final form | first form and `dice_in_hand` |
|---|---|---|---|---|
| Best or level, of 19 | 14 | 15 | 14 | 15 |
| Points lost a position | 1.9 (1.3 to 2.6) | 1.7 (1.0 to 2.3) | 2.1 (1.4 to 2.7) | 1.5 (0.9 to 2.2) |
| Shoot now or play on 1 | plays on, 5.4 behind | **shoots the three** | **shoots the three** | **shoots the three** |
| Board 1 | does nothing, 7.8 behind | the same | the same | **steps in and Steals, best** |
| Board 3 | best (25.6) | best (25.6) | 7.7 behind (2.6 to 12.7) | 5.5 behind (1.5 to 9.6) |
| Closeout, the shooter cannot move | 8.5 behind | 8.5 behind | 8.5 behind | 8.5 behind |

- **No setting improves the set clearly and breaks none.** The first form of `keep_settled` does on the set, and
  fails on speed. The final form fits on speed and moves board 3. `dice_in_hand` fixes board 1 and moves board 3.
- **Board 3 is a coin toss.** The defence reads 24 turns exactly level there (29.7). The two it has picked from
  them play out at 25.6 and at 33.3. Doing nothing plays at 32.9. Which of the 24 it picks changes with any change
  to a list, because level turns are split by the spread of the replies behind them. The default's 25.6 is the
  lucky end. So board 3 can't tell a good change from a bad one until the computer can tell those turns apart.
- **With `dice_in_hand` the pick on board 3 is not a toss:** the search prefers the Steal, reading it at 27.6.
  Play gives 31.1. That is better than doing nothing and worse than the lucky 25.6. The search is too hopeful about
  what follows a Steal that fails.

**The four tests you named:**

| Test | The default | With `keep_settled` | With `dice_in_hand` as well |
|---|---|---|---|
| Closeout, the shooter cannot move: does the defence keep the Move? | No. It does nothing: 30.0 by play, 8.5 behind your order (3.8 to 13.3). | No. | No. |
| Closeout, the shooter can move: does the Move closer stay best? | By play yes, level with doing nothing (30.5 and 30.0). The computer does nothing. | The same. | The same. |
| "Hold the ball" after your order: does the offence pass? | No. It reads the held ball at 27.5. Play gives 19.9. | No. | **Yes.** It reads the held ball at 19.1 and the pass at 21.0, and passes. |
| Shoot now or play on 1: does the open three stay on the list? | No. It plays on, 5.4 behind (1.6 to 9.1). | **Yes.** It shoots, 30. | Yes. |

**`eval.ball_loss` showed no value.** For the offence it adds nothing once `dice_in_hand` is on: the held ball
already reads 19.1. In the defence's own search it counts the same Steal after every one of its turns, whether it
steps in now or waits, so the defence puts the Steal off. On the Steal position at clock 10 it did nothing, 5.9
behind (0.4 better to 12.1 worse). I stopped work on it there.

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

**The backstop head to head,** All-Star, 80 paired possessions each, under the new rules:

| | Points a pair for the first named | Won, lost, level |
|---|---|---|
| `keep_settled` (first form) against the default | 0.8 behind (3.4 behind to 1.8 ahead) | 17, 25, 38 |
| `dice_in_hand` and `keep_settled` (first form) against `keep_settled` (first form) | 2.4 ahead (0.5 behind to 5.4 ahead) | 25, 18, 37 |

- Neither is clear of chance. `keep_settled` is level with the default. `dice_in_hand` leans ahead.
- I ran 160 pairs, not 200: the limit was better spent on timing the fix once speed turned out to be the problem.

## Part 4: the zone

Not retested. Two reasons. It needs about 4 core-hours (21 positions replayed and 2 runs of 120 possessions), which
did not fit beside the rest; I said so in `docs/runs/step18j/PREDICTIONS.md` before the first run. And the prompt
makes it conditional on part 3 passing, which it did not.

## Part 5: the recheck

The default's judgement did not change, so the recheck is the "This step's default" column in Part 3b. Against 18i:

- **Points a possession:** 26.9 against 27.5. The ranges overlap.
- **Ball lost in 100 phases kept:** 17 against 16. No change.
- **Shots by phase:** the same shape. 82 shots in 100 in the first two phases against 78.
- **Shots contested:** 30 in 100 against 24, the rise all soft.
- **Shots rushed:** 15 in 100 against 13. The ranges overlap.
- **Nothing moved the wrong way clear of chance.**

**With `dice_in_hand` on** (and `keep_settled` in its first form), 160 possessions, beside the default:

| | The default | With `dice_in_hand` |
|---|---|---|
| Points a possession | 26.9 (25.1 to 28.7) | 25.4 (23.7 to 27.2) |
| Steals tried a possession | 0.60 (0.49 to 0.71) | 0.97 (0.82 to 1.12) |
| Steal fouls a possession | 0.25 (0.17 to 0.33) | 0.51 (0.39 to 0.62) |
| Ball lost, in 100 phases kept | 17 (12 to 24) | 24 (16 to 33) |
| Shots in phase 1, in 100 | 49 | 63 |
| Shots contested, in 100 | 30 (23 to 38) | 36 (28 to 44) |
| ... by a hard contest | 12 (7 to 18) | 21 (15 to 28) |
| Threes contested, in 100 | 21 (14 to 30) | 32 (24 to 42) |
| Shots rushed, in 100 | 15 (10 to 22) | 18 (12 to 25) |

- **This is a different game.** A defence that sees every Steal uses it, because outside the penalty a steal foul
  now costs it nothing in points. It Steals about once a possession and fouls on half of them.
- **The offence sees it coming and shoots early.** 63 shots in 100 go up in phase 1. Possessions get shorter.
- **Contests rise toward what you expected:** threes contested go from 21 to 32 in 100, and hard contests nearly
  double.

## Speed

The time to finish 1 pair on 9 decisions in 10, in seconds. Each line is two rounds, and each round times 18i's
code and this step's in turn (D-161). The machine ran at different speeds across the afternoon, so compare within
a line, not down a column.

| Setting | Level | Target | 18i's code | This step | |
|---|---|---|---|---|---|
| **The default** | Rookie | 0.3 | 0.28, 0.27 | 0.28, 0.27 | level |
| | Starter | 1.0 | 1.06, 0.96 | 0.98, 0.94 | 5% faster |
| | All-Star | 2.5 | 2.13, 2.00 | 1.83, 1.97 | 8% faster |
| `keep_settled`, first form | Rookie | 0.3 | 0.24, 0.25 | 0.28, 0.31 | 19% slower |
| | Starter | 1.0 | 0.92, 0.94 | 1.04, 1.05 | **13% slower, on the target line** |
| | All-Star | 2.5 | 1.88, 1.83 | 2.02, 1.92 | 6% slower |
| `keep_settled`, final form | Rookie | 0.3 | 0.26, 0.27 | 0.26, 0.27 | level |
| | Starter | 1.0 | 1.00, 1.02 | 1.02, 1.01 | level |
| | All-Star | 2.5 | 2.05, 2.06 | 1.98, 2.00 | 3% faster |
| `dice_in_hand` with `keep_settled` | Rookie | 0.3 | 0.27, 0.26 | 0.27, 0.31 | 10% slower, inside the swing |
| | Starter | 1.0 | 0.93, 0.97 | 0.97, 0.89 | level |
| | All-Star | 2.5 | 2.05, 1.88 | 2.09, 1.92 | 2% slower |

- **The default fits.** Scaled to 18i's report as D-161 asks: Rookie about 0.24, Starter about 0.85, All-Star
  about 1.7.
- **The first form of `keep_settled` did not fit,** which is why it was rebuilt. The final form costs nothing
  measurable.
- **The All-Star's middle decision is slower** with the two rules on (about 1.55 against 1.35) though its 9 in 10
  is not. The soft contest adds a little work to every reading.
- **`rules.zone` is not timed.** It is off, and it is timed when the zone is retested.

## Compute

Estimate 10.5. Hard limit 12. **Used: 10.4.**

| Run | Estimated | Used | |
|---|---|---|---|
| The set replayed under the two rule changes | 1.9 | 2.25 | |
| Self-play under the two rule changes, 160 possessions | 1.1 | 0.82 | |
| The three foul situations by play | 0.4 | 0.21 | |
| The fault shown, and traces of the answers that moved | 0.3 | 0.41 | |
| The fix: pilots and the gate, new choices played out | 2.0 | 0.42 | most choices already had an answer |
| The backstop head to head, 160 pairs | 1.5 | 1.27 | |
| The zone retest | 0 | 0 | did not fit; said before the first run |
| Self-play with parts of the fix on, 2 runs of 160 | 1.1 | 1.37 | |
| Agreement checks, tests, speed | 2.0 | 3.14 | speed took 1.15: finding which change cost the time |
| Searches | 0.2 | 0.15 | |
| Exam position 10 by play | 0 | 0.34 | not planned; a test failed and play had to say why |

- **What the rest would cost:** the zone retest, about 4. The other 15 positions of the set under the new rules,
  about 2.5.

**How the predictions came out** (`docs/runs/step18j/PREDICTIONS.md`):

1. Shots contested above 45 in 100, points down by 1 to 3: **wrong.** 30 in 100, and points did not clearly move.
2. Fouled shots return: **wrong.** None. The computer stopped jumping from the side instead.
3. Steals tried rise, and the computer holds back at 4 fouls: **wrong on both.** Steals fell, and it Steals at 4
   fouls.
4. The reply list is too narrow to hold a Move followed by a Steal: **right.** The speed cost came from a
   different part, keeping settled turns, and that part was rebuilt.
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
- **`ai_profiles.json`:** `search.keep_settled`, `search.dice_in_hand` and `eval.ball_loss`, all off, each with a
  note of what the gate found; the two foul numbers remeasured (0.25 and 26.9).
- **`DECISIONS.md`** D-177 to D-180; the rules register and `RULES_CURRENT.md`.
- **Tools:** `tools/step_18j.py`; `tools/sense_18h.py` replays under the new rules (`answers_18j.json`);
  `tools/js_equivalence.py --soft --dice-in-hand --ball-loss --keep-settled`.
- **Tests:** `tests/test_contest_18j.py` (13 tests: each line of the contest rule, the steal foul, the scenario
  card); `tests/test_see_the_steal_18j.py` (5 tests); `tests/test_fiba_18i.py` updated for the steal foul.

## 3. What it proves

- **The two engines agree.** With the two rules on: 200 positions and 12 searches; with `rules.zone` on as well,
  200 positions and 8 searches; 100 positions with a broken zone and 4 searches; 200 shot reactions. With all three
  parts of the fix on: 60 positions and 14 searches. No differences.
- **With the two rules off, play is unchanged:** self-play gives step 18i's result to the decimal (27.48).
- **Tests, the 23 named files:** 413 passed, 12 expected failures, 1 expected failure that now passes, 2 failed.
  The 11 browser tests pass. `tests/test_rules_current.py` passes with `RULES_CURRENT.md` regenerated.
  - **Failed, as since 18f:** the timing test. Not loosened.
  - **Failed, new: exam position 10.** It expects the All-Star to decline an early Steal on a strong dribbler. It
    now Steals, because the foul costs no points. By play, 48 play-outs each: the Steal 30.5 (29.2 to 31.9), holding
    back 29.5 (26.8 to 32.2). Level. I have not changed the test.
  - **Three tests stated the old rule** (+5 on every steal foul in the app) and now state D-179: one each in
    `test_step3m.py`, `test_step3n.py` and `test_step6.py`. `test_fiba_18i.py` likewise. The table's side of each
    is untouched.
  - **Exam positions 2 and 14 passed in 18i and fail now.** Both are on the exam's open list, so the run counts
    them as expected failures. Position 2: the defender goes to the same square with 4 on the clock and with 12.
    Position 14: one first action is chosen 9 times in 10 where the exam wants more variety.
  - **`test_an_early_cut_is_flagged_with_a_legal_reorder`** was an expected failure and now passes.
- **What it does not prove:** how a person plays under the two rules. And 19 positions is a small gate: one board
  each way decided `dice_in_hand`.

## 4. For Shaun to decide

1. **Adopt the zone, and how.** This step adds no new evidence. 18g's stands: under the zone the offence dribbles
   more and scores about the same, and the computer does not find your closeout order under either rule set. My
   advice: decide it after the list fix in Part 3, because that fix is what lets the computer play the zone's best
   defence.
2. **Which parts of the fix to turn on.** None passed "break none", so all are off. My advice:
   - **`keep_settled`: on.** It stops the offence dropping an open three (5.4 points on that position) and costs
     no time. Its first form was level head to head. Its one loss is the board 3 coin toss.
   - **`dice_in_hand`: on only after item 3.** It does what this step was for, and it leans ahead head to head.
     But with a steal foul free of points it makes the defence Steal about once a possession and the offence shoot
     in phase 1 on 63 shots in 100.
   - **`ball_loss`: leave off.**
3. **Is a steal foul that costs no points what you want?** That is D-179 as ruled. With the computer's present
   judgement it changes little, though it already fails exam position 10: the computer no longer declines an early
   Steal on a strong dribbler. If the rule stands, that exam position should change to match. Once the defence
   sees its Steals (item 2), it Steals about once a possession and fouls on half of them, because outside the
   penalty the foul only locks the defender. Two simple levers if you want a price back: a smaller bonus than the
   old +5, or the penalty starting a foul sooner.
4. **Board 3 in the gate.** The computer reads 24 turns level there and they play out 8 points apart, so the board
   passes or fails by luck. Options: leave it; or score a level pick by the average of the turns it reads level,
   which costs about 1 core-hour once to play them all out.
5. **The hard contest from the side or behind has vanished from the computer's play.** Two foul rolls and the
   fouled shot's price put it out of reach. If you want to see it sometimes, the lever is rule 4: one roll from the
   side with the arrow on him, two from behind.
6. **Threes are contested about 1 time in 5, not half.** A soft contest needs a defender next to the shooter. If a
   hand up should reach further, that is a rule: for example a defender two squares away, in front, with his arrow
   on the shooter.
7. **Does the penalty bite enough?** It costs about twice what it did, and the computer still Steals at 4 fouls
   where the Steal is good. To make it bite harder, the penalty could give the two free throws and the ball back.
8. **The three readings of the contest rule in Part 0.**

## 5. Noticed, not touched

- **The search is too hopeful about a Steal that fails.** On board 3 it reads the Steal at 27.6 and play gives
  31.1. A locked defender costs more over the next turns than the reading sees.
- **Level turns are split by luck.** Board 3 is where it showed, but any board where many turns read exactly level
  has it.
- **The offence's quick list is still hand-written.** `keep_settled` protects shots the rules can value exactly.
  Other turns can still be cut before the defence's answer is read.
- **Board 8 and game EB3F5B still miss,** as they did before this step: 6.3 and 3.0 behind.
- **The timing test still fails** as it has since 18f (`test_the_agent_only_plays_legal_actions_within_its_budget`).
  Not loosened.
- **Steals tried fell under the new rules** with the default. I traced one position, not the whole run.
- **Exam positions 2 and 14 now fail** (above). Not traced.
- **`tools/sense_18h.py score` stops with an error** when asked to add play-outs for one position only. The
  play-outs are kept and a second run reads them.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next step is the defence's list: what counts as a copy, what the kept turns are
ranked by, and how level turns are split. It is search work in both engines under a fixed speed budget, with your
closeout order and board 3 as the tests.
