# Step 18c: the compute estimate, and predictions written before each run

## The estimate (written before any run)

**About 14 core-hours** on this machine (4 cores). What this step needs:

| Work | Core-hours | Why |
|---|---|---|
| `eval.settle_shots` at Rookie and Starter, 160 pairs each | 1.5 | 18a's level checks cost 0.54 and 1.06 |
| Boards 1 and 3 taken apart, the diagnosis, the agreement checks | 1.5 | each defence board is about 8 core-minutes a pass |
| Head to head, `eval.help_readings` on, up to 400 pairs | 2.5 | 18b's decided at 160 pairs for 0.8; a smaller gain needs more |
| The outcome exam, the default and the new switch | 2.0 | 18b's cost 1.85 |
| The defence's list cost, 12 positions, switch off and on | 3.5 | about 8 core-minutes a position a pass |
| Self-play for shot timing, 200 possessions | 0.6 | 18b's cost 0.53 |
| A second variant (the coverage budget with the readings as its prices), only if the readings gain alone | 2.5 | one more head to head |

App only: nothing is measured under the table's rules (Shaun, 11 Nov 2026).

## 1. `eval.settle_shots` at Rookie and Starter (each against its calibrated self without it, 160 pairs, its own pick noise)

- Cost: 0.5 and 1.0.
- Rookie: no clear difference. Its pick noise (5.0) is larger than the fix's effect; I expect -1 to +3 a pair with
  zero inside the interval.
- Starter: a small gain, 0 to +3 a pair; the interval may include zero.
- Neither loses clearly, so the switch goes on by default.
- **Result:** 0.65 and 0.94 core-hours. Rookie: **+11.4 a pair** (interval +8.8 to +13.9): far above the predicted
  range, and clear. Starter: +2.4 (interval +0.3 to +4.5): as predicted, and clear of zero. Neither loses: the switch
  is on by default.

## 2. Head to head: `eval.help_readings` (the floor) on, against the default (sequential, up to 400 pairs)

Written after boards 1 and 3 were taken apart: with the offence to act, half of the horizon readings sit below the
best shot the offence can release that turn, by 4.4 points on average (two thirds of them in the defence's searches).

- Cost: 1.0 to 2.5.
- Result: a gain of 1 to 3 points a pair, clear of zero within 240 pairs. Mostly from the defence: it can now see
  which of its turns lower the shot the offence can take at once.
- Shot timing: little change. 70% to 78% of shots in phases 1 and 2.
- **Result:** 1.97 core-hours. +0.4 a pair (interval -1.1 to +1.9), stopped at 240 pairs with "no gain". **Wrong:** I
  predicted a clear gain of 1 to 3. Shot timing as predicted (75% in phases 1 and 2).

## 3. The defence's list cost: 12 defence positions from play, the switch off and on

Written after board 1 showed that no defence turn of 457,510 lowers the offence's 32 there.

- Cost: 3.5 for both passes.
- By the computer's own 1-pair reading, the search's choice is the best turn found on at least half of the 12, and
  the average left on the table is under 1 point: smaller than on offence (0.75), because the defence's turn so
  rarely changes what the offence can take.
- The switch on or off makes no clear difference to that.
- **Result:** 1.86 core-hours for both passes, 11 positions (one phase had only one usable position). Switch off:
  the choice is the best turn found on 4 of 11, and 1.2 points are left on the table (interval 0.4 to 2.1).
  **Wrong:** I predicted at least half and under 1 point. Switch on: 8 of 11, and 0.9 (interval -0.3 to +2.0); the
  intervals overlap, as predicted.

## 4. The order of the levels on the new default (`eval.settle_shots` on): 80 pairs each

Added because the Rookie gained 11.4 points a pair from the switch, which could close the gap to the Starter.

- Cost: 0.8.
- Starter over Rookie: still ahead, but by less than 18a's 10.0: 3 to 8.
- All-Star over Starter: 3 to 9, as in 18a (6.8).
- **Result:** 0.94 core-hours. All-Star over Starter: +5.4 (interval +2.6 to +8.1): as predicted. Starter over
  Rookie: +2.6 (interval -0.8 to +5.9): just below the predicted 3 to 8, and not clear of zero.

## Not run

The outcome exam, the self-play run and the `eval.coverage_budget` route (5.1 of the estimate): the reading showed no gain
head to head, so nothing was left for them to measure. Used in all: about 8 of the 14 estimated.
