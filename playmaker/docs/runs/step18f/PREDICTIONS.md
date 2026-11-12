# Step 18f: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine.

## Estimate: about 30 core-hours

| Part | Core-hours | Why |
|---|---|---|
| 1. One-action turns: pilot (12 defence and 24 offence positions, two settings), a head to head up to 400 pairs | 6 | the pilot 1 a pass on defence; the head to head 3 to 4 |
| 2. Equal turns: how often the top is a tie, the build, boards 2 and 10, a head to head | 5 | |
| 3. Unused actions: the build, three sense checks, a head to head | 6 | a sense check is about 0.5 |
| 4. The offence's pilot again | 0.3 | 0.24 at step 18e |
| 5. The open list for the Rookie and Starter: speed, then the levels' order (80 pairs each) | 2 | |
| 6. The map refit: self-play at each level, the fit | 4 | |
| 7. The end: a head to head up to 400 pairs, the boards, self-play, speed | 6 | |

Stop rules: each part stops at its pilot if its value doesn't show. A head to head stops when its sequential test
gives a verdict (after at least 160 pairs), or at 400 pairs.
