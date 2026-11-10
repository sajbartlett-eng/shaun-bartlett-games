# Step 17, checkpoint 1: learn the weights

## The checkpoint result, with intervals

**Checkpoint 1 fails. I stopped here, as the step says. Stage 2 is not started.**

| Test | Needed | Result |
|---|---|---|
| Head to head against today's computer | a win at p < 0.05 | **A loss.** -4.1 points a pair, interval -5.6 to -2.5, over 320 pairs. 74 wins, 213 losses, 33 ties. A sequential test would have stopped at 91 pairs |
| The exam | beat today's computer, the intervals apart | **No clear gain.** +1.1 points a position, interval -0.3 to +2.5. Marks 24.8 (22.6 to 26.9) against 23.7 (21.7 to 25.8): the intervals overlap |
| The speed budget | stay inside | Inside on a desktop. On a phone, over (as today's computer is) |

**The stop rule also fires.** On held-out possessions the learned weights predict what a possession goes on to earn
no better than the phase average alone: an error of 15.79 points against 15.78 (`fit_pilot.json`, 640 possessions,
27,447 positions). The learning curve flattens onto that level: 16.5, 16.0, 15.8, 15.8 at 64, 160, 320 and 640
possessions. That is at 27,000 labels, not 50,000; I didn't buy the rest, because the head-to-head had already
answered.

## Why it lost

- **The loss is on defence.** In the head-to-head its offence scored 22.2 a possession against today's defence, where
  today's computer scores 21.9 against itself. But it conceded 26.3.
- **The labels came from a weak player.** To afford 640 possessions I played them with the Rookie's settings and
  heavy pick noise. That player scores 15.5 a possession and nothing at all on 45% of them. The weights learned what
  a position is worth *to that player*: about 16 points whatever the board shows.
- **A near-flat judgement gives the defence nothing to defend against.** If every position reads about 16, no
  defensive move looks better than another. On offence the same flatness is harmless or even useful: it takes a good
  shot when one is there, after 23 decisions where today's computer takes 36.
- **The readings didn't separate good positions from bad for that player.** Only in the last phase did they carry
  weight: the shot now, the look this turn, the best look before the cover, the tokens left. In phase 1 no reading's
  weight was clear of zero.

**The outcome exam, by group** (`exam_default_learned.json`; learned less today's computer, points a position):

| Group | Positions | Gain | Interval |
|---|---|---|---|
| All | 152 | +1.1 | -0.3 to +2.5 |
| The hand boards | 22 | -1.3 | -5.3 to +3.1 |
| Stored self-play positions | 130 | +1.6 | +0.1 to +3.0 |
| Phases 1 and 2 | 64 | -1.3 and -2.1 | both include zero |
| Phase 4 | 22 | +4.6 | +1.7 to +7.7 |
| Phases 3, 5 and 6 | 66 | +1.6, +3.6, +2.7 | all include zero |
| The defence to act | 7 | +0.8 | -5.3 to +7.3 |

**The exam missed what the head-to-head caught.** Only 7 of its 152 positions have the defence to act, because the
stored positions are nearly all the offence's. An exam that barely tests defence can't see a defensive loss. It needs
defence positions before it can stand in for the head-to-head.

**What all this does and doesn't show.** It shows labels must come from play as strong as the engine being built,
and that the defence needs its own evidence. It doesn't yet show the readings are missing information: a weak
player's results would hide it either way.

## Compute used against the prediction

| Run | Predicted | Used | Result against the prediction |
|---|---|---|---|
| Head to head, learned against today's computer, 320 pairs | 2.3 core-hours; a gain of 2 to 5 points | 2.53 | **Wrong.** A loss of 4.1. The 40-pair pilot behind the prediction had the seeding fault (checkpoint 0) |
| The outcome exam, 152 positions, 4 seeds, 2 engines | 2.5 core-hours | 2.46 | Partly right: gains in the late phases, losses in phases 1 and 2, no clear gain overall |
| Speed | a little slower, inside the desktop budget | minutes | As predicted |
| The self-check again, 60 pairs | not predicted | about 0.7 | Zero inside the interval |

Total for step 17 so far: about 12 core-hours.

## Speed against the budget

The time to finish 1 pair on 9 decisions in 10, in seconds (`speed_default_learned.json`; phone is the assumed quarter
speed):

| Level | Target: desktop, phone | Today's computer | Learned |
|---|---|---|---|
| Rookie | 0.3, 1.0 | 0.22, 0.87 | 0.26, 1.03 |
| Starter | 1.0, 2.0 | 0.56, 2.26 | 0.68, 2.73 |
| All-Star | 2.5, 3.0 | 1.13, 4.50 | 1.42, 5.67 |

The learned judgement is 20% to 25% slower: its readings include the defence's shares, which today's default doesn't
compute.

## Anything flagged about the fixed items

- **Compute against the plan.** Labels from play as strong as today's computer cost 180 possessions a core-hour. The
  5,000 possessions a real attempt needs are about 28 core-hours, 7 hours on this machine. That is a long run, so it
  needs your go-ahead under the compute rule; the prediction for it is below.
- Nothing about the rules, the weights rule, the explanation rule or the two engines.

## 1. Changes to the printed game

None. `eval.learned` is off.

## 2. What changed

- **The named readings** (`Read.features`, 15 of them, each with its meaning in words in `decide.FEATURES`), in both
  engines: the shot now, the look this turn, the best and second look after the cover, the best look before it, the
  best look after the defence's shares, the paint look next phase, free looks, mismatches by one and two bands, each
  side's tokens, who is to act, defenders and attackers who have moved.
- **`eval.learned`** (off), in both engines: what a position has left to earn = a per-phase average plus each
  reading's weight times how far the reading is from its own average. It replaces the hand-combined reading at the
  search's horizon. Nothing else in the search changes.
- **One weights file,** `playmaker_engine/data/learned_weights.json`: names, per-phase averages and spreads, weights,
  each weight's spread over 20 resampled fits, version and hash. Both engines refuse a file that names other readings.
  The site build and the app carry it.
- **The reasons record** (`Agent._why`, when `eval.learned` is on): the three readings whose weighted parts differ
  most between the chosen turn and the runner-up, a "close call" mark, and a mark on any reading whose weight changes
  sign across the resampled fits.
- **Tools:** `tools/learn_17.py` fits the weights (ridge, per phase, held out by possession), runs the outcome exam
  and the speed measure.

## 3. What it proves

- **The two engines agree on the learned judgement:** 1,000 positions, the readings equal on 915 and the learned
  value on 951 (every one compared), within 1e-9 (`golden_learned_1000.json`). Whole searches with it on: 4 of 4
  equal (`js_equivalence_learned.json`).
- **Tests, every switch off:** `test_rules_current`, `test_static`, `test_step3n`, `test_step3m`: 77 pass, 13 expected
  failures, 1 unexpected pass, and 1 fail in the long run: board 10's test, which runs on the Python search's clock.
  Run alone on an idle machine it passes, and the exam-board tests give step 16's result (7 pass, 10 expected
  failures). Board 10 also passes alone on the code before this step's last changes.
- **The weights that were clear of zero** (last phase, points per one spread of the reading): the best look before
  the cover +1.1, the look this turn +0.6, the shot now +0.5, the defence's tokens +0.7, the offence's tokens -0.6,
  defenders moved -0.8.
- **Near zero in every phase** (evidence, not failure): attackers moved, the best look after the cover, free looks,
  mismatches by two bands.

## 4. For Shaun to decide

- **Try again with labels from strong play?** This is the one experiment that separates "weak labels" from "the
  readings are missing something".
  - Predicted cost: a pilot of 640 possessions by today's computer, 3.6 core-hours, about an hour. Then, only if the
    held-out fit beats the phase average, 5,000 possessions, 28 core-hours.
  - Predicted gain: unknown, and I'd say so plainly. The pilot's question is yes or no: do the readings predict a
    strong player's results at all?
- **Or stop the learned route here** and keep `eval.learned` off as a measured dead end at this size.
- **The exam** (from checkpoint 0): accept the outcome exam, or spend the nights on measured answers.
- **A finding that stands on its own: today's computer holds the ball.** It shoots late, and its reading runs 6 to
  20 points above what the possession goes on to earn. That is a fault you may want fixed whichever route you take.

## 5. Noticed, not touched

- **The weights file in the repo is the failed pilot's.** It is there so the golden test has a file to run on. Don't
  switch `eval.learned` on with it.
- **No worked examples of the reasons record here.** The checkpoint failed, so there is no better judgement to
  explain; the record is built and tested for the format only.
- **The exam book** isn't updated: there are no measured answers to add.
- **Stage 2 (learning which moves to consider) is not started.**

## 6. Model for the next step

Claude Fable 5.2, effort high, if the strong-play pilot goes ahead: reading its result is a research call. If the
learned route stops here, fixing the late shooting is ordinary engine work: Claude Opus 5.5, effort high.
