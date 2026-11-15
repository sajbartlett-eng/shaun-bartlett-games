# Step 18p: estimates and predictions, stage by stage

No fixed limit (D-196), but each stage is estimated before it starts and says what the compute buys. If a stage runs
past twice its estimate I stop and report.

## Stage 0 (do now): estimate 0.3 core-hours

- What it buys: the old setup's time at each level, and the speed with the zone on.
- No play-outs: the zone's speed was timed in 18o.

## Stage 1 (the reading): estimate 8 core-hours

| Part | Core-hours | What it buys |
|---|---|---|
| Four exact checks for the plan (searches, no play-outs) | 0.3 | Where the reading goes wrong, shown on Shaun's board |
| Play for the first fit: 320 possessions, a turn drawn at most once in each | 2.6 | About 6,000 positions, each with what it went on to earn, including positions the computer never chooses to reach |
| Play for the second fit, with the first fit's reading | 2.6 | The same, once both sides read the lane, so the fit doesn't keep the first round's flaws |
| The design checks by forced lines (about 8 groups of 16 play-outs) | 1.0 | Whether checks 1, 2, 3, 4 and 7 fall out |
| Agreement of the two engines, speed, tests | 1.5 | The stage's gate |

**Predictions, before any fit:**

1. The first fit gives "the ball handler's best paint look next phase" a clear worth above nothing in phases 1 to 3.
2. With the first fit the search chooses the Sprint into the empty lane on Shaun's board after the beat. (Check 1.)
3. With the first fit the defence, to act with the lane open, puts a defender between the ball and the rim more
   often than not. I am less sure of this one: it may need the second fit.
4. The fitted reading's held-out error is lower than the hand reading's straightened per phase, by a little
   (under 1 point): what a position goes on to earn is mostly dice.
5. The closeout pause (check 7) is not cured by the fit: no part of the reading counts standing next to a ball
   handler. If so it needs a new part, and I stop and ask.
6. The fitted reading costs time: each reading computes every part. I expect the speed budget to be the hard gate.

## Compute tally (core-hours)

- one core: four exact checks for the plan (searches on Shaun's board): 0.25 (running total 0.25)
- play for the fit (fit1, 320 possessions, a drawn turn at rate 0.125): 1.9 (running total 2.22)
- one core: a forced line for the offence, dropped (its line was wrong: the ball handler can't move again in the phase he Sprints): 0.04 (running total 2.25)
- one core: the design checks by the reading and the search, twice: 0.02 (running total 2.27)
- check 1 played (baseline) (4 positions, 16 each): 0.34 (running total 2.61)
- speed, round 1 (one core): 0.05 (running total 2.67)
- speed, round 2 (one core): 0.05 (running total 2.72)
- one core: the named tests (1,350 seconds), the site tests (101), and reruns: 0.44 (running total 3.16)

**Stage 1 stopped after the first fit (2.6 core-hours of the 8 estimated): the fit showed a second round could not help. Total for the step: 3.2 core-hours.**
