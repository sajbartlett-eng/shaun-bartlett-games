# Step 17: predictions, written before each run

This machine: 4 cores. Measured throughput (`throughput.json`, and the first one-pair tests):

| Policy | Core seconds per possession | Possessions per core-hour |
|---|---|---|
| Rookie settings, 1 team turn ahead | 0.9 | 4,200 (but it never shoots: 7 points a possession) |
| Rookie settings, 1 pair ahead | 8.9 | 405 |
| Starter settings, 1 pair ahead | 15.9 | 226 |
| All-Star settings, 1 pair ahead | about 35 | about 100 |

A possession is 40 to 90 decisions, not the 12 to 24 the research assumed, so everything costs 3 to 5 times its
estimate.

## Run 1 (checkpoint 0 batch, about 60 minutes wall, 4 core-hours). Written 12:10, before any result was read.

- **Head to head, today's computer against itself:** 40 pairs.
  - Predict: a mean difference inside its interval of zero, and a standard deviation of the paired difference near
    15 points. That gives the pairs a real gain needs: about 860 for 1 point, 215 for 2.
  - Cost: about 1 core-hour.
- **The hand boards measured:** 22 decisions, the computer's top 3 turns, 16 rollouts each with the cheap policy.
  - Predict: standard errors near 3 points, so only gaps over about 6 will show. This is the pilot that sizes the
    exam: a standard error of 1 needs about 150 rollouts a turn.
  - Cost: about 1.5 core-hours.
- **Self-play pilot for the labels:** 640 possessions by the cheap policy, every position kept with its readings.
  - Predict: about 30,000 positions from 640 outcomes. Enough to see whether the readings predict the outcome better
    than today's hand-combined reading on held-out possessions (the stop rule's question, at a tenth of the size).
  - Cost: about 1.6 core-hours.

## Run 2 (stage 1 labels), if the pilot shows a gain. Not started.

- 6,400 possessions by the cheap policy: about 16 core-hours, 4 hours wall.
- Predict: held-out error falls with data along the pilot's learning curve. Scale only if the curve is still falling
  at 640.

## Run 3 (checkpoint 1 batch, about 75 minutes wall, 5 core-hours). Written 13:15, after the 40-pair pilot.

The pilot: the learned judgement (640 possessions of labels) against today's computer, 40 pairs: +3.85 points a pair,
interval -0.9 to +8.6, standard deviation 15.4. Its possessions are half as long (20 decisions against 40).

- **Head to head, learned against today's computer:** 320 pairs.
  - Predict: a gain of 2 to 5 points a pair. At 320 pairs the interval is about 1.7 either side, so a gain of 2 or
    more will show at p < 0.05.
  - Cost: about 2.3 core-hours.
- **The outcome exam:** 152 positions (the 22 hand-board decisions and 130 stored positions spread over the phases),
  4 seeds, each engine playing the side to act against today's computer.
  - Predict: the learned judgement gains on the positions where the offence is to act, most in the late phases.
  - Cost: about 2.5 core-hours.
- **Speed:** the time to finish 1 pair, by level. Predict: slower per position (the readings include the shares), but
  inside the desktop budget.

**13:20: the first self-check failed, and was right to.** The same engine on both sides came out 7.7 points apart
(interval 2.5 to 12.9). Every start had been given the same dice and the same pick noise, so the 40 pairs were one
experiment 40 times. Each position now has its own. The 40-pair pilot above had the same fault, so its interval can't
be trusted; the batch was stopped and restarted with the self-check (60 pairs) first.
