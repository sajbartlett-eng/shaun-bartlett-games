# Step 18i report: FIBA rules for single possessions

## First

- **Speed fits.** With the three rules on, no level is slower than step 18g's code timed in the same hour.
- **Compute: 6.3 core-hours,** against my estimate of 7.5 and the hard limit of 12.
- **Three seconds, closely guarded and the FIBA fouled shot are built in both engines and the app, and on by default
  in the app.** Each has its own switch and can be turned off from the address. Nothing for the table changed.
- **The penalty has no bite under the rules as they stand,** and that is the finding you most need from this step.
  Two free throws are worth what the rest of a possession is worth, so the fifth team foul costs no more than the
  first. See Part 4.

## In plain words: what each rule changed

**Three seconds.** Almost nothing in how the computer plays. It sees the end of the phase coming and steps its man
out of the key. One violation in 160 possessions. A player now has a reason to leave the key, and a marker that
tells him when.

**Closely guarded.** Nothing yet. The computer's ball handler nearly always moves or passes before a count can
build: he never got past one phase end with a defender on him. The rule is there for a person who holds the ball.

**The fouled shot.** This one changed play. A fouled shot is now worth much more than an open one: the shot still
counts and free throws follow. So the defence stopped making the Contests that risk a foul. Five shots in 160 were
fouled before. None after.

**The foul situation.** The computer's Steals do change with it, but the opposite way to basketball. With no fouls
and 10 possessions left it holds back. With 4 fouls it Steals. The numbers behind that:

- A steal foul outside the penalty gives the offence +5 and it keeps the ball. The rest of that possession is worth
  about 27 to 29.
- A steal foul in the penalty gives +5 and two free throws, and the possession ends. Two free throws are worth
  about 29.
- So the fifth team foul costs the defence no more than the first. Being "in foul trouble" has nothing to teach
  until one of those numbers moves. That is a rules question, and it is yours.

## Part 0: rulings and the capture rule

- **Step 18g is merged** (pull request 69). The rulings are D-168 to D-176 in `DECISIONS.md`.
- **What the app is** (D-168) is also principle 14 in `docs/reference/SHAUN_PRINCIPLES.md`.
- **The capture rule (D-170) is built in `rules.zone`,** still off, in both engines, with tests. It replaces step
  18g's reading of the barrier.

| Your words | How it is built |
|---|---|
| "As soon as the offence touches a square adjacent to an arrow, they are captured." | The capture square is the one square the arrow points at. Checked at every square of the ball handler's movement, and where he starts. Any defender can catch him, not only one next to him at the start. |
| "The other arrow restricts where he can get through." | Once caught, he can't cross the other arrow's line to the side away from the arrow that caught him. He may step onto the line. He may leave any other way. |
| "The ball handler can break through with a Dribble action." | A Dribble won against that defender this phase: nothing of his bars the ball handler. |
| A defender whose arrows don't catch him | Bars nothing. |

**Three places I had to choose; each is flagged for you:**

1. **How long the barred line is.** I used the squares along it that the defender's movement left still reaches
   (ruling 5 of D-167: strength is movement left), and always at least the arrow's own square, his foot. So a
   defender who has spent all his movement still bars the one square beside him.
2. **How long he stays caught.** For the rest of that movement. A later Move or Quick Step starts fresh: he is caught
   again only if he starts on, or touches, an arrow's square.
3. **"A square adjacent to an arrow."** Built as the square the arrow points at. The wider reading (every square next
   to the arrow's line) would catch a ball handler two squares from the defender; I did not build it.

- **The noticed items are fixed:** `tools/exam_book.py` and `BASELINE.md` give boards 1, 3 and 8 their played-out
  answers, with the old answer beside each. The printed book itself is regenerated the next time that tool is run.

## Part 1: three seconds in the key (D-172)

- **The key is the lane as the lines are drawn on the board:** columns G to K, from the baseline row to the
  free-throw line (rows 1 to 6). That is larger than the green rim zone (rows 2 to 4). **For you to confirm.**
- **The count.** At each phase end every attacker in the key is marked IN KEY. One who is already marked commits
  the violation: the possession is over and scores 0, as any turnover does in the app.

| FIBA allows | In the game |
|---|---|
| A shooter in the key | Falls out: the shot ends the possession before a phase end. |
| A player in under 3 seconds who dribbles in to shoot | Falls out if he shoots before the next phase ends. If that phase ends first, it is a violation. **Flagged.** |
| A player on his way out of the key | Does not fall out. He is judged where he stands when the phase ends. **Flagged.** |
| A player who steps out and straight back in | Does not fall out. Out and back within one phase still reads as two phase ends in a row. **Flagged.** |

## Part 2: closely guarded, and picking the ball up (D-173)

- **Closely guarded:** a defender next to the ball handler with an arrow on him. Under `rules.zone`, either arrow of
  a standing zone.
- **The ball handler is in one of three states,** kept in the game and shown on him:

| State | How he gets there | What counts |
|---|---|---|
| Holding since the catch | He catches a pass, or starts the possession with the ball | Each phase end closely guarded adds one (HELD 1, HELD 2). The third is the violation. A phase end with nobody on him puts it back to none. |
| Dribbling | He Moves, Quick Steps or Sprints with the ball, or tries a Dribble | Nothing. A live dribble is never counted. |
| Picked up (PICKED UP) | Dribbling, then two whole phases with no action from him | He may only pass or shoot. The count runs as for a holder. |

- **What keeps him active** is as you ruled: his own Move, Quick Step, Sprint or Dribble. A pass or a shot hands the
  ball on or ends the possession. A Hesitate or a teammate's action does not count.
- **One place I chose, flagged:** the phase end at which he becomes PICKED UP is not also counted as HELD 1. The
  count starts at the next one.
- **Nothing else in the rules looked like it should keep him active.** A Screen can't be set by the ball handler.

## Part 3: the fouled shot (D-174)

**What the app did before** (`playmaker_engine/resolve.py`, `contest_outcome`; the value from
`playmaker_engine/scoring.py`, `foul_on_shot_points` and `free_throws`):

- The shot was not rolled and did not count.
- The free throws were not rolled either. They scored 2 or 3 times the shooter's free-throw rating.
- If the open shot was worth more than those free throws, the foul scored the open shot instead.

**What it does now:**

- The shot counts at its contested rating, as it would with no foul.
- Free throws follow by the rules: 1 if it went in, 2 or 3 if it missed, each at the shooter's free-throw rating.
- The score is what that is worth on average, to the nearest whole point, like every other score in the app.
- **The dice are shown apart from the score.** The log adds one line: the shot's roll, how many free throws, how
  many went in. The score does not move with it.

| Across all 75 cards, an average Contest | The open shot | Fouled, before | Fouled, now |
|---|---|---|---|
| A three | 26.3 | 43.8 | 50.9 |
| A layup | 35.0 | 35.1 | 41.4 |

- **The value ceiling (D-145) stands as it is.** It says no position is worth more than the best open shot,
  because the defence can always decline to Contest. That is still true: a fouled shot is worth more than an open
  one, but the defence never has to give one.
- **In play:** fouled shots fell from 5 in 160 possessions (scoring 45.6 on average) to 0 in 160. The defence's
  fouls fell from 0.49 a possession (0.37 to 0.62) to 0.35 (0.26 to 0.44).

**The Steal's value in its parts** (the set's Steal position at clock 10; X3 steps in, then tries a Steal; each part
as the All-Star reads it):

| | Chance | Worth to the offence | Before this step | After, no situation set |
|---|---|---|---|---|
| The foul | 45 in 100 | +5 and play on from a possession worth 38: 43 | 19.4 | 19.4 |
| The miss (no foul, ball kept) | 38.5 in 100 | play on: 38 | 14.6 | 14.6 |
| The ball won | 16.5 in 100 | 0 | 0 | 0 |
| **The Steal as a whole** | | | **34.0** | **34.0** |

- **This step changes nothing here,** because nobody is shooting: the fouled-shot rule does not apply to a Steal on
  a ball handler.
- **How the foul weighs:** it is the largest part. X3 fouls on 45 Steals in 100 and wins the ball on 16 or 17. The
  foul gives the offence +5 and it plays on. The miss leaves the possession where it was, with X3 locked. The ball
  won ends it at 0. So the try is worth it for the 1 time in 6 it wins the ball outright.

## Part 4: the foul situation, set by the scenario (D-175)

**What was already there.** Step 3n built team fouls across a quarter: the count, the penalty from the fifth, and
a price for a foul over the possessions left. It ran on two numbers set by hand.

**What this step did:**

- **Those two numbers are now measured** from 160 possessions of self-play under the app's rules: the defence fouls
  0.35 times a possession (0.26 to 0.44; it was set at 0.25), and a possession is worth 27.5 to the offence (25.5 to
  29.4; it was set at 20).
- **A scenario can set the situation.** Cards 12 and 13 carry it, and the app shows it in plain words: "The defence
  has 4 team fouls; the offence has 1. 3 possessions left in the quarter."
- **A possession in the app's format can be given one from the address:** `?fouls=4&left=3`.
- **The computer's reading uses the cost** wherever a foul can happen, on both sides, and the coach's judging of a
  player's choice runs on the same reading.
- **An Intercept rolls no foul** in the rules, so there is nothing there to price.

**The cost of a foul, by the rules as they stand:**

| | Now | Later |
|---|---|---|
| A steal foul, team fouls 0 to 3 | +5, and the offence keeps a possession worth about 27.5 | brings the penalty one foul nearer |
| A steal foul from the 5th team foul | +5 and two free throws, about 29; the possession ends | nothing more |
| A foul on a shot | the fouled shot (Part 3) | one team foul nearer the penalty |

- **So the penalty costs about 1.7 points more than an ordinary steal foul** (29.2 against 27.5), and those two
  numbers overlap. Bringing it nearer is worth almost nothing.

**The same Steal position under three situations** (the set's Steal position at clock 10; each candidate played out
under each situation, 32 play-outs, the foul's later cost counted in the score):

| The situation | The computer's choice | By play: step in, then Steal | By play: no Steal | Right by play? |
|---|---|---|---|---|
| 0 team fouls, 10 possessions left | **holds back** (X5 moves to B3) | 28.5 (21.9 to 35.2) | 35.4 (32.9 to 37.8) | No: 6.8 worse (-0.7 to 14.3), not clear |
| 4 team fouls, 10 left | **X3 steps in and tries the Steal** | 26.7 (20.4 to 33.0) | 33.6 (31.0 to 36.2) | Yes |
| 4 team fouls, 1 left | the same | 26.7 | 33.6 | Yes |

- **The choice does change with the situation, the opposite way to basketball.** With no fouls and 10 possessions
  left the computer holds back, because a foul now brings the penalty nearer. At 4 fouls it Steals, because the
  next foul is the penalty foul and costs no more than any other.
- **By play the Steal is the better turn in all three.** At 0 fouls the computer's restraint costs about 7 points,
  not clear of chance on 32 play-outs.
- **The last two rows are identical** because at 4 fouls a further foul has no later cost, with 10 possessions left
  or with 1.

**A player in foul trouble: not built, and here is why.** The cost of losing him is the difference in a
possession's worth between his card and his replacement's. A possession's score swings by about 12.5 points from one
to the next, so 160 possessions pin an average down to about 2 points either way. One card swapped for a weaker one
of the same job moves a possession by less than that. Measuring it for one pair would take about 600 possessions,
close to 4 core-hours, and there are 75 cards. I did not run the pilot: the arithmetic from this step's own runs
says it can't be cheap and reliable. Team fouls only are built, as you allowed.

## Part 5: the measures

**The sense-check set, replayed under the three rules** (19 positions: every position near a shot, and boards 1, 3
and 8):

| | Before (the three rules off) | Under the three rules |
|---|---|---|
| The computer's choice is the best by play, or level with it | 18 of 19 | 19 of 19 |
| Points lost a position | 0.7 (0.2 to 1.1) | 0.6 (-0.1 to 1.3) |

The new answers are at 32 play-outs a candidate; the first answers were at 64.

**Which answers moved.** The best candidate changed on 4 of the 19. None of the four changes is clear of chance.

| Position | Best before | Best now | Why (my reading; not traced play by play) |
|---|---|---|---|
| The closeout, shooter can move | X3 Quick Steps to E3, then Moves to B3: 28.8 | X3 Moves to C4: 28.6 (the old best now 35.0) | The old best ended next to the shooter with a Contest that could foul. A foul there now costs about 51, not 44. |
| The closeout, step 2 | X3 Moves next to him, then a Steal: 6.8 | X3 Moves next to him and stops: 10.0 (the Steal 11.4) | Level. A foul on a Steal at a shooter now scores the shot and the free throws. |
| Shoot now or play on 1 | O1 shoots the three: 30.0 | O1 passes to O2: 31.2 | Level. This was the one miss before; the computer's pass is now as good as the shot. |
| Board 3 | nobody moves: 28.4 | the old answer, the low man helps and another covers: 27.6 (nobody moves 30.3) | Level (2.7 apart). Worth watching: your ruling's answer and the board's old answer have swapped places. |

- **The closeout board, shooter unable to move:** your order now scores 25.3 and the computer's Move closer 25.8.
  Under the old rules your order was 4.0 better. It is level now (0.5 apart, -7.2 to 8.2).
- **The set's Steal position at clock 10:** stepping in and Stealing is better for the defence than before (27.5
  against 32.0), and the computer chooses it.

**Self-play, All-Star, 160 possessions each** (`measures.json`, `fidelity.json`):

| | Before (the three rules off) | After (on) |
|---|---|---|
| Points a possession | 29.3 (27.4 to 31.3) | 27.5 (25.5 to 29.4) |
| Three-second violations in 100 possessions | none | 0.6 (0.1 to 3.5) |
| Closely guarded violations in 100 possessions | none | 0 (0 to 2.3) |
| Turns where the ball handler is closely guarded | 34% (32 to 37) | 35% (32 to 38) |
| ... and he then moves with the ball | 68% | 70% |
| ... passes | 16% | 14% |
| ... tries a Dribble | 5% | 6% |
| ... does nothing with it that turn | 11% | 10% |
| Turns that began with a count on him (HELD 1; HELD 2) | not counted | 8; 0 |
| Shots by phase, 1 to 6 (in 100) | 46, 26, 12, 9, 4, 2 | 47, 30, 15, 7, 0, 1 |
| Shots contested | 24% (18 to 32) | 24% (17 to 32) |
| Fouled shots in 100 possessions, and what they scored | 3.1 (1.3 to 7.1); 45.6 | 0 (0 to 2.3) |
| Steals tried a possession | 0.94 (0.76 to 1.11) | 0.83 (0.69 to 0.98) |
| The ball lost, per 100 phases kept | 11.3 (7.5 to 16.6) | 16.2 (11.2 to 22.9) |

- **Where the 1.9 points went.** Not clear of chance on 160 possessions. Most of it is the five fouled shots that
  no longer happen: they scored 45.6 each, and those possessions now end in an ordinary shot.

## Part 6: speed

The time to finish 1 pair on 9 decisions in 10, in seconds. Two rounds on a quiet machine, each timing 18g's code,
this step's with the three rules off, and with them on (`speed.json`).

| Level | Target | 18g's code | This step, rules off | This step, rules on | Rules on against 18g |
|---|---|---|---|---|---|
| Rookie | 0.3 | 0.24, 0.23 | 0.26, 0.25 | 0.22, 0.26 | 2% slower |
| Starter | 1.0 | 0.90, 0.92 | 0.89, 0.95 | 0.86, 0.92 | 2% faster |
| All-Star | 2.5 | 1.91, 1.88 | 1.96, 1.92 | 1.77, 1.86 | 4% faster |

- **Every level fits** by D-161. The differences are inside the round-to-round swing.
- The counts are a few whole-number checks at a phase end. The fouled shot is one sum.
- **The capture rule is not timed here.** `rules.zone` is off; it is timed when the zone is retested after step 18j.

## Compute against the estimate and the hard limit

Estimate 7.5. Hard limit 12. **Used: 6.3.**

| Run | Estimated | Used | |
|---|---|---|---|
| Agreement checks between the two engines, tests | 1.5 | 1.3 | |
| The sense-check set: 19 positions replayed under the three rules | 2.0 | 1.85 | |
| Self-play, 160 possessions before and after | 2.0 | 2.1 | |
| A pilot of the three rules, 32 possessions each way | 0.5 | 0.5 | |
| The same Steal position under three foul situations, by play | 0.5 | 0.35 | |
| A player in foul trouble: the pilot | 0.5 | 0 | not run (Part 4) |
| Speed | 0.3 | 0.2 | |
| Searches | 0.2 | 0 | |

- **What the rest would cost:** the other 15 positions of the set under the three rules, about 2.5; one pair of
  cards measured for foul trouble, about 4.

## 1. Changes to the printed game

None. All four rules are for the app only. `RULES_CURRENT.md` lists the three new ones under "Split by format",
with the table's side reading "No such rule" or the table's own fouled-shot rule.

## 2. What changed

- **`rules.three_seconds`, `rules.closely_guarded`, `rules.fiba_fouled_shot`:** on in the app's format, off at the
  table, in `playmaker_engine` and `playmaker_web/static/engine.js`. `?three=0`, `?guarded=0` and `?fouledshot=0`
  turn each off.
- **The game state** keeps two new counts: who was in the key at the last phase end, and the ball handler's state.
- **The app:** IN KEY, HELD 1, HELD 2 and PICKED UP markers on the players and in the player list; a line for each
  violation; the dice line for a fouled shot; a reminder of each rule; `?fouls=` and `?left=` for a foul situation.
- **`rules.zone`** (off): the capture rule (D-170) in place of step 18g's barrier.
- **Scenario cards 12 and 13** carry a foul situation, shown in plain words.
- **`ai_profiles.json`:** the two numbers that price a foul over a quarter are measured, not set by hand.
- **`DECISIONS.md`** D-168 to D-176; **`SHAUN_PRINCIPLES.md`** principle 14; the rules register and
  `RULES_CURRENT.md`.
- **Tools:** `tools/step_18i.py`; `tools/sense_18h.py` replays under the FIBA rules and a foul situation, and splits
  a Steal's value into its parts; `tools/js_equivalence.py --fiba`.
- **Tests:** `tests/test_fiba_18i.py` (20 tests: each rule, the foul situation, the markers); `tests/test_zone_18g.py`
  (the capture rule).

## 3. What it proves

- **The two engines agree** with the three rules on: 300 positions and 16 searches, and 200 shot reactions, no
  differences. With the capture rule: 300 positions and 12 searches, and 150 positions with a broken zone and 6
  searches, no differences.
- **With the three rules off, play is unchanged:** the "before" self-play gives step 18g's result to the decimal
  (29.34).
- **Tests, with the three rules on by default in the app:** the 21 named test files: 397 passed, 11 expected
  failures, 1 failed, the timing test that has failed since 18f. After the two foul numbers were measured, the
  files they touch were run again: 148 passed, 3 expected failures. The 11 browser tests pass.
  `tests/test_rules_current.py` passes with `RULES_CURRENT.md` regenerated for the three rules.
- **What it does not prove:** how a person plays under these rules. The computer avoids both violations so well
  that neither has been seen to matter in its own play.

## 4. For Shaun to decide

1. **The foul situation has no bite. Do you want it to?** Under today's rules the penalty costs the defence about
   as much as any steal foul. If "4 fouls with 10 possessions left" is to teach restraint, a rule has to change:
   what the +5 is worth, what a free throw is worth beside a possession, or what the penalty gives. Which one is
   yours.
2. **Scenario cards play under the table's rules in the app.** The foul situation only means something under the
   app's rules. Cards 12 and 13 show their situation and pass it to the engine, but the table's foul rule is what
   plays. Should a card that sets a situation play under the app's rules?
3. **The key:** the lane as drawn (G to K, rows 1 to 6), or the green rim zone only?
4. **The three-second cases that don't fall out of the phase-end count** (Part 1): leave them, or add allowances?
5. **The capture rule's three choices** (Part 0): the length of the barred line, how long he stays caught, and the
   capture square.
6. **A player in foul trouble:** leave it out, or spend about 4 core-hours a pair to measure it?

## 5. Noticed, not touched

- **A fouled shot is now worth far more than an open one,** so the computer's defence has stopped fouling shooters
  altogether. Real defences do foul shooters. Whether the game should see more of it is a question about the foul
  roll and the Contest, not about this step's scoring.
- **The timing test still fails** as it has since 18f (`test_the_agent_only_plays_legal_actions_within_its_budget`).
  Not loosened.
- **The ball is lost more often with the rules on** (11 to 16 in 100 phases kept; the ranges overlap). Three
  seconds accounts for 1 of the 4 extra. I have not traced the rest.
- **`tools/exam_book.py`'s printed book** still needs a rerun to pick up the new text for boards 1, 3 and 8.

## 6. Model for the next step

Claude Fable 5.2, effort high. Step 18j opens the offence's judgement with the set as its gate, under these rules.
It is search work in both engines, and step 18g gave it a clear target: the offence does not picture a defender
Moving in and then Stealing.
