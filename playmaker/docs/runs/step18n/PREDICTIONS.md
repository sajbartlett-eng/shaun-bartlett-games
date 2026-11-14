# Step 18n: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine; single-core work (tests, agreement checks) counts as one
core and is in the tally too.

## Estimate: 7.0 core-hours. Hard stop: 10 (the lower of 10 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| Self-play for the refit: All-Star 200, Starter 90, Rookie 120 possessions | 1.7 | 18l's runs on today's cards cost 1.45, 0.16 and 0.07 |
| All-Star self-play on the final default, 200 possessions (the matchup tables and the FIBA table) | 1.4 | |
| The sense-check set on today's cards and rules: every candidate 16 play-outs; board 3 by the average of its level turns | 1.9 | 18l's replay cost 2.06 |
| Speed at every level, 18l's code and this step's in turn | 0.2 | one core |
| Agreement checks between the two engines | 0.7 | one core; small ones while building, the full set once |
| Tests: the named set once, and small runs while re-recording | 0.9 | one core |
| Searches and small checks | 0.2 | |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 10.
- Every run plays today's cards: the pool is rebuilt with `python3 tools/step_18.py pools` and the tool refuses a
  stale one; the set is played from `positions_18n.json`, guarded the same way.
- Long runs go in batches that survive a machine restart.

## Predictions

1. **Points:** with jump shots contested by anyone next to the shooter, and the inside contests back at full size,
   the All-Star falls from 1.36 points a possession to between 1.10 and 1.25.
2. **Contested threes:** most threes taken with a defender next to the shooter are by shooters rated 9 or more.
   Shooters rated 7 or less take almost none contested.
3. **Inside shots:** the defence goes for the block on fewer than 1 inside shot in 4, and shooting fouls stay under
   10 in 100 rim shots: straight up from in front is now safe and automatic.
4. **Speed:** the search is no slower, and a little faster at the All-Star.
5. **The sense-check set:** the computer is best or level on 13 to 16 of 19.

## Tally (core-hours used)

- a trial of the measuring tool (rookie, 8 possessions): 0.01 (running total 0.01)
- self-play (fit_allstar, allstar, 200 possessions): 2.17 (running total 2.18)
- self-play (fit_starter, starter, 90 possessions): 0.27 (running total 2.45)
- self-play (fit_rookie, rookie, 120 possessions): 0.08 (running total 2.52)
- self-play (final, allstar, 200 possessions): 1.67 (running total 4.2)
- searches (n18a, 3 positions): 0.0 (running total 4.2)
- the set replay stopped 19 minutes into its first group (2 cores), to be cut to what fits: 0.64 (running total 4.84)
- searches (n18a, 7 positions): 0.0 (running total 4.84)
- play-outs (22 candidate copies of 16 on 7 positions): 0.21 (running total 5.05)
- searches (n18a, 1 positions): 0.0 (running total 5.05)
- play-outs (6 candidate copies of 16 on 1 positions): 0.51 (running total 5.56)
- searches (n18a, 2 positions): 0.0 (running total 5.56)
- speed, round 1 (one core): 0.07 (running total 5.63)
- speed, round 2 (one core): 0.07 (running total 5.7)
- speed, round 1 (one core): 0.08 (running total 5.78)
- play-outs (7 candidate copies of 16 on 2 positions): 0.31 (running total 6.09)
- speed, round 2 (one core): 0.08 (running total 6.17)
- self-play (fit_starter2, starter, 90 possessions): 0.21 (running total 6.39)
- self-play (fit_rookie2, rookie, 120 possessions): 0.07 (running total 6.46)
