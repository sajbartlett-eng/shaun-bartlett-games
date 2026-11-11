# Step 18e: compute estimate and predictions

Written before the runs. Core-hours on this 4-core machine.

## Estimate: about 12 core-hours without part 4, about 20 with it

| Part | Core-hours | Why |
|---|---|---|
| 1. The rule as the default | 0.2 | agreement checks only; no refit (18d found the map's error didn't rise) |
| 2. Pilot: the 11 defence positions, up to three passes | 2.7 | 0.9 a pass at 18d's settings |
| 2. Head to head, up to 400 pairs, All-Star, sequential | 5.0 | 18c's 240 pairs cost 2.0; the open list makes each search slower |
| 2. The sense checks played out by the rules | 1.0 | a few positions, two moves each, a few hundred play-outs |
| 2. Speed, agreement checks | 0.8 | |
| 3. Shaun's playtest | 0.1 | one position, two settings |
| 4. The offence's list: pilot on 18a's 48 positions, then a head to head | 8.0 | only if part 2 wins and the pilot shows a gain |
| 5. The 19 boards, shot timing and the rushed shares | 2.0 | one self-play run of 200 possessions, the boards at 1 pair |

Stop rules: part 2 stops at the pilot if the choice isn't best more often and the points left don't fall. Part 4
stops at its pilot the same way. The head to head stops early once its interval is clear of 0 either way.

## Cost found before building (not a run over 30 minutes)

Reading every legal defence action with the full ordering reading costs about 250 microseconds an action, and a
defence position has 500 to 1,200 legal first actions (a Move to each square with each of 8 facings is most of them).
A search asks for a list at about 25 positions, each with first and second actions. That is tens of seconds a
decision. So the build uses the form the prompt allows: a cheap first read of every legal action, by the reading's own
re-read of one moved defender, then the full read of the best.
