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
