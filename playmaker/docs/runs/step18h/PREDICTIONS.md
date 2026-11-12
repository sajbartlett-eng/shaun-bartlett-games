# Step 18h: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine.

## Estimate: 9.5 core-hours. Hard stop: 12 (the lower of 12 and twice the estimate)

| Part | Core-hours | Why |
|---|---|---|
| 1. The floor shown | 0.1 | readings only, no play |
| 2. The sense-check set: about 24 positions, 3 or 4 candidates each, 64 play-outs a candidate | 3.5 | 18f's closeout check cost 0.5 for 640 play-outs; shot reactions are much shorter |
| 3. The fit of the new reading | 0.1 | from step 18f's stored self-play: its rows already hold the reading's parts |
| 3. The gate: each setting's own choices played out where they are new | 0.5 | |
| 3. The backstop head to head, up to 200 pairs | 2.2 | 400 pairs cost 4.1 at 18f |
| 4 and 5. Self-play on the final default: the All-Star 200 (it is also part 5's recheck), the Starter 200, the Rookie 240 | 2.2 | 2.4 at 18f |
| 6. Speed beside 18f's code, 2 rounds | 0.3 | one core |
| Agreement checks, tests | 0.6 | |

- **A running tally is kept at the foot of this file.** No run is started that can't finish inside 12.
- If the sense-check set costs more than 3.5 on its first positions, I cut play-outs a candidate, not positions.

## Predictions

1. **The floor shown.** On the sense set's defence positions the third term of the reading ("play on": the phase
   table plus the looks left after the cover, less the phase's average) decides at least 3 positions in 4, and
   candidate turns that differ by 5 points or more in the shot they leave read within 0.5 of each other.
2. **The sense-check set, today's default:** the computer's choice is the played-out best, or inside its interval,
   on about half the positions; it loses 2 to 3 points a position on average against the best.
3. **With the floor removed:** it matches on 2 in 3, and loses 1 to 2 points a position. It gets the closeout order.
   I am least sure of the "shoot now or play on" positions: the new reading could tip them either way.
4. **The backstop head to head:** level, between -1.5 and +2.5 a pair at 200 pairs.
5. **The recheck:** shots contested back above 30 in 100; first-phase shots back to about 4 in 10 with a map for
   each level.

## Tally (core-hours used)

- harvest (40 possessions): 0.16 (running total 0.16)
- searches (probe, 6 positions): 0.0 (running total 0.16)
- searches (probe2, 35 positions): 0.0 (running total 0.16)
- searches (reactions, 35 positions): 0.0 (running total 0.17)
- searches (last turns, 4 positions): 0.0 (running total 0.17)
- searches (offence turns, 154 positions): 0.07 (running total 0.24)
- searches (board 2, 1 positions): 0.0 (running total 0.24)
- searches (reactions, 35 positions): 0.0 (running total 0.24)
- searches (last turns, 4 positions): 0.0 (running total 0.24)
- searches (offence turns, 154 positions): 0.06 (running total 0.3)
- searches (board 2, 1 positions): 0.0 (running total 0.31)
- play-outs (68 candidates on 25 positions): 4.85 (running total 5.16)
- searches (reactions, 35 positions): 0.0 (running total 5.16)
- searches (last turns, 3 positions): 0.0 (running total 5.16)
- searches (offence turns, 154 positions): 0.07 (running total 5.22)
- searches (board 2, 1 positions): 0.0 (running total 5.22)
- searches (reactions, 35 positions): 0.0 (running total 5.22)
- searches (last turns, 3 positions): 0.0 (running total 5.23)
- searches (offence turns, 154 positions): 0.06 (running total 5.29)
- searches (board 2, 1 positions): 0.0 (running total 5.29)
- searches (A choices, 24 positions): 0.02 (running total 5.31)
- searches (B choices, 24 positions): 0.02 (running total 5.33)
- searches (C choices, 24 positions): 0.02 (running total 5.35)
- searches (D choices, 24 positions): 0.02 (running total 5.37)
- play-outs (80 candidate copies of 16 on 20 positions): 1.24 (running total 6.61)
- searches (today, 24 positions): 0.01 (running total 6.62)
- play-outs (14 candidate copies of 16 on 8 positions): 0.51 (running total 7.14)
- searches (no_floor, 24 positions): 0.01 (running total 7.15)
- play-outs (16 candidate copies of 16 on 8 positions): 0.41 (running total 7.56)
- searches (no_floor_kept, 24 positions): 0.01 (running total 7.57)
- play-outs (2 candidate copies of 16 on 2 positions): 0.03 (running total 7.6)
- searches (kept, 24 positions): 0.01 (running total 7.61)
- play-outs (2 candidate copies of 16 on 2 positions): 0.06 (running total 7.67)
- searches (maps choices, 24 positions): 0.01 (running total 7.68)
- searches (maps, 24 positions): 0.01 (running total 7.69)
- searches (check, 1 positions): 0.0 (running total 7.69)
- searches (check, 1 positions): 0.0 (running total 7.69)
- searches (exact choices, 24 positions): 0.01 (running total 7.7)
- searches (exact_shot, 24 positions): 0.01 (running total 7.71)
- play-outs (2 candidate copies of 16 on 2 positions): 0.02 (running total 7.73)
- self-play (starter, 120 possessions): 0.42 (running total 8.15)
- self-play (rookie, 160 possessions): 0.19 (running total 8.34)

### Results against the predictions (written as they came in)

- **1, the floor shown:** right on how often "play on" is returned (36 of 42 candidate positions with the offence
  to act); **wrong on what it hides.** Of 15 pairs of candidates whose shot now differs by 5 or more, only 3 read
  within half a point today.
- **2, the set on today's default: wrong, it is better than I thought.** The computer's choice is the played-out best
  or level with it on 22 of 24 positions; 0.9 points lost a position (0.3 to 1.4).
- **3, the floor removed: wrong.** 20 of 24, 1.5 lost (0.9 to 2.0); it breaks three positions that passed. With the
  control-aware cover 18 of 24, 2.4 lost. The control-aware cover alone 20 of 24, 1.8 lost. A second form (the shot
  kept exact, "play on" mapped alone) 21 of 24, 1.2 lost. None passes the gate; all stay off.
- **The set cost 6.1 core-hours, not 3.5:** play-outs from early in a possession take 8 to 10 seconds each, not the 3
  I took from 18f's closeout check; and a fault in my tool (results paired in the wrong order) cost part of a run.
- **4, the backstop head to head for the floor: not run.** Nothing passed the gate.
- self-play (allstar, 200 possessions): 1.23 (running total 9.57)
- head to head maps, pairs 1 to 40: 0.35 (running total 9.92)
- head to head maps, pairs 41 to 80: 0.54 (running total 10.46)
- speed (18f, round 1): 0.03 (running total 10.5)
- speed (18h, round 1): 0.03 (running total 10.53)
- speed (18f, round 2): 0.03 (running total 10.57)
- speed (18h, round 2): 0.03 (running total 10.6)
- agreement checks (four runs, one core): 0.08 (running total 10.68)
- **5, the recheck: half right.** First-phase shots fall from 6 in 10 to under 5 in 10 with a map for each level
  (48 in 100; 40 at 18e). Shots contested do not come back: 23 in 100 (17 to 30), as at 18f.
- **The backstop head to head for the maps** (not predicted; 0.89): level, -0.4 a pair (-3.2 to 2.4) at 80 pairs.
- searches (final choices, 24 positions): 0.01 (running total 10.69)
- the named tests, first run (one core): 0.38 (running total 11.07)
- checks after the level fix (one core): 0.05 (running total 11.12)
- searches (final, 24 positions): 0.01 (running total 11.13)
- the named tests, second run after the fix (one core): 0.39 (running total 11.52)

## At the end

- **Used: about 11.5 core-hours.** Estimate 9.5; hard limit 12. Single-core runs (speed, agreement checks, tests)
  are counted at one core.
- **The floor: none of three forms passed the gate; all off.** The final default (rank-in-hand, a map for each
  level) scores 22 of 24 on the set, 0.86 points lost a position (0.34 to 1.38); the start of the step 22 of 24,
  0.87 (0.30 to 1.44).
