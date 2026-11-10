# Step 17, checkpoint 0: measure properly

## The checkpoint result, with intervals

**The baseline.** Today's computer (the All-Star, 1 pair ahead) against itself, 60 paired possessions from the stored
possession starts (`h2h_default_vs_default_b.json`):

| | Result |
|---|---|
| Points per possession | 21.9 (23.2 for one copy on offence, 20.6 for the other) |
| Difference between the two copies, per pair | +2.6, interval -1.4 to +6.7: zero is inside, as it should be |
| Wins, losses, ties | 21, 20, 19 |
| Standard deviation of the paired difference | 15.9 points |
| Pairs a real gain needs to show | 243 for 2 points; 971 for 1 point; 3,883 for half a point |

**Flagged first: the bigger exam isn't built as asked, because this machine can't afford it.**

- A possession is 40 to 90 decisions, not the 12 to 24 the research assumed. Playing one costs 9 to 35 core seconds.
- The pilot on the hand boards (below) shows a standard error near 4 points at 16 rollouts a turn. An answer good to
  1 point needs about 150 rollouts a turn.
- 150 positions, 4 turns each, 150 rollouts: about 225 core-hours, 56 hours on these 4 cores.
- **What I built in its place: an outcome exam.** From each of 152 positions the engine under test plays the side to
  act to the end of the possession, against today's computer, on the same dice for every engine. Engines are compared
  position by position. It needs no per-position answer, and costs 2.5 core-hours. Its first run is in checkpoint 1.

## Compute used against the prediction

`docs/runs/step17/PREDICTIONS.md` was written before each run.

| Run | Predicted | Used |
|---|---|---|
| Head to head, today's computer against itself, 40 pairs | 1 core-hour | 0.45 |
| The hand boards measured, 22 decisions, 3 turns, 16 rollouts | 1.5 core-hours; standard errors near 3 | 1.49; median standard error 3.9 |
| Self-play pilot, 640 possessions | 1.6 core-hours; about 30,000 positions | 1.41; 27,447 positions |
| The self-check again after the fix, 60 pairs | not predicted | about 0.7 |

**Throughput** (`throughput.json`), possessions per core-hour:

| Policy | Per core-hour | Points per possession |
|---|---|---|
| Any level, 1 team turn ahead | 2,000 to 4,200 | 5.5 to 7: it never shoots |
| Rookie settings, 1 pair ahead, with pick noise | 405 to 452 | 15.5 (interval 14.3 to 16.7); 45% of possessions score nothing |
| Starter settings, 1 pair ahead | 226 | 21.6 |
| All-Star settings, 1 pair ahead | 100 to 180 | 21.9 |

## Speed against the budget

Nothing in the default game changed. Measured again on the hand boards (`speed_default_learned.json`): 0.22, 0.56 and
1.13 s for 1 pair on 9 decisions in 10. All fit a desktop. At the assumed phone speed the Starter and the All-Star are
over, as before.

## Anything flagged about the fixed items

- **The exam's size and precision against this machine,** above. It isn't a rule or a principle, but it is a fixed
  part of this step I couldn't meet.
- Nothing about the rules, the weights rule, or the explanation rule.

## 1. Changes to the printed game

None.

## 2. What changed

- **Step 16 merged** (pull request 59). D-131 to D-134 are recorded. `docs/reference/` holds the four documents.
- **`tools/playout.js`:** plays possessions with the app's own engine: rollouts of a position or of each candidate
  turn on common dice, paired head-to-head with the sides swapped, self-play that keeps every position, bulk searches.
- **`tools/learn_17.py`:** splits the work over the cores and does the statistics: the mean difference with its 95%
  interval, the win rate with a Wilson interval, the pairs a gain needs, a sequential stop.
- **The engine can write a position back out** (`stateJSON`), and a search can start from a built position.

## 3. What it proves

- **The harness is sound now, and wasn't at first.** The first self-check put the same engine 7.7 points ahead of
  itself (interval 2.5 to 12.9). Every start had been given the same dice and pick noise, so 40 pairs were one
  experiment 40 times. Each position now has its own; the self-check then reads +2.6, zero inside the interval.
- **Today's computer holds the ball.**
  - Looking 1 team turn ahead, it never shoots: it keeps "improving" until the clock runs out.
  - Looking 1 pair ahead with no pick noise, one traced possession took 92 decisions and the shot came with the last
    token.
- **Today's reading is far too hopeful.** On the hand boards the search valued its top turns at 20 to 42 points; the
  same turns played out earned 6 to 25. Over 27,447 self-play positions, its error against what the possession went
  on to earn is 21.6 points; the phase average alone has 15.8.
- **The hand boards measured** (`hand_boards_measured.json`; the computer's top 3 turns, 16 rollouts each):
  - the computer's pick is the measured best on 9 of 22 decisions;
  - it is clearly worse than another of its own top 3 on 3: board 7's last phase, board 14 and board 16;
  - the other 10 can't be told apart at this precision.

## 4. For Shaun to decide

- **The exam.**
  - Option: accept the outcome exam as the bigger exam for now.
  - Option: run measured answers over several nights. About 56 hours on this machine for 150 positions.
  - Option: fewer positions (the 22 hand-board decisions alone are about 25 core-hours).
- **The hand boards' labels (D-133).** No disagreement between your label and the measurement can be listed yet:
  the measurement is too coarse to rule on any board, and I measured the computer's own top turns, not each board's
  labelled answer. That needs the measured answers above.

## 5. Noticed, not touched

- **The stored possessions (step 3n) averaged 25.3 points.** Today's computer scores 21.9 against itself. The rules
  and the reading have changed since they were played, so the two aren't comparable.
- **Common dice only help until the two games part.** Paired differences between candidate turns had intervals of 8
  to 13 points at 16 rollouts.
- **The categories step 14 was to draft** (advantages by stage, the mirror, tier matchups, one-change pairs) aren't
  drafted. The outcome exam's positions are the hand boards and stored self-play positions, spread over the phases.

## 6. Model for the next step

Claude Fable 5.2, effort high: the next work is stage 1's judgement of whether the learned weights carry real
information, which is a research call.
