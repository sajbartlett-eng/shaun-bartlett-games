# Step 18f: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine.

## Estimate: about 30 core-hours

| Part | Core-hours | Why |
|---|---|---|
| 1. One-action turns: pilot (12 defence and 24 offence positions, two settings), a head to head up to 400 pairs | 6 | the pilot 1 a pass on defence; the head to head 3 to 4 |
| 2. Equal turns: how often the top is a tie, the build, boards 2 and 10, a head to head | 5 | |
| 3. Unused actions: the build, three sense checks, a head to head | 6 | a sense check is about 0.5 |
| 4. The offence's pilot again | 0.3 | 0.24 at step 18e |
| 5. The open list for the Rookie and Starter: speed, then the levels' order (80 pairs each) | 2 | |
| 6. The map refit: self-play at each level, the fit | 4 | |
| 7. The end: a head to head up to 400 pairs, the boards, self-play, speed | 6 | |

Stop rules: each part stops at its pilot if its value doesn't show. A head to head stops when its sequential test
gives a verdict (after at least 160 pairs), or at 400 pairs.

## 1. Part 1's pilot: `search.whole_turns` on 18e's 12 defence and 24 offence positions

- One pass with the switch on (the default's own choices are 18e's, and are valued in this pass too). Cost: about 1.
- **What the default's choices are worth once the other side has replied:** on defence, about half of them are no
  longer the best turn found, and they sit about 1 point behind it on average. On offence, little: under 0.3.
- **With the switch on:** the choice is the best turn found on 9 or more of the 12 defence positions and 17 or more
  of the 24 offence positions.
- A worry, seen on the EB3F5B position before the run: the offence's replies inside the search miss "move, then
  shoot" when the move isn't one of its three best first actions. With the switch on the defence's turns are judged
  against those replies, so a turn that leaves a sidestep open can read too well.
- **Result (part 1's pilot):** 1.16 core-hours. **The measure can't judge the switch.** With the switch on a
  one-action turn is valued as "this action, then stop", which is the least it is worth, so the default's
  one-action choices look worse than they play (the computer plays one action, then decides again). By its own
  values the switch's choice is the best turn found on 9 of 12 defence positions (0.8 points left, -0.05 to 1.66)
  and 16 of 24 offence positions (1.08 left, 0.08 to 2.07): no better than the default's 9 of 12 and 17 of 24 by
  its own. The head to head is the test.

## 2. Part 1's head to head: `search.whole_turns` against the default, up to 400 pairs

- Cost: about 3.
- I expect a small gain, +0.5 to +1.5 a pair, and the sequential test to need most of the pairs. The risk named
  above (the offence's replies miss "move, then shoot") could cancel it.

## 3. Self-play for the looks reading's map: the All-Star, 240 possessions, whole turns on

- Cost: about 1.5. Run beside part 1's head to head, so both take longer on the clock.
- I expect the looks reading to sit below today's reading on a third to a half of positions (where the phase
  table's floor is what today's reading returns), and a straight line fitted to it to have a slope of 0.15 to 0.3,
  like today's map. Held-out error: within 0.1 of today's reading refit, either way.
- **Result (the self-play for the looks map):** 2.97 core-hours (it shared the machine). 240 possessions, 3,935
  positions; 29.4 points a possession; the ball lost 7.7 times in 100 phases kept.
  - **Wrong on how often the floor decides:** the looks reading is below today's reading on 9 positions in 10 or
    more (every position with the defence to act in phases 1 and 2). Today's reading is the phase table's value
    nearly everywhere.
  - Right on the slope (0.08 to 0.29) and on the error: 8.79 for the looks map against 8.79 for today's reading
    refit; the map in the file now gives 9.35.
  - **Neither reading tells much about what a position goes on to earn:** a flat average for each phase and side
    gives 8.84. The outcome is mostly the dice and later play.
  - The All-Star shoots early, so there are too few late positions: the looks map has lines for phases 1 to 4 only.
    Self-play at the Rookie and Starter is added for the later phases.
- **Result (part 1's head to head):** 7.55 core-hours (it shared the machine with the self-play; alone it is about
  4.5). 400 pairs: **+1.7 points a pair (0.3 to 3.1),** 155 wins, 137 losses, 108 ties. Inside the predicted range,
  a little above it. The sequential test gave no verdict; the interval is clear of 0. On offence it loses the ball
  less (11.1 times in 100 phases kept against 17.6).

## 4. Part 3's head to head: the looks reading and the control-aware cover against the default, up to 400 pairs

- The default here is whole turns on and today's reading with its map refit on the same 800 possessions the looks
  map is fitted on (an early refit, so that the looks reading isn't helped by a fresher map).
- Cost: about 4.5.
- I expect no clear difference: between -1 and +1.5 a pair. The looks reading predicts what positions go on to earn
  only a shade better than today's (held-out error 11.08 against 11.11), and on the closeout board the offence's
  best reply is to pass out of the corner, so the Move kept doesn't change the value there.
- **Result (part 3's head to head):** 5.91 core-hours. 400 pairs: **+0.8 points a pair (-0.8 to 2.4),** 126 wins,
  131 losses, 143 ties. Inside the predicted range: no clear difference. It led by 2.3 (0.1 to 4.6) at 240 pairs and
  fell back, so the early lead was the dice. **Both switches stay off.**

## The estimate, revised after part 3: about 42 core-hours

A 400-pair head to head costs about 6, not the 3 to 4 I allowed, and the looks reading needed self-play at all
three levels (6) that the first estimate didn't have. Spent so far: about 21. Still to come: part 2's head to head
(6), part 4's pilot (0.3), part 5 (2.5), self-play at each level for the last refit (5, the All-Star's also serving
part 7), part 7's head to head (6) and boards (0.2).

## 5. Part 2's pilot: `search.split_ties` on the 218 stored positions and the 19 boards

Under 30 minutes, so no prediction was owed. Results:

- The first turn reads exactly the same as another on 76 decisions in 100 today (70 to 81), 7.6 turns on average.
  With the switch, 54 in 100 (48 to 61) still can't be told apart after the other side's next-best replies are
  compared, 3.7 turns on average.
- The same position decided twice with the All-Star's pick noise: the first action differs 58 times in 100 today
  (54 to 63), 12 in 100 with the switch (9 to 14).
- The 19 boards at 1 pair: 9 passed today, 11 with the switch (boards 6 and 16 gained). Board 10 passes both ways;
  board 2 fails both ways with the same turn ("X2 moves to C7, then X1 tries a Steal").

## 6. Part 2's head to head: `search.split_ties` against the default, up to 400 pairs

- Cost: about 6.
- I expect a small gain, 0 to +1.5 a pair, and no sequential verdict. The switch takes chance out of the choice
  between turns that read the same; the turn it prefers leaves the other side worse second choices, which matters
  only when the other side's own pick noise sends it off its best reply.
- **Result (part 2's head to head):** 6.0 core-hours. 400 pairs: **149 won, 111 lost, 140 tied: 57 in 100 of the
  decided pairs (51 to 63).** In points, +1.2 a pair (-0.3 to 2.7): inside the predicted range, and its interval
  just reaches 0. No sequential verdict. **Turned on:** it won more pairs than it lost, clear of chance, and it does
  what the part asked (chance no longer chooses between equal turns). The points gain alone would not have been
  enough; that is said in the report.

## 7. Part 3 again: `eval.kept_actions` alone against the default, up to 400 pairs

- Why: with the map refit, the control-aware cover alone gives the expected answer on the closeout board (the Quick
  Step closer reads 1.25 better than the Move closer, where the default reads them level). Its first head to head
  was as a pair with the looks reading, so the switch that passes the test has not been measured alone.
- The default here: whole turns and the tie splitter on, the refit map.
- Cost: about 6.
- I expect no clear difference again, between -1 and +1.5 a pair: the switch changes the reading only where a
  defender's last movement was a Quick Step or a Sprint and he is the one covering the look.
