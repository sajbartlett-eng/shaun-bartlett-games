# Step 18j: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine; single-core runs count as one core.

## Estimate: 10.5 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| The two rule changes on their own: the set replayed (19 positions near a shot) | 1.9 | 18i's replay cost 1.85 |
| ... and 160 possessions of self-play, with the two foul numbers remeasured from it | 1.1 | 18i's cost |
| ... and the three foul situations by play | 0.4 | 18i's cost |
| The fault shown: searches and a few play-outs on the set | 0.3 | |
| The fix: pilots on the set's four named positions | 0.5 | searches, and play-outs of new choices |
| The gate: the fix's choices on the set, new choices played out | 1.5 | only choices that have no answer yet |
| The backstop head to head, up to 120 pairs | 1.5 | 200 would be 2.5; cut to fit |
| The zone retest: 21 positions replayed, and 2 x 120 possessions | 0 | **does not fit**; run only if the parts above come in under |
| The recheck: 160 possessions on the final default | 1.1 | |
| Agreement checks, tests, speed | 2.0 | one core |
| Searches | 0.2 | |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 12.
- **The zone retest (part 4) is about 4 core-hours and does not fit beside the rest.** I say so now, before any run.

## Predictions

1. **The soft contest:** shots contested rise from 24 in 100 to above 45, nearly all the rise soft. Points a
   possession fall by 1 to 3.
2. **The hard contest's fouls:** fouled shots return (above 2 in 100 possessions) because a hard contest from the
   side now rolls twice even with the arrow on him.
3. **The penalty:** with no +5 on an ordinary steal foul, Steals tried rise (a foul costs less now), and the
   computer holds back at 4 fouls with 10 possessions left.
4. **The fault:** the reply inside the offence's search is too narrow to hold a defender's Move followed by a Steal.
   Widening what the reply follows fixes the "hold the ball" position, at a cost in speed I expect to have to pay
   for elsewhere.
5. **The closeout order:** I give 1 chance in 3 that the computer finds your order after the fix.

## Tally (core-hours used)

- the fault shown: one position, 16 play-outs: 0.04 (running total 0.04)
- the fault shown: one position, 16 play-outs: 0.02 (running total 0.06)
- searches (j18x choices, 7 positions): 0.01 (running total 0.07)
- searches (j18x choices, 7 positions): 0.01 (running total 0.08)
- searches (j18x choices, 7 positions): 0.01 (running total 0.09)
- searches (j18x choices, 12 positions): 0.01 (running total 0.1)
- searches (j18x choices, 6 positions): 0.01 (running total 0.1)
- self-play (rules, 160 possessions): 0.81 (running total 0.92)
- searches (j18, 19 positions): 0.01 (running total 0.93)
- play-outs (112 candidate copies of 16 on 19 positions): 2.25 (running total 3.18)
- searches (j18fix, 19 positions): 0.01 (running total 3.19)
- play-outs (10 candidate copies of 16 on 5 positions): 0.22 (running total 3.41)
- searches (x_ks choices, 19 positions): 0.01 (running total 3.41)
- searches (x_ksd choices, 19 positions): 0.01 (running total 3.42)
- searches (x_bl choices, 19 positions): 0.01 (running total 3.43)
- searches (x_none choices, 19 positions): 0.01 (running total 3.44)
- searches (x_o3 choices, 19 positions): 0.01 (running total 3.44)
- searches (x_all3 choices, 19 positions): 0.01 (running total 3.45)
- the fault shown: one position, 16 play-outs: 0.04 (running total 3.49)
- the fault shown: one position, 16 play-outs: 0.04 (running total 3.53)
- the fault shown: one position, 16 play-outs: 0.04 (running total 3.57)
- searches (j18ksd, 19 positions): 0.01 (running total 3.57)
- play-outs (2 candidate copies of 16 on 1 positions): 0.01 (running total 3.58)
- searches (j18ksd, 1 positions): 0.0 (running total 3.58)
- play-outs (10 candidate copies of 16 on 1 positions): 0.15 (running total 3.73)
