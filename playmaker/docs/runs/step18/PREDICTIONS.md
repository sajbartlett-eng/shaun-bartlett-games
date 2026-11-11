# Step 18a: predictions, written before each run

Cap for 18a: about 9 core-hours. Costs are core-hours on this machine (4 cores). Each prediction was written before
its run started; the result is added under it afterwards and the prediction is not edited.

## 1. Rookie, calibrated against its uncalibrated self, 160 pairs (Senior Pro, the app's rules, 1 pair ahead)

- Cost: 0.7.
- Result: a gain, smaller than the All-Star's +3.2, because the Rookie's pick noise (5.0) swamps small differences
  in the reading. I expect +0.5 to +2.5 a pair, and the interval may include zero.
- Shot timing: earlier than its uncalibrated self; the clock runs out less often.
- **Result:** 0.54 core-hours. +4.9 a pair (interval +1.7 to +8.0): above the predicted range, and clear of zero.
  Mean shot phase 3.6 against 4.1. The clock ran out on 3 in 100 for both: the second part was wrong.

## 2. Starter, calibrated against its uncalibrated self, 160 pairs

- Cost: 1.2.
- Result: +1 to +3 a pair.
- Shot timing: earlier; fewer decisions a possession.
- **Result:** 1.06 core-hours. +2.8 a pair (interval +0.4 to +5.2): as predicted. Mean shot phase 2.9 against 4.3;
  32 decisions against 49.

## 3. The order of the levels, calibrated: All-Star against Starter, Starter against Rookie, 80 pairs each

- Cost: 1.1 for both.
- Result: each stronger level ahead. Starter over Rookie by 2 to 6 points a pair (the Rookie's noise is large).
  All-Star over Starter by 0 to 3, and at 80 pairs that interval will probably include zero: the two differ mainly in
  pick noise at this look-ahead.
- **Result:** 0.79 core-hours. Starter over Rookie by 10.0 (interval +6.8 to +13.3): above the range. All-Star over
  Starter by 6.8 (interval +3.6 to +9.9): above the range, and clear of zero, which I said it probably wouldn't be.

## 4. Junior Amateur, the All-Star calibrated (Senior Pro map scaled by the phase table) against uncalibrated, 160 pairs

- Cost: 1.4.
- Result: a gain, +1 to +3 a pair. The risk: the Junior Amateur phase table is built from 16 stored possessions, so
  the scale is rough (0.60 in phase 1 to 0.86 in phases 5 and 6). If the scale is wrong the gain could vanish.
- **Result:** 0.88 core-hours. +1.7 a pair (interval -0.4 to +3.8): inside the range, but not clear of zero.

## 5. The table's rules: today's computer (uncalibrated) playing itself, 200 possessions

- Cost: 1.3.
- The shot-clock expiry rate (a forced shot): 5 to 12 in 100. Step 3n measured 10 in 100 on 60 possessions, with an
  older reading; step 17D measured 3 in 100 under the app's rules.
- Points a possession: lower than the app's 26.5, about 22 to 25, because a turnover costs 5 and play goes on.
- **Result:** 1.26 core-hours. The expiry rate: 9 in 100 (interval 5.8 to 13.8), as predicted. Points: 30.2 (interval
  29.1 to 31.3). **Wrong, and in the wrong direction:** the table's possessions earn more, because a turnover
  doesn't end them and the clock running out still gives a forced shot.

## 6. The table's rules: the calibrated computer (the digital map) playing itself, 200 possessions

- Cost: 0.7.
- The expiry rate: 0 to 2 in 100.
- Shots: 65% to 75% in phases 1 and 2, as under the app's rules.
- The map: under the table's rules a turnover doesn't end the possession, so what is left to earn should be a little
  higher than the digital map says late in the clock. I expect the table's own map to beat the digital map on
  held-out error by a small margin, not clearly: "no material difference".
- **Result:** 0.51 core-hours. The expiry rate: 0 in 200 (interval 0 to 1.9), as predicted. Shots: 73% in phases 1
  and 2, as predicted. The map: **wrong.** The table's own map beats the app's on held-out error clearly (8.26
  against 8.94; the paired gain's interval is clear of zero). Positions at the table go on to earn 29 to 30 at
  every phase; the app's map says 25 to 27. A material difference, so the table's own map is fitted (D-141).

## 7. The 19 boards on the calibrated computer

- Cost: 0.2.
- 9 to 11 of 19 at 1 pair (9 before). Boards 1, 8 and 9 still fail.
- **Result:** 9 of 19 at 1 pair and 10 on the clock, the same counts as before. Board 10 is gained and board 16
  lost. Boards 1, 8 and 9 still fail. As predicted.

## 8. The candidate diagnosis, a full-width search at 1 pair on the persistent boards

- Cost: 1.5.
- I expect the board's move to be legal and in the full list on every board, and, on boards 8 and 9, to be searched
  and lose on value (judgement). On board 1 (the defence against a drive) I expect the board's turns to be cut
  before they are searched (candidates). So a mixed answer, leaning to judgement.
- **Result:** 1.4 core-hours for both passes (the default game, and with `play_on`). A mixed answer, as predicted,
  but not the mix I predicted. Board 9 is candidates, not judgement. Board 8 is judgement, as predicted. Board 1 is
  judgement, not candidates: none of the 350 turns its own reading likes best meets the board. And a full-width
  search wasn't possible: a team turn has 15,000 to 21,000 options on offence and 270,000 to 530,000 on defence, so
  every legal turn was read one team turn ahead and the best 300 searched at 1 pair.

## 9. Added during the diagnosis: what the list leaves out, on positions from play (48 offence, 12 defence)

Written after the boards' diagnosis showed the search's list holding 24 of 15,000 to 21,000 legal team turns on
offence. The boards are 10 hand-made decisions; this asks the same question of positions from play.

- Cost: 0.2 for the offence positions; up to 1.0 for the defence ones (about 500,000 legal turns each).
- By the computer's own 1-pair reading, the search's choice is the best turn found on 30% to 50% of positions.
- Mean regret (the best turn found less the choice): 1.5 to 3 points on offence, more on defence, because the
  defence's list is built from 20 of about 1,000 legal actions.
- **Changed before it finished:** the defence positions were dropped to stay inside the 9 core-hour cap (each costs
  about 8 core-minutes). The offence positions were run twice: the default game, and with `play_on`.

## 10. Under the table's rules, with the table's own map: self-play (200 possessions) and head to head against the app's map (160 pairs)

- Cost: 0.5 for the self-play, 0.9 for the head to head.
- Self-play: the expiry rate stays at 0 to 2 in 100. It shoots a little later than with the app's map (the table's
  map values holding the ball 3 to 4 points higher): 60% to 70% of shots in phases 1 and 2.
- Head to head: the table's own map ahead by 0 to 2 points a pair; the interval probably includes zero. A level
  shift changes only the choice between shooting now and playing on.
- **Result:** self-play 0.98 core-hours, head to head 1.11: **over on cost**, because possessions with the table's
  map are twice as long (41 decisions against 20). Self-play: the expiry rate is 3.5 in 100 (interval 1.7 to 7.0):
  **wrong**, above the predicted 0 to 2. Shots are spread evenly over the six phases (34% in phases 1 and 2):
  **wrong**, much later than predicted. Head to head: the table's own map ahead by 1.7 a pair (interval +0.6 to
  +2.8): inside the range, and clear of zero, which I said it probably wouldn't be.
- **Result:** 0.4 core-hours for both passes, 48 offence positions. **Wrong, in the good direction.** The search's
  choice is the best turn found on 32 of 48 positions (67%), not 30% to 50%. Mean regret 0.75 points (interval 0.3
  to 1.2), not 1.5 to 3. The defence wasn't measured.
