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
