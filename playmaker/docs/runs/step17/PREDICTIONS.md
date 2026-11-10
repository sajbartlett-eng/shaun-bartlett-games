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

## Run 3: what happened (14:55)

- **Head to head, 320 pairs:** predicted a gain of 2 to 5 points. **Measured a loss of 4.1** (interval -5.6 to
  -2.5). The prediction rested on a pilot with the seeding fault. Cost 2.53 core-hours against 2.3 predicted.
- **The outcome exam:** predicted gains with the offence to act, most in the late phases. Measured +1.1 overall
  (interval -0.3 to +2.5), +4.6 in phase 4, losses in phases 1 and 2. Cost 2.46 core-hours against 2.5.
- **Speed:** as predicted: 20% to 25% slower, inside the desktop budget.
- **Checkpoint 1 fails.** Run 2 (6,400 possessions by the cheap policy) is cancelled: more labels from a weak player
  would not help.

## Run 4 (not started; needs Shaun's go-ahead): labels from strong play

- A pilot of 640 possessions by today's computer, every position kept: about 3.6 core-hours, an hour wall.
- Predict: honestly unknown. The question is yes or no: on held-out possessions, do the readings predict a strong
  player's results better than the phase average? If no, the readings are missing information and the learned route
  stops. If yes, 5,000 possessions (28 core-hours) and a head-to-head of 320 pairs.

# Step 17D (cap: 16 core-hours, the second round included)

## Run 4: the strong-play pilot. Written before it started.

- 640 possessions by today's computer (All-Star settings, pick noise 0.5), both sides, every position kept with its
  readings; one defence-to-act position kept from each for the exam; how each possession ended.
- Cost: predicted 3.6 core-hours, about 55 minutes wall.
- Predict:
  - points a possession near 22, from the self-check;
  - the clock runs out with no shot on more than 1 possession in 100 (the fault D-137 names): I expect 5 to 15;
  - today's reading over by 6 points or more in every phase;
  - the learned weights against the phase average: honestly unknown. Yes or no.

**Run 4, what happened:** 3.73 core-hours (3.6 predicted). 26.5 points a possession (22 predicted: too low). The
clock ran out on 3 in 100 (5 to 15 predicted: too high). The reading is over by 2 points in phase 1 rising to 10 in
phase 6 (6 or more everywhere predicted: wrong early, right late). The learned weights: **no** (13.68 against the
phase average's 13.65).

## Run 5: the calibrated reading against today's computer, head to head. Written before it started.

- The map: per phase and side to act, earned = a + b x reading (the best of four forms on held-out error: 13.64,
  against 13.67 pooled, 13.73 never-falling, 13.79 level only, 14.99 today's reading).
- Sequential, in batches of 80 pairs, up to 480 pairs: at most 3.8 core-hours.
- Predict: a gain of 1 to 3 points a pair. The reading still ranks positions (slopes 0.2 early to 0.8 late), so the
  defence keeps its sense of better and worse, and shots are no longer held against a hope of 6 to 10 points too
  many late in the clock. Fewer possessions should run the clock out; the shot should come earlier.

**Run 5, what happened:** the sequential test stopped at 160 pairs with "a gain": +3.2 points a pair, interval +0.9
to +5.5 (1 to 3 predicted). 1.46 core-hours (at most 3.8 predicted). The calibrated computer shot on 96% of its
possessions against 83%, never ran the clock out in 160 against 5 in 100, and took its shot in phase 2.3 on average
against 3.7.

## Run 6: the second round. Written before it started.

- 640 possessions by the calibrated computer against itself, every position kept. Its possessions are shorter (23
  decisions against 38), so predicted 2.3 core-hours, about 35 minutes.
- Then the map is fitted again on its own play, and tested head to head against today's computer (sequential, up to
  320 pairs, at most 2.5 core-hours).
- Predict: the second map is close to the first in the early phases and less harsh late, because a computer that
  shoots earlier leaves fewer late positions to waste. The head-to-head gain stays within the first round's interval
  (0.9 to 5.5); I don't expect a clear further gain.
- The learned weights are fitted again on this play (the question asked again, as D-136 says). Predict: unknown.

**Run 6, what happened:** self-play 1.96 core-hours (2.3 predicted); head to head 3.25 (at most 2.5 predicted: over,
because the second-round computer's possessions were longer than I expected). The second map: +2.1 points a pair,
interval +0.2 to +4.0, over 320 pairs. Not better than the first (+3.2, +0.9 to +5.5), as predicted. It also has a
hole: the calibrated computer so rarely reaches the last phase that there were too few positions to fit one, so in
phase 6 it fell back on today's reading. **The first round's map is kept, and the rounds stop here.**
The learned weights on calibrated play: 8.75 against the phase average's 8.82, the interval -0.04 to +2.44: not
clear of zero, but closer than before, and the learning curve is still falling.

## Run 7: the outcome exam with the defence positions. Written before it started.

- The 152 positions of checkpoint 1 and about 66 with the defence to act (from the strong-play run, spread over the
  phases), 4 seeds, today's computer and the calibrated one (the first round's map).
- Cost: predicted 3.5 core-hours, about 55 minutes. That takes the step to about 14 of its 16.
- Predict: a gain where the offence is to act, about 2 to 3 points; about level where the defence is to act.

**Run 7, what happened:** 4.42 core-hours (3.5 predicted: over). +3.0 points a position overall (interval +1.9 to
+4.0); +4.0 with the offence to act (2 to 3 predicted: higher); +0.9 with the defence to act, zero inside the interval
(level predicted). Step 17D used about 14.9 of its 16 core-hours.
