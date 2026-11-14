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
