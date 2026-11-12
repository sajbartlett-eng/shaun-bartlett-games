# Step 18f report: the computer's judgement, now that it sees every move

## First: speed, and what this step cost

- **Every level fits its target at the speed the machine ran at step 18e.** The machine ran about 30% slower
  today, and at today's speed the Rookie and the Starter sit on their targets, some rounds over. Step 18e's own code,
  timed again today, does the same. The Speed section has both sets of numbers; section 4 asks you which yardstick
  counts.
- **The step used about 52 core-hours against the 30 I estimated.** A 400-pair head to head costs 5 to 6, I ran
  seven of them, and two were for switches the first estimate didn't have.
- **Six switches were built. Two won their head to head and are on. Four are off.**

## In plain words: what the computer now judges better, and what it still can't

**What it judges better:**

- **A turn is judged after the other side has replied.** Before, a one-action turn was judged with the computer's
  own second action still to come, so it looked better than it was.
- **When turns read the same, evidence chooses, not chance.** The computer looks at the other side's second-best
  reply, then its third, and takes the turn that leaves the worst of them. Asked the same position twice, it now
  plays the same first action about 9 times in 10. Before, 4 times in 10.
- **Every level defends the same way.** The Rookie and the Starter are on the open list. Levels now differ in how
  many turns they read and in their pick noise, as D-157 asks. They stay in order.
- **It passes 12 of the 19 boards,** where it passed 8.
- **It beats the computer from the start of this step:** 168 pairs won to 127 lost.

**What it still can't do:**

- **See a Move kept.** On the closeout board your order (Quick Step closer, keep the Move) holds the offence to
  20.5 points; the computer's order (Move closer) gives up 26.1. The computer still reads the two as level.
- **Tell apart positions that read below the average.** This is the cause underneath. Early in a possession the
  reading returns the phase's average whenever the looks read lower, which is 9 positions in 10. So most defence
  turns read exactly the same number. That one floor is behind the Move it can't see, the ties that are left, and
  second actions it throws away.
- **See "move, then shoot" in the other side's reply,** about 1 time in 10. On your game EB3F5B it went back to the
  Quick Step closer, which a sidestep beats.
- **Contest as many shots as it did.** In All-Star self-play 23% of shots are contested, where 40% were at
  18e. The offence has learned to step away from a closeout faster than the defence has learned to expect it.
- **It shoots earlier than it did:** 6 shots in 10 in phase 1, where 4 in 10. That came with the last map refit
  (part 7), not with the switches.
- **The offence's list is still hand-written.**
- **And a limit of mine:** a 400-pair head to head can't see a gain under about 1.5 points a pair. Three of the four
  switches left off may be small gains. Section 4 proposes a sharper test.

## Part 0: rulings

- **Step 18e is merged** (pull request 66). D-157, D-158 and D-159 are recorded in `DECISIONS.md`.

## Part 1: a one-action turn judged after the other side's reply (`search.whole_turns`): on

- **`quiet_points` no longer fits,** so I built a plainer form. A one-action turn is valued as the turn ended there:
  the side's own End turn is played, and the other side has its reply before the position is judged.
- **The pilot couldn't judge it** (`regret_whole_turns.json`). The regret method values a one-action turn as "this
  action, then stop", which is the least it is worth, so it marks the old default down for the very thing being
  fixed. By its own values the switch's choice is the best turn found on 9 of 12 defence positions and 16 of 24
  offence positions; the old default had 9 and 17 by its own. I went to the head to head.
- **The head to head** (`h2h_whole_turns.json`, All-Star, 400 pairs):

| | Result |
|---|---|
| Points a pair | **+1.7 (0.3 to 3.1)** |
| Pairs won, lost, tied | 155, 137, 108 |
| The ball lost on offence, per 100 phases kept | 11.1 (8.4 to 14.6) against 17.6 (14.0 to 21.7) |

- **Turned on.**
- **Its cost in speed was more than I first said.** I reported about 7% at the pilot. Timed properly it is 15 to 30%
  on the time to finish 1 pair, because the position after a one-action turn is now the other side's full list. Two
  speed-ups that change no result pay for it (see Speed).

## Part 2: turns that read exactly the same (`search.split_ties`): on

- **How it separates them.** Turns that read the same share the other side's best reply. So the computer compares
  the other side's second-best reply, then its third, and so on, and takes the turn that leaves the worst of them.
  That is evidence the search already has; nothing about kinds of move. Turns that still tie share one draw of the
  pick noise, so chance no longer picks between them.
- **How often the first turn is a tie** (218 stored positions, 1 pair ahead, no pick noise; `ties_*.json`):

| | The first turn reads the same as another | Turns level with it |
|---|---|---|
| Start of the step | 79 in 100 (74 to 84) | 9.6 |
| With whole turns | 76 in 100 (70 to 81) | 7.6 |
| With the tie splitter | **54 in 100 (48 to 61) still can't be told apart** | 3.7 |

- **The same position decided twice** (the All-Star's pick noise): the first action differed 58 times in 100
  before (54 to 63), **12 in 100 now** (9 to 14). With no pick noise the search gives the same turn every run, before
  and after; before, that turn was only the first one listed.
- **Boards 2 and 10:** board 10 now passes. Board 2 still fails: the computer steps next to the ball handler and
  tries the Steal where the board wants the sag. That is no longer a tie, it is the computer's view.
- **The head to head** (`h2h_split.json`, 400 pairs):

| | Result |
|---|---|
| Pairs won, lost, tied | **149, 111, 140: 57 in 100 of the decided pairs (51 to 63)** |
| Points a pair | +1.2 (-0.3 to 2.7) |

- **Turned on, and I want you to see on what.** It won more pairs than it lost, clear of chance. Its points gain
  alone is not clear of 0. I counted the pairs because the switch's job is to stop chance choosing, and it costs
  nothing in speed. If you want the stricter points test, it goes off (section 4).

## Part 3: what a player's unused actions are worth: built, measured, off

**What I found first.** The reading already tells a Move kept from a Quick Step kept, in its looks: on the closeout
board the three is worth 15 after the Quick Step closer and 21 after the Move closer. Two things hid it:

- **The cover's own re-read didn't know the control rule.** It read a moved defender's Contest with his old control
  state.
- **The floor.** Today's reading returns the phase's average whenever the looks read below it. Anything a kept
  action changes below the average is invisible.

**What I built,** each behind its own switch, no worth set by hand for any action:

- **`eval.kept_actions`:** the cover reads each defender's Contest with the control state his action leaves him
  (set after a Move, rushed after a Quick Step or Sprint), for both sides.
- **The looks reading** (a second reading mode in the `eval` block, with its own map): the best look itself, without
  the floor.

**The head to heads** (All-Star, 400 pairs each):

| Switch | Points a pair | Pairs won, lost, tied | Decision |
|---|---|---|---|
| Both together (`h2h_looks.json`) | +0.8 (-0.8 to 2.4) | 126, 131, 143 | off |
| `eval.kept_actions` alone (`h2h_kept.json`) | 0.0 (-1.6 to 1.6) | 107, 122, 171 | off |

- The pair led by 2.3 (0.1 to 4.6) at 240 pairs and fell back. The early lead was the dice.
- **The looks reading predicts what a position goes on to earn only a shade better** than today's: held-out error
  11.08 against 11.11 on 19,901 positions. A flat average for each phase and side does nearly as well. What a
  possession earns is mostly the dice and later play.

**The three tests** (`lines_*.json`; nothing was told to the computer):

| Test | Expected | The final default | With `eval.kept_actions` |
|---|---|---|---|
| Closeout, the shooter can't move | keep the Move | **no:** X3 Moves closer, X2 moves to B6. It reads the Quick Step closer as level | a Quick Step closer, but to E3, not E4 |
| Closeout, the shooter can move | the Move closer | **yes:** X3 Moves closer, X1 Quick Steps | yes |
| Game EB3F5B, the pass in the air | the Move closer (18e) | **no:** X4 Quick Steps to E4 | no |

## The sense checks

Both moves played out by the rules 160 times each with the same dice, the All-Star on the final default on both
sides (`sense_checks.json`). The number is what the offence went on to score.

*1. The closeout board, the shooter can't move.* O4 (three 11) has the ball at A3. X3 is at F4.

| The defence's turn | Offence scored | Against the computer's |
|---|---|---|
| The computer's: X3 Moves to C4, then X2 moves to B6 | 26.1 (24.1 to 28.1) | |
| **Your order: X3 Quick Steps to E4, then X2 moves to B6** | **20.5 (18.1 to 22.9)** | **5.6 better** (2.4 to 8.7) |
| X3 Quick Steps to E3, then X2 moves to B6 (`eval.kept_actions`' choice) | 27.1 (25.1 to 29.0) | 1.0 worse (2.1 better to 4.1 worse) |
| X3 Quick Steps to E4, then the computer chooses the rest | 32.4 (29.7 to 35.1) | 6.4 worse (3.1 to 9.6) |
| Nothing | 31.7 (29.9 to 33.4) | 5.6 worse |

- **My view: your order is right, and by more than 18e showed.** Two things matter here and the computer sees one.
  - It sees that X2 must cover O2, because the offence passes out of the corner rather than shoot over X3.
  - It doesn't see that X3 should keep his Move. With X2 in place either way, the Move kept is worth 5.6 points.
- **The fourth row is the same weakness from the other side.** After your Quick Step the computer reads four second
  actions as level and moves X1, which helps nothing. O2 is left free and the offence passes to him.
- **`eval.kept_actions` finds a Quick Step closer but the wrong square,** and by play it is no better than the
  default.

*2. Game EB3F5B, the pass to the corner in the air.* X4 is at F4.

| The defence's first action | Offence scored | Against the computer's |
|---|---|---|
| The computer's: X4 Quick Steps to E4 | 33.0 (every play-out) | |
| X4 Moves to C4, facing him | 30.4 (30.3 to 30.6) | **2.6 better** (2.4 to 2.7) |
| The defence Pauses | 33.0 (every play-out) | level |

- **My view: the computer is wrong here, and I know why.** It reads its Quick Step as 28.6. The true value is 33:
  the shooter sidesteps to A2 and shoots open, and the computer's picture of the offence's reply doesn't hold that
  turn (part 4). Step 18e's computer chose the Move closer; whole turns lost it.

## Part 4: the offence ranks good moves too low: the cause found, a fix built, off

- **Parts 1 to 3 fixed the ranking at the offence's own turn.** On 18e's 24 offence positions with whole turns on,
  the choice is not the best turn found on 8. The reading now ranks the better turn 1st on four of them and 6th and
  7th on two; at 18e it was 38th, 55th and 136th. What is left is the hand-written list: on 6 of the 8 the better
  turn's first action is never offered.
- **But whole turns opened the same fault one level down,** and your game showed it (sense check 2).
- **The term that puts it low, in plain words:** with whole turns, each first action is ranked as if the turn
  stopped there, and only the best three are followed by a second action. "O4 moves to A2" alone is worth little,
  so "moves to A2, then shoots" is never looked at.
- **How often** (`tools/reply_miss_18f.js`, 145 stored offence positions): the reply list misses the best reply the
  wider list at the computer's own turn finds on 19 positions, by 10 points or more on the worst. Every one is a
  "move, then shoot".
- **The fix (`search.rank_in_hand`, off):** first actions are ranked, and the ones to follow chosen, by the reading
  with the second action still in hand. The turn itself is still valued whole. It recovers 13 of the 19 at no extra
  reads. Nothing names a kind of move.
- **Its head to head** (`h2h_in_hand.json`, 400 pairs): **+0.9 points a pair (-0.7 to 2.4),** 139 won, 125 lost,
  136 tied. Not clear, so by the step's rule it is off.
- **What it does and doesn't mend.** With it the computer reads the EB3F5B closeouts truly (33 after either, because
  a sidestep beats both). It then has nothing to choose between them and still plays the Quick Step. So it mends the
  reading there, not the move.
- **In All-Star self-play with it on** (200 possessions, `fidelity.json`): 30% of shots are contested (23 to 37)
  against 23% without (17 to 30), and the offence scores 27.3 points a possession (25.7 to 28.9) against 27.8. The
  direction is right; the intervals overlap.

## Part 5: the open list for the Rookie and the Starter (D-157): done

- **Every level now defends from the open list.** The hand-written defence list is no longer any level's default.
- **How it fits.** Nothing was cut by kind of move:
  - the levels differ in how many turns they read in full and how many first actions they follow: the Rookie 2 and
    1, the Starter 4 and 2, the All-Star 8 and 4 (untouched);
  - two speed-ups that change no result (see Speed).
- **The levels stay in order** (80 pairs each, each level's own pick noise; `h2h_order_*.json`):

| | Points a pair | Pairs won, lost, tied |
|---|---|---|
| All-Star over Starter | **+12.2 (8.3 to 16.2)** | 43, 19, 18 |
| Starter over Rookie | **+8.6 (4.3 to 12.9)** | 38, 27, 15 |

- **The open list changes how the lower levels play.** Against their own level they now lose the ball twice as
  often (15 times in 100 phases kept, where 7), because their defence steps in and Steals as the All-Star's does.
  The Rookie scores 21.3 points a possession against itself (19.2 to 23.4), where 26.4.

## Part 6: the map refit

- **Refit twice, as the prompt allows.** Early, on play with whole turns, so part 3's new reading wasn't helped by
  a fresher map. And last, on play from the final default: the All-Star 200 possessions, the Rookie 240, the
  Starter 200 (15,260 positions; `fit_trace_app_final_r_final_s.json`). The same form as 17D.
- **Held-out error on the final default's play: 14.2,** where the early refit's map gave 14.4. It is higher than
  18e's 10.8 because the lower levels now lose the ball more, and a possession that ends at 0 is far from any
  reading. On the Rookie's play alone the refit takes it from 16.0 to 15.0.
- The looks reading's map is refit on the same play, so the switch stays usable.

## Part 7: the re-measure on the final default

The final default: whole turns, the tie splitter, the open list at every level, the refit map.

**Head to head against the start of the step** (`h2h_final.json`, All-Star, 400 pairs). The other side is 18e's
default: the old map, this step's switches off. I checked it against 18e's own code, search for search: identical.

| | Result |
|---|---|
| Pairs won, lost, tied | **168, 127, 105: 57 in 100 of the decided pairs (51 to 63)** |
| Points a pair | +1.2 (-0.3 to 2.6) |
| Points a possession | 27.3 against 26.1 |

- It wins more pairs, clear of chance. The points gain is not clear of 0, and is below the +2 to +4 I predicted:
  the two switches' gains don't add up.
- **On offence the final default lost the ball more than the old one did:** 21.3 times in 100 phases kept (17.0 to
  26.4) against 16.3 (13.0 to 20.2). Part 1's head to head went the other way (11.1 against 17.6). It still scored
  more. I haven't traced which decisions changed; that is the first job of the next step's sharper test.

**The 19 boards at 1 pair** (`exam_final_fixed.json`): **12 pass, where 8 did.** Boards 6, 10, 11 and 16 are gained;
none is lost.

**Six boards move by move** (`boards.json`, and the exam's choice for 2 and 10):

| Board | The computer's turn | Against the board |
|---|---|---|
| 1 | X2 Quick Steps to D6, then X5 moves to O3 | fails. Doing nothing reads 0.9 worse; the straight drive is still worth more than the next look |
| 2 | X3 Quick Steps to N7, then X1 tries a Steal | fails. The board wants X2 to sag to C7 or D7 |
| 3 | X2 Quick Steps to D6, then nothing | fails. It reads the board's early help as 4.4 to 5.7 worse than doing nothing (1.6 to 2.1 at 18e) |
| 8 | O2 cuts to E10, then O1 passes to him | fails, narrowly: the cut and the pass, but the board wants the cut to the rim (D7), which reads 0.9 behind |
| 9 | O1 Quick Steps to K4, then O2 Quick Steps to B8 | fails. The kick-out reads 3.8 behind; the corner man relocating 5.5 behind, and still isn't on the list |
| 10 | X2 moves to C7, then X4 tries a Steal | **passes** |

**Self-play, All-Star, 200 possessions** (`fidelity.json`), beside 18e's final default:

| | 18e's final default | The final default |
|---|---|---|
| Points a possession | 26.8 (25.1 to 28.4) | 27.8 (26.1 to 29.6) |
| Possessions that end with the ball lost | 29 of 200 | 29 of 200 |
| The ball lost, in 100 phases kept | 14.2 (10.1 to 19.7) | 21.5 (15.4 to 29.1) |
| Shots in phases 1 and 2 | 76% | **89%** |
| Shots by phase, 1 to 6 | 40, 36, 19, 4, 2, 1% | **60, 29, 9, 2, 1, 0%** |
| The clock runs out | 0 of 200 | 0 of 200 |
| Shots taken rushed | 13% (9 to 19) | 11% (7 to 17) |
| Shots contested | 40% (33 to 48) | **23% (17 to 30)** |
| Contests after a Move | 62% (51 to 73) | 62% (46 to 75) |
| Contests after a Quick Step, after a Sprint | 22%, 14% | 23%, 8% |
| Contests that draw a foul | 16% (9 to 26) | 33% (21 to 49) |
| The map's error | 10.8 (9.2 to 12.4) | 11.9 (10.3 to 13.5) |

- **The ball is lost on the same number of possessions.** The rate for each phase kept rose only because
  possessions are shorter.
- **It shoots earlier: 6 shots in 10 come in phase 1.** Before the last refit it was 4 in 10
  (`fidelity_fit_run.json`), as at 18e. The cause is the map. It is fitted on all three levels' play, as at 17D, and
  the lower levels now lose the ball often, so the map reads waiting as worth less for every level.
- **Fewer shots are contested.** The offence steps away from a closeout and the defence doesn't expect it (part 4).

## Speed

The time to finish 1 pair on 9 decisions in 10, in seconds, on the 22 hand-board decisions. **The machine's speed
changed through the day,** so each round times step 18e's code and this step's in turn
(`speed_final_beside_18e.json`, 4 rounds).

| Level | Target | 18e's code, at 18e | 18e's code, today | The final default, today | The final default at 18e's speed |
|---|---|---|---|---|---|
| **Rookie** | 0.3 | 0.23 (its old list) | 0.27 to 0.35 | 0.27 to 0.35 | **about 0.23** |
| Starter | 1.0 | 0.64 to 0.69 (its old list) | 0.89 to 0.94 | 0.93 to 1.09 | **about 0.75** |
| All-Star | 2.5 | 1.99 to 2.02 (the open list) | 2.42 to 2.67 | 2.13 to 2.20 | **about 1.7** |

- **The Rookie with the open list is as fast as the Rookie was on its old list.** The Starter is about 13% slower
  than it was, and the All-Star about 16% faster.
- **At today's speed the Rookie is over its target on 2 rounds of 4 and the Starter on 3 of 4.** So is the Rookie on
  18e's own code. I haven't trimmed them further; section 4.
- **At the assumed phone speed** (4 times slower than 18e's machine): the Rookie 0.9 s against 1.0, the Starter
  3.0 s against 2.0, the All-Star 6.8 s against 3.0. The Starter and the All-Star were over before this step.
- **Two speed-ups that change no result** (654 whole searches each, at three levels, none different):
  - the chance a pass arrives is read without building the parts per defender that only a few squares ever use
    (about 20% off the Rookie's time);
  - only the six looks kept for each attacker are built in full (5 to 12% more).
- A third idea saved nothing and was taken out.

## Compute against the estimate

Estimate: 30 core-hours, revised to 42 and then 56 as runs were added. Used: about 52.

| Run | Predicted | Used | Against the prediction |
|---|---|---|---|
| Part 1's pilot | 1; the switch's choice best on 9 of 12 and 17 of 24 | 1.2 | the method couldn't judge the switch |
| Part 1's head to head | 3; +0.5 to +1.5 | 7.6 | right, a little above: +1.7. It shared the machine |
| Self-play for the looks map, three levels | 1.5 | 6.1 | **wrong on the floor:** it decides 9 positions in 10, not a third to a half |
| Part 3's head to head, the pair | 4.5; no clear difference | 5.9 | right: +0.8 |
| Part 2's head to head | 6; 0 to +1.5, no verdict | 6.0 | right: +1.2 |
| `eval.kept_actions` alone | 6; no clear difference | 4.8 | right: 0.0 |
| `search.rank_in_hand` | 6; +0.3 to +2 | 4.8 | inside it, not clear: +0.9 |
| The levels' order | 2 | 1.2 | |
| Self-play on the final default, three levels | 6; the map's error unchanged | 2.4 | **wrong on the map:** the lower levels lose the ball twice as often |
| Part 7's head to head | 5; +2 to +4 | 4.1 | **wrong on the size:** +1.2 |
| The sense checks | 1 | 1.3 | |
| The last self-play, with and without `rank_in_hand` | | 1.9 | |
| Speed, the speed-ups' proofs, ties, boards, agreement checks, tests | 2 | about 5 | the machine's speed had to be measured too |

- **What I'd do differently:** I ran the pair of part 3's switches before either alone, and built `rank_in_hand`
  late, after its cause showed up in a test I had mislabelled. Both cost a head to head each.

## 1. Changes to the printed game

None. Nothing in this step touches the rules or any printed page.

## 2. What changed

- **Step 18e is merged.** D-157 to D-159 are recorded.
- **On by default:** `search.whole_turns`, `search.split_ties`, the open list for the Rookie and the Starter
  (`profiles.<level>.open_list`, with each level's own `open_full` and `open_follow`), and the refit map.
- **Built and off:** `eval.kept_actions`, the looks reading and its map, `search.rank_in_hand`.
- **Both engines:** `search.py`, `decide.py` and `agent.py` in Python; `engine.js` for the app. The two speed-ups
  are in `engine.js` only, behind `SPEED.lane_p` and `SPEED.look_lazy`; they change no value.
- **`learned_weights.json`:** the map refit; a second map for the looks reading. The learned weights are untouched.
- **Tools:** `tools/step_18f.py` (every run in this report), `tools/reply_miss_18f.js`, and the new switches in the
  play-out, line, diagnosis, exam and agreement tools. The line tool now shows the engine's own choice and the
  other side's replies.
- **Never deleted:** `quiet_points` and the hand-written defence list are still in the code, off.

## 3. What it proves

- **The two engines agree,** 0 mismatches in every run:
  - the final default: 600 positions and 4 whole searches, and 300 shot reactions;
  - the open list forced on for the defence: 300 positions, 130 open lists turn for turn, 2 whole searches;
  - `eval.kept_actions` with `search.rank_in_hand`: 300 positions and 2 whole searches;
  - the looks reading with `eval.kept_actions`: 200 positions and 2 whole searches;
  - the open list off: 200 positions and 2 whole searches.
- **The speed-ups change nothing:** with this step's switches off and the old map, today's code gives the same
  values in the same order as 18e's code on 20 whole searches at two levels.
- **Nothing names a kind of move** in whole turns, the tie splitter, `rank_in_hand` or the levels' list widths.
- **Tests on the final default** (`test_rules_current`, `test_static`, `test_step3n`, `test_step3m`,
  `test_course_boards` and the golden tests): 88 pass, 13 expected failures, 1 fail.
  - One of 18e's 14 expected failures now passes.
  - The fail is the timing test that sits at its limit: 3.24 s against 1.70 s (2.16 s at 18e). The slower machine
    and whole turns both add to it. Not loosened.

**Three things a coach could say, from the measured positions:**

- "Close out with the Quick Step and keep your Move for the Contest, as long as someone has the pass out covered.
  With X2 on O2 that order held them to 20 points; Move first and it was 26."
- "Don't judge your first action as if your second were still coming. Ask what it leaves them if you stop there."
- "A shooter who has just caught it can step away from a closeout. From four squares off, the Quick Step alone
  doesn't get you there: he sidesteps and it's an open three."

## 4. For Shaun to decide

- **The tie splitter.** I turned it on for pairs won (149 to 111), not for points (+1.2, -0.3 to 2.7). Say if the
  points test is the one that counts, and it goes off. My view: keep it. It is why the computer now gives the same
  answer twice.
- **`search.rank_in_hand`.** It didn't win clearly (+0.9, -0.7 to 2.4), so it is off. It mends a reading error I
  can show on 13 positions in 145, costs no speed, and didn't lose. My view: turn it on. It is your rule to bend.
- **Which speed counts.** The machine's speed moved 30% inside a day, so "the machine the measurements run on" is
  no longer one number. Options:
  - judge every step against 18e's code timed in the same hour, as this report does (my view);
  - hold to the raw number on the day, and I trim the Rookie's and the Starter's lists further;
  - measure a real phone (D-126) and set the budget from that.
- **The floor.** It is the next thing between the computer and your closeout. The looks reading takes it away and
  didn't win as built. Do you want the next step to go at it again? I'd pair it with a sharper test (below).
- **A sharper test than the head to head.** 400 pairs can't see under 1.5 points, and each costs 5 core-hours. The
  sense-check method can: a few hundred positions from play, each candidate turn played out with the same dice. It
  showed 5.6 points on your closeout in half a core-hour. I'd make it the gate for changes to the reading, and keep
  the head to head for the end of a step. Your call, since the gate is your rule.
- **One map or one for each level.** The map is fitted on all three levels' play, as at 17D. Now that the lower
  levels lose the ball often, it pulls the All-Star towards shooting early. My view: fit each level's map on its own
  play. It is a change of form from 17D, so it is yours.
- **The lower levels now Steal.** A new player against the Rookie will lose the ball about as often as against the
  All-Star's style of defence, only with more noise. That follows from D-157. Say if the Rookie should be gentler;
  the honest lever is its pick noise or look-ahead, not a scripted list.

## 5. Noticed, not touched

- **The offence finds open shots faster than the defence expects them.** In self-play fewer shots are contested
  than at 18e. `rank_in_hand` is aimed at exactly this.
- **Board 9's corner man relocating still isn't on the offence's list.** That list is hand-written and out of scope.
- **Board 3's early help now reads 4 to 6 points worse than doing nothing.** The board says help early. Worth a
  sense check of its own.
- **The timing test still sits at its limit,** and the slower machine pushes it further over. Not loosened.
- **The trainer's lists are still the old ones.**
- **The exam book** is untouched.
- **A labelling fault of mine, found and fixed:** for part of the step the line tool ran with whole turns off when I
  thought it was on. No head to head or timing used it; the test tables above are from the corrected tool.

## 6. Model for the next step

Claude Fable 5.2, effort high. The next work is the floor inside the reading and a new test method, in both
engines, where a small change moves every decision and the speed budget.
