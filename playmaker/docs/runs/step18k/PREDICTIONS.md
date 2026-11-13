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
