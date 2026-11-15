# Step 18o: estimate and predictions

Written at the start of the measuring work, after the rule was built and before any play-out had finished.

## Estimate: 12.5 core-hours. Hard stop: 14 (the limit; twice the estimate is higher).

| Part | Core-hours |
|---|---|
| Agreement checks of the two engines, on one core | 0.5 |
| Setup: trials while building, and the pools of starts by the new setup | 1.3 |
| Sense checks 1 to 4 (about 25 placements, 16 play-outs each) | 2.7 |
| Refit: self-play at each level (All-Star 200, Starter 90, Rookie 120) | 2.5 |
| The test: arm A and arm B, 200 All-Star possessions each | 3.7 |
| Game EB3F5B in each arm, and the set's positions that can move | 0.9 |
| Speed, against 18n's code | 0.35 |
| The named tests, on one core | 0.9 |
| **Total** | **12.9, called 12.5** |

A play-out costs about 30 core-seconds (step 18n). If the sense checks or an arm run long, the set replay is cut first,
then the Starter and Rookie refit runs are shortened. Arm B gets a map of its own only if its play needs one.

## Predictions

1. **Jump shots.** With the original contests back and the full rating only for a square defender, fewer threes
   are taken against a set defender in front, and more of the contested threes come against a defender who isn't
   square (beside, or rushed). Contested threes fall from 41 in 100 to under 30.
2. **Scoring, arm A.** About the same as 18n or a little lower: 1.20 to 1.30 a possession. The inside shot, not the
   three, was the generous part, and this step doesn't touch it.
3. **The setup.** The search's reading at tip-off barely tells placements apart (about 1 point between very different
   defences on Shaun's board), so a setup "judged by play" inside the setup's time will pick among placements that
   read level. I expect 16 play-outs not to separate them either (about 6 points either way).
4. **Help.** On Shaun's board the lane defence will not play out clearly better than his game's defence at 16
   play-outs. If it does, the gap will be in drives finished at the rim.
5. **The straight drive.** The code will confirm it: with the zone off, a single arrow at an adjacent ball handler
   stops no square, so no placement of X1 walls the drive. With the zone on, I10 will.
6. **Arm B.** The zone lowers scoring by 0.05 to 0.15 a possession and cuts rim shots.
7. **Speed.** No level slower than 18n's code in play. Setup inside its budget at every level.

## Compute tally (core-hours)

- a first look at placements on Shaun's board (6 placements, 16 each, allstar): 0.69 (running total 0.73)
- one core: the search setup for 48 deals (3 setups each, allstar): 0.06 (running total 0.79)
- self-play (setup stored, allstar, 48 possessions): 0.3 (running total 1.09)
- self-play (setup man, allstar, 48 possessions): 0.34 (running total 1.43)
- self-play (setup search, allstar, 48 possessions): 0.19 (running total 1.61)
- one core: a preparation run stopped after 18 minutes (under the zone the bridge sent the readings to the slow Python search): 0.3 (running total 1.91)
- one core: the faster named tests, first run, and reruns of the re-recorded ones: 0.2 (running total 2.12)
- one core: the search's own reading of arrows and of X1's squares on Shaun's board: 0.08 (running total 2.2)
- one core: the full agreement checks of the two engines (1,335 seconds): 0.37 (running total 2.57)
- sense check: beaten (3 placements, 16 each, allstar): 0.32 (running total 2.88)
- sense check: drive (4 placements, 16 each, allstar): 0.43 (running total 3.32)
- sense check: zone_setup (4 placements, 16 each, allstar, zone on): 0.51 (running total 3.83)
- sense check: zone_beaten (3 placements, 16 each, allstar, zone on): 0.33 (running total 4.16)
- sense check: zone_drive (4 placements, 16 each, allstar, zone on): 0.36 (running total 4.52)
- sense check: arrows (1 placements, 16 each, allstar): 0.13 (running total 4.65)
- sense check: zone_arrows (1 placements, 16 each, allstar, zone on): 0.19 (running total 4.84)
- sense check: beaten_drive (4 placements, 16 each, allstar): 0.96 (running total 5.8)
- self-play (fit_allstar, allstar, 200 possessions): 1.73 (running total 7.53)
- self-play (fit_starter, starter, 90 possessions): 0.13 (running total 7.67)
- self-play (fit_rookie, rookie, 120 possessions): 0.05 (running total 7.72)
- self-play (armA, allstar, 200 possessions): 1.08 (running total 8.8)
