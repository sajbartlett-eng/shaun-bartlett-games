# Step 18k report: one foul price, and the defence's shortlist

## In five lines

1. **No foul gives +5 in the app now, and every possession starts from a foul situation** (2 team fouls, 8
   possessions left, shown on the screen).
2. **That left a steal foul with no price at all.** Two free throws are worth about what the possession was worth
   anyway, so the penalty does not bite. The computer Steals as often as it can see a Steal.
3. **The shortlist fix is built, and off.** Its plain form gains one board and leans slightly behind head to head.
   Its full form lets the defence find every step-in Steal, which fixes two boards and floods the game with Steals
   (121 tried and 61 fouled in 100 possessions).
4. **Your closeout order is still not found, and the list is not the reason.** The order only pays off on the
   defence's next turn, after the offence has replied. The defence's search stops one turn before that.
5. **Speed fits. Compute: 10.2 core-hours** against an estimate of 10.0 and a limit of 12. A machine restart
   cost 2.75 of those.

## Part 0: the rulings, built

- **Step 18j is merged** (pull request 71). The rulings are D-181 to D-183 in `DECISIONS.md`.
- **No +5 on any foul in the app (D-181).** A steal foul from the 5th team foul is two free throws and nothing
  more. The table keeps its +5.
- **The default foul situation (D-182).** With nothing set, a possession in the app starts at 2 team fouls each
  with 8 possessions left in the quarter. The screen reads "Team fouls 2 · bonus from the 5th · 8 possessions left
  this quarter". A running quarter between the same two players, or `?fouls=` and `?left=`, still sets its own.
- **`search.keep_settled` is on.** `eval.ball_loss` stays off.
- **Exam position 10** now passes whether the computer Steals early on a strong dribbler or holds back.
- **Board 3** is scored by the average of the turns the computer reads level. All 24 were played out.

**Checked against basketball.** 160 possessions of All-Star self-play under the new default. The band is about 8
steals and 8 to 10 non-shooting fouls in 100 possessions a team.

| In 100 possessions | Basketball | The default | `dice_in_hand` on | `keep_in_hand` full | `keep_in_hand` `'moves'` |
|---|---|---|---|---|---|
| Steals tried | not counted | 69 (57 to 82) | 111 (94 to 127) | 121 (104 to 138) | 73 (59 to 86) |
| Steals won | about 8 | 11 (6 to 16) | 19 (13 to 26) | 19 (13 to 26) | 13 (7 to 18) |
| Steal fouls | 8 to 10 | 34 (25 to 44) | 56 (44 to 67) | 61 (49 to 73) | 36 (27 to 46) |

- **Steals won sit inside twice the band with the default.** With either switch on they sit a little above it.
- **Steal fouls are far outside the band everywhere:** 3 to 4 times it with the default, 6 times with a switch on.
  About half of all Steals tried end in a foul. That share comes from the cards' foul ratings and the two foul rolls
  from the side or behind, not from what the computer chooses.
- **So `dice_in_hand` stays off,** by your rule.
- **Nothing was tuned to move these.**

**Why the penalty does not bite.** A possession here scores about 27. Two free throws score twice the shooter's
free-throw rating: 26 to 31 for these cards. So ending the possession with two free throws costs the defence about
what letting it run would have. In basketball two free throws are worth about one and a half possessions. Here
they are worth one. With the +5 gone from the penalty too, a foul's later cost is close to nothing at any count.

## Part 1: why your closeout order is lost

18j said the list drops your order as a copy. That is true, and it is not the whole reason. Three facts, all on
the closeout board with the shooter unable to move:

| | What the search reads |
|---|---|
| After your order, the offence's best reply, when the offence is the one searching | 27.5 (21.7 with `dice_in_hand`) |
| After the same turn with X2 on B8 and not B6, the offence's best reply | 31.7 |
| X3's Quick Step with X2 to B6, when the defence is the one searching | 30.1 |
| Doing nothing, when the defence is the one searching | 30.0 |

- **The offence's search sees your order work.** It looks at its own turn and then the defence's answer, so it sees
  X3 step in and X2 with a hand up at the catch.
- **The defence's search does not.** It looks at its own turn and the offence's reply, and stops. At that point
  your order has not paid off yet. It reads 0.1 worse than doing nothing.
- **What separates B6 from B8 for X2 is where the offence's next pass will be caught.** No reading of the board as
  it stands shows that. It shows only after the offence moves.

So the defence needs to look one turn further for a turn like yours: its own turn, the reply, and its own answer.

**What that costs,** measured on this board at the All-Star:

- One more turn on the list, read as today: 54 thousandths of a second, about 3.5% of the search.
- One turn read one turn further: about as long as a whole search today, 1.3 to 2 seconds.
- The All-Star has about 0.6 seconds to spare inside its target. Starter has about 0.15. Rookie has 0.05.

That does not fit for every turn on the list. It would fit for one or two, if the search could tell which. That is
the next piece of work, and I describe it under the decisions.

## Part 2: what was built

One switch, `search.keep_in_hand`, in both engines, in two forms.

| Form | Two turns are not copies when they leave a defender a different... |
|---|---|
| `'moves'` | movement left this phase (a Move, a Quick Step), or set against rushed |
| `true` (full) | all of that, and a Steal he can roll from where he stands or still reach with the movement he has left |

- **No kind of move is named.** Every action carries the same record of what it leaves in hand, and the list keeps
  one turn for each different reading and record.
- **A pair of movements is now read as a pair** when one of them only puts a Steal in hand (full form). Before, a
  pair needed each movement to lower the reading.
- **On the closeout board the list grows from 84 kept turns to 179.**

**Ranking the kept turns by what the search reads after the reply.** The search already does this for the 24 turns
it keeps. Doing it for more costs 3.5% of the All-Star's time a turn, as above. I did not widen the list: the
closeout board shows the extra turns would be read level with the rest anyway.

**Splitting level turns by evidence.** I tested the evidence before building anything. Board 3's 24 level turns,
each played out:

- **They play out from 26.7 to 37.3.** Average 31.
- **A reading one turn shorter is the same for all 24.** It can't split them.
- **A deeper look splits them the wrong way.** It prefers the turns that leave the defence a second action. By play
  those are 3.5 points worse than stopping after one: the computer's second action there does harm.
- **So I built no new splitter.** Nothing cheap points the right way, and the costly one points the wrong way. The
  spread of replies stays.

## Part 3: the gate

The 19 positions near a shot, replayed under the rules after Part 0. Every candidate was played 16 times; the
positions the gate turns on were played 32 times.

| | The default | `keep_in_hand` `'moves'` | `keep_in_hand` full | `dice_in_hand` |
|---|---|---|---|---|
| Best or level, of 19 | 15 | 16 | 16 | 16 |
| Points lost a position | 1.6 (1.0 to 2.2) | 1.6 (1.0 to 2.2) | 1.7 (1.0 to 2.4) | 1.3 (0.7 to 1.9) |
| Closeout, the shooter cannot move | does nothing, 6.5 behind (1.8 to 11.3) | the same | the same | the same |
| Game EB3F5B | 3.0 behind | **best** | **best** | 3.0 behind |
| Board 1 | does nothing, 6.5 behind (2.9 to 10.1) | the same | **steps in and Steals, best** | **steps in and Steals, best** |
| Board 3 | a level pick: 4.6 behind on average (0.2 ahead to 9.4 behind) | a level pick: 4.3 behind on average (0.4 ahead to 9.1 behind) | Steals, 4.6 behind (1.5 ahead to 10.8 behind) | the same Steal |
| Board 8 | 6.1 behind | the same | the same | the same |
| Shoot now or play on 4 | best | best | **broken:** sets a screen, 8.6 behind (2.6 to 14.6) | best |
| The Steal position, clock 2 | level, 2.9 behind | level, 5.1 behind (0.8 ahead to 11.0) | level, 5.1 behind (0.8 ahead to 11.0) | level |

- **Is your order found? No,** under any setting. Part 1 says why.
- **Board 3, scored by its average, passes,** though only just: the average level pick is 4.6 behind the best turn
  known.
- **The full form fixes two boards and breaks one.** With it the offence on "shoot now or play on 4" expects a
  defence that Steals more, and picks a worse turn.
- **The plain form gains one board and breaks none.** In self-play it is level with the default on every measure.
  Head to head it leans behind (below). One board gained and a backstop leaning the other way is not a clear
  improvement, so it is off.

**The backstop head to head,** All-Star, 80 paired possessions under the new rules, the plain form against the
default: 1.8 points a pair behind (4.2 behind to 0.6 ahead); 15 won, 22 lost, 43 level. Two batches of 40 with
dice of their own gave 1.7 and 1.9 behind. I stopped at 80: the answer was not going to turn into a clear gain.

## Part 4: the recheck

All-Star self-play, 160 possessions, beside 18j's default.

| | Step 18j | This step's default | `keep_in_hand` `'moves'` | `keep_in_hand` full |
|---|---|---|---|---|
| Points a possession | 26.9 (25.1 to 28.7) | 27.8 (26.2 to 29.4) | 27.4 (25.8 to 29.1) | 24.9 (22.9 to 26.9) |
| Steals tried a possession | 0.60 | 0.69 | 0.72 | 1.21 |
| Steal fouls a possession | 0.25 | 0.34 | 0.36 | 0.61 |
| Ball lost, in 100 phases kept | 17 (12 to 24) | 13 (9 to 20) | 14 (9 to 21) | 27 (20 to 36) |
| Shots in phase 1, 2, 3, 4 and later, in 100 | 49, 33, 15, 4 | 41, 46, 9, 5 | 46, 37, 9, 8 | 52, 37, 12, 0 |
| Shots contested, in 100 | 30 (23 to 38) | 36 (29 to 44) | 34 (26 to 42) | 37 (29 to 46) |
| ... soft, hard | 18, 12 | 24, 12 | 18, 15 | 21, 16 |
| Threes contested, in 100 | 21 (14 to 30) | 26 (18 to 35) | 25 (17 to 35) | 28 (20 to 39) |

- **The default against 18j:** nothing moved clear of chance. Steals and steal fouls are up a little, as you would
  expect with the price gone.
- **The full form is a different game:** twice the Steals, twice the ball lost, 3 points fewer a possession.

**Speed.** The time to finish 1 pair on 9 decisions in 10, in seconds, two rounds each, 18j's code timed in turn
with this step's.

| Setting | Level | Target | 18j's code | This step |
|---|---|---|---|---|
| The default | Rookie | 0.3 | 0.24, 0.22 | 0.29, 0.24 |
| | Starter | 1.0 | 0.86, 0.85 | 0.91, 0.78 |
| | All-Star | 2.5 | 1.73, 1.61 | 2.14, 1.58 |
| `keep_in_hand` `'moves'` | Rookie | 0.3 | 0.25, 0.21 | 0.21, 0.25 |
| | Starter | 1.0 | 0.82, 0.77 | 0.84, 0.70 |
| | All-Star | 2.5 | 1.58, 1.49 | 1.72, 1.62 |
| `keep_in_hand` full | Rookie | 0.3 | 0.24, 0.28 | 0.19, 0.21 |
| | Starter | 1.0 | 0.72, 0.81 | 0.72, 0.74 |
| | All-Star | 2.5 | 1.68, 1.61 | 1.52, 1.79 |

- **Every setting is inside every target.** The differences from 18j's code are inside the round-to-round swing.
  The first round of the default ran beside the test run, which is the 2.14.

## Compute

Estimate 10.0. Hard limit 12. **Used: 10.2.**

| Run | Estimated | Used | |
|---|---|---|---|
| The set replayed, first try | | 2.75 | lost to a machine restart 41 minutes in |
| The set replayed in batches | 2.6 | 1.22 | every candidate 16 times, the positions the gate turns on 32 |
| Board 3: every level turn played out | 1.5 | 1.34 | |
| Self-play, 4 runs of 160 | 2.1 | 2.43 | one more run than planned: the plain form |
| Searches, and timing where the search spends its time | 0.7 | 0.21 | |
| The backstop head to head, 80 pairs | 0.9 | 0.59 | |
| Speed | 0.6 | 0.33 | |
| Agreement checks, tests | 1.6 | 1.34 | |

- **The restart.** The first replay ran as one 50-minute job that kept its results in memory. Everything after it
  ran in small batches that save as they go.

## Changes to the printed game

None. `RULES_CURRENT.md` now says the +5 on a steal foul is the table's alone.

## What changed

- **`playmaker_engine` and `engine.js`:** no +5 on a penalty steal foul under `rules.fiba_steal_foul`; the foul
  table prices the penalty without it; `search.keep_in_hand`.
- **The app:** the default foul situation; the line for a penalty steal foul; the rule reminder.
- **`ai_profiles.json`:** `keep_settled` on; `keep_in_hand` off, with a note of what the gate found.
- **`DECISIONS.md`** D-181 to D-183; the rules register and `RULES_CURRENT.md`.
- **Tools:** `tools/step_18k.py`; `tools/sense_18h.py` replays under these rules (`answers_18k.json`) and scores a
  level pick by its average.
- **Tests:** `tests/test_foul_price_18k.py` (8 tests). Three older tests now state D-181.

## What it proves

- **The two engines agree.** With the rules on: 200 positions and 12 searches; with `rules.zone` on as well, 200
  positions and 8 searches; 100 positions with a broken zone and 4 searches; 200 shot reactions. With
  `keep_in_hand` `'moves'`: 100 positions and 12 searches. With the full form, `dice_in_hand` and `ball_loss` all
  on: 60 positions and 12 searches. No differences.
- **Tests, the 24 named files:** 423 passed, 11 expected failures, 1 expected failure that now passes, 1 failed.
  The 11 browser tests pass. `tests/test_rules_current.py` passes with `RULES_CURRENT.md` regenerated.
  - **Failed, as since 18f:** the timing test. Not loosened.
  - **Exam position 10 passes** with its answer updated (D-183). Position 16 passes again.
  - **Three tests stated the +5 in the app's penalty** and now state D-181: one each in `test_contest_18j.py` and
    `test_step6.py`, and the check of printed numbers in `test_rules_current.py`, which now covers a number the
    table alone plays by. The table's side of each is untouched.
- **What it does not prove:** how a person plays under these rules. And the set's answers under the new rules rest on
  16 play-outs for most candidates, 32 on the positions the gate turns on.

## Noticed, not touched

- **On board 3 the computer's second action does harm.** Turns that stop after one action play 3.5 points better
  than the same turns left open for a second.
- **Board 8 still misses,** as it has since 18j.
- **The timing test still fails** as it has since 18f. Not loosened.
- **Level picks are averaged on board 3 only.** About 14 of the 19 positions have a pick among level turns. Playing
  them all out would cost about 6 core-hours.
- **The two numbers that price a foul** (0.25 fouls a possession, 26.9 a possession) are 18j's. This step measured
  0.34 and 27.8. I left them: decision 1 will change what they mean.

## For Shaun to decide (three)

1. **Give the penalty a price.** *Recommend: in the app, score the penalty's two free throws at 3 times the
   free-throw rating, where today it is 2 times.* Why: that makes them worth about one and a half possessions, the
   ratio you gave for basketball, so a team in the penalty stops reaching and a foul before it has a cost. It does
   mean a penalty free throw scores more than its chance of going in.
2. **The full shortlist form (`keep_in_hand` true), and `dice_in_hand`.** *Recommend: leave both off until decision
   1 is in, then gate them again.* Why: they let the defence see its Steals, which is right, but with a free foul
   that means a Steal every possession.
3. **What the next step is.** *Recommend: decision 1 first, then the zone retest; the defence's third turn of
   look-ahead after that.* Why: the foul price changes how every possession plays, so anything measured before it
   would have to be measured again.

## Model for the next step

Claude Fable 5.2, effort high. A small rules change in both engines, then the gate and self-play again.
