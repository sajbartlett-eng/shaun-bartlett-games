# Step 18g: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine; single-core runs are counted at one core.

## Estimate: 9.5 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| Grow the set: ten positions two turns before an open shot, 3 or 4 candidates, 32 play-outs each | 2.8 | a play-out from early in a possession takes about 9 seconds (measured at 18h) |
| Bring to 64 play-outs the candidates in contention | 0.5 | not every candidate: all of them would cost about 3 more, which I under-estimated in 18h's report |
| The zone's gate: the closeouts, EB3F5B, six of the new positions, boards 1, 3 and 8, replayed under the zone rule at 32 play-outs | 2.5 | about 40 candidates |
| Fidelity: self-play at the All-Star, today's rules and the zone, 120 possessions each | 1.6 | 200 each would be 2.6; cut to fit |
| One extra setting (the zone for strong defenders only), 100 possessions | 0.7 | only if the rest is inside 10.5 |
| Speed with the rule on, beside 18h's code | 0.3 | one core |
| Agreement checks (switch off and on), tests | 1.0 | one core |
| Searches | 0.1 | |

- A running tally is kept at the foot of this file. No run is started that can't finish inside 12.

## Predictions

1. **The new positions (today's rules):** on at least half, no candidate turn changes what the offence goes on to
   score by more than 2 points. Where one does, it is a turn that keeps a defender within reach of the player who
   goes on to shoot.
2. **The closeout board under the zone:** the computer keeps the Move (it Quick Steps closer) without being told,
   because under the zone the Move kept is the reach of his stance. I give this 1 chance in 2: the reading may still
   see the two as level.
3. **Defence under the zone is stronger:** the offence scores 2 to 5 points a possession less in self-play, more
   shots are contested (above 30 in 100), and more Dribbles are tried.
4. **Speed:** the zone costs under 10% at each level (the same eight facings, each covering two lines).

## Tally (core-hours used)

- searches (reactions, 35 positions): 0.0 (running total 0.0)
- searches (two turns before, 10 positions): 0.01 (running total 0.01)
- searches (zone choices, 9 positions): 0.01 (running total 0.01)
- searches (today choices, 9 positions): 0.01 (running total 0.02)
- play-outs (40 candidate copies of 16 on 11 positions): 1.47 (running total 1.5)
- play-outs lost when the session's worker restarted (4 cores, about 8 minutes, nothing kept): 0.55 (running total 2.05)
- agreement checks between the two engines, zone off and on (one core each, some lost to the restart): 0.6 (running total 2.65)
- play-outs (14 candidate copies of 16 on 4 positions): 0.43 (running total 3.08)
- play-outs (12 candidate copies of 16 on 3 positions): 0.6 (running total 3.68)
- play-outs (14 candidate copies of 16 on 3 positions): 0.66 (running total 4.34)
- searches (today choices, 10 positions): 0.02 (running total 4.36)
- searches (today, 10 positions): 0.01 (running total 4.37)
- play-outs (6 candidate copies of 16 on 7 positions): 0.44 (running total 4.81)
- searches (zone_near, 19 positions): 0.02 (running total 4.83)
- self-play (today, 160 possessions): 1.9 (running total 6.73)
- correction: the self-play under today's rules shared its cores with another run, so its clock time counted double; by processor time it used 0.98: -0.92 (running total 5.81)
- self-play (zone, 160 possessions): 1.87 (running total 7.68)
- correction: the self-play under the zone shared its cores with the gate's play-outs; by processor time it used 1.0: -0.88 (running total 6.81)
- play-outs (112 candidate copies of 16 on 19 positions): 3.06 (running total 9.87)
- correction: the gate's first batch shared its cores with the two self-play runs; by processor time it used 1.86: -1.2 (running total 8.67)
- sense check detail (closeout, shooter cannot move, zone): 0.27 (running total 8.94)
- self-play (zone_b, 48 possessions): 0.35 (running total 9.29)
- sense check detail (closeout, shooter cannot move, today): 0.01 (running total 9.31)
- searches (zone choices, 10 positions): 0.0 (running total 9.31)
- searches (zone_rest, 4 positions): 0.0 (running total 9.31)
- play-outs (8 candidate copies of 16 on 4 positions): 0.23 (running total 9.55)
- searches (zone_two, 2 positions): 0.0 (running total 9.55)
- play-outs (6 candidate copies of 16 on 2 positions): 0.17 (running total 9.72)
- searches (today choices, 34 positions): 0.01 (running total 9.74)
- searches (today_same_21, 21 positions): 0.01 (running total 9.75)
- speed, round 1 (one core): 0.1 (running total 9.85)
- play-outs (12 candidate copies of 16 on 9 positions): 0.35 (running total 10.2)
- searches (today_all, 34 positions): 0.01 (running total 10.21)
- play-outs (0 candidate copies of 16 on 10 positions): 0.0 (running total 10.21)
