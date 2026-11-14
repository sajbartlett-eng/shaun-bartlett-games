# Step 18k: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine; single-core runs count as one core.

## Estimate: 10.0 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| The set replayed under the rules after part 0 (19 positions, 63 candidates, 32 play-outs each) | 2.6 | 18j's replay cost 2.25 for 56 candidates |
| Board 3: every turn the computer reads level, played out (about 24 turns) | 1.0 | as ruled; again in part for the level turns after the fix: 0.5 |
| Self-play, 160 possessions: `dice_in_hand` off, and on (the check against basketball) | 1.4 | 18j: 0.6 to 0.8 a run |
| The shortlist fix: pilots (searches) and the gate, new choices played out | 0.7 | |
| The backstop head to head, 80 to 120 pairs | 0.9 | 0.36 for 40 pairs in 18j |
| The recheck: 160 possessions on the final default | 0.7 | |
| Speed at every level, each change apart | 0.6 | |
| Agreement checks between the two engines, tests | 1.6 | one core |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 12.
- **Level picks are averaged on board 3 only,** as ruled. The set has about 14 positions where the computer's pick
  is one of several level turns. Playing every level turn on all of them would cost about 6 core-hours.

## Predictions

1. **The foul price:** at 2 team fouls with 8 possessions left a steal foul's later cost is small, under 2 points.
   Steals tried and steal fouls stay close to 18j's with `dice_in_hand` off, and stay well above twice basketball's
   band with it on. So `dice_in_hand` stays off.
2. **The shortlist:** keeping turns that leave different things in hand lets your closeout order onto the list, and
   the search then picks it. 2 chances in 3.
3. **Speed:** ranking the kept turns by the search's own reading costs too much in full. The form that fits ranks
   only the first cut that way.
4. **Board 3:** scored by the average of its level turns it fails, by 3 to 5 points, before and after the fix.

## Tally (core-hours used)

- searches (x_kdef choices, 19 positions): 0.01 (running total 0.01)
- searches (x_kih choices, 19 positions): 0.01 (running total 0.03)
- searches (k18a, 19 positions) (frozen copy): 0.01 (running total 0.03)
- the set replay lost to a machine restart 41 minutes in (4 cores): 2.75 (running total 2.79)
- searches (k18a, 3 positions): 0.0 (running total 2.79)
- play-outs (15 candidate copies of 16 on 3 positions): 0.17 (running total 2.96)
- searches (k18a, 3 positions): 0.0 (running total 2.96)
- play-outs (11 candidate copies of 16 on 3 positions): 0.08 (running total 3.04)
- searches (k18a, 4 positions): 0.0 (running total 3.04)
- play-outs (9 candidate copies of 16 on 4 positions): 0.0 (running total 3.04)
- searches (k18a, 4 positions): 0.0 (running total 3.04)
- play-outs (12 candidate copies of 16 on 4 positions): 0.3 (running total 3.34)
- searches (k18a, 4 positions): 0.0 (running total 3.35)
- play-outs (10 candidate copies of 16 on 4 positions): 0.11 (running total 3.45)
- searches (k18a, 1 positions): 0.0 (running total 3.45)
- play-outs (26 candidate copies of 16 on 1 positions): 0.47 (running total 3.92)
- searches (k18h, 19 positions): 0.01 (running total 3.93)
- searches (check, 1 positions): 0.0 (running total 3.93)
- play-outs (2 candidate copies of 16 on 2 positions): 0.01 (running total 3.94)
- searches (k18d, 19 positions): 0.01 (running total 3.95)
- searches (k18hd, 19 positions): 0.01 (running total 3.96)
- self-play (base, 160 possessions): 0.64 (running total 4.6)
- self-play (dice, 160 possessions): 0.53 (running total 5.13)
- self-play (hand, 160 possessions): 0.62 (running total 5.75)
- searches (k18a, 3 positions): 0.0 (running total 5.75)
- play-outs (15 candidate copies of 16 on 3 positions): 0.18 (running total 5.92)
- searches (k18a, 2 positions): 0.0 (running total 5.92)
- play-outs (8 candidate copies of 16 on 2 positions): 0.06 (running total 5.98)
- searches (k18a, 2 positions): 0.0 (running total 5.98)
- searches run in the working copy (choices under each setting, the fault checks), about: 0.05 (running total 6.03)
- play-outs (6 candidate copies of 16 on 2 positions): 0.1 (running total 6.13)
- searches (k18a, 1 positions): 0.0 (running total 6.13)
- speed, round 1 (one core): 0.06 (running total 6.2)
- speed, round 2 (one core): 0.06 (running total 6.25)
- speed, round 1 (one core) keep_in_hand=moves: 0.05 (running total 6.3)
- speed, round 2 (one core) keep_in_hand=moves: 0.05 (running total 6.36)
- speed, round 1 (one core) keep_in_hand=true: 0.05 (running total 6.41)
- speed, round 2 (one core) keep_in_hand=true: 0.05 (running total 6.46)
- play-outs (28 candidate copies of 16 on 1 positions): 0.53 (running total 6.99)
- searches (k18h, 3 positions): 0.0 (running total 7.0)
- play-outs (9 candidate copies of 16 on 2 positions): 0.21 (running total 7.2)
- searches (k18a, 19 positions): 0.01 (running total 7.21)
- searches (k18h, 19 positions): 0.01 (running total 7.22)
- searches (k18d, 19 positions): 0.01 (running total 7.23)
- searches (k18hd, 19 positions): 0.01 (running total 7.23)
- searches (k18m, 3 positions): 0.0 (running total 7.23)
- play-outs (16 candidate copies of 16 on 1 positions): 0.34 (running total 7.57)
- searches (k18m, 19 positions): 0.01 (running total 7.58)
- self-play (moves, 160 possessions): 0.64 (running total 8.22)
- head to head moves_vs_default, pairs 1 to 40: 0.26 (running total 8.48)
- head to head moves_vs_default, pairs 1 to 40: 0.32 (running total 8.81)
- agreement checks between the two engines, one core (not written by the tools): 0.95 (running total 9.76)
- tests, one core: the named files, the browser tests, the new tests while writing them: 0.39 (running total 10.15)
- timing where the search spends its time on three positions, one core: 0.05 (running total 10.2)

**Used: 10.2 core-hours.** Estimate 10.0. Hard stop 12. Of the 10.2, 2.75 was a set replay lost to a machine restart
41 minutes in; the replay was then run in small batches that save as they go, and trimmed (every candidate 16 times,
the positions the gate turns on 32 times) to stay inside the limit.

## How the predictions came out

1. **Right.** A steal foul's later cost is close to nothing, and with `dice_in_hand` on Steals and steal fouls land
   far outside the band (111 tried and 56 fouled in 100 possessions). It stays off.
2. **Wrong.** Your closeout order is not found. Keeping turns that leave different things in hand does not bring it
   back: the order only pays off on the defence's next turn, one turn past where its search stops.
3. **Right.** Reading one more turn after the reply costs 3.5% of the All-Star's time; reading a turn one turn
   further costs about a whole search.
4. **Half right.** Board 3 scored by its average is 4.6 behind the best turn, inside chance on these play-outs.
