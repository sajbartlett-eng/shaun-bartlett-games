# Step 18l: compute estimate and predictions

Written before the runs (one 8-possession trial of the measuring tool came first: 0.01, in the tally). Core-hours on
this 4-core machine; single-core runs count as one core.

## Estimate: 9.5 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| Self-play for the refit: Rookie 160, Starter 120, All-Star 200 possessions | 1.85 | 18h's own runs cost 0.19, 0.42 and 1.23 |
| The sense-check set replayed on the new cards with the rule on (every candidate 16 play-outs, a second 16 on the positions the score turns on) | 2.6 | 18k's replay |
| All-Star self-play on the final default, 200 possessions (the FIBA table) | 1.2 | |
| The same 200 possessions with `rules.off_balance` off (what the rule changed) | 1.2 | |
| Speed at every level, 18k's code and this step's in turn | 0.3 | one core |
| Agreement checks between the two engines | 0.6 | one core |
| The named tests, twice | 1.2 | one core, about 25 minutes a run |
| Searches, small checks, the EB3F5B replay | 0.55 | |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 12.
- Long runs go in batches that survive a machine restart: each batch leaves a marker and a rerun skips it.

## Predictions

1. **Points:** the lower jump shots take All-Star self-play from 27.8 points a possession on the 20-sided scale
   (1.39 real points) to between 21 and 24 (1.05 to 1.2). Still above FIBA's 0.95 to 1.0: the game has no misses
   off the rim, only ratings.
2. **Steals:** with a missed reach now leaving the defender 2 worse against the drive, Steals tried fall from 69 per
   100 possessions to between 35 and 55. Fouls on a Steal fall with them but stay above FIBA's 5 to 8 per 100.
3. **The off-balance tests:** after a missed Steal the offence drives at that defender on its next action more than
   1 time in 3. A Sprint closeout is driven past more often than a set defender (by about the 10 points in 100 the
   2 is worth). Ball handlers seldom Sprint into a Dribble, so that test has few cases.
4. **The sense-check set:** the computer's score on the re-recorded answers is 14 to 16 of 19.
5. **Speed:** no level slower by more than the noise between runs (the rule adds one check to each roll).

## Tally (core-hours used)

- self-play (smoke, rookie, 8 possessions): 0.01 (running total 0.01)
- self-play (fit_rookie, rookie, 160 possessions): 0.14 (running total 0.15)
- self-play (fit_starter, starter, 120 possessions): 0.3 (running total 0.45)
- self-play (fit_allstar, allstar, 200 possessions): 1.06 (running total 1.51)
- the final-default run stopped a minute in, to add a second 200 possessions to the All-Star's map (its phase 3 lines had 105 and 70 positions and sloped down): 0.03 (running total 1.54)
- self-play (fit_allstar2, allstar, 200 possessions): 1.14 (running total 2.68)
- self-play (final, allstar, 200 possessions): 1.26 (running total 3.94)
- self-play (off, allstar, 160 possessions): 0.94 (running total 4.88)
- searches (l18a, 3 positions): 0.0 (running total 4.88)
- play-outs (17 candidate copies of 16 on 3 positions): 0.32 (running total 5.2)
- searches (l18a, 3 positions): 0.0 (running total 5.2)
- play-outs (15 candidate copies of 16 on 3 positions): 0.25 (running total 5.46)
- searches (l18a, 4 positions): 0.0 (running total 5.46)
- play-outs (9 candidate copies of 16 on 4 positions): 0.0 (running total 5.46)
- searches (l18a, 4 positions): 0.0 (running total 5.46)
- play-outs (12 candidate copies of 16 on 4 positions): 0.47 (running total 5.93)
- searches (l18a, 4 positions): 0.0 (running total 5.94)
- play-outs (11 candidate copies of 16 on 4 positions): 0.19 (running total 6.12)
- searches (l18a, 1 positions): 0.0 (running total 6.12)
- play-outs (27 candidate copies of 16 on 1 positions): 0.7 (running total 6.82)
- searches (l18a, 3 positions): 0.0 (running total 6.83)
- self-play (new_allstar, allstar, 200 possessions): 1.45 (running total 8.28)
- self-play (new_starter, starter, 90 possessions): 0.16 (running total 8.44)
- self-play (new_rookie, rookie, 120 possessions): 0.07 (running total 8.51)
- speed, round 1 (one core): 0.11 (running total 8.62)
- speed, round 2 (one core): 0.1 (running total 8.72)
- a second pass of the old-card set replay stopped 2 minutes in (4 cores), when the old cards were found: 0.13 (running total 8.85)
- searches: the set on the cards before D-184 and on the cards now (19 positions each): 0.02 (running total 8.87)
- the named tests, three runs, and the changed files once (one core): 1.13 (running total 10.0)
- agreement checks between the two engines, twice: before and after the store fix (one core): 1.03 (running total 11.03)
- finding the store fault: the two failing checks again with the rule off, and the comparisons that tracked it down (one core): 0.56 (running total 11.59)
- small test runs while re-recording the card-value tests (one core): 0.13 (running total 11.72)
- the static test on its own (one core): 0.03 (running total 11.75)

**Total: 11.75 core-hours of the 12 allowed** (estimate 9.5). 6.9 of them went on runs that played the cards from before D-184 by mistake: see the report.
