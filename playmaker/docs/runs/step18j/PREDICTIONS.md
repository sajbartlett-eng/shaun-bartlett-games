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
- searches (jfinal, 1 positions): 0.0 (running total 3.73)
- play-outs (6 candidate copies of 16 on 1 positions): 0.07 (running total 3.8)
- searches (jfinal, 1 positions): 0.0 (running total 3.8)
- sense check detail (shoot now or play on 1, today): 0.12 (running total 3.93)
- play-outs (6 candidate copies of 16 on 1 positions): 0.07 (running total 4.0)
- searches (jfinal, 1 positions): 0.0 (running total 4.0)
- sense check detail (closeout, step 2, today): 0.01 (running total 4.01)
- sense check detail (closeout, step 2, today): 0.02 (running total 4.03)
- play-outs (6 candidate copies of 16 on 1 positions): 0.07 (running total 4.1)
- sense check detail (18e's Steal position, clock 2, today): 0.01 (running total 4.11)
- sense check detail (18e's Steal position, clock 2, today): 0.01 (running total 4.12)
- self-play (final, 160 possessions): 0.77 (running total 4.89)
- head to head final_vs_rules, pairs 1 to 40: 0.36 (running total 5.25)
- head to head final_vs_rules, pairs 41 to 80: 0.35 (running total 5.6)
- head to head dice_vs_final, pairs 1 to 40: 0.28 (running total 5.88)
- head to head dice_vs_final, pairs 41 to 80: 0.27 (running total 6.15)
- self-play (dice, 160 possessions): 0.6 (running total 6.75)
- searches (jnone, 19 positions): 0.01 (running total 6.76)
- searches (jks, 19 positions): 0.01 (running total 6.77)
- searches (jksd, 19 positions): 0.01 (running total 6.77)
- speed, round 1 (one core): 0.06 (running total 6.84)
- speed, round 2 (one core): 0.06 (running total 6.9)
- searches (jks2 choices, 19 positions): 0.01 (running total 6.91)
- the fault shown: one position, 16 play-outs: 0.04 (running total 6.95)
- searches (jks2, 1 positions): 0.0 (running total 6.95)
- searches (jks2, 19 positions): 0.01 (running total 6.96)
- play-outs (2 candidate copies of 16 on 1 positions): 0.04 (running total 7.0)
- speed, round 1 (one core): 0.06 (running total 7.06)
- speed, round 2 (one core): 0.06 (running total 7.12)
- speed, round 1 (one core): 0.06 (running total 7.19)
- speed, round 2 (one core): 0.06 (running total 7.25)
- sense check detail (closeout, shooter cannot move, today): 0.01 (running total 7.26)
- sense check detail (closeout, shooter cannot move, today): 0.0 (running total 7.26)
- exam position 10 by play (new rules): 0.32 (running total 7.58)
- agreement checks between the two engines, one core (not written by the tools): 1.2 (running total 8.78)
- tests, one core: the named files, the browser tests, the two exam files again, 18i's exam positions: 0.79 (running total 9.57)
- speed, one core, beyond the rounds above: each change timed apart, and dice_in_hand: 0.77 (running total 10.34)
- a play-out stopped part way (exam position 10 under 18i's rules): 0.02 (running total 10.36)

**Used: 10.4 core-hours.** Estimate 10.5. Hard stop 12.

## How the predictions came out

1. **Wrong.** Shots contested rose from 24 to 30 in 100, not above 45. Points did not clearly move.
2. **Wrong.** No shot was fouled. The computer stopped making hard contests from the side or behind instead.
3. **Wrong on both.** Steals tried fell (0.83 to 0.60 a possession), and the computer Steals at 4 fouls with 10
   possessions left. By play it is right to.
4. **Right** about the cause: the reply list follows too few first actions and drops a Move that only sets up a
   Steal. The speed cost I expected came from a different part (keeping settled turns), and was removed.
5. **Not found.** The order is cut from the defence's list as a copy of other turns before the search compares it.
